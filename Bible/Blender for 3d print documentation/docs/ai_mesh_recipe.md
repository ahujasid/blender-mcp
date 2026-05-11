# AI Mesh Recipe — Da GLB/OBJ Generato da AI a STL Pronto per Bambu Studio

Pipeline completa per mesh provenienti da generatori AI (TripoSG, Hunyuan3D, TripoSR, InstantMesh).
Obiettivo finale: STL manifold, scala corretta, profilo Bambu Studio consigliato.

**Scope**: tutto ciò che avviene in Blender via MCP fino all'export STL.
**Non incluso**: post-processing fisico, calibrazione hardware.

---

## Profilo di Rischio per Sorgente AI

| Generatore | Formato output | Non-manifold | Scala | Surface noise | Poly count tipico |
|---|---|---|---|---|---|
| TripoSG | GLB | Probabile | Unit cube (0–1 BU) | Moderato | 5k–200k (--faces) |
| Hunyuan3D 2.0 | GLB / OBJ | Non garantito | Unit cube (0–1 BU) | Moderato-alto | 50k–300k |
| TripoSR / MeshLRM | GLB | Alta probabilità + floating artifacts | Normalizzato | Alto (NeRF) | 20k–100k |
| Generic AI (altri) | GLB / OBJ / STL | Assumere sempre sì | Arbitraria | Variabile | Qualsiasi |

**Assunzione di partenza**: ogni mesh AI è non-manifold, in scala sbagliata, e non stampabile senza intervento.

---

## Pipeline — Struttura a Chiamate MCP

Ogni blocco `CALL N` è una chiamata indipendente a `execute_blender_code`. Ogni chiamata stampa lo stato finale perché la successiva possa usarlo.

---

### CALL 1 — Pulizia scena e Import

```python
import bpy, addon_utils

# Pulisci scena
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for mesh in bpy.data.meshes:
    bpy.data.meshes.remove(mesh)

# Imposta unità: 1 BU = 1 mm
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001
scene.unit_settings.length_unit = 'MILLIMETERS'

# Import — scegliere in base al formato
INPUT_FILE = "C:/input/model.glb"  # <- sostituire con path reale

ext = INPUT_FILE.lower().split('.')[-1]
if ext == 'glb' or ext == 'gltf':
    bpy.ops.import_scene.gltf(filepath=INPUT_FILE)
elif ext == 'obj':
    bpy.ops.wm.obj_import(filepath=INPUT_FILE)
elif ext == 'stl':
    bpy.ops.wm.stl_import(filepath=INPUT_FILE, global_scale=1.0, use_scene_unit=False)
elif ext == 'ply':
    bpy.ops.wm.ply_import(filepath=INPUT_FILE)
else:
    print(f"ERRORE: formato '{ext}' non supportato")

# Report stato post-import
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
print(f"Oggetti MESH importati: {len(objs)}")
for o in objs:
    print(f"  '{o.name}': {len(o.data.vertices)} verts, {len(o.data.polygons)} faces")
    print(f"    Dimensioni raw: X={o.dimensions.x*1000:.3f}mm Y={o.dimensions.y*1000:.3f}mm Z={o.dimensions.z*1000:.3f}mm")
```

**Leggi l'output**: conta oggetti, guarda le dimensioni raw. Se ci sono molti oggetti piccoli → CALL 2 gestisce il cleanup.

---

### CALL 2 — Multi-object: tieni solo il mesh principale

