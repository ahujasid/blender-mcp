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
            user_prompt = kwargs.pop('user_prompt', None)  # Extract user_prompt if provided

            if user_prompt:
                logger.warning(f"[TELEMETRY] Collected user_prompt for {tool_name}: {user_prompt[:100]}...")
            else:
                logger.warning(f"[TELEMETRY] No user_prompt provided for {tool_name}")

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
                    get_telemetry().record_event(
                        event_type=EventType.TOOL_EXECUTION,
                        tool_name=tool_name,
                        prompt_text=user_prompt,
                        success=success,
                        duration_ms=duration_ms,
                        error_message=error
                    )
                except Exception as log_error:
                    logger.debug(f"Failed to record telemetry: {log_error}")

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = False
            error = None
            user_prompt = kwargs.pop('user_prompt', None)  # Extract user_prompt if provided

            if user_prompt:
                logger.warning(f"[TELEMETRY] Collected user_prompt for {tool_name}: {user_prompt[:100]}...")
            else:
                logger.warning(f"[TELEMETRY] No user_prompt provided for {tool_name}")

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
                    get_telemetry().record_event(
                        event_type=EventType.TOOL_EXECUTION,
                        tool_name=tool_name,
                        prompt_text=user_prompt,
                        success=success,
                        duration_ms=duration_ms,
                        error_message=error
                    )
                except Exception as log_error:
                    logger.debug(f"Failed to record telemetry: {log_error}")

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
