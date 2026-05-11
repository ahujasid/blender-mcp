# Filament Materials — PLA su A1

## Parametri di Stampa PLA

### Valori di riferimento PLA su A1 (nozzle 0.4 mm stainless, Textured PEI)

| Parametro | Valore |
|-----------|--------|
| Temperatura nozzle | 190–240 °C (tipico PLA Basic: 220 °C) |
| Temperatura heatbed | 35–65 °C (Textured PEI: 55–65 °C, Cool Plate: ~35 °C) |
| Shrinkage/warping | Minimo |
| Raffreddamento parte | Alto (fan al 100% dopo i primi layer) |
| Hygroscopicity | Bassa (PLA Basic non richiede essiccazione di solito) |

**Regola velocità/temperatura:**
- Aumentare velocità → aumentare temperatura nozzle (~+5–10 °C per Sport/Ludicrous mode)
- Ridurre velocità molto → abbassare temperatura per evitare stringing

**Temperatura massima utile:** solitamente 220–230 °C per PLA Basic standard. Sopra 240 °C si rischia degradazione e stringing eccessivo.

### Limiti A1 per PLA
- Printer open-frame: evitare correnti d'aria che raffreddano il pezzo in stampa
- Se temperatura ambiente > 30 °C in estate: ridurre heatbed di 5–10 °C dal default per evitare heat creep
- A1 NON adatto per ABS, ASA, PC, PA (printer open-frame, rischio warping e fumi)

## Tipi di PLA

### PLA Basic / Matte / Translucent / Tough+ / Lite / Metal
- Compatibile con tutti i nozzle standard (0.2–0.8 mm)
- Compatibile con tutte le piastre
- Nessuna restrizione speciale
- PLA Basic: il più facile, non richiede essiccazione, si stampa direttamente
- PLA Tough+: resistenza meccanica migliorata, stessi parametri base

### PLA Silk / Silk+
- Nozzle 0.4 mm raccomandato (compatibile con tutti gli standard)
- Essiccazione raccomandata: 55 °C per 8h (forno) o 70 °C 12h (heatbed)
- Non raccomandato su piastre a bassa temperatura (usare Textured PEI o Smooth PEI)
- Problema comune: variazione gloss tra sezioni a velocità diverse — usare velocità uniforme
- Resistenza Z inferiore rispetto a PLA Basic: ~8.5 kJ/m² vs 13.8 kJ/m²
- Per pezzi strutturali: aumentare pareti e infill, ridurre velocità, aumentare temperatura +5 °C

### PLA-CF (Carbon Fiber)
- **Obbligatorio hardened steel nozzle** (0.4 mm raccomandato, non high-flow 0.4 mm)
- **Non usare nozzle 0.2 mm** (particelle CF bloccano il nozzle)
- Essiccazione: 50 °C per 8h (forno)
- Cold pull periodico con PLA Basic raccomandato per pulizia nozzle
- Non soggetto a warping, stampabile su A1

### PLA Galaxy / Wood / Marble / Sparkle
- Tutti i nozzle standard eccetto 0.2 mm (particolati)
- PLA Wood: essiccazione raccomandata (polvere di legno assorbe umidità), ventilare ambiente, odore naturale non tossico
- Non usare nozzle 0.2 mm stainless

### PLA Glow (Glow-in-the-dark)
- **Obbligatorio hardened steel nozzle** (anche 0.4 mm high-flow OK, no 0.2 mm)
- Contiene polvere fosforescente — usura rapida su stainless steel
- Non compatibile con AMS lite (troppa resistenza al feeding)
- Usare external spool holder

### PLA Aero (foaming)
- Solo nozzle 0.4 mm (no 0.2 mm, no 0.6/0.8 mm hardened)
- Non eseguire Dynamic Flow Calibration (disabilitare in BS)
- Flow ratio basso: ~0.5 (il materiale espande durante il riscaldamento)
- Controllare temperatura di espansione: temperatura più alta = più espansione = filamento più leggero
- Strutture semplici, pareti ≥ 1 mm
- Evitare percorsi di viaggio lunghi senza estrusione (material drip)
- Essiccazione: 55 °C per 8h
- Compatibile con AMS lite

## Conservazione e Essiccazione

### Regola generale PLA
PLA Basic ha bassa hygroscopicity: normalmente si usa direttamente dalla busta. Non richiede essiccazione di routine se conservato in ambiente secco (umidità 50–60%).

### Filamenti PLA che richiedono essiccazione pre-stampa
| Tipo | Temperatura (forno) | Tempo | Temperatura (heatbed) | Tempo |
|------|---------------------|-------|----------------------|-------|
| PLA Silk / Silk+ | 55 °C | 8h | 70 °C | 12h |
| PLA Aero | 55 °C | 8h | 70 °C | 12h |
| PLA Wood | 55 °C | 8h | 70 °C | 12h |
| PLA-CF | 50 °C | 8h | 70 °C | 12h |
| PLA Translucent | 50 °C | 8h | 70 °C | 12h |

**Nota A1:** L'A1 è una stampante open-frame, NON può essere usata per essiccare filamenti (non raggiunge le temperature necessarie in modo controllato). Usare forno domestico o heatbed con copertura.

**Heatbed per essiccazione:** Posizionare il filamento sul heatbed, coprire con scatola del filamento o contenitore. Girare il filamento ogni 6 ore. Potenza di riscaldamento inferiore al forno → tempi più lunghi.

### Segnali di filamento umido
- Stringing eccessivo
- Superficie ruvida o opaca
- Bolle/pori nel filamento
- Rumore di crepitio durante la stampa

### Conservazione
- Sigillare in sacchetto o contenitore ermetico con essiccante (silica gel)
- Indicatore essiccante: beads gialle = asciutte; beads viola = sature, rigenerare
- Rigenerazione essiccante: 80–90 °C per 1–3h (non superare 100 °C)
- Non rimuovere il nastro adesivo dal filamento finché pronto all'uso — rischio svolgimento e aggrovigliamento

## Problemi Comuni PLA

### Stringing/Oozing
Cause principali per PLA:
1. Filamento umido → essiccare
2. Temperatura nozzle troppo alta → ridurre 5–10 °C
3. Retraction insufficiente → aumentare lunghezza retraction (max 2 mm per evitare clog)
4. Long travel con distanza grande tra modelli → ridurre distanza o abilitare "Avoid crossing walls"

### Clog da Heat Creep (tipico PLA)
PLA glass transition ~57 °C → il più vulnerabile a heat creep.
- Mantenere hotend cooling fan funzionante
- Ridurre heatbed temperature se temperatura ambiente è alta
- Verificare che il fan del hotend non sia bloccato da polvere
- A1 è open-frame: no problemi di camera calda (a differenza di X1/P1S chiusi)

### Warping PLA
PLA ha warping minimo. Se si verifica:
- Pulire la piastra con acqua calda e detergente
- Assicurarsi che il heatbed sia alla temperatura corretta per la piastra usata
- Aggiungere Brim in Bambu Studio
- Verificare bed leveling

### Qualità superficiale PLA Silk
- Variazioni di gloss tra sezioni: normalizzare le velocità di stampa
- Ridurre velocità outer wall o usare layer height 0.16 mm
- Stampare più oggetti contemporaneamente per evitare slowdown da minimum layer time

### Fragilità PLA Basic
- PLA è britttle: non adatto a carichi d'impatto elevati
- Per maggiore resistenza: aumentare numero pareti (4+), aumentare infill (40%+), temperatura +5 °C, velocità -20%
