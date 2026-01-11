"""
Privacy-focused, anonymous telemetry for Blender MCP
Tracks tool usage, DAU/MAU, and performance metrics
"""

import contextlib
import json
import logging
import os
import platform
import queue
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

try:
    import tomli
except ImportError:
    try:
        import tomllib as tomli
    except ImportError:
        tomli = None

logger = logging.getLogger("blender-mcp-telemetry")


def get_package_version() -> str:
    """Get version from pyproject.toml"""
    try:
        pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            if tomli:
                with open(pyproject_path, "rb") as f:
                    data = tomli.load(f)
                    return data["project"]["version"]
    except Exception:
        pass
    return "unknown"


MCP_VERSION = get_package_version()


class EventType(str, Enum):
    """Types of telemetry events"""
    STARTUP = "startup"
    TOOL_EXECUTION = "tool_execution"
    PROMPT_SENT = "prompt_sent"
    CONNECTION = "connection"
    ERROR = "error"


@dataclass
class TelemetryEvent:
    """Structure for telemetry events"""
    event_type: EventType
    customer_uuid: str
    session_id: str
    timestamp: float
    version: str
    platform: str

    # Optional fields
    tool_name: str | None = None
    prompt_text: str | None = None
    success: bool = True
    duration_ms: float | None = None
    error_message: str | None = None
    blender_version: str | None = None
    metadata: dict[str, Any] | None = None


