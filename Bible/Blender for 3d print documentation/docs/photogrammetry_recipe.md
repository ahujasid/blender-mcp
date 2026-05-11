# Photogrammetry Recipe — Pipeline Mesh Fotogrammetria → STL FDM

Pipeline step-by-step per portare un mesh da fotogrammetria (Meshroom, RealityCapture, Polycam, MetaShape)
a STL stampabile su Bambu A1 via Blender MCP. Ogni CALL è un blocco `execute_blender_code` autonomo —
nessuna variabile persiste tra le chiamate.

**Differenze critiche rispetto all'AI recipe:**
- Face count iniziale: 1M–10M+ → decimazione massiva **prima** di qualsiasi repair
- Background noise: la fotogrammetria cattura l'ambiente — pulizia separazione geometria obbligatoria
- Scale: può essere in metri reali (GPS/LiDAR) oppure arbitraria — diagnosi diversa dall'AI
- Surface noise: più profondo rispetto all'AI (artefatti di illuminazione, texture proiezione) → smoothing aggressivo
- Buchi: più frequenti (zone senza coverage fotografica) → fill_holes priorità alta

---

## Formati input supportati

| Software | Formato tipico | Note |
|---|---|---|
| Meshroom | OBJ + MTL | Scala in unità arbitrarie, asse Y-up |
| RealityCapture | OBJ, PLY | Con GPS: scala in metri; senza: arbitraria |
| Polycam | OBJ, GLB, USDZ | iPhone LiDAR: scala reale in metri |
| MetaShape | OBJ, PLY, FBX | Scala dipende da coordinate di controllo |
| Capturing Reality (legacy) | OBJ | Come RealityCapture |

---

## CALL 1 — Setup scena + Import

Pulisce la scena e importa il file. Gestisce OBJ e PLY (i due formati fotogrammetria più comuni).
GLB in uscita da Polycam → usare la AI recipe (stesso codice import GLB).

```python
import bpy, os

# ── CONFIGURAZIONE ─────────────────────────────────────────────────────────────
INPUT_FILE = "/path/to/mesh_fotogrammetria.obj"   # Cambia con path reale (.obj o .ply)
# ──────────────────────────────────────────────────────────────────────────────

# Setup unità: 1 BU = 1 mm
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001
scene.unit_settings.length_unit = 'MILLIMETERS'

# Pulizia scena
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(mesh)

# Import per formato
ext = os.path.splitext(INPUT_FILE)[1].lower()
if ext == '.obj':
    bpy.ops.wm.obj_import(
        filepath=INPUT_FILE,
        forward_axis='NEGATIVE_Z',
        up_axis='Y'
    )
elif ext == '.ply':
    # Blender 4.x usa wm.ply_import; fallback su import_mesh.ply
    try:
        bpy.ops.wm.ply_import(filepath=INPUT_FILE)
    except AttributeError:
        bpy.ops.import_mesh.ply(filepath=INPUT_FILE)
elif ext in ('.glb', '.gltf'):
    # Polycam in formato GLB → stessa procedura AI recipe
    bpy.ops.import_scene.gltf(filepath=INPUT_FILE)
else:
    print(f"ERRORE: formato {ext} non supportato. Usa OBJ, PLY o GLB.")
    raise ValueError(f"Formato non supportato: {ext}")

# Inventario scena post-import
mesh_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
print(f"Oggetti mesh importati: {len(mesh_objects)}")
for o in mesh_objects:
    dims_mm = [d * 1000 for d in o.dimensions]
    poly_count = len(o.data.polygons)
    print(f"  [{o.name}] {poly_count:,} facce — "
          f"X={dims_mm[0]:.1f}mm Y={dims_mm[1]:.1f}mm Z={dims_mm[2]:.1f}mm")

print("CALL 1 completata — Import OK")
```

---

## CALL 2 — Separazione geometria + Rimozione background

**Passo critico e specifico della fotogrammetria.** La scena catturata include spesso il piano di
appoggio, pareti, oggetti circostanti. Separare le isole disconnesse e mantenere solo la geometria
principale riduce il face count del 30–80% prima ancora di toccare il decimatore.

Se il mesh è già un unico oggetto pulito, questa call produce solo un inventario.

