# 3D Print Toolbox — Reference operativo per MCP

L'addon `object_print3d_utils` ships built-in con Blender (Edit > Preferences > Add-ons > "Mesh: 3D Print Toolbox" → enable). Espone una serie di operator `bpy.ops.mesh.print3d_*` per analisi/cleanup/transform/info/export specifici per stampa 3D. È invocabile da `execute_blender_code` via MCP.

**Source di verità**: `https://github.com/blender/blender-addons/tree/main/object_print3d_utils` (4.x) o `https://projects.blender.org/extensions/print3d_toolbox` (5.x). File rilevanti: `operators.py`, `ui.py`, `mesh_helpers.py`, `report.py`, `export.py`.

## Abilitazione programmatica

```python
import addon_utils
loaded_default, loaded_state = addon_utils.check('object_print3d_utils')
if not loaded_state:
    addon_utils.enable('object_print3d_utils')
```
Idempotente. Già wrappato dal playbook `repair_aggressive`.

## Lettura programmatica dei risultati

**Critico**: gli operator `print3d_check_*` NON modificano la selezione in EDIT mode. Salvano i risultati in un modulo-global `object_print3d_utils.report._data`, accessibile via:

```python
from object_print3d_utils import report
results = report.info()  # list of (label_str, (elem_type, [indices]))
for label, (etype, ids) in results:
    print(label, len(ids))
# 'elem_type' è una bm sequence type, es. 'EDGES', 'FACES'
```

Per **convertire risultato in selezione EDIT mode** (necessario per follow-up ops mirate):
```python
bpy.ops.mesh.print3d_select_report(index=0)  # 0 = primo report tuple
# ora sei in EDIT mode con la selezione ai problem elements
```

`report._data` è module-global, **NON persistito in .blend**, perso su addon disable/reload.

## Scene properties

Tutte sotto `bpy.context.scene.print_3d`:

| Property | Tipo | Default | Range / Unit | Letto da |
|---|---|---|---|---|
| `thickness_min` | float | **0.001 m (1mm)** | 0.0–10.0, DISTANCE | `print3d_check_thick` |
| `threshold_zero` | float | 1e-4 | 0.0–0.2 | `print3d_check_degenerate` |
| `angle_distort` | float | π/4 (45°) | 0–π, ANGLE | `print3d_check_distort`, `print3d_clean_distorted.invoke` |
| `angle_sharp` | float | ~2.79 (160°) | 0–π, ANGLE | `print3d_check_sharp` |
| `angle_overhang` | float | π/4 (45°) | 0–π/2, ANGLE | `print3d_check_overhang` |
| `use_alignxy_face_area` | bool | False | — | `print3d_align_to_xy` (face area weight su average normal) |
| `export_format` | enum | 'STL' | STL / PLY / OBJ / X3D | `print3d_export` |
| `export_path` | string | "//" | DIR_PATH max 1024 | `print3d_export` |
| `use_apply_scale` | bool | False | — | `print3d_export` |
| `use_export_texture` | bool | False | — | `print3d_export` |
| `use_data_layers` | bool | False | — | `print3d_export` (UV/normals/vcols dove supportato) |

**Critico per Bambu A1**: il default `thickness_min = 0.001 m` (1mm) è troppo permissivo. La soglia FDM con nozzle 0.4mm è 0.8mm (2 perimetri) o 0.45mm (1 perimetro singolo). Imposta esplicitamente prima di ogni `check_thick`:

```python
# Default Blender unit_settings.scale_length = 1.0 → 1 BU = 1m
bpy.context.scene.print_3d.thickness_min = 0.0008  # 0.8 mm
# Se hai unit_settings.scale_length = 0.001 (1 BU = 1mm)
bpy.context.scene.print_3d.thickness_min = 0.8
```

## Operators — Info (read-only, output via `self.report({'INFO'}, ...)`)

### `bpy.ops.mesh.print3d_info_volume()`
Calcola volume del mesh attivo (modifier applicati via `obj.evaluated_get(deps).to_mesh()`). Output: status bar + cache in `report._data`. **No selection change**. Cancella silenziosamente se active object non è mesh.

