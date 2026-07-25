#!/usr/bin/env python3
"""
Cádiz Asset Pack v0.1 — full workflow via Blender MCP socket (same transport as MCP tools).

Requires Blender 5.1 GUI + addon MCP server on BLENDER_HOST:9876.

Usage:
  BLENDER_HOST=172.19.96.1 uv run --directory . python scripts/run_cadiz_dogfooding_workflow.py \\
    --geojson /mnt/c/Users/druiz/blender-data/gta-andalucia/cadiz-centro/cadiz-centro_buildings.geojson \\
    --benchmark-out /path/to/BENCHMARK-CADIZ-MCP-ISSUE-219-appendix.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Repo src on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from blender_mcp.server import BlenderConnection  # noqa: E402

GEOJSON_DEFAULT = (
    "/mnt/c/Users/druiz/blender-data/gta-andalucia/cadiz-centro/cadiz-centro_buildings.geojson"
)
GLB_DEFAULT = "/mnt/c/Users/druiz/blender-exports/cadiz_buildings_full.glb"
SCREENSHOT_DIR = "/mnt/c/Users/druiz/blender-data/gta-andalucia/screenshots"


class BenchLog:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def record(self, command: str, elapsed: float, status: str, detail: str = "") -> None:
        line = f"Comando: {command}\nTiempo: {elapsed:.2f}s\nStatus: {status}"
        if detail:
            line += f"\nNotas: {detail}"
        self.lines.append(line)
        print(line.replace("\n", " | "))

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        body = "\n\n---\n\n".join(self.lines)
        path.write_text(
            f"# Cádiz MCP workflow benchmark (auto)\n\n"
            f"Generado: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n---\n\n{body}\n",
            encoding="utf-8",
        )


def run_code(conn: BlenderConnection, code: str, bench: BenchLog, label: str) -> dict:
    t0 = time.perf_counter()
    try:
        result = conn.send_command("execute_code", {"code": code})
        bench.record(label, time.perf_counter() - t0, "OK")
        return result
    except Exception as exc:
        bench.record(label, time.perf_counter() - t0, "FAIL", str(exc))
        raise


def phase_cleanup(conn: BlenderConnection, bench: BenchLog) -> None:
    code = """
import bpy
removed = []
for name in ("Cube", "Light", "Camera"):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)
        removed.append(name)
