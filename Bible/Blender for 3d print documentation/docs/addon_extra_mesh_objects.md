# Extra Mesh Objects — Reference operativo

Addon `add_mesh_extra_objects` (extensions.blender.org, GPL-3.0, v0.4.1 Feb 2025). Community-maintained, attivo. Espone primitive parametriche utili come **cutter Boolean** per operazioni FDM (mounting holes chamfered, countersink, channel routing, gear, structural beams).

Mode: **OBJECT**. Tutti gli operator creano nuovo mesh object al 3D cursor location, lo rendono active+selected. Tutti accettano il mixin `AddObjectHelper` con params standard `align`, `location`, `rotation`, `layers` oltre a quelli specifici.

## Primitive utili per FDM

### `bpy.ops.mesh.primitive_round_cube_add(...)`

Bevelled cube parametrico — il **cutter Boolean più utile** per chamfered/filleted holes e edge breaks.

| Param | Type | Default | Range | Note |
|---|---|---|---|---|
| `radius` | float | 1.0 | — | Bevel radius |
| `size` | 3-vec | (0,0,0) | — | Dimensions XYZ; (0,0,0) = sphere-like |
| `arc_div` | int | 8 | ≥1 | Subdivisions su arc (chamfer smoothness) |
| `lin_div` | float | 0.0 | — | Linear subdiv tra arcs |
| `div_type` | enum | `CORNERS` | `CORNERS` \| `ALL` \| `EDGES` | Dove applicare bevel |
| `odd_axis_align` | bool | False | — | |
| `no_limit` | bool | False | — | True bypassa sanity cap (~10000 verts max default) |

Use case primary: **chamfered mounting hole cutter** in pochi righi di Python.

### `bpy.ops.mesh.primitive_pipe_*` family

Cable channel cutters, manifold-routing geometry.

| Operator | Param chiave |
|---|---|
| `mesh.primitive_elbow_joint_add` | `radius=1.0, div=32, angle=π/4 (45°), startLength=3.0, endLength=3.0` |
| `mesh.primitive_tee_joint_add` | `radius=1.0, div=32, angle=π/2 (90°), startLength=3.0, endLength=3.0, branchLength=3.0` |
| `mesh.primitive_wye_joint_add` | `radius=1.0, div=32, angle=π/4, startLength=3.0, endLength=3.0, branchLength=3.0` |
| `mesh.primitive_cross_joint_add` | `radius=1.0, div=32, startLength=3.0, endLength=3.0, branch1Length=3.0, branch2Length=3.0` |
| `mesh.primitive_n_joint_add` | `radius=1.0, div=32, number=3, length=3.0` |

Tutti i `radius` in 0.01..100, `div` 3..256.

### `bpy.ops.mesh.primitive_gear(...)`

Print-ready spur gear. Aggiunge vertex groups `Tips` e `Valleys`.

| Param | Type | Default | Range |
|---|---|---|---|
| `number_of_teeth` | int | 12 | ≥2 |
| `radius` | float | 1.0 | — |
| `addendum` | float | 0.1 | — |
| `dedendum` | float | 0.1 | — |
| `angle` | float | 0.349 (20°) | rad, pressure angle |
| `base` | float | 0.2 | inner base disc |
| `width` | float | 0.2 | extrude depth |
| `skew` | float | 0 | — |
| `conangle` | float | 0 | cone angle |
| `crown` | float | 0 | crown bulge |

Negative `radius` → crown gear.

### `bpy.ops.mesh.primitive_worm_gear(...)`

Worm drive parts. Stesso shape di `primitive_gear` con `number_of_rows` extra (default 32) + `row_height` (0.2) + `skew` per row (default 11.25°).

### `bpy.ops.mesh.primitive_diamond_add(...)`

Diamond-shape ottimo come **countersink cutter**.

| Param | Default | Range |
|---|---|---|
| `segments` | 32 | 3..256 |
| `girdle_radius` | 1.0 | — |
| `table_radius` | 0.6 | — |
| `crown_height` | 0.35 | — |
| `pavilion_height` | 0.8 | — |

### `bpy.ops.mesh.primitive_steppyramid_add(...)`

Test/tolerance staircase, overhang test cubes.

| Param | Default | Range |
|---|---|---|
| `num_sides` | 4 | ≥3 |
| `num_steps` | 10 | ≥1 |
| `width` | 2.0 | — |
| `height` | 0.1 | per step |
| `reduce_by` | 0.20 | taper factor |

