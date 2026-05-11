# Mesh Repair Tools — Reference operativo

Addon `mesh_repair_tools` di SineWave (extensions.blender.org, GPL-3.0, v4.0.2 from 2024-09-18). Stale ma stabile su Blender 4.2+. Espone un **mega-operator** `object.fix_mesh_global` (la "AutoFix") + 7 ops locali per cleanup mirato in EDIT mode.

**Killer feature vs 3D Print Toolbox**: il custom hole-fill rimuove >2-face shared boundary verts PRIMA di `edgeloop_fill` su ogni boundary loop — risolve il caso "il built-in `fill_holes` non chiude" tipico di mesh AI con boundary irregolari.

## N-panel UI

`View3D > Sidebar > "Mesh Repair"`:
- `Local Fix` panel (visible solo in EDIT mode)
- `Global Fix` panel (OBJECT o EDIT)

## Operators

### `bpy.ops.object.fix_mesh_global()` — la "AutoFix"

Mode: OBJECT o EDIT (auto-switch). Selection: nessuna richiesta.

**No operator-level params**. Pipeline driven da `bpy.context.scene.meshfixtool_properties` toggles. Sequenza interna:

1. `mesh.remove_doubles` (default threshold)
2. `mesh.quads_convert_to_tris` (se `tri_boolean=True`) o `mesh.tris_convert_to_quads` (se `quad_boolean=True`)
3. `mesh.normals_make_consistent` (se `face_normal_boolean=True`)
4. `bm_remove_spikes` custom (se `spikes_boolean=True`)
5. `bm_smooth_mesh` intersection (se `intersection_boolean=True`)
6. `remove_loose_parts` (se `minor_parts_boolean=True`)
7. (opzionale) volume-intersection boolean union (se `volume_intersection_boolean=True`) — **clear modifiers + drop vertex groups**
8. Custom `fill_holes` (se `holes_boolean=True`) — edgeloop_fill su ogni boundary
9. Final `remove_doubles` + retri/quad

**⚠ Performance**: panel warns su mesh > 300k verts. Su mesh più grandi pre-decimate.

### Properties da settare prima

`bpy.context.scene.meshfixtool_properties` (PropertyGroup):

| Prop | Type | Default | Effetto |
|---|---|---|---|
| `tri_boolean` | bool | True | Tris finale (mutex con quad_boolean) |
| `quad_boolean` | bool | False | Quads finale |
| `face_normal_boolean` | bool | True | Recalc normals outside |
| `minor_parts_boolean` | bool | True | Delete noise shells |
| `minor_parts_threshold` | float | 1.0 | % del face count totale (0.1–5) |
| `spikes_boolean` | bool | True | Dissolve vertex spikes |
| `spikes_angle_limit` | float | 10.0 | deg, 1–60 (180-x usato internally) |
| `intersection_boolean` | bool | True | Smooth self-intersection |
| `intersection_angle_limit` | float | 10.0 | deg |
| `holes_boolean` | bool | True | Custom edgeloop_fill |
| `volume_intersection_boolean` | bool | False | **CAUTION**: clears modifiers + drops vgroups |
| `wiz_boolean` | bool | False | Fix Wizard branch (paid companion, lascia False) |

### `bpy.ops.object.local_face_normal()` — smart recalc

Mode: EDIT, face selection.
Mechanism: `mesh.normals_make_consistent(inside=False)` poi se nessuna normal cambiata, `mesh.flip_normals` — unify-then-toggle. Smarter del built-in che richiede 2 passi manuali.

### `bpy.ops.object.remesh_local_v2()`

Mode: EDIT, face selection.
Pipeline: `subdivide(1)` → `vertices_smooth_laplacian(repeat=10)` → `decimate(ratio=0.3)`.
**Quirk**: può collassare small islands.

### `bpy.ops.object.smooth_local_v2()`

Mode: EDIT.
Mechanism: `mesh.vertices_smooth(factor=0.5, repeat=5)`.

### `bpy.ops.object.flatten_local()`

Mode: EDIT, contiguous face selection.
Mechanism: `mesh.looptools_flatten` → resize 0.5 → translate by `bumper_reduction` offset → delete face → re-bridge → subdivide+smooth.
**Requirement**: LoopTools addon abilitato (auto-enabled da MRT).
**Failure**: "Invalid mesh selection" se selected faces NON sono single connected island.

### `bpy.ops.object.reduce_local()`

Mode: EDIT, face selection.
Mechanism: `mesh.decimate(ratio=0.5)`.

### `bpy.ops.object.refind_local()` — "Refine" (typo nel bl_idname)

Mode: EDIT, face selection.
Pipeline: `select_less` → subdivide → laplacian smooth → `select_more` → tris.

### `bpy.ops.object.mrts_sinewave()`

UI link to author. Skip programmaticamente.

## Patterns

### 1. AutoFix completo per mesh AI decimata

```python
import bpy
obj = bpy.context.active_object  # o by name
bpy.context.view_layer.objects.active = obj

p = bpy.context.scene.meshfixtool_properties
p.tri_boolean = True
p.face_normal_boolean = True
p.minor_parts_boolean = True
p.minor_parts_threshold = 1.0
p.spikes_boolean = True
p.spikes_angle_limit = 10.0
p.intersection_boolean = True
p.intersection_angle_limit = 10.0
p.holes_boolean = True
p.volume_intersection_boolean = False  # safe default
p.wiz_boolean = False
bpy.ops.object.fix_mesh_global()
```

### 2. AutoFix + 3D Print Toolbox QC chained

```python
import bpy

# AutoFix MRT
p = bpy.context.scene.meshfixtool_properties
p.tri_boolean = True
p.face_normal_boolean = True
p.minor_parts_boolean = True
p.spikes_boolean = True
p.holes_boolean = True
bpy.ops.object.fix_mesh_global()

# QC con 3D Print Toolbox
bpy.ops.mesh.print3d_check_all()

from object_print3d_utils import report
for label, (etype, ids) in report.info():
    print(f"{label}: {len(ids)}")
# Se non-manifold > 0 nonostante AutoFix → considera Voxel Remesh (fallback nuclear)
```

### 3. Smart normal recalc dopo Boolean

```python
import bpy
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.object.local_face_normal()
bpy.ops.object.mode_set(mode='OBJECT')
```

### 4. Fix con volume_intersection (CAUTION)

```python
import bpy

# Backup vertex groups e modifiers PRIMA (vengono droppati)
backup_vgroups = [vg.name for vg in obj.vertex_groups]

p = bpy.context.scene.meshfixtool_properties
# ... configura tutti i toggle base ...
p.volume_intersection_boolean = True  # ← dangerous
bpy.ops.object.fix_mesh_global()

# Re-create vertex groups se servono (data persa)
for name in backup_vgroups:
    if name not in obj.vertex_groups:
        obj.vertex_groups.new(name=name)
```

## Failure modes

- **`object.fix_mesh_global` su mesh > 300k verts**: panel warns, può richiedere minuti. Pre-decimate prima.
- **`volume_intersection_boolean=True`**: clear modifier stack + drop vertex groups. Backup prima.
- **`object.flatten_local` senza LoopTools**: error. MRT auto-enabled LoopTools, ma verifica con `addon_utils.check('mesh_looptools')`.
- **Custom holes_fill su boundary già planari ma irregolari**: produce edgeloop fill che a volte ha self-intersection. Re-check con `print3d_check_intersect` post.
- **Spikes_angle_limit basso (<5°)**: aggressive dissolve, può rimuovere feature legittime. Default 10° safe.

## Comparison vs 3D Print Toolbox

| Capability | Mesh Repair Tools | 3D Print Toolbox | Quale usare |
|---|---|---|---|
| Manifold cleanup | `object.fix_mesh_global` (multi-pass, configurable) | `mesh.print3d_clean_non_manifold` (single op) | **MRT per AI/scan** (più aggressivo). PT3D per hand-modeled. |
| Fill holes | Custom: rimuove >2-face shared verts poi `edgeloop_fill` | Part di `clean_non_manifold` (built-in `fill_holes`) | **MRT** quando boundary irregolare (PT3D fallisce). PT3D per loop chiusi puliti. |
| Recalc normals | `object.local_face_normal` (auto-flip) | Inside `clean_non_manifold` | MRT per selection-only; PT3D per whole-object. |
| Spike removal | `spikes_boolean` (vertex-angle dissolve) | `mesh.print3d_check_distort` | **MRT actually fixes**; PT3D solo reports. |
| Loose parts | `minor_parts_boolean` (% threshold tunable) | `mesh.print3d_check_isolated` | Equivalent. MRT espone threshold. |
| Self-intersect | `volume_intersection_boolean` (boolean union of intersecting islands) | `mesh.print3d_check_intersect` (reports only) | **MRT actually fixes**; PT3D solo reports. |
| Pre-print analysis (vol, area, sharp, overhang, dim, error reports) | nessuno | full | **PT3D** — keep per QC dopo MRT cleanup. |
| Export STL | nessuno | `mesh.print3d_export` | PT3D. |

**Recommended workflow Bambu A1**: MRT `fix_mesh_global` → PT3D `print3d_check_all` per QC → fix issues flaggati manualmente → PT3D `print3d_export`.

## Maintenance status

- Single 2024-09-18 release (`v4.0.2`).
- 0 GitHub issues sul repo stub `MWW-AC/Mesh-Repair-Tools` (real source ships in zip).
- Stale ma stabile. Usa con fiducia su Blender 4.2+.

## Cross-reference

- [blender_3d_print_toolbox] — overlap detail + complementarità
- [mesh_repair] — operator built-in (uguali a quelli che MRT chiama internalmente)
- [addon_looptools] — required dependency per `flatten_local`
- [decimation_remesh] — pre-decimate se mesh > 300k

## Source

- [Mesh Repair Tools — Blender Extensions](https://extensions.blender.org/add-ons/mesh-repair-tools/)
- [MWW-AC/Mesh-Repair-Tools releases](https://github.com/MWW-AC/Mesh-Repair-Tools/releases) — stub repo, real source nel zip
- [Version history](https://extensions.blender.org/add-ons/mesh-repair-tools/versions/)
