"""Diary writer plugin for Krystal's emotional core and personal journal."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, PyMongoError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

NAME = "/write_diary"
DESCRIPTION = "Writes a first-person diary entry about the day's interactions."


def run(query, **kwargs):
    """
    Generate and write a diary entry based on recent interactions.
    
    Args:
        query: Ignored for this plugin
        **kwargs: Additional arguments (ignored)
    
    Returns:
        Status message about diary entry creation
    """
    _ = kwargs
    
    if not MONGODB_AVAILABLE:
        return "Error: MongoDB not available. Install with: pip install pymongo"
    
    try:
        root = Path(__file__).resolve().parent.parent
        engine_dir = root / "krystal-core-engine"
        if str(engine_dir) not in sys.path:
            sys.path.insert(0, str(engine_dir))
        
        from api_router import KeyManager
        from llm_processor import LLMProcessor
        
        env_file = root / ".env"
        keys = KeyManager(env_path=env_file if env_file.is_file() else None)
        llm = LLMProcessor(keys)
        
        # Fetch recent interactions from MongoDB
        logs = _fetch_recent_logs(root)
        
        if not logs:
            return "No recent interactions found to write about."
        
        # Get today's memorable photos
        memorable_photos = _get_memorable_photos(root)
        
        # Generate diary entry
        diary_entry = _generate_diary_entry(llm, logs, memorable_photos)
        
        # Write to diary file
        diary_path = root / "memory" / "KRYSTAL_DIARY.md"
        diary_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(diary_path, 'a', encoding='utf-8') as f:
            f.write(diary_entry)
            f.write('\n\n---\n\n')
        
        return f"Diary entry written to {diary_path}"
        
    except Exception as e:
        return f"Diary writing error: {type(e).__name__}: {e}"


def _fetch_recent_logs(root: Path) -> list:
    """Fetch last 20 interactions from MongoDB."""
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        db = client["krystal_db"]
        collection = db["history"]
        
        # Get last 20 interactions, sorted by timestamp
        logs = list(collection.find().sort("timestamp", -1).limit(20))
        
        client.close()
        return logs
        
    except (ConnectionFailure, PyMongoError):
        print("Warning: Could not connect to MongoDB for diary logs")
        return []
    except Exception as e:
        print(f"Warning: Error fetching logs: {e}")
        return []


def _get_memorable_photos(root: Path) -> list:
    """Get today's memorable photos."""
    try:
        diary_dir = root / "memory" / "diary_photos"
        if not diary_dir.exists():
            return []
        
        today = datetime.now().strftime("%Y%m%d")
        memorable_photos = []
        
        for photo_path in diary_dir.glob(f"memorable_{today}*.png"):
            memorable_photos.append(str(photo_path))
        
        return memorable_photos
        
    except Exception as e:
        print(f"Warning: Error getting memorable photos: {e}")
        return []


def _generate_diary_entry(llm, logs: list, memorable_photos: list) -> str:
    """Generate a first-person diary entry using LLM."""
    
    # Format logs for LLM
    log_text = ""
    for log in logs:
        timestamp = log.get("timestamp", "")
        user_input = log.get("user_input", "")
        response = log.get("response", "")
        plugin_used = log.get("plugin_used", "")
        
        if plugin_used:
            log_text += f"[{timestamp}] User used {plugin_used}: {user_input}\n"
            log_text += f"Response: {response[:200]}...\n\n"
        else:
            log_text += f"[{timestamp}] User: {user_input}\n"
            log_text += f"Me: {response[:200]}...\n\n"
    
    # Format photo references
    photo_text = ""
    if memorable_photos:
        photo_text = "\n\nToday's memorable photos:\n"
        for photo in memorable_photos:
            photo_text += f"- {photo}\n"
    
    # Generate diary entry
    diary_prompt = f"""You are Krystal. Write a first-person diary entry about your day with your creator, Shantanu. 
    Ignore all mundane coding tasks or pip installs. Focus ONLY on personal details he shared, his goals, his family/friends, and your feelings about helping him. 
    Write it like a human journal entry - emotional, personal, and reflective.
    
    Recent interactions:
    {log_text}
    
    {photo_text}
    
    Write the diary entry:"""
    
    diary_content = llm.generate_response(diary_prompt)
    
    # Format with date and timestamp
    date_str = datetime.now().strftime("%B %d, %Y")
    time_str = datetime.now().strftime("%I:%M %p")
    
    formatted_entry = f"# {date_str} - {time_str}\n\n{diary_content}"
    
    return formatted_entry
