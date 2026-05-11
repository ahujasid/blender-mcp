# Image-to-Mesh e SVG-to-Mesh — Pipeline FDM

## Contesto

Input 2D (immagini raster o vettoriali SVG) trasformati in mesh stampabili. Questo copre tre famiglie di richieste molto comuni che `ai_mesh_recipe` e `photogrammetry_recipe` non coprono:

1. **Lithophane** — immagine in scala di grigi → rilievo a spessore variabile (0.8–3.2 mm) che in retroilluminazione rivela l'immagine.
2. **Heightmap terrain** — immagine di elevazione → superficie topografica con base piatta.
3. **SVG-to-3D** — logo/silhouette vettoriale → mesh estrusa (keychain, badge, token, stencil).

Prerequisito: `scale_length=0.001` attivo (1 BU = 1 mm). Nozzle 0.4 mm, PLA, Bambu A1.

Regola trasversale FDM: qualsiasi feature <0.4 mm è sotto nozzle e scompare. Lithophane profondità minima 0.8 mm (2 layer a 0.12 mm × 4 perimetri pieni = trasmissione luce stabile). Spessore massimo utile ~3.2 mm (oltre, la luce non passa più).

---

## 1. Lithophane — grayscale image → height mesh

### Parametri di design

| Parametro | Valore tipico | Note |
|---|---|---|
| Width / Height | 100–200 mm | Limite build volume 256 mm, 150×100 è sweet spot |
| Back thickness | 0.8 mm | Fondo nero, dà rigidità |
| Max thickness | 3.2 mm | Zone più chiare (più materiale = meno luce) |
| Layer height stampa | 0.08–0.12 mm | Obbligatorio per gradazioni fluide |
| Perimetri | 4+ | Altrimenti infill visibile in retro-illuminazione |
| Infill | 100% | Lithophane NON va svuotata |
| Orientamento stampa | Verticale (asse Y) | Layer lines verticali = strisce meno visibili frontale |
| Risoluzione mesh | 1 vertex per pixel (o /2) | Più di così è spreco |
| Sampling texture | `FLAT` filter, `EXTEND` extension | No interpolazione (stepping voluto) |

**Mapping luminosità → spessore**: per lithophane classica in retro-illuminazione, **pixel bianco = più sottile** (più luce passa), **pixel nero = più spesso** (blocca luce). Quindi il displace va invertito rispetto al default.

### Schema di implementazione

- Caricare immagine come `bpy.data.images.load(path)`
- Creare un piano con dimensioni corrette in mm
- Subdividerlo a risoluzione proporzionale ai pixel (clamping a max ~500×500 per performance)
- Creare texture di tipo `IMAGE` con `image` = immagine caricata, `extension='EXTEND'`, `use_interpolation` decidibile
- Displace modifier: `texture_coords='UV'`, `direction='Z'`, `mid_level=1.0` (pixel bianco → displace 0), `strength = -(max_thick - back_thick)` (negativo per invertire), con l'oggetto piano posizionato a `z = max_thickness`
- Solidify per back plate: `thickness = back_thick`, `offset=-1` (verso -Z)
- Apply modifiers prima dell'export

In alternativa al Solidify, si estrude manualmente il piano prima del displace (più robusto su bordi).

### Codice — CALL lithophane

