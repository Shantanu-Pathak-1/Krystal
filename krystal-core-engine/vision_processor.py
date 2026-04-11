"""
Cloud-only vision: Groq primary with model chain, Gemini fallback — no local inference.

Groq uses a base64 ``data:`` URL in the chat ``image_url`` part with model chain (90b->11b).
Gemini uses ``google-genai`` with a PIL image as fallback when Groq fails.
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors
from groq import APIStatusError, Groq, GroqError, RateLimitError
from PIL import Image

from api_router import KeyManager

GROQ_VISION_MODEL_PRIMARY = "llama-3.3-70b-versatile"
GROQ_VISION_MODEL_FALLBACK = "llama-3.1-8b-instant"
GEMINI_VISION_MODEL = "gemini-2.5-flash"
DEFAULT_PROMPT = "Describe this image in detail"


def _should_rotate_gemini_key(exc: BaseException) -> bool:
    """True when switching to the next Gemini key may help (rate limits / overload)."""
    if isinstance(exc, genai_errors.ClientError):
        code = getattr(exc, "code", None)
        if code == 429:
            return True
        status = (getattr(exc, "status", None) or "").upper()
        if "RESOURCE_EXHAUSTED" in status or "UNAVAILABLE" in status:
            return True
    if isinstance(exc, genai_errors.ServerError):
        code = getattr(exc, "code", None)
        if code in (500, 502, 503, 504):
            return True
    msg = str(exc).lower()
    return (
        "429" in msg
        or "resource exhausted" in msg
        or "quota" in msg
        or "rate limit" in msg
    )


class VisionProcessor:
    """
    Primary: Groq ``llama-3.2-90b-vision-preview`` with model chain (90b->11b) and per-key rotation.
    Fallback: Gemini ``gemini-2.5-flash`` when Groq cannot return a result.
    """

    def __init__(
        self,
        key_manager: KeyManager,
        *,
        groq_primary_model: str = GROQ_VISION_MODEL_PRIMARY,
        groq_fallback_model: str = GROQ_VISION_MODEL_FALLBACK,
        gemini_model: str = GEMINI_VISION_MODEL,
    ) -> None:
        self._keys = key_manager
        self._groq_primary_model = groq_primary_model
        self._groq_fallback_model = groq_fallback_model
        self._gemini_model = gemini_model

    def analyze_image(
        self,
        image_path: str | Path,
        prompt: str = DEFAULT_PROMPT,
    ) -> str:
        path = Path(image_path)
        if not path.is_file():
            return f"[Vision error] Image not found: {path}"

        text = (prompt or DEFAULT_PROMPT).strip() or DEFAULT_PROMPT
        data_url, _mime = _image_to_data_url(path)

        groq_note: str | None = None
        if self._keys.has_groq_keys():
            groq_text, groq_note = self._try_groq_primary(text, data_url)
            if groq_text is not None:
                return groq_text

        if self._keys.has_gemini_keys():
            return self._try_gemini_fallback(path, text, groq_note)

        return (
            groq_note
            or "[Vision error] No Groq keys and no Gemini keys configured for fallback."
        )

    def _try_groq_primary(
        self,
        prompt: str,
        data_url: str,
    ) -> tuple[str | None, str | None]:
        """Try Groq primary model, then fallback model on 400/404 errors."""
        attempts = max(1, self._keys.groq_key_count)
        last_retryable: BaseException | None = None

        for _ in range(attempts):
            api_key = self._keys.get_next_groq_key()
            try:
                # Try primary model first
                out = self._groq_vision_call(api_key, self._groq_primary_model, prompt, data_url)
                return (out, None)
            except (APIStatusError, GroqError) as exc:
                code = getattr(exc, "status_code", None)
                if code in (400, 404):
                    # Model decommissioned, try fallback model with same key
                    try:
                        out = self._groq_vision_call(api_key, self._groq_fallback_model, prompt, data_url)
                        return (out, None)
                    except (APIStatusError, GroqError):
                        # Both models failed, continue to next key
                        continue
                elif code == 429:
                    last_retryable = exc
                    continue
                elif code is not None and 500 <= int(code) < 600:
                    last_retryable = exc
                    continue
                elif code in (401, 403):
                    return (None, f"[Groq auth] {getattr(exc, 'message', exc)}")
                else:
                    return (None, f"[Groq API error] {type(exc).__name__}: {getattr(exc, 'message', str(exc))}")
            except Exception as exc:
                last_retryable = exc
                continue

        detail = str(last_retryable) if last_retryable else "unknown"
        return (
            None,
            f"[Groq] All keys exhausted after rate limits or errors. Last: {detail}",
        )

    def _try_gemini_fallback(
        self,
        path: Path,
        prompt: str,
        groq_note: str | None,
    ) -> str:
        prefix = f"(Fallback after Groq: {groq_note})\n\n" if groq_note else ""
        attempts = max(1, self._keys.gemini_key_count)
        last_retryable: BaseException | None = None

        for _ in range(attempts):
            api_key = self._keys.get_next_gemini_key()
            client = genai.Client(api_key=api_key)
            try:
                im = Image.open(path)
                try:
                    rgb = im.convert("RGB")
                    response = client.models.generate_content(
                        model=self._gemini_model,
                        contents=[rgb, prompt],
                    )
                finally:
                    im.close()
                body = _genai_response_text(response)
                if not body:
                    continue
                return prefix + body
            except genai_errors.APIError as exc:
                if _should_rotate_gemini_key(exc):
                    last_retryable = exc
                    continue
                return prefix + (
                    f"[Gemini API error] {type(exc).__name__}: {exc}"
                )
            except Exception as exc:  # noqa: BLE001
                if _should_rotate_gemini_key(exc):
                    last_retryable = exc
                    continue
                return prefix + f"[Gemini error] {type(exc).__name__}: {exc}"

        detail = str(last_retryable) if last_retryable else "unknown"
        return prefix + (
            f"[Gemini] All keys exhausted after rate limits or errors. Last: {detail}"
        )

    def _groq_vision_call(
        self,
        api_key: str,
        model: str,
        prompt: str,
        data_url: str,
    ) -> str:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url,
                                "detail": "auto",
                            },
                        },
                    ],
                }
            ],
        )
        if not response.choices:
            return ""
        content = response.choices[0].message.content
        return (content or "").strip()


def _image_to_data_url(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    b64 = base64.standard_b64encode(raw).decode("ascii")
    guessed, _ = mimetypes.guess_type(str(path))
    mime = guessed or "image/png"
    if mime not in ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"):
        mime = "image/png"
    data_url = f"data:{mime};base64,{b64}"
    return data_url, mime


def _genai_response_text(response: object) -> str:
    pf = getattr(response, "prompt_feedback", None)
    if pf is not None:
        br = getattr(pf, "block_reason", None)
        if br:
            return f"[Gemini blocked] {br}"
    text = getattr(response, "text", None)
    if text:
        return str(text).strip()
    return ""