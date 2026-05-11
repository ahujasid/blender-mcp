# Bisect & Splitting — Cutting planare, angolato, puzzle, multi-split

## Contesto

Tagliare una mesh con un piano è un'operazione comune per FDM:
- **Split oversized** — modello più grande del bed → dividere in N pezzi
- **Angled cut** — tagliare a 45° per rimuovere overhang / creare base piatta
- **Puzzle cut** — taglio con registration features (pin, dovetail) per assemblaggio preciso
- **Color change cut** — inserire pause G-code a una certa altezza (gestito in slicer, qui solo il marker)
- **Cross-section extraction** — ottenere una slice piatta per misurare o stampare
- **Multi-layer slicing** — suddividere verticalmente in pezzi orizzontali (es. grandi vasi)

Questo doc copre `bmesh.ops.bisect_plane` (API programmatica, preferita) e `bpy.ops.mesh.bisect` (operator, quando serve usare edit mode). La differenza rispetto a `[workflow_patterns]#split-oversized` è che quello usa Boolean con cubi come cutter; **bisect è più pulito e veloce** per tagli planari e gestisce bene la chiusura del foro.

Prerequisito: `scale_length=0.001`, scale applicate.

---

## 1. bisect_plane vs Boolean DIFFERENCE

| Aspetto | `bmesh.ops.bisect_plane` | Boolean DIFFERENCE |
|---|---|---|
| Velocità | O(n) lineare | O(n·m) |
| Robustezza su mesh AI | alta | media (richiede sanitize) |
| Crea faccia di taglio | opzionale (parametro `clear_*`) | sì (lato del cutter) |
| Input | piano (punto + normale) | oggetto cutter |
| Preserva UV | sì | sì (con EXACT) |
| Output multi-pezzo | automatic (con use_separate_all) | manuale |
| Fill del taglio | via `bmesh.ops.edgenet_fill` post | automatico |

**Regola**: per tagli planari (anche angolati) usare **bisect**. Per tagli con forma non planare o sottrazione di volume usare Boolean.

---

## 2. API — bisect_plane di base

```python
import bpy
import bmesh
from mathutils import Vector

def bisect_object(obj, plane_co_mm, plane_no, keep='BOTH', fill_cut=True):
    """
    Taglia obj con un piano.
    
    plane_co_mm: punto sul piano in world-mm
    plane_no: normale al piano (Vector, sarà normalizzato)
    keep: 'BOTH' | 'POS' (lato verso la normale) | 'NEG'
    fill_cut: riempie la sezione creata con n-gon (necessario per mesh chiusa)
    
    Opera in edit mode su una copia DUPLICATA (MCP-safe).
    Ritorna l'oggetto risultante (con nome _cut).
    """
    assert obj.type == 'MESH'
    # Duplica
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.duplicate()
    new = bpy.context.active_object
    new.name = obj.name + "_cut"
    
    # Converti piano in local space di new
    mw_inv = new.matrix_world.inverted()
    plane_co_local = mw_inv @ (Vector(plane_co_mm) * 0.001)   # BU local
    # Normale: trasforma senza shift
    plane_no_local = (mw_inv.to_3x3() @ Vector(plane_no)).normalized()
    
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(new.data)
    
    clear_inner = (keep == 'POS')    # rimuove il lato opposto alla normale (−)
    clear_outer = (keep == 'NEG')    # rimuove il lato della normale (+)
    
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    ret = bmesh.ops.bisect_plane(
        bm,
        geom=geom,
        dist=1e-6,
        plane_co=plane_co_local,
        plane_no=plane_no_local,
        clear_inner=clear_inner,
        clear_outer=clear_outer,
    )
    
    # Fill del taglio
    if fill_cut:
        cut_geom = ret.get('geom_cut', [])
        cut_edges = [g for g in cut_geom if isinstance(g, bmesh.types.BMEdge)]
        if cut_edges:
            bmesh.ops.edgenet_fill(bm, edges=cut_edges)
    
    bmesh.update_edit_mesh(new.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Recalc normals
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    print(f"[BISECT] {obj.name} → {new.name} at {plane_co_mm}mm, normal={tuple(plane_no)}, keep={keep}")
    return new
```

