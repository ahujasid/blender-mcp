# Support Strategy — Quando e Come Usare i Supporti FDM

Documento operativo per decidere se un modello richiede supporti, quale tipo usare e come configurarli in Bambu Studio per PLA su Bambu A1.

---

## Principio Base

I supporti FDM sono strutture temporanee stampate sotto le aree del modello che non possono auto-supportarsi. L'obiettivo non è eliminarli sempre, ma ridurli al minimo tramite orientamento intelligente, e quando servono configurarli per essere rimovibili con il minor danno alla superficie.

---

## Quando Servono i Supporti (Decision Tree)

### Passo 1 — Identificare le aree critiche

Un'area richiede supporti se soddisfa ENTRAMBE queste condizioni:
- La normale alla faccia punta verso il basso (componente Z negativa)
- L'angolo dalla verticale è **> 45°** (con buon cooling) oppure **> 60°** (con cooling ottimizzato)

Verifica programmatica in Blender:
```python
import bpy
import bmesh
import math
import mathutils

def detect_overhang_faces(obj_name, threshold_deg=45.0):
    """
    Restituisce lista di facce che richiederebbero supporti.
    Threshold_deg = angolo dalla verticale oltre il quale serve supporto.
    """
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        return []
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = obj_eval.to_mesh()
    
    threshold_rad = math.radians(threshold_deg)
    up = mathutils.Vector((0, 0, 1))
    
    overhang_faces = []
    total_area = 0.0
    overhang_area = 0.0
    
    for poly in mesh.polygons:
        normal = (obj_eval.matrix_world.to_3x3() @ poly.normal).normalized()
        total_area += poly.area
        
        # Angolo tra normale e up
        angle_from_up = normal.angle(up)  # 0=tetto, π=pavimento, π/2=parete
        
        # Faccia è rivolta verso il basso e supera la soglia di overhang
        if angle_from_up > (math.pi - threshold_rad):
            overhang_faces.append({
                "center": list(poly.center),
                "area_mm2": poly.area * 1e6,
                "angle_from_up_deg": math.degrees(angle_from_up)
            })
            overhang_area += poly.area
    
    obj_eval.to_mesh_clear()
    
    print(f"Overhang analysis (threshold={threshold_deg}°):")
    print(f"  Facce in overhang: {len(overhang_faces)}")
    print(f"  Area overhang: {overhang_area*1e6:.1f} mm²")
    print(f"  % su totale: {overhang_area/max(total_area,1e-9)*100:.1f}%")
    
    return overhang_faces
```

### Passo 2 — Valutare se rimuovibile tramite orientamento

Prima di aggiungere supporti, verificare se cambiare l'orientamento (vedi `orientation_strategy.md`) elimina o riduce gli overhang. I supporti hanno sempre costi:
- Tempo di stampa +15–50%
- Materiale extra
- Rischio di danni alla superficie al momento della rimozione
- Post-processing obbligatorio

### Passo 3 — Valutare Bridge

Se l'overhang è un ponte (due lati supportati), verificare la lunghezza del bridge prima di decidere se serve supporto:
- Bridge PLA affidabile su A1: ≤ 30 mm
- Bridge fino a 60 mm: possibile con buon cooling e velocità ridotta (≤ 40 mm/s)
- Bridge > 60 mm: supporto raccomandato

---

## Tipi di Supporto in Bambu Studio

### Normal Support
- Struttura a colonne verticali con pattern interno (zig-zag, grid, ecc.)
- Pro: semplice, prevedibile, facile da configurare
- Contro: difficile da rimuovere in cavità strette, lascia segni sulla superficie
- Quando usarlo: oggetti tecnici dove la superficie di supporto non è visibile

### Tree Support
- Struttura ad albero che cresce dal letto e raggiunge i punti di overhang
- Pro: tocca il modello in meno punti, più facile da rimuovere, meno materiale
- Contro: più lento da calcolare, può essere instabile su modelli molto alti e sottili
- Quando usarlo: figurine organiche, oggetti con superfici visibili importanti

### Support Painting (manuale)
- Si dipinge manualmente dove si vuole/non si vuole il supporto
- Disponibile in Bambu Studio: icona pennello nella toolbar
- Quando usarlo: dopo aver fatto il preview e aver notato che il supporto automatico è sovra/sotto dimensionato

**Strumenti disponibili:**

| Strumento | Comportamento |
|---|---|
| **Sphere Tool** | Colora tutti i facet nel raggio 3D, incluse cavità interne — per geometrie complesse |
| **Fill Tool** | Si propaga sulle facce connesse fino a un angolo soglia (Smart Fill Angle) — un click colora tutta la zona |
| **Gap Fill** | Chiude automaticamente piccoli vuoti tra aree colorate — usa come passo finale per evitare isole non supportate |

**Workflow efficiente:** Auto support → Block Support sulle zone esteticamente critiche → Enforce Support sui bridge reali → Gap Fill → preview → verifica.

---

## Parametri Chiave Bambu Studio per Supporti PLA/A1

