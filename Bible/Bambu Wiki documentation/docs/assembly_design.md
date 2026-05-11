# Assembly Design — Progettazione per Assemblaggio FDM PLA

Design di giunzioni meccaniche stampabili in FDM PLA: snap-fit, dovetail, registration pin, living hinge. Valori quantitativi e best practice.

---

## Proprietà Meccaniche PLA FDM (Baseline)

| Proprietà | Valore |
|---|---|
| Tensile Modulus (Young's) | 3500–3600 MPa |
| Yield Strength | 60 MPa |
| Elongation at Break | 3–8% |
| Flexural Modulus | 3800 MPa |
| Flexural Strength | 83 MPa |
| Shrinkage | 0.2–0.4% |

**Critico**: PLA è fragile (elongazione bassa). Non progettare snap-fit che richiedono deflessioni elevate. Usare safety factor 1.5–2.0× sui valori.

### Anisotropia — Resistenza per Asse di Stampa

| Orientamento | Resistenza relativa | Failure mode |
|---|---|---|
| Y-axis (filamenti paralleli al carico) | Massima | Frattura del polimero |
| X-axis | Intermedia | Delaminazione parziale |
| Z-axis (filamenti perpendicular al carico) | **−20–30% tensile, −50% elongation** | Separazione layer |

**Regola**: qualsiasi feature che deve flettersi (snap-fit, living hinge) deve essere orientata in modo che il carico di flessione agisca LUNGO il percorso del filamento, mai attraverso i layer.

---

## 1. Snap-Fit — Cantilever

### Formula Deformazione Massima (Modified Beam Theory)

$$\epsilon = \frac{1.5 \cdot t \cdot Y}{L^2 \cdot Q}$$

Dove:
- `ε` = strain alla radice (max 4–8% PLA singolo uso, max 2–4% riuso)
- `t` = spessore braccio alla radice (mm)
- `Y` = deflessione necessaria = profondità undercut (mm)
- `L` = lunghezza braccio (mm)
- `Q` = deflection-magnification factor (vedi tabella sotto)

**Fattore Q** (compensa la compliance della parete di attacco):

| Aspect ratio L/t | Q (blocco solido) | Q (parete sottile) |
|---|---|---|
| 2.0 | ~1.6 | ~2.5 |
| 4.0 | ~1.3 | ~1.8 |
| 8.0 | ~1.1 | ~1.3 |
| ≥10.0 | ~1.0 | ~1.1 |

Per PLA in Z-axis: ridurre la strain ammissibile del **50%** (1–2% max).

### Forza di Accoppiamento

$$P = \frac{b \cdot t^2 \cdot E \cdot \epsilon}{6 \cdot L}$$
$$W = P \cdot \left[\frac{\mu + \tan\alpha}{1 - \mu \cdot \tan\alpha}\right]$$

- `b` = larghezza braccio (mm)
- `E` = modulo elastico (3500 N/mm² per PLA FDM)
- `μ` = coefficiente attrito plastica-plastica = 0.3–0.6 (FDM è ruvido → 0.5)
- `α` = angolo lead-in = 30° standard, angolo di ritenzione = 45–90°

### Design Pratico Snap-Fit PLA

| Parametro | Valore consigliato |
|---|---|
| Strain massima (uso singolo) | 4–6% |
| Strain massima (riuso frequente) | 2–3% |
| Strain massima (asse Z) | 1–2% |
| Angolo lead-in | 30° (facile assemblaggio) |
| Angolo di ritorno (ritenzione permanente) | 90° |
| Angolo di ritorno (disassemblabile) | 30–45° |
| Undercut depth (Y) | 0.5–1.5 mm |
| Perimetri attorno alla radice | ≥4 |

---

## 2. Dovetail Joints

Ideali per connettere parti troppo grandi per il volume di stampa. Il profilo a coda di rondine blocca meccanicamente su 1–2 assi.

### Geometria Consigliata

| Parametro | Valore |
|---|---|
| Angolo dovetail | 60–65° (auto-supportante senza supporti) |
| Clearance standard | 0.1–0.2 mm |
| Tight / interference fit | 0.05–0.1 mm |
| Sliding / modular | 0.3–0.5 mm |
| Chamfer sugli spigoli vivi | 0.5 mm (evita blob da overextrusion) |

**Slicer: Outer Wall First** per migliore accuratezza dimensionale sulle superfici di accoppiamento.

**Attenzione pareti multiple**: con 4–6 perimetri la larghezza cumulativa può chiudere il gap del dovetail. Testare con gauge prima del pezzo definitivo.

---

## 3. Registration Pins e Fori di Allineamento

### Fit per Diametro Pin vs Foro

| Applicazione | Relazione pin/foro |
|---|---|
| Metal pin light press fit | Foro CAD = pin −0.1 mm |
| Printed pin snug fit | Foro CAD = pin +0.1–0.2 mm |
| Free sliding / pivot | Foro CAD = pin +0.3–0.4 mm |
| Medium press fit (mallet) | Foro CAD = pin −0.2–0.4 mm |
| Tight press fit (vice) | Foro CAD = pin −0.4–0.6 mm |

**Regola "Hole Undersize"** (vedi anche `tolerances_and_fits.md`):
- Fori verticali (asse Z): −0.1–0.3 mm rispetto al CAD → compensare con +0.2 mm nel modello
- Fori orizzontali: sagging sulla volta superiore → forma "a D" → preferire fori verticali per alta precisione

**Configurazione hole-and-slot**: usa un foro circolare su un lato e un foro oblong (slot) sull'altro per evitare overconstrained geometry tra due pin.

---

## 4. Living Hinge (Cerniere Flessibili)

| Parametro | Valore PLA FDM |
|---|---|
| Spessore | 0.5–0.8 mm |
| Larghezza (asse della cerniera) | ≥ 5 mm |
| Orientamento stampa | Asse flessione nel piano XY (non in Z) |
| Cicli max PLA | 20–50 (fragile) — preferire PETG o TPU |

**PLA per living hinge**: sconsigliato per uso intensivo. Accettabile per aperture occasionali (contenitori, coperchi).

---

## 5. Lead-in, Chamfer, Fillet — Contrastare l'Elephant's Foot

Il primo layer FDM è overextruded per adesione al letto → espansione alla base (Elephant's Foot) di ~0.2–0.5 mm.

Soluzioni:
- **Chamfer 0.5–1.0 mm alla base** di pin, dovetail tail, qualsiasi feature che deve incastrarsi in un foro → bypassa i layer espansi
- **Fillet alla radice degli snap-fit** ≥ 0.6 mm → distribuisce lo stress e riduce l'intaglio
- **Elephant's Foot Compensation**: 0.15 mm default A1, aumentare a 0.20 mm per parti di assemblaggio

---

## 6. Infill per Giunzioni

Le giunzioni meccaniche richiedono pareti solide, non infill denso:

- **Snap-fit root e boss**: ≥4 perimetri (solid shell, indipendente dall'infill del corpo)
- **Press-fit housing**: ≥4 perimetri, Gyroid 40% per resistenza radiale
- **Dovetail surface**: Outer Wall First, 3–4 perimetri per accuratezza
- **General assembly**: 3 perimetri + Grid/Cubic 40% è il baseline ragionevole

Aumentare infill sopra 40–60% ha rendimenti decrescenti. È più efficace aumentare i perimetri.

---

## 7. Adesivi per Giunzioni Permanenti

| Adesivo | Forza | Quando usarlo |
|---|---|---|
| **Cianoacrilato (CA gel)** | Fragile, break on impact | Solo giunzioni statiche decorative |
| **Epossidico bicomponente** | Alta resistenza, rigido | Giunzioni permanenti strutturali |
| **Solvent welding DCM** | Massima, monolitica | Unione parti PLA grandi (fume hood!) |
| **Friction welding** | Strutturale | Sezioni grandi senza prodotti chimici |

PLA è poroso (gaps tra layer) → adesivi a bassa viscosità penetrano nella parte. Usare gel (alta viscosità) per giunzioni di superficie. Prima applicazione → seconda applicazione dopo assorbimento.

---

## 8. Calibrazione Prima dell'Assemblaggio Definitivo

1. **Tolerance Gauge**: stampare una serie pin+fori da 0.05 a 0.5 mm di gap → identificare il "satisfying click" e il "free slide" specifici per la propria macchina + bobina
2. **Shrinkage test**: blocco 100 mm → misurare → calcolare shrinkage % → applicare come scaling nel slicer
3. **Hole gauge**: fori da 9.8 a 10.4 mm (step 0.1) → trovare il sistematico undersizing

---

## Relazioni con altri doc KB

- `tolerances_and_fits.md` → clearance numerica per ogni tipo di fit
- `threads_and_fasteners.md` → fissaggi filettati da integrare nell'assieme
- `design_rules_fdm.md` → geometrie FDM base (overhang, spessori)
- `slicing_profiles.md` → profilo "Parte Funzionale" per parti di assemblaggio
- `hollowing_and_lightening.md` → Wall Count vs Infill per le giunzioni
