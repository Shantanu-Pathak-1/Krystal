"""
Background autonomy loop: periodic LLM check on a daemon thread.
"""

from __future__ import annotations

import threading
from typing import Any
import logging

# Setup logger
logger = logging.getLogger("Krystal.heartbeat")

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
                logger.info("[Heartbeat: Waking up & thinking...]")
                reply = self._llm.generate_response(
                    _HEARTBEAT_USER,
                    system_prompt=_HEARTBEAT_SYSTEM,
                )
            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"[Heartbeat] Network error: {e}")
                continue
            except Exception as e:  # noqa: BLE001
                logger.error(f"[Heartbeat] Error: {e}")
                continue
            line = (reply or "").strip()
            if not line or line.upper() == "NONE":
                logger.info("[Heartbeat: All clear. Sleeping.]")
                continue
            if line.startswith(("No Groq", "All configured", "[LLM error]", "[Groq API")):
                continue
            logger.info(f"[heartbeat] {line}")
