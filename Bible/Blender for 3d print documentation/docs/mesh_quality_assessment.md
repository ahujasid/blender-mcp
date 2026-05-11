# Mesh Quality Assessment — Blender Tools and Metrics

A mesh intended for FDM printing must satisfy a different set of constraints than a mesh built for rendering. The slicer (Bambu Studio) treats the mesh as a closed solid: it needs a watertight boundary, consistent outward-facing normals, real-world scale, and wall thicknesses above the nozzle's minimum. This document describes the Blender tools and programmatic APIs available to evaluate those properties, and explains what each metric actually means for printability.

---

## 3D Print Toolbox (`bpy.ops.mesh.print3d_*`)

The 3D Print Toolbox is an official Blender addon. It must be explicitly enabled before its operators are available:

```python
bpy.ops.preferences.addon_enable(module='object_print3d_utils')
```

The addon operates on the active mesh object. Most operators run best with the object selected in Object Mode, though some internally switch context. The scene-level properties it exposes are the thresholds used during analysis:

```python
scene = bpy.context.scene
scene.print_3d.thickness_min    # minimum wall thickness for check_thick() — default 1.0 mm
scene.print_3d.overhang_angle   # angle above which faces are flagged — default 45 degrees
scene.print_3d.export_path      # output path for export operator
```

These thresholds should be adjusted before running checks. For the Bambu A1 with a 0.4mm nozzle, a practical `thickness_min` is 0.8mm (two extrusion widths); 0.45mm is the hard floor below which geometry is silently dropped by the slicer.

**Analysis operators:**

- `bpy.ops.mesh.print3d_check_solid()` — tests whether the mesh is watertight. Reports non-manifold edges and open boundary loops. A non-zero result means the slicer cannot guarantee a closed volume.
- `bpy.ops.mesh.print3d_check_intersect()` — tests for self-intersecting faces. Self-intersections do not prevent slicing but create ambiguous interior regions that produce unpredictable wall structures.
- `bpy.ops.mesh.print3d_check_thick()` — identifies faces whose local wall thickness falls below `thickness_min`. Uses ray-cast sampling, so it is an approximation. Very thin results signal features that will not survive slicing.
- `bpy.ops.mesh.print3d_check_sharp()` — flags faces with high internal angle distortion. Distorted faces cause normal calculation errors and can produce slicer artifacts.
- `bpy.ops.mesh.print3d_check_overhang()` — selects faces whose angle from horizontal exceeds `overhang_angle`. These are candidates for support material unless the model can be reoriented.
- `bpy.ops.mesh.print3d_check_all()` — runs all checks in sequence and writes results to `scene.print_3d` properties. After calling this, problematic elements are left selected in the viewport.

After `check_all()`, the count of flagged faces can be retrieved programmatically:

```python
import bmesh
bm = bmesh.from_edit_mesh(obj.data)
flagged = [f for f in bm.faces if f.select]
print(len(flagged))
```

**Cleanup operators:**

- `bpy.ops.mesh.print3d_clean_non_manifold()` — automated attempt to fix non-manifold edges. Works well on meshes with isolated bad edges; unreliable on meshes with topological holes.
- `bpy.ops.mesh.print3d_clean_distorted()` — triangulates or dissolves distorted faces.
- `bpy.ops.mesh.print3d_select_non_manifold_verts()` — selection-only; surfaces the problem locations without modifying geometry.

---

## BMesh Programmatic Analysis

BMesh gives direct access to mesh topology without relying on UI operators. It is the correct approach when analysis results need to drive downstream decisions in code.

```python
import bpy, bmesh, mathutils

obj = bpy.context.active_object
bm = bmesh.new()
bm.from_mesh(obj.data)
bm.edges.ensure_lookup_table()
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# Non-manifold edges: anything not shared by exactly 2 faces
non_manifold_edges = [e for e in bm.edges if len(e.link_faces) != 2]

# Boundary edges: edges with exactly 1 linked face (open holes)
boundary_edges = [e for e in bm.edges if e.is_boundary]

# Duplicate vertices within a merge distance
result = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=0.0001)
# result['targetmap'] is a dict mapping each duplicate vert to its merge target

# Degenerate faces (zero area)
zero_faces = [f for f in bm.faces if f.calc_area() < 1e-8]

# Topology counts
n_faces = len(bm.faces)
n_verts = len(bm.verts)
n_edges = len(bm.edges)

# Object real-world dimensions
dims = obj.dimensions  # mathutils.Vector in Blender Units

bm.free()
```

`non_manifold_edges` and `boundary_edges` overlap: a boundary edge is a specific type of non-manifold edge (one face). Non-manifold also includes T-junctions (three or more faces sharing one edge), which are topology errors that holes do not explain.

For bounding box in world space:

```python
bb_world = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
# obj.bound_box gives 8 corners in local space; matrix_world transforms to scene space
```

---

## Key Metrics and What They Mean

