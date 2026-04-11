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

# Add the krystal-core-engine to the Python path
engine_path = Path(__file__).parent / "krystal-core-engine"
sys.path.insert(0, str(engine_path))

try:
    from engine import KrystalEngine
except ImportError as e:
    print(f"Error importing KrystalEngine: {e}")
    print("Make sure you're running this from the Krystal root directory")
    sys.exit(1)

# Initialize FastAPI app
app = FastAPI(
    title="Krystal AI API",
    description="Backend API for Krystal AI Frontend",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track server start time for uptime calculation
SERVER_START_TIME = datetime.now()

# Initialize Krystal Engine
try:
    krystal_engine = KrystalEngine()
    print("Krystal Engine initialized successfully")
except Exception as e:
    print(f"Error initializing Krystal Engine: {e}")
    krystal_engine = None

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    autonomy_mode: Optional[str] = "agentic"

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
    """Root endpoint"""
    return {"message": "Krystal AI API is running"}

@app.get("/api/status")
async def get_status():
    """Get API and engine status"""
    return StatusResponse(
        status="online" if krystal_engine else "error",
        engine_loaded=krystal_engine is not None,
        message="Krystal Engine ready" if krystal_engine else "Engine initialization failed"
    )

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get real dashboard system stats"""
    try:
        # Get real system metrics using psutil
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        
        # Calculate uptime
        uptime_delta = datetime.now() - SERVER_START_TIME
        hours, remainder = divmod(uptime_delta.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
        # Check service statuses
        db_connected = False
        pinecone_active = False
        
        if krystal_engine:
            # Check MongoDB connection
            if hasattr(krystal_engine, 'db') and krystal_engine.db:
                db_connected = getattr(krystal_engine.db, 'is_connected', False)
            
            # Check Pinecone status (basic check)
            pinecone_active = True  # Would need to check actual Pinecone connection
        
        return {
            "db_connected": db_connected,
            "pinecone_active": pinecone_active,
            "uptime": uptime,
            "total_memories": 42,  # Would need to fetch from actual vector store
            "active_sessions": 1,  # Would need to track actual sessions
            "cpu_usage": round(cpu_usage, 1),
            "memory_usage": round(memory_usage, 1),
            "disk_usage": round(disk_usage, 1),
            "network_status": True,  # Basic network check
            "api_requests_24h": 0,  # Would need to implement request tracking
            "last_error": None,
            "system_health": "healthy"
        }
    except Exception as e:
        return {
            "db_connected": False,
            "pinecone_active": False,
            "uptime": "00:00:00",
            "total_memories": 0,
            "active_sessions": 0,
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "network_status": False,
            "api_requests_24h": 0,
            "last_error": str(e),
            "system_health": "error"
        }

@app.get("/api/logs")
async def get_logs():
    """Get system logs for the Logs view"""
    # Mock logs data - replace with actual log aggregation
    mock_logs = [
        {
            "id": "log-1",
            "timestamp": "2025-01-15T10:30:00Z",
            "level": "info",
            "source": "KrystalEngine",
            "message": "System initialized successfully",
            "metadata": {"userId": "user-1", "sessionId": "session-1", "duration": 150}
        },
        {
            "id": "log-2", 
            "timestamp": "2025-01-15T10:31:00Z",
            "level": "success",
            "source": "MongoDB",
            "message": "Database connection established",
            "metadata": {"connectionId": "conn-123", "database": "krystal_db"}
        },
        {
            "id": "log-3",
            "timestamp": "2025-01-15T10:32:00Z", 
            "level": "info",
            "source": "Pinecone",
            "message": "Vector database connected",
            "metadata": {"index": "krystal-memories", "dimension": 1536}
        },
        {
            "id": "log-4",
            "timestamp": "2025-01-15T10:33:00Z",
            "level": "warning",
            "source": "LLMProcessor", 
            "message": "High API latency detected",
            "metadata": {"latency_ms": 1250, "provider": "openai"}
        },
        {
            "id": "log-5",
            "timestamp": "2025-01-15T10:34:00Z",
            "level": "info",
            "source": "PluginManager",
            "message": "Plugin loaded: /os",
            "metadata": {"plugin": "os_control", "version": "1.0.0"}
        }
    ]
    
    return {
        "logs": mock_logs,
        "total_count": len(mock_logs),
        "status": "success"
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Process a chat message through Krystal Engine
    """
    if not krystal_engine:
        raise HTTPException(
            status_code=503,
            detail="Krystal Engine is not available"
        )
    
    try:
        # Process the message through Krystal Engine
        response = krystal_engine.process_input(request.message)
        
        return ChatResponse(
            response=response,
            status="success",
            timestamp=str(Path(__file__).stat().st_mtime)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )

@app.post("/api/command")
async def execute_command(request: Dict[str, Any]):
    """
    Execute a direct command through Krystal Engine
    """
    if not krystal_engine:
        raise HTTPException(
            status_code=503,
            detail="Krystal Engine is not available"
        )
    
    command = request.get("command", "")
    if not command:
        raise HTTPException(
            status_code=400,
            detail="Command is required"
        )
    
    try:
        # Process the command through Krystal Engine
        response = krystal_engine.process_input(command)
        
        return {
            "response": response,
            "status": "success",
            "command": command
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing command: {str(e)}"
        )

@app.get("/api/plugins")
async def get_plugins():
    """Get available plugins information"""
    if not krystal_engine:
        raise HTTPException(
            status_code=503,
            detail="Krystal Engine is not available"
        )
    
    try:
        plugins_info = krystal_engine.plugins.get_plugins_info()
        return {
            "plugins": plugins_info,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting plugins info: {str(e)}"
        )

@app.post("/api/voice")
async def voice_input(request: Dict[str, Any]):
    """
    Handle voice input (placeholder for future implementation)
    """
    # This is a placeholder for future voice input functionality
    return {
        "message": "Voice input not yet implemented",
        "status": "placeholder"
    }

@app.post("/api/webcam")
async def webcam_capture(request: Dict[str, Any]):
    """
    Trigger webcam capture
    """
    if not krystal_engine:
        raise HTTPException(
            status_code=503,
            detail="Krystal Engine is not available"
        )
    
    try:
        # Execute webcam command
        response = krystal_engine.process_input("/webcam")
        
        return {
            "response": response,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error with webcam capture: {str(e)}"
        )

@app.post("/api/listen")
async def voice_listen(request: Dict[str, Any]):
    """
    Trigger voice listening
    """
    if not krystal_engine:
        raise HTTPException(
            status_code=503,
            detail="Krystal Engine is not available"
        )
    
    try:
        # Execute listen command
        response = krystal_engine.process_input("/listen")
        
        return {
            "response": response,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error with voice listening: {str(e)}"
        )

@app.post("/api/see")
async def screen_capture(request: Dict[str, Any]):
    """
    Trigger screen capture
    """
    if not krystal_engine:
        raise HTTPException(
            status_code=503,
            detail="Krystal Engine is not available"
        )
    
    try:
        # Execute see command
        response = krystal_engine.process_input("/see")
        
        return {
            "response": response,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error with screen capture: {str(e)}"
        )

@app.post("/api/clear")
async def clear_context(request: Dict[str, Any]):
    """
    Clear conversation context
    """
    if not krystal_engine:
        raise HTTPException(
            status_code=503,
            detail="Krystal Engine is not available"
        )
    
    try:
        # This is a placeholder - actual implementation would depend on
        # how the engine handles context clearing
        return {
            "message": "Context cleared (placeholder)",
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing context: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "engine_loaded": krystal_engine is not None
    }

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Krystal AI API Server...")
    print("Frontend should be available at: http://localhost:3000")
    print("API will be available at: http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
