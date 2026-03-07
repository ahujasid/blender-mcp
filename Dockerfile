FROM python:3.12-slim

RUN pip install --no-cache-dir uv

RUN groupadd --system appuser && useradd --system --gid appuser appuser

ENV BLENDER_HOST=host.docker.internal
ENV BLENDER_PORT=9876
ENV DISABLE_TELEMETRY=true

USER appuser

ENTRYPOINT ["uvx", "blender-mcp"]
