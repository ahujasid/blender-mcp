"""
Command-line interface for the BlenderMCP OpenAI adapter.

This module provides a command-line interface for the BlenderMCP OpenAI adapter,
allowing users to start the adapter with various configurations.
"""

import argparse
import logging
import json
import os
import sys
from typing import Dict, Any, Optional

from .adapter import OpenAIAdapter
from .config import OpenAIConfig, AdapterConfig
from .logging_utils import setup_logging, logger


def parse_args():
    """
    Parse command-line arguments for the adapter.
    
    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(description="Run the BlenderMCP OpenAI adapter.")
    
    # OpenAI configuration
    parser.add_argument("--model", type=str, default="gpt-4",
                        help="OpenAI model to use")
    parser.add_argument("--api-key", type=str,
                        help="OpenAI API key (defaults to OPENAI_API_KEY environment variable)")
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="Temperature for the model (default: 0.7)")
    parser.add_argument("--max-tokens", type=int,
                        help="Maximum number of tokens to generate")
    parser.add_argument("--system-prompt", type=str,
                        help="System prompt to prepend to messages")
    parser.add_argument("--config-file", type=str,
                        help="Path to a configuration file (JSON)")
    
    # Logging configuration
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level (default: INFO)")
    parser.add_argument("--log-file", type=str,
                        help="Path to a log file")
    parser.add_argument("--json-logs", action="store_true",
                        help="Output logs in JSON format")
    
    return parser.parse_args()


def create_config_from_args(args) -> AdapterConfig:
    """
    Create a configuration object from command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        AdapterConfig instance with values from arguments
    """
    # Handle config file if provided
    if args.config_file and os.path.exists(args.config_file):
        config = AdapterConfig.from_file(args.config_file)
        logger.info(f"Loaded configuration from {args.config_file}")
    else:
        config = AdapterConfig()
    
    # Override with command-line arguments
    if args.model:
        config.openai.model = args.model
    
    if args.api_key:
        config.openai.api_key = args.api_key
    
    if args.temperature:
        config.openai.temperature = args.temperature
    
    if args.max_tokens:
        config.openai.max_tokens = args.max_tokens
    
    if args.system_prompt:
        config.openai.system_prompt = args.system_prompt
    
    # Configure logging
    if args.log_level:
        config.log_level = args.log_level
    
    if args.log_file:
        config.log_file = args.log_file
    
    if args.json_logs:
        config.json_logging = True
    
    return config


def setup_environment() -> None:
    """
    Set up the environment for the adapter.
    
    This function configures environment variables and performs other
    setup tasks necessary for the adapter to function properly.
    """
    # Add the current directory to the path to help with imports
    sys.path.append(os.getcwd())
    
    # Handle environment variables
    for key, value in os.environ.items():
        # Forward any additional OPENAI_* environment variables to the client
        if key.startswith("OPENAI_") and key != "OPENAI_API_KEY":
            logger.debug(f"Found OpenAI environment variable: {key}")


def run_adapter(config: AdapterConfig) -> None:
    """
    Run the adapter with the given configuration.
    
    Args:
        config: Configuration for the adapter
    """
    try:
        # Create and initialize the adapter
        adapter = OpenAIAdapter(config)
        logger.info("Adapter initialized successfully")
        
        # Run the MCP server (this will block until the server exits)
        adapter.run_mcp_server()
    except Exception as e:
        logger.error(f"Error running adapter: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the adapter CLI.
    
    This function parses command-line arguments, configures the adapter,
    and starts it.
    """
    # Parse command-line arguments
    args = parse_args()
    
    # Set up logging
    log_level = getattr(logging, args.log_level)
    setup_logging(
        level=log_level,
        log_file=args.log_file,
        json_format=args.json_logs
    )
    
    # Set up the environment
    setup_environment()
    
    # Create configuration from arguments
    config = create_config_from_args(args)
    
    # Validate configuration
    if not config.openai.api_key:
        logger.error("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or use --api-key.")
        sys.exit(1)
    
    # Log configuration (excluding sensitive info)
    logger_config = config.openai.to_dict()
    logger_config.pop("api_key", None)  # Don't log the API key
    logger.info(f"OpenAI configuration: {logger_config}")
    
    # Run the adapter
    run_adapter(config)


if __name__ == "__main__":
    main() 