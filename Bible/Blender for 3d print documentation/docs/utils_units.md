# Utilities, Units & Custom Properties — Blender Python API

This document covers `bpy.utils`, `bpy.utils.units`, `bpy.app`, `bl_math`, and the ID property (custom property) system — utility APIs frequently needed when writing 3D print automation scripts.

---

## bpy.utils.units — Unit Conversion (Critical for 3D Printing)

Blender's internal coordinate system uses **Blender Units (BU)**. The relationship between BU and real-world units depends on `scene.unit_settings.scale_length`:

- Default: `scale_length = 1.0` → 1 BU = 1 meter
- For 3D printing: `scale_length = 0.001` → 1 BU = 1 millimeter

**All mesh vertex coordinates are always in BU.** `unit_settings` only affects display and operator UI — it does not rescale the mesh. If you set `scale_length = 0.001` and create a cube with size `1.0`, it is 1mm × 1mm × 1mm.

### bpy.utils.units.to_value

```python
bpy.utils.units.to_value(unit_system, unit_category, str_input, *, str_ref_unit=None) → float
```

Converts a human-readable string to a raw float value in **the unit system's base unit**.

| Parameter | Type | Notes |
|---|---|---|
| `unit_system` | str | `'METRIC'`, `'IMPERIAL'`, or `'NONE'` — from `bpy.utils.units.systems` |
| `unit_category` | str | `'LENGTH'`, `'AREA'`, `'VOLUME'`, etc. — from `bpy.utils.units.categories` |
| `str_input` | str | Input string, e.g. `'10 mm'`, `'2.5cm'`, `'1m 50cm'` |
| `str_ref_unit` | str or None | Reference unit used if `str_input` has no explicit unit |

Returns the value in the **base unit** of the system: for `METRIC` + `LENGTH`, the base unit is **meters**.

```python
import bpy

bpy.utils.units.to_value('METRIC', 'LENGTH', '10 mm')    # → 0.01  (meters)
bpy.utils.units.to_value('METRIC', 'LENGTH', '2.5 cm')   # → 0.025 (meters)
bpy.utils.units.to_value('METRIC', 'LENGTH', '100')       # → 100.0 (assumed meters without unit)
```

To get the value in BU (for a scene with `scale_length = 0.001`):
```python
meters = bpy.utils.units.to_value('METRIC', 'LENGTH', '10 mm')  # 0.01
bu = meters / scene.unit_settings.scale_length                   # 0.01 / 0.001 = 10.0 BU
```

Or the direct formula when `scale_length = 0.001`: `BU = mm_value` (since 1mm = 0.001m, and 0.001m / 0.001 = 1.0 BU).

Raises `ValueError` if the string cannot be parsed.

### bpy.utils.units.to_string

```python
bpy.utils.units.to_string(unit_system, unit_category, value, *, precision=3, split_unit=False, compatible_unit=False) → str
```

Converts a float value to a human-readable string with units.

| Parameter | Type | Notes |
|---|---|---|
| `value` | float | Value in the base unit of the system (meters for METRIC+LENGTH) |
| `precision` | int | Decimal digits after the point |
| `split_unit` | bool | If True, may produce `"1m 5cm"` instead of `"1.05m"` |
| `compatible_unit` | bool | If True, uses ASCII-safe units (e.g., `m2` instead of `m²`) |

### Available Categories and Systems

```python
bpy.utils.units.categories
# NONE, LENGTH, AREA, VOLUME, MASS, ROTATION, TIME, TIME_ABSOLUTE,
# VELOCITY, ACCELERATION, CAMERA, POWER, TEMPERATURE, WAVELENGTH,
# COLOR_TEMPERATURE, FREQUENCY

bpy.utils.units.systems
# NONE, METRIC, IMPERIAL
```

### Scale Length Context

```python
scene = bpy.context.scene
scene.unit_settings.length_unit   # 'MILLIMETERS', 'CENTIMETERS', 'METERS', etc.
scene.unit_settings.scale_length  # float multiplier; 0.001 for mm workflow
scene.unit_settings.system        # 'METRIC', 'IMPERIAL', 'NONE'
```

Setting up a metric mm scene:
```python
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.unit_settings.scale_length = 0.001
```

After this, a mesh vertex at position `(10, 20, 5)` BU represents `(10mm, 20mm, 5mm)` in physical space.

---

## bpy.utils — Addon and Path Utilities

### Class Registration (addon development)

