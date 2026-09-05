FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies first so this layer is cached across source changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Blender runs on the host, not in the container. host.docker.internal
# resolves to the host on Docker Desktop (macOS/Windows); on Linux pass
# --add-host=host.docker.internal:host-gateway or use --network=host.
ENV BLENDER_HOST=host.docker.internal \
    BLENDER_PORT=9876

ENTRYPOINT ["blender-mcp"]
