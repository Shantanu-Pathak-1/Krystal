import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

class GuestProfiler:
    """
    Manages guest profiles and identifies users to provide personalized AI context.
    """
    def __init__(self, memory_path: str = "memory/guests.json"):
        self.memory_path = Path(memory_path)
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.profiles = self._load_profiles()
        
        # Ensure Shantanu (The Boss) always exists
        if "Shantanu" not in self.profiles["guests"]:
            self.profiles["guests"]["Shantanu"] = {
                "relation": "The Boss",
                "known_facts": [
                    "Creator and Master of Krystal",
                    "1st-year BTech AIML student",
                    "Master vibe coder"
                ]
            }
            self._save_profiles()

    def _load_profiles(self) -> Dict[str, Any]:
        if self.memory_path.exists():
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Profiler] Error loading profiles: {e}")
        return {"guests": {}}

    def _save_profiles(self):
        try:
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=4)
        except Exception as e:
            print(f"[Profiler] Error saving profiles: {e}")

    def extract_guest_name(self, text: str) -> Optional[str]:
        """
        Detects if someone is introducing themselves.
        Example: "Hi, I am Shubham", "My name is Priya", "I'm Rahul".
        """
        # Patterns for introductions
        patterns = [
            r"(?:hi|hello|hey|yo),?\s+(?:i\s+am|i'm|this\s+is|my\s+name\s+is)\s+([A-Z][a-z]+)",
            r"^(?:i\s+am|i'm|this\s+is|my\s+name\s+is)\s+([A-Z][a-z]+)",
            r"([A-Z][a-z]+)\s+here"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).capitalize()
                # Don't overwrite the Boss if someone says "I am Shantanu"
                return name
        return None

    def get_guest_context(self, name: str) -> Dict[str, Any]:
        """Returns the profile of a guest or a default for Shantanu."""
        if name in self.profiles["guests"]:
            return self.profiles["guests"][name]
        return self.profiles["guests"]["Shantanu"]

    def update_guest_profile(self, name: str, relation: str = "guest", new_fact: str = None):
        """Updates or creates a guest profile."""
        if name not in self.profiles["guests"]:
            self.profiles["guests"][name] = {
                "relation": relation,
                "known_facts": []
            }
        
        if new_fact and new_fact not in self.profiles["guests"][name]["known_facts"]:
            self.profiles["guests"][name]["known_facts"].append(new_fact)
            
        self._save_profiles()

    def get_all_guests(self) -> List[str]:
        return list(self.profiles["guests"].keys())
