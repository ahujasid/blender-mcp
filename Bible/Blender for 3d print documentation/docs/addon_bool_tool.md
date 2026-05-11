# Bool Tool — Reference operativo

Addon `bool_tool` di nickberckley (extensions.blender.org, GPL-3.0, v2.0.0+). Wrapper Boolean modifier con due workflow paralleli: **brush** (non-destructive, modifier sticky) e **auto** (destructive, apply + delete cutter immediato).

**⚠ Nomenclatura confusa**: "brush" = NON-distruttivo (modifier rimane), "auto" = distruttivo (apply immediato). Counter-intuitive ma è la convenzione dell'addon.

## Operators

Mode richiesto: **OBJECT**. Selection contract: ≥2 objects, **active = canvas/target**, others = cutters.

### Brush family (non-destructive)

Aggiungono un Boolean modifier per cutter sul canvas. Cutter taggato, opzionalmente parented al canvas e moved a collection `boolean_cutters` (preferenze addon).

| bl_idname | Op |
|---|---|
| `object.boolean_brush_union` | UNION |
| `object.boolean_brush_difference` | DIFFERENCE |
| `object.boolean_brush_intersect` | INTERSECT |
| `object.boolean_brush_slice` | SLICE (crea nuovi sliced objects) |

### Auto family (destructive)

Stesso comportamento di brush, **+ apply immediato + delete cutter**.

| bl_idname | Op |
|---|---|
| `object.boolean_auto_union` | UNION |
| `object.boolean_auto_difference` | DIFFERENCE |
| `object.boolean_auto_intersect` | INTERSECT |
| `object.boolean_auto_slice` | SLICE |

### Cutter / Canvas management (solo per brush workflow)

| bl_idname | Purpose |
|---|---|
| `object.boolean_toggle_cutter` | Toggle effetto di un singolo cutter (param `method='ALL'/'SPECIFIED'`) |
| `object.boolean_remove_cutter` | Rimuove cutter da canvas(es) |
| `object.boolean_apply_cutter` | Apply un cutter (default keymap Ctrl+NumpadEnter) |
| `object.boolean_toggle_all` | Toggle tutti i cutter sui canvas selezionati |
| `object.boolean_remove_all` | Rimuove tutti i cutter dai canvas |
| `object.boolean_apply_all` | Apply tutti i cutter (con confirm dialog) |

### Properties per-operator (mixin `ModifierProperties`)

| Property | Type | Default | Note |
|---|---|---|---|
| `material_mode` | Enum | `INDEX` | INDEX o TRANSFER |
| `use_self` | bool | False | self-intersection |
| `use_hole_tolerant` | bool | False | (solo se solver=EXACT) |
| `double_threshold` | float | 1e-6 | merge threshold pre-op |

**Solver NON è parametro per-call**. È letto dalle add-on preferences:
```python
prefs = bpy.context.preferences.addons['bl_ext.user_default.bool_tool'].preferences
prefs.solver = 'MANIFOLD'  # 'FLOAT' | 'EXACT' | 'MANIFOLD'
```
Default `FLOAT`. Per spingere su MANIFOLD (Blender 4.5+, più veloce su closed mesh), set le prefs prima del batch.

## Side effects

**Brush ops**:
- Aggiunge Boolean modifier sul canvas (1 modifier per cutter).
- Cutter taggato con `obj['booltool_cutter'] = True` (o equivalente — verifica via `obj.boolean_cutters` PropertyGroup).
- Cutter opzionalmente parented al canvas (preferenze: `parent=True`).
- Cutter opzionalmente moved a collection `boolean_cutters` (preferenze: `use_collection=True`).
- Cutter display set a wireframe (preferenze: `wireframe=True`).
- Canvas resta active e selected.

**Auto ops**:
- Stesso di brush, poi:
- `bpy.ops.object.modifier_apply()` per ogni modifier aggiunto.
- `bpy.data.objects.remove(cutter)`.

## Failure modes

