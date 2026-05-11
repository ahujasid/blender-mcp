# LoopTools — Reference operativo

Addon `mesh_looptools` (extensions.blender.org, GPL, no longer bundled da Blender 4.2). 8 operator per manipolazione edge loops e mesh repair, indispensabili per riparare buchi grandi/irregolari su mesh AI post-decimate.

Mode richiesto: **EDIT** (`context.mode == 'EDIT_MESH'`, `ob.type == 'MESH'`). Tutti gli operator sotto namespace `bpy.ops.mesh.looptools_*`.

## Operators

### `bpy.ops.mesh.looptools_bridge(...)`

Bridge tra due (o N) edge loops. Best per chiudere gap tra boundary loops o lofting multi-section.

| Param | Type | Default | Note |
|---|---|---|---|
| `cubic_strength` | float | 1.0 | Per `interpolation='cubic'` |
| `interpolation` | enum | `cubic` | `cubic` \| `linear` |
| `loft` | bool | False | True = multi-loop loft |
| `loft_loop` | bool | False | Closed loft |
| `min_width` | int | 0 | % minimum face width |
| `mode` | enum | `shortest` | `basic` \| `shortest`. **Hidden in UI** ma callable. `shortest` matcha vertici greedy by 3D distance. |
| `remove_faces` | bool | True | Rimuove face originali |
| `reverse` | bool | False | Inverte direzione (per twist correction) |
| `segments` | int | 1 | 0 = auto |
| `twist` | int | 0 | Aggiunge twist N positions |

**Selezione**: 2 open edge loops (o N se `loft=True`). Equal vertex count NON strettamente richiesto — `mode='shortest'` matcha vertici greedy. Risultato con count differente: triangoli/skewed quads.

**Side effect importante**: bridge fa anche `mesh.normals_make_consistent` internamente (line 3419 source). Gli altri op LoopTools no.

### `bpy.ops.mesh.looptools_circle(...)`

Rende un loop una circle (best-fit + flatten in uno shot).

| Param | Type | Default | Note |
|---|---|---|---|
| `fit` | enum | `best` | `best` (best-fit center) \| `inside` (inscribed) |
| `flatten` | bool | True | Project su best-fit plane prima |
| `custom_radius` | bool | False | True = usa `radius` esplicito |
| `radius` | float | 1.0 | Solo se custom_radius |
| `angle` | float | 0.0 | rad, rotation offset |
| `regular` | bool | True | Vertices spaced equally |
| `influence` | float | 100.0 | 0-100, fade verso forma originale |
| `lock_x/y/z` | bool | False | **lowercase**. Lock asse durante move |

**Quirk**: con `flatten=False` su loop bumpy, projection su mesh può dare self-intersection.

### `bpy.ops.mesh.looptools_flatten(...)`

Coplanar projection di vertices/loop su un piano.

| Param | Type | Default | Note |
|---|---|---|---|
| `plane` | enum | `best_fit` | `best_fit` \| `normal` (face normale) \| `view` |
| `restriction` | enum | `none` | `none` \| `bounding_box` |
| `influence` | float | 100.0 | |
| `lock_x/y/z` | bool | False | Combina con plane='best_fit' per project su asse specifico |

**Pattern flatten bottom Z=0**:
```python
bpy.ops.mesh.looptools_flatten(plane='best_fit', lock_x=True, lock_y=True, influence=100.0)
# Poi snap Z = 0 con translate
```

### `bpy.ops.mesh.looptools_relax(...)`

De-noising vertex positions (loop-aware smoothing).

| Param | Type | Default | Note |
|---|---|---|---|
| `interpolation` | enum | `cubic` | `cubic` (preserve volume) \| `linear` (project on edges) |
| `input` | enum | `selected` | `selected` \| `all` (incl parallel loops) |
| `iterations` | enum | `'1'` | **STRING enum** `'1'`/`'3'`/`'5'`/`'10'`/`'25'` — NON int! |
| `regular` | bool | True | |

**⚠ Gotcha tipico**: `iterations=3` (int) NON funziona. Devi passare `iterations='3'` (string). Errori su questo punto sono silent.

