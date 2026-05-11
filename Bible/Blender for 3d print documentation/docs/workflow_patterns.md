# Combinazioni di Operazioni — Blender per Stampa 3D FDM

Questo documento descrive cosa producono le combinazioni di operazioni Blender, in quali condizioni
hanno senso, e come interagiscono tra loro. Non è una lista di procedure da eseguire in sequenza:
è una mappa di effetti che consente di scegliere autonomamente cosa applicare in base al problema.

Il target è sempre STL per stampa FDM su Bambu A1 (volume 256×256×256 mm). Le unità di scena
devono essere impostate con `scale_length=0.001` (1 Blender Unit = 1 mm).

---

## Import STL + Repair + Export STL

`wm.stl_import` carica la geometria grezza da file. Il parametro `global_scale` determina se le
dimensioni dell'STL vengono rispettate letteralmente o riscalate all'import; con `use_scene_unit=False`
la scala numerica del file viene usata as-is, con `True` viene adattata alle unità di scena correnti.
Dopo l'import l'oggetto attivo è quello appena caricato.

Le operazioni di repair agiscono su problemi diversi e non si sostituiscono a vicenda.
`print3d_clean_non_manifold` individua e tenta di correggere bordi non-manifold in modo automatizzato.
Le operazioni in edit mode (`remove_doubles`, `dissolve_degenerate`, `normals_make_consistent`,
`fill_holes`) completano quello che il toolbox automatico non risolve: vertici sovrapposti, facce
degeneri, normali invertite, buchi residui. Entrambi i livelli di repair sono spesso necessari
su geometrie importate da sorgenti esterne o generate da CAD.

`transform_apply(rotation=True, scale=True)` va eseguito prima dell'export: senza di esso la
trasformazione rimane come dato object-level e non è incisa nella mesh — Bambu Studio può
interpretarla correttamente ma è una pratica rischiosa. `stl_export` con `use_scene_unit=True`
e `scale_length=0.001` garantisce che i valori numerici nel file siano millimetri reali.

```python
import bpy, addon_utils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.wm.stl_import(
    filepath="C:/input/modello.stl",
    global_scale=1.0,
    use_scene_unit=False
)
obj = bpy.context.active_object

addon_utils.enable("object_print3d_utils", default_set=True)
bpy.ops.mesh.print3d_clean_non_manifold()

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0001)
bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.mesh.fill_holes(sides=0)
bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bpy.ops.mesh.print3d_check_all()

bpy.ops.wm.stl_export(
    filepath="C:/output/modello_fixed.stl",
    export_selected_objects=True,
    use_scene_unit=True,
    ascii_format=False
)
```

---

## origin_set + Scale Computation + transform_apply

Questa combinazione risolve il problema di portare un modello a dimensioni note in millimetri.
`origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')` è il passo preliminare essenziale: sposta
l'origine dell'oggetto al centro del bounding box, rendendo `obj.dimensions` un riferimento
affidabile per il calcolo successivo.

`obj.dimensions.x` (e `.y`, `.z`) restituisce la dimensione corrente in Blender Units. Con
`scale_length=0.001`, 1 BU = 1 mm, quindi `obj.dimensions.x * 1000` dà i millimetri correnti.
Il fattore di scala per raggiungere `target_mm` è `target_mm * 0.001 / obj.dimensions.x` —
questo converte il target in BU e lo divide per la dimensione BU corrente.

Il fattore va moltiplicato su `obj.scale` (non assegnato direttamente) per preservare eventuali
scale non-uniformi preesistenti. Dopo la modifica, `transform_apply(scale=True)` imprime la
scala nella geometria della mesh. Senza questo passo, il modificatore boolean e il solidify
operano sulla scala non-applicata con risultati imprevedibili.

Il riposizionamento `obj.location.z = obj.dimensions.z / 2` porta la base del modello a Z=0
— condizione necessaria per Bambu Studio, che piazza il piano di stampa a quota 0.

```python
import bpy

obj = bpy.context.active_object
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001

bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

target_x_mm = 100.0
scale_factor = target_x_mm * 0.001 / obj.dimensions.x
obj.scale *= scale_factor

bpy.ops.object.transform_apply(scale=True)

# Porta la base a Z=0
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
obj.location.z = obj.dimensions.z / 2
```

---

## Boolean UNION: fusione di volumi separati

Un modificatore BOOLEAN con `operation='UNION'` e `solver='EXACT'` unisce due mesh in un unico
solido chiuso. Il risultato sostituisce la mesh base incorporando il volume del cutter; il cutter
viene poi eliminato dalla scena. `solver='EXACT'` è preferito a `'FAST'` per stampabilità: produce
bordi più puliti e gestisce meglio le intersezioni tangenti.

La combinazione è appropriata quando si hanno componenti separati che devono diventare un singolo
pezzo stampabile: supporti aggiunti come oggetti distinti, dettagli modellati separatamente,
assemblaggi multi-body esportati come mesh non connesse. Dopo l'unione, un ciclo di
`remove_doubles` + `normals_make_consistent` è quasi sempre necessario perché il boolean può
lasciare vertici sovrapposti sulle superfici di intersezione.

