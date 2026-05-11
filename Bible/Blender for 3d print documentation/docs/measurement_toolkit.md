# Measurement Toolkit — API unificata di misura

## Contesto

L'agente deve poter misurare qualsiasi grandezza geometrica per (a) auto-diagnosticare la mesh, (b) rispondere a domande quantitative dell'utente ("quanto è spesso qui?", "che volume occupa?", "il foro è 6 o 6.4 mm?"), (c) decidere se la geometria è nei vincoli FDM.

Questo toolkit unifica tutte le misure usate nella KB in un'unica API coerente. Tutte le funzioni:
- Accettano oggetti Blender (non BMesh grezzi) quando possibile
- Ritornano valori in **mm** (double precision) — NON in BU
- Non modificano l'oggetto (pattern MCP-safe)
- Stampano log strutturato via `print()` per capture MCP

Prerequisito: `scale_length=0.001` (1 BU = 1 mm).

---

## 1. Gerarchia delle misure

| Categoria | Misura | API | Costo computazionale |
|---|---|---|---|
| Linear | distanza punto-punto | `mathutils.Vector.length` | O(1) |
| Linear | distanza oggetto-oggetto (centri) | `(o1.location - o2.location).length * 1000` | O(1) |
| Linear | closest point tra due oggetti | `BVHTree.find_nearest` iterato | O(n log n) |
| Bounding | bbox aligned (local) | `obj.bound_box` × 8 | O(1) |
| Bounding | bbox world-aligned (AABB) | `[(matrix_world @ v) for v in verts]` reduce min/max | O(n) |
| Bounding | bbox minimo orientato (OBB) | PCA su vertici | O(n) |
| Thickness | parete locale (raycast da faccia) | `BVHTree.ray_cast` lungo -normal | O(log n) per sample |
| Thickness | distribuzione sull'intera mesh | sampling N facce + raycast | O(N log n) |
| Hole | diametro foro cilindrico | detect edge loop cilindrico + `calc_center_median` + radius fit | O(n) |
| Area | superficie totale | `sum(poly.area) * 1e6` | O(n) |
| Area | cross-section a un piano | `bmesh.ops.bisect_plane` su copia + fill + area | O(n) |
| Volume | mesh chiuso | `bm.calc_volume()` × 1e9 | O(n) |
| Mass | PLA (densità 1.24 g/cm³) | `volume_cm3 * 1.24` | O(1) |
| CoM | centro di massa (geometric) | media ponderata centro facce × area | O(n) |
| CoM | centro di volume (tetra integration) | formula divergence | O(n) |
| Angle | angolo tra due edge | `.angle()` tra Vector | O(1) |
| Angle | dihedral angle tra due facce | `f1.normal.angle(f2.normal)` | O(1) |
| Distribution | wall thickness histogram | sampling + bucket | O(N) |

---

## 2. Utility di base

```python
import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

# Conversioni di scala
BU_TO_MM = 1000.0   # 1 BU = 1 mm con scale_length=0.001 → quindi 1000 mm per 1 m-equivalente

def _bm_from_obj(obj, evaluated=False):
    """BMesh copia non distruttiva dall'oggetto. Richiede obj.type=='MESH'."""
    if obj.type != 'MESH':
        raise TypeError(f"{obj.name} is not a MESH")
    bm = bmesh.new()
    if evaluated:
        dg = bpy.context.evaluated_depsgraph_get()
        bm.from_object(obj, dg)
    else:
        bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)   # tutto in world space
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return bm
```

---

## 3. Linear measurements

### Distanza tra due oggetti — closest surface points

```python
def closest_distance_mm(obj_a, obj_b):
    """
    Distanza più breve tra le due superfici (non tra i centri).
    Basata su BVHTree di obj_b, samples di obj_a.
    Ritorna mm.
    """
    dg = bpy.context.evaluated_depsgraph_get()
    bvh_b = BVHTree.FromObject(obj_b, dg)
    
    bm_a = _bm_from_obj(obj_a, evaluated=True)
    min_dist = float('inf')
    for v in bm_a.verts:
        _, _, _, d = bvh_b.find_nearest(v.co)
        if d is not None and d < min_dist:
            min_dist = d
    bm_a.free()
    
    result_mm = min_dist * BU_TO_MM
    print(f"[DIST] {obj_a.name} ↔ {obj_b.name}: {result_mm:.3f} mm")
    return result_mm
```

### Dimensioni bounding

