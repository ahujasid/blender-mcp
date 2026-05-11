# Workflow CAD e 3MF multi-materiale per Bambu

Fonte: ricerca "Analisi dei Workflow Professionali e dell'Integrazione CAD in Blender 5.1".
Uso: importare file B-Rep (STEP/IGES) in Blender, mantenere gerarchie assieme, esportare 3MF multi-materiale per Bambu Studio, produrre layout bin-packing per CNC/laser.

Copre il gap tra Blender (mesh-based) e CAD tradizionali (B-Rep parametrici), con focus sulla produzione additiva moderna.

---

## 1. Import B-Rep: STEP e IGES

Blender non supporta nativamente `.step`/`.stp`/`.iges`/`.igs` perché questi formati definiscono geometria via **equazioni NURBS**, non tessellazione. L'import richiede un *toolkit di conversione* che effettui tassellazione controllata.

### Opzione A: add-on "Import CAD Model" (consigliato)

Basato sul toolkit **Mayo** (wrapper open su OpenCascade). Funziona in Blender 4.0+/5.x.

**Parametri di qualità (tassellazione):**

| Preset | Descrizione | Uso |
|---|---|---|
| `Very Coarse` | Densità minima, forma approssimata | Anteprima assiemi > 100 parti |
| `Medium` | Bilanciato | Rendering tecnico standard |
| `Precise` | Alta risoluzione su curvature | Visualizzazione + modellazione secondaria |
| `Very Precise` | Max fedeltà NURBS | Simulazione fisica, close-up macro |

**Trade-off chiave:** `Very Precise` può produrre mesh > 1M triangoli per assieme medio. Per stampa 3D, `Medium` o `Precise` sono solitamente sufficienti.

### Opzione B: FreeCAD / OpenCascade CAD Assistant come intermediario

Per qualità delle normali superiori (utile su fillet complessi):

1. Apri STEP in **FreeCAD** o **CAD Assistant**
2. Export mesh come **GLTF** (non OBJ — vedi sotto)
3. Import GLTF in Blender: `bpy.ops.import_scene.gltf(filepath=...)`

**Perché GLTF e non OBJ:**

| Aspetto | OBJ | GLTF |
|---|---|---|
| Gerarchia assieme (parent-child) | ❌ appiattita | ✅ preservata |
| Nomi componenti | Opzionale, spesso persi | ✅ intatti |
| Materiali | MTL (limitato) | PBR nativo |
| Coordinate system | Y-up variabile | Standard (convertibile) |
| Dimensioni assieme > 700 parti | Problemi indicizzazione | Stabile |

**Uso operativo:** per assiemi CAD robotici/automotive con centinaia di parti, GLTF via FreeCAD è la strada più robusta.

### Opzione C: SimLab Soft plugin

Soluzione commerciale multipiattaforma (Win/macOS). Auto-corregge:
- Scala unità (mm vs inch)
- Orientamento Up Vector (Y-up CAD → Z-up Blender)
- Assiemi nominati

Non valutata in profondità qui; citata per completezza.

### Opzione D: Plasticity → Blender bridge

Plasticity è un CAD NURBS "per artisti". Il bridge ufficiale:
- Modellazione in Plasticity (solidi esatti)
- Sync live in Blender
- **Refacet**: ricalcola topologia con N-gons raggruppati → riduce drasticamente i triangoli mantenendo fedeltà

Elimina la retopologia manuale tipica del flusso CAD → mesh.

---

## 2. Correzione post-import

Problemi tipici dopo import CAD:

| Problema | Causa | Soluzione |
|---|---|---|
| Scala 1000× o 0.001× | CAD in m, Blender in m-as-m ma scene unit mm | `bpy.ops.transform.resize(value=(0.001,)*3)` + `transform_apply` |
| Orientamento Y-up | Convenzione CAD | Rotate -90° su X, apply |
| Gerarchie perse | Import via OBJ | Ri-creare via `object.parent_set` |
| Fillet con shading artefatto | Tassellazione grossolana | CAD Assistant per normali di qualità, o modifier `Smooth by Angle` |
| Normal flipped su parti concave | Convenzione CAD inversa | `bpy.ops.mesh.normals_make_consistent(inside=False)` |

---

## 3. Export 3MF multi-materiale per Bambu Studio