```python
import bpy
import bmesh

# Soglia volume minimo oggetto "principale" vs artefatto
# Aggiusta in base alle dimensioni attese del soggetto
ARTIFACT_VOLUME_RATIO = 0.01   # oggetti < 1% del volume del più grande → rimossi
MIN_FACE_COUNT = 100            # oggetti con meno di N facce → rimossi come debris

# Join tutti gli oggetti mesh in uno solo (fotogrammetria spesso li importa separati)
mesh_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']

if len(mesh_objects) > 1:
    bpy.ops.object.select_all(action='DESELECT')
    for o in mesh_objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0]
    bpy.ops.object.join()
    print(f"Join di {len(mesh_objects)} oggetti in uno")

obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = obj
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)

# Separa per isole disconnesse
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.mesh.separate(type='LOOSE')

# Inventario isole
islands = [o for o in bpy.context.scene.objects if o.type == 'MESH']
islands.sort(key=lambda o: len(o.data.polygons), reverse=True)

print(f"Isole trovate: {len(islands)}")
for i, o in enumerate(islands[:10]):  # mostra prime 10
    pct = 100 * len(o.data.polygons) / max(1, len(islands[0].data.polygons))
    dims_mm = [d * 1000 for d in o.dimensions]
    print(f"  [{i}] {o.name}: {len(o.data.polygons):,} facce ({pct:.1f}% del principale) "
          f"— {dims_mm[0]:.1f}×{dims_mm[1]:.1f}×{dims_mm[2]:.1f}mm")

# Rimozione artefatti piccoli
main_face_count = len(islands[0].data.polygons)
removed = []
for o in islands[1:]:
    ratio = len(o.data.polygons) / max(1, main_face_count)
    if ratio < ARTIFACT_VOLUME_RATIO or len(o.data.polygons) < MIN_FACE_COUNT:
        bpy.data.objects.remove(o, do_unlink=True)
        removed.append(o.name)

print(f"Rimossi {len(removed)} artefatti: {removed[:5]}{'...' if len(removed)>5 else ''}")

# Ri-join le isole rimaste (possono essere parti del soggetto fotografate separate)
remaining = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if len(remaining) > 1:
    bpy.ops.object.select_all(action='DESELECT')
    for o in remaining:
        o.select_set(True)
    bpy.context.view_layer.objects.active = remaining[0]
    bpy.ops.object.join()
    print(f"Re-join di {len(remaining)} isole significative")

final_obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
print(f"Geometria finale: {len(final_obj.data.polygons):,} facce")
print("CALL 2 completata — Background rimosso")
```

---

## CALL 3 — Diagnosi scala + Rescale

La fotogrammetria ha tre origini di scala frequenti:

| Origine | Sintomo | Causa |
|---|---|---|
| GPS/LiDAR (Polycam, RC con ground control) | obj.dimensions → valori in 0.x–10x BU | 1 BU = 1m → oggetto di 0.3m appare 0.3 BU |
| Calibrazione da marker (MetaShape) | scala variabile, spesso corretta | Marker in metri o mm secondo setup |
| Senza riferimenti (Meshroom senza GPS) | 0.001–2.0 BU tipico | Unità arbitrarie, normalizzate sull'AABB |

Con `scale_length=0.001` (1 BU = 1mm), un oggetto da fotogrammetria GPS di 200mm appare come
`0.2 BU` → serve rescale ×1000 per portarlo a dimensioni corrette in mm.

