# Blender Mesh Operators — Riferimento 3D Printing

Operatori `bpy.ops.mesh.*` rilevanti per stampa 3D, mesh repair e modellazione.

---

## Repair

### `bpy.ops.mesh.fill_holes(*, sides=4)`
Riempie i buchi della mesh (boundary edge loops).
- `sides` `int` [0–1000] — Numero di lati del buco da riempire; `0` = riempi tutti i buchi

### `bpy.ops.mesh.remove_doubles(*, threshold=0.0001, use_centroid=True, use_unselected=False, use_sharp_edge_from_normals=False)`
Fondi vertici vicini (Merge by Distance).
- `threshold` `float` [1e-06–50] — Distanza massima per il merge (default `0.0001`)
- `use_centroid` `bool` — Sposta al centroide del cluster, altrimenti usa il vertice più vicino (default `True`)
- `use_unselected` `bool` — Unisce selezionati ad altri non selezionati (default `False`)
- `use_sharp_edge_from_normals` `bool` — Calcola sharp edges dai custom normals (default `False`)

### `bpy.ops.mesh.dissolve_degenerate(*, threshold=0.0001)`
Dissolve facce a zero area e edge a zero lunghezza.
- `threshold` `float` [1e-06–50] — Distanza massima per il merge (default `0.0001`)

### `bpy.ops.mesh.delete_loose(*, use_verts=True, use_edges=True, use_faces=False)`
Elimina geometria sciolta non connessa.
- `use_verts` `bool` — Rimuovi vertici sciolti (default `True`)
- `use_edges` `bool` — Rimuovi edge sciolti (default `True`)
- `use_faces` `bool` — Rimuovi facce sciolte (default `False`)

### `bpy.ops.mesh.symmetrize(*, direction='NEGATIVE_X', threshold=0.0001)`
Applica simmetria topologica e geometrica su un asse.
- `direction` `Literal[Symmetrize Direction Items]` — Lato da copiare (default `'NEGATIVE_X'`)
- `threshold` `float` [0–10] — Tolleranza per snap dei vertici centrali (default `0.0001`)

### `bpy.ops.mesh.intersect(*, mode='SELECT_UNSELECT', separate_mode='CUT', threshold=1e-06, solver='EXACT')`
Taglia intersezioni tra facce selezionate.
- `mode` `Literal['SELECT', 'SELECT_UNSELECT']` — `SELECT`: auto-intersect; `SELECT_UNSELECT`: selected vs unselected (default `'SELECT_UNSELECT'`)
- `separate_mode` `Literal['ALL', 'CUT', 'NONE']` — `ALL`: separa; `CUT`: taglia mantenendo entrambi i lati; `NONE`: unisce (default `'CUT'`)
- `threshold` `float` [0–0.01] — Soglia merge (default `1e-06`)
- `solver` `Literal['FLOAT', 'EXACT']` — `EXACT` più accurato per coplanari (default `'EXACT'`)

### `bpy.ops.mesh.intersect_boolean(*, operation='DIFFERENCE', use_swap=False, use_self=False, threshold=1e-06, solver='EXACT')`
Boolean tra geometria selezionata e non selezionata.
- `operation` `Literal['INTERSECT', 'UNION', 'DIFFERENCE']` — Operazione booleana (default `'DIFFERENCE'`)
- `use_swap` `bool` — Inverte quale lato viene mantenuto in DIFFERENCE (default `False`)
- `use_self` `bool` — Auto-unione o auto-intersezione (default `False`)
- `threshold` `float` [0–0.01] — Soglia merge (default `1e-06`)
- `solver` `Literal['FLOAT', 'EXACT']` — (default `'EXACT'`)

---

## Normals

### `bpy.ops.mesh.normals_make_consistent(*, inside=False)`
Orienta tutte le normali verso l'esterno o verso l'interno (Recalculate Outside/Inside).
- `inside` `bool` — Se `True`, orienta verso l'interno (default `False`)

### `bpy.ops.mesh.flip_normals(*, only_clnors=False)`
Inverte la direzione delle normali delle facce selezionate.
- `only_clnors` `bool` — Inverte solo i custom loop normals (default `False`)

---

## Select

### `bpy.ops.mesh.select_non_manifold(*, extend=True, use_wire=True, use_boundary=True, use_multi_face=True, use_non_contiguous=True, use_verts=True)`
Seleziona tutti i vertici/edge non manifold.
- `extend` `bool` — Estendi la selezione (default `True`)
- `use_wire` `bool` — Edge wire (default `True`)
- `use_boundary` `bool` — Edge boundary (default `True`)
- `use_multi_face` `bool` — Edge condivisi da più di 2 facce (default `True`)
- `use_non_contiguous` `bool` — Edge tra facce con direzioni alternate (default `True`)
- `use_verts` `bool` — Vertici che connettono più regioni di facce (default `True`)

