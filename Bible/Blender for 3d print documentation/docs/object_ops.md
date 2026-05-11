# Object & Transform Operators — Blender Python API

Operatori rilevanti per mesh editing e stampa 3D. Esclude animazione, rigging, constraints.

---

## Object Mode — Operatori chiave

### Selezione

#### bpy.ops.object.select_all
```python
bpy.ops.object.select_all(*, action='TOGGLE')
```
Cambia selezione di tutti gli oggetti visibili.
`action`: `'TOGGLE'` | `'SELECT'` | `'DESELECT'` | `'INVERT'`

```python
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_all(action='SELECT')
```

#### bpy.ops.object.select_by_type
```python
bpy.ops.object.select_by_type(*, extend=False, type='MESH')
```
Seleziona tutti gli oggetti visibili di un certo tipo.
`type`: `'MESH'` | `'CURVE'` | `'SURFACE'` | `'META'` | `'FONT'` | `'ARMATURE'` | `'LATTICE'` | `'EMPTY'` | `'GPENCIL'` | `'CAMERA'` | `'LIGHT'`

```python
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
```

### Gestione oggetti

#### bpy.ops.object.join
```python
bpy.ops.object.join()
```
Unisce gli oggetti selezionati nell'oggetto attivo. Tutti devono essere dello stesso tipo.

```python
# Pattern: seleziona, imposta attivo, join
bpy.ops.object.select_all(action='DESELECT')
for obj in objects_to_join:
    obj.select_set(True)
bpy.context.view_layer.objects.active = objects_to_join[0]
bpy.ops.object.join()
```

#### bpy.ops.object.delete
```python
bpy.ops.object.delete(*, use_global=False, confirm=True)
```
Elimina gli oggetti selezionati.
- `use_global=True`: rimuove da tutte le scene
- `confirm=False`: non chiede conferma (utile da script)

```python
bpy.ops.object.delete(use_global=False, confirm=False)
```

#### bpy.ops.object.duplicate
```python
bpy.ops.object.duplicate(*, linked=False, mode='TRANSLATION')
```
Duplica gli oggetti selezionati.
- `linked=True`: duplica l'oggetto ma non i dati (linked duplicate, condivide la mesh)
- `linked=False`: duplica tutto (deep copy)

#### bpy.ops.object.duplicate_move
```python
bpy.ops.object.duplicate_move(*, OBJECT_OT_duplicate={}, TRANSFORM_OT_translate={})
```
Duplica e sposta in un'unica operazione. Passa argomenti come dict.

```python
bpy.ops.object.duplicate_move(
    OBJECT_OT_duplicate={"linked": False},
    TRANSFORM_OT_translate={"value": (1, 0, 0)}
)
```

#### bpy.ops.object.make_single_user
```python
bpy.ops.object.make_single_user(*, type='SELECTED_OBJECTS',
                                  object=False, obdata=False,
                                  material=False, animation=False,
                                  obdata_animation=False)
```
Rende i dati linked locali a ogni oggetto.
- `type`: `'SELECTED_OBJECTS'` | `'ALL'`
- `object=True`: rende l'oggetto single-user
- `obdata=True`: rende la mesh/curva single-user (necessario prima di modifiche)

```python
# Prima di modificare una mesh linked
bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=True, obdata=True)
```

### Trasformazioni oggetto

#### bpy.ops.object.transform_apply
```python
bpy.ops.object.transform_apply(*, location=True, rotation=True, scale=True,
                                  properties=True, corrective_flip_normals=True,
                                  isolate_users=False)
```
Applica la trasformazione dell'oggetto ai suoi dati (azzera location/rotation/scale).
**Critico per stampa 3D**: applicare scala prima di export.

```python
# Applica solo scala (più comune per print)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Applica tutto
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
```

#### bpy.ops.object.origin_set
```python
bpy.ops.object.origin_set(*, type='GEOMETRY_ORIGIN', center='MEDIAN')
```
Imposta l'origine dell'oggetto.

| `type` | Descrizione |
|--------|-------------|
| `'GEOMETRY_ORIGIN'` | Sposta la geometria all'origine (muove i dati, non l'oggetto) |
| `'ORIGIN_GEOMETRY'` | Sposta l'origine al centro della geometria |
| `'ORIGIN_CURSOR'` | Sposta l'origine al cursore 3D |
| `'ORIGIN_CENTER_OF_MASS'` | Centro di massa (superficie) |
| `'ORIGIN_CENTER_OF_VOLUME'` | Centro di massa (volume, richiede mesh manifold) |

