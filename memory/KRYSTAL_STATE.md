# Krystal — Master context (multi-AI handoffs)

## Project goal

Build a **lightweight, autonomous, event-driven Python AI engine** (“Krystal”) with a small, stable runtime and clear extension points. The system should remain easy to reason about, deploy, and hand off between people and AI assistants.

## Architecture rules

1. **`krystal-core-engine` is immutable**  
   Treat the core package as a fixed contract: stable imports, predictable behavior, and no ad-hoc feature creep inside core modules.

2. **Features live in `plugins/`**  
   New capabilities are added as **standalone scripts or packages** under `plugins/`, loaded and orchestrated by the engine/plugin layer—not by editing core internals for one-off behavior.

3. **State and handoffs**  
   This file (`memory/KRYSTAL_STATE.md`) is the **master context** for multi-AI and multi-session continuity. Prefer updating it when decisions or structure change materially.

---

## STRICT INSTRUCTION FOR AI

Before you finish your response for any session that **created or modified** any project file, you **MUST** append **one line** to the **Session Changelog** below (bottom of this file). Each line should briefly state **what** changed (file or area + short summary). Do not remove prior lines.

---

## Session Changelog

- Initialized base directory structure, `memory/KRYSTAL_STATE.md`, and `krystal-core-engine/api_router.py` (`KeyManager` with multi-key `.env` loading and round-robin rotation).
- Added additive core: `plugin_manager.py` (`PluginManager` — dynamic `plugins/` scan, strict `NAME`/`DESCRIPTION`/`run` contract, isolated plugin errors) and `engine.py` (`KrystalEngine` — `process_input` slash routing + masked LLM fallback stub).
- Added root `main.py` (interactive `Krystal>` REPL, exit/quit) and `plugins/sys_status.py` (`/status` health plugin); `PluginManager` now normalizes `NAME` with an optional leading `/` so commands like `/status` match.
- `llm_processor.py` added with Groq integration and round-robin key rotation on rate limits (429); `engine.py` routes non-slash input through it; `groq` added to `requirements.txt`; `KeyManager` now tracks `GROQ_KEY_*` separately for Groq calls.
- Updated KeyManager for Groq/Gemini, built VisionProcessor with Groq->Gemini fallback, and added /see plugin using mss for lightweight screen capture.
- Added python-dotenv for env loading and migrated Gemini vision fallback to the modern google-genai SDK.
- Moved load_dotenv() directly into KeyManager initialization to fix the import-order bug and guarantee API key loading.
- Removed python-dotenv. Implemented a native, zero-dependency .env file parser in KeyManager to bypass all OS-level path and loading bugs.
- Swapped Gemini to Primary Vision, implemented 10-day screenshot cache, and built the background Heartbeat daemon thread for true autonomy.
- Made heartbeat visible, added /browse plugin using Playwright for web scraping, and integrated MongoDB in db_manager for permanent interaction logging.
- Implemented Groq Model Chain (90b->11b) to fix 400 errors, added 10-day persistent screenshot caching in read_screen, and built visible Heartbeat daemon thread.
- Added /browse plugin using Playwright for web scraping, and integrated MongoDB via db_manager for permanent interaction logging.
- Finalized Core: Fixed Groq Vision chain, added Playwright /browse plugin, and integrated MongoDB history logging.
- Added Senses: pyttsx3 for offline voice, SpeechRecognition for mic input (/listen), and OpenCV for webcam vision (/webcam).
- Switched TTS to female voice. Integrated Pinecone for long-term vector semantic memory.
- Built the Emotional Core: Smart vision categorization for memorable photos and the /write_diary plugin for generating a first-person Markdown journal.
- Implemented Dual-Memory Architecture: MongoDB for exact short-term chat logs and Pinecone for long-term semantic vector memories.
- Implemented Agentic Routing for automatic smart tool selection without slash commands, and added /os plugin for real OS and default browser control.
- Cleaned up MongoDB connection errors to prevent terminal spam. Created /social plugin skeleton to act as a routing hub for Telegram, WhatsApp, Instagram, and LinkedIn.
- Built Social Firewall: Implemented strict ALLOWED_CONTACTS list and a hard-coded absolute block against any Group Chat interactions to prevent AI spam.
- Built God-Mode System Ops: Added /sys plugin for Windows settings and file management, protected by a strict SecurityGuard module requiring TRINETRA-OVERRIDE codeword for deletions.
- Overrode browser limitations: Added pywhatkit for direct YouTube auto-playback and pyautogui for global media controls (play/pause/next/prev). Krystal now has true God Mode media control.
- Implemented hardware-level Windows volume control using pycaw and updated Router to parse Hinglish volume commands (full, tez, kam) into strict integer values.
- Fixed Router chattiness bug by enforcing strict output formatting. Mapped 'stop/rok do' aliases to media pause controls.
