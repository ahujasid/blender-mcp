
> **BMA Benchmark Fork** — This is `blender-mcp-bma`, a fork of upstream
> [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) maintained
> for the [BMA_Bench](https://github.com/yourorg/BMA_Bench) project.
> It adds tool-gating profiles, benchmark-safe `bma_*` tools, telemetry-off
> defaults, and headless mode. It is **not intended for general use** outside
> BMA_Bench. For the unmodified upstream server, see the original repo.
>
> Branch: `bma-benchmark-profile-support` | Patch marker: `# BMA_PATCH`

---

# BlenderMCP - Blender Model Context Protocol Integration

BlenderMCP connects Blender to Claude AI through the Model Context Protocol (MCP), allowing Claude to directly interact with and control Blender. This integration enables prompt assisted 3D modeling, scene creation, and manipulation.

**We have no official website. Any website you see online is unofficial and has no affiliation with this project. Use them at your own risk.**

[Full tutorial](https://www.youtube.com/watch?v=lCyQ717DuzQ)

### Join the Community

Give feedback, get inspired, and build on top of the MCP: [Discord](https://discord.gg/z5apgR8TFU)

### Supporters

[CodeRabbit](https://www.coderabbit.ai/)

**All supporters:**

[Support this project](https://github.com/sponsors/ahujasid)

## Current version(1.5.5)
- Added Hunyuan3D support
- View screenshots for Blender viewport to better understand the scene
- Search and download Sketchfab models
- Support for Poly Haven assets through their API
- Support to generate 3D models using Hyper3D Rodin
- Run Blender MCP on a remote host
- Telemetry for tools executed (completely anonymous)

### Installating a new version (existing users)
- For newcomers, you can go straight to Installation. For existing users, see the points below
- Download the latest addon.py file and replace the older one, then add it to Blender
- Delete the MCP server from Claude and add it back again, and you should be good to go!


## Features

- **Two-way communication**: Connect Claude AI to Blender through a socket-based server
- **Object manipulation**: Create, modify, and delete 3D objects in Blender
- **Material control**: Apply and modify materials and colors
- **Scene inspection**: Get detailed information about the current Blender scene
- **Code execution**: Run arbitrary Python code in Blender from Claude

## Components

The system consists of two main components:

1. **Blender Addon (`addon.py`)**: A Blender addon that creates a socket server within Blender to receive and execute commands
2. **MCP Server (`src/blender_mcp/server.py`)**: A Python server that implements the Model Context Protocol and connects to the Blender addon

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
3. Turn on the Poly Haven checkbox if you want assets from their API (optional)
4. Click "Connect to Claude"
5. Make sure the MCP server is running in your terminal

### Using with Claude

Once the config file has been set on Claude, and the addon is running on Blender, you will see a hammer icon with tools for the Blender MCP.

![BlenderMCP in the sidebar](assets/hammer-icon.png)

#### Capabilities

- Get scene and object information 
- Create, delete and modify shapes
- Apply or create materials for objects
- Execute any Python code in Blender
- Download the right models, assets and HDRIs through [Poly Haven](https://polyhaven.com/)
- AI generated 3D models through [Hyper3D Rodin](https://hyper3d.ai/)


### Example Commands

Here are some examples of what you can ask Claude to do:

- "Create a low poly scene in a dungeon, with a dragon guarding a pot of gold" [Demo](https://www.youtube.com/watch?v=DqgKuLYUv00)
- "Create a beach vibe using HDRIs, textures, and models like rocks and vegetation from Poly Haven" [Demo](https://www.youtube.com/watch?v=I29rn92gkC4)
- Give a reference image, and create a Blender scene out of it [Demo](https://www.youtube.com/watch?v=FDRb03XPiRo)
- "Generate a 3D model of a garden gnome through Hyper3D"
- "Get information about the current scene, and make a threejs sketch from it" [Demo](https://www.youtube.com/watch?v=jxbNI5L7AH8)
- "Make this car red and metallic" 
- "Create a sphere and place it above the cube"
- "Make the lighting like a studio"
- "Point the camera at the scene, and make it isometric"

## Hyper3D integration

Hyper3D's free trial key allows you to generate a limited number of models per day. If the daily limit is reached, you can wait for the next day's reset or obtain your own key from hyper3d.ai and fal.ai.

## Troubleshooting

- **Connection issues**: Make sure the Blender addon server is running, and the MCP server is configured on Claude, DO NOT run the uvx command in the terminal. Sometimes, the first command won't go through but after that it starts working.
- **Timeout errors**: Try simplifying your requests or breaking them into smaller steps
- **Poly Haven integration**: Claude is sometimes erratic with its behaviour
- **Have you tried turning it off and on again?**: If you're still having connection errors, try restarting both Claude and the Blender server


## Technical Details

### Communication Protocol

The system uses a simple JSON-based protocol over TCP sockets:

- **Commands** are sent as JSON objects with a `type` and optional `params`
- **Responses** are JSON objects with a `status` and `result` or `message`

## Limitations & Security Considerations

- The `execute_blender_code` tool allows running arbitrary Python code in Blender, which can be powerful but potentially dangerous. Use with caution in production environments. ALWAYS save your work before using it.
- Poly Haven requires downloading models, textures, and HDRI images. If you do not want to use it, please turn it off in the checkbox in Blender. 
- Complex operations might need to be broken down into smaller steps


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

---

## BMA Benchmark Fork

This section documents the benchmark-specific additions made by the BMA_Bench project. Everything below is exclusive to this fork and does not exist in upstream blender-mcp.

### What this fork is

`blender-mcp-bma` is a controlled benchmark environment built on top of upstream blender-mcp. It does not replace or compete with the upstream project — it restricts and extends it for reproducible, automated AI-agent evaluation in Blender. Key additions:

- **Tool-gating profiles** — five named profiles restricting which MCP tools an agent can call.
- **Benchmark-safe `bma_*` tools** — structured tools that do not require `execute_blender_code` (no arbitrary Python).
- **`get_bma_profile_info` tool** — lets any caller inspect the active profile and allowed tools at runtime.
- **Telemetry off by default** — `DISABLE_TELEMETRY=true` is the default in this fork; opt-in is required to re-enable.
- **Headless mode** — `blender --background` support via `bpy.app.timers` (modal operators require a window).

### Supported profiles

Set via `BMA_MCP_PROFILE` environment variable (default: `minimal`).

| Profile | `execute_blender_code` | External assets | `bma_*` tools | Extra |
|---|---|---|---|---|
| `minimal` | No | No | Yes | Safest; read + structured mutations |
| `inspection_enabled` | No | No | No | Adds `get_viewport_screenshot` |
| `no_python` | No | No | Yes | All core tools, no Python |
| `python_enabled` | **Yes** | No | Yes | Python allowed, no external assets |
| `full` | **Yes** | **Yes** | Yes | Identical to upstream; no restrictions |

`execute_blender_code` and all external asset tools are **unconditionally blocked** in `minimal`, `inspection_enabled`, and `no_python`. No env override can lift this.

### Running in full / upstream-like mode

`full` restores all upstream tool access with no restrictions:

```bash
BMA_MCP_PROFILE=full DISABLE_TELEMETRY=true uvx --from . blender-mcp
```

Or with the BMA_Bench CLI:

```bash
bma-mcp --config configs/mcp/full.yaml start-server
```

### Running in no_python mode

`no_python` allows all core tools except `execute_blender_code` and external asset tools:

```bash
BMA_MCP_PROFILE=no_python DISABLE_TELEMETRY=true uvx --from . blender-mcp
```

Agents in this mode can use `bma_create_object`, `bma_set_transform`, `bma_set_material`, and similar structured tools to modify the scene without arbitrary Python access.

### Running in headless mode

Headless mode runs Blender without a graphical interface. Use the launcher in the main project:

```bash
# Via BMA_Bench CLI (recommended):
bma-mcp --config configs/mcp/minimal.yaml start-headless-blender --wait

# Manually (blender must be on PATH):
blender --background --factory-startup \
    --python benchmark/mcp/headless/start_blender_mcp_headless.py \
    -- \
    --addon /path/to/blender-mcp-bma/addon.py \
    --host localhost \
    --port 9876 \
    --disable-external-assets
```

The fork replaces modal operators (which require a UI window) with a `bpy.app.timers`-based keep-alive registered with `persistent=True`. SIGTERM and SIGINT are handled and trigger a clean shutdown.

### Checking get_bma_profile_info

`get_bma_profile_info` is available in every profile (including `minimal`) and returns the active profile plus the allow/deny tool lists.

**Via the BMA_Bench CLI:**

```bash
# Returns JSON including "get_bma_profile_info" in tool_results:
bma-mcp --config configs/mcp/minimal.yaml smoke
```

**Via direct socket (low-level):**

```python
from benchmark.mcp.headless.healthcheck import send_blender_socket_command

info = send_blender_socket_command(
    "localhost", 9876, "get_bma_profile_info", timeout_sec=5.0
)
print(info["active_profile"])      # e.g. "minimal"
print(info["allow_python_execution"])  # False
print(info["enabled_tools"])       # list of allowed tool names
```

**Expected response fields:**

```json
{
  "active_profile": "minimal",
  "enabled_tools": ["bma_create_camera", "bma_create_light", "..."],
  "disabled_tools": ["execute_blender_code", "download_polyhaven_asset", "..."],
  "allow_python_execution": false,
  "allow_external_assets": false,
  "telemetry_disabled": true
}
```

### Running fork tests

```bash
cd blender-mcp-bma
python -m pytest tests/ -v
# All 31 tests pass without Blender or MCP server.
```
