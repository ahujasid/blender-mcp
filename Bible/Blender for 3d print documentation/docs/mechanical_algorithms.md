# Algoritmi di ingegneria meccanica in Blender / BMesh

Fonte: ricerca "Refactoring Algoritmico e Ingegneria Meccanica nella Generazione Geometrica in Blender BMesh".
Uso: generare proceduralmente ingranaggi, alberi, parti con tolleranze ISO 286, calcolare proprietà fisiche (volume, centro di massa, OBB), applicare pattern robusti di escalation per operazioni booleane.

Questo file raccoglie algoritmi matematici e pattern di codice per trasformare Blender da tool estetico a motore di generazione CAD meccanica. Usa solo `math` nativo e `bmesh`/`mathutils` per massima portabilità; NumPy è un plus per vettorizzazione.

---

## 1. Ingranaggi ad evolvente di cerchio

### Perché evolvente e non trapezi/cicloidali

L'evolvente mantiene **rapporto di velocità costante** anche con piccole variazioni di interasse tra alberi. È lo standard ISO 53. Una coppia di ingranaggi ad evolvente trasmette moto fluido con contatto in un singolo punto che si sposta lungo una linea retta (*line of action*).

### Parametri meccanici standard (ISO 53)

| Parametro | Simbolo | Formula | Valore tipico |
|---|---|---|---|
| Modulo | $m$ | $p / \pi$ | 0.5 / 1 / 1.5 / 2 mm |
| Passo primitivo | $p$ | $\pi \cdot m$ | derivato |
| Angolo di pressione | $\alpha$ | — | 20° (ISO 53) |
| Raggio primitivo | $r_p$ | $m \cdot Z / 2$ ($Z$=denti) | — |
| Raggio di base | $r_b$ | $r_p \cdot \cos(\alpha)$ | — |
| Addendum | $h_a$ | $1.00 \cdot m$ | — |
| Dedendum | $h_f$ | $1.25 \cdot m$ | — |
| Altezza totale | $h$ | $2.25 \cdot m$ | — |

### Parametrizzazione curva evolvente

Per un punto sulla curva, dato angolo di rotolamento $t$ in radianti:

$$x(t) = r_b \cdot (\cos(t) + t \cdot \sin(t))$$
$$y(t) = r_b \cdot (\sin(t) - t \cdot \cos(t))$$

La curva è definita **solo per $r \geq r_b$**. Sotto il cerchio di base (zona di sottotaglio) va gestita separatamente con linea radiale o curva trocoidale.

### Implementazione BMesh senza NumPy

```python
import math
import bmesh

def generate_involute_gear(
    num_teeth: int,
    module: float,
    pressure_angle_deg: float = 20.0,
    width: float = 5.0,
    samples_per_flank: int = 16,
) -> bmesh.types.BMesh:
    """Genera ingranaggio dritto ad evolvente come BMesh pronto per estrusione."""
    alpha = math.radians(pressure_angle_deg)
    r_p = module * num_teeth / 2.0              # raggio primitivo
    r_b = r_p * math.cos(alpha)                  # raggio base
    r_a = r_p + module                           # raggio testa (addendum)
    r_f = r_p - 1.25 * module                    # raggio radice (dedendum)
    
    # Angolo massimo parametrico per arrivare a r_a
    t_max = math.sqrt((r_a / r_b) ** 2 - 1.0)
    
    # Larghezza dente al primitivo (metà passo)
    angular_tooth_width = math.pi / num_teeth
    
    bm = bmesh.new()
    angle_per_tooth = 2.0 * math.pi / num_teeth
    
    # Genera profilo del dente (mezzo + mirror)
    def involute_point(t: float) -> tuple:
        return (
            r_b * (math.cos(t) + t * math.sin(t)),
            r_b * (math.sin(t) - t * math.cos(t)),
        )
    
    tooth_points = []
    for i in range(samples_per_flank + 1):
        t = t_max * i / samples_per_flank
        tooth_points.append(involute_point(t))
    
    # TODO: applicare offset angolare, mirror per creare il dente completo,
    #       ripetere per num_teeth, gestire zona r < r_b con raccordo radiale,
    #       creare face inferiore, estrudere per `width`.
    
    return bm
```

**Strategie refactoring per sottotaglio:** se $Z < 17$ (con $\alpha = 20°$), $r_f < r_b$. Options:
- Linea radiale tra radice e cerchio di base (veloce, approssimato)
- Curva trocoidale (percorso utensile creatore) — accurato, più complesso da parametrizzare
- Profile shift (positive addendum modification): spostare il profilo in direzione radiale per mantenere $r_f \geq r_b$

---

## 2. Boolean robusto — escalation pattern

Il fallimento di un boolean non è accettabile in produzione. Implementare *escalation automatica*:

```python
import bpy

def robust_boolean(
    base_obj,
    cutter_obj,
    operation: str = "DIFFERENCE",
    self_jitter: float = 1e-6,
) -> bool:
    """Prova FLOAT → EXACT → EXACT+hole_tolerant → jitter+EXACT. Ritorna True se successo."""
    
    attempts = [
        {"solver": "FLOAT", "use_self": False, "use_hole_tolerant": False},
        {"solver": "EXACT", "use_self": False, "use_hole_tolerant": False},
        {"solver": "EXACT", "use_self": True,  "use_hole_tolerant": True},
    ]
    
    for i, cfg in enumerate(attempts):
        mod = base_obj.modifiers.new(f"bool_try_{i}", type="BOOLEAN")
        mod.operation = operation
        mod.object = cutter_obj
        mod.solver = cfg["solver"]
        mod.use_self = cfg["use_self"]
        if cfg["solver"] == "EXACT":
            mod.use_hole_tolerant = cfg["use_hole_tolerant"]
        
        # Applica e valida
        bpy.ops.object.select_all(action="DESELECT")
        base_obj.select_set(True)
        bpy.context.view_layer.objects.active = base_obj
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except RuntimeError:
            base_obj.modifiers.remove(mod)
            continue
        
        # Validazione post-op
        if base_obj.data.validate(verbose=False):
            # validate ha dovuto correggere qualcosa → mesh sospetta
            pass
        if len(base_obj.data.polygons) > 0 and _volume_sanity_check(base_obj):
            return True
    
    # Ultimo tentativo: jitter geometrico
    cutter_obj.location.x += self_jitter
    mod = base_obj.modifiers.new("bool_jittered", type="BOOLEAN")
    mod.operation = operation
    mod.object = cutter_obj
    mod.solver = "EXACT"
    mod.use_hole_tolerant = True
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return True
    except RuntimeError:
        return False


def _volume_sanity_check(obj) -> bool:
    """True se il volume è positivo e non NaN."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    vol = bm.calc_volume(signed=False)
    bm.free()
    return vol > 0 and not (vol != vol)  # non NaN
```

**Tassonomia solver (aggiornata 5.1):**

| Solver | Overlap/complanari | Performance | Quando |
|---|---|---|---|
| `FLOAT` (ex `FAST`) | ❌ | Elevate | Solidi semplici, no facce complanari |
| `EXACT` | ✅ | Moderate | Default sicuro per CAD |
| `MANIFOLD` | ✅ (parziale) | Molto elevate | Entrambi solidi chiusi |

Vedi `boolean_troubleshooting.md` per troubleshooting esteso e `api_migration_5x.md` per il rename `FAST → FLOAT`.

---

## 3. Valutazione spessore parete

### Raycasting (veloce, approssimato)

Algoritmo: per ogni vertice/face center, sparare raggio lungo normale invertita; distanza alla prima collisione = spessore locale.

```python
import bpy
from mathutils import Vector

def wall_thickness_raycast(obj, sample_stride: int = 1) -> dict:
    """Ritorna dict face_index → thickness (None se no hit)."""
    bvh = _make_bvh(obj)  # BVHTree.FromObject(obj, depsgraph)
    thickness = {}
    for i, poly in enumerate(obj.data.polygons):
        if i % sample_stride != 0:
            continue
        origin = obj.matrix_world @ poly.center
        direction = -poly.normal.to_4d()
        direction.w = 0
        direction = (obj.matrix_world @ direction).to_3d().normalized()
        
        # offset origine di ε verso l'interno per non colpire sé stesso
        epsilon = 1e-5
        hit_loc, hit_normal, hit_idx, hit_dist = bvh.ray_cast(
            origin + direction * epsilon, direction
        )
        thickness[i] = hit_dist if hit_dist is not None else None
    return thickness
```

**Limitazioni:** in prossimità di curvature elevate o angoli acuti la normale non punta necessariamente alla parete opposta più vicina. Workaround: cono di raggi (stochastic sampling in cono di 10°), prendere il minimo.

### Asse mediale (Medial Axis Transform)

L'Asse Mediale è l'insieme dei punti che hanno ≥ 2 punti più vicini sulla superficie. Cattura **scheletro + spessore** (raggio della sfera inscritta massima per ogni punto).

**Pro:** separa informazione di spessore da orientazione; abilita deformazioni ARAP (as-rigid-as-possible) che preservano volume.
**Contro:** computazionalmente pesante; sensibile a rumore topologico.

**Non implementato nativamente in Blender.** Per uso serio, integrare via subprocess con tool esterni (CGAL, VoxelArt, o skeleton_3d Python).

Raccomandazione pratica: raycasting per verifica real-time in Blender, medial axis solo per analisi finale di integrità strutturale.

Vedi `measurement_toolkit.md` §thickness per pattern completi.

---

## 4. Proprietà fisiche con BMesh

### Volume signed vs unsigned

```python
import bmesh

def compute_volume_mm3(obj, scene_unit_scale: float = 0.001) -> float:
    """Ritorna volume in mm³ da object evaluato. Richiede mesh manifold + normals outward."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)  # volume in world space
    vol_bu = bm.calc_volume(signed=False)
    bm.free()
    # 1 BU = 1 m a scene_unit_scale=1.0, 1 BU = 1 mm a scene_unit_scale=0.001
    return vol_bu * (scene_unit_scale * 1000.0) ** 3
```

**Pitfall critico:** `calc_volume(signed=True)` restituisce valore negativo se normali sono flipped. Un volume "sommatorio" negativo indica normali invertite globalmente → `bpy.ops.mesh.normals_make_consistent(inside=False)` prima del calcolo.

### Massa

Data densità $\rho$ del materiale (PLA ≈ 1.24 g/cm³):

```python
def compute_mass_grams(obj, density_g_cm3: float, scene_unit_scale: float = 0.001) -> float:
    vol_mm3 = compute_volume_mm3(obj, scene_unit_scale)
    vol_cm3 = vol_mm3 / 1000.0
    return vol_cm3 * density_g_cm3
```

**Densità comuni (g/cm³):**

| Materiale | ρ |
|---|---|
| PLA | 1.24 |
| PETG | 1.27 |
| ABS | 1.04 |
| TPU 95A | 1.21 |
| PA-CF | 1.10 |

### Centro di massa

Per densità uniforme, CoM = centroide volumetrico = media pesata dei centroidi dei tetraedri formati da ogni faccia con l'origine:

$$C = \frac{\sum_i V_i \cdot R_i}{\sum_i V_i}$$

```python
import bmesh
from mathutils import Vector

def center_of_mass(obj) -> Vector:
    """CoM in coordinate mondo, densità uniforme, mesh manifold + outward normals."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    
    total_vol = 0.0
    weighted = Vector((0.0, 0.0, 0.0))
    for f in bm.faces:
        # Triangolate il poligono come fan attorno al primo vertice
        verts = [l.vert.co for l in f.loops]
        v0 = verts[0]
        for i in range(1, len(verts) - 1):
            a, b, c = v0, verts[i], verts[i + 1]
            # Volume tetraedro con origine in (0,0,0)
            v_tet = a.dot(b.cross(c)) / 6.0
            # Centroide tetraedro
            centroid = (a + b + c) / 4.0
            total_vol += v_tet
            weighted += centroid * v_tet
    
    bm.free()
    if abs(total_vol) < 1e-12:
        return Vector((0, 0, 0))
    return weighted / total_vol
```

Uso operativo: posizionare `obj.origin_set(type='ORIGIN_CENTER_OF_VOLUME')` come utility MCP, o spostare pivot al CoM fisico per simulazioni dinamiche (ODE, AGX).

---

## 5. Oriented Bounding Box (OBB)

Differenza con AABB (axis-aligned): OBB si adatta all'orientamento naturale dell'oggetto, minimizzando volume vuoto.

### Algoritmo dei Calibri Rotanti

Teorema di Freeman & Shapira: almeno un lato del rettangolo di area minima deve essere collineare a un edge del convex hull.

**Complessità:** 2D $O(n)$ dopo hull; 3D esatto $O(n^3)$ (O'Rourke) — spesso impraticabile.

### Implementazione pratica 3D (proiezione sulle facce del hull)

```python
import bmesh
from mathutils import Matrix, Vector

def compute_obb_via_convex_hull(obj) -> tuple:
    """Ritorna (center, axes_matrix_3x3, dimensions). Approssimazione hull-face."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    
    # Convex hull riduce drasticamente il dominio di ricerca
    hull_result = bmesh.ops.convex_hull(bm, input=bm.verts)
    hull_faces = [g for g in hull_result["geom"] if isinstance(g, bmesh.types.BMFace)]
    
    best_volume = float("inf")
    best_config = None
    
    for f in hull_faces:
        # Asse Z dell'OBB = normale della face
        z_axis = f.normal.normalized()
        # Asse X = edge di riferimento proiettato
        edge0 = (f.verts[1].co - f.verts[0].co).normalized()
        x_axis = edge0 - edge0.dot(z_axis) * z_axis
        x_axis.normalize()
        y_axis = z_axis.cross(x_axis).normalized()
        
        R = Matrix((x_axis, y_axis, z_axis)).transposed()
        R_inv = R.transposed()  # R è ortonormale
        
        # Proietta tutti i vertici nel frame locale
        mins = Vector((float("inf"),) * 3)
        maxs = Vector((float("-inf"),) * 3)
        for v in bm.verts:
            local = R_inv @ v.co
            for i in range(3):
                mins[i] = min(mins[i], local[i])
                maxs[i] = max(maxs[i], local[i])
        
        dims = maxs - mins
        volume = dims.x * dims.y * dims.z
        
        if volume < best_volume:
            best_volume = volume
            center_local = (mins + maxs) * 0.5
            best_config = (R @ center_local, R, dims)
    
    bm.free()
    return best_config
```

**Tabella metodi:**

| Metodo | Accuratezza | Complessità | Uso |
|---|---|---|---|
| AABB | Bassa | $O(n)$ | Preview rapida, culling |
| PCA OBB | Media | $O(n)$ | Casi generali |
| Rotating Calipers (hull-face) | Alta | $O(f \cdot n)$ | Packing, tolleranze |
| O'Rourke esatto | Massima | $O(n^3)$ | Ricerca teorica |

Uso pratico per Bambu Studio: OBB minimo → orientamento ottimale su piatto (`object_placement_alignment.md` + `orientation_strategy.md`).

---

## 6. Tolleranze ISO 286

Sistema di accoppiamento: codice tipo **`H7/g6`**.
- Lettera maiuscola = foro, minuscola = albero
- Lettera definisce **deviazione fondamentale** (posizione zona rispetto al nominale)
- Numero = grado IT (International Tolerance) → **ampiezza zona**

### Tabella deviazione fondamentale per alberi (subset comune)

Per albero di diametro nominale $d$ in mm, deviazione fondamentale $e_s$ in μm:

| Lettera | Deviazione (qualitativa) | Uso tipico |
|---|---|---|
| `h` | 0 (coincide con nominale) | Riferimento |
| `g` | Lieve offset negativo | Slide fit |
| `f` | Offset negativo medio | Free running |
| `e` | Offset maggiore | Loose running |
| `k`, `m`, `p` | Offset positivo (interferenza) | Press fit |

### Tabella IT grade (ampiezza in μm) per range dimensione nominale

| Range d (mm) | IT6 | IT7 | IT8 | IT9 |
|---|---|---|---|---|
| 1–3 | 6 | 10 | 14 | 25 |
| 3–6 | 8 | 12 | 18 | 30 |
| 6–10 | 9 | 15 | 22 | 36 |
| 10–18 | 11 | 18 | 27 | 43 |
| 18–30 | 13 | 21 | 33 | 52 |
| 30–50 | 16 | 25 | 39 | 62 |
| 50–80 | 19 | 30 | 46 | 74 |

### Implementazione vertex offset

Per generare un albero di diametro nominale $d_n = 50$ mm con tolleranza `g6`:

```python
import numpy as np

def iso286_offset_shaft(obj, nominal_diameter_mm: float,
                        letter: str, grade: int) -> None:
    """Applica offset radiale ai vertici per conformità ISO 286 (albero)."""
    fundamental_dev = _lookup_fundamental_deviation(letter, nominal_diameter_mm)  # μm
    it_range = _lookup_it_grade(grade, nominal_diameter_mm)                       # μm
    
    # Albero: zona di tolleranza è sotto o intorno al nominale
    # Per "g6": deviation fondamentale negativa, zona spessa it_range
    delta_radius_mm = (fundamental_dev + it_range / 2.0) / 1000.0  # μm → mm
    
    # Offset vettoriale lungo normali vertex
    mesh = obj.data
    n = len(mesh.vertices)
    coords = np.empty(n * 3, dtype=np.float32)
    normals = np.empty(n * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", coords)
    mesh.vertices.foreach_get("normal", normals)
    coords = coords.reshape(-1, 3)
    normals = normals.reshape(-1, 3)
    
    coords += normals * delta_radius_mm
    
    mesh.vertices.foreach_set("co", coords.ravel())
    mesh.update()
```

**Pitfall:** su mesh con spigoli vivi (chamfer, fillet), le normali al vertice sono medie pesate → offset distorce il profilo. Soluzioni:
- Usare normale per **loop** (`MeshLoop.normal`) se spigoli vivi presenti
- Applicare *shell*: moltiplicatore basato su `vertex.sharpness` (1.0 su smooth, fattore maggiore su spigoli)
- Preferire modifier `Solidify` con `use_even_offset=True` per uniformità geometrica

### Compensazione produzione (FDM vs ISO)

Le tolleranze ISO 286 sono pensate per CNC con precisione ~±10 μm. FDM ha precisione ~±100 μm. Per Bambu A1 vedi `bambu_a1_physical_constants.md` §tolleranze (0.1/0.2/0.3 mm fits).

---

## 7. BMesh — custom data layers per metadati meccanici

BMesh supporta layer per associare metadati direttamente alla geometria:

| Layer | Uso meccanico |
|---|---|
| `edge.layers.crease` | Edge da mantenere vivi in SubSurf |
| `vert.layers.deform` | Pesi per simulazione FEM esterna |
| `face.layers.int` | Material ID custom |
| `face.layers.string` | Tag testuali (es. "critical_load") |

```python
import bmesh

def tag_load_zones(bm: bmesh.types.BMesh, face_indices: list, tag: str):
    tag_layer = bm.faces.layers.string.get("load_tag") or \
                bm.faces.layers.string.new("load_tag")
    bm.faces.ensure_lookup_table()
    for idx in face_indices:
        bm.faces[idx][tag_layer] = tag.encode()
```

Utile per esportazione verso FEM esterni (ABAQUS, CalculiX) dove zone di carico devono essere identificate.

---

## 8. Best practice per refactoring

### Gestione memoria BMesh

```python
bm = bmesh.new()
try:
    bm.from_mesh(obj.data)
    # ... operazioni ...
    bm.to_mesh(obj.data)
    obj.data.update()
finally:
    bm.free()  # SEMPRE, anche su eccezione
```

Mai fare `bm.to_mesh()` senza `bm.free()` subito dopo — leak persiste tra chiamate MCP.

### Stato mesh corretto prima di to_mesh

Prima di `bm.to_mesh`:
1. `bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)` — pulizia duplicati
2. Verificare nessuna faccia con < 3 vertici
3. Selezione coerente: se face selezionata, tutti i suoi verts + edges devono essere selezionati

---

## Cross-reference

- `bisect_and_splitting.md` — `bisect_plane` per slicing ingranaggi
- `boolean_troubleshooting.md` — escalation FLOAT → EXACT dettagliato
- `measurement_toolkit.md` — thickness raycast, CoM, dimensions
- `cad_import_workflow.md` — vettorizzazione `foreach_get/set`
- `api_migration_5x.md` — rename solver FAST → FLOAT
- `bambu_a1_physical_constants.md` — fits PLA (0.1/0.2/0.3 mm)
- `functional_patterns_library.md` — pattern di generazione parametrica
