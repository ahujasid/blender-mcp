# Blender Mesh Types — Struttura Dati

Fonte: Blender Python API 5.x — `bpy.types.Mesh*`
Contesto: accesso dati mesh da Python per scripting stampa 3D FDM.

---

## Mesh (`bpy.types.Mesh`)

**Classe:** `class bpy.types.Mesh(ID)`
Mesh data-block che definisce superfici geometriche. Accessibile tramite `obj.data` quando `obj.type == 'MESH'`.

### Collezioni principali

| Proprietà | Tipo | Descrizione |
|-----------|------|-------------|
| `vertices` | `MeshVertices[MeshVertex]` | Tutti i vertici della mesh (readonly) |
| `edges` | `MeshEdges[MeshEdge]` | Tutti gli edge della mesh (readonly) |
| `polygons` | `MeshPolygons[MeshPolygon]` | Tutte le facce (poligoni) della mesh (readonly) |
| `loops` | `MeshLoops[MeshLoop]` | Tutti i loop (face corners) della mesh (readonly) |
| `loop_triangles` | `MeshLoopTriangles[MeshLoopTriangle]` | Tessellazione in triangoli (readonly) |
| `loop_triangle_polygons` | `bpy_prop_collection[ReadOnlyInteger]` | Indice faccia per ogni loop triangle (readonly) |
| `materials` | `IDMaterials[Material]` | Materiali assegnati (readonly) |

### Attributi e dati extra

| Proprietà | Tipo | Descrizione |
|-----------|------|-------------|
| `attributes` | `AttributeGroupMesh[Attribute]` | Geometry attributes generici (readonly) |
| `color_attributes` | `AttributeGroupMesh[Attribute]` | Attributi colore geometria (readonly) |
| `uv_layer_clone` | `MeshUVLoopLayer` | UV layer usato come sorgente clone |
| `uv_layer_stencil` | `MeshUVLoopLayer` | UV layer usato come stencil |
| `skin_vertices` | `bpy_prop_collection[MeshSkinVertexLayer]` | Skin vertices (readonly) |
| `shape_keys` | `Key` | Shape keys (readonly) |
| `corner_normals` | `bpy_prop_collection[MeshNormalValue]` | Normali split per face corner (readonly) |
| `polygon_normals` | `bpy_prop_collection[MeshNormalValue]` | Normali per ogni faccia (readonly) |

### Proprietà statistiche (editmode)

| Proprietà | Tipo | Descrizione |
|-----------|------|-------------|
| `total_vert_sel` | `int` | Numero vertici selezionati |
| `total_edge_sel` | `int` | Numero edge selezionati |
| `total_face_sel` | `int` | Numero facce selezionate |
| `is_editmode` | `bool` | True se in editmode (readonly) |
| `has_custom_normals` | `bool` | True se ci sono normali custom (readonly) |
| `normals_domain` | `Literal['POINT','FACE','CORNER']` | Dominio normali (readonly) |

### Proprietà remesh e simmetria

| Proprietà | Tipo | Default |
|-----------|------|---------|
| `remesh_mode` | `Literal['VOXEL','QUAD']` | `'VOXEL'` |
| `remesh_voxel_size` | `float` | `0.1` |
| `remesh_voxel_adaptivity` | `float` | `0.0` |
| `use_remesh_preserve_volume` | `bool` | `False` |
| `use_remesh_preserve_attributes` | `bool` | `False` |
| `use_mirror_x/y/z` | `bool` | `False` |

### Metodi principali

```python
mesh.update(calc_edges=False, calc_edges_loose=False)
# Aggiorna la mesh dopo modifiche ai dati

mesh.from_pydata(vertices, edges, faces, shade_flat=True)
# Crea mesh da liste Python: vertices=[(x,y,z),...], faces=[(i,j,k),...]
# IMPORTANTE: chiamare mesh.validate() dopo se i dati non sono verificati

mesh.validate(verbose=False, clean_customdata=True) -> bool
# Valida geometria, corregge/rimuove geometria invalida. Ritorna True se ci sono stati fix

mesh.validate_material_indices() -> bool
# Valida indici materiale dei poligoni

mesh.clear_geometry()
# Rimuove tutta la geometria (NON rimuove shape keys o materiali)

mesh.count_selected_items() -> bpy_prop_array[int]
# Ritorna (n_vert_sel, n_edge_sel, n_face_sel)

mesh.shade_flat()
# Imposta shading flat su tutte le facce

mesh.shade_smooth()
# Imposta shading smooth su tutte le facce
```

