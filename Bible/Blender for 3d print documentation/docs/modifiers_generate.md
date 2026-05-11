# Blender Generate Modifiers — Python API Reference for 3D Printing

Source: `bpy.types` — Blender Python API  
Apply pattern: `bpy.ops.object.modifier_apply(modifier="ModName")`  
Add pattern: `mod = obj.modifiers.new(name="ModName", type='TYPE_ENUM')`

---

## Modifier (base class)

`class bpy.types.Modifier(bpy_struct)`  
Base class for all modifiers. Common inherited properties on every modifier:

| Property | Type | Default | Description |
|---|---|---|---|
| `name` | str | `''` | Modifier name (used in apply call) |
| `show_viewport` | bool | `False` | Display in viewport |
| `show_render` | bool | `False` | Use during render |
| `show_in_editmode` | bool | `False` | Display in Edit mode |
| `show_on_cage` | bool | `False` | Adjust edit cage to result |
| `show_expanded` | bool | `False` | Expanded in UI |
| `is_active` | bool | `False` | Active modifier in stack |
| `use_pin_to_last` | bool | `False` | Keep at end of stack |
| `execution_time` | float | `0.0` | Eval time in seconds (readonly) |

---

## BooleanModifier

`class bpy.types.BooleanModifier(Modifier)`  
Boolean set operations between meshes.

```python
mod = obj.modifiers.new(name="Bool", type='BOOLEAN')
mod.operation = 'DIFFERENCE'   # or 'UNION', 'INTERSECT'
mod.object = cutter_obj
mod.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="Bool")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `operation` | Literal | `'DIFFERENCE'` | `INTERSECT`, `UNION`, `DIFFERENCE` |
| `operand_type` | Literal | `'OBJECT'` | `OBJECT` or `COLLECTION` |
| `object` | Object | — | Mesh object used as operand |
| `collection` | Collection | — | Collection of mesh operands |
| `solver` | Literal | `'EXACT'` | `FLOAT` (fast), `EXACT` (coplanar safe), `MANIFOLD` (fastest, manifold only) |
| `double_threshold` | float | `1e-06` | Overlap geometry threshold [0, 1] |
| `material_mode` | Literal | `'INDEX'` | `INDEX` or `TRANSFER` material assignment |
| `use_self` | bool | `False` | Allow self-intersection in operands |
| `use_hole_tolerant` | bool | `False` | Better results with holes (slower) |

**3D Printing use:** Cut holes, subtract supports, combine parts into a single manifold mesh. Use `EXACT` solver for watertight results. `MANIFOLD` solver is fastest when both meshes are already manifold.

---

## SolidifyModifier

`class bpy.types.SolidifyModifier(Modifier)`  
Adds thickness/wall to a surface mesh.

```python
mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
mod.thickness = 0.002       # 2 mm wall thickness
mod.offset = -1.0           # extrude inward
mod.use_even_offset = True
bpy.ops.object.modifier_apply(modifier="Solidify")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `thickness` | float | `0.01` | Shell thickness [-inf, inf] |
| `offset` | float | `-1.0` | Center offset: -1=inside, 0=center, 1=outside |
| `solidify_mode` | Literal | `'EXTRUDE'` | `EXTRUDE` (Simple) or `NON_MANIFOLD` (Complex/watertight) |
| `use_even_offset` | bool | `False` | Maintain thickness at sharp corners |
| `use_flip_normals` | bool | `False` | Invert face direction |
| `use_rim` | bool | `True` | Add edge loops between inner/outer surfaces |
| `use_rim_only` | bool | `False` | Only add rim to original data |
| `use_quality_normals` | bool | `False` | More even thickness normals (slow) |
| `use_flat_faces` | bool | `False` | Minimal vertex weight for parallel faces (slow) |
| `thickness_clamp` | float | `0.0` | Offset clamp based on geometry scale [0, 100] |
| `thickness_vertex_group` | float | `0.0` | Thickness factor for zero vgroup influence [0, 1] |
| `nonmanifold_thickness_mode` | Literal | `'CONSTRAINTS'` | `FIXED`, `EVEN`, `CONSTRAINTS` |
| `nonmanifold_boundary_mode` | Literal | `'NONE'` | `NONE`, `ROUND`, `FLAT` |
| `nonmanifold_merge_threshold` | float | `0.0001` | Merge threshold for degenerate geometry [0, 1] |
| `bevel_convex` | float | `0.0` | Bevel weight for outside edges [-1, 1] |
| `material_offset` | int | `0` | Material index offset for generated faces |
| `material_offset_rim` | int | `0` | Material index offset for rim faces |
| `vertex_group` | str | `''` | Vertex group driving thickness |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |

**3D Printing use:** Convert surface/shell meshes into printable walls with controlled thickness. Use `NON_MANIFOLD` mode for watertight output. Set `thickness` to minimum wall requirement (e.g., 0.8–1.2 mm for FDM).

---

## ArrayModifier

`class bpy.types.ArrayModifier(Modifier)`  
Duplicates geometry in a pattern.

```python
mod = obj.modifiers.new(name="Array", type='ARRAY')
mod.count = 5
mod.use_relative_offset = True
mod.relative_offset_displace = (1.0, 0.0, 0.0)
mod.use_merge_vertices = True
mod.merge_threshold = 0.01
bpy.ops.object.modifier_apply(modifier="Array")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `fit_type` | Literal | `'FIXED_COUNT'` | `FIXED_COUNT`, `FIT_LENGTH`, `FIT_CURVE` |
| `count` | int | `2` | Number of duplicates [1, inf] |
| `fit_length` | float | `0.0` | Length to fit array within [0, inf] |
| `curve` | Object | — | Curve object to fit length to |
| `use_relative_offset` | bool | `True` | Offset relative to object bounding box |
| `relative_offset_displace` | Vector | `(1.0, 0.0, 0.0)` | Relative offset per duplicate |
| `use_constant_offset` | bool | `False` | Add a constant offset |
| `constant_offset_displace` | Vector | `(1.0, 0.0, 0.0)` | Constant distance between items |
| `use_object_offset` | bool | `False` | Use another object's transform for offset |
| `offset_object` | Object | — | Object defining distance and rotation |
| `use_merge_vertices` | bool | `False` | Merge vertices in adjacent duplicates |
| `use_merge_vertices_cap` | bool | `False` | Merge vertices in first and last duplicates |
| `merge_threshold` | float | `0.01` | Limit below which to merge vertices |
| `start_cap` | Object | — | Mesh object as start cap |
| `end_cap` | Object | — | Mesh object as end cap |
| `offset_u` | float | `0.0` | UV offset on U axis [-1, 1] |
| `offset_v` | float | `0.0` | UV offset on V axis [-1, 1] |

**3D Printing use:** Create repeated patterns (grilles, teeth, ribs), linear arrays of fastener holes, or fill a given length. Enable `use_merge_vertices` for seamless joints.

---

## MirrorModifier

`class bpy.types.MirrorModifier(Modifier)`  
Mirrors geometry across one or more axes.

```python
mod = obj.modifiers.new(name="Mirror", type='MIRROR')
mod.use_axis[0] = True      # mirror on X
mod.use_bisect_axis[0] = True
mod.use_mirror_merge = True
mod.merge_threshold = 0.001
bpy.ops.object.modifier_apply(modifier="Mirror")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `use_axis` | bool[3] | `(False, False, False)` | Enable mirror per axis (X, Y, Z) |
| `use_bisect_axis` | bool[3] | `(False, False, False)` | Cut mesh across the mirror plane |
| `use_bisect_flip_axis` | bool[3] | `(False, False, False)` | Flip direction of the bisect cut |
| `use_mirror_merge` | bool | `True` | Merge vertices within threshold |
| `merge_threshold` | float | `0.001` | Vertex merge distance [0, inf] |
| `bisect_threshold` | float | `0.001` | Vertices within this distance of bisect plane are removed |
| `use_clip` | bool | `False` | Prevent vertices crossing the mirror plane |
| `mirror_object` | Object | — | Custom mirror center object |
| `use_mirror_vertex_groups` | bool | `True` | Mirror vertex groups (e.g. .R -> .L) |
| `use_mirror_u` | bool | `False` | Mirror U texture coordinate |
| `use_mirror_v` | bool | `False` | Mirror V texture coordinate |
| `use_mirror_udim` | bool | `False` | Mirror UV around each tile center |
| `mirror_offset_u` | float | `0.0` | UV flip point offset on U [-1, 1] |
| `mirror_offset_v` | float | `0.0` | UV flip point offset on V [-1, 1] |

