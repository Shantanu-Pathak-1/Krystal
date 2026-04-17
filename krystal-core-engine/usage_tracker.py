"""
Usage tracker for monitoring API calls and resource consumption.
Tracks provider usage, request counts, and daily limits.
"""

import json
import os
from datetime import datetime, date
from typing import Dict, Any, Optional
from pathlib import Path
import logging

# Setup logger
logger = logging.getLogger("Krystal.usage")

class UsageTracker:
    """Tracks API usage across different providers."""
    
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            # Store usage data in krystal-core-engine directory
            self.storage_path = Path(__file__).parent / "usage_data.json"
        else:
            self.storage_path = Path(storage_path)
        
        self.usage_data = self._load_usage_data()
    
    def _load_usage_data(self) -> Dict[str, Any]:
        """Load usage data from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"[Usage Tracker] Error loading usage data: {e}")
                pass
            except Exception as e:
                logger.error(f"[Usage Tracker] Unexpected error loading data: {e}")
                pass
        
        # Return default structure
        return {
            "providers": {
                "groq": {
                    "total_requests": 0,
                    "daily_requests": 0,
                    "daily_limit": 2000,
                    "last_reset": date.today().isoformat()
                },
                "sambanova": {
                    "total_requests": 0,
                    "daily_requests": 0,
                    "daily_limit": 1000,
                    "last_reset": date.today().isoformat()
                },
                "together": {
                    "total_requests": 0,
                    "daily_requests": 0,
                    "daily_limit": 1500,
                    "last_reset": date.today().isoformat()
                },
                "openrouter": {
                    "total_requests": 0,
                    "daily_requests": 0,
                    "daily_limit": 3000,
                    "last_reset": date.today().isoformat()
                },
                "fireworks": {
                    "total_requests": 0,
                    "daily_requests": 0,
                    "daily_limit": 2500,
                    "last_reset": date.today().isoformat()
                },
                "gemini": {
                    "total_requests": 0,
                    "daily_requests": 0,
                    "daily_limit": 1500,
                    "last_reset": date.today().isoformat()
                },
                "huggingface": {
                    "total_requests": 0,
                    "daily_requests": 0,
                    "daily_limit": 1000,
                    "last_reset": date.today().isoformat()
                },
                "ollama": {
                    "total_requests": 0,
                    "daily_requests": 0,
                    "daily_limit": 999999,  # Unlimited for local
                    "last_reset": date.today().isoformat()
                }
            },
            "storage": {
                "mongodb": {
                    "database_size_mb": 0,
                    "document_count": 0,
                    "last_updated": datetime.utcnow().isoformat()
                },
                "pinecone": {
                    "vector_count": 0,
                    "index_fullness_percent": 0,
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _save_usage_data(self):
        """Save usage data to storage."""
        try:
            self.usage_data["last_updated"] = datetime.utcnow().isoformat()
            with open(self.storage_path, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except (PermissionError, OSError) as e:
            logger.warning(f"[Usage Tracker] Permission error saving data: {e}")
        except Exception as e:
            logger.error(f"[Usage Tracker] Failed to save usage data: {e}")
    
    def _reset_daily_counters_if_needed(self):
        """Reset daily counters if it's a new day."""
        today = date.today()
        
        for provider, data in self.usage_data["providers"].items():
            last_reset = date.fromisoformat(data["last_reset"])
            if today > last_reset:
                data["daily_requests"] = 0
                data["last_reset"] = today.isoformat()
    
    def track_request(self, provider: str):
        """Track a single API request to a provider."""
        self._reset_daily_counters_if_needed()
        
        if provider not in self.usage_data["providers"]:
            # Add new provider if not exists
            self.usage_data["providers"][provider] = {
                "total_requests": 0,
                "daily_requests": 0,
                "daily_limit": 1000,
                "last_reset": date.today().isoformat()
            }
        
        provider_data = self.usage_data["providers"][provider]
        provider_data["total_requests"] += 1
        provider_data["daily_requests"] += 1
        
        self._save_usage_data()
    
    def update_storage_stats(self, mongodb_stats: Dict[str, Any], pinecone_stats: Dict[str, Any]):
        """Update storage statistics."""
        self.usage_data["storage"]["mongodb"] = {
            "database_size_mb": mongodb_stats.get("database_size_mb", 0),
            "document_count": mongodb_stats.get("document_count", 0),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        self.usage_data["storage"]["pinecone"] = {
            "vector_count": pinecone_stats.get("vector_count", 0),
            "index_fullness_percent": pinecone_stats.get("index_fullness_percent", 0),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        self._save_usage_data()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics."""
        self._reset_daily_counters_if_needed()
        
        # Calculate daily usage percentages
        for provider, data in self.usage_data["providers"].items():
            daily_limit = data["daily_limit"]
            daily_requests = data["daily_requests"]
            data["daily_usage_percent"] = min(100, (daily_requests / daily_limit) * 100) if daily_limit > 0 else 0
        
        return self.usage_data
    
    def get_provider_stats(self, provider: str) -> Dict[str, Any]:
        """Get stats for a specific provider."""
        if provider not in self.usage_data["providers"]:
            return {}
        
        data = self.usage_data["providers"][provider].copy()
        data["daily_usage_percent"] = min(100, (data["daily_requests"] / data["daily_limit"]) * 100) if data["daily_limit"] > 0 else 0
        return data
    
    def reset_provider_stats(self, provider: str):
        """Reset stats for a specific provider."""
        if provider in self.usage_data["providers"]:
            self.usage_data["providers"][provider] = {
                "total_requests": 0,
                "daily_requests": 0,
                "daily_limit": self.usage_data["providers"][provider]["daily_limit"],
                "last_reset": date.today().isoformat()
            }
            self._save_usage_data()


# Global instance for easy access
_usage_tracker = None

def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance."""
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = UsageTracker()
    return _usage_tracker

def track_api_call(provider: str):
    """Track an API call to the specified provider."""
    tracker = get_usage_tracker()
    tracker.track_request(provider)
