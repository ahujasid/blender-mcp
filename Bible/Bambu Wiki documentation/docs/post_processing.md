# Post-Processing PLA — Sanding, Primer, Vernici, Resiners

Workflow completo dalla stampa grezza alla finitura professionale su PLA FDM. Comprende sanding, filler, primer, pittura e coating.

---

## Regola Fondamentale: NO Acetone su PLA

L'acetone NON scioglie il PLA in modo controllato — lo rende gommoso, fragile e soggetto a cricche nel tempo. Molti primer e vernici spray usano acetone come carrier solvent. **Verificare sempre la scheda tecnica** prima di usare un prodotto.

---

## Sequenza Workflow (dall'inizio alla fine)

```
1. Rimozione supporti → pulizia meccanica (cutter, pinzette, spatole)
2. Sanding grossolano (120 grit) → rimozione layer lines pronunciate
3. Sanding medio (220 grit) → preparazione per filler
4. Filler primer / stucco → colmare le valli tra layer
5. Sanding fine (400 grit) → levigatura primer
6. Sanding wet fine (600–800 grit) → preparazione pittura
7. Primer finale (sottile) → ancoraggio colore
8. Pittura (2–3 mani sottili) → colore
9. Clear coat / coating epossidico → protezione e finitura
10. (Opzionale) Wet sanding 1000–2000 grit + polish → finitura lucida
```

---

## Sanding — Progressione Grit

| Grit | Funzione | Tecnica |
|---|---|---|
| **120** | Rimozione scars supporti, layer lines prominenti | Sanding a secco, pressione leggera, evitare accumulo calore |
| **220** | Rimozione graffi grossolani, transizione a fase media | Movimenti circolari, no solchi direzionali |
| **400** | Preparazione per primer, crea "tooth" per adesione chimica | Inizio wet sanding con acqua |
| **600–800** | Levigatura layers primer, rimozione difetti fini | Wet sanding costante con acqua come lubrificante |
| **1000–2000** | Extra-fine per finitura lucida o tra mani di verniciatura | Pressione uniforme, molto leggera |

### Wet Sanding — Perché è Essenziale
PLA ha Tg ~60°C: il calore da attrito può ammorbidire e smussare la plastica. L'acqua:
- Dissipa il calore (evita il "gumming up" della carta)
- Sospende le particelle di PLA rimosso (no ridepositi)
- Produce graffi più fini rispetto al sanding a secco alla stessa grit

Iniziare il wet sanding da **400 grit** in poi.

### Su dettagli fini
Con 120 grit si rischia di abraidere i dettagli. Se il modello ha features < 1 mm, partire da **220 grit** e accettare che le layer lines sui dettagli rimangano parzialmente visibili.

---

## Filler — Colmare le Valli

Le layer lines creano picchi (carta vetrata) E valli (richiede filler). Il sanding da solo non elimina le valli su layer height 0.20+ mm.

| Prodotto | Tipo | Pro | Contro |
|---|---|---|---|
| **Bondo Glazing & Spot Putty** | Monocomponente | Asciuga 30 min, facile da carteggiare, waterproof | Odore, solo per difetti medi |
| **Filler Primer (Rust-Oleum)** | Aerosol alto-solidi | Penetra nelle micro-valli per capillarità, sandabile | Copre dettagli fini |
| **Vallejo Plastic Putty** | Brush-on | Precisione su fessure sottili | Non per aree grandi |
| **Milliput / Apoxie Sculpt** | Bicomponente epossidico | No shrinkage, durissimo | Lento (mixing + cure) |

**Tecnica Bondo slurry**: diluire Bondo con minima quantità di solvente (etil acetato — no acetone) → pennellare su tutto il modello → si deposita per capillarità nelle valli. Riduce drasticamente il sanding successivo.

---

## Solventi Compatibili con PLA

| Solvente | Interazione PLA | Applicazione |
|---|---|---|
| **Etil Acetato** | Scioglie PLA in modo controllato | Smoothing vapor/brush, welding, thinning filler |
| **IPA (alcool isopropilico)** | Solo pulizia, non scioglie | Degreasing prima di primer/paint |
| **Diclorometano (DCM)** | Scioglie rapidamente | Solvent welding parti, alta tossicità — fume hood + DPI |
| Acetone | Rende gommoso e fragile | **DA EVITARE** |
| THF (tetraidrofurano) | Scioglie PLA | Hazardous, risultati inconsistenti |

---

## Primer

Il primer crea il legame chimico e meccanico tra PLA e vernice. Senza primer le vernici "beadano" invece di aderire uniformemente.

