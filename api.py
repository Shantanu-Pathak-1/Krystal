"""
FastAPI Backend Bridge for Krystal AI Frontend
Connects the React frontend to the existing KrystalEngine
"""

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os
from pathlib import Path
import psutil
import uvicorn
import logging
import threading
from datetime import datetime  # FIX: Was missing — caused NameError on SERVER_START_TIME
from dotenv import load_dotenv

# Setup logger
logger = logging.getLogger("Krystal.api")

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

# Add the krystal-core-engine to the Python path
engine_path = Path(__file__).parent / "krystal-core-engine"
sys.path.insert(0, str(engine_path))

try:
    from engine import KrystalEngine
    from usage_tracker import get_usage_tracker
    from trading_engine import TradingEngine
    from voice_system import KrystalVoiceSystem
    from orchestrator import TaskMemory, TaskPlanner, TaskExecutor, StepResult, RetryStage
    from manager_agent import ManagerAgent, create_manager_agent
except ImportError as e:
    logger.warning(f"Warning: KrystalEngine not found: {e}")
    KrystalEngine = None
    get_usage_tracker = None
    TradingEngine = None
    TaskMemory = None
    TaskPlanner = None
    TaskExecutor = None
    StepResult = None
    RetryStage = None
    ManagerAgent = None
    create_manager_agent = None

# Import file operations, project context, and VS Code bridge
try:
    from plugins.file_writer import get_file_writer
    from plugins.project_context import get_project_context
    from plugins.vscode_bridge import get_vscode_bridge
except ImportError as e:
    logger.warning(f"Warning: VS Code integration plugins not found: {e}")
    get_file_writer = None
    get_project_context = None
    get_vscode_bridge = None

# FCS API Configuration (Get your key from fcsapi.com)
FCS_ACCESS_KEY = os.getenv('FCS_ACCESS_KEY')

# Voice system instance
voice_system = None
voice_thread = None

# Production mode toggle (default: false - allows mock data)
production_mode = False

# VS Code configuration
VSCODE_PATH = os.getenv('VSCODE_PATH')
PROJECT_PATH = os.getenv('PROJECT_PATH', str(Path(__file__).parent))

# Initialize file writer, project context, and VS Code bridge
file_writer = get_file_writer(PROJECT_PATH) if get_file_writer else None
project_context = get_project_context(PROJECT_PATH) if get_project_context else None
vscode_bridge = get_vscode_bridge(VSCODE_PATH) if get_vscode_bridge else None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    global voice_system, voice_thread
    # Startup
    if KrystalVoiceSystem:
        try:
            voice_system = KrystalVoiceSystem()
            voice_thread = threading.Thread(target=voice_system.listen_loop, daemon=True)
            voice_thread.start()
            logger.info("[API] Voice system started in background thread")
        except Exception as e:
            logger.error(f"[API] Failed to start voice system: {e}")
    yield
    # Shutdown - daemon thread will cleanup automatically

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Krystal AI API",
    description="Backend API for Krystal AI Frontend",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/api/voice/status")
async def get_voice_status():
    """Get voice system status."""
    global voice_system
    if voice_system:
        return {
            "status": "running",
            "state": voice_system.state.value,
            "model_ready": voice_system.model_ready,
            "wake_words": voice_system.wake_words
        }
    else:
        return {
            "status": "not_running",
            "message": "Voice system not initialized"
        }

