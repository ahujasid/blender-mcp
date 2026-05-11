# bpy Basics — Accesso ai dati Blender via Python

> Fonte: Blender Python API docs — bpy.context, bpy.data, bpy.ops, bpy.props

---

## bpy.context — Accesso al contesto corrente

`bpy.context` rispecchia il contesto attuale dell'interfaccia: cambia a seconda di dove si trova il cursore, qual è l'oggetto attivo, in che modalità si è. È **read-only**: i valori non si possono assegnare direttamente, ma si possono cambiare tramite la data API o gli operatori.

> Nota: `bpy.context.active_object = obj` genera un errore.  
> Usare invece: `bpy.context.view_layer.objects.active = obj`

### Proprietà principali

| Proprietà | Tipo | Descrizione |
|---|---|---|
| `active_object` | `Object` o `None` | L'oggetto attivo nel viewport |
| `object` | `Object` o `None` | Alias di `active_object` (usato in operatori) |
| `selected_objects` | `list[Object]` | Tutti gli oggetti selezionati |
| `scene` | `Scene` | La scena corrente |
| `view_layer` | `ViewLayer` | Il view layer corrente |
| `mode` | `str` | Modalità corrente: `'OBJECT'`, `'EDIT'`, `'SCULPT'`, etc. |
| `window` | `Window` | La finestra corrente |
| `screen` | `Screen` | Lo screen corrente |
| `area` | `Area` | L'area corrente (es. VIEW_3D) |
| `region` | `Region` | La regione corrente |
| `tool_settings` | `ToolSettings` | Impostazioni degli strumenti |

### Come usarle in script

```python
import bpy

# Oggetto attivo
obj = bpy.context.active_object
if obj is None:
    print("Nessun oggetto attivo")
else:
    print(obj.name, obj.type)

# Oggetti selezionati
for obj in bpy.context.selected_objects:
    print(obj.name)

# Scena e view layer
scene = bpy.context.scene
vl = bpy.context.view_layer

# Impostare l'oggetto attivo (via view_layer, non context direttamente)
target = bpy.data.objects['Cube']
bpy.context.view_layer.objects.active = target

# Modalità corrente
print(bpy.context.mode)  # 'OBJECT', 'EDIT_MESH', etc.

# Controllare che ci sia un oggetto selezionato prima di operare
if bpy.context.active_object and bpy.context.active_object.type == 'MESH':
    mesh = bpy.context.active_object.data
```

---

## bpy.data — Accesso ai dati globali del file .blend

`bpy.data` è il punto di accesso a tutti i dati del file .blend caricato. Corrisponde al tipo `bpy.types.BlendData` e contiene collezioni di tutti i data-block.

### Collezioni principali

| Accesso | Tipo | Descrizione |
|---|---|---|
| `bpy.data.objects` | `BlendDataObjects` | Tutti gli oggetti della scena |
| `bpy.data.meshes` | `BlendDataMeshes` | Tutti i dati mesh |
| `bpy.data.materials` | `BlendDataMaterials` | Tutti i materiali |
| `bpy.data.collections` | `BlendDataCollections` | Tutte le collezioni |
| `bpy.data.scenes` | `BlendDataScenes` | Tutte le scene |
| `bpy.data.images` | `BlendDataImages` | Tutte le immagini |
| `bpy.data.filepath` | `str` | Percorso del file .blend corrente |

### Iterare e accedere per nome

```python
import bpy

# Iterare su tutti gli oggetti
for obj in bpy.data.objects:
    print(obj.name)

# Accesso per nome (stringa)
obj = bpy.data.objects['Cube']

# Accesso per indice (meno stabile se la scena cambia)
obj = bpy.data.objects[0]

# Verificare esistenza prima di accedere
if 'Cube' in bpy.data.objects:
    obj = bpy.data.objects['Cube']

# Lista dei nomi di tutte le scene
print(bpy.data.scenes.keys())

# Lista di tutti gli oggetti
all_objs = list(bpy.data.objects)
```

### bpy.data.meshes — Gestione mesh

```python
import bpy

# Accedere alla mesh di un oggetto tramite bpy.data
mesh = bpy.data.meshes['Cube']

# Accedere alla mesh tramite l'oggetto
obj = bpy.data.objects['Cube']
mesh = obj.data  # equivalente se obj.type == 'MESH'

# Rimuovere una mesh orfana
if 'Cube' in bpy.data.meshes:
    mesh = bpy.data.meshes['Cube']
    bpy.data.meshes.remove(mesh)
```

### bpy.data.materials — Materiali

```python
import bpy

# Creare un nuovo materiale
mat = bpy.data.materials.new(name="MyMaterial")

# Assegnare un materiale a un oggetto
obj = bpy.context.active_object
if obj.data.materials:
    obj.data.materials[0] = mat
else:
    obj.data.materials.append(mat)

# Accedere a materiali esistenti
for mat in bpy.data.materials:
    print(mat.name)
```

### bpy.data.collections — Collections

```python
import bpy

# Creare una nuova collection
col = bpy.data.collections.new("MyTestCollection")

# Aggiungere la collection alla scena
bpy.context.scene.collection.children.link(col)

# Spostare un oggetto in una collection
obj = bpy.data.objects['Cube']
col.objects.link(obj)
# Rimuovere dalla collection precedente se necessario
bpy.context.scene.collection.objects.unlink(obj)

# Proprietà custom su una collection
col["MySettings"] = {"foo": 10, "bar": "spam"}
del col["MySettings"]
```

### Creare, duplicare, eliminare dati

```python
import bpy

# Creare una nuova mesh (non si usa bpy.types.Mesh() direttamente!)
mesh = bpy.data.meshes.new(name="MyMesh")

# Creare un nuovo oggetto e linkarlo alla scena
obj = bpy.data.objects.new(name="MyObject", object_data=mesh)
bpy.context.scene.collection.objects.link(obj)

# Rimuovere un oggetto dalla scena
bpy.data.objects.remove(obj, do_unlink=True)

# Rimuovere una mesh
bpy.data.meshes.remove(mesh)

# Creare un materiale
mat = bpy.data.materials.new(name="MyMaterial")
bpy.data.materials.remove(mat)
```

### bpy.context.active_object vs bpy.data.objects['name']

| | `bpy.context.active_object` | `bpy.data.objects['name']` |
|---|---|---|
| Dipende da contesto | Si (può essere None) | No |
| Richiede che sia attivo | Si | No |
| Uso tipico | Script interattivi | Script che operano su oggetti specifici |
| Accesso diretto | Sempre rapido | Sempre rapido |

```python
# Context: oggetto attivo (dipende dall'utente)
obj = bpy.context.active_object

# Data: accesso diretto per nome (indipendente dal contesto)
obj = bpy.data.objects['Cube']
```

---

## bpy.ops — Usare gli operatori

Gli operatori (`bpy.ops`) sono gli strumenti che l'utente usa tramite pulsanti, menu e shortcut. Da Python si possono chiamare con impostazioni personalizzate.

### Come funzionano

Gli operatori richiedono un **contesto corretto** per funzionare. Se il contesto non è valido, sollevano un `RuntimeError`. Ogni operatore ha un metodo `poll()` che verifica se può essere eseguito nel contesto corrente.

```python
import bpy

# Chiamare un operatore semplice
bpy.ops.mesh.subdivide(number_cuts=3, smoothness=0.5)

# Controllare poll() prima di chiamare (evita RuntimeError)
if bpy.ops.object.mode_set.poll():
    bpy.ops.object.mode_set(mode='EDIT')

# Esempio: flip normals (richiede Edit Mode + mesh selezionata)
bpy.ops.mesh.flip_normals()
bpy.ops.mesh.hide(unselected=False)
bpy.ops.object.transform_apply()
```

### Override context (temp_override)

Permette di sovrascrivere temporaneamente il contesto che vede l'operatore:

```python
import bpy
from bpy import context

# Eliminare tutti gli oggetti in scena (non solo i selezionati)
context_override = context.copy()
context_override["selected_objects"] = list(context.scene.objects)
with context.temp_override(**context_override):
    bpy.ops.object.delete()

# Eseguire un operatore in un'area specifica (es. VIEW_3D)
for window in context.window_manager.windows:
    screen = window.screen
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            with context.temp_override(window=window, area=area):
                bpy.ops.screen.screen_full_area()
            break
```

### Execution context

```python
import bpy

# Eseguire con interazione utente (INVOKE chiama anche invoke())
bpy.ops.object.collection_instance_add('INVOKE_DEFAULT')

# Default: EXEC_DEFAULT (solo execute(), nessuna interazione utente)
bpy.ops.object.delete()  # equivalente a EXEC_DEFAULT
```

### Limiti degli operatori

- **Non ricevono dati diretti** (oggetti, mesh, materiali) — usano il contesto
- Il valore di ritorno è lo stato (`{'FINISHED'}`, `{'CANCELLED'}`)
- Se il poll() fallisce, sollevano `RuntimeError`
- Sono più lenti del direct data access per operazioni ripetitive

### Differenza: ops vs data access diretto

| Situazione | Usa |
|---|---|
| Operazione complessa già implementata in Blender | `bpy.ops.*` |
| Modificare proprietà singole | `bpy.data.*` direct access |
| Performance critica / loop | `bpy.data.*` direct access |
| Aggiungere/rimuovere vertici, facce | `bmesh` API |
| Bisogno di interazione utente (invoke) | `bpy.ops.*` con `INVOKE_DEFAULT` |

---

## Pattern essenziali

```python
import bpy

# --- Selezionare oggetti ---
# Deselezionare tutto
bpy.ops.object.select_all(action='DESELECT')
# Selezionare per nome
bpy.data.objects['Cube'].select_set(True)
# Rendere attivo
bpy.context.view_layer.objects.active = bpy.data.objects['Cube']

# --- Cambiare mode ---
# Richede che ci sia un oggetto attivo
bpy.ops.object.mode_set(mode='EDIT')    # OBJECT -> EDIT
bpy.ops.object.mode_set(mode='OBJECT')  # EDIT -> OBJECT
# Verifica sicura
if bpy.context.active_object:
    bpy.ops.object.mode_set(mode='OBJECT')

# --- Accedere alla mesh ---
obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    mesh = obj.data                    # bpy.types.Mesh
    verts = mesh.vertices              # in OBJECT mode
    polys = mesh.polygons              # facce (n-gon support)
    loops = mesh.loop_triangles        # triangoli tessellati

# --- Iterare su oggetti della scena ---
# Tutti gli oggetti
for obj in bpy.context.scene.objects:
    print(obj.name, obj.type)

# Solo mesh
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        print(obj.name)

# Tramite bpy.data (tutti, non solo nella scena attiva)
for obj in bpy.data.objects:
    print(obj.name)

# --- Modificare proprietà ---
obj = bpy.context.active_object
obj.location = (1.0, 2.0, 0.0)       # Mathutils Vector
obj.scale = (1.0, 1.0, 1.0)
obj.name = "NuovoNome"

# Proprietà annidate
bpy.context.scene.render.resolution_x = 1920
bpy.data.scenes[0].render.resolution_percentage = 100
bpy.data.scenes[0].objects["Torus"].data.vertices[0].co.x = 1.0

# --- Creare nuovo oggetto mesh da zero ---
mesh = bpy.data.meshes.new("MyMesh")
obj = bpy.data.objects.new("MyObj", mesh)
bpy.context.scene.collection.objects.link(obj)

# Popolare la mesh con dati
verts = [(0,0,0), (1,0,0), (1,1,0), (0,1,0)]
faces = [(0, 1, 2, 3)]
mesh.from_pydata(verts, [], faces)
mesh.update()
```

---

## bpy.props — Definire proprietà personalizzate

`bpy.props` si usa per aggiungere proprietà a classi Blender (Operator, Panel, etc.). Si usa raramente in script MCP diretti, ma è utile per addon.

```python
import bpy

# Tipi disponibili:
# bpy.props.BoolProperty()
# bpy.props.IntProperty()
# bpy.props.FloatProperty()
# bpy.props.FloatVectorProperty()
# bpy.props.StringProperty()
# bpy.props.EnumProperty()
# bpy.props.CollectionProperty()
# bpy.props.PointerProperty()

# Esempio: aggiungere proprietà a una classe esistente
bpy.types.Object.my_custom_float = bpy.props.FloatProperty(
    name="My Float",
    default=1.0,
    min=0.0,
    max=10.0
)

# Rimuovere la proprietà
bpy.utils.unregister_class  # (se era parte di una classe registrata)
del bpy.types.Object.my_custom_float
```

### Proprietà custom su data-block (senza bpy.props)

```python
import bpy

# Assegnabile su qualsiasi ID data-block
obj = bpy.context.object
obj["MyOwnProperty"] = 42

if "SomeProp" in obj:
    print("Property found:", obj["SomeProp"])

# Fallback value (come dict.get)
value = bpy.data.scenes["Scene"].get("test_prop", "fallback value")

# Supporta: int, float, string, array di int/float, dict (solo basic types)
```