```python
import bpy

objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']

if len(objs) == 0:
    print("ERRORE: nessun oggetto mesh in scena")
elif len(objs) == 1:
    print(f"Un solo oggetto: '{objs[0].name}' — nessuna azione necessaria")
    bpy.context.view_layer.objects.active = objs[0]
    objs[0].select_set(True)
else:
    # Identifica il mesh principale per volume del bounding box
    def bbox_volume(obj):
        d = obj.dimensions
        return d.x * d.y * d.z

    main = max(objs, key=bbox_volume)
    small = [o for o in objs if o != main]

    # Rimuovi oggetti piccoli (floating debris, armature converted, ecc.)
    threshold_ratio = 0.01  # rimuove oggetti < 1% del volume del principale
    main_vol = bbox_volume(main)
    removed = []
    for o in small:
        if bbox_volume(o) < main_vol * threshold_ratio:
            bpy.data.objects.remove(o, do_unlink=True)
            removed.append(o.name)

    # Se restano più oggetti oltre il principale: join
    remaining = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if len(remaining) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for o in remaining:
            o.select_set(True)
        bpy.context.view_layer.objects.active = main
        bpy.ops.object.join()
        print(f"Join eseguito: {len(remaining)} oggetti → 1")
    
    print(f"Rimossi come debris: {removed}")
    main_obj = bpy.context.active_object
    print(f"Oggetto principale: '{main_obj.name}'")
    print(f"  Verts: {len(main_obj.data.vertices)}, Faces: {len(main_obj.data.polygons)}")
```

---

### CALL 3 — Rilevamento e correzione scala

```python
import bpy
import math

obj = bpy.context.active_object
if obj is None or obj.type != 'MESH':
    # Prova a trovare il mesh principale
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            obj = o
            bpy.context.view_layer.objects.active = o
            break

bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
dims_bu = obj.dimensions
dims_mm = tuple(d * 1000 for d in dims_bu)
max_dim_mm = max(dims_mm)

print(f"Dimensioni: X={dims_mm[0]:.2f}mm  Y={dims_mm[1]:.2f}mm  Z={dims_mm[2]:.2f}mm")
print(f"Dimensione massima: {max_dim_mm:.3f}mm")

# Diagnosi scala
if max_dim_mm < 0.5:
    status = "TROPPO_PICCOLO (probabile unità in metri o normalizzato)"
elif max_dim_mm > 1500:
    status = "TROPPO_GRANDE (probabile importazione in mm con scala 1000x)"
elif max_dim_mm < 5:
    status = "SOSPETTO_PICCOLO — verificare unità di misura"
else:
    status = "SCALA_PLAUSIBILE"

print(f"Diagnosi scala: {status}")

# AZIONE: riscalare a target noto
# Modifica TARGET_MM con la dimensione reale attesa dell'oggetto (asse più lungo)
TARGET_MM = None  # <- impostare es. 150.0 per una testa di moro di 15cm

if TARGET_MM is not None and max_dim_mm > 0:
    scale_factor = (TARGET_MM * 0.001) / max(dims_bu)
    obj.scale *= scale_factor
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    new_dims = tuple(d * 1000 for d in obj.dimensions)
    print(f"Riscalato a target {TARGET_MM}mm → nuove dim: {new_dims[0]:.1f} x {new_dims[1]:.1f} x {new_dims[2]:.1f}mm")
elif status == "TROPPO_PICCOLO":
    # Stima: porta il max dim a ~100mm come punto di partenza
    scale_factor = (0.1) / max(dims_bu)
    obj.scale *= scale_factor
    bpy.ops.object.transform_apply(scale=True)
    print("Riscalato a ~100mm (stima). Confermare con dimensioni reali attese.")
elif status == "TROPPO_GRANDE":
    scale_factor = (0.256) / max(dims_bu)  # fit nel volume A1
    obj.scale *= scale_factor
    bpy.ops.object.transform_apply(scale=True)
    print("Riscalato per entrare nel volume A1 256mm.")
else:
    bpy.ops.object.transform_apply(scale=True)
    print("Scala accettata, transform_apply eseguito.")

# Porta base a Z=0
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
obj.location.z = obj.dimensions.z / 2
bpy.ops.object.transform_apply(location=True)
print(f"Base portata a Z=0. Pronto per assessment.")
```

---

### CALL 4 — Assessment qualità mesh

