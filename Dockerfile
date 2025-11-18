# Dockerfile for blender-mcp MCP server
FROM python:3.11-slim

# Install UV package manager
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY main.py ./

# Install dependencies
RUN uv pip install --system -e .

# Set environment variables
ENV BLENDER_HOST=host.docker.internal
ENV BLENDER_PORT=9876

# Expose MCP server port (stdio-based, no port needed)
# The server communicates via stdin/stdout

# Run the MCP server via the console script to avoid double-import warnings
CMD ["blender-mcp"]
