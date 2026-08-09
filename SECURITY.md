# Security

## Overview

Blender MCP links an AI client to Blender over a local TCP socket and can call third-party 3D APIs with keys the user configures.

## Recommendations

- Keep API keys in addon preferences (password fields) or environment variables; avoid storing them in `.blend` files.
- Treat `execute_blender_code` as full access to the Blender process.
- The control socket should stay on localhost.
- Optional usage telemetry can be disabled with `BLENDER_MCP_DISABLE_TELEMETRY=1` or the addon privacy checkbox.

## Reporting

Please report security issues privately to the maintainers. Do not post live credentials in public issues.
