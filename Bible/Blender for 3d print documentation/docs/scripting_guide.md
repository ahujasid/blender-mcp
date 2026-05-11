# Scripting Guide — Blender Python per MCP e stampa 3D

> Fonte: Blender Python API docs — Quickstart, Overview, Best Practice, Gotchas, Tips & Tricks  
> Contesto: script eseguiti via `execute_blender_code` (MCP) direttamente in Blender

---

## Concetti fondamentali

### Come funziona bpy

Blender ha un interprete Python embedded che si avvia con Blender e rimane attivo per tutta la sessione. I moduli `bpy`, `bmesh`, `mathutils` sono disponibili nell'interprete senza installazione aggiuntiva.

```python
import bpy        # accesso a dati, operatori, tipi Blender
import bmesh      # API avanzata per manipolazione mesh
import mathutils  # Vector, Matrix, Euler, Quaternion
```

Quando si esegue codice via MCP (`execute_blender_code`), il codice gira direttamente nell'interprete di Blender con accesso completo al file .blend corrente e allo stato della UI.

### Data-blocks vs runtime data

**Data-blocks** (salvati nel .blend, accessibili via `bpy.data`):
- Objects, Meshes, Materials, Collections, Scenes, Images...
- Persistenti: sopravvivono a undo/redo, save/load
- Creati solo tramite `bpy.data.*.new()`, non con `bpy.types.Mesh()` direttamente

**Runtime data** (temporanei, non salvati):
- Stato del contesto (`bpy.context`)
- Dati BMesh (devono essere liberati esplicitamente con `bm.free()`)
- Dati di sessione come depsgraph evaluated

```python
import bpy

# CORRETTO: creare mesh tramite bpy.data
mesh = bpy.data.meshes.new(name="MyMesh")

# ERRORE: bpy.types.Mesh() non funziona
# mesh = bpy.types.Mesh()  # TypeError!
```

### Modifica diretta dei dati Blender

I riferimenti Python agli ID data-block **puntano direttamente ai dati interni** di Blender. Modificarli è immediatamente visibile nel viewport:

```python
import bpy

# Sposta il primo vertice del Cube direttamente
bpy.data.objects["Cube"].data.vertices[0].co.x += 1.0
# Il viewport si aggiorna immediatamente
```

---

## Gotchas critici per scripting mesh

### 1. Edit Mode vs Object Mode: i dati non sono sincronizzati

**Problema**: in Edit Mode, i dati mesh sono in un buffer separato (`BMesh`). Modifiche fatte in Edit Mode non sono visibili in `obj.data.vertices` fino a quando non si esce da Edit Mode.

```python
import bpy

# PROBLEMA: se l'utente è in Edit Mode, obj.data.vertices è out of sync
obj = bpy.context.active_object
mesh = obj.data
print(len(mesh.vertices))  # potrebbe non riflettere lo stato corrente!

# SOLUZIONE 1: assicurarsi di essere in Object Mode prima
bpy.ops.object.mode_set(mode='OBJECT')
mesh = bpy.context.active_object.data
print(len(mesh.vertices))  # dati aggiornati

# SOLUZIONE 2: usare bmesh.from_edit_mesh() per lavorare in Edit Mode
import bmesh
if bpy.context.mode == 'EDIT_MESH':
    bm = bmesh.from_edit_mesh(mesh)
    # lavora su bm...
    bmesh.update_edit_mesh(mesh)
```

### 2. BMesh: obbligatorio to_mesh() e free()

Dopo aver modificato una mesh con BMesh **devi sempre**:
1. Chiamare `bm.to_mesh(mesh)` per scrivere i dati nella mesh
2. Chiamare `bm.free()` per liberare la memoria