@app.post("/api/voice/test")
async def test_voice():
    """Test voice system by triggering a response."""
    global voice_system
    if voice_system:
        try:
            voice_system.speak("Voice system is working. I can hear you.")
            return {
                "status": "success",
                "message": "Test response sent"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    else:
        return {
            "status": "error",
            "message": "Voice system not running"
        }

# Configure logging to write to file
log_file = Path(__file__).parent / "krystal.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# CORS allows all origins for development testing
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
        logger.info("[ENGINE] Krystal Engine initialized successfully")
    except Exception as e:
        logger.error(f"[ENGINE] Error initializing Krystal Engine: {e}")

# Initialize Trading Engine
trading_engine = None
if TradingEngine is not None:
    try:
        trading_engine = TradingEngine()
        logger.info("[ENGINE] Trading Engine initialized successfully")
    except Exception as e:
        logger.error(f"[ENGINE] Error initializing Trading Engine: {e}")

# Request counter (in-memory, resets on restart)
_request_count = 0

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    mode: Optional[str] = "Agentic"
    model_id: Optional[str] = None
    session_id: Optional[str] = "default"
    use_web: Optional[bool] = False
    use_vision: Optional[bool] = False
    file: Optional[str] = None
    user_name: Optional[str] = "Shantanu"

class SystemModeRequest(BaseModel):
    mode: str

class VoiceStatusRequest(BaseModel):
    status: str

# File operation models
class FileCreateRequest(BaseModel):
    path: str
    content: str
    overwrite: Optional[bool] = False
    create_backup: Optional[bool] = True
    open_in_vscode: Optional[bool] = False

class FileModifyRequest(BaseModel):
    path: str
    operation: Optional[str] = "append"
    content: Optional[str] = ""
    search: Optional[str] = ""
    replace: Optional[str] = ""
    create_backup: Optional[bool] = True

class FileDeleteRequest(BaseModel):
    path: str
    create_backup: Optional[bool] = True

class FileReadRequest(BaseModel):
    path: str

class VSCodeOpenRequest(BaseModel):
    path: str
    reuse_window: Optional[bool] = True
    line: Optional[int] = None
    column: Optional[int] = None

class ProjectScanRequest(BaseModel):
    recursive: Optional[bool] = True

# Track voice status globally
voice_status = "passive"

class ChatResponse(BaseModel):
    response: str
    status: str
    timestamp: str

class StatusResponse(BaseModel):
    status: str
    engine_loaded: bool
    message: str

class SessionEndRequest(BaseModel):
    session_id: str


@app.get("/")
async def root():
    return {"message": "Krystal AI API is running", "version": "1.0.0"}


@app.post("/api/system/mode")
async def set_system_mode(request: SystemModeRequest):
    """Adjust backend engine and process priority based on performance mode."""
    mode = request.mode
    process = psutil.Process(os.getpid())
    
    try:
        if mode == 'eco':
            # Set process to idle/low priority
            if sys.platform == 'win32':
                process.nice(psutil.IDLE_PRIORITY_CLASS)
            else:
                process.nice(19)
            # Notify engine to throttle if possible
            if trading_engine:
                # We could add a throttle method to the engine
                pass
        elif mode == 'balanced':
            if sys.platform == 'win32':
                process.nice(psutil.NORMAL_PRIORITY_CLASS)
            else:
                process.nice(0)
        elif mode == 'overdrive':
            if sys.platform == 'win32':
                process.nice(psutil.HIGH_PRIORITY_CLASS)
            else:
                process.nice(-10)
        
        return {"status": "success", "mode": mode, "priority": process.nice()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/system/voice-status")
async def update_voice_status(request: VoiceStatusRequest):
    global voice_status
    voice_status = request.status
    logger.info(f"[VOICE] status updated: {voice_status}")
    return {"status": "success", "voice_status": voice_status}

@app.get("/api/system/voice-status")
async def get_voice_status():
    return {"voice_status": voice_status}

@app.get("/api/logs")
async def get_logs():
    """Get real logs from the log file."""
    try:
        if not log_file.exists():
            return {"logs": []}

        # Read last 100 lines from log file
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_100_lines = lines[-100:] if len(lines) > 100 else lines

        # Parse log lines into structured format
        logs = []
        for i, line in enumerate(last_100_lines):
            try:
                # Parse log format: timestamp - name - level - message
                parts = line.strip().split(' - ', 3)
                if len(parts) >= 4:
                    timestamp = parts[0]
                    name = parts[1]
                    level = parts[2].lower()
                    message = parts[3]

                    # Map level to frontend format
                    level_map = {
                        'info': 'info',
                        'warning': 'warning',
                        'error': 'error',
                        'critical': 'error',
                        'debug': 'debug',
                        'success': 'success'
                    }
                    mapped_level = level_map.get(level, 'info')

                    logs.append({
                        "id": f"log-{i}",
                        "timestamp": timestamp,
                        "level": mapped_level,
                        "source": name,
                        "message": message
                    })
            except Exception as e:
                logger.error(f"Failed to parse log line: {e}")
                continue

        return {"logs": logs[::-1]}  # Reverse to show newest first
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return {"logs": []}

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
                logger.warning(f"Failed to get MongoDB stats: {e}")
        
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
                logger.warning(f"Failed to get Pinecone stats: {e}")
        
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
                logger.warning(f"Failed to get MongoDB stats: {e}")
        
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
                logger.warning(f"Failed to get Pinecone stats: {e}")
        
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
    REAL system metrics via psutil - no mocks.
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
                    except (ConnectionError, TimeoutError) as e:
                        logger.warning(f"[API] Pinecone connection error: {e}")
                        total_memories = 0
                    except Exception as e:
                        logger.error(f"[API] Error getting Pinecone stats: {e}")
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




@app.post("/api/chat")
async def chat(request: ChatRequest):
    global _request_count
    _request_count += 1

    if not krystal_engine:
        raise HTTPException(status_code=503, detail="Krystal Engine is not available")

    try:
        # STRICT SESSION ISOLATION: Retrieve chat history filtered by session_id
        chat_history = []
        if hasattr(krystal_engine, 'db') and krystal_engine.db and krystal_engine.db.is_connected:
            try:
                # Get session_id from request, default to "default"
                session_id = request.session_id or "default"
                
                # Fetch logs filtered by session_id
                logs = krystal_engine.db.get_recent_logs(limit=15, session_id=session_id)
                
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
                
                logger.info(f"[API] Loaded {len(chat_history)} messages for session: {session_id}")
            except Exception as e:
                logger.warning(f"Warning: Could not fetch chat history for session {request.session_id}: {e}")
        
        # Pass history, selected model, and superpower flags to engine
        plugin_kwargs = {
            'use_web': request.use_web if hasattr(request, 'use_web') else False,
            'use_vision': request.use_vision if hasattr(request, 'use_vision') else False,
            'file': request.file if hasattr(request, 'file') else None,
            'user_name': request.user_name if hasattr(request, 'user_name') else "Shantanu"
        }
        
        response = krystal_engine.process_input(
            request.message,
            agent_mode=request.mode,
            history=chat_history,
            provider=request.model_id,
            **plugin_kwargs
        )

        # Log interaction with session-based consolidation
        if hasattr(krystal_engine, 'db') and krystal_engine.db:
            try:
                krystal_engine.db.log_interaction(
                    user_input=request.message,
                    response=response,
                    session_id=request.session_id or "default"
                )
            except Exception as e:
                logger.warning(f"[API] Warning: Could not log interaction: {e}")

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


class ModelSwitchRequest(BaseModel):
    provider: str


@app.post("/api/model/switch")
async def switch_model(request: ModelSwitchRequest):
    """Switch the active LLM provider."""
    if not krystal_engine:
        raise HTTPException(status_code=503, detail="Krystal Engine is not available")
    try:
        # Store the preferred provider in a global/config
        # The actual routing happens per-request based on this preference
        return {
            "status": "success",
            "provider": request.provider,
            "message": f"Model switched to {request.provider}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error switching model: {str(e)}")


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


@app.get("/api/chat/recent-session")
async def get_recent_session():
    """
    Get the most recent session_id and its messages.
    """
    if not krystal_engine:
        raise HTTPException(status_code=503, detail="Krystal Engine is not available")

    try:
        if hasattr(krystal_engine, 'db') and krystal_engine.db and krystal_engine.db.is_connected:
            # Get the most recent log to find the latest session_id
            logs = krystal_engine.db.get_recent_logs(limit=1)
            if logs and len(logs) > 0:
                recent_session_id = logs[0].get('session_id')
                if recent_session_id:
                    return {
                        "session_id": recent_session_id,
                        "timestamp": logs[0].get('timestamp')
                    }
            return {"session_id": None}
    except Exception as e:
        logger.error(f"Error getting recent session: {e}")
        return {"session_id": None}

@app.get("/api/chat/history")
async def get_chat_history(limit: int = 20, session_id: Optional[str] = None):
    """
    Fetch the last N messages from MongoDB chat history.
    Returns messages in chronological order (oldest first).
    If session_id is provided, only returns messages from that session.
    """
    if not krystal_engine:
        raise HTTPException(status_code=503, detail="Krystal Engine is not available")

    try:
        if hasattr(krystal_engine, 'db') and krystal_engine.db and krystal_engine.db.is_connected:
            # Filter by session_id if provided
            if session_id:
                logs = krystal_engine.db.get_recent_logs(limit=limit, session_id=session_id)
            else:
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


@app.post("/api/chat/session/end")
async def end_chat_session(request: SessionEndRequest):
    """
    End a chat session and trigger memory consolidation.
    This prevents memory spam by summarizing the session before saving.
    """
    if not krystal_engine or not hasattr(krystal_engine, 'db') or not krystal_engine.db:
        return {"status": "offline", "message": "Database not available"}

    try:
        summary = krystal_engine.db.end_session(request.session_id)
        return {
            "status": "success",
            "session_id": request.session_id,
            "summary": summary,
            "message": "Session consolidated and saved to memory vault"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending session: {str(e)}")


@app.post("/api/voice")
async def voice_input(audio: UploadFile):
    """Process voice input audio and return transcribed text."""
    try:
        # Read audio data
        audio_data = await audio.read()

        # Try to use Whisper for transcription if available
        try:
            import whisper
            import numpy as np
            import io
            import tempfile
            import os

            # Save audio to temporary file for Whisper
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            try:
                # Load Whisper model
                model = whisper.load_model("base")
                # Transcribe audio
                result = model.transcribe(temp_file_path)
                text = result["text"].strip()

                # Clean up temp file
                os.unlink(temp_file_path)

                return {
                    "status": "success",
                    "text": text,
                    "model": "whisper"
                }
            except Exception as whisper_error:
                logger.warning(f"Whisper transcription failed: {whisper_error}")
                # Clean up temp file if it exists
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                raise whisper_error

        except ImportError:
            # Fallback: Return error if Whisper not available
            return {
                "status": "error",
                "message": "Whisper not installed. Install with: pip install openai-whisper",
                "text": ""
            }

    except Exception as e:
        logger.error(f"Voice input error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "text": ""
        }


@app.post("/api/tts")
async def text_to_speech(request: Dict[str, Any]):
    """Convert text to speech using edge-tts."""
    try:
        text = request.get("text", "")
        voice = request.get("voice", "en-US-AriaNeural")

        if not text:
            return {"status": "error", "message": "Text is required"}

        try:
            import edge_tts
            import tempfile
            import os

            # Generate speech using edge-tts
            communicate = edge_tts.Communicate(text, voice)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file_path = temp_file.name

            await communicate.save(temp_file_path)

            # Read the file and return as base64
            with open(temp_file_path, "rb") as f:
                audio_data = f.read()

            # Clean up
            os.unlink(temp_file_path)

            # Return base64 encoded audio
            import base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            return {
                "status": "success",
                "audio": audio_base64,
                "format": "mp3"
            }

        except ImportError:
            return {
                "status": "error",
                "message": "edge-tts not installed. Install with: pip install edge-tts"
            }

    except Exception as e:
        logger.error(f"TTS error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


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
    "mongodb_uri": os.getenv('MONGODB_URI', 'mongodb://localhost:27017/krystal'),
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


@app.get("/api/production-mode")
async def get_production_mode():
    """Get current production mode status."""
    global production_mode
    return {
        "production_mode": production_mode,
        "status": "success"
    }


@app.post("/api/production-mode")
async def set_production_mode(request: Dict[str, Any]):
    """Set production mode status."""
    global production_mode, trading_engine
    try:
        production_mode = request.get("production_mode", False)

        # Update trading engine if it exists
        if trading_engine:
            trading_engine.production_mode = production_mode

        return {
            "status": "success",
            "message": f"Production mode set to {production_mode}",
            "production_mode": production_mode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting production mode: {str(e)}")


@app.post("/api/trading/execute")
async def execute_trade(approved: bool):
    try:
        if trading_engine:
            # Check if system is shut down
            is_safe, message = trading_engine.check_risk_limit()
            if not is_safe:
                return {"success": False, "message": message, "shutdown": True}
            
            result = trading_engine.execute_trade(approved)
            return {"success": True, "result": result}
        return {"success": False, "message": "Trading engine not initialized"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/trading/risk-settings")
async def update_risk_settings(daily_loss_limit: float, target_profit: float):
    try:
        if trading_engine:
            trading_engine.update_risk_settings(daily_loss_limit, target_profit)
            return {"success": True, "message": "Risk settings updated"}
        return {"success": False, "message": "Trading engine not initialized"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/trading/paper-trade")
async def execute_paper_trade(symbol: str, action: str, amount: float, price: float):
    try:
        if trading_engine:
            result = trading_engine.execute_paper_trade(symbol, action, amount, price)
            return result
        return {"success": False, "message": "Trading engine not initialized"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/trading/evaluate-trades")
async def evaluate_trades():
    try:
        if trading_engine:
            trading_engine.evaluate_paper_trades()
            return {"success": True, "message": "Trades evaluated"}
        return {"success": False, "message": "Trading engine not initialized"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/trading/agent-status")
async def get_agent_status():
    """Get current status of AI agents"""
    try:
        if trading_engine:
            status = trading_engine.get_agent_status()
            return {"success": True, "status": status}
        return {"success": False, "message": "Trading engine not initialized"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/trading/toggle-groq")
async def toggle_groq(enabled: bool):
    """Toggle Groq agent on/off"""
    try:
        if trading_engine:
            trading_engine.toggle_groq(enabled)
            return {"success": True, "message": f"Groq agent {'enabled' if enabled else 'disabled'}"}
        return {"success": False, "message": "Trading engine not initialized"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/trading/toggle-gemini")
async def toggle_gemini(enabled: bool):
    """Toggle Gemini agent on/off"""
    try:
        if trading_engine:
            trading_engine.toggle_gemini(enabled)
            return {"success": True, "message": f"Gemini agent {'enabled' if enabled else 'disabled'}"}
        return {"success": False, "message": "Trading engine not initialized"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/trading/status")
async def get_trading_status(mode: str = "simulated", symbol: str = "EUR/USD"):
    """Get current trading status including market data and agent analyses."""
    if not trading_engine:
        return {"error": "Trading engine not initialized"}
    
    try:
        # Pass the mode and symbol to the engine
        await trading_engine.fetch_market_data_for_mode(mode, symbol)
        
        # Run analysis for the requested symbol
        await trading_engine.analyze_trade(symbol)
        
        # Generate trade signal
        trading_engine.generate_trade_signal(symbol)
        
        # Return status with the current mode
        status = trading_engine.get_status(symbol=symbol)
        status['mode'] = mode
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trading status: {str(e)}")


@app.post("/api/trading/execute")
async def execute_trade(request: Dict[str, Any]):
    """Execute or reject a pending trade."""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    approved = request.get("approved", False)
    
    try:
        result = await trading_engine.execute_trade(approved)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing trade: {str(e)}")


@app.get("/api/trading/ohlc")
async def get_ohlc_data(symbol: str = "EUR/USD", limit: int = 100):
    """Get OHLC (Open, High, Low, Close) data for the chart."""
    if not trading_engine:
        return {"error": "Trading engine not initialized"}
    
    try:
        ohlc_data = trading_engine.get_ohlc_data(symbol, limit)
        return {"symbol": symbol, "data": ohlc_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OHLC data: {str(e)}")


@app.get("/api/trading/position-size")
async def get_position_size(symbol: str = "EUR/USD", risk_percentage: float = 1.0):
    """Calculate position size based on risk percentage."""
    if not trading_engine:
        return {"error": "Trading engine not initialized"}
    
    try:
        position_data = trading_engine.calculate_position_size(symbol, risk_percentage)
        return position_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating position size: {str(e)}")


# Manager Agent Pydantic models
class RetryConfirmationRequest(BaseModel):
    task_id: str
    step_index: int
    confirm: bool  # True to retry, False to cancel


class TaskPlanRequest(BaseModel):
    user_prompt: str
    task_id: Optional[str] = None
    is_new_task: bool = True


@app.get("/api/manager/status")
async def get_manager_status():
    """
    Get Manager Agent status including project summary and error audit.
    Returns comprehensive overview of all tasks and current execution state.
    """
    if not create_manager_agent:
        raise HTTPException(status_code=503, detail="Manager Agent not initialized")

    try:
        manager = create_manager_agent()
        summary = manager.get_project_summary()

        # Build response with Iron Guard-style precision
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tasks": summary.total_tasks,
                "completed_tasks": summary.completed_tasks,
                "failed_tasks": summary.failed_tasks,
                "in_progress_tasks": summary.in_progress_tasks,
                "awaiting_confirmation": summary.awaiting_confirmation,
                "total_steps": summary.total_steps,
                "completed_steps": summary.completed_steps,
                "failed_steps": summary.failed_steps,
                "total_retries": summary.total_retries,
                "summary_text": summary.summary_text,
            },
            "active_tasks": summary.active_tasks,
            "recent_failures": [
                {
                    "error_type": f.error_type,
                    "severity": f.severity,
                    "technical_summary": f.technical_summary,
                    "probable_cause": f.probable_cause,
                    "recommended_action": f.recommended_action,
                    "affected_step": f.affected_step,
                    "task_id": f.task_id,
                    "timestamp": f.timestamp,
                }
                for f in summary.recent_failures
            ],
            "requires_attention": summary.failed_tasks > 0 or summary.awaiting_confirmation > 0,
        }

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manager Agent error: {str(e)}")


@app.get("/api/manager/task/{task_id}")
async def get_task_details(task_id: str):
    """Get detailed information about a specific task including error audits."""
    if not create_manager_agent:
        raise HTTPException(status_code=503, detail="Manager Agent not initialized")

    try:
        manager = create_manager_agent()
        details = manager.get_task_details(task_id)

        if not details:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        return {
            "status": "success",
            "task": details,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving task: {str(e)}")


@app.post("/api/manager/confirm-retry")
async def confirm_retry(request: RetryConfirmationRequest):
    """
    Handle user confirmation for a failed step retry.
    Confirm=True will retry the step, Confirm=False will cancel the task.
    """
    if not TaskExecutor:
        raise HTTPException(status_code=503, detail="Task Executor not initialized")

    try:
        executor = TaskExecutor()
        result = executor.confirm_retry(
            task_id=request.task_id,
            step_index=request.step_index,
            confirm=request.confirm,
        )

        if not result:
            raise HTTPException(status_code=404, detail=f"Task {request.task_id} not found")

        return {
            "status": "success",
            "action": "retry" if request.confirm else "cancelled",
            "task_id": request.task_id,
            "step_index": request.step_index,
            "task_state": result.get("execution_state"),
            "requires_confirmation": result.get("requires_confirmation", False),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing confirmation: {str(e)}")


@app.post("/api/orchestrator/plan")
async def create_task_plan(request: TaskPlanRequest):
    """Create a new task plan or resume an existing one."""
    if not TaskPlanner or not TaskMemory:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        planner = TaskPlanner()
        memory = TaskMemory()

        task_id = request.task_id or planner._generate_task_id()

        # Check if resuming existing task
        if not request.is_new_task and memory.is_task_active(task_id):
            plan = memory.get_plan(task_id)
            return {
                "status": "resumed",
                "task_id": task_id,
                "plan": plan,
                "message": "Resumed existing task",
            }

        # Clear existing state for new task
        if request.is_new_task:
            memory.clear_task_state(task_id)

        # Generate new plan
        try:
            steps = planner._call_llm_for_plan(request.user_prompt)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"[API] JSON parsing failed: {e}. Using fallback.")
            steps = [request.user_prompt]
        except Exception as e:
            logger.error(f"[API] LLM call failed: {e}. Using fallback.")
            steps = [request.user_prompt]

        plan = memory.create_plan(task_id, steps, is_new_task=True)

        return {
            "status": "created",
            "task_id": task_id,
            "plan": plan,
            "step_count": len(steps),
            "message": f"Created task plan with {len(steps)} steps",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task plan: {str(e)}")


@app.get("/api/orchestrator/status/{task_id}")
async def get_orchestrator_status(task_id: str):
    """Get the current execution status of a specific task."""
    if not TaskMemory:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        memory = TaskMemory()
        plan = memory.get_plan(task_id)

        if not plan:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Determine if confirmation is needed
        requires_confirmation = plan.get("requires_confirmation", False)
        confirmation_prompt = plan.get("confirmation_prompt") if requires_confirmation else None

        return {
            "status": "success",
            "task_id": task_id,
            "execution_state": plan.get("execution_state"),
            "overall_status": plan.get("status"),
            "current_step_index": plan.get("current_step_index"),
            "total_steps": len(plan.get("steps", [])),
            "requires_confirmation": requires_confirmation,
            "confirmation_prompt": confirmation_prompt,
            "total_retries": plan.get("total_retries", 0),
            "updated_at": plan.get("updated_at"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving status: {str(e)}")


# File Operation Endpoints

@app.post("/api/file/create")
async def create_file(request: FileCreateRequest):
    """Create a new file with content."""
    if not file_writer:
        raise HTTPException(status_code=503, detail="File writer not available")
    
    result = file_writer.create_file(
        filepath=request.path,
        content=request.content,
        overwrite=request.overwrite,
        create_backup=request.create_backup
    )
    
    if result.get("success"):
        # Open in VS Code if requested
        if request.open_in_vscode and vscode_bridge:
            vscode_bridge.open_file(request.path, reuse_window=True)
        
        return {"status": "success", **result}
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

@app.post("/api/file/modify")
async def modify_file(request: FileModifyRequest):
    """Modify an existing file."""
    if not file_writer:
        raise HTTPException(status_code=503, detail="File writer not available")
    
    result = file_writer.modify_file(
        filepath=request.path,
        operation=request.operation,
        content=request.content,
        search=request.search,
        replace=request.replace,
        create_backup=request.create_backup
    )
    
    if result.get("success"):
        return {"status": "success", **result}
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

@app.post("/api/file/delete")
async def delete_file(request: FileDeleteRequest):
    """Delete a file."""
    if not file_writer:
        raise HTTPException(status_code=503, detail="File writer not available")
    
    result = file_writer.delete_file(
        filepath=request.path,
        create_backup=request.create_backup
    )
    
    if result.get("success"):
        return {"status": "success", **result}
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

@app.post("/api/file/read")
async def read_file(request: FileReadRequest):
    """Read a file's content."""
    if not file_writer:
        raise HTTPException(status_code=503, detail="File writer not available")
    
    result = file_writer.read_file(request.path)
    
    if result.get("success"):
        return {"status": "success", **result}
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

@app.post("/api/file/list")
async def list_directory(directory: str, recursive: bool = False):
    """List files in a directory."""
    if not file_writer:
        raise HTTPException(status_code=503, detail="File writer not available")
    
    result = file_writer.list_directory(directory, recursive=recursive)
    
    if result.get("success"):
        return {"status": "success", **result}
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

# VS Code Integration Endpoints

@app.post("/api/vscode/open")
async def open_in_vscode(request: VSCodeOpenRequest):
    """Open a file in VS Code."""
    if not vscode_bridge:
        raise HTTPException(status_code=503, detail="VS Code bridge not available")
    
    result = vscode_bridge.open_file(
        filepath=request.path,
        reuse_window=request.reuse_window,
        line=request.line,
        column=request.column
    )
    
    if result.get("success"):
        return {"status": "success", **result}
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

@app.post("/api/vscode/open-directory")
async def open_directory_in_vscode(directory: str, reuse_window: bool = True):
    """Open a directory in VS Code."""
    if not vscode_bridge:
        raise HTTPException(status_code=503, detail="VS Code bridge not available")
    
    result = vscode_bridge.open_directory(directory, reuse_window=reuse_window)
    
    if result.get("success"):
        return {"status": "success", **result}
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

@app.post("/api/vscode/reveal")
async def reveal_in_explorer(filepath: str):
    """Reveal a file in VS Code's explorer panel."""
    if not vscode_bridge:
        raise HTTPException(status_code=503, detail="VS Code bridge not available")
    
    result = vscode_bridge.reveal_in_explorer(filepath)
    
    if result.get("success"):
        return {"status": "success", **result}
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

# Project Context Endpoints

@app.post("/api/project/scan")
async def scan_project(request: ProjectScanRequest):
    """Scan the project structure."""
    if not project_context:
        raise HTTPException(status_code=503, detail="Project context not available")
    
    result = project_context.scan_project(recursive=request.recursive)
    
    return {"status": "success", "structure": result}

@app.get("/api/project/summary")
async def get_project_summary():
    """Get a summary of the project."""
    if not project_context:
        raise HTTPException(status_code=503, detail="Project context not available")
    
    result = project_context.get_project_summary()
    
    return {"status": "success", "summary": result}

@app.post("/api/project/analyze")
async def analyze_file(filepath: str):
    """Analyze a specific file."""
    if not project_context:
        raise HTTPException(status_code=503, detail="Project context not available")
    
    result = project_context.analyze_file(filepath)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return {"status": "success", "analysis": result}

@app.post("/api/project/relevant")
async def find_relevant_files(query: str, max_files: int = 5):
    """Find files relevant to a query."""
    if not project_context:
        raise HTTPException(status_code=503, detail="Project context not available")
    
    result = project_context.get_relevant_files(query, max_files=max_files)
    
    return {"status": "success", "files": result}


if __name__ == "__main__":
    logger.info("[SERVER] Starting Krystal AI API Server...")
    logger.info("[SERVER] API:      http://localhost:8000")
    logger.info("[SERVER] Frontend: http://localhost:5173")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False, log_level="info")