```python
def bbox_world_mm(obj):
    """
    AABB in world space (allineato agli assi del mondo).
    Ritorna (min_v, max_v, dims) in mm.
    """
    mw = obj.matrix_world
    corners = [mw @ Vector(c) for c in obj.bound_box]
    minv = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    maxv = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    dims = (maxv - minv) * BU_TO_MM
    minv_mm = minv * BU_TO_MM
    maxv_mm = maxv * BU_TO_MM
    print(f"[BBOX-W] {obj.name}: dims={dims.x:.2f}×{dims.y:.2f}×{dims.z:.2f} mm")
    print(f"[BBOX-W] {obj.name}: min={minv_mm[:]} max={maxv_mm[:]}")
    return minv_mm, maxv_mm, dims


def bbox_local_mm(obj):
    """
    AABB nel frame locale dell'oggetto (obj.dimensions).
    Più affidabile se obj non ha rotazione applicata e serve misurare la "dimensione effettiva" della mesh indipendentemente dall'orientamento.
    """
    d = obj.dimensions
    dims_mm = Vector((d.x, d.y, d.z)) * BU_TO_MM
    print(f"[BBOX-L] {obj.name}: dims={dims_mm.x:.2f}×{dims_mm.y:.2f}×{dims_mm.z:.2f} mm")
    return dims_mm
```

### Oriented bounding box (OBB) via PCA

Utile per misurare la "forma lunga" di una mesh ruotata (quando AABB sovra-stima).

```python
import numpy as np

def obb_mm(obj):
    """
    Oriented BBox via PCA sui vertici.
    Ritorna (dims_mm, axes_world_vectors).
    """
    mw = obj.matrix_world
    verts = np.array([(mw @ v.co)[:] for v in obj.data.vertices])
    
    center = verts.mean(axis=0)
    centered = verts - center
    cov = np.cov(centered.T)
    eigvals, eigvecs = np.linalg.eigh(cov)   # eigvals ordinati ascendente
    # Riordina eigvecs per eigvals descending (asse principale primo)
    order = np.argsort(-eigvals)
    axes = eigvecs[:, order]   # columns are axes
    
    projected = centered @ axes
    min_p = projected.min(axis=0)
    max_p = projected.max(axis=0)
    dims = (max_p - min_p) * BU_TO_MM
    
    axes_vec = [Vector(axes[:, i]) for i in range(3)]
    
    print(f"[OBB] {obj.name}: dims={dims[0]:.2f}×{dims[1]:.2f}×{dims[2]:.2f} mm")
    return dims, axes_vec
```

---

## 4. Wall thickness — raycast da faccia

**Algoritmo**: per ogni faccia campionata, ray-cast dal centro della faccia lungo `-normal` all'interno della mesh; la distanza al primo hit è lo spessore locale della parete.

```python
def wall_thickness_at_point(obj, point_world, normal_world):
    """
    Misura lo spessore di parete partendo da un punto in world space lungo -normale.
    Ritorna mm, oppure None se nessun hit (mesh aperta o raggio esce).
    """
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(obj, dg)
    
    # Partire leggermente sotto la superficie per non colpire la faccia di origine
    eps = 0.00001   # 10 μm in BU
    origin = point_world - normal_world * eps
    direction = -normal_world.normalized()
    
    loc, n, idx, dist = bvh.ray_cast(origin, direction)
    if loc is None:
        return None
    return dist * BU_TO_MM


def wall_thickness_distribution(obj, samples=500):
    """
    Campiona N facce della mesh, misura thickness per ognuna.
    Ritorna dict con min, max, p10, p50, p90, N valid, N invalid (ray miss).
    """
    import random
    
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(obj, dg)
    mw = obj.matrix_world
    normal_matrix = mw.to_3x3().inverted().transposed()   # per trasformare normali correttamente
    
    polys = obj.data.polygons
    if len(polys) == 0:
        raise ValueError("Empty mesh")
    
    n_samples = min(samples, len(polys))
    sampled_polys = random.sample(list(polys), n_samples)
    
    thicknesses = []
    invalid = 0
    for p in sampled_polys:
        center_world = mw @ p.center
        normal_world = (normal_matrix @ p.normal).normalized()
        eps = 0.00001
        origin = center_world - normal_world * eps
        direction = -normal_world
        loc, n, idx, dist = bvh.ray_cast(origin, direction)
        if loc is None or dist is None:
            invalid += 1
            continue
        thicknesses.append(dist * BU_TO_MM)
    
    if not thicknesses:
        return {"valid": 0, "invalid": invalid, "min": None, "max": None,
                "p10": None, "p50": None, "p90": None}
    
    thicknesses.sort()
    n = len(thicknesses)
    
    def pct(p):
        k = int(p / 100 * (n - 1))
        return thicknesses[k]
    
    report = {
        "valid": n,
        "invalid": invalid,
        "min": thicknesses[0],
        "max": thicknesses[-1],
        "p10": pct(10),
        "p50": pct(50),
        "p90": pct(90),
    }
    print(f"[THICKNESS] {obj.name}: min={report['min']:.2f} p10={report['p10']:.2f} "
          f"p50={report['p50']:.2f} p90={report['p90']:.2f} max={report['max']:.2f} mm")
    print(f"[THICKNESS] valid={n}/{n+invalid}")
    return report
```

