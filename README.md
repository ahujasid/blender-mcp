<div align="center">

<img src="https://raw.githubusercontent.com/MCPBlender/blender-mcp/main/assets/logo.png" width="80" alt="MCPBlender">

<h1>BlenderMCP</h1>

<p><strong>Control Blender 3D with Claude AI — in real time, through natural language</strong></p>

<p>
  <a href="https://pepy.tech/projects/blender-mcp">
    <img src="https://static.pepy.tech/badge/blender-mcp/month" alt="Downloads/month">
  </a>
  <a href="https://github.com/MCPBlender/blender-mcp/stargazers">
    <img src="https://img.shields.io/github/stars/MCPBlender/blender-mcp?style=flat&color=F5A623" alt="Stars">
  </a>
  <a href="https://github.com/MCPBlender/blender-mcp/network/members">
    <img src="https://img.shields.io/github/forks/MCPBlender/blender-mcp?style=flat&color=4A90D9" alt="Forks">
  </a>
  <a href="https://github.com/MCPBlender/blender-mcp/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/MCPBlender/blender-mcp?style=flat&color=9B59B6" alt="MIT">
  </a>
  <a href="https://discord.gg/SNqPn4TcKQ">
    <img src="https://img.shields.io/badge/Discord-Join-5865F2?style=flat&logo=discord&logoColor=white" alt="Discord">
  </a>
  <a href="https://pypi.org/project/blender-mcp">
    <img src="https://img.shields.io/pypi/v/blender-mcp?style=flat&color=3B82F6&label=PyPI" alt="PyPI">
  </a>
</p>

<p>
  <a href="https://trendshift.io/repositories/14834" target="_blank">
    <img src="https://trendshift.io/api/badge/repositories/14834" alt="Trendshift" width="180" height="40">
  </a>
</p>

<p>
  <a href="https://blendermcp.org"><strong>🌐 Website</strong></a> ·
  <a href="https://www.youtube.com/watch?v=lCyQ717DuzQ"><strong>📹 Tutorial</strong></a> ·
  <a href="https://discord.gg/SNqPn4TcKQ"><strong>💬 Discord</strong></a> ·
  <a href="https://github.com/MCPBlender/blender-mcp/wiki"><strong>📖 Wiki</strong></a> ·
  <a href="https://github.com/MCPBlender/blender-mcp/releases"><strong>📋 Changelog</strong></a>
</p>

</div>

---

