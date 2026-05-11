# Tolerances and Fits — Accoppiamenti Dimensionali PLA su Bambu A1

Valori misurati e configurazione slicer per ottenere press-fit, slip-fit e running-fit con PLA su Bambu A1 + nozzle 0.4mm.

---

## Precisione di Base del Sistema A1

| Sistema | Precisione tipica |
|---|---|
| Entry-level FDM | ±0.20–0.50 mm |
| Bambu A1 (default) | ±0.10–0.20 mm |
| Bambu X1C (LIDAR) | ±0.05–0.10 mm |
| FDM industriale / SLA | ±0.025–0.05 mm |

La A1 raggiunge ±0.10 mm grazie a Pressure Advance attivo e vibration compensation. Questa è la baseline *prima* di qualsiasi compensazione software.

---

## Perché i Fori Escono Sempre Più Piccoli

Tre meccanismi concorrenti riducono sistematicamente il diametro dei fori stampati:

1. **Poligonalizzazione** — STL approssima i cerchi con segmenti poligonali: la corda è sempre più corta dell'arco
2. **Filament tension / "corner cutting"** — il filamento fuso è tirato verso il centro dell'arco durante la deposizione
3. **Die swell** — il materiale espandendosi radialmente entra nel vuoto del foro

Risultato empirico su A1 con PLA: fori verticali (asse Z) escono **0.1–0.3 mm più piccoli** rispetto al CAD.

---

## Compensazioni in Bambu Studio (Quality → Precision)

### XY Hole Compensation (fori interni)
- Positivo (+0.1 mm) = sposta il toolpath verso l'esterno → aumenta il diametro di 0.2 mm (è un raggio)
- Default A1: 0 mm → aggiungere **+0.1 mm** come punto di partenza per parti funzionali

### XY Contour Compensation (pareti esterne)
- Negativo (−0.1 mm) = riduce le dimensioni esterne
- Default A1: 0 mm → aggiungere **−0.05 a −0.1 mm** per parti che devono incastrarsi in cavità

> **Critica**: non usare "XY Size Compensation" globale (presente in slicer legacy) — agisce su tutto indiscriminatamente. Hole e Contour devono essere indipendenti.

### Shrinkage Compensation (filament profile)
Formula: `Sc = (Dm / Dd) × 100`
- Dm = dimensione misurata del pezzo stampato
- Dd = dimensione CAD
- PLA standard: 0.2–0.5% di shrinkage → valore tipico nel profilo 99.5–99.8%

---

## Tabella Fit — Clearance Consigliata in CAD (PLA A1)

| Tipo di Fit | Clearance CAD | Con compensazione (+0.1H /−0.1C) | Risultato fisico |
|---|---|---|---|
| Interference (press tight, mallet) | −0.2 mm | −0.2 mm | Richiede forza + mazza |
| Light press fit | 0 mm (line-to-line) | 0 mm | Snug, richiede forza manuale |
| Snug fit (assemblaggio preciso) | +0.1 mm | +0.1 mm | Attrito, si smonta a mano |
| Slip fit (assemblaggio / smontaggio) | +0.2–0.3 mm | +0.2 mm | Scorrevole, nessun gioco |
| Running fit (rotazione) | +0.3–0.5 mm | +0.3 mm | Rotazione libera |
| Clearance ampia | +0.4+ mm | +0.4 mm | Gioco percepibile |

**Baseline A1 non calibrata**: il "clearance floor" (minimo per non fusione tra pezzi print-in-place) è **0.20–0.25 mm**.

---

## Tabella Empirica — A1 Default vs Calibrata

| Clearance CAD | A1 Default | A1 Calibrata (+0.1H/−0.1C) |
|---|---|---|
| 0.05 mm | ❌ Fuso/bloccato | ❌ Fuso/bloccato |
| 0.10 mm | ❌ Fuso/bloccato | ❌ Fuso/bloccato |
| 0.15 mm | ❌ Richiede forza eccessiva | ✅ Snug, forza iniziale |
| 0.20 mm | ❌ Scorre con difficoltà | ✅ Slip fit scorrevole |
| 0.25 mm | ✅ Con forza manuale | ✅ Slip libero |
| 0.30 mm | ✅ A mano | ✅ Free movement |
| 0.40 mm | ✅ Gioco | ✅ Gioco udibile |

---

## Caso Speciale: Bearing 608 (skateboard bearing)

Il 608 ha diametro esterno 22.0 mm. Su A1:
- Design a 22.0 mm → uscirà ~21.85–21.9 mm → serraggio eccessivo
- **Press fit permanente**: design a 22.1 mm + XY Hole Compensation +0.05 mm
- **Fit rimovibile (a mano)**: design a **22.2–22.3 mm**
- **Slip libero**: design a 22.4 mm

---

## Altri Parametri Slicer che Influenzano le Tolleranze

### Wall Order: Outer Wall First
- "Inner-Outer" (default): la parete interna spinge leggermente quella esterna → esterne oversized
- **"Outer-Inner"**: la parete esterna viene depositata per prima, senza interferenze → dimensioni più accurate per parti meccaniche

### Elephant's Foot Compensation
- L'A1 usa 0.15 mm di default
- Per parti di assemblaggio verticale: aumentare a **0.15–0.20 mm** + aggiungere chamfer 0.5 mm alla base del modello in CAD

### Scarf Seam e Z-Seam
La seam (punto di inizio/fine layer) genera un piccolo blob. Non posizionarla su superfici di accoppiamento. Usare `Seam position = Back` o `Aligned` per controllarne la posizione.

### Slice Gap Closing Radius e Resolution
Per fori piccoli e curve precise (Quality → Precision):
- Resolution: 0.012 mm (da default 0.025 mm)
- Gap closing radius: 0.049 mm
Aumenta il numero di segmenti per cerchio → fori più rotondi.

---

## Misurazione: Caveat sui Calibri

I calibri digitali su fori interni FDM sottostimano sistematicamente di **0.05–0.1 mm** (le punte non seguono il centro del cerchio). Per validazione ingegneristica:
- Usare **pin gauge** (cilindri di precisione) per trovare il diametro funzionale massimo
- Per fori di allineamento: test fisico di accoppiamento è più affidabile del calipro

---

## Design Best Practice

1. **Chamfer alla base**: 0.5 mm chamfer al fondo di pin e dovetail per bypass del Elephant's Foot
2. **Nessuna feature critica al primo layer**: la prima layer è overextruded per adesione → evitare fori e snap alla quota Z=0
3. **Orientamento fori verticale**: fori con asse parallelo a Z sono più rotondi di quelli orizzontali (che escono "a D" per gravitational sag)
4. **Test di tolleranza prima del definitivo**: stampare un gauge 9.8–10.4 mm a step 0.1 mm per caratterizzare la specifica bobina + macchina

---

## Relazioni con altri doc KB

- `bambu_studio_settings.md` → XY Hole/Contour Compensation dettagliati
- `design_rules_fdm.md` → regole geometriche base
- `assembly_design.md` → snap-fit, dovetail, pin con tolleranze applicative
- `threads_and_fasteners.md` → fori per viti e inserti con clearance specifici