### `bpy.ops.mesh.primitive_solid_add(...)`

Platonic / Archimedean / Catalan solids.

| Param | Default | Note |
|---|---|---|
| `source` | enum | 4 (tetra) / 6 (cube) / 8 (octa) / 12 (dodeca) / 20 (icosa) |
| `size` | 1.0 | 0.01..100 |
| `vTrunc` | 0 | 0..2, vertex truncation |
| `eTrunc` | 0 | 0..1, edge truncation |
| `snub` | enum | snub variations |
| `dual` | bool | dual polyhedron |
| `keepSize` | bool | maintain size on truncate |

### `bpy.ops.mesh.add_beam(...)`

Structural profile (C/I/L/T/U/rectangular).

| Param | Default |
|---|---|
| `Type` | enum (C/I/L/T/U/rectangular) |
| `beamX/Y/Z` | size dimensions |
| `beamW` | wall thickness |
| `edgeA` | int taper |

### `bpy.ops.mesh.honeycomb_add(...)`

Honeycomb pattern — infill cutter / lightweighting.

| Param | Default |
|---|---|
| `rows` | int |
| `cols` | int |
| `edge` | float, hex side |

### Altri (meno centrali per FDM)

`mesh.primitive_supertoroid_add`, `mesh.primitive_torusknot_add`, `mesh.primitive_twisted_torus_add` — torus variants decorativi.
`mesh.primitive_brilliant_add`, `mesh.primitive_gem_add` — variant dei diamond.
`mesh.menger_sponge_add`, `mesh.primitive_xyz_function_surface`, `mesh.primitive_z_function_surface` — niche.
`mesh.add_equilateral_grid`, `mesh.make_triangle`, `mesh.primitive_vert_add`, `mesh.primitive_star_add`, `mesh.wall_add`, `mesh.primitive_teapot_add`.

## Failure modes

- **`arc_div` / `lin_div` molto alto su `round_cube` senza `no_limit=True`**: aborts con sanity check (default cap ~10000 verts).
- **`mesh.primitive_xyz_function_surface`**: evaluates user-supplied Python expressions. **Security**: NON passare untrusted strings. Errors su division by zero / domain errors.
- **Pipe joints con angle near ±180°**: self-intersect, mesh non-manifold.
- **`primitive_gear` con `number_of_teeth=2` o `=3`**: degenerate (too few teeth per profile evolvente). Min pratica 8.
- **AddObjectHelper location**: usa 3D cursor di default. Set `bpy.context.scene.cursor.location = (x,y,z)` PRIMA della call se serve location esatta, altrimenti `bpy.ops.mesh.primitive_*_add(location=(x,y,z))`.

## Patterns (FDM cutter creation)

### 1. Chamfered mounting hole cutter

```python
import bpy

# Cutter: cubo bevellato 8×8×4mm, chamfer 1mm raggio
bpy.ops.mesh.primitive_round_cube_add(
    radius=0.001,                     # 1mm chamfer (assumendo scale_length=1.0)
    size=(0.008, 0.008, 0.004),       # 8×8×4mm
    arc_div=3,
    lin_div=0.0,
    div_type='CORNERS',
)
cutter = bpy.context.active_object
cutter.name = 'mounting_hole_cutter'

# Posiziona dove serve il foro
cutter.location = (0.025, 0.025, 0)   # 25mm,25mm,0

# Boolean DIFFERENCE su plate
plate = bpy.data.objects['plate']
m = plate.modifiers.new('cut', 'BOOLEAN')
m.object = cutter
m.operation = 'DIFFERENCE'
m.solver = 'EXACT'
bpy.context.view_layer.objects.active = plate
bpy.ops.object.modifier_apply(modifier='cut')
bpy.data.objects.remove(cutter, do_unlink=True)
```

### 2. Cable channel via elbow joint

```python
import bpy

# Elbow 2mm bore, 90°, 20mm su ogni lato
bpy.ops.mesh.primitive_elbow_joint_add(
    radius=0.002,        # 2mm bore
    div=32,
    angle=1.5708,        # 90°
    startLength=0.020,   # 20mm
    endLength=0.020,
)
channel = bpy.context.active_object
channel.name = 'cable_channel'

# Posiziona sul body
channel.location = (0.010, 0.010, 0.005)

# Boolean DIFFERENCE per creare canale interno
body = bpy.data.objects['body']
m = body.modifiers.new('chan', 'BOOLEAN')
m.object = channel
m.operation = 'DIFFERENCE'
m.solver = 'EXACT'
bpy.context.view_layer.objects.active = body
bpy.ops.object.modifier_apply(modifier='chan')
bpy.data.objects.remove(channel, do_unlink=True)
```

