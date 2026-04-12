"""MongoDB database manager for permanent interaction logging."""

import os
from datetime import datetime
from typing import Optional

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False


class MongoManager:
    """
    MongoDB manager for logging Krystal interactions.
    Handles connection management and provides graceful fallback when MongoDB is unavailable.
    """
    
    def __init__(self, connection_string: Optional[str] = None, 
                 database_name: str = "krystal_db", 
                 collection_name: str = "chat_logs"):
                 
        self.connection_string = connection_string or os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self.is_connected = False
        
        if not PYMONGO_AVAILABLE:
            print("\033[90m[MongoDB Warning: pymongo not installed]\033[0m")
            return
            
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to MongoDB with a short timeout to prevent hanging."""
        try:
            # 2-second timeout so it doesn't freeze the terminal
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
            # Force ping to check if server is actually online
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            self.is_connected = True
        except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError):
            # Silently handle database errors - No terminal spam!
            print("\033[90m[MongoDB Offline: Running Krystal without chat history logs]\033[0m")
            self.is_connected = False
        except Exception:
            self.is_connected = False
    
    def log_interaction(self, user_input: str, response: str, plugin_used: Optional[str] = None) -> None:
        """Log an interaction to the database."""
        if not self.is_connected:
            return
            
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_input": user_input,
                "response": response,
                "plugin_used": plugin_used,
                "session_id": "default"
            }
            self.collection.insert_one(log_entry)
        except Exception:
            pass # Silent fail during runtime
    
    def get_recent_logs(self, limit: int = 5) -> list:
        """Fetch recent interaction logs from MongoDB."""
        if not self.is_connected:
            return []
            
        try:
            logs = list(self.collection.find({}, {'_id': 0}).sort("timestamp", -1).limit(limit))
            return logs
        except Exception:
            return []
    
    def close(self) -> None:
        """Close the MongoDB connection."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
            self.is_connected = False
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.close()