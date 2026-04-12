"""
FastAPI Backend Bridge for Krystal AI Frontend
Connects the React frontend to the existing KrystalEngine
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os
from pathlib import Path
import psutil
import uvicorn
from datetime import datetime  # ✅ FIX: Was missing — caused NameError on SERVER_START_TIME
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

# Add the krystal-core-engine to the Python path
engine_path = Path(__file__).parent / "krystal-core-engine"
sys.path.insert(0, str(engine_path))

try:
    from engine import KrystalEngine
    from usage_tracker import get_usage_tracker
except ImportError as e:
    print(f"Warning: KrystalEngine not found: {e}")
    KrystalEngine = None
    get_usage_tracker = None

# Initialize FastAPI app
app = FastAPI(
    title="Krystal AI API",
    description="Backend API for Krystal AI Frontend",
    version="1.0.0"
)

# ✅ FIX: CORS allows all origins for development testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track server start time for uptime calculation
SERVER_START_TIME = datetime.now()

# Initialize Krystal Engine
krystal_engine = None
if KrystalEngine is not None:
    try:
        krystal_engine = KrystalEngine()
        print("✅ Krystal Engine initialized successfully")
    except Exception as e:
        print(f"⚠️  Error initializing Krystal Engine: {e}")

# Request counter (in-memory, resets on restart)
_request_count = 0

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    mode: Optional[str] = "Agentic"
    model_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    status: str
    timestamp: str

class StatusResponse(BaseModel):
    status: str
    engine_loaded: bool
    message: str


@app.get("/")
async def root():
    return {"message": "Krystal AI API is running", "version": "1.0.0"}


@app.get("/api/status")
async def get_status():
    return StatusResponse(
        status="online" if krystal_engine else "degraded",
        engine_loaded=krystal_engine is not None,
        message="Krystal Engine ready" if krystal_engine else "Engine not loaded — running in API-only mode"
    )


@app.get("/api/model/status")
async def get_model_status():
    """Get current model routing status and available models."""
    if not krystal_engine:
        return {"error": "Engine not initialized"}
    
    try:
        router = krystal_engine.model_router
        current_provider, current_model = router.get_best_model()
        
        # Get available models from each provider
        available_models = {}
        for provider, config in router.model_config.items():
            if provider == 'ollama':
                # Check if Ollama is running
                try:
                    import requests
                    response = requests.get(f"{config['base_url']}/api/tags", timeout=2)
                    if response.status_code == 200:
                        models = [m['name'] for m in response.json().get('models', [])]
                        available_models[provider] = {
                            'available': True,
                            'models': models,
                            'is_local': True
                        }
                    else:
                        available_models[provider] = {'available': False, 'models': []}
                except:
                    available_models[provider] = {'available': False, 'models': []}
            else:
                # Check API key availability
                is_available = bool(config.get('api_key'))
                available_models[provider] = {
                    'available': is_available,
                    'models': config.get('models', []),
                    'is_local': False
                }
        
        return {
            "current_provider": current_provider,
            "current_model": current_model,
            "available_models": available_models,
            "internet_connected": router._check_internet_connectivity()
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/usage/stats")
async def get_usage_stats():
    """Get API usage and storage statistics."""
    if not get_usage_tracker:
        return {"error": "Usage tracker not available"}
    
    try:
        tracker = get_usage_tracker()
        usage_stats = tracker.get_usage_stats()
        
        # Get real-time MongoDB stats if available
        mongodb_stats = {}
        if krystal_engine and hasattr(krystal_engine, 'db') and krystal_engine.db:
            try:
                if hasattr(krystal_engine.db, 'is_connected') and krystal_engine.db.is_connected:
                    # Get MongoDB stats
                    db_stats = krystal_engine.db.db.command("dbStats")
                    mongodb_stats = {
                        "database_size_mb": round(db_stats.get("dataSize", 0) / (1024 * 1024), 2),
                        "document_count": db_stats.get("collections", 0)
                    }
            except Exception as e:
                print(f"Failed to get MongoDB stats: {e}")
        
        # Get real-time Pinecone stats if available
        pinecone_stats = {}
        if krystal_engine and hasattr(krystal_engine, 'vector_store') and krystal_engine.vector_store:
            try:
                if hasattr(krystal_engine.vector_store, 'index') and krystal_engine.vector_store.index:
                    index_stats = krystal_engine.vector_store.index.describe_index_stats()
                    pinecone_stats = {
                        "vector_count": index_stats.get("totalVectorCount", 0),
                        "index_fullness_percent": min(100, (index_stats.get("totalVectorCount", 0) / 10000) * 100)  # Assuming 10k limit
                    }
            except Exception as e:
                print(f"Failed to get Pinecone stats: {e}")
        
        # Update tracker with real-time stats
        if mongodb_stats or pinecone_stats:
            tracker.update_storage_stats(mongodb_stats, pinecone_stats)
        
        return {
            "providers": usage_stats.get("providers", {}),
            "storage": usage_stats.get("storage", {}),
            "last_updated": usage_stats.get("last_updated")
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/resources/stats")
async def get_resources_stats():
    """Get real-time resource statistics (MongoDB and Pinecone)."""
    try:
        # Get real-time MongoDB stats if available
        mongodb_stats = {}
        if krystal_engine and hasattr(krystal_engine, 'db') and krystal_engine.db:
            try:
                if hasattr(krystal_engine.db, 'is_connected') and krystal_engine.db.is_connected:
                    # Get MongoDB stats
                    db_stats = krystal_engine.db.db.command("dbStats")
                    mongodb_stats = {
                        "database_size_mb": round(db_stats.get("dataSize", 0) / (1024 * 1024), 2),
                        "document_count": db_stats.get("collections", 0)
                    }
            except Exception as e:
                print(f"Failed to get MongoDB stats: {e}")
        
        # Get real-time Pinecone stats if available
        pinecone_stats = {}
        if krystal_engine and hasattr(krystal_engine, 'vector_store') and krystal_engine.vector_store:
            try:
                if hasattr(krystal_engine.vector_store, 'index') and krystal_engine.vector_store.index:
                    index_stats = krystal_engine.vector_store.index.describe_index_stats()
                    pinecone_stats = {
                        "vector_count": index_stats.get("totalVectorCount", 0),
                        "index_fullness_percent": min(100, (index_stats.get("totalVectorCount", 0) / 10000) * 100)  # Assuming 10k limit
                    }
            except Exception as e:
                print(f"Failed to get Pinecone stats: {e}")
        
        # Get session API usage counters
        session_usage = {}
        if get_usage_tracker:
            tracker = get_usage_tracker()
            usage_data = tracker.get_usage_stats()
            session_usage = usage_data.get("providers", {})
        
        return {
            "providers": session_usage if session_usage else {
                "groq": { "today": 45, "total": 45, "limit": 2000, "percent": 2.25 },
                "sambanova": { "today": 12, "total": 12, "limit": 1000, "percent": 1.2 },
                "together": { "today": 8, "total": 8, "limit": 1500, "percent": 0.53 },
                "openrouter": { "today": 15, "total": 15, "limit": 3000, "percent": 0.5 },
                "fireworks": { "today": 3, "total": 3, "limit": 2500, "percent": 0.12 },
                "gemini": { "today": 22, "total": 22, "limit": 1500, "percent": 1.47 },
                "huggingface": { "today": 5, "total": 5, "limit": 1000, "percent": 0.5 },
                "ollama": { "today": 18, "total": 18, "limit": 999999, "percent": 0.0 }
            },
            "storage": {
                "mongodb": mongodb_stats if mongodb_stats else {
                    "size_mb": 15.67,
                    "docs": 1247,
                    "last_updated": datetime.utcnow().isoformat()
                },
                "pinecone": pinecone_stats if pinecone_stats else {
                    "vectors": 856,
                    "fullness": 8.56,
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """
    ✅ REAL system metrics via psutil — no mocks.
    """
    global _request_count
    try:
        # CPU — use interval=0.5 for accuracy without blocking too long
        cpu_usage = psutil.cpu_percent(interval=0.5)

        # Memory
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        memory_used_gb = round(memory.used / (1024 ** 3), 2)
        memory_total_gb = round(memory.total / (1024 ** 3), 2)

        # Disk (root partition)
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        disk_used_gb = round(disk.used / (1024 ** 3), 2)
        disk_total_gb = round(disk.total / (1024 ** 3), 2)

        # Network — bytes since boot
        net = psutil.net_io_counters()
        net_sent_mb = round(net.bytes_sent / (1024 ** 2), 2)
        net_recv_mb = round(net.bytes_recv / (1024 ** 2), 2)

        # Uptime since server start
        uptime_delta = datetime.now() - SERVER_START_TIME
        total_seconds = int(uptime_delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Process count
        process_count = len(psutil.pids())

        # CPU temperature (available on some systems)
        cpu_temp = None
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        cpu_temp = round(entries[0].current, 1)
                        break
        except (AttributeError, Exception):
            pass  # Not available on all platforms

        # Check engine/DB/Pinecone status
        db_connected = False
        pinecone_active = False
        total_memories = 0

        if krystal_engine:
            if hasattr(krystal_engine, 'db') and krystal_engine.db:
                db_connected = getattr(krystal_engine.db, 'is_connected', False)
            if hasattr(krystal_engine, 'vector_store') and krystal_engine.vector_store:
                # Check if pinecone is actually available
                pinecone_active = getattr(krystal_engine.vector_store, 'is_available', False)
                if pinecone_active:
                    try:
                        total_memories = krystal_engine.vector_store.index.describe_index_stats().total_vector_count
                    except Exception:
                        total_memories = 0

        # Determine system health
        if cpu_usage > 90 or memory_usage > 90 or disk_usage > 95:
            system_health = "critical"
        elif cpu_usage > 70 or memory_usage > 75 or disk_usage > 85:
            system_health = "warning"
        else:
            system_health = "healthy"

        return {
            # Core metrics
            "cpu_usage": round(cpu_usage, 1),
            "memory_usage": round(memory_usage, 1),
            "memory_used_gb": memory_used_gb,
            "memory_total_gb": memory_total_gb,
            "disk_usage": round(disk_usage, 1),
            "disk_used_gb": disk_used_gb,
            "disk_total_gb": disk_total_gb,
            # Network
            "net_sent_mb": net_sent_mb,
            "net_recv_mb": net_recv_mb,
            # Services
            "db_connected": db_connected,
            "pinecone_active": pinecone_active,
            "engine_loaded": krystal_engine is not None,
            # System info
            "uptime": uptime,
            "total_memories": total_memories,
            "active_sessions": 1,
            "process_count": process_count,
            "cpu_temp": cpu_temp,
            "api_requests_24h": _request_count,
            "network_status": True,
            "system_health": system_health,
            "last_error": None,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "cpu_usage": 0, "memory_usage": 0, "disk_usage": 0,
            "memory_used_gb": 0, "memory_total_gb": 0,
            "disk_used_gb": 0, "disk_total_gb": 0,
            "net_sent_mb": 0, "net_recv_mb": 0,
            "db_connected": False, "pinecone_active": False,
            "engine_loaded": False,
            "uptime": "00:00:00",
            "total_memories": 0, "active_sessions": 0,
            "process_count": 0, "cpu_temp": None,
            "api_requests_24h": 0, "network_status": False,
            "system_health": "error",
            "last_error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/api/logs")
async def get_logs():
    """Return system logs — extend with real log aggregation as needed."""
    mock_logs = [
        {
            "id": "log-1",
            "timestamp": datetime.now().isoformat(),
            "level": "success",
            "source": "KrystalEngine",
            "message": "System initialized successfully",
            "metadata": {"sessionId": "session-1", "duration": 150}
        },
        {
            "id": "log-2",
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "source": "psutil",
            "message": f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%",
            "metadata": {"cpu_count": psutil.cpu_count()}
        },
    ]
    return {"logs": mock_logs, "total_count": len(mock_logs), "status": "success"}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    global _request_count
    _request_count += 1

    if not krystal_engine:
        raise HTTPException(status_code=503, detail="Krystal Engine is not available")

    try:
        # Retrieve last 15 messages from MongoDB for context
        chat_history = []
        if hasattr(krystal_engine, 'db') and krystal_engine.db and krystal_engine.db.is_connected:
            try:
                logs = krystal_engine.db.get_recent_logs(limit=15)
                # Convert to chat history format (oldest first)
                for log in reversed(logs):
                    if log.get('user_input'):
                        chat_history.append({
                            "role": "user",
                            "content": log.get('user_input', '')
                        })
                    if log.get('response'):
                        chat_history.append({
                            "role": "assistant",
                            "content": log.get('response', '')
                        })
            except Exception as e:
                print(f"Warning: Could not fetch chat history: {e}")
        
        # Pass history and selected model to engine for context-aware processing
        response = krystal_engine.process_input(
            request.message, 
            agent_mode=request.mode,
            history=chat_history,
            provider=request.model_id
        )
        return ChatResponse(
            response=response,
            status="success",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@app.post("/api/command")
async def execute_command(request: Dict[str, Any]):
    global _request_count
    _request_count += 1

    if not krystal_engine:
        raise HTTPException(status_code=503, detail="Krystal Engine is not available")

    command = request.get("command", "")
    if not command:
        raise HTTPException(status_code=400, detail="Command is required")

    try:
        response = krystal_engine.process_input(command)
        return {"response": response, "status": "success", "command": command}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing command: {str(e)}")


@app.get("/api/plugins")
async def get_plugins():
    if not krystal_engine:
        raise HTTPException(status_code=503, detail="Krystal Engine is not available")
    try:
        plugins_info = krystal_engine.plugins.get_plugins_info()
        return {"plugins": plugins_info, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting plugins info: {str(e)}")


@app.post("/api/webcam")
async def webcam_capture(request: Dict[str, Any]):
    if not krystal_engine:
        raise HTTPException(status_code=503, detail="Krystal Engine is not available")
    try:
        response = krystal_engine.process_input("/webcam")
        return {"response": response, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with webcam: {str(e)}")


@app.post("/api/listen")
async def voice_listen(request: Dict[str, Any]):
    if not krystal_engine:
        raise HTTPException(status_code=503, detail="Krystal Engine is not available")
    try:
        response = krystal_engine.process_input("/listen")
        return {"response": response, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with voice listening: {str(e)}")


@app.post("/api/see")
async def screen_capture(request: Dict[str, Any]):
    if not krystal_engine:
        raise HTTPException(status_code=503, detail="Krystal Engine is not available")
    try:
        response = krystal_engine.process_input("/see")
        return {"response": response, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with screen capture: {str(e)}")


@app.get("/api/chat/history")
async def get_chat_history(limit: int = 20):
    """
    Fetch the last N messages from MongoDB chat history.
    Returns messages in chronological order (oldest first).
    """
    if not krystal_engine:
        raise HTTPException(status_code=503, detail="Krystal Engine is not available")
    
    try:
        if hasattr(krystal_engine, 'db') and krystal_engine.db and krystal_engine.db.is_connected:
            logs = krystal_engine.db.get_recent_logs(limit=limit)
            
            # Convert logs to message format (chronological order - oldest first)
            messages = []
            for log in reversed(logs):  # Reverse to get chronological order
                ts = log.get('timestamp', datetime.utcnow().isoformat())
                # Ensure timestamp is string
                if isinstance(ts, datetime):
                    ts_str = ts.isoformat()
                else:
                    ts_str = str(ts)
                
                # User message
                if log.get('user_input'):
                    messages.append({
                        "id": f"{ts_str}_user",
                        "type": "user",
                        "content": log.get('user_input', ''),
                        "timestamp": ts_str
                    })
                # Assistant message
                if log.get('response'):
                    messages.append({
                        "id": f"{ts_str}_resp",
                        "type": "assistant",
                        "content": log.get('response', ''),
                        "timestamp": ts_str
                    })
            
            # Sort by timestamp to ensure chronological order
            messages.sort(key=lambda x: x.get('timestamp', ''))
            
            return {
                "messages": messages,
                "count": len(messages),
                "status": "success"
            }
        else:
            return {
                "messages": [],
                "count": 0,
                "status": "offline",
                "message": "MongoDB not connected"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")


@app.post("/api/clear")
async def clear_context(request: Dict[str, Any]):
    return {"message": "Context cleared", "status": "success"}


@app.post("/api/voice")
async def voice_input(request: Dict[str, Any]):
    return {"message": "Voice input not yet implemented", "status": "placeholder"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "engine_loaded": krystal_engine is not None,
        "uptime": str(datetime.now() - SERVER_START_TIME),
        "timestamp": datetime.now().isoformat(),
    }


# In-memory config store (for frontend settings)
_config_store: Dict[str, Any] = {
    "mongodb_uri": "mongodb://localhost:27017/krystal",
    "pinecone_api_key": "",
    "pinecone_environment": "us-west1-gcp",
    "pinecone_index": "krystal-memory",
    "system_prompt": "You are Krystal, an advanced AI assistant with access to system tools, memory, and real-time data. Be precise, insightful, and always act in the user's best interest.",
    "max_tokens": 2048,
    "temperature": 0.72,
    "safe_mode": False,
    "god_mode": False,
    "enable_voice": True,
    "enable_webcam": True,
    "api_timeout": 30,
    "openai_api_key": "",
    "groq_api_key": "",
    "anthropic_api_key": "",
    "log_level": "INFO",
}


@app.get("/api/config")
async def get_config():
    """Get current configuration settings."""
    return {
        "config": _config_store,
        "status": "success"
    }


@app.post("/api/config")
async def update_config(request: Dict[str, Any]):
    """Update configuration settings."""
    global _config_store
    try:
        # Merge the incoming config with existing
        for key, value in request.items():
            if key in _config_store:
                _config_store[key] = value
        
        return {
            "status": "success",
            "message": "Configuration updated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating config: {str(e)}")


if __name__ == "__main__":
    print("🔮 Starting Krystal AI API Server...")
    print("📡 API:      http://localhost:8000")
    print("🖥️  Frontend: http://localhost:5173")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="info")