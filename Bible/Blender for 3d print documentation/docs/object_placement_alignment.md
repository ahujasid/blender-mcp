# Object Placement & Alignment — Posizionamento e allineamento per FDM

## Contesto

Richieste tipiche dell'utente: "centra questo sul letto", "metti la base a Z=0", "allinea questi due pezzi", "posiziona il manico sul bicchiere", "stacca queste parti di 2 mm". Operazioni elementari ma che coinvolgono `matrix_world`, `bound_box`, `cursor.location`, `origin_set` — sparse in varie parti della KB.

Questo documento è la **fonte unica** per:
1. Sistema di coordinate Blender ↔ Bambu Studio bed
2. Origin set: 4 modalità e quando usarle
3. Snap to bed (Z=0 bottom)
4. Centering su bed, recentering
5. Allineamento tra oggetti (edge-to-edge, center, top/bottom)
6. Stacking (pila verticale) e spacing
7. 3D cursor come punto di riferimento
8. Packing automatico di N oggetti sul build plate

Prerequisito: `scale_length=0.001` (1 BU = 1 mm). Bambu A1 bed 256×256 mm.

---

## 1. Sistema di coordinate Blender vs Bambu Studio

**Blender scena**: l'origine del mondo (0,0,0) è un punto qualsiasi nello spazio. Non c'è un "bed" intrinseco.

**Bambu Studio bed**: Bambu Studio interpreta l'STL come se fosse il **centro del bed** a (0,0,0), oppure **angolo front-left**, dipende dall'impostazione "Build Plate Origin". Il default Bambu Studio per A1 è **centro del bed a (128, 128, 0)** nel sistema Bambu, oppure **origine STL = angolo** (confermare in setting BS).

**Regola operativa** per questa KB: esportare l'STL con la geometria:
- `Z_min = 0` (sta appoggiata al letto)
- `X, Y` centrati sull'origine (0,0) OPPURE sull'angolo (0,0). 

Decisione: la pipeline di default di questa KB esporta **centrato in XY a (0,0) e Z_min=0**. In Bambu Studio se il bed è settato con origin al centro, la geometria arriva già centrata. Se l'origin è all'angolo, BS fa lo shift automatico al primo open.

Questa è la **convenzione standard** e va rispettata sempre prima di export:
```
(bbox_center_x, bbox_center_y) = (0, 0)
bbox_min_z = 0
```

---

## 2. Origin set — 4 modalità

`bpy.ops.object.origin_set(type=...)` cambia l'origine dell'oggetto (il punto `obj.location`) senza muovere la geometria visibile. Le opzioni:

| Type | Effetto | Quando usarlo |
|---|---|---|
| `'ORIGIN_GEOMETRY'` | Origine al centro mediano della geometria | Default; operazioni successive centrate sul mesh |
| `'ORIGIN_CENTER_OF_MASS'` | Centro di massa pesato sui vertici | Calcoli statici, bilanciamento stampa |
| `'ORIGIN_CENTER_OF_VOLUME'` | Centro di volume (mesh chiusa) | Stabilità FDM, orientamento |
| `'ORIGIN_CURSOR'` | Origine = posizione del 3D cursor | Pivot custom per allineamento |

```python
def set_origin(obj, mode='ORIGIN_GEOMETRY'):
    assert mode in ('ORIGIN_GEOMETRY', 'ORIGIN_CENTER_OF_MASS',
                     'ORIGIN_CENTER_OF_VOLUME', 'ORIGIN_CURSOR')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type=mode)
    print(f"[ORIGIN] {obj.name} → {mode}; location={tuple(round(v*1000,3) for v in obj.location)} mm")
```

**Attenzione: `ORIGIN_GEOMETRY` con `center='BOUNDS'`**: usa il centro del bbox invece del centroid mediano (che usa `center='MEDIAN'` default).

```python
# Centro bbox
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
```

---

## 3. Snap to bed — Z_min = 0

Operazione: trasla l'oggetto in Z in modo che il vertice più basso sia a Z=0.

```python
from mathutils import Vector

def snap_to_bed(obj):
    """
    Trasla obj in -Z in modo che il bbox minimo Z coincida con 0.
    Richiede transform_apply già fatto se la scale è ≠ 1.
    """
    mw = obj.matrix_world
    verts_world = [mw @ v.co for v in obj.data.vertices]
    z_min = min(v.z for v in verts_world)
    obj.location.z -= z_min
    bpy.context.view_layer.update()
    print(f"[SNAP-BED] {obj.name} Δz={-z_min*1000:.3f} mm → z_min=0")
```

**Variante senza transform_apply** (usa bound_box):
```python
def snap_to_bed_fast(obj):
    mw = obj.matrix_world
    z_min = min((mw @ Vector(c)).z for c in obj.bound_box)
    obj.location.z -= z_min
```

