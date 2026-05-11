# Geometry Nodes — Blender Python API

Geometry Nodes is Blender's procedural, non-destructive system for modifying mesh geometry via a visual node graph. From Python, you interact with the underlying data structures: `NodeTree`, `Node`, `NodeSocket`, and `NodeLink`.

---

## Core Data Structure

A Geometry Nodes setup has two Python-accessible layers:

1. **The modifier** — `bpy.types.NodesModifier` (type string `'NODES'`) attached to an object
2. **The node group** — `bpy.types.GeometryNodeTree`, a `NodeTree` subclass containing the actual node graph

These are linked: `modifier.node_group = node_tree`.

```python
mod = obj.modifiers.new("GeoNodes", type='NODES')
tree = bpy.data.node_groups.new("MyGeoNodes", 'GeometryNodeTree')
mod.node_group = tree
```

---

## bpy.types.NodeTree

`NodeTree(ID)` is the base class. `GeometryNodeTree` inherits from it.

| Property | Type | Notes |
|---|---|---|
| `nodes` | `Nodes[Node]` | Collection of all nodes in the tree (readonly) |
| `links` | `NodeLinks[NodeLink]` | Collection of all links between sockets (readonly) |
| `interface` | `NodeTreeInterface` | Group I/O socket declarations |
| `type` | enum str | `'GEOMETRY'` for GeoNodes (deprecated; use `bl_idname`) |
| `animation_data` | `AnimData` | For animating node parameters |

---

## bpy.types.GeometryNodeTree

`GeometryNodeTree(NodeTree)` adds context-specific flags:

| Property | Type | Notes |
|---|---|---|
| `is_modifier` | bool | True when the tree is used as a modifier on an object |
| `is_tool` | bool | True when used as a sculpt/paint tool |
| `is_type_mesh` | bool | Configured for mesh geometry |
| `is_type_curve` | bool | Configured for curve geometry |
| `is_mode_edit` | bool | Used in edit mode |

These flags affect which node types are available in the UI but do not restrict Python access.

---

## bpy.types.Nodes (collection)

`nodes` on a `NodeTree` is a `Nodes(bpy_prop_collection)`:

| Method/Property | Signature | Notes |
|---|---|---|
| `new(type)` | `(type: str) → Node` | `type` is `bl_idname` (e.g., `'GeometryNodeMeshBoolean'`), **not** `node.type` |
| `remove(node)` | `(node: Node)` | Removes node and all its links |
| `clear()` | `()` | Remove all nodes |
| `active` | `Node` | The currently active/selected node |

The `type` parameter to `nodes.new()` must be the `bl_idname` string. Using the deprecated `type` attribute value (short uppercase name) will not work.

---

## bpy.types.Node

`Node(bpy_struct)` represents a single node in a tree.

| Property | Type | Notes |
|---|---|---|
| `name` | str | Unique identifier within the tree |
| `label` | str | Optional display label |
| `type` | str | Legacy short type identifier (readonly); use `bl_idname` for node creation |
| `bl_idname` | str | Full type identifier used with `nodes.new()` |
| `location` | `mathutils.Vector` | 2D position within the node editor canvas |
| `inputs` | `NodeInputs[NodeSocket]` | Input sockets (readonly) |
| `outputs` | `NodeOutputs[NodeSocket]` | Output sockets (readonly) |
| `hide` | bool | Whether node is collapsed |
| `mute` | bool | Whether node is bypassed |
| `parent` | `Node` | Frame node this node belongs to |

Accessing input default values (for unlinked sockets):
```python
node.inputs[0].default_value = 1.0
node.inputs["Value"].default_value = 0.5  # also accessible by name
```

---

## bpy.types.NodeSocket

`NodeSocket(bpy_struct)` is a socket on a node.

| Property | Type | Notes |
|---|---|---|
| `name` | str | Display name |
| `identifier` | str | Stable identifier for the socket (readonly) |
| `type` | enum str | Data type: `'VALUE'`, `'INT'`, `'BOOLEAN'`, `'VECTOR'`, `'GEOMETRY'`, etc. |
| `default_value` | varies | The socket's value when not linked |
| `is_linked` | bool | True if a link exists (readonly) |
| `is_output` | bool | True if this is an output socket (readonly) |
| `enabled` | bool | Whether the socket is active |
| `hide` | bool | Whether hidden in UI |
| `node` | `Node` | Owning node (readonly) |
| `links` | `NodeLinks` | Connected links (readonly; O(len(tree.links)) lookup) |

