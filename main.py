"""
Krystal Autonomous AI Engine — interactive entry point.

Imports the engine from the ``krystal-core-engine`` directory. Python cannot
parse a hyphen in a dotted import, so that folder is added to ``sys.path`` and
``KrystalEngine`` is imported from the ``engine`` module there.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parent / "krystal-core-engine"
_engine_path = str(_ENGINE_DIR)
if _engine_path not in sys.path:
    sys.path.insert(0, _engine_path)

from engine import KrystalEngine  # noqa: E402
from heartbeat import Heartbeat  # noqa: E402


def main() -> None:
    engine = KrystalEngine()
    Heartbeat(engine.llm, interval_sec=60.0).start()
    print("Krystal engine ready. Commands: `/status`, or type exit/quit.")
    while True:
        try:
            line = input("Krystal> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not line.strip():
            continue

        if line.strip().lower() in ("exit", "quit"):
            print("Goodbye.")
            break

        print(engine.process_input(line))


if __name__ == "__main__":
    main()
