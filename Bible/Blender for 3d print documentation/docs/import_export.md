# Blender Import/Export — Riferimento 3D Printing

Operatori per import/export STL (unico formato usato per stampa FDM su Bambu A1).

---

## STL Export

### `bpy.ops.wm.stl_export(*, filepath='', check_existing=True, ascii_format=False, use_batch=False, export_selected_objects=False, collection='', global_scale=1.0, use_scene_unit=False, forward_axis='Y', up_axis='Z', apply_modifiers=True, filter_glob='*.stl')`

Salva la scena in un file STL.

| Parametro | Tipo | Default | Note |
|---|---|---|---|
| `filepath` | `str` | `''` | Path al file di output |
| `check_existing` | `bool` | `True` | Avvisa prima di sovrascrivere |
| `ascii_format` | `bool` | `False` | `True` = ASCII STL; `False` = Binary STL |
| `use_batch` | `bool` | `False` | Esporta ogni oggetto in un file separato |
| `export_selected_objects` | `bool` | `False` | Esporta solo gli oggetti selezionati |
| `collection` | `str` | `''` | Esporta solo oggetti dalla collection specificata |
| `global_scale` | `float` [1e-06–1e+06] | `1.0` | Scala globale applicata all'export |
| `use_scene_unit` | `bool` | `False` | Applica la unit scale della scena ai dati esportati |
| `forward_axis` | `Literal['X','Y','Z','NEGATIVE_X','NEGATIVE_Y','NEGATIVE_Z']` | `'Y'` | Asse Forward |
| `up_axis` | `Literal['X','Y','Z','NEGATIVE_X','NEGATIVE_Y','NEGATIVE_Z']` | `'Z'` | Asse Up |
| `apply_modifiers` | `bool` | `True` | Applica i modifier alle mesh esportate |

**Esempio pratico:**
```python
bpy.ops.wm.stl_export(
    filepath='/path/to/model.stl',
    export_selected_objects=True,
    ascii_format=False,        # binary: più compatto e veloce
    use_scene_unit=False,      # NON usare con scale_length=0.001 (vedi nota sotto)
    apply_modifiers=True,
    forward_axis='Y',
    up_axis='Z',
    global_scale=1000.0        # BU → mm: 0.25 BU * 1000 = 250mm
)
```

---

## STL Import

### `bpy.ops.wm.stl_import(*, filepath='', directory='', files=None, check_existing=False, global_scale=1.0, use_scene_unit=False, use_facet_normal=False, forward_axis='Y', up_axis='Z', use_mesh_validate=True, filter_glob='*.stl')`

Importa un file STL come oggetto.

| Parametro | Tipo | Default | Note |
|---|---|---|---|
| `filepath` | `str` | `''` | Path al file STL |
| `directory` | `str` | `''` | Directory del file |
| `files` | `bpy_prop_collection` | `None` | Lista file per import multiplo |
| `global_scale` | `float` [1e-06–1e+06] | `1.0` | Scala globale applicata all'import |
| `use_scene_unit` | `bool` | `False` | Applica la unit scale della scena ai dati importati |
| `use_facet_normal` | `bool` | `False` | Usa le facet normals del file (dà shading flat) |
| `forward_axis` | `Literal['X','Y','Z','NEGATIVE_X','NEGATIVE_Y','NEGATIVE_Z']` | `'Y'` | Asse Forward |
| `up_axis` | `Literal['X','Y','Z','NEGATIVE_X','NEGATIVE_Y','NEGATIVE_Z']` | `'Z'` | Asse Up |
| `use_mesh_validate` | `bool` | `True` | Valida la mesh all'import (disabilitare può causare crash) |

**Esempio pratico:**
```python
bpy.ops.wm.stl_import(
    filepath='/path/to/model.stl',
    global_scale=1.0,
    use_scene_unit=True,
    use_mesh_validate=True,
    forward_axis='Y',
    up_axis='Z'
)
```

---

---

## 3MF Export

### Cos'è il 3MF e perché usarlo