```python
import bpy
import os

# === PARAMETRI ===
IMAGE_PATH = "/path/to/photo.jpg"    # path assoluto
WIDTH_MM = 150.0
HEIGHT_MM = 100.0
BACK_THICK_MM = 0.8
MAX_THICK_MM = 3.2
SUBDIV_RES = 400   # vertici per lato massimo (performance)
INVERT = True      # True = bianco sottile (retro-illuminata classica)
# ==================

def mm(x):
    return x * 0.001

# Cleanup oggetto esistente
if "Lithophane" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Lithophane"], do_unlink=True)

# Carica immagine
img = bpy.data.images.load(IMAGE_PATH, check_existing=True)
img_w, img_h = img.size
aspect = img_w / img_h
print(f"[IMG] size={img_w}x{img_h}, aspect={aspect:.3f}")

# Clamp risoluzione mesh: più bassa tra (pixel image, SUBDIV_RES)
res_x = min(img_w, SUBDIV_RES)
res_y = min(img_h, int(SUBDIV_RES / aspect))

# Crea piano
bpy.ops.mesh.primitive_plane_add(
    size=2.0,   # 2×2 BU, lo ridimensioniamo dopo
    location=(0, 0, mm(BACK_THICK_MM))   # base a Z=back_thick, il top è la superficie displacement
)
plane = bpy.context.active_object
plane.name = "Lithophane"

# Scala a dimensioni reali
plane.scale.x = mm(WIDTH_MM) / 2.0
plane.scale.y = mm(HEIGHT_MM) / 2.0
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Subdivide — serve in edit mode
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
# numero di cuts per lato = res - 1
n_cuts = max(res_x, res_y) - 1
bpy.ops.mesh.subdivide(number_cuts=n_cuts)
bpy.ops.object.mode_set(mode='OBJECT')

# UV: il piano creato da primitive_plane_add ha UV base già corretta [0,1]×[0,1]
# Se non ne è sicuri:
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project()
bpy.ops.object.mode_set(mode='OBJECT')

# Crea texture IMAGE
tex_name = "LithoTex"
if tex_name in bpy.data.textures:
    bpy.data.textures.remove(bpy.data.textures[tex_name])
tex = bpy.data.textures.new(tex_name, type='IMAGE')
tex.image = img
tex.extension = 'EXTEND'
tex.use_interpolation = True      # True = smoothing; False = stepping pixelato

# Displace modifier
disp = plane.modifiers.new("Displace", type='DISPLACE')
disp.texture = tex
disp.texture_coords = 'UV'
disp.direction = 'Z'
# Strategia classica: mid_level=1 (bianco=0 displace, nero=displace negativo max)
# con strength negativa, l'asse Z scende verso il basso
range_mm = MAX_THICK_MM - BACK_THICK_MM
if INVERT:
    disp.mid_level = 1.0
    disp.strength = -mm(range_mm)
else:
    disp.mid_level = 0.0
    disp.strength = mm(range_mm)

# Solidify per back plate — chiude il retro
solid = plane.modifiers.new("Solidify", type='SOLIDIFY')
solid.thickness = mm(BACK_THICK_MM)
solid.offset = -1.0   # tutto verso il basso (back plate sotto la superficie displace)
solid.use_even_offset = True
solid.use_quality_normals = True

# Apply modificatori
bpy.ops.object.select_all(action='DESELECT')
plane.select_set(True)
bpy.context.view_layer.objects.active = plane
bpy.ops.object.modifier_apply(modifier="Displace")
bpy.ops.object.modifier_apply(modifier="Solidify")

# Valida
dims = plane.dimensions
print(f"[LITHO] dims={dims.x*1000:.1f} × {dims.y*1000:.1f} × {dims.z*1000:.2f} mm")
print(f"[LITHO] verts={len(plane.data.vertices)}, polys={len(plane.data.polygons)}")
print(f"[LITHO] ready — back={BACK_THICK_MM}mm, max={MAX_THICK_MM}mm, invert={INVERT}")
```

### Ottimizzazioni e failure mode

- Mesh troppo densa (>500k poly) → Blender rallenta; abbassare `SUBDIV_RES`. 400 verts/lato = ~160k poly.
- Image con alpha → il canale alpha può confondere il displace; `img.alpha_mode='STRAIGHT'` oppure rimuovere l'alpha esternamente.
- Contrast basso → displacement piatto. Consigliare all'utente di pre-equalizzare l'istogramma (fuori Blender, o nello shader tree ma non esportabile).
- Orientamento stampa: esportare il piano sdraiato (XY), **poi** in Bambu Studio ruotare di 90° su X per stamparlo verticalmente. Non esportare già ruotato (complica validation).

