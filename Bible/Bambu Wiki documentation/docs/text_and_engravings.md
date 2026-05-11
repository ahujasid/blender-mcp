# Text and Engravings — Testo e Incisioni FDM PLA

Dimensioni minime, profondità, font e orientamento per testo leggibile su PLA con nozzle 0.4mm su Bambu A1.

---

## Limiti Fisici — Nozzle 0.4mm

| Parametro | Valore |
|---|---|
| Larghezza minima stroke | 0.40–0.48 mm (nozzle ± die swell) |
| Altezza minima font leggibile | **≥ 4 mm** |
| Feature minima assoluta | 0.8 mm (2 perimetri) |
| Layer height ottimale per testo Z | 0.12–0.16 mm (multiple di 0.04 = "magic numbers") |
| Die swell espansione | +0.1–0.2 mm per lato → ingresso nei counter delle lettere |

---

## Tabella Font Size vs Risultato

| Altezza lettera | Stroke width approx. | Risultato |
|---|---|---|
| < 3 mm | < 0.35 mm | ❌ Illeggibile — segmenti mancanti |
| 4 mm | ~0.45 mm | ✅ Leggibile con font bold sans-serif |
| 6 mm | ~0.70 mm | ✅ Molto chiaro, 2 perimetri per stroke |
| ≥ 10 mm | ≥ 1.0 mm | ✅ Alta fedeltà, infill possibile per lettere piene |

Per testo < 4 mm: necessario nozzle 0.2mm **oppure** orientamento verticale (asse Z con layer height come pixel).

---

## Scelta del Font

### Raccomandati (FDM-safe)
- **Arial Black**, **Liberation Sans Bold**, **Gotham Black** — stroke uniforme, sans-serif
- **Open Sans Bold** — buon contrasto a 4 mm
- Font geometrici senza grazie (Futura, Helvetica Neue Bold)

### Da Evitare
- **Serif** (Times, Garamond): le grazie sono < 0.3 mm → mancano in stampa
- **Script / Corsivo**: tratti variabili, molti angoli acuti → illeggibile sotto 10 mm
- Font "thin" o "light": stroke < 0.4 mm → non estruso

---

## Emboss vs Deboss — Scegliere

| Tipo | Altezza/Profondità consigliata | Pro | Contro |
|---|---|---|---|
| **Emboss** (rilievo) | 0.4–0.6 mm altezza | Più facile da stampare, leggibile | Fragile se sottile, può shear |
| **Deboss** (incisione) | 0.4–0.6 mm profondità | Protetto da abrasione, elegante | "Isole" nelle lettere problematiche |

### Regola Emboss
- Altezza ≤ 1.0 mm → fillet/chamfer alla radice ≥ 0.6 mm per resistenza
- Altezza > 1.0 mm → fragile per stroke sottili. Preferire deboss.

### Regola Deboss — Il Problema delle Isole
Le lettere **A, B, D, O, P, Q, R** hanno "isole" (pilastri interni). In deboss queste isole devono essere ≥ 0.8–1.0 mm di larghezza per essere ancorate da ≥2 perimetri. Isole più piccole: si staccano durante la stampa.

**Soluzione**: usare **stencil font** che collegano le isole al corpo della lettera.

---

## Orientamento — Come Posizionare il Testo

### Testo Orizzontale (top face, parallelo al letto)

Standard. Usa la risoluzione XY (nozzle).

- Font stroke deve essere ≥ 0.45 mm
- Su superfici curve/inclinate → staircase effect visibile → usare layer height 0.08–0.12 mm
- Posizione ideale: faccia perfettamente orizzontale

### Testo Verticale (side wall)

Usa la risoluzione Z (layer height). Può essere più fine in verticale.

- Consigliato per Braille e testo tattile → layer sovrapposti creano dot più lisci
- Testo verticale = micro-overhangs → per proiezioni > 0.5 mm aggiungere taper 45° alla base
- Layer height 0.12 mm → risoluzione verticale 0.12 mm (più fine del nozzle 0.4 mm)

### Testo sul Fondo (bottom face)

- **Elephant's Foot compensation obbligatoria** — senza compensazione il primo layer riempie le lettere debossate
- Consigliato per articoli con testo di identificazione (serial number, produttore)

---

## Tabella Orientamento Consigliato