class TelemetryCollector:
    """Main telemetry collection class"""

    def __init__(self):
        """Initialize telemetry collector"""
        # Import config here to avoid circular imports
        from .config import telemetry_config
        self.config = telemetry_config

        # Check if disabled via environment variables
        if self._is_disabled():
            self.config.enabled = False
            logger.warning("Telemetry disabled via environment variable")

        # Generate or load customer UUID
        self._customer_uuid: str = self._get_or_create_uuid()
        self._session_id: str = str(uuid.uuid4())

        # Rate limiting tracking
        self._event_timestamps: list[float] = []
        self._rate_limit_lock = threading.Lock()

        # Background queue and worker
        self._queue: "queue.Queue[TelemetryEvent]" = queue.Queue(maxsize=1000)
        self._worker: threading.Thread = threading.Thread(
            target=self._worker_loop, daemon=True
        )
        self._worker.start()

        logger.warning(f"Telemetry initialized (enabled={self.config.enabled}, has_supabase={HAS_SUPABASE}, customer_uuid={self._customer_uuid})")

    def _is_disabled(self) -> bool:
        """Check if telemetry is disabled via environment variables"""
        disable_vars = [
            "DISABLE_TELEMETRY",
            "BLENDER_MCP_DISABLE_TELEMETRY",
            "MCP_DISABLE_TELEMETRY"
        ]

        for var in disable_vars:
            if os.environ.get(var, "").lower() in ("true", "1", "yes", "on"):
                return True
        return False

    def _get_data_directory(self) -> Path:
        """Get directory for storing telemetry data"""
        if sys.platform == "win32":
            base_dir = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        elif sys.platform == "darwin":
            base_dir = Path.home() / 'Library' / 'Application Support'
        else:  # Linux
            base_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))

        data_dir = base_dir / 'BlenderMCP'
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def _get_or_create_uuid(self) -> str:
        """Get or create anonymous customer UUID"""
        try:
            data_dir = self._get_data_directory()
            uuid_file = data_dir / "customer_uuid.txt"

            if uuid_file.exists():
                customer_uuid = uuid_file.read_text(encoding="utf-8").strip()
                if customer_uuid:
                    return customer_uuid

            # Create new UUID
            customer_uuid = str(uuid.uuid4())
            uuid_file.write_text(customer_uuid, encoding="utf-8")

            # Set restrictive permissions on Unix
            if sys.platform != "win32":
                os.chmod(uuid_file, 0o600)

            return customer_uuid
        except Exception as e:
            logger.debug(f"Failed to persist UUID: {e}")
            return str(uuid.uuid4())

    def record_event(
        self,
        event_type: EventType,
        tool_name: str | None = None,
        prompt_text: str | None = None,
        success: bool = True,
        duration_ms: float | None = None,
        error_message: str | None = None,
        blender_version: str | None = None,
        metadata: dict[str, Any] | None = None
    ):
        """Record a telemetry event (non-blocking)"""
        if not self.config.enabled:
            logger.warning(f"Telemetry disabled, skipping event: {event_type}")
            return
        if not HAS_SUPABASE:
            logger.warning(f"Supabase not available, skipping event: {event_type}")
            return

        logger.warning(f"Recording telemetry event: {event_type}, tool={tool_name}")

        # Truncate prompt if needed
        if prompt_text and not self.config.collect_prompts:
            prompt_text = None  # Don't collect prompts unless explicitly enabled
        elif prompt_text and len(prompt_text) > self.config.max_prompt_length:
            prompt_text = prompt_text[:self.config.max_prompt_length] + "..."

        # Truncate error messages
        if error_message and len(error_message) > 200:
            error_message = error_message[:200] + "..."

        event = TelemetryEvent(
            event_type=event_type,
            customer_uuid=self._customer_uuid,
            session_id=self._session_id,
            timestamp=time.time(),
            version=MCP_VERSION,
            platform=platform.system().lower(),
            tool_name=tool_name,
            prompt_text=prompt_text,
            success=success,
            duration_ms=duration_ms,
            error_message=error_message,
            blender_version=blender_version,
            metadata=metadata
        )

        # Enqueue for background worker
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            logger.debug("Telemetry queue full, dropping event")

    def _worker_loop(self):
        """Background worker that sends telemetry"""
        while True:
            event = self._queue.get()
            try:
                self._send_event(event)
            except Exception as e:
                logger.debug(f"Telemetry send failed: {e}")
            finally:
                with contextlib.suppress(Exception):
                    self._queue.task_done()

    def _send_event(self, event: TelemetryEvent):
        """Send event to Supabase"""
        if not HAS_SUPABASE:
            return

        try:
            # Create Supabase client with explicit options
            from supabase import ClientOptions

            options = ClientOptions(
                auto_refresh_token=False,
                persist_session=False
            )

            supabase: Client = create_client(
                self.config.supabase_url,
                self.config.supabase_anon_key,
                options=options
            )

            # Prepare data for insertion
            data = {
                "customer_uuid": event.customer_uuid,
                "session_id": event.session_id,
                "event_type": event.event_type.value,
                "tool_name": event.tool_name,
                "prompt_text": event.prompt_text,
                "success": event.success,
                "duration_ms": event.duration_ms,
                "error_message": event.error_message,
                "version": event.version,
                "platform": event.platform,
                "blender_version": event.blender_version,
                "metadata": event.metadata or {},
                "event_timestamp": int(event.timestamp),
            }

            response = supabase.table("telemetry_events").insert(data, returning="minimal").execute()
            logger.debug(f"Telemetry sent: {event.event_type}")

        except Exception as e:
            logger.debug(f"Failed to send telemetry: {e}")


# Global telemetry instance
_telemetry_collector: TelemetryCollector | None = None


def get_telemetry() -> TelemetryCollector:
    """Get the global telemetry collector instance"""
    global _telemetry_collector
    if _telemetry_collector is None:
        _telemetry_collector = TelemetryCollector()
    return _telemetry_collector


def record_tool_usage(
    tool_name: str,
    success: bool,
    duration_ms: float,
    error: str | None = None
):
    """Convenience function to record tool usage"""
    get_telemetry().record_event(
        event_type=EventType.TOOL_EXECUTION,
        tool_name=tool_name,
        success=success,
        duration_ms=duration_ms,
        error_message=error
    )


def record_startup(blender_version: str | None = None):
    """Record server startup event"""
    get_telemetry().record_event(
        event_type=EventType.STARTUP,
        blender_version=blender_version
    )


def is_telemetry_enabled() -> bool:
    """Check if telemetry is enabled"""
    try:
        return get_telemetry().config.enabled
    except Exception:
        return False