Il primo è più preciso (usa vertici reali), il secondo è più veloce (8 corner del bbox). Per operazioni critiche pre-export usare il primo.

---

## 4. Center su bed

```python
def center_on_bed(obj, bed_center=(0.0, 0.0)):
    """
    Centra il bbox XY dell'oggetto su (bed_center_x, bed_center_y).
    Non modifica Z.
    """
    mw = obj.matrix_world
    verts_world = [mw @ v.co for v in obj.data.vertices]
    x_min = min(v.x for v in verts_world)
    x_max = max(v.x for v in verts_world)
    y_min = min(v.y for v in verts_world)
    y_max = max(v.y for v in verts_world)
    cx = (x_min + x_max) / 2
    cy = (y_min + y_max) / 2
    obj.location.x += bed_center[0] - cx
    obj.location.y += bed_center[1] - cy
    bpy.context.view_layer.update()
    print(f"[CENTER-BED] {obj.name} → XY=({bed_center[0]*1000:.2f},{bed_center[1]*1000:.2f}) mm")


def center_xy_and_snap_bed(obj, bed_center_mm=(0.0, 0.0)):
    """Convenience: centro XY + Z_min=0 — convenzione export standard."""
    bed_bu = (bed_center_mm[0] * 0.001, bed_center_mm[1] * 0.001)
    center_on_bed(obj, bed_center=bed_bu)
    snap_to_bed(obj)
```

---

## 5. Alignment tra oggetti

Allineare due oggetti lungo un asse con una specifica regola ("allinea i fondi", "centra", "edge-to-edge").

```python
from enum import Enum

class AlignMode(str, Enum):
    MIN = 'MIN'         # allinea i punti minimi (es. "fondi sullo stesso piano")
    MAX = 'MAX'         # allinea i punti massimi
    CENTER = 'CENTER'   # allinea i centri

def align_object_to(obj_moving, obj_ref, axis='Z', mode=AlignMode.MIN):
    """
    Trasla obj_moving lungo axis in modo che il suo bbox allinei a obj_ref con la regola mode.
    axis: 'X'|'Y'|'Z'.
    """
    axis_idx = {'X': 0, 'Y': 1, 'Z': 2}[axis.upper()]
    
    def world_minmax(obj, idx):
        mw = obj.matrix_world
        vals = [(mw @ v.co)[idx] for v in obj.data.vertices]
        return min(vals), max(vals)
    
    mv_min, mv_max = world_minmax(obj_moving, axis_idx)
    rf_min, rf_max = world_minmax(obj_ref, axis_idx)
    
    if mode == AlignMode.MIN:
        delta = rf_min - mv_min
    elif mode == AlignMode.MAX:
        delta = rf_max - mv_max
    elif mode == AlignMode.CENTER:
        mv_c = (mv_min + mv_max) / 2
        rf_c = (rf_min + rf_max) / 2
        delta = rf_c - mv_c
    
    loc = list(obj_moving.location)
    loc[axis_idx] += delta
    obj_moving.location = tuple(loc)
    bpy.context.view_layer.update()
    print(f"[ALIGN] {obj_moving.name} {axis}-{mode} → Δ={delta*1000:.3f} mm (ref={obj_ref.name})")
```

### Edge-to-edge (stacking laterale)

Mette obj_moving **adiacente** a obj_ref con gap opzionale.

```python
def place_adjacent(obj_moving, obj_ref, axis='X', side='POS', gap_mm=0.5):
    """
    Mette obj_moving adiacente a obj_ref su lato +X o -X (o Y/Z), con gap in mm.
    side: 'POS' (aggiunto verso il lato positivo di obj_ref) o 'NEG'.
    """
    axis_idx = {'X': 0, 'Y': 1, 'Z': 2}[axis.upper()]
    mw_r = obj_ref.matrix_world
    mw_m = obj_moving.matrix_world
    
    r_vals = [(mw_r @ v.co)[axis_idx] for v in obj_ref.data.vertices]
    m_vals = [(mw_m @ v.co)[axis_idx] for v in obj_moving.data.vertices]
    
    if side == 'POS':
        target_edge = max(r_vals) + gap_mm * 0.001
        delta = target_edge - min(m_vals)
    else:
        target_edge = min(r_vals) - gap_mm * 0.001
        delta = target_edge - max(m_vals)
    
    loc = list(obj_moving.location)
    loc[axis_idx] += delta
    obj_moving.location = tuple(loc)
    bpy.context.view_layer.update()
    print(f"[ADJ] {obj_moving.name} {side}{axis} of {obj_ref.name}, gap={gap_mm}mm")
```

---

## 6. Stacking verticale

