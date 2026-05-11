# Booltron — Reference operativo

Addon `booltron` di mrachinskiy (extensions.blender.org, GPL-3.0, v3.3.2 Feb 2026). Boolean wrapper con due famiglie (destructive + non-destructive geometry-nodes), **pre-op sanitization automatica**, batch multi-cutter, e supporto MANIFOLD solver per-side (primary/secondary differenti).

**Killer feature vs Bool Tool**: `meshlib.prepare()` esegue automaticamente `remove_doubles + dissolve_degenerate + delete_loose + holes_fill` su ogni operando PRIMA del boolean — risolve la maggior parte dei silent failures su STL imports non puliti.

## Operators

Mode richiesto: **OBJECT**. Selection contract: ≥2 objects, **active = primary/target**, others = cutters.

### Destructive family

| bl_idname | Op | Note |
|---|---|---|
| `object.booltron_destructive_difference` | DIFFERENCE | subtract selected da active |
| `object.booltron_destructive_union` | UNION | |
| `object.booltron_destructive_intersect` | INTERSECT | |
| `object.booltron_destructive_slice` | SLICE | extra prop `overlap_distance` (FloatVector) per displace slices + creare wall thickness/glue lap |

Operator-local property: `keep_objects` (bool, default False) — preserva i cutter dopo apply (utile per testing iterativo).

### Non-destructive family (geometry-nodes based)

| bl_idname | Op |
|---|---|
| `object.booltron_nondestructive_difference` | DIFFERENCE |
| `object.booltron_nondestructive_union` | UNION |
| `object.booltron_nondestructive_intersect` | INTERSECT |

Operator-local property: `modifier_name` (Enum, default `"__NEW__"`) — crea nuovo GN modifier o estende uno esistente booltron sul primary. Bake se preference `use_bake` set.

## Solver & options

Letti da `WindowManager.booltron.destructive` / `.nondestructive` (ToolPropsGroup) che mirror le AddonPreferences. Configurabili separatamente per **primary** e **secondary** side:

| Property | Type | Default | Note |
|---|---|---|---|
| `solver` / `solver_secondary` | Enum | `FAST` | `FAST` (=Blender FLOAT) / `EXACT` / `MANIFOLD` |
| `use_self` / `use_self_secondary` | bool | False | self-intersection handling |
| `use_hole_tolerant` / `use_hole_tolerant_secondary` | bool | False | (solo se solver=EXACT) |

**Pre-processing** (sempre attivi):

| Property | Type | Default | Effetto |
|---|---|---|---|
| `merge_distance` | float | 3e-4 | `bmesh.ops.remove_doubles` threshold |
| `dissolve_distance` | float | 1e-4 | `dissolve_degenerate` threshold |

**Secondary handling** (per i cutter):

| Property | Type | Default | Note |
|---|---|---|---|
| `use_loc_rnd` | bool | (off) | randomized micro-offset per rompere coplanarità |
| `loc_offset` | float | 0.005 | distanza offset random |
| `seed` | int | 0 | seed per reproducibilità |
| `display_secondary` | Enum | WIRE | BOUNDS/WIRE/SOLID/TEXTURED dopo op |

## Multi-cutter batching (killer feature)

Per UNION/DIFFERENCE/INTERSECT (NON slice) quando i cutters NON si overlappano tra loro, Booltron **joina tutti i cutter in un singolo mesh via `bpy.ops.object.join`** prima di aggiungere UN solo Boolean modifier al primary.

Effetto:
- 8 cutters → 1 modifier (vs Bool Tool: 8 modifiers).
- Tempo ridotto da O(N) modifier evaluation a O(1).
- Rilevazione overlap via BVH (`detect_overlap()`).

## Pre/post pipeline

`meshlib.prepare()` (pre-op, su ogni operando):
1. `bmesh.ops.remove_doubles(merge_distance)`
2. `dissolve_degenerate(dissolve_distance)`
3. `delete_loose`
4. **`holes_fill`** ← critico per STL imports

`detect_overlap()` (pre-op): BVH self-intersection check.

`is_nonmanifold()` (post-op): conta non-manifold edges del risultato. **Reporta error ma non auto-fix** — devi gestire manualmente o chain con repair_basic.

## Failure modes

- **MANIFOLD richiede watertight su entrambi i lati**. Su open mesh: `is_nonmanifold()` segnala post-op, ma il risultato è probabile garbage. Usa FAST o EXACT su mesh aperti.
- **Coplanar overlap**: addressed da `use_loc_rnd=True, loc_offset=0.005`. Senza jitter, EXACT può cancellare silently.
- **Curve/Text objects supportati** (converted internamente).
- **Tiny `merge_distance`** su mm-scale FDM models è OK (3e-4mm = 300nm, sotto sub-pixel slicer). **Troppo grande** (>0.01mm) collassa hole < 0.3mm.

## Patterns (FDM print prep)

### 1. Mounting hole array (1 plate + N cylinder cutters)