Per unire più di due oggetti si itera: ogni oggetto viene fuso all'oggetto base sequenzialmente.
L'ordine non influisce sul risultato geometrico finale per UNION.

```python
import bpy

names = ['Base', 'Attachment', 'Connector']
base = bpy.data.objects[names[0]]

for name in names[1:]:
    cutter = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = base

    mod = base.modifiers.new(name=f"Bool_{name}", type='BOOLEAN')
    mod.operation = 'UNION'
    mod.object = cutter
    mod.solver = 'EXACT'

    bpy.ops.object.modifier_apply(modifier=f"Bool_{name}")
    bpy.data.objects.remove(cutter, do_unlink=True)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0001)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
```

---

## Boolean DIFFERENCE: cavità, fori, scavi

DIFFERENCE sottrae il volume del cutter dall'oggetto base. Il cutter è un oggetto Blender ordinario
(cilindro, cubo, mesh arbitraria) posizionato dove deve comparire la cavità. La geometria del cutter
non compare nel risultato: conta solo il volume che occupa.

Per un foro passante il cutter deve attraversare completamente la mesh base da un lato all'altro —
se non la perfora, il boolean produce un incavo anziché un foro. Le dimensioni del cutter vanno
espresse in BU: con `scale_length=0.001`, un raggio di `0.0016` corrisponde a 1.6 mm (diametro
3.2 mm, adatto a un foro M3 con clearance di 0.2 mm).

`primitive_cylinder_add` crea il cutter già come oggetto attivo, semplificando il posizionamento
immediato via `location`. Se il posizionamento richiede precisione millimetrica, va calcolato in BU:
`pos_mm * 0.001`. Dopo l'apply, il cutter va rimosso con `bpy.data.objects.remove`.

```python
import bpy

# Foro M3: raggio 1.6mm = 0.0016 BU con scale_length=0.001
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.0016,
    depth=0.02,       # 20mm profondità — perfora la mesh base
    location=(0, 0, 0)
)
cutter = bpy.context.active_object
cutter.name = "HoleCutter"

base = bpy.data.objects['Base']
bpy.context.view_layer.objects.active = base

mod = base.modifiers.new(name="Hole", type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = cutter
mod.solver = 'EXACT'

bpy.ops.object.modifier_apply(modifier="Hole")
bpy.data.objects.remove(cutter, do_unlink=True)
```

---

## Regole critiche per operazioni Boolean

### Regola 1 — Coplanarità: MAI facce sovrapposte o a filo

> ⚠ **Non permettere mai che le facce del cutter siano coplanari (a filo) con le facce dell'oggetto base, né che si sovrappongano senza intersezione di volume.**

Se le facce coincidono esattamente, il solver Boolean non può determinare quale geometria appartiene all'interno e quale all'esterno: il risultato è imprevedibile — facce mancanti, geometria corrotta, o operazione silenziosa che non modifica nulla.

**Regola pratica:** il cutter deve sempre **estendersi oltre** la mesh base su tutti i lati interessati dall'operazione, con un margine minimo di `0.001 BU` (= 1mm con `scale_length=0.001`).

```python
# SBAGLIATO — cutter a filo con la superficie superiore della base
bpy.ops.mesh.primitive_cube_add(size=0.02)  # fondo a Z=0, tetto a Z=0.02
# se la base ha la faccia superiore esattamente a Z=0.02 → coplanare → boolean invalido

# CORRETTO — cutter che perfora con margine esplicito
MARGIN = 0.001  # 1mm in BU con scale_length=0.001
bpy.ops.mesh.primitive_cube_add(size=0.022)  # +1mm per lato
```

Per **fori passanti**: il cutter deve emergere da entrambi i lati della mesh base. Se la mesh ha spessore `d`, il cutter deve avere `depth > d + 2 * MARGIN`.

Per **Boolean UNION**: le due mesh devono **intersecarsi** (sovrapposizione di volume), mai toccarsi solo in un punto o una faccia.

### Regola 2 — Appiattimento della base con Boolean DIFFERENCE

Per rendere la base di un oggetto perfettamente piatta e complanare con Z=0 (requisito per stampa FDM senza supporti), si usa un cutter piatto molto largo sottratto dall'oggetto.

```python
import bpy

# ── Flatten-bottom: rende il fondo perfettamente piatto a Z=0 ──
obj = bpy.context.active_object
dims = obj.dimensions

# Cutter: un cubo largo e sottile che "taglia via" tutto sotto Z=0
MARGIN = 0.05   # 50mm di margine per lati (BU con scale_length=0.001)
DEPTH  = 0.01   # 10mm di profondità verso il basso (BU)

bpy.ops.mesh.primitive_cube_add(size=1)
cutter = bpy.context.active_object
cutter.name = "FlattenCutter"

# Scala il cutter: X e Y molto più larghi dell'oggetto, Z sottile
cutter.scale.x = (dims.x + MARGIN * 2) / 1.0   # da BU
cutter.scale.y = (dims.y + MARGIN * 2) / 1.0
cutter.scale.z = DEPTH / 2.0

# Posiziona il centro del cutter a Z = -DEPTH/2 (tetto a Z=0, base a Z=-DEPTH)
cutter.location.z = -DEPTH / 2.0
bpy.ops.object.transform_apply(scale=True, location=True)

bpy.context.view_layer.objects.active = obj
mod = obj.modifiers.new(name="FlattenBase", type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = cutter
mod.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="FlattenBase")
bpy.data.objects.remove(cutter, do_unlink=True)

print("Base appiattita: tutto sotto Z=0 rimosso")
```

