"""
Centralized logging configuration for Krystal AI.
Provides consistent logging across all modules.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(
    name: str = "Krystal",
    level: str = "INFO",
    log_file: str = None,
    log_dir: str = None
) -> logging.Logger:
    """
    Setup and configure a logger for Krystal modules.
    
    Args:
        name: Logger name (default: "Krystal")
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file name
        log_dir: Directory for log files (default: logs/)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler with color formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Color formatter for console
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if log_file is specified
    if log_file:
        log_path = Path(log_dir) / log_file if log_dir else Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        
        # File formatter with more details
        file_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (if None, returns root Krystal logger)
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"Krystal.{name}")
    return logging.getLogger("Krystal")


# Initialize root logger on import
_root_logger = setup_logger(
    name="Krystal",
    level="INFO",
    log_file="krystal.log",
    log_dir="logs"
)


# Convenience functions for different log levels
def debug(message: str, module: str = None):
    """Log debug message."""
    logger = get_logger(module)
    logger.debug(message)


def info(message: str, module: str = None):
    """Log info message."""
    logger = get_logger(module)
    logger.info(message)


def warning(message: str, module: str = None):
    """Log warning message."""
    logger = get_logger(module)
    logger.warning(message)


def error(message: str, module: str = None):
    """Log error message."""
    logger = get_logger(module)
    logger.error(message)


def critical(message: str, module: str = None):
    """Log critical message."""
    logger = get_logger(module)
    logger.critical(message)
