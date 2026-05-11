# BMesh Scripting — Blender Python API

## Pattern base BMesh

```python
import bpy, bmesh

obj = bpy.context.active_object

# --- Modo oggetto: from_mesh / to_mesh ---
bm = bmesh.new()
bm.from_mesh(obj.data)          # carica la mesh
# ... operazioni ...
bm.to_mesh(obj.data)            # scrive i risultati
obj.data.update()
bm.free()                       # libera memoria esplicitamente

# --- Edit mode: from_edit_mesh ---
bm = bmesh.from_edit_mesh(obj.data)
# ... operazioni ...
bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=True)
# NON chiamare bm.free() in edit mode!
```

### Funzioni modulo bmesh

| Funzione | Descrizione |
|----------|-------------|
| `bmesh.new(*, use_operators=True)` | Crea BMesh vuoto. `use_operators=True` abilita bmesh.ops (richiede memoria extra). |
| `bmesh.from_edit_mesh(mesh)` | Accede alla mesh in edit mode. |
| `bmesh.update_edit_mesh(mesh, *, loop_triangles=True, destructive=True)` | Aggiorna mesh dopo modifiche in edit mode. |

---

## bmesh.ops — Operatori chiave per 3D printing

Tutti gli operatori restituiscono un `dict` con slot di output (es. `ret['geom']`, `ret['faces']`).

### Pulizia mesh / Repair

#### remove_doubles
```python
bmesh.ops.remove_doubles(bm, verts=[], use_connected=False, dist=0)
```
Unisce vertici entro distanza `dist`. Equivale a "Merge by Distance".
```python
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0001)
```

#### recalc_face_normals
```python
bmesh.ops.recalc_face_normals(bm, faces=[])
```
Ricalcola le normali verso "fuori". Essenziale prima di export STL.
```python
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
```

#### dissolve_limit
```python
bmesh.ops.dissolve_limit(bm, angle_limit=0, use_dissolve_boundaries=False,
                          verts=[], edges=[], delimit=set())
```
Limited Dissolve: elimina facce planari e spigoli co-lineari entro `angle_limit` (radianti).
```python
import math
bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5),
                          verts=bm.verts[:], edges=bm.edges[:])
```

#### reverse_faces
```python
bmesh.ops.reverse_faces(bm, faces=[], flip_multires=False)
```
Inverte il winding (e quindi la normale) delle facce selezionate.

### Tappare buchi / Fill

#### holes_fill
```python
bmesh.ops.holes_fill(bm, edges=[], sides=0)
# -> dict con 'faces': list[BMFace]
```
Riempie boundary edges con facce, copiando i custom-data adiacenti.
`sides`: numero massimo di lati del buco (0 = illimitato).
```python
boundary = [e for e in bm.edges if e.is_boundary]
ret = bmesh.ops.holes_fill(bm, edges=boundary, sides=4)
new_faces = ret['faces']
```

#### bridge_loops
```python
bmesh.ops.bridge_loops(bm, edges=[], use_pairs=False, use_cyclic=False,
                        use_merge=False, merge_factor=0, twist_offset=0)
# -> dict con 'faces': list[BMFace], 'edges': list[BMEdge]
```
Collega due edge loop con facce (bridge).
```python
ret = bmesh.ops.bridge_loops(bm, edges=loop_a_edges + loop_b_edges)
```

#### grid_fill
Crea facce da due edge loop disconnessi che condividono bordi.

### Topologia

#### triangulate
```python
bmesh.ops.triangulate(bm, faces=[], quad_method='BEAUTY', ngon_method='BEAUTY')
# -> dict con 'edges', 'faces', 'face_map'
```
Triangola quads e n-gon. Necessario per export STL/OBJ.
`quad_method`: `'BEAUTY'` | `'FIXED'` | `'ALTERNATE'` | `'SHORT_EDGE'` | `'LONG_EDGE'`
`ngon_method`: `'BEAUTY'` | `'EAR_CLIP'`
```python
bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY')
```

#### beautify_fill
```python
bmesh.ops.beautify_fill(bm, faces=[], edges=[], use_restrict_tag=False, method='AREA')
# -> dict con 'geom': list[BMVert|BMEdge|BMFace]
```
Ruota gli spigoli per ottenere triangoli meglio proporzionati.
`method`: `'AREA'` | `'ANGLE'`

#### connect_verts
```python
bmesh.ops.connect_verts(bm, verts=[], faces_exclude=[], check_degenerate=False)
# -> dict con 'edges': list[BMEdge]
```
Divide facce aggiungendo spigoli tra i vertici indicati.

