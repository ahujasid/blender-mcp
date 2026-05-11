# Camera e Screenshot per Verifica Modelli — MCP Workflow

## Contesto e obiettivo

Durante il workflow MCP, `get_viewport_screenshot` cattura la vista corrente del viewport. Per un'ispezione sistematica del modello occorre posizionare il viewport su viste standard (Top, Front, Side, Isometrica) e fare il frame dell'oggetto prima di ogni screenshot. Questo documento documenta i pattern Python per farlo in modo automatico e ripetibile.

---

## Operatori viewport principali

### Frame selected / Frame all

```python
import bpy

# Trova area VIEW_3D
def get_view3d_area():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            space = next((s for s in area.spaces if s.type == 'VIEW_3D'), None)
            return area, region, space
    return None, None, None

area, region, space = get_view3d_area()

# Frame tutto (equivalente numpad .)
if area:
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.view3d.view_all(center=False)

# Frame solo la selezione
if area:
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.view3d.view_selected()
```

### Cambio vista (numpad views)

```python
import bpy

# Viste standard corrispondono ai numpad shortcuts
# RV3D_VIEW_FRONT = 1, BACK = 3, RIGHT = 7, TOP = 27 (numpad /)
# I valori usabili in view3d.view_axis:

STANDARD_VIEWS = {
    'TOP':    {'type': 'TOP'},
    'BOTTOM': {'type': 'BOTTOM'},
    'FRONT':  {'type': 'FRONT'},
    'BACK':   {'type': 'BACK'},
    'RIGHT':  {'type': 'RIGHT'},
    'LEFT':   {'type': 'LEFT'},
}

def set_viewport_view(view_type, area, region):
    """
    Imposta la vista del viewport a una delle viste standard.
    view_type: 'TOP', 'FRONT', 'RIGHT', 'LEFT', 'BACK', 'BOTTOM'
    """
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.view3d.view_axis(type=view_type)

# Vista isometrica: ruota manualmente il viewpoint
def set_isometric_view(area, region, space):
    """
    Imposta vista isometrica (prospettiva) con angolo standard 45/35°.
    """
    import math
    from mathutils import Quaternion, Vector
    
    r3d = space.region_3d
    # Quaternione standard isometrico (45° azimuth, 35.26° elevation)
    # Equivale a numpad 5 poi ruota — approssimazione pratica
    r3d.view_perspective = 'ORTHO'
    # Rotazione standard: guarda dall'alto-sinistra-davanti
    angle = math.radians(45)
    elev  = math.radians(35.264)  # arctan(1/sqrt(2))
    
    # Quaternione: prima ruota di elevation attorno a X, poi di azimuth attorno a Z
    q_x = Quaternion((1, 0, 0), elev)
    q_z = Quaternion((0, 0, 1), angle)
    r3d.view_rotation = q_z @ q_x
    
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.view3d.view_selected()
```

---

## Pattern 4-view screenshot sistematico

Cattura 4 screenshot standard (Top, Front, Right, Isometrico) e li salva come file PNG.