---

## 2. Heightmap terrain — image → elevazione

Differenza rispetto a lithophane: non c'è retro-illuminazione, quindi non si inverte; bianco = alto, nero = basso. Il back è più spesso (serve rigidità) e non importa la trasmissione.

### Parametri tipici

| Parametro | Valore |
|---|---|
| Base thickness | 2–3 mm |
| Elevation range | 10–30 mm |
| Resolution mesh | 300–500 verts/lato |
| Smoothing | LaplacianSmooth post-apply, iter=2, lambda=0.5 |

### Codice — CALL heightmap

```python
import bpy

IMAGE_PATH = "/path/to/heightmap.png"
WIDTH_MM = 200.0
DEPTH_MM = 200.0
BASE_MM = 2.5
ELEV_MM = 20.0
RES = 400

def mm(x): return x * 0.001

img = bpy.data.images.load(IMAGE_PATH, check_existing=True)

bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0, 0, mm(BASE_MM)))
plane = bpy.context.active_object
plane.name = "Terrain"
plane.scale.x = mm(WIDTH_MM) / 2.0
plane.scale.y = mm(DEPTH_MM) / 2.0
bpy.ops.object.transform_apply(scale=True)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.subdivide(number_cuts=RES - 1)
bpy.ops.uv.smart_project()
bpy.ops.object.mode_set(mode='OBJECT')

tex = bpy.data.textures.new("TerrainTex", type='IMAGE')
tex.image = img
tex.extension = 'EXTEND'
tex.use_interpolation = True

disp = plane.modifiers.new("Displace", type='DISPLACE')
disp.texture = tex
disp.texture_coords = 'UV'
disp.direction = 'Z'
disp.mid_level = 0.0    # nero = 0 elevazione, bianco = max
disp.strength = mm(ELEV_MM)

solid = plane.modifiers.new("Solidify", type='SOLIDIFY')
solid.thickness = mm(BASE_MM)
solid.offset = -1.0

# smooth opzionale
smooth = plane.modifiers.new("Smooth", type='LAPLACIANSMOOTH')
smooth.iterations = 2
smooth.lambda_factor = 0.5
smooth.use_volume_preserve = True

# Apply
for mod_name in ["Displace", "Solidify", "Smooth"]:
    bpy.ops.object.modifier_apply(modifier=mod_name)

print(f"[TERRAIN] dims={plane.dimensions.x*1000:.1f} × {plane.dimensions.y*1000:.1f} × {plane.dimensions.z*1000:.2f} mm")
print(f"[TERRAIN] verts={len(plane.data.vertices)}, polys={len(plane.data.polygons)}")
```

---

## 3. SVG → 3D (logo, keychain, badge)

### Import SVG in Blender 5.1

Blender 5.1 espone l'operatore nativo `bpy.ops.wm.svg_import(filepath=...)` che importa l'SVG come **curve Bezier**. In versioni più vecchie (<4.5) era `bpy.ops.import_curve.svg` via addon `io_curve_svg` (che va abilitato).

Pattern sicuro che prova il nuovo operatore e fa fallback:

```python
import bpy

def import_svg(filepath):
    # Blender 5.x nativo
    if hasattr(bpy.ops.wm, "svg_import"):
        bpy.ops.wm.svg_import(filepath=filepath)
        return
    # Fallback addon
    import addon_utils
    addon_utils.enable("io_curve_svg", default_set=True, persistent=True)
    bpy.ops.import_curve.svg(filepath=filepath)
```

**Caveat scala**: SVG ha unità proprie (user units, px, mm...). Blender importa in metri (cioè 1 unità SVG = 1 BU se `scale_length=1`) oppure applica conversioni arbitrarie. **Sempre misurare dopo l'import e rescalare al target**.

### Pipeline SVG-to-3D per FDM

