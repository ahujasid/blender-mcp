"""
Backward compatibility module for the BlenderMCP OpenAI adapter.

This module provides backward compatibility with the original openai_adapter.py file,
allowing existing code to continue working without modification.
"""

import os
import sys
import argparse
import logging

from .adapter import OpenAIAdapter
from .config import OpenAIConfig
from .logging_utils import setup_logging, logger


def main() -> None:
    """
    Main entry point for the legacy openai_adapter.py script.
    
    This function provides a drop-in replacement for the original
    openai_adapter.py script, parsing the same command-line arguments
    and providing the same functionality.
    """
    # Parse command line arguments (mimicking the original script)
    parser = argparse.ArgumentParser(description="OpenAI Adapter for BlenderMCP")
    parser.add_argument("--model", default="gpt-4", help="OpenAI model to use")
    parser.add_argument("--api-key", help="OpenAI API key")
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(level=logging.INFO)
    logger.info("Starting BlenderMCP OpenAI Adapter (legacy mode)")
    
    # Add current directory to path to help with imports
    sys.path.append(os.getcwd())
    
    # Create configuration
    config = OpenAIConfig(
        model=args.model,
        api_key=args.api_key or os.environ.get("OPENAI_API_KEY")
    )
    
    # Validate configuration
    if not config.api_key:
        logger.error("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or use --api-key.")
        sys.exit(1)
    
    # Create and run adapter
    try:
        logger.info(f"Using OpenAI model: {config.model}")
        adapter = OpenAIAdapter(config)
        adapter.run_mcp_server()
    except Exception as e:
        logger.error(f"Error running adapter: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)
    
    
if __name__ == "__main__":
    main() 