```python
import bpy
import os

def screenshot_4views(obj_name, output_dir="/tmp/blender_qa"):
    """
    Cattura Top, Front, Right, Iso screenshot dell'oggetto specificato.
    
    Args:
        obj_name: nome dell'oggetto da inquadrare
        output_dir: cartella di output per i PNG
    
    Returns:
        list[str] — percorsi dei file salvati
    """
    import math
    from mathutils import Quaternion
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Trova viewport
    area, region, space = None, None, None
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            reg = next((r for r in a.regions if r.type == 'WINDOW'), None)
            spc = next((s for s in a.spaces if s.type == 'VIEW_3D'), None)
            if reg and spc:
                area, region, space = a, reg, spc
                break
    
    if not area:
        print("ERROR: nessuna area VIEW_3D trovata")
        return []
    
    # Seleziona e attiva l'oggetto
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        print(f"ERROR: oggetto '{obj_name}' non trovato")
        return []
    
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    r3d = space.region_3d
    saved_files = []
    
    # Definisce le 4 viste
    views = [
        {
            'name': 'top',
            'setup': lambda: setattr(r3d, 'view_rotation',
                Quaternion((1, 0, 0), 0)),  # guarda dall'alto (Z+)
            'perspective': 'ORTHO',
            'axis': 'TOP',
        },
        {
            'name': 'front',
            'setup': lambda: None,
            'perspective': 'ORTHO',
            'axis': 'FRONT',
        },
        {
            'name': 'right',
            'setup': lambda: None,
            'perspective': 'ORTHO',
            'axis': 'RIGHT',
        },
        {
            'name': 'iso',
            'setup': lambda: None,
            'perspective': 'PERSP',
            'axis': None,  # isometrico: angolo custom
        },
    ]
    
    for view in views:
        # Imposta tipo prospettiva
        r3d.view_perspective = view['perspective']
        
        if view['axis']:
            with bpy.context.temp_override(area=area, region=region):
                bpy.ops.view3d.view_axis(type=view['axis'])
        else:
            # Vista isometrica manuale
            angle = math.radians(45)
            elev  = math.radians(35.264)
            q_x = Quaternion((1, 0, 0), elev)
            q_z = Quaternion((0, 0, 1), angle)
            r3d.view_rotation = q_z @ q_x
            r3d.view_perspective = 'PERSP'
        
        # Frame l'oggetto nella vista
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.view3d.view_selected()
        
        # Salva screenshot
        filepath = os.path.join(output_dir, f"{obj_name}_{view['name']}.png")
        bpy.ops.screen.screenshot(filepath=filepath)
        saved_files.append(filepath)
        print(f"Screenshot salvato: {filepath}")
    
    return saved_files

# Uso
files = screenshot_4views("MyMesh", output_dir="/tmp/qa_screenshots")
print(f"Salvati {len(files)} screenshot")
```

---

## QA visuale rapida via viewport screenshot MCP

Per il workflow MCP, `get_viewport_screenshot` è sufficiente per ispezione visiva senza salvare file. Il pattern è: posiziona viewport → screenshot → analizza → ripeti.

```python
import bpy
import math
from mathutils import Quaternion

def setup_qa_view(view_name, obj_name=None):
    """
    Configura il viewport per una vista QA specifica.
    Chiamare PRIMA di get_viewport_screenshot via MCP.
    
    view_name: 'top' | 'front' | 'right' | 'iso' | 'bottom' | 'back'
    obj_name: se specificato, fa il frame dell'oggetto; altrimenti frame all
    """
    VIEW_AXES = {
        'top':    ('ORTHO', 'TOP'),
        'bottom': ('ORTHO', 'BOTTOM'),
        'front':  ('ORTHO', 'FRONT'),
        'back':   ('ORTHO', 'BACK'),
        'right':  ('ORTHO', 'RIGHT'),
        'left':   ('ORTHO', 'LEFT'),
        'iso':    ('PERSP', None),
    }
    
    if view_name not in VIEW_AXES:
        print(f"Viste disponibili: {list(VIEW_AXES.keys())}")
        return
    
    perspective, axis = VIEW_AXES[view_name]
    
    # Trova viewport
    area = region = space = None
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            reg = next((r for r in a.regions if r.type == 'WINDOW'), None)
            spc = next((s for s in a.spaces if s.type == 'VIEW_3D'), None)
            if reg and spc:
                area, region, space = a, reg, spc
                break
    
    if not area:
        print("ERROR: nessun viewport VIEW_3D")
        return
    
    r3d = space.region_3d
    r3d.view_perspective = perspective
    
    # Seleziona oggetto target (se specificato)
    if obj_name:
        obj = bpy.data.objects.get(obj_name)
        if obj:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    
    if axis:
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.view3d.view_axis(type=axis)
    else:
        # Isometrico
        q_x = Quaternion((1, 0, 0), math.radians(35.264))
        q_z = Quaternion((0, 0, 1), math.radians(45))
        r3d.view_rotation = q_z @ q_x
    
    # Frame
    with bpy.context.temp_override(area=area, region=region):
        if obj_name and bpy.context.selected_objects:
            bpy.ops.view3d.view_selected()
        else:
            bpy.ops.view3d.view_all()
    
    print(f"Viewport configurato: {view_name} — pronto per get_viewport_screenshot")


# WORKFLOW MCP tipico:
# CALL 1: setup_qa_view('iso', 'MyMesh')
# CALL 2: get_viewport_screenshot → verifica forma generale
# CALL 3: setup_qa_view('top', 'MyMesh')
# CALL 4: get_viewport_screenshot → verifica planare top
# CALL 5: setup_qa_view('front', 'MyMesh')
# CALL 6: get_viewport_screenshot → verifica altezza e proporzioni
```

