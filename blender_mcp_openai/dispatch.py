"""
Tool dispatch utilities for BlenderMCP OpenAI adapter.

This module handles the execution of MCP tools, including error handling
and result formatting for OpenAI function calling.
"""

import json
import traceback
from typing import Dict, Any, Optional, Union

from .context import AdapterContext
from .logging_utils import logger


class ToolExecutionError(Exception):
    """
    Exception raised when a tool execution fails.
    
    This exception includes structured information about the error,
    making it easier to handle and report to users.
    
    Attributes:
        tool_name: Name of the tool that failed
        error: Error message
        details: Additional error details (e.g., traceback)
    """
    
    def __init__(self, tool_name: str, error: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize a ToolExecutionError.
        
        Args:
            tool_name: Name of the tool that failed
            error: Error message
            details: Additional error details
        """
        self.tool_name = tool_name
        self.error = error
        self.details = details or {}
        super().__init__(f"Error executing tool {tool_name}: {error}")
    
    def to_response(self) -> Dict[str, Any]:
        """
        Convert to a structured error response.
        
        Returns:
            Dictionary with error information
        """
        return {
            "error": {
                "tool": self.tool_name,
                "message": str(self.error),
                "details": self.details
            }
        }


def execute_tool(
    adapter_ctx: AdapterContext,
    tool_name: str, 
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a tool with proper error handling.
    
    This function executes an MCP tool using the given parameters,
    handling errors and formatting the result for OpenAI function calling.
    
    Args:
        adapter_ctx: Adapter context for tool execution
        tool_name: Name of the tool to execute
        params: Parameters for the tool
        
    Returns:
        Dictionary with the tool execution result
        
    Raises:
        ToolExecutionError: If the tool execution fails
    """
    # Find the tool function
    tool_func = adapter_ctx.mcp_server.mcp.tools.get(tool_name)
    if not tool_func:
        raise ToolExecutionError(
            tool_name, 
            f"Tool not found: {tool_name}",
            {"available_tools": list(adapter_ctx.mcp_server.mcp.tools.keys())}
        )
    
    logger.info(f"Executing tool: {tool_name} with params: {params}")
    
    # Execute the tool with a proper context
    with adapter_ctx.create_tool_context() as ctx:
        try:
            # Call the tool function
            result = tool_func(ctx, **params)
            
            # Log success
            logger.info(f"Tool {tool_name} executed successfully")
            logger.debug(f"Tool {tool_name} result: {result}")
            
            return {"result": result}
        except Exception as e:
            # Log and raise a structured error
            logger.error(f"Error executing tool {tool_name}: {e}")
            logger.debug(traceback.format_exc())
            
            raise ToolExecutionError(
                tool_name,
                str(e),
                {
                    "exception_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )


def handle_tool_calls(
    adapter_ctx: AdapterContext,
    tool_calls: list
) -> Dict[str, Any]:
    """
    Handle a list of tool calls from OpenAI.
    
    This function processes a list of tool calls from an OpenAI response,
    executing each tool and returning the results.
    
    Args:
        adapter_ctx: Adapter context for tool execution
        tool_calls: List of tool calls from OpenAI
        
    Returns:
        Dictionary mapping tool call IDs to their results
    """
    results = {}
    
    for tool_call in tool_calls:
        if tool_call.type == 'function':
            call_id = tool_call.id
            function_name = tool_call.function.name
            
            try:
                # Parse arguments
                try:
                    function_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError as e:
                    # Handle invalid JSON
                    raise ToolExecutionError(
                        function_name,
                        f"Invalid JSON arguments: {e}",
                        {"raw_arguments": tool_call.function.arguments}
                    )
                
                # Execute the tool
                result = execute_tool(adapter_ctx, function_name, function_args)
                results[call_id] = result.get("result", "")
                
            except ToolExecutionError as e:
                # Return the error as the result
                error_response = e.to_response()
                logger.warning(f"Tool execution error: {error_response}")
                results[call_id] = f"Error: {e.error}"
    
    return results 