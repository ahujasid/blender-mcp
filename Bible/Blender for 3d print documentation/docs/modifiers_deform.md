# Blender Deform & Mesh Modifiers — Python API Reference for 3D Printing

Source: `bpy.types` — Blender Python API  
Apply pattern: `bpy.ops.object.modifier_apply(modifier="ModName")`  
Add pattern: `mod = obj.modifiers.new(name="ModName", type='TYPE_ENUM')`

---

## DecimateModifier

`class bpy.types.DecimateModifier(Modifier)`  
Reduces polygon count while preserving shape.

```python
mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
mod.decimate_type = 'COLLAPSE'
mod.ratio = 0.5           # keep 50% of faces
bpy.ops.object.modifier_apply(modifier="Decimate")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `decimate_type` | Literal | `'COLLAPSE'` | `COLLAPSE` (edge collapse), `UNSUBDIV` (un-subdivide), `DISSOLVE` (planar) |
| `ratio` | float | `1.0` | Target face ratio for COLLAPSE mode [0, 1] |
| `iterations` | int | `0` | Reduction iterations for UNSUBDIV mode [0, 32767] |
| `angle_limit` | float | `0.0872665` | Max angle to dissolve faces for DISSOLVE mode [0, pi] (~5 degrees default) |
| `face_count` | int | `0` | Current face count after decimation (readonly) |
| `use_collapse_triangulate` | bool | `False` | Keep triangulated faces from decimation (COLLAPSE only) |
| `use_dissolve_boundaries` | bool | `False` | Dissolve all vertices between face boundaries (DISSOLVE only) |
| `use_symmetry` | bool | `False` | Maintain symmetry on an axis |
| `symmetry_axis` | Literal | `'X'` | Symmetry axis: `X`, `Y`, `Z` |
| `vertex_group` | str | `''` | Vertex group for selective decimation (COLLAPSE only) |
| `vertex_group_factor` | float | `1.0` | Vertex group weight strength [0, 1000] |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |
| `delimit` | set | `set()` | Limit geometry merging (seams, sharp, material boundaries) |

**3D Printing use:** Reduce file size and slicing time for high-poly scans or sculpts. Set `ratio = 0.1–0.5` for aggressive reduction. `DISSOLVE` mode is ideal for flat-surfaced mechanical parts (dissolves coplanar faces into n-gons). Always verify no holes appear after decimation.

---

## SubsurfModifier

`class bpy.types.SubsurfModifier(Modifier)`  
Catmull-Clark subdivision surface for smooth, rounded geometry.

```python
mod = obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod.subdivision_type = 'CATMULL_CLARK'
mod.levels = 2            # viewport subdivisions
mod.render_levels = 3     # render subdivisions
mod.use_creases = True
bpy.ops.object.modifier_apply(modifier="Subsurf")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `subdivision_type` | Literal | `'CATMULL_CLARK'` | `CATMULL_CLARK` (smooth curves) or `SIMPLE` (no shape change) |
| `levels` | int | `1` | Subdivisions in viewport [0, 11] |
| `render_levels` | int | `2` | Subdivisions during render [0, 11] |
| `quality` | int | `3` | Vertex position accuracy; lower = faster [1, 10] |
| `use_limit_surface` | bool | `True` | Place vertices at infinite-subdivision surface (smoothest shape) |
| `use_creases` | bool | `True` | Use mesh crease data to sharpen edges/corners |
| `use_custom_normals` | bool | `False` | Interpolate existing custom normals |
| `boundary_smooth` | Literal | `'ALL'` | Open boundary smoothing control |
| `uv_smooth` | Literal | `'PRESERVE_BOUNDARIES'` | UV smoothing control |
| `use_adaptive_subdivision` | bool | `False` | Adaptive subdivision based on camera distance |
| `adaptive_space` | Literal | `'PIXEL'` | `PIXEL` or `OBJECT` for adaptive subdivision |
| `adaptive_pixel_size` | float | `1.0` | Target polygon pixel size for adaptive mode [0.1, 1000] |
| `adaptive_object_edge_length` | float | `0.01` | Target edge length for adaptive mode [0.0001, 1000] |
| `show_only_control_edges` | bool | `True` | Hide interior subdivided edges in viewport |