---

## Checklist QA visiva per stampa 3D

Sequenza di viste raccomandata per validare un modello prima di esportare STL:

| Passo | Vista | Cosa verificare |
|---|---|---|
| 1 | ISO | Forma generale, proporzioni, nessun artifact evidente |
| 2 | TOP | Simmetria XY, footprint, nessun elemento fuori area |
| 3 | FRONT | Altezza, overhangs evidenti, sezioni verticali |
| 4 | RIGHT | Profondità, eventuali estrusioni laterali |
| 5 | ISO + wireframe | Manifold issues, facce interne, mesh doppia |
| 6 | ISO + normals overlay | Normali flipped (facce blu = flipped) |

```python
import bpy

# Abilitare overlay wireframe per QA
def toggle_wireframe_overlay(enable=True):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.overlay.show_wireframes = enable
                    break

# Abilitare overlay normali
def show_normals_overlay(enable=True, size=0.05):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.overlay.show_vertex_normals = False
                    space.overlay.show_split_normals = False
                    space.overlay.show_face_normals = enable
                    space.overlay.normals_length = size
                    break

# Uso nel workflow QA
toggle_wireframe_overlay(True)   # poi get_viewport_screenshot
show_normals_overlay(True)       # poi get_viewport_screenshot — facce blu = flipped
toggle_wireframe_overlay(False)  # ripristina
show_normals_overlay(False)
```

---

## Nota su `bpy.ops.screen.screenshot` vs `get_viewport_screenshot`

| | `bpy.ops.screen.screenshot` | `get_viewport_screenshot` (MCP) |
|---|---|---|
| Output | File PNG su disco | Immagine direttamente nel risultato MCP |
| Uso | Salvare file, batch QA | Ispezione visiva interattiva |
| Dipendenza | `filepath` valido | Nessuna — usa viewport corrente |
| Risoluzione | Tutta la finestra Blender | Solo il viewport |

Per il workflow MCP interattivo: usare `setup_qa_view()` + `get_viewport_screenshot`.
Per report automatici multi-view: usare `screenshot_4views()` + file PNG.

---

## Screenshot Decision Matrix — quando lo screenshot vale il costo

L'MCP è cieco (vedi [mcp_blind_operating_protocol]). Lo screenshot è l'unica forma di "vista" reale ma è **costoso in token**: ogni call genera un'immagine ~50-200KB che entra nel context. Va usato strategicamente.

**Regola base**: se la domanda può essere risposta con `analyze_mesh_for_print` o `print3d_check_*` → NON serve screenshot. Lo screenshot copre solo cose che le metriche numeriche non possono catturare.

### Recipe per situazione

#### R1 — Verifica orientation pre-print (silhouette estetica)

**Quando**: hai scelto un'orientation candidate basata su `bottom_contact_area_mm2` + overhang count, ma vuoi confermare che la silhouette visibile sarà accettabile.

**Setup**:
```python
import bpy
area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
space = next(s for s in area.spaces if s.type == 'VIEW_3D')
space.shading.type = 'SOLID'
space.shading.show_cavity = True       # accentua topology
space.shading.cavity_type = 'BOTH'

with bpy.context.temp_override(area=area):
    bpy.ops.view3d.view_axis(type='FRONT')
    bpy.ops.view3d.view_orbit(angle=0.785, type='ORBITRIGHT')   # +45° azimuth
    bpy.ops.view3d.view_orbit(angle=0.615, type='ORBITUP')      # +35.264° elevation
    bpy.ops.view3d.view_selected()
# Poi chiama get_viewport_screenshot dal MCP, max_size=600
```

