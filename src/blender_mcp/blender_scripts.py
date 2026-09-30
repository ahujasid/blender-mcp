"""Scripts the server runs inside Blender through the addon's execute_code command.

Building observation tools out of execute_code instead of new addon commands
means they work with every addon already installed; only this package has to
update. Each script reads its arguments from an `ARGS` dict and prints one
RESULT_MARKER line carrying its JSON result, which `parse_result` picks out of
whatever else the script printed.
"""

import json

RESULT_MARKER = "__MCP_RESULT__"


def build(script: str, args: dict) -> str:
    """Wrap a script body in a function, so it can `return` its result early.

    The addon catches Exception around execute_code, but not SystemExit, so an
    early exit must never be spelled as one.
    """
    body = "\n".join("    " + line if line.strip() else "" for line in script.strip("\n").splitlines())
    # json.loads of a Python string literal, since JSON's true/null aren't Python.
    return (
        "import json as _json\n"
        f"ARGS = _json.loads({json.dumps(json.dumps(args))})\n"
        f"def _main():\n{body}\n"
        f"print({RESULT_MARKER!r} + _json.dumps(_main()))\n"
    )


def parse_result(output: str) -> dict:
    for line in reversed((output or "").splitlines()):
        if line.startswith(RESULT_MARKER):
            return json.loads(line[len(RESULT_MARKER):])
    raise ValueError("Blender script finished without a result")


# One line per object, so a scene of hundreds of objects still costs a few
# hundred tokens. Dimensions come from the evaluated world bounding box, which
# is what matters for placement (modifiers and parent scale included).
SCENE_SUMMARY = r'''
import bpy
from mathutils import Vector

scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()
limit = max(1, min(int(ARGS.get("limit") or 50), 500))
query = (ARGS.get("query") or "").strip().lower()
root_name = ARGS.get("root")

def r(v):
    return round(float(v), 2)

def bounds(obj):
    try:
        ev = obj.evaluated_get(depsgraph)
        pts = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    except Exception:
        return None
    if obj.type in {"EMPTY", "LIGHT", "CAMERA"}:
        return None
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return lo, hi

def line(obj, depth=0):
    parts = [("  " * depth) + obj.name, obj.type.lower()]
    loc = obj.matrix_world.translation
    parts.append(f"at ({r(loc.x)}, {r(loc.y)}, {r(loc.z)})")
    b = bounds(obj)
    if b:
        size = [r(b[1][i] - b[0][i]) for i in range(3)]
        parts.append(f"size {size[0]}x{size[1]}x{size[2]}")
        if abs(b[0][2]) < 0.005:
            parts.append("on ground")
        elif b[0][2] < -0.005:
            parts.append(f"below ground by {r(-b[0][2])}")
    if obj.type == "MESH":
        parts.append(f"{len(obj.data.polygons)} faces")
        mats = [s.material.name for s in obj.material_slots if s.material]
        if mats:
            parts.append("mat " + ", ".join(mats[:3]) + ("..." if len(mats) > 3 else ""))
    elif obj.type == "ARMATURE":
        parts.append(f"{len(obj.data.bones)} bones")
    elif obj.type == "LIGHT":
        parts.append(f"{obj.data.type.lower()} {r(obj.data.energy)}W")
    if obj.modifiers:
        parts.append("mods " + ", ".join(m.type.lower() for m in obj.modifiers))
    if obj.animation_data and obj.animation_data.action:
        parts.append(f"anim {obj.animation_data.action.name}")
    if obj.hide_get() or obj.hide_render:
        parts.append("hidden")
    if obj.children:
        parts.append(f"{len(obj.children)} children")
    return " | ".join(parts)

lines = []
total = 0
if root_name:
    root = bpy.data.objects.get(root_name)
    if root is None:
        return {"error": f"No object named {root_name!r}"}
    def walk(obj, depth):
        nonlocal total
        total += 1
        if len(lines) < limit:
            lines.append(line(obj, depth))
        for child in obj.children:
            walk(child, depth + 1)
    walk(root, 0)
else:
    if query:
        objs = [o for o in scene.objects if query in o.name.lower()]
    else:
        objs = [o for o in scene.objects if o.parent is None]
    total = len(objs)
    lines = [line(o) for o in objs[:limit]]

counts = {}
for o in scene.objects:
    counts[o.type.lower()] = counts.get(o.type.lower(), 0) + 1

world = scene.world
hdri = None
if world and world.use_nodes:
    for n in world.node_tree.nodes:
        if n.type == "TEX_ENVIRONMENT" and n.image:
            hdri = n.image.name

active = bpy.context.view_layer.objects.active
header = {
    "scene": scene.name,
    "file": bpy.data.filepath or "(unsaved)",
    "blender": bpy.app.version_string,
    "engine": scene.render.engine,
    "frames": [scene.frame_start, scene.frame_end, scene.frame_current],
    "fps": scene.render.fps,
    "resolution": [scene.render.resolution_x, scene.render.resolution_y],
    "camera": scene.camera.name if scene.camera else None,
    "world_hdri": hdri,
    "unit_scale": scene.unit_settings.scale_length,
    "object_counts": counts,
    "selected": [o.name for o in bpy.context.selected_objects][:20],
    "active": active.name if active else None,
    "mode": bpy.context.mode,
}
return {"header": header, "lines": lines, "total": total, "shown": len(lines)}
'''