### `bpy.ops.mesh.print3d_info_area()`
Same shape — calcola surface area via `sum(face.calc_area())`.

> Per leggere il valore programmaticamente, usa direttamente `bmesh.calc_volume()` invece di parsare l'Info editor (vedi [measurement_toolkit]).

## Operators — Checks (analizzano, salvano risultati in `report._data`, NON modificano selezione)

Pattern uniforme: build evaluated bmesh → identifica elementi problematici → `report.update(*tuples)` → ritorna `{'FINISHED'}`.

### `bpy.ops.mesh.print3d_check_solid()`
Reporta:
- `Non Manifold Edge: N` (edges con `not e.is_manifold`)
- `Bad Contiguous Edges: M` (edges dove le due facce adiacenti hanno **winding opposto** → normali flipped tra loro)

Nota: "Bad Contiguous" ≠ non-manifold. Fix: `bpy.ops.mesh.normals_make_consistent(inside=False)` (Shift-N in EDIT).

### `bpy.ops.mesh.print3d_check_intersect()`
Self-intersection check. Costruisce `BVHTree.FromBMesh()` e usa `tree.overlap(tree)` per overlap pair triangoli. Reporta `Intersect Face: N`. **Costo O(n²)** — evita su mesh > 200k facce, decimate prima.

### `bpy.ops.mesh.print3d_check_degenerate()`
Usa `scene.print_3d.threshold_zero` (default 1e-4). Reporta:
- `Zero Faces: N` (`face.calc_area() < threshold`)
- `Zero Edges: M` (`edge.calc_length() < threshold`)

### `bpy.ops.mesh.print3d_check_distort()`
Usa `scene.print_3d.angle_distort` (default π/4). Reporta `Non-Flat Faces: N` via `face_is_distorted(face, angle)` che confronta face normal vs per-loop normals.

### `bpy.ops.mesh.print3d_check_thick()`
Usa `scene.print_3d.thickness_min` (default 1mm). Triangola, costruisce temp object + BVH, casts **6 ray per face** da punti offset lungo `-normal`. Reporta `Thin Faces: N`.

**Failure mode**: su mesh aperta, ray che escono dal volume attraverso buchi vengono **silenziosamente droppati**. Conseguenza: **undercount** (mesh con 1 lato aperto può riportare "Thin Faces: 0" pur avendo pareti sottili). Sempre eseguire dopo `analyze_mesh_for_print` riporta `watertight == True`. Vedi [mesh_quality_assessment] §Failure modes.

Inoltre il check è in **object local space** — applica `transform_apply(scale=True)` prima se hai scale non-uniforme.

### `bpy.ops.mesh.print3d_check_sharp()`
Usa `scene.print_3d.angle_sharp` (default ~2.79 rad / 160°). Flag manifold edges con dihedral angle che eccede threshold. Edges sharp = pareti che lo slicer non risolve correttamente.

### `bpy.ops.mesh.print3d_check_overhang()`
Usa `scene.print_3d.angle_overhang` (default π/4, max π/2). Flag faces la cui normale forma angolo troppo ripido con `+Z`. **Skippa silenziosamente se angle == π/2** (no-op). Calcolato in **object local space** — applica rotation prima se stai testando orientations alternative.

### `bpy.ops.mesh.print3d_check_all()`
Esegue sequenzialmente i 7 `main_check` sopra e concatena i risultati in un unico report. Read-only, ma report._data contiene tutti i tuple.

## Operators — Cleanup (mutano mesh)

### `bpy.ops.mesh.print3d_clean_distorted(angle=π/4)`
`bl_options={REGISTER, UNDO}`. `invoke()` preset `angle` da `scene.print_3d.angle_distort`. Triangola facce che falliscono il distortion test. Ritorna conteggio facce triangolate.

### `bpy.ops.mesh.print3d_clean_non_manifold(threshold=1e-4, sides=0)`
Pipeline interna sequenziale:
1. `delete_loose` — rimuove vertices/edges loose
2. `remove_doubles(threshold)` — merge near-duplicate vertices
3. `dissolve_degenerate(threshold)` — rimuove zero-area
4. delete interior faces — facce racchiuse interamente
5. `select_non_manifold` → iterative `fill_holes(sides=sides)` con re-check
6. `make_normals_consistent` — recalc normals outside