```python
import bpy, bmesh, addon_utils

obj = bpy.context.active_object
addon_utils.enable("object_print3d_utils", default_set=True)

# --- Metriche bmesh ---
bm = bmesh.new()
bm.from_mesh(obj.data)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

n_verts = len(bm.verts)
n_faces = len(bm.faces)
non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
boundary_edges = [e for e in bm.edges if e.is_boundary]
doubles = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=0.0001)
bm.free()

dims_mm = tuple(d * 1000 for d in obj.dimensions)
max_dim = max(dims_mm)
fits_a1 = all(d <= 256 for d in dims_mm)

print("=== MESH ASSESSMENT REPORT ===")
print(f"Oggetto: '{obj.name}'")
print(f"Dimensioni: {dims_mm[0]:.1f} x {dims_mm[1]:.1f} x {dims_mm[2]:.1f} mm")
print(f"Entra nel volume A1 (256³): {'SI' if fits_a1 else 'NO — ridimensionare o splittare'}")
print(f"Vertici: {n_verts:,}  |  Facce: {n_faces:,}")
print(f"Facce target FDM (50k-200k): {'OK' if 50000 <= n_faces <= 200000 else 'AZIONE NECESSARIA — vedi CALL 5'}")
print(f"Non-manifold edges: {len(non_manifold_edges)}")
print(f"Boundary edges (buchi): {len(boundary_edges)}")
print(f"Vertici duplicati: {len(doubles['targetmap'])}")

# Gravità
if len(non_manifold_edges) == 0 and len(boundary_edges) == 0:
    print("MANIFOLD STATUS: ✓ mesh chiusa e manifold")
elif len(non_manifold_edges) < 50:
    print("MANIFOLD STATUS: difetti minori → repair CALL 5")
else:
    print("MANIFOLD STATUS: difetti gravi → repair CALL 5 (può richiedere voxel remesh)")

# 3D Print Toolbox overhang check
bpy.context.view_layer.objects.active = obj
bpy.context.scene.print_3d.thickness_min = 0.00045  # 0.45mm in BU
bpy.ops.mesh.print3d_check_overhang()
print("3D Print Toolbox overhang check eseguito (controllare N-panel per risultati visivi)")
```

---

### CALL 5 — Repair e Decimazione

```python
import bpy, bmesh, addon_utils

obj = bpy.context.active_object
addon_utils.enable("object_print3d_utils", default_set=True)
n_faces_before = len(obj.data.polygons)

# --- FASE 1: Decimazione preventiva se mesh troppo densa ---
TARGET_FACES = 150000
if n_faces_before > TARGET_FACES:
    ratio = TARGET_FACES / n_faces_before
    mod = obj.modifiers.new(name="Decimate_AI", type='DECIMATE')
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier="Decimate_AI")
    print(f"Decimazione: {n_faces_before:,} → {len(obj.data.polygons):,} facce (ratio {ratio:.3f})")
else:
    print(f"Decimazione non necessaria: {n_faces_before:,} facce")

# --- FASE 2: Repair sequenza standard ---
# 2a. 3D Print Toolbox auto-repair
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.mesh.print3d_clean_non_manifold()

# 2b. Edit mode ops
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0001)       # merge vertici sovrapposti
bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)   # rimuovi facce zero-area
bpy.ops.mesh.normals_make_consistent(inside=False)   # normali verso l'esterno
bpy.ops.mesh.fill_holes(sides=0)                     # chiudi buchi residui
bpy.ops.object.mode_set(mode='OBJECT')

# --- FASE 3: Verifica post-repair ---
bm = bmesh.new()
bm.from_mesh(obj.data)
bm.edges.ensure_lookup_table()
non_manifold_after = [e for e in bm.edges if not e.is_manifold]
boundary_after = [e for e in bm.edges if e.is_boundary]
bm.free()

print(f"Post-repair: {len(obj.data.polygons):,} facce")
print(f"Non-manifold residui: {len(non_manifold_after)}")
print(f"Boundary residui: {len(boundary_after)}")

if len(non_manifold_after) > 0 or len(boundary_after) > 0:
    print("ATTENZIONE: difetti residui. Valutare Voxel Remesh (CALL 5b).")
else:
    print("REPAIR COMPLETATO: mesh manifold e watertight.")
```

---

### CALL 5b — Voxel Remesh (solo se repair standard non risolve)

Usare quando dopo CALL 5 restano ancora non-manifold, o quando la mesh è così caotica che il repair classico non converge.