#### subdivide_edges
```python
bmesh.ops.subdivide_edges(bm, edges=[], smooth=0, smooth_falloff='SMOOTH',
                           fractal=0, along_normal=0, cuts=0, seed=0,
                           custom_patterns={}, edge_percents={},
                           quad_corner_type='STRAIGHT_CUT', use_grid_fill=False,
                           use_single_edge=False, use_only_quads=False,
                           use_sphere=False, use_smooth_even=False)
```
Subdivide gli spigoli con opzioni avanzate.

### Dissolve

#### dissolve_verts
```python
bmesh.ops.dissolve_verts(bm, verts=[], use_face_split=False, use_boundary_tear=False)
```

#### dissolve_edges
```python
bmesh.ops.dissolve_edges(bm, edges=[], use_verts=False, use_face_split=False,
                          angle_threshold=0)
# -> dict con 'region': list[BMFace]
```
`use_verts=True`: dissolve anche i vertici rimasti tra soli 2 spigoli.

#### dissolve_faces
```python
bmesh.ops.dissolve_faces(bm, faces=[], use_verts=False)
# -> dict con 'region': list[BMFace]
```

### Geometria solida

#### solidify
```python
bmesh.ops.solidify(bm, geom=[], thickness=0)
# -> dict con 'geom': list[BMVert|BMEdge|BMFace]
```
Trasforma una mesh in shell con spessore `thickness`. Utile per rendere manifold superfici sottili.
```python
bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.002)
```

#### convex_hull
```python
bmesh.ops.convex_hull(bm, input=[], use_existing_faces=False)
# -> dict con 'geom', 'geom_interior', 'geom_unused', 'geom_holes'
```
Costruisce la convex hull dai vertici in `input`.
- `geom`: vertici/facce/spigoli del hull
- `geom_interior`: elementi interni non usati dall'output
- `use_existing_faces=True`: non sovrascrive facce già esistenti
```python
ret = bmesh.ops.convex_hull(bm, input=bm.verts[:] + bm.edges[:] + bm.faces[:])
interior = ret['geom_interior']  # geometria interna da eliminare
```

### Estrusione

#### extrude_face_region
```python
bmesh.ops.extrude_face_region(bm, geom=[], edges_exclude=set(),
                               use_keep_orig=False, use_normal_flip=False,
                               use_normal_from_adjacent=False,
                               use_dissolve_ortho_edges=False,
                               use_select_history=False, skip_input_flip=False)
# -> dict con 'geom': list[BMVert|BMEdge|BMFace]
```
Estrude facce (non trasforma, usare translate/scale dopo).
```python
ret = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
new_geom = ret['geom']
new_verts = [e for e in new_geom if isinstance(e, bmesh.types.BMVert)]
bmesh.ops.translate(bm, verts=new_verts, vec=(0, 0, 0.01))
```

### Trasformazioni

#### translate
```python
bmesh.ops.translate(bm, vec=(0,0,0), space=Matrix.Identity(4), verts=[], use_shapekey=False)
```

#### rotate
```python
bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Identity(4), verts=[],
                 space=Matrix.Identity(4), use_shapekey=False)
```
```python
import math, mathutils
bmesh.ops.rotate(bm, verts=bm.verts[:],
                 cent=(0, 0, 0),
                 matrix=mathutils.Matrix.Rotation(math.radians(90), 3, 'Z'))
```

#### scale
```python
bmesh.ops.scale(bm, vec=(1,1,1), space=Matrix.Identity(4), verts=[], use_shapekey=False)
```

#### transform
```python
bmesh.ops.transform(bm, matrix=Matrix.Identity(4), space=Matrix.Identity(4),
                    verts=[], use_shapekey=False)
```
Trasformazione generica con matrice 4x4.

### Duplica / Elimina

#### duplicate
```python
bmesh.ops.duplicate(bm, geom=[], dest=None, use_select_history=False,
                    use_edge_flip_from_face=False)
# -> dict con 'geom_orig', 'geom', 'vert_map', 'edge_map', 'face_map'
```
Duplica geometria, opzionalmente in un BMesh di destinazione.

#### delete
```python
bmesh.ops.delete(bm, geom=[], context='VERTS')
```
`context`: `'VERTS'` | `'EDGES'` | `'FACES_ONLY'` | `'EDGES_FACES'` | `'FACES'` | `'FACES_KEEP_BOUNDARY'` | `'TAGGED_ONLY'`
```python
# Elimina solo facce interne (non boundary)
inner = [f for f in bm.faces if not any(e.is_boundary for e in f.edges)]
bmesh.ops.delete(bm, geom=inner, context='FACES_ONLY')
```

