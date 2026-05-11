# Slicing Profiles — Preset Operativi Bambu Studio per PLA su A1

Ricette pratiche per i casi d'uso più frequenti. Ogni profilo è pensato per PLA Basic o PLA+ su Bambu A1 con nozzle 0.4mm stainless steel (default).

> Fonte: derivati dai parametri documentati in `bambu_studio_settings.md`, `design_rules_fdm.md`, `filament_materials.md`. Valori da verificare/affinare in sessione reale e annotare in FIELD_NOTES.

---

## Struttura di un Profilo

Ogni profilo specifica i parametri che deviano dal default A1 + PLA Basic. Parametri non elencati → usa il preset Bambu default.

**Layer height base**: 0.20 mm (standard), 0.28 mm (veloce), 0.12 mm (qualità).

---

## Profilo 1 — Figurina Estetica / Testa di Moro

**Use case**: modello organico da esporre, dettaglio superficiale importante, nessuna funzione meccanica.

```
QUALITY
  Layer height:           0.12 mm         [dettaglio fine]
  First layer height:     0.20 mm         [adesione garantita]
  
WALLS
  Wall loops:             4               [superfici curve continue]
  Top surface pattern:    Monotonic       [superficie superiore liscia]
  Bottom surface pattern: Monotonic
  Seam position:          Back            [posiziona seam nella parte posteriore]

INFILL
  Infill density:         15%             [solo per supportare superfici esterne]
  Infill pattern:         Gyroid          [isotropico, nessuna linea visibile in superficie]

SUPPORT
  Enable support:         YES (se necessario — vedi orientation_strategy)
  Support type:           Tree (normal)
  Threshold angle:        45°
  Top Z distance:         0.20 mm
  Interface layers:       3
  Interface spacing:      0.15 mm

SPEED
  Print speed:            100 mm/s        [ridotta per dettaglio]
  Outer wall speed:       60 mm/s         [critico per qualità superficiale]
  First layer speed:      30 mm/s

COOLING
  Fan speed:              80–100%
  Slow down for overhang: ON

STRENGTH / ADHESION
  Brim:                   ON, 5 mm        [figurine hanno base piccola]
  Brim type:              Outer brim only
```

**Note specifiche**:
- Con PLA Silk: ridurre velocità outer wall a 40 mm/s, aumentare temperatura di 5°C
- Testa di Moro: orientare verticalmente (testa in alto), inclinare 10–15° verso l'indietro per ridurre overhang su naso/mento

---

## Profilo 2 — Parte Funzionale Standard

**Use case**: clip, coperchi, supporti, parti di assemblaggio che subiscono forze moderate.

```
QUALITY
  Layer height:           0.20 mm
  First layer height:     0.20 mm

WALLS
  Wall loops:             4               [resistenza laterale]
  Detect thin walls:      ON

INFILL
  Infill density:         40%
  Infill pattern:         Grid            [resistenza bilanciata XY]

SUPPORT
  Enable support:         dipende dal design (vedi support_strategy.md)

SPEED
  Print speed:            200 mm/s        [default A1]
  Outer wall speed:       100 mm/s

COOLING
  Fan speed:              70%

STRENGTH / ADHESION
  Brim:                   OFF (se base ≥ 20×20 mm)
  Top shell layers:       5
  Bottom shell layers:    4
```

**Note specifiche**:
- Per tolleranze di accoppiamento con altri pezzi: aggiungere XY Hole Compensation (+0.1 mm) e XY Contour Compensation (-0.1 mm) — vedi `bambu_studio_settings.md`
- Elephant Foot Compensation: 0.1–0.15 mm per il primo layer

---

## Profilo 3 — Parte Meccanica ad Alta Resistenza

**Use case**: ingranaggi, giunti, parti che subiscono impatto o trazione ripetuta.

```
QUALITY
  Layer height:           0.20 mm

WALLS
  Wall loops:             6               [resistenza massima guscio]
  Top shell layers:       6
  Bottom shell layers:    5

INFILL
  Infill density:         60–80%
  Infill pattern:         Cubic           [resistenza isotropica 3D]
  Infill/wall overlap:    30%             [legame infill-pareti più forte]

SUPPORT
  Orientare per evitare supporti — se impossibile da evitare: Normal support

SPEED
  Print speed:            150 mm/s        [ridotta per adesione layer migliore]
  Outer wall speed:       80 mm/s

COOLING
  Fan speed:              60%             [raffreddamento ridotto = adesione layer migliore]
  Slow down for overhang: ON

STRENGTH / ADHESION
  Brim:                   ON, 8 mm        [parti alte e sottili: rischio warping]
```

**Note specifiche**:
- Aumentare temperatura nozzle di 5°C rispetto al profilo standard per migliore layer adhesion
- Orientare in modo che le forze principali siano nel piano XY (non in Z)
- PLA+ invece di PLA Basic: migliore tenacità agli impatti

---

## Profilo 4 — Miniatura / Oggetto Piccolo (< 50 mm)