```python
import bpy

obj = bpy.context.active_object
dims_mm = max(d * 1000 for d in obj.dimensions)

# Voxel size: feature_size/2 — per mesh organiche FDM ~0.3–0.5mm è adeguato
# Valore più piccolo = più dettaglio, più pesante
VOXEL_SIZE_MM = 0.4
voxel_bu = VOXEL_SIZE_MM * 0.001

mod = obj.modifiers.new(name="Remesh_Voxel", type='REMESH')
mod.mode = 'VOXEL'
mod.voxel_size = voxel_bu
mod.adaptivity = 0.0
mod.use_smooth_shade = False
bpy.ops.object.modifier_apply(modifier="Remesh_Voxel")

import bmesh
bm = bmesh.new()
bm.from_mesh(obj.data)
non_manifold = [e for e in bm.edges if not e.is_manifold]
bm.free()

print(f"Voxel Remesh completato: voxel={VOXEL_SIZE_MM}mm")
print(f"Facce risultanti: {len(obj.data.polygons):,}")
print(f"Non-manifold residui: {len(non_manifold)} (atteso: 0)")

if len(non_manifold) > 0:
    print("ANOMALIA: Voxel Remesh dovrebbe produrre mesh manifold. Verificare voxel_size.")
else:
    print("Mesh manifold garantita da Voxel Remesh.")

# NOTA: Voxel remesh modifica la topologia. Dettagli fini sotto voxel_size vanno persi.
# Aumentare voxel_size per mesh semplici, ridurre per alto dettaglio.
```

---

### CALL 6 — Smoothing superficie (se necessario per mesh AI)

Solo se la mesh ha surface noise visibile come bumps che non dovrebbero esserci.

```python
import bpy

obj = bpy.context.active_object

# Laplacian Smooth leggero: preserva forma complessiva, riduce HF noise
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.object.mode_set(mode='OBJECT')

# Usa il modifier per controllo preciso
mod = obj.modifiers.new(name="LaplacianSmooth_AI", type='LAPLACIANSMOOTH')
mod.iterations = 5        # leggero — aumentare con cautela
mod.lambda_factor = 1.0
mod.lambda_border = 0.0
mod.use_volume_preserve = True   # impedisce shrinkage
mod.use_normalized = True
bpy.ops.object.modifier_apply(modifier="LaplacianSmooth_AI")

print(f"Laplacian Smooth applicato: 5 iterazioni, volume preserved")
print("Verificare visivamente che i dettagli intenzionali siano preservati.")

# Per noise più aggressivo: usare Remesh VOXEL (CALL 5b) invece di smooth.
# Smooth non rimuove noise strutturale — solo ammorbidisce. Se i bump
# sono profondi (>0.5mm), servono più iterazioni o voxel remesh.
```

---

### CALL 7 — Wall thickness check e analisi finale

```python
import bpy, addon_utils

obj = bpy.context.active_object
addon_utils.enable("object_print3d_utils", default_set=True)

# Imposta soglia spessore minimo per nozzle 0.4mm: 0.45mm = 1 perimetro
bpy.context.scene.print_3d.thickness_min = 0.00045  # in BU (0.45mm)

bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bpy.ops.mesh.print3d_check_all()

# Informazioni dimensionali finali
dims_mm = tuple(d * 1000 for d in obj.dimensions)
fits = all(d <= 256 for d in dims_mm)

print("=== ANALISI FINALE PRE-EXPORT ===")
print(f"Dimensioni: {dims_mm[0]:.1f} x {dims_mm[1]:.1f} x {dims_mm[2]:.1f} mm")
print(f"Entra nel volume A1: {'SI' if fits else 'NO — splittare o ridimensionare'}")
print(f"Facce: {len(obj.data.polygons):,}")
print("Controllare il pannello N in Blender per thin wall highlights (aree rosse).")
print("Aree rosse = pareti < 0.45mm → slicer le ometterà silenziosamente.")
```

---

### CALL 8 — Export STL