**3D Printing use:** Smooth mechanical parts and organic shapes from low-poly base meshes. Use `levels = 2–3` before export. Add edge creases (`Ctrl+E > Crease`) to preserve sharp corners like mounting tabs or mating surfaces. `SIMPLE` mode just subdivides without rounding — useful for adding resolution to flat surfaces.

---

## BevelModifier

`class bpy.types.BevelModifier(Modifier)`  
Rounds edges and vertices.

```python
mod = obj.modifiers.new(name="Bevel", type='BEVEL')
mod.width = 0.002         # 2 mm bevel
mod.segments = 3          # number of edge loops
mod.limit_method = 'ANGLE'
mod.angle_limit = 0.523599  # 30 degrees
bpy.ops.object.modifier_apply(modifier="Bevel")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `width` | float | `0.1` | Bevel amount in OFFSET mode [0, inf] |
| `width_pct` | float | `0.1` | Bevel amount for PERCENT mode [0, inf] |
| `segments` | int | `1` | Edge loops for rounding [1, 1000] |
| `affect` | Literal | `'EDGES'` | `EDGES` or `VERTICES` |
| `limit_method` | Literal | `'ANGLE'` | `NONE`, `ANGLE`, `WEIGHT`, `VGROUP` |
| `angle_limit` | float | `0.523599` | Angle threshold above which to bevel [0, pi] (~30° default) |
| `offset_type` | Literal | `'OFFSET'` | `OFFSET`, `WIDTH`, `DEPTH`, `PERCENT`, `ABSOLUTE` |
| `profile` | float | `0.5` | Profile shape: 0.5 = round, 0 = concave, 1 = convex [0, 1] |
| `profile_type` | Literal | `'SUPERELLIPSE'` | `SUPERELLIPSE` or `CUSTOM` |
| `miter_outer` | Literal | `'MITER_SHARP'` | Outer miter pattern: `MITER_SHARP`, `MITER_PATCH`, `MITER_ARC` |
| `miter_inner` | Literal | `'MITER_SHARP'` | Inner miter pattern: `MITER_SHARP`, `MITER_ARC` |
| `spread` | float | `0.1` | Spread for inner miter arcs [0, inf] |
| `loop_slide` | bool | `True` | Prefer sliding along edges for even widths |
| `use_clamp_overlap` | bool | `True` | Clamp width to avoid overlap |
| `harden_normals` | bool | `False` | Match normals of new faces to adjacent |
| `face_strength_mode` | Literal | `'FSTR_NONE'` | Face strength assignment |
| `vmesh_method` | Literal | `'ADJ'` | Vertex mesh at intersections: `ADJ` (grid fill) or `CUTOFF` |
| `mark_seam` | bool | `False` | Mark seams along beveled edges |
| `mark_sharp` | bool | `False` | Mark beveled edges as sharp |
| `material` | int | `-1` | Material index (-1 = automatic) |
| `vertex_group` | str | `''` | Vertex group for VGROUP limit method |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |

**3D Printing use:** Remove sharp 90° edges that cause stress concentrations, delamination, or print artifacts. Use `segments = 2–4` for smooth chamfers. Set `limit_method = 'ANGLE'` to only bevel non-flat edges. Minimum printable bevel is roughly 0.4 mm for FDM.

---

## ShrinkwrapModifier

`class bpy.types.ShrinkwrapModifier(Modifier)`  
Projects vertices onto a target surface.

```python
mod = obj.modifiers.new(name="Shrinkwrap", type='SHRINKWRAP')
mod.target = target_mesh_obj
mod.wrap_method = 'NEAREST_SURFACEPOINT'
mod.offset = 0.001        # 1 mm clearance
bpy.ops.object.modifier_apply(modifier="Shrinkwrap")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `target` | Object | — | Mesh target to shrink to |
| `auxiliary_target` | Object | — | Additional mesh target |
| `wrap_method` | Literal | `'NEAREST_SURFACEPOINT'` | Shrinkwrap algorithm type |
| `wrap_mode` | Literal | `'ON_SURFACE'` | How vertices are constrained to surface |
| `offset` | float | `0.0` | Distance to maintain from target [-inf, inf] |
| `project_limit` | float | `0.0` | Max projection distance (0 = unlimited) [0, inf] |
| `use_positive_direction` | bool | `True` | Allow movement in positive axis direction |
| `use_negative_direction` | bool | `False` | Allow movement in negative axis direction |
| `use_project_x` | bool | `False` | Project along X |
| `use_project_y` | bool | `False` | Project along Y |
| `use_project_z` | bool | `False` | Project along Z |
| `cull_face` | Literal | `'OFF'` | Cull faces facing toward/away from projection |
| `use_invert_cull` | bool | `False` | Invert cull mode for negative direction |
| `subsurf_levels` | int | `0` | Subdivisions before extracting positions [0, 6] |
| `vertex_group` | str | `''` | Vertex group for selective influence |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |

**3D Printing use:** Conform a mesh (gasket, label, pad) to a curved surface. Use `offset` to add clearance between printed parts. Useful for generating support surfaces that follow complex contours.

---

## LaplacianSmoothModifier

`class bpy.types.LaplacianSmoothModifier(Modifier)`  
Applies Laplacian smoothing to reduce noise while preserving volume.

```python
mod = obj.modifiers.new(name="LaplacianSmooth", type='LAPLACIANSMOOTH')
mod.iterations = 10
mod.lambda_factor = 0.01
mod.use_volume_preserve = True
bpy.ops.object.modifier_apply(modifier="LaplacianSmooth")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `iterations` | int | `1` | Smoothing iterations [0, 32767] |
| `lambda_factor` | float | `0.01` | Smooth effect strength [-inf, inf] |
| `lambda_border` | float | `0.01` | Lambda for border vertices [-inf, inf] |
| `use_normalized` | bool | `True` | Improve and stabilize the enhanced shape |
| `use_volume_preserve` | bool | `True` | Apply volume preservation after smoothing |
| `use_x` | bool | `True` | Smooth along X axis |
| `use_y` | bool | `True` | Smooth along Y axis |
| `use_z` | bool | `True` | Smooth along Z axis |
| `vertex_group` | str | `''` | Vertex group for selective influence |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |

**3D Printing use:** Clean up noisy scan data or sculpted meshes while maintaining overall volume. More stable than simple smooth for preserving mass. Use `iterations = 5–20` with `lambda_factor = 0.005–0.02`.

---

## CorrectiveSmoothModifier

`class bpy.types.CorrectiveSmoothModifier(Modifier)`  
Corrects deformation artifacts caused by other modifiers/animation.

```python
mod = obj.modifiers.new(name="CorrectiveSmooth", type='CORRECTIVE_SMOOTH')
mod.factor = 0.5
mod.iterations = 5
mod.smooth_type = 'SIMPLE'
bpy.ops.object.modifier_apply(modifier="CorrectiveSmooth")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `factor` | float | `0.5` | Smooth effect strength [-inf, inf] |
| `iterations` | int | `5` | Number of smoothing iterations [0, 32767] |
| `scale` | float | `1.0` | Compensate for scale from other modifiers [-inf, inf] |
| `smooth_type` | Literal | `'SIMPLE'` | `SIMPLE` (average of adjacent edges) or `LENGTH_WEIGHTED` |
| `rest_source` | Literal | `'ORCO'` | Rest position source: `ORCO` (original coords) or `BIND` |
| `is_bind` | bool | `False` | Currently bound (readonly) |
| `use_only_smooth` | bool | `False` | Smooth without surface reconstruction |
| `use_pin_boundary` | bool | `False` | Exclude boundary vertices from smoothing |
| `vertex_group` | str | `''` | Vertex group for selective influence |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |

**3D Printing use:** Fix pinching or waviness artifacts introduced by Armature or other deform modifiers. Useful for organic shapes that need post-deformation cleanup before export.

---

## TriangulateModifier

`class bpy.types.TriangulateModifier(Modifier)`  
Converts all faces to triangles (required by many 3D print formats/slicers).

```python
mod = obj.modifiers.new(name="Triangulate", type='TRIANGULATE')
mod.quad_method = 'SHORTEST_DIAGONAL'
mod.ngon_method = 'BEAUTY'
mod.min_vertices = 4
bpy.ops.object.modifier_apply(modifier="Triangulate")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `quad_method` | Literal | `'SHORTEST_DIAGONAL'` | How to split quads: `BEAUTY`, `FIXED`, `FIXED_ALTERNATE`, `SHORTEST_DIAGONAL`, `LONGEST_DIAGONAL` |
| `ngon_method` | Literal | `'BEAUTY'` | How to split n-gons: `BEAUTY`, `CLIP` |
| `min_vertices` | int | `4` | Only triangulate polygons with >= this many vertices [4, inf] |
| `keep_custom_normals` | bool | `False` | Try to preserve custom normals (FIXED method recommended) |

**3D Printing use:** STL and many slicers require triangulated meshes. Apply before export to ensure compatibility. `SHORTEST_DIAGONAL` gives the most stable triangulation for curved surfaces. `BEAUTY` produces cleaner quads-to-triangles conversion. Alternatively use `bpy.ops.export_mesh.stl()` which auto-triangulates.

---

## WeldModifier

`class bpy.types.WeldModifier(Modifier)`  
Merges vertices within a distance threshold.

```python
mod = obj.modifiers.new(name="Weld", type='WELD')
mod.merge_threshold = 0.001   # 1 mm merge distance
mod.mode = 'ALL'
bpy.ops.object.modifier_apply(modifier="Weld")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `merge_threshold` | float | `0.001` | Vertex merge distance [0, inf] |
| `mode` | Literal | `'ALL'` | `ALL` (full merge by distance) or `CONNECTED` (only along edges) |
| `loose_edges` | bool | `False` | Collapse edges without faces (cloth sewing edges) |
| `vertex_group` | str | `''` | Vertex group for selective merging |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |

**3D Printing use:** Fix duplicate/overlapping vertices from boolean operations, imports, or array seams. Essential cleanup step before export. Use `CONNECTED` mode to only merge along edges (safer, avoids unintended topology changes).

> **Weld vs. Merge by Distance:** The Weld Modifier is the **non-destructive** counterpart to the destructive Edit Mode operation `bpy.ops.mesh.merge_by_distance()` (UI: Mesh > Clean Up > Merge by Distance). Prefer the Weld Modifier in MCP scripts — it is stackable, reversible before apply, and does not require entering Edit Mode. Apply with `bpy.ops.object.modifier_apply(modifier="Weld")` only when you need the topology change to be permanent (e.g., immediately before STL export).

---

## DisplaceModifier

`class bpy.types.DisplaceModifier(Modifier)`  
Displaces vertices using a texture's intensity.

