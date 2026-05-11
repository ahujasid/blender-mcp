# Blender Add-on Recommendati per il Workflow Print-Prep

Lista curata di add-on Blender da installare, ordinata per ROI sul workflow STL-AI → FDM-Bambu-A1. Tutti **GPL**, tutti via **Extensions Platform** (extensions.blender.org) con installazione 1-click — abilita prima `Edit > Preferences > Extensions > Get Extensions Online`.

Tutti gli add-on raccomandati espongono `bpy.ops.*` callable da MCP via `execute_blender_code`. Add-on pure-UI sono esclusi (non utili in ambiente headless agente).

## Tier 1 — Da installare subito

### 1. **3D Print Toolbox** (`object_print3d_utils`) — CRITICO

**Status**: built-in in Blender 4.x, bundled. Reference completa in [blender_3d_print_toolbox].

**Valore**: 7 check operator (manifold, intersect, thick, sharp, overhang, distort, degenerate), 2 clean operator, transform helper, scale/align utility, hollow VDB. È il fondamento di tutta la pipeline cleanup.

### 2. **3MF Import/Export** (`threemf-io`) — CRITICO per Bambu

**Reference completa in [addon_threemf_io]**.

**⚠ Bug critico Blender 4.5+**: Ghostkeeper master è **rotto** (TypeError). Su Blender 4.5/5.x usa **LeeGillie fork v2.2.1+** ([github.com/LeeGillie/Blender3mfFormat](https://github.com/LeeGillie/Blender3mfFormat)). Operator API identica.

**MCP API base**:
```python
bpy.ops.import_mesh.threemf(filepath="/path/in.3mf")
bpy.ops.export_mesh.threemf(
    filepath="/path/out.3mf",
    use_selection=True,
    use_mesh_modifiers=True,
    global_scale=1.0,           # se scale_length=1.0 default
    coordinate_precision=4,
)
```

**Valore**: handoff Bambu Studio formale. 3MF preserva multi-object, units esplicite, materiale → basematerials displaycolor (NO texture).

**Limiti noti**: Blender emette solo Core 3MF; Bambu's Production Extension (modifier mesh, negative parts, AMS filament IDs, multi-plate config) **NON è scrivibile da Blender** — vanno aggiunti in Bambu Studio post-import. Per multi-plate: emetti file 3MF separati per plate (vedi [bambu_3mf_export]).

### 3. **Booltron** (`booltron`, mrachinskiy) — HIGH

**Reference completa in [addon_booltron]**.

**URL**: [extensions.blender.org/add-ons/booltron](https://extensions.blender.org/add-ons/booltron/), [GitHub](https://github.com/mrachinskiy/booltron) (v3.3.2 Feb 2026)
**License**: GPL
**MCP API**:
```python
bpy.ops.booltron.destructive_difference()
bpy.ops.booltron.destructive_union()
bpy.ops.booltron.destructive_intersect()
bpy.ops.booltron.nondestructive_difference()
# ...
```

**Valore**: usa il nuovo **solver `MANIFOLD`** di Blender 4.5+ (più veloce e robusto di FAST/EXACT per geometrie print). Auto-check non-manifold post-op. Complementare a Bool Tool: Booltron per **batch multi-object boolean**, Bool Tool per **interactive single cut**.

Critical per il workflow: quando applichi Boolean su mesh AI (es. per cut piattaforma a Z=0, splitting modello, mounting holes), Booltron riduce drasticamente i fallimenti silenziosi (vedi [boolean_troubleshooting] §Failure modes).

### 4. **Bool Tool** (`bool_tool`, nickberckley) — HIGH

**Reference completa in [addon_bool_tool]**.

**URL**: [extensions.blender.org/add-ons/bool-tool](https://extensions.blender.org/add-ons/bool-tool/), [GitHub](https://github.com/nickberckley/bool_tool)
**License**: GPL
**MCP API**:
```python
bpy.ops.object.boolean_brush_difference()
bpy.ops.object.boolean_brush_union()
bpy.ops.object.boolean_brush_intersect()
bpy.ops.object.boolean_auto_difference()  # wrapper modifier-based
# ...
```

**Valore**: wrappa la "modifier dance" (add modifier → set op → apply → delete cutter) in operator atomici. Ideale per cut singoli scriptati: mounting holes, registration pin holes (vedi [bisect_splitting]), tolerance reliefs.

### 5. **LoopTools** (`looptools`) — MEDIUM-HIGH

**Reference completa in [addon_looptools]**.

**URL**: [extensions.blender.org/add-ons/looptools](https://extensions.blender.org/add-ons/looptools/) (non più bundled da Blender 4.2)
**License**: GPL
**MCP API**:
```python
bpy.ops.mesh.looptools_bridge()    # bridge tra due edge loop
bpy.ops.mesh.looptools_circle()    # rende un loop perfetta circle
bpy.ops.mesh.looptools_flatten()   # appiattisce loop selezionato
bpy.ops.mesh.looptools_gstretch()  # snap a curva grease pencil (raro per print)
bpy.ops.mesh.looptools_relax()     # smoothing minimale loop
bpy.ops.mesh.looptools_space()     # ridistribuisce vertices uniformemente
```

**Valore**: **bridge_edge_loops** è esattamente quello che serve per riparare buchi grandi lasciati da Decimate aggressivo su mesh AI. **circle** e **flatten** utili per re-bottom-flat dopo orientation, prima dell'export.

Esempio uso:
```python
# Dopo aver eliminato n facce e lasciato 2 edge loop aperti su side opposti
bpy.ops.mesh.select_all(action='DESELECT')
# select i due loop manualmente o programmaticamente
bpy.ops.mesh.looptools_bridge(loft=False, segments=1, twist=0)
```

### 6. **F2** (`f2`) — MEDIUM

**Reference completa in [addon_f2]**.

**⚠ Quirk killer per MCP**: `autograb=True` di default stalla in headless mode. Set `bpy.context.preferences.addons['mesh_f2'].preferences.autograb = False` PRIMA della call, e invoca con `bpy.ops.mesh.f2('INVOKE_DEFAULT')`.

**URL**: [extensions.blender.org/add-ons/f2](https://extensions.blender.org/add-ons/f2/)
**License**: GPL
**MCP API**: `bpy.ops.mesh.f2()` — quad fill da singolo vertex o edge

**Valore**: cheap, scriptable hole patching per gap 3-5 vertici tipici di Meshy/TripoSG output dopo Decimate. Più semplice di `fill_holes` per cases puntuali, perché interpola il quad shape dai loop adiacenti.

### 7. **Mesh Repair Tools** (`mesh-repair-tools`) — MEDIUM

**Reference completa in [addon_mesh_repair_tools]**.

**URL**: [extensions.blender.org/add-ons/mesh-repair-tools](https://extensions.blender.org/add-ons/mesh-repair-tools/)
**License**: GPL
**MCP API**: operator-based (fill_holes_advanced, flatten_surface, recalc_normals_smart, etc.)

**Valore**: ops mirate complementari a 3D Print Toolbox. Fill-Holes implementation **più robusta** del built-in per boundaries irregolari (tipico AI mesh dopo Decimate).

## Tier 2 — Utility primitive

### 8. **Extra Mesh Objects** (`extra-mesh-objects`) — LOW-MEDIUM

**Reference completa in [addon_extra_mesh_objects]**.

**URL**: [extensions.blender.org/add-ons/extra-mesh-objects](https://extensions.blender.org/add-ons/extra-mesh-objects/)
**License**: GPL
**MCP API**:
```python
bpy.ops.mesh.primitive_round_cube_add(radius=2.0, divisions=3)  # bevelled box
bpy.ops.mesh.primitive_xyz_function_surface(...)
# 30+ primitive parametriche
```

**Valore**: round cube e parametric primitives sono **cutter Boolean perfetti** per chamfered mounting holes, bevelled slots con tolerance FDM. Più cleane che modellare da scratch un cylinder + bevel modifier.

## NON raccomandati (con motivo)

| Add-on | Motivo skip |
|---|---|
| **MeasureIt / MeasureIt-ARCH** | Pure overlay viewport. Operator esistono ma **creano draw objects**, non ritornano misure. Per leggere dimensioni programmaticamente usa `obj.dimensions` direttamente. |
| **Quad Remesher (Exoside, $139.90)** | Eccellente per topologia organica MA **ridondante** con Voxel Remesh + QuadriFlow built-in per print-prep. Necessario solo se l'utente fa anche sculpt/rigging. |
| **Quadify (Pro/Ultra)** | Tri-to-quad è concern di rigging, non di print. Slicer triangola comunque. |
| **MeshLint** (rking) | Last update ~2018, no Blender 4.x maintenance. **3D Print Toolbox copre già** tutti i check non-manifold/tri/ngon. Abbandonato. |
| **NS Toolkit Mesh Cleanup Pro / Smart Mesh Cleaner Pro** | UI-overlay heavy. Operator esistono ma overlap 100% con 3D Print Toolbox + Mesh Repair Tools. |
| **CAD Sketcher / CAD Transform** | Wrong scope (parametric sketching). Out of scope per cleanup AI mesh esistente. |
| **Tweaker-3** (ChristophSchranz) | Non è un addon Blender, è pkg Python standalone. **GPL-3.0 virale** — wrapparlo costringerebbe `blender-mcp` a GPL-3.0. Rimplementa l'algoritmo se serve (~80 righe NumPy). Vedi [orientation_strategy] §Tweaker-3. |

## Built-in / bundled potenzialmente sottoutilizzati

In Blender 4.2+ quasi tutto è migrato a Extensions Platform. Verifica che l'utente abbia abilitato (Edit > Preferences > Get Extensions, online ON):

- **3D Print Toolbox** — già installato (utente conferma).
- **STL / OBJ / PLY / glTF I/O** — bundled core. Operator moderni: `bpy.ops.wm.stl_import`/`stl_export`, `wm.obj_import`/`obj_export`, `wm.ply_import`/`ply_export`. Il vecchio `bpy.ops.import_mesh.stl` (addon legacy) è deprecato — preferisci `wm.stl_export` (vedi `addon.py` wrapper logic).
- **Built-in remesher**: `bpy.ops.object.voxel_remesh()` (sul `obj.data.remesh_voxel_size`) e `bpy.ops.object.quadriflow_remesh(target_faces=...)`. Spesso ignorati a favore del modifier — chiamare diretti è più veloce per pipeline scriptate (vedi [decimation_remesh] §QuadriFlow).
- **Solver Manifold per Boolean** (Blender 4.5+): nuovo solver del modifier Boolean. Set via `mod.solver = 'MANIFOLD'` invece di 'EXACT' o 'FAST'. Più veloce e robusto per geometry print. Booltron usa questo solver internamente.

## Decisione 3MF — quale fork installare

Tre fork live in 2026:

| Fork | Blender support | Bambu Studio interop | Status |
|---|---|---|---|
| **`threemf-io`** (Ghostkeeper lineage, Extensions Platform ufficiale) | 4.2–4.5 | A1 template, paint/seam/support roundtrip con Orca + Bambu | **Raccomandato primary** — Jan 2026 update |
| **LeeGillie/Blender3mfFormat** | 5.0+ | Stesso operator surface, v1.4.0 spec, "minimal support" community fork | Solo se sei su Blender 5.x |
| **eki-github/Blender3mfFormat-Fix** | 4.4 niche | bambulab-file-specific fixes | Skip — superseded da threemf-io extension |

**Verdetto**: install `threemf-io` dall'Extensions Platform. Quando upgrade a Blender 5.x, swap a LeeGillie's zip. Entrambi espongono **identico** `bpy.ops.import_mesh.threemf` / `bpy.ops.export_mesh.threemf` → MCP code resta portabile.

Evita: `shusain/3mf-import-and-color-split`, `Korchy/blender_3mf` (scope narrower, no Bambu A1 templates, no maintenance attivo).

## Install order one-shot

1. Edit > Preferences > Extensions > **enable online access** (toggle in alto destra).
2. Cerca e installa via Extensions Platform (1-click each):
   - `print3d-toolbox` (3D Print Toolbox)
   - `threemf-io`
   - `bool-tool`
   - `booltron`
   - `looptools`
   - `f2`
   - `mesh-repair-tools`
   - `extra-mesh-objects` (opzionale)
3. Verifica caricamento:
```python
import bpy
required = ('print3d_toolbox', 'threemf_io', 'bool_tool', 'booltron',
            'looptools', 'mesh_f2', 'mesh_repair_tools', 'add_mesh_extra_objects')
addons = bpy.context.preferences.addons.keys()
for name in required:
    print(f"{name}: {'OK' if name in addons else 'MISSING'}")
```

Nota: i nomi reali in `bpy.context.preferences.addons.keys()` possono differire lievemente dal module name del package — il check sopra è indicativo, verifica nel preferences panel.

## Conflitti & coesistenza

Nessuno dei 7 raccomandati confligge con gli altri o con `blender-mcp`. **Bool Tool + Booltron** sono **intenzionalmente complementari** (interactive single vs batch multi). 3D Print Toolbox + Mesh Repair Tools hanno overlap su fill_holes ma le implementazioni sono diverse — usa il più appropriato per il caso:
- `print3d_clean_non_manifold` → mesh con T-junction densi (ma T48565)
- `mesh_repair_tools` fill_holes → buchi grandi con boundary irregolare

## MCP wrapper consigliato

Per ogni operator add-on, considera di creare un wrapper nel server `blender-mcp` se il pattern si ripete frequentemente. Esempi che varrebbero un wrapper:

- `bpy.ops.export_mesh.threemf(...)` con i parametri fissi per Bambu A1 → tool MCP `export_3mf_bambu(object_name, filepath)`
- `bpy.ops.mesh.looptools_bridge(...)` con detection automatica dei due loop aperti → tool MCP `bridge_open_loops(object_name)`
- `bpy.ops.booltron.destructive_difference(...)` con sanitize_for_boolean pre-step → tool MCP `safe_boolean_difference(target, cutter)`

Per ora i playbook li usano via `execute_blender_code`. Se vediamo abuso ripetuto in field testing, promuovo a tool.

## Riferimenti

- [Extensions Platform — extensions.blender.org](https://extensions.blender.org/)
- [3MF Spec Core](https://github.com/3MFConsortium/spec_core)
- [3MF Spec Production Extension](https://github.com/3MFConsortium/spec_production)
- [bambu_3mf_export] — handoff details + bug Issue references
- [blender_3d_print_toolbox] — reference completa Toolbox
- [orientation_strategy] — perché Tweaker-3 NON wrappato
