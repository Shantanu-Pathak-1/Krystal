"""Primary-monitor screenshot + cloud vision (Groq primary with model chain, Gemini fallback)."""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

NAME = "/see"
DESCRIPTION = "Takes a screenshot of the current screen and analyzes it."


def clean_old_screenshots(cache_dir: Path, days: int = 10) -> None:
    """Delete ``*.png`` in ``cache_dir`` whose modification time is older than ``days``."""
    if not cache_dir.is_dir():
        return
    cutoff = time.time() - float(days) * 86400.0
    for path in cache_dir.glob("*.png"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink(missing_ok=True)
        except OSError:
            pass


def run(query, **kwargs):
    _ = kwargs
    
    # Dynamic import: Only load mss when this tool is actually called
    try:
        import mss
        from mss import tools as mss_tools
    except ImportError:
        return "Error: mss not available. Install with: pip install mss"
    
    root = Path(__file__).resolve().parent.parent
    engine_dir = root / "krystal-core-engine"
    if str(engine_dir) not in sys.path:
        sys.path.insert(0, str(engine_dir))

    from api_router import KeyManager
    from vision_processor import VisionProcessor

    # Clean old screenshots first
    cache_dir = root / "memory" / "vision_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    clean_old_screenshots(cache_dir, days=10)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_path = cache_dir / f"temp_vision_{stamp}.png"

    env_file = root / ".env"
    keys = KeyManager(env_path=env_file if env_file.is_file() else None)

    try:
        with mss.mss() as sct:
            mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            shot = sct.grab(mon)
            mss_tools.to_png(shot.rgb, shot.size, output=str(temp_path))

        vp = VisionProcessor(keys)
        
        # First, categorize the screenshot
        categorization_prompt = """Is this image purely technical/work (like code, IDE, terminal) or is it personal/memorable (a face, a nice view, a personal chat, family photos)? 
        Respond with ONLY one word: "technical" or "memorable"."""
        
        categorization = vp.analyze_image(temp_path, prompt=categorization_prompt).strip().lower()
        is_memorable = "memorable" in categorization
        
        # Determine final save location based on categorization
        if is_memorable:
            # Save to diary_photos for memorable images
            diary_dir = root / "memory" / "diary_photos"
            diary_dir.mkdir(parents=True, exist_ok=True)
            path = diary_dir / f"memorable_{stamp}.png"
            print(f"Memorable screenshot saved to diary: {path}")
        else:
            # Save to regular cache for technical images
            path = cache_dir / f"vision_capture_{stamp}.png"
        
        # Move to final location
        temp_path.rename(path)
        
        prompt = (
            query.strip()
            if query and query.strip()
            else "Describe this screen capture in detail."
        )
        
        analysis = vp.analyze_image(path, prompt=prompt)
        
        result = analysis
        if is_memorable:
            result += f"\n\n[This screenshot was saved as memorable in the diary]"
        
        return result
    except Exception as exc:  # noqa: BLE001
        return f"[/see error] {type(exc).__name__}: {exc}"