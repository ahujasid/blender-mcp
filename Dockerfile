FROM python:3.11-slim

# Install uv for fast, reproducible dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install dependencies first for better layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the project and install it
COPY . .
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Run as a networked MCP server (Streamable HTTP) rather than the stdio mode
# used when a client spawns this package directly. Point BLENDER_HOST at a
# reachable Blender instance's addon socket -- see README.
ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

# Streamable HTTP endpoint, served at /mcp
EXPOSE 8000

ENTRYPOINT ["blender-mcp"]
