"""
BlenderMCP OpenAI Adapter - Use OpenAI models with BlenderMCP.

This package provides an adapter to use OpenAI's models (like GPT-4) 
with the BlenderMCP project instead of Claude.
"""

__version__ = "0.1.0"

# Import main components for easy access
from .adapter import OpenAIAdapter
from .cli import main

# For backward compatibility and convenience
__all__ = ["OpenAIAdapter", "main"] 