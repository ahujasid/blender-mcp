# Blender MCP — Tool Reference

## Tool disponibili (blender-mcp v1.5.5)

### `execute_blender_code(code: str) -> str`
**Il tool principale.** Esegue codice Python arbitrario in Blender.
- Spezza operazioni complesse in chiamate separate (max affidabilità)
- Restituisce stdout/stderr come stringa
- Il codice gira nel contesto Blender con accesso completo a `bpy`, `bmesh`, `mathutils`

```python
# Pattern base
import bpy
obj = bpy.context.active_object
print(obj.name, obj.dimensions)
```

### `get_scene_info() -> str`
Restituisce JSON con info sulla scena: oggetti, materiali, luci, camera.
- Usare per capire cosa c'è in scena prima di operare
- Restituisce: nome oggetti, tipo (MESH/LIGHT/CAMERA), location, scale, dimensioni

### `get_object_info(object_name: str) -> str`
Dettagli su un oggetto specifico: vertex count, face count, materiali, bounding box, modifiers.

### `get_viewport_screenshot(max_size: int = 800) -> Image`
Screenshot del viewport 3D. Utile per verificare lo stato visivo della scena.

---

---

## ⚠ REGOLE OPERATIVE MCP — OBBLIGATORIE

Queste regole derivano da test diretti in ambiente MCP stateless (Blender 5.1). Violarle causa corruzione delle mesh o perdita di lavoro.

### 1. `bpy.ops.ed.undo()` è VIETATO negli script

In ambiente MCP stateless l'undo stack non è controllabile. `undo()` può annullare operazioni di sessioni precedenti o un numero arbitrario di step. **Non usarlo mai.**

Pattern corretto per operazioni reversibili:
```python
# ✗ SBAGLIATO — undo imprevedibile
bpy.ops.mesh.bisect(...)
# ... verifica ...
bpy.ops.ed.undo()

# ✓ CORRETTO — duplica, opera sul duplicato, elimina se non serve
import bpy
bpy.ops.object.select_all(action='DESELECT')
orig = bpy.data.objects['NomeOriginale']
orig.select_set(True)
bpy.context.view_layer.objects.active = orig
bpy.ops.object.duplicate()
temp = bpy.context.active_object
temp.name = "TEMP_verifica"
# ... opera su temp ...
# se OK: continua con orig
# se KO: bpy.data.objects.remove(temp, do_unlink=True) — niente undo
```

### 2. Operazioni distruttive richiedono approvazione esplicita

Operazioni distruttive = bisect, boolean, delete, solidify apply, decimate apply, qualsiasi modifier apply.

**Protocollo obbligatorio:**
1. Descrivere l'operazione e il suo effetto alla mesh
2. Attendere conferma esplicita dell'utente
3. Solo allora eseguire

Non agire autonomamente anche se l'operazione sembra ovvia o necessaria.

### 3. Verifiche visive NON devono modificare la mesh originale

Per cross-section, ispezioni interne, check geometrici visivi:
```python
# ✓ Duplica → opera sul duplicato → screenshot → elimina
bpy.ops.object.duplicate()
temp = bpy.context.active_object
bpy.ops.mesh.bisect(plane_co=(0,0,0), plane_no=(0,0,1), clear_inner=True)
# screenshot
bpy.data.objects.remove(temp, do_unlink=True)
# originale intatto
```

### 4. Screenshot: posizionare la camera prima di ogni call con viewport

```python
import bpy

# Seleziona oggetto di interesse, poi framing corretto
bpy.ops.object.select_all(action='DESELECT')
obj = bpy.data.objects['NomeOggetto']
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

# Cerca area 3D e imposta vista
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        with bpy.context.temp_override(area=area):
            bpy.ops.view3d.view_selected()       # zoom sull'oggetto
            bpy.ops.view3d.view_axis(type='FRONT')  # vista frontale
        break
```

### 5. Algoritmi di verifica: solo da KB o da metriche certe

Metriche affidabili: `len(mesh.vertices)`, `len(mesh.polygons)`, `bm.calc_volume()`, conteggio open edges via bmesh.
Non inventare euristiche non documentate (es. "range radiale", "distanza media dal centro") — danno falsi positivi su mesh complesse.

### 6. Stateless: ogni CALL deve essere autonoma

Nessuna variabile persiste tra le call. Tutto il passaggio di stato avviene tramite `print()` nell'output della call precedente. Se servono dati da una call precedente, rileggerli da scena (`bpy.data.objects`, `obj.dimensions`, ecc.) all'inizio della call successiva.

---

## Tool NON rilevanti per stampa 3D
- `get_polyhaven_*` — asset ambientali (HDRI, texture, modelli decorativi)
- `generate_hyper3d_*` / `generate_hunyuan3d_*` — generazione AI modelli
- `search_sketchfab_*` / `download_sketchfab_*` — download modelli esterni
- `asset_creation_strategy` — strategia per scene creative

---

## Pattern di utilizzo `execute_blender_code`

### Selezione oggetto per nome
```python
import bpy
bpy.ops.object.select_all(action='DESELECT')
obj = bpy.data.objects['NomeOggetto']
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
```

### Cambiare modalità
```python
import bpy
bpy.ops.object.mode_set(mode='EDIT')    # entra in Edit Mode
bpy.ops.object.mode_set(mode='OBJECT')  # torna in Object Mode
# Modi: 'OBJECT', 'EDIT', 'SCULPT', 'VERTEX_PAINT', 'WEIGHT_PAINT'
```

### Selezionare tutto in Edit Mode
```python
import bpy
bpy.ops.mesh.select_all(action='SELECT')   # seleziona tutto
bpy.ops.mesh.select_all(action='DESELECT') # deseleziona tutto
```

### Accedere ai dati mesh
```python
import bpy
obj = bpy.context.active_object
mesh = obj.data  # bpy.types.Mesh
print(f"Vertices: {len(mesh.vertices)}, Faces: {len(mesh.polygons)}")
print(f"Dimensions: {obj.dimensions}")  # Vector (x, y, z) in Blender units
```