Dopo questa operazione il fondo dell'oggetto si trova esattamente a Z=0 e può essere messo in stampa direttamente senza manipolazioni aggiuntive.

### Regola 3 — Applicare la scala PRIMA di qualsiasi Boolean

> ⚠ **Eseguire `bpy.ops.object.transform_apply(scale=True)` su ENTRAMBI gli oggetti (base e cutter) prima di aggiungere il modificatore Boolean. Una scala non applicata (valori diversi da 1.0 in `obj.scale`) causa risultati errati o silenziosi nel Boolean.**

Il Boolean opera sulla geometria della mesh in coordinate locali moltiplicata per la scala object-level. Se la scala non è applicata, il solver riceve dimensioni inconsistenti tra i due oggetti e può:
- produrre geometria errata senza messaggi di errore
- ignorare silenziosamente l'operazione (la mesh non cambia)
- generare artefatti o inversioni di normali

**Sequenza sicura prima di ogni Boolean:**

```python
import bpy

def apply_scale_safe(obj):
    """Applica la scala di un oggetto rendendola 1,1,1 — obbligatorio prima di Boolean."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    is_clean = all(abs(s - 1.0) < 0.0001 for s in obj.scale)
    print(f"{obj.name}: scala applicata → {list(obj.scale)} — OK: {is_clean}")
    return is_clean

base = bpy.data.objects['Base']
cutter = bpy.data.objects['Cutter']

apply_scale_safe(base)
apply_scale_safe(cutter)

# Solo ora è sicuro aggiungere il modificatore Boolean
bpy.context.view_layer.objects.active = base
mod = base.modifiers.new(name="BoolOp", type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = cutter
mod.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="BoolOp")
bpy.data.objects.remove(cutter, do_unlink=True)
```

**Quando è più critico:** quando si duplicano oggetti (`bpy.ops.object.duplicate()`), i duplicati ereditano la scala dell'originale — che potrebbe essere non-unitaria se l'oggetto era stato scalato in Object Mode senza applicare. Applicare sempre la scala dopo ogni duplicazione che precede un Boolean.

---

## Solidify: aggiungere spessore a mesh thin

Il modificatore SOLIDIFY trasforma una mesh a spessore zero (o insufficiente) in un solido con
pareti di spessore definito. È necessario quando si lavora con superfici generate da CAD, scansioni
o modelli architettonici che non hanno volume proprio ma sono geometricamente corretti.

`thickness` è in BU: con `scale_length=0.001`, `0.0012` corrisponde a 1.2 mm — spessore minimo
raccomandato per stampabilità con nozzle 0.4 mm (3 pareti). `offset=-1.0` espande la mesh verso
l'esterno rispetto alle normali: la superficie originale diventa la faccia interna del solido.
`offset=+1.0` espande verso l'interno, riducendo le dimensioni esterne. `fill_rim=True` chiude
i bordi perimetrali, producendo un solido manifold.

L'apply del modificatore va eseguito prima di qualsiasi boolean successivo. Un SOLIDIFY non
applicato interagisce in modo inaffidabile con i boolean perché la geometria effettiva non è ancora
nella mesh.

```python
import bpy

obj = bpy.context.active_object

mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
mod.thickness = 0.0012      # 1.2mm con scale_length=0.001
mod.offset = -1.0           # espande verso l'esterno
mod.use_even_offset = True
mod.fill_rim = True

bpy.ops.object.modifier_apply(modifier="Solidify")
```

---

## Solidify come compensazione tolleranza FDM (parametric offset)

Le stampanti FDM producono dimensioni leggermente diverse da quelle nominali: tipicamente un **over-extrusion di 0.1–0.3 mm** in diametro per fori e perni. Invece di modificare la geometria della mesh, si applica un modificatore SOLIDIFY con `use_rim_only=True` all'oggetto cutter per compensare la tolleranza in modo parametrico e reversibile.

**Logica:**
- `use_rim_only=True` — il Solidify espande (o contrae) solo la superficie perimetrale dell'oggetto, lasciando le facce superiori e inferiori invariate. Ideale per cutters cilindrici (fori) e prismatici (perni).
- `use_even_offset=True` — l'offset viene distribuito uniformemente anche su curve e angoli, mantenendo la circolarità di fori cilindrici.
- `offset=1` con `thickness` positivo → espande verso l'esterno (foro più largo → accomodare over-extrusion)
- `offset=-1` con `thickness` positivo → contrae verso l'interno (perno più stretto → entra nel foro over-extruded)