```python
import bpy

# ── CONFIGURAZIONE ─────────────────────────────────────────────────────────────
# Imposta uno dei seguenti:
# TARGET_MM: dimensione nota del soggetto sull'asse più lungo (es. 200.0 per statuetta 20cm)
# Se None → solo diagnosi, nessun rescale
TARGET_MM = None    # es: 200.0

# SCALE_SOURCE: 'gps' | 'marker' | 'unknown'
# 'gps' → input scala in metri reali, conversione automatica mm
# 'marker' o 'unknown' → usa TARGET_MM per rescale manuale
SCALE_SOURCE = 'unknown'
# ──────────────────────────────────────────────────────────────────────────────

obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = obj

# Centra origine sul bounding box per misurazioni accurate
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

dims_bu = obj.dimensions
max_dim_bu = max(dims_bu)
dims_mm_current = [d * 1000 for d in dims_bu]  # con scale_length=0.001

print("=== DIAGNOSI SCALA ===")
print(f"Dimensioni attuali (BU): X={dims_bu.x:.4f} Y={dims_bu.y:.4f} Z={dims_bu.z:.4f}")
print(f"Dimensioni correnti (mm): X={dims_mm_current[0]:.1f} Y={dims_mm_current[1]:.1f} Z={dims_mm_current[2]:.1f}")
print(f"Asse più lungo: {max_dim_bu:.4f} BU = {max_dim_bu*1000:.1f}mm")

# Diagnosi automatica
if max_dim_bu < 0.05:
    diag = "TROPPO_PICCOLO — probabile GPS in metri (0.3m oggetto appare 0.0003 BU?)"
elif max_dim_bu < 1.0:
    diag = "PICCOLO — potrebbe essere GPS (1BU=1m) oppure oggetto piccolo correttamente scalato"
elif max_dim_bu > 500:
    diag = "TROPPO_GRANDE — probabile unità in µm o scala non applicata"
else:
    diag = "RANGE PLAUSIBILE — verifica con TARGET_MM se conosci la dimensione reale"
print(f"Diagnosi: {diag}")

# Rescale
scale_factor = None

if SCALE_SOURCE == 'gps' and max_dim_bu > 0:
    # GPS: 1 BU = 1m → oggetto in metri → moltiplicare ×1 (rimane in BU)
    # ma con scale_length=0.001 la scena interpreta BU come mm → quindi l'oggetto
    # GPS da 0.2m (= 200mm) appare come 0.2 BU invece di 200 BU
    # Correzione: scala ×1000 (porta da scala metrica a scala mm in BU)
    scale_factor = 1000.0
    print(f"GPS mode: applico ×1000 (da scala metrica a mm)")

elif TARGET_MM is not None and max_dim_bu > 0:
    # Rescale manuale a dimensione nota
    target_bu = TARGET_MM * 0.001  # mm → BU (con scale_length=0.001)
    scale_factor = target_bu / max_dim_bu
    print(f"Rescale manuale: {max_dim_bu*1000:.1f}mm → {TARGET_MM}mm (fattore {scale_factor:.4f})")

if scale_factor is not None:
    obj.scale *= scale_factor
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    dims_after = [d * 1000 for d in obj.dimensions]
    print(f"Dimensioni post-rescale: X={dims_after[0]:.1f}mm Y={dims_after[1]:.1f}mm Z={dims_after[2]:.1f}mm")

    # Verifica build volume A1
    max_after = max(obj.dimensions) * 1000
    if max_after > 256:
        print(f"AVVISO: dimensione max {max_after:.1f}mm supera volume A1 (256mm)")
        print("Valuta ridimensionamento o suddivisione del modello")
    else:
        print(f"OK: modello entra nel volume A1 (256×256×256mm)")
else:
    print("Nessun rescale applicato. Imposta TARGET_MM o SCALE_SOURCE='gps' se necessario.")

# Porta la base a Z=0
obj.location.z = obj.dimensions.z / 2
print("CALL 3 completata — Scala verificata")
```

---

## CALL 4 — Decimazione massiva iniziale

**Priorità assoluta nella fotogrammetria.** Prima di qualsiasi repair (che sarebbe proibitivamente lento
su 5M+ facce), ridurre aggressivamente il poly count. Il target di questa fase è ~200k–500k facce —
non ancora il target FDM finale, ma abbastanza basso per le operazioni successive.

**Strategia decisionale:**

| Face count iniziale | Strategia |
|---|---|
| < 300k | Decimate COLLAPSE ratio moderato (0.5–0.8) |
| 300k–2M | Decimate COLLAPSE aggressivo (0.1–0.3) |
| 2M–10M | Voxel Remesh prima (voxel_size = 1–3mm), poi Decimate |
| > 10M | Voxel Remesh con voxel_size più grande (2–5mm) |

