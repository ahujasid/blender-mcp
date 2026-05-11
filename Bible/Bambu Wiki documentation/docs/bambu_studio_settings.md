# Bambu Studio Settings — Parametri Slicer

## Supporti

### Impostazioni base supporti (Process → Support)
- **Enable support:** attiva strutture di supporto
- **Support type:** Normal (standard) o Tree support (migliore per geometrie complesse)
- **Support threshold angle:** angolo oltre il quale vengono generati supporti (default 45°)
- **Top Z Distance:** gap tra supporto e modello (con stesso filamento: bilanciare tra rimozione facile e qualità superficie)

### Support Painting Tool
BS permette di "dipingere" manualmente dove aggiungere o escludere supporti:
- Modalità "Enforce Support": forza supporto in zone selezionate
- Modalità "Block Support": esclude supporto in zone selezionate
- Utile per geometrie complesse o per controllare precisamente dove si formano i supporti

**Strumenti di pennello:**

| Strumento | Comportamento | Quando usare |
|---|---|---|
| **Sphere Tool** | Colora tutti i facet nel raggio 3D incluse cavità interne | Geometrie complesse con sbalzi interni |
| **Fill Tool** | Propaga il colore su tutte le facce connesse fino a un angolo soglia (Smart Fill Angle) | Superfici piane o moderatamente curve — un click colora tutta la zona |
| **Gap Fill** | Rileva e riempie automaticamente piccoli vuoti tra aree già colorate | Post-pittura per evitare "isole" non supportate |

**Workflow consigliato:** Auto-support come base → Block Support sulle zone estetiche critiche (dove le cicatrici non sono accettabili) → Enforce Support sui punti di bridge realmente a rischio → Gap Fill per chiudere isole → verifica screenshot del risultato.

**Smart Fill Angle:** soglia angolare per lo strumento Fill. Un angolo basso (es. 10°) espande solo sulle superfici quasi complanari; un angolo alto (es. 45°) espande su tutta una faccia curva. Regola in base alla complessità del modello.

### Consigli PLA single filament
- Con PLA, i supporti si rimuovono meccanicamente
- Aumentare Top Z Distance rende la rimozione più facile ma peggiora la superficie superiore al supporto
- Abilitare "Slow down for overhangs" può eliminare la necessità di supporti fino a ~55–60°

## Seam

### Posizionamento seam (Process → Quality → Seam)
| Opzione | Comportamento | Uso consigliato |
|---------|--------------|----------------|
| Nearest | Nasconde in angoli concavi/convessi | Modelli irregolari con angoli |
| Aligned | Seam allineato verticalmente | Modelli cilindrici, vasi |
| Back | Seam nel retro del modello | Pezzi con fronte definito (maschere, decorazioni) |
| Random | Posizione casuale ogni layer | **Da evitare** — causa zits/dots |

**Scarf seam:** sfuma l'inizio e la fine della parete sovrapponendoli gradualmente (simile a giunzione a sciarpa in falegnameria). Quasi invisibile su superfici curve. Distribuisce lo stress meccanico su un'area più ampia eliminando il punto di debolezza verticale del seam tradizionale.

**Configurazione ottimale Scarf Seam:**
- Ordine pareti: **Inner/Outer/Inner** — il primo inner fornisce struttura, l'outer (scarf) garantisce estetica, il secondo inner consolida il legame e minimizza il ritiro termico sulla superficie visibile
- Lunghezza sovrapposizione: ~20mm (default BS)
- Velocità parete esterna: ridurre a 50–75 mm/s per migliore definizione della rampa
- Overhang Detection: se il seam cade su un overhang, BS v2.x disabilita automaticamente lo scarf in quella zona (prevenzione fallimento)

**Seam Gap:** controllo del gap tra inizio e fine perimetro. Ridurre se si notano discontinuità.

**Wipe Speed:** velocità durante il wipe del seam — influisce sull'aspetto della giunzione.

## Cooling

### Parametri cooling (Filament Settings → Cooling)
**Part Cooling Fan:**
- Min Fan Speed: velocità minima fan (quando il layer impiega molto tempo)
- Max Fan Speed: velocità massima fan (quando il layer è molto rapido)
- Layer time threshold: soglie di tempo che determinano la velocità fan
  - Es. default PLA: 100% fan per layer < 3s; 10% per layer > 30s

