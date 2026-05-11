# Parametric Design Patterns — Blender Python per FDM

## Contesto

Questo documento raccoglie pattern Python pronti per progettare from-scratch geometrie stampabili direttamente in Blender. Tutti i valori sono in **mm** e convertiti internamente in BU (×0.001). I pattern rispettano le regole FDM della Bambu A1 con nozzle 0.4mm e PLA.

Prerequisito: `scale_length=0.001` attivo nella scena (1 BU = 1mm).

---

## Utility comuni

```python
import bpy
import bmesh
import math
from mathutils import Vector

def mm(x):
    """Converte mm in Blender Units (scale_length=0.001)."""
    return x * 0.001

def new_mesh_obj(name, mesh_data):
    """Crea e linka un oggetto mesh nella scena corrente."""
    obj = bpy.data.objects.new(name, mesh_data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj

def apply_all_transforms(obj):
    """Applica loc/rot/scale. Necessario prima di export o boolean."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
```

---

## Pattern 1: Box / Enclosure parametrico

Scatola con pareti di spessore definito, aperta su un lato (es. contenitore, case elettronico).

```python
import bpy
import bmesh
from mathutils import Vector

def create_box_enclosure(
    width_mm=60.0,
    depth_mm=40.0,
    height_mm=30.0,
    wall_mm=2.4,       # ≥ 6 pareti × 0.4mm nozzle per resistenza
    open_top=True,
    name="Enclosure"
):
    """
    Crea un box con pareti di spessore wall_mm.
    FDM: wall_mm minimo = 2× nozzle = 0.8mm; robusto = 6× nozzle = 2.4mm
    """
    w, d, h, wt = width_mm, depth_mm, height_mm, wall_mm
    
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm = bmesh.new()
    
    # Outer box
    outer_verts = [
        bm.verts.new(Vector((mm(x), mm(y), mm(z))))
        for x,y,z in [
            (0,0,0), (w,0,0), (w,d,0), (0,d,0),    # bottom
            (0,0,h), (w,0,h), (w,d,h), (0,d,h),    # top
        ]
    ]
    
    # Inner box (offset da wall_mm)
    inner_verts = [
        bm.verts.new(Vector((mm(x), mm(y), mm(z))))
        for x,y,z in [
            (wt, wt, wt), (w-wt, wt, wt), (w-wt, d-wt, wt), (wt, d-wt, wt),    # inner bottom
            (wt, wt, h),  (w-wt, wt, h),  (w-wt, d-wt, h),  (wt, d-wt, h),    # inner top
        ]
    ]
    
    bm.verts.ensure_lookup_table()
    
    def face(*indices):
        return bm.faces.new([bm.verts[i] for i in indices])
    
    # Facce esterne
    o = 0   # offset outer
    i = 8   # offset inner
    
    # Bottom (piena — outer solo, inner non tocca il fondo)
    face(o+0, o+1, o+2, o+3)  # outer bottom
    
    # Pareti outer (quad strip tra outer e inner)
    # Front (y=0)
    bm.faces.new([outer_verts[0], outer_verts[1], inner_verts[1], inner_verts[0]])
    # Right (x=w)
    bm.faces.new([outer_verts[1], outer_verts[2], inner_verts[2], inner_verts[1]])
    # Back (y=d)
    bm.faces.new([outer_verts[2], outer_verts[3], inner_verts[3], inner_verts[2]])
    # Left (x=0)
    bm.faces.new([outer_verts[3], outer_verts[0], inner_verts[0], inner_verts[3]])
    
    # Bottom frame (ring che unisce outer bottom e inner bottom)
    bm.faces.new([outer_verts[0], outer_verts[1], inner_verts[1], inner_verts[0]])
    bm.faces.new([outer_verts[1], outer_verts[2], inner_verts[2], inner_verts[1]])
    bm.faces.new([outer_verts[2], outer_verts[3], inner_verts[3], inner_verts[2]])
    bm.faces.new([outer_verts[3], outer_verts[0], inner_verts[0], inner_verts[3]])
    
    # Pareti outer alte
    for base_o, base_i in [(0,0),(1,1),(2,2),(3,3)]:
        o_bot = outer_verts[base_o]
        o_top = outer_verts[base_o + 4]
        i_bot = inner_verts[base_i]
        i_top = inner_verts[base_i + 4]
    
    # Semplificato: solidify modifier è più robusto per box
    # Usiamo approccio modifier invece
    bm.free()
    
    # Approccio semplificato con Solidify modifier
    mesh2 = bpy.data.meshes.new(f"{name}_mesh")
    bm2 = bmesh.new()
    bmesh.ops.create_cube(bm2, size=1)
    bm2.to_mesh(mesh2)
    bm2.free()
    
    obj = new_mesh_obj(name, mesh2)
    obj.scale = (mm(w), mm(d), mm(h))
    apply_all_transforms(obj)
    
    # Solidify per creare le pareti
    mod_solid = obj.modifiers.new("Shell", type='SOLIDIFY')
    mod_solid.thickness = -mm(wall_mm)  # negativo = verso interno
    mod_solid.offset = 1.0
    mod_solid.use_even_offset = True
    mod_solid.use_rim = True
    
    # Apri il top: rimuovi la faccia top
    if open_top:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier="Shell")
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        # Seleziona facce con normale verso Z+ (top)
        import bmesh as bm_mod
        bm3 = bm_mod.from_edit_mesh(obj.data)
        for face in bm3.faces:
            if face.normal.z > 0.9:  # facce che guardano verso l'alto
                face.select = True
        bm_mod.update_edit_mesh(obj.data)
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')
    
    print(f"Box '{name}': {w}×{d}×{h}mm, parete {wall_mm}mm")
    return obj
```