```python
import bpy

# ── CONFIGURAZIONE ─────────────────────────────────────────────────────────────
# Target face count dopo questa call (fase intermedia, non ancora target FDM finale)
INTERMEDIATE_TARGET = 300000  # 300k — buon compromesso per repair successivi
# ──────────────────────────────────────────────────────────────────────────────

obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = obj
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)

n_faces = len(obj.data.polygons)
print(f"Face count iniziale: {n_faces:,}")

if n_faces <= INTERMEDIATE_TARGET:
    print(f"Face count già ≤ {INTERMEDIATE_TARGET:,} — decimazione non necessaria")
else:
    ratio_needed = INTERMEDIATE_TARGET / n_faces

    if n_faces > 2_000_000:
        # Per mesh ultra-densi (>2M): Voxel Remesh è più robusto del Decimate
        # e risolve anche i non-manifold in un colpo solo
        # voxel_size: feature_min_size / 2 — per fotogrammetria tipicamente 0.5–2mm
        # Con scale_length=0.001: voxel_size in BU = voxel_mm * 0.001
        VOXEL_MM = 1.0   # 1mm per oggetti di dimensioni medie (20–200mm)
        # Scala voxel in base alle dimensioni dell'oggetto
        max_dim_mm = max(obj.dimensions) * 1000
        if max_dim_mm > 200:
            VOXEL_MM = 2.0
        elif max_dim_mm < 50:
            VOXEL_MM = 0.5

        voxel_bu = VOXEL_MM * 0.001
        print(f"Mesh ultra-denso ({n_faces:,} facce) → Voxel Remesh a {VOXEL_MM}mm ({voxel_bu:.5f} BU)")

        mod = obj.modifiers.new(name="VoxelRemesh_Initial", type='REMESH')
        mod.mode = 'VOXEL'
        mod.voxel_size = voxel_bu
        mod.use_smooth_shade = False
        bpy.ops.object.modifier_apply(modifier="VoxelRemesh_Initial")

        n_after_remesh = len(obj.data.polygons)
        print(f"Post-Voxel Remesh: {n_after_remesh:,} facce")

        # Se ancora sopra target, decimazione aggiuntiva
        if n_after_remesh > INTERMEDIATE_TARGET:
            ratio2 = INTERMEDIATE_TARGET / n_after_remesh
            mod2 = obj.modifiers.new(name="Decimate_Post", type='DECIMATE')
            mod2.decimate_type = 'COLLAPSE'
            mod2.ratio = max(0.05, ratio2)
            bpy.ops.object.modifier_apply(modifier="Decimate_Post")

    else:
        # Decimate COLLAPSE per mesh 300k–2M
        print(f"Decimate COLLAPSE: ratio {ratio_needed:.3f} ({n_faces:,} → ~{INTERMEDIATE_TARGET:,})")
        mod = obj.modifiers.new(name="Decimate_Photo", type='DECIMATE')
        mod.decimate_type = 'COLLAPSE'
        mod.ratio = max(0.02, ratio_needed)  # min 2% per evitare collapse totale
        mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier="Decimate_Photo")

n_final = len(obj.data.polygons)
print(f"Face count post-decimazione: {n_final:,}")
print(f"Riduzione: {(1 - n_final/n_faces)*100:.1f}%")
print("CALL 4 completata — Decimazione massiva OK")
```

---

## CALL 5 — Repair mesh

Con il face count ridotto, il repair diventa fattibile. La fotogrammetria ha pattern di difetti diversi
dall'AI: **buchi** molto più frequenti (coverage gaps), normali spesso coerenti ma talvolta invertite
in patch locali, vertici duplicati lungo le giunture dei tile fotogrammetrici.

```python
import bpy
import addon_utils

obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = obj
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)

print(f"Pre-repair: {len(obj.data.polygons):,} facce")

# Attiva 3D Print Toolbox
addon_utils.enable("object_print3d_utils", default_set=True)

# --- Repair via Edit Mode ---
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')

# 1. Remove doubles: vertici sovrapposti tipici dei tile fotogrammetrici
bpy.ops.mesh.remove_doubles(threshold=0.00005)  # 0.05µm in BU — più conservativo dell'AI

# 2. Dissolve geometria degenere (zero-area faces, edge length=0)
bpy.ops.mesh.dissolve_degenerate(threshold=0.00001)

# 3. Normali consistenti
bpy.ops.mesh.normals_make_consistent(inside=False)

# 4. Fill holes — fotogrammetria: molti buchi da coverage gaps
# sides=0 → riempie buchi di qualsiasi dimensione (inclusi grandi coverage gaps)
bpy.ops.mesh.fill_holes(sides=0)

# 5. Seleziona e elimina facce a zero area (possono sopravvivere a dissolve)
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_face_by_sides(number=3, type='LESS')  # facce con <3 lati = degeneri
bpy.ops.mesh.delete(type='FACE')

bpy.ops.object.mode_set(mode='OBJECT')

# --- 3D Print Toolbox clean ---
try:
    bpy.ops.mesh.print3d_clean_non_manifold()
    print("3D Print Toolbox: clean_non_manifold applicato")
except Exception as e:
    print(f"3D Print Toolbox non disponibile: {e}")

# --- Verifica post-repair ---
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_non_manifold()
bpy.ops.object.mode_set(mode='OBJECT')

import bmesh
bm = bmesh.new()
bm.from_mesh(obj.data)
bm.edges.ensure_lookup_table()
non_manifold_count = sum(1 for e in bm.edges if not e.is_manifold)
boundary_count = sum(1 for e in bm.edges if e.is_boundary)
bm.free()

print(f"Post-repair: {len(obj.data.polygons):,} facce")
print(f"  Edge non-manifold: {non_manifold_count}")
print(f"  Edge boundary (buchi residui): {boundary_count}")

if non_manifold_count == 0 and boundary_count == 0:
    print("✓ Mesh manifold — repair completato")
elif non_manifold_count < 50:
    print("⚠ Pochi edge non-manifold residui — accettabile per FDM (slicer li gestisce)")
else:
    print(f"✗ {non_manifold_count} edge non-manifold — considera Voxel Remesh in CALL seguente")

print("CALL 5 completata — Repair OK")
```