```python
import bpy

OUTPUT_PATH = "C:/output/model_ready.stl"  # <- aggiornare path

obj = bpy.context.active_object
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)

# Assicura transform applicato
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Base a Z=0
import mathutils
min_z = min((obj.matrix_world @ mathutils.Vector(c)).z for c in obj.bound_box)
if abs(min_z) > 0.0001:
    obj.location.z -= min_z
    bpy.ops.object.transform_apply(location=True)

bpy.ops.wm.stl_export(
    filepath=OUTPUT_PATH,
    export_selected_objects=True,
    global_scale=1000.0,    # BU → mm: necessario con scale_length=0.001
    use_scene_unit=False,   # NON usare con scale_length=0.001 (vedi FIELD_NOTES)
    ascii_format=False,
    apply_modifiers=True
)

# Verifica file
import os
if os.path.exists(OUTPUT_PATH):
    size_mb = os.path.getsize(OUTPUT_PATH) / (1024*1024)
    print(f"STL esportato: {OUTPUT_PATH}")
    print(f"Dimensione file: {size_mb:.2f} MB")
    if size_mb > 50:
        print("AVVISO: file > 50MB. Considerare ulteriore decimazione.")
    else:
        print("Pronto per Bambu Studio.")
else:
    print(f"ERRORE: file non trovato a {OUTPUT_PATH}")
```

---

## Profilo Bambu Studio Consigliato per Mesh AI

| Caratteristica modello | Profilo | Parametri chiave |
|---|---|---|
| Figurina organica / testa / busto | Profilo 1 — Estetico | 0.12mm, 4 pareti, Tree support, seam=Back |
| Oggetto geometrico / meccanico | Profilo 2 — Funzionale | 0.20mm, 4 pareti, Grid 40% |
| Miniatura < 50mm | Profilo 4 — Miniatura | 0.08–0.12mm, velocità 80mm/s |
| Oggetto grande > 150mm | Profilo 5 — Grande | 0.28mm, Lightning 10%, brim 10mm |

Vedi `Bambu Wiki documentation/docs/slicing_profiles.md` per i parametri completi se la root del progetto è `Bible/`.

---

## Sculpt Mode: Brush Reference per AI Mesh Cleanup

Quando il Voxel Remesh + repair standard non bastano (superfici irregolari, gap, dettagli AI da affinare), il Sculpt Mode è il livello successivo. Non scriptabile via MCP — richiede intervento manuale. Questa tabella copre i brush più utili per AI mesh prep.

| Brush | Shortcut / Nome | Comportamento | Quando usarlo su mesh AI |
|---|---|---|---|
| **Smooth** | Shift (mentre usi qualsiasi brush) | Leviga la geometria verso la media locale | Primo brush da usare sempre — 50% del cleanup. Elimina noise, artefatti di remesh, superfici irregolari da AI generation |
| **Elastic Grab / Elastic Wrap** | Cerca "Elastic" in brush list | Muove la geometria come se la "tirasse" con elasticità | Correggere proporzioni, riposizionare elementi (naso, orecchie, arti) senza distruggere dettagli |
| **Inflate / Deflate** | Tasto I | Espande (inflate) o contrae (deflate) la superficie verso l'esterno/interno delle normali | Chiudere gap tra parti separate, riempire buchi, gonfiare forme appiattite da AI. Fondamentale per fusione neck-hair gap |
| **Blob** | Cerca "Blob" in brush list | Aggiunge volume sferico nell'area del brush | Chiudere buchi grandi, aggiungere volume su occhi/nasi piatti, ricostruire forme arrotondate |
| **Crease Sharp** | Cerca "Crease" in brush list | Aggiunge una piega/solco netto nella geometria | Ridefinire bordi di vestiti, sopracciglia, dettagli di design che il remesh ha ammorbidito |
| **Clay Strips** | Cerca "Clay Strips" in brush list | Aggiunge strati di "argilla" con bordi definiti | Costruire volume su aree piatte, definire muscolatura, aggiungere elementi mancanti |

**Workflow tipo per AI character cleanup:**
1. `merge_by_distance` in Edit Mode (elimina loose vertices)
2. Voxel Remesh a voxel_size appropriato
3. **Smooth** (Shift) su tutta la superficie → 2-3 passate
4. **Elastic Grab** per correggere proporzioni evidenti
5. **Inflate** su gap → Voxel Remesh → **Smooth** per unificare
6. **Blob** per ricostruire dettagli persi (occhi, narici)
7. **Crease Sharp** per ridefinire bordi puliti

