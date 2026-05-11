# Hollowing and Lightening — Svuotamento e Alleggerimento per FDM

---

> ## ⚠ REGOLA PRIMARIA — LEGGERE PRIMA DI QUALSIASI ALTRA COSA
>
> **Per stampa FDM su Bambu A1: NON fare hollowing in Blender.**
>
> Lo slicer gestisce già la struttura interna tramite infill. Hollow in Blender introduce complessità inutile, rischio di mesh non-manifold e non produce alcun vantaggio rispetto a configurare correttamente Bambu Studio.
>
> **Soluzione corretta per oggetti decorativi (figurine, teste, oggetti estetici):**
> - Bambu Studio → Infill pattern: **Lightning** o **Gyroid**
> - Infill density: **10–15%**
> - Wall loops: **3–5** (= 1.2–2.0mm con nozzle 0.4mm)
> - Questo equivale funzionalmente a "hollow" senza toccare la mesh.
>
> **Solidify in Blender è giustificato SOLO se:** la mesh è una shell aperta (superficie senza spessore) e deve diventare un solido stampabile. Non per svuotare solidi già chiusi.

---

Documento operativo su come ridurre peso e materiale di un modello FDM mantenendo la resistenza strutturale necessaria. Include svuotamento (hollowing) tramite Blender e scelta dei pattern di infill in slicer.

---

## Quando Ha Senso Svuotare

### Svuotare è utile:
- Modello decorativo/estetico: non subisce forze meccaniche → shell + infill 10–15%
- Modello grande (> 100 mm in una dimensione): risparmio materiale significativo
- Stampa in resina (non FDM) dove lo svuotamento è quasi sempre obbligatorio

### Svuotare NON conviene:
- Modello già gestito dallo slicer con infill → lo slicer fa già il lavoro interno
- Pareti sottili: se lo spessore residuo post-hollowing è < 1.2 mm (3 perimetri), la parte è fragile
- Parti con carichi meccanici concentrati: la shell senza struttura interna rompe per fatica

### La verità sull'infill FDM
Per stampa FDM il modello **non deve essere svuotato in Blender** nella maggior parte dei casi. Lo slicer applica già l'infill (struttura interna porosa). Hollowing in Blender serve solo per:
1. Controllare lo spessore delle pareti in modo esplicito
2. Creare voids interni per oggetti meccanici (assemblati, incassati)
3. Casi in cui la mesh AI-generated è già solida ma non vuoi infill (es. ti serve una shell precisa per inserti)

---

## Metodo 1 — Solidify Modifier (Approccio FDM Corretto)

Il Solidify modifier converte una mesh **superficie aperta** (shell) in una mesh con spessore controllato. È il metodo corretto per mesh AI o fotogrammetria che rappresentano superfici, non solidi.

```python
import bpy

def apply_solidify_for_print(obj_name, thickness_mm=1.2, offset=-1.0):
    """
    Aggiunge spessore stampabile a una mesh-shell.
    
    thickness_mm: spessore pareti in mm. 
        - 1.2 mm = 3 perimetri con nozzle 0.4mm (raccomandato minimo strutturale)
        - 0.8 mm = 2 perimetri (decorativo, fragile)
        - 2.4 mm = 6 perimetri (robusto, per parti meccaniche)
    offset: -1.0 = spessore aggiunto verso l'interno (default corretto per hollowing)
             0.0 = spessore equidistribuito
             1.0 = spessore verso l'esterno (aumenta dimensioni esterne)
    """
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        print(f"Oggetto '{obj_name}' non trovato")
        return
    
    # Converti mm in BU (con scale_length=0.001: 1mm = 0.001 BU)
    thickness_bu = thickness_mm * 0.001
    
    mod = obj.modifiers.new(name="Solidify_Print", type='SOLIDIFY')
    mod.thickness = thickness_bu
    mod.offset = offset
    mod.use_even_offset = True          # Spessore uniforme anche su curve
    mod.use_quality_normals = True       # Normali coerenti sullo spessore
    mod.use_rim = True                   # Chiude i bordi aperti
    mod.use_rim_only = False
    
    print(f"Solidify applicato: thickness={thickness_mm}mm, offset={offset}")
    print(f"Equivale a {thickness_mm/0.4:.0f} perimetri con nozzle 0.4mm")
```

**Importante**: dopo Solidify applicare `transform_apply(scale=True)` prima dell'export.

---

## Metodo 2 — Boolean Difference (Hollowing Vero)

Per svuotare un solido chiuso creando un guscio cavo con fori di scarico:

