"""
Background autonomy loop: periodic LLM check on a daemon thread.
"""

from __future__ import annotations

import threading
from typing import Any

_HEARTBEAT_SYSTEM = (
    "You are Krystal's background process. Is there any scheduled task or "
    "observation you need to make? Reply with 'NONE' if nothing."
)
_HEARTBEAT_USER = "Report briefly."


class Heartbeat:
    """
    Runs ``LLMProcessor`` on an interval inside a daemon thread.
    Non-``NONE`` replies are printed in a dim ANSI color (when supported).
    """

    def __init__(
        self,
        llm_processor: Any,
        *,
        interval_sec: float = 60.0,
    ) -> None:
        self._llm = llm_processor
        self._interval = interval_sec
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="KrystalHeartbeat", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            try:
                print("\033[90m[Heartbeat: Waking up & thinking...]\033[0m", flush=True)
                reply = self._llm.generate_response(
                    _HEARTBEAT_USER,
                    system_prompt=_HEARTBEAT_SYSTEM,
                )
            except Exception:  # noqa: BLE001
                continue
            line = (reply or "").strip()
            if not line or line.upper() == "NONE":
                print("\033[90m[Heartbeat: All clear. Sleeping.]\033[0m", flush=True)
                continue
            if line.startswith(("No Groq", "All configured", "[LLM error]", "[Groq API")):
                continue
            print(f"\033[90m[heartbeat] {line}\033[0m", flush=True)