### Smoothing

#### smooth_vert
```python
bmesh.ops.smooth_vert(bm, verts=[], factor=0,
                       mirror_clip_x=False, mirror_clip_y=False, mirror_clip_z=False,
                       clip_dist=0, use_axis_x=False, use_axis_y=False, use_axis_z=False)
```
Smooth base con media dei vertici.

#### smooth_laplacian_vert
```python
bmesh.ops.smooth_laplacian_vert(bm, verts=[], lambda_factor=0, lambda_border=0,
                                 use_x=False, use_y=False, use_z=False,
                                 preserve_volume=False)
```
Laplacian smooth (Desbrun et al.). `preserve_volume=True` riduce la contrazione.

### Spin

```python
bmesh.ops.spin(bm, geom=[], cent=(0,0,0), axis=(0,0,1), dvec=(0,0,0),
               angle=0, space=Matrix.Identity(4), steps=0,
               use_merge=False, use_normal_flip=False, use_duplicate=False)
# -> dict con 'geom_last': geometria dell'ultimo step
```
Estrude/duplica geometria ruotando di `angle` radianti in `steps` passi.

### Mirror

```python
bmesh.ops.mirror(bm, geom=[], matrix=Matrix.Identity(4), merge_dist=0,
                 axis='X', mirror_u=False, mirror_v=False,
                 mirror_udim=False, use_shapekey=False)
# -> dict con 'geom': geometria specchiata
```

---

## bmesh.types — Tipi fondamentali

### BMesh

Struttura principale che contiene tutta la mesh.

```python
bm.verts    # BMVertSeq — sequenza di vertici
bm.edges    # BMEdgeSeq — sequenza di spigoli
bm.faces    # BMFaceSeq — sequenza di facce
bm.loops    # BMLoopSeq — accesso solo per layer data
bm.select_mode  # set{'VERT', 'EDGE', 'FACE'}
bm.is_valid     # bool
bm.is_wrapped   # True se owned da Blender (edit mode)
```

**Metodi chiave:**

| Metodo | Descrizione |
|--------|-------------|
| `bm.from_mesh(mesh)` | Carica da bpy.types.Mesh |
| `bm.to_mesh(mesh)` | Scrive su bpy.types.Mesh |
| `bm.from_object(obj, depsgraph)` | Carica da oggetto (con modificatori applicati) |
| `bm.free()` | Libera memoria esplicitamente |
| `bm.calc_volume(signed=False)` | Calcola volume mesh |
| `bm.calc_loop_triangles()` | Tessellation n-gon → triangoli |
| `bm.normal_update()` | Aggiorna tutte le normali |
| `bm.transform(matrix)` | Trasforma intera mesh |
| `bm.select_flush(select)` | Propaga selezione dai vertici |
| `bm.select_flush_mode()` | Propaga selezione in base al select_mode |
| `bm.copy()` | Copia il BMesh |
| `bm.clear()` | Cancella tutti i dati |

### BMVert

```python
v.co          # mathutils.Vector — coordinate 3D
v.normal      # mathutils.Vector — normale
v.is_manifold # bool (read-only) — manifold se ogni spigolo ha esattamente 2 facce
v.is_boundary # bool (read-only) — connesso a boundary edges
v.is_wire     # bool (read-only) — non connesso a facce
v.is_valid    # bool
v.hide        # bool
v.select      # bool
v.tag         # bool — uso libero per script
v.index       # int (può essere dirty, aggiornare con bm.verts.index_update())
v.link_edges  # BMElemSeq[BMEdge]
v.link_faces  # BMElemSeq[BMFace]
v.link_loops  # BMElemSeq[BMLoop]
```

**Metodi:**
- `v.calc_edge_angle(fallback=None)` — angolo tra i due spigoli connessi
- `v.calc_shell_factor()` — moltiplicatore per shell thickness
- `v.normal_update()` — aggiorna normale del vertice
- `v.select_set(select)` — imposta selezione con flush
- `v.hide_set(hide)` — imposta visibilità con flush

### BMEdge

```python
e.verts         # tuple[BMVert, BMVert]
e.is_manifold   # bool — esattamente 2 facce connesse
e.is_boundary   # bool — bordo di una faccia (1 sola faccia)
e.is_wire       # bool — 0 facce connesse
e.is_contiguous # bool — manifold E stesso winding
e.is_convex     # bool — join tra due facce convesse
e.is_valid      # bool
e.hide, e.select, e.tag, e.index
e.seam          # bool — UV seam
e.link_faces    # BMElemSeq[BMFace]
e.link_loops    # BMElemSeq[BMLoop]
```

**Metodi:**
- `e.calc_length()` — lunghezza spigolo
- `e.calc_face_angle(fallback=None)` — angolo tra le due facce (radianti)
- `e.calc_face_angle_signed(fallback=None)` — negativo per concavo
- `e.other_vert(vert)` — l'altro vertice
- `e.normal_update()` — aggiorna normali facce/vertici connessi

### BMFace

```python
f.normal        # mathutils.Vector — normale faccia
f.material_index # int
f.is_valid      # bool
f.hide, f.select, f.tag, f.index
f.edges         # BMElemSeq[BMEdge]
f.loops         # BMElemSeq[BMLoop] — angoli della faccia
f.verts         # BMElemSeq[BMVert] (via loops)
```

**Metodi:**
- `f.calc_area()` — area
- `f.calc_perimeter()` — perimetro
- `f.calc_center_median()` — centro mediano
- `f.calc_center_bounds()` — centro bounding box
- `f.normal_flip()` — inverte normale/winding
- `f.normal_update()` — ricalcola normale

### BMLoop

Rappresenta un angolo di faccia (corner). Acceduto via `face.loops`.

```python
loop.vert       # BMVert
loop.edge       # BMEdge (tra questo loop e il successivo)
loop.face       # BMFace
loop.link_loop_next     # BMLoop — angolo successivo nella faccia
loop.link_loop_prev     # BMLoop — angolo precedente
loop.link_loop_radial_next  # BMLoop — loop successivo attorno allo stesso spigolo
loop.link_loop_radial_prev
loop.is_convex  # bool
loop.is_valid   # bool
loop.index      # int
```

**Metodi:**
- `loop.calc_angle()` — angolo al corner (più piccolo = più tagliente)
- `loop.calc_normal()` — normale al corner
- `loop.calc_tangent()` — tangente al corner

---

## bmesh.utils — Utility

### edge_split
```python
bmesh.utils.edge_split(edge, vert, fac) -> tuple[BMEdge, BMVert]
```
Divide uno spigolo creando un nuovo vertice a posizione `fac` [0-1] tra i due vertici.
`vert` definisce la direzione della divisione.

### edge_rotate
```python
bmesh.utils.edge_rotate(edge, ccw=False) -> BMEdge | None
```
Ruota topologicamente uno spigolo (spin edge). Restituisce None se impossibile.

### face_split
```python
bmesh.utils.face_split(face, vert_a, vert_b, *, coords=(), use_exist=True, source=None)
    -> tuple[BMFace, BMLoop]
```
Divide una faccia tra due suoi vertici, con punti intermedi opzionali.

### face_join
```python
bmesh.utils.face_join(faces, remove=True) -> BMFace | None
```
Unisce una sequenza di facce in una sola. `remove=True` rimuove spigoli/vertici intermedi.

### face_flip
```python
bmesh.utils.face_flip(face)
```
Inverte la direzione della faccia.

### vert_collapse_edge
```python
bmesh.utils.vert_collapse_edge(vert, edge) -> BMEdge
```
Collassa un vertice in uno spigolo (merge).

### vert_collapse_faces
```python
bmesh.utils.vert_collapse_faces(vert, edge, fac, join_faces) -> BMEdge
```
Collassa un vertice con solo 2 spigoli manifold.

### vert_dissolve
```python
bmesh.utils.vert_dissolve(vert) -> bool
```
Dissolve e rimuove il vertice.

### vert_separate
```python
bmesh.utils.vert_separate(vert, edges) -> tuple[BMVert, ...]
```
Separa un vertice in più vertici lungo gli spigoli indicati.

### vert_splice
```python
bmesh.utils.vert_splice(vert, vert_target)
```
Fonde `vert` in `vert_target`. I vertici non devono condividere spigoli.

### loop_separate
```python
bmesh.utils.loop_separate(loop) -> BMVert | None
```
Stacca un vertice da un angolo di faccia, creando un nuovo vertice.

### face_vert_separate
```python
bmesh.utils.face_vert_separate(face, vert) -> BMVert | None
```
Alias di `loop_separate` per convenienza.

### face_split_edgenet
```python
bmesh.utils.face_split_edgenet(face, edgenet) -> tuple[BMFace, ...]
```
Divide una faccia in più regioni definite da una rete di spigoli.

---

## Pattern comuni per stampa 3D