| Prodotto | Uso ideale | Metodo |
|---|---|---|
| **Rust-Oleum Filler Primer** | Props grandi, parti meccaniche (layer lines evidenti) | Aerosol a 25–30 cm, 3 mani sottili |
| **Tamiya Surface Primer** | Figurine, prototipi con alto dettaglio | Aerosol o airbrush |
| **Vallejo Surface Primer** | Workshop indoor, airbrush precision | Brush o airbrush |
| **Gesso (art primer)** | Modelli grandi economici | Brush — difficile da levigare |

**3 mani sottili** sono sempre meglio di 1 mano spessa. Mano spessa = sagging, perdita dettaglio.

**Tempo di cura filler primer**: 10–15 min dry to touch, 24h full cure. Carteggiare dopo 30 min ma non prima.

---

## Vernici

### Acrilici (raccomandato per PLA)
- Water-based, non-toxic, asciugano in 5–10 min
- Multipli strati sottili: 2–3 mani con 1h tra una e l'altra
- Full cure: 24h–1 settimana
- NO solventi aggressivi → sicure per PLA

Marchi affidabili: Vallejo Model Color/Air, Citadel, Tamiya Acrylic, Liquitex.

### Smalti (enamel)
- Oil-based, finish durissimo, resistente all'usura
- Drying: 24+ ore, full hardness 72h
- Attenzione: solventi forti — verificare compatibilità PLA
- Ideali per parti che vengono toccate spesso

### Lacche
- Asciugatura ultra-rapida (minuti)
- Lacche hobby (Tamiya, Mr. Color): generalmente PLA-safe se applicate a strati sottili
- Lacche industriali: possono contenere THF o Etil Acetato in concentrazione → applicare SOLO strati leggerissimi o rischiano di sciogliere il modello

### Regola universale vernici
Applicare **sempre** su primer asciutto, mani sottili, lasciare asciugare completamente tra le mani.

---

## Coating Epossidico — XTC-3D

Per finitura glass-like o rinforzo strutturale. Elimina tutte le layer lines in un passaggio.

| Proprietà | Valore |
|---|---|
| Mixing ratio | 2A : 1B (volume) oppure 100A : 42B (peso) |
| Viscosità misto | 350 cps (bassa, penetra nei dettagli) |
| Pot life | 10 min in massa, 20 min in film sottile |
| Cure time | 3.5–4 ore a 23°C |
| Durezza finale | 80 Shore D (rigido come plastica strutturale) |

**Gestire l'esotermia**: non mescolare grandi quantità in un unico contenitore cilindrico — il calore accumulato può sciogliere il modello. Versare il misto in un vassoio piatto di alluminio → raddoppia il pot life.

**Applicazione**: pennello di schiuma o chip brush, strati < 1/64" (~0.4 mm). Due mani dà risultato ottimale.

**Alternative XTC-3D**:
- UV-cure resin SLA/DLP: pennellare + UV lamp → cure istantanea, working time infinito fino all'UV
- Z-Poxy (30 min epoxy): resistente a shock e solventi, comune in RC community
- Amazing Clear Cast: epossidico generico, cure 24h

---

## Tempi Tecnici (Dry vs Cure)

"Dry to touch" ≠ "cured". Non carteggiare o applicare il prossimo strato troppo presto.

| Materiale | Dry to touch | Pronto per sanding | Full cure |
|---|---|---|---|
| Filler Primer | 10–15 min | 30 min | 24h |
| Bondo Spot Putty | 5–10 min | 30 min | 2h |
| Acrylic Paint | 5–10 min | 24h (poi clear coat) | 24h–1 settimana |
| XTC-3D Epoxy | 2h | 4h | 24h |
| UV Resin | Secondi (UV) | Immediato | Istantaneo |

PLA max temperatura: **50°C**. Non usare forno o heat gun prolungato. Un ventilatore per accelerare l'evaporazione solventi è ok.

---

## Giunzione di Parti Multi-Pezzo

### Friction Welding
Filamento PLA in rotary tool (dremel) → la rotazione fonde il filamento e il PLA delle parti → saldatura strutturale.

### Solvent Welding
DCM (Weld-On #16, Scigrip #4) scioglie entrambe le superfici di contatto → fusione monolitica. Superiore al cianocrilato per carichi dinamici.

### Cianoacrilato (super glue)
Legame fragile, si rompe agli impatti. Usare solo per parti statiche decorative o come primer per incollare su aree molto piccole.

---

## Waterproofing

- **XTC-3D**: sigilla i pori degli strati FDM → watertight
- **Polyurethane + vernice alternati**: meno durevole ma funzionante per contenitori

---

## Relazioni con altri doc KB

- `print_quality_issues.md` → problemi di superficie da risolvere prima del post-processing
- `filament_materials.md` → Tg e comportamento termico specifici per tipo PLA
- `slicing_profiles.md` → profilo estetico (0.12 mm) per ridurre il lavoro di post-processing
