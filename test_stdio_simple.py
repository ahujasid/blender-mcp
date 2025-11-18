#!/usr/bin/env python3
"""
Simple test for Blender MCP stdio server.
Sends MCP requests to stdin, reads responses from stdout.
"""

import json
import subprocess
import sys
import os
from pathlib import Path

# Detect Blender executable
def detect_blender():
    """Detect Blender installation"""
    # Check if .blender.env exists
    env_file = Path(__file__).parent.parent / ".blender.env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("BLENDER_EXE="):
                    return line.split("=", 1)[1].strip()

    # Common Windows locations
    if sys.platform == "win32":
        possible_paths = [
            "C:\\Program Files\\Blender Foundation\\Blender 4.3\\blender.exe",
            "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe",
            "C:\\Program Files (x86)\\Blender Foundation\\Blender 4.3\\blender.exe",
        ]
        for path in possible_paths:
            if Path(path).exists():
                return path

    # Try PATH
    import shutil
    blender = shutil.which("blender")
    if blender:
        return blender

    print("❌ Blender not found. Run: bash ../scripts/detect_blender.sh", file=sys.stderr)
    sys.exit(1)


def send_request(proc, request_id: int, method: str, params: dict = None):
    """Send MCP request to Blender"""
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params or {}
    }

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Request {request_id}: {method}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(json.dumps(request, indent=2), file=sys.stderr)

    # Send request
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    # Read response (skip Blender startup noise)
    while True:
        response_line = proc.stdout.readline()
        if response_line == "":
            raise RuntimeError("Blender process terminated unexpectedly")
        stripped = response_line.strip()
        if not stripped:
            continue
        try:
            response = json.loads(stripped)
            break
        except json.JSONDecodeError:
            print(f"[ignored stdout] {stripped}", file=sys.stderr)
            continue

    print(f"\nResponse:", file=sys.stderr)
    print(json.dumps(response, indent=2), file=sys.stderr)

    return response


def main():
    blender_exe = detect_blender()
    script_path = Path(__file__).parent / "blender_mcp_stdio.py"

    print(f"🎨 Testing Blender MCP Stdio Server", file=sys.stderr)
    print(f"Blender: {blender_exe}", file=sys.stderr)
    print(f"Script: {script_path}", file=sys.stderr)
    print("", file=sys.stderr)

    # Start Blender with stdio server
    proc = subprocess.Popen(
        [blender_exe, "--background", "--python", str(script_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    try:
        # Test 1: Initialize
        response = send_request(proc, 1, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })
        assert "result" in response
        assert response["result"]["protocolVersion"] == "2024-11-05"
        print("✅ Test 1: Initialize PASSED", file=sys.stderr)

        # Test 2: List tools
        response = send_request(proc, 2, "tools/list")
        assert "result" in response
        tools = response["result"]["tools"]
        print(f"✅ Test 2: Found {len(tools)} tools", file=sys.stderr)
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}", file=sys.stderr)

        # Test 3: Get scene info
        response = send_request(proc, 3, "tools/call", {
            "name": "get_scene_info",
            "arguments": {}
        })
        assert "result" in response
        content = json.loads(response["result"]["content"][0]["text"])
        print(f"✅ Test 3: Scene has {content['object_count']} objects", file=sys.stderr)

        # Test 4: Execute code
        response = send_request(proc, 4, "tools/call", {
            "name": "execute_code",
            "arguments": {
                "code": "print('Hello from Blender!'); print(f'Version: {bpy.app.version_string}')"
            }
        })
        assert "result" in response
        result = json.loads(response["result"]["content"][0]["text"])
        print(f"✅ Test 4: Code executed: {result['executed']}", file=sys.stderr)
        print(f"   Output: {result.get('output', '(no output)')}", file=sys.stderr)

        # Test 5: List addons
        response = send_request(proc, 5, "tools/call", {
            "name": "list_addons",
            "arguments": {}
        })
        assert "result" in response
        addons = json.loads(response["result"]["content"][0]["text"])
        print(f"✅ Test 5: Found {addons['enabled_count']} enabled addons", file=sys.stderr)

        print("\n" + "="*60, file=sys.stderr)
        print("✅ All tests PASSED!", file=sys.stderr)
        print("="*60, file=sys.stderr)

    except Exception as e:
        print(f"\n❌ Test FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1
    finally:
        proc.terminate()
        proc.wait(timeout=5)

    return 0


if __name__ == "__main__":
    sys.exit(main())