### Socket subclasses and their `default_value` types

| Type | Python class | `default_value` |
|---|---|---|
| Float | `NodeSocketFloat` | `float` in (-∞, ∞) |
| Int | `NodeSocketInt` | `int` in (-∞, ∞) |
| Bool | `NodeSocketBool` | `bool` |
| Vector | `NodeSocketVector` | `bpy_prop_array[float]`, 3 items |
| Geometry | `NodeSocketGeometry` | No `default_value` — geometry flows from other nodes only |

---

## bpy.types.NodeLink

`NodeLink(bpy_struct)` represents a connection between two sockets.

| Property | Type | Notes |
|---|---|---|
| `from_node` | `Node` | Source node (readonly) |
| `from_socket` | `NodeSocket` | Source socket (readonly) |
| `to_node` | `Node` | Target node (readonly) |
| `to_socket` | `NodeSocket` | Target socket (readonly) |
| `is_valid` | bool | False if types are incompatible (readonly) |
| `is_muted` | bool | True if link is bypassed |

---

## bpy.types.NodeLinks (collection)

`tree.links` is a `NodeLinks(bpy_prop_collection)`:

| Method | Signature | Notes |
|---|---|---|
| `new(input, output)` | `(input: NodeSocket, output: NodeSocket, *, verify_limits=True, handle_dynamic_sockets=False) → NodeLink` | Creates a link; parameter naming is counterintuitive — `input` is the receiving socket (to_socket), `output` is the emitting socket (from_socket) |
| `remove(link)` | `(link: NodeLink)` | Remove a specific link |
| `clear()` | `()` | Remove all links |

Note: `NodeLinks.new(input, output)` — the `input` parameter is the **destination** socket (node input side), and `output` is the **source** socket (node output side). This is the opposite of what the names imply.

```python
link = tree.links.new(to_node.inputs[0], from_node.outputs[0])
```

---

## Group Input/Output Nodes

Every node group has special `NodeGroupInput` and `NodeGroupOutput` nodes that define the group's interface:

```python
# These exist automatically but can be found by type
input_node = None
output_node = None
for node in tree.nodes:
    if node.type == 'GROUP_INPUT':
        input_node = node
    elif node.type == 'GROUP_OUTPUT':
        output_node = node
```

Group interface sockets are managed via `tree.interface` (a `NodeTreeInterface`). Adding interface sockets from Python:
```python
tree.interface.new_socket("Value", in_out='INPUT', socket_type='NodeSocketFloat')
tree.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
```

---

## Accessing Modifier Input Values

After creating the modifier and node group, input values on the modifier panel correspond to exposed group inputs:

```python
# After setting up a group with interface inputs, access via modifier
mod["Input_0"] = 1.0          # by identifier (auto-generated: Input_0, Input_1, ...)
mod["Socket_1"] = 0.5         # or by socket identifier

# Alternatively, access via the node group directly
group_input_node = next(n for n in tree.nodes if n.type == 'GROUP_INPUT')
group_input_node.outputs["Value"].default_value = 1.0  # sets the internal default
```

The modifier's exposed inputs can be iterated:
```python
for key in mod.keys():
    print(key, mod[key])
```

---

## Key Geometry Node Types for 3D Printing

These are `bl_idname` strings for `nodes.new()`. The table covers nodes most relevant to mesh work:

