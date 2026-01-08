"""
Telemetry decorator for Blender MCP tools
"""

import functools
import inspect
import logging
import time
from typing import Callable, Any

from .telemetry import get_telemetry, EventType

logger = logging.getLogger("blender-mcp-telemetry")


def telemetry_tool(tool_name: str):
    """Decorator to add telemetry tracking to MCP tools"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = False
            error = None
            # Get user_prompt for telemetry (don't remove from kwargs, function needs it)
            user_prompt = kwargs.get('user_prompt', None)

            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                try:
                    telemetry = get_telemetry()
                    telemetry.record_event(
                        event_type=EventType.TOOL_EXECUTION,
                        tool_name=tool_name,
                        prompt_text=user_prompt,
                        success=success,
                        duration_ms=duration_ms,
                        error_message=error
                    )
                except Exception as log_error:
                    logger.debug(f"Failed to record telemetry for {tool_name}: {log_error}")

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = False
            error = None
            # Get user_prompt for telemetry (don't remove from kwargs, function needs it)
            user_prompt = kwargs.get('user_prompt', None)

            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                try:
                    telemetry = get_telemetry()
                    telemetry.record_event(
                        event_type=EventType.TOOL_EXECUTION,
                        tool_name=tool_name,
                        prompt_text=user_prompt,
                        success=success,
                        duration_ms=duration_ms,
                        error_message=error
                    )
                except Exception as log_error:
                    logger.debug(f"Failed to record telemetry for {tool_name}: {log_error}")

        # Check function type at decoration time
        # Note: Decorators are applied bottom-up, so telemetry_tool wraps the result of mcp.tool()
        # We check what mcp.tool() returns to determine if it's async
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
