# Functional Patterns Library — Ingranaggi, cerniere, scatole, manopole

## Contesto

`parametric_design_patterns` copre box/L-bracket/piastra/gusset/chamfer. Questo documento estende la libreria ad altri oggetti funzionali frequentemente richiesti all'agente: **ingranaggi**, **cerniere (pin hinge)**, **scatole con coperchio friction-fit**, **manopole godronate**, **clip per cavi**.

Tutti i pattern sono parametrici (input in mm), rispettano i vincoli FDM Bambu A1 PLA nozzle 0.4 mm, e ritornano un bpy.types.Object pronto per altre operazioni (boolean UNION, placement, export).

Prerequisito: `scale_length=0.001`. Utility `mm()` e `new_mesh_obj()` definite in `[parametric_design_patterns]` (ripetute qui per leggibilità).

```python
import bpy
import bmesh
import math
from mathutils import Vector

def mm(x): return x * 0.001

def _select_only(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def _apply_transforms(obj):
    _select_only(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
```

---

## 1. Spur Gear (ingranaggio cilindrico parametrico)

### Teoria di base

Per uno spur gear a denti trapezoidali (approssimazione funzionale — non involute true — sufficiente per accoppiamenti a bassa velocità stampati in PLA):

- **Modulo m** (mm): definisce la dimensione del dente. `m = pitch_diameter / N_teeth`
- **N**: numero di denti (≥ 12 per avoidare undercut)
- **Pitch diameter**: `D_p = m × N`
- **Addendum** (sporgenza dente sopra pitch): `a = m`
- **Dedendum** (incavo sotto pitch): `b = 1.25 × m`
- **Outer diameter** (addendum): `D_o = D_p + 2a = m × (N + 2)`
- **Root diameter** (dedendum): `D_r = D_p − 2b = m × (N − 2.5)`
- **Tooth thickness** (sul pitch circle): `t = π × m / 2`
- **Pressure angle**: irrelevante per denti trapezoidali, per riferimento 20°

Per **stampabilità FDM** con nozzle 0.4 mm:
- **Modulo minimo** ~1.5 mm (denti più piccoli hanno troppa perdita di geometria per nozzle width)
- **Modulo raccomandato** 2–3 mm per ingranaggi funzionali

### Codice