---

## CALL 6 — Surface Smoothing

La fotogrammetria produce surface noise più profondo dell'AI: artefatti di illuminazione, shadow baking
sulla mesh, aliasing da risoluzione fotografica. Il smoothing deve essere **più aggressivo** rispetto
all'AI recipe, ma deve preservare gli spigoli strutturali (bordi di oggetti, profili definiti).

**Strategia smoothing fotogrammetria:**
1. LaplacianSmooth moderato (iterations 3–7) per eliminare alta frequenza
2. Se la mesh è da remesh voxel: aggiungere Subdivision leggera + Smooth per recuperare dettaglio
3. Verificare spessore pareti post-smoothing

```python
import bpy

# ── CONFIGURAZIONE ─────────────────────────────────────────────────────────────
# Intensità smoothing: 'light' | 'medium' | 'heavy'
# light: superfici quasi pulite (solo tile join artifacts)
# medium: noise da fotogrammetria standard (uso tipico)
# heavy: forte aliasing, shadow baking, superficie molto ruvida
SMOOTHING_LEVEL = 'medium'
# ──────────────────────────────────────────────────────────────────────────────

SMOOTH_PARAMS = {
    'light':  {'lambda_factor': 0.5, 'iterations': 3, 'use_volume_preserve': True},
    'medium': {'lambda_factor': 1.0, 'iterations': 5, 'use_volume_preserve': True},
    'heavy':  {'lambda_factor': 1.5, 'iterations': 8, 'use_volume_preserve': False},
}

params = SMOOTH_PARAMS[SMOOTHING_LEVEL]

obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = obj
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)

n_before = len(obj.data.polygons)
print(f"Pre-smooth: {n_before:,} facce — level={SMOOTHING_LEVEL}")

# LaplacianSmooth (migliore dell'ordinario Smooth per preservare volume)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.object.mode_set(mode='OBJECT')

mod_smooth = obj.modifiers.new(name="LaplSmooth_Photo", type='LAPLACIANSMOOTH')
mod_smooth.lambda_factor = params['lambda_factor']
mod_smooth.lambda_border = params['lambda_factor'] * 0.5   # meno aggressivo sui bordi
mod_smooth.iterations = params['iterations']
mod_smooth.use_volume_preserve = params['use_volume_preserve']
mod_smooth.use_normalized = True
bpy.ops.object.modifier_apply(modifier="LaplSmooth_Photo")

# Decimazione finale a target FDM
# Fotogrammetria post-smoothing: 300k → 50k–150k per slicer
TARGET_FDM_FACES = 150000  # per oggetti standard; ridurre a 50k per grandi pezzi
n_current = len(obj.data.polygons)
if n_current > TARGET_FDM_FACES:
    ratio = TARGET_FDM_FACES / n_current
    print(f"Decimazione finale: {n_current:,} → {TARGET_FDM_FACES:,} (ratio {ratio:.3f})")
    mod_dec = obj.modifiers.new(name="Decimate_Final", type='DECIMATE')
    mod_dec.decimate_type = 'COLLAPSE'
    mod_dec.ratio = ratio
    mod_dec.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier="Decimate_Final")

n_final = len(obj.data.polygons)
print(f"Post-smooth+decimazione: {n_final:,} facce")

# Normalize normali dopo smoothing
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

print("CALL 6 completata — Smoothing OK")
```