**Vantaggi rispetto alla modifica diretta della mesh:**
- Cambiare la tolleranza = modificare un solo valore (`mod.thickness`)
- Se la stampante cambia, basta aggiornare `TOLERANCE_MM` e ri-applicare
- Non distrugge la forma originale del cutter — undo semplice

```python
import bpy

# ── CONFIGURAZIONE TOLLERANZA ───────────────────────────────────────────────
TOLERANCE_MM = 0.2    # offset per compensare over-extrusion della stampante (in mm)
# Positivo = espande cutter foro (foro più largo)
# Negativo = contrae cutter perno (perno più stretto)
# ───────────────────────────────────────────────────────────────────────────

cutter = bpy.context.active_object  # il cilindro/prisma che fa il foro

# Il Solidify va applicato PRIMA del Boolean
mod = cutter.modifiers.new(name="TolOffset", type='SOLIDIFY')
mod.thickness = TOLERANCE_MM * 0.001   # converti mm → BU con scale_length=0.001
mod.offset = 1                          # espande verso esterno (+1) o interno (-1)
mod.use_rim_only = True                 # non chiude tetto/fondo, solo bordi laterali
mod.use_even_offset = True             # mantiene circolarità su curve

bpy.ops.object.modifier_apply(modifier="TolOffset")

# Ora applica la scala (obbligatorio prima del Boolean — vedi Regola 3)
bpy.ops.object.transform_apply(scale=True)

print(f"Tolleranza applicata: {TOLERANCE_MM}mm — cutter pronto per Boolean DIFFERENCE")
```

**Esempio pratico — foro M3 con tolleranza FDM:**

```python
# Foro M3 nominale: diametro 3.2mm (con 0.1mm clearance geometrica)
# La stampante stampa ~0.2mm in più → il foro effettivo sarebbe 3.4mm (troppo largo)
# Strategia: progettare il cutter a 3.0mm, espandere di 0.2mm con Solidify

TOLERANCE_MM = 0.20   # la stampante aggiunge ~0.2mm al diametro → compensare con -0.2mm
                       # ma per un foro vogliamo che entri → espandiamo il cutter

bpy.ops.mesh.primitive_cylinder_add(radius=0.0015, depth=0.02)  # 3.0mm diametro nominale
cutter = bpy.context.active_object
cutter.name = "M3_HoleCutter"

mod = cutter.modifiers.new(name="FDM_Tol", type='SOLIDIFY')
mod.thickness = 0.20 * 0.001   # 0.2mm espansione
mod.offset = 1                  # espande verso esterno → foro effettivo 3.4mm
mod.use_rim_only = True
mod.use_even_offset = True
bpy.ops.object.modifier_apply(modifier="FDM_Tol")

# → raggio effettivo dopo Solidify ≈ 1.7mm → diametro ≈ 3.4mm ✓ per bolt M3 FDM
```

**Workflow vertice-gruppo (Solidify selettivo):** per applicare la tolleranza solo a una parte del cutter (es. solo il filetto, non la testa del bullone), creare un vertex group nel cutter, assegnare la geometria del filetto, e impostare `mod.vertex_group = "NomeGruppo"`. Il Solidify espande solo i vertici nel gruppo.

---

## Analisi dimensionale: compatibilità con il volume di stampa

`obj.dimensions` restituisce il bounding box dell'oggetto nello spazio world, già tenendo conto
di scale e rotazioni applicate. Con `scale_length=0.001`, moltiplicare per 1000 dà i millimetri.

Il confronto sistematico degli assi contro i 256 mm del volume A1 permette di identificare:
quale asse supera i limiti (e quindi richiede ridimensionamento o riorientamento), qual è
l'asse più alto (che dovrebbe corrispondere a Z per minimizzare supporti), e se il modello
ha proporzioni che suggeriscono una rotazione.

L'analisi non implica azioni correttive automatiche: le decisioni su come riorientare o riscalare
dipendono dalla geometria specifica e dall'uso previsto del pezzo. Il codice sotto raccoglie i
dati; le azioni conseguenti usano le combinazioni descritte nelle altre sezioni.

```python
import bpy

obj = bpy.context.active_object
dims = obj.dimensions

dims_mm = {
    'X': dims.x * 1000,
    'Y': dims.y * 1000,
    'Z': dims.z * 1000
}

tallest_axis = max(dims_mm, key=dims_mm.get)
exceeds = [ax for ax, val in dims_mm.items() if val > 256]

print(f"Dimensioni: X={dims_mm['X']:.1f}mm  Y={dims_mm['Y']:.1f}mm  Z={dims_mm['Z']:.1f}mm")
print(f"Asse più alto: {tallest_axis} = {dims_mm[tallest_axis]:.1f}mm")
print(f"Volume build A1: 256x256x256mm")

if exceeds:
    print(f"FUORI VOLUME: assi {exceeds} superano 256mm")
else:
    print("Dimensioni compatibili con A1")
```

---

## Split modello oversized: piano di taglio + registration pins