**⚠ Volume loss**: `iterations='25'` con `interpolation='linear'` collassa loop chiuso visibilmente. Sempre preferire `cubic` per loop chiusi; linear solo per project su edge esistenti. Vedi [T90600](https://developer.blender.org/T90600).

### `bpy.ops.mesh.looptools_space(...)`

Distribuisce vertices uniformemente lungo loop. Pattern obbligatorio prima di `bridge` su loop con vertex count uguale ma spacing irregolare.

| Param | Type | Default | Note |
|---|---|---|---|
| `interpolation` | enum | `cubic` | `cubic` \| `linear` |
| `input` | enum | `selected` | `selected` \| `all` |
| `influence` | float | 100.0 | |
| `lock_x/y/z` | bool | False | |

### `bpy.ops.mesh.looptools_curve(...)`

Smoothing che produce curve "fluente" (oltre relax).

| Param | Type | Default | Note |
|---|---|---|---|
| `boundaries` | bool | False | Include boundary edges |
| `interpolation` | enum | `cubic` | |
| `regular` | bool | True | |
| `restriction` | enum | `none` | `none` \| `extrude` \| `indent` |
| `influence` | float | 100.0 | |
| `lock_x/y/z` | bool | False | |

### `bpy.ops.mesh.looptools_loft(...)`

Multi-loop loft (più loop, simile a `bridge(loft=True)` ma più controllo).

### `bpy.ops.mesh.looptools_gstretch(...)`

Snap mesh a grease pencil strokes. **Non rilevante per FDM**, skip.

## Quirks critici per uso MCP

### `iterations` di relax è EnumProperty di string

```python
# WRONG (silent failure):
bpy.ops.mesh.looptools_relax(iterations=3)

# CORRECT:
bpy.ops.mesh.looptools_relax(iterations='3')
```

### lock_x/y/z lowercase

```python
# WRONG (silent ignore o error):
bpy.ops.mesh.looptools_flatten(lock_X=True)

# CORRECT:
bpy.ops.mesh.looptools_flatten(lock_x=True)
```

### Cache invalidation

LoopTools cacha risultati per operator (`cache_read`/`cache_write`). Se selection cambia tra call e re-run rapido, stale cached loops applicati.

Workaround:
```python
bpy.ops.ed.undo_push(message="invalidate looptools cache")
# ora chiamata successiva è clean
```

O toggle un property dell'operator (es. `iterations='3'` → `'1'` → `'3'`).

### Bridge con vertex count diverso

NON fallisce, ma produce triangoli/quads skewed. Per result clean: equalizza con `looptools_space` prima, o subdivide/dissolve per matchare count.

### Bridge non-parallel loops

Funziona se `mode='shortest'`. Se `reverse=False` produce twist visibile, set `reverse=True`.

## Patterns per FDM mesh repair

Workflow canonico per riparare buco su AI mesh post-decimate:

```python
import bpy

def repair_boundary_hole_with_looptools(obj_name):
    obj = bpy.data.objects[obj_name]
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')

    # 1. Seleziona boundary edges (gap aperto)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()  # boundary edges del buco

    # 2. De-noise il boundary (3 iter cubic)
    bpy.ops.mesh.looptools_relax(interpolation='cubic', iterations='3', regular=True)

    # 3. Re-circolarizza se hole è approx round
    bpy.ops.mesh.looptools_circle(fit='best', flatten=True, regular=True, influence=100.0)

    # 4. Flatten su best-fit plane
    bpy.ops.mesh.looptools_flatten(plane='best_fit', influence=100.0)

    # 5. Chiudi (3 opzioni alternative):
    #    a) fill_holes built-in se loop chiuso, sides up to 32
    bpy.ops.mesh.fill_holes(sides=32)
    #    b) edge_face_add se loop molto piccolo (n-gon)
    # bpy.ops.mesh.edge_face_add()
    #    c) bridge con altro loop (se ce n'è uno separato)
    # bpy.ops.mesh.looptools_bridge(...)

    # 6. Recalc normals (fill_holes/edge_face_add NON lo fanno)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)

    bpy.ops.object.mode_set(mode='OBJECT')
```

### Pattern bridge tra 2 shell separate

```python
import bpy
bpy.ops.object.mode_set(mode='EDIT')
# Pre-requisiti: due boundary loop selezionati, uno per shell
# (es. via select_linked + select_non_manifold per shell singola)

# Equalizza spacing prima del bridge
bpy.ops.mesh.looptools_space(interpolation='cubic', input='selected', influence=100.0)

# Bridge
bpy.ops.mesh.looptools_bridge(
    segments=1,
    interpolation='cubic',
    cubic_strength=1.0,
    mode='shortest',     # matcha vertici greedy
    remove_faces=True,
    loft=False,
    reverse=False,       # set True se vedi twist
)
# Bridge chiama normals_make_consistent internamente — non serve manuale
bpy.ops.object.mode_set(mode='OBJECT')
```

### Pattern flatten bottom face per build plate

```python
import bpy
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type='VERT')
bpy.ops.mesh.select_all(action='DESELECT')

# Seleziona vertici a Z minimo (entro tolleranza)
import bmesh
bm = bmesh.from_edit_mesh(obj.data)
zmin = min(v.co.z for v in bm.verts)
for v in bm.verts:
    if v.co.z < zmin + 0.001:  # 1mm tolerance
        v.select = True
bmesh.update_edit_mesh(obj.data)

# Flatten al piano XY (lock_x + lock_y → solo Z move)
bpy.ops.mesh.looptools_flatten(plane='best_fit', lock_x=True, lock_y=True, influence=100.0)

# Snap Z = 0
bpy.ops.transform.translate(value=(0, 0, -zmin))

bpy.ops.object.mode_set(mode='OBJECT')
```

## Comparison vs built-in equivalents

| LoopTools | Blender built-in | Quando preferire LoopTools |
|---|---|---|
| `looptools_bridge` | `mesh.bridge_edge_loops` | Loop con vertex count differente o non-aligned. Built-in per smooth profile-shaped joins tra loop allineati. |
| `looptools_circle` | `mesh.to_sphere` (Shift+Alt+S, factor=1) | `to_sphere` interpola verso sfera; `looptools_circle` è best-fit circle + flatten in uno shot. **Per hole repair sempre LoopTools**. |
| `looptools_flatten` | `mesh.vert_align`, scale-to-zero su asse | Built-in serve pivot/asse manuale; LoopTools computa best-fit plane auto. |
| `looptools_relax` | `mesh.vertices_smooth` (Smooth Vertices) | Smooth shrinks geometry; relax con cubic preserve volume meglio + loop-aware. |
| `looptools_space` | (nessuno) | Closest = `mesh.subdivide` + edits manuali. LoopTools è canonical "even spacing". |
| `looptools_curve` | (nessuno) | No equivalent. |

## Cross-reference

- [addon_f2] — F2 per quad fill su 3-5 vertex gap (complementare a LoopTools per buchi piccoli)
- [mesh_repair] — operatori built-in (fill_holes, normals_make_consistent)
- [addon_mesh_repair_tools] — fix_mesh_global pipeline (chain con relax+circle+flatten per casi difficili)
- [blender_addons_recommended] — workflow canonico repair AI mesh

## Source

- [LoopTools source (mesh_looptools.py)](https://github.com/blender/blender-addons/blob/main/mesh_looptools.py) — Bart Crouch / Vladimir Spivak, v4.7.7
- [LoopTools — Blender Extensions](https://extensions.blender.org/add-ons/looptools/)
- [LoopTools — Blender Manual](https://docs.blender.org/manual/en/latest/addons/mesh/looptools.html)
- Bug report relax volume loss: [T90600](https://developer.blender.org/T90600)
- Tracker tool: [T26189](https://developer.blender.org/T26189)
- Discussion bridge unequal vertex count: [blenderartists.org thread](https://blenderartists.org/t/how-to-even-out-vertex-count-on-two-open-edgeloops-for-clean-bridge-results/1291481)