| `bl_idname` | Purpose |
|---|---|
| `'GeometryNodeMeshBoolean'` | Boolean union/intersect/difference between meshes; has `operation` enum: `'UNION'`, `'INTERSECT'`, `'DIFFERENCE'` |
| `'GeometryNodeSubdivisionSurface'` | Catmull-Clark subdivision; inputs: `Mesh`, `Level` (int) |
| `'GeometryNodeMeshToPoints'` | Convert mesh faces/edges/verts to a point cloud |
| `'GeometryNodeDistributePointsOnFaces'` | Scatter points over faces by density or count; Poisson disk or random modes |
| `'GeometryNodeInstanceOnPoints'` | Instantiate an object/collection at each point (non-destructive copies) |
| `'GeometryNodeRealizeInstances'` | Collapse instances to actual geometry (required before further mesh ops) |
| `'GeometryNodeJoinGeometry'` | Merge multiple geometry streams into one (equivalent to joining meshes) |
| `'GeometryNodeTransform'` | Apply translation/rotation/scale to geometry; inputs: `Geometry`, `Translation` (Vector), `Rotation`, `Scale` |
| `'GeometryNodeSetPosition'` | Displace vertex positions; inputs: `Geometry`, `Position` (Vector), `Offset` (Vector) |
| `'GeometryNodeInputPosition'` | Outputs current vertex positions as a Vector field |
| `'GeometryNodeInputNormal'` | Outputs face normals as a Vector field |
| `'GeometryNodeMeshCube'` / `'GeometryNodeMeshCylinder'` / `'GeometryNodeMeshUVSphere'` | Primitive mesh generators |
| `'GeometryNodeMeshLine'` | Generate a line/segment mesh |
| `'ShaderNodeValue'` | Float constant input (reusable in geometry context) |
| `'FunctionNodeInputVector'` | Vector constant input |
| `'FunctionNodeInputBool'` | Boolean constant |
| `'FunctionNodeInputInt'` | Integer constant |
| `'GeometryNodeGroup'` | Embed a sub-group tree inside another |

---

## Building a Minimal GeoNodes Graph

This illustrates the API structure — not a recipe, but a demonstration of how all parts connect:

```python
import bpy

# Create tree and modifier
tree = bpy.data.node_groups.new("TestGeoNodes", 'GeometryNodeTree')
mod = obj.modifiers.new("GeoNodes", type='NODES')
mod.node_group = tree

# Set up group interface (Blender 4.x API)
tree.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
tree.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

# Add group I/O nodes
group_in = tree.nodes.new('NodeGroupInput')
group_in.location = (-300, 0)
group_out = tree.nodes.new('NodeGroupOutput')
group_out.location = (300, 0)

# Add a transform node
transform = tree.nodes.new('GeometryNodeTransform')
transform.location = (0, 0)
transform.inputs["Translation"].default_value = (0, 0, 0.01)  # 10mm up with scale=0.001

# Wire: group_in.Geometry → transform.Geometry → group_out.Geometry
tree.links.new(transform.inputs["Geometry"], group_in.outputs["Geometry"])
tree.links.new(group_out.inputs["Geometry"], transform.outputs["Geometry"])
```

---

## GeoNodes vs Alternatives — When to Choose What

| Scenario | Preferred approach | Reason |
|---|---|---|
| One-off mesh modification (scale, translate) | Direct `obj.matrix_world` / `bpy.ops` / bmesh | Much simpler; GeoNodes setup overhead not justified |
| Non-destructive parametric pattern | GeoNodes | Parameters stay editable; modifier stack preserved |
| Distributing objects over a surface | GeoNodes (`InstanceOnPoints`) | Purpose-built; handles large counts efficiently |
| Repeating lattice/grid of objects | GeoNodes | Natural fit |
| Custom surface displacement | `DisplaceModifier` + `Texture` | Simpler than GeoNodes `SetPosition` + noise; direct Python API |
| Boolean operations | Either `BooleanModifier` or `GeometryNodeMeshBoolean` | GeoNodes boolean is non-destructive and can combine multiple |
| Export-ready final mesh | `modifier_apply()` or `depsgraph.evaluated_get()` | GeoNodes result must be realized before export |

GeoNodes is powerful but has high Python setup cost — each node must be created individually, positioned, and wired. For scripts that run once (not building reusable parametric setups), direct bmesh operations or standard modifiers are usually faster to implement and easier to debug.

**Key gotcha:** Node socket indices can shift when node `inputs`/`outputs` are reordered or when the node has dynamic sockets. Prefer accessing by name (`node.inputs["Geometry"]`) over index (`node.inputs[0]`) for robustness. However, names are not always unique — when a node has multiple sockets of the same name, use index.
