"""
Groq-backed LLM calls for natural-language input.

Keys are supplied by ``KeyManager`` (never hard-coded). Configure Groq keys in
your ``.env`` at the project root, for example::

    GROQ_KEY_1=gsk_xxxxxxxx
    GROQ_KEY_2=gsk_yyyyyyyy

Use incrementing suffixes (``GROQ_KEY_3``, …) for more keys. Only variables
whose names start with ``GROQ_KEY_`` are used for Groq requests.
"""

from __future__ import annotations

from typing import Any

from groq import APIStatusError, Groq, GroqError, RateLimitError

DEFAULT_MODEL = "llama-3.1-8b-instant"


class LLMProcessor:
    """
    Calls the Groq Chat Completions API using keys from ``KeyManager``.

    On ``429`` / ``RateLimitError``, advances to the next Groq key and retries
    until each configured key has been tried once for this request.
    """

    def __init__(self, key_manager: Any, model: str | None = None) -> None:
        self._keys = key_manager
        self._model = model or DEFAULT_MODEL

    def generate_response(
        self,
        user_text: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        text = (user_text or "").strip()
        if not text and not (system_prompt and system_prompt.strip()):
            return "(No message to send.)"

        if not self._keys.has_groq_keys():
            return (
                "No Groq API keys configured. Add entries to your `.env`, e.g. "
                "`GROQ_KEY_1`, `GROQ_KEY_2`, ... (see `llm_processor` module docstring)."
            )

        attempts = max(1, self._keys.groq_key_count)
        last_rate_limit: RateLimitError | APIStatusError | None = None

        user_message = text if text else "."
        for _ in range(attempts):
            api_key = self._keys.get_next_groq_key()
            try:
                return self._call_groq(api_key, user_message, system_prompt=system_prompt)
            except RateLimitError as exc:
                last_rate_limit = exc
                continue
            except APIStatusError as exc:
                if getattr(exc, "status_code", None) == 429:
                    last_rate_limit = exc
                    continue
                return self._format_error(exc)
            except GroqError as exc:
                return self._format_error(exc)
            except Exception as exc:  # noqa: BLE001 — last-resort surface
                return f"[LLM error] {type(exc).__name__}: {exc}"

        detail = getattr(last_rate_limit, "message", str(last_rate_limit))
        return (
            "All configured Groq keys hit rate limits (or returned 429) for this request. "
            f"Last error: {detail}"
        )

    def _call_groq(
        self,
        api_key: str,
        user_message: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        client = Groq(api_key=api_key)
        messages: list[dict[str, str]] = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": user_message})
        response = client.chat.completions.create(
            model=self._model,
            messages=messages,
        )
        if not response.choices:
            return ""
        content = response.choices[0].message.content
        return (content or "").strip()

    def generate_response_from_messages(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        """Generate response from a list of messages (for full conversation context)."""
        if not messages:
            return "(No messages to send.)"

        if not self._keys.has_groq_keys():
            return (
                "No Groq API keys configured. Add entries to your `.env`, e.g. "
                "`GROQ_KEY_1`, `GROQ_KEY_2`, ... (see `llm_processor` module docstring)."
            )

        attempts = max(1, self._keys.groq_key_count)
        last_rate_limit: RateLimitError | APIStatusError | None = None

        for _ in range(attempts):
            api_key = self._keys.get_next_groq_key()
            try:
                return self._call_groq_with_messages(api_key, messages)
            except RateLimitError as exc:
                last_rate_limit = exc
                continue
            except APIStatusError as exc:
                if getattr(exc, "status_code", None) == 429:
                    last_rate_limit = exc
                    continue
                return self._format_error(exc)
            except GroqError as exc:
                return self._format_error(exc)
            except Exception as exc:
                return f"[LLM error] {type(exc).__name__}: {exc}"

        detail = getattr(last_rate_limit, "message", str(last_rate_limit))
        return (
            "All configured Groq keys hit rate limits (or returned 429) for this request. "
            f"Last error: {detail}"
        )

    def _call_groq_with_messages(
        self,
        api_key: str,
        messages: list[dict[str, str]],
    ) -> str:
        """Internal method to call Groq with pre-formatted messages list."""
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=messages,
        )
        if not response.choices:
            return ""
        content = response.choices[0].message.content
        return (content or "").strip()

    @staticmethod
    def _format_error(exc: GroqError) -> str:
        return f"[Groq API error] {type(exc).__name__}: {getattr(exc, 'message', str(exc))}"
