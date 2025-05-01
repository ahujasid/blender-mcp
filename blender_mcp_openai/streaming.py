"""
Streaming utilities for BlenderMCP OpenAI adapter.

This module handles streaming of responses from OpenAI, including
processing and executing tool calls that appear mid-stream.
"""

import json
from typing import Dict, Any, Iterator, List, Optional, Union

from .logging_utils import logger
from .context import AdapterContext
from .dispatch import handle_tool_calls, ToolExecutionError


class ToolAwareStream:
    """
    Stream handler that can process tool calls mid-stream.
    
    This class wraps an OpenAI streaming response and adds support for
    processing tool calls that appear mid-stream. It buffers tool call data
    until complete, executes the tools, and then continues streaming.
    
    Attributes:
        stream: The OpenAI streaming response
        adapter_ctx: The adapter context for tool execution
        buffer: Buffer for accumulating tool call data
        tool_calls: List of completed tool calls
        current_tool_call: The current tool call being processed
        content_buffer: Buffer for text content
    """
    
    def __init__(self, stream, adapter_ctx: AdapterContext):
        """
        Initialize the stream handler.
        
        Args:
            stream: The OpenAI streaming response
            adapter_ctx: The adapter context for tool execution
        """
        self.stream = stream
        self.adapter_ctx = adapter_ctx
        self.buffer = []
        self.tool_calls = []
        self.current_tool_call = None
        self.content_buffer = []
        
        # Dictionary to store tool calls by ID
        self.tool_call_buffers = {}
        
        logger.debug("Initialized ToolAwareStream")
    
    def __iter__(self) -> Iterator[str]:
        """
        Iterate over the stream, yielding text content and processing tool calls.
        
        This method iterates over the OpenAI streaming response, yielding text
        content as it arrives and processing any tool calls that appear mid-stream.
        After all tool calls are processed, it executes them and continues streaming.
        
        Yields:
            Text content from the stream
        """
        # Flag to track if we're in a tool call
        in_tool_call = False
        
        # Process each chunk in the stream
        for chunk in self.stream:
            # Check if this chunk has a tool call delta
            if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'tool_calls'):
                tool_call_deltas = chunk.choices[0].delta.tool_calls
                if tool_call_deltas:
                    in_tool_call = True
                    self._process_tool_call_deltas(tool_call_deltas)
            # Check if this chunk has text content
            elif not in_tool_call and hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.content:
                # Yield the content directly
                yield chunk.choices[0].delta.content
            
            # Check if we've reached the end of the tool calls
            if hasattr(chunk, 'choices') and chunk.choices[0].finish_reason == 'tool_calls':
                # Execute all tool calls
                tool_results = self._execute_all_tool_calls()
                
                # Yield a message about tool execution
                tools_msg = f"\n[Executing {len(tool_results)} tools...]\n"
                yield tools_msg
                
                # We're done with tool calls for now
                in_tool_call = False
                
                logger.debug("Finished processing tool calls in stream")
    
    def _process_tool_call_deltas(self, tool_call_deltas) -> None:
        """
        Process tool call deltas from a stream chunk.
        
        This method accumulates tool call data from stream deltas, building
        up complete tool calls that can be executed later.
        
        Args:
            tool_call_deltas: List of tool call deltas from the stream
        """
        for delta in tool_call_deltas:
            # Get or create the buffer for this tool call
            tool_call_id = delta.index
            if tool_call_id not in self.tool_call_buffers:
                self.tool_call_buffers[tool_call_id] = {
                    "id": None,
                    "type": None,
                    "function": {
                        "name": "",
                        "arguments": ""
                    }
                }
            
            # Update the buffer with this delta
            buffer = self.tool_call_buffers[tool_call_id]
            
            # Update ID and type if provided
            if hasattr(delta, 'id') and delta.id:
                buffer["id"] = delta.id
            if hasattr(delta, 'type') and delta.type:
                buffer["type"] = delta.type
            
            # Update function name and arguments if provided
            if hasattr(delta, 'function'):
                if hasattr(delta.function, 'name') and delta.function.name:
                    buffer["function"]["name"] += delta.function.name
                if hasattr(delta.function, 'arguments') and delta.function.arguments:
                    buffer["function"]["arguments"] += delta.function.arguments
            
            logger.debug(f"Updated tool call buffer for ID {tool_call_id}: {buffer}")
    
    def _execute_all_tool_calls(self) -> Dict[str, Any]:
        """
        Execute all accumulated tool calls.
        
        This method converts the buffered tool call data into a format suitable
        for execution, executes the tools, and returns the results.
        
        Returns:
            Dictionary mapping tool call IDs to their results
        """
        if not self.tool_call_buffers:
            return {}
        
        # Convert buffers to a format suitable for handle_tool_calls
        tool_calls = []
        for tool_call_id, buffer in self.tool_call_buffers.items():
            # Create a simple object with the necessary attributes
            class ToolCall:
                def __init__(self, id, type, function_name, function_arguments):
                    self.id = id
                    self.type = type
                    self.function = type('', (), {})()
                    self.function.name = function_name
                    self.function.arguments = function_arguments
            
            tool_call = ToolCall(
                buffer["id"],
                buffer["type"],
                buffer["function"]["name"],
                buffer["function"]["arguments"]
            )
            tool_calls.append(tool_call)
        
        # Execute the tool calls
        logger.info(f"Executing {len(tool_calls)} tool calls")
        results = handle_tool_calls(self.adapter_ctx, tool_calls)
        
        # Clear the buffers for the next round
        self.tool_call_buffers = {}
        
        return results 