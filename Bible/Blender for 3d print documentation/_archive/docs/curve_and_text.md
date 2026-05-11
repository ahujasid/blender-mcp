# Curve Objects e Text Geometry — Blender Python

## Contesto

Le **Curve** in Blender coprono tutto quello che non è mesh poligonale: profili 2D, tubi, cavi, cornici, e testo 3D. Per la stampa FDM sono utili per: pipe/tubo parametrico, logo/testo in rilievo, border/frame arrotondati, e forme con spessore controllato via profilo.

Il workflow standard per la stampa è: crea Curve → configura → **converti a mesh** (necessario per export STL).

---

## bpy.types.Curve — fondamentali

```python
import bpy

# Creare una curva via bpy.data
curve_data = bpy.data.curves.new(name="MyCurve", type='CURVE')
curve_data.dimensions = '3D'  # '2D' per curve piane, '3D' per path nello spazio

# Creare l'oggetto e collegarlo alla scena
obj = bpy.data.objects.new("CurveObject", curve_data)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
```

### Tipi di curva (`type`)

| Valore | Descrizione | Uso tipico |
|---|---|---|
| `'CURVE'` | Bezier o NURBS — forma libera | Path, profili, pipe |
| `'SURFACE'` | Superficie NURBS | Raramente usato per stampa |
| `'FONT'` | Testo 3D | Loghi, etichette incise |

---

## Splines — Bezier

```python
import bpy

curve_data = bpy.data.curves.new("BezierCurve", type='CURVE')
curve_data.dimensions = '3D'

# Aggiunge una spline Bezier
spline = curve_data.splines.new(type='BEZIER')
# Di default ha 1 punto; ridimensiona per aggiungerne altri
spline.bezier_points.add(3)  # aggiunge 3 punti → totale 4

# Configura ogni punto: co = posizione, handle_left/right = tangenti
pts = spline.bezier_points
pts[0].co = (0, 0, 0)
pts[0].handle_left  = (-0.5, 0, 0)
pts[0].handle_right = (0.5, 0, 0)

pts[1].co = (2, 1, 0)
pts[1].handle_left  = (1.5, 1, 0)
pts[1].handle_right = (2.5, 1, 0)

pts[2].co = (4, 0, 0)
pts[2].handle_right = (4.5, 0, 0)
pts[2].handle_left  = (3.5, 0, 0)

pts[3].co = (6, 1, 0)
pts[3].handle_left  = (5.5, 1, 0)
pts[3].handle_right = (6.5, 1, 0)

# Chiudi la spline (loop)
spline.use_cyclic_u = True

# Tipi di handle per punto
# 'FREE' = libero, 'ALIGNED' = allineato, 'VECTOR' = vettore (spigolo vivo), 'AUTO' = auto-smooth
for pt in pts:
    pt.handle_left_type  = 'AUTO'
    pt.handle_right_type = 'AUTO'
```

## Splines — POLY (segmenti retti)

Per forme con soli spigoli vivi (più semplice del Bezier):

```python
import bpy

curve_data = bpy.data.curves.new("PolyCurve", type='CURVE')
curve_data.dimensions = '3D'

spline = curve_data.splines.new(type='POLY')
spline.points.add(3)  # aggiunge 3 → totale 4 (il primo già c'è)

# POLY usa .points (non .bezier_points); ogni punto ha .co come Vector4 (x,y,z,w)
coords = [(0,0,0), (2,0,0), (2,2,0), (0,2,0)]
for i, (x,y,z) in enumerate(coords):
    spline.points[i].co = (x, y, z, 1.0)  # w=1 sempre

spline.use_cyclic_u = True  # chiudi il loop (rettangolo)
```

---

## Bevel — dare spessore alla curva

`bevel_depth` e `bevel_resolution` controllano il profilo circolare attorno alla curva. Ottimo per tubi e cavi.

```python
import bpy

curve_data = bpy.data.curves.new("Tube", type='CURVE')
curve_data.dimensions = '3D'

# Aggiunge path semplice (NURBS)
spline = curve_data.splines.new(type='NURBS')
spline.points.add(3)
spline.points[0].co = (0, 0, 0, 1)
spline.points[1].co = (0, 0, 20, 1)   # 20mm su Z (con scale=0.001 → 20 BU)
spline.points[2].co = (10, 0, 20, 1)
spline.points[3].co = (10, 0, 0, 1)
spline.use_endpoint_u = True

# === BEVEL — crea il tubo ===
curve_data.bevel_depth = 0.003       # raggio in BU → 3mm (con scale_length=0.001)
curve_data.bevel_resolution = 8      # segmenti per il cerchio (4=quadrato, 8=ottogono, 16=liscio)
curve_data.use_fill_caps = True      # chiudi le estremità del tubo

obj = bpy.data.objects.new("TubeObj", curve_data)
bpy.context.collection.objects.link(obj)

# Per FDM: bevel_depth minimo 0.4mm = 0.0004 BU (1 parete nozzle 0.4)
# Pratico: ≥ 0.8mm = 0.0008 BU (2 pareti)
```

### Bevel con profilo custom