---

## 3. Split in due — modello oversized

Caso: modello alto 300 mm, bed A1 = 256 mm. Tagliare a metà altezza Z=150 mm e esportare due parti.

```python
def split_two_halves(obj, cut_z_mm, fill=True):
    """
    Taglia obj in due metà lungo piano orizzontale Z=cut_z_mm (world).
    Ritorna (bottom_obj, top_obj).
    """
    plane_co = (0, 0, cut_z_mm)
    plane_no = Vector((0, 0, 1))
    
    bottom = bisect_object(obj, plane_co, plane_no, keep='NEG', fill_cut=fill)
    bottom.name = obj.name + "_bottom"
    
    top = bisect_object(obj, plane_co, plane_no, keep='POS', fill_cut=fill)
    top.name = obj.name + "_top"
    
    # Facoltativo: rimuovi originale (richiederebbe approvazione MCP — qui solo nascondilo)
    obj.hide_viewport = True
    obj.hide_render = True
    
    print(f"[SPLIT-2] {obj.name} → {bottom.name} + {top.name} @ Z={cut_z_mm}mm")
    return bottom, top
```

---

## 4. Split in N pezzi

```python
def split_n_horizontal(obj, n_pieces, fill=True):
    """
    Divide obj in n_pieces pezzi di altezza uguale lungo Z.
    Ritorna lista di oggetti [bottom, ..., top].
    """
    mw = obj.matrix_world
    zs = [(mw @ v.co).z for v in obj.data.vertices]
    z_min = min(zs) * 1000
    z_max = max(zs) * 1000
    total_h = z_max - z_min
    piece_h = total_h / n_pieces
    
    pieces = []
    remaining = obj
    
    for i in range(n_pieces - 1):
        cut_z = z_min + piece_h * (i + 1)
        plane_co = (0, 0, cut_z)
        plane_no = Vector((0, 0, 1))
        
        # Bottom piece: tieni lato -Z di "remaining"
        bottom = bisect_object(remaining, plane_co, plane_no, keep='NEG', fill_cut=fill)
        bottom.name = obj.name + f"_p{i+1}"
        pieces.append(bottom)
        
        # Remaining: tieni lato +Z
        next_rem = bisect_object(remaining, plane_co, plane_no, keep='POS', fill_cut=fill)
        next_rem.name = obj.name + f"_rem_{i+1}"
        if remaining is not obj:
            bpy.data.objects.remove(remaining, do_unlink=True)
        remaining = next_rem
    
    # Ultimo pezzo
    remaining.name = obj.name + f"_p{n_pieces}"
    pieces.append(remaining)
    
    obj.hide_viewport = True
    print(f"[SPLIT-N] {obj.name} → {n_pieces} pieces of ~{piece_h:.1f}mm height each")
    return pieces
```