```python
import bpy
import mathutils

def hollow_solid_mesh(obj_name, shell_thickness_mm=2.0, add_drain_holes=True,
                       drain_hole_diameter_mm=3.0):
    """
    Svuota un mesh solido chiuso creando un guscio cavo.
    
    Procedura:
    1. Duplica il mesh originale (diventa il 'cutter')
    2. Scalalo verso l'interno di shell_thickness
    3. Inverti le normali del cutter
    4. Boolean Difference: originale - cutter = shell cava
    5. (Opzionale) aggiunge fori di scarico per prevenire pressione interna
    
    ATTENZIONE: operazione distruttiva. Fare backup prima.
    """
    scene = bpy.context.scene
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        print(f"Oggetto '{obj_name}' non trovato")
        return
    
    # Passo 1: Duplica per creare il cutter
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.duplicate(linked=False)
    cutter = bpy.context.active_object
    cutter.name = obj_name + "_cutter"
    
    # Passo 2: Scala verso l'interno
    # Con scale_length=0.001: 1mm = 0.001 BU
    thickness_bu = shell_thickness_mm * 0.001
    # Stima dimensione caratteristica per calcolare il fattore di scala
    dim = max(obj.dimensions)
    scale_factor = (dim - 2 * thickness_bu) / dim if dim > 0 else 0.95
    scale_factor = max(0.5, min(0.99, scale_factor))  # clamp sicuro
    
    cutter.scale *= scale_factor
    bpy.ops.object.transform_apply(scale=True)
    
    # Passo 3: Inverti normali del cutter (facce verso l'interno)
    bpy.context.view_layer.objects.active = cutter
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Passo 4: Boolean Difference sull'originale
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bool_mod = obj.modifiers.new(name="Hollow_Boolean", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = cutter
    bool_mod.solver = 'EXACT'
    
    bpy.ops.object.modifier_apply(modifier="Hollow_Boolean")
    
    # Rimuovi il cutter (non più necessario)
    bpy.data.objects.remove(cutter, do_unlink=True)
    
    print(f"Hollowing completato: shell={shell_thickness_mm}mm")
    
    # Passo 5 (opzionale): fori di scarico
    if add_drain_holes:
        print(f"Aggiungere fori di scarico manualmente in Bambu Studio o come Boolean Difference")
        print(f"Diametro consigliato: {drain_hole_diameter_mm}mm, posizione: punto più basso del modello")
```

### Perché i Fori di Scarico Sono Critici
Una shell cava chiusa ha aria intrappolata. Durante la stampa FDM (la shell viene stampata dallo slicer come shell + infill intorno al vuoto), questo non è un problema. **Ma se il modello viene stampato in resina o se la shell cava viene effettivamente stampata come vuoto**, la pressione interna può causare distorsioni. Per FDM standard, lo slicer gestisce l'interno — il "vuoto" Blender diventa infill come qualsiasi altro solido.

**Regola pratica per FDM su A1: non fare hollowing in Blender. Usa le impostazioni infill dello slicer.**

---

## Metodo 3 — Infill Pattern Selection (Solo Slicer)

Per FDM, il modo corretto di alleggerire è configurare il pattern di infill in Bambu Studio, **senza toccare la mesh in Blender**.

### Tabella Pattern Infill per Caso d'Uso

| Pattern | Uso ideale | Resistenza | Tempo | Materiale |
|---|---|---|---|---|
| **Grid** | Parti generiche | ★★★ | ★★★ | ★★★ |
| **Gyroid** | Parti con forze multidirezionali, figurine | ★★★★ | ★★★★ | ★★★★ |
| **Honeycomb** | Parti con carico prevalentemente verticale | ★★★★ | ★★★ | ★★★ |
| **Lightning** | Parti puramente estetiche (solo per supportare superfici esterne) | ★★ | ★★★★★ | ★★★★★ |
| **Rectilinear** | Parti piatte con carico XY | ★★★ | ★★ | ★★ |
| **Triangles** | Parti con carico isotropico nel piano | ★★★★ | ★★★ | ★★★ |
| **Cubic** | Parti con carichi 3D isotropici | ★★★★★ | ★★★★ | ★★★★ |

**Simboli**: ★★★★★ = ottimo, ★ = scadente (per la categoria indicata)

### Densità Infill per Caso d'Uso (PLA A1)

| Uso | Densità | Note |
|---|---|---|
| Puramente decorativo/estetico | 10–15% | Figurine, oggetti da esporre |
| Parti leggere funzionali | 20–30% | Supporti, clip, staffe leggere |
| Parti meccaniche standard | 40–60% | Ingranaggi, case, connettori |
| Parti ad alta resistenza | 80–100% | Bulloni, giunti, parti che subiscono impatto |

**Nota**: aumentare la densità oltre il 40% porta rendimenti decrescenti sulla resistenza. È più efficace aumentare il numero di perimetri (pareti) che la densità infill.

---

## Wall Count vs Infill Density — Tradeoff

Per resistenza meccanica:

| Obiettivo | Perimetri | Infill | Ragione |
|---|---|---|---|
| Massima resistenza con minimo materiale | 4–6 | 20% | Le pareti esterne sono continue e isotropiche nel piano XY |
| Resistenza uniforme 3D | 3 | 40% | Equilibrio tra skin e struttura interna |
| Velocità massima (prototipazione) | 2 | 10% | Accettabile per modelli usa e getta |
| Pezzi solidi standard | 3 | 15% Gyroid | Impostazione di default ragionevole |

---

## Checklist Pre-export per Modelli Alleggeriti

- [ ] Se usato Solidify: spessore ≥ 1.2 mm (3 perimetri con 0.4mm nozzle)
- [ ] Se usato Boolean Difference: mesh risultante è manifold (verificare con `mesh_quality_assessment`)
- [ ] Pareti sottili identificate con 3D Print Toolbox (scene.print_3d.thickness_min)
- [ ] Orientamento ottimizzato per non avere pareti sottili in direzione Z (più fragili)
- [ ] Infill scelto in Bambu Studio in base all'uso finale

---

## Relazioni con altri doc KB

- `modifiers_generate.md` → Solidify dettagliato con tutti i parametri
- `mesh_repair.md` → Boolean Difference può introdurre non-manifold, repair successivo
- `workflow_patterns.md` → Solidify nel contesto della pipeline completa
- `bambu_studio_settings.md` → configurazione infill density/pattern da slicer
- `fdm_printing_constraints.md` → spessori minimi pareti per nozzle 0.4mm
