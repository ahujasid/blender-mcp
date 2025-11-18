# Blender MCP - Docker Deployment

This directory contains the Dockerized version of the Blender MCP server for use in containerized environments.

## Overview

The Blender MCP server enables Claude AI to control Blender through the Model Context Protocol (MCP). This Docker image packages the MCP server for easy deployment.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  Claude AI      │◄───────►│  blender-mcp     │
│  (MCP Client)   │  stdio  │  (Container)     │
└─────────────────┘         └────────┬─────────┘
                                     │ TCP 9876
                            ┌────────▼─────────┐
                            │  Blender         │
                            │  (with addon)    │
                            └──────────────────┘
```

## Building the Image

### Local Build

```bash
cd blender-mcp
docker build -t blender-mcp:latest .
```

### GitHub Actions CI/CD

The image is automatically built and pushed to GitHub Container Registry on:
- Push to `main` branch
- New version tags (`v*`)
- Pull requests (build only, no push)

**Image location**: `ghcr.io/elasticdotventures/blender-mcp:latest`

## Usage

### With Docker Compose

The blender-mcp service is defined in the main project's `docker-compose.yml`:

```yaml
services:
  blender-mcp:
    build:
      context: ../blender-mcp
      dockerfile: Dockerfile
    environment:
      - BLENDER_HOST=blender-dev
      - BLENDER_PORT=9876
```

To run with the MCP profile:

```bash
# Start all services including MCP
docker-compose --profile mcp up

# Or just the blender-dev and blender-mcp services
docker-compose up blender-dev blender-mcp
```

### Standalone Docker Run

```bash
docker run -i --network=host \
  -e BLENDER_HOST=host.docker.internal \
  -e BLENDER_PORT=9876 \
  blender-mcp:latest
```

**Note**: The MCP server communicates via stdin/stdout, so `-i` (interactive) is required.

### With Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "blender": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network=host",
        "blender-mcp:latest"
      ]
    }
  }
}
```

Or use the pre-built image from GHCR:

```json
{
  "mcpServers": {
    "blender": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network=host",
        "ghcr.io/elasticdotventures/blender-mcp:latest"
      ]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BLENDER_HOST` | `host.docker.internal` | Hostname/IP where Blender addon is running |
| `BLENDER_PORT` | `9876` | Port where Blender addon listens |

## Network Configuration

### Docker-to-Host Communication

When Blender runs on the host and blender-mcp runs in Docker:

**Linux**:
```bash
docker run -i --network=host blender-mcp:latest
```

**macOS/Windows**:
```bash
docker run -i -e BLENDER_HOST=host.docker.internal blender-mcp:latest
```

### Docker-to-Docker Communication

When both services run in Docker (via docker-compose):

```yaml
environment:
  - BLENDER_HOST=blender-dev  # Service name in docker-compose
  - BLENDER_PORT=9876
```

## Prerequisites

### Blender Addon Setup

The Blender MCP addon must be installed and running:

1. Copy `addon.py` to Blender's addons directory:
   ```bash
   cp addon.py ~/.config/blender/4.2/scripts/addons/blender_mcp_addon.py
   ```

2. Enable the addon in Blender:
   ```python
   import bpy
   bpy.ops.preferences.addon_enable(module='blender_mcp_addon')
   ```

3. The addon will start a TCP server on port 9876

## Troubleshooting

### Connection Refused

**Symptom**: `Could not connect to Blender. Make sure the Blender addon is running.`

**Solutions**:
- Verify Blender addon is enabled and running
- Check `BLENDER_HOST` points to correct host
- Ensure port 9876 is accessible (firewall rules)
- On Linux, use `--network=host` for Docker

### MCP Server Not Responding

**Symptom**: Claude Desktop shows MCP server as disconnected

**Solutions**:
- Ensure Docker container is running with `-i` flag (stdin required)
- Check Docker logs: `docker logs <container-id>`
- Verify MCP server starts: Look for "BlenderMCP server starting up" in logs

## CI/CD Pipeline

### Workflow Steps

1. **Checkout**: Clone repository
2. **Setup Buildx**: Enable multi-platform builds
3. **Login**: Authenticate to GitHub Container Registry
4. **Metadata**: Extract tags and labels
5. **Build & Push**: Build for amd64/arm64, push to registry
6. **Attestation**: Generate build provenance

### Manual Trigger

```bash
gh workflow run docker-build.yml
```

### Image Tags

- `latest` - Latest build from main branch
- `main` - Main branch builds
- `v1.2`, `v1`, `1.2`, `1` - Semantic version tags
- `main-<sha>` - Commit SHA tags

## Development

### Local Testing

```bash
# Build
docker build -t blender-mcp:dev .

# Test
docker run -i \
  -e BLENDER_HOST=localhost \
  -e BLENDER_PORT=9876 \
  blender-mcp:dev
```

### Rebuild on Code Changes

```bash
# Watch for changes and rebuild
docker-compose up --build blender-mcp
```

## Multi-Architecture Support

The GitHub Actions workflow builds for:
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64/Apple Silicon)

Pull the appropriate image for your platform:

```bash
# Auto-selects correct architecture
docker pull ghcr.io/elasticdotventures/blender-mcp:latest
```

## Security

- No privileged capabilities required
- Network access limited to Blender TCP connection
- SBOM and attestation generated for supply chain security

## License

MIT License - See [LICENSE](LICENSE)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test with Docker build
5. Submit pull request

GitHub Actions will automatically build and validate your changes.
