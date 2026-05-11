# Blender → Bambu Studio handoff via 3MF

Workflow completo per esportare da Blender un file 3MF importabile in Bambu Studio. Copre i 3 addon disponibili, i bug noti, il trick Parent Empty per multi-plate, e le cose che si **perdono sempre** nel round-trip.

## Background: STL vs 3MF vs Bambu 3MF

| Axis | STL (binary) | Generic 3MF (Blender export) | Bambu Studio Project 3MF |
|---|---|---|---|
| Units | Implicite, slicer assume mm | Explicit `unit="millimeter"` (default) | Explicit mm + Bambu xy_size_compensation, plate dimensions |
| Multi-object | One mesh / file | N `<object>` + per-object transforms | Multi-object + multi-plate via 3MF **Production Extension** (object refs in separate XML) |
| Modifier / negative parts | ❌ | ❌ (Bambu `part_type` attribute dropped) | ✅ in `Metadata/model_settings.config`: normal_part / negative_part / modifier_part / support_blocker / support_enforcer |
| Profile / slicer metadata | ❌ | Optional `<metadata>` generica | ✅ `Metadata/project_settings.config`, `slice_info.config`, `plate_*.gcode`, AMS filament_ids per object |
| Round-trip lossless con Bambu | ❌ (no settings) | Solo geometria; colors e modifier attribs droppati (Issue #7775) | Lossless dentro Bambu; ma 3MF-into-3MF perde object/modifier settings (Issue #6976) |
| File size | Più grande (raw triangoli) | Piccolo (ZIP+XML, 3-10x più piccolo di STL) | Leggermente più grande del generico per config embedded |

**Important**: i 3MF emessi da Bambu Studio usano la **Production Extension** (refs multi-file per parsing parallelo) — questi 3MF **non aprono in PrusaSlicer/Cura** senza warning (Issue #3316). Per cross-slicer handoff, usa "Export → Generic 3MF" o STL.

## I 3 fork dell'addon 3MF — quale usare

| Fork | Blender | Status | Bambu support |
|---|---|---|---|
| **`threemf-io`** Extensions Platform (Ghostkeeper lineage) | 4.2–4.5 | **Update Jan 2026**, attivo | A1 template aggiunto, paint/seam/support roundtrip con Orca + Bambu |
| **LeeGillie/Blender3mfFormat** | 5.0+ | Community fork, "minimal support" | Stesso operator surface, v1.4.0 spec |
| **eki-github/Blender3mfFormat-Fix** | 4.4 niche | Stale | Bambulab-specific fixes, superseduto da threemf-io |
| `shusain/3mf-import-and-color-split` | varia | Stale | Skip |
| `Korchy/blender_3mf` | varia | Stale | Skip |

**Decisione**: install `threemf-io` dall'Extensions Platform (1-click). Se sei su Blender 5.x e threemf-io non c'è ancora aggiornato, swap a LeeGillie zip. Entrambi espongono identico `bpy.ops.import_mesh.threemf` / `bpy.ops.export_mesh.threemf` — il codice MCP resta portabile.

## Pre-export pipeline (DA FARE SEMPRE)

Bambu Studio fa assumptions che Blender non garantisce di default. Esegui questi step prima di ogni `export_mesh.threemf` o `wm.stl_export`:

```python
import bpy

obj = bpy.data.objects['<name>']
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

# 1. Apply transforms — slicer legge raw vertex coords
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 2. Origin to lowest-Z — Bambu posa l'oggetto con pivot sul piatto
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
# Translate so min_z = 0
import bmesh
bm = bmesh.new(); bm.from_mesh(obj.data)
min_z = min(v.co.z for v in bm.verts)
bm.free()
obj.location.z -= min_z

# 3. Recalc normals outward
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)

# 4. Triangulate (3MF spec wants triangles; addon triangulates implicitly but
#    explicit prevents non-planar quad artifacts)
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')

# 5. Object naming descrittivo — il name propaga a Bambu Studio Objects panel
obj.name = "MyPart_A1"
```

**Skip frequente che rovina l'import**: punto 1 (transform_apply). È la causa #1 di "il modello è enorme/piccolissimo/floating" in Bambu Studio.

## Export single-color / multi-object

```python
bpy.ops.export_mesh.threemf(
    filepath='/tmp/assembly.3mf',
    use_selection=True,           # solo selected, oppure False = scene intera
    use_mesh_modifiers=True,      # apply modifiers a export-time
    global_scale=1000.0,          # BU(m) → mm; o 1.0 se hai unit_settings scale_length=0.001
    coordinate_precision=4,       # decimali nei vertex coords XML
)
```

**Critico su `global_scale`**: dipende dal scene unit setting.
- `scale_length=1.0` (default Blender, 1 BU = 1m) → `global_scale=1000.0` per ottenere mm.
- `scale_length=0.001` (1 BU = 1mm) → `global_scale=1.0` (no scaling).

Vedi FIELD_NOTES [2026-04-13] per il bug analogo su `wm.stl_export(use_scene_unit=...)`.

## Import in Bambu Studio

**Path consigliato**: `File → Import → Import 3MF` (NON `Open Project` — quello aspetta un Bambu Project 3MF, non un Generic 3MF).

Comportamento atteso:
- Tutti gli object atterrano sulla plate 1.
- Usa `Auto-Arrange` per layout iniziale.
- Object names da Blender appaiono nell'Objects panel.
- Material slots di Blender NON mappano a filament IDs Bambu — i colori vanno riassegnati post-import (Issue #7775).

Per usare una mesh Blender come **negative part** in Bambu Studio:
1. Importa il main object in Bambu Studio.
2. Right-click sul main → `Add Negative Part → Load…` → seleziona un secondo STL/3MF dalla cartella di lavoro.
3. Bambu **non legge** `part_type` da 3MF esterni — devi sempre dichiararlo nel UI di Bambu.

## Multi-plate da Blender — **NON è possibile direttamente**

**Correzione importante**: contrariamente a quanto comunemente affermato, `threemf-io` **NON** mappa Parent Empty a plate separate in Bambu Studio. Verificato leggendo il source di import_3mf.py / export_3mf.py (Ghostkeeper master + LeeGillie fork).

**Cosa fa davvero un Parent Empty in export**:
- Root objects (no parent) → `<build><item>` entries.
- Children objects → `<components>` con transform relativo al parent.
- Empty parent → diventa un parentless `<item>` senza mesh (raggruppamento logico).
- **Resta UN file 3MF con UN plate**. Bambu Studio importa tutti su plate 1.

**Perché non funziona il "trick"**: la plate config Bambu vive in `Metadata/model_settings.config` (proprietary Production Extension format). Nessun fork threemf-io scrive questo file. PR [#58](https://github.com/Ghostkeeper/Blender3mfFormat/pull/58) lo aggiungerebbe ma è unmerged dal 2022.

**Workaround per multi-plate**:

### Opzione A — Un file 3MF per plate (raccomandato)

```python
import bpy

def export_plate(plate_objects, filepath):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for name in plate_objects:
        bpy.data.objects[name].select_set(True)
    bpy.ops.export_mesh.threemf(
        filepath=filepath,
        use_selection=True,
        use_mesh_modifiers=True,
        global_scale=1.0,  # se scale_length=1.0 default
    )

export_plate(['part_a', 'part_b', 'part_c'], '/tmp/plate_1.3mf')
export_plate(['part_d'], '/tmp/plate_2.3mf')
```

Poi in Bambu Studio: New Project → Import 3MF plate_1.3mf → Add Plate → Import 3MF plate_2.3mf.

### Opzione B — Tutto su 1 plate, riarrangia in Bambu Studio

```python
# Export tutti gli oggetti su un file
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_mesh.threemf(
    filepath='/tmp/all.3mf',
    use_selection=True,
    use_mesh_modifiers=True,
)
```

In Bambu Studio: Import 3MF → tutti su plate 1 → manualmente Move to Plate per quelli che vanno su plate diverse.

### Opzione C — Grouping via Parent Empty (un solo plate)

Utile NON per separare plates, ma per **raggruppare logicamente** oggetti nella Objects panel di Bambu Studio:

```python
import bpy

empty = bpy.data.objects.new("Assembly", None)
bpy.context.scene.collection.objects.link(empty)
for name in ('part_a', 'part_b', 'part_c'):
    bpy.data.objects[name].parent = empty

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_mesh.threemf(filepath='/tmp/assy.3mf', use_selection=True)
```

In Bambu Studio: tutti gli object appaiono insieme sulla plate 1, ma raggruppati visualmente sotto "Assembly" nella Objects panel. **Non sono plate separate**.

## Cosa si perde all'import in Bambu Studio

Inevitabilmente:

1. **Material colors** — Blender material slot ≠ Bambu filament_id. Le mesh arrivano grigie, vanno colorate post (Issue #7775).
2. **Per-object slicer settings** — non c'è modo di embeddarli nel Core 3MF emesso da Blender. Even Bambu's own Project 3MF round-trips lose these when imported into another Bambu project (Issue #6976).
3. **Modifier / negative part flags** — vanno applicati nel Bambu UI dopo l'import.
4. **AMS filament IDs** — solo se sourcing da un Bambu Project 3MF, NON da Generic 3MF.
5. **Paint (seam, support, color)** — `threemf-io` v Jan 2026 supporta paint roundtrip per OrcaSlicer e Bambu (NUOVO); su Blender 5.x con LeeGillie fork il supporto è meno maturo.

**Cosa SOPRAVVIVE sempre**:
- Geometria (vertices, faces, normali se recalcolate)
- Object transforms se applicate via `transform_apply`
- Object names
- Parent-child gerarchia (per multi-plate trick)
- Units (millimeter esplicito)

## Known bugs e workaround

### Issue [BambuStudio#7775](https://github.com/bambulab/BambuStudio/issues/7775) — Color discarded on external 3MF import
**Sintomo**: Bambu Studio scarta info materiale/colore da 3MF esterni.
**Workaround**: esporta ogni color region come object/3MF separato, assembla in Bambu via `Add Part`, poi paint-assign filaments. Oppure split-mesh-by-material in Blender prima di 3MF export.

### Issue [BambuStudio#6976](https://github.com/bambulab/BambuStudio/issues/6976) — Bambu→Bambu 3MF loses object settings
**Sintomo**: Importare un Bambu Project 3MF in un altro Bambu project perde object-level e modifier-level settings (geometria, paint, height-range modifier sopravvivono; per-object slicer settings no).
**Workaround**: mantieni un master project e usa `File → Import → Geometry Only` deliberatamente; ri-applica object settings, oppure apri direttamente con `File → Open Project`.

### Issue [BambuStudio#3316](https://github.com/bambulab/BambuStudio/issues/3316) — Bambu 3MF non apre in PrusaSlicer/Cura
**Sintomo**: 3MF emessi da Bambu Studio falliscono in PrusaSlicer ("Invalid 3MF format") e Cura ("No models in file") a causa delle Production Extension component refs.
**Workaround**: in Bambu Studio, `Export → Export as STL` o `Export Generic 3MF` (se esposto) prima di handoff a non-Bambu slicer.

## OrcaSlicer come alternativa

OrcaSlicer è fork di PrusaSlicer-via-Bambu Studio per Bambu A1 (community). Vantaggi rispetto a Bambu Studio:
- Stesso formato 3MF (bit-compatible)
- **Migliore handling 3MF esterni** (meno warning)
- Profile portability migliore tra slicer

Per multi-plate, support paint, e profile management è spesso preferito da utenti A1 power. Il `threemf-io` Jan 2026 supporta entrambi.

## Comparazione con `wm.stl_export`

Quando STL basta:
- Single object, no plate management
- Pipeline che richiede max compatibilità (cross-slicer)
- File piccolo necessario (raro — 3MF è più piccolo)

Quando 3MF è meglio:
- Multi-object scenes
- Multi-plate setup
- Paint info da preservare (con `threemf-io` Jan 2026+)
- Material slot → filament mapping (parziale, vedi sopra)

## Cross-reference

- [import_export] — STL parameters details, FIELD_NOTES bug su `global_scale`
- [bambu_studio_workflow] — full Bambu Studio user flow
- [bambu_studio_settings] — per-object settings da configurare post-import
- [blender_addons_recommended] §3MF Decision — quale fork installare
- FIELD_NOTES [2026-04-13] — bug `use_scene_unit=True` con `scale_length=0.001`

## Riferimenti

- [3MF Spec Core](https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md)
- [3MF Spec Production Extension](https://github.com/3MFConsortium/spec_production/blob/master/3MF%20Production%20Extension.md)
- [Ghostkeeper Blender3mfFormat (original)](https://github.com/Ghostkeeper/Blender3mfFormat)
- [LeeGillie Blender3mfFormat (5.x fork)](https://github.com/LeeGillie/Blender3mfFormat)
- [threemf-io Extensions Platform](https://extensions.blender.org/add-ons/threemf-io/)
- [Bambu Wiki — 3MF Compatibility](https://wiki.bambulab.com/en/software/bambu-studio/3mf-compatibility)
- [Bambu Wiki — Modifier](https://wiki.bambulab.com/en/software/bambu-studio/modifier)
- [Bambu Wiki — Subtract a Part](https://wiki.bambulab.com/en/software/bambu-studio/subtract-a-part)
