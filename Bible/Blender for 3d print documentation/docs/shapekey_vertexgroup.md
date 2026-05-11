# Shape Keys and Vertex Groups — Blender Python API

Covers `bpy.types.VertexGroup`, `bpy.types.VertexGroups`, `bpy.types.VertexGroupElement`,
`bpy.types.ShapeKey`, `bpy.types.ShapeKeyPoint`, and `bpy.types.Key`.
Focused on FDM 3D printing use cases.

---

## VertexGroup (`bpy.types.VertexGroup`)

A `VertexGroup` is a named subset of vertices on a mesh object, each vertex carrying a
weight in [0.0, 1.0]. Vertex groups live on the object (not the mesh data), so they
survive data-block swaps that keep the same object.

### Properties

| Property | Type | Range / Default | Notes |
|---|---|---|---|
| `name` | `str` | default `''` | Unique identifier; rename by assignment |
| `index` | `int` | [0, ∞), readonly | Position in `obj.vertex_groups`; used by `VertexGroupElement.group` |
| `lock_weight` | `bool` | default `False` | Prevents weight-paint tools from modifying the group; does not affect Python writes |

### Methods

**`add(index, weight, type)`**

Assigns a weight to one or more vertices. The `index` parameter is a sequence of integer
vertex indices (not a single int). The `type` enum controls how the new weight interacts
with any existing weight on those vertices:

| `type` value | Behaviour |
|---|---|
| `'REPLACE'` | Overwrites the current weight unconditionally |
| `'ADD'` | Adds `weight` to the current weight (clamped to 1.0) |
| `'SUBTRACT'` | Subtracts `weight` from the current weight (clamped to 0.0) |

`'REPLACE'` is the expected choice when building groups from scratch via script.

**`remove(index)`**

Removes the listed vertex indices from the group entirely. Has no effect on indices that
are not already members.

**`weight(index) → float`**

Returns the weight of a single vertex (by integer index) in [0.0, 1.0]. Raises a
`RuntimeError` if the vertex is not a member of the group — callers should iterate
`mesh.vertices[i].groups` to test membership before querying.

---

## VertexGroups collection (`obj.vertex_groups`)

`bpy.types.VertexGroups` is a `bpy_prop_collection` of `VertexGroup` objects accessible
as `obj.vertex_groups` on any mesh (or lattice) object. It is iterable and supports
name-based lookup (`obj.vertex_groups["TopHalf"]`).

### Properties

| Property | Type | Notes |
|---|---|---|
| `active` | `VertexGroup` | The currently selected group in the UI; assignable |
| `active_index` | `int` [0, ∞) | Index of the active group; synced with `active` |

### Methods

| Method | Return | Notes |
|---|---|---|
| `new(*, name='Group')` | `VertexGroup` | Creates and returns a new empty group |
| `remove(group)` | — | Deletes a `VertexGroup` instance; shifts indices of subsequent groups |
| `clear()` | — | Removes all groups from the object |

After `remove()` all previously obtained `index` values for groups after the deleted one
are invalidated — re-query them if needed.

---

## VertexGroupElement (`bpy.types.VertexGroupElement`)

A `VertexGroupElement` is a lightweight record that pairs a vertex group index with a
weight. It is what you get when iterating `mesh.vertices[i].groups`.

### Properties

| Property | Type | Range / Default | Notes |
|---|---|---|---|
| `group` | `int` | [0, ∞), readonly | Index into `obj.vertex_groups`; resolve the name with `obj.vertex_groups[elem.group].name` |
| `weight` | `float` | [0.0, 1.0], default 0.0 | Current weight of this vertex in that group |

`VertexGroupElement` instances are read from `MeshVertex.groups` (and `LatticePoint.groups`).
A vertex carries one element per group it belongs to; vertices not in any group have an
empty `groups` collection.

---

## Accessing vertex groups from mesh data

`obj.data.vertices[i].groups` returns a collection of `VertexGroupElement` items.
This is the path to read all membership information for a specific vertex. The `group`
field on each element is the group's index, not its name.

A common pattern to read all weights for a vertex:

```python
mesh = obj.data
for vert in mesh.vertices:
    for elem in vert.groups:
        grp_name = obj.vertex_groups[elem.group].name
        # elem.weight is the weight in [0.0, 1.0]
```