Il formato 3MF v1.4.0 è lo standard per stampanti multi-materiale moderne (Bambu X1/P1/A1 con AMS, Prusa XL). Supera STL perché trasporta:
- Unità esplicite (mm)
- Struttura multi-oggetto
- Metadati slicer
- Face sets (zone colore/supporto)
- Materiali PBR

### Setup estensione

`threemf-io` è una Core Extension. In Blender 5.1:

```python
import addon_utils
addon_utils.enable("threemf-io", default_set=True, persistent=True)
```

### Mappatura Blender → 3MF per produzione

| Asset Blender | Campo 3MF | Effetto in Bambu Studio |
|---|---|---|
| Material slot | `m:triangle.material_index` | Automazione cambio filamento AMS |
| Sculpt Face Set | `m:triangleset` | Preserva zone "pittura" dello slicer |
| Linked duplicate (Alt+D) | `m:component` (shared resource) | Riduzione dimensione file 3MF |
| Object origin | `m:transform` matrice | Posizionamento su piatto |

### Comando API

```python
bpy.ops.export_mesh.threemf(
    filepath="/output/part.3mf",
    use_selection=True,          # esporta solo oggetti selezionati
    global_scale=1.0,            # tenere 1.0 se scene_unit=MM già in mm
    use_mesh_modifiers=True,     # applica Boolean/Mirror/Array in export
    coordinate_precision=6,      # 6 cifre decimali: evita crack inter-layer
)
```

**Parametri critici:**

| Parametro | Default | Raccomandato per Bambu |
|---|---|---|
| `global_scale` | 1.0 | 1.0 (se unità scena già mm) |
| `use_selection` | False | True (controllo esplicito) |
| `use_mesh_modifiers` | True | True (no modifier stack persistito in 3MF) |
| `coordinate_precision` | 4 | 6 (evita artefatti di precisione float) |

### Workflow Bambu Studio / Orca Slicer

1. **CAD prep in Blender:**
   - Assegna material slots (uno per filamento)
   - Apply scale/rotation (`Ctrl+A`)
   - Parent/Join oggetti che devono stare insieme sul piatto
2. **Export 3MF** con flag sopra
3. **Import in Bambu Studio:**
   - Material index → mappato su slot AMS
   - Triangle sets → zone pittura preservate
4. **Slicing:** nessuna ri-assegnazione manuale necessaria

### Problema comune: oggetti "compressi" sul piatto

Se esporti più oggetti distinti, Bambu Studio può collassarli in posizione incorretta. **Fix:**
- `Ctrl+A` → Apply All Transforms su ogni oggetto
- Oppure: Parent sotto un Empty comune prima di export
- Oppure: Join (`Ctrl+J`) se sono rigidi e condividono materiale

---

## 4. Automazione parametrica (Gridfinity e simili)

Per design iterativi (es. scatole Gridfinity variabili), wrap su `export_mesh.threemf`:

```python
def export_gridfinity(width: int, depth: int, height: int, out_dir: str):
    """Genera e esporta un modulo Gridfinity parametrico."""
    obj = generate_gridfinity(width, depth, height)  # funzione di generazione
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    filepath = f"{out_dir}/grid_{width}x{depth}x{height}.3mf"
    bpy.ops.export_mesh.threemf(
        filepath=filepath,
        use_selection=True,
        global_scale=1.0,
        use_mesh_modifiers=True,
        coordinate_precision=6,
    )
    return filepath
```

Con palette filamenti personalizzata tramite "Detect from Materials palette builder", lo slicer carica profili pre-configurati eliminando setup manuale.

---

## 5. Riparazione mesh CAD — T-junction e self-intersection

Mesh tessellate da CAD possono presentare patologie topologiche non visibili ma letali per slicer.

### T-junction detection

Definizione: un vertice sta su un edge di un'altra faccia senza esservi connesso topologicamente. Blender mostra superficie continua, lo slicer vede *crack*.

Algoritmo di rilevamento (soglia ε ≈ 1e-5 BU):