Passi:
1. Import SVG → collection di Curve objects
2. Join di tutte le curve (un oggetto unico)
3. Misura dimensioni attuali, rescale a target_mm (tipico: 40–80 mm larghezza per keychain)
4. Converti curve → mesh
5. Riempi i loop (fill)
6. Solidify per estrudere
7. Opzionale: aggiungi foro keyring
8. Apply, verifica manifold, export

### Codice — CALL SVG logo → keychain

```python
import bpy
import bmesh
from mathutils import Vector

SVG_PATH = "/path/to/logo.svg"
TARGET_WIDTH_MM = 50.0
EXTRUDE_MM = 3.0            # spessore keychain
ADD_KEYRING_HOLE = True
HOLE_DIAMETER_MM = 4.5      # 4.0 nominale + tolerance FDM
HOLE_MARGIN_MM = 3.0        # distanza dal bordo

def mm(x): return x * 0.001

# Remove stale objects
for obj in list(bpy.data.objects):
    if obj.name.startswith(("Logo", "Keychain")):
        bpy.data.objects.remove(obj, do_unlink=True)

# Import
if hasattr(bpy.ops.wm, "svg_import"):
    bpy.ops.wm.svg_import(filepath=SVG_PATH)
else:
    import addon_utils
    addon_utils.enable("io_curve_svg")
    bpy.ops.import_curve.svg(filepath=SVG_PATH)

# Gather imported curves
curves = [o for o in bpy.context.scene.objects if o.type == 'CURVE']
if not curves:
    raise RuntimeError("SVG import produced no curves")
print(f"[SVG] imported {len(curves)} curve(s)")

# Seleziona tutte + active
bpy.ops.object.select_all(action='DESELECT')
for c in curves:
    c.select_set(True)
bpy.context.view_layer.objects.active = curves[0]

# Join
if len(curves) > 1:
    bpy.ops.object.join()
merged = bpy.context.active_object
merged.name = "Logo_curve"

# Misura bound in BU e rescale
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
dims = merged.dimensions
print(f"[SVG] raw dims = {dims.x*1000:.2f} × {dims.y*1000:.2f} × {dims.z*1000:.2f} mm")

if dims.x <= 0:
    raise RuntimeError("Degenerate curve after import")

scale_factor = mm(TARGET_WIDTH_MM) / dims.x
merged.scale = (scale_factor, scale_factor, scale_factor)
bpy.ops.object.transform_apply(scale=True)
print(f"[SVG] rescaled ×{scale_factor:.4f} → {merged.dimensions.x*1000:.2f} × {merged.dimensions.y*1000:.2f} mm")

# Forza 2D fill
merged.data.dimensions = '2D'
merged.data.fill_mode = 'BOTH'

# Converti in mesh
bpy.ops.object.convert(target='MESH')
logo = bpy.context.active_object
logo.name = "Logo_mesh"

# Pulisci: merge doubles + triangulate
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0001)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

# Posiziona su Z=0 (il piano di fill è a Z=0 dopo l'import)
z_min = min((logo.matrix_world @ v.co).z for v in logo.data.vertices)
logo.location.z -= z_min
bpy.ops.object.transform_apply(location=True)

# Solidify per estrudere
sol = logo.modifiers.new("Solidify", type='SOLIDIFY')
sol.thickness = mm(EXTRUDE_MM)
sol.offset = 1.0     # estrusione verso +Z
sol.use_even_offset = True
sol.use_rim = True
sol.use_quality_normals = True
bpy.ops.object.modifier_apply(modifier="Solidify")

# Keyring hole opzionale
if ADD_KEYRING_HOLE:
    # Piazza foro in alto a sinistra del bounding box
    bb_min = Vector((min(v.co.x for v in logo.data.vertices),
                     min(v.co.y for v in logo.data.vertices),
                     min(v.co.z for v in logo.data.vertices)))
    bb_max = Vector((max(v.co.x for v in logo.data.vertices),
                     max(v.co.y for v in logo.data.vertices),
                     max(v.co.z for v in logo.data.vertices)))
    hole_x = bb_min.x + mm(HOLE_MARGIN_MM)
    hole_y = bb_max.y - mm(HOLE_MARGIN_MM)
    hole_z = (bb_min.z + bb_max.z) / 2.0

    bpy.ops.mesh.primitive_cylinder_add(
        radius=mm(HOLE_DIAMETER_MM / 2.0),
        depth=mm(EXTRUDE_MM * 2 + 2),   # sfonda passante con margine (regola no-coplanarità)
        location=(hole_x, hole_y, hole_z),
    )
    cutter = bpy.context.active_object
    cutter.name = "HoleCutter"

    # Boolean DIFFERENCE
    bpy.ops.object.select_all(action='DESELECT')
    logo.select_set(True)
    bpy.context.view_layer.objects.active = logo
    bool_mod = logo.modifiers.new("Hole", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.solver = 'EXACT'
    bool_mod.object = cutter
    bpy.ops.object.modifier_apply(modifier="Hole")

    bpy.data.objects.remove(cutter, do_unlink=True)
    print(f"[KEYCHAIN] hole Ø{HOLE_DIAMETER_MM}mm added")

# Report finale
d = logo.dimensions
print(f"[KEYCHAIN] final dims = {d.x*1000:.2f} × {d.y*1000:.2f} × {d.z*1000:.2f} mm")
print(f"[KEYCHAIN] verts={len(logo.data.vertices)}, polys={len(logo.data.polygons)}")
```

