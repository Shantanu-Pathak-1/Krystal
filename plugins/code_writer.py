"""
Code Writer Plugin for Krystal Engine
Allows Krystal to create, modify, and delete files through natural language.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import requests

logger = logging.getLogger("Krystal.code_writer")

class CodeWriter:
    """Plugin for Krystal to perform file operations through natural language."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """
        Initialize CodeWriter with API URL.
        
        Args:
            api_url: URL of the Krystal API
        """
        self.api_url = api_url
    
    def _call_api(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the Krystal API endpoint."""
        try:
            url = f"{self.api_url}{endpoint}"
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"[CodeWriter] API call failed: {e}")
            return {"success": False, "error": str(e)}
    
    def create_file(self, filepath: str, content: str, open_in_vscode: bool = True) -> str:
        """
        Create a new file with content.
        
        Args:
            filepath: Path to the file
            content: File content
            open_in_vscode: Open file in VS Code after creation
            
        Returns:
            Result message
        """
        data = {
            "path": filepath,
            "content": content,
            "overwrite": False,
            "create_backup": True,
            "open_in_vscode": open_in_vscode
        }
        
        result = self._call_api("/api/file/create", data)
        
        if result.get("success"):
            return f"✅ Created file: {filepath}"
        else:
            return f"❌ Failed to create file: {result.get('error', 'Unknown error')}"
    
    def modify_file(self, filepath: str, operation: str, content: str = "", search: str = "", replace: str = "") -> str:
        """
        Modify an existing file.
        
        Args:
            filepath: Path to the file
            operation: 'append', 'replace', 'edit'
            content: Content to add
            search: Search string for edit operation
            replace: Replace string for edit operation
            
        Returns:
            Result message
        """
        data = {
            "path": filepath,
            "operation": operation,
            "content": content,
            "search": search,
            "replace": replace,
            "create_backup": True
        }
        
        result = self._call_api("/api/file/modify", data)
        
        if result.get("success"):
            return f"✅ Modified file: {filepath} (operation: {operation})"
        else:
            return f"❌ Failed to modify file: {result.get('error', 'Unknown error')}"
    
    def delete_file(self, filepath: str) -> str:
        """
        Delete a file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Result message
        """
        data = {
            "path": filepath,
            "create_backup": True
        }
        
        result = self._call_api("/api/file/delete", data)
        
        if result.get("success"):
            return f"✅ Deleted file: {filepath}"
        else:
            return f"❌ Failed to delete file: {result.get('error', 'Unknown error')}"
    
    def read_file(self, filepath: str) -> str:
        """
        Read a file's content.
        
        Args:
            filepath: Path to the file
            
        Returns:
            File content or error message
        """
        data = {"path": filepath}
        result = self._call_api("/api/file/read", data)
        
        if result.get("success"):
            return result.get("content", "")
        else:
            return f"❌ Failed to read file: {result.get('error', 'Unknown error')}"
    
    def open_in_vscode(self, filepath: str) -> str:
        """
        Open a file in VS Code.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Result message
        """
        data = {
            "path": filepath,
            "reuse_window": True
        }
        
        result = self._call_api("/api/vscode/open", data)
        
        if result.get("success"):
            return f"✅ Opened file in VS Code: {filepath}"
        else:
            return f"❌ Failed to open file: {result.get('error', 'Unknown error')}"
    
    def get_project_structure(self, recursive: bool = True) -> str:
        """
        Get the project structure.
        
        Args:
            recursive: Scan subdirectories recursively
            
        Returns:
            Project structure as JSON string
        """
        data = {"recursive": recursive}
        result = self._call_api("/api/project/scan", data)
        
        if result.get("success"):
            structure = result.get("structure", {})
            return json.dumps(structure, indent=2)
        else:
            return f"❌ Failed to scan project: {result.get('error', 'Unknown error')}"


# Global instance
_code_writer = None

def get_code_writer(api_url: str = "http://localhost:8000") -> CodeWriter:
    """Get a CodeWriter instance."""
    global _code_writer
    if _code_writer is None:
        _code_writer = CodeWriter(api_url)
    return _code_writer


# Plugin registration for Krystal engine
def register_plugin(plugin_manager):
    """Register the code writer plugin with Krystal's plugin manager."""
    
    code_writer = get_code_writer()
    
    @plugin_manager.register_command("create_file")
    def create_file_command(filepath: str, content: str, open_vscode: str = "true") -> str:
        """Create a new file with content. Usage: /create_file <filepath> <content> [--open_vscode]"""
        open_in_vscode = open_vscode.lower() == "true"
        return code_writer.create_file(filepath, content, open_in_vscode)
    
    @plugin_manager.register_command("modify_file")
    def modify_file_command(filepath: str, operation: str = "append", content: str = "") -> str:
        """Modify an existing file. Usage: /modify_file <filepath> <operation> <content>"""
        return code_writer.modify_file(filepath, operation, content)
    
    @plugin_manager.register_command("delete_file")
    def delete_file_command(filepath: str) -> str:
        """Delete a file. Usage: /delete_file <filepath>"""
        return code_writer.delete_file(filepath)
    
    @plugin_manager.register_command("read_file")
    def read_file_command(filepath: str) -> str:
        """Read a file's content. Usage: /read_file <filepath>"""
        return code_writer.read_file(filepath)
    
    @plugin_manager.register_command("open_vscode")
    def open_vscode_command(filepath: str) -> str:
        """Open a file in VS Code. Usage: /open_vscode <filepath>"""
        return code_writer.open_in_vscode(filepath)
    
    @plugin_manager.register_command("project_structure")
    def project_structure_command(recursive: str = "true") -> str:
        """Get the project structure. Usage: /project_structure [--recursive]"""
        return code_writer.get_project_structure(recursive.lower() == "true")
    
    logger.info("[CodeWriter] Plugin registered with Krystal engine")