**Failure mode noto** (bug T48565): su mesh con T-junction densi o high-genus può **introdurre nuovi non-manifold** (il loop fill_holes termina senza convergere). Workaround: esegui 2 volte; se persiste, escalation a Voxel Remesh / QuadriFlow / R007.

### `bpy.ops.mesh.print3d_clean_thin()` — **STUB, non chiamare**
**NOT IMPLEMENTED** in main attuale. Ritorna `{'FINISHED'}` immediatamente senza effetto. Da non includere in pipeline. Per thin walls usa Solidify (vedi [wall_thickness_actionable]).

## Operators — Transform / Edit

### `bpy.ops.mesh.print3d_scale_to_volume(volume=...)`
`invoke()` misura volume corrente in `volume_init` e mostra popup. `execute()` calcola `factor = (volume / volume_init) ** (1/3)` e applica resize uniforme via `bpy.ops.transform.resize`. **Unità: VOLUME del scene unit system** (m³ default, mm³ se hai cambiato).

### `bpy.ops.mesh.print3d_scale_to_bounds(length=...)`
Same pattern usando dominant bbox axis; uniform scale a fit. **Unità: LENGTH** (metri default).
```python
# Bambu A1 max dim 256mm → length=0.256
bpy.ops.mesh.print3d_scale_to_bounds(length=0.256)
```

### `bpy.ops.mesh.print3d_align_to_xy()`
Richiede EDIT_MESH o OBJECT con almeno una face selezionata per object. Calcola normale media (area-weighted se `scene.print_3d.use_alignxy_face_area=True`), computa quaternion che ruota quella normale a `-Z`, moltiplica in `obj.matrix_world.rotation`. Cancella per-object se nessuna face selezionata.

```python
# Per "lay flat" auto: seleziona la face che vuoi sul piatto, poi:
bpy.context.scene.print_3d.use_alignxy_face_area = True
bpy.ops.mesh.print3d_align_to_xy()
```

### `bpy.ops.mesh.print3d_hollow(offset_direction='INSIDE', offset=1.0, voxel_size=1.0, make_hollow_duplicate=False)`
`bl_options={REGISTER, UNDO, PRESET}`. **Richiede `pyopenvdb`** (bundled in Blender moderno). Costruisce VDB SDF, offset, opzionalmente combina per shell, converte back via `convertToQuads()`, crea nuovo object con normali corrette. Cancella con error se `offset == 0`.

Parametri:
- `offset_direction`: 'INSIDE' (svuota) | 'OUTSIDE' (gonfia)
- `offset`: spessore shell (in metri se default scale_length)
- `voxel_size`: risoluzione VDB
- `make_hollow_duplicate`: se True, duplica oggetto invece di sostituirlo

> Caveat FDM: per Bambu A1 NON svuotare in Blender — l'infill dello slicer è più efficiente (vedi `_archive/docs/hollowing_and_lightening.md`). `print3d_hollow` ha senso solo per casi speciali (modelli per silicone/cera persa, vase mode prep).

## Operators — Selection helper

### `bpy.ops.mesh.print3d_select_report(index=N)`
`bl_options={'INTERNAL'}`. Legge `report.info()[index]`, switcha a EDIT_MESH, set select_mode (VERT/EDGE/FACE) per tipo, deseleziona tutto, seleziona elementi per indice.

**Warning**: se la mesh è stata modificata dopo l'ultimo check, gli indici sono stale → il report logga warning ma non blocca.

## Operators — Export

### `bpy.ops.mesh.print3d_export()`
Legge tutte `scene.print_3d.export_*` e dispatcha via `export.write_mesh()` al matching exporter (`bpy.ops.wm.{stl,obj,ply,x3d}_export`). Scrive in `export_path`. Ritorna `{'CANCELLED'}` su writer failure.

> Per controllo fine usa direttamente `bpy.ops.wm.stl_export(...)` con parametri espliciti — vedi `import_export.md` e FIELD_NOTES per caveat su `global_scale` / `use_scene_unit`.

