# Orientation Strategy — Scelta Orientamento per Stampa FDM

Determinare l'orientamento ottimale di una mesh prima del slicing è uno dei passi più impattanti sulla qualità, resistenza e quantità di supporti. Questo documento descrive il ragionamento, le metriche quantitative e il codice per automatizzare la scelta.

---

## Principi Fisici FDM

### Anisotropia
FDM produce pezzi anisotropi: le layer XY sono forti (polimero fuso ben fuso insieme), la direzione Z è debole (adesione tra layer, tipicamente 50–70% della resistenza XY per PLA). Implicazione: le forze critiche devono essere **parallele** al piano XY.

### Overhang
- Angolo ≤ 45° dalla verticale → stampabile senza supporti su PLA con buon cooling
- Angolo 45–60° → possibile con buon cooling, qualità superficiale degradata
- Angolo > 60° → richiede supporti

L'angolo di overhang si misura tra la normale alla faccia e il vettore Up (0, 0, -1). In Blender:
```python
import mathutils
down = mathutils.Vector((0, 0, -1))
overhang_angle = math.degrees(normal.angle(down))
# faccia è overhang se overhang_angle < 90 e l'angolo con UP < 45
```

### Superficie visibile
L'orientamento espone la "pancia" del modello al letto (layer lines orizzontali, visibili). Le facce visivamente importanti vanno orientate lateralmente o verso l'alto.

### Impronta (footprint)
- Piccola impronta → meno rischio warping, meno brim necessario
- Grande impronta → più stabilità sul letto, meno altezza = meno tempo stampa

---

## Metriche di Scoring

Definire 4 metriche su cui ottimizzare l'orientamento:

| Metrica | Cosa misura | Peso consigliato |
|---|---|---|
| `overhang_area` | Area totale facce con angolo > 45° | Alto (−) |
| `support_footprint` | Proiezione XY delle aree overhang | Alto (−) |
| `z_height` | Altezza del modello nella direzione scelta | Medio (−) |
| `bottom_flatness` | Planarity dell'area di contatto col letto | Medio (+) |

Score totale: `S = −w1·overhang_area − w2·support_footprint − w3·z_height + w4·bottom_flatness`

---

## Implementazione — Score per Orientamento Dato

```python
import bpy
import bmesh
import math
import mathutils

def score_orientation(obj_name, rotation_euler=(0, 0, 0), overhang_threshold_deg=45.0):
    """
    Calcola un punteggio per l'orientamento definito da rotation_euler (radianti).
    
    Restituisce un dict con metriche individuali e score composito.
    Score più alto = orientamento migliore.
    
    Pesi: overhang_area e z_height hanno impatto negativo.
    """
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        return {"error": f"Object '{obj_name}' not found"}
    
    # Costruisci matrice di rotazione temporanea
    rot_matrix = mathutils.Euler(rotation_euler, 'XYZ').to_matrix().to_4x4()
    world_matrix = rot_matrix  # assumiamo oggetto centrato all'origine
    
    # Accedi alla mesh via depsgraph (con modifier applicati)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = obj_eval.to_mesh()
    
    overhang_area = 0.0
    total_area = 0.0
    
    # Vettore "down" nel sistema mondo
    down = mathutils.Vector((0, 0, -1))
    threshold_rad = math.radians(overhang_threshold_deg)
    
    for poly in mesh.polygons:
        # Normale nel sistema mondo dopo rotazione
        normal_world = (rot_matrix.to_3x3() @ poly.normal).normalized()
        face_area = poly.area  # in Blender units²
        total_area += face_area
        
        # Angolo tra normale e vettore "down"
        angle = normal_world.angle(down)
        # Faccia è overhang se punta verso il basso (angle < 90°) oltre la soglia
        if angle < (math.pi / 2):  # normale punta verso il basso
            overhang_from_horizontal = (math.pi / 2) - angle  # 0=orizzontale, π/2=verticale
            if overhang_from_horizontal > threshold_rad:
                # Angolo rispetto alla verticale > threshold → overhang
                pass
            # Logica corretta: overhang = faccia orizzontale che guarda verso il basso
            # angle(normal, down) piccolo → faccia guarda in basso = overhang grave
            if angle < (math.pi / 2 - threshold_rad):
                overhang_area += face_area
    
    # Bounding box dopo rotazione
    bbox_corners = [rot_matrix @ mathutils.Vector(c) for c in obj.bound_box]
    z_values = [c.z for c in bbox_corners]
    z_height = max(z_values) - min(z_values)
    
    obj_eval.to_mesh_clear()
    
    # Score composito (normalizzato su total_area per indipendenza dalla scala)
    overhang_ratio = overhang_area / max(total_area, 1e-9)
    
    # Pesi
    w_overhang = 2.0
    w_height = 0.5
    
    score = -(w_overhang * overhang_ratio) - (w_height * z_height / 100.0)
    
    return {
        "rotation_deg": [math.degrees(r) for r in rotation_euler],
        "overhang_area_mm2": overhang_area * 1e6,  # BU² → mm² (con scale_length=0.001)
        "overhang_ratio": overhang_ratio,
        "z_height_mm": z_height * 1000,
        "total_area_mm2": total_area * 1e6,
        "score": score
    }

# Esempio d'uso: confronta 3 orientamenti
results = []
for rx, rz in [(0,0), (math.pi/2, 0), (0, math.pi/2), (math.pi, 0)]:
    r = score_orientation("MyObject", rotation_euler=(rx, 0, rz))
    results.append(r)
    print(f"Rot {r['rotation_deg']}: overhang={r['overhang_ratio']:.1%}, z={r['z_height_mm']:.1f}mm, score={r['score']:.4f}")

# Orientamento migliore = score più alto
best = max(results, key=lambda x: x.get("score", float('-inf')))
print(f"\nMigliore: Rotazione {best['rotation_deg']}, score={best['score']:.4f}")
```

