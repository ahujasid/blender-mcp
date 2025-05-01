"""
Logging utilities for the BlenderMCP OpenAI adapter.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    json_format: bool = False,
) -> logging.Logger:
    """
    Configure logging for the adapter.
    
    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to a log file
        json_format: Whether to use JSON formatting for logs
        
    Returns:
        The configured logger
    """
    logger = logging.getLogger("blender_mcp_openai")
    logger.setLevel(level)
    logger.handlers = []  # Clear any existing handlers
    
    # Create formatter
    if json_format:
        formatter = logging.Formatter(
            '{"time":"%(asctime)s", "name":"%(name)s", "level":"%(levelname)s", "message":"%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Default logger instance
logger = logging.getLogger("blender_mcp_openai")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler) 