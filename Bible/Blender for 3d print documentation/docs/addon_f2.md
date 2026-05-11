# F2 — Reference operativo

Addon `mesh_f2` (extensions.blender.org, GPL). Singolo operator per quad fill da 1 vertex / 1 edge / N vertex selection. Inferisce la 4ª vertex da topology vicina invece di limitarsi a connettere selection (come fa il built-in `mesh.edge_face_add` con tasto F).

Mode richiesto: **EDIT**.

## ⚠ Quirk killer per uso MCP

F2 ha **solo `invoke()`, no `execute()`** — DEVE essere chiamato con `'INVOKE_DEFAULT'`:

```python
# WRONG (silent failure):
bpy.ops.mesh.f2()

# CORRECT:
bpy.ops.mesh.f2('INVOKE_DEFAULT')
```

In più, `autograb=True` di default invoca `bpy.ops.transform.translate('INVOKE_DEFAULT')` dopo creare la face — in modal grab. **In context non-interattivo (MCP `execute_blender_code`) il modal stalla aspettando user input → silent failure**. Documentato in bug [T52506](https://developer.blender.org/T52506).

**Solution obbligatoria**:
```python
import bpy
bpy.context.preferences.addons['mesh_f2'].preferences.autograb = False
bpy.ops.mesh.f2('INVOKE_DEFAULT')
```

## Operator

### `bpy.ops.mesh.f2('INVOKE_DEFAULT')`

| Branch in invoke() | Trigger | Comportamento |
|---|---|---|
| ≥3 verts selected | qualsiasi | Delegata a Blender's `mesh.edge_face_add` (n-gon) |
| 2 verts su same edge | edge selezionato (entrambi i suoi endpoint) | `quad_from_edge`: crea quad proiettando dai 2 open-edge neighbours degli endpoint |
| 2 verts NON su same edge | 2 vertex non connessi | Fallback a `mesh.edge_face_add` |
| 1 vert selected | vertex con esattamente 2 open (boundary) edges | `quad_from_vertex`: mirror nuovo vertex e crea quad |
| 1 vert + `extendvert=True` | vertex con 2-3 connected edges + 1-2 connected faces | `expand_vert` (variante) |

**Caso d'uso primario**: 1 vertex selection con 2 boundary edges → F2 inventa il 4° vertex e crea quad consistente con flow surrounding. **Built-in `F` non può** — richiede 2+ vertices già connessi.

## Add-on preferences

`F2AddonPreferences`, tutti `BoolProperty`:

| Pref | Default | Effetto |
|---|---|---|
| `adjustuv` | False | Estende UV mapping al nuovo quad |
| `autograb` | **True** | Invoca `transform.translate` dopo create. **Disabilita per MCP**. |
| `extendvert` | False | Abilita `expand_vert` branch |
| `quad_from_e_mat` | True | Inherita material slot da edge neighbours |
| `quad_from_v_mat` | True | Inherita material slot da vertex neighbours |
| `tris_from_v_mat` | True | Material per tris from vertex |
| `ngons_v_mat` | True | Material per n-gon from vertex |

## Failure modes

### Selezione errata su gap concavo

Per gap a 3 vertici (concave corner + 2 vertices), seleziona **SOLO il middle vertex** (concave corner), NON tutti e 3. Se selezioni i 3, F2 routes a `edge_face_add` e fa tri/n-gon (NON quad). Vedi [thread blenderartists](https://blenderartists.org/t/using-f2-properly-difficulty-with-native-addon/1331772).

### Vertex con `extendvert=True` near existing faces

Può lasciare il nuovo diagonal vertex un-merged con uno esistente. Workaround: chain con `mesh.remove_doubles(threshold=0.001)` post-F2.

### Headless mode silent failure

Documentato in [T52506](https://developer.blender.org/T52506): "doesn't create faces" — root cause è il modal `transform.translate` che stalla. Soluzione: set `autograb=False` come sopra.

### F2 require boundary edges

`quad_from_vertex` funziona solo se il vertex ha esattamente 2 **open (boundary) edges**. Se è interno (4+ edges, tutti shared by 2 faces), F2 falls back a `edge_face_add`. Verifica via:
```python
import bmesh
bm = bmesh.from_edit_mesh(obj.data)
v = bm.select_history.active  # last selected
boundary_edges = sum(1 for e in v.link_edges if e.is_boundary)
print(f"vertex has {boundary_edges} boundary edges")
# Per F2 quad_from_vertex serve == 2
```

## Patterns (FDM mesh repair)

### 1. Setup obbligatorio per uso MCP

```python
import bpy
# UNA VOLTA per sessione (idempotente):
bpy.context.preferences.addons['mesh_f2'].preferences.autograb = False
```

### 2. Fill 1 vertex gap su boundary

```python
import bpy, bmesh
obj = bpy.data.objects['<name>']
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type='VERT')
bpy.ops.mesh.select_all(action='DESELECT')

# Seleziona programmaticamente il vertex concave-corner del gap
bm = bmesh.from_edit_mesh(obj.data)
target_idx = ...  # determinato dall'analisi
bm.verts.ensure_lookup_table()
bm.verts[target_idx].select = True
bmesh.update_edit_mesh(obj.data)

# Setup + call
bpy.context.preferences.addons['mesh_f2'].preferences.autograb = False
bpy.ops.mesh.f2('INVOKE_DEFAULT')

bpy.ops.object.mode_set(mode='OBJECT')
```

### 3. Loop su N vertices per chiudere multi-quad gap

```python
import bpy

bpy.context.preferences.addons['mesh_f2'].preferences.autograb = False

for vert_idx in target_vertex_indices:
    bpy.ops.mesh.select_all(action='DESELECT')
    # ... select vert_idx via bmesh ...
    bpy.ops.mesh.f2('INVOKE_DEFAULT')

# Cleanup duplicati eventualmente introdotti
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0001)
```

### 4. Fill irregular boundary chain

Per riparare boundary irregolare con LoopTools + F2:

```python
import bpy

# 1. De-noise + circolarizza con LoopTools
bpy.ops.mesh.select_non_manifold()
bpy.ops.mesh.looptools_relax(interpolation='cubic', iterations='3', regular=True)
bpy.ops.mesh.looptools_circle(fit='best', flatten=True)

# 2. Try built-in fill_holes (più veloce per loop chiuso piccolo)
result = bpy.ops.mesh.fill_holes(sides=8)

# 3. Per i gaps residui (boundary edges ancora selezionati), F2 quad-by-quad
import bmesh
bpy.context.preferences.addons['mesh_f2'].preferences.autograb = False
bm = bmesh.from_edit_mesh(obj.data)
boundary_verts = [v for v in bm.verts if v.select and any(e.is_boundary for e in v.link_edges)]
for v in boundary_verts:
    bpy.ops.mesh.select_all(action='DESELECT')
    v.select = True
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.mesh.f2('INVOKE_DEFAULT')
```

## Comparison vs built-in `mesh.edge_face_add` (F key)

| | `mesh.edge_face_add` (F) | `mesh.f2` (F2) |
|---|---|---|
| 2+ verts selected → bridge | ✓ | ✓ (delega a edge_face_add se ≥3) |
| 1 vert with 2 boundary edges | ❌ (no face creata) | ✓ inventa 4° vertex e crea quad |
| 1 edge selected | crea edge tra endpoints (no face) | ✓ `quad_from_edge` proietta dai neighbours |
| Inherita material slot | ❌ | ✓ (configurable via prefs) |
| Headless safe | ✓ | ❌ (richiede autograb=False) |

**Regola**: usa F per bridge plain, F2 per inferire quad consistente con flow.

## Cross-reference

- [addon_looptools] — workflow canonico (relax + circle + flatten + F2 final fill)
- [mesh_repair] — built-in fill_holes (più veloce per loop chiuso piccolo)
- [blender_addons_recommended] — F2 per gap 3-5 vertex tipici post-decimate
- [addon_mesh_repair_tools] — fix_mesh_global include holes_fill ma su boundary irregolari F2 è più preciso

## Source

- [F2 source (mesh_f2.py)](https://github.com/blender/blender-addons/blob/main/mesh_f2.py)
- [F2 — Blender Extensions](https://extensions.blender.org/add-ons/f2/)
- [F2 — Blender Manual](https://docs.blender.org/manual/en/2.81/addons/mesh/f2.html)
- Bug headless mode: [T52506](https://developer.blender.org/T52506)
- Discussion concave neighbours: [blenderartists](https://blenderartists.org/t/using-f2-properly-difficulty-with-native-addon/1331772)
