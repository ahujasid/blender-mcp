# Installation

## Requirements

| | Minimum |
|---|---|
| Blender | 3.0 |
| Python | 3.10 |
| uv | latest |

## 1. Install uv

**macOS**
```bash
brew install uv
```

**Windows**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
$localBin = "$env:USERPROFILE\.local\bin"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$userPath;$localBin", "User")
```

**Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. Configure MCP Client

### Claude Desktop
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

### Cursor — macOS/Linux
Settings → MCP → Add new global MCP server

### Cursor — Windows
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

### VS Code
```json
{
  "mcpServers": {
    "blender": { "command": "uvx", "args": ["blender-mcp"] }
  }
}
```

### Claude Code CLI
```bash
claude mcp add blender uvx blender-mcp
```

## 3. Install Blender Addon

1. Download [addon.py](https://github.com/MCPBlender/blender-mcp/raw/main/addon.py)
2. In Blender: **Edit > Preferences > Add-ons > Install...**
3. Select `addon.py`
4. Enable **"Interface: Blender MCP"**

## 4. Connect

Open 3D View sidebar (`N`) → **BlenderMCP** tab → **Connect to Claude**