**Use case**: pedine, gettoni, figurine in scala, oggetti di dettaglio.

```
QUALITY
  Layer height:           0.08–0.12 mm    [massimo dettaglio]
  First layer height:     0.20 mm

WALLS
  Wall loops:             3
  Detect thin walls:      ON

INFILL
  Infill density:         20%
  Infill pattern:         Gyroid

SUPPORT
  Support type:           Tree
  Threshold angle:        40°             [più aggressivo per piccoli dettagli]
  Interface spacing:      0.10 mm         [distacco preciso su dettagli fini]

SPEED
  Print speed:            80 mm/s         [ridotta fortemente per dimensioni piccole]
  Outer wall speed:       40 mm/s
  Travel speed:           150 mm/s

COOLING
  Fan speed:              100%            [massimo per solidificazione rapida]

STRENGTH / ADHESION
  Brim:                   ON, 3 mm        [base piccola: brim leggero]
  Raft:                   Considerare se altezza > 50mm e base < 10mm
```

**Note specifiche**:
- Layer height 0.08 mm è lento: stimare 3–5x il tempo rispetto a 0.20 mm
- Verificare che feature minima modello ≥ 0.8 mm (limite A1 con nozzle 0.4)
- Preferire nozzle 0.2 mm per dettagli estremi (richede cambio nozzle fisico)

---

## Profilo 5 — Oggetto Grande (> 200 mm)

**Use case**: vasi, contenitori, sculture, basi, pannelli.

```
QUALITY
  Layer height:           0.28 mm         [velocità prioritaria]
  First layer height:     0.28 mm

WALLS
  Wall loops:             3
  Seam position:          Aligned + Back  [seam in posizione controllata]

INFILL
  Infill density:         10%
  Infill pattern:         Lightning       [velocità massima, solo supporto superfici]

SUPPORT
  Enable support:         NO (orientare per evitarli)

SPEED
  Print speed:            250–300 mm/s    [massimo A1]
  Outer wall speed:       120 mm/s
  First layer speed:      30 mm/s         [critico per adesione su oggetti grandi]

COOLING
  Fan speed:              70%
  Slow down threshold:    ≥ 15 s/layer    [evita deformazione su layer grandi lenti]

STRENGTH / ADHESION
  Brim:                   ON, 10 mm       [obbligatorio per oggetti grandi]
  Brim type:              Outer brim only
```

**Note specifiche**:
- Rischio warping aumenta con l'area: pulizia piastra PEI con acqua+detergente prima della stampa
- Controllare il modello su Bambu Studio "Overhang" view: a 0.28 mm ogni overhang è più visibile
- Se il modello non entra nel build volume 256×256×256 mm: splittare in Blender con Boolean + piano di taglio

---

## Profilo 6 — Parte Sottile a Parete Singola (< 2 mm)

**Use case**: clip pieghevoli, coperchi leggeri, packaging, snap-fit.

```
QUALITY
  Layer height:           0.16 mm         [buon dettaglio su spessore ridotto]

WALLS
  Wall loops:             2               [pareti sottili: non aggiungere più di 2]
  Detect thin walls:      ON
  Min feature size:       0.4 mm          [singola linea nozzle]

INFILL
  Infill density:         0%              [parte è solo shell, no infill]
  Sparse infill density:  0%

SPEED
  Print speed:            120 mm/s
  Outer wall speed:       60 mm/s

COOLING
  Fan speed:              100%            [solidificazione rapida critica per pareti fini]
```

**Note specifiche**:
- Verificare in Bambu Studio preview "Line type" che non ci siano gap nelle pareti sottili
- Live hinge (cerniera flessibile): spessore 0.5–0.8 mm, orientare in modo che il lato della flessione sia in XY
- PLA è relativamente rigido per snap-fit: usare angolo snap-fit ≥ 30°, altezza snap ≤ 0.5 mm

---

## Quick Reference — Scelta del Profilo

| Scenario | Profilo |
|---|---|
| Figurina, busto, oggetto organico decorativo | 1 — Estetico |
| Parte che si assembla, clip, supporto | 2 — Funzionale Standard |
| Parte sotto carico, ingranaggio, snap-fit critico | 3 — Alta Resistenza |
| Dettaglio < 50 mm, pedina, miniatura | 4 — Miniatura |
| Pezzo > 200 mm, vaso, contenitore, base | 5 — Grande |
| Parete flessibile, snap, packaging | 6 — Sottile |

---

## Relazioni con altri doc KB

- `bambu_studio_settings.md` → parametri slicer completi con spiegazione
- `bambu_studio_workflow.md` → come applicare i profili in Bambu Studio
- `design_rules_fdm.md` → limiti fisici A1 a monte della scelta profilo
- `filament_materials.md` → differenze PLA Basic / Silk / CF che cambiano i parametri
- `print_quality_issues.md` → se il profilo produce artefatti, diagnosi qui
- `support_strategy.md` → profilo 1 e 4 rimandano qui per la logica supporti