```python
bpy.utils.register_class(cls)
# Registers a subclass of Panel, Operator, PropertyGroup, NodeTree, Node, NodeSocket, etc.
# Raises ValueError if cls is not a registerable Blender type.

bpy.utils.unregister_class(cls)
# Unloads the registered class.
```

### Path Utilities

```python
bpy.utils.resource_path(type, *, major=bpy.app.version[0], minor=bpy.app.version[1]) → str
# type: 'USER', 'LOCAL', or 'SYSTEM'
# Returns the base path for storing Blender system files (scripts, addons, etc.)

bpy.utils.script_paths() → Iterator[str]
# Returns all current Python script search directories.
# Call after adding new script paths to update sys.path.

bpy.utils.extension_path_user(package, *, path='', create=False) → str
# Returns a user-writable directory for an extension's data.
# package: the extension's __package__ string.
# create: if True, creates the directory if absent.

bpy.utils.blend_paths(*, absolute=False, packed=False, local=False) → list[str]
# Returns all external file paths referenced in the current .blend file.
# absolute=True: return absolute paths; packed=True: include packed file paths.

bpy.utils.is_path_builtin(path) → bool
# Returns True if path is within Blender's built-in directory structure.
```

### Addon Activation

```python
import addon_utils

addon_utils.enable(module_name, *, default_set=False, persistent=False, handle_error=None)
# Activates an addon by its module name.
# module_name: e.g., 'object_print3d_utils' for the 3D Print Toolbox.
# default_set=True: also saves preference so addon stays enabled.

addon_utils.disable(module_name, *, default_set=False, handle_error=None)
# Deactivates the addon.

addon_utils.check(module_name) → (is_loaded_default, is_loaded_state)
# Returns a tuple of bools: is the addon enabled by default, is it currently loaded.

addon_utils.modules() → list[module]
# Returns all discovered addon modules.

# Example: activating 3D Print Toolbox
addon_utils.enable('object_print3d_utils', default_set=True)
```

---

## bpy.app — Application Information

Read-only access to Blender's runtime state and version.

| Property | Type | Description |
|---|---|---|
| `bpy.app.version` | `tuple[int, int, int]` | Version as (major, minor, patch), e.g., `(5, 1, 0)` |
| `bpy.app.version_string` | str | Version as a formatted string, e.g., `'5.1.0'` |
| `bpy.app.version_cycle` | str | Release stage: `'alpha'`, `'beta'`, `'rc'`, or `'release'` |
| `bpy.app.binary_path` | str | Absolute path to the Blender executable |
| `bpy.app.tempdir` | str | Blender's temporary directory for this session |
| `bpy.app.is_job_thread` | bool | True if running in a background job thread (not main thread) |

### bpy.app.handlers

`bpy.app.handlers` is a module with lists of callback functions that Blender calls at specific events. Handlers are persistent across file loads only if decorated with `@bpy.app.handlers.persistent`.

Key handler lists:

| Handler | Trigger |
|---|---|
| `frame_change_pre` | Before each frame change (animation) |
| `frame_change_post` | After each frame change |
| `load_pre` | Before opening a .blend file |
| `load_post` | After opening a .blend file |
| `save_pre` | Before saving a .blend file |
| `save_post` | After saving |
| `depsgraph_update_post` | After depsgraph evaluation (geometry/transform changed) |
| `render_pre` | Before a render starts |
| `render_post` | After a render completes |

```python
def on_depsgraph_update(scene, depsgraph):
    # called after any geometry update
    pass

bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)
# Remove with: bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update)
```

---

## bl_math — Math Helpers

`bl_math` provides three simple numeric utilities, useful for parameter calculations in Python scripts.

```python
import bl_math

bl_math.clamp(value, min=0.0, max=1.0) → float
# Clamps value to [min, max]. Unlike Python's built-in, defaults are 0.0 and 1.0.
bl_math.clamp(1.5)           # → 1.0
bl_math.clamp(-0.1, 0.0, 1.0)  # → 0.0
bl_math.clamp(0.5, 0.2, 0.8)   # → 0.5

bl_math.lerp(from_value, to_value, factor) → float
# Linear interpolation: from_value * (1-factor) + to_value * factor.
# factor=0 → from_value; factor=1 → to_value; factor outside [0,1] extrapolates.
bl_math.lerp(0.0, 10.0, 0.25)  # → 2.5

bl_math.smoothstep(from_value, to_value, value) → float
# Hermite interpolation: result in [0, 1] that smoothly transitions from 0 to 1
# as value goes from from_value to to_value. Returns 0 outside the lower edge,
# returns 1 outside the upper edge.
bl_math.smoothstep(0.0, 1.0, 0.5)  # → 0.5 (midpoint)
bl_math.smoothstep(0.0, 1.0, 0.1)  # → ~0.028 (smooth start)
```

