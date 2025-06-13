"""
Schema utilities for BlenderMCP OpenAI adapter.

This module handles extraction of JSON schemas from Python functions,
particularly for converting MCP tool signatures to OpenAI function schemas.
"""

import inspect
import typing
from typing import Dict, Any, List, Optional, Union, get_type_hints, get_origin, get_args
import docstring_parser

from .logging_utils import logger


def extract_schema(func) -> Dict[str, Any]:
    """
    Extract a JSON schema from a function signature using type hints.
    
    This function analyzes the signature and docstring of a function to
    generate a JSON schema for use with OpenAI function calling. It uses
    type hints, default values, and docstring information to build a
    comprehensive schema.
    
    Args:
        func: The function to extract a schema from
        
    Returns:
        A JSON schema object compatible with OpenAI function calling
    """
    # Get type hints and signature
    try:
        hints = get_type_hints(func)
    except (TypeError, NameError):
        # If we can't get type hints, use an empty dict
        hints = {}
    
    sig = inspect.signature(func)
    
    # Skip the first parameter which is typically 'ctx' or 'self'
    parameters = list(sig.parameters.items())[1:]
    
    # Parse docstring for parameter descriptions
    docstring = func.__doc__ or ""
    parsed_docstring = docstring_parser.parse(docstring)
    param_docs = {param.arg_name: param.description for param in parsed_docstring.params}
    
    # Create the schema object
    schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    # Process each parameter
    for name, param in parameters:
        # Check if parameter is required
        if param.default == inspect.Parameter.empty:
            schema["required"].append(name)
            
        # Get parameter schema based on type hint
        if name in hints:
            param_schema = _type_to_schema(hints[name])
        else:
            # Default to string if no type hint
            param_schema = {"type": "string"}
            
        # Add description from docstring if available
        if name in param_docs and param_docs[name]:
            param_schema["description"] = param_docs[name]
            
        # Add default value if available and compatible with JSON
        if param.default != inspect.Parameter.empty:
            try:
                # Only add if JSON serializable
                if param.default is not None and not callable(param.default):
                    param_schema["default"] = param.default
            except (TypeError, ValueError):
                pass
            
        schema["properties"][name] = param_schema
    
    # If no required parameters, remove the required field
    if not schema["required"]:
        schema.pop("required")
        
    logger.debug(f"Extracted schema for function {func.__name__}: {schema}")
    return schema


def _type_to_schema(typ) -> Dict[str, Any]:
    """
    Convert a Python type to a JSON schema.
    
    This function handles conversion of Python types to their JSON schema
    equivalents, including handling of generics, unions, and nested types.
    
    Args:
        typ: The Python type to convert
        
    Returns:
        A JSON schema representation of the type
    """
    # Handle basic types
    if typ == str:
        return {"type": "string"}
    elif typ == int:
        return {"type": "integer"}
    elif typ == float:
        return {"type": "number"}
    elif typ == bool:
        return {"type": "boolean"}
    elif typ == dict or typ == Dict:
        return {"type": "object"}
    elif typ == list or typ == List:
        return {"type": "array"}
    elif typ == None or typ == type(None):
        return {"type": "null"}
        
    # Handle typing.List with item type
    origin = get_origin(typ)
    if origin == list or origin == List:
        args = get_args(typ)
        item_type = args[0] if args else Any
        return {
            "type": "array",
            "items": _type_to_schema(item_type)
        }
        
    # Handle typing.Dict with key/value types
    if origin == dict or origin == Dict:
        args = get_args(typ)
        if args and args[0] == str:  # Only handle string keys
            value_type = args[1] if len(args) > 1 else Any
            return {
                "type": "object",
                "additionalProperties": _type_to_schema(value_type)
            }
        return {"type": "object"}
        
    # Handle typing.Optional as Union[T, None]
    if origin == Union:
        args = get_args(typ)
        # Check if it's Optional[T] (Union[T, None])
        if len(args) == 2 and (args[1] == type(None) or args[1] == None):
            schema = _type_to_schema(args[0])
            # Add "null" to the type if it's a string type
            if isinstance(schema.get("type"), str):
                schema["type"] = [schema["type"], "null"]
            return schema
            
        # Handle general unions as oneOf
        return {
            "oneOf": [_type_to_schema(arg) for arg in args]
        }
        
    # Default to string for unknown types
    return {"type": "string"}


def extract_tools_schema(mcp_tools: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract OpenAI function schemas from MCP tools.
    
    This function processes a dictionary of MCP tools and converts them
    to OpenAI function schemas for use with the ChatCompletion API.
    
    Args:
        mcp_tools: Dictionary of MCP tools from the server
        
    Returns:
        List of OpenAI function schemas
    """
    tools = []
    
    for tool_name, tool_func in mcp_tools.items():
        # Get the docstring for the function description
        doc = tool_func.__doc__ or ""
        parsed_doc = docstring_parser.parse(doc)
        description = parsed_doc.short_description or f"Tool: {tool_name}"
        
        # Create an OpenAI-compatible tool definition
        tool = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": extract_schema(tool_func)
            }
        }
        tools.append(tool)
        
    logger.info(f"Extracted schemas for {len(tools)} tools")
    return tools 