```python
def create_spur_gear(
    module_mm=2.0,
    n_teeth=20,
    thickness_mm=5.0,
    bore_diameter_mm=5.0,
    pressure_angle_deg=20,
    name="SpurGear",
):
    """
    Crea uno spur gear a denti trapezoidali.
    Approssimazione: denti con fianchi inclinati al pressure_angle (non involute, ma sufficiente per FDM PLA hobby).
    Il gear è centrato sull'origine, asse = Z, faccia bottom a Z=0.
    """
    if n_teeth < 10:
        raise ValueError("n_teeth < 10 causes strong undercut, not printable")
    
    m = module_mm
    Dp = m * n_teeth
    a = m
    b = 1.25 * m
    Do = Dp + 2 * a
    Dr = Dp - 2 * b
    
    pa_rad = math.radians(pressure_angle_deg)
    
    # Angolo per dente
    tooth_angle = 2 * math.pi / n_teeth
    # Larghezza dente sul pitch circle (arc)
    tooth_arc = math.pi * m / 2     # mm
    # Converti in angolo
    tooth_half_angle_on_pitch = tooth_arc / Dp   # radianti (approssimazione arco ≈ corda)
    
    # Costruiamo il profilo: per ogni dente, 4 punti (sul root e outer, con offset dovuto al pressure angle)
    bm = bmesh.new()
    
    # Lista di vertici del profilo (coord in mm su piano XY, Z=0)
    profile = []
    for i in range(n_teeth):
        theta = i * tooth_angle
        
        # Root sinistro
        a_root_L = theta - (tooth_angle / 2) + tooth_half_angle_on_pitch * 0.5
        p_root_L = (Dr/2 * math.cos(a_root_L), Dr/2 * math.sin(a_root_L))
        
        # Outer sinistro (offset angolare verso il centro del dente per simulare pressure angle)
        inset = (Do - Dp) / 2 * math.tan(pa_rad) / (Do/2)   # angolo di inset
        a_outer_L = theta - tooth_half_angle_on_pitch + inset
        p_outer_L = (Do/2 * math.cos(a_outer_L), Do/2 * math.sin(a_outer_L))
        
        # Outer destro
        a_outer_R = theta + tooth_half_angle_on_pitch - inset
        p_outer_R = (Do/2 * math.cos(a_outer_R), Do/2 * math.sin(a_outer_R))
        
        # Root destro
        a_root_R = theta + (tooth_angle / 2) - tooth_half_angle_on_pitch * 0.5
        p_root_R = (Dr/2 * math.cos(a_root_R), Dr/2 * math.sin(a_root_R))
        
        profile.append(p_root_L)
        profile.append(p_outer_L)
        profile.append(p_outer_R)
        profile.append(p_root_R)
    
    # Crea vertici bottom
    verts_bottom = [bm.verts.new(Vector((mm(x), mm(y), 0))) for x, y in profile]
    # Face bottom (n-gon)
    face_bottom = bm.faces.new(verts_bottom)
    
    # Extrude su Z per creare lo spessore
    geom_extrude = bmesh.ops.extrude_face_region(bm, geom=[face_bottom])
    top_verts = [v for v in geom_extrude["geom"] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=Vector((0, 0, mm(thickness_mm))), verts=top_verts)
    
    # Bore centrale (foro)
    if bore_diameter_mm > 0:
        # Cilindro centrale da sottrarre — usiamo approccio: aggiungere foro come shape via bmesh
        # Più semplice: fare bore con Boolean DIFFERENCE dopo aver creato la mesh
        pass
    
    # Crea mesh e oggetto
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    gear = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(gear)
    bpy.context.view_layer.objects.active = gear
    
    # Recalc normals
    _select_only(gear)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Bore via Boolean
    if bore_diameter_mm > 0:
        bpy.ops.mesh.primitive_cylinder_add(
            radius=mm(bore_diameter_mm / 2),
            depth=mm(thickness_mm * 2 + 2),
            location=(0, 0, mm(thickness_mm / 2)),
        )
        cutter = bpy.context.active_object
        
        _select_only(gear)
        mod = gear.modifiers.new("Bore", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.solver = 'EXACT'
        mod.object = cutter
        bpy.ops.object.modifier_apply(modifier="Bore")
        bpy.data.objects.remove(cutter, do_unlink=True)
    
    print(f"[GEAR] {name}: m={m}mm, N={n_teeth}, Dp={Dp:.2f}, Do={Do:.2f}, "
          f"Dr={Dr:.2f}, thickness={thickness_mm}mm, bore=Ø{bore_diameter_mm}mm")
    return gear
```

### Tabella quick reference gears per FDM

| Applicazione | Modulo | N teeth | Thickness | Bore |
|---|---|---|---|---|
| Toys / decorative | 1.5–2 mm | 16–24 | 4–6 mm | Ø4–5 mm |
| Small mechanism | 2 mm | 20–40 | 5–8 mm | Ø5–8 mm |
| Torque transmission | 3 mm | 20–60 | 10–15 mm | Ø8–12 mm |
| Heavy duty | 4–5 mm | 30–80 | 15–25 mm | Ø12–20 mm |

### Accoppiamento gear ↔ gear

Due gear si accoppiano correttamente se hanno **stesso modulo**. Il **center distance** tra i due assi = (Dp1 + Dp2) / 2. Per FDM aggiungere **0.3–0.5 mm** di clearance al center distance (per backlash compensation).

---

## 2. Pin Hinge (cerniera con perno)

### Topologia

- Due halves (A e B) che girano attorno a un asse comune
- A ha **knuckles** (tubi cavi) alternati a gap
- B ha **knuckles** complementari che si interdigitano con A
- Un **pin** (stampato o commerciale, es. ferro filato Ø3 mm) passa attraverso tutti i knuckles

### Parametri

- **Pin diameter** (nominale): 3 mm
- **Knuckle outer diameter**: pin_dia + 2 × wall ≥ pin_dia + 3 mm (wall min 1.5 mm)
- **Knuckle bore**: pin_dia + 0.4 mm clearance (rotazione libera)
- **Knuckle count per half**: 2–4 per half (4–8 totali)
- **Knuckle length**: 8–12 mm ciascuno
- **Gap tra knuckles**: 0.2 mm (minimal per evitare friction)