```python
import bmesh
from mathutils import kdtree

def find_t_junctions(bm: bmesh.types.BMesh, epsilon: float = 1e-5):
    """Ritorna lista di tuple (vert, edge) dove vert giace su edge senza connessione."""
    # Costruisci KDTree dei vertici
    tree = kdtree.KDTree(len(bm.verts))
    for v in bm.verts:
        tree.insert(v.co, v.index)
    tree.balance()
    
    suspects = []
    for e in bm.edges:
        v0, v1 = e.verts
        mid = (v0.co + v1.co) * 0.5
        edge_len = (v1.co - v0.co).length
        # cerca vertici vicini al midpoint entro edge_len/2
        for co, idx, dist in tree.find_range(mid, edge_len * 0.5):
            v = bm.verts[idx]
            if v in (v0, v1):
                continue
            # è un T-junction se v è quasi sul segmento
            if is_point_on_segment(v.co, v0.co, v1.co, epsilon):
                suspects.append((v, e))
    return suspects
```

Riparazione: per ogni (v, e), `bmesh.utils.edge_split(e, v_source, fac=t)` + `bmesh.ops.weld_verts`.

### Self-intersection: BVH overlap

Per mesh "solide in apparenza" con auto-intersezioni interne (risultato di Spin/Array aggressivi):

```python
import bmesh
import mathutils

def detect_self_intersections(bm: bmesh.types.BMesh, epsilon: float = 1e-5):
    tree = mathutils.bvhtree.BVHTree.FromBMesh(bm, epsilon=epsilon)
    overlaps = tree.overlap(tree)  # lista coppie (face_idx_1, face_idx_2)
    # filtra auto-coppie e coppie adiacenti
    return [(a, b) for a, b in overlaps if a != b]
```

**Strategie di riparazione:**

| Severità | Metodo | Pro | Contro |
|---|---|---|---|
| Leggera | `bmesh.ops.intersect(use_self=True)` | Preserva topologia esterna | Mesh interna non pulita |
| Media | Boolean Union modifier con `use_self=True`, operando solo su sé stesso | Chirurgico | Solver EXACT lento |
| Totale | **Voxel Remesh** (nuclear option) | Sempre watertight | Perde tutto il dettaglio interno |

Per modelli stampa-resina dove la topologia interna è irrilevante, Voxel Remesh è la via pragmatica. Per FDM con parti funzionali (viti, cerniere), Boolean Union con `use_self` preserva le superfici critiche.

---

## 6. Mesh smoothing volume-preserving

Limite storico: Laplacian Smoothing standard causa contrazione di volume fino al **91.3%** dopo 100 iterazioni (collasso quasi completo).

**Alternativa in Blender:**
- `CorrectiveSmoothModifier` con `smooth_type='SIMPLE'` + `use_bind_mode` — preserva shape iniziale
- `LaplacianSmoothModifier` con `use_volume_preserve=True` (flag esplicito)
- Per mesh scansione/CAD tassellata: iterazioni limitate (3–5) e `lambda_factor ≤ 0.5`

Vedi `modifiers_deform.md` §LaplacianSmooth / CorrectiveSmooth per parametri completi.

---

## 7. Vettorizzazione NumPy per mesh grandi

Per mesh > 10k vertici, loop Python nativi sono impraticabili. Il pattern `foreach_get` / `foreach_set` trasferisce dati in buffer numpy riducendo overhead RNA di **60×**.

### Benchmark 25M vertici

| Metodo | Tempo |
|---|---|
| Loop Python su `vertex.co` | > 100 s (stima) |
| `foreach_get` + loop Python | 2–4 s |
| `foreach_get` + NumPy vettorizzato | ~1 s |

### Pattern canonico

```python
import numpy as np

def vectorized_offset_along_normal(obj, delta: float):
    """Offset tutti i vertici lungo la loro normale di delta mm."""
    mesh = obj.data
    n_verts = len(mesh.vertices)
    
    # LEGGI tutti i dati in un buffer numpy
    coords = np.empty(n_verts * 3, dtype=np.float32)
    normals = np.empty(n_verts * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", coords)
    mesh.vertices.foreach_get("normal", normals)
    
    coords = coords.reshape(-1, 3)
    normals = normals.reshape(-1, 3)
    
    # MODIFICA vettorizzato
    coords += normals * delta
    
    # SCRIVI back
    mesh.vertices.foreach_set("co", coords.ravel())
    mesh.update()
```

Applicazione in `mechanical_algorithms.md` per ISO 286 offset.

