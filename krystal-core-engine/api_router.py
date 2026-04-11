"""API key discovery and round-robin distribution for external model providers.

Environment / ``.env`` examples (each family rotates on its own; names sort for stable order)::

    GROQ_KEY_1=gsk_...
    GROQ_KEY_2=gsk_...
    GEMINI_KEY_1=...
    GEMINI_KEY_2=...

The repo-root ``.env`` is read by ``KeyManager`` using a small built-in parser
(no third-party dotenv dependency).
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

_KEY_PREFIXES = ("GEMINI_KEY_", "GROQ_KEY_")


class KeyManager:
    """
    Loads multiple API keys from the environment (typically via `.env`) and
    returns them in round-robin order to spread load across keys.
    """

    def __init__(self, env_path: str | Path | None = None) -> None:
        """
        Parse the project ``.env`` into ``os.environ``, then optionally merge a
        second file if ``env_path`` is given. After that, discover
        ``GEMINI_KEY_*`` / ``GROQ_KEY_*`` entries.
        """
        root_env = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".env",
        )
        self._ingest_env_file(root_env)
        if env_path is not None:
            self._ingest_env_file(os.path.abspath(os.fspath(env_path)))

        self._keys: list[str] = self._discover_keys()
        self._groq_keys: list[str] = self._discover_keys_with_prefix("GROQ_KEY_")
        self._gemini_keys: list[str] = self._discover_keys_with_prefix("GEMINI_KEY_")
        self._lock = threading.Lock()
        self._next_index = 0
        self._groq_next_index = 0
        self._gemini_next_index = 0

    @staticmethod
    def _ingest_env_file(path: str) -> None:
        """Read ``path`` as UTF-8 and set ``os.environ`` for each ``KEY=value`` line."""
        if not os.path.exists(path):
            return
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if not key:
                    continue
                os.environ[key] = value

    @staticmethod
    def _discover_keys() -> list[str]:
        pairs: list[tuple[str, str]] = []
        for name, value in os.environ.items():
            if not any(name.startswith(p) for p in _KEY_PREFIXES):
                continue
            stripped = (value or "").strip()
            if not stripped:
                continue
            pairs.append((name, stripped))
        pairs.sort(key=lambda item: item[0])
        return [v for _, v in pairs]

    @staticmethod
    def _discover_keys_with_prefix(prefix: str) -> list[str]:
        pairs: list[tuple[str, str]] = []
        for name, value in os.environ.items():
            if not name.startswith(prefix):
                continue
            stripped = (value or "").strip()
            if not stripped:
                continue
            pairs.append((name, stripped))
        pairs.sort(key=lambda item: item[0])
        return [v for _, v in pairs]

    @property
    def key_count(self) -> int:
        return len(self._keys)

    def has_keys(self) -> bool:
        return bool(self._keys)

    @property
    def groq_key_count(self) -> int:
        return len(self._groq_keys)

    def has_groq_keys(self) -> bool:
        return bool(self._groq_keys)

    def get_next_groq_key(self) -> str:
        """
        Return the next **Groq-only** API key in rotation (``GROQ_KEY_*`` vars).

        Raises:
            RuntimeError: If no Groq keys were found.
        """
        if not self._groq_keys:
            raise RuntimeError(
                "No Groq API keys found. Add non-empty variables named "
                "`GROQ_KEY_1`, `GROQ_KEY_2`, ... to your environment or `.env` file."
            )
        with self._lock:
            key = self._groq_keys[self._groq_next_index % len(self._groq_keys)]
            self._groq_next_index += 1
        return key

    @property
    def gemini_key_count(self) -> int:
        return len(self._gemini_keys)

    def has_gemini_keys(self) -> bool:
        return bool(self._gemini_keys)

    def get_next_gemini_key(self) -> str:
        """
        Return the next **Gemini-only** API key in rotation (``GEMINI_KEY_*`` vars).

        Raises:
            RuntimeError: If no Gemini keys were found.
        """
        if not self._gemini_keys:
            raise RuntimeError(
                "No Gemini API keys found. Add non-empty variables named "
                "`GEMINI_KEY_1`, `GEMINI_KEY_2`, ... to your environment or `.env` file."
            )
        with self._lock:
            key = self._gemini_keys[self._gemini_next_index % len(self._gemini_keys)]
            self._gemini_next_index += 1
        return key

    def get_next_key(self) -> str:
        """
        Return the next key in rotation. Thread-safe.

        Raises:
            RuntimeError: If no keys were found in the environment.
        """
        if not self._keys:
            raise RuntimeError(
                "No API keys found. Define one or more non-empty variables "
                f"whose names start with {', '.join(repr(p) for p in _KEY_PREFIXES)} "
                "in your environment or `.env` file."
            )
        with self._lock:
            key = self._keys[self._next_index % len(self._keys)]
            self._next_index += 1
        return key

    def peek_next_key(self) -> str:
        """
        Return the key that would be handed out next, without advancing rotation.

        Raises:
            RuntimeError: If no keys were found.
        """
        if not self._keys:
            raise RuntimeError(
                "No API keys found. Define one or more non-empty variables "
                f"whose names start with {', '.join(repr(p) for p in _KEY_PREFIXES)} "
                "in your environment or `.env` file."
            )
        with self._lock:
            return self._keys[self._next_index % len(self._keys)]