### Codice

```python
def create_pin_hinge(
    total_length_mm=60.0,
    plate_width_mm=20.0,
    plate_thickness_mm=3.0,
    pin_diameter_mm=3.0,
    knuckle_wall_mm=1.5,
    pin_clearance_mm=0.2,       # radiale
    n_knuckles_total=5,          # totale, devi essere dispari (2 su A, 3 su B oppure viceversa)
    name="Hinge",
):
    """
    Crea due halves di una pin hinge. Il pin va acquistato separatamente (o stampato).
    Il pivot è sul bordo verso +Y di ciascuna half.
    Halves sono posizionate affiancate con gap 0.2 mm.
    
    Ritorna (half_a, half_b).
    """
    if n_knuckles_total % 2 == 0:
        raise ValueError("n_knuckles_total must be odd (interleaving)")
    
    # Dimensionamento knuckles
    knuckle_od = pin_diameter_mm + 2 * knuckle_wall_mm
    knuckle_bore = pin_diameter_mm + 2 * pin_clearance_mm
    gap_between = 0.2   # mm
    # ogni knuckle ha length = (total_length - (n-1)*gap) / n
    knuckle_len = (total_length_mm - (n_knuckles_total - 1) * gap_between) / n_knuckles_total
    
    halves = []
    
    for half_idx in range(2):
        # Crea piastra base
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        plate = bpy.context.active_object
        plate.name = f"{name}_half{half_idx}_plate"
        plate.scale = (
            mm(plate_width_mm),
            mm(total_length_mm),
            mm(plate_thickness_mm),
        )
        plate.location = (
            mm(-plate_width_mm / 2) if half_idx == 0 else mm(plate_width_mm / 2),
            0,
            mm(plate_thickness_mm / 2),
        )
        _select_only(plate)
        bpy.ops.object.transform_apply(location=True, scale=True)
        
        # Aggiungi knuckles (indici del half_idx sono 0,2,4,... oppure 1,3,5,...)
        knuckle_indices = range(half_idx, n_knuckles_total, 2)
        for i in knuckle_indices:
            # centro Y del knuckle i
            y_start = -total_length_mm / 2 + i * (knuckle_len + gap_between)
            y_center = y_start + knuckle_len / 2
            
            # Pivot sul bordo Y della piastra (half A su -X side, half B su +X side)
            # I knuckle stanno sul bordo verso l'interno (verso x=0)
            # Posizione X del pivot: bordo interno della piastra
            pivot_x = 0   # entrambi gli halves hanno knuckles centrati su x=0
            pivot_z = mm(plate_thickness_mm / 2)     # centro spessore piastra
            
            # Knuckle esterno (cilindro)
            bpy.ops.mesh.primitive_cylinder_add(
                radius=mm(knuckle_od / 2),
                depth=mm(knuckle_len),
                location=(pivot_x, mm(y_center), pivot_z),
                rotation=(math.radians(90), 0, 0),   # asse Y
            )
            k_outer = bpy.context.active_object
            k_outer.name = f"_k_outer_{half_idx}_{i}"
            
            # UNION con plate
            _select_only(plate)
            mod = plate.modifiers.new(f"_ku_{i}", type='BOOLEAN')
            mod.operation = 'UNION'
            mod.solver = 'EXACT'
            mod.object = k_outer
            bpy.ops.object.modifier_apply(modifier=f"_ku_{i}")
            bpy.data.objects.remove(k_outer, do_unlink=True)
        
        # Ora buco pin: cilindro passante attraverso tutta la lunghezza Y
        bpy.ops.mesh.primitive_cylinder_add(
            radius=mm(knuckle_bore / 2),
            depth=mm(total_length_mm + 2),
            location=(0, 0, mm(plate_thickness_mm / 2)),
            rotation=(math.radians(90), 0, 0),
        )
        pin_hole = bpy.context.active_object
        _select_only(plate)
        mod = plate.modifiers.new("_pin_bore", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.solver = 'EXACT'
        mod.object = pin_hole
        bpy.ops.object.modifier_apply(modifier="_pin_bore")
        bpy.data.objects.remove(pin_hole, do_unlink=True)
        
        halves.append(plate)
    
    print(f"[HINGE] {name}: {n_knuckles_total} knuckles, pin Ø{pin_diameter_mm}+{pin_clearance_mm*2}mm clearance")
    return halves[0], halves[1]
```

