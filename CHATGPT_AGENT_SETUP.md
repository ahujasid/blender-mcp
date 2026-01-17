# ChatGPT 5.2 Agent Mode Setup Instructions for Blender MCP

Use these instructions to have ChatGPT 5.2 Agent Mode help you set up Blender MCP with Claude.ai.

---

## Copy and paste this prompt into ChatGPT 5.2 Agent Mode:

---

```
I need your help setting up Blender MCP for use with Claude.ai. You have access to my GitHub via the GitHub connector. Please follow these steps:

## Step 1: Review the Repository
Access my repository at https://github.com/ahump20/blender-mcp and review:
- The README.md for general setup instructions
- The REMOTE_SETUP.md for Cloudflare Tunnel configuration
- The claude_desktop_config.json for the MCP server configuration

## Step 2: Guide Me Through Local Setup
Help me complete these steps on my local machine:

1. **Install prerequisites:**
   - Verify I have Blender 3.0+ installed
   - Install the `uv` package manager if not already installed
   - Install `cloudflared` CLI for Cloudflare Tunnel

2. **Set up the Blender addon:**
   - Download addon.py from the repository
   - Guide me through installing it in Blender (Edit > Preferences > Add-ons > Install)
   - Help me enable and connect the addon

3. **Start the MCP server:**
   - Run `uvx blender-mcp` to start the server
   - Verify it's running on port 9876

4. **Create Cloudflare Tunnel:**
   - Help me run `cloudflared tunnel --url http://localhost:9876`
   - Capture the generated public URL (e.g., https://random-words.trycloudflare.com)

## Step 3: Add the Connector to Claude.ai
Once we have the Cloudflare tunnel URL:

1. **Navigate to Claude.ai connector settings:**
   - Go to: https://claude.ai/settings/connectors?modal=add-custom-connector
   
2. **Add the custom connector:**
   - Enter the connector name: "Blender MCP"
   - Enter the tunnel URL we generated
   - Complete the connection setup

3. **Verify the connection:**
   - Confirm the Blender MCP tools appear in Claude
   - Test with a simple command like "Get scene information"

## Step 4: Troubleshooting
If anything fails, help me troubleshoot by:
- Checking if Blender is running with the addon connected
- Verifying the MCP server is active
- Confirming the Cloudflare tunnel is running
- Testing the tunnel URL in a browser

## Important Notes:
- I need Blender running on my machine with the addon enabled BEFORE starting the MCP server
- The Cloudflare quick tunnel URL changes each restart - for a permanent URL, help me set up a named tunnel
- Keep all three services running: Blender, MCP server, and Cloudflare tunnel

Please guide me through this step-by-step, waiting for my confirmation at each stage before proceeding.
```

---

## What This Prompt Does

1. **Leverages GitHub Access** - ChatGPT can read your repository files directly
2. **Step-by-Step Guidance** - Walks through prerequisites, setup, and verification
3. **Autonomous Claude Setup** - Directs the agent to the exact URL to add the connector
4. **Built-in Troubleshooting** - Includes common issues and solutions

## Tips for Best Results

- Run ChatGPT in **Agent Mode** (not standard chat)
- Have Blender open and ready before starting
- Keep a terminal window available for commands
- The agent will wait for your confirmation at each step

## Quick Reference: URLs Needed

| Resource | URL |
|----------|-----|
| Your Repository | https://github.com/ahump20/blender-mcp |
| Claude.ai Add Connector | https://claude.ai/settings/connectors?modal=add-custom-connector |
| Cloudflare Tunnel Docs | https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/ |