---

## Custom Properties (ID Properties)

Any type derived from `ID` or `bpy_struct` (Object, Mesh, Scene, Material, etc.) supports arbitrary custom properties.

### Reading and Writing

```python
obj["my_int"] = 42
obj["my_float"] = 3.14
obj["my_string"] = "hello"
obj["my_array"] = [1.0, 2.0, 3.0]  # stored as IDPropertyArray

# Reading
val = obj["my_int"]
val = obj.get("my_int", default=0)  # safe access with default
```

Supported types: `int`, `float`, `str`, `bool`, Python `list` (stored as `IDPropertyArray` or `IDPropertyGroup`), Python `dict` (stored as `IDPropertyGroup`).

### idprop.types.IDPropertyArray

```python
import idprop

arr = obj["my_array"]
isinstance(arr, idprop.types.IDPropertyArray)  # True

arr.to_list()     # → Python list
arr.typecode      # 'f' (float32), 'd' (float64), 'i' (int), 'b' (bool)
len(arr)          # number of elements
arr[0]            # element access
```

Note: Float arrays created from Python `list[float]` default to `'f'` (32-bit). For precision-critical data, use `mathutils.Vector` or `numpy` arrays when needed, not IDPropertyArray.

### idprop.types.IDPropertyGroup

```python
obj["my_group"] = {"x": 1.0, "y": 2.0}  # stored as IDPropertyGroup
group = obj["my_group"]
isinstance(group, idprop.types.IDPropertyGroup)  # True

group["x"]               # 1.0
group.get("z", 0.0)      # 0.0 (safe access)
group.keys()             # IDPropertyGroupViewKeys
group.items()            # IDPropertyGroupViewItems
group.to_dict()          # → Python dict
group.update({"z": 3.0}) # update like dict
group.clear()            # remove all keys
group.pop("x")           # remove and return
```

### UI Metadata for Custom Properties

Custom properties can have UI annotations (description, range, default) via `id_properties_ui`:

```python
obj["wall_thickness"] = 1.2
ui = obj.id_properties_ui("wall_thickness")
ui.update(description="Wall thickness in BU", min=0.1, max=10.0, default=1.0, subtype='DISTANCE')
```

Subtype values that affect display: `'NONE'`, `'DISTANCE'`, `'ANGLE'`, `'FACTOR'`, `'PERCENTAGE'`, `'PIXEL'`, `'UNSIGNED'`, `'COLOR'`, `'DIRECTION'`.

### Bulk Operations

```python
obj.id_properties_clear()   # removes ALL custom properties from obj
obj.keys()                  # list of custom property key names
obj.items()                 # list of (key, value) tuples
obj.values()                # list of values
```

### Custom Properties on Non-Object Types

Custom properties work on any `bpy_struct`:

```python
mesh["source_file"] = "/path/to/source.stl"
scene["print_config"] = {"layer_height": 0.2, "infill": 0.15}
mat["filament_color"] = (1.0, 0.5, 0.0, 1.0)  # RGBA
```

This is useful for embedding metadata (print settings, provenance, version) directly in the .blend file, accessible via MCP or scripting without external files.

---

## Enum Value Reference

Frequently needed enum strings for type checks and operator calls:

### Object Mode (`bpy.context.mode`)
`'OBJECT'`, `'EDIT_MESH'`, `'SCULPT'`, `'VERTEX_PAINT'`, `'WEIGHT_PAINT'`, `'TEXTURE_PAINT'`

### Modifier Types (for `obj.modifiers.new(name, type=...)`)
| Type | Description |
|---|---|
| `'ARRAY'` | Array modifier |
| `'BOOLEAN'` | Boolean modifier |
| `'BEVEL'` | Bevel modifier |
| `'DECIMATE'` | Decimate modifier |
| `'DISPLACE'` | Displace modifier |
| `'MIRROR'` | Mirror modifier |
| `'NODES'` | Geometry Nodes modifier |
| `'REMESH'` | Remesh modifier |
| `'SCREW'` | Screw/lathe modifier |
| `'SHRINKWRAP'` | Shrinkwrap modifier |
| `'SKIN'` | Skin modifier |
| `'SOLIDIFY'` | Solidify modifier |
| `'SUBSURF'` | Subdivision Surface modifier |
| `'TRIANGULATE'` | Triangulate modifier |
| `'WELD'` | Weld (merge by distance) modifier |
| `'WIREFRAME'` | Wireframe modifier |
| `'LATTICE'` | Lattice modifier |