- **MANIFOLD solver fail su open mesh**: solo Difference-with-plane è special-cased (limitazione core Blender). Per altri op + open mesh → switch a FLOAT o EXACT.
- **Unapplied scale silently warps result**: applica `transform_apply(scale=True)` su canvas E cutters PRIMA dell'op.
- **Bug Blender 5.0 beta** ([blender#148829](https://projects.blender.org/blender/blender/issues/148829)): regression nota.
- `basic_poll` requires active object non-linked: se canvas è linked da altra scene, op cancella.

## Patterns (FDM print prep)

### 1. Cutter library reversibile (1 logo, possibili modifiche post)

```python
import bpy
canvas = bpy.data.objects["body"]
cutter = bpy.data.objects["logo_cutter"]
bpy.ops.object.select_all(action='DESELECT')
cutter.select_set(True)
canvas.select_set(True)
bpy.context.view_layer.objects.active = canvas
bpy.ops.object.boolean_brush_difference()
# Modifier rimane; cutter visibile come wireframe nella collection boolean_cutters
# Quando finisci di iterare, finalizza:
bpy.ops.object.boolean_apply_all()
```

### 2. Quick destructive cut (1 cutter, no library reversible)

```python
import bpy
canvas = bpy.data.objects["plate"]
cutter = bpy.data.objects["mounting_hole"]
bpy.ops.object.select_all(action='DESELECT')
cutter.select_set(True)
canvas.select_set(True)
bpy.context.view_layer.objects.active = canvas
bpy.ops.object.boolean_auto_difference()
# canvas modificato in-place, cutter eliminato
```

### 3. Set MANIFOLD solver per closed mesh (più veloce)

```python
import bpy
prefs = bpy.context.preferences.addons['bl_ext.user_default.bool_tool'].preferences
prefs.solver = 'MANIFOLD'
# Adesso ogni boolean_brush_*/boolean_auto_* userà MANIFOLD
```

### 4. Pre-flight (apply scale + check open meshes)

```python
import bpy

def pre_flight(canvas, cutter):
    for o in (canvas, cutter):
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # Quick manifold check (richiede 3D Print Toolbox)
    # ... vedi blender_3d_print_toolbox.md per check_solid pattern

pre_flight(canvas, cutter)
```

### 5. Toggle un cutter off temporaneamente

```python
# canvas selected, cutter visibile in collection boolean_cutters
bpy.context.view_layer.objects.active = canvas
bpy.ops.object.boolean_toggle_cutter(method='SPECIFIED', cutter_name='logo_cutter')
# Boolean modifier disabilitato, mesh canvas torna intero. Re-toggle per riattivare.
```

## Conflitti & coesistenza con Booltron

- **No bl_idname collision** (`object.boolean_*` vs `object.booltron_*`). Possono coesistere safe.
- Stesso N-panel category "Edit" → entrambi i panel appaiono. Rinomina uno se cluttered (preferences).
- **Cutter management ops di Bool Tool NON applicabili a cutter Booltron** (e viceversa). Usa i due workflow su disjoint objects per evitare confusion.

## Comparison rapido vs Booltron

| Feature | Bool Tool | Booltron |
|---|---|---|
| Pre-op sanitization | ❌ | ✅ (`prepare()`: remove_doubles + dissolve_degenerate + delete_loose + holes_fill) |
| Multi-cutter batch | 1 modifier per cutter | Joina N cutter in 1 mesh, 1 modifier solo |
| Solver per-call | ❌ (in prefs globali) | ✅ (per primary AND secondary differenti) |
| Coplanar jitter | ❌ | ✅ (`use_loc_rnd=True, loc_offset=0.005`) |
| Non-destructive | "brush" family | "nondestructive" family (geometry-nodes based) |
| Cutter library mgmt | ✅ (collection, parent, toggle/apply/remove ops) | ❌ |
| Recommended use | **Interactive single cutter, library reversibile** | **Batch + STL importati non-pulito** |

Vedi [addon_booltron] per dettagli sull'altro.

## Cross-reference

- [addon_booltron] — alternativa con sanitize automatico
- [boolean_troubleshooting] — failure modes dei Boolean modifier in generale
- [blender_addons_recommended] — quando preferire quale
- [mesh_repair] — sanitize_for_boolean utility (da fare manualmente prima di Bool Tool, automatico in Booltron)

## Source

- [github.com/nickberckley/bool_tool](https://github.com/nickberckley/bool_tool) — operators in `source/operators/{boolean,cutter,canvas,select}.py`, preferences in `source/preferences.py`
- [Bool Tool — Blender Extensions](https://extensions.blender.org/add-ons/bool-tool/)
- Bug Blender 5.0 beta: [issue #148829](https://projects.blender.org/blender/blender/issues/148829)
- Boolean Modifier docs: [docs.blender.org/manual/.../booleans.html](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/booleans.html)
