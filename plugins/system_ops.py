"""System Operations plugin for Windows OS control with security protection."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Import security guard
import sys
sys.path.append(str(Path(__file__).parent.parent))
from security_guard import SecurityManager

NAME = "/sys"
DESCRIPTION = "Controls Windows OS settings (volume, brightness, wifi) and manages files (list, move, delete)."


def run(query, **kwargs):
    """
    Execute system operations with security protection.
    
    Args:
        query: The command to execute
        **kwargs: Additional arguments (codeword for protected operations)
    
    Returns:
        Success or error message
    """
    if not query.strip():
        return "Error: Please provide a system command. Usage: /sys <command> [parameters]"
    
    try:
        # Parse command
        parts = query.strip().split(None, 1)
        if len(parts) < 1:
            return "Error: No command provided"
        
        command = parts[0].lower()
        params = parts[1].strip() if len(parts) > 1 else ""
        
        # Route to appropriate function
        if command == "list":
            return _list_files(params)
        elif command == "move":
            return _move_file(params, **kwargs)
        elif command == "delete":
            return _delete_file(params, **kwargs)
        elif command == "volume":
            return _set_volume(params)
        elif command in ["set volume", "volume up", "volume down", "increase volume", "decrease volume"]:
            return _set_volume(params)
        elif command == "brightness":
            return _set_brightness(params)
        elif command == "wifi":
            return _toggle_wifi(params)
        else:
            return f"Error: Unknown command '{command}'. Available: list, move, delete, volume, brightness, wifi"
            
    except Exception as e:
        return f"System Ops error: {type(e).__name__}: {e}"


def _list_files(directory: str) -> str:
    """List files in a directory."""
    try:
        if not directory:
            return "Error: Please provide directory path"
        
        path = Path(directory)
        if not path.exists():
            return f"Error: Directory '{directory}' does not exist"
        
        files = []
        for item in path.iterdir():
            if item.is_file():
                size = item.stat().st_size
                files.append(f"FILE: {item.name} ({size} bytes)")
            else:
                files.append(f"DIR:  {item.name}/")
        
        if not files:
            return f"Directory '{directory}' is empty"
        
        return f"Contents of '{directory}':\n" + "\n".join(sorted(files))
        
    except Exception as e:
        return f"Error listing files: {e}"


def _move_file(src_dest: str, **kwargs) -> str:
    """Move file with security check."""
    try:
        if not src_dest:
            return "Error: Please provide source and destination (format: 'source -> destination')"
        
        if "->" not in src_dest:
            return "Error: Invalid format. Use 'source -> destination'"
        
        src, dest = src_dest.split("->", 1)
        src = src.strip()
        dest = dest.strip()
        
        if not src or not dest:
            return "Error: Both source and destination are required"
        
        # Security check for destination
        auth_result, message = SecurityManager.authorize_deletion(dest, kwargs.get("codeword", ""))
        if not auth_result:
            return message
        
        # Perform move
        src_path = Path(src)
        dest_path = Path(dest)
        
        if not src_path.exists():
            return f"Error: Source file '{src}' does not exist"
        
        shutil.move(str(src_path), str(dest_path))
        return f"Moved '{src}' to '{dest}' successfully"
        
    except Exception as e:
        return f"Error moving file: {e}"


def _delete_file(filepath: str, **kwargs) -> str:
    """Delete file with security authorization."""
    try:
        if not filepath:
            return "Error: Please provide file path to delete"
        
        # Security check
        auth_result, message = SecurityManager.authorize_deletion(filepath, kwargs.get("codeword", ""))
        if not auth_result:
            return message
        
        # Perform deletion
        path = Path(filepath)
        if not path.exists():
            return f"Error: File '{filepath}' does not exist"
        
        if path.is_dir():
            shutil.rmtree(str(path))
            return f"Deleted directory '{filepath}' and all contents"
        else:
            path.unlink()
            return f"Deleted file '{filepath}'"
        
    except Exception as e:
        return f"Error deleting file: {e}"


def _set_volume(level_str: str) -> str:
    """Set system volume using pycaw for precise control."""
    try:
        # Extract only the numbers from the input string (e.g., "100%" -> 100)
        match = re.search(r'\d+', str(level_str))
        if not match:
            return "Error: Could not understand the volume level."
        
        level = int(match.group())
        level = max(0, min(100, level))  # Clamp between 0 and 100
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # pycaw expects a scalar value between 0.0 and 1.0
        scalar_level = level / 100.0
        volume.SetMasterVolumeLevelScalar(scalar_level, None)
        return f"System volume successfully set to {level}%."
    except Exception as e:
        return f"Failed to set volume: {str(e)}"


def _set_brightness(level: str) -> str:
    """Set screen brightness using PowerShell."""
    try:
        if not level:
            return "Error: Please provide brightness level (0-100)"
        
        try:
            brightness_level = int(level)
            if brightness_level < 0 or brightness_level > 100:
                return "Error: Brightness level must be between 0 and 100"
        except ValueError:
            return "Error: Brightness level must be a number"
        
        # Use PowerShell to set brightness
        ps_command = f"Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods | ForEach-Object {{$_.WmiSetBrightness(1,{brightness_level})}}"
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return f"Brightness set to {brightness_level}%"
        else:
            return f"Error setting brightness: {result.stderr}"
        
    except Exception as e:
        return f"Error setting brightness: {e}"


def _toggle_wifi(state: str) -> str:
    """Toggle WiFi using netsh."""
    try:
        if not state:
            return "Error: Please provide WiFi state (enable/disable)"
        
        if state.lower() not in ["enable", "disable"]:
            return "Error: State must be 'enable' or 'disable'"
        
        # Use netsh to toggle WiFi
        interface = "Wi-Fi"
        command = f"netsh interface set interface \"{interface}\" admin={state}"
        
        result = subprocess.run(
            ["netsh", "interface", "set", f"interface=\"{interface}\"", f"admin={state}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return f"WiFi {state}d successfully"
        else:
            return f"Error toggling WiFi: {result.stderr}"
        
    except Exception as e:
        return f"Error toggling WiFi: {e}"