3MF (3D Manufacturing Format) è lo standard moderno pensato appositamente per la stampa 3D, mantenuto dal 3MF Consortium (Microsoft, Autodesk, Ultimaker, Bambu Lab, ecc.). Rispetto a STL risolve diversi problemi strutturali.

| Caratteristica | STL | 3MF |
|---|---|---|
| Unità di misura | **Non specificate** (implicite) | **mm espliciti nel file** |
| Più oggetti in un file | No (1 mesh per file) | Sì — modello multi-parte in un file |
| Informazioni colore/materiale | No | Sì (colore per faccia/oggetto) |
| Metadati (autore, stampante) | No | Sì |
| Formato | Binario o ASCII | ZIP con XML interno |
| Dimensione file | Medio | Più compatto del ASCII STL |
| Supporto slicer | Universale | Tutti i moderni (Bambu Studio, PrusaSlicer, Cura) |

**Quando preferire 3MF a STL:**
- Hai più oggetti separati da mandare come un unico file (es. pezzi di un assembly)
- Vuoi evitare ambiguità di scala (3MF specifica sempre mm)
- Stai lavorando con modelli multi-colore o multi-materiale
- Vuoi preservare nomi degli oggetti nello slicer

**Quando STL è ancora sufficiente:**
- Singolo oggetto, workflow semplice
- Pipeline già consolidata con STL
- Compatibilità massima con tool legacy

---

### Export 3MF da Blender — io_mesh_3mf addon

In Blender 4.x/5.x, il supporto 3MF è fornito dall'addon **io_mesh_3mf**, che in Blender 5.1 è incluso come addon built-in (non richiede installazione separata).

```python
import bpy
import addon_utils

# Verifica e abilita l'addon io_mesh_3mf se non è già attivo
def ensure_3mf_addon():
    addon_name = "io_mesh_3mf"
    loaded, enabled = addon_utils.check(addon_name)
    if not enabled:
        addon_utils.enable(addon_name, default_set=True)
        print(f"Addon '{addon_name}' abilitato")
    else:
        print(f"Addon '{addon_name}' già attivo")

ensure_3mf_addon()
```

**Firma dell'operatore:**

```python
bpy.ops.export_mesh.threemf(
    filepath="",                    # OBBLIGATORIO: path al file .3mf
    check_existing=True,
    filter_glob="*.3mf",
    
    # === GEOMETRIA ===
    use_selection=False,            # True = solo oggetti selezionati
    use_mesh_modifiers=True,        # applica modifier prima dell'export
    
    # === SCALA ===
    # 3MF specifica sempre mm internamente
    # Con scale_length=0.001 (1 BU = 1mm): global_scale=1000 come per STL
    global_scale=1000.0,            # BU → mm (con scale_length=0.001)
)
```

**Esempio pratico — export 3MF corretto:**

```python
import bpy

bpy.ops.export_mesh.threemf(
    filepath='/path/to/output.3mf',
    use_selection=True,         # esporta solo gli oggetti selezionati
    use_mesh_modifiers=True,    # bake modifier come Solidify, Boolean
    global_scale=1000.0,        # CRITICO: BU → mm con scale_length=0.001
)
```

**Export multi-oggetto (assembly):**

```python
import bpy

# Seleziona tutti gli oggetti MESH della scena
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

# Export tutti in un unico file 3MF
bpy.ops.export_mesh.threemf(
    filepath='/path/to/assembly.3mf',
    use_selection=True,
    use_mesh_modifiers=True,
    global_scale=1000.0,
)
print(f"Esportati {len(bpy.context.selected_objects)} oggetti in assembly.3mf")
```

---

### Nota: Bambu 3MF vs Standard 3MF

Bambu Studio usa il formato `.3mf` in due modi distinti:

| Tipo | Contenuto | Generato da |
|---|---|---|
| **Bambu Project File** (`.3mf`) | Modello + impostazioni slicer + profili | Bambu Studio "Save Project" |
| **Standard 3MF** (`.3mf`) | Solo geometria + unità | Blender, altri CAD |

