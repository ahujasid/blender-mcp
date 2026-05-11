# Bambu Lab A1 — Costanti fisiche deterministiche

Fonte: ricerca tecnica "Analisi Deterministica dei Parametri Fisici e Cinematici per l'Ecosistema Bambu Lab A1 e Studio".
Uso: progettazione CAD a monte (dimensionamento fori, tolleranze di accoppiamento, layer height valido, keep-out zones) e calibrazione slicer.

Questo file raccoglie i valori fisici *certi* derivati da meccanica, cinematica e reologia della A1. Complementa `fdm_printing_constraints.md` (limiti di stampabilità generici FDM) con le costanti specifiche dell'hardware.

---

## 1. Risoluzione asse Z e layer height validi

La A1 aziona il piatto tramite motore stepper NEMA standard con vite T8. Costanti:

| Parametro | Valore | Derivazione |
|---|---|---|
| Angolo passo motore | 1.8° | NEMA 17 standard |
| Passi completi per rivoluzione | 200 | 360°/1.8° |
| Lead vite T8 | 8 mm | Multi-start T8 Bambu |
| **Passo fisico minimo Z** | **0.04 mm** | 8/200 |

**Regola operativa:** usare layer height *multipli interi di 0.04 mm* per allineare la testina ai detent fisici del motore. Valori fuori multiplo forzano il driver sul microstepping, dove la coppia di tenuta e l'accuratezza posizionale degradano.

Layer height "benedetti":

| Layer (mm) | Multiplo | Uso |
|---|---|---|
| 0.04 | 1× | Teorico; flusso volumetrico troppo basso per estrusione stabile |
| 0.08 | 2× | "Fine" — lithophane, rilievi ad alto contrasto ottico |
| 0.12 | 3× | "Standard qualità" — dettaglio visivo ottimale |
| 0.16 | 4× | Bilanciato |
| 0.20 | 5× | Standard default |
| 0.24 | 6× | Draft/veloce |
| 0.28 | 7× | Draft massimo (sopra 0.28 limite nozzle 0.4) |

**Per lithophane:** il range valido è **0.08–0.12 mm** con nozzle 0.4. Sotto 0.08 il volume estruso può scendere sotto la soglia di stabilità del sensore di pressione; sopra 0.12 si perde risoluzione ottica.

---

## 2. Geometria nozzle 0.4 mm e larghezza linea

**Default Bambu Studio:** `line_width = 0.42 mm` per nozzle 0.4 mm.

Non è arrotondamento. È scelta reologica deterministica:
- Il filamento fuso in uscita subisce *die swell* (espansione al drop)
- La faccia piatta (land) del nozzle schiaccia il filamento contro il layer sottostante
- Con 0.42 mm di target si ottiene uno "squish" positivo → maggiore area di contatto → adesione inter-linea migliore

Se `line_width = 0.40 mm` esatti, la sovrapposizione tra linee adiacenti è marginale e aumenta il rischio di vuoti microscopici e delaminazione.

**Range valido spessore parete singola linea (PLA, nozzle 0.4):**

| Larghezza linea | Effetto |
|---|---|
| < 0.30 mm | Tensione superficiale frammenta la linea, fedeltà persa |
| 0.30–0.42 mm | OK per pareti singole sottili |
| 0.42 mm | Default raccomandato |
| 0.42–0.60 mm | OK, richiede controllo flusso |
| > 0.60 mm | Rigonfiamenti laterali, nozzle non appiattisce uniformemente |

**Regola CAD:** lo spessore parete del modello deve essere un multiplo intero della `line_width` scelta. Altrimenti lo slicer ricorre a *gap filling* (euristico, artefatti superficiali, vibrazioni). Vedi anche `fdm_printing_constraints.md` per la regola "between 1–2 perimeters = not printable".

---

## 3. Sistema di coordinate e zone di esclusione

**Origine coordinate mondo:** angolo **anteriore sinistro** del piatto (non centro).

### Keep-out zones operative

Anche se il volume pubblicizzato è 256×256×256 mm³, lo spazio utile è inferiore per via di vincoli meccanici.

| Zona | Dimensioni/Posizione | Causa |
|---|---|---|
| **Cutter zone** | 18×28 mm angolo anteriore-sinistro | Meccanismo di taglio filamento: la testina preme su una leva; oggetti in quest'area verrebbero colpiti |
| **Probing point** | X=128, Y=261 (circa retro-centro) | Sensore eddy current del piatto; ostruire = impedisce avvio stampa |
| **Rear clearance** | 140 mm dietro la stampante | Movimento piatto bed-slinger Y; cavo riscaldato soggetto a stress |
| **Front clearance** | ~101 mm davanti | Estensione bed anteriore durante movimento |
| **Z height limit** | ~250 mm standard | Z-hop + sicurezza cutter |

### Implicazione scripting Blender

