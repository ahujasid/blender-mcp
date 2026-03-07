FROM python:3.12-slim

RUN pip install --no-cache-dir uv

ENTRYPOINT ["uvx", "blender-mcp"]
