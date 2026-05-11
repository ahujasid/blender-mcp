# Gestione Oggetti Multipli — Scena, Import, Separazione, Unione

## Contesto

Mesh da generatori AI e fotogrammetria spesso arrivano come strutture multi-body: più oggetti nella stessa scena, o un singolo oggetto che contiene geometrie disconnesse (isole separate). Per la stampa FDM su Bambu A1 l'obiettivo tipico è arrivare a un singolo mesh watertight per ogni pezzo da stampare.

---

## Inventario scena — cosa c'è nella scena dopo import

```python
import bpy

# Lista tutti gli oggetti mesh con dimensioni e conteggio poligoni
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH':
        continue
    mesh = obj.data
    dims = obj.dimensions
    scene = bpy.context.scene
    sl = scene.unit_settings.scale_length or 0.001
    print(
        f"{obj.name:30s} "
        f"verts:{len(mesh.vertices):6d} "
        f"polys:{len(mesh.polygons):6d} "
        f"dims:{dims.x/sl:.1f}×{dims.y/sl:.1f}×{dims.z/sl:.1f}mm"
    )
```

## Rilevare isole disconnesse in un singolo oggetto

Un mesh può sembrare un oggetto unico ma contenere geometrie separate (isole). Questo è comune nei mesh AI fotogrammetrici (rumore di sfondo che diventa floating geometry).

```python
import bpy, bmesh

def count_islands(obj):
    """Conta le isole di geometria connessa nel mesh."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    visited = set()
    islands = 0

    for start_vert in bm.verts:
        if start_vert.index in visited:
            continue
        islands += 1
        # BFS per marcare tutti i vertici connessi
        queue = [start_vert]
        while queue:
            v = queue.pop()
            if v.index in visited:
                continue
            visited.add(v.index)
            for edge in v.link_edges:
                other = edge.other_vert(v)
                if other.index not in visited:
                    queue.append(other)

    bm.free()
    return islands

n = count_islands(bpy.context.active_object)
print(f"Isole di geometria: {n}")
```

**Soglie pratiche:**
- 1 isola → mesh connesso (normale)
- 2–5 isole → probabile struttura multi-part intenzionale o rumore
- > 10 isole → alta probabilità di floating artifacts da fotogrammetria

---

## Separare in oggetti distinti

### Per isole di geometria (floating geometry)
```python
import bpy

obj = bpy.context.active_object
bpy.context.view_layer.objects.active = obj

# Separate by Loose Parts: ogni isola disconnessa diventa un oggetto separato
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.mesh.separate(type='LOOSE')
# Ora nella scena ci sono N oggetti, uno per isola
```

### Per materiali (se il mesh ha material_index variabili)
```python
bpy.ops.mesh.separate(type='MATERIAL')
```

### Per selezione manuale
```python
# In Edit Mode: seleziona le facce che vuoi separare, poi:
bpy.ops.mesh.separate(type='SELECTED')
```

---

## Filtrare e rimuovere isole piccole (rumore)

Dopo `separate(type='LOOSE')`, ogni isola è un oggetto separato. Eliminare quelle sotto una soglia dimensionale:

```python
import bpy

def remove_small_objects(min_volume_mm3=1.0, min_dim_mm=2.0):
    """
    Rimuove oggetti mesh la cui dimensione massima è inferiore a min_dim_mm
    o il cui bounding box volume è inferiore a min_volume_mm3.
    Utile dopo separate(LOOSE) per pulire floating artifacts.
    """
    scene = bpy.context.scene
    sl = scene.unit_settings.scale_length or 0.001

    to_remove = []
    for obj in list(scene.objects):
        if obj.type != 'MESH':
            continue
        dims = obj.dimensions
        dims_mm = [d / sl for d in dims]
        max_dim = max(dims_mm)
        vol = dims_mm[0] * dims_mm[1] * dims_mm[2]

        if max_dim < min_dim_mm or vol < min_volume_mm3:
            to_remove.append(obj)

    for obj in to_remove:
        bpy.data.objects.remove(obj, do_unlink=True)

    print(f"Rimossi {len(to_remove)} oggetti piccoli")
    return len(to_remove)

remove_small_objects(min_dim_mm=5.0)  # rimuovi tutto < 5mm su qualsiasi asse
```