---

## 8. Lattice / LSTO (Lattice Structure Topology Optimization)

Workflow 2-fasi per design ottimizzato di parti meccaniche leggere:

### Fase 1 — ottimizzazione densità (SIMP)

Formula: $E(\rho) = \rho^p E_0$ (Solid Isotropic Material with Penalization, tipicamente $p=3$).

Blender non ha solver FEM nativo. Workflow:
1. Export mesh in formato FEM (es. ABAQUS `.inp`) via `bpy.ops.export_anim.bvh` custom o script
2. Solve in CalculiX / OpenFOAM → mappa di densità $\rho(x, y, z)$
3. Import back come vertex group peso o attributo

### Fase 2 — latticizzazione

Opzioni in Blender:

| Metodo | Controllo | Performance | Uso |
|---|---|---|---|
| Geometry Nodes + Points on Faces | Parametrico, field-driven | Ottima (interno C++) | Lattici Voronoi per osteointegrazione |
| Script BMesh + NumPy | Massimo | Buona | LSTO custom |
| Add-on "Lattice Microstructure" | Preset | Limitata | Rapid prototyping |

Esempio pattern GeoNodes: `DistributePointsOnFaces` → `InstanceOnPoints` (strut primitivo) → scala con field della densità.

---

## 9. Automazione G-code: inject temperature tower

Per calibrazione fine (PETG, PA-CF), Blender può generare geometria di test e un post-processor G-code in Python inietta comandi di variazione parametro:

```python
import re

def inject_temp_tower(filepath: str, start_z: float, step_z: float,
                     start_temp: int, temp_step: int):
    """Inietta M104 ad altezze Z specifiche nel G-code per temp tower."""
    with open(filepath) as f:
        lines = f.readlines()
    
    out_lines = []
    current_temp = start_temp
    for line in lines:
        m = re.search(r"Z(\d+\.?\d*)", line)
        if m:
            z = float(m.group(1))
            if z >= start_z and (z - start_z) % step_z < 0.001:
                out_lines.append(f"M104 S{current_temp}\n")
                current_temp -= temp_step
        out_lines.append(line)
    
    with open(f"mod_{filepath}", "w") as f:
        f.writelines(out_lines)
```

Consente test di temperatura/velocità/fan in un unico provino.

---

## 10. 2D Bin-packing per CNC/laser

Per produzione parti piatte su fogli standard, integrare libreria `rectpack` (installabile via pip):

### Algoritmi disponibili

| Algoritmo | Meccanismo | Uso |
|---|---|---|
| `Skyline` | Mappa altezza 1D | Veloce, packing online |
| `Guillotine` | Tagli ortogonali ricorsivi | Compatibilità macchine edge-to-edge |
| `MaxRects` | Tracking rettangoli massimali | Max densità (più costoso) |

### Integrazione con Blender

```python
from rectpack import newPacker

def pack_objects_2d(objs, sheet_w: float, sheet_h: float, margin: float = 2.0):
    """Packa bounding box 2D (proiezione XY) su foglio sheet_w × sheet_h mm."""
    packer = newPacker(rotation=True)
    
    rects = []
    for obj in objs:
        # bbox proiettato XY in mm
        dims = obj.dimensions
        w = dims.x + margin
        h = dims.y + margin
        rects.append((w, h, obj.name))
    
    for w, h, name in rects:
        packer.add_rect(w, h, rid=name)
    packer.add_bin(sheet_w, sheet_h)
    packer.pack()
    
    placements = {}
    for rect in packer.rect_list():
        bin_idx, x, y, w, h, rid = rect
        placements[rid] = (x, y, w, h)
    return placements
```

Output: coordinate di posizionamento sul foglio per CNC router, laser cutter, waterjet.

---

## Cross-reference

- `import_export.md` — API base STL/3MF
- `api_migration_5x.md` — estensione `threemf-io` e flag `use_hole_tolerant`
- `mesh_repair.md` — T-junction e self-intersection nel contesto mesh AI
- `mechanical_algorithms.md` — uso di `foreach_get`/`foreach_set` per ISO 286
- `bambu_a1_physical_constants.md` — compensazioni XY/hole per Bambu A1
- `modifiers_deform.md` — LaplacianSmooth `use_volume_preserve`