### Trovare elementi non-manifold

```python
import bpy, bmesh

obj = bpy.context.active_object
bm = bmesh.new()
bm.from_mesh(obj.data)

# Vertici non-manifold
non_manifold_verts = [v for v in bm.verts if not v.is_manifold]

# Spigoli non-manifold (boundary o wire)
non_manifold_edges = [e for e in bm.edges if not e.is_manifold]

# Boundary edges (buchi)
boundary_edges = [e for e in bm.edges if e.is_boundary]

# Wire edges (non connessi a facce)
wire_edges = [e for e in bm.edges if e.is_wire]

print(f"Non-manifold verts: {len(non_manifold_verts)}")
print(f"Non-manifold edges: {len(non_manifold_edges)}")
print(f"Boundary edges (buchi): {len(boundary_edges)}")

bm.free()
```

### Calcolare il volume

```python
import bpy, bmesh

obj = bpy.context.active_object
bm = bmesh.new()
bm.from_mesh(obj.data)

# Assicurarsi che le normali siano corrette prima
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

volume = bm.calc_volume(signed=False)
print(f"Volume: {volume:.6f} m³")
print(f"Volume: {volume * 1e6:.2f} cm³")  # se unità = metri

bm.free()
```

### Trovare buchi (boundary edges)

```python
import bpy, bmesh

obj = bpy.context.active_object
bm = bmesh.new()
bm.from_mesh(obj.data)

boundary_edges = [e for e in bm.edges if e.is_boundary]

if boundary_edges:
    print(f"Trovati {len(boundary_edges)} boundary edges (mesh non chiusa)")
    # Tappa i buchi
    ret = bmesh.ops.holes_fill(bm, edges=boundary_edges, sides=0)
    print(f"Aggiunte {len(ret['faces'])} facce per chiudere i buchi")
else:
    print("Mesh chiusa (waterproof)")

bm.to_mesh(obj.data)
obj.data.update()
bm.free()
```

### Iterare su vertici e facce

```python
import bpy, bmesh

obj = bpy.context.active_object
bm = bmesh.new()
bm.from_mesh(obj.data)

# Ensure lookup tables are valid
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# Iterare su vertici
for v in bm.verts:
    if v.co.z < 0:
        v.co.z = 0  # flatten sotto Z=0

# Iterare su facce con accesso ai loop (per UV, normali angolo, ecc.)
for f in bm.faces:
    area = f.calc_area()
    if area < 0.000001:
        f.tag = True  # marca facce degeneri

# Eliminare facce marcate
degenerate = [f for f in bm.faces if f.tag]
bmesh.ops.delete(bm, geom=degenerate, context='FACES')

# Accedere ai vertici di una faccia tramite loops
for f in bm.faces:
    for loop in f.loops:
        v = loop.vert
        # v.co, v.normal, ecc.

bm.to_mesh(obj.data)
obj.data.update()
bm.free()
```

### Pipeline completa repair per stampa 3D

```python
import bpy, bmesh, math

def repair_mesh_for_print(obj, merge_dist=0.0001):
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    # 1. Rimuovi duplicati
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=merge_dist)

    # 2. Ricalcola normali
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    # 3. Chiudi buchi
    boundary = [e for e in bm.edges if e.is_boundary]
    if boundary:
        bmesh.ops.holes_fill(bm, edges=boundary, sides=0)

    # 4. Dissolvi geometria degenere
    bmesh.ops.dissolve_limit(bm,
        angle_limit=math.radians(0.1),
        verts=bm.verts[:], edges=bm.edges[:])

    # 5. Verifica finale
    non_manifold = [e for e in bm.edges if not e.is_manifold]
    volume = bm.calc_volume()

    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()

    return {
        'non_manifold_edges': len(non_manifold),
        'volume_m3': volume
    }

obj = bpy.context.active_object
result = repair_mesh_for_print(obj)
print(result)
```

### Custom data — Accesso UV e vertex groups

```python
# UV layers
uv_lay = bm.loops.layers.uv.active
for face in bm.faces:
    for loop in face.loops:
        uv = loop[uv_lay].uv  # mathutils.Vector 2D

# Shape keys
shape_lay = bm.verts.layers.shape["Key.001"]
for v in bm.verts:
    pos = v[shape_lay]  # mathutils.Vector

# Vertex groups (deform weights)
dvert_lay = bm.verts.layers.deform.active
group_index = obj.vertex_groups.active_index
for v in bm.verts:
    dvert = v[dvert_lay]
    weight = dvert.get(group_index, 0.0)
```