---

## MeshVertex (`bpy.types.MeshVertex`)

**Classe:** `class bpy.types.MeshVertex(bpy_struct)`
Singolo vertice in una Mesh data-block.

### Proprietà

| Proprietà | Tipo | Default | Note |
|-----------|------|---------|------|
| `co` | `mathutils.Vector` | `(0,0,0)` | Coordinata 3D del vertice |
| `normal` | `mathutils.Vector` | `(0,0,0)` | Normale del vertice (readonly) |
| `index` | `int` | `0` | Indice del vertice (readonly) |
| `select` | `bool` | `False` | Stato selezione |
| `hide` | `bool` | `False` | Stato nascosto |
| `groups` | `bpy_prop_collection[VertexGroupElement]` | — | Vertex groups e pesi (readonly) |
| `undeformed_co` | `mathutils.Vector` | `(0,0,0)` | Coordinata senza deformatori (readonly) |

### Note pratiche

- `co` è in object space (non world space). Usa `obj.matrix_world @ vertex.co` per world space.
- `normal` è la normal interpolata dal vertice, aggiornata dopo `mesh.update()`.
- `undeformed_co` è utile per texture coordinates generate.
- `groups` dà accesso ai vertex group weights: `for grp in v.groups: grp.group, grp.weight`.

---

## MeshEdge (`bpy.types.MeshEdge`)

**Classe:** `class bpy.types.MeshEdge(bpy_struct)`
Edge in una Mesh data-block.

### Proprietà

| Proprietà | Tipo | Default | Note |
|-----------|------|---------|------|
| `vertices` | `bpy_prop_array[int]` | `(0, 0)` | Indici dei 2 vertici dell'edge |
| `index` | `int` | `0` | Indice dell'edge (readonly) |
| `select` | `bool` | `False` | Stato selezione |
| `hide` | `bool` | `False` | Stato nascosto |
| `is_loose` | `bool` | `False` | True se non connesso a nessuna faccia (readonly) |
| `use_edge_sharp` | `bool` | `False` | Edge sharp per shading |
| `use_seam` | `bool` | `False` | Seam edge per UV unwrapping |
| `key` | — | — | Chiave ordinata dei vertici (readonly) |

### Note pratiche

- `edge.vertices[0]` e `edge.vertices[1]` sono gli indici dei due vertici.
- `is_loose` è utile per trovare edge non connessi (potenziale problema manifold).
- `use_edge_sharp` influenza il calcolo delle normali split.

---

## MeshPolygon (`bpy.types.MeshPolygon`)

**Classe:** `class bpy.types.MeshPolygon(bpy_struct)`
Faccia (poligono) in una Mesh data-block.

### Proprietà

| Proprietà | Tipo | Default | Note |
|-----------|------|---------|------|
| `vertices` | `bpy_prop_array[int]` | `(0,0,0)` | Indici dei vertici della faccia |
| `loop_start` | `int` | `0` | Indice del primo loop di questa faccia |
| `loop_total` | `int` | `0` | Numero di loop (vertici) di questa faccia (readonly) |
| `normal` | `mathutils.Vector` | `(0,0,0)` | Normale locale unitaria (readonly) |
| `center` | `mathutils.Vector` | `(0,0,0)` | Centro della faccia (readonly) |
| `area` | `float` | `0.0` | Area della faccia in object space (readonly) |
| `index` | `int` | `0` | Indice della faccia (readonly) |
| `select` | `bool` | `False` | Stato selezione |
| `hide` | `bool` | `False` | Stato nascosto |
| `material_index` | `int` | `0` | Indice del materiale assegnato |
| `use_smooth` | `bool` | `False` | Shading smooth su questa faccia |
| `edge_keys` | — | — | Chiavi degli edge (readonly) |
| `loop_indices` | — | — | Indici dei loop (readonly) |