### Object Types (`obj.type`)
`'MESH'`, `'CURVE'`, `'SURFACE'`, `'META'`, `'FONT'`, `'VOLUME'`, `'ARMATURE'`, `'LATTICE'`, `'EMPTY'`, `'LIGHT'`, `'CAMERA'`, `'SPEAKER'`, `'LIGHT_PROBE'`

### Mesh Select Modes (for `bpy.context.tool_settings.mesh_select_mode`)
`('VERT', False, False)` — vertex mode; `(False, 'EDGE', False)` — edge; `(False, False, 'FACE')` — face

### Attribute Domains
`'POINT'` (vertices), `'EDGE'`, `'FACE'`, `'CORNER'` (face corners / loops), `'CURVE'`, `'INSTANCE'`

---

## Startup File — Persistenza delle impostazioni di unità

### bpy.ops.wm.save_homefile()

```python
bpy.ops.wm.save_homefile()
```

Salva lo stato corrente del file .blend come **startup file** (`userpref.blend`). All'avvio successivo di Blender, la scena si aprirà già con le impostazioni salvate — incluse quelle delle unità.

**Uso in MCP CALL_0:** Se il workflow richiede `scale_length=0.001` su ogni sessione, inserire `save_homefile()` alla fine di CALL_0 (dopo aver configurato le unità) evita di dover ripetere la configurazione a ogni chiamata.

```python
import bpy

# CALL_0 — Configurazione unità + overlay griglia + salvataggio startup
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.unit_settings.scale_length = 0.001

# Sincronizza la griglia del viewport con scale_length=0.001
# Senza questo, la griglia mostra incrementi in metri anziché millimetri
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.overlay.grid_scale = 0.001  # 1 linea griglia = 1mm
                space.clip_end = 10000             # evita clipping per oggetti grandi
                break

# Salva come startup: la prossima sessione parte già configurata
bpy.ops.wm.save_homefile()
print("Startup file salvato con unità mm (scale_length=0.001)")
```

> **Attenzione:** `save_homefile()` sovrascrive il file di startup globale di Blender. In ambienti condivisi o quando si lavora su più workflow con unità diverse, evitare questa chiamata e configurare le unità all'inizio di ogni sessione MCP.

### Grid Overlay Scale

`space.overlay.grid_scale` controlla la scala della griglia visualizzata nel viewport 3D. Deve essere sincronizzata con `scale_length` per evitare che la griglia mostri tacche in unità diverse dalla scena.

Con `scale_length=0.001` (1 BU = 1mm), impostare `grid_scale=0.001` fa sì che ogni quadrato della griglia corrisponda a 1mm. Senza questa impostazione la griglia mostra incrementi in metri (il default Blender), rendendo il viewport visivamente fuorviante durante il modeling di precisione.

```python
import bpy

# Imposta grid_scale su tutti i viewport 3D aperti
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.overlay.grid_scale = 0.001   # 1 cella griglia = 1mm
                space.overlay.grid_subdivisions = 10  # 10 suddivisioni per cella (= ogni 0.1mm)
                break

print("Grid overlay: scala mm attivata")
```

`grid_subdivisions` (default: 10) definisce le tacche secondarie all'interno di ogni cella. Con `grid_scale=0.001` e `grid_subdivisions=10`, le tacche secondarie sono a 0.1mm — utile per verificare visivamente dimensioni sub-millimetriche.

---

## Viewport — Clipping End per oggetti grandi

Blender usa un valore di **Clipping End** per il viewport per determinare fino a quale distanza dalla camera virtuale viene disegnata la geometria. Con il valore di default (~1000 BU = 1 km in scala metro, ma solo 1m con `scale_length=0.001`), gli oggetti grandi sbiadiscono o scompaiono dal viewport durante il posizionamento.

Con `scale_length=0.001` (1 BU = 1mm), un oggetto di 256mm corrisponde a `0.256 BU` — molto piccolo rispetto alla camera di default. Per oggetti grandi o scene con più elementi distanti, aumentare il Clipping End via Python:

```python
import bpy

# Aumenta il clipping end per evitare che gli oggetti spariscano
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.clip_end = 10000  # 10000 BU — adeguato per qualsiasi oggetto stampa 3D
                break

print("Viewport Clipping End impostato a 10000 BU")
```

Valore raccomandato: `10000` (sufficiente per qualsiasi oggetto entro il volume di stampa A1 e oltre). Non ha impatto sulle prestazioni per scene semplici come quelle tipiche del workflow di stampa 3D.