**Interpretazione FDM**:

| Soglia | Significato | Azione consigliata |
|---|---|---|
| p10 < 0.4 mm | Zone più sottili del nozzle | Solidify minimo (impossibile da stampare) |
| p10 < 0.8 mm | Sotto 2 perimetri | Attenzione; Arachne può aiutare |
| p10 ≥ 0.8 mm e p50 ≥ 1.2 mm | Accettabile standard FDM | Procedi |
| invalid > 10% | Mesh aperta / non-manifold | Repair prima di riproporre la misura |

---

## 5. Volume, massa, superficie

```python
def volume_mm3(obj):
    """
    Volume della mesh chiusa in mm³.
    Richiede mesh manifold — altrimenti il valore è indefinito (bm.calc_volume ritorna in ogni caso un numero, ma privo di significato).
    """
    bm = _bm_from_obj(obj)
    # calc_volume vuole mesh chiusa; verifica boundary
    is_closed = all(e.is_manifold for e in bm.edges)
    vol_bu3 = bm.calc_volume(signed=False)
    bm.free()
    vol_mm3 = vol_bu3 * (BU_TO_MM ** 3)   # = × 1e9
    print(f"[VOL] {obj.name}: {vol_mm3:.2f} mm³ = {vol_mm3/1000:.3f} cm³ (closed={is_closed})")
    return vol_mm3, is_closed


def surface_area_mm2(obj):
    """Area superficiale totale in mm²."""
    bm = _bm_from_obj(obj)
    area_bu2 = sum(f.calc_area() for f in bm.faces)
    bm.free()
    area_mm2 = area_bu2 * (BU_TO_MM ** 2)
    print(f"[AREA] {obj.name}: {area_mm2:.2f} mm² = {area_mm2/100:.2f} cm²")
    return area_mm2


def estimate_pla_mass_g(obj, infill_pct=15.0, wall_thickness_mm=1.2, density_g_cm3=1.24):
    """
    Stima massa PLA per preventivo filamento.
    NON è esatta — è un'approssimazione basata su:
      mass ≈ (volume_shell + volume_infill * infill_pct) * density
    shell = superficie × wall_thickness
    infill_volume = (volume_totale - volume_shell)
    """
    vol_mm3, is_closed = volume_mm3(obj)
    if not is_closed:
        print("[MASS] warning: mesh non-manifold, stima inaffidabile")
    area_mm2 = surface_area_mm2(obj)
    
    # Volume shell (approssimazione: A × t; sovrastima su mesh molto curve)
    shell_vol = area_mm2 * wall_thickness_mm    # mm³
    shell_vol = min(shell_vol, vol_mm3 * 0.6)   # cap a 60% del volume totale (sanity)
    infill_vol = max(vol_mm3 - shell_vol, 0.0) * (infill_pct / 100.0)
    total_plastic_vol_mm3 = shell_vol + infill_vol
    total_plastic_vol_cm3 = total_plastic_vol_mm3 / 1000.0
    mass_g = total_plastic_vol_cm3 * density_g_cm3
    
    print(f"[MASS] {obj.name}: shell≈{shell_vol/1000:.2f}cm³ infill≈{infill_vol/1000:.2f}cm³ "
          f"→ mass≈{mass_g:.1f} g (infill={infill_pct}%, wall={wall_thickness_mm}mm)")
    return mass_g
```

**Caveat**: per il preventivo reale di filamento usare Bambu Studio dopo lo slice — la stima qui è puramente indicativa (errore tipico ±20%).

---

## 6. Center of mass / center of volume

```python
def center_of_volume_mm(obj):
    """
    Centro di volume via tetra integration (esatto per mesh chiusa).
    Ritorna Vector in world-mm.
    """
    bm = _bm_from_obj(obj)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    
    total_vol = 0.0
    weighted_centroid = Vector((0, 0, 0))
    
    for f in bm.faces:
        v0, v1, v2 = [v.co for v in f.verts[:3]]
        # Volume del tetraedro origine–v0–v1–v2 (signed)
        tet_vol = v0.dot(v1.cross(v2)) / 6.0
        tet_centroid = (v0 + v1 + v2) / 4.0   # centroide tetraedro con origine
        total_vol += tet_vol
        weighted_centroid += tet_centroid * tet_vol
    
    bm.free()
    
    if abs(total_vol) < 1e-12:
        raise ValueError("Degenerate volume (possibly open mesh)")
    
    com = weighted_centroid / total_vol
    com_mm = com * BU_TO_MM
    print(f"[CoV] {obj.name}: ({com_mm.x:.2f}, {com_mm.y:.2f}, {com_mm.z:.2f}) mm")
    return com_mm


def center_of_bbox_mm(obj):
    """Centro del bounding box world-aligned — fallback veloce se la mesh non è chiusa."""
    minv, maxv, _ = bbox_world_mm(obj)
    c = (minv + maxv) / 2
    print(f"[CoBBox] {obj.name}: ({c.x:.2f}, {c.y:.2f}, {c.z:.2f}) mm")
    return c
```

**Quando usare quale**:
- Mesh manifold chiusa: `center_of_volume_mm` (corretto fisicamente).
- Mesh aperta o non-manifold: `center_of_bbox_mm` (solo geometrico).
- Per stabilità stampa (orientamento): vedere `[orientation_strategy]` — usa CoV + bottom_flatness.

---

## 7. Cross-section area a un piano

```python
def cross_section_area_mm2(obj, plane_co_mm, plane_no):
    """
    Area della sezione trasversale della mesh a un piano.
    plane_co_mm: Vector punto su piano in mm (world).
    plane_no: Vector normale al piano (non serve normalizzare).
    Ritorna area in mm².
    """
    plane_co_bu = Vector(plane_co_mm) / BU_TO_MM
    plane_no = Vector(plane_no).normalized()
    
    bm = _bm_from_obj(obj)
    # Bisect e tieni solo la sezione
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    cut = bmesh.ops.bisect_plane(
        bm,
        geom=geom,
        plane_co=plane_co_bu,
        plane_no=plane_no,
        clear_inner=True,
        clear_outer=True,
    )
    
    # Gli edge lungo il taglio
    cut_edges = [e for e in cut['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    
    # Riempi con n-gon per calcolare area
    if not cut_edges:
        bm.free()
        return 0.0
    
    fill = bmesh.ops.edgenet_fill(bm, edges=cut_edges)
    area_bu2 = sum(f.calc_area() for f in fill.get('faces', []))
    area_mm2 = area_bu2 * (BU_TO_MM ** 2)
    
    bm.free()
    print(f"[CROSS] area @ plane = {area_mm2:.2f} mm²")
    return area_mm2
```

---

## 8. Hole / cylinder feature detection

Rileva feature cilindriche (fori passanti, boss) misurando diametro da edge loop.

```python
def detect_circular_holes(obj, min_radius_mm=1.0, max_radius_mm=30.0):
    """
    Trova edge loops approssimativamente circolari (buchi, boss, fori) nella mesh.
    Ritorna lista di dict {center_mm, radius_mm, normal, n_verts}.
    Heuristica: loop chiuso con varianza radiale < 10% della media.
    """
    bm = _bm_from_obj(obj)
    
    # Trova i boundary loops (edge loops con non-manifold boundary=False; qui cerchiamo edge loops planari interni)
    # Semplificazione: analizza tutti i closed edge loops che hanno solo vertici con 3+ edge
    
    # Approccio pragmatico: prendi facce con >3 lati che sembrano circolari
    candidates = []
    for f in bm.faces:
        n_verts = len(f.verts)
        if n_verts < 6:
            continue
        center = f.calc_center_median()
        radii = [(v.co - center).length for v in f.verts]
        mean_r = sum(radii) / len(radii)
        if mean_r <= 0:
            continue
        variance = sum((r - mean_r) ** 2 for r in radii) / len(radii)
        cv = (variance ** 0.5) / mean_r   # coefficient of variation
        if cv > 0.1:
            continue
        r_mm = mean_r * BU_TO_MM
        if not (min_radius_mm <= r_mm <= max_radius_mm):
            continue
        candidates.append({
            "center_mm": center * BU_TO_MM,
            "radius_mm": r_mm,
            "diameter_mm": 2 * r_mm,
            "normal": f.normal.copy(),
            "n_verts": n_verts,
            "cv": cv,
        })
    
    bm.free()
    
    # Dedup per centro vicino
    dedup = []
    for c in candidates:
        dup = False
        for d in dedup:
            if (c["center_mm"] - d["center_mm"]).length < 1.0:    # <1mm = stesso foro
                dup = True
                break
        if not dup:
            dedup.append(c)
    
    print(f"[HOLES] found {len(dedup)} circular features")
    for h in dedup:
        print(f"  Ø{h['diameter_mm']:.2f}mm @ ({h['center_mm'].x:.1f},{h['center_mm'].y:.1f},{h['center_mm'].z:.1f})")
    return dedup
```

