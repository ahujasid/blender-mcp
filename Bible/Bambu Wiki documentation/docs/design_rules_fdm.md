# Design Rules FDM — Regole di Progettazione per Stampa 3D

## Limiti Geometrici

### Volume di stampa A1
- Volume nominale: 256 × 256 × 256 mm³
- Con single filament (no AMS): volume pieno accessibile (richiede modifica meccanica stopper + impostazioni BS)
- Default BS: altezza stampabile limitata a 250 mm (riserva per Z-hop); per usare 256 mm, modificare "Excluded bed area" e printable height in Printer Settings
- Limite Z effettivo: Z-hop + Z-hop upper boundary ≤ 256 mm

### Spessori minimi
- Pareti: minimo 1 × line width (con nozzle 0.4 mm: ~0.4–0.45 mm)
- Consigliato per robustezza: almeno 2 pareti (~0.8–0.9 mm)
- Dettagli sottili < 0.4 mm: non stampabili con nozzle 0.4 mm

### Nozzle 0.4 mm — valori di riferimento
| Parametro | Range consigliato |
|-----------|-------------------|
| Layer height | 0.08–0.28 mm |
| First layer height | 0.2 mm (default) |
| Line width | 0.3–0.6 mm (0.75×–1.5× diametro nozzle) |
| Wall minimum | 0.4 mm (1 parete) |

### Nozzle 0.2 mm — limiti dettaglio estremo
- Layer height: 0.05–0.12 mm
- Velocità massima volumetrica: ~2 mm³/s
- Solo PLA Basic/Matte/Translucent — no particolati, no CF, no Glow, no Galaxy
- Resistenza ridotta rispetto a nozzle 0.4 mm (layer più sottili = minor bonding)
- Unclog: metodo hot hex wrench + cold pull (non usare pin standard)

## Tolleranze e Accoppiamenti

### Shrinkage PLA
- PLA ha bassa contrazione rispetto ad ABS/ASA
- Contrazione tipica PLA: 0.3–1% (dipende da geometria, velocità, temperatura)
- Formula calibrazione: Shrinkage % = (Dimensione misurata / Dimensione progettata) × 100
- Esempio: pezzo progettato 20 mm misurato 19.6 mm → Shrinkage = 98%
- In Bambu Studio: Filament Settings → tre puntini → Edit → Shrinkage (default 100% = nessuna correzione)
- Testare con cubo 20×20×20 mm prima di stampare pezzi critici
- Impostazione per filamento (non globale), applicata ad ogni stampa con quel profilo

### Elephant Foot (espansione primo layer)
- Il primo layer si espande leggermente per gravità + compressione
- Compensazione in BS: Process → Quality → Elephant Foot Compensation
- Valore tipico: 0.1–0.2 mm
- Importante per accoppiamenti precisi al piano base

### XY Hole Compensation
- I fori risultano più piccoli del progettato per: shrinkage, elephant foot, seam, flow
- BS offre due impostazioni separate:
  - **XY Hole Compensation:** modifica dimensione fori (non tocca il contorno esterno)
  - **XY Contour Compensation:** modifica il contorno esterno (non tocca i fori)
- Calibrazione: stampare modello test con fori di diametro noto (M3/M4/M5/M6), misurare, applicare offset

### Tolleranze pratiche per accoppiamenti
- Fori per viti: aggiungere 0.2–0.4 mm al diametro nominale (verificare con stampa test)
- Accoppiamenti maschio-femmina: clearance 0.2–0.5 mm per lato
- Calibrazione va ripetuta per ogni filamento differente

## Viti e Fastener

### Tipi di viti — notazione: Tipo + Diametro × Lunghezza (mm)
| Tipo | Nome | Uso |
|------|------|-----|
| M | Metric machine screws | Fori filettati o dadi; smontaggio ripetuto |
| BT | Self-tapping per plastica | Thread su parti plastiche; non intercambiabile con M |
| ST | Self-tapping per lamiera | Lamiera 1–3 mm; profilo thread più fine |
| MG | Partially threaded | Fissaggio + posizionamento preciso |

- **NON intercambiare BT, ST e M** — thread diversi, rischio cracking della plastica o danni ai fori filettati
- Notazione: M3×10 = vite M serie, diametro 3 mm, lunghezza 10 mm (lunghezza esclude la testa)