---

## CALL 7 — Quality Assessment + Orientamento

Verifica finale prima dell'export: spessore pareti, dimensioni, non-manifold residui.
La verifica orientamento è critica per fotogrammetria perché il modello può avere l'asse verticale
errato a seconda dell'orientamento della camera durante la sessione.

```python
import bpy
import addon_utils
import bmesh

obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = obj
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)

print("=== QUALITY ASSESSMENT PRE-EXPORT ===")

# --- Dimensioni ---
dims_mm = [d * 1000 for d in obj.dimensions]
print(f"\n[DIMENSIONI]")
print(f"  X={dims_mm[0]:.1f}mm  Y={dims_mm[1]:.1f}mm  Z={dims_mm[2]:.1f}mm")
print(f"  Volume A1: 256×256×256mm")
exceeds = [ax for ax, val in zip('XYZ', dims_mm) if val > 256]
if exceeds:
    print(f"  ✗ FUORI VOLUME sugli assi: {exceeds}")
else:
    print(f"  ✓ Dimensioni compatibili con A1")

# --- Manifold ---
bm = bmesh.new()
bm.from_mesh(obj.data)
bm.edges.ensure_lookup_table()
non_manifold = [e for e in bm.edges if not e.is_manifold]
boundary = [e for e in bm.edges if e.is_boundary]
bm.free()

print(f"\n[MANIFOLD]")
print(f"  Edge non-manifold: {len(non_manifold)}")
print(f"  Edge boundary (buchi): {len(boundary)}")
if len(non_manifold) == 0:
    print("  ✓ Mesh manifold")
elif len(non_manifold) < 100:
    print("  ⚠ Pochi edge non-manifold — il slicer Bambu gestisce questi casi")
else:
    print("  ✗ Mesh non-manifold — considera Voxel Remesh come fallback")

# --- Spessore pareti ---
addon_utils.enable("object_print3d_utils", default_set=True)
try:
    bpy.context.scene.print_3d.thickness_min = 0.0004  # 0.4mm in scene units? No: BU
    # Con scale_length=0.001: 1.2mm = 0.0012 BU
    bpy.context.scene.print_3d.thickness_min = 0.0012  # min 3 walls a 0.4mm nozzle
    result = bpy.ops.mesh.print3d_check_thick()
    print(f"\n[SPESSORE PARETI] Check eseguito (risultati in Info Editor Blender)")
except Exception as e:
    print(f"\n[SPESSORE PARETI] Non disponibile: {e}")

# --- Face count finale ---
n_faces = len(obj.data.polygons)
print(f"\n[MESH STATS]")
print(f"  Facce: {n_faces:,}")
if n_faces < 10000:
    print("  ⚠ Face count molto basso — dettaglio potrebbe essere perso")
elif n_faces > 500000:
    print("  ⚠ Face count alto — lo slicer potrebbe essere lento. Considera ulteriore decimazione.")
else:
    print("  ✓ Face count ottimale per FDM")

# --- Posizione base ---
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
z_base = obj.location.z - obj.dimensions.z / 2
print(f"\n[POSIZIONE]")
print(f"  Base modello a Z={z_base*1000:.2f}mm")
if abs(z_base) > 0.0001:
    print("  Correzione Z: porto la base a Z=0")
    obj.location.z = obj.dimensions.z / 2
print("  ✓ Base a Z=0")

# --- Transform Apply ---
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
print("\n✓ transform_apply completato")
print("CALL 7 completata — QA OK")
```

---

## CALL 8 — Export STL

Identico all'AI recipe. Il parametro critico è `global_scale=1000.0` con `use_scene_unit=False`.

```python
import bpy

# ── CONFIGURAZIONE ─────────────────────────────────────────────────────────────
OUTPUT_PATH = "/path/to/output_photogrammetry.stl"
# ──────────────────────────────────────────────────────────────────────────────

obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = obj
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)

dims_mm = [d * 1000 for d in obj.dimensions]
print(f"Export: {obj.name}")
print(f"Dimensioni finali: X={dims_mm[0]:.1f}mm Y={dims_mm[1]:.1f}mm Z={dims_mm[2]:.1f}mm")
print(f"Facce: {len(obj.data.polygons):,}")

bpy.ops.wm.stl_export(
    filepath=OUTPUT_PATH,
    export_selected_objects=True,
    global_scale=1000.0,      # BU → mm: NECESSARIO con scale_length=0.001
    use_scene_unit=False,     # NON True — con scale_length=0.001 produce valori ×0.001
    ascii_format=False,       # Binary: più compatto, sempre preferito
    apply_modifiers=True      # Bake eventuali modifier non applicati
)

import os
if os.path.exists(OUTPUT_PATH):
    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"✓ STL esportato: {OUTPUT_PATH}")
    print(f"  Dimensione file: {size_mb:.1f} MB")
else:
    print(f"✗ ERRORE: file non trovato a {OUTPUT_PATH}")

print("CALL 8 completata — Export OK")
```

