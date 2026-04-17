"""
File Writer Plugin for Krystal AI
Provides safe file creation, modification, and deletion operations.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger("Krystal.file_writer")

# Blocked directories to prevent accidental system file modifications
BLOCKED_DIRECTORIES = [
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\Windows\\System32",
    "C:\\Windows\\SysWOW64",
    "C:\\Users\\Default",
    "C:\\ProgramData"
]

class FileWriter:
    """Safe file operations with path validation and backup support."""
    
    def __init__(self, allowed_base_path: Optional[str] = None):
        """
        Initialize FileWriter with optional base path restriction.
        
        Args:
            allowed_base_path: If specified, only allow operations within this directory
        """
        self.allowed_base_path = Path(allowed_base_path).resolve() if allowed_base_path else None
    
    def _is_path_safe(self, filepath: str) -> bool:
        """
        Check if a path is safe for operations.
        
        Args:
            filepath: Path to check
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            abs_path = Path(filepath).resolve()
            
            # Check against blocked directories
            for blocked_dir in BLOCKED_DIRECTORIES:
                if str(abs_path).lower().startswith(blocked_dir.lower()):
                    logger.warning(f"[FileWriter] Blocked path: {abs_path}")
                    return False
            
            # Check if within allowed base path
            if self.allowed_base_path:
                try:
                    abs_path.relative_to(self.allowed_base_path)
                except ValueError:
                    logger.warning(f"[FileWriter] Path outside allowed base: {abs_path}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"[FileWriter] Error checking path safety: {e}")
            return False
    
    def create_file(
        self, 
        filepath: str, 
        content: str, 
        overwrite: bool = False,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new file with content.
        
        Args:
            filepath: Path to the file
            content: File content
            overwrite: Allow overwriting existing file
            create_backup: Create backup before overwriting
            
        Returns:
            Dict with operation status
        """
        try:
            if not self._is_path_safe(filepath):
                return {
                    "success": False,
                    "error": "Path is not safe for operation"
                }
            
            file_path = Path(filepath)
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists
            if file_path.exists():
                if not overwrite:
                    return {
                        "success": False,
                        "error": "File already exists. Use overwrite=True to overwrite."
                    }
                
                # Create backup if enabled
                if create_backup:
                    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                    shutil.copy2(file_path, backup_path)
                    logger.info(f"[FileWriter] Created backup: {backup_path}")
            
            # Write content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"[FileWriter] Created file: {file_path}")
            
            return {
                "success": True,
                "path": str(file_path),
                "size": len(content),
                "backup_created": file_path.exists() and create_backup
            }
            
        except PermissionError as e:
            logger.error(f"[FileWriter] Permission error: {e}")
            return {
                "success": False,
                "error": f"Permission denied: {e}"
            }
        except Exception as e:
            logger.error(f"[FileWriter] Error creating file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def modify_file(
        self,
        filepath: str,
        operation: str = "append",
        content: str = "",
        search: str = "",
        replace: str = "",
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Modify an existing file.
        
        Args:
            filepath: Path to the file
            operation: 'append', 'replace', 'edit', 'prepend'
            content: Content to add/replace with
            search: Search string for 'edit' operation
            replace: Replace string for 'edit' operation
            create_backup: Create backup before modifying
            
        Returns:
            Dict with operation status
        """
        try:
            if not self._is_path_safe(filepath):
                return {
                    "success": False,
                    "error": "Path is not safe for operation"
                }
            
            file_path = Path(filepath)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": "File does not exist"
                }
            
            # Create backup if enabled
            if create_backup:
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                shutil.copy2(file_path, backup_path)
                logger.info(f"[FileWriter] Created backup: {backup_path}")
            
            # Read existing content
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            # Apply operation
            if operation == "append":
                new_content = existing_content + "\n" + content
            elif operation == "prepend":
                new_content = content + "\n" + existing_content
            elif operation == "replace":
                new_content = content
            elif operation == "edit":
                if search:
                    new_content = existing_content.replace(search, replace)
                else:
                    new_content = existing_content.replace(search, content) if search else existing_content
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"[FileWriter] Modified file: {file_path} (operation: {operation})")
            
            return {
                "success": True,
                "path": str(file_path),
                "operation": operation,
                "backup_created": create_backup
            }
            
        except PermissionError as e:
            logger.error(f"[FileWriter] Permission error: {e}")
            return {
                "success": False,
                "error": f"Permission denied: {e}"
            }
        except Exception as e:
            logger.error(f"[FileWriter] Error modifying file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_file(self, filepath: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        Delete a file.
        
        Args:
            filepath: Path to the file
            create_backup: Create backup before deleting
            
        Returns:
            Dict with operation status
        """
        try:
            if not self._is_path_safe(filepath):
                return {
                    "success": False,
                    "error": "Path is not safe for operation"
                }
            
            file_path = Path(filepath)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": "File does not exist"
                }
            
            # Create backup if enabled
            if create_backup:
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                shutil.copy2(file_path, backup_path)
                logger.info(f"[FileWriter] Created backup before delete: {backup_path}")
            
            # Delete file
            file_path.unlink()
            
            logger.info(f"[FileWriter] Deleted file: {file_path}")
            
            return {
                "success": True,
                "path": str(file_path),
                "backup_created": create_backup
            }
            
        except PermissionError as e:
            logger.error(f"[FileWriter] Permission error: {e}")
            return {
                "success": False,
                "error": f"Permission denied: {e}"
            }
        except Exception as e:
            logger.error(f"[FileWriter] Error deleting file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def read_file(self, filepath: str) -> Dict[str, Any]:
        """
        Read a file's content.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Dict with operation status and content
        """
        try:
            if not self._is_path_safe(filepath):
                return {
                    "success": False,
                    "error": "Path is not safe for operation"
                }
            
            file_path = Path(filepath)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": "File does not exist"
                }
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "path": str(file_path),
                "content": content,
                "size": len(content)
            }
            
        except PermissionError as e:
            logger.error(f"[FileWriter] Permission error: {e}")
            return {
                "success": False,
                "error": f"Permission denied: {e}"
            }
        except Exception as e:
            logger.error(f"[FileWriter] Error reading file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_directory(self, directory: str, recursive: bool = False) -> Dict[str, Any]:
        """
        List files in a directory.
        
        Args:
            directory: Directory path
            recursive: Recursively list subdirectories
            
        Returns:
            Dict with operation status and file list
        """
        try:
            if not self._is_path_safe(directory):
                return {
                    "success": False,
                    "error": "Path is not safe for operation"
                }
            
            dir_path = Path(directory)
            
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
            
            files = []
            if recursive:
                for item in dir_path.rglob("*"):
                    files.append({
                        "path": str(item.relative_to(dir_path)),
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else 0
                    })
            else:
                for item in dir_path.iterdir():
                    files.append({
                        "path": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else 0
                    })
            
            return {
                "success": True,
                "path": str(dir_path),
                "files": files,
                "count": len(files)
            }
            
        except PermissionError as e:
            logger.error(f"[FileWriter] Permission error: {e}")
            return {
                "success": False,
                "error": f"Permission denied: {e}"
            }
        except Exception as e:
            logger.error(f"[FileWriter] Error listing directory: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance (can be configured later)
_file_writer = FileWriter()

def get_file_writer(allowed_base_path: Optional[str] = None) -> FileWriter:
    """Get a FileWriter instance."""
    if allowed_base_path:
        return FileWriter(allowed_base_path)
    return _file_writer