---

## Fill / Close

### `bpy.ops.mesh.fill(*, use_beauty=True)`
Riempie un edge loop selezionato con facce.
- `use_beauty` `bool` — Usa la triangolazione ottimale (default `True`)

### `bpy.ops.mesh.fill_grid(*, span=1, offset=0, use_interp_simple=False)`
Riempie con una griglia da due loop.
- `span` `int` [1–1000] — Numero di colonne della griglia (default `1`)
- `offset` `int` [-1000–1000] — Vertice angolo della griglia (default `0`)
- `use_interp_simple` `bool` — Interpolazione semplice (default `False`)

### `bpy.ops.mesh.beautify_fill(*, angle_limit=3.14159)`
Riorganizza triangoli per ridurre geometria degenere.
- `angle_limit` `float` [0–3.14159] — Limite angolo max (default `3.14159` = 180°)

### `bpy.ops.mesh.bridge_edge_loops(*, type='SINGLE', use_merge=False, merge_factor=0.5, twist_offset=0, number_cuts=0, interpolation='PATH', smoothness=1.0, profile_shape_factor=0.0, profile_shape='SMOOTH')`
Crea un bridge di facce tra due o più edge loop.
- `type` `Literal['SINGLE', 'CLOSED', 'PAIRS']` — Metodo di connessione (default `'SINGLE'`)
- `use_merge` `bool` — Unisci invece di creare facce (default `False`)
- `merge_factor` `float` [0–1] — Fattore posizione per merge (default `0.5`)
- `twist_offset` `int` [-1000–1000] — Offset torsione per loop chiusi (default `0`)
- `number_cuts` `int` [0–1000] — Tagli intermedi (default `0`)
- `interpolation` `Literal['LINEAR', 'PATH', 'SURFACE']` — Metodo interpolazione (default `'PATH'`)
- `smoothness` `float` [0–1000] — Fattore smoothness (default `1.0`)

### `bpy.ops.mesh.convex_hull(*, delete_unused=True, use_existing_faces=True, make_holes=False, join_triangles=True, face_threshold=0.698132, shape_threshold=0.698132, topology_influence=0.0, uvs=False, vcols=False, seam=False, sharp=False, materials=False, deselect_joined=False)`
Racchiude i vertici selezionati in un poliedro convesso.
- `delete_unused` `bool` — Elimina elementi selezionati non usati dallo hull (default `True`)
- `use_existing_faces` `bool` — Salta triangoli hull coperti da facce esistenti (default `True`)
- `make_holes` `bool` — Elimina facce selezionate usate dallo hull (default `False`)
- `join_triangles` `bool` — Unisce triangoli adiacenti in quad (default `True`)
- `face_threshold` `float` [0–3.14159] — Limite angolo facce (~40°; default `0.698132`)
- `shape_threshold` `float` [0–3.14159] — Limite angolo forma (default `0.698132`)
- `topology_influence` `float` [0–2] — Peso griglia regolare di quad (default `0.0`)

---

## Extrude / Modify

### `bpy.ops.mesh.extrude_region()`
Estrude la regione selezionata di facce (usato con TRANSFORM_OT_translate).

### `bpy.ops.mesh.extrude_faces_move(*, MESH_OT_extrude_faces_indiv={}, TRANSFORM_OT_shrink_fatten={})`
Estrude ogni faccia individualmente lungo le normali locali.
- `MESH_OT_extrude_faces_indiv` `dict` — Parametri estrude individuale
- `TRANSFORM_OT_shrink_fatten` `dict` — Parametri shrink/fatten

### `bpy.ops.mesh.extrude_manifold(*, MESH_OT_extrude_region={}, TRANSFORM_OT_translate={})`
Estrude e dissolve edge le cui facce formano superficie piatta; interseca nuovi edge.

### `bpy.ops.mesh.inset(*, use_boundary=True, use_even_offset=True, use_relative_offset=False, use_edge_rail=False, thickness=0.0, depth=0.0, use_outset=False, use_select_inset=False, use_individual=False, use_interpolate=True, release_confirm=False)`
Crea nuove facce inset nelle facce selezionate.
- `use_boundary` `bool` — Inset ai boundary (default `True`)
- `use_even_offset` `bool` — Spessore uniforme (default `True`)
- `use_relative_offset` `bool` — Scala offset per geometria adiacente (default `False`)
- `use_edge_rail` `bool` — Inset lungo edge esistenti (default `False`)
- `thickness` `float` [0–inf] — Spessore (default `0.0`)
- `depth` `float` [-inf–inf] — Profondità (default `0.0`)
- `use_outset` `bool` — Outset invece di inset (default `False`)
- `use_individual` `bool` — Inset individuale per faccia (default `False`)
- `use_interpolate` `bool` — Blend dei dati attraverso l'inset (default `True`)