### Metodi

```python
polygon.flip()  # Inverte il winding della faccia (ribalta la normale)
```

### Relazione loop-polygon

La mesh usa un sistema loop per accedere alle coordinate per-face:
- Ogni faccia ha `loop_start` (primo loop) e `loop_total` (numero di loop/vertici)
- I loop indices della faccia: `range(poly.loop_start, poly.loop_start + poly.loop_total)`
- Ogni `MeshLoop` ha `vertex_index` e `edge_index`

---

## MeshLoop (`bpy.types.MeshLoop`)

**Classe:** `class bpy.types.MeshLoop(bpy_struct)`
Loop (face corner) in una Mesh data-block. Un loop è un angolo di una faccia — combina vertice + edge + faccia.

### Proprietà

| Proprietà | Tipo | Default | Note |
|-----------|------|---------|------|
| `vertex_index` | `int` | `0` | Indice del vertice |
| `edge_index` | `int` | `0` | Indice dell'edge |
| `index` | `int` | `0` | Indice del loop (readonly) |
| `normal` | `mathutils.Vector` | `(0,0,0)` | Normale del face corner, tiene conto di sharp edges/faces (readonly) |
| `tangent` | `mathutils.Vector` | `(0,0,0)` | Tangente locale (richiede `calc_tangents()`) (readonly) |
| `bitangent` | `mathutils.Vector` | `(0,0,0)` | Bitangente locale (richiede `calc_tangents()`) (readonly) |
| `bitangent_sign` | `float` | `0.0` | Segno della bitangente, `bitangent = sign * cross(normal, tangent)` (readonly) |

---

## Collezioni (`MeshVertices`, `MeshEdges`, `MeshPolygons`, `MeshLoops`)

Tutte le collezioni mesh sono `bpy_prop_collection` con metodo `add()`:

```python
mesh.vertices.add(count)   # Aggiunge N vertici
mesh.edges.add(count)      # Aggiunge N edge
mesh.polygons.add(count)   # Aggiunge N poligoni
mesh.loops.add(count)      # Aggiunge N loop

# MeshPolygons ha anche:
mesh.polygons.active       # Indice della faccia attiva (int, read/write)
```

**Nota:** Usare `mesh.from_pydata()` per creazione mesh da zero — è più semplice e sicuro.

---

## Pattern pratici per stampa 3D

### Accesso base a vertici e facce

```python
import bpy
import numpy as np

obj = bpy.context.object
mesh = obj.data

# Accesso iterativo (lento per mesh grandi)
for v in mesh.vertices:
    print(v.index, v.co, v.normal)

for poly in mesh.polygons:
    print(poly.index, poly.normal, poly.area)
```

### `foreach_get` per performance (consigliato)

```python
import bpy
import numpy as np

obj = bpy.context.object
mesh = obj.data
n_verts = len(mesh.vertices)
n_polys = len(mesh.polygons)

# Lettura MOLTO più veloce con foreach_get
coords = np.empty(n_verts * 3, dtype=np.float32)
mesh.vertices.foreach_get('co', coords)
coords = coords.reshape(n_verts, 3)

normals = np.empty(n_verts * 3, dtype=np.float32)
mesh.vertices.foreach_get('normal', normals)
normals = normals.reshape(n_verts, 3)

# Leggere selezione
selected = np.empty(n_verts, dtype=bool)
mesh.vertices.foreach_get('select', selected)

# Normali poligoni
poly_normals = np.empty(n_polys * 3, dtype=np.float32)
mesh.polygons.foreach_get('normal', poly_normals)
poly_normals = poly_normals.reshape(n_polys, 3)

# Aree poligoni
areas = np.empty(n_polys, dtype=np.float32)
mesh.polygons.foreach_get('area', areas)
```

### Calcolare bounding box manuale

