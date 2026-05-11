# FBX Import Guide — Blender Python

## Contesto

L'FBX è il formato primario di output dei generatori AI 3D (Rodin, Hyper3D, HunyuanVideo). Ogni AI ha convenzioni diverse su scala, asse up, unità di misura, e struttura della mesh. Questo documento documenta i parametri di `bpy.ops.import_scene.fbx()` e i problemi tipici degli FBX AI-generated.

---

## Parametri `bpy.ops.import_scene.fbx()`

```python
import bpy

bpy.ops.import_scene.fbx(
    filepath="",            # OBBLIGATORIO: percorso assoluto al file .fbx
    
    # === SCALA E UNITÀ ===
    global_scale=1.0,       # scala globale applicata all'import
                            # AI FBX spesso in cm → 0.01 per convertire in m
                            # Con scale_length=0.001: usare 0.001 per FBX in mm
    use_manual_orientation=False,  # se True, usa axis_forward/axis_up
    axis_forward='-Z',      # asse del file che diventa asse Forward di Blender
    axis_up='Y',            # asse del file che diventa asse Up di Blender
                            # Standard FBX: forward=-Z, up=Y
                            # Alcuni AI: forward=Y, up=Z (Maya convention)
    
    # === GEOMETRIA ===
    use_custom_normals=True,  # importa normali custom (split normals FBX)
                              # AI mesh: spesso False è meglio (normali corrotte)
    use_image_search=True,    # cerca texture in cartelle vicine
    use_alpha_decals=False,
    decal_offset=0.0,
    use_anim=False,           # AI mesh: di solito False (no animation needed)
    anim_offset=1.0,
    use_subsurf=False,        # non applicare subdivision
    use_custom_props=True,
    use_custom_props_enum_as_string=True,
    ignore_leaf_bones=False,
    force_connect_children=False,
    automatic_bone_orientation=False,
    primary_bone_axis='Y',
    secondary_bone_axis='X',
    use_prepost_rot=True,
)
```

---

## Problemi tipici degli FBX AI-generated

### Problema 1: Scala in centimetri (il più comune)

La maggior parte degli AI genera FBX in centimetri anche se il modello "sembra" in mm. In Blender con `scale_length=0.001` (1 BU = 1mm), un modello da 100mm dovrebbe misurare 0.1 BU. Se misura 10 BU, è in centimetri.

**Diagnosi:**
```python
import bpy

obj = bpy.context.active_object
dims = obj.dimensions
print(f"Dimensioni importate: {dims.x:.4f} × {dims.y:.4f} × {dims.z:.4f} BU")
print(f"= {dims.x/0.001:.1f} × {dims.y/0.001:.1f} × {dims.z/0.001:.1f} mm")
# Se i mm sembrano 100× troppo grandi → FBX era in cm
```

**Fix:**
```python
# Opzione A: reimporta con global_scale=0.01
bpy.ops.import_scene.fbx(filepath="...", global_scale=0.01)

# Opzione B: scala l'oggetto già importato
obj = bpy.context.active_object
obj.scale *= 0.01
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
```

### Problema 2: Asse up sbagliato (Y vs Z)

Blender usa Z-up; Maya (e molti AI) usa Y-up. Il modello appare ruotato di 90°.

```python
# Fix all'import
bpy.ops.import_scene.fbx(
    filepath="model.fbx",
    use_manual_orientation=True,
    axis_forward='-Z',
    axis_up='Y',         # FBX Y-up → Blender Z-up
)

# Fix post-import
obj = bpy.context.active_object
import math
obj.rotation_euler.x = math.radians(-90)
bpy.ops.object.transform_apply(rotation=True)
```

### Problema 3: Normali custom corrotte (split normals)

FBX AI spesso include normali custom che in Blender producono shading artefatti o errori nel 3D Print Toolbox.

```python
# Fix: rimuovi normali custom PRIMA di qualsiasi operazione
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.mode_set(mode='OBJECT')

# Poi ricalcola normali standard
bpy.ops.object.shade_smooth()
# oppure: ricalcola solo normali (non smooth shading)
mesh = bpy.context.active_object.data
mesh.calc_normals_split()
```

### Problema 4: Mesh multipli come oggetti separati

Molti AI generano FBX con body, accessori, armatura come oggetti separati. Occorre unire solo le mesh rilevanti.

```python
import bpy

def collect_fbx_meshes():
    """Raccoglie e unisce tutte le MESH importate dall'FBX in un unico oggetto."""
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    
    if not mesh_objects:
        print("Nessuna mesh trovata dopo import FBX")
        return None
    
    print(f"Trovate {len(mesh_objects)} mesh: {[o.name for o in mesh_objects]}")
    
    if len(mesh_objects) == 1:
        return mesh_objects[0]
    
    # Seleziona e unisci
    bpy.ops.object.select_all(action='DESELECT')
    for o in mesh_objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0]
    bpy.ops.object.join()
    
    result = bpy.context.active_object
    print(f"Joined in: '{result.name}' — {len(result.data.vertices)} verts")
    return result
```

### Problema 5: Armatura / Bones embedded

FBX AI contiene spesso armatura (skeleton). Per la stampa 3D non serve, ma può interferire con le operazioni.