Writing weights back via `VertexGroupElement.weight` is possible but the preferred route
for bulk assignments is `VertexGroup.add()` with `type='REPLACE'`, which is faster and
more explicit. After any programmatic change to vertex data, call `obj.data.update()` to
propagate changes to the evaluated mesh.

---

## Using vertex groups as modifier masks

Many Blender deform and generate modifiers expose a `vertex_group` string property
(the group name, not the index) that restricts the modifier's influence to the specified
group, scaled by each vertex's weight. The `invert_vertex_group` bool reverses the mask
so that weight 0.0 means full effect and 1.0 means no effect.

### Modifiers with vertex group masking

| Modifier type | Property name(s) | What the mask controls |
|---|---|---|
| `DISPLACE` | `vertex_group` | Which vertices are displaced and by how much |
| `SMOOTH` | `vertex_group` | Smoothing influence per vertex |
| `SOLIDIFY` | `vertex_group`, `invert_vertex_group` | Thickness scaling; weight drives shell offset |
| `SHRINKWRAP` | `vertex_group` | Projection strength per vertex |
| `WARP` | `vertex_group` | Warp falloff |
| `CAST` | `vertex_group` | Cast effect strength |
| `WAVE` | `vertex_group` | Wave amplitude |
| `SIMPLE_DEFORM` | `vertex_group`, `invert_vertex_group` | Deform region |
| `LATTICE` | `vertex_group` | Lattice deformation influence |
| `HOOK` | `vertex_group` | Hook pull strength |

Setting the modifier's `vertex_group` property to an empty string `""` disables masking.
The value must match exactly the name of an existing `VertexGroup` on the object.

```python
mod = obj.modifiers["Displace"]
mod.vertex_group = "TopHalf"
mod.invert_vertex_group = False
```

For FDM printing this pattern enables spatially selective deformations — for example,
adding a surface texture only to the top face of a part while the flat print bed face
stays planar.

---

## ShapeKey (`bpy.types.ShapeKey`)

A `ShapeKey` represents one named deformation state of a mesh. Its `data` collection
holds one `ShapeKeyPoint` per vertex, storing the displaced position of that vertex when
the shape key is fully active. The Basis shape key (index 0) stores the undeformed
positions.

### Properties

| Property | Type | Range / Default | Notes |
|---|---|---|---|
| `name` | `str` | default `''` | Display name; also used as key in `key_blocks` |
| `value` | `float` | [0.0, 1.0], default 0.0 | Blend factor; 0 = no effect, 1 = full displacement |
| `mute` | `bool` | default `False` | When `True`, shape key has no effect regardless of `value` |
| `relative_key` | `ShapeKey` | never `None` | The reference shape for relative mode; defaults to Basis |
| `vertex_group` | `str` | default `''` | Name of a `VertexGroup` that masks the blend; empty string = no mask |
| `slider_min` | `float` | [-10, 10], default 0.0 | Lower bound shown in UI slider |
| `slider_max` | `float` | [-10, 10], default 1.0 | Upper bound shown in UI slider |
| `lock_shape` | `bool` | default `False` | Prevents accidental sculpt/edit of the shape |
| `data` | `bpy_prop_collection[UnknownType]` | readonly | Legacy access to shape key point data |
| `points` | `bpy_prop_collection[ShapeKeyPoint]` | readonly | Optimised access via `foreach_get`/`foreach_set`; not available for curve shape keys |
| `interpolation` | enum | default `'KEY_LINEAR'` | Interpolation for absolute keys: `KEY_LINEAR`, `KEY_CARDINAL`, `KEY_CATMULL_ROM`, `KEY_BSPLINE` |
| `frame` | `float` | readonly | Frame position for absolute keys |

`value` above 0.0 directly deforms the evaluated mesh at render/export time. Shape keys
do not modify the stored base mesh coordinates — the deformation is applied during mesh
evaluation by the dependency graph.

---

## ShapeKeyPoint (`bpy.types.ShapeKeyPoint`)

A `ShapeKeyPoint` holds the absolute local-space coordinates of one vertex in a specific
shape key state.

### Properties

| Property | Type | Range / Default | Notes |
|---|---|---|---|
| `co` | `mathutils.Vector` | array of 3 floats, default (0,0,0) | Absolute local position of the vertex in this shape key |

`co` is the full position, not an offset. The displacement relative to the basis is
`shapekey.data[i].co - basis.data[i].co`.

The preferred way to read or write all positions in bulk is `foreach_get`/`foreach_set`
via `shapekey.points`:

```python
import numpy as np
sk = obj.data.shape_keys.key_blocks["Deformed"]
coords = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
sk.points.foreach_get("co", coords)
coords = coords.reshape(-1, 3)
```

---

## Key (`bpy.types.Key`)

`Key` is the ID data-block that owns all shape keys for a mesh, lattice, or curve. It is
accessed as `obj.data.shape_keys` and is `None` when no shape keys exist.

### Properties

| Property | Type | Notes |
|---|---|---|
| `key_blocks` | `bpy_prop_collection[ShapeKey]` | Ordered collection of all shape keys including Basis; readonly |
| `reference_key` | `ShapeKey` | The Basis shape key (index 0); readonly, never `None` |
| `use_relative` | `bool` | `True` = relative mode (each key blends from its `relative_key`); `False` = absolute/sequence mode driven by `eval_time` |
| `eval_time` | `float` | [0, 1048570], default 0.0 | Evaluation time for absolute (sequence) shape keys |
| `user` | `ID` | The mesh/curve/lattice data-block that owns this Key; readonly |

**Relative mode** (`use_relative=True`) is the standard for 3D printing: each shape key
independently blends from its `relative_key` (usually Basis) by its `value`. Multiple
shape keys can be active simultaneously and their displacements accumulate.

**Absolute mode** (`use_relative=False`) treats the keys as animation frames ordered by
their `frame` values and driven by `eval_time`. This mode is rarely useful for static
print geometry.

---

## Accessing and creating shape keys

`obj.data.shape_keys` is the `Key` object (or `None` if no shape keys have been added).
Shape keys are created and removed through methods on the `Object`, not on the mesh data.

| Operation | API | Notes |
|---|---|---|
| Create a shape key | `obj.shape_key_add(name='', from_mix=True)` | `from_mix=False` copies current mesh positions; `from_mix=True` captures the evaluated (mixed) state |
| Remove all shape keys | `obj.shape_key_clear()` | Also destroys the `Key` data-block |
| Remove one shape key | `obj.shape_key_remove(key)` | Accepts a `ShapeKey` instance |
| Access the Key block | `obj.data.shape_keys` | Returns `Key` or `None` |
| Read/write blend value | `obj.data.shape_keys.key_blocks["MyKey"].value = 0.5` | Value in [0.0, 1.0] |
| Iterate all keys | `for sk in obj.data.shape_keys.key_blocks: ...` | Includes Basis at index 0 |

The first shape key created becomes the Basis (`reference_key`). Subsequent keys are
relative to the Basis by default. Deleting the Basis while other keys exist is not
possible through the normal API.

---

## Applying shape keys permanently (baking)

Shape key values above 0.0 deform the mesh during depsgraph evaluation but do not alter
the stored base mesh vertex coordinates. The underlying `obj.data.vertices` positions
always reflect the Basis shape.

To permanently bake the current mixed state into geometry:

```python
import bpy
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
baked_mesh = bpy.data.meshes.new_from_object(eval_obj)
# baked_mesh now contains actual vertex positions with all shape key values applied
```

Alternatively, the "Apply as Shape Key" and "New Shape from Mix" operators bake into a
new shape key without removing existing ones.

The Shape Keys modifier (added automatically when shape keys exist) cannot be manually
applied from Python; the `new_from_object` / `to_mesh` route is the reliable approach
for generating final export geometry.

---

## For 3D printing (FDM context)

**Shape keys** provide parametric, non-destructive deformation. A single mesh can encode
multiple geometric variants (different wall thicknesses, embossed text on/off, tolerance
adjustments) by storing them as shape keys, all within one `.blend` file. Setting
`value = 1.0` on a key and exporting the evaluated mesh via `new_from_object` produces
the variant geometry without permanently altering the base mesh.

**Vertex groups** are primarily useful in 3D printing scripts as modifier masks.
Assigning vertices of a flat bottom face weight 0.0 in a group used by a Displace
modifier ensures that the print bed contact surface is unaffected while the rest of the
model receives texture or topology changes.

**Data update requirement**: after programmatically modifying vertex group weights or
shape key point coordinates, call `obj.data.update()` to ensure the change is visible
to the depsgraph. Without this, `new_from_object` may return stale geometry.

```python
# After bulk weight assignment:
obj.data.update()

# After modifying shape key point positions directly:
obj.data.shape_keys.key_blocks["MyKey"].data[0].co = (x, y, z)
obj.data.update()
```