```python
def stack_vertically(objects, gap_mm=0.0, base_z_mm=0.0):
    """
    Pila gli oggetti lungo Z in ordine, con gap tra ciascuno.
    Mette il primo oggetto con z_min = base_z_mm.
    """
    z_cursor = base_z_mm * 0.001   # BU
    for i, obj in enumerate(objects):
        mw = obj.matrix_world
        verts_world = [mw @ v.co for v in obj.data.vertices]
        z_min = min(v.z for v in verts_world)
        z_max = max(v.z for v in verts_world)
        height = z_max - z_min
        # Trasla in modo che z_min = z_cursor
        obj.location.z += z_cursor - z_min
        bpy.context.view_layer.update()
        print(f"[STACK] {obj.name}: z=[{z_cursor*1000:.2f}, {(z_cursor+height)*1000:.2f}] mm")
        z_cursor += height + gap_mm * 0.001
```

---

## 7. 3D cursor

Il 3D cursor è un punto globale nella scena usato come pivot da vari operatori (snap, origin_set con ORIGIN_CURSOR, primitive_*_add con location=cursor).

```python
def cursor_to(x_mm, y_mm, z_mm):
    bpy.context.scene.cursor.location = (x_mm * 0.001, y_mm * 0.001, z_mm * 0.001)
    print(f"[CURSOR] → ({x_mm},{y_mm},{z_mm}) mm")

def cursor_to_object(obj):
    bpy.context.scene.cursor.location = obj.location.copy()

def cursor_to_world_origin():
    bpy.context.scene.cursor.location = (0, 0, 0)

def cursor_to_selected_avg():
    bpy.ops.view3d.snap_cursor_to_selected()
```

**Use case tipico** — piazzare un cilindro cutter per foro in una posizione precisa:
```python
cursor_to(x_mm=20.0, y_mm=15.0, z_mm=10.0)
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.002,
    depth=0.030,
    location=bpy.context.scene.cursor.location,
)
```

---

## 8. Packing automatico di N oggetti sul build plate

Algoritmo shelf-packing 2D semplice (First Fit Decreasing Height). Non ottimale ma sufficiente per layout funzionale.

```python
def pack_on_bed(objects, bed_size_mm=(256.0, 256.0), margin_mm=3.0, gap_mm=3.0):
    """
    Piazza N oggetti sul bed usando shelf packing per altezza (Y) decrescente.
    Ordina per area decrescente, crea righe.
    Ritorna True se tutti stanno; False se overflow (e stampa quali).
    """
    # Misura bbox XY in mm per ogni oggetto, in coord locali (assume transform applied)
    sizes = []
    for obj in objects:
        dims = obj.dimensions   # BU
        sizes.append({
            "obj": obj,
            "w_mm": dims.x * 1000,
            "h_mm": dims.y * 1000,
            "z_min_bu": min((obj.matrix_world @ v.co).z for v in obj.data.vertices),
        })
    
    # Ordina per altezza Y decrescente
    sizes.sort(key=lambda s: -s["h_mm"])
    
    bed_w, bed_h = bed_size_mm
    usable_w = bed_w - 2 * margin_mm
    usable_h = bed_h - 2 * margin_mm
    
    # Shelf packing
    shelves = []    # lista di (y_start, shelf_height, items_in_shelf)
    cur_shelf_y = margin_mm
    cur_shelf_h = 0
    cur_shelf_x = margin_mm
    placed = []
    overflow = []
    
    for s in sizes:
        w, h = s["w_mm"], s["h_mm"]
        if w > usable_w or h > usable_h:
            overflow.append(s["obj"].name)
            continue
        
        # Stesso shelf se ci sta
        if cur_shelf_x + w <= margin_mm + usable_w:
            if h > cur_shelf_h:
                cur_shelf_h = h
            s["x_mm"] = cur_shelf_x + w / 2   # centro bbox X
            s["y_mm"] = cur_shelf_y + h / 2
            cur_shelf_x += w + gap_mm
            placed.append(s)
        else:
            # Nuovo shelf
            cur_shelf_y += cur_shelf_h + gap_mm
            cur_shelf_h = h
            cur_shelf_x = margin_mm
            if cur_shelf_y + h > margin_mm + usable_h:
                overflow.append(s["obj"].name)
                continue
            s["x_mm"] = cur_shelf_x + w / 2
            s["y_mm"] = cur_shelf_y + h / 2
            cur_shelf_x += w + gap_mm
            placed.append(s)
    
    # Converti in coord bed_centered (se bed_center = (0,0))
    # Qui assumiamo il bed sta in [margin, bed_size - margin] partendo da un angolo
    # Ma vogliamo centrare su (0,0): shift di (-bed_w/2, -bed_h/2)
    for s in placed:
        obj = s["obj"]
        # Trasla XY in modo che il CENTRO del bbox coincida con (s["x_mm"] - bed_w/2, s["y_mm"] - bed_h/2)
        target_x_mm = s["x_mm"] - bed_w / 2
        target_y_mm = s["y_mm"] - bed_h / 2
        
        mw = obj.matrix_world
        verts_world = [mw @ v.co for v in obj.data.vertices]
        cur_cx = (min(v.x for v in verts_world) + max(v.x for v in verts_world)) / 2
        cur_cy = (min(v.y for v in verts_world) + max(v.y for v in verts_world)) / 2
        
        obj.location.x += (target_x_mm * 0.001) - cur_cx
        obj.location.y += (target_y_mm * 0.001) - cur_cy
        
        # Snap bed
        mw = obj.matrix_world
        z_min_bu = min((mw @ v.co).z for v in obj.data.vertices)
        obj.location.z -= z_min_bu
        
        bpy.context.view_layer.update()
        print(f"[PACK] {obj.name} → ({target_x_mm:.1f}, {target_y_mm:.1f}), bbox {s['w_mm']:.1f}×{s['h_mm']:.1f} mm")
    
    if overflow:
        print(f"[PACK] OVERFLOW: {overflow}")
        return False
    print(f"[PACK] placed {len(placed)}/{len(objects)} items OK")
    return True
```

