"""
Context management for BlenderMCP OpenAI adapter.

This module handles the creation and management of context objects
for BlenderMCP tools. It ensures that tools receive proper context objects
rather than empty mocks.
"""

import uuid
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from .logging_utils import logger


class AdapterContext:
    """
    Context wrapper that adapts between OpenAI and MCP contexts.
    
    This class provides a bridge between the OpenAI function calling paradigm
    and the Context objects expected by MCP tools. It handles context creation,
    session tracking, and resource cleanup.
    
    Attributes:
        mcp_server: Reference to the MCP server module
        session_id: Unique identifier for this session
        state: Dictionary to store session state
    """
    
    def __init__(self, mcp_server, session_id: Optional[str] = None):
        """
        Initialize the adapter context.
        
        Args:
            mcp_server: Reference to the MCP server module
            session_id: Optional session ID (generated if not provided)
        """
        self.mcp_server = mcp_server
        self.session_id = session_id or str(uuid.uuid4())
        self.state = {}
        logger.info(f"Initialized adapter context with session ID: {self.session_id}")
    
    @contextmanager
    def create_tool_context(self) -> Iterator[Any]:
        """
        Create a proper context object for MCP tools.
        
        This context manager creates a real context object for MCP tools
        instead of an empty mock. It also handles proper cleanup of resources
        when the context is exited.
        
        Yields:
            A proper context object for MCP tools
        """
        # Check if the MCP server has a context creation method
        if hasattr(self.mcp_server, "create_context"):
            try:
                # Create a real FastMCP Context
                ctx = self.mcp_server.create_context(self.session_id)
                logger.debug(f"Created real context for session {self.session_id}")
                yield ctx
            finally:
                # Clean up context resources if needed
                if hasattr(ctx, "close") and callable(ctx.close):
                    ctx.close()
                    logger.debug(f"Closed context for session {self.session_id}")
        else:
            # Fallback to a mock context if create_context is not available
            class MockContext:
                """Mock context with session information."""
                def __init__(self, session_id: str, state: Dict[str, Any]):
                    self.session_id = session_id
                    self.state = state
            
            logger.warning("Creating mock context - MCP server does not support create_context")
            yield MockContext(self.session_id, self.state)
    
    def update_state(self, key: str, value: Any) -> None:
        """
        Update the session state.
        
        Args:
            key: State key to update
            value: New value for the key
        """
        self.state[key] = value
        logger.debug(f"Updated state: {key}={value}")
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the session state.
        
        Args:
            key: State key to retrieve
            default: Default value if key is not found
            
        Returns:
            The state value or default if not found
        """
        return self.state.get(key, default) 