Un modello che supera i 256mm su almeno un asse deve essere suddiviso in pezzi stampabili
separatamente e poi assemblati. La procedura usa un cutter cubico (piano di taglio) con Boolean
DIFFERENCE per produrre due metà, poi aggiunge pin e foro di accoppiamento per l'allineamento.

**Logica del taglio:**
Il cutter è un cubo che copre metà dell'oggetto; posizionato sul piano di taglio desiderato,
sottratto in sequenza da una copia dell'originale per produrre parte A (sotto il taglio)
e parte B (sopra il taglio). Il piano di taglio Z è la variabile di configurazione principale.

**Dimensionamento registration pin (PLA, press-fit):**
- Diametro pin: 4mm, diametro foro: 4.1mm (clearance 0.05mm lato → slip-fit leggero)
- Lunghezza pin: 6–8mm (incasso in entrambe le metà di 3–4mm)
- Con `scale_length=0.001`: raggio pin = 0.002 BU, lunghezza = 0.006 BU

```python
import bpy, math

# ── CONFIGURAZIONE ─────────────────────────────────────────────────────────────
OBJ_NAME = "Modello"           # nome dell'oggetto da dividere
CUT_Z_MM = 120.0               # altezza del piano di taglio in mm
PIN_DIAMETER_MM = 4.0          # diametro pin di allineamento
PIN_HOLE_CLEARANCE_MM = 0.10   # clearance diametrale foro (0.10 = slip-fit sicuro)
PIN_LENGTH_MM = 8.0            # lunghezza totale pin (3–4mm per metà)
OUTPUT_DIR = "/path/to/output/"
# ──────────────────────────────────────────────────────────────────────────────

def mm_to_bu(mm):
    """Converti mm in Blender Units con scale_length=0.001"""
    return mm * 0.001

def make_cutter(name, size_bu, location):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    cutter = bpy.context.active_object
    cutter.name = name
    cutter.scale = size_bu
    bpy.ops.object.transform_apply(scale=True)
    return cutter

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001

orig = bpy.data.objects[OBJ_NAME]
dims_mm = [d * 1000 for d in orig.dimensions]
print(f"Modello: X={dims_mm[0]:.1f}  Y={dims_mm[1]:.1f}  Z={dims_mm[2]:.1f}mm")

cut_z_bu = mm_to_bu(CUT_Z_MM)
total_z_bu = orig.dimensions.z
total_xy_bu = max(orig.dimensions.x, orig.dimensions.y) * 2  # cutter più largo del modello

# ----- PARTE A (metà inferiore: Z < CUT_Z_MM) -----
orig.select_set(True)
bpy.context.view_layer.objects.active = orig
bpy.ops.object.duplicate()
part_a = bpy.context.active_object
part_a.name = f"{OBJ_NAME}_PartA"

# Cutter A: cubo che copre la metà superiore → la sottrae → rimane metà inferiore
cutter_a_height_bu = total_z_bu - cut_z_bu + 0.01  # un po' oltre per sicurezza
cutter_a_z_bu = cut_z_bu + cutter_a_height_bu / 2   # centro del cutter, sopra il taglio

cutter_a = make_cutter(
    "CutterA_Upper",
    (total_xy_bu / 2, total_xy_bu / 2, cutter_a_height_bu / 2),
    (orig.location.x, orig.location.y, orig.location.z - orig.dimensions.z/2 + cutter_a_z_bu)
)

bpy.context.view_layer.objects.active = part_a
mod_a = part_a.modifiers.new(name="SplitA", type='BOOLEAN')
mod_a.operation = 'DIFFERENCE'
mod_a.object = cutter_a
mod_a.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="SplitA")
bpy.data.objects.remove(cutter_a, do_unlink=True)

# ----- PARTE B (metà superiore: Z > CUT_Z_MM) -----
orig.select_set(True)
bpy.context.view_layer.objects.active = orig
bpy.ops.object.duplicate()
part_b = bpy.context.active_object
part_b.name = f"{OBJ_NAME}_PartB"

cutter_b_height_bu = cut_z_bu + 0.01
cutter_b_z_bu = cut_z_bu / 2 - cut_z_bu / 2  # centro del cutter, sotto il taglio

cutter_b = make_cutter(
    "CutterB_Lower",
    (total_xy_bu / 2, total_xy_bu / 2, cutter_b_height_bu / 2),
    (orig.location.x, orig.location.y, orig.location.z - orig.dimensions.z/2 + cutter_b_height_bu/2)
)

bpy.context.view_layer.objects.active = part_b
mod_b = part_b.modifiers.new(name="SplitB", type='BOOLEAN')
mod_b.operation = 'DIFFERENCE'
mod_b.object = cutter_b
mod_b.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="SplitB")
bpy.data.objects.remove(cutter_b, do_unlink=True)

# ----- REGISTRATION PIN su Parte A (pin maschio) -----
pin_r_bu = mm_to_bu(PIN_DIAMETER_MM / 2)
pin_l_bu = mm_to_bu(PIN_LENGTH_MM / 2)  # metà pin per metà — si incassa per 4mm
cut_z_world = orig.location.z - orig.dimensions.z/2 + cut_z_bu
pin_offset_bu = mm_to_bu(15.0)  # offset dal centro (regola in base alla geometria)

for offset in [(pin_offset_bu, 0), (-pin_offset_bu, 0), (0, pin_offset_bu)]:
    bpy.ops.mesh.primitive_cylinder_add(
        radius=pin_r_bu,
        depth=pin_l_bu,
        location=(orig.location.x + offset[0],
                  orig.location.y + offset[1],
                  cut_z_world - pin_l_bu / 2)
    )
    pin = bpy.context.active_object
    pin.name = "Pin"
    bpy.context.view_layer.objects.active = part_a
    part_a.select_set(True)
    pin.select_set(True)
    bpy.ops.object.join()

# ----- FORO PIN su Parte B (foro femmina) -----
hole_r_bu = mm_to_bu((PIN_DIAMETER_MM + PIN_HOLE_CLEARANCE_MM) / 2)
hole_depth_bu = mm_to_bu(PIN_LENGTH_MM / 2 + 0.5)  # 0.5mm profondità extra

for offset in [(pin_offset_bu, 0), (-pin_offset_bu, 0), (0, pin_offset_bu)]:
    bpy.ops.mesh.primitive_cylinder_add(
        radius=hole_r_bu,
        depth=hole_depth_bu,
        location=(orig.location.x + offset[0],
                  orig.location.y + offset[1],
                  cut_z_world + hole_depth_bu / 2)
    )
    hole_cutter = bpy.context.active_object
    hole_cutter.name = "HoleCutter"
    bpy.context.view_layer.objects.active = part_b
    mod_hole = part_b.modifiers.new(name="PinHole", type='BOOLEAN')
    mod_hole.operation = 'DIFFERENCE'
    mod_hole.object = hole_cutter
    mod_hole.solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier="PinHole")
    bpy.data.objects.remove(hole_cutter, do_unlink=True)

# ----- Transform apply + export separato -----
for part, suffix in [(part_a, "A"), (part_b, "B")]:
    bpy.context.view_layer.objects.active = part
    bpy.ops.object.select_all(action='DESELECT')
    part.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    # Porta la base di ogni pezzo a Z=0
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    part.location.z = part.dimensions.z / 2

    filepath = f"{OUTPUT_DIR}{OBJ_NAME}_Part{suffix}.stl"
    bpy.ops.wm.stl_export(
        filepath=filepath,
        export_selected_objects=True,
        global_scale=1000.0,
        use_scene_unit=False,
        ascii_format=False,
        apply_modifiers=True
    )
    dims = [d * 1000 for d in part.dimensions]
    print(f"Parte {suffix}: X={dims[0]:.1f}mm Y={dims[1]:.1f}mm Z={dims[2]:.1f}mm → {filepath}")

print("Split completato — stampare le due parti separatamente, assemblare con press-fit sui pin")
```