## N-Panel UI (3D View → tab "3D-Print")

Layout 4 sezioni:
- **Analyze** (open by default): Volume, Area, poi 7 check ognuno con la sua threshold prop, poi Check All, poi dynamic clickable Result list
- **Clean Up** (closed): Distorted + angle, Make Manifold
- **Edit** (closed): Hollow, Scale to Volume, Scale to Bounds, Align XY + use_alignxy_face_area
- **Export** (closed): path, format, options, Export button

## Pattern idiomatici

### 1. Set threshold PRIMA di check_thick (FDM 0.4mm nozzle → 0.8mm walls)

```python
import bpy
bpy.context.scene.print_3d.thickness_min = 0.0008  # metri (assumendo scale_length=1.0)
obj = bpy.data.objects['<name>']
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.mesh.print3d_check_thick()

from object_print3d_utils import report
results = report.info()
# results = [('Thin Faces: N', ('FACES', [idx0, idx1, ...]))]
```

### 2. Check + select_report + edit follow-up

```python
# Trovi distortion + triangoli quelli specifici
bpy.ops.mesh.print3d_check_distort()
bpy.ops.mesh.print3d_select_report(index=0)  # ora sei in EDIT mode con i bad faces selezionati
bpy.ops.mesh.tris_convert_to_quads()
bpy.ops.object.mode_set(mode='OBJECT')
```

### 3. One-shot triage con check_all

```python
bpy.ops.mesh.print3d_check_all()
from object_print3d_utils import report
for label, (etype, ids) in report.info():
    print(f"{label}: {len(ids)} {etype}")
# Output esempio:
# Non Manifold Edge: 12 EDGES
# Bad Contiguous Edges: 0 EDGES
# Intersect Face: 3 FACES
# Zero Faces: 0 FACES
# Zero Edges: 0 EDGES
# Non-Flat Faces: 24 FACES
# Thin Faces: 8 FACES
# Sharp Edge: 56 EDGES
# Overhang Face: 142 FACES
```

### 4. Repair iterativo (R005 escalation)

```python
import bmesh
obj = bpy.data.objects['<name>']
for i in range(3):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.print3d_clean_non_manifold(threshold=1e-4, sides=8)
    bm = bmesh.from_edit_mesh(obj.data)
    nm_count = sum(1 for e in bm.edges if not e.is_manifold)
    bpy.ops.object.mode_set(mode='OBJECT')
    if nm_count == 0:
        break
```

### 5. Scale-to-bounds programmaticamente per Bambu A1

```python
# Ridimensiona mesh per stare dentro 256mm max dim
bpy.ops.mesh.print3d_scale_to_bounds(length=0.256)  # m
# Poi apply scale per blocked-in coordinates
bpy.ops.object.transform_apply(scale=True)
```

### 6. Auto-orient face piatta verso il letto

```python
# 1. Identifica face piatta più grande (in EDIT mode)
import bmesh
bm = bmesh.from_edit_mesh(obj.data)
faces_by_area = sorted(bm.faces, key=lambda f: f.calc_area(), reverse=True)
target = faces_by_area[0]
bpy.ops.mesh.select_all(action='DESELECT')
target.select = True
bmesh.update_edit_mesh(obj.data)

# 2. Align
bpy.context.scene.print_3d.use_alignxy_face_area = True
bpy.ops.mesh.print3d_align_to_xy()
```

### 7. Pre-emptive overhang assessment per orientation_strategy

```python
# Prima di valutare un'orientation candidate
obj.rotation_euler = (rx, ry, rz)
bpy.ops.object.transform_apply(rotation=True)  # critico — overhang check è local space
bpy.context.scene.print_3d.angle_overhang = 0.785  # 45° rad
bpy.ops.mesh.print3d_check_overhang()
from object_print3d_utils import report
overhang_count = len(report.info()[0][1][1]) if report.info() else 0
```

## Confronto con `analyze_mesh_for_print` (tool MCP custom)

| | `analyze_mesh_for_print` | 3D Print Toolbox |
|---|---|---|
| Output | JSON strutturato (parsabile) | `report._data` modulo-global (Python-leggibile via `report.info()`) |
| Scope | snapshot completo (manifold, holes, shells, normals, wall thickness, dimensions, partial inversion) | un check alla volta, granulare per category |
| Latenza | una chiamata MCP | una `bpy.ops` per check |
| Wall thickness | sampling 5000 face centroids, p10/p50/under_min_pct | 6 ray per face su tutta la mesh, conta count |
| Sharp edges | ❌ | ✅ `check_sharp` |
| Overhang count | ❌ | ✅ `check_overhang` |
| Self-intersect | ❌ | ✅ `check_intersect` (lento O(n²)) |
| Normals partial inversion | ✅ `inverted_face_pct` | ❌ (solo Bad Contiguous count) |
| Disconnected shells | ✅ | ❌ |
| Mutator ops | ❌ (solo analisi) | ✅ `clean_*`, `align_to_xy`, `hollow`, `scale_to_*` |
| Use case | **Decisione di routing** (`kb_route`) | **Investigazione mirata + mutazione** dopo routing |

**Workflow integrato consigliato**:

1. `analyze_mesh_for_print` → output JSON → `kb_route` decide quale playbook attivare.
2. Playbook esegue mutazioni con Toolbox (`clean_non_manifold`, `align_to_xy`, ecc.).
3. Per drill-down (es. "trova esattamente le facce thin"), eseguire toolbox check + `select_report` per selezione visiva nel viewport.
4. Re-`analyze_mesh_for_print` per verifica delta atteso.

**Toolbox unicamente per**: sharp edge detection, overhang count per orientation scoring (vedi [orientation_strategy] §Migliorie 2024-2026), self-intersection (su mesh decimate sotto 200k), hollow VDB-based per casi speciali.

**MCP unicamente per**: routing automatico, partial inversion, shell counting, statistical wall thickness distribution.

## Quirks ricapitolati

1. `check_*` operator NON modificano selezione, salvano in `report._data` modulo-global.
2. `check_thick` su mesh aperta: undercount (rays escono dai buchi e vengono droppati silenziosamente).
3. `check_overhang` opera in **object local space** — apply rotation prima.
4. `clean_non_manifold` può **introdurre** nuovi non-manifold su T-junction densi (T48565). Iterare 2-3 volte.
5. `clean_thin` è **stub vuoto** — non chiamare.
6. `report._data` è module-global, perso su addon disable/reload, NON in .blend.
7. `align_to_xy` richiede face selezionate per object — cancella per-object se nessuna selezione.
8. `hollow` richiede `pyopenvdb`; per FDM A1 quasi sempre meglio infill slicer.
9. "Bad Contiguous Edges" ≠ non-manifold; sono normali flipped tra facce adiacenti. Fix: `normals_make_consistent`.
10. `print3d_info_volume` cache in report._data — può essere letto via `report.info()` invece che parsare status bar.

## Riferimenti

- Source: [`blender-addons/object_print3d_utils`](https://github.com/blender/blender-addons/tree/main/object_print3d_utils)
- 5.x: [`projects.blender.org/extensions/print3d_toolbox`](https://projects.blender.org/extensions/print3d_toolbox)
- Manual: [docs.blender.org/manual/en/latest/addons/mesh/3d_print_toolbox.html](https://docs.blender.org/manual/en/latest/addons/mesh/3d_print_toolbox.html)
- Bug T48565 (`clean_non_manifold` introduces new non-manifold): [developer.blender.org/T48565](https://developer.blender.org/T48565)
- Bad Contiguous Edges discussion: [blenderartists.org/t/bad-contiguous-edges/1601955](https://blenderartists.org/t/bad-contiguous-edges/1601955)
- [mesh_repair] §Failure modes — quirks di `clean_non_manifold` nel contesto pipeline
- [mesh_quality_assessment] §Failure modes — quirks di `check_thick` e `check_intersect`
- [orientation_strategy] §Migliorie 2024-2026 — usa `check_overhang` per scoring
- [wall_thickness_actionable] — alternativa a `check_thick` per metric strutturate
- Playbook `repair_aggressive` — uso reale di `print3d_clean_non_manifold` con escalation