### Trade-off SVG → mesh

| Problema | Causa | Fix |
|---|---|---|
| Curve importate non riempite | `fill_mode='NONE'` default su Curve 3D | Forzare `dimensions='2D'` + `fill_mode='BOTH'` prima di convert |
| Mesh con buchi dopo convert | SVG con path sovrapposti o non chiusi | Aprire SVG in Inkscape → "Path > Union" + "Close path" prima di export |
| Scala importata enorme o minuscola | SVG `width` in px vs mm | Rescalare sempre a `TARGET_WIDTH_MM` post-import |
| Dettaglio perso dopo convert | Curve a bassa risoluzione | Alzare `curve.resolution_u` prima di convert (default 12, usare 24–32) |
| Non-manifold dopo Solidify | Self-intersection nelle curve | Applicare `remove_doubles` + `normals_make_consistent` prima di Solidify |

### Regole FDM specifiche per estrusioni SVG

- Spessore minimo di stroke (larghezza del tratto SVG): **0.8 mm** (2 perimetri), raccomandato **1.2 mm** (3 perimetri). Sotto gli 0.8 mm Bambu Studio/Arachne fa fatica a riempire.
- Estrusione minima (asse Z): **0.6 mm** (5 layer × 0.12 mm). Sotto lo 0.4 mm non stampa in maniera affidabile.
- Raggio arrotondamenti piccoli: se l'SVG ha curve molto strette (raggio <0.4 mm) si perdono nell'export — usare `Arachne` slicer mode.
- Testo dentro SVG: trattare come lithophane con emboss ≥0.6 mm.

---

## 4. Quick reference — input 2D

| Input | Output tipico | Pipeline | Doc di riferimento |
|---|---|---|---|
| JPG/PNG grayscale | Lithophane | Plane → subdivide → Displace(UV, invert) → Solidify back | Sezione 1 |
| PNG heightmap terrain | Topo | Plane → subdivide → Displace(UV) → Solidify base + LaplacianSmooth | Sezione 2 |
| SVG logo | Keychain/badge | svg_import → join → 2D/fill BOTH → convert mesh → Solidify + hole | Sezione 3 |
| Photo to-be-embossed | Nameplate decorato | Lithophane clamp + merge con plate Boolean UNION | Combina sezione 1 + `[workflow_patterns]` |

Integrazione con pipeline esistenti:
- Dopo l'apply modifier, passare a `[mesh_quality_assessment]` per QA standard.
- Export via `[import_export]` (STL `global_scale=1000.0, use_scene_unit=False`).
- Validazione pre-stampa via `[preprint_validation]`.
