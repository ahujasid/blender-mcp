FROM python:3.12-slim

RUN pip install --no-cache-dir uv

ENV BLENDER_HOST=host.docker.internal
ENV BLENDER_PORT=9876

ENTRYPOINT ["uvx", "blender-mcp"]