print("removed", removed)
"""
    run_code(conn, code, bench, "execute_code (scene cleanup)")


def phase_import(conn: BlenderConnection, bench: BenchLog, geojson_path: str) -> None:
    # Windows path for Blender on Windows; fallback WSL mount
    win_path = geojson_path.replace("/mnt/c/", "C:\\\\").replace("/", "\\\\")
    code = f'''
import bpy
import json
import bmesh
from mathutils import Vector

path_wsl = r"{geojson_path}"
path_win = r"{win_path}"
for p in (path_win, path_wsl):
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        path_used = p
        break
    except OSError:
        data = None
if not data:
    raise FileNotFoundError("GeoJSON not found: " + path_wsl)

coll_name = "cadiz-centro_buildings"
if coll_name in bpy.data.collections:
    old = bpy.data.collections[coll_name]
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)

coll = bpy.data.collections.new(coll_name)
bpy.context.scene.collection.children.link(coll)

count = 0
for feat in data.get("features", []):
    geom = feat.get("geometry") or {{}}
    if geom.get("type") != "Polygon":
        continue
    rings = geom.get("coordinates") or []
    if not rings:
        continue
    coords = rings[0]
    mesh = bpy.data.meshes.new(f"Building_{{count:04d}}")
    bm = bmesh.new()
    verts = [bm.verts.new((c[0], c[1], 0.0)) for c in coords]
    bm.verts.ensure_lookup_table()
    try:
        bm.faces.new(verts)
    except ValueError:
        bm.free()
        continue
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(mesh.name, mesh)
    coll.objects.link(obj)
    props = feat.get("properties") or {{}}
    for k, v in props.items():
        try:
            obj[k] = v
        except TypeError:
            pass
    count += 1

print("imported", count, "from", path_used)
'''
    run_code(conn, code, bench, "execute_code (import GeoJSON)")


def phase_heights(conn: BlenderConnection, bench: BenchLog) -> None:
    code = '''
import bpy

def get_building_height(obj):
    height_tag = obj.get("height")
    if height_tag:
        try:
            return max(float(str(height_tag).split()[0].replace("m","")), 3.0)
        except ValueError:
            pass
    levels_tag = obj.get("building:levels")
    if levels_tag:
        try:
            return float(levels_tag) * 3.0
        except ValueError:
            pass
    building_type = obj.get("building", "yes")
    heights = {
        "cathedral": 25.0, "church": 18.0, "house": 9.0,
        "apartments": 15.0, "commercial": 12.0, "yes": 9.0,
    }
    return heights.get(building_type, 9.0)

collection = bpy.data.collections.get("cadiz-centro_buildings")
if not collection:
    collection = bpy.data.collections.get("GeoJSON_Import")
if not collection:
    print("no collection")
else:
    n = 0
    for obj in collection.objects:
        if obj.type != "MESH":
            continue
        height = get_building_height(obj)
        mod = obj.modifiers.new("Building_Height", "SOLIDIFY")
        mod.thickness = height
        mod.offset = 1.0
        n += 1
    print("solidify", n)
'''
    run_code(conn, code, bench, "execute_code (Solidify 2355)")


def phase_materials(conn: BlenderConnection, bench: BenchLog) -> None:
    code = '''
import bpy
mat = bpy.data.materials.get("Building_Material_Basic")
if not mat:
    mat = bpy.data.materials.new("Building_Material_Basic")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.9, 0.85, 0.8, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.7
    out = nodes.new("ShaderNodeOutputMaterial")
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

collection = bpy.data.collections.get("cadiz-centro_buildings") or bpy.data.collections.get("GeoJSON_Import")
count = 0
if collection:
    for obj in collection.objects:
        if obj.type != "MESH":
            continue
        if not obj.data.materials:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
        count += 1
print("materials", count)
'''
    run_code(conn, code, bench, "execute_code (materials)")


def phase_fix_z(conn: BlenderConnection, bench: BenchLog) -> None:
    code = '''
import bpy
from mathutils import Matrix

collection = bpy.data.collections.get("cadiz-centro_buildings") or bpy.data.collections.get("GeoJSON_Import")
if not collection:
    print("no collection")
else:
    z_min = float("inf")
    for obj in collection.objects:
        if obj.type != "MESH":
            continue
        for v in obj.data.vertices:
            world_co = obj.matrix_world @ v.co
            z_min = min(z_min, world_co.z)
    print("z_min_before", round(z_min, 2))
    if z_min < 0:
        offset = abs(z_min) + 0.5
        translation = Matrix.Translation((0, 0, offset))
        for obj in collection.objects:
            if obj.type == "MESH":
                obj.data.transform(translation)
        print("offset_applied", round(offset, 2))
    else:
        print("no_fix_needed")
'''
    run_code(conn, code, bench, "execute_code (fix elevation Z)")


def phase_export_glb(conn: BlenderConnection, bench: BenchLog, glb_path: str) -> None:
    win_path = glb_path.replace("/mnt/c/", "C:\\\\").replace("/", "\\\\")
    code = f'''
import bpy
import os

collection = bpy.data.collections.get("cadiz-centro_buildings") or bpy.data.collections.get("GeoJSON_Import")
bpy.ops.object.select_all(action="DESELECT")
if collection:
    for obj in collection.objects:
        obj.select_set(True)
out_paths = [r"{win_path}", r"{glb_path}"]
for output_path in out_paths:
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        bpy.ops.export_scene.gltf(
            filepath=output_path,
            use_selection=True,
            export_format="GLB",
            export_materials="EXPORT",
            export_colors=True,
        )
        size = os.path.getsize(output_path)
        print("glb", output_path, size)
        break
    except OSError as e:
        last = e
else:
    raise last
'''
    run_code(conn, code, bench, "execute_code (export GLB)")


def phase_screenshot(conn: BlenderConnection, bench: BenchLog, out_dir: str) -> None:
    t0 = time.perf_counter()
    try:
        win_dir = out_dir.replace("/mnt/c/", "C:/").replace("/", "/")
        path = f"{win_dir}/cadiz-mcp-perspective.png"
        conn.send_command(
            "get_viewport_screenshot",
            {"max_size": 1920, "filepath": path, "format": "png"},
        )
        bench.record("get_viewport_screenshot", time.perf_counter() - t0, "OK", path)
    except Exception as exc:
        bench.record("get_viewport_screenshot", time.perf_counter() - t0, "FAIL", str(exc))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.getenv("BLENDER_HOST", "172.19.96.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("BLENDER_PORT", "9876")))
    parser.add_argument("--geojson", default=GEOJSON_DEFAULT)
    parser.add_argument("--glb", default=GLB_DEFAULT)
    parser.add_argument("--benchmark-out", default="")
    parser.add_argument("--skip-import", action="store_true", help="Scene already has GeoJSON_Import")
    args = parser.parse_args()

    bench = BenchLog()
    conn = BlenderConnection(host=args.host, port=args.port)

    t0 = time.perf_counter()
    # Fail fast if Blender is not listening (avoid ~130s WSL→Windows TCP timeout)
    import socket as _socket

    probe = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    probe.settimeout(10.0)
    try:
        probe.connect((args.host, args.port))
        probe.close()
    except OSError as exc:
        bench.record("connect", time.perf_counter() - t0, "FAIL", f"{args.host}:{args.port} — {exc}")
        if args.benchmark_out:
            bench.write(Path(args.benchmark_out))
        print("Blender MCP server not reachable. Open Blender GUI and Start MCP Server.")
        return 2

    if not conn.connect():
        bench.record("connect", time.perf_counter() - t0, "FAIL", f"{args.host}:{args.port}")
        if args.benchmark_out:
            bench.write(Path(args.benchmark_out))
        print("Blender MCP server not reachable. Open Blender GUI and Start MCP Server.")
        return 2

    bench.record("connect", time.perf_counter() - t0, "OK")

    t0 = time.perf_counter()
    try:
        info = conn.send_command("get_scene_info")
        bench.record("get_scene_info", time.perf_counter() - t0, "OK", json.dumps(info)[:200])
    except Exception as exc:
        bench.record("get_scene_info", time.perf_counter() - t0, "FAIL", str(exc))
        if args.benchmark_out:
            bench.write(Path(args.benchmark_out))
        return 3

    try:
        phase_cleanup(conn, bench)
        if not args.skip_import:
            phase_import(conn, bench, args.geojson)
        phase_heights(conn, bench)
        phase_materials(conn, bench)
        phase_fix_z(conn, bench)
        phase_export_glb(conn, bench, args.glb)
        phase_screenshot(conn, bench, SCREENSHOT_DIR)
    finally:
        conn.disconnect()

    if args.benchmark_out:
        bench.write(Path(args.benchmark_out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
