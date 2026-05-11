# Scale Detection — Verificare e Correggere la Scala di un Mesh Importato

## Il problema

STL non contiene metadata sulle unità. Un file STL è solo una lista di coordinate numeriche — il significato di quei numeri (mm, pollici, unità arbitrarie) dipende dal tool che lo ha esportato. Blender importa i numeri così come sono, interpretandoli come Blender Units (BU).

Con scena impostata a mm (`scale_length=0.001`):
- Un oggetto con vertici a coordinate 50/30/20 → `obj.dimensions` = (0.05, 0.03, 0.02) BU → display come 50×30×20mm ✓
- Un oggetto con vertici a coordinate 0.05/0.03/0.02 → `obj.dimensions` = (0.00005, ...) → display come 0.05mm ✗ (scala di 1000× troppo piccola)
- Un oggetto con vertici a coordinate 50000/30000/20000 → display come 50000mm ✗ (scala di 1000× troppo grande)

## Origine delle scale sbagliate

| Origine | Scala tipica vertici | Dimensioni display (con scale_length=0.001) | Interpretazione |
|---------|---------------------|---------------------------------------------|-----------------|
| Slicer (Bambu Studio, PrusaSlicer) | mm | corrette | OK |
| Tool di modellazione mm (Fusion360, SolidWorks) | mm | corrette | OK |
| Tool con unità metres | 0.001×dim_mm | es. 0.08m per 80mm → display 0.08mm | 1000× troppo piccolo |
| AI generators normalizzati (0–1 range) | 0.0–1.0 | max ~1mm | scala arbitraria |
| AI generators (unità proprie) | variabile | variabile | dipende dal tool |
| Fotogrammetria con GPS (coordinate reali) | metri reali | migliaia mm | 1000× troppo grande |
| Fotogrammetria senza riferimento | arbitrario | arbitrario | richiede riferimento esterno |

## Come rilevare la scala

```python
import bpy

obj = bpy.context.active_object
scene = bpy.context.scene

# Assicurarsi che la scena sia in mm
scale_length = scene.unit_settings.scale_length  # dovrebbe essere 0.001
dims = obj.dimensions  # in BU

# Conversione in mm (quando scale_length=0.001: 1 BU = 1mm nel display)
# obj.dimensions restituisce le dimensioni world già moltiplicate per la scala oggetto
# Con scale_length=0.001, dims * 1 = mm displayed
max_dim_mm = max(dims) / scale_length if scale_length > 0 else max(dims) * 1000

print(f"Dimensioni: {dims.x/scale_length:.2f} × {dims.y/scale_length:.2f} × {dims.z/scale_length:.2f} mm")
print(f"Dimensione massima: {max_dim_mm:.2f} mm")
```

## Soglie euristiche di diagnosi

```python
def diagnose_scale(obj, expected_range_mm=(5, 256)):
    """
    Stima se la scala di un oggetto importato è plausibile per stampa 3D su A1.
    Ritorna: ('ok'|'too_small'|'too_large'|'suspicious'), factor_suggerito
    """
    scene = bpy.context.scene
    sl = scene.unit_settings.scale_length or 0.001
    dims = obj.dimensions
    max_dim_mm = max(dims) / sl

    if max_dim_mm < 0.1:
        # Probabilmente in metri o unità normalizzate (0–1)
        # Suggerisci scaling a una dimensione di default (es. 100mm)
        return 'too_small', 100.0 / max_dim_mm

    elif max_dim_mm < expected_range_mm[0]:
        # Oggetto molto piccolo — potrebbe essere intenzionale o errore di scala
        return 'suspicious', expected_range_mm[0] / max_dim_mm

    elif max_dim_mm > 1000:
        # Probabilmente in millimetri interpretati come metres (x1000 troppo grande)
        return 'too_large', expected_range_mm[1] / max_dim_mm

    elif max_dim_mm > expected_range_mm[1]:
        # Supera il volume di stampa A1 (256mm)
        return 'too_large', expected_range_mm[1] / max_dim_mm

    else:
        return 'ok', 1.0
```

## Correggere la scala

Una volta identificato il fattore correttivo, la procedura è identica indipendentemente dalla causa:

```python
import bpy

def rescale_to_target_mm(obj, target_max_mm):
    """
    Scala obj proporzionalmente in modo che la sua dimensione massima
    sia uguale a target_max_mm.
    Applica la trasformazione (bake nei vertici).
    """
    scene = bpy.context.scene
    sl = scene.unit_settings.scale_length or 0.001

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    # Centra l'origine prima di scalare
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    current_max_dim = max(obj.dimensions)
    target_bu = target_max_mm * sl
    factor = target_bu / current_max_dim

    obj.scale = (obj.scale.x * factor,
                 obj.scale.y * factor,
                 obj.scale.z * factor)

    # Bake della scala nei vertici (necessario per export STL corretto)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
```

**Invariante critica**: `transform_apply(scale=True)` deve sempre essere chiamato dopo una modifica di scala prima dell'export STL. Un oggetto con scala (0.001, 0.001, 0.001) e vertici a 1000mm NON è equivalente a un oggetto con scala (1,1,1) e vertici a 1mm dal punto di vista dell'export.

## Stima scala da contesto semantico

Se conosci la dimensione reale attesa dell'oggetto (es. "questo è un portachiavi, circa 60mm"), la scala si calcola direttamente:

```python
# Oggetto atteso ~60mm nel punto più lungo
target_mm = 60.0
rescale_to_target_mm(bpy.context.active_object, target_mm)
```

Se non conosci la dimensione, la soglia pratica per la stampa FDM A1:
- **Oggetti piccoli** (gioielli, accessori): 10–50mm
- **Oggetti medi** (contenitori, parti meccaniche): 50–150mm
- **Oggetti grandi**: 150–256mm (limite A1)

## Verifica dopo correzione

```python
import bpy

obj = bpy.context.active_object
scene = bpy.context.scene
sl = scene.unit_settings.scale_length or 0.001

dims_mm = [d / sl for d in obj.dimensions]
print(f"Post-scala: {dims_mm[0]:.1f} × {dims_mm[1]:.1f} × {dims_mm[2]:.1f} mm")

fits_a1 = all(d <= 256 for d in dims_mm)
print(f"Entra nel volume A1 (256³mm): {fits_a1}")
```

## Note STL-specifiche

- `use_scene_unit=True` all'import applica `scale_length` inverso ai vertici importati. Se la scena è già in mm (`scale_length=0.001`) e il file STL è in mm, usare `use_scene_unit=False, global_scale=1.0` è più prevedibile.
- `global_scale` all'import moltiplica tutte le coordinate al momento dell'import. `global_scale=0.001` converte un STL in metres a BU corretti per scena mm.
- Dopo import, verificare sempre `obj.scale` — deve essere (1.0, 1.0, 1.0) per confermare che non ci siano scale non applicate.