```python
import bpy
import numpy as np

obj = bpy.context.object
mesh = obj.data

# Metodo veloce con foreach_get
n_verts = len(mesh.vertices)
coords = np.empty(n_verts * 3, dtype=np.float32)
mesh.vertices.foreach_get('co', coords)
coords = coords.reshape(n_verts, 3)

bbox_min = coords.min(axis=0)
bbox_max = coords.max(axis=0)
dimensions = bbox_max - bbox_min
center = (bbox_min + bbox_max) / 2

print(f"Min: {bbox_min}")
print(f"Max: {bbox_max}")
print(f"Dims (mm): {dimensions * 1000}")  # se scene in m, target mm

# Alternativa: usa obj.bound_box (in object space, 8 corner)
bbox_corners = [obj.matrix_world @ v[:] for v in obj.bound_box]
```

### Trovare facce con normale verso il basso (candidati overhang)

```python
import bpy
import numpy as np
from mathutils import Vector

obj = bpy.context.object
mesh = obj.data
mat = obj.matrix_world.to_3x3().normalized()  # solo rotazione/scala

OVERHANG_THRESHOLD = -0.5  # cos(120°) ≈ -0.5, overhang > 60°

overhang_faces = []
for poly in mesh.polygons:
    # Trasforma normale in world space
    world_normal = mat @ poly.normal
    world_normal.normalize()
    # Dot con vettore down (0,0,-1)
    dot_down = world_normal.z  # .dot(Vector((0,0,1))) = z component
    if dot_down < OVERHANG_THRESHOLD:
        overhang_faces.append((poly.index, poly.area, dot_down))

print(f"Facce overhang: {len(overhang_faces)}")
total_overhang_area = sum(a for _, a, _ in overhang_faces)
print(f"Area overhang totale: {total_overhang_area:.4f} m²")

# Versione numpy (più veloce)
n_polys = len(mesh.polygons)
normals = np.empty(n_polys * 3, dtype=np.float32)
mesh.polygons.foreach_get('normal', normals)
normals = normals.reshape(n_polys, 3)

# Applica rotazione world (senza scala non uniforme)
mat_np = np.array(mat)
world_normals = (mat_np @ normals.T).T
# Normalizza
norms = np.linalg.norm(world_normals, axis=1, keepdims=True)
world_normals = world_normals / np.maximum(norms, 1e-8)

# z component = dot con (0,0,1)
z_components = world_normals[:, 2]
overhang_mask = z_components < OVERHANG_THRESHOLD
print(f"Facce overhang: {overhang_mask.sum()}")
```

### Calcolare area superficiale totale

```python
import bpy
import numpy as np

obj = bpy.context.object
mesh = obj.data
n_polys = len(mesh.polygons)

# Lettura veloce con foreach_get
areas = np.empty(n_polys, dtype=np.float32)
mesh.polygons.foreach_get('area', areas)

total_area = areas.sum()
print(f"Area totale: {total_area:.6f} m²")
print(f"Area totale: {total_area * 1e6:.2f} mm²")  # conversione se scene in metri

# Divisa per materiale
mat_indices = np.empty(n_polys, dtype=np.int32)
mesh.polygons.foreach_get('material_index', mat_indices)
for mat_idx in range(len(mesh.materials)):
    mat_area = areas[mat_indices == mat_idx].sum()
    mat_name = mesh.materials[mat_idx].name if mesh.materials[mat_idx] else f"mat_{mat_idx}"
    print(f"  {mat_name}: {mat_area * 1e6:.2f} mm²")
```

### Accedere ai dati loop per UV e normali split

```python
import bpy

obj = bpy.context.object
mesh = obj.data

# Iterare loop di ogni faccia
for poly in mesh.polygons:
    loop_indices = range(poly.loop_start, poly.loop_start + poly.loop_total)
    for li in loop_indices:
        loop = mesh.loops[li]
        vert = mesh.vertices[loop.vertex_index]
        print(f"  Vert {loop.vertex_index}: co={vert.co}, loop_normal={loop.normal}")
```