**Note di assemblaggio post-stampa:**
- Superficie di taglio liscia → applicare CA glue o epossidico per permanente
- Per assemblaggio reversibile: foro passante + vite M3 invece del pin (→ `threads_and_fasteners.md`)
- Orientare le parti in Bambu Studio con la faccia di taglio sul bed (nessun supporto sulla giuntura)

---

## QA Pipeline automatizzata

Script completo che esegue tutti i controlli di qualità in sequenza e produce un report testuale
strutturato. Da eseguire come singolo blocco `execute_blender_code` prima dell'export finale.
Il report viene stampato via `print()` e catturato dalla risposta MCP.

```python
import bpy
import bmesh
import addon_utils
from datetime import datetime

def run_qa_pipeline(obj_name=None):
    """
    Esegue tutti i controlli QA su un mesh e restituisce un report strutturato.
    Se obj_name è None, usa l'oggetto mesh attivo nella scena.
    """

    # ── Selezione oggetto ──────────────────────────────────────────────────────
    if obj_name:
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            return f"ERRORE: oggetto '{obj_name}' non trovato"
    else:
        obj = next((o for o in bpy.context.scene.objects if o.type == 'MESH'), None)
        if not obj:
            return "ERRORE: nessun oggetto MESH nella scena"

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    results = {}
    warnings = []
    errors = []

    # ── CHECK 1: Unità scena ──────────────────────────────────────────────────
    scene = bpy.context.scene
    scale_length = scene.unit_settings.scale_length
    unit_system = scene.unit_settings.system
    results['units'] = {
        'system': unit_system,
        'scale_length': scale_length,
        'ok': (scale_length == 0.001 and unit_system == 'METRIC')
    }
    if not results['units']['ok']:
        errors.append(f"Unità errate: system={unit_system}, scale_length={scale_length} (atteso METRIC, 0.001)")

    # ── CHECK 2: Dimensioni vs build volume ───────────────────────────────────
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    dims_bu = obj.dimensions
    dims_mm = {'X': dims_bu.x * 1000, 'Y': dims_bu.y * 1000, 'Z': dims_bu.z * 1000}
    max_dim = max(dims_mm.values())
    results['dimensions'] = {
        'mm': dims_mm,
        'max_mm': max_dim,
        'fits_a1': all(v <= 256 for v in dims_mm.values())
    }
    if not results['dimensions']['fits_a1']:
        over = [f"{ax}={v:.1f}mm" for ax, v in dims_mm.items() if v > 256]
        errors.append(f"Fuori volume A1: {', '.join(over)} (max 256mm per asse)")
    if max_dim < 1.0:
        errors.append(f"Modello microscopico: dimensione max {max_dim:.3f}mm — scala probabilmente errata")
    elif max_dim < 5.0:
        warnings.append(f"Modello molto piccolo ({max_dim:.1f}mm) — verifica scala")

    # ── CHECK 3: Manifold ─────────────────────────────────────────────────────
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
    boundary_edges = [e for e in bm.edges if e.is_boundary]
    zero_area_faces = [f for f in bm.faces if f.calc_area() < 1e-10]
    isolated_verts = [v for v in bm.verts if not v.link_edges]

    results['manifold'] = {
        'non_manifold_edges': len(non_manifold_edges),
        'boundary_edges': len(boundary_edges),
        'zero_area_faces': len(zero_area_faces),
        'isolated_verts': len(isolated_verts),
        'is_manifold': (len(non_manifold_edges) == 0 and len(boundary_edges) == 0)
    }

    if len(non_manifold_edges) > 100:
        errors.append(f"Mesh gravemente non-manifold: {len(non_manifold_edges)} edge problematici")
    elif len(non_manifold_edges) > 0:
        warnings.append(f"{len(non_manifold_edges)} edge non-manifold — il slicer Bambu gestisce casi lievi")
    if len(boundary_edges) > 50:
        errors.append(f"{len(boundary_edges)} buchi nella mesh (boundary edges)")

    # ── CHECK 4: Face count ───────────────────────────────────────────────────
    n_faces = len(bm.faces)
    n_verts = len(bm.verts)
    n_edges = len(bm.edges)
    results['poly_count'] = {'faces': n_faces, 'verts': n_verts, 'edges': n_edges}

    if n_faces > 500000:
        warnings.append(f"Face count alto ({n_faces:,}) — lo slicer potrebbe essere lento. Target: < 200k")
    elif n_faces < 500:
        warnings.append(f"Face count molto basso ({n_faces}) — mesh forse sovra-decimata")

    bm.free()

    # ── CHECK 5: Normali ─────────────────────────────────────────────────────
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()

    # Conta normali verso l'interno via dot product con direzione verso centro
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh_data = obj.data
    inward_normals = 0
    for poly in mesh_data.polygons:
        center_to_face = poly.center - obj.location
        if poly.normal.dot(center_to_face) < 0:
            inward_normals += 1

    pct_inward = 100 * inward_normals / max(1, len(mesh_data.polygons))
    results['normals'] = {
        'inward_count': inward_normals,
        'inward_pct': pct_inward,
        'ok': pct_inward < 5.0  # < 5% invertite = accettabile
    }
    if pct_inward > 30:
        errors.append(f"Normali criticamente errate: {pct_inward:.1f}% rivolte verso l'interno")
    elif pct_inward > 5:
        warnings.append(f"Normali parzialmente errate: {pct_inward:.1f}% invertite")

    # ── CHECK 6: Transforms applicati ────────────────────────────────────────
    scale_applied = all(abs(s - 1.0) < 0.001 for s in obj.scale)
    rot_applied = all(abs(r) < 0.001 for r in obj.rotation_euler)
    results['transforms'] = {
        'scale_applied': scale_applied,
        'rotation_applied': rot_applied
    }
    if not scale_applied:
        errors.append(f"Scale non applicata: {list(obj.scale)} — eseguire transform_apply(scale=True)")
    if not rot_applied:
        warnings.append(f"Rotazione non applicata: {list(obj.rotation_euler)}")

    # ── CHECK 7: Base modello ─────────────────────────────────────────────────
    base_z_mm = (obj.location.z - obj.dimensions.z / 2) * 1000
    results['base_z'] = {'base_z_mm': base_z_mm, 'ok': abs(base_z_mm) < 0.5}
    if base_z_mm < -0.5:
        warnings.append(f"Base modello a Z={base_z_mm:.2f}mm (sotto piano stampa)")
    elif abs(base_z_mm) > 1.0:
        warnings.append(f"Base modello non a Z=0 (Z={base_z_mm:.2f}mm)")

    # ── WALL THICKNESS via 3D Print Toolbox ──────────────────────────────────
    try:
        addon_utils.enable("object_print3d_utils", default_set=True)
        bpy.context.scene.print_3d.thickness_min = 0.0012  # 1.2mm = 3 pareti nozzle 0.4mm
        bpy.ops.mesh.print3d_check_thick()
        results['wall_thickness'] = {'checked': True, 'note': 'Vedi Info Editor per dettagli'}
    except Exception as e:
        results['wall_thickness'] = {'checked': False, 'error': str(e)}

    # ── REPORT ────────────────────────────────────────────────────────────────
    sep = "=" * 60
    report_lines = [
        sep,
        f"  QA REPORT — {obj.name}",
        f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        sep,
        "",
        "[UNITÀ]",
        f"  Sistema: {results['units']['system']} — scale_length: {results['units']['scale_length']}",
        f"  {'✓ Corrette' if results['units']['ok'] else '✗ ERRATE'}",
        "",
        "[DIMENSIONI]",
        f"  X={dims_mm['X']:.1f}mm  Y={dims_mm['Y']:.1f}mm  Z={dims_mm['Z']:.1f}mm",
        f"  {'✓ Entra nel volume A1' if results['dimensions']['fits_a1'] else '✗ FUORI VOLUME A1'}",
        "",
        "[MANIFOLD]",
        f"  Edge non-manifold: {results['manifold']['non_manifold_edges']}",
        f"  Edge boundary (buchi): {results['manifold']['boundary_edges']}",
        f"  Facce zero-area: {results['manifold']['zero_area_faces']}",
        f"  {'✓ Manifold' if results['manifold']['is_manifold'] else '⚠ Non-manifold'}",
        "",
        "[POLY COUNT]",
        f"  Facce: {n_faces:,}  Vertici: {n_verts:,}  Edge: {n_edges:,}",
        f"  {'✓ Ottimale (< 200k)' if n_faces < 200000 else '⚠ Alto — considera decimazione' if n_faces < 500000 else '✗ Molto alto — decimazione necessaria'}",
        "",
        "[NORMALI]",
        f"  Normali verso interno: {results['normals']['inward_count']} ({results['normals']['inward_pct']:.1f}%)",
        f"  {'✓ OK' if results['normals']['ok'] else '⚠ Verificare normali'}",
        "",
        "[TRANSFORMS]",
        f"  Scale applicata: {'✓' if results['transforms']['scale_applied'] else '✗'}",
        f"  Rotazione applicata: {'✓' if results['transforms']['rotation_applied'] else '⚠'}",
        "",
        "[BASE Z]",
        f"  Base a Z={results['base_z']['base_z_mm']:.2f}mm  {'✓' if results['base_z']['ok'] else '⚠ Correggere'}",
        "",
    ]

    if errors:
        report_lines.append("[✗ ERRORI CRITICI]")
        for e in errors:
            report_lines.append(f"  • {e}")
        report_lines.append("")

    if warnings:
        report_lines.append("[⚠ AVVISI]")
        for w in warnings:
            report_lines.append(f"  • {w}")
        report_lines.append("")

    if not errors and not warnings:
        report_lines.append("✓ MESH PRONTA PER EXPORT — nessun problema rilevato")
    elif not errors:
        report_lines.append("⚠ MESH ACCETTABILE — avvisi non critici, può procedere all'export")
    else:
        report_lines.append("✗ ERRORI CRITICI — correggere prima dell'export")

    report_lines.append(sep)
    return "\n".join(report_lines)


# ── Esecuzione ─────────────────────────────────────────────────────────────────
report = run_qa_pipeline()  # passa obj_name="NomeOggetto" per oggetto specifico
print(report)
```