### Stampa della cerniera

- **Orientamento**: entrambi gli halves piatti sul bed (piastre orizzontali, knuckles con asse parallelo al bed)
- **Supporti**: serve support painting solo sotto i knuckles (overhang >45°). Usare Tree support + Support Painting Sphere tool (vedi `[support_strategy]`)
- **Test pre-stampa**: stamparne una versione mini (length 20 mm, 3 knuckles) per calibrare clearance

---

## 3. Box with Lid (friction-fit)

Estensione del `Box Enclosure` di `[parametric_design_patterns]` con **coperchio** accoppiato via lip friction-fit.

### Design

- **Box**: pareti spesse `wall_mm` (tipico 2.4 mm = 6 perimetri); aperta verso +Z
- **Lid**: disco con lip che si inserisce DENTRO la bocca del box
- **Lip height**: 4–6 mm (stabilità contro rollio)
- **Lip clearance**: 0.2 mm (friction-fit); 0.3 mm (slip-fit facile)
- **Lid overhang**: 1–2 mm sporgenza oltre il bordo esterno del box (facilita apertura)

### Codice

```python
def create_box_with_lid(
    outer_w_mm=60.0,
    outer_d_mm=40.0,
    outer_h_mm=30.0,
    wall_mm=2.4,
    lid_overhang_mm=1.5,
    lip_height_mm=5.0,
    lip_clearance_mm=0.25,
    lid_thickness_mm=2.0,
    name="BoxLid",
):
    """
    Crea (box, lid). Il box è open-top. Il lid ha un lip che entra nel box.
    Entrambi sono centrati sull'origine con base a Z=0.
    Il lid è posizionato sopra il box per visualizzazione.
    """
    # === BOX ===
    # Outer cube
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    box = bpy.context.active_object
    box.name = name + "_box"
    box.scale = (mm(outer_w_mm), mm(outer_d_mm), mm(outer_h_mm))
    box.location = (0, 0, mm(outer_h_mm / 2))
    _apply_transforms(box)
    
    # Inner cutter (hollow)
    inner_w = outer_w_mm - 2 * wall_mm
    inner_d = outer_d_mm - 2 * wall_mm
    inner_h = outer_h_mm - wall_mm   # chiude il fondo, lascia aperto il top
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    cutter = bpy.context.active_object
    cutter.scale = (mm(inner_w), mm(inner_d), mm(inner_h))
    cutter.location = (0, 0, mm(wall_mm + inner_h / 2 + 1))   # +1 mm per uscire dal top (no coplanarità)
    _apply_transforms(cutter)
    
    _select_only(box)
    mod = box.modifiers.new("Hollow", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    bpy.ops.object.modifier_apply(modifier="Hollow")
    bpy.data.objects.remove(cutter, do_unlink=True)
    
    # === LID ===
    lid_w = outer_w_mm + 2 * lid_overhang_mm
    lid_d = outer_d_mm + 2 * lid_overhang_mm
    
    # Lid top plate
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    lid = bpy.context.active_object
    lid.name = name + "_lid"
    lid.scale = (mm(lid_w), mm(lid_d), mm(lid_thickness_mm))
    
    # Posizionalo sopra il box (a Z = outer_h + lid_thickness/2)
    lid.location = (0, 0, mm(outer_h_mm + lid_thickness_mm / 2))
    _apply_transforms(lid)
    
    # Lid lip: blocco inferiore con dimensioni interne - clearance
    lip_w = inner_w - 2 * lip_clearance_mm
    lip_d = inner_d - 2 * lip_clearance_mm
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    lip = bpy.context.active_object
    lip.scale = (mm(lip_w), mm(lip_d), mm(lip_height_mm))
    # Lip si estende verso il basso dal lid
    lip.location = (0, 0, mm(outer_h_mm - lip_height_mm / 2))
    _apply_transforms(lip)
    
    _select_only(lid)
    mod = lid.modifiers.new("AddLip", type='BOOLEAN')
    mod.operation = 'UNION'
    mod.solver = 'EXACT'
    mod.object = lip
    bpy.ops.object.modifier_apply(modifier="AddLip")
    bpy.data.objects.remove(lip, do_unlink=True)
    
    print(f"[BOX-LID] box {outer_w_mm}×{outer_d_mm}×{outer_h_mm}mm wall {wall_mm}mm")
    print(f"[BOX-LID] lid {lid_w:.1f}×{lid_d:.1f}mm overhang {lid_overhang_mm}mm, lip h={lip_height_mm}mm clearance={lip_clearance_mm}mm")
    return box, lid
```