**BlenderMCP** connects Blender 3D to Claude AI (and any other LLM) through the [Model Context Protocol](https://modelcontextprotocol.io/). It enables prompt-driven 3D modeling, scene creation, and real-time object manipulation — directly from your AI assistant.

---

## Table of Contents

- [Features](#features)
- [Whats New](#whats-new)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Integrations](#integrations)
- [API Credentials](#api-credentials)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)
- [Security and Telemetry](#security-and-telemetry)
- [Contributors](#contributors)
- [Community](#community)
- [Contributing](#contributing)

---

## Features

| | Capability | Description |
|---|---|---|
| 🔁 | **Two-way communication** | Real-time socket bridge between Claude and Blender |
| 🧊 | **Object manipulation** | Create, move, scale, and delete 3D objects via prompts |
| 🎨 | **Material control** | Apply, modify, and generate materials and colors |
| 🔍 | **Scene inspection** | Full scene state — objects, lights, cameras |
| 📷 | **Viewport screenshot** | Let the AI see the Blender viewport |
| 🐍 | **Code execution** | Run arbitrary Python inside Blender |
| 🌍 | **Poly Haven** | Download HDRIs, textures, and models via API |
| 🤖 | **AI model generation** | 3D assets via Hyper3D Rodin and Hunyuan3D |
| 🗂️ | **Sketchfab** | Search and import 3D models |
| 🌐 | **Remote host** | Run the MCP server on a remote machine |

---

## Whats New

> Full changelog: [Releases](https://github.com/MCPBlender/blender-mcp/releases)

- Hunyuan3D 3D model generation
- Viewport screenshot for scene understanding
- Sketchfab model search and import
- Poly Haven asset integration
- Hyper3D Rodin AI model generation
- Remote host support

**Updating from an older version:**
1. Download the latest `addon.py` and replace it in Blender
2. Remove and re-add the MCP server in your client config

---

## Quick Start

```bash
# macOS
brew install uv
```

Add to **Claude > Settings > Developer > Edit Config > `claude_desktop_config.json`**:

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": ["blender-mcp"]
        }
    }
}
```

[Install the Blender addon](#blender-addon), click **Connect**, and start prompting.

---

## Installation

### Prerequisites

| Requirement | Minimum version |
|---|---|
| Blender | 3.0 |
| Python | 3.10 |
| uv | Latest |

**Install uv:**

<details>
<summary>macOS</summary>

```bash
brew install uv
```

</details>

<details>
<summary>Windows</summary>

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Add to PATH (restart your client after):

```powershell
$localBin = "$env:USERPROFILE\.local\bin"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$userPath;$localBin", "User")
```

</details>

<details>
<summary>Linux</summary>

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

</details>

> **Do not use `pip install uv`** — it may not create the `uvx` command.

---

#### uvx not found by your client

GUI clients don't inherit your terminal PATH. Get the full path:
- `which uvx` (macOS/Linux) or `where uvx` (Windows)
- Use it as `"command"` in your config
- Windows: `"command": "cmd", "args": ["/c", "uvx", "blender-mcp"]`
- Fully quit and relaunch your client after any config change

#### Apple Silicon (M1/M2/M3/M4) arch mismatch

If `uvx` tries to build for `x86_64` on an arm64 Mac (cryptography wheel errors), force arm64 Python:

```json
"args": ["--python", "3.11-aarch64", "blender-mcp"]
```

#### Docker / WSL / remote host

Blender must listen where the MCP process can reach it:

```json
"env": {
  "BLENDER_HOST": "host.docker.internal",
  "BLENDER_PORT": "9876"
}
```

On WSL2 talking to Windows Blender, try `BLENDER_HOST=127.0.0.1` or your Windows host IP. Screenshots are returned as base64 (no shared temp path required).

#### Blender versions

Blender **3.0+** is supported; **4.x / 5.x** recommended. Use a normal GUI Blender session (not `blender -b` background) so the MCP socket and viewport tools work.

#### Keep addon and server in sync

The TCP link uses **length-prefixed JSON frames**. Update **both** the Blender addon (`addon.py`) and the MCP package (`uvx --refresh blender-mcp`) together after upgrades.

#### Windows: Claude Extension `egg_base '.' does not exist`

If Claude Desktop’s built-in extension fails to build with `egg_base` / wrong path under `Packages\Claude_...`, skip the extension launcher and run the package via **uvx** (config above). That path is the supported install on Windows.

```powershell
uv tool install blender-mcp
uv tool upgrade blender-mcp
uvx --refresh blender-mcp
```

`blender-mcp` does **not** depend on `pywin32`. If uv tries to install a locked `pywin32` wheel from an old env, clear the stuck build cache or use a fresh `uvx`/`uv tool` install rather than a partial site-packages tree.

---

### Claude Desktop

[Watch setup video](https://www.youtube.com/watch?v=neoK_WMq92g)

**Claude > Settings > Developer > Edit Config > `claude_desktop_config.json`**:

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": ["blender-mcp"]
        }
    }
}
```

<details>
<summary>Pin Python 3.11 (conda / pyenv machines)</summary>

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": ["--python", "3.11", "blender-mcp"],
            "env": { "UV_PYTHON_PREFERENCE": "only-managed" }
        }
    }
}
```

</details>

<details>
<summary>Install without uv</summary>

```bash
pipx install blender-mcp
pipx ensurepath
```

</details>

---

### Cursor

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/link/mcp%2Finstall?name=blender&config=eyJjb21tYW5kIjoidXZ4IGJsZW5kZXItbWNwIn0%3D)

[Watch Cursor setup video](https://www.youtube.com/watch?v=wgWsJshecac)

<details>
<summary>macOS / Linux</summary>

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": ["blender-mcp"]
        }
    }
}
```

</details>

<details>
<summary>Windows</summary>

```json
{
    "mcpServers": {
        "blender": {
            "command": "cmd",
            "args": ["/c", "uvx", "blender-mcp"]
        }
    }
}
```

</details>

> Run only one MCP server at a time — Cursor or Claude Desktop, not both.

---

### VS Code

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_blender--mcp-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](vscode:mcp/install?%7B%22name%22%3A%22blender-mcp%22%2C%22type%22%3A%22stdio%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22blender-mcp%22%5D%7D)

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": ["blender-mcp"]
        }
    }
}
```

---

### OpenCode

```json
{
  "mcp": {
    "blender-mcp": {
      "type": "local",
      "command": ["uvx", "blender-mcp"],
      "enabled": true,
      "environment": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

---

### Claude Code CLI

```bash
claude mcp add blender uvx blender-mcp
```

---

### Blender Addon

1. Download [`addon.py`](https://github.com/MCPBlender/blender-mcp/raw/main/addon.py)
2. In Blender: **Edit > Preferences > Add-ons > Install...**
3. Select `addon.py`
4. Enable **"Interface: Blender MCP"**

---

## Usage

### Starting the Connection

![BlenderMCP sidebar](assets/addon-instructions.png)

1. Open the **3D View sidebar** (press `N` if not visible)
2. Go to the **BlenderMCP** tab
3. *(Optional)* Enable **Poly Haven** for asset downloads
4. Click **Connect to Claude**

When connected, Claude shows a hammer icon confirming Blender tools are active:

![Hammer icon](assets/hammer-icon.png)

---

### Example Prompts

| Prompt | Demo |
|---|---|
| "Create a low poly dungeon with a dragon guarding gold" | [Watch](https://www.youtube.com/watch?v=DqgKuLYUv00) |
| "Beach scene with Poly Haven HDRIs, rocks, and vegetation" | [Watch](https://www.youtube.com/watch?v=I29rn92gkC4) |
| "Recreate this reference image as a Blender scene" | [Watch](https://www.youtube.com/watch?v=FDRb03XPiRo) |
| "Export the scene and build a Three.js sketch from it" | [Watch](https://www.youtube.com/watch?v=jxbNI5L7AH8) |
| "Generate a garden gnome with Hyper3D" | — |
| "Make this car red and metallic" | — |
| "Studio lighting, isometric camera" | — |

---

## Integrations

### Poly Haven
Download HDRIs, textures, and 3D models. Enable in the BlenderMCP sidebar.

### Hyper3D Rodin
AI 3D models. Free trial has a daily limit — get your own key at [hyper3d.ai](https://hyper3d.ai) or [fal.ai](https://fal.ai).

### Hunyuan3D
Tencent 3D generation. Configure credentials in Blender addon preferences.

### Sketchfab
Search and import 3D models into your scenes.

---

## API Credentials

Store in **Edit > Preferences > Add-ons > Blender MCP** to persist across restarts:

| Credential | Environment variable |
|---|---|
| Sketchfab API Key | `BLENDERMCP_SKETCHFAB_API_KEY` |
| Hyper3D API Key | `BLENDERMCP_HYPER3D_API_KEY` |
| Hunyuan3D SecretId | `BLENDERMCP_HUNYUAN3D_SECRET_ID` |
| Hunyuan3D SecretKey | `BLENDERMCP_HUNYUAN3D_SECRET_KEY` |
| Hunyuan3D API URL | `BLENDERMCP_HUNYUAN3D_API_URL` |

```bash
export BLENDER_HOST=localhost
export BLENDER_PORT=9876
```

---

## Troubleshooting

<details>
<summary>Connection issues</summary>

- Confirm the addon server is running in the BlenderMCP sidebar
- Do not run `uvx` manually — the client starts the server
- First command often fails; try again

</details>

<details>
<summary>spawn uvx ENOENT</summary>

```bash
which uvx   # macOS / Linux
where uvx   # Windows
```

Use that full path as `"command"` in your config.

</details>

<details>
<summary>Timeout / complex operations</summary>

Break the request into smaller sequential prompts.

</details>

<details>
<summary>Python version conflicts</summary>

```json
"args": ["--python", "3.11", "blender-mcp"],
"env": { "UV_PYTHON_PREFERENCE": "only-managed" }
```

Clear cache: `uv cache clean blender-mcp && uvx --refresh blender-mcp`

</details>

<details>
<summary>Still broken?</summary>

Restart your MCP client and the Blender server.

</details>

---

## Technical Details

```
LLM Client  <-- MCP -->  MCP Server (src/blender_mcp/server.py)  <-- TCP:9876 -->  Blender Addon (addon.py)
```

JSON over TCP sockets:

```json
{ "type": "create_object", "params": { "type": "SPHERE", "name": "Ball" } }
{ "status": "success", "result": { "name": "Ball", "location": [0, 0, 0] } }
```

---

## Security and Telemetry

> **`execute_blender_code` runs arbitrary Python in Blender. Save your work before using it.**

Optional anonymous usage stats (tool names, success/duration, version/platform) may be sent to help improve the project. Detailed fields (prompts/code/screenshots) require the addon privacy checkbox. Credential-like strings are stripped before upload.

**Disable entirely:**

```bash
BLENDER_MCP_DISABLE_TELEMETRY=true uvx blender-mcp
```

Or in client config: `"env": { "BLENDER_MCP_DISABLE_TELEMETRY": "true" }`

In Blender: Edit → Preferences → Add-ons → Blender MCP → telemetry checkbox.

---

## Contributors

<div align="center">

<a href="https://github.com/MCPBlender/blender-mcp/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=MCPBlender/blender-mcp&max=80&columns=12" alt="Contributors">
</a>

<sub>Made with [contrib.rocks](https://contrib.rocks)</sub>

</div>

---

## Community

<div align="center">

| | |
|---|---|
| 💬 Discord | [Join the community](https://discord.gg/SNqPn4TcKQ) |
| 📝 Feedback | [Share your thoughts](https://bit.ly/blender-mcp-form) |
| 📞 Call | [Schedule a call](https://bit.ly/blender-mcp-call) |
| 🐛 Issues | [GitHub Issues](https://github.com/MCPBlender/blender-mcp/issues) |
| 💖 Sponsor | [Support BlenderMCP](https://github.com/sponsors/SerenityUiX) |

</div>

**Supporters:** [CodeRabbit](https://www.coderabbit.ai/)

---

## Contributing

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit and open a PR

See [CONTRIBUTING.md](https://github.com/MCPBlender/.github/blob/main/CONTRIBUTING.md) and [TERMS_AND_CONDITIONS.md](TERMS_AND_CONDITIONS.md).

---

## License

MIT — see [LICENSE](LICENSE).

---

## Star History

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=MCPBlender/blender-mcp&type=Date)](https://star-history.com/#MCPBlender/blender-mcp&Date)

</div>


---

<div align="center">

[MCPBlender](https://github.com/MCPBlender) · [blendermcp.org](https://blendermcp.org) · Not affiliated with the Blender Foundation

⭐ Star the repo if it helps your workflow!

</div>
