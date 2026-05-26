---
name: blender-cli
description: Use this skill when you want to control a running Blender instance via the BlenderMCP addon socket using the `blender-cli` command (scene/object inspection, viewport screenshots, executing Blender Python, PolyHaven/Sketchfab/Hyper3D/Hunyuan3D workflows). Assumes the addon server is reachable (default `localhost:9876`).
metadata:
  short-description: Control Blender via CLI
---

# Blender CLI (BlenderMCP addon socket)

This repo provides a terminal client `blender-cli` that talks directly to the BlenderMCP Blender addon socket server (JSON over TCP).

## Preconditions

- Blender is running and the **Blender MCP** addon is enabled.
- The addon’s socket server is reachable (default `localhost:9876`).
- If needed, override connection with `--host/--port` or env vars `BLENDER_HOST` / `BLENDER_PORT`.

## Quick start (connection check)

- `blender-cli scene`

If it fails to connect, have the user verify the addon is running and the port matches.

## CLI flags

- Global flags (e.g. `--compact`, `--host`, `--port`, `-v`) must come **before** the subcommand:
  - `blender-cli --compact scene`
  - `blender-cli --host localhost --port 9876 scene`

## Core commands

- **Inspect scene**
  - `blender-cli scene`
- **Inspect object**
  - `blender-cli object "Cube"`
- **Viewport screenshot**
  - `blender-cli screenshot /tmp/viewport.png --max-size 800`
- **Execute Blender Python**
  - Prefer small, safe, step-by-step snippets.
  - `blender-cli exec --code 'import bpy; print(bpy.app.version_string)'`
  - Or pipe via stdin:
    - `cat script.py | blender-cli exec`

## Asset workflows

- **PolyHaven**
  - `blender-cli polyhaven status`
  - `blender-cli polyhaven categories --asset-type textures`
  - `blender-cli polyhaven search --asset-type textures --categories wood,metal`
  - `blender-cli polyhaven download <asset_id> --asset-type textures --resolution 2k`
  - `blender-cli polyhaven set-texture <object_name> <texture_id>`

- **Sketchfab**
  - `blender-cli sketchfab status`
  - `blender-cli sketchfab search "wood chair" --count 10`
  - `blender-cli sketchfab preview <uid> --out /tmp/preview.jpg`
  - `blender-cli sketchfab download <uid> --target-size 1.0`

- **Hyper3D (Rodin)**
  - `blender-cli hyper3d status`
  - Create job (text):
    - `blender-cli hyper3d generate-text "a small wooden stool" --bbox 1 1 1`
  - Create job (images):
    - `blender-cli hyper3d generate-images --image-path /abs/path/a.jpg --image-path /abs/path/b.jpg`
  - Poll:
    - `blender-cli hyper3d poll --subscription-key <key>`
    - `blender-cli hyper3d poll --request-id <id>`
  - Import:
    - `blender-cli hyper3d import Stool --task-uuid <uuid>`
    - `blender-cli hyper3d import Stool --request-id <id>`

- **Hunyuan3D**
  - `blender-cli hunyuan3d status`
  - Create job:
    - `blender-cli hunyuan3d generate --text-prompt "卡通风格咖啡杯" --image https://...`
  - Poll:
    - `blender-cli hunyuan3d poll job_xxx`
  - Import:
    - `blender-cli hunyuan3d import Cup <zip_file_url>`

## Advanced / escape hatch

- Send a raw command to the addon (type + params JSON):
  - `blender-cli raw get_scene_info`
  - `blender-cli raw execute_code --params-json '{"code":"import bpy; print(bpy.data.objects.keys())"}'`

## Safety notes

- `blender-cli exec` runs arbitrary Python inside Blender: confirm intent and run minimal code first.
- If a command times out, reduce scope (smaller code snippet, fewer assets, simpler request) and retry.