**Output esempio:**

```
============================================================
  QA REPORT — Modello_repaired
  2025-09-12 14:32:07
============================================================

[UNITÀ]
  Sistema: METRIC — scale_length: 0.001
  ✓ Corrette

[DIMENSIONI]
  X=87.3mm  Y=54.1mm  Z=112.6mm
  ✓ Entra nel volume A1

[MANIFOLD]
  Edge non-manifold: 0
  Edge boundary (buchi): 2
  Facce zero-area: 0
  ⚠ Non-manifold

[POLY COUNT]
  Facce: 142,817  Vertici: 71,408  Edge: 214,224
  ✓ Ottimale (< 200k)

[NORMALI]
  Normali verso interno: 12 (0.0%)
  ✓ OK

[TRANSFORMS]
  Scale applicata: ✓
  Rotazione applicata: ✓

[BASE Z]
  Base a Z=0.00mm  ✓

[⚠ AVVISI]
  • 2 buchi nella mesh (boundary edges)

⚠ MESH ACCETTABILE — avvisi non critici, può procedere all'export
============================================================
```

---

## Checklist pre-export

- `transform_apply(rotation=True, scale=True)` applicato — scala e rotazione incise nella mesh
- Dimensioni verificate: X ≤ 256mm, Y ≤ 256mm, Z ≤ 256mm per Bambu A1
- Base del modello a Z=0 (o comunque Z positiva — Bambu Studio rifiuta oggetti sotto il piano)
- `print3d_check_all()` eseguito — nessun errore critico su solid/non-manifold
- Normali consistenti verso esterno (`normals_make_consistent(inside=False)`)
- Vertici duplicati rimossi (`remove_doubles` applicato)
- Export con `global_scale=1000.0` e `use_scene_unit=False` — i valori numerici STL sono millimetri (⚠ NON usare `use_scene_unit=True` con `scale_length=0.001`: produce vertici ×0.001, Bambu Studio legge volume zero)
- `export_selected_objects=True` — esporta solo il pezzo selezionato, non tutta la scena
