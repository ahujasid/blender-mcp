# PLA Post-Processing — Field Data

Trattamenti post-stampa per PLA con risultati misurati dalla community Bambu A1 e validati con test indipendenti (CNC Kitchen, Stefan / Made With Layers). Per A1 specifically — open frame, no enclosure, no active chamber control.

## Annealing PLA — curva risultati

Annealing = riscaldare PLA stampato sopra Tg (60°C) per cristallizzarlo, aumentando rigidezza e resistenza a temperatura. **Trade-off**: shrinkage non-uniforme nelle dimensioni.

### Curva temperatura/tempo

| Temp (°C) | Tempo | Risultato strength | XY shrinkage | Z growth | Note |
|---|---|---|---|---|---|
| 60-70 | 30-60 min | +20% strength, +30% stiffness | <1% | <1% | Safe zone — minimal distortion |
| 80 | 60 min | +40% strength, +60% stiffness | 2-3% | 1-2% | Peak senza warping severo |
| 85 | 90 min | +80% strength, +100% stiffness | 4-5% | 2% | **Sweet spot** per parti funzionali |
| 90 | 60 min | +80% strength (no further gain) | 5-6% | 3% | Warping inizia per parti tall/thin |
| 100+ | qualsiasi | Soggetto a sagging | 7%+ | varia | Solo per parti compattamento simmetriche |

**Critical**: la shrinkage è **anisotropa**. XY si contrae 4-5%, Z **cresce** 1-3% — perché in Z le layer line si compattano. Compensare in CAD se aspetti dimensione precise post-anneal.

**Source**: [CNC Kitchen PLA annealing](https://www.cnckitchen.com/blog/better-performing-3d-prints-with-annealing-but-part-1-pla).

### Procedura

1. Stampa il modello con dimensions **+4-5% oversized** in XY e **-2% Z** per compensare post-anneal shrinkage.
2. Forno preheat a temperature target (verifica con thermometer separato — i forni domestici hanno ±15°C error).
3. Place il modello su bed sabbia/silica beads (supporta tutte le superfici durante softening).
4. Bake per tempo target.
5. **Cooldown lento in forno** (NON estrarre subito — thermal shock cause cracking).
6. Misura dopo 24h (PLA continua piccola contrazione per ore).

### Quando NON annealing

- Modelli con feature ≤1mm dimensions (shrinkage non-lineare li distorce).
- Modelli con bordi sottili (warp inevitable >80°C).
- Modelli con metallic embed (different CTE, separazione).
- Parti dimensionalmente critiche (snap-fit, threading) — usa modelli stampati con dimensions compensate.

## Acetone vapor smoothing — NON adatto a PLA su A1

Vapor smoothing funziona su ABS/ASA. **Non funziona su PLA** (PLA non si scioglie in acetone).

Per superficie smooth su PLA → solo **sanding meccanico**.

**Caveat A1 specifico**: A1 non ha enclosure. Anche se vuoi stampare ABS per vapor smoothing, **NON puoi su A1** — l'ABS richiede chamber 60°C+ per evitare warping. A1 raggiunge solo bed 100°C, chamber ambient.

Conclusione: se devi smoothing acetone, stampa su X1C o usa filament alternativi (ASA/PETG no acetone).

## Sanding PLA — grit progression

Per ottenere finitura liscia visibile:

| Grit | Effetto | Tempo medio (50cm² superficie) |
|---|---|---|
| 120-180 | Remove layer lines visible | 5-10 min |
| 240 | Remove sanding marks 180 grit | 3-5 min |
| 400 | First smooth visible | 3-5 min |
| 800 | Pre-paint smooth | 5 min |
| 1500 | Smooth finish (con paint) | 5 min |
| 2000+ | Polish (raro per PLA — surface non glossy) | 5 min |

**Tip community**:
- Use **wet sanding** dal 400 grit in poi (water + drop of dish soap). Riduce heat e sanding marks.
- **Stop al 800 se vuoi paint** (rifletti spray adhesion). **Continua a 1500+ solo se NO paint** (clear finish).
- **NON sandpaper su layer line VICINO** (45° angled) — destroy il pattern uniforme.

**Tempo totale tipico** per modello figurina 100mm: 30-60 min di sanding completo.

## Primer + paint per finitura

Workflow community-converged per finitura cosmetic top-tier:

1. **Sand to 240 grit** (rimuove layer lines visible).
2. **Filler primer spray** (Tamiya Surface Primer L o equivalente) — 2-3 coats sottili.
3. **Sand primer to 400 grit** wet (riempie residual scalfi).
4. **Second primer coat** se necessario.
5. **Color paint** acrylic spray (Vallejo, Citadel, Tamiya).
6. **Top coat** matte/gloss as desired (Mod Podge per matte cheap, Krylon clear gloss).

Tempo totale paint cycle (sanding + primer + paint + topcoat): 4-8 ore lavoro + drying time.

## Smoothing termico via heat gun — caveat

Esiste tecnica di **heat gun smoothing**: passare un heat gun a 200-250°C sopra la superficie PLA per fondere localmente la surface, riducendo layer lines visibility.

**Funziona**: per parti **massicce** (>3mm wall), su superfici **planari**.

**NON funziona**:
- Pareti sottili (<2mm): distorce la geometry interna.
- Feature fini: si fondono via.
- Modelli con cavità: heat penetra e collapse interno.

**Risk**: troppo facile rovinare il modello con heat gun. Sanding è più consistent.

## Filler putty / Bondo — gap filling

Per layer line evidenti o gap visibili dopo support removal:

1. **Bondo Spot Putty** o **Tamiya Putty White** — squeeze + apply with spatula.
2. **Asciuga 30-60 min**.
3. **Sand flush** con 240 grit, poi 400.
4. **Primer over** per uniformare.

Bondo è cheap ma over-shrinks (re-apply needed). Tamiya Putty è premium ma cara.

## XTC-3D (epoxy coating) — alternative a primer/sand

XTC-3D = epoxy 2-component che riempie e liscia layer lines in 1 pass. Costoso ma elimina sanding intensivo.

**Procedura**: mix → brush su modello asciutto → cure 4h. Surface diventa smooth glossy.

**Caveat**:
- Aggiunge ~0.1-0.3mm di material — perdi dettagli fini.
- Non penetra in cavità complesse.
- Una bottle costa $25-30 per ~0.5 m² covered.

**Use case**: large display models con relativamente poco dettaglio fine.

## Cross-reference

- [filament_materials] — proprietà PLA pre-print
- [bambu_studio_settings] — parametri che riducono layer line visibility a priori
- [print_quality_issues] — sintomi pre-print da fixare prima del post-process

## Source

- [CNC Kitchen — Better performing 3D prints with annealing (PLA Part 1)](https://www.cnckitchen.com/blog/better-performing-3d-prints-with-annealing-but-part-1-pla)
- [forum.bambulab.com — Various A1 finishing threads](https://forum.bambulab.com)
- Community consensus from Reddit r/3Dprinting and r/BambuLab finishing megathreads