**Keep Fan Always On:** il fan non si spegne mai, rimane almeno alla velocità minima.

**Slow Printing Down for Better Layer Cooling:** se il fan è al massimo ma la stampa è troppo rapida, riduce la velocità di stampa per garantire raffreddamento sufficiente.

**Special Cooling Settings:**
- Controlla velocità fan nei primi N layer (durante i quali il fan principale è disabilitato per migliorare adesione al bed)
- Default: fan al 0% per il primo layer, poi rampa verso la velocità target

**Slow down for overhangs (Process → Quality):**
Riduce automaticamente la velocità dei wall in zone con overhang. Le linee vengono categorizzate per grado di overhang (% della larghezza non supportata dal layer inferiore) e ricevono velocità diverse. Evita di dover ridurre la velocità globale per gestire gli overhang.

## Compensazioni Geometriche

### Elephant Foot Compensation (Process → Quality)
- Corregge l'espansione del primo layer compresso sulla piastra
- Valore tipico: 0.1–0.2 mm
- Importante per accoppiamenti precisi: attivare quando il pezzo deve interfacciarsi con altri

### XY Hole Compensation (Process → Advanced)
- Aggiusta dimensione dei fori (chiusi, aree vuote)
- Valori positivi: allarga i fori; negativi: li restringe
- Non influenza il contorno esterno del modello

### XY Contour Compensation (Process → Advanced)
- Aggiusta il contorno esterno del modello
- Non influenza i fori interni
- Utile quando il modello risulta troppo grande/piccolo rispetto al progetto

### Shrinkage (Filament Settings)
- Scala il modello per compensare il ritiro termico del materiale durante il raffreddamento
- Formula: (dimensione misurata / dimensione progettata) × 100 = valore da inserire
- Default 100% = nessuna correzione; es. 98% scala il modello del 2% in più

### Adaptive Layer Height
- Varia automaticamente l'altezza del layer in base alla geometria
- Aree con slope piccolo → layer più sottile (maggiore dettaglio)
- Aree con slope grande → layer più spesso (risparmio tempo)
- Range: 0.08–0.28 mm per nozzle 0.4 mm
- Attivare in BS selezionando l'oggetto → Enable Variable Layer Height

## Strength

### Parametri di resistenza (Process → Strength)
**Wall loops:** numero di perimetri. Default 2, raccomandato 3–4 per pezzi funzionali.

**Top/Bottom shells:** numero di layer solidi top e bottom. Default 3–4. Aumentare per superficie più chiusa e robusta.

**Infill density:** % di riempimento interno.
- 10–15%: estetico/leggero
- 20–30%: uso funzionale leggero
- 40–60%: funzionale robusto
- 80–100%: massima resistenza

**Infill pattern:**
- Gyroid: ottimo rapporto resistenza/peso, isotropico
- Cubic/3D Honeycomb: buona resistenza multidirezionale
- Grid: rapido ma anisotropico (debole in diagonale)
- Lightning: molto veloce, solo supporto interno (non per pezzi strutturali)

**Infill/Wall overlap:** default 15% — la zona infill si sovrappone leggermente alla parete per migliore ancoraggio. Non superare 50% (causa gonfiore superficiale).

**Infill direction:** angolo delle linee infill (default 45°). Modificare se si vuole ottimizzare per carichi specifici.

**Minimum sparse infill threshold:** aree infill più piccole della soglia vengono riempite con solid infill (migliora robustezza delle zone strette).

### Beam Interlocking
Rilevante solo per multi-material — non applicabile a single filament.

## Parametri Avanzati

### Retraction (Printer Settings → Extruder / Filament Settings → Overrides)
- **Length:** quantità di filamento ritratto prima del travel. Default A1 PLA: ~0.8–1 mm. Non superare 2 mm.
- **Z hop:** sollevamento Z durante travel. Evita sfregamento nozzle sul pezzo. Limite: 5 mm.
- **Z Hop type:** Slope, Normal, Spiral, Auto. Auto seleziona automaticamente il tipo più adatto.

### Line Width (Process → Quality)
- Normalmente uguale al diametro del nozzle (0.4 mm per nozzle 0.4 mm)
- Range consentito: 0.75×–1.5× diametro nozzle (0.3–0.6 mm per nozzle 0.4 mm)
- Non modificare senza motivo preciso — può degradare qualità
- Line width più larga: stampa più rapida ma meno dettaglio