---

## Unire oggetti in un singolo mesh

### Join (ctrl+J) — unisce senza risolvere intersezioni

```python
import bpy

# Seleziona tutti i mesh objects da unire
bpy.ops.object.select_all(action='DESELECT')
mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

for obj in mesh_objects:
    obj.select_set(True)

# Rendi attivo il primo (diventerà il "container")
bpy.context.view_layer.objects.active = mesh_objects[0]
bpy.ops.object.join()
```

**Attenzione**: `join()` crea un multi-body mesh — le geometrie originali restano come isole separate all'interno dello stesso oggetto. Non risolve intersezioni né crea un mesh watertight unificato.

### Boolean UNION — unisce risolvendo le intersezioni

Per avere un singolo mesh watertight da oggetti che si sovrappongono o si toccano:

```python
import bpy

def boolean_union_all(objects):
    """
    Applica Boolean UNION iterativo su una lista di oggetti.
    Ritorna l'oggetto risultante (gli altri vengono rimossi).
    """
    if not objects:
        return None

    base = objects[0]
    bpy.context.view_layer.objects.active = base

    for i in range(1, len(objects)):
        cutter = objects[i]
        mod = base.modifiers.new(name=f"BoolUnion_{i}", type='BOOLEAN')
        mod.operation = 'UNION'
        mod.object = cutter
        mod.solver = 'EXACT'
        bpy.ops.object.modifier_apply(modifier=f"BoolUnion_{i}")
        bpy.data.objects.remove(cutter, do_unlink=True)

    return base

mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
result = boolean_union_all(mesh_objects)
```

**Quando usare join vs Boolean UNION:**
- `join()`: oggetti che non si intersecano e non devono fondersi → più veloce, topologia intatta
- `Boolean UNION`: oggetti che si sovrappongono o devono essere un solido unico → lento ma corretto per slicer

---

## Gestire la scena dopo import STL

Un tipico import STL porta un solo oggetto. Ma se il file STL contiene geometrie disconnesse (comune in fotogrammetria), può essere utile separare, analizzare, e tenere solo la parte principale:

```python
import bpy

def clean_import(keep_largest=True):
    """
    Dopo import STL: separa isole, rimuove piccoli artefatti,
    e opzionalmente torna al mesh principale (il più grande).
    """
    # Assume un solo oggetto appena importato
    imported = bpy.context.active_object
    if not imported or imported.type != 'MESH':
        return

    # Separa isole
    bpy.ops.mesh.separate(type='LOOSE')

    # Raccoglie tutti i mesh objects creati
    all_mesh = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

    if len(all_mesh) <= 1:
        return  # un solo mesh, niente da fare

    if keep_largest:
        # Tieni solo il più grande per volume di bounding box
        def bbox_volume(obj):
            d = obj.dimensions
            return d.x * d.y * d.z

        largest = max(all_mesh, key=bbox_volume)
        for obj in all_mesh:
            if obj != largest:
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.context.view_layer.objects.active = largest
        largest.select_set(True)
        print(f"Mantenuto: {largest.name} (rimosse {len(all_mesh)-1} isole minori)")

clean_import(keep_largest=True)
```

---

## Proprietà di Object rilevanti per gestione multi-oggetto

| Proprietà/Metodo | Tipo | Descrizione |
|-----------------|------|-------------|
| `obj.type` | str | `'MESH'`, `'CURVE'`, `'EMPTY'`, ecc. Filtrare per `'MESH'` |
| `obj.name` | str | Nome univoco nella scena |
| `obj.dimensions` | Vector | Dimensioni bounding box world-space |
| `obj.hide_viewport` | bool | Oggetto visibile nel viewport |
| `obj.select_set(True/False)` | method | Seleziona/deseleziona |
| `obj.select_get()` | method → bool | Stato selezione |
| `bpy.data.objects.remove(obj, do_unlink=True)` | method | Elimina definitivamente |
| `bpy.context.view_layer.objects.active = obj` | assign | Rende oggetto attivo |
| `bpy.context.selected_objects` | list | Oggetti attualmente selezionati |
| `bpy.context.scene.objects` | collection | Tutti gli oggetti nella scena |
