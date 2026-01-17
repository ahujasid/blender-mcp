# Remote Deployment Guide for Blender MCP

This guide explains how to set up Blender MCP as a remote server for use with **Claude.ai (web)** and **ChatGPT**.

## Why Remote Deployment?

Claude.ai and ChatGPT web interfaces require MCP servers to be accessible via a public HTTPS URL. This guide covers two methods:

1. **Cloudflare Tunnel** (Recommended) - Expose your local server securely
2. **Docker Deployment** - Run on a remote server/VPS

---

## Method 1: Cloudflare Tunnel (Recommended for Personal Use)

This method lets you expose your local Blender MCP server to the internet securely, without opening ports on your router.

### Prerequisites
- Blender installed locally with the BlenderMCP addon
- A Cloudflare account (free)
- `cloudflared` CLI installed

### Step 1: Install Cloudflared

**Mac:**
```bash
brew install cloudflare/cloudflare/cloudflared
```

**Windows:**
```powershell
winget install --id Cloudflare.cloudflared
```

**Linux:**
```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

### Step 2: Login to Cloudflare
```bash
cloudflared tunnel login
```
This opens a browser to authenticate with your Cloudflare account.

### Step 3: Create a Tunnel
```bash
cloudflared tunnel create blender-mcp
```
Note the tunnel ID that's generated.

### Step 4: Configure the Tunnel

Create a config file at `~/.cloudflared/config.yml`:
```yaml
tunnel: <YOUR_TUNNEL_ID>
credentials-file: ~/.cloudflared/<YOUR_TUNNEL_ID>.json

ingress:
  - hostname: blender-mcp.yourdomain.com
    service: http://localhost:9876
  - service: http_status:404
```

Replace:
- `<YOUR_TUNNEL_ID>` with your actual tunnel ID
- `blender-mcp.yourdomain.com` with your desired subdomain

### Step 5: Create DNS Record
```bash
cloudflared tunnel route dns blender-mcp blender-mcp.yourdomain.com
```

### Step 6: Start Everything

1. **Start Blender** and enable the BlenderMCP addon:
   - Press `N` in the 3D viewport to open the sidebar
   - Find the "BlenderMCP" tab
   - Click "Connect to Claude"

2. **Start the MCP server:**
   ```bash
   uvx blender-mcp
   ```

3. **Start the Cloudflare tunnel:**
   ```bash
   cloudflared tunnel run blender-mcp
   ```

Your Blender MCP is now accessible at `https://blender-mcp.yourdomain.com`!

---

## Method 2: Quick Tunnel (Temporary/Testing)

For quick testing without permanent setup:

1. **Start Blender** with the addon connected

2. **Start the MCP server:**
   ```bash
   uvx blender-mcp
   ```

3. **Create a quick tunnel:**
   ```bash
   cloudflared tunnel --url http://localhost:9876
   ```

4. **Copy the generated URL** (e.g., `https://random-words.trycloudflare.com`)

> ⚠️ This URL changes each time you restart the tunnel. Use Method 1 for a permanent URL.

---

## Connecting to Claude.ai

1. Go to [claude.ai](https://claude.ai)
2. Navigate to **Settings → Connectors**
3. Click **"Add custom connector"**
4. Enter your tunnel URL:
   - Permanent: `https://blender-mcp.yourdomain.com`
   - Quick tunnel: `https://random-words.trycloudflare.com`
5. Click **Connect**

You should now see Blender MCP tools available in Claude!

---

## Connecting to ChatGPT

1. Go to [chat.openai.com](https://chat.openai.com)
2. Navigate to **Settings → Connectors → Advanced**
3. Enable **Developer Mode**
4. Click **Create New Connector**
5. Enter your tunnel URL
6. Save and connect

---

## Docker Deployment (Advanced)

For running on a remote VPS or cloud server, use the included Dockerfile.

### Build and Run
```bash
docker build -t blender-mcp .
docker run -p 9876:9876 -e BLENDER_HOST=<your-blender-host> blender-mcp
```

> ⚠️ Note: Blender must be running and accessible from the Docker container. This is more complex and typically requires running Blender in headless mode on the same server.

---

## Troubleshooting

### Connection Issues
- Ensure Blender is running with the addon connected
- Verify the MCP server is running (`uvx blender-mcp`)
- Check that the Cloudflare tunnel is active

### Tunnel Not Working
- Run `cloudflared tunnel list` to verify your tunnel exists
- Check `cloudflared tunnel info <tunnel-name>` for status
- Ensure your DNS records are properly configured

### Claude.ai Can't Connect
- Verify your URL is accessible in a browser
- Check that you're using HTTPS (not HTTP)
- Try the quick tunnel method to test connectivity

---

## Security Considerations

- Cloudflare Tunnel encrypts all traffic end-to-end
- Consider adding authentication for production use
- The `execute_blender_code` tool can run arbitrary Python - be cautious about who has access
- Always save your Blender work before using MCP tools

---

## Additional Resources

- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [Blender MCP README](./README.md)
- [Model Context Protocol Docs](https://modelcontextprotocol.io/)