`center`: `'MEDIAN'` | `'BOUNDS'`

```python
# Centrar l'origine alla geometria
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

# Portare l'oggetto all'origine del mondo
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
bpy.context.active_object.location = (0, 0, 0)
```

**Pattern stampa 3D — base a Z=0 (piano di stampa):**
```python
# Porta l'origine al centro del bounding box, poi posiziona la base sul piano Z=0
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
obj = bpy.context.active_object
obj.location.z = obj.dimensions.z / 2  # centro geometria a Z=dim/2 → base a Z=0
```

### Conversione

#### bpy.ops.object.convert
```python
bpy.ops.object.convert(*, target='MESH', keep_original=False,
                         merge_customdata=True, thickness=5,
                         faces=True, offset=0.01)
```
Converte oggetti selezionati in un altro tipo.

| `target` | Descrizione |
|----------|-------------|
| `'MESH'` | Da Curve/Surface/Metaball/Text → Mesh |
| `'CURVE'` | Da Mesh/Text → Curve |
| `'POINTCLOUD'` | Da Mesh → Point Cloud |
| `'CURVES'` | Da Curve valutata → Curves |
| `'GREASEPENCIL'` | Da Curve/Mesh → Grease Pencil |

```python
# Convertire una curva in mesh (necessario per export STL)
bpy.ops.object.convert(target='MESH', keep_original=False)
```

### Modificatori

#### bpy.ops.object.modifier_add
```python
bpy.ops.object.modifier_add(*, type='SUBSURF', use_selected_objects=False)
```
Aggiunge un modificatore all'oggetto attivo.
`type` comuni per 3D printing: `'SOLIDIFY'` | `'REMESH'` | `'DECIMATE'` | `'BOOLEAN'` | `'SUBSURF'` | `'SMOOTH'` | `'WELD'` | `'MIRROR'`

```python
bpy.ops.object.modifier_add(type='SOLIDIFY')
# Poi configurare i parametri del modificatore:
obj = bpy.context.active_object
mod = obj.modifiers[-1]
mod.thickness = 0.002
mod.use_even_offset = True
```

#### bpy.ops.object.modifier_apply
```python
bpy.ops.object.modifier_apply(*, modifier='', report=False,
                                merge_customdata=True, single_user=False,
                                all_keyframes=False, use_selected_objects=False)
```
Applica e rimuove un modificatore dallo stack.
- `modifier`: nome del modificatore (stringa)
- `single_user=True`: rende i dati single-user se necessario

```python
obj = bpy.context.active_object
for mod in obj.modifiers:
    bpy.ops.object.modifier_apply(modifier=mod.name)
```

#### bpy.ops.object.modifier_remove
```python
bpy.ops.object.modifier_remove(*, modifier='', report=False,
                                 use_selected_objects=False)
```
Rimuove un modificatore senza applicarlo.

```python
obj = bpy.context.active_object
# Rimuovi tutti i modificatori
for mod in reversed(obj.modifiers):
    bpy.ops.object.modifier_remove(modifier=mod.name)
```

### Shading

#### bpy.ops.object.shade_smooth
```python
bpy.ops.object.shade_smooth(*, keep_sharp_edges=True)
```
Imposta smooth shading sulle facce (interpolazione normali). Non modifica la geometria.
`keep_sharp_edges=True`: mantiene gli spigoli marcati come sharp.

#### bpy.ops.object.shade_flat
```python
bpy.ops.object.shade_flat(*, keep_sharp_edges=True)
```
Imposta flat shading (normali per faccia).

### Data transfer

#### bpy.ops.object.data_transfer
```python
bpy.ops.object.data_transfer(*, use_reverse_transfer=False, use_freeze=False,
                               data_type='VGROUP_WEIGHTS', use_create=True,
                               vert_mapping='NEAREST', edge_mapping='NEAREST',
                               loop_mapping='NEAREST_POLYNOR', poly_mapping='NEAREST',
                               use_auto_transform=False, use_object_transform=True,
                               use_max_distance=False, max_distance=1.0,
                               ray_radius=0.0, islands_precision=0.1,
                               layers_select_src='ACTIVE', layers_select_dst='ACTIVE',
                               mix_mode='REPLACE', mix_factor=1.0)
```
Trasferisce layer dati (pesi, sharp edges, UV, normali custom, ecc.) dall'oggetto attivo ai selezionati.