**Cosa cercare**: silhouette, overhangs come zone in shadow profondo, layer line direction.

#### R2 — Verifica feature preservation post-Voxel Remesh

**Quando**: Voxel Remesh con `voxel_size=0.4mm`. Metriche confermano manifold ma feature ≤1mm potrebbe essere appiattita.

**Setup**: zoom sulla feature critica.
```python
import bpy, bmesh
obj = bpy.data.objects['<name>']
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bm = bmesh.from_edit_mesh(obj.data)
# Seleziona via bbox della feature
for v in bm.verts:
    if 0.020 < v.co.x < 0.025 and 0.010 < v.co.z < 0.015:
        v.select = True
bmesh.update_edit_mesh(obj.data)

area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
with bpy.context.temp_override(area=area):
    bpy.ops.view3d.view_axis(type='FRONT')
    bpy.ops.view3d.view_selected()
bpy.ops.object.mode_set(mode='OBJECT')
# get_viewport_screenshot(max_size=1024)  ← detail fine, alta risoluzione giustificata
```

**Cosa cercare**: feature shape ancora riconoscibile, edge non eccessivamente smussato.

#### R3 — Verifica posizione foro post-Boolean DIFFERENCE

**Quando**: Boolean DIFFERENCE eseguito. Volume diminuito conferma che il cut è avvenuto, ma non sai se è nella **posizione corretta**.

**Setup**: 2 view (top + side) per triangolare.
```python
import bpy
area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')

# View 1: TOP (foro deve essere visibile da sopra)
with bpy.context.temp_override(area=area):
    bpy.ops.view3d.view_axis(type='TOP')
    bpy.ops.view3d.view_selected()
# get_viewport_screenshot(max_size=600)

# View 2: FRONT (passante deve uscire da front)
with bpy.context.temp_override(area=area):
    bpy.ops.view3d.view_axis(type='FRONT')
    bpy.ops.view3d.view_selected()
# get_viewport_screenshot(max_size=600)
```

**Cosa cercare**: posizione foro corretta da entrambe le proiezioni.

#### R4 — Debug normali residue post-recalc

**Quando**: `normals_make_consistent(inside=False)` chiamato ma `inverted_face_pct > 5`. Probabilmente `disconnected_shells > 1` e recalc opera solo sulla shell connessa.

**Setup**: Face Orientation overlay (rosso = flipped).
```python
import bpy
area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
space = next(s for s in area.spaces if s.type == 'VIEW_3D')
space.overlay.show_face_orientation = True

with bpy.context.temp_override(area=area):
    bpy.ops.view3d.view_axis(type='FRONT')
    bpy.ops.view3d.view_orbit(angle=0.785, type='ORBITRIGHT')
    bpy.ops.view3d.view_orbit(angle=0.615, type='ORBITUP')
    bpy.ops.view3d.view_selected()
# get_viewport_screenshot(max_size=800)

# Disabilita dopo
space.overlay.show_face_orientation = False
```

**Cosa cercare**: zone rosse residue (= shells disgiunte con normale opposta). Decidi: split, ri-import, o re-meshing.

#### R5 — Pre-export visual sanity (gate finale)

**Quando**: tutti i check numerici passati, prima di `export_stl`. Singolo iso-screenshot per "ho davvero costruito quello che pensavo?".

**Setup**:
```python
import bpy
area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
space = next(s for s in area.spaces if s.type == 'VIEW_3D')
space.shading.type = 'SOLID'
space.shading.color_type = 'OBJECT'   # diversifica object multipli
space.overlay.show_face_orientation = False
space.overlay.show_wireframes = False

with bpy.context.temp_override(area=area):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.view3d.view_axis(type='FRONT')
    bpy.ops.view3d.view_orbit(angle=0.785, type='ORBITRIGHT')
    bpy.ops.view3d.view_orbit(angle=0.615, type='ORBITUP')
    bpy.ops.view3d.view_all()
# get_viewport_screenshot(max_size=800)
```