---

## Ricerca a Griglia — Orientamento Automatico

Per una ricerca sistematica (costosa ma affidabile):

```python
import numpy as np

def find_best_orientation(obj_name, steps=8, overhang_threshold_deg=45.0):
    """
    Cerca l'orientamento ottimale campionando rotazioni a griglia.
    
    steps=8: griglia 8×8 su (X: 0–360°, Z: 0–360°) = 64 campioni.
    Per uso pratico, campionare solo X (inclinazione) con Z=0 è sufficiente.
    """
    angles = np.linspace(0, 2 * math.pi, steps, endpoint=False)
    results = []
    
    for rx in angles:
        for rz in angles:
            r = score_orientation(obj_name, rotation_euler=(rx, 0, rz),
                                   overhang_threshold_deg=overhang_threshold_deg)
            if "error" not in r:
                results.append(r)
    
    results.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"Top 3 orientamenti per '{obj_name}':")
    for i, r in enumerate(results[:3]):
        print(f"  #{i+1}: rot={[f'{v:.0f}°' for v in r['rotation_deg']]}, "
              f"overhang={r['overhang_ratio']:.1%}, z={r['z_height_mm']:.1f}mm, "
              f"score={r['score']:.4f}")
    
    return results[0] if results else None

# best = find_best_orientation("MyObject", steps=12)
```

---

## Applicare la Rotazione

Dopo aver identificato l'orientamento ottimale, applicarlo all'oggetto:

```python
def apply_orientation(obj_name, rotation_euler_rad):
    """
    Applica la rotazione e porta l'oggetto con il fondo sul piano Z=0.
    Esegue transform_apply(rotation=True) per consolidare.
    """
    import bpy
    import mathutils
    
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        print(f"Oggetto '{obj_name}' non trovato")
        return
    
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    # Applica rotazione
    obj.rotation_euler = mathutils.Euler(rotation_euler_rad, 'XYZ')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    
    # Porta il fondo a Z=0
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    min_z = min((obj.matrix_world @ mathutils.Vector(c)).z for c in obj.bound_box)
    obj.location.z -= min_z
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    
    print(f"Rotazione applicata. Dimensioni: {[f'{d*1000:.1f}mm' for d in obj.dimensions]}")
```

---

## Criteri di Scelta Manuale (Euristiche)

Quando non si usa la ricerca a griglia, seguire questa gerarchia decisionale:

