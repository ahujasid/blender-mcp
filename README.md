

# BlenderMCP - Blender Model Context Protocol Integration

BlenderMCP connects Blender to Claude AI through the Model Context Protocol (MCP).
This fork is **refocused on STL print-prep**: take an AI-generated STL (e.g. from
Meshy), inspect and repair it in Blender, then export a print-ready file for a
slicer. It does not cover modeling from scratch, materials, rendering, or
animation. For domain knowledge about mesh repair and FDM constraints the fork
ships a second MCP server (`blender-kb`) backed by the `Bible/` knowledge base.

**We have no official website. Any website you see online is unofficial and has no affiliation with this project. Use them at your own risk.**

### Join the Community

Give feedback, get inspired, and build on top of the MCP: [Discord](https://discord.gg/z5apgR8TFU)

### Supporters

[CodeRabbit](https://www.coderabbit.ai/)

**All supporters:**

[Support this project](https://github.com/sponsors/ahujasid)

## Current version (1.6.0 — print-prep refocus)

This fork removed the Polyhaven / Sketchfab / Hyper3D Rodin / Hunyuan3D
asset-generation tools to focus on the STL cleanup workflow. The MCP server
now exposes 7 tools and one prompt (`print_prep_strategy`).

### Migrating from upstream
- Reinstall the addon: download `addon.py` from this fork and replace your old
  install in Blender. The sidebar no longer shows Polyhaven/Sketchfab/Hyper3D
  checkboxes — only the port and the Connect/Disconnect buttons.
- Re-add the MCP server in your client config (no change needed if you already
  use `uvx blender-mcp`).
- If you want the Bible knowledge base, also register the `blender-kb` server
  (see `Bible/KB_SERVER.md`).

## Features

- **Two-way communication**: socket-based connection between Claude and Blender
- **STL import / export**: `import_stl`, `export_stl` wrappers compatible with
  Blender 3.x and 4.x operators
- **Structured print-readiness check**: `analyze_mesh_for_print` returns JSON
  (watertight, non-manifold edges, hole loops, shell count, inverted normals,
  dimensions in mm, ready_to_slice flag) so the LLM doesn't have to parse
  free-text
- **Scene inspection**: `get_scene_info`, `get_object_info`, viewport screenshot
- **Arbitrary Python**: `execute_blender_code` for anything the dedicated tools
  don't cover (bmesh ops, modifiers, boolean cuts, supports)
- **Print-prep prompt**: `print_prep_strategy` walks the assistant through
  import → analyze → consult KB → cleanup → re-analyze → export

## Components

1. **Blender Addon (`addon.py`)**: socket server inside Blender that executes
   the print-prep handlers on the main thread
2. **MCP Server (`src/blender_mcp/server.py`)**: FastMCP server that exposes the
   handlers as MCP tools
3. **Knowledge Base MCP Server (`src/blender_kb/server.py`)**: optional second
   MCP server that serves the `Bible/` docs on demand. See `Bible/KB_SERVER.md`.

## Installation


### Prerequisites

- Blender 3.0 or newer
- Python 3.10 or newer
- uv package manager: 

**If you're on Mac, please install uv as**
```bash
brew install uv
```
**On Windows**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex" 
```
and then add uv to the user path in Windows (you may need to restart Claude Desktop after):
```powershell
$localBin = "$env:USERPROFILE\.local\bin"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$userPath;$localBin", "User")
```

Otherwise installation instructions are on their website: [Install uv](https://docs.astral.sh/uv/getting-started/installation/)

**⚠️ Do not proceed before installing UV**

### Environment Variables

The following environment variables can be used to configure the Blender connection:

- `BLENDER_HOST`: Host address for Blender socket server (default: "localhost")
- `BLENDER_PORT`: Port number for Blender socket server (default: 9876)

Example:
```bash
export BLENDER_HOST='host.docker.internal'
export BLENDER_PORT=9876
```

### Claude for Desktop Integration

[Watch the setup instruction video](https://www.youtube.com/watch?v=neoK_WMq92g) (Assuming you have already installed uv)

Go to Claude > Settings > Developer > Edit Config > claude_desktop_config.json to include the following:

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": [
                "blender-mcp"
            ]
        }
    }
}
```
<details>
<summary>Claude Code</summary>

Use the Claude Code CLI to add the blender MCP server:

```bash
claude mcp add blender uvx blender-mcp
```
</details>

### Cursor integration

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/link/mcp%2Finstall?name=blender&config=eyJjb21tYW5kIjoidXZ4IGJsZW5kZXItbWNwIn0%3D)

For Mac users, go to Settings > MCP and paste the following 

- To use as a global server, use "add new global MCP server" button and paste
- To use as a project specific server, create `.cursor/mcp.json` in the root of the project and paste


```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": [
                "blender-mcp"
            ]
        }
    }
}
```

For Windows users, go to Settings > MCP > Add Server, add a new server with the following settings:

```json
{
    "mcpServers": {
        "blender": {
            "command": "cmd",
            "args": [
                "/c",
                "uvx",
                "blender-mcp"
            ]
        }
    }
}
```

[Cursor setup video](https://www.youtube.com/watch?v=wgWsJshecac)

**⚠️ Only run one instance of the MCP server (either on Cursor or Claude Desktop), not both**

### Visual Studio Code Integration

_Prerequisites_: Make sure you have [Visual Studio Code](https://code.visualstudio.com/) installed before proceeding.

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_blender--mcp_server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=ffffff)](vscode:mcp/install?%7B%22name%22%3A%22blender-mcp%22%2C%22type%22%3A%22stdio%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22blender-mcp%22%5D%7D)

### Installing the Blender Addon

1. Download the `addon.py` file from this repo
1. Open Blender
2. Go to Edit > Preferences > Add-ons
3. Click "Install..." and select the `addon.py` file
4. Enable the addon by checking the box next to "Interface: Blender MCP"


## Usage

### Starting the Connection
![BlenderMCP in the sidebar](assets/addon-instructions.png)

1. In Blender, go to the 3D View sidebar (press N if not visible)
2. Find the "BlenderMCP" tab
3. Click "Connect to MCP server"
4. Make sure the MCP server is running in your client (Claude Desktop / Cursor / VS Code)

### Using with Claude

Once the config file has been set on Claude, and the addon is running on Blender, you will see a hammer icon with tools for the Blender MCP.

![BlenderMCP in the sidebar](assets/hammer-icon.png)

#### Capabilities

Tools exposed by `blender-mcp`:

| Tool | What it does |
| --- | --- |
| `get_scene_info` | Scene name, object list (first 10), unit system, scale length |
| `get_object_info` | Per-object data: type, transform, materials, mesh counts, world bounding box, dimensions in mm |
| `get_viewport_screenshot` | PNG of the active 3D viewport (auto-resized to `max_size`) |
| `execute_blender_code` | Run arbitrary Python inside Blender's main thread |
| `import_stl` | Import an STL, report verts/edges/faces and dimensions in mm |
| `export_stl` | Export a single mesh to STL (`apply_modifiers=True` by default) |
| `analyze_mesh_for_print` | Structured JSON: watertight, non-manifold edges, boundary loops, shells, degenerate faces, normals consistency, signed volume, `ready_to_slice` |

Prompt:
- `print_prep_strategy` — guides the assistant through the full STL cleanup
  pipeline and points it at `blender-kb` topics for recipes.

### Example commands

- "Import `~/meshy/dragon.stl`, analyze it, and tell me what's broken"
- "The model has 17 non-manifold edges and 3 hole loops — fix them"
- "Orient this part so the largest flat face is on the build plate"
- "Decimate this mesh to ~50k triangles while keeping the silhouette"
- "Run a final analyze_mesh_for_print and export to `out/dragon_clean.stl`"

## Troubleshooting

- **Connection issues**: Make sure the Blender addon server is running (you should see the green "Disconnect from MCP server" button in the BlenderMCP sidebar). Do NOT run `uvx blender-mcp` manually in a terminal — your MCP client launches it.
- **Timeout errors**: Break the request into smaller `execute_blender_code` chunks. Long-running bmesh ops can exceed the 180s socket timeout.
- **STL import operator missing**: Blender 4.x uses `bpy.ops.wm.stl_import`, 3.x uses `bpy.ops.import_mesh.stl`. The addon picks the right one automatically. If both are missing your Blender build is broken.
- **Have you tried turning it off and on again?**: Restart both the MCP client and the Blender server on persistent issues.


## Technical Details

### Communication Protocol

The system uses a simple JSON-based protocol over TCP sockets:

- **Commands** are sent as JSON objects with a `type` and optional `params`
- **Responses** are JSON objects with a `status` and `result` or `message`

## Limitations & Security Considerations

- The `execute_blender_code` tool allows running arbitrary Python code in Blender, which can be powerful but potentially dangerous. Use with caution in production environments. ALWAYS save your work before using it.
- `import_stl` and `export_stl` take absolute filesystem paths. They do not sandbox; treat the MCP server as having the same filesystem access as the user running Blender.
- Complex operations might need to be broken down into smaller steps.


#### Telemetry Control

BlenderMCP collects anonymous usage data to help improve the tool. You can control telemetry in two ways:

1. **In Blender**: Go to Edit > Preferences > Add-ons > Blender MCP and uncheck the telemetry consent checkbox
   - With consent (checked): Collects anonymized prompts, code snippets, and screenshots
   - Without consent (unchecked): Only collects minimal anonymous usage data (tool names, success/failure, duration)

2. **Environment Variable**: Completely disable all telemetry by running:
```bash
DISABLE_TELEMETRY=true uvx blender-mcp
```

Or add it to your MCP config:
```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": ["blender-mcp"],
            "env": {
                "DISABLE_TELEMETRY": "true"
            }
        }
    }
}
```

All telemetry data is fully anonymized and used solely to improve BlenderMCP.


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This is a third-party integration and not made by Blender. Made by [Siddharth](https://x.com/sidahuj)
