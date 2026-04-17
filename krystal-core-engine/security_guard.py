"""Security Guard module for protecting system files and operations."""

import os
import hashlib
from pathlib import Path
from typing import Tuple
import logging

# Setup logger
logger = logging.getLogger("Krystal.security")

# Security configuration
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
    Enforces strict access controls with hash-based authentication.
    """

    @staticmethod
    def _get_secret_hash() -> str:
        """Get the hash of the secret codeword from environment."""
        secret_codeword = os.getenv('SECURITY_CODEWORD')
        if not secret_codeword:
            return ""
        return hashlib.sha256(secret_codeword.encode()).hexdigest()

    @staticmethod
    def _hash_codeword(codeword: str) -> str:
        """Hash a codeword for comparison."""
        return hashlib.sha256(codeword.encode()).hexdigest()

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

            # Check if security codeword is configured
            secret_hash = SecurityManager._get_secret_hash()
            if not secret_hash:
                return (False, "Security Guard: SECURITY_CODEWORD not configured in environment. Set it to enable authorization.")

            # Verify codeword using hash comparison
            user_hash = SecurityManager._hash_codeword(user_codeword)
            if user_hash != secret_hash:
                return (False, "Security Guard: Invalid Codeword. Deletion blocked.")

            return (True, "Authorized")

        except (ValueError, KeyError) as e:
            return (False, f"Security Guard Error: {e}")
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
        except (FileNotFoundError, PermissionError) as e:
            logger.warning(f"[Security Guard] File check error: {e}")
            return False
        except Exception as e:
            logger.error(f"[Security Guard] Error checking path: {e}")
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