`data_type` rilevanti: `'SHARP_EDGE'` | `'CUSTOM_NORMAL'` | `'UV'` | `'VGROUP_WEIGHTS'` | `'SMOOTH'`
`mix_mode`: `'REPLACE'` | `'ABOVE_THRESHOLD'` | `'BELOW_THRESHOLD'` | `'MIX'` | `'ADD'` | `'SUB'`

---

## Transform Operators

Operatori nel modulo `bpy.ops.transform`. Agiscono sugli elementi selezionati nella viewport.

### bpy.ops.transform.translate
```python
bpy.ops.transform.translate(*, value=(0.0, 0.0, 0.0),
                              orient_type='GLOBAL',
                              constraint_axis=(False, False, False),
                              mirror=False,
                              use_proportional_edit=False,
                              snap=False, ...)
```
Sposta gli elementi selezionati.
- `value`: vettore spostamento (x, y, z)
- `constraint_axis`: blocca assi, es. `(True, False, False)` = solo X
- `orient_type`: `'GLOBAL'` | `'LOCAL'` | `'NORMAL'` | `'CURSOR'` | `'VIEW'`

```python
# Sposta di 10mm sull'asse Z
bpy.ops.transform.translate(value=(0, 0, 0.01),
                              constraint_axis=(False, False, True))
```

### bpy.ops.transform.resize
```python
bpy.ops.transform.resize(*, value=(1.0, 1.0, 1.0),
                           orient_type='GLOBAL',
                           constraint_axis=(False, False, False),
                           mirror=False, ...)
```
Scala (ridimensiona) gli elementi selezionati.
- `value`: fattore di scala per asse

```python
# Scala uniformemente 2x
bpy.ops.transform.resize(value=(2, 2, 2))

# Scala solo sull'asse Z
bpy.ops.transform.resize(value=(1, 1, 0.5),
                           constraint_axis=(False, False, True))
```

### bpy.ops.transform.rotate
```python
bpy.ops.transform.rotate(*, value=0.0,
                           orient_axis='Z',
                           orient_type='GLOBAL',
                           constraint_axis=(False, False, False),
                           mirror=False, ...)
```
Ruota gli elementi selezionati.
- `value`: angolo in radianti
- `orient_axis`: `'X'` | `'Y'` | `'Z'`

```python
import math
bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Z')
```

### bpy.ops.transform.transform
```python
bpy.ops.transform.transform(*, mode='TRANSLATION',
                              value=(0.0, 0.0, 0.0, 0.0),
                              orient_axis='Z',
                              orient_type='GLOBAL',
                              constraint_axis=(False, False, False), ...)
```
Trasformazione generica per tipo. `mode`: `'TRANSLATION'` | `'ROTATION'` | `'RESIZE'` | `'SKIN_RESIZE'` | `'TOSPHERE'` | `'SHEAR'` | `'BEND'` | `'SHRINKFATTEN'` | `'TILT'` | `'TRACKBALL'` | `'PUSHPULL'` | `'ALIGN'`

### bpy.ops.transform.shrink_fatten
```python
bpy.ops.transform.shrink_fatten(*, value=0.0, use_even_offset=False,
                                   mirror=False,
                                   use_proportional_edit=False, ...)
```
Sposta i vertici selezionati lungo le loro normali (inflate/deflate).
- `value > 0`: fatten (gonfia), `value < 0`: shrink (stringi)
- `use_even_offset=True`: offset uniforme per spessore omogeneo

```python
# Utile per aggiungere spessore a mesh sottili
bpy.ops.transform.shrink_fatten(value=0.001, use_even_offset=True)
```

### bpy.ops.transform.push_pull
```python
bpy.ops.transform.push_pull(*, value=0.0, mirror=False,
                              use_proportional_edit=False, ...)
```
Sposta gli elementi verso o lontano dal centro.
- `value > 0`: pull (allontana dal centro)
- `value < 0`: push (avvicina al centro)

### bpy.ops.transform.edge_slide
```python
bpy.ops.transform.edge_slide(*, value=0.0, single_side=False,
                               use_even=False, flipped=False,
                               use_clamp=True, correct_uv=True, ...)
```
Scivola un edge loop lungo la mesh.
- `value`: fattore [-10, 10], normalmente [-1, 1]
- `use_even=True`: mantiene la forma del loop adiacente
- `use_clamp=True`: limita all'estensione degli spigoli

### bpy.ops.transform.vert_slide
```python
bpy.ops.transform.vert_slide(*, value=0.0, use_even=False,
                               flipped=False, use_clamp=True,
                               direction=(0.0, 0.0, 0.0), ...)
```
Scivola un singolo vertice lungo uno spigolo connesso.