### 3. Print-ready spur gear

```python
import bpy

# Gear M=1.5mm, 20 denti, addendum standard
bpy.ops.mesh.primitive_gear(
    number_of_teeth=20,
    radius=0.015,        # 15mm pitch radius
    addendum=0.0008,     # 0.8mm
    dedendum=0.001,      # 1mm
    angle=0.349,         # 20° pressure angle (standard)
    base=0.002,          # 2mm base disc
    width=0.004,         # 4mm thickness
)
gear = bpy.context.active_object
gear.name = 'spur_gear_M1.5_T20'
# Già print-ready. Apply transforms + export STL/3MF.
```

### 4. Diamond countersink

```python
import bpy

# Countersink M3 vite (3mm head, 90° angle)
bpy.ops.mesh.primitive_diamond_add(
    segments=32,
    girdle_radius=0.003,   # 3mm raggio max
    table_radius=0.0015,   # 1.5mm raggio min
    crown_height=0.002,    # 2mm depth
    pavilion_height=0.00001,  # quasi zero (no bottom point)
)
cs = bpy.context.active_object
cs.name = 'countersink_M3'
# Boolean DIFFERENCE su body...
```

### 5. Honeycomb infill cutter (custom infill regional)

```python
import bpy

# Honeycomb 10×10 cells, hex side 5mm
bpy.ops.mesh.honeycomb_add(rows=10, cols=10, edge=0.005)
honey = bpy.context.active_object
honey.name = 'honey_pattern'

# Solidify per dare wall thickness
sm = honey.modifiers.new('thick', 'SOLIDIFY')
sm.thickness = 0.002  # 2mm wall
bpy.context.view_layer.objects.active = honey
bpy.ops.object.modifier_apply(modifier='thick')

# Adesso usa come modifier mesh in Bambu Studio per infill regionale
# (vedi hidden_bambu_studio_settings.md)
```

### 6. Test staircase per overhang calibration

```python
import bpy

bpy.ops.mesh.primitive_steppyramid_add(
    num_sides=4,
    num_steps=10,
    width=0.020,        # 20mm base
    height=0.005,       # 5mm per step → tot 50mm height
    reduce_by=0.18,     # taper progressivo
)
# Stampa per testare overhang threshold del filament/profile
```

### 7. Beam structural profile starter

```python
import bpy

# I-beam 20×30×100mm
bpy.ops.mesh.add_beam(
    Type='I',
    beamX=0.020,
    beamY=0.030,
    beamZ=0.100,
    beamW=0.003,        # 3mm wall
    edgeA=2,
)
# Già print-ready come parte funzionale
```

## Comparison vs creating primitives via bmesh

L'addon è **solo per primitives non-banali** (round cube bevellato, gear, pipe joint). Per primitives semplici (cube, cylinder, sphere), usa direttamente `bpy.ops.mesh.primitive_*_add` built-in:

- `mesh.primitive_cube_add` (built-in)
- `mesh.primitive_uv_sphere_add` / `primitive_ico_sphere_add` (built-in)
- `mesh.primitive_cylinder_add`
- `mesh.primitive_cone_add`
- `mesh.primitive_torus_add`
- `mesh.primitive_grid_add`
- `mesh.primitive_monkey_add` (Suzanne)

Extra Mesh Objects è un **addon di estensione** non di sostituzione.

## Cross-reference

- [addon_booltron] / [addon_bool_tool] — cutter creati qui poi consumati per Boolean
- [boolean_troubleshooting] — sanitize cutter prima di Boolean operations
- [bisect_splitting] — alternativa per split modello senza cutter geometrico
- [hidden_bambu_studio_settings] — modifier mesh in Bambu Studio per regional settings (es. honeycomb infill regionale)

## Source

- [Extra Mesh Objects — Blender Extensions](https://extensions.blender.org/add-ons/extra-mesh-objects/)
- Source: [projects.blender.org/extensions/add_mesh_extra_objects](https://projects.blender.org/extensions/add_mesh_extra_objects)
- Legacy mirror (archived): [github.com/blender/blender-addons/tree/main/add_mesh_extra_objects](https://github.com/blender/blender-addons/tree/main/add_mesh_extra_objects)