---

## Pattern 2: Bracket / Mensola a L parametrica

```python
import bpy
import bmesh
from mathutils import Vector

def create_l_bracket(
    flange_width_mm=40.0,   # larghezza flangia orizzontale
    flange_depth_mm=30.0,   # profondità flangia orizzontale
    wall_height_mm=40.0,    # altezza della parete verticale
    thickness_mm=3.0,       # spessore del materiale
    gusset_mm=15.0,         # triangolo di rinforzo (0 = nessuno)
    name="LBracket"
):
    """
    Bracket a L con flangia orizzontale, parete verticale, e gusset triangolare.
    FDM: stampare con parete verso il basso per massima resistenza a flessione.
    thickness_mm: ≥ 2.4mm (6 pareti) per parte strutturale
    """
    fw = flange_width_mm
    fd = flange_depth_mm
    wh = wall_height_mm
    t  = thickness_mm
    g  = gusset_mm
    
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm = bmesh.new()
    
    # Flangia orizzontale (piatta su XY, spessore su Z)
    verts_flange = [
        bm.verts.new(Vector((mm(x), mm(y), mm(z))))
        for x,y,z in [
            (0,0,0), (fw,0,0), (fw,fd,0), (0,fd,0),
            (0,0,t), (fw,0,t), (fw,fd,t), (0,fd,t),
        ]
    ]
    bmesh.ops.contextual_create(bm, geom=verts_flange)
    
    # Parete verticale (su XZ a y=0, spessore su Y)
    verts_wall = [
        bm.verts.new(Vector((mm(x), mm(y), mm(z))))
        for x,y,z in [
            (0,0,t), (fw,0,t), (fw,t,t), (0,t,t),            # bottom della parete = top della flangia
            (0,0,t+wh), (fw,0,t+wh), (fw,t,t+wh), (0,t,t+wh),
        ]
    ]
    bmesh.ops.contextual_create(bm, geom=verts_wall)
    
    # Gusset triangolare (se richiesto)
    if g > 0:
        # Triangolo nel piano YZ a x=fw/2
        x_mid = fw / 2
        gusset_verts = [
            bm.verts.new(Vector((mm(x_mid - t/2), mm(g), mm(t)))),  # punto base esterno
            bm.verts.new(Vector((mm(x_mid + t/2), mm(g), mm(t)))),
            bm.verts.new(Vector((mm(x_mid - t/2), mm(0), mm(t + g)))),  # punto cima
            bm.verts.new(Vector((mm(x_mid + t/2), mm(0), mm(t + g)))),
        ]
        bm.faces.new([gusset_verts[0], gusset_verts[1], gusset_verts[3], gusset_verts[2]])
    
    # Unifica e ricalcola normali
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=mm(0.01))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    
    obj = new_mesh_obj(name, mesh)
    apply_all_transforms(obj)
    
    print(f"Bracket '{name}': flange={fw}×{fd}mm, wall h={wh}mm, t={t}mm")
    return obj
```

---

## Pattern 3: Piastra con pattern di fori

Piastra rettangolare con fori in griglia o pattern personalizzato.