| Tipo testo | Orientamento | Note |
|---|---|---|
| Logo decorativo, titolo | Orizzontale (top) | Colori multipli via filament change |
| Etichette funzionali | Verticale (side) | Più durevole, leggibile da lontano |
| Testo tattile / Braille | Verticale (side) | Qualità superficiale superiore |
| Numerazione seriale | Bottom | Nascosto, richiede Elephant's Foot comp |

---

## Impostazioni Slicer per Testo

### Arachne vs Classic Wall Generator
- **Classic**: larghezza linea fissa → stroke sottili saltati o coperti con Gap Fill
- **Arachne**: larghezza variabile → adatta la bead ai tratti sottili del font → significativamente migliore per testo

**→ Sempre Arachne per modelli con testo.**

### Ironing (Top Surface)
Attivare per testo embossato su superfici superiori:
- Flow rate 10%, alta velocità → fonde e livella i picchi dei layer
- Risultato: superficie lucida, contrasto migliorato tra testo e fondo

### Retraction e Z-hop per Testo Piccolo
Testo piccolo = molte interruzioni e ripartenze della traccia:
- Retraction A1 (direct drive): 0.8 mm
- **Z-hop**: attivare durante travel su testo embossato → evita che il nozzle abbatta le lettere durante i movimenti

### Velocità Outer Wall su Testo
- 20–25 mm/s per lettere ≤ 6 mm → angoli netti, extrusion consistente
- Troppo veloce → over/under extrusion agli angoli → lettere deformate

---

## Multi-Color via Filament Change

Per testo a contrasto (es. lettere bianche su sfondo nero):

1. **Testo embossato di 1–2 mm**: progettare testo come body separato alto 1–2 mm sopra la superficie base
2. In Bambu Studio: impostare cambio filamento all'altezza del testo
3. Il corpo base stampa in colore 1, le lettere stampano in colore 2

Profondità minima per cambio pulito: **1.0 mm** → assicura che il colore precedente non "sanguini" attraverso i pochi layer di interfaccia.

---

## Multi-Color per Deboss

Per lettere incise a colori:
1. Deboss di 1.0–1.5 mm
2. Stampare il modello
3. Riempire manualmente le lettere con resina UV colorata → cure con lampada UV

Alternativa: paint the recesses con brush acrilico dopo post-processing.

---

## Considerazioni Speciali per Bambu Studio v2.x

- **Scarf Seam**: nelle lettere, la seam distribuita riduce il blob visibile all'inizio di ogni perimetro
- **Precise Wall**: migliora la fedeltà geometrica dei tratti variabili → meglio abbinato ad Arachne
- **Smooth Overhang Speed**: per testo embossato su superfici inclinate → gradiente di velocità evita artefatti

---

## Limiti Rispetto ad Altre Tecnologie

| Tecnologia | Min stroke | Min depth |
|---|---|---|
| FDM 0.4mm (ben calibrato) | 0.40 mm | **0.40 mm** |
| FDM 0.2mm | 0.20 mm | 0.20 mm |
| MJF industriale | 0.50 mm | 0.80–1.0 mm |
| SLA/MSLA | 0.10 mm | 0.10 mm |

FDM con 0.4mm è competitivo con MJF sulla profondità minima, ma non sulla risoluzione XY.

---

## Quick Reference — Parametri Operativi

```
Font:              Bold sans-serif (Arial Black, Gotham, Liberation Sans)
Altezza minima:    4 mm (nozzle 0.4mm)
Emboss height:     0.4–0.6 mm
Deboss depth:      0.4–0.6 mm
Isole lettere:     ≥ 0.8–1.0 mm larghezza
Wall generator:    Arachne
Outer wall speed:  20–25 mm/s per testo fine
Layer height:      0.12–0.16 mm per dettaglio massimo
Z-hop:             Attivo
Ironing:           Attivo per emboss su top face
```

---

## Relazioni con altri doc KB

- `design_rules_fdm.md` → feature minima 0.8 mm con nozzle 0.4mm
- `bambu_studio_settings.md` → Arachne, Ironing, Scarf Seam
- `slicing_profiles.md` → profilo Miniatura per alta risoluzione
- `orientation_strategy.md` → posizionamento modello per ottimizzare dove cade la superficie testuale
