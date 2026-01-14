# Blender MCP Remote Server Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \n    curl \n    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY main.py ./

# Install dependencies
RUN uv sync

# Environment variables for Blender connection
ENV BLENDER_HOST=host.docker.internal
ENV BLENDER_PORT=9876

# Expose the MCP server port
EXPOSE 8080

# Run the MCP server
CMD ["uv", "run", "blender-mcp"]