### `bpy.ops.mesh.bevel(*, offset_type='OFFSET', offset=0.0, profile_type='SUPERELLIPSE', offset_pct=0.0, segments=1, profile=0.5, affect='EDGES', clamp_overlap=False, loop_slide=True, mark_seam=False, mark_sharp=False, material=-1, harden_normals=False, face_strength_mode='NONE', miter_outer='SHARP', miter_inner='SHARP', spread=0.1, vmesh_method='ADJ', release_confirm=False)`
Taglia le geometrie selezionate con un angolo per creare bevel o chamfer.
- `offset_type` `Literal['OFFSET', 'WIDTH', 'DEPTH', 'PERCENT', 'ABSOLUTE']` — Metodo dimensione bevel (default `'OFFSET'`)
- `offset` `float` [0–1e+06] — Ampiezza bevel (default `0.0`)
- `segments` `int` [1–1000] — Segmenti per edge curvo (default `1`)
- `profile` `float` [0–1] — Forma profilo: `0.5` = rotondo (default `0.5`)
- `affect` `Literal['VERTICES', 'EDGES']` — Bevel su vertici o edge (default `'EDGES'`)
- `clamp_overlap` `bool` — Evita sovrapposizioni (default `False`)
- `loop_slide` `bool` — Preferisce scorrimento su edge per spessori uniformi (default `True`)
- `harden_normals` `bool` — Allinea normali nuove facce alle adiacenti (default `False`)
- `miter_outer` `Literal['SHARP', 'PATCH', 'ARC']` — Pattern miter esterno (default `'SHARP'`)
- `miter_inner` `Literal['SHARP', 'ARC']` — Pattern miter interno (default `'SHARP'`)

### `bpy.ops.mesh.solidify(*, thickness=0.01)`
Crea un skin solido estrudendo e compensando gli angoli acuti.
- `thickness` `float` [-10000–10000] — Spessore (default `0.01`)

### `bpy.ops.mesh.wireframe(*, use_boundary=True, use_even_offset=True, use_relative_offset=False, use_replace=True, thickness=0.01, offset=0.01, use_crease=False, crease_weight=0.01)`
Crea un wireframe solido dalle facce.
- `use_boundary` `bool` — Inset ai boundary (default `True`)
- `use_even_offset` `bool` — Offset uniforme (default `True`)
- `use_replace` `bool` — Rimuove le facce originali (default `True`)
- `thickness` `float` [0–10000] — Spessore (default `0.01`)
- `offset` `float` [0–10000] — Offset (default `0.01`)
- `use_crease` `bool` — Crease sugli hub edge per subdivision (default `False`)

### `bpy.ops.mesh.bisect(*, plane_co=(0.0, 0.0, 0.0), plane_no=(0.0, 0.0, 0.0), use_fill=False, clear_inner=False, clear_outer=False, threshold=0.0001, xstart=0, xend=0, ystart=0, yend=0, flip=False, cursor=5)`
Taglia la geometria lungo un piano.
- `plane_co` `Vector` — Punto sul piano (default `(0,0,0)`)
- `plane_no` `Vector` — Normale del piano (default `(0,0,0)`)
- `use_fill` `bool` — Riempi il taglio (default `False`)
- `clear_inner` `bool` — Rimuovi geometria dietro il piano (default `False`)
- `clear_outer` `bool` — Rimuovi geometria davanti al piano (default `False`)
- `threshold` `float` [0–10] — Soglia asse per preservare geometria esistente (default `0.0001`)

### `bpy.ops.mesh.loopcut(*, number_cuts=1, smoothness=0.0, falloff='INVERSE_SQUARE', object_index=-1, edge_index=-1)`
Aggiunge nuovi loop tra loop esistenti.
- `number_cuts` `int` [1–1000000] — Numero di tagli (default `1`)
- `smoothness` `float` [-1000–1000] — Fattore smoothness (default `0.0`)

### `bpy.ops.mesh.offset_edge_loops(*, use_cap_endpoint=False)`
Crea edge loop offset dalla selezione corrente.
- `use_cap_endpoint` `bool` — Estendi il loop agli endpoint (default `False`)

---

## Dissolve / Delete

### `bpy.ops.mesh.delete(*, type='VERT')`
Elimina vertici, edge o facce selezionati.
- `type` `Literal['VERT', 'EDGE', 'FACE', 'EDGE_FACE', 'ONLY_FACE']` — Metodo eliminazione (default `'VERT'`)

### `bpy.ops.mesh.dissolve_verts(*, use_face_split=False, use_boundary_tear=False)`
Dissolve vertici, unisce edge e facce.
- `use_face_split` `bool` — Separa angoli faccia per mantenere geometria adiacente (default `False`)
- `use_boundary_tear` `bool` — Separa angoli invece di unire facce (default `False`)