1. **Resistenza meccanica prima di tutto**: le forze attese (trazione, flessione) devono essere nel piano XY. Esempio: una staffa a L va orientata con il lato lungo orizzontale.
2. **Superfici visibili verso l'alto o laterali**: la faccia visibile al pubblico non deve essere sul letto (strato bottom ha layer-lines visibili). Non deve essere su overhang (stringing e qualità degradata).
3. **Geometria con cavità profonde**: orientare in modo che le cavità siano aperte verso l'alto, così il slicer non genera supporti interni impossibili da rimuovere.
4. **Minimizzare altezza Z**: meno layer = meno tempo stampa. Oggetti piatti vanno flat sul letto.
5. **Impronta stabile**: base ampia riduce il rischio di distacco durante stampa lunga.

---

## Caso Speciale: Teste e Busti (figurine organiche)

Orientamento quasi universale: **verticale** (testa in alto, collo verso il basso).

Ragionamenti:
- Le normali al viso sono prevalentemente laterali → nessun overhang frontale
- Le orecchie e sporgenze frontali sono in overhang → accettabile, le estremità sono piccole
- La resistenza del collo (Z) è la più debole, ma regge peso statico
- Alternativa: **inclinare di ~15° verso l'indietro** per ridurre overhang sul mento e sul naso

Per `testa_di_moro_*.stl`: valutare inclinazione 0–20° verso l'indietro, verificare il naso e le sporgenze della corona.

---

## Migliorie 2024-2026 (deep research findings)

Lo scorer base sopra è funzionale ma migliorabile. Quattro estensioni emerse dalla letteratura recente meritano integrazione:

### Bridge exception nello score overhang

Una face downward che spazia ≤10mm tra due edge supportati è un **bridge**, non un overhang vero — Bambu A1 PLA stampa bridge fino a 30mm con fan 100% (vedi P3 in [fdm_printing_constraints]). Includerla in `overhang_area` penalizza orientamenti che non meritano penalità.

```python
def is_bridgeable(face, bvh, max_span_mm=10.0):
    """Una face è bridgeable se i suoi edge sono supportati da geometria
    sottostante a distanza orizzontale ≤ max_span_mm.

    Implementazione: cast ray verso -Z dai vertices della face; se
    entrambi gli endpoint di ogni edge trovano hit entro max_span_mm
    horizontal, l'edge è supportato e la face non è un vero overhang.
    """
    import mathutils
    supported_edges = 0
    for edge in face.edges:
        v0, v1 = edge.verts[0].co, edge.verts[1].co
        # Project endpoints downward, check if geometry below within span
        for v in (v0, v1):
            origin = v + mathutils.Vector((0, 0, 1e-6))
            hit, _, _, dist = bvh.ray_cast(origin, mathutils.Vector((0, 0, -1)))
            if hit is not None and (v.xy - hit.xy).length <= max_span_mm:
                supported_edges += 0.5  # half per endpoint
                break
    return supported_edges >= len(face.edges)

# In score_orientation, escludi bridges dal penalty:
overhang_faces = [f for f in mesh.polygons
                  if normal_angle_from_vertical(f) > overhang_threshold
                  and not is_bridgeable(f, bvh)]
```

### Convex-hull stability come metrica primaria

`bottom_flatness` (area face piatta a Z_min) è meno robusto di `hull_stability = bottom_contact_hull_area / bbox_xy_area`. Se i vertices a Z_min formano un convex hull esteso, l'oggetto è stabile durante print anche senza una face piatta singola (es. tripode, base con 3-4 piedi).

```python
import scipy.spatial
zmin = min(v.co.z for v in obj.data.vertices)
verts_at_bottom = [v for v in obj.data.vertices if v.co.z < zmin + 0.0002]
if len(verts_at_bottom) >= 3:
    pts_2d = [(v.co.x, v.co.y) for v in verts_at_bottom]
    # In scipy, ConvexHull(2D).volume restituisce l'AREA del poligono 2D
    hull_area = scipy.spatial.ConvexHull(pts_2d).volume
    bbox_xy_area = obj.dimensions.x * obj.dimensions.y
    hull_stability = hull_area / max(bbox_xy_area, 1e-9)  # 0..1
```

Tipico: hull_stability < 0.15 → instabile durante print, aggiungi brim.

### Two-stage search invece di brute grid

64 sample casuali su SO(3) sono inefficienti. Approccio migliore:

