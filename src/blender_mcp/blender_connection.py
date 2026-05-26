from __future__ import annotations

import json
import logging
import socket
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("blender-mcp-connection")

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876


@dataclass
class BlenderConnection:
    host: str
    port: int
    sock: socket.socket | None = None  # 'sock' avoids naming conflict with module name

    def connect(self) -> bool:
        """Connect to the Blender addon socket server."""
        if self.sock:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info("Connected to Blender at %s:%s", self.host, self.port)
            return True
        except Exception as e:
            logger.error("Failed to connect to Blender: %s", str(e))
            self.sock = None
            return False

    def disconnect(self) -> None:
        """Disconnect from the Blender addon."""
        if not self.sock:
            return
        try:
            self.sock.close()
        except Exception as e:
            logger.error("Error disconnecting from Blender: %s", str(e))
        finally:
            self.sock = None

    def receive_full_response(self, sock: socket.socket, buffer_size: int = 8192) -> bytes:
        """Receive a complete JSON response, potentially in multiple chunks."""
        chunks: list[bytes] = []
        sock.settimeout(180.0)

        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        if not chunks:
                            raise Exception("Connection closed before receiving any data")
                        break

                    chunks.append(chunk)

                    try:
                        data = b"".join(chunks)
                        json.loads(data.decode("utf-8"))
                        logger.info("Received complete response (%d bytes)", len(data))
                        return data
                    except json.JSONDecodeError:
                        continue
                except socket.timeout:
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error("Socket connection error during receive: %s", str(e))
                    raise
        except socket.timeout:
            logger.warning("Socket timeout during chunked receive")
        except Exception as e:
            logger.error("Error during receive: %s", str(e))
            raise

        if not chunks:
            raise Exception("No data received")

        data = b"".join(chunks)
        logger.info("Returning data after receive completion (%d bytes)", len(data))
        try:
            json.loads(data.decode("utf-8"))
            return data
        except json.JSONDecodeError:
            raise Exception("Incomplete JSON response received")

    def send_command(self, command_type: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a command to Blender and return the response 'result' dict."""
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Blender")

        command = {"type": command_type, "params": params or {}}

        try:
            logger.info("Sending command: %s params=%s", command_type, params)
            self.sock.sendall(json.dumps(command).encode("utf-8"))
            self.sock.settimeout(180.0)
            response_data = self.receive_full_response(self.sock)
            response = json.loads(response_data.decode("utf-8"))

            if response.get("status") == "error":
                raise Exception(response.get("message", "Unknown error from Blender"))

            return response.get("result", {})
        except socket.timeout:
            logger.error("Socket timeout while waiting for response from Blender")
            self.sock = None
            raise Exception("Timeout waiting for Blender response - try simplifying your request")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error("Socket connection error: %s", str(e))
            self.sock = None
            raise Exception(f"Connection to Blender lost: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON response from Blender: %s", str(e))
            raise Exception(f"Invalid response from Blender: {str(e)}")
        except Exception as e:
            logger.error("Error communicating with Blender: %s", str(e))
            self.sock = None
            raise Exception(f"Communication error with Blender: {str(e)}")