| Metric | How to get | Good threshold | Meaning for printability |
|--------|-----------|---------------|--------------------------|
| Non-manifold edge count | `[e for e in bm.edges if len(e.link_faces) != 2]` | 0 | Any value > 0 means slicer may produce empty or broken layers |
| Boundary edge count | `[e for e in bm.edges if e.is_boundary]` | 0 | Open holes; slicer cannot determine interior |
| Duplicate vertex count | `find_doubles(dist=0.0001)` | 0 | Ghost geometry that creates false edges and corrupt normals |
| Zero-area face count | `f.calc_area() < 1e-8` | 0 | Degenerate triangles; cause normal errors and slicer instability |
| Face count | `len(bm.faces)` | < 500k preferred | > 2M likely needs decimation; slicer performance degrades |
| Min face area | `min(f.calc_area() for f in bm.faces)` | > 0.01 mm² | Very small faces indicate mesh noise or artifacts |
| Object dimensions | `obj.dimensions` | Fit within 256×256×256 mm | Hard build volume limit on Bambu A1 |
| Wall thickness | `print3d_check_thick()` | ≥ 0.8 mm | Below 0.45 mm the slicer silently drops the feature |
| Overhang faces | `print3d_check_overhang()` | 0 faces above 45° | Above 45° requires supports or model reorientation |

---

## Scale Assessment

Scale is the first thing to verify because every other metric is meaningless if the mesh is in the wrong unit system. Blender's default scene uses meters; FDM modeling needs millimeters.

```python
scene = bpy.context.scene
scale_length = scene.unit_settings.scale_length  # 0.001 = metric mm; 1.0 = meters
unit = scene.unit_settings.length_unit           # 'MILLIMETERS' or 'METERS'

# If scale_length == 0.001 and unit == 'MILLIMETERS':
#   obj.dimensions values are in mm directly
# Otherwise multiply: real_size_mm = obj.dimensions * (1.0 / scale_length) * 1000
```

A common error is an object that visually looks the right size in Blender but has an unapplied scale transform. `obj.scale` of `(0.001, 0.001, 0.001)` with vertex coordinates in meters gives the same visual size as a properly scaled mesh — but STL export writes raw vertex coordinates, not display-corrected values. The scale must be baked into mesh data via `bpy.ops.object.transform_apply(scale=True)` before export.

The Bambu A1 build plate is 256×256×256 mm. Any dimension exceeding this must be addressed by splitting the model or scaling it down before slicing.

---

## Normal Consistency

Normals determine which side of each face is "outside." STL uses normals to communicate orientation to the slicer. Inverted normals cause the slicer to treat a region of the model as interior, which manifests as missing walls or hollow sections in the print.

```python
# Programmatic recalculation check — compare face normal direction
# with the vector from object origin to face center
for poly in obj.data.polygons:
    face_center = poly.center  # local space
    outward_vec = (face_center - mathutils.Vector((0, 0, 0))).normalized()
    if poly.normal.dot(outward_vec) < 0:
        # Possibly inverted — not definitive but a fast heuristic
        pass
```

This heuristic only works for roughly convex objects. For complex shapes, `bmesh.ops.recalc_face_normals()` is the reliable approach, but it requires a watertight mesh to produce correct results. On a mesh with holes, normal recalculation can produce inconsistent results at the hole boundaries.

---

## 3D Print Toolbox — Additional Operators

### Volume and Area
```python
bpy.ops.mesh.print3d_info_volume()   # prints mesh volume to info panel
bpy.ops.mesh.print3d_info_area()     # prints surface area to info panel
```
Volume is useful to estimate material cost and print time. Surface area helps detect excessive polygon density relative to mesh size.

### Scale to Bounds
```python
# Scale object so its longest dimension equals the given value (in scene units)
bpy.ops.mesh.print3d_scale_to_bounds(length=0.256)   # 256mm if scale_length=0.001
```
`print3d_scale_to_bounds` scales the object proportionally so its bounding box fits within a target length. Useful to quickly fit a model to build volume or a specific size requirement without manual scale calculation.

### Configuring Thresholds
```python
scene = bpy.context.scene
scene.print_3d.thickness_min = 0.0008   # 0.8mm minimum wall (2 perimeters @ 0.4mm nozzle)
scene.print_3d.overhang_angle = 45.0    # degrees from horizontal
```
These thresholds are read by `print3d_check_thick()` and `print3d_check_overhang()`. Setting `thickness_min` to 0.0008 (0.8mm) flags anything below 2 perimeters with a 0.4mm nozzle.

---

## Assessment Priority Order

The order of assessment matters because earlier problems can invalidate later measurements.

1. **Scale** — if the model is in meters instead of millimeters, all dimensional checks (thickness, build volume) will report false results.
2. **Non-manifold / watertight** — a mesh with open boundaries cannot produce a valid sliced output. All other issues are secondary to this.
3. **Dimensions vs. build volume** — a watertight mesh that exceeds 256mm on any axis cannot be printed as-is.
4. **Wall thickness** — features below 0.45mm will be silently dropped; between 0.45mm and 0.8mm they are marginal.
5. **Polygon count** — above 500k, slicer performance degrades meaningfully; above 2M, decimation is usually necessary before slicing.
6. **Overhangs** — faces above 45° from horizontal affect support strategy and surface quality but not fundamental printability.
7. **Surface noise** — micro-bumps and high-frequency detail affect surface finish and slicer processing time but rarely block printing.

A mesh that passes checks 1–4 is printable. Checks 5–7 affect quality and workflow, not feasibility.