### `bpy.ops.mesh.dissolve_edges(*, use_verts=True, angle_threshold=3.14159, use_face_split=False)`
Dissolve edge, unisce facce.
- `use_verts` `bool` — Dissolve i vertici residui connessi solo a 2 edge (default `True`)
- `angle_threshold` `float` [0–3.14159] — Vertici che separano coppie di edge sono preservati se l'angolo supera questa soglia (default `3.14159`)
- `use_face_split` `bool` — Separa angoli faccia (default `False`)

### `bpy.ops.mesh.dissolve_faces(*, use_verts=False)`
Dissolve facce.
- `use_verts` `bool` — Dissolve vertici residui connessi solo a 2 edge (default `False`)

### `bpy.ops.mesh.dissolve_limited(*, angle_limit=0.0872665, use_dissolve_boundaries=False, delimit={'NORMAL'})`
Dissolve edge e vertici selezionati limitati dall'angolo della geometria adiacente.
- `angle_limit` `float` [0–3.14159] — Angolo massimo (~5°; default `0.0872665`)
- `use_dissolve_boundaries` `bool` — Dissolve tutti i vertici tra i boundary delle facce (default `False`)
- `delimit` `set` — Modalità di delimitazione (default `{'NORMAL'}`)

### `bpy.ops.mesh.merge(*, type='CENTER', uvs=False)`
Unisce i vertici selezionati.
- `type` `Literal['CENTER', 'CURSOR', 'COLLAPSE', 'FIRST', 'LAST']` — Metodo merge (default `'CENTER'`)
- `uvs` `bool` — Sposta UV di conseguenza (default `False`)

### `bpy.ops.mesh.separate(*, type='SELECTED')`
Separa la geometria selezionata in una nuova mesh.
- `type` `Literal['SELECTED', 'MATERIAL', 'LOOSE']` — Tipo separazione (default `'SELECTED'`)

---

## Triangulate / Retopology

### `bpy.ops.mesh.quads_convert_to_tris(*, quad_method='BEAUTY', ngon_method='BEAUTY')`
Triangolizza le facce selezionate.
- `quad_method` `Literal[Modifier Triangulate Quad Method Items]` — Metodo per splittare quad in triangoli (default `'BEAUTY'`)
- `ngon_method` `Literal[Modifier Triangulate Ngon Method Items]` — Metodo per splittare n-gon in triangoli (default `'BEAUTY'`)

### `bpy.ops.mesh.tris_convert_to_quads(*, face_threshold=0.698132, shape_threshold=0.698132, topology_influence=0.0, uvs=False, vcols=False, seam=False, sharp=False, materials=False, deselect_joined=False)`
Unisce triangoli in quad dove possibile.
- `face_threshold` `float` [0–3.14159] — Limite angolo faccia (~40°; default `0.698132`)
- `shape_threshold` `float` [0–3.14159] — Limite angolo forma (default `0.698132`)
- `topology_influence` `float` [0–2] — Peso griglia regolare di quad (default `0.0`)
- `uvs/vcols/seam/sharp/materials` `bool` — Attributi comparati per il join (default tutti `False`)

### `bpy.ops.mesh.subdivide(*, number_cuts=1, smoothness=0.0, ngon=True, quadcorner='STRAIGHT_CUT', fractal=0.0, fractal_along_normal=0.0, seed=0)`
Subdivide gli edge selezionati.
- `number_cuts` `int` [1–100] — Numero di tagli (default `1`)
- `smoothness` `float` [0–1000] — Fattore smoothness (default `0.0`)
- `ngon` `bool` — Permette n-gon nelle facce create (default `True`)
- `quadcorner` `Literal['INNERVERT', 'PATH', 'STRAIGHT_CUT', 'FAN']` — Tipo angolo quad (default `'STRAIGHT_CUT'`)
- `fractal` `float` [0–1e+06] — Randomness frattale (default `0.0`)

### `bpy.ops.mesh.unsubdivide(*, iterations=2)`
Riduce la suddivisione degli edge/facce selezionati.
- `iterations` `int` [1–1000] — Numero di iterazioni (default `2`)

### `bpy.ops.mesh.decimate(*, ratio=1.0, use_vertex_group=False, vertex_group_factor=1.0, invert_vertex_group=False, use_symmetry=False, symmetry_axis='Y')`
Semplifica la geometria collassando edge.
- `ratio` `float` [0–1] — Rapporto di decimazione; `1.0` = nessuna riduzione (default `1.0`)
- `use_vertex_group` `bool` — Usa il vertex group attivo come influenza (default `False`)
- `vertex_group_factor` `float` [0–1000] — Peso del vertex group (default `1.0`)
- `use_symmetry` `bool` — Mantieni simmetria su un asse (default `False`)
- `symmetry_axis` `Literal[Axis Xyz Items]` — Asse di simmetria (default `'Y'`)