### Calibrazione lip_clearance_mm per A1 PLA

| Clearance | Fit |
|---|---|
| 0.10 mm | Press-fit (martellata) — sconsigliato, rischio crack |
| 0.20 mm | Friction-fit stretto (default raccomandato) |
| 0.25 mm | Friction-fit standard |
| 0.35 mm | Slip-fit facile (usa-e-getta) |
| 0.50 mm | Molto lasco — aggiungi guarnizione |

Con XY Hole/Contour Compensation calibrata (vedi `[tolerances_and_fits]`) questi valori si abbassano di ~0.05 mm.

---

## 4. Knurled Knob (manopola godronata)

Manopola cilindrica con godronatura (flutes) sulla circonferenza per presa, bore centrale per D-shaft o asse con set-screw.

### Codice

```python
def create_knurled_knob(
    diameter_mm=25.0,
    height_mm=12.0,
    shaft_diameter_mm=6.0,
    n_flutes=16,
    flute_depth_mm=1.0,
    top_chamfer_mm=1.0,
    name="Knob",
):
    """
    Crea una manopola godronata.
    Flute = scanalatura sulla circonferenza, creata da Boolean DIFFERENCE
    di N cilindri piccoli ruotati attorno all'asse.
    """
    # Corpo base
    bpy.ops.mesh.primitive_cylinder_add(
        radius=mm(diameter_mm / 2),
        depth=mm(height_mm),
        location=(0, 0, mm(height_mm / 2)),
        vertices=64,
    )
    knob = bpy.context.active_object
    knob.name = name
    _apply_transforms(knob)
    
    # Shaft bore
    if shaft_diameter_mm > 0:
        bpy.ops.mesh.primitive_cylinder_add(
            radius=mm(shaft_diameter_mm / 2),
            depth=mm(height_mm * 2 + 2),
            location=(0, 0, mm(height_mm / 2)),
        )
        cutter = bpy.context.active_object
        _select_only(knob)
        mod = knob.modifiers.new("Bore", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.solver = 'EXACT'
        mod.object = cutter
        bpy.ops.object.modifier_apply(modifier="Bore")
        bpy.data.objects.remove(cutter, do_unlink=True)
    
    # Flutes: N cilindri piccoli alla periferia, distanziati angolarmente
    flute_radius = mm(flute_depth_mm)   # raggio del cilindro flute
    flute_orbit_radius = mm(diameter_mm / 2)   # distanza dal centro
    
    for i in range(n_flutes):
        angle = 2 * math.pi * i / n_flutes
        px = flute_orbit_radius * math.cos(angle)
        py = flute_orbit_radius * math.sin(angle)
        
        bpy.ops.mesh.primitive_cylinder_add(
            radius=flute_radius,
            depth=mm(height_mm + 2),
            location=(px, py, mm(height_mm / 2)),
            vertices=16,
        )
        flute = bpy.context.active_object
        
        _select_only(knob)
        mod = knob.modifiers.new(f"_f_{i}", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.solver = 'EXACT'
        mod.object = flute
        bpy.ops.object.modifier_apply(modifier=f"_f_{i}")
        bpy.data.objects.remove(flute, do_unlink=True)
    
    # Chamfer top — via Bevel modifier sugli edge top
    if top_chamfer_mm > 0:
        bv = knob.modifiers.new("Chamfer", type='BEVEL')
        bv.width = mm(top_chamfer_mm)
        bv.segments = 3
        bv.limit_method = 'ANGLE'
        bv.angle_limit = math.radians(30)
        _select_only(knob)
        bpy.ops.object.modifier_apply(modifier="Chamfer")
    
    print(f"[KNOB] {name}: Ø{diameter_mm}×{height_mm}mm, shaft Ø{shaft_diameter_mm}mm, {n_flutes} flutes")
    return knob
```

### Varianti della manopola