Invece di un cerchio, usa una curva 2D come profilo (es. profilo a T, profilo rettangolare):

```python
import bpy

# Crea il profilo 2D (rettangolo 4×2mm)
profile_data = bpy.data.curves.new("Profile", type='CURVE')
profile_data.dimensions = '2D'
sp = profile_data.splines.new(type='POLY')
sp.points.add(3)
profile_pts = [(0.002, 0.001, 0), (−0.002, 0.001, 0), (−0.002, −0.001, 0), (0.002, −0.001, 0)]
for i, (x,y,z) in enumerate(profile_pts):
    sp.points[i].co = (x, y, z, 1)
sp.use_cyclic_u = True

profile_obj = bpy.data.objects.new("ProfileObj", profile_data)
bpy.context.collection.objects.link(profile_obj)

# Assegna il profilo alla curva principale
main_curve = bpy.data.curves["Tube"]
main_curve.bevel_mode = 'OBJECT'
main_curve.bevel_object = profile_obj
```

---

## Extrude — curve 2D estruse su Z

Per profili 2D con spessore uniforme (es. lettere, loghi):

```python
import bpy

curve_data = bpy.data.curves.new("Extruded2D", type='CURVE')
curve_data.dimensions = '2D'

# Forma 2D (es. rettangolo)
spline = curve_data.splines.new(type='POLY')
spline.points.add(3)
for i, (x, y) in enumerate([(0,0), (0.05,0), (0.05,0.05), (0,0.05)]):
    spline.points[i].co = (x, y, 0, 1)
spline.use_cyclic_u = True

# Estrudi su Z
curve_data.extrude = 0.003       # 3mm in BU → profondità estrusione
curve_data.offset = 0.0          # offset del profilo (positivo = allarga)
curve_data.fill_mode = 'BOTH'    # 'FRONT' | 'BACK' | 'BOTH' | 'NONE'

obj = bpy.data.objects.new("ExtrudedShape", curve_data)
bpy.context.collection.objects.link(obj)
```

---

## Text Geometry (bpy.types.TextCurve)

### Creare testo 3D da script

```python
import bpy

# Crea text curve
text_data = bpy.data.curves.new(name="MyText", type='FONT')
text_data.body = "Hello"            # il testo

# Font: usa il built-in di default
# Per font custom: text_data.font = bpy.data.fonts.load("/path/to/font.ttf")

# Dimensioni del testo
text_data.size = 0.006              # altezza carattere in BU → 6mm (scala 0.001)
text_data.space_character = 1.0    # spaziatura tra caratteri (1.0 = normale)
text_data.space_word = 1.0         # spaziatura tra parole
text_data.space_line = 1.0         # spaziatura tra righe

# Estrusione (profondità Z) — per emboss su superficie
text_data.extrude = 0.0004         # 0.4mm = 1 layer height (minimo funzionale FDM)
# Raccomandato per FDM: 0.6–1.2mm (0.0006–0.0012 BU)

# Offset laterale (ingrandisce/rimpicciolisce il contorno del testo)
text_data.offset = 0.0001          # piccolo offset positivo compensa die swell FDM

# Allineamento
text_data.align_x = 'CENTER'       # 'LEFT' | 'CENTER' | 'RIGHT' | 'JUSTIFY' | 'FLUSH'
text_data.align_y = 'CENTER'       # 'TOP' | 'TOP_BASELINE' | 'CENTER' | 'BOTTOM_BASELINE' | 'BOTTOM'

# Oggetto
obj = bpy.data.objects.new("TextObject", text_data)
bpy.context.collection.objects.link(obj)
obj.location = (0, 0, 0)

print(f"Testo creato: '{text_data.body}', size={text_data.size*1000:.1f}mm, extrude={text_data.extrude*1000:.2f}mm")
```

### Caricare font custom

```python
import bpy
import os

def load_font(font_path):
    """Carica un font .ttf o .otf se non già caricato."""
    # Controlla se già caricato
    font_name = os.path.basename(font_path)
    existing = bpy.data.fonts.get(font_name)
    if existing:
        return existing
    
    if not os.path.exists(font_path):
        print(f"Font non trovato: {font_path}")
        return None
    
    font = bpy.data.fonts.load(font_path)
    print(f"Font caricato: {font.name}")
    return font

# Assegna font al testo
font = load_font("/path/to/ArialBlack.ttf")
if font:
    text_data = bpy.data.curves.get("MyText")
    if text_data:
        text_data.font = font
```

### Conversione Curve/Text → Mesh (obbligatoria per STL)

Le curve e il testo devono essere convertiti in mesh prima dell'export.

```python
import bpy

def convert_curve_to_mesh(obj):
    """
    Converte un oggetto Curve o Font in Mesh.
    Dopo la conversione il tipo è 'MESH' e può essere esportato STL.
    """
    if obj.type not in ('CURVE', 'FONT'):
        print(f"'{obj.name}' non è una curva/testo ({obj.type})")
        return obj
    
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    
    # Conversione
    bpy.ops.object.convert(target='MESH')
    
    # Dopo conversione: applica scala
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    print(f"'{obj.name}' convertito → MESH: {len(obj.data.vertices)} verts, {len(obj.data.polygons)} polys")
    return obj

# Uso
text_obj = bpy.data.objects["TextObject"]
convert_curve_to_mesh(text_obj)
```