**Cosa cercare**: matches user expectation. Non ci dovrebbero essere sorprese — è check di sanità, non scoperta.

#### R6 — Pre/post sculpt comparison

**Quando**: l'utente farà Sculpt manuale (Inflate per chiudere buco, Smooth, ecc.). Sculpt non scriptabile, ma puoi confermare delta visivo.

**Setup** (prima e dopo, identica view):
```python
import bpy
area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
with bpy.context.temp_override(area=area):
    bpy.ops.view3d.view_axis(type='FRONT')
    bpy.ops.view3d.view_orbit(angle=0.785, type='ORBITRIGHT')
    bpy.ops.view3d.view_orbit(angle=0.615, type='ORBITUP')
    bpy.ops.view3d.view_selected()
# get_viewport_screenshot(max_size=600)  ← PRIMA
# ... sculpt session manuale dell'utente ...
# get_viewport_screenshot(max_size=600)  ← DOPO (stessa view)
```

**Cosa cercare**: cambiamento avvenuto nella zona target, no distorsione fuori, silhouette globale preservata.

#### R7 — Diagnose sliver concentration post-decimate

**Quando**: post-decimate aggressivo, R013 ha matchato (`aspect_ratio_p95 > 10`). Vuoi vedere visivamente dove si concentrano gli sliver.

**Setup**: wireframe overlay completo.
```python
import bpy
area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
space = next(s for s in area.spaces if s.type == 'VIEW_3D')
space.overlay.show_wireframes = True
space.overlay.wireframe_threshold = 1.0   # mostra TUTTI gli edge

with bpy.context.temp_override(area=area):
    bpy.ops.view3d.view_axis(type='FRONT')
    bpy.ops.view3d.view_orbit(angle=0.785, type='ORBITRIGHT')
    bpy.ops.view3d.view_selected()
# get_viewport_screenshot(max_size=1024)  ← detail fine, alta risoluzione

space.overlay.show_wireframes = False
```

**Cosa cercare**: zone con triangoli ad ago concentrati = sliver. Tipicamente vicino a feature curve dove decimate ha collapsato troppo.

### Costi screenshot — table di reference

| max_size | File size tipico | Cost | Use case |
|---|---|---|---|
| 400 | ~30 KB | basso | Quick sanity, thumbnail |
| 600 | ~80 KB | medio-basso | Default per QA recipes (R1, R3, R5, R6) |
| 800 | ~120 KB | medio | R4 (debug overlays) |
| 1024 | ~200 KB | alto | R2, R7 (detail inspection feature critica / sliver) |
| 1600+ | ~500 KB+ | molto alto | Quasi mai necessario |

**Default per la maggior parte dei casi**: `max_size=600`.

### Anti-patterns

❌ **Screenshot dopo OGNI playbook step**. Le metriche di `verification.expect` sono il check primario. Screenshot solo se la metrica non basta.

❌ **Screenshot per contare cose**. Per "quanti object nella scena" usa `len(bpy.context.scene.objects)`. Per "quanti buchi nel modello" usa `boundary_loops`.

❌ **Screenshot senza setup**. Senza camera positioning, l'immagine è quello che il viewport mostrava prima — spesso view casuale. Sempre `view_selected` + axis preset prima.

❌ **Screenshot a `max_size=1600` di default**. Cost alto per zero beneficio.

❌ **Screenshot per validare numeri**. "Ha funzionato il Boolean?" → confronta `signed_volume_mm3 / volume_mm3` pre/post, NON screenshot.

❌ **Multipli screenshot consecutivi senza setup diverso**. Stessa view = stesso info, costa il doppio in token.

## Cross-reference

- [mcp_blind_operating_protocol] — perché lo screenshot è il "Senso 3" e quando giustifica il costo
- [orientation_strategy] — decisione orientation con metriche, screenshot solo per silhouette finale
- [blender_3d_print_toolbox] — `print3d_check_overhang` per drill-down su overhang (alternativa a screenshot)
- [analyze_to_action] — routing decisions vanno su metriche, mai su screenshot
