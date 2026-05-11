# Decimazione e Remeshing — Riduzione Poligoni per Stampa 3D

## Contesto

Mesh da fotogrammetria e da generatori AI hanno spesso un conteggio poligoni eccessivo rispetto a quello necessario per la stampa FDM. I slicer moderni (Bambu Studio) gestiscono bene fino a ~500k triangoli; oltre 1–2M il tempo di slicing aumenta significativamente senza miglioramento qualitativo reale, poiché la risoluzione del nozzle (0.4mm) è il limite fisico, non il numero di poligoni.

**Target realistico per stampa FDM**: 50k–200k triangoli per oggetti di dimensione media (50–150mm). Riduzioni aggressive fino a 20k–50k sono spesso accettabili per oggetti semplici.

## Strumenti disponibili e loro tradeoff

### DecimateModifier

```python
mod = obj.modifiers.new("Decimate", type='DECIMATE')
```

Tre modalità, con comportamenti molto diversi:

#### COLLAPSE (default)
```python
mod.decimate_type = 'COLLAPSE'
mod.ratio = 0.1          # mantieni 10% delle facce
mod.use_collapse_triangulate = True   # triangolizza prima del decimate
```
- `ratio`: 0.0–1.0. `1.0` = nessuna riduzione, `0.1` = mantieni 10% delle facce
- Algoritmo: collassa edge in ordine di costo (quadric error metrics)
- Risultato: preserva la forma complessiva ma può produrre edge non-manifold su geometria complessa
- Veloce: operazione O(n log n)
- **Non garantisce manifold**: su mesh già problematiche può peggiorare la topologia
- Buon punto di partenza: `ratio=0.1` su mesh fotogrammetriche (riduce 2M → 200k)

#### DISSOLVE
```python
mod.decimate_type = 'DISSOLVE'
mod.angle_limit = 0.0873  # radianti ≈ 5°
```
- Rimuove edge/vertex dove l'angolo tra facce adiacenti è inferiore a `angle_limit`
- Ottimale per superfici piane o quasi-piane (rimuove triangoli inutili in aree flat)
- **Preserva meglio la topologia** rispetto a COLLAPSE
- Non riduce efficacemente mesh organiche/curve
- `angle_limit` in radianti: 5° = 0.0873, 10° = 0.1745, 15° = 0.2618
- Utile come secondo passaggio dopo COLLAPSE per pulire aree planari residue

#### UNSUBDIV
```python
mod.decimate_type = 'UNSUBDIV'
mod.iterations = 2
```
- Funziona solo su mesh con topologia di subdivisione regolare (quads organizzati)
- Non adatto a triangle soup da AI/fotogrammetria
- Ogni iterazione dimezza approssimativamente il numero di facce

---

### RemeshModifier

Ricostruisce l'intera mesh da zero basandosi sulla forma. **Sempre manifold** come risultato.

```python
mod = obj.modifiers.new("Remesh", type='REMESH')
```

#### VOXEL (raccomandato per fotogrammetria/AI)
```python
mod.mode = 'VOXEL'
mod.voxel_size = 0.002    # 2mm con scale_length=0.001
mod.adaptivity = 0.0      # 0 = uniforme; >0 = adattivo (più denso dove c'è dettaglio)
mod.use_smooth_shade = False
```
- `voxel_size`: dimensione in BU di ciascun voxel. Con scale_length=0.001: `0.002` = 2mm
- **Regola pratica**: `voxel_size` = dimensione_minima_feature_desiderata / 2
  - Feature da 1mm → voxel_size=0.001 (1mm)
  - Feature da 2mm → voxel_size=0.002 (2mm)
  - Solo forma generale → voxel_size=0.005 (5mm)
- Risultato: mesh uniforme, sempre watertight, perde dettagli più piccoli del voxel
- Lento su mesh grandi; può richiedere 10–30 secondi per 2M triangoli
- **Uso principale**: fix radicale di mesh fotogrammetriche con buchi/non-manifold + decimazione in un solo passaggio

#### SHARP / SMOOTH (legacy)
```python
mod.mode = 'SHARP'    # preserva spigoli vivi
mod.mode = 'SMOOTH'   # leviga la superficie
mod.octree_depth = 6  # 6–9; più alto = più dettaglio, più lento
```
- Meno controllo rispetto a VOXEL
- `octree_depth=6` ≈ risoluzione media, `octree_depth=8` ≈ alta risoluzione
- Utile quando VOXEL produce risultati con troppo aliasing sugli spigoli

---

## Tabella di Calibrazione Pratica — Voxel Size per Stampa FDM

Valori empirici per workflow scale_length=0.001 (1 BU = 1mm).
**RAM stimata** si riferisce al picco durante il calcolo del remesh, non alla mesh finale.