| Parametro | Valore consigliato | Note |
|---|---|---|
| Support type | Tree (normal) | Per figurine organiche usare Tree |
| Threshold angle | 45° | Default A1 con PLA standard |
| Support top Z distance | 0.20 mm (1 layer) | Distanza tra supporto e superficie modello |
| Support bottom Z distance | 0.20 mm | Distanza tra letto e base supporto |
| Support interface layers | 2–3 | Layer di interfaccia più densi per superficie migliore |
| Interface pattern | Grid | Più resistente, ma più difficile da rimuovere |
| Interface spacing | 0.2 mm | Distanza linee interfaccia — più piccola = migliore superficie ma più difficile rimozione |
| Support infill density | 15–25% | Bassa densità per risparmio materiale |
| Support pattern | Zig-zag | Più facile da rimuovere rispetto a Grid |
| Remove small overhangs | On | Elimina piccoli supporti inutili |

**Nota critica su Z distance**: il parametro "Support top Z distance" determina la qualità della superficie supportata. Con PLA su A1:
- 0.20 mm (1 layer standard 0.20): distacco facile, superficie accettabile
- 0.15 mm: distacco più difficile ma superficie migliore
- 0.10 mm: quasi fuso al modello, rimozione difficile ma superficie ottima (utile per superfici interne non visibili)

---

## Configurazione da Bambu Studio (passi operativi)

1. **Slice il modello** senza supporti → guarda la preview colorata per overhang (colori caldi = overhang)
2. **Attiva supporti**: `Process → Support → Enable support`
3. **Scegli il tipo**: Normal per tecnico, Tree per organico/figurine
4. **Preview post-supporti**: verifica che i supporti tocchino tutte le aree critiche e non tocchino superfici dove non devono
5. **Usa Support Painting** se ci sono false positivi (supporti su superfici che si supportano da sole) o false negativi
6. **Stima materiale**: confronta il peso stimato con e senza supporti — se > 30% aumento, riconsiderare l'orientamento

---

## Superfici Non Supportabili — Strategie Alternatives

### Overhang frontale di facce organiche (nasi, menti, sopracciglia)
- **Design fix**: aggiungere angolo 45° nella modellazione (se permesso)
- **Orientamento fix**: inclinare leggermente il modello per portare l'overhang sotto i 45°
- **Supporti accettati**: Tree support tocca in modo limitato, leggibile nella preview

### Buchi orizzontali (fori passanti in direzione Z)
- Buchi ≤ 10 mm di diametro: non servono supporti (bridge corto)
- Buchi 10–30 mm: bridge con supporto solo ai bordi (droop accettabile < 1 mm)
- Buchi > 30 mm: ruotare il modello per orientare i buchi in direzione XY

### Superfici piane orizzontali a quota intermedia (shelf)
- Inevitabilmente richiedono supporti se l'area è > 4×30 mm
- Usare "Normal support" con interface layers 3 + interface spacing 0.15 mm per superficie pulita
- Post-processing: sanding con grit 220+ dopo rimozione supporti

---

## Stima Impatto Supporti

```python
def estimate_support_impact(overhang_area_mm2, support_density=0.20):
    """
    Stima approssimativa del materiale aggiuntivo per i supporti.
    
    overhang_area_mm2: area totale facce in overhang (da detect_overhang_faces)
    support_density: ratio densità supporto (0.15–0.25 per FDM)
    
    Ritorna volume stimato supporti in mm³.
    
    NOTA: stima molto approssimativa — lo slicer è la fonte definitiva.
    """
    # Stima: supporto è alto in media quanto la proiezione Z dell'overhang (euristico)
    # Non calcolabile senza slicing, ma utile per orientamento decisionale
    avg_height_estimate_mm = 20.0  # placeholder
    support_volume = overhang_area_mm2 * avg_height_estimate_mm * support_density
    pla_density_g_mm3 = 1.24e-3  # g/mm³
    print(f"Volume supporti stimato: ~{support_volume:.0f} mm³ (~{support_volume*pla_density_g_mm3:.1f}g PLA)")
    return support_volume
```

---

## Checklist Pre-slicing per Supporti

- [ ] Verificato che l'orientamento sia già ottimizzato (vedi `orientation_strategy.md`)
- [ ] Identificato le aree in overhang > 45° con `detect_overhang_faces()`
- [ ] Verificato se i bridge sono ≤ 30 mm (nessun supporto necessario)
- [ ] Scelto il tipo: Tree per figurine organiche, Normal per tecnico
- [ ] Impostato `support_top_z_distance` appropriato per il finish richiesto
- [ ] Preview fatto con colorazione layer-type attivata in Bambu Studio
- [ ] Stimato incremento di materiale e tempo — se non accettabile, rivedere orientamento

---

## Relazioni con altri doc KB

- `orientation_strategy.md` → ridurre gli overhang prima di aggiungere supporti
- `fdm_printing_constraints.md` → angoli overhang e lunghezze bridge per A1
- `bambu_studio_settings.md` → parametri slicer dettagliati
- `print_quality_issues.md` → problemi tipici legati ai supporti (strapping, surface blemishes)
- `workflow_patterns.md` → sequenza operativa completa import→repair→export
