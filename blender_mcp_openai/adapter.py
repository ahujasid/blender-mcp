"""
Main adapter class for BlenderMCP OpenAI integration.

This module contains the main OpenAIAdapter class that coordinates all components
of the BlenderMCP OpenAI integration, including schema extraction, context management,
dispatching, and streaming.
"""

import importlib.util
import os
import sys
import json
from typing import Dict, Any, List, Optional, Iterator, Union, Tuple

from openai import OpenAI

from .logging_utils import logger
from .config import OpenAIConfig, AdapterConfig
from .context import AdapterContext
from .schema import extract_tools_schema
from .dispatch import handle_tool_calls, ToolExecutionError
from .streaming import ToolAwareStream


class OpenAIAdapter:
    """
    Adapter to use OpenAI models with the BlenderMCP project.
    
    This class provides the main interface for using OpenAI models with BlenderMCP.
    It handles initialization, schema extraction, context management, and communication
    with the OpenAI API.
    
    Attributes:
        config: Configuration for the adapter
        client: OpenAI API client
        mcp_server: Reference to the MCP server module
        tools: List of OpenAI function tools extracted from MCP
        adapter_ctx: Context manager for adapter operations
    """
    
    def __init__(
        self,
        config: Optional[Union[OpenAIConfig, AdapterConfig]] = None,
        mcp_server = None
    ):
        """
        Initialize the OpenAI adapter.
        
        Args:
            config: Configuration for the adapter (default: AdapterConfig())
            mcp_server: Reference to the MCP server module (default: auto-import)
        """
        # Initialize configuration
        if config is None:
            config = AdapterConfig()
        elif isinstance(config, OpenAIConfig):
            # Convert OpenAIConfig to AdapterConfig
            adapter_config = AdapterConfig()
            adapter_config.openai = config
            config = adapter_config
        
        self.config = config
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=config.openai.api_key)
        
        # Import MCP server if not provided
        self.mcp_server = mcp_server or self._import_mcp_server()
        
        # Create adapter context
        self.adapter_ctx = AdapterContext(self.mcp_server)
        
        # Extract tools schema
        self.tools = extract_tools_schema(self.mcp_server.mcp.tools)
        
        logger.info(f"OpenAI adapter initialized with {len(self.tools)} tools")
        logger.debug(f"Using model: {config.openai.model}")
    
    def _import_mcp_server(self):
        """
        Import the MCP server module.
        
        This method attempts to import the BlenderMCP server module using various
        strategies, falling back to more flexible approaches if needed.
        
        Returns:
            The imported MCP server module
            
        Raises:
            ImportError: If the MCP server module cannot be imported
        """
        # Try to import as a module
        try:
            # Dynamically import the original blender_mcp module
            spec = importlib.util.find_spec("blender_mcp.server")
            if spec:
                mcp_server = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mcp_server)
                logger.info("Successfully imported blender_mcp.server as a module")
                return mcp_server
        except ImportError:
            logger.warning("Failed to import blender_mcp.server as a module")
        
        # Try to import from the src directory
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
            import blender_mcp.server as mcp_server
            logger.info("Imported blender_mcp.server from src directory")
            return mcp_server
        except ImportError:
            logger.error("Failed to import blender_mcp.server from src directory")
        
        # Try to import from the current directory
        try:
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            import blender_mcp.server as mcp_server
            logger.info("Imported blender_mcp.server from current directory")
            return mcp_server
        except ImportError:
            logger.error("Failed to import blender_mcp.server from current directory")
            raise ImportError("Could not import blender_mcp.server - make sure it's installed or in your path")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> Union[str, Iterator[str]]:
        """
        Send a chat request to OpenAI and process the response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            stream: Whether to stream the response
            
        Returns:
            If stream=True, returns an iterator of response chunks.
            If stream=False, returns the complete response.
        """
        try:
            # Apply system prompt if configured
            prepared_messages = self.config.openai.get_messages(messages)
            
            # Prepare the API parameters
            params = self.config.openai.to_dict()
            params["messages"] = prepared_messages
            params["tools"] = self.tools
            params["stream"] = stream
            
            logger.info(f"Sending chat request to OpenAI with model {params['model']}")
            logger.debug(f"Parameters: {params}")
            
            # Handle streaming or non-streaming
            if stream:
                return self._stream_chat(params)
            else:
                return self._sync_chat(params)
                
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Error communicating with OpenAI: {e}"
    
    def _sync_chat(self, params: Dict[str, Any]) -> str:
        """
        Handle synchronous (non-streaming) chat completion.
        
        Args:
            params: Parameters for the OpenAI API call
            
        Returns:
            The completed response text
        """
        # Create completion
        response = self.client.chat.completions.create(**params)
        
        # Process and return the response
        message = response.choices[0].message
        
        # Handle tool calls if present
        if message.tool_calls:
            logger.info(f"Response contains {len(message.tool_calls)} tool calls")
            
            # Execute the tools
            tool_results = handle_tool_calls(self.adapter_ctx, message.tool_calls)
            
            # Add the tool results to the messages
            for tool_call in message.tool_calls:
                call_id = tool_call.id
                function_name = tool_call.function.name
                
                # Add the assistant message with tool calls
                params["messages"].append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                
                # Add the tool response message
                params["messages"].append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": str(tool_results.get(call_id, ""))
                })
            
            logger.info("Getting second response with tool results")
            
            # Get the model's response with the tool results
            params["stream"] = False  # Ensure non-streaming
            second_response = self.client.chat.completions.create(**params)
            
            return second_response.choices[0].message.content
        
        return message.content
    
    def _stream_chat(self, params: Dict[str, Any]) -> Iterator[str]:
        """
        Handle streaming chat completion with tool call support.
        
        Args:
            params: Parameters for the OpenAI API call
            
        Returns:
            Iterator of response chunks
        """
        # Create completion with streaming
        stream = self.client.chat.completions.create(**params)
        
        # Wrap the stream with our tool-aware handler
        tool_aware_stream = ToolAwareStream(stream, self.adapter_ctx)
        
        # Return the wrapped stream
        return tool_aware_stream
    
    def run_mcp_server(self) -> None:
        """
        Run the MCP server.
        
        This method starts the MCP server using its original main function.
        """
        logger.info("Starting the MCP server...")
        self.mcp_server.main() 