### bpy.ops.transform.vertex_random
```python
bpy.ops.transform.vertex_random(*, offset=0.0, uniform=0.0,
                                   normal=0.0, seed=0, wait_for_input=True)
```
Randomizza la posizione dei vertici.
- `offset`: distanza massima
- `uniform=1.0`: distribuzione uniforme (0 = non uniforme)
- `normal`: allineamento offset alle normali [0-1]
- `seed`: seed per il generatore random

---

## Sculpt Operators

### bpy.ops.sculpt.sculptmode_toggle
```python
bpy.ops.sculpt.sculptmode_toggle()
```
Entra/esce dalla modalità sculpt nella 3D view.

### bpy.ops.sculpt.dynamic_topology_toggle
```python
bpy.ops.sculpt.dynamic_topology_toggle()
```
Attiva/disattiva il dynamic topology (Dyntopo). Rimagli la mesh dinamicamente durante la scultura. Utile per aggiungere dettaglio localizzato.

**Nota**: Dyntopo rimuove custom data (UV, vertex colors). Da usare su copie o prima di UV unwrapping.

### bpy.ops.sculpt.brush_stroke
```python
bpy.ops.sculpt.brush_stroke(*, stroke=None, mode='NORMAL',
                              brush_toggle='None', pen_flip=False, ...)
```
Non utile da script: richiede dati stroke interattivi. Usare invece bmesh.ops per modifiche procedurali.

---

## Pattern pratici per stampa 3D

### Workflow completo: object → print-ready

```python
import bpy, math

def prepare_for_print(obj):
    """Prepara un oggetto per l'export STL/3MF."""
    # Assicurati che sia l'oggetto attivo
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # 1. Rendi la mesh single-user (se linked)
    bpy.ops.object.make_single_user(
        type='SELECTED_OBJECTS',
        object=True, obdata=True
    )

    # 2. Applica tutti i modificatori
    for mod in reversed(obj.modifiers[:]):
        bpy.ops.object.modifier_apply(modifier=mod.name)

    # 3. Applica la scala (CRITICO per dimensioni corrette)
    bpy.ops.object.transform_apply(
        location=False, rotation=True, scale=True
    )

    # 4. Centra l'origine alla geometria
    bpy.ops.object.origin_set(
        type='ORIGIN_GEOMETRY', center='BOUNDS'
    )

prepare_for_print(bpy.context.active_object)
```

### Aggiungere solidify per pareti sottili

```python
import bpy

obj = bpy.context.active_object
bpy.context.view_layer.objects.active = obj

# Aggiungi modificatore Solidify
bpy.ops.object.modifier_add(type='SOLIDIFY')
mod = obj.modifiers[-1]
mod.thickness = 0.002          # 2mm
mod.use_even_offset = True     # spessore uniforme
mod.use_quality_normals = True # normali di qualità

# Applica
bpy.ops.object.modifier_apply(modifier=mod.name)
```

### Convertire curve in mesh

```python
import bpy

# Seleziona tutte le curve
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='CURVE')

if bpy.context.selected_objects:
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.convert(target='MESH', keep_original=False)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
```

### Join multipli oggetti mesh

```python
import bpy

# Seleziona solo le mesh nella scena
bpy.ops.object.select_all(action='DESELECT')
mesh_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']

if mesh_objects:
    for obj in mesh_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0]
    bpy.ops.object.join()
    # Applica trasformazioni al risultato
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
```

### Scala uniforme a dimensione target

```python
import bpy

obj = bpy.context.active_object
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

# Applica scala corrente
bpy.ops.object.transform_apply(scale=True)

# Calcola bounding box e scala a target_height mm
target_height = 0.100  # 100mm in metri
bbox = obj.bound_box
height = max(v[2] for v in bbox) - min(v[2] for v in bbox)
if height > 0:
    factor = target_height / height
    bpy.ops.transform.resize(value=(factor, factor, factor))
    bpy.ops.object.transform_apply(scale=True)
```

**Bounding box in world space** (considera scala e rotazione dell'oggetto):
```python
# bound_box è in local space; @ matrix_world converte in world space
obj = bpy.context.active_object
world_corners = [obj.matrix_world @ v for v in obj.bound_box]
# world_corners è una lista di 8 Vector in coordinate mondo
min_z = min(v[2] for v in world_corners)
max_z = max(v[2] for v in world_corners)
height_world = max_z - min_z
```