### Hex socket (Bambu Lab usa prevalentemente)
- Chiavi necessarie: H1.5 e H2.0 per assemblaggio standard
- MakerWorld assembly può richiedere H1.3 e H2.5

### Threadlocker (pre-applicato in fabbrica)
| Tipo | Forza | Uso tipico |
|------|-------|-----------|
| Rosso | Alta (one-time) | Lead-screw nut, struttura critica; cura 24h, difficile rimuovere |
| Blu | Media | Motori, manutenzione periodica; patch nylon, riutilizzabile |

### Fori per viti in parti stampate FDM
- Design con clearance 0.2–0.4 mm oltre il diametro nominale (es. foro M3 → 3.2–3.4 mm)
- Per BT self-tapping in PLA: usare diametro pilota ~85% del diametro nominale per evitare cracking
- Aggiungere chamfer all'ingresso del foro per guidare la vite

## Velocità Volumetrica

### Definizione
Volumetric Speed (mm³/s) = Layer height × Layer width × Print speed

Con nozzle 0.4 mm, layer width 0.45 mm, layer height 0.2 mm:
- 200 mm/s → 18 mm³/s
- 300 mm/s → 27 mm³/s

### Limite massimo volumetrico (MVS)
- Ogni filamento ha un **Maximum Volumetric Speed** oltre il quale si genera under-extrusion
- PLA Basic con nozzle 0.4 mm standard: tipicamente 15–25 mm³/s (dipende da temperatura e filamento)
- Nozzle 0.2 mm: ~2 mm³/s
- Il MVS è il parametro chiave per determinare la velocità massima reale
- BS riduce automaticamente la velocità se il flusso calcolato supera il MVS impostato

### Dove trovare il MVS in BS
Filament → selezionare materiale → Edit → tab Filament → scorrere fino a Max Volumetric Speed

### Impatto sulla qualità
- Superare MVS: under-extrusion, layer deboli, difetti superficiali
- Stare sotto MVS: qualità migliore, superfici più lisce
- Aumentare temperatura nozzle (+5–10 °C) permette velocità più alte

## Orientamento e Resistenza

### Principi FDM sulla resistenza
- La resistenza è **anisotropica**: più alta in XY, più bassa in Z (interlayer)
- Strato su strato: la zona di giunzione Z è il punto debole
- Regola: orientare il pezzo in modo che le forze principali agiscano nel piano XY

### Orientamento per resistenza massima
- **Carichi di trazione:** allineare asse di trazione con XY
- **Carichi di flessione:** le pareti lunghe devono essere parallele alla direzione di flessione
- **Carichi di compressione:** la Z regge bene in compressione (strati che si comprimono tra loro)

### Overhang e angoli
- Overhang < 45° dal piano: stampabile senza supporti (self-supporting)
- Overhang > 45°: richiedono supporti o rallentamento velocità
- L'angolo di overhang si misura dalla superficie del heatbed (non dalla verticale)
- Bridge (ponti): PLA sopporta bene bridge fino a ~50–60 mm con raffreddamento adeguato

### Numero di pareti e infill per resistenza
| Uso | Pareti | Infill |
|-----|--------|--------|
| Estetico | 2 | 10–15% |
| Funzionale leggero | 3 | 20–30% |
| Funzionale robusto | 4+ | 40%+ |
| Massima resistenza | 4–6 | 80–100% |

### Considerazioni per Blender → stampa
- Pareti troppo sottili (< 0.4 mm) vengono ignorate dallo slicer
- Geometrie non-manifold (mesh non chiuse) causano errori di slicing
- Fori < 1 mm sono difficili da stampare con precisione con nozzle 0.4 mm
- Evitare spigoli vivi sul primo layer (aumentano stress termico e warping)
- Aggiungere filetti/chamfer agli spigoli interni migliora resistenza e rimuove layer artifacts da bridging

## PLA Aero (foaming) — solo se usi materiali leggeri per RC models
- Flow ratio ridotto a ~0.5
- Velocità ridotta (non adatto a print veloci)
- Evitare travel senza estrusione (riscaldamento non uniforme)
- Spiral vase mode compatibile con modelli a parete singola chiusa