**3D Printing use:** Model only half of a symmetrical part (bracket, enclosure, clip) then mirror. Use `use_bisect_axis` to ensure clean zero-thickness seam. Always enable `use_mirror_merge` for a watertight result.

---

## RemeshModifier

`class bpy.types.RemeshModifier(Modifier)`  
Generates new regular topology following the shape of the input mesh.

```python
mod = obj.modifiers.new(name="Remesh", type='REMESH')
mod.mode = 'VOXEL'
mod.voxel_size = 0.005   # 5 mm resolution
mod.adaptivity = 0.0
bpy.ops.object.modifier_apply(modifier="Remesh")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `mode` | Literal | `'VOXEL'` | `BLOCKS`, `SMOOTH`, `SHARP`, `VOXEL` |
| `voxel_size` | float | `0.1` | Voxel side length in object space; smaller = finer [0, inf] |
| `adaptivity` | float | `0.0` | Reduce face count where detail not needed (>0 disables Fix Poles) |
| `octree_depth` | int | `4` | Resolution for non-voxel modes [1, 24] |
| `scale` | float | `0.9` | Largest dimension over grid size ratio [0, 0.99] |
| `sharpness` | float | `1.0` | Sharp mode outlier tolerance; lower = more noise filtering |
| `threshold` | float | `1.0` | Min component size to preserve (ratio vs largest component) [0, 1] |
| `use_remove_disconnected` | bool | `True` | Remove disconnected pieces below threshold |
| `use_smooth_shade` | bool | `False` | Output smooth shading |

**3D Printing use:** Fix non-manifold, self-intersecting, or messy topology before export. `VOXEL` mode produces watertight meshes. Lower `voxel_size` for higher detail. `SHARP` preserves hard edges.

---

## ScrewModifier

`class bpy.types.ScrewModifier(Modifier)`  
Revolves a profile along an axis (lathe operation).

```python
mod = obj.modifiers.new(name="Screw", type='SCREW')
mod.axis = 'Z'
mod.angle = 6.28319      # full 360 degrees
mod.steps = 64
mod.screw_offset = 0.0   # 0 = pure rotation, >0 = helical
bpy.ops.object.modifier_apply(modifier="Screw")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `axis` | Literal | `'Z'` | Revolution axis: `X`, `Y`, `Z` |
| `angle` | float | `6.28319` | Full revolution angle in radians (6.28319 = 360°) |
| `steps` | int | `16` | Steps in viewport revolution [1, 10000] |
| `render_steps` | int | `16` | Steps during render [1, 10000] |
| `iterations` | int | `1` | Number of times to apply the screw [1, 10000] |
| `screw_offset` | float | `0.0` | Translation along axis per revolution (creates helix) |
| `object` | Object | — | Object defining the screw axis |
| `use_object_screw_offset` | bool | `False` | Use distance between objects for screw offset |
| `use_merge_vertices` | bool | `False` | Merge adjacent vertices (offset must be zero) |
| `merge_threshold` | float | `0.01` | Merge vertex limit |
| `use_normal_calculate` | bool | `False` | Calculate edge order (needed for raw meshes) |
| `use_normal_flip` | bool | `False` | Flip normals of lathed faces |
| `use_smooth_shade` | bool | `True` | Output smooth shading |
| `use_stretch_u` | bool | `False` | Stretch U coords 0–1 |
| `use_stretch_v` | bool | `False` | Stretch V coords 0–1 |

**3D Printing use:** Generate rotationally symmetric objects (vases, bowls, threaded rods, bottle necks) from a 2D profile curve. Set `steps = 64–128` for smooth cylinders. Use `screw_offset` for helical threads.

---

## SkinModifier

`class bpy.types.SkinModifier(Modifier)`  
Generates a skin mesh from vertices and edges (wire frame skeleton).

```python
mod = obj.modifiers.new(name="Skin", type='SKIN')
mod.branch_smoothing = 0.5
mod.use_x_symmetry = True
bpy.ops.object.modifier_apply(modifier="Skin")
```

Vertex radii are controlled via `MeshSkinVertex` attributes in Edit Mode (Ctrl+A to resize skin).