Quando si posizionano oggetti per l'export verso Bambu Studio, *non* mettere geometria nell'angolo X∈[0,18], Y∈[0,28] (in coordinate piatto mm). Controllo programmatico:

```python
def is_in_cutter_zone(obj_min_x: float, obj_min_y: float) -> bool:
    """Obj min coords in mm, origine = angolo anteriore-sinistro piatto."""
    return obj_min_x < 18.0 and obj_min_y < 28.0
```

Vedi `object_placement_alignment.md` per pattern di posizionamento al piatto.

---

## 4. Tolleranze di accoppiamento PLA (nozzle 0.4, A1)

Valori calibrati dalla community Bambu + profili ufficiali. Usare come offset in design CAD o via XY compensation in slicer.

| Tipo accoppiamento | Gap (mm) | Uso |
|---|---|---|
| **Friction fit** | 0.10 | Montaggio fisso per attrito; richiede flow ratio calibrato |
| **Mechanical slide** | 0.20 | Cerniere print-in-place; gioco minimo senza fondere |
| **Loose fit** | 0.30 | Movimento libero, compensa espansione termica |
| **Press fit** | 0.05–0.08 | Interferenza; post-processing per assemblaggio |

**Compensazione fori:** i fori cilindrici stampati risultano sistematicamente più piccoli del CAD per contrazione centripeta del filamento in raffreddamento. Correzione:
- CAD: aumentare diametro foro di 0.10 mm rispetto al nominale, oppure
- Slicer: `XY Hole Compensation = +0.10 mm`

Vedi `fdm_printing_constraints.md` §tolleranze per i valori generici FDM.

---

## 5. Sbalzi e soglie overhang

Bambu Studio applica "Overhang Slowdown" basato sulla **percentuale di linea sospesa**.

| Angolo (dal piano stampa) | Sovrapposizione layer | Stato |
|---|---|---|
| ≤ 45° | ≥ 50% | Safe senza supporto (PLA) |
| 45–55° | 30–50% | Richiede raffreddamento 100% + slowdown |
| 55–70° | 10–30% | Slowdown drastico (10–30 mm/s); rischio spaghetti |
| > 70° | < 10% | Supporto necessario |

**Trick per overhang critici senza supporto:**
- Aumentare `line_width` esterna a 0.6 mm (maggior massa termica, più area laterale solidificata)
- Ridurre `layer_height` a 0.12 mm (più passate = più ancoraggio laterale)
- Tassativamente fan 100% su perimetri overhang

Vedi `support_strategy.md` per il decision tree completo.

---

## 6. Dinamica e calibrazione

### Accelerazione

- **Massima nominale:** 10000 mm/s²
- **Cinematica bed-slinger:** la massa dell'oggetto si somma al piatto mobile → forze laterali crescono con altezza

**Scaling raccomandato per oggetti alti:** usare Height Range Modifier in Bambu Studio:

| Altezza Z | Max accelerazione |
|---|---|
| 0–50 mm | 10000 mm/s² |
| 50–100 mm | 6000 mm/s² |
| 100–150 mm | 4000 mm/s² |
| > 150 mm | 2000 mm/s² |

Scopo: minimizzare momento torcente su base → evitare ringing + distacco.

### Flusso volumetrico

- **Max nominale:** 28 mm³/s (PLA)
- **Operativo raccomandato:** 60–70% = 17–20 mm³/s per qualità superficiale costante
- **Relazione temperatura:** velocità alte richiedono temperatura alta (fino a 230 °C PLA) per garantire fusione completa nel breve tempo di permanenza in zona riscaldata

### Pressure advance

Calibrato automaticamente dalla A1 estrudendo linea di test e leggendo sensore di forza. Effetti:
- **PA troppo basso:** angoli arrotondati, "bleeding" in esterni
- **PA troppo alto:** rigonfiamenti all'inizio linea, punti di partenza evidenti

Va ricalibrato a ogni cambio filamento (marca diversa o tipo diverso).

---

## 7. Gestione termica

### Temperatura ugello vs velocità

PLA range operativo: 200–230 °C. Regola lineare approssimata:

```
T_nozzle ≈ 200 + 0.005 × v_mm_s      # semi-empirico, PLA generico
```

### Cooling dinamico

La ventola componenti è a loop chiuso. Per strati con tempo totale < 4–8 s la stampante **riduce velocità automaticamente** per dare tempo al layer di raffreddarsi sotto T_g (≈ 60 °C per PLA) prima del successivo.

Implicazione CAD: modelli con punte sottili o torri piccole beneficiano di design con `minimum_layer_time` esplicito (valore slicer) oltre al dimensionamento nativo.

---

## 8. Coefficienti di espansione / ritiro

Valori tipici (riferimento per tolleranze CAD):