**Nota MCP**: ogni bisect duplica → la scena si riempie di intermedi. Dopo il loop rimuovere i `_rem_*`. L'operazione è distruttiva per l'originale (`hide_viewport = True` lo nasconde; se l'utente vuole cancellare serve approvazione).

---

## 5. Angled cut — rimozione overhang

Caso: busto con cavalletto, angolazione naturale crea overhang sotto il mento. Tagliare con un piano inclinato per creare base piatta "posta contro bed" che elimini gli overhang.

```python
import math

def cut_at_angle(obj, pivot_mm, tilt_axis='X', tilt_angle_deg=45, keep='POS'):
    """
    Taglio planare inclinato.
    pivot_mm: punto per cui passa il piano (world-mm)
    tilt_axis: asse rispetto al quale il piano è inclinato ('X' o 'Y')
    tilt_angle_deg: inclinazione del piano rispetto al piano XY (orizzontale)
    keep: quale lato tenere
    """
    angle_rad = math.radians(tilt_angle_deg)
    if tilt_axis.upper() == 'X':
        # Piano inclinato attorno all'asse X: normale ruota in YZ
        plane_no = Vector((0, -math.sin(angle_rad), math.cos(angle_rad)))
    elif tilt_axis.upper() == 'Y':
        plane_no = Vector((math.sin(angle_rad), 0, math.cos(angle_rad)))
    else:
        raise ValueError("tilt_axis must be 'X' or 'Y'")
    
    return bisect_object(obj, pivot_mm, plane_no, keep=keep, fill_cut=True)
```

Dopo il taglio, l'oggetto va **riorientato** con la nuova faccia di taglio sul bed: riposizionamento `ORIGIN_CURSOR` + rotazione, poi `snap_to_bed` (vedi `[object_placement]`).

---

## 6. Puzzle cut con registration features

Dividere in due pezzi con pin di registrazione **cilindrici** per riallineamento preciso durante incollaggio. Questo estende il "registration pin" di `[workflow_patterns]#split_oversized` al caso più generale.

### Design dei pin

- **Diametro**: 4 mm (buon compromesso resistenza/precisione)
- **Altezza**: 3–5 mm sporgenza
- **Numero**: 2–3 pin sul piano di taglio per evitare rotazione
- **Posizionamento**: asimmetrico (rende impossibile invertire i pezzi per errore)
- **Clearance foro**: +0.10 mm (slip fit PLA)

### Implementazione

```python
def split_with_registration_pins(
    obj,
    cut_z_mm,
    pin_diameter_mm=4.0,
    pin_height_mm=3.0,
    pin_clearance_mm=0.10,
    pin_positions_mm=None,    # lista di (x, y) in mm relative al centro del bbox
):
    """
    Divide obj in due metà a Z=cut_z_mm e aggiunge pin di registrazione.
    Il pezzo BOTTOM riceve PIN MASCHI (cilindri che sporgono verso +Z).
    Il pezzo TOP riceve FORI FEMMINE (cilindri cutter che creano fori).
    """
    # Posizioni di default: 2 pin asimmetrici
    if pin_positions_mm is None:
        # Piazza approssimativamente a 25% e 75% X, leggermente spostati in Y
        mw = obj.matrix_world
        verts = [mw @ v.co for v in obj.data.vertices]
        x_min = min(v.x for v in verts) * 1000
        x_max = max(v.x for v in verts) * 1000
        y_min = min(v.y for v in verts) * 1000
        y_max = max(v.y for v in verts) * 1000
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        pin_positions_mm = [
            (cx - (x_max - x_min) * 0.25, cy - (y_max - y_min) * 0.1),
            (cx + (x_max - x_min) * 0.25, cy + (y_max - y_min) * 0.1),
        ]
    
    # 1. Split a due metà
    bottom, top = split_two_halves(obj, cut_z_mm)
    
    # 2. Pin maschi su BOTTOM (UNION con cilindri sopra cut_z)
    male_r = pin_diameter_mm / 2 * 0.001
    pin_h_bu = pin_height_mm * 0.001
    pin_z_center = (cut_z_mm + pin_height_mm / 2) * 0.001   # metà sporge sopra cut_z
    
    for i, (px, py) in enumerate(pin_positions_mm):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=male_r,
            depth=pin_h_bu * 2,   # metà sotto cut_z (affonda nel bottom), metà sopra (sporge)
            location=(px * 0.001, py * 0.001, (cut_z_mm * 0.001)),
        )
        pin = bpy.context.active_object
        pin.name = f"_pin_male_{i}"
        
        # UNION con bottom
        bpy.ops.object.select_all(action='DESELECT')
        bottom.select_set(True)
        bpy.context.view_layer.objects.active = bottom
        mod = bottom.modifiers.new(f"_un_{i}", type='BOOLEAN')
        mod.operation = 'UNION'
        mod.solver = 'EXACT'
        mod.object = pin
        bpy.ops.object.modifier_apply(modifier=f"_un_{i}")
        bpy.data.objects.remove(pin, do_unlink=True)
    
    # 3. Fori femmina su TOP (DIFFERENCE con cilindri con clearance)
    female_r = (pin_diameter_mm / 2 + pin_clearance_mm) * 0.001
    for i, (px, py) in enumerate(pin_positions_mm):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=female_r,
            depth=pin_h_bu * 2 + 0.002,   # eccesso per evitare coplanarità
            location=(px * 0.001, py * 0.001, (cut_z_mm + pin_height_mm / 2) * 0.001),
        )
        hole = bpy.context.active_object
        hole.name = f"_hole_{i}"
        
        bpy.ops.object.select_all(action='DESELECT')
        top.select_set(True)
        bpy.context.view_layer.objects.active = top
        mod = top.modifiers.new(f"_di_{i}", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.solver = 'EXACT'
        mod.object = hole
        bpy.ops.object.modifier_apply(modifier=f"_di_{i}")
        bpy.data.objects.remove(hole, do_unlink=True)
    
    print(f"[PUZZLE] {obj.name} split @ Z={cut_z_mm}mm + {len(pin_positions_mm)} pins")
    print(f"[PUZZLE] pin: Ø{pin_diameter_mm}mm male, Ø{pin_diameter_mm + 2*pin_clearance_mm}mm female")
    return bottom, top
```

### Alternative registration features

| Feature | Pro | Contro |
|---|---|---|
| **Cilindro** (pin dritto) | Semplice, stampabile, nessun supporto | Non orienta — permette scivolamento angolare |
| **Cono troncato** | Self-centering | Richiede angolo <45° per stampabilità |
| **Dovetail trasversale** | Auto-locking in una direzione | Design e tolleranze complesse |
| **Key prismatico** (es. slot rettangolare) | Previene rotazione con 1 feature | Richiede tolerance laterale accurata |
| **Offset asimmetrico** | Impossibile invertire | Nessun meccanismo di lock |

Per la maggior parte dei casi FDM, **2 cilindri asimmetrici** sono lo standard — bilanciano robustezza, stampabilità e tolleranza.

---

## 7. Color change pause marker

Caso: stampante single-filament che supporta "pause & swap" per cambio colore. Non è un taglio fisico della mesh, ma **marker di altezza**. Il taglio è virtuale, serve solo per informare lo slicer dove mettere il pause G-code.

Approccio 1 — **annotazione via custom property**:
```python
def mark_color_change(obj, z_mm):
    """Segna l'altezza di cambio colore come custom property."""
    if "color_changes_mm" not in obj:
        obj["color_changes_mm"] = []
    changes = list(obj["color_changes_mm"])
    changes.append(z_mm)
    obj["color_changes_mm"] = sorted(set(changes))
    print(f"[COLOR] {obj.name} pause markers at Z={obj['color_changes_mm']} mm")
```

Approccio 2 — **split effettivo** e assemblaggio manuale post-stampa (per parti incollabili):
```python
# Usa split_two_halves(obj, cut_z_mm=z_pause, fill=False)
# Esporta separatamente, stampa sequenziale, incolla.
```

Bambu Studio supporta cambio colore nativo via pause G-code (da aggiungere in slicer), quindi **non** serve splittare la mesh per cambio colore — lasciare al slicer. Il marker custom property serve solo come reminder.

---

## 8. Cross-section planare (2D slice)

Estrai un contorno 2D dalla mesh a una Z data — utile per creare "sezioni" stampabili (cameo, silhouette).

```python
def extract_cross_section(obj, z_mm, extrude_mm=0.8):
    """
    Estrae la sezione trasversale della mesh a Z=z_mm e la estrude in un pezzo stampabile.
    Ritorna il nuovo oggetto.
    """
    # Duplica
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.duplicate()
    new = bpy.context.active_object
    new.name = obj.name + f"_slice_Z{int(z_mm)}"
    
    # Bisect e tieni solo la sezione piana
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(new.data)
    plane_co = Vector((0, 0, z_mm * 0.001))
    plane_no = Vector((0, 0, 1))
    
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    ret = bmesh.ops.bisect_plane(
        bm,
        geom=geom,
        plane_co=plane_co,
        plane_no=plane_no,
        clear_inner=True,
        clear_outer=True,
    )
    
    # ret contiene geom_cut = edge sul piano
    cut_edges = [g for g in ret.get('geom_cut', []) if isinstance(g, bmesh.types.BMEdge)]
    
    # Fill
    if cut_edges:
        fill = bmesh.ops.edgenet_fill(bm, edges=cut_edges)
        # Estrude le facce create
        face_list = fill.get('faces', [])
        if face_list:
            bmesh.ops.extrude_face_region(bm, geom=face_list)
            # Move extruded verts up by extrude_mm
            # Gli extruded verts sono quelli nuovi (dopo extrude_face_region)
            # Semplifichiamo: usa `translate` sulla selezione corrente in operator mode
    
    bmesh.update_edit_mesh(new.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Estrusione via Solidify (più affidabile dello modo manuale sopra)
    sol = new.modifiers.new("Solidify", type='SOLIDIFY')
    sol.thickness = extrude_mm * 0.001
    sol.offset = 1.0
    bpy.ops.object.select_all(action='DESELECT')
    new.select_set(True)
    bpy.context.view_layer.objects.active = new
    bpy.ops.object.modifier_apply(modifier="Solidify")
    
    print(f"[SLICE] {new.name}: Z={z_mm}mm, extruded {extrude_mm}mm")
    return new
```

---

## 9. Caveat e failure mode

| Sintomo | Causa | Fix |
|---|---|---|
| Faccia di taglio non si riempie (buco) | `edgenet_fill` non trova loop chiuso (self-intersection o buchi originali) | Sanitize mesh prima di bisect (vedi `[boolean_troubleshooting]`) |
| Pezzi bisect con normali flipped | L'originale aveva normali inconsistenti | `bpy.ops.mesh.normals_make_consistent(inside=False)` post-bisect |
| Piano coplanare con una faccia → geometria instabile | Floating point edge case | Sposta plane_co di ±0.001 mm (1e-6 BU) |
| Pin maschio non stampabile (overhang) | Piano di stampa è la faccia di taglio, il pin sporge lungo -Z | Stampare il pezzo BOTTOM con la faccia di taglio **in alto**, oppure invertire maschi/femmine |
| Pin clearance troppo serrata | clearance < 0.10 mm su A1 default | Aumentare clearance a 0.15 mm o calibrare XY Hole Compensation nello slicer |
| Slice 2D con n-gon non triangolato causa issue nel slicer | `fill_cut=True` lascia n-gon | Aggiungere `bmesh.ops.triangulate(bm, faces=...)` dopo il fill |

---

## 10. Quick reference

| Richiesta | Funzione |
|---|---|
| "dividilo a metà altezza" | `split_two_halves(obj, cut_z_mm)` |
| "dividilo in 4 pezzi orizzontali" | `split_n_horizontal(obj, 4)` |
| "tagliane via una fetta a 45°" | `cut_at_angle(obj, pivot_mm, tilt_angle_deg=45)` |
| "dividilo con pin per incollarlo" | `split_with_registration_pins(obj, cut_z_mm)` |
| "fai una silhouette 2D da qui" | `extract_cross_section(obj, z_mm)` |
| "dove cambio colore" | `mark_color_change(obj, z_mm)` (annotazione, il resto in slicer) |

---

## 11. Integrazione con altre KB

- Sanitize pre-bisect: `[boolean_troubleshooting]#2` (sanitize_for_boolean anche per bisect).
- Riposizionare pezzi dopo split: `[object_placement]` (`place_adjacent`, `pack_on_bed`).
- Export separato per ogni pezzo: `[import_export]` STL per oggetto o 3MF multi-part.
- Caso split oversized già coperto in semplice: `[workflow_patterns]#split-oversized`; qui l'estensione a N pezzi e puzzle cut.
- Per cut con supporto (Cut Tool di Bambu Studio con Plug/Dowel/Dovetail) vedere `[bambu_studio_settings]` — alternativa lato-slicer senza toccare la mesh.
