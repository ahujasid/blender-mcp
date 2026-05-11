# Blender mathutils — Math Utilities per Mesh 3D

Fonte: Blender Python API 5.x — `mathutils`, `mathutils.geometry`, `mathutils.bvhtree`, `mathutils.kdtree`
Contesto: operazioni matematiche per scripting mesh e analisi stampa 3D FDM.

---

## Vector (`mathutils.Vector`)

**Costruzione:**

```python
from mathutils import Vector

v = Vector((1.0, 2.0, 3.0))   # 3D
v2 = Vector((1.0, 2.0))        # 2D
v4 = Vector((1.0, 2.0, 3.0, 1.0))  # 4D (homogeneous)

# Metodi classmethod
Vector.Fill(3, 0.0)            # (0, 0, 0)
Vector.Linspace(0.0, 1.0, 5)  # 5 valori da 0 a 1
Vector.Range(0, 5)             # (0, 1, 2, 3, 4)
Vector.Repeat(v, 5)            # ripete v fino a size 5
```

### Accesso componenti

```python
v = Vector((1.0, 2.0, 3.0))
v.x, v.y, v.z         # per nome
v[0], v[1], v[2]      # per indice
v[:2]                  # slice → (1.0, 2.0)

# Swizzle
v.xyz = v.zyx          # inversione assi
v.xy = Vector((1, 2))
```

### Proprietà

| Proprietà | Tipo | Descrizione |
|-----------|------|-------------|
| `length` | `float` | Lunghezza (magnitudine) del vettore |
| `length_squared` | `float` | Lunghezza al quadrato (più veloce) |
| `magnitude` | `float` | Alias di `length` |
| `is_frozen` | `bool` | True se immutabile |
| `is_valid` | `bool` | True se il dato owner è valido |

### Operazioni aritmetiche

```python
a = Vector((1, 0, 0))
b = Vector((0, 1, 0))

c = a + b              # somma: (1, 1, 0)
c = a - b              # differenza: (1, -1, 0)
c = a * 2.0            # scala: (2, 0, 0)
c = a @ b              # dot product: 0.0 (equiv. a.dot(b))
c = -a                 # negazione: (-1, 0, 0)
```

### Metodi principali

```python
v.length               # lunghezza vettore
v.normalized()         # copia normalizzata (length=1), NON modifica v
v.normalize()          # normalizza in-place

v.dot(other)           # prodotto scalare → float
v.cross(other)         # prodotto vettoriale → Vector (solo 3D)
v.angle(other)         # angolo tra i vettori in radianti → float
v.angle(other, fallback=0.0)  # con fallback per vettori zero

v.project(other)       # proiezione di v su other → Vector
v.reflect(mirror)      # riflessione rispetto a mirror → Vector
v.lerp(other, factor)  # interpolazione lineare [0,1] → Vector
v.slerp(other, factor) # interpolazione sferica → Vector

v.rotation_difference(other)  # quaternion differenza rotazione → Quaternion
v.rotate(euler_or_quat_or_matrix)  # ruota il vettore in-place

v.to_2d()    # copia 2D (x, y)
v.to_3d()    # copia 3D (x, y, z)
v.to_4d()    # copia 4D (x, y, z, w=1)

v.to_track_quat(track='Z', up='Y')  # quaternion da tracking direction

v.copy()     # copia indipendente dal dato wrapped
v.freeze()   # rende immutabile (hashable)
v.negate()   # nega tutti i valori in-place
v.orthogonal()  # vettore perpendicolare (asse non definito)
```

### Esempi pratici stampa 3D