| Materiale | Ritiro lineare | Implicazione |
|---|---|---|
| PLA | ~0.2–0.3% | Parti funzionali: design nominale, compensazione minima |
| PETG | ~0.5% | Fori più piccoli, aggiungere +0.15 mm |
| ABS | ~0.8% | Non raccomandato A1 (camera aperta) |
| TPU | ~1–2% (variabile) | Dimensioni imprevedibili, test fisico obbligatorio |

---

## Sintesi operativa: le 8 costanti da ricordare

1. **Passo Z:** 0.04 mm → layer valido = multiplo intero
2. **Linea default:** 0.42 mm per nozzle 0.4
3. **Origine coordinate:** angolo anteriore-sinistro
4. **Cutter zone:** X<18, Y<28 mm (no geometria)
5. **Probing:** (X=128, Y=261) non ostruire
6. **Rear clearance:** 140 mm dalla parete
7. **Fits PLA:** 0.1 fisso / 0.2 slide / 0.3 libero
8. **Flow max operativo:** 17–20 mm³/s (70% di 28)

---

## Approfondimenti deep research (2024-2026)

### Bedslinger I_eff(Z) — rationale per la tabella accelerazione

La tabella `accel max vs Z` (10000 → 6000 → 4000 → 2000 mm/s² a Z = 0/50/100/150 mm) segue il **teorema dell'asse parallelo**: l'inerzia effettiva dell'asse Y (= bed) cresce col quadrato della distanza Z dell'oggetto stampato.

```
I_eff(Z) = I_bed + m_part × Z²
f_res = √(k / I_eff)
```

L'**input shaping è calibrato a piatto vuoto** (`Z=0`), per-asse X e Y separatamente. A `Z=150mm` con oggetto da 200g, `f_res` può scendere da 50Hz a 25Hz — fuori dalla banda dello shaper → invece di cancellare le vibrazioni, le **inietta**.

**Implicazione operativa**:
- Su moves diagonali (X+Y simultanei), accel = `min(accel_X, accel_Y)`. X e Y hanno shaper a frequenze diverse, il più basso vince.
- Modelli wide+short (low aspect ratio, low Z) → resta vicino al `accel` baseline.
- Modelli tall+thin (high aspect ratio, high Z) → degradano rapidamente: spesso il vincolo è `accel` non MVS.
- Schedule rampa: oggetto >100mm con `aspect_ratio > 4` → assert max `accel = 4000 mm/s²` per evitare ringing visibile sotto i 30mm dal top.

### Compensazione fori scalata (1/r law)

La regola tabellare `+0.10mm hole comp` è la **media** per fori 5–10 mm. La fisica reale (PLA contrazione 0.2–0.3%, materiale concentrato sul lato concavo dell'arco) dà compensation che scala come `1/r`:

| Diametro nominale | Errore reale tipico | Compensazione CAD consigliata |
|---|---|---|
| Ø2 mm | ~0.35 mm | +0.30 mm (foro CAD 2.30) |
| Ø3 mm (M3 clearance) | ~0.25 mm | +0.25 mm |
| Ø5 mm | ~0.20 mm | +0.20 mm |
| Ø10 mm | ~0.10 mm | +0.10 mm (Bambu default OK) |
| Ø20 mm | ~0.05 mm | +0.05 mm |
| Ø30+ mm | ~0.03 mm | trascurabile |

Per fori inferiori a Ø2mm: spesso **non stampare il foro**, stampa pieno + foratura post (drill bit standard è più preciso del nozzle 0.4mm sotto Ø2mm).

Riferimento: [fdm_printing_constraints] §P5.

### Flow rate ceiling — chiarimento

Constante #8 sopra dice "17–20 mm³/s operativo" (70% di 28). Il valore preciso varia per filament:

| Filament class | Flow ceiling realistico A1 (mm³/s) |
|---|---|
| Bambu Basic PLA (QA controlled) | 21 (default profile) |
| Bambu PLA Matte | 18 |
| Bambu PLA Silk | 14 |
| Bambu PLA Marble / Glitter | 12 |
| PolyTerra PLA / PolyLite | 22 |
| Sunlu PLA Meta @ 230°C | 24 |
| **Generico PLA (sconosciuto)** | **12 baseline, calibra incrementale** |
| PETG (raro su A1 no enclosure) | 14 |

Il **28 mm³/s** è il limite hardware (nozzle + hotend thermal capacity). Il **realistico** dipende da filament + temp + cooling. Vedi [mvs_filament_table] nel sub-KB Bambu per tabella estesa community-validated.

### Cross-reference

- [fdm_printing_constraints] §Why these numbers — physics basis per P1–P7
- [Bambu Wiki/mvs_filament_table] — tabella community per filament
- [Bambu Wiki/a1_field_kit] — quirks A1 specifici non in docs ufficiali
- [orientation_strategy] §Migliorie — accel scaling per acceleration-aware orientation

Questi valori, se rispettati, sostituiscono l'approccio empirico "trial-and-error" con design deterministico pronto alla stampa.