```python
import bpy
import bmesh
import math
from mathutils import Vector, Matrix

def create_plate_with_holes(
    width_mm=80.0,
    depth_mm=60.0,
    thickness_mm=3.0,
    hole_diameter_mm=3.4,    # 3.4mm = foro M3 per inserto termico (FDM regola)
    hole_rows=2,
    hole_cols=3,
    hole_margin_mm=8.0,      # margine dal bordo al centro del foro
    countersink=False,
    name="MountingPlate"
):
    """
    Piastra di montaggio con fori in griglia.
    hole_diameter_mm: standard FDM = diametro nominale + 0.4mm clearance
    Esempi: M3=3.4mm, M4=4.4mm, M5=5.4mm (inserti termici)
    """
    w, d, t = width_mm, depth_mm, thickness_mm
    r = hole_diameter_mm / 2
    
    # Crea il box base
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bm.to_mesh(mesh)
    bm.free()
    
    obj = new_mesh_obj(name, mesh)
    obj.scale = (mm(w), mm(d), mm(t))
    obj.location = (mm(w/2), mm(d/2), mm(t/2))
    apply_all_transforms(obj)
    
    # Calcola posizioni fori
    if hole_rows == 1 and hole_cols == 1:
        hole_positions = [(w/2, d/2)]
    else:
        x_positions = [hole_margin_mm + i*(w - 2*hole_margin_mm)/(max(hole_cols-1,1))
                      for i in range(hole_cols)]
        y_positions = [hole_margin_mm + i*(d - 2*hole_margin_mm)/(max(hole_rows-1,1))
                      for i in range(hole_rows)]
        hole_positions = [(x,y) for y in y_positions for x in x_positions]
    
    # Crea cilindri cutter per ogni foro
    cutters = []
    for hx, hy in hole_positions:
        cutter_data = bpy.data.meshes.new("hole_cutter")
        bm_c = bmesh.new()
        bmesh.ops.create_cone(
            bm_c,
            cap_ends=True,
            cap_tris=False,
            segments=16,
            radius1=mm(r),
            radius2=mm(r),
            depth=mm(t + 0.2),  # leggermente più alto per boolean pulito
        )
        bm_c.to_mesh(cutter_data)
        bm_c.free()
        
        cutter = bpy.data.objects.new("HoleCutter", cutter_data)
        bpy.context.collection.objects.link(cutter)
        cutter.location = (mm(hx), mm(hy), mm(t/2))
        apply_all_transforms(cutter)
        cutters.append(cutter)
    
    # Applica boolean per ogni foro
    bpy.context.view_layer.objects.active = obj
    for cutter in cutters:
        mod = obj.modifiers.new("Hole", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = cutter
        mod.solver = 'EXACT'
        bpy.ops.object.modifier_apply(modifier="Hole")
        bpy.data.objects.remove(cutter, do_unlink=True)
    
    print(f"Piastra '{name}': {w}×{d}×{t}mm, {len(hole_positions)} fori Ø{hole_diameter_mm}mm")
    return obj
```

---

## Pattern 4: Gusset / Rib di rinforzo

```python
import bpy
import bmesh
from mathutils import Vector
import math

def add_gusset_rib(
    base_obj,
    position_mm=(0, 0, 0),  # centro del gusset in world space mm
    width_mm=3.0,            # spessore del rib
    height_mm=20.0,          # altezza
    depth_mm=15.0,            # profondità (proiezione orizzontale)
    axis='X',               # asse lungo cui corre il rib
    name="Gusset"
):
    """
    Aggiunge un triangolo di rinforzo gusset all'oggetto base.
    Orientamento FDM: il rib dovrebbe avere layer lines parallele alla forza.
    
    width_mm: ≥ 2× nozzle = 0.8mm; robusto ≥ 2.4mm
    """
    w, h, dep = width_mm, height_mm, depth_mm
    x0, y0, z0 = [v * 0.001 for v in position_mm]
    
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm = bmesh.new()
    
    if axis == 'X':
        # Rib che corre lungo X, si innalza su Z, profondo su Y
        hw = mm(w/2)
        verts = [
            bm.verts.new(Vector((x0, y0, z0))),
            bm.verts.new(Vector((x0, y0 + mm(dep), z0))),
            bm.verts.new(Vector((x0, y0, z0 + mm(h)))),
            bm.verts.new(Vector((x0 + hw, y0, z0))),
            bm.verts.new(Vector((x0 + hw, y0 + mm(dep), z0))),
            bm.verts.new(Vector((x0 + hw, y0, z0 + mm(h)))),
        ]
        # Facce
        bm.faces.new([verts[0], verts[1], verts[2]])  # triangolo sinistra
        bm.faces.new([verts[3], verts[5], verts[4]])  # triangolo destra
        bm.faces.new([verts[0], verts[3], verts[4], verts[1]])  # bottom
        bm.faces.new([verts[0], verts[2], verts[5], verts[3]])  # back
        bm.faces.new([verts[1], verts[4], verts[5], verts[2]])  # hypotenuse face
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    
    rib_obj = new_mesh_obj(name, mesh)
    
    # Unisce con base (opzionale)
    # Se vuoi unirlo: seleziona entrambi e usa bpy.ops.object.join()
    
    print(f"Gusset '{name}': {w}×{h}×{dep}mm lungo {axis}")
    return rib_obj
```