1. **Stage 1 — Candidate set (~30 candidati)**: genera orientamenti da face normals weighted by area (Tweaker-3-style algorithm) + 14 cardinali (±X/±Y/±Z + 8 diagonali principali).
2. **Stage 2 — Local refinement**: prendi i top-3 dello stage 1, applica `scipy.optimize.minimize` (Nelder-Mead) su ±15° box di ognuno.

Risultato: ~50 valutazioni totali con qualità superiore a 64 sample casuali su 200k faces.

### Pareto front invece di somma pesata

Lo score `S = w1·overhang + w2·footprint + w3·height + w4·flatness` mescola unità incommensurabili (mm² vs mm vs adimensionale). Meglio restituire il dict di metriche separate e lasciare al chiamante (o all'utente via `kb_route(needs_user_input=true)`) scegliere dal Pareto front:

```python
def pareto_front(results):
    """results = lista di dict metric→valore. Restituisce sotto-lista
    di candidati non dominati."""
    pareto = []
    for r in results:
        dominated = any(
            all(other[k] <= r[k] for k in r) and any(other[k] < r[k] for k in r)
            for other in results if other is not r
        )
        if not dominated:
            pareto.append(r)
    return pareto
```

L'utente sceglie tra "min overhang" (qualità superficie) vs "min height" (tempo + stabilità).

### Heuristic thresholds per early termination

Alcune orientazioni sono ovviamente buone — non vale la pena valutare alternative:

```python
if (overhang_ratio < 0.05 and hull_stability > 0.6 and z_height_mm < 150):
    return current_orientation  # praticamente ottima, stop
```

## Tweaker-3 — perché NON wrapparlo (alert licensa)

[Tweaker-3](https://github.com/ChristophSchranz/Tweaker-3) è il tool open-source più maturo per print orientation (algoritmo candidate-set + area cumulation, calibrato con EA offline). **Pure Python + NumPy**, callable come libreria via `from MeshTweaker import Tweak`.

**MA è GPL-3.0**. Wrappare Tweaker-3 in `blender-mcp` forzerebbe **l'intero progetto a GPL-3.0** (clausola virale). Sconsigliato. Soluzione: **rimplementare l'idea** (candidate-set + area-cumulation scoring) — ~80 righe NumPy, license-clean.

Stessa logica per Bambu Studio / OrcaSlicer auto-orient: AGPL-3.0 source, ma è C++ inaccessibile da Python comunque.

## Bambu Studio ha già auto-orient nativo

`Object → Auto Orient` in Bambu Studio (ed Orca). Funzione di costo: `f(overhang_area, bottom_area, convex_hull_area, appearance_area)`. **Limiti documentati**: bridge detection debole, overhang estimation rough pre-slice. Il Blender-side orient ha valore quando:
- Multi-object scene con vincoli relativi (es. "queste 3 parti devono mantenere posa relativa")
- Pipeline headless/MCP (no Bambu Studio open)
- Custom load-axis constraint (es. "questa parte va caricata in compressione lungo asse X")
- Bake della rotation nell'STL prima di handoff a tool downstream

## Riferimenti academic (2022-2024)

- Zhang et al. (2022). *Build orientation optimization coupled with adaptive slicing*. Int. J. Adv. Manuf. Tech. doi:10.1007/s00170-022-10237-9. → Couples orientation con adaptive layer height; fixed-layer scoring overestimates support cost ~15%.
- Mele & Campana (2022). *Multi-Part Orientation Planning Schema*. Micromachines 13(10):1777. → NSGA-II per ottimizzare più parti su un piatto.
- Comparative study (2024). doi:10.1515/mt-2024-0099. → Whale Optimization e Differential Evolution superano i GA per budget ≤30s.

## Relazioni con altri doc KB

- `fdm_printing_constraints.md` → angoli overhang e lunghezze bridge per A1, sezione "Why these numbers — physical basis"
- `support_strategy.md` → questo doc decide SE servono supporti, quello decide COME metterli
- `mathutils.md` → BVHTree e Vector per calcoli geometrici
- `mesh_quality_assessment.md` → `print3d_overhang` per analisi overhang con 3D Print Toolbox
- `blender_3d_print_toolbox.md` → reference completa di `print3d_check_overhang` per drill-down sulla geometria critica
