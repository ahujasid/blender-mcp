#!/usr/bin/env python
# OpenAI adapter for blender-mcp

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, Optional, List, Iterator

# Import OpenAI libraries
from openai import OpenAI
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OpenAI-BlenderMCP-Adapter")

# Try to import the original MCP server
try:
    # Dynamically import the original blender_mcp module
    spec = importlib.util.find_spec("blender_mcp.server")
    if spec:
        blender_mcp_server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(blender_mcp_server)
        logger.info("Successfully imported blender_mcp.server")
    else:
        # Fallback to direct import if not found as a module
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        import blender_mcp.server as blender_mcp_server
        logger.info("Imported blender_mcp.server from src directory")
except ImportError as e:
    logger.error(f"Failed to import blender_mcp.server: {e}")
    sys.exit(1)

class OpenAIAdapter:
    """
    Adapter to use OpenAI's models instead of Claude with the blender-mcp project.
    """
    def __init__(self, model_name: str = "gpt-4", api_key: Optional[str] = None):
        """
        Initialize the OpenAI adapter.
        
        Args:
            model_name: The OpenAI model to use (default: "gpt-4")
            api_key: Optional OpenAI API key. If not provided, it will use the OPENAI_API_KEY environment variable.
        """
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key)
        self.tools = self._get_mcp_tools()
        logger.info(f"OpenAI adapter initialized with model: {model_name}")
        
    def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """
        Extract MCP tools from the blender_mcp server and convert them to OpenAI tool format.
        """
        tools = []
        
        # Extract tools from the FastMCP server object
        mcp_tools = blender_mcp_server.mcp.tools
        
        for tool_name, tool_func in mcp_tools.items():
            # Get the docstring and parse parameters
            doc = tool_func.__doc__ or ""
            
            # Create an OpenAI-compatible tool definition
            tool = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": doc,
                    "parameters": self._extract_parameters(tool_func)
                }
            }
            tools.append(tool)
            
        logger.info(f"Extracted {len(tools)} tools from MCP server")
        return tools
    
    def _extract_parameters(self, tool_func) -> Dict[str, Any]:
        """
        Extract parameters from a tool function and convert to OpenAI function parameters format.
        """
        import inspect
        
        # Get the signature of the function
        sig = inspect.signature(tool_func)
        
        # Skip the first parameter which is typically 'ctx' or 'self'
        parameters = list(sig.parameters.items())[1:]
        
        # Create the parameters object for OpenAI
        params_obj = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for name, param in parameters:
            # Add to properties
            param_type = "string"  # Default type
            
            # Try to determine the type from the annotation
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == str:
                    param_type = "string"
                elif param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif getattr(param.annotation, "__origin__", None) == list:
                    param_type = "array"
                    
            params_obj["properties"][name] = {"type": param_type}
            
            # Check if parameter is required
            if param.default == inspect.Parameter.empty:
                params_obj["required"].append(name)
        
        return params_obj
    
    def _call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """
        Call an MCP tool with the given parameters.
        """
        # Find the tool function
        tool_func = blender_mcp_server.mcp.tools.get(tool_name)
        if not tool_func:
            logger.error(f"Tool not found: {tool_name}")
            return f"Error: Tool '{tool_name}' not found"
            
        # Create a mock context
        class MockContext:
            def __init__(self):
                pass
        
        ctx = MockContext()
        
        try:
            # Call the tool function
            result = tool_func(ctx, **params)
            return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return f"Error calling tool {tool_name}: {e}"
    
    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> Iterator[str] or str:
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
            # Prepare the API call
            if stream:
                return self._stream_chat(messages)
            else:
                return self._sync_chat(messages)
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Error communicating with OpenAI: {e}"
    
    def _sync_chat(self, messages: List[Dict[str, str]]) -> str:
        """Handle synchronous (non-streaming) chat completion"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=self.tools
        )
        
        # Process and return the response
        message = response.choices[0].message
        
        # Handle tool calls if present
        if message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.type == 'function':
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        function_args = {}
                    
                    # Call the MCP tool
                    result = self._call_mcp_tool(function_name, function_args)
                    
                    # Add the tool result to messages
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": function_name,
                                    "arguments": tool_call.function.arguments
                                }
                            }
                        ]
                    })
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
                    
            # Get the model's response with the tool results
            second_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return second_response.choices[0].message.content
        
        return message.content
    
    def _stream_chat(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Handle streaming chat completion"""
        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=self.tools,
            stream=True
        )
        
        # Process the streaming response
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
        # Check if there are tool calls
        # Note: This is simplified and may need enhancement for complex tool interactions

def main():
    """
    Main entry point for the OpenAI adapter.
    """
    parser = argparse.ArgumentParser(description="OpenAI adapter for blender-mcp")
    parser.add_argument("--model", default="gpt-4", help="OpenAI model to use")
    parser.add_argument("--api-key", help="OpenAI API key (optional, can use OPENAI_API_KEY env var)")
    args = parser.parse_args()
    
    # Initialize adapter with specified model
    adapter = OpenAIAdapter(model_name=args.model, api_key=args.api_key)
    
    # Start the MCP server using the original functionality
    # This only initializes the server without running it
    logger.info("Initializing MCP server...")
    
    # Run the original server's main function (this starts the FastMCP server)
    logger.info("Starting the MCP server...")
    blender_mcp_server.main()

if __name__ == "__main__":
    main() 