```python
from mathutils import Vector
import math

# Distanza tra due punti
p1 = Vector((0, 0, 0))
p2 = Vector((10, 0, 0))
dist = (p2 - p1).length  # 10.0

# Angolo tra due normali
n1 = Vector((0, 0, 1))   # faccia verso l'alto
n2 = Vector((0, 0, -1))  # faccia verso il basso
angle_deg = math.degrees(n1.angle(n2))  # 180.0°

# Verificare se normale punta verso il basso (overhang)
DOWN = Vector((0, 0, -1))
face_normal = Vector((0.3, 0, -0.95)).normalized()
cos_angle = face_normal.dot(DOWN)  # > 0 = punta in giu
is_overhang = face_normal.z < -0.5  # angolo > 60° rispetto a down

# Trasformare vertice in world space
import bpy
obj = bpy.context.object
vert_local = obj.data.vertices[0].co
vert_world = obj.matrix_world @ vert_local  # matmul con Matrix
```

---

## Matrix (`mathutils.Matrix`)

**Costruzione:**

```python
from mathutils import Matrix
import math

# Matrice identità
m = Matrix.Identity(4)   # 4x4
m = Matrix.Identity(3)   # 3x3

# Matrice di traslazione (4x4)
m = Matrix.Translation((2.0, 3.0, 4.0))

# Matrice di rotazione
m = Matrix.Rotation(math.radians(45.0), 4, 'X')  # 45° attorno X, 4x4
m = Matrix.Rotation(math.radians(45.0), 4, 'Y')  # 45° attorno Y
m = Matrix.Rotation(math.radians(45.0), 4, (1, 0, 0))  # asse arbitrario

# Matrice di scala
m = Matrix.Scale(2.0, 4)                    # scala uniforme 2x
m = Matrix.Scale(0.5, 4, (0, 0, 1))        # scala 0.5x solo su Z

# Matrice diagonale
m = Matrix.Diagonal((2.0, 3.0, 1.0))

# LocRotScale combinata (molto utile!)
loc = (1, 2, 3)
rot = Euler((0, 0, math.radians(45)), 'XYZ')
sca = (1, 1, 1)
m = Matrix.LocRotScale(loc, rot, sca)       # None per componenti opzionali

# Da righe
m = Matrix(((1,0,0,0), (0,1,0,0), (0,0,1,0), (0,0,0,1)))
```

### Accesso elementi

```python
m = Matrix.Identity(4)
m[0][0]      # elemento riga 0, colonna 0
m[0][0:3]    # slice di riga
m[0].xyz     # prime 3 componenti riga (come Vector)
m.col[0]     # accesso per colonna
```

### Operazioni

```python
a = Matrix.Identity(4)
b = Matrix.Translation((1, 0, 0))
c = a @ b    # moltiplicazione matrice (matmul)
v = Vector((1, 0, 0))
vt = m @ v   # trasforma vettore con matrice
```

### Metodi principali

```python
# Invertire
m.inverted()           # copia invertita (ValueError se non invertibile)
m.inverted(fallback)   # con fallback se non invertibile
m.inverted_safe()      # mai errore, aggiunge epsilon se degenere
m.invert()             # in-place
m.invert_safe()        # in-place, mai errore

# Trasposta
m.transposed()         # copia trasposta
m.transpose()          # in-place

# Decomposizione
loc, rot, sca = m.decompose()
# loc: Vector traslazione
# rot: Quaternion rotazione
# sca: Vector scala

# Conversioni
m.to_euler(order='XYZ') -> Euler       # matrice → euler
m.to_quaternion() -> Quaternion         # matrice → quaternion
m.to_translation() -> Vector            # estrae traslazione (4x4)
m.to_scale() -> Vector                  # estrae scala (3x3/4x4)
m.to_3x3() -> Matrix                    # riduce a 3x3
m.to_4x4() -> Matrix                    # estende a 4x4

# Altre utilità
m.determinant() -> float
m.identity()           # setta all'identità in-place
m.zero()               # setta tutti a zero in-place
m.normalize()          # normalizza colonne (3x3/4x4)
m.normalized() -> Matrix
m.lerp(other, factor) -> Matrix        # interpolazione

# Proprietà
m.is_identity  # bool (read-only)
m.is_negative  # bool, scala negativa (read-only)
m.is_orthogonal  # bool (read-only)
```

### Esempi pratici

```python
from mathutils import Matrix, Vector, Euler
import math

# Combinare trasformazioni
mat_loc = Matrix.Translation((2.0, 3.0, 4.0))
mat_rot = Matrix.Rotation(math.radians(45.0), 4, 'Z')
mat_sca = Matrix.Scale(2.0, 4)
mat_combined = mat_loc @ mat_rot @ mat_sca  # ordine: prima scala, poi rot, poi traslazione

# Estrarre componenti da matrix_world oggetto
import bpy
obj = bpy.context.object
loc, rot, sca = obj.matrix_world.decompose()
print(f"Posizione: {loc}")
print(f"Rotazione: {rot.to_euler()}")
print(f"Scala: {sca}")

# Trasformare normale in world space (solo rotazione, no traslazione)
mat_rot_only = obj.matrix_world.to_3x3().normalized()
local_normal = Vector((0, 0, 1))
world_normal = mat_rot_only @ local_normal
world_normal.normalize()

# Matrice inversa per trasformare da world a local
mat_inv = obj.matrix_world.inverted()
world_point = Vector((5, 5, 0))
local_point = mat_inv @ world_point
```

---

## Euler (`mathutils.Euler`)

**Costruzione:**

```python
from mathutils import Euler
import math

eul = Euler((0.0, 0.0, math.radians(45.0)), 'XYZ')  # angoli in radianti, ordine XYZ
eul = Euler((0.0, 0.0, 0.0))  # default XYZ

# Componenti
eul.x  # rotazione X in radianti
eul.y  # rotazione Y in radianti
eul.z  # rotazione Z in radianti
eul.order  # 'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'
```

### Metodi

```python
eul.to_matrix() -> Matrix       # 3x3 rotation matrix
eul.to_quaternion() -> Quaternion
eul.rotate(other)               # ruota di Euler/Quaternion/Matrix (in-place)
eul.rotate_axis('Z', math.radians(45))  # ruota attorno asse (wraps a range unico)
eul.make_compatible(other)      # compatibilità per interpolazione
eul.copy() -> Euler
eul.zero()                      # setta tutto a zero
```

### Esempi pratici

```python
from mathutils import Euler
import math

# Rotazione di 45° attorno a Z (asse stampa 3D)
rot = Euler((0, 0, math.radians(45)), 'XYZ')

# Da angoli oggetto a matrice
import bpy
obj = bpy.context.object
euler = obj.rotation_euler  # è già un Euler
mat = euler.to_matrix()     # 3x3

# Impostare rotazione oggetto
obj.rotation_euler = Euler((0, 0, math.radians(90)), 'XYZ')
# oppure
obj.rotation_euler.z = math.radians(90)
```

---

## mathutils.geometry — Funzioni chiave

```python
from mathutils import geometry, Vector
```

### Intersezione e distanza

```python
# Ray-triangle intersection
geometry.intersect_ray_tri(v1, v2, v3, ray, orig, clip=True) -> Vector | None
# v1,v2,v3: vertici triangolo (Vector)
# ray: direzione raggio (Vector, normalizzato internamente)
# orig: origine raggio (Vector)
# clip=True: restringe all'area del triangolo
# Ritorna punto di intersezione o None

# Distanza punto-piano (con segno, negativo sotto la normale)
geometry.distance_point_to_plane(pt, plane_co, plane_no) -> float
# pt: punto (Vector)
# plane_co: punto sul piano (Vector)
# plane_no: normale del piano (Vector)

# Punto più vicino su un triangolo
geometry.closest_point_on_tri(pt, tri_p1, tri_p2, tri_p3) -> Vector

# Intersezione line-line (closest points)
geometry.intersect_line_line(v1, v2, v3, v4) -> tuple[Vector, Vector] | None
# Ritorna (punto_su_linea1, punto_su_linea2) o None se parallele

# Intersezione punto-linea (closest point + parametro t)
geometry.intersect_point_line(pt, line_p1, line_p2) -> tuple[Vector, float]
# Ritorna (punto_più_vicino_sulla_linea, t)
# t=0 → line_p1, t=1 → line_p2, fuori [0,1] = estrapolato

# Intersezione raggio-piano
geometry.intersect_line_plane(line_a, line_b, plane_co, plane_no) -> Vector | None

# Intersezione 2 piani → linea di intersezione
geometry.intersect_plane_plane(plane_a_co, plane_a_no, plane_b_co, plane_b_no) -> tuple[Vector, Vector] | tuple[None, None]
```

### Area e normale

```python
# Area triangolo (2D o 3D)
geometry.area_tri(v1, v2, v3) -> float

# Normale di un poligono 3D (dal winding order)
geometry.normal(*vectors) -> Vector
# Richiede 3+ Vector per il poligono

# Volume tetraedro (assoluto)
geometry.volume_tetrahedron(v1, v2, v3, v4) -> float
```

### Tessellazione e 2D

```python
# Tessellazione poligono in triangoli
geometry.tessellate_polygon(polylines) -> list[tuple[int, int, int]]
# polylines: lista di poligoni, ogni poligono è una lista di punti 2D/3D
# Ritorna lista di triple di indici

# Convex hull 2D
geometry.convex_hull_2d(points) -> list[int]
# Indici dei punti che formano il convex hull (CCW)

# Best fit rettangolo 2D (angolo di rotazione ottimale)
geometry.box_fit_2d(points) -> float
```

### Bezier

```python
# Interpolazione curva bezier
geometry.interpolate_bezier(knot1, handle1, handle2, knot2, resolution) -> list[Vector]
```

---

## BVHTree (`mathutils.bvhtree`)

BVH (Bounding Volume Hierarchy) tree per ricerche di prossimità e ray cast su geometria.

```python
from mathutils.bvhtree import BVHTree
```

### Costruzione

```python
# Da mesh Blender (modo più comune)
import bpy
obj = bpy.context.object
depsgraph = bpy.context.evaluated_depsgraph_get()
obj_eval = obj.evaluated_get(depsgraph)
mesh_eval = obj_eval.data
bvh = BVHTree.FromMesh(mesh_eval, epsilon=0.0)

# Da oggetto Blender (con deformazioni valutate)
bvh = BVHTree.FromObject(obj, depsgraph, deform=True, cage=False, epsilon=0.0)

# Da BMesh
import bmesh
bm = bmesh.new()
bm.from_mesh(mesh)
bvh = BVHTree.FromBMesh(bm, epsilon=0.0)
bm.free()

# Da polygon soup (vertici + poligoni raw)
verts = [(0,0,0), (1,0,0), (0,1,0), (1,1,0)]
polys = [(0,1,2), (1,3,2)]
bvh = BVHTree.FromPolygons(verts, polys, all_triangles=False, epsilon=0.0)
```

### Metodi principali

```python
# Ray cast sulla geometria
location, normal, index, distance = bvh.ray_cast(origin, direction, distance=sys.float_info.max)
# origin: Vector punto di partenza
# direction: Vector direzione (normalizzata internamente)
# Ritorna (pos, normal, face_index, dist) — tutti None se nessun hit

# Trova elemento più vicino a un punto
location, normal, index, distance = bvh.find_nearest(origin, distance=1.84e+19)
# origin: Vector punto di ricerca
# Ritorna (pos, normal, face_index, dist) — tutti None se nessun hit

# Trova tutti gli elementi nel range
results = bvh.find_nearest_range(origin, distance)
# Ritorna list[(pos, normal, face_index, dist)]

# Overlap tra due alberi (utile per collision detection)
pairs = bvh.overlap(other_tree)
# Ritorna list[(index_self, index_other)]
```

### Esempi pratici stampa 3D

```python
from mathutils.bvhtree import BVHTree
from mathutils import Vector
import bpy

obj = bpy.context.active_object
depsgraph = bpy.context.evaluated_depsgraph_get()
obj_eval = obj.evaluated_get(depsgraph)
bvh = BVHTree.FromObject(obj_eval, depsgraph)

# Check overhang con ray casting verso il basso
DOWN = Vector((0, 0, -1))

overhang_info = []
for poly in obj.data.polygons:
    # Trasforma centro in world space
    center_world = obj.matrix_world @ poly.center
    # Sposta leggermente verso l'alto per evitare self-intersection
    origin = center_world + Vector((0, 0, 0.001))
    
    loc, norm, idx, dist = bvh.ray_cast(origin, DOWN)
    if loc is None:
        # Nessuna geometria sotto → faccia a rischio overhang
        normal_world = obj.matrix_world.to_3x3() @ poly.normal
        if normal_world.z < -0.3:  # punta verso il basso
            overhang_info.append(poly.index)

print(f"Facce overhang potenziali: {len(overhang_info)}")

# Trovare punti superficie più vicini (per analisi clearance)
point = Vector((0, 0, 5))
loc, norm, idx, dist = bvh.find_nearest(point)
if loc:
    print(f"Punto più vicino: {loc}, distanza: {dist:.3f}m")

# Rilevare mesh interpenetranti
bvh1 = BVHTree.FromObject(bpy.data.objects['ObjA'], depsgraph)
bvh2 = BVHTree.FromObject(bpy.data.objects['ObjB'], depsgraph)
overlapping = bvh1.overlap(bvh2)
if overlapping:
    print(f"Interpenetrazione rilevata! {len(overlapping)} coppie di facce")
```

---

## KDTree (`mathutils.kdtree`)

KD-tree 3D generico per ricerche spaziali su insiemi di punti.

```python
from mathutils.kdtree import KDTree
```

### Costruzione

```python
# OBBLIGATORIO: specificare la dimensione massima in anticipo
size = len(mesh.vertices)
kd = KDTree(size)

# Inserire punti
for i, v in enumerate(mesh.vertices):
    kd.insert(v.co, i)  # co: coordinate 3D, i: indice arbitrario non-negativo

# OBBLIGATORIO: bilanciare dopo tutti gli insert (costruisce l'albero)
kd.balance()
# NOTA: non chiamare balance() dopo ogni insert — farlo una sola volta alla fine
```

### Metodi di ricerca

```python
# Trova il punto più vicino
co, index, dist = kd.find(co_find)
# co: Vector posizione trovata
# index: indice del punto (quello passato a insert)
# dist: distanza

# Trova i N punti più vicini
results = kd.find_n(co_find, n)
# Ritorna list[(co, index, dist)]

# Trova tutti i punti nel raggio
results = kd.find_range(co_find, radius)
# Ritorna list[(co, index, dist)]

# Filtro personalizzato
co, index, dist = kd.find(co_find, filter=lambda idx: idx % 2 == 0)
# Funzione filter: prende un indice, ritorna True per includere
```

### Esempi pratici stampa 3D

```python
from mathutils.kdtree import KDTree
from mathutils import Vector
import bpy

obj = bpy.context.active_object
mesh = obj.data

# Costruire KDTree dai vertici della mesh
kd = KDTree(len(mesh.vertices))
for i, v in enumerate(mesh.vertices):
    kd.insert(v.co, i)
kd.balance()

# Trovare il vertice più vicino a un punto target
target = Vector((0.05, 0.0, 0.0))  # 50mm in X se scale=0.001
co, idx, dist = kd.find(target)
print(f"Vertice più vicino: idx={idx}, co={co}, dist={dist:.4f}m = {dist*1000:.2f}mm")

# Trovare tutti i vertici entro 5mm dal target
radius_m = 0.005  # 5mm in metri
nearby = kd.find_range(target, radius_m)
print(f"Vertici entro 5mm: {len(nearby)}")

# Clustering proximity: trovare vertici "sovrapposti" (doppi vertici)
MERGE_THRESHOLD = 0.0001  # 0.1mm
merged = set()
for i, v in enumerate(mesh.vertices):
    if i in merged:
        continue
    near = kd.find_range(v.co, MERGE_THRESHOLD)
    if len(near) > 1:
        for co, idx, dist in near:
            if idx != i:
                merged.add(idx)
print(f"Vertici doppi trovati: {len(merged)}")

# Trovare i 10 vertici più vicini al cursore 3D
cursor_local = obj.matrix_world.inverted() @ bpy.context.scene.cursor.location
top10 = kd.find_n(cursor_local, 10)
for co, idx, dist in top10:
    print(f"  Vert {idx}: {co}, dist={dist*1000:.2f}mm")
```

