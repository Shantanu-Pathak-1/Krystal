"""Security Guard module for protecting system files and operations."""

import os
from pathlib import Path
from typing import Tuple

# Security configuration
SECRET_CODEWORD = "TRINETRA-OVERRIDE"
BLOCKED_DIRECTORIES = [
    "C:\\Windows",
    "C:\\Program Files", 
    "C:\\Program Files (x86)",
    "C:\\Windows\\System32",
    "C:\\Windows\\SysWOW64",
    "C:\\Users\\Default",
    "C:\\ProgramData"
]


class SecurityManager:
    """
    Security manager for protecting system files and operations.
    Enforces strict access controls and codeword authentication.
    """
    
    @staticmethod
    def authorize_deletion(filepath: str, user_codeword: str) -> Tuple[bool, str]:
        """
        Authorize file deletion with security checks.
        
        Args:
            filepath: Path to file being deleted
            user_codeword: User-provided codeword
            
        Returns:
            Tuple of (authorized: bool, message: str)
        """
        try:
            # Get absolute path
            abs_path = os.path.abspath(filepath)
            
            # Check if path is in blocked directories
            for blocked_dir in BLOCKED_DIRECTORIES:
                if abs_path.lower().startswith(blocked_dir.lower()):
                    return (False, "CRITICAL ERROR: Attempted to modify protected system files. Access Denied.")
            
            # Check codeword
            if user_codeword != SECRET_CODEWORD:
                return (False, "Security Guard: Invalid Codeword. Deletion blocked.")
            
            return (True, "Authorized")
            
        except Exception as e:
            return (False, f"Security Guard Error: {e}")
    
    @staticmethod
    def is_protected_path(filepath: str) -> bool:
        """
        Check if a path is in protected directories.
        
        Args:
            filepath: Path to check
            
        Returns:
            True if path is protected, False otherwise
        """
        try:
            abs_path = os.path.abspath(filepath)
            for blocked_dir in BLOCKED_DIRECTORIES:
                if abs_path.lower().startswith(blocked_dir.lower()):
                    return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def validate_operation(operation: str, filepath: str = None) -> Tuple[bool, str]:
        """
        Validate if an operation is allowed.
        
        Args:
            operation: Type of operation (delete, move, modify)
            filepath: Target file path (optional)
            
        Returns:
            Tuple of (allowed: bool, message: str)
        """
        if filepath and SecurityManager.is_protected_path(filepath):
            return (False, f"Operation '{operation}' blocked: Path is in protected system directory")
        
        if operation in ["delete", "rmtree", "remove"] and not filepath:
            return (False, f"Operation '{operation}' requires explicit filepath for security validation")
        
        return (True, "Operation allowed")