```python
mod = obj.modifiers.new(name="Displace", type='DISPLACE')
mod.texture = my_texture
mod.strength = 0.005      # 5 mm max displacement
mod.direction = 'NORMAL'
mod.mid_level = 0.5
bpy.ops.object.modifier_apply(modifier="Displace")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `texture` | Texture | — | Source texture for displacement |
| `direction` | Literal | `'NORMAL'` | `X`, `Y`, `Z`, `NORMAL`, `CUSTOM_NORMAL`, `RGB_TO_XYZ` |
| `strength` | float | `1.0` | Displacement amount [-inf, inf] |
| `mid_level` | float | `0.5` | Texture value with zero displacement [-inf, inf] |
| `space` | Literal | `'LOCAL'` | Displacement space: `LOCAL` or `GLOBAL` |
| `texture_coords` | Literal | `'LOCAL'` | UV source: `LOCAL`, `GLOBAL`, `OBJECT`, `UV` |
| `texture_coords_object` | Object | — | Object for texture coordinate space |
| `texture_coords_bone` | str | `''` | Bone for texture coordinates |
| `uv_layer` | str | `''` | UV map name |
| `vertex_group` | str | `''` | Vertex group for selective influence |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |

**3D Printing use:** Add surface texture/relief patterns (wood grain, knurling, embossing) directly to the mesh before export. Set `mid_level = 0.5` so grey = neutral, white = raised, black = indented. Use `direction = 'NORMAL'` for consistent outward displacement.

---

## EdgeSplitModifier

`class bpy.types.EdgeSplitModifier(Modifier)`  
Splits edges at sharp angles to create hard normals for rendering. Also splits the actual mesh topology.

```python
mod = obj.modifiers.new(name="EdgeSplit", type='EDGE_SPLIT')
mod.split_angle = 0.523599   # 30 degrees
mod.use_edge_angle = True
mod.use_edge_sharp = True
bpy.ops.object.modifier_apply(modifier="EdgeSplit")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `split_angle` | float | `0.523599` | Angle above which to split edges [0, pi] (~30° default) |
| `use_edge_angle` | bool | `True` | Split edges with high angle between faces |
| `use_edge_sharp` | bool | `True` | Split edges marked as sharp |

**3D Printing use:** Separates mesh topology at hard edges for correct normal display and slicing. Applying this modifier increases vertex/face count due to topology splitting. Typically not needed for STL export but useful for cleaning up shading issues in preview.

---

## NormalEditModifier

`class bpy.types.NormalEditModifier(Modifier)`  
Generates or modifies custom vertex normals.

```python
mod = obj.modifiers.new(name="NormalEdit", type='NORMAL_EDIT')
mod.mode = 'RADIAL'
mod.mix_factor = 1.0
bpy.ops.object.modifier_apply(modifier="NormalEdit")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `mode` | Literal | `'RADIAL'` | `RADIAL` (from ellipsoid) or `DIRECTIONAL` (track target) |
| `target` | Object | — | Target object for DIRECTIONAL mode |
| `mix_factor` | float | `1.0` | Mix amount between old and new normals [0, 1] |
| `mix_limit` | float | `3.14159` | Max angle between old and new normals [0, pi] |
| `mix_mode` | Literal | `'COPY'` | `COPY`, `ADD`, `SUB`, `MUL` |
| `offset` | Vector | `(0, 0, 0)` | Offset from object center for radial mode |
| `use_direction_parallel` | bool | `True` | Use same direction for all normals (DIRECTIONAL only) |
| `no_polynors_fix` | bool | `False` | Do not flip polygons for inconsistent normals |
| `vertex_group` | str | `''` | Vertex group for selective influence |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |

**3D Printing use:** Primarily a rendering modifier; limited direct use for 3D printing. Can help correct normal direction issues on imported meshes before watertightness analysis.

---

## WeightedNormalModifier

`class bpy.types.WeightedNormalModifier(Modifier)`  
Generates custom normals weighted by face area or angle for better shading on non-uniform geometry.

```python
mod = obj.modifiers.new(name="WeightedNormal", type='WEIGHTED_NORMAL')
mod.mode = 'FACE_AREA'
mod.weight = 50
mod.keep_sharp = True
bpy.ops.object.modifier_apply(modifier="WeightedNormal")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `mode` | Literal | `'FACE_AREA'` | `FACE_AREA`, `CORNER_ANGLE`, `FACE_AREA_WITH_ANGLE` |
| `weight` | int | `50` | Corrective factor: 50 = neutral, lower = weak faces boost, higher = strong faces boost [1, 100] |
| `thresh` | float | `0.01` | Threshold for equal weights [0, 10] |
| `keep_sharp` | bool | `False` | Keep sharp edges from default normals |
| `use_face_influence` | bool | `False` | Use face influence weighting |
| `vertex_group` | str | `''` | Vertex group for selective influence |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |

**3D Printing use:** Primarily a shading modifier. Useful for correcting visual artifacts on flat-faced models (architectural parts, enclosures) in preview renders, not directly for print geometry.

---

## SimpleDeformModifier

`class bpy.types.SimpleDeformModifier(Modifier)`  
Applies simple twist, bend, taper, or stretch deformations.

```python
mod = obj.modifiers.new(name="SimpleDeform", type='SIMPLE_DEFORM')
mod.deform_method = 'BEND'
mod.angle = 1.5708        # 90 degrees bend
mod.deform_axis = 'X'
bpy.ops.object.modifier_apply(modifier="SimpleDeform")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `deform_method` | Literal | `'TWIST'` | `TWIST`, `BEND`, `TAPER`, `STRETCH` |
| `deform_axis` | Literal | `'X'` | Local axis for deformation: `X`, `Y`, `Z` |
| `angle` | float | `0.785398` | Deformation angle in radians (~45° default) [-inf, inf] |
| `factor` | float | `0.785398` | Deformation amount [-inf, inf] |
| `limits` | float[2] | `(0.0, 1.0)` | Lower/upper deformation limits [0, 1] |
| `lock_x` | bool | `False` | Lock X axis |
| `lock_y` | bool | `False` | Lock Y axis |
| `lock_z` | bool | `False` | Lock Z axis |
| `origin` | Object | — | Object defining deform origin and orientation |
| `vertex_group` | str | `''` | Vertex group for selective influence |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |

**Deform methods:**
- `TWIST`: Rotate around the Z axis (use for screws, drill bits)
- `BEND`: Bend the mesh over Z axis (use for curved ducts, hooks)
- `TAPER`: Linear scale along Z (use for tapered posts, cone-like shapes)
- `STRETCH`: Stretch along Z (use for length adjustment)

**3D Printing use:** Quickly create helical, curved, or tapered parts without manual mesh editing. Use `BEND` for curved brackets or hooks. Use `TAPER` for ergonomic grips. Set `limits` to restrict deformation to a portion of the mesh.

---

## CastModifier

`class bpy.types.CastModifier(Modifier)`  
Projects/morphs vertices toward a sphere, cylinder, or cube shape.

```python
mod = obj.modifiers.new(name="Cast", type='CAST')
mod.cast_type = 'SPHERE'
mod.factor = 0.5          # 0 = original, 1 = full sphere
mod.radius = 0.0          # 0 = infinite (all vertices)
bpy.ops.object.modifier_apply(modifier="Cast")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `cast_type` | Literal | `'SPHERE'` | Target shape: `SPHERE`, `CYLINDER`, `CUBOID` |
| `factor` | float | `0.5` | Blend between original and cast shape [-inf, inf] |
| `radius` | float | `0.0` | Only affect vertices within this radius (0 = all) [0, inf] |
| `size` | float | `0.0` | Projection shape size (0 = auto) [0, inf] |
| `use_radius_as_size` | bool | `True` | Use radius as projection shape size |
| `use_transform` | bool | `False` | Use object transform to control projection |
| `use_x` | bool | `True` | Cast on X axis |
| `use_y` | bool | `True` | Cast on Y axis |
| `use_z` | bool | `True` | Cast on Z axis |
| `object` | Object | — | Control object: location = effect center |
| `vertex_group` | str | `''` | Vertex group for selective influence |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |

**3D Printing use:** Spherify or cylindrify irregular meshes to create rounded enclosures or corrective shapes. `factor = 1.0` with `cast_type = 'SPHERE'` fully spherifies the mesh. `CUBOID` useful for squaring off rounded objects. Disable unused axes (e.g., `use_z = False`) for partial projection (cylindrical cast).