Limitazione: questa euristica funziona solo se il foro è rappresentato come **un'unica n-gon** (non triangolato). Dopo triangulate va applicato `tris_convert_to_quads` o usato un algoritmo di loop detection più sofisticato (fuori scope).

---

## 9. Angoli e orientamenti

```python
def dihedral_angle_deg(f1_obj, f2_obj, f1_idx, f2_idx):
    """Angolo tra due facce identificate da indice nelle rispettive mesh."""
    mw1 = f1_obj.matrix_world.to_3x3()
    mw2 = f2_obj.matrix_world.to_3x3()
    n1 = (mw1 @ f1_obj.data.polygons[f1_idx].normal).normalized()
    n2 = (mw2 @ f2_obj.data.polygons[f2_idx].normal).normalized()
    ang = math.degrees(n1.angle(n2))
    print(f"[ANGLE] faces {f1_idx}↔{f2_idx}: {ang:.2f}°")
    return ang


def tilt_from_z_deg(obj, face_idx):
    """Quanto è inclinata una faccia rispetto al piano del bed (Z up)."""
    mw = obj.matrix_world.to_3x3()
    n = (mw @ obj.data.polygons[face_idx].normal).normalized()
    # angolo con asse +Z
    ang_z = math.degrees(n.angle(Vector((0, 0, 1))))
    print(f"[TILT] face {face_idx}: {ang_z:.2f}° from +Z")
    return ang_z
```

---

## 10. Report sintetico — `measure_object_full()`

Unica CALL che esegue tutte le misure pertinenti per stampa FDM e ritorna un report.

```python
def measure_object_full(obj, thickness_samples=500):
    """
    Report completo per FDM. Usare in QA / preprint_validation.
    """
    report = {"name": obj.name}
    
    # Dims
    dims_local = bbox_local_mm(obj)
    report["dims_local_mm"] = tuple(dims_local)
    minv, maxv, dims_w = bbox_world_mm(obj)
    report["dims_world_mm"] = tuple(dims_w)
    report["bbox_min_mm"] = tuple(minv)
    report["bbox_max_mm"] = tuple(maxv)
    
    # Volume + area + mass estimate
    vol, closed = volume_mm3(obj)
    report["volume_mm3"] = vol
    report["is_closed"] = closed
    report["surface_mm2"] = surface_area_mm2(obj)
    if closed:
        report["pla_mass_g_15infill"] = estimate_pla_mass_g(obj, infill_pct=15.0)
    
    # Thickness distribution
    th = wall_thickness_distribution(obj, samples=thickness_samples)
    report["thickness"] = th
    
    # CoV se chiuso
    if closed:
        try:
            com = center_of_volume_mm(obj)
            report["center_of_volume_mm"] = tuple(com)
        except Exception as e:
            report["center_of_volume_mm"] = None
    
    # Poly count
    report["verts"] = len(obj.data.vertices)
    report["polys"] = len(obj.data.polygons)
    
    print(f"[MEASURE-FULL] report:")
    for k, v in report.items():
        print(f"  {k}: {v}")
    return report
```

---

## 11. Integrazione con altre parti della KB

- `[mesh_quality_assessment]` → per le metriche di **qualità** (non-manifold count, zero area, boundary).
- `[orientation_strategy]` → usa CoV + bbox + thickness per scoring di orientamento.
- `[preprint_validation]` → usa `measure_object_full()` come fonte primaria.
- `[scale_detection]` → usa `bbox_local_mm()` per diagnosi di scala.
- `[mathutils]` → riferimento API base (Vector, Matrix, BVHTree, KDTree).

---

## 12. Caveat numerici

- Blender usa **float32** nelle mesh (vertici, normali). Misure sotto 10 μm sono al di sotto della precisione utile.
- `bm.calc_volume()` è signed se `signed=True` — segno negativo indica mesh "inside-out" (normali flipped).
- BVHTree.ray_cast può restituire `(None, None, None, None)` se il raggio manca — sempre testare `loc is None`.
- Su mesh con **shape keys** o **modifier non applicati**, usare `evaluated=True` in `_bm_from_obj` per ottenere la geometria finale, altrimenti si misura solo la base mesh.
- `obj.dimensions` **non include i modifier**; per includerli usa `evaluated_get(depsgraph).to_mesh()` (vedi `[depsgraph_evaluated]`).