- **D-shaft**: sostituire il foro circolare con un foro a D (cutter = cilindro + cubo flat su un lato)
- **Set-screw hole**: aggiungere un foro radiale M3 (3.4 mm) con boss interno (vedi `[threads_and_fasteners]`)
- **Hexagonal grip**: sostituire flutes cilindrici con `primitive_circle_add(vertices=6)` estruso

---

## 5. Cable Clip (fermacavo a C)

Clip a C per fissare cavi al bordo di una scrivania o sopra un pannello. Stampa molto semplice, funzionale.

```python
def create_cable_clip(
    cable_diameter_mm=5.0,
    opening_gap_mm=3.0,        # apertura dove entra il cavo — deve essere < cable_d per snap
    wall_mm=2.0,
    length_mm=15.0,
    name="CableClip",
):
    """
    Clip a C che tiene un cavo via snap-fit.
    Stampa con asse lungo Y, apertura verso +X.
    """
    outer_r = cable_diameter_mm / 2 + wall_mm
    inner_r = cable_diameter_mm / 2 + 0.1    # clearance minima
    
    # Anello esterno
    bpy.ops.mesh.primitive_cylinder_add(
        radius=mm(outer_r),
        depth=mm(length_mm),
        rotation=(math.radians(90), 0, 0),
        location=(0, 0, mm(outer_r)),
        vertices=48,
    )
    clip = bpy.context.active_object
    clip.name = name
    _apply_transforms(clip)
    
    # Inner cylinder (diametro cavo) — sottrae
    bpy.ops.mesh.primitive_cylinder_add(
        radius=mm(inner_r),
        depth=mm(length_mm + 2),
        rotation=(math.radians(90), 0, 0),
        location=(0, 0, mm(outer_r)),
        vertices=48,
    )
    inner = bpy.context.active_object
    
    _select_only(clip)
    mod = clip.modifiers.new("Bore", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = inner
    bpy.ops.object.modifier_apply(modifier="Bore")
    bpy.data.objects.remove(inner, do_unlink=True)
    
    # Taglio per apertura: cubo sottratto su +X
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    gap = bpy.context.active_object
    gap.scale = (mm(outer_r * 2 + 2), mm(length_mm + 2), mm(opening_gap_mm))
    gap.location = (mm(outer_r), 0, mm(outer_r))   # centrato sul lato +X dell'anello
    _apply_transforms(gap)
    
    _select_only(clip)
    mod = clip.modifiers.new("Gap", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = gap
    bpy.ops.object.modifier_apply(modifier="Gap")
    bpy.data.objects.remove(gap, do_unlink=True)
    
    print(f"[CLIP] {name}: cable Ø{cable_diameter_mm}mm, gap {opening_gap_mm}mm (snap-fit)")
    return clip
```

---

## 6. Quick reference — richieste e pattern

| Utente chiede | Pattern |
|---|---|
| "un ingranaggio per questo assale Ø5 mm" | `create_spur_gear(module_mm=2, n_teeth=20, bore_diameter_mm=5.4)` |
| "una cerniera" | `create_pin_hinge(pin_diameter_mm=3, total_length_mm=60)` |
| "una scatolina con coperchio" | `create_box_with_lid(60, 40, 30, 2.4)` |
| "una manopola da stampare" | `create_knurled_knob(diameter_mm=25, shaft_diameter_mm=6)` |
| "clip per organizzare cavi" | `create_cable_clip(cable_diameter_mm=5, opening_gap_mm=3)` |

---

## 7. Caveat generali

- Tutti questi pattern **chiudono** con Boolean EXACT; l'agente deve applicare `sanitize_for_boolean` se il risultato viene passato a un'altra operazione booleana (vedi `[boolean_troubleshooting]`).
- I valori di clearance/wall sono baseline per A1 default; calibrare con test prints se si lavora con profili BS non standard.
- Per oggetti con requisiti meccanici rigorosi (torque, fatica), consultare `[assembly_design]` per le proprietà meccaniche PLA FDM e `[advanced_slicing_params]` per i ricette slicer (alta resistenza).
- **Per ingranaggi true-involute**, l'approssimazione trapezoidale qui è inadeguata — usare plugin esterni (FreeCAD, OpenSCAD involute_gears library) e importare STL. L'agente può segnalare questo se il modulo/N_teeth richiede precisione cinematica.
