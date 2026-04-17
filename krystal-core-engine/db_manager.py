"""MongoDB database manager for permanent interaction logging with session-based consolidation."""

import os
import json
from datetime import datetime
from typing import Optional, Dict, List
import logging

# Setup logger
logger = logging.getLogger("Krystal.db")

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

# In-memory session buffer for consolidation
# Structure: {session_id: [{timestamp, user_input, response, plugin_used}, ...]}
_session_buffer: Dict[str, List[dict]] = {}


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

        # Session consolidation settings
        self.consolidation_threshold = 5  # Consolidate after 5 interactions
        self.summaries_collection_name = "session_summaries"
        self.summaries_collection = None

        if not PYMONGO_AVAILABLE:
            logger.warning("MongoDB Warning: pymongo not installed")
            return

        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to MongoDB with a short timeout to prevent hanging."""
        try:
            # 10-second timeout for MongoDB Atlas (was 2s, too short for cloud)
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=10000)
            # Force ping to check if server is actually online
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            self.summaries_collection = self.db[self.summaries_collection_name]
            self.is_connected = True
        except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError):
            # Silently handle database errors - No terminal spam!
            logger.info("MongoDB Offline: Running Krystal without chat history logs")
            self.is_connected = False
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"[DB] Network error connecting to MongoDB: {e}")
            self.is_connected = False
        except Exception as e:
            logger.error(f"[DB] Error connecting to MongoDB: {e}")
            self.is_connected = False
    
    def log_interaction(self, user_input: str, response: str, plugin_used: Optional[str] = None, session_id: str = "default") -> None:
        """Buffer interaction for session-based consolidation. Does NOT save to DB immediately."""
        global _session_buffer

        if session_id not in _session_buffer:
            _session_buffer[session_id] = []

        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": user_input,
            "response": response,
            "plugin_used": plugin_used,
            "session_id": session_id
        }

        _session_buffer[session_id].append(interaction)

        # Check if we should consolidate
        if len(_session_buffer[session_id]) >= self.consolidation_threshold:
            self._consolidate_session(session_id)

    def _consolidate_session(self, session_id: str) -> Optional[str]:
        """Consolidate session interactions into a summary and save to DB."""
        global _session_buffer

        if session_id not in _session_buffer or not _session_buffer[session_id]:
            return None

        interactions = _session_buffer[session_id]

        # Generate a simple summary from the session
        # This is a condensed representation of the conversation
        summary = self._create_session_summary(interactions)

        # Save the summary to the database
        if self.is_connected and self.summaries_collection is not None:
            try:
                summary_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "session_id": session_id,
                    "interaction_count": len(interactions),
                    "summary": summary,
                    "interactions": interactions  # Keep raw data for reference
                }
                self.summaries_collection.insert_one(summary_entry)

                # Also save to the main chat logs as a consolidated entry
                consolidated_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_input": f"[Session {session_id}] {len(interactions)} interactions",
                    "response": summary,
                    "plugin_used": "session_consolidation",
                    "session_id": session_id,
                    "consolidated": True,
                    "interaction_count": len(interactions)
                }
                self.collection.insert_one(consolidated_entry)

            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"[DB] Network error consolidating session: {e}")
            except Exception as e:
                logger.error(f"[DB] Error consolidating session: {e}")

        # Clear the buffer for this session
        del _session_buffer[session_id]
        return summary

    def _create_session_summary(self, interactions: List[dict]) -> str:
        """Create a summary from session interactions using simple extraction."""
        if not interactions:
            return "No interactions"

        # Extract key topics/commands from user inputs
        user_commands = [i["user_input"] for i in interactions[:3]]  # First 3 commands

        # Simple summary format - can be enhanced with LLM
        summary_parts = []

        # Check for command patterns
        for cmd in user_commands:
            if any(x in cmd.lower() for x in ["play", "song", "music", "video"]):
                summary_parts.append("requested media playback")
            elif any(x in cmd.lower() for x in ["search", "find", "look up"]):
                summary_parts.append("performed searches")
            elif any(x in cmd.lower() for x in ["task", "plan", "execute", "run"]):
                summary_parts.append("executed tasks via orchestrator")
            elif any(x in cmd.lower() for x in ["trading", "trade", "stock", "crypto"]):
                summary_parts.append("queried trading/market data")
            elif any(x in cmd.lower() for x in ["memory", "vault", "remember"]):
                summary_parts.append("interacted with memory system")

        if summary_parts:
            # Remove duplicates while preserving order
            seen = set()
            unique_parts = [x for x in summary_parts if not (x in seen or seen.add(x))]
            return f"User {', '.join(unique_parts)}. ({len(interactions)} total exchanges)"
        else:
            return f"General conversation session with {len(interactions)} exchanges"

    def end_session(self, session_id: str) -> Optional[str]:
        """End a session and force consolidation of remaining interactions."""
        return self._consolidate_session(session_id)
    
    def get_recent_logs(self, limit: int = 5, session_id: str = None) -> list:
        """
        Fetch recent interaction logs from MongoDB.
        
        Args:
            limit: Maximum number of logs to return
            session_id: Optional session_id to filter logs by for strict session isolation
            
        Returns:
            List of log entries
        """
        if not self.is_connected:
            return []
            
        try:
            # Build query with session_id filter if provided
            query = {}
            if session_id:
                query["session_id"] = session_id
            
            logs = list(self.collection.find(query, {'_id': 0}).sort("timestamp", -1).limit(limit))
            return logs
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"[DB] Network error fetching logs: {e}")
            return []
        except Exception as e:
            logger.error(f"[DB] Error fetching logs: {e}")
            return []
    
    def close(self) -> None:
        """Close the MongoDB connection."""
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                logger.error(f"[DB] Error closing connection: {e}")
            self.client = None
            self.is_connected = False
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.close()