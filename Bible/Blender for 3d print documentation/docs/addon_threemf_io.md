# threemf-io — Reference operativo

Addon per import/export 3MF, primario nel handoff Blender → Bambu Studio. Due fork attivi (Ghostkeeper original e LeeGillie fork) con **identica operator API** ma compatibilità Blender molto diversa.

**⚠ Bug critico Blender 4.5+**: Ghostkeeper master (la versione su `extensions.blender.org`) è **rotto** su Blender 4.5+ con `TypeError: Import3MF.__init__() takes 1 positional argument but 2 were given` ([#81](https://github.com/Ghostkeeper/Blender3mfFormat/issues/81)/[#84](https://github.com/Ghostkeeper/Blender3mfFormat/issues/84)/[#87](https://github.com/Ghostkeeper/Blender3mfFormat/issues/87)/[#92](https://github.com/Ghostkeeper/Blender3mfFormat/issues/92)). **Per Blender 4.5/5.x usa LeeGillie fork v2.2.1+** ([github.com/LeeGillie/Blender3mfFormat](https://github.com/LeeGillie/Blender3mfFormat)).

## Operators

Solo 2 operator registrati. Entrambi richiedono **OBJECT mode** (export da EDIT mode raise context error in 4.x).

### `bpy.ops.import_mesh.threemf(...)`

`bl_idname = "import_mesh.threemf"`, `bl_options = {'UNDO'}`, `filename_ext = ".3mf"`.

| Param | Type | Default | Range | Note |
|---|---|---|---|---|
| `filepath` | str | `""` | path absoluto richiesto | ImportHelper |
| `filter_glob` | str | `"*.3mf"` | hidden | leave default |
| `files` | CollectionProperty | — | — | per multi-file batch |
| `directory` | str (DIR_PATH) | — | — | con `files` |
| `global_scale` | float | `1.0` | 0.001–1000 | scale post-load dall'origine |

Restituisce `{'FINISHED'}` o `{'CANCELLED'}` (solo su `zipfile.BadZipFile`/`EnvironmentError`). Warning per-object loggati via `self.report({'WARNING'}, ...)` ma non abortano.

### `bpy.ops.export_mesh.threemf(...)`

`bl_idname = "export_mesh.threemf"`, `filename_ext = ".3mf"`.

| Param | Type | Default | Range | Note |
|---|---|---|---|---|
| `filepath` | str | `""` | path absoluto | ExportHelper |
| `filter_glob` | str | `"*.3mf"` | hidden | |
| `use_selection` | bool | `False` | — | True = `context.selected_objects`; False = `scene.objects` |
| `global_scale` | float | `1.0` | 0.001–1000 | moltiplicato con `unit_settings.scale_length` |
| `use_mesh_modifiers` | bool | `True` | — | True = depsgraph evaluated; False = raw mesh |
| `coordinate_precision` | int | `4` | 0–12 | digit decimali nei vertex coords XML |

## Capabilities & limits

**Spec coverage**:
- Ghostkeeper v1.0.2: 3MF Core Spec **1.2.3 only**. README esplicito: "No 3MF format extensions are currently supported."
- LeeGillie v2.2.1 (Feb 2026): Core **1.4.0** + Triangle Sets v1.3.0 (organizational grouping).
- Nessuno dei due supporta Beam Lattice, Slice, Secure Content, **Production Extension** (paint Bambu, multi-plate config).
- PR [#58](https://github.com/Ghostkeeper/Blender3mfFormat/pull/58) (aperto da 2022, **unmerged**) aggiunge Production Extension *read* + Color Groups I/O.

**Materials**:
- Mappatura via Principled BSDF Base Color → 3MF `<basematerials>` `displaycolor` come `#RRGGBB`/`#RRGGBBAA`.
- Una `<basematerials>` group per file.
- Slot dominante = material dell'object; triangoli divergenti emettono `pindex` overrides.
- **NO texture/UV roundtrip** — issue [#52](https://github.com/Ghostkeeper/Blender3mfFormat/issues/52) closed Won't Fix.

**Multi-plate via Parent Empty** (CORREZIONE): contrariamente a quanto sentito in giro, questo NON è una feature reale. L'exporter walka parent-child: root objects (no parent) diventano `<build><item>` entries; children diventano `<components>`. Un Empty parent diventa parentless `<item>` senza mesh — utile per **grouping** in slicer che rispettano `<item>` per object, ma **NON splitta in plates separate Bambu Studio**. La plate config Bambu vive in proprietary `Metadata/model_settings.config` che questo addon non scrive.

**Units**:
- Export scrive `unit="millimeter"` e applica `global_scale * scene.unit_settings.scale_length * 1000` (Blender stora metri internamente).
- Default `scale_length=1.0` (m) + `global_scale=1.0` → mm corretto.
- Import scala solo per `global_scale` — no auto-conversion a scene units.

**Paint / support paint**: NON supportato in nessun fork. Issue [#41](https://github.com/Ghostkeeper/Blender3mfFormat/issues/41) closed Won't Fix. Per paint Bambu ↔ vertex colors: solo `shusain/3mf-import-and-color-split` (separato).

## Quirks

### Tiny exports con `scale_length=0.001` ([#89](https://github.com/Ghostkeeper/Blender3mfFormat/issues/89))

Con `scene.unit_settings.scale_length = 0.001` ("Millimeters" preset) il prodotto effettivo diventa `1 * 0.001 * 1000 = 1` → un cubo Blender di edge 10 esporta come 10mm correttamente. **MA** se l'utente aspetta `scale_length=1.0` con display mm, ottiene un 1000× shrink.

Workaround:
```python
sl = bpy.context.scene.unit_settings.scale_length
gs = 1.0 / sl if sl < 1.0 else 1.0   # yields 1000.0 per mm preset, 1.0 per default m
bpy.ops.export_mesh.threemf(filepath="/tmp/part.3mf", global_scale=gs, use_selection=True)
```

### Almost nothing opens the file ([#61](https://github.com/Ghostkeeper/Blender3mfFormat/issues/61))

Windows 3D Viewer, 3D Builder, Solidworks rifiutano. Cura e Blender accettano. **Bambu Studio e PrusaSlicer generalmente accettano**. Root cause non risolto — probabile thumbnail/rels strictness.

### Blender 4.5+ TypeError (Ghostkeeper master)

```
TypeError: Import3MF.__init__() takes 1 positional argument but 2 were given
```

Confermato in [#81](https://github.com/Ghostkeeper/Blender3mfFormat/issues/81)/[#84](https://github.com/Ghostkeeper/Blender3mfFormat/issues/84)/[#87](https://github.com/Ghostkeeper/Blender3mfFormat/issues/87)/[#92](https://github.com/Ghostkeeper/Blender3mfFormat/issues/92). Soluzione: usa **LeeGillie v2.2.1+** (Blender 4.5/5.x) o **eki-github/Blender3mfFormat-Fix** (4.4 only).

### `hide_render` ignored su export ([#91](https://github.com/Ghostkeeper/Blender3mfFormat/issues/91), open)

L'exporter include render-disabled objects. Pre-filtra manualmente:

```python
sel = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render]
for o in bpy.context.scene.objects: o.select_set(False)
for o in sel: o.select_set(True)
bpy.ops.export_mesh.threemf(filepath="/tmp/printable.3mf", use_selection=True)
```

### Import names = "3MF Object" (vecchie installazioni)

Issue [#76](https://github.com/Ghostkeeper/Blender3mfFormat/issues/76) — pre Feb 2025 tutti gli object importati ricevevano nome generico "3MF Object". Fix in master + LeeGillie. Verifica versione installata.

### Production Extension non scritto

Roundtrippare un Bambu Studio 3MF attraverso Blender **droppa** plate config, paint, e assemblies referenziate via `p:path`. Treat l'addon come **one-way mesh+material conduit** quando il source è Bambu Studio.

## Patterns

### 1. Standard mm export Bambu Studio (scene default scale_length=1.0)

```python
import bpy
bpy.ops.export_mesh.threemf(
    filepath="/tmp/part.3mf",
    use_selection=True,
    global_scale=1.0,
    use_mesh_modifiers=True,
    coordinate_precision=4,
)
```

### 2. Auto-compensate per scene unit setting

```python
sl = bpy.context.scene.unit_settings.scale_length
gs = 1.0 / sl if sl < 1.0 else 1.0
bpy.ops.export_mesh.threemf(filepath="/tmp/part.3mf", global_scale=gs, use_selection=True)
```

### 3. Batch export tutti i mesh, modifier applicati, alta precisione

```python
import bpy
for o in bpy.context.scene.objects: o.select_set(False)
for o in [obj for obj in bpy.data.objects if obj.type == 'MESH']:
    o.select_set(True)
bpy.ops.export_mesh.threemf(
    filepath="/tmp/all_meshes.3mf",
    use_selection=True,
    coordinate_precision=6,
)
```

### 4. Group multi-object via Parent Empty (UN file, oggetti raggruppati)

```python
import bpy
empty = bpy.data.objects.new("Assembly", None)
bpy.context.collection.objects.link(empty)
for mesh in target_meshes:
    mesh.parent = empty
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_mesh.threemf(filepath="/tmp/assy.3mf", use_selection=True)
```

> **Nota**: questo NON crea plates separate in Bambu Studio. Crea un assembly grouping. Per plates multipli serve fare manualmente in Bambu Studio, o emettere file 3MF separati.

### 5. Filter out hide_render objects (workaround #91)

```python
sel = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render]
for o in bpy.context.scene.objects: o.select_set(False)
for o in sel: o.select_set(True)
bpy.ops.export_mesh.threemf(filepath="/tmp/printable.3mf", use_selection=True)
```

### 6. Import sanity check (load back, verify count + bbox)

```python
before = set(bpy.data.objects.keys())
bpy.ops.import_mesh.threemf(filepath="/tmp/part.3mf", global_scale=1.0)
new_objs = [bpy.data.objects[n] for n in bpy.data.objects.keys() - before]
assert new_objs, "no objects imported"
for o in new_objs:
    if o.type != 'MESH': continue
    dx = max(v.co.x for v in o.data.vertices) - min(v.co.x for v in o.data.vertices)
    print(o.name, "bbox-x in scene units:", dx)
```

### 7. Try/except wrapper

```python
try:
    r = bpy.ops.import_mesh.threemf(filepath=path)
    if 'CANCELLED' in r:
        raise RuntimeError("3MF unreadable")
except RuntimeError as e:
    print(f"3MF import failed: {e}")
```

## Comparison: threemf-io (Ghostkeeper) vs LeeGillie fork

| Aspect | Ghostkeeper v1.0.2 | LeeGillie v2.2.1+ |
|---|---|---|
| Blender range | 2.80–4.4 (rotto su 4.5+) | 4.2.0+ (testato 5.0) |
| 3MF Core spec | 1.2.3 | 1.4.0 |
| Operator API | `import_mesh.threemf` + `export_mesh.threemf` | **identico** (stesso bl_idname + params) |
| Triangle Sets v1.3.0 | no | yes (organizzazionale only) |
| Manifest | legacy `bl_info` | `blender_manifest.toml` |
| License | GPLv2+ | GPL-3.0 |
| Maintenance attiva | minimale (last 2025-02) | attiva (2026-02) |
| Paint / support paint | no | no |
| Production Extension write | no | no |

**Recommendation**:
- Blender ≤ 4.4 → entrambi vanno. Preferisci LeeGillie per spec freshness.
- Blender 4.5/5.x → **obbligatorio LeeGillie 2.2.1+** (Ghostkeeper rotto).
- Stesso codice MCP funziona per entrambi (operator API identica).

## Cross-reference

- [bambu_3mf_export] — workflow completo handoff Blender → Bambu Studio + bug noti
- [import_export] — STL parameters
- [blender_addons_recommended] — install order + decisione fork
- FIELD_NOTES [2026-04-13] — caveat scale_length su `wm.stl_export` (analogo)

## Source

- Ghostkeeper: [github.com/Ghostkeeper/Blender3mfFormat](https://github.com/Ghostkeeper/Blender3mfFormat)
- LeeGillie: [github.com/LeeGillie/Blender3mfFormat](https://github.com/LeeGillie/Blender3mfFormat)
- Extensions Platform: [extensions.blender.org/add-ons/threemf-io](https://extensions.blender.org/add-ons/threemf-io/)
- Source operators: [`import_3mf.py`](https://raw.githubusercontent.com/Ghostkeeper/Blender3mfFormat/master/io_mesh_3mf/import_3mf.py), [`export_3mf.py`](https://raw.githubusercontent.com/Ghostkeeper/Blender3mfFormat/master/io_mesh_3mf/export_3mf.py)
- 3MF Core spec: [github.com/3MFConsortium/spec_core](https://github.com/3MFConsortium/spec_core)
- 3MF Production spec: [github.com/3MFConsortium/spec_production](https://github.com/3MFConsortium/spec_production)