---

## Pattern FDM completi

### Pattern 1: testo emboss su superficie piana

```python
import bpy

# Parametri (in mm, poi convertiti in BU con *0.001)
TEXT_STRING   = "SAMPLE"
TEXT_SIZE_MM  = 8.0      # altezza carattere — minimo 4mm per leggibilità
EXTRUDE_MM    = 0.6      # profondità emboss — minimo 0.4mm (1 layer)
BASE_WIDTH_MM = 50.0
BASE_DEPTH_MM = 15.0
BASE_THICK_MM = 3.0

# 1. Base piatta
bpy.ops.mesh.primitive_cube_add(size=1)
base = bpy.context.active_object
base.name = "Base"
base.scale = (BASE_WIDTH_MM*0.001/2, BASE_DEPTH_MM*0.001/2, BASE_THICK_MM*0.001/2)
bpy.ops.object.transform_apply(scale=True)

# 2. Testo
text_data = bpy.data.curves.new("EmbossText", type='FONT')
text_data.body    = TEXT_STRING
text_data.size    = TEXT_SIZE_MM * 0.001
text_data.extrude = EXTRUDE_MM * 0.001
text_data.align_x = 'CENTER'
text_data.align_y = 'CENTER'

text_obj = bpy.data.objects.new("EmbossTextObj", text_data)
bpy.context.collection.objects.link(text_obj)
# Posiziona sopra la base
text_obj.location.z = BASE_THICK_MM * 0.001 / 2

# 3. Converti a mesh
bpy.context.view_layer.objects.active = text_obj
text_obj.select_set(True)
bpy.ops.object.convert(target='MESH')
bpy.ops.object.transform_apply(scale=True)

# 4. Unisci base e testo
bpy.ops.object.select_all(action='DESELECT')
base.select_set(True)
text_obj.select_set(True)
bpy.context.view_layer.objects.active = base
bpy.ops.object.join()

print("Testo emboss pronto per export STL")
```

### Pattern 2: tubo parametrico

```python
import bpy

def create_tube(
    path_points,      # lista di tuple (x,y,z) in mm
    outer_radius_mm=5.0,
    wall_thickness_mm=1.2,  # ≥ 3 pareti × 0.4mm nozzle
    bevel_resolution=12,
    close_path=False,
    name="Tube"
):
    """
    Crea un tubo (pipe) lungo un path di punti in mm.
    Usa bevel_depth per il raggio esterno; wall thickness gestita dallo slicer.
    
    Regola FDM wall_thickness: ≥ 3 × 0.4mm = 1.2mm minimo robusto
    """
    # Converti in BU
    pts_bu = [(x*0.001, y*0.001, z*0.001) for x,y,z in path_points]
    radius_bu = outer_radius_mm * 0.001
    
    curve_data = bpy.data.curves.new(name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = radius_bu
    curve_data.bevel_resolution = bevel_resolution
    curve_data.use_fill_caps = True
    
    spline = curve_data.splines.new(type='POLY')
    spline.points.add(len(pts_bu) - 1)
    for i, (x,y,z) in enumerate(pts_bu):
        spline.points[i].co = (x, y, z, 1.0)
    spline.use_cyclic_u = close_path
    
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    
    print(f"Tubo '{name}': r={outer_radius_mm}mm, {len(pts_bu)} punti")
    return obj

# Esempio: tubo a L di 30×30mm
tube = create_tube(
    path_points=[(0,0,0), (0,0,30), (30,0,30)],
    outer_radius_mm=4.0,
    wall_thickness_mm=1.2,
    name="LShapeTube"
)

# Converti a mesh prima dell'export
bpy.context.view_layer.objects.active = tube
bpy.ops.object.convert(target='MESH')
bpy.ops.object.transform_apply(scale=True)
```

---

## Limitazioni FDM per curve e testo

| Parametro | Minimo funzionale | Raccomandato | Note |
|---|---|---|---|
| Altezza testo | 4mm | 6–8mm | Sotto 4mm illeggibile con nozzle 0.4mm |
| Profondità emboss | 0.4mm (1 layer) | 0.6–1.2mm | Sotto 0.4mm slicer ignora |
| Profondità deboss | 0.4mm | 0.6–0.8mm | ≤ 0.3mm: rischio isola mesh |
| Raggio tubo (bevel) | 0.4mm | ≥ 1.2mm | Sotto 0.4mm non stampabile |
| Risoluzione bevel | 4 (ottogono) | 8–12 | 4=quadrato visibile, 12=liscio |
| Font consigliati | — | Arial Black, Liberation Sans Bold | No serif/script sotto 8mm |

**Nota die swell:** il nozzle espande di ~0.1–0.2mm per lato. Per testo ≤ 6mm: usare `text_data.offset = -0.0001` (−0.1mm) per compensare il gonfiamento laterale.