### Bridge Settings (Process → Quality → Bridge)
- **Bridge Flow:** aumentare per ridurre gap tra linee del bridge (default <1, aumentare verso 1.1–1.2)
- **Bridge Speed:** ridurre per dare più tempo di raffreddamento (migliora qualità ponte)
- **Bridge Direction:** angolo linee bridge (0 = automatico)

### Layer Height (Process → Quality)
| Profile | Layer Height | Uso |
|---------|-------------|-----|
| 0.08 mm | Ultra-fine | Dettaglio massimo, miniature |
| 0.12 mm | Fine | Alta qualità |
| 0.16 mm | High Quality | Buon bilanciamento |
| 0.20 mm | Optimal | Standard — uso quotidiano |
| 0.24 mm | Draft | Veloce |
| 0.28 mm | Extra Draft | Velocissimo |

### Spiral Vase (Process → Others → Special Mode)
- Stampa l'outer wall in spirale continua — niente seam sulle pareti
- Automanticamente imposta: 1 parete, 0 top layers, 0% infill
- Solo per modelli semplici a parete singola (vasi, contenitori)
- Non funziona su modelli con strutture interne o overhangs complessi

### Even-Odd Mode (Process → Others → Special Slicing Mode)
- Per modelli RC o modelli con geometrie non-manifold che si intersecano
- Interpreta correttamente contorni chiusi sovrapposti come strutture interne

### Brim (Process → Other)
- **Auto brim:** BS determina automaticamente la larghezza in base a forma, altezza e materiale
- **Manual brim:** impostare Brim Width manualmente
- **Brim-object gap:** gap tra brim e oggetto (0 mm = connesso; utile per rimozione facile con un piccolo gap)

### Preset System
- **Printer Preset:** hardware settings (max speed, area stampa, diametro nozzle)
- **Filament Preset:** temperatura, heatbed, flow ratio, cooling, retraction specifici del filamento
- **Process Preset:** layer height, supporti, infill, seam — salva per riuso

Workflow: selezionare il Process preset come base, poi modificare al livello object o part per override locali senza cambiare il preset globale.

---

## Bambu Studio 2.x — Novità e Rinominazioni

### Rinominazioni UI (v1.x → v2.x)

| Vecchio nome (v1.x) | Nuovo nome (v2.x) | Note |
|---|---|---|
| Simulation | **Assess** | Analisi predittiva dei failure prima della stampa |
| Optimization | **Enhance** | Ottimizzazione multi-obiettivo velocità/estetica/robustezza |
| HMS (Health Management System) | **Assistant (HMS)** | Diagnostica proattiva con guide interattive |
| Support type: Hybrid | **Support style → Tree Hybrid** | Ora è uno "stile" dentro la categoria Tree |
| Use AMS (toggle) | **Mappatura diretta sorgente** | Selezione slot o spool esterna nel dialogo di invio |

### Nuovi Stili Supporto Albero

- **Tree Slim**: minimo materiale, piccoli sbalzi
- **Tree Strong**: rami più spessi, modelli pesanti/strutturali
- **Tree Hybrid**: Normal support su aree ampie + Tree su dettagli complessi — default consigliato per figurine organiche

**Miglioramenti strutturali (v2.5.3)**: chamfer alla base dei supporti (+2 mm di espansione verso il basso) per evitare collassi su bedslinger A1 ad alta accelerazione.

### Nuovi Pattern Infill

- **Locked Zag**: skin a "Cross Zag" + scheletro a zigzag interno. Buona qualità superficiale + rigidità. 4 parametri di continuità per evitare punti deboli tra aree.

### Nuove Feature di Qualità

- **Precise Wall** (Developer mode, v2.1+): regola dinamicamente la sovrapposizione parete esterna/interna per colmare extrusion over/under — migliora accuratezza dimensionale.
- **Precise Z Height**: regola gli ultimi 5 strati per compensare errori di arrotondamento `altura / layer_height`. Utile per parti che devono matchare un'altezza CAD esatta.
- **Smooth Overhang Transition Speed** (v1.9.1+): interpolazione lineare della velocità tra le soglie di overhang — addio gradini di velocità visibili sulla superficie.