```python
import bpy

def remove_armatures():
    """Rimuove tutti gli oggetti di tipo ARMATURE dalla scena."""
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    for arm in armatures:
        bpy.data.objects.remove(arm, do_unlink=True)
    print(f"Rimosse {len(armatures)} armature")
    
def remove_modifiers_armature(obj):
    """Rimuove modifier ARMATURE dall'oggetto mesh."""
    to_remove = [m.name for m in obj.modifiers if m.type == 'ARMATURE']
    for name in to_remove:
        obj.modifiers.remove(obj.modifiers[name])
    print(f"Rimossi {len(to_remove)} modifier ARMATURE da '{obj.name}'")
```

---

## CALL_1 standard per FBX AI — script di import completo

Equivalente del CALL_1 per STL, ma per FBX. Da eseguire immediatamente dopo aver ricevuto un FBX da un generatore AI.

```python
import bpy
import math

# ===== CONFIGURAZIONE =====
FBX_PATH      = "/path/to/model.fbx"    # percorso al file FBX
EXPECTED_SIZE_MM = 100.0                  # dimensione attesa (lato più lungo in mm)
AUTO_FIX_SCALE = True                     # scala automaticamente se fuori range

# ===== IMPORT FBX =====
print("=== FBX IMPORT ===")

# Pulisci scena prima (rimuovi oggetti esistenti se necessario)
# bpy.ops.object.select_all(action='SELECT')
# bpy.ops.object.delete()

# Import con parametri AI standard
bpy.ops.import_scene.fbx(
    filepath=FBX_PATH,
    global_scale=1.0,           # correggeremo dopo se necessario
    use_manual_orientation=True,
    axis_forward='-Z',
    axis_up='Y',                 # gestisce Y-up degli AI
    use_custom_normals=False,    # ignora normali custom (spesso corrotte)
    use_anim=False,              # niente animazioni
    ignore_leaf_bones=True,
)

# Identifica le mesh importate
mesh_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
arm_objects  = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
print(f"Importati: {len(mesh_objects)} mesh, {len(arm_objects)} armature")

# Rimuovi armature
for arm in arm_objects:
    bpy.data.objects.remove(arm, do_unlink=True)

# Unisci mesh multipli
if len(mesh_objects) > 1:
    bpy.ops.object.select_all(action='DESELECT')
    for o in mesh_objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0]
    bpy.ops.object.join()

obj = bpy.context.active_object
print(f"Oggetto finale: '{obj.name}'")

# Rimuovi normali custom (artefatti FBX AI)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.mode_set(mode='OBJECT')

# Applica trasformazioni
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Controlla scala
dims = obj.dimensions
max_dim_mm = max(dims) / 0.001  # converti BU in mm
print(f"Dimensioni: {dims.x/0.001:.1f} × {dims.y/0.001:.1f} × {dims.z/0.001:.1f} mm")
print(f"Dimensione massima: {max_dim_mm:.1f}mm (attesa: {EXPECTED_SIZE_MM}mm)")

if AUTO_FIX_SCALE and EXPECTED_SIZE_MM > 0:
    ratio = EXPECTED_SIZE_MM / max_dim_mm
    if abs(ratio - 1.0) > 0.05:  # differenza > 5%
        print(f"Correzione scala: ×{ratio:.4f}")
        obj.scale *= ratio
        bpy.ops.object.transform_apply(scale=True)
        dims = obj.dimensions
        print(f"Dimensioni corrette: {dims.x/0.001:.1f} × {dims.y/0.001:.1f} × {dims.z/0.001:.1f} mm")

# Report finale
mesh = obj.data
print(f"\n=== REPORT FBX IMPORT ===")
print(f"Oggetto: {obj.name}")
print(f"Vertices: {len(mesh.vertices)}")
print(f"Polygons: {len(mesh.polygons)}")
print(f"Location: {[round(v/0.001,1) for v in obj.location]} mm")
print(f"Scala: {list(obj.scale)} (dovrebbe essere 1,1,1)")
print("Pronto per: mesh_repair → 3D Print Toolbox → export STL")
```

---

## Tabella: comportamento AI generatori FBX

| Generatore | Unità FBX | Asse Up | Normali | Struttura |
|---|---|---|---|---|
| Rodin (Hyper3D) | metri (1 unità ≈ 1m) | Y-up | Custom spesso corrotte | 1–3 mesh separate |
| HunyuanVideo | cm o mm (variabile) | Y-up | Standard | Single mesh |
| Meshy | cm | Z-up | Custom | Single mesh + texture |
| CSM (Common Sense Machines) | m | Y-up | Custom | Single mesh |
| Shap-E / Zero123 | variabile | Y-up | Standard | Single mesh |

**Regola pratica:** dopo ogni import FBX AI, verifica sempre dimensioni e confronta con EXPECTED_SIZE_MM. Il 90% dei problemi di scala si risolve con un semplice fattore 0.01 (da cm a m) o con la correzione automatica del CALL_1.

---

## Differenze FBX vs STL per workflow stampa 3D

| Aspetto | STL | FBX |
|---|---|---|
| Struttura | Sempre single mesh | Multi-mesh + armatura + materiali |
| Scala | Esplicita (mm o pollici) | Ambigua (dipende dall'esportatore) |
| Normali | Standard | Custom split normals (spesso corrotte) |
| Post-import richiesto | Applicare scala, repair | Più passi: unire, rimuovere rig, fix normali, scala |
| Preferenza | Sì, se disponibile | Solo se STL non disponibile o se serve la struttura |
