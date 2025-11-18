#!/usr/bin/env python3
"""
Connectivity check for the configured vLLM endpoint.

Executes the same health-check logic used by the MCP server and exits with a
non-zero status code when the endpoint is unreachable.
"""

import json
import logging
import sys
from typing import Optional

from blender_mcp.server import _default_vllm_endpoint, _ensure_vllm_reachable


def main(endpoint: Optional[str] = None) -> int:
    logging.basicConfig(level=logging.INFO)
    target = endpoint or _default_vllm_endpoint()
    result = _ensure_vllm_reachable(target, force=True)
    print(json.dumps(result, indent=2))
    return 0 if result.get("reachable") else 1


if __name__ == "__main__":
    endpoint_arg = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(main(endpoint_arg))