# Renders the 3D viewport offscreen with chosen camera matrices and shading,
# tiles the results into one PNG, and restores every setting it touched. The
# offscreen path matches the addon's own screenshot, which works while the
# Blender window is in the background.
LOOK = r'''
import bpy, math
import gpu
import numpy as np
from mathutils import Vector, Matrix

scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()
mode = ARGS["mode"]
max_size = int(ARGS.get("max_size") or 1000)

area = space = region = None
for a in bpy.context.screen.areas:
    if a.type == "VIEW_3D":
        area, space = a, a.spaces.active
        region = next((rg for rg in a.regions if rg.type == "WINDOW"), None)
        break
if region is None:
    return {"error": "No 3D viewport is open in Blender"}

names = ARGS.get("target") or []
if names:
    missing = [n for n in names if n not in bpy.data.objects]
    if missing:
        return {"error": "No object named " + ", ".join(repr(m) for m in missing)}
    targets = []
    def add(o):
        if o not in targets:
            targets.append(o)
            for c in o.children:
                add(c)
    for n in names:
        add(bpy.data.objects[n])
else:
    targets = [o for o in scene.objects if o.visible_get() and o.type not in {"CAMERA", "LIGHT"}]

def world_points(objs):
    pts = []
    for o in objs:
        if o.type in {"EMPTY"} and not o.children:
            pts.append(o.matrix_world.translation.copy())
            continue
        try:
            ev = o.evaluated_get(depsgraph)
            pts.extend(ev.matrix_world @ Vector(c) for c in ev.bound_box)
        except Exception:
            pts.append(o.matrix_world.translation.copy())
    return pts

pts = world_points(targets) or [Vector((0, 0, 0))]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
center = (lo + hi) / 2
radius = max((hi - lo).length / 2, 0.05)

FOV = math.radians(35)

def perspective(aspect, near, far):
    f = 1 / math.tan(FOV / 2)
    return Matrix((
        (f / aspect, 0, 0, 0),
        (0, f, 0, 0),
        (0, 0, (far + near) / (near - far), 2 * far * near / (near - far)),
        (0, 0, -1, 0),
    ))

def orbit(direction, aspect):
    direction = Vector(direction).normalized()
    fit = FOV / 2 if aspect >= 1 else math.atan(math.tan(FOV / 2) * aspect)
    dist = radius / math.sin(fit) * 1.1
    eye = center + direction * dist
    # The camera looks down its local -Z with local Y up; to_track_quat keeps
    # that Y as close to world Z as the direction allows, so the horizon stays level.
    rot = (center - eye).to_track_quat("-Z", "Y").to_matrix().to_4x4()
    view = (Matrix.Translation(eye) @ rot).inverted()
    return view, perspective(aspect, max(dist - radius * 3, dist * 0.01), dist + radius * 3)

ANGLES = {
    "front": (0, -1, 0), "back": (0, 1, 0), "right": (1, 0, 0), "left": (-1, 0, 0),
    # Top is tilted a hair toward -Y so "up" in the image is +Y, as in Blender's top view.
    "top": (0, -0.001, 1), "three_quarter": (1, -1, 0.7),
}

def current_view():
    r3d = space.region_3d
    return r3d.view_matrix.copy(), r3d.window_matrix.copy()

def camera_view(w, h):
    cam = scene.camera
    if cam is None:
        return None
    win = cam.calc_matrix_camera(depsgraph, x=w, y=h,
                                 scale_x=scene.render.pixel_aspect_x, scale_y=scene.render.pixel_aspect_y)
    return cam.matrix_world.inverted(), win

def draw(view, win, w, h):
    off = gpu.types.GPUOffScreen(w, h)
    try:
        off.draw_view3d(scene, bpy.context.view_layer, space, region, view, win,
                        do_color_management=True)
        buf = off.texture_color.read()
    finally:
        off.free()
    buf.dimensions = w * h * 4
    return np.asarray(buf, dtype=np.float32).reshape(h, w, 4) / 255.0

def sheet(tiles, cols):
    h, w = tiles[0].shape[:2]
    rows = math.ceil(len(tiles) / cols)
    gap = 4
    out = np.ones((rows * h + (rows - 1) * gap, cols * w + (cols - 1) * gap, 4), dtype=np.float32)
    out[..., :3] = 0.08
    # Blender images are stored bottom row first, so the first tile goes top-left.
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        y = (rows - 1 - r) * (h + gap)
        x = c * (w + gap)
        out[y:y + h, x:x + w] = t
    return out

# Settings each mode changes, restored afterwards.
shading, overlay = space.shading, space.overlay
saved = []
def set_attr(obj, attr, value):
    if not hasattr(obj, attr):
        return
    saved.append((obj, attr, getattr(obj, attr)))
    try:
        setattr(obj, attr, value)
    except Exception:
        saved.pop()

requested = ARGS.get("shading")
shading_types = {"solid": "SOLID", "material": "MATERIAL", "rendered": "RENDERED", "wireframe": "WIREFRAME"}
if requested:
    set_attr(shading, "type", shading_types[requested])

if mode != "viewport":
    # The 3D cursor sits in the middle of generated views and reads as part of the scene.
    set_attr(overlay, "show_cursor", False)

info = {"mode": mode, "targets": len(targets), "center": [round(v, 2) for v in center],
        "size": [round(v, 2) for v in (hi - lo)]}
frame_before = scene.frame_current

try:
    if mode == "topology":
        if not requested:
            set_attr(shading, "type", "SOLID")
        set_attr(shading, "light", "MATCAP")
        set_attr(shading, "color_type", "SINGLE")
        set_attr(overlay, "show_overlays", True)
        set_attr(overlay, "show_wireframes", True)
        set_attr(overlay, "wireframe_threshold", 1.0)
        import bmesh
        stats = []
        for o in [t for t in targets if t.type == "MESH"][:10]:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            sides = [len(f.verts) for f in bm.faces]
            poles = sum(1 for v in bm.verts if len(v.link_edges) not in (0, 2, 4) and not v.is_boundary)
            stats.append({
                "object": o.name, "verts": len(bm.verts), "faces": len(sides),
                "tris": sides.count(3), "quads": sides.count(4), "ngons": sum(1 for s in sides if s > 4),
                "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary),
                "boundary_edges": sum(1 for e in bm.edges if e.is_boundary),
                "loose_verts": sum(1 for v in bm.verts if not v.link_edges),
                "poles": poles,
                "modifiers": [m.type.lower() for m in o.modifiers],
            })
            bm.free()
        info["mesh_stats"] = stats
    elif mode == "rig":
        set_attr(shading, "show_xray", True)
        set_attr(shading, "xray_alpha", 0.35)
        set_attr(overlay, "show_overlays", True)
        set_attr(overlay, "show_bones", True)
        rigs = []
        for o in targets:
            if o.type == "ARMATURE":
                set_attr(o, "show_in_front", True)
                bones = o.data.bones
                rigs.append({"armature": o.name, "bones": len(bones),
                             "deform_bones": sum(1 for b in bones if b.use_deform),
                             "roots": [b.name for b in bones if b.parent is None][:5]})
            elif o.type == "MESH":
                arm = next((m.object for m in o.modifiers if m.type == "ARMATURE" and m.object), None)
                if arm is None:
                    continue
                deform = {b.name for b in arm.data.bones if b.use_deform}
                groups = {g.index: g.name for g in o.vertex_groups if g.name in deform}
                unweighted = sum(1 for v in o.data.vertices
                                 if not any(g.group in groups and g.weight > 0 for g in v.groups))
                rigs.append({"mesh": o.name, "armature": arm.name, "vertices": len(o.data.vertices),
                             "unweighted_vertices": unweighted,
                             "deform_bones_without_group": sorted(deform - set(groups.values()))[:10]})
        info["rig_stats"] = rigs

    if mode == "viewport":
        w, h = region.width, region.height
        s = min(1.0, max_size / max(w, h))
        w, h = max(1, int(w * s)), max(1, int(h * s))
        view, win = current_view()
        image = draw(view, win, w, h)
    elif mode == "camera":
        rx, ry = scene.render.resolution_x, scene.render.resolution_y
        s = max_size / max(rx, ry)
        w, h = max(1, int(rx * s)), max(1, int(ry * s))
        cv = camera_view(w, h)
        if cv is None:
            return {"error": "The scene has no camera. Add one or use mode='angles'."}
        info["camera"] = scene.camera.name
        image = draw(cv[0], cv[1], w, h)
    elif mode == "frames":
        start, end = scene.frame_start, scene.frame_end
        frames = ARGS.get("frames") or []
        if not frames:
            n = max(2, min(int(ARGS.get("frame_count") or 6), 12))
            frames = sorted({round(start + (end - start) * i / (n - 1)) for i in range(n)})
        frames = frames[:12]
        cols = 3 if len(frames) > 4 else 2
        w = max(64, max_size // cols)
        h = int(w * 0.75)
        use_camera = scene.camera is not None and ARGS.get("view") == "camera"
        tiles = []
        for f in frames:
            scene.frame_set(int(f))
            if use_camera:
                view, win = camera_view(w, h)
            elif ARGS.get("view") in ANGLES:
                view, win = orbit(ANGLES[ARGS["view"]], w / h)
            else:
                view, win = current_view()
            tiles.append(draw(view, win, w, h))
        info["frames"] = [int(f) for f in frames]
        image = sheet(tiles, cols)
    else:
        views = ARGS.get("views") or ["front", "right", "top", "three_quarter"]
        views = [v for v in views if v in ANGLES][:6] or ["three_quarter"]
        cols = 1 if len(views) == 1 else (3 if len(views) > 4 else 2)
        w = max(64, max_size // cols)
        h = w
        tiles = [draw(*orbit(ANGLES[v], 1.0), w, h) for v in views]
        info["views"] = views
        image = sheet(tiles, cols)
finally:
    if scene.frame_current != frame_before:
        scene.frame_set(frame_before)
    for obj, attr, value in reversed(saved):
        try:
            setattr(obj, attr, value)
        except Exception:
            pass

h, w = image.shape[:2]
img = bpy.data.images.new("mcp_look", w, h, alpha=True)
try:
    img.pixels.foreach_set(image.ravel())
    img.filepath_raw = ARGS["filepath"]
    img.file_format = "PNG"
    img.save()
finally:
    bpy.data.images.remove(img)
info["width"], info["height"] = w, h
return info
'''


# Bounding box of freshly imported objects, so a generation or import result
# says how big the thing is and whether it sits on the ground.
BOUNDS = r'''
import bpy
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
out = []
for name in ARGS["names"]:
    o = bpy.data.objects.get(name)
    if o is None:
        continue
    objs = [o] + list(o.children_recursive)
    pts = []
    for x in objs:
        if x.type in {"MESH", "CURVE", "SURFACE", "FONT", "META", "CURVES", "POINTCLOUD", "VOLUME"}:
            ev = x.evaluated_get(dg)
            pts.extend(ev.matrix_world @ Vector(c) for c in ev.bound_box)
    if not pts:
        continue
    lo = [round(min(p[i] for p in pts), 3) for i in range(3)]
    hi = [round(max(p[i] for p in pts), 3) for i in range(3)]
    out.append({"name": o.name, "world_bounding_box": [lo, hi],
                "size": [round(hi[i] - lo[i], 3) for i in range(3)]})
return out
'''