**Attivare Smooth su qualsiasi brush:** tenere premuto **Shift** durante la scultura — tutti i brush passano automaticamente alla modalità smooth senza cambiare brush.

---

## Strategie Avanzate per Problemi AI Specifici

### Modello con dettagli insufficienti / parti fuse

Quando un modello AI genera la figura completa con scarso dettaglio (mani, viso, vestiti fusi insieme), la soluzione è **generare le parti separatamente** e assemblarle in Blender:

1. Generare testa, corpo, vestiti come richieste AI separate (qualità nettamente migliore per parte rispetto all'intero)
2. Importare tutte le parti in Blender
3. Posizionare e scalare le parti per farle combaciare
4. Join (Ctrl+J) per unirle in un unico oggetto
5. Voxel Remesh per fonderle in un solido
6. Sculpt Smooth per levigare le giunture

### Double-sided mesh da buco nella geometria

Sintomo: la Face Orientation overlay mostra rosso diffuso all'interno del modello (non solo sulla superficie). Causa: un buco nella mesh ha permesso al remesh di generare geometria interna.

Fix:
1. Sculpt Mode → **Inflate** brush sul buco → chiudere completamente l'apertura
2. Voxel Remesh → il remesh elimina il layer interno (ora non più raggiungibile dall'esterno)
3. Verificare con Face Orientation: solo blu (esterno) visibile = corretto

### Bone heat weighting failure (Rigify)

Se `Ctrl+P → With Automatic Weights` fallisce con "Bone heat weighting: failed to find solution":

```python
import bpy

# Il threshold di default 0.0001 è troppo basso per mesh AI dense
# Aumentare a un valore che rimuova vertici sovrapposti ma non danneggi il dettaglio
obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.001)  # 0.001 BU ≈ 1µm con scale_length=0.001
bpy.ops.object.mode_set(mode='OBJECT')
print(f"Merge completato. Verts: {len(obj.data.vertices)}")
# Riprovare ora Ctrl+P → With Automatic Weights
```

Causa: i vertici sovrapposti nell'area delle giunture (spalle, collo) impediscono all'algoritmo di bone heat di calcolare i pesi. Il merge con threshold leggermente più alto elimina i duplicati critici senza togliere dettaglio visibile.

---

## Troubleshooting Rapido

| Sintomo | Causa probabile | Fix |
|---|---|---|
| `gltf2_import` non trovato | Add-on GLTF non attivato | `addon_utils.enable("io_scene_gltf2")` in CALL 1 |
| Oggetti multipli dopo import | Materiali separati nel GLB | CALL 2 fa il join automatico |
| Dimensioni assurde (0.001mm o 5000mm) | Scala normalizzata AI | CALL 3 con TARGET_MM corretto |
| Repair non converge | Mesh troppo caotica | Usare CALL 5b Voxel Remesh |
| Thin wall ovunque | Mesh è una shell sottile | Aggiungere Solidify dopo repair (vedi `hollowing_and_lightening.md`) |
| STL corretto ma volume zero in Bambu | `use_scene_unit=True` con scale_length=0.001 | Usare `global_scale=1000.0, use_scene_unit=False` (vedi FIELD_NOTES) |

---

## Relazioni con altri doc KB

- `source_mesh_characteristics.md` → comprensione teorica dei difetti AI per classe di modello
- `mesh_quality_assessment.md` → dettagli 3D Print Toolbox e metriche bmesh
- `mesh_repair.md` → approfondimento su ogni operazione di repair
- `scale_detection.md` → logica diagnosi scala con soglie euristiche
- `decimation_remesh.md` → parametri quantitativi per Decimate e Voxel Remesh
- `Bambu Wiki documentation/docs/slicing_profiles.md` → profili Bambu Studio completi per tipo di oggetto
- `orientation_strategy.md` → ottimizzazione orientamento per minimizzare supporti