| Tipo modello | Dim. max (mm) | voxel_size (BU) | = mm | Face count stimato | RAM picco |
|---|---|---|---|---|---|
| Miniatura / figurina piccola | 30–50 | 0.0003–0.0005 | 0.3–0.5 mm | 500k–2M | 4–8 GB |
| Figurina media | 50–100 | 0.0005–0.001 | 0.5–1 mm | 200k–600k | 2–4 GB |
| Oggetto decorativo | 80–150 | 0.001–0.002 | 1–2 mm | 100k–300k | 1–2 GB |
| Parte funzionale (generale) | 50–150 | 0.002 | 2 mm | 80k–200k | 512 MB–1 GB |
| Parte meccanica con incastri | 20–80 | 0.0005–0.001 | 0.5–1 mm | 150k–400k | 1–3 GB |
| Oggetto grande decorativo | 150–256 | 0.003–0.005 | 3–5 mm | 60k–150k | 256–512 MB |
| Solo forma generale (test) | qualsiasi | 0.005–0.01 | 5–10 mm | 10k–50k | <256 MB |

**Regola rapida per FDM con nozzle 0.4 mm:**
- Feature detail da preservare = 2× nozzle = **0.8mm** → `voxel_size = 0.0004` (0.4mm = feature_size/2)
- Sotto 0.5mm voxel: il remesh diventa lento e il dettaglio non è stampabile comunque
- **Sweet spot pratico per la maggior parte dei modelli**: `voxel_size = 0.001` (1mm)

```python
# Scelta rapida voxel_size per FDM (nozzle 0.4mm, PLA, A1)
# Livello       voxel_size   Risultato atteso
# FAST TEST     0.005        <30s, ~50k faces, solo forma
# STANDARD      0.002        <2min, ~100–200k faces, buona qualità FDM
# DETAIL        0.001        2–10min, ~300–600k faces, feature ~1mm
# HIGH DETAIL   0.0005       10–30min, ~1M+ faces, feature ~0.5mm (limite nozzle)
```

**Nota RAM critica:** `voxel_size = 0.0003` su un modello 100mm può richiedere 8–16 GB di RAM.
Se Blender va in freeze o crash: raddoppia `voxel_size` e riprova.

---

## Stima del `voxel_size` target

```python
def estimate_voxel_size(obj, target_face_count=100_000):
    """
    Stima il voxel_size per ottenere approssimativamente target_face_count.
    Formula empirica basata sulla relazione area/risoluzione.
    """
    import bpy, math

    # Area superficiale approssimativa (in BU²)
    mesh = obj.data
    total_area = sum(p.area for p in mesh.polygons)

    # Ogni voxel produce ~2 triangoli; area ≈ n_faces * (voxel_size²/2)
    # n_faces ≈ 2 * total_area / voxel_size²
    # voxel_size = sqrt(2 * total_area / target_face_count)
    voxel_size = math.sqrt(2 * total_area / target_face_count)
    return voxel_size

obj = bpy.context.active_object
vs = estimate_voxel_size(obj, target_face_count=100_000)
print(f"Voxel size suggerito per ~100k facce: {vs:.5f} BU ({vs/0.001:.2f}mm)")
```

---

## Stima ratio Decimate per target face count

```python
def estimate_decimate_ratio(obj, target_faces=100_000):
    current = len(obj.data.polygons)
    if current == 0:
        return 1.0
    ratio = min(1.0, target_faces / current)
    return ratio

ratio = estimate_decimate_ratio(bpy.context.active_object, 100_000)
print(f"Ratio per ~100k facce: {ratio:.4f}")
```

---

## Comparazione strumenti per caso d'uso

| Caso | Strumento consigliato | Parametro chiave | Note |
|------|----------------------|-----------------|------|
| Mesh pulita, troppi poligoni | Decimate COLLAPSE | ratio=0.05–0.2 | Veloce, controlla ratio |
| Mesh fotogrammetrica con noise | Remesh VOXEL | voxel_size=feature_size/2 | Risolve noise + non-manifold |
| Mesh con aree piatte dense | Decimate DISSOLVE | angle_limit 5–10° | Combinare dopo COLLAPSE |
| Mesh AI con non-manifold | Remesh VOXEL | voxel_size=0.001–0.003 | Nuclear option, sempre safe |
| Preservare spigoli vivi | Remesh SHARP | octree_depth=7 | Meglio di VOXEL per hard-surface |

---

## Applicazione e verifica

```python
import bpy

obj = bpy.context.active_object

# Applica il modifier (bake nella mesh)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_apply(modifier="Decimate")  # o "Remesh"

# Verifica risultato
mesh = obj.data
mesh.update()
print(f"Triangoli dopo: {len(mesh.polygons)}")

# Verifica manifold dopo decimazione
import bmesh
bm = bmesh.new()
bm.from_mesh(mesh)
non_manifold = [e for e in bm.edges if not e.is_manifold]
bm.free()
print(f"Edge non-manifold: {len(non_manifold)}")
# Se > 0 dopo Decimate: considera Remesh VOXEL invece
```

## Ordine di operazioni

Decimazione e remesh alterano la topologia. L'ordine rispetto ad altre operazioni è rilevante:

- **Prima** di Decimate/Remesh: rimuovi duplicati (`remove_doubles`) per evitare che il decimatore collassi geometria falsa
- **Dopo** Decimate COLLAPSE: verificare manifold — se ci sono nuovi non-manifold, passare a Remesh VOXEL
- **Dopo** Remesh VOXEL: la mesh è sempre manifold ma può aver perso feature sottili → verificare wall thickness con 3D Print Toolbox
- **Non** applicare Decimate dopo Solidify se stai usando Solidify per aggiungere spessore — il Decimate può eliminare le facce dei bordi aggiunte dal Solidify