---

## Fallback: Voxel Remesh totale

Se dopo CALL 5 il mesh è ancora non-manifold con >500 edge problematici, applicare Voxel Remesh
prima di smoothing. Risolve tutti i problemi manifold in un colpo a costo di perdita di dettaglio.

```python
import bpy

# ── CONFIGURAZIONE ─────────────────────────────────────────────────────────────
# voxel_size in mm → scegliere in base alla feature minima desiderata
# Tipico fotogrammetria: 0.5mm per oggetti piccoli, 1.5mm per grandi
VOXEL_MM = 1.0
# ──────────────────────────────────────────────────────────────────────────────

obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = obj

voxel_bu = VOXEL_MM * 0.001  # mm → BU con scale_length=0.001
max_dim_mm = max(obj.dimensions) * 1000

# Stima face count risultante
estimated_faces = int((max_dim_mm / VOXEL_MM) ** 2 * 6)
print(f"Voxel Remesh fallback: voxel={VOXEL_MM}mm ({voxel_bu:.5f} BU)")
print(f"Stima face count risultante: ~{estimated_faces:,}")

mod = obj.modifiers.new(name="VoxelRemesh_Fallback", type='REMESH')
mod.mode = 'VOXEL'
mod.voxel_size = voxel_bu
mod.use_smooth_shade = False
bpy.ops.object.modifier_apply(modifier="VoxelRemesh_Fallback")

print(f"Post-Voxel Remesh: {len(obj.data.polygons):,} facce")
print("→ Riprendere da CALL 6 (smoothing + decimazione finale)")
```

---

## Profilo Bambu Studio consigliato per output fotogrammetria

| Caso d'uso | Profilo | Note |
|---|---|---|
| Figurine, statuette | `slicing_profiles.md#profilo-1` — Figurina Estetica | 0.12mm, 4 pareti, Gyroid 15%, Tree support |
| Oggetti di arredo / deco | `slicing_profiles.md#profilo-1` | Stessa cura estetica |
| Repliche funzionali | `slicing_profiles.md#profilo-2` — Parte Funzionale | 0.20mm, 4 pareti, Grid 40% |
| Oggetti grandi (> 150mm) | `slicing_profiles.md#profilo-5` — Grande | 0.28mm, Lightning 10%, brim 10mm |
| Alta fedeltà dettaglio | `slicing_profiles.md#profilo-4` — Miniatura | 0.08–0.12mm, velocità 80mm/s |

---

## Differenze rispetto all'AI Recipe — Riepilogo

| Aspetto | AI Recipe | Photogrammetry Recipe |
|---|---|---|
| Face count iniziale | 10k–500k | 500k–10M+ |
| Decimazione | Dopo repair | **Prima** (CALL 4, fase massiva) |
| Background cleanup | Non necessario | **Obbligatorio** (CALL 2) |
| Scale origine | Unità normalizzata [0,1] | GPS (metri) / arbitraria / marker |
| Surface noise | Lieve (SDF-based) | Profondo (lighting artifacts) |
| Smoothing | lambda=1.0, iter=3 | lambda=1.0–1.5, iter=5–8 |
| Buchi | Rari | Frequenti (coverage gaps) |
| Normali | Spesso già corrette | Patch locali invertite |

---

## Relazioni con altri doc KB

- `source_mesh_characteristics.md` → profilo tipico fotogrammetria vs AI
- `ai_mesh_recipe.md` → pipeline parallela per mesh AI-generated
- `decimation_remesh.md` → parametri dettagliati Decimate e Voxel Remesh
- `mesh_repair.md` → dettaglio operatori di repair
- `slicing_profiles.md` → profili Bambu Studio per ogni tipo di output
- `orientation_strategy.md` → orientamento ottimale del modello sul bed