| Property | Type | Default | Description |
|---|---|---|---|
| `branch_smoothing` | float | `0.0` | Smooth complex geometry around branches [0, 1] |
| `use_smooth_shade` | bool | `False` | Output smooth shading |
| `use_x_symmetry` | bool | `True` | Avoid unsymmetrical quads across X |
| `use_y_symmetry` | bool | `False` | Avoid unsymmetrical quads across Y |
| `use_z_symmetry` | bool | `False` | Avoid unsymmetrical quads across Z |

**3D Printing use:** Quickly build organic lattice structures, armatures, and branching support frameworks from a simple wire skeleton. Combine with Subdivision Surface for smooth organic shapes.

---

## WireframeModifier

`class bpy.types.WireframeModifier(Modifier)`  
Converts faces to a wireframe of tubes along their edges.

```python
mod = obj.modifiers.new(name="Wireframe", type='WIREFRAME')
mod.thickness = 0.02
mod.use_even_offset = True
mod.use_replace = True
bpy.ops.object.modifier_apply(modifier="Wireframe")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `thickness` | float | `0.02` | Wire tube thickness |
| `offset` | float | `0.0` | Offset from center |
| `use_even_offset` | bool | `True` | Scale offset for even thickness |
| `use_relative_offset` | bool | `False` | Scale offset by surrounding geometry |
| `use_replace` | bool | `True` | Remove original geometry |
| `use_boundary` | bool | `False` | Support face boundaries |
| `use_crease` | bool | `False` | Crease hub edges for subdivision |
| `crease_weight` | float | `1.0` | Crease weight value |
| `material_offset` | int | `0` | Material index offset for generated faces |
| `thickness_vertex_group` | float | `0.0` | Thickness factor for zero vgroup influence [0, 1] |
| `vertex_group` | str | `''` | Vertex group for affected areas |
| `invert_vertex_group` | bool | `False` | Invert vertex group influence |

**3D Printing use:** Create open-cell lattice/grid structures that reduce material weight while maintaining shape. Set `thickness` to minimum printable line width (e.g., 0.4–0.8 mm for FDM). Enable `use_even_offset` for uniform struts.

---

## VolumeToMeshModifier

`class bpy.types.VolumeToMeshModifier(Modifier)`  
Converts a Volume object (VDB) to a mesh.

```python
mod = obj.modifiers.new(name="VolToMesh", type='VOLUME_TO_MESH')
mod.object = volume_obj
mod.resolution_mode = 'VOXEL_SIZE'
mod.voxel_size = 0.005
mod.threshold = 0.0
bpy.ops.object.modifier_apply(modifier="VolToMesh")
```

| Property | Type | Default | Description |
|---|---|---|---|
| `object` | Object | — | Source Volume object |
| `grid_name` | str | `''` | VDB grid name to convert |
| `resolution_mode` | Literal | `'GRID'` | `GRID`, `VOXEL_AMOUNT`, `VOXEL_SIZE` |
| `voxel_size` | float | `0.0` | Desired voxel side length (smaller = finer) [0, inf] |
| `voxel_amount` | int | `0` | Approximate voxels along one axis [0, inf] |
| `threshold` | float | `0.0` | Voxels above this value are inside the mesh [0, inf] |
| `adaptivity` | float | `0.0` | Simplify geometry where detail not needed [0, 1] |
| `use_smooth_shade` | bool | `False` | Output smooth shading |

**3D Printing use:** Convert fluid simulations, medical scan volumes (CT/MRI as VDB), or procedural volumes into printable meshes. Use `VOXEL_SIZE` mode for predictable resolution control.

---

## ObjectModifiers Collection

`class bpy.types.ObjectModifiers(bpy_prop_collection)`  
Collection of modifiers on an object, accessed via `obj.modifiers`.

```python
# Add modifier
mod = obj.modifiers.new(name="MyMod", type='BOOLEAN')

# Access by name
mod = obj.modifiers["MyMod"]

# Iterate all modifiers
for mod in obj.modifiers:
    print(mod.name, mod.type)

# Remove a modifier
obj.modifiers.remove(mod)

# Clear all modifiers
obj.modifiers.clear()

# Apply all modifiers in stack
import bpy
bpy.ops.object.convert(target='MESH')

# Apply single modifier
bpy.ops.object.modifier_apply(modifier="MyMod")

# Move modifier in stack
obj.modifiers.move(from_index=0, to_index=1)
```

**Note:** `modifier_apply` requires the object to be the active object: `bpy.context.view_layer.objects.active = obj`