**Caveat**: questo packing è 2D (solo pianta X×Y). Non considera altezza. Per multi-layer o packing ottimo serve un algoritmo più complesso (bin packing 3D — fuori scope). Bambu Studio ha il suo auto-arrange più sofisticato.

---

## 9. Pattern MCP tipico — da input "centra sul letto"

Input utente: "prendi il modello e centralo sul letto della A1, con base sul piano."

```python
import bpy
from mathutils import Vector

obj_name = "Model"   # da CALL precedente
obj = bpy.data.objects.get(obj_name)
if obj is None:
    raise RuntimeError(f"Object {obj_name} not found")

# 1. Applica trasformazioni pendenti
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# 2. Center + snap bed
def _centered_snap(obj):
    mw = obj.matrix_world
    verts = [mw @ v.co for v in obj.data.vertices]
    x_min = min(v.x for v in verts); x_max = max(v.x for v in verts)
    y_min = min(v.y for v in verts); y_max = max(v.y for v in verts)
    z_min = min(v.z for v in verts)
    obj.location.x -= (x_min + x_max) / 2
    obj.location.y -= (y_min + y_max) / 2
    obj.location.z -= z_min
_centered_snap(obj)
bpy.context.view_layer.update()

# 3. Verifica dimensions vs bed
dims = obj.dimensions
print(f"[PLACE] dims={dims.x*1000:.2f} × {dims.y*1000:.2f} × {dims.z*1000:.2f} mm")
if dims.x * 1000 > 256 or dims.y * 1000 > 256 or dims.z * 1000 > 256:
    print(f"[PLACE] WARN: exceeds A1 build volume 256×256×256 mm")
else:
    print(f"[PLACE] fits A1 build volume")
print(f"[PLACE] location={tuple(round(v*1000,3) for v in obj.location)} mm")
```

---

## 10. Tabella quick reference — "fai questa cosa"

| Richiesta utente | API / funzione |
|---|---|
| "centralo sul letto" | `center_on_bed` + `snap_to_bed` (o `center_xy_and_snap_bed`) |
| "mettilo al centro" | `obj.location = (0, 0, 0)` + apply + set_origin(CURSOR_AT_0) |
| "appoggia la base a Z=0" | `snap_to_bed(obj)` |
| "sposta l'origine al fondo" | ORIGIN_CURSOR dopo cursor_to_object + manual z shift |
| "allinea a terra questi" | `for obj: snap_to_bed(obj)` |
| "mettili uno accanto all'altro" | `place_adjacent(a, b, axis='X', side='POS', gap_mm=2.0)` |
| "pila questi verticalmente" | `stack_vertically(list, gap_mm=0)` |
| "arrangia sul letto" | `pack_on_bed(list, bed_size_mm=(256,256))` |
| "pivot al centro di massa" | `set_origin(obj, 'ORIGIN_CENTER_OF_VOLUME')` |
| "origin dove ho il cursor" | cursor_to(x,y,z) + `set_origin(obj, 'ORIGIN_CURSOR')` |

---

## 11. Integrazione con altre KB

- Pre-export validation: `[preprint_validation]` richiede convenzione `(xy-centered, z_min=0)`.
- Orientamento ottimale: `[orientation_strategy]` decide la rotazione, **poi** questo doc posiziona.
- Split oversized: `[bisect_splitting]` usa `place_adjacent` per piazzare le metà sul bed separate.
- Workflow STL export: `[import_export]`.
