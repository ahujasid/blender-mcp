# Blender Object & Scene Types — Struttura Dati

Fonte: Blender Python API 5.x — `bpy.types.Object`, `Scene`, `BlendData`, `Context`, `ViewLayer`, `UnitSettings`, `Collection`, `Material`
Contesto: accesso struttura scena da Python per scripting stampa 3D FDM.

---

## Object (`bpy.types.Object`)

**Classe:** `class bpy.types.Object(ID)`
Data-block oggetto che definisce un oggetto nella scena.

### Proprietà identità e tipo

| Proprietà | Tipo | Note |
|-----------|------|------|
| `name` | `str` | Nome dell'oggetto (ereditato da ID) |
| `type` | `Literal['MESH','CURVE','SURFACE','META','FONT','ARMATURE','LATTICE','EMPTY','GPENCIL','CAMERA','LIGHT','SPEAKER','LIGHT_PROBE','VOLUME','CURVES','POINTCLOUD']` | Tipo oggetto (readonly) |
| `data` | `ID` | Dati dell'oggetto (mesh, curve, ecc.) |
| `mode` | `Literal[Object Mode Items]` | Modalità interazione (readonly) |

### Trasformazioni

| Proprietà | Tipo | Default | Note |
|-----------|------|---------|------|
| `location` | `mathutils.Vector` | `(0,0,0)` | Posizione in world space |
| `rotation_euler` | `mathutils.Euler` | `(0,0,0)` | Rotazione Euler (XYZ gradi in radianti) |
| `rotation_quaternion` | `mathutils.Quaternion` | `(1,0,0,0)` | Rotazione Quaternion |
| `scale` | `mathutils.Vector` | `(1,1,1)` | Scala |
| `dimensions` | `mathutils.Vector` | `(0,0,0)` | Dimensioni bounding box assolute (world space) |
| `matrix_world` | `mathutils.Matrix` | Identity | Matrice trasformazione world space (4x4) |
| `matrix_local` | `mathutils.Matrix` | Identity | Matrice locale rispetto al parent |
| `matrix_basis` | `mathutils.Matrix` | Identity | Matrice base (senza constraints/parent) |
| `delta_location` | `mathutils.Vector` | `(0,0,0)` | Traslazione extra aggiunta |
| `delta_rotation_euler` | `mathutils.Euler` | `(0,0,0)` | Rotazione extra aggiunta |
| `delta_scale` | `mathutils.Vector` | `(1,1,1)` | Scala extra aggiunta |

### Visualizzazione e selezione

| Proprietà | Tipo | Default | Note |
|-----------|------|---------|------|
| `hide_viewport` | `bool` | `False` | Nascosto nei viewport |
| `hide_render` | `bool` | `False` | Nascosto in render |
| `hide_select` | `bool` | `False` | Non selezionabile |
| `color` | `bpy_prop_array[float]` | `(1,1,1,1)` | Colore oggetto RGBA |
| `display_type` | `Literal['BOUNDS','WIRE','SOLID','TEXTURED']` | `'TEXTURED'` | Tipo visualizzazione |

### Bounding box

| Proprietà | Tipo | Note |
|-----------|------|------|
| `bound_box` | `bpy_prop_array[float]` | 8 corner × 3 coordinate in object space (readonly) |
| `dimensions` | `mathutils.Vector` | Dimensioni assolute bounding box (readonly) |

### Materiali

| Proprietà | Tipo | Note |
|-----------|------|------|
| `active_material` | `Material` | Materiale attivo |
| `active_material_index` | `int` | Indice slot materiale attivo |
| `material_slots` | — | Lista slot materiali |

### Modifiers e constraints

| Proprietà | Tipo | Note |
|-----------|------|------|
| `modifiers` | `ObjectModifiers[Modifier]` | Modificatori che agiscono sulla geometria (readonly) |
| `constraints` | `ObjectConstraints[Constraint]` | Constraints sulla trasformazione (readonly) |

### Shape keys

| Proprietà | Tipo | Note |
|-----------|------|------|
| `active_shape_key` | `ShapeKey` | Shape key corrente (readonly) |
| `active_shape_key_index` | `int` | Indice shape key corrente |
| `add_rest_position_attribute` | `bool` | Aggiunge attributo `rest_position` |

### Metodi principali

```python
# Selezione
obj.select_get(view_layer=None) -> bool
# Testa se l'oggetto è selezionato (per view layer)

obj.select_set(state: bool, view_layer=None)
# Seleziona/deseleziona l'oggetto

# Visibilità
obj.hide_get(view_layer=None) -> bool
# Testa se l'oggetto è nascosto nel viewport

obj.hide_set(state: bool, view_layer=None)
# Nasconde/mostra l'oggetto nel viewport
```

### Pattern d'uso comuni

```python
import bpy

obj = bpy.context.active_object
# oppure
obj = bpy.data.objects['NomeOggetto']

# Tipo check
if obj.type == 'MESH':
    mesh = obj.data  # bpy.types.Mesh

# Selezione
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

# Dimensioni in mm (se scena in metri con scale_length=0.001)
dims_mm = obj.dimensions * 1000
print(f"X={dims_mm.x:.2f}mm, Y={dims_mm.y:.2f}mm, Z={dims_mm.z:.2f}mm")

# Trasformazione world space vertex
import mathutils
world_co = obj.matrix_world @ mathutils.Vector(obj.data.vertices[0].co)

# Bounding box in world space (8 angoli)
bbox_world = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
bbox_min = mathutils.Vector((min(v.x for v in bbox_world),
                              min(v.y for v in bbox_world),
                              min(v.z for v in bbox_world)))
bbox_max = mathutils.Vector((max(v.x for v in bbox_world),
                              max(v.y for v in bbox_world),
                              max(v.z for v in bbox_world)))
```

---

## Scene (`bpy.types.Scene`)

**Classe:** `class bpy.types.Scene(ID)`
Data-block scena, contiene oggetti e definisce impostazioni tempo e render.

### Proprietà principali

| Proprietà | Tipo | Note |
|-----------|------|------|
| `objects` | `SceneObjects[Object]` | Tutti gli oggetti della scena (readonly) |
| `collection` | `Collection` | Root collection della scena (readonly, never None) |
| `unit_settings` | `UnitSettings` | Impostazioni unità di misura (readonly, never None) |
| `cursor` | `View3DCursor` | Cursore 3D della scena (readonly, never None) |
| `camera` | `Object` | Camera attiva per il rendering |
| `background_set` | `Scene` | Scena di sfondo |

### Frame e animazione

| Proprietà | Tipo | Default | Note |
|-----------|------|---------|------|
| `frame_current` | `int` | `1` | Frame corrente |
| `frame_start` | `int` | `1` | Primo frame playback/render |
| `frame_end` | `int` | `250` | Ultimo frame playback/render |
| `frame_step` | `int` | `1` | Step frame durante playback |

### Fisica

| Proprietà | Tipo | Default | Note |
|-----------|------|---------|------|
| `gravity` | `mathutils.Vector` | `(0,0,-9.81)` | Accelerazione gravitazionale |

### Pattern d'uso

```python
import bpy

scene = bpy.context.scene
# oppure
scene = bpy.data.scenes['Scene']

# Iterare oggetti scena
for obj in scene.objects:
    if obj.type == 'MESH':
        print(obj.name, obj.dimensions)

# Cursor position
cursor_loc = scene.cursor.location

# Unit settings
units = scene.unit_settings
print(units.system, units.scale_length, units.length_unit)
```

---

## UnitSettings (`bpy.types.UnitSettings`)

**Classe:** `class bpy.types.UnitSettings(bpy_struct)`
Impostazioni unità di misura della scena (accessibile via `scene.unit_settings`).

### Proprietà

| Proprietà | Tipo | Default | Valori |
|-----------|------|---------|--------|
| `system` | `Literal['NONE','METRIC','IMPERIAL']` | `'NONE'` | Sistema unità |
| `scale_length` | `float` | `0.0` | Scala per conversione Blender units ↔ dimensioni reali |
| `length_unit` | `Literal['DEFAULT',...]` | `'DEFAULT'` | Unità lunghezza (DEFAULT, MILLIMETERS, CENTIMETERS, METERS, ecc.) |
| `system_rotation` | `Literal['DEGREES','RADIANS']` | `'DEGREES'` | Unità per angoli |
| `use_separate` | `bool` | `False` | Mostra unità in coppia (es. 1m 0cm) |

### Setup per stampa 3D (millimetri)

```python
import bpy

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001  # 1 BU = 1mm
scene.unit_settings.length_unit = 'MILLIMETERS'

# Verificare setup corrente
units = scene.unit_settings
print(f"Sistema: {units.system}")
print(f"Scale: {units.scale_length}")  # 0.001 = mm, 0.01 = cm, 1.0 = m
print(f"Unità: {units.length_unit}")
```

**Schema conversioni:**
- `scale_length = 0.001` → 1 BU = 1mm (corretto per stampa 3D in mm)
- `scale_length = 0.01` → 1 BU = 1cm
- `scale_length = 1.0` → 1 BU = 1m (default Blender)

---

## BlendData (`bpy.types.BlendData`)

**Classe:** `class bpy.types.BlendData(bpy_struct)`
Struttura dati principale che rappresenta il file `.blend`. Accessibile globalmente come `bpy.data`.

### Collezioni principali

| Proprietà | Tipo | Descrizione |
|-----------|------|-------------|
| `objects` | `BlendDataObjects[Object]` | Tutti gli oggetti |
| `meshes` | `BlendDataMeshes[Mesh]` | Tutte le mesh |
| `materials` | `BlendDataMaterials[Material]` | Tutti i materiali |
| `collections` | `BlendDataCollections[Collection]` | Tutte le collection |
| `scenes` | `BlendDataScenes[Scene]` | Tutte le scene |
| `images` | `BlendDataImages[Image]` | Tutte le immagini |
| `textures` | `BlendDataTextures[Texture]` | Tutte le texture |
| `node_groups` | `BlendDataNodeTrees[NodeTree]` | Tutti i node group |
| `cameras` | `BlendDataCameras[Camera]` | Tutte le camere |
| `lights` | `BlendDataLights[Light]` | Tutte le luci |
| `curves` | `BlendDataCurves[Curve]` | Tutte le curve |
| `armatures` | `BlendDataArmatures[Armature]` | Tutte le armature |
| `actions` | `BlendDataActions[Action]` | Tutte le action |

### Proprietà file

| Proprietà | Tipo | Note |
|-----------|------|------|
| `filepath` | `str` | Percorso al file .blend (readonly) |
| `is_dirty` | `bool` | Ci sono modifiche non salvate (readonly) |
| `is_saved` | `bool` | Il file è stato salvato (readonly) |
| `version` | `bpy_prop_array[int]` | Versione formato file (readonly) |

### Metodi

```python
bpy.data.batch_remove(ids)
# Rimuove più ID in un colpo solo (più veloce di remove() singoli)
# ATTENZIONE: può rompere Blender se si rimuovono dati critici

bpy.data.pack_linked_ids_hierarchy(root_id)
# Packa un ID linked e le sue dipendenze nel blend corrente
```

### Pattern d'uso

```python
import bpy

# Accesso per nome
obj = bpy.data.objects['Cube']
mesh = bpy.data.meshes['CubeMesh']
mat = bpy.data.materials['MyMaterial']

# Accesso per indice
first_obj = bpy.data.objects[0]

# Iterare
for obj in bpy.data.objects:
    print(obj.name, obj.type)

# Creare nuovo materiale
mat = bpy.data.materials.new(name='NuovoMat')

# Creare nuova mesh
mesh = bpy.data.meshes.new(name='NuovaMesh')

# Rimuovere oggetto
obj = bpy.data.objects['OggettoDaRimuovere']
bpy.data.objects.remove(obj, do_unlink=True)

# Rimuovere mesh orfana
for mesh in bpy.data.meshes:
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

# Batch remove (più veloce)
orphans = [m for m in bpy.data.meshes if m.users == 0]
bpy.data.batch_remove(orphans)
```

---

## Context (`bpy.types.Context`)

**Classe:** `class bpy.types.Context(bpy_struct)`
Contesto corrente del window manager. Accessibile come `bpy.context`.

### Proprietà principali

| Proprietà | Tipo | Note |
|-----------|------|------|
| `scene` | `Scene` | Scena corrente (readonly) |
| `view_layer` | `ViewLayer` | View layer attivo (readonly) |
| `blend_data` | `BlendData` | Equivalente a `bpy.data` (readonly) |
| `collection` | `Collection` | Collection corrente (readonly) |
| `mode` | `Literal[Context Mode Items]` | Modalità corrente es. 'OBJECT', 'EDIT_MESH' (readonly) |
| `area` | `Area` | Area corrente UI (readonly) |
| `region` | `Region` | Regione corrente (readonly) |
| `tool_settings` | `ToolSettings` | Impostazioni tool (readonly) |
| `preferences` | `Preferences` | Preferenze Blender (readonly) |

### Screen Context (molto usato in scripting)

| Proprietà | Tipo | Note |
|-----------|------|------|
| `active_object` | `Object` | Oggetto attivo |
| `object` | `Object` | Oggetto corrente |
| `selected_objects` | `Sequence[Object]` | Oggetti selezionati |
| `visible_objects` | `Sequence[Object]` | Oggetti visibili nel viewport |
| `editable_objects` | `Sequence[Object]` | Oggetti editabili |
| `selected_editable_objects` | `Sequence[Object]` | Selezionati ed editabili |
| `edit_object` | `Object` | Oggetto in edit mode |

### Buttons Context

| Proprietà | Tipo | Note |
|-----------|------|------|
| `object` | `Object` | Oggetto corrente nei Properties |
| `mesh` | `Mesh` | Mesh corrente nei Properties |
| `material` | `Material` | Materiale corrente |
| `material_slot` | `MaterialSlot` | Slot materiale corrente |

### Pattern d'uso

```python
import bpy

ctx = bpy.context

# Oggetto attivo
obj = ctx.active_object
if obj and obj.type == 'MESH':
    mesh = obj.data

# Oggetti selezionati
for sel_obj in ctx.selected_objects:
    print(sel_obj.name)

# Cambio modalità
bpy.ops.object.mode_set(mode='EDIT')
print(ctx.mode)  # 'EDIT_MESH'
bpy.ops.object.mode_set(mode='OBJECT')

# View layer corrente
vl = ctx.view_layer
```

---

## ViewLayer (`bpy.types.ViewLayer`)

**Classe:** `class bpy.types.ViewLayer(bpy_struct)`
Layer di visualizzazione che controlla quali oggetti vengono renderizzati.

### Proprietà principali

| Proprietà | Tipo | Note |
|-----------|------|------|
| `name` | `str` | Nome del view layer |
| `objects` | `LayerObjects[Object]` | Tutti gli oggetti in questo layer (readonly) |
| `layer_collection` | `LayerCollection` | Root collection hierarchy (readonly) |
| `active_layer_collection` | `LayerCollection` | Collection layer attiva |
| `depsgraph` | `Depsgraph` | Dependency graph (readonly) |
| `material_override` | `Material` | Materiale override per tutti gli oggetti |
| `use` | `bool` | Abilita/disabilita il rendering di questo layer |

### Render passes (stampa 3D: non rilevanti ma utili per preview)

| Proprietà | Default | Note |
|-----------|---------|------|
| `use_pass_combined` | `True` | RGBA completo |
| `use_pass_ambient_occlusion` | `False` | Ambient Occlusion |
| `use_pass_cryptomatte_object` | `False` | Cryptomatte per oggetti |

### Pattern d'uso

```python
import bpy

view_layer = bpy.context.view_layer

# Settare oggetto attivo
view_layer.objects.active = bpy.data.objects['MioOggetto']

# Oggetti nel layer
for obj in view_layer.objects:
    print(obj.name, obj.visible_get())

# Usato spesso con select_set
obj = bpy.data.objects['Target']
obj.select_set(True, view_layer=view_layer)
view_layer.objects.active = obj
```

---

## Collection (`bpy.types.Collection`)

**Classe:** `class bpy.types.Collection(ID)`
Collezione di oggetti (come i layer di Blender pre-2.8). Accessibile da `bpy.data.collections`.

### Proprietà

| Proprietà | Tipo | Note |
|-----------|------|------|
| `objects` | `CollectionObjects[Object]` | Oggetti direttamente in questa collection (readonly) |
| `all_objects` | `bpy_prop_collection[Object]` | Tutti gli oggetti incluse sub-collection (readonly) |
| `children` | `CollectionChildren[Collection]` | Sub-collection dirette (readonly) |
| `children_recursive` | `list[Collection]` | Tutti i discendenti (readonly, O(n)) |
| `hide_viewport` | `bool` | Nascosto nei viewport |
| `hide_render` | `bool` | Nascosto nel render |
| `hide_select` | `bool` | Non selezionabile |
| `instance_offset` | `mathutils.Vector` | Offset dall'origine per instancing |
| `color_tag` | `Literal[Collection Color Items]` | Tag colore |

### Metodi

```python
collection.children_recursive  # property: lista flat di tutte le sub-collection
collection.users_dupli_group   # property: tuple di oggetti che istanziano questa collection
```

### Pattern d'uso

```python
import bpy

# Creare collection
coll = bpy.data.collections.new('MiaCollection')
bpy.context.scene.collection.children.link(coll)

# Aggiungere oggetto a collection
obj = bpy.data.objects['Cube']
coll.objects.link(obj)

# Rimuovere oggetto da collection
coll.objects.unlink(obj)

# Iterare tutti gli oggetti (incluse sub-collection)
for obj in coll.all_objects:
    print(obj.name)

# Nascondere collection intera
coll.hide_viewport = True

# Trovare collection per nome
my_coll = bpy.data.collections.get('MiaCollection')
if my_coll:
    print("Trovata:", my_coll.name)
```

---

## Material (`bpy.types.Material`)

**Classe:** `class bpy.types.Material(ID)`
Materiale che definisce l'aspetto visivo degli oggetti.

### Proprietà principali

| Proprietà | Tipo | Default | Note |
|-----------|------|---------|------|
| `use_nodes` | `bool` | — | Usa node tree per il materiale |
| `node_tree` | `NodeTree` | — | Node tree (readonly, quando `use_nodes=True`) |
| `diffuse_color` | `bpy_prop_array[float]` | `(0.8,0.8,0.8,1.0)` | Colore diffuso RGBA |
| `roughness` | `float` | `0.4` | Rugosità [0,1] |
| `metallic` | `float` | `0.0` | Metallic [0,1] |
| `specular_color` | `mathutils.Color` | `(1,1,1)` | Colore speculare RGB |
| `specular_intensity` | `float` | `0.5` | Intensità speculare [0,1] |
| `alpha_threshold` | `float` | `0.5` | Soglia alpha per trasparenza |

### Blend mode e render

| Proprietà | Tipo | Default | Note |
|-----------|------|---------|------|
| `blend_method` | `Literal['OPAQUE','CLIP','HASHED','BLEND']` | `'OPAQUE'` | Modo blend (deprecated: usa `surface_render_method`) |
| `displacement_method` | `Literal['BUMP','DISPLACEMENT','BOTH']` | `'BUMP'` | Metodo displacement |
| `pass_index` | `int` | `0` | Indice per Material Index render pass |

### Pattern d'uso

```python
import bpy

# Creare materiale semplice
mat = bpy.data.materials.new(name='PrintMaterial')
mat.use_nodes = True

# Impostare colore diffuso (senza nodes)
mat.diffuse_color = (1.0, 0.0, 0.0, 1.0)  # rosso
mat.roughness = 0.8
mat.metallic = 0.0

# Assegnare materiale a oggetto
obj = bpy.context.active_object
if obj.data.materials:
    obj.data.materials[0] = mat
else:
    obj.data.materials.append(mat)

# Accedere al Principal BSDF node
if mat.use_nodes:
    principled = mat.node_tree.nodes.get('Principled BSDF')
    if principled:
        principled.inputs['Base Color'].default_value = (0.2, 0.5, 0.8, 1.0)
        principled.inputs['Roughness'].default_value = 0.7

# Colori per identificare parti (stampa multi-materiale Bambu)
colors = [
    (0.8, 0.1, 0.1, 1.0),  # rosso — parte 1
    (0.1, 0.8, 0.1, 1.0),  # verde — parte 2
    (0.1, 0.1, 0.8, 1.0),  # blu — parte 3
]
for i, color in enumerate(colors):
    m = bpy.data.materials.new(f'Part_{i}')
    m.diffuse_color = color
    obj.data.materials.append(m)
```