Blender esporta **Standard 3MF**. Bambu Studio lo importa correttamente come modello geometrico, esattamente come farebbe con uno STL, ma con il vantaggio che le unità (mm) sono esplicite nel file — nessuna ambiguità di scala.

**Workflow consigliato con Bambu Studio:**
```
Blender → export .3mf (global_scale=1000) → importa in Bambu Studio
```
Il modello apparirà già nella dimensione corretta in mm senza bisogno di scalare manualmente.

---

### Script helper: export STL o 3MF parametrico

```python
import bpy

def export_for_print(
    filepath,
    selected_only=True,
    apply_modifiers=True,
    format='STL'       # 'STL' | '3MF'
):
    """
    Esporta per stampa FDM in formato STL o 3MF.
    Gestisce automaticamente la scala BU→mm (scale_length=0.001).
    
    format='STL': compatibilità massima, singolo oggetto
    format='3MF': unità esplicite, multi-oggetto, raccomandato per assembly
    """
    import os
    
    # Assicura estensione corretta
    base = os.path.splitext(filepath)[0]
    filepath = base + ('.stl' if format == 'STL' else '.3mf')
    
    if format == 'STL':
        result = bpy.ops.wm.stl_export(
            filepath=filepath,
            export_selected_objects=selected_only,
            apply_modifiers=apply_modifiers,
            ascii_format=False,
            use_scene_unit=False,
            global_scale=1000.0,    # BU → mm
            forward_axis='Y',
            up_axis='Z',
        )
    elif format == '3MF':
        result = bpy.ops.export_mesh.threemf(
            filepath=filepath,
            use_selection=selected_only,
            use_mesh_modifiers=apply_modifiers,
            global_scale=1000.0,    # BU → mm
        )
    else:
        print(f"Formato non supportato: {format}")
        return
    
    if 'FINISHED' in result:
        size_kb = os.path.getsize(filepath) / 1024
        print(f"Export OK: {filepath} ({size_kb:.1f} KB)")
    else:
        print(f"Export FALLITO: {result}")


# Uso
export_for_print('/tmp/part.stl', format='STL')
export_for_print('/tmp/assembly.3mf', format='3MF')
```

---

## Note Pratiche

STL è il formato principale per stampa FDM su Bambu A1. **3MF è preferito per assembly multi-oggetto** o quando si vuole evitare ambiguità di scala. FBX è usato solo per import da generatori AI (vedi `fbx_import_guide.md`).

### Scale e Unità

- **Blender default**: unità = 1 Blender Unit = 1 metro. Per stampa 3D lavorare in millimetri: impostare `Unit System = Metric`, `Unit Scale = 0.001`.
- **STL export con scale_length=0.001**: NON usare `use_scene_unit=True`. Con scale_length=0.001, Blender esporta i vertici moltiplicati per 0.001 (0.25 BU → 0.00025) — Bambu Studio legge quei valori come mm e rileva volume zero, rimuovendo l'oggetto. Usare invece `use_scene_unit=False` + `global_scale=1000.0` per convertire BU → mm esplicitamente.

### Binary vs ASCII STL

- **Binary** (`ascii_format=False`): formato raccomandato. ~6x più compatto, import più veloce. Tutti gli slicer moderni lo supportano.
- **ASCII** (`ascii_format=True`): leggibile a testo, utile per debug o toolchain che richiedono testo. File molto più grandi.

### Assi di Orientamento

| App | Forward | Up |
|---|---|---|
| STL export default | `Y` | `Z` |
| Bambu Studio / slicer | tipicamente `Z` up |

Per stampa 3D: usare `forward_axis='Y'`, `up_axis='Z'` all'export. Se il modello appare ruotato nel slicer, correggere questi parametri oppure ruotare direttamente nel slicer.

### apply_modifiers

STL export ha `apply_modifiers=True` di default. Questo è il comportamento corretto per la stampa 3D — assicura che modifier come Subdivision, Boolean, Mirror, Solidify siano baked nella mesh esportata.

### Validazione mesh all'import

`use_mesh_validate=True` (STL) — mantenere abilitato. Disabilitarlo può importare mesh corrotte che causano crash in edit mode.