```python
import bpy
import bmesh

obj = bpy.context.active_object
mesh = obj.data

# OBJECT MODE: crea BMesh da mesh esistente
bpy.ops.object.mode_set(mode='OBJECT')
bm = bmesh.new()
bm.from_mesh(mesh)

# Modifica il BMesh
bmesh.ops.triangulate(bm, faces=bm.faces[:])

# OBBLIGATORIO: scrivi i risultati nella mesh
bm.to_mesh(mesh)
mesh.update()

# OBBLIGATORIO: libera la memoria BMesh
bm.free()

# EDIT MODE: usa from_edit_mesh / update_edit_mesh invece
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(mesh)
# ... modifica ...
bmesh.update_edit_mesh(mesh)
# NON chiamare bm.free() se usato con from_edit_mesh!
```

### 3. bpy.ops richiedono contesto corretto

Ogni operatore verifica il suo `poll()`. Se il contesto non è valido, solleva `RuntimeError`.

```python
import bpy

# ERRORE se nessun oggetto è attivo
# bpy.ops.object.mode_set(mode='EDIT')  # RuntimeError se poll() fallisce

# CORRETTO: verificare prima
if bpy.ops.object.mode_set.poll():
    bpy.ops.object.mode_set(mode='EDIT')

# OPPURE: gestire l'eccezione
try:
    bpy.ops.object.mode_set(mode='EDIT')
except RuntimeError as e:
    print(f"Contesto non valido: {e}")
```

**Cause comuni di poll() failure:**
- Nessun oggetto attivo
- Oggetto non selezionabile (locked, hidden)
- Modalità sbagliata (es. operatore mesh in Object Mode)
- Area UI sbagliata (es. operatore view3d eseguito da console)

### 4. Context Override con `bpy.context.temp_override()` — Blender 4.0+

In Blender 4.0 e superiori (incluso 5.x), il meccanismo per sovrascrivere il contesto di un operatore è cambiato. Il vecchio `bpy.ops.some_op(ctx, ...)` passando un dict context è **deprecato** e non funziona in 5.x. Si usa `bpy.context.temp_override(**kwargs)`.

**Perché è necessario:**  
Molti `bpy.ops.*` verificano il contesto corrente (area, regione, oggetto attivo). Quando si esegue codice via MCP in background o fuori da un'area VIEW_3D, questi operatori falliscono con `RuntimeError: poll() failed`. `temp_override` permette di forgiare temporaneamente un contesto valido.

#### Pattern base

```python
import bpy

# Sovrascrittura del contesto per un singolo operatore
with bpy.context.temp_override(area=area, region=region):
    bpy.ops.view3d.snap_selected_to_cursor()
```

#### Pattern MCP: trovare area VIEW_3D

```python
import bpy

def get_view3d_context():
    """
    Restituisce (area, region, space) dell'area VIEW_3D attiva.
    Usare con temp_override per operatori che richiedono viewport.
    """
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            space = next((s for s in area.spaces if s.type == 'VIEW_3D'), None)
            if region and space:
                return area, region, space
    return None, None, None

area, region, space = get_view3d_context()
if area:
    with bpy.context.temp_override(area=area, region=region, space_data=space):
        bpy.ops.view3d.view_all()  # opera come se eseguito nel viewport
```

#### Pattern MCP: operatori su oggetto specifico

```python
import bpy

def run_op_on_object(obj, op_func):
    """
    Esegue op_func con obj come active object, senza toccare lo stato corrente.
    """
    # Salva stato
    prev_active = bpy.context.view_layer.objects.active
    prev_selected = [o for o in bpy.context.selected_objects]
    
    # Imposta contesto per obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    # Esegui operazione
    result = op_func()
    
    # Ripristina stato precedente
    bpy.ops.object.select_all(action='DESELECT')
    for o in prev_selected:
        o.select_set(True)
    bpy.context.view_layer.objects.active = prev_active
    
    return result

# Esempio: applica modifier su oggetto non attivo
target = bpy.data.objects["MyMesh"]
run_op_on_object(target, lambda: bpy.ops.object.modifier_apply(modifier="Remesh"))
```

#### Pattern MCP: Edit Mode con temp_override

```python
import bpy

# Problema: bpy.ops.mesh.* richiedono contesto EDIT_MESH
# Soluzione: usare temp_override con oggetto attivo corretto

obj = bpy.data.objects["MyMesh"]
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

# Entra in Edit Mode
bpy.ops.object.mode_set(mode='EDIT')

# Trova area VIEW_3D per operatori che la richiedono
area, region, space = get_view3d_context()  # funzione definita sopra

if area:
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.0001)

bpy.ops.object.mode_set(mode='OBJECT')
```

#### Parametri disponibili per temp_override

| Parametro | Tipo | Descrizione |
|---|---|---|
| `area` | `bpy.types.Area` | Area UI (VIEW_3D, NODE_EDITOR, etc.) |
| `region` | `bpy.types.Region` | Regione (WINDOW, HEADER, etc.) |
| `space_data` | `bpy.types.Space` | Space dell'area (VIEW_3D, etc.) |
| `active_object` | `bpy.types.Object` | Oggetto attivo nel viewport |
| `selected_objects` | `list[Object]` | Lista oggetti selezionati |
| `edit_object` | `bpy.types.Object` | Oggetto in Edit Mode |
| `scene` | `bpy.types.Scene` | Scena corrente |
| `window` | `bpy.types.Window` | Finestra principale |

#### Nota per MCP (execute_blender_code)

Via MCP, Blender è in foreground con UI attiva, quindi `bpy.context.screen.areas` è popolato normalmente. `temp_override` funziona. Il caso in cui fallisce è quando Blender è avviato in **background mode** (`blender --background`), dove non ci sono aree UI — ma questo non si applica al workflow MCP standard.

```python
# Verifica sicura prima di usare temp_override
if bpy.context.screen is None:
    print("WARNING: Blender in background mode — temp_override non disponibile")
else:
    area, region, space = get_view3d_context()
    if area is None:
        print("WARNING: Nessuna area VIEW_3D trovata")
```

---

### 5. Tipi di facce: Polygon vs LoopTriangle vs BMFace

| Tipo | Accesso | Usare per |
|---|---|---|
| `bpy.types.MeshPolygon` | `mesh.polygons` | Export, lettura in Object Mode |
| `bpy.types.MeshLoopTriangle` | `mesh.loop_triangles` | Export a formati no n-gon (STL, etc.) |
| `bmesh.types.BMFace` | BMesh API, Edit Mode | Creazione e modifica mesh |

```python
import bpy

mesh = bpy.data.objects['Cube'].data

# Poligoni (Object Mode, n-gon support)
for poly in mesh.polygons:
    print(f"Faccia {poly.index}: {len(poly.vertices)} vertici")

# Triangoli (per export STL, etc.)
mesh.calc_loop_triangles()
for tri in mesh.loop_triangles:
    print(tri.vertices[:])  # tuple di 3 indici

# Area e normale di ogni faccia
for poly in mesh.polygons:
    print(poly.area, poly.normal)
```

### 5. Accedere a mesh valutata (con modificatori applicati)

```python
import bpy

obj = bpy.context.active_object
# La mesh "raw" senza modificatori
raw_mesh = obj.data

# La mesh con modificatori applicati (per export, analisi)
depsgraph = bpy.context.evaluated_depsgraph_get()
obj_eval = obj.evaluated_get(depsgraph)
eval_mesh = obj_eval.to_mesh()

# Usa eval_mesh per analisi/export
# IMPORTANTE: libera sempre dopo
obj_eval.to_mesh_clear()
```

---

## Best practice per script MCP

### Usa bpy.data direttamente invece di bpy.ops

Accesso diretto ai dati è più veloce, più controllabile, e non dipende dal contesto UI.

```python
import bpy

# LENTO/FRAGILE: usa ops (dipende dal contesto)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_pattern(pattern="Cube*")

# VELOCE/ROBUSTO: accesso diretto
for obj in bpy.data.objects:
    obj.select_set(obj.name.startswith("Cube"))
bpy.context.view_layer.objects.active = bpy.data.objects.get("Cube")

# LENTO: modificare proprietà via ops
# bpy.ops.transform.translate(value=(1,0,0))

# VELOCE: modifica diretta
bpy.context.active_object.location.x += 1.0
```

### Applicare trasformazioni prima di leggere i dati

Le coordinate dei vertici sono in **local space**. Per avere coordinate world space, applica prima la trasformazione.

```python
import bpy
import mathutils

obj = bpy.context.active_object
mesh = obj.data

# Coordinate locali (raw)
local_co = mesh.vertices[0].co

# Coordinate world (applica matrix_world)
world_co = obj.matrix_world @ local_co

# Per misurare dimensioni reali dell'oggetto
# PRIMA applica la scala (importante per stampa 3D!)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# OPPURE calcola le dimensioni tenendo conto della scala
bbox = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
# bound_box ha 8 angoli del bounding box in local space
```

### foreach_get / foreach_set — accesso rapido a grandi mesh

Iterare su `mesh.vertices` in Python puro è lento per mesh grandi. Usare `foreach_get`/`foreach_set` con array numpy o flat list.

```python
import bpy
import numpy as np

obj = bpy.context.active_object
mesh = obj.data

n = len(mesh.vertices)

# LENTO: loop Python
coords_slow = [v.co[:] for v in mesh.vertices]

# VELOCE: foreach_get
coords = np.zeros(n * 3, dtype=np.float32)
mesh.vertices.foreach_get("co", coords)
coords = coords.reshape((n, 3))

# Leggere le normali
normals = np.zeros(n * 3, dtype=np.float32)
mesh.vertices.foreach_get("normal", normals)
normals = normals.reshape((n, 3))

# foreach_set per scrivere (es. spostare tutti i vertici)
coords[:, 2] += 0.1  # sposta tutti i vertici di 0.1 su Z
mesh.vertices.foreach_set("co", coords.flatten())
mesh.update()

# Per i poligoni: leggere material index
n_polys = len(mesh.polygons)
mat_indices = np.zeros(n_polys, dtype=np.int32)
mesh.polygons.foreach_get("material_index", mat_indices)
```

### Misurare dimensioni oggetto

```python
import bpy
import mathutils

obj = bpy.data.objects['MyObject']

# Dimensioni tenendo conto della scala (in world units)
dims = obj.dimensions  # Vector(x, y, z) in world units

# Bounding box in world space
bbox_world = [obj.matrix_world @ mathutils.Vector(v) for v in obj.bound_box]
min_x = min(v.x for v in bbox_world)
max_x = max(v.x for v in bbox_world)
size_x = max_x - min_x

print(f"Dimensioni: {obj.dimensions.x:.3f} x {obj.dimensions.y:.3f} x {obj.dimensions.z:.3f} m")
```

---

## Workflow mesh per stampa 3D (Object Mode)

### Pattern completo: modifica mesh in Object Mode

```python
import bpy
import bmesh

def process_mesh_for_print(obj_name):
    obj = bpy.data.objects.get(obj_name)
    if obj is None or obj.type != 'MESH':
        print(f"Oggetto {obj_name} non trovato o non è una mesh")
        return

    # 1. Assicurarsi di essere in Object Mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # 2. Rendere l'oggetto attivo
    bpy.context.view_layer.objects.active = obj

    # 3. Applicare scala (CRITICO per stampa 3D)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # 4. Lavorare con BMesh
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Esempi di operazioni:
    # Triangola tutto
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    # Rimuovi duplicati
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0001)
    # Ricollega normali
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    # 5. Scrivi risultati e libera
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()

    print(f"Mesh processata: {len(mesh.vertices)} verts, {len(mesh.polygons)} polys")

process_mesh_for_print('Cube')
```

### Pattern: accesso mesh in EDIT Mode (bmesh.from_edit_mesh)

```python
import bpy
import bmesh

obj = bpy.context.active_object
mesh = obj.data

# Solo se siamo in Edit Mode
if bpy.context.mode == 'EDIT_MESH':
    bm = bmesh.from_edit_mesh(mesh)

    # Operazioni sul BMesh
    for face in bm.faces:
        face.select = face.normal.z > 0.5  # seleziona facce verso l'alto

    # Aggiorna la mesh nell'editor (non serve to_mesh)
    bmesh.update_edit_mesh(mesh)
    # NON chiamare bm.free() qui
```

---

## Tips & Tricks utili

### Debug: print e terminal

```python
import bpy

# print() va nel terminale (non nella UI)
# Avviare Blender dal terminale per vedere l'output

# Info base sull'oggetto attivo
obj = bpy.context.active_object
if obj:
    print(f"Nome: {obj.name}")
    print(f"Tipo: {obj.type}")
    print(f"Location: {obj.location[:]}")
    print(f"Dimensioni: {obj.dimensions[:]}")
    if obj.type == 'MESH':
        mesh = obj.data
        print(f"Vertices: {len(mesh.vertices)}")
        print(f"Edges: {len(mesh.edges)}")
        print(f"Polygons: {len(mesh.polygons)}")

# Misurare tempo di esecuzione
import time
t0 = time.time()
# ... operazione ...
print(f"Tempo: {time.time() - t0:.4f} sec")
```

### Accedere al data path di qualsiasi proprietà

In Blender, tasto destro su qualsiasi proprietà UI > "Copy Data Path" dà il path Python completo.

```python
import bpy

# Esempio di paths ottenuti così:
bpy.context.scene.render.resolution_x
bpy.context.active_object.modifiers["Subdivision"].levels
bpy.data.materials["Material"].node_tree.nodes["Principled BSDF"].inputs[0].default_value
```

### Eseguire script esterno dall'interno di Blender

```python
import bpy
import os

# Script relativo al .blend file
filename = os.path.join(os.path.dirname(bpy.data.filepath), "myscript.py")
exec(compile(open(filename).read(), filename, 'exec'))

# Oppure con importlib per reload (sviluppo iterativo)
import importlib
import myscript
importlib.reload(myscript)
myscript.main()
```

### Abilitare debug operatori

```python
import bpy

# Logga ogni operatore chiamato (nel terminale)
bpy.app.debug_wm = True

# Disabilita dopo l'uso
bpy.app.debug_wm = False
```

### Iterare su tutti gli oggetti mesh della scena con filtro tipo

```python
import bpy

# Solo mesh objects
mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

# Tutti gli oggetti visibili
visible = [obj for obj in bpy.context.scene.objects if not obj.hide_viewport]

# Oggetti selezionati di tipo MESH
selected_meshes = [
    obj for obj in bpy.context.selected_objects
    if obj.type == 'MESH'
]
```

### Interrompere un loop infinito accidentale

In Blender (avviato da terminale): `Ctrl+C` nel terminale interrompe lo script.

### Verificare modo corrente e cambiarlo in sicurezza

```python
import bpy

def ensure_object_mode():
    """Assicura che siamo in Object Mode."""
    if bpy.context.active_object is None:
        return False
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    return True

def ensure_edit_mode(obj):
    """Entra in Edit Mode sull'oggetto specificato."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
```

---

## Riferimento rapido errori comuni

| Errore | Causa | Soluzione |
|---|---|---|
| `RuntimeError: Operator poll() failed` | Contesto non valido per l'operatore | Verificare mode, selezione, area UI |
| `TypeError: bpy_struct.__new__` | Tentativo di creare tipo con `()` | Usare `bpy.data.*.new()` |
| Vertici non aggiornati in Edit Mode | BMesh desincronizzato | Uscire da Edit Mode o usare `bmesh.from_edit_mesh()` |
| Crash accesso dati eliminati | Puntatore Python a dati rimossi | Non tenere riferimenti dopo `remove()` |
| Dimensioni sbagliate | Scala non applicata | `bpy.ops.object.transform_apply(scale=True)` |
| Mesh corrotta dopo BMesh | Dimenticato `bm.to_mesh()` o `bm.free()` | Chiamare sempre entrambi |
| `RuntimeError: poll()` con ops viewport | Area VIEW_3D non nel contesto MCP | Usare `temp_override(area=area, region=region)` |
| `AttributeError: temp_override` | Blender < 4.0 (vecchia API) | In 5.x sempre disponibile; non usare dict context override |
