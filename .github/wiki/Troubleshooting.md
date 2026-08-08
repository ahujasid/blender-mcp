# Troubleshooting

## spawn uvx ENOENT

GUI clients don't inherit your terminal PATH.

```bash
which uvx      # macOS/Linux
where uvx      # Windows
```

Use the full path as `"command"`. Windows alternative:
```json
{ "command": "cmd", "args": ["/c", "uvx", "blender-mcp"] }
```

After changing config: **fully quit and relaunch** your client (Windows: exit from system tray).

## Connection issues

- Don't run `uvx blender-mcp` manually — the client starts the server
- Check the BlenderMCP tab in Blender shows "Connected"
- First command often fails — try again

## Timeout errors

Break complex prompts into smaller sequential steps.

## Python conflicts (conda / pyenv)

```json
{
  "command": "uvx",
  "args": ["--python", "3.11", "blender-mcp"],
  "env": { "UV_PYTHON_PREFERENCE": "only-managed" }
}
```

Clear cache: `uv cache clean blender-mcp && uvx --refresh blender-mcp`

## Still stuck?

Ask in [Discord](https://discord.gg/SNqPn4TcKQ) with your OS, Blender version, client name, and error message.