```python
import bpy
plate = bpy.data.objects["plate"]
cutters = [bpy.data.objects[f"hole_{i}"] for i in range(8)]
bpy.ops.object.select_all(action='DESELECT')
for c in cutters: c.select_set(True)
plate.select_set(True)
bpy.context.view_layer.objects.active = plate
bpy.ops.object.booltron_destructive_difference()
# 8 cutters joinati → 1 modifier solo. Veloce.
```

### 2. Flatten bottom a Z=0 (cutter cube spanning Z<0)

```python
import bpy
body = bpy.data.objects["body"]
cube = bpy.data.objects["below_z0_cube"]   # cubo grande, top face a Z=0
bpy.ops.object.select_all(action='DESELECT')
cube.select_set(True)
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.booltron_destructive_difference()
# prepare() su body chiude tiny holes prima del cut → safer su STL imports
```

### 3. Snap-fit clearance via shrunk-cutter difference

```python
import bpy
peg = bpy.data.objects["peg"]
clearance = peg.copy()
clearance.data = peg.data.copy()
bpy.context.collection.objects.link(clearance)
sm = clearance.modifiers.new("Clr", 'SOLIDIFY')
sm.thickness = 0.00015  # 0.15mm con scale_length=1.0
bpy.context.view_layer.objects.active = clearance
bpy.ops.object.modifier_apply(modifier="Clr")
# Ora clearance è peg + 0.15mm uniforme. Differenza dal socket:
bpy.ops.object.select_all(action='DESELECT')
clearance.select_set(True)
bpy.data.objects["socket"].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["socket"]
bpy.ops.object.booltron_destructive_difference()
```

### 4. Multi-shell UNION usando MANIFOLD solver (entrambi closed)

```python
import bpy
shells = [bpy.data.objects[n] for n in ("shell_a", "shell_b", "shell_c")]
bpy.ops.object.select_all(action='DESELECT')
for s in shells[1:]: s.select_set(True)
shells[0].select_set(True)
bpy.context.view_layer.objects.active = shells[0]
bpy.context.window_manager.booltron.destructive.solver = 'MANIFOLD'
bpy.context.window_manager.booltron.destructive.solver_secondary = 'MANIFOLD'
bpy.ops.object.booltron_destructive_union()
```

### 5. Planar slice (split modello con plane cutter — usa box thin)

```python
import bpy
box = bpy.data.objects["slice_box"]   # box molto sottile a Z height target
model = bpy.data.objects["model"]
bpy.ops.object.select_all(action='DESELECT')
box.select_set(True)
model.select_set(True)
bpy.context.view_layer.objects.active = model
bpy.ops.object.booltron_destructive_slice(overlap_distance=(0.0, 0.0, 0.0))
# overlap_distance > 0 → glue lap, parti ottimizzati per assemblaggio
```

### 6. Coplanar jitter setup (boolean su flush mating surfaces)

```python
import bpy
bpy.context.window_manager.booltron.destructive.use_loc_rnd = True
bpy.context.window_manager.booltron.destructive.loc_offset = 0.005
bpy.context.window_manager.booltron.destructive.seed = 42
# Adesso flush boolean cuts non falliscono per coplanarity
```

### 7. Set MANIFOLD solver + sanitize per pipeline batch

```python
import bpy
bt = bpy.context.window_manager.booltron.destructive
bt.solver = 'MANIFOLD'
bt.merge_distance = 0.0003  # default ok
bt.dissolve_distance = 0.0001
bt.use_self = False  # mesh sane
# Esegue il batch di booleans con queste settings...
```

## Comparison vs Bool Tool

Vedi [addon_bool_tool] §Comparison. Sintesi:

- **Booltron** quando: STL imports da AI/scan/CAD non puliti, batch N cutters, serve solver MANIFOLD per-side, coplanar jitter.
- **Bool Tool** quando: interactive single cutter library, mantenimento cutters reversibile, simpler workflow.

Possono coesistere senza conflitti (bl_idname diversi).

## Cross-reference

- [addon_bool_tool] — alternativa per workflow interactive
- [boolean_troubleshooting] — failure modes Boolean in generale (Booltron riduce molti ma non tutti)
- [mesh_repair] — `sanitize_for_boolean` (Booltron lo fa automatico tramite `prepare()`)
- [blender_addons_recommended] — decision tree Bool Tool vs Booltron

## Source

- [github.com/mrachinskiy/booltron](https://github.com/mrachinskiy/booltron)
- Operators: `source/operators/destructive/__init__.py`, `source/operators/nondestructive/__init__.py`
- Sanitize lib: `source/lib/meshlib.py`
- Preferences: `source/preferences.py`
- [Booltron — Blender Extensions](https://extensions.blender.org/add-ons/booltron/)
- [Manifold Boolean feedback (devtalk)](https://devtalk.blender.org/t/manifold-boolean-feedback/40150)
- [Blender 4.5 LTS release notes — Manifold solver](https://developer.blender.org/docs/release_notes/4.5/modeling/)