---

## Quaternion (`mathutils.Quaternion`)

```python
from mathutils import Quaternion, Vector
import math

# Costruzione
q = Quaternion()                           # identità (1, 0, 0, 0)
q = Quaternion((w, x, y, z))             # componenti
q = Quaternion((1, 0, 0), math.pi/2)     # asse + angolo (Vector, angolo)

# Componenti
q.w, q.x, q.y, q.z

# Operazioni
q1 @ q2          # composizione rotazione (matmul)
q @ v            # ruota vettore V (Vector)
q.inverted()     # quaternion inverso (= coniugato per unitari)
q.normalized()   # normalizza
q.conjugated()   # coniugato (= inverso se normalizzato)

# Conversioni
q.to_matrix() -> Matrix       # 3x3 rotation matrix
q.to_euler(order='XYZ') -> Euler
q.to_axis_angle() -> tuple[Vector, float]  # (asse, angolo in rad)

# Interpolazione
q1.slerp(q2, factor)          # interpolazione sferica [0,1]
q1.rotation_difference(q2)    # quaternion differenza tra le due rotazioni

# Utilità
q.dot(other) -> float          # prodotto scalare
q.angle                        # angolo della rotazione in radianti
q.axis                         # asse di rotazione (Vector)
q.copy() -> Quaternion
q.freeze()                     # rende immutabile
```

### Pattern stampa 3D

```python
from mathutils import Quaternion, Vector, Matrix
import math

# Ruotare oggetto di 90° attorno a Z (per ottimizzare stampa)
import bpy
obj = bpy.context.active_object
q = Quaternion((0, 0, 1), math.radians(90))  # asse Z, 90°
obj.rotation_mode = 'QUATERNION'
obj.rotation_quaternion = q

# Quaternion da normale: trovare la rotazione che porta Z → normale
def quat_from_normal(normal):
    """Ritorna quaternion che ruota (0,0,1) verso normal."""
    z_axis = Vector((0, 0, 1))
    normal = Vector(normal).normalized()
    return z_axis.rotation_difference(normal)

# Calcolare orientamento ottimale per stampa
# (minimizzare volume supporti = massimizzare facce verso l'alto)
q = quat_from_normal((0, 0.2, 0.98))  # leggermente inclinato
```

---

## Recap — Quando usare cosa

| Problema | Strumento |
|----------|-----------|
| Trasformare vertici local → world | `obj.matrix_world @ vertex.co` |
| Angolo tra due normali | `n1.angle(n2)` |
| Distanza punto da piano | `geometry.distance_point_to_plane(pt, plane_co, plane_no)` |
| Ray cast su mesh (check overhang, solidità) | `BVHTree.ray_cast()` |
| Punto mesh più vicino a un punto 3D | `BVHTree.find_nearest()` |
| Trovare N vertici più vicini a un punto | `KDTree.find_n()` |
| Trovare vertici doppi (merge) | `KDTree.find_range()` con threshold |
| Intersezione geometrie (collision) | `BVHTree.overlap()` |
| Area triangolo | `geometry.area_tri(v1, v2, v3)` |
| Intersezione raggio-triangolo | `geometry.intersect_ray_tri()` |
| Rotazione che porta A → B | `Vector.rotation_difference()` |
| Comporre trasformazioni | `Matrix @ Matrix` |
| Decomporre matrix_world | `matrix.decompose()` → `(loc, rot, sca)` |