---

## Pattern 5: Chamfer e Fillet FDM

Per design FDM, chamfer è preferito al fillet perché è più semplice geometricamente e non crea sliver faces.

### Chamfer via Bevel modifier

```python
import bpy

def add_fdm_chamfer(obj, width_mm=0.5, segments=1, limit_method='ANGLE'):
    """
    Aggiunge chamfer agli spigoli vivi via Bevel modifier.
    
    width_mm: 
        - 0.4–0.5mm → chamfer minimo (anti-elephant-foot)
        - 1.0–2.0mm → chamfer decorativo/funzionale
    segments=1 → chamfer (spigolo dritto)
    segments=3–5 → fillet approssimato (curvo)
    limit_method='ANGLE' → solo spigoli con angolo < soglia (default ~30°)
    """
    mod = obj.modifiers.new("Chamfer", type='BEVEL')
    mod.width = mm(width_mm)
    mod.segments = segments
    mod.limit_method = limit_method  # 'ANGLE' | 'WEIGHT' | 'VGROUP'
    
    if limit_method == 'ANGLE':
        mod.angle_limit = 1.0472  # radianti ≈ 60° — spigoli acuti
    
    # Per uso con boolean successivi: applica il modifier
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Chamfer")
    
    print(f"Chamfer applicato: {width_mm}mm, {segments} segmenti")
    return obj

# Regole FDM per chamfer:
# - Base dell'oggetto: chamfer 0.4–0.5mm per compensare elephant foot
# - Spigoli superiori: chamfer 0.5–1mm per overhang graceful degradation
# - Fori: chamfer 0.3–0.5mm per agevolare inserimento viti/pin
```

### Fillet approssimato con SubSurf

```python
import bpy

def add_smooth_fillet(obj, radius_mm=2.0, crease_sharp_edges=True):
    """
    Fillet soft via Subdivision Surface + crease su spigoli da preservare.
    Usare per oggetti organici; non adatto a parti meccaniche di precisione.
    
    radius_mm approssimato: corrisponde circa a livello 2 + crease 0.8
    """
    # Aggiungi crease agli spigoli da preservare (valore 1.0 = spigolo vivo)
    if crease_sharp_edges:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        # Imposta crease (richiede data layer)
        bpy.ops.transform.edge_crease(value=0.8)  # 0.0–1.0
        bpy.ops.object.mode_set(mode='OBJECT')
    
    mod = obj.modifiers.new("SmoothFillet", type='SUBSURF')
    mod.levels = 2           # livello viewport
    mod.render_levels = 2
    
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="SmoothFillet")
    
    print(f"Fillet smooth applicato (SubSurf 2)")
    return obj
```

---

## Tabella: regole FDM per design parametrico

| Feature | Minimo | Raccomandato | Note |
|---|---|---|---|
| Spessore parete | 0.8mm (2× nozzle) | 2.4mm (6×) | Sotto 0.8mm slicer ignora |
| Larghezza rib | 1.2mm (3×) | 2.4mm | ≥ 3 perimetri per resistenza |
| Chamfer base | 0.4mm | 0.5mm | Compensazione elephant foot |
| Foro M3 (inserto) | 3.8mm Ø | 4.0mm Ø | Con XY Hole Compensation +0.1mm |
| Foro M3 (autofilettante) | 2.5mm Ø | 2.6mm Ø | PLA — vedere threads_and_fasteners.md |
| Boss per vite | Ø_ext = 2.5× vite | 3× vite | Parete minima boss ≥ 2.4mm |
| Overhang senza supporto | < 45° | < 40° | Regola conservativa FDM |
| Bridge senza supporto | ≤ 40mm | ≤ 25mm | PLA A1 standard |
| Distanza tra fori | ≥ 3mm bordo a bordo | ≥ 5mm | Meno con pareti rinforzate |
