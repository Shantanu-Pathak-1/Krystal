"""
VS Code Bridge Plugin for Krystal AI
Provides integration with VS Code CLI to open files and control VS Code.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("Krystal.vscode")

class VSCodeBridge:
    """Bridge to control VS Code through CLI commands."""
    
    def __init__(self, vscode_path: Optional[str] = None):
        """
        Initialize VSCodeBridge with optional custom VS Code path.
        
        Args:
            vscode_path: Custom path to VS Code executable (code.exe on Windows)
        """
        self.vscode_path = vscode_path or self._find_vscode_path()
        logger.info(f"[VSCodeBridge] VS Code path: {self.vscode_path}")
    
    def _find_vscode_path(self) -> Optional[str]:
        """
        Find VS Code executable in common installation paths.
        
        Returns:
            Path to VS Code executable or None if not found
        """
        common_paths = [
            r"C:\Program Files\Microsoft VS Code\bin\code.exe",
            r"C:\Program Files (x86)\Microsoft VS Code\bin\code.exe",
            r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\bin\code.exe".format(os.getenv('USERNAME', '')),
            r"C:\Program Files\Microsoft VS Code\Code.exe",
            r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Try to find 'code' in PATH
        code_in_path = shutil.which("code")
        if code_in_path:
            return code_in_path
        
        logger.warning("[VSCodeBridge] VS Code not found in common paths")
        return None
    
    def is_available(self) -> bool:
        """Check if VS Code is available."""
        return self.vscode_path is not None
    
    def open_file(self, filepath: str, reuse_window: bool = True, line: int = None, column: int = None) -> Dict[str, Any]:
        """
        Open a file in VS Code.
        
        Args:
            filepath: Path to the file
            reuse_window: Open in existing VS Code window
            line: Jump to specific line (1-indexed)
            column: Jump to specific column (1-indexed)
            
        Returns:
            Dict with operation status
        """
        try:
            if not self.is_available():
                return {
                    "success": False,
                    "error": "VS Code not found"
                }
            
            file_path = Path(filepath).resolve()
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": "File does not exist"
                }
            
            # Build command
            cmd = [self.vscode_path]
            
            if reuse_window:
                cmd.append("--reuse-window")
            
            # Add line/column if specified
            if line is not None:
                cmd.append(f"--goto")
                if column is not None:
                    cmd.append(f"{file_path}:{line}:{column}")
                else:
                    cmd.append(f"{file_path}:{line}")
            else:
                cmd.append(str(file_path))
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                logger.info(f"[VSCodeBridge] Opened file in VS Code: {file_path}")
                return {
                    "success": True,
                    "path": str(file_path),
                    "command": " ".join(cmd)
                }
            else:
                logger.error(f"[VSCodeBridge] Error opening file: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"[VSCodeBridge] Error opening file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def open_directory(self, directory: str, reuse_window: bool = True) -> Dict[str, Any]:
        """
        Open a directory in VS Code.
        
        Args:
            directory: Path to the directory
            reuse_window: Open in existing VS Code window
            
        Returns:
            Dict with operation status
        """
        try:
            if not self.is_available():
                return {
                    "success": False,
                    "error": "VS Code not found"
                }
            
            dir_path = Path(directory).resolve()
            
            if not dir_path.exists():
                return {
                    "success": False,
                    "error": "Directory does not exist"
                }
            
            if not dir_path.is_dir():
                return {
                    "success": False,
                    "error": "Path is not a directory"
                }
            
            # Build command
            cmd = [self.vscode_path]
            
            if reuse_window:
                cmd.append("--reuse-window")
            
            cmd.append(str(dir_path))
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                logger.info(f"[VSCodeBridge] Opened directory in VS Code: {dir_path}")
                return {
                    "success": True,
                    "path": str(dir_path),
                    "command": " ".join(cmd)
                }
            else:
                logger.error(f"[VSCodeBridge] Error opening directory: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"[VSCodeBridge] Error opening directory: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def reveal_in_explorer(self, filepath: str) -> Dict[str, Any]:
        """
        Reveal a file in VS Code's explorer panel.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Dict with operation status
        """
        try:
            if not self.is_available():
                return {
                    "success": False,
                    "error": "VS Code not found"
                }
            
            file_path = Path(filepath).resolve()
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": "File does not exist"
                }
            
            # Build command with --reveal flag
            cmd = [self.vscode_path, "--reveal", str(file_path)]
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                logger.info(f"[VSCodeBridge] Revealed file in VS Code explorer: {file_path}")
                return {
                    "success": True,
                    "path": str(file_path),
                    "command": " ".join(cmd)
                }
            else:
                logger.error(f"[VSCodeBridge] Error revealing file: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"[VSCodeBridge] Error revealing file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def diff_files(self, file1: str, file2: str) -> Dict[str, Any]:
        """
        Open a diff view comparing two files in VS Code.
        
        Args:
            file1: Path to the first file
            file2: Path to the second file
            
        Returns:
            Dict with operation status
        """
        try:
            if not self.is_available():
                return {
                    "success": False,
                    "error": "VS Code not found"
                }
            
            path1 = Path(file1).resolve()
            path2 = Path(file2).resolve()
            
            if not path1.exists():
                return {
                    "success": False,
                    "error": f"File does not exist: {file1}"
                }
            
            if not path2.exists():
                return {
                    "success": False,
                    "error": f"File does not exist: {file2}"
                }
            
            # Build command with --diff flag
            cmd = [self.vscode_path, "--diff", str(path1), str(path2)]
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                logger.info(f"[VSCodeBridge] Opened diff view: {path1} vs {path2}")
                return {
                    "success": True,
                    "file1": str(path1),
                    "file2": str(path2),
                    "command": " ".join(cmd)
                }
            else:
                logger.error(f"[VSCodeBridge] Error opening diff: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"[VSCodeBridge] Error opening diff: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def focus_window(self) -> Dict[str, Any]:
        """
        Bring VS Code window to focus.
        
        Returns:
            Dict with operation status
        """
        try:
            if not self.is_available():
                return {
                    "success": False,
                    "error": "VS Code not found"
                }
            
            # Build command to bring to focus (open a new empty tab)
            cmd = [self.vscode_path, "--new-window", "--reuse-window"]
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                logger.info("[VSCodeBridge] Focused VS Code window")
                return {
                    "success": True,
                    "command": " ".join(cmd)
                }
            else:
                logger.error(f"[VSCodeBridge] Error focusing window: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"[VSCodeBridge] Error focusing window: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance (configured later)
_vscode_bridge = None

def get_vscode_bridge(vscode_path: Optional[str] = None) -> VSCodeBridge:
    """Get a VSCodeBridge instance."""
    global _vscode_bridge
    if _vscode_bridge is None or vscode_path:
        _vscode_bridge = VSCodeBridge(vscode_path)
    return _vscode_bridge