### A1-Specific: Calibrazione Flusso via Eddy Current

La A1 usa un sensore a correnti parassite (non LIDAR) per la calibrazione automatica Pressure Advance. Da firmware 01.04.00.00:
- Il valore K risultante può essere **più alto del previsto rispetto a calibrazione manuale** — è intenzionale (previene accumulo negli angoli).
- Gestire da **Calibration** tab → salvare per slot.

### A1-Specific: Fan Pre-Start (v2.1+)

Il cooling fan parte **2 secondi prima** di arrivare su aree critiche (bridge, dettagli sottili). Riduce deformazioni su stampe PLA veloci. Non disabilitare su A1.

### A1-Specific: Retraction PLA (v2.1+)

Aggiornati i profili di retrazione per PLA Basic e PLA Matte su nozzle 0.4/0.6/0.8 mm. Se stai usando profili custom vecchi e noti stringing eccessivo: resettare al preset factory e ricalibrare.

### Feature Operative Utili (v2.x)

- **Skip Object remoto** (v2.2+): se un oggetto si stacca durante la stampa, si può istruire la stampante da remoto a ignorarlo — salva gli altri oggetti sul piatto.
- **Scarf Seam con Overhang Detection**: se la seam cade su un overhang che potrebbe fallire, il sistema disabilita automaticamente la Scarf Seam in quella zona.
- **Copia impostazioni tra oggetti**: click destro su oggetto → copia parametri di processo su altri oggetti nella stessa build plate.

---

## Cut Tool (Strumento di Taglio)

Divide il modello in Bambu Studio senza tornare al software CAD. Ogni metà può essere orientata indipendentemente e stampata con impostazioni diverse.

### Tipologie di connettore

| Tipo | Meccanismo | Quando usare |
|---|---|---|
| **Planar** | Taglio piano netto, nessun connettore | Per aggiungere una base piatta artificiale o separare pezzi da incollare |
| **Plug (Pioli)** | Connettore maschio-femmina integrato | Posizionamento rapido, dipende dalla precisione di stampa |
| **Dowel (Spinotti)** | Fori su entrambi i lati + spinotti da stampare separatamente | **Migliore per resistenza**: gli spinotti si stampano in orientamento ottimale e si scalano per l'accoppiamento perfetto senza ristampare il pezzo grande |
| **Dovetail (Coda di Rondine)** | Giunzione autobloccante che resiste alla trazione | Assemblaggi che devono sopportare carichi senza sola colla (es. ali di modellismo) |
| **Snap (Scatto)** | Usa la flessibilità del materiale | Solo per materiali flessibili o con snap-fit calibrato; fragile su PLA rigido |

**Tolleranza connettori:** ~0.1mm come punto di partenza. Variare in base alla calibrazione del flusso del filamento specifico. Se il fit è troppo stretto: aumentare XY Hole Compensation. Vedi `tolerances_and_fits.md` per la procedura empirica.

**Workflow taglio per modello oversized:** Cut Tool in BS → stampa le due metà separatamente orientando ciascuna con la superficie di taglio sul bed (nessun supporto sulla giuntura) → assemblare con colla CA o epossidica. Alternativa per giunti reversibili: Dowel + vite M3 (vedi `threads_and_fasteners.md`).

---

## Fuzzy Skin (Pelle Ruvida)

Introduce un jitter casuale nel percorso dell'ugello sulle pareti esterne. Effetti: nasconde le linee degli strati, crea grip su maniglie, produce texture organica/naturale.

| Parametro | Valore | Effetto |
|---|---|---|
| **Point Distance** | 0.1mm | Grana fine (texture sottile) |
| **Point Distance** | 0.4–0.8mm | Grana grossa (texture più evidente) |
| **Thickness** | 0.1–0.2mm | Lieve spostamento, aspetto morbido |
| **Thickness** | 0.3–0.5mm | Spostamento marcato, texture pronunciata |

**Limitazioni:**
- Aumenta leggermente il consumo di filamento (percorso più lungo)
- Non usare su superfici che devono accoppiarsi con tolleranze (il jitter aggiunge variazione dimensionale)
- Su A1 ad alta velocità verificare che il jitter non ecceda la risposta meccanica della testina (ridurre velocità parete esterna al 70% del normale se si notano artefatti)
