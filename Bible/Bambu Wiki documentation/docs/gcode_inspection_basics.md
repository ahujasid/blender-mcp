# G-Code Inspection — Lettura del Preview Bambu Studio

Guida alla lettura del preview G-code in Bambu Studio prima di avviare la stampa. Checklist e interpretazione dei colori / metriche.

---

## Modalità Preview Disponibili

Attivabili dalla toolbar in alto a destra dopo lo slicing:

| Modalità | Shortcut | Cosa mostra |
|---|---|---|
| **Line Type** | Default | Tipo strutturale di ogni traccia (vedi tabella sotto) |
| **Speed** | Gradiente caldo/freddo | Velocità istantanea del toolhead |
| **Flow** | Gradiente | Flusso volumetrico (mm³/s) vs limite materiale |
| **Layer Time** | Per layer | Durata di ogni layer → gestione cooling |
| **Fan Speed** | Per layer | Velocità ventola per layer |
| **Travel** | Linee azzurre | Movimenti senza estrusione (rischio stringing) |
| **Filament** | (Multi-mat) | Distribuzione filamenti / cambio colore |

---

## Mappa Colori — Line Type

| Tipo | Colore | Ruolo |
|---|---|---|
| **Outer Wall** | Rosso | Superficie esterna visibile — accuratezza dimensionale e estetica |
| **Inner Wall** | Verde scuro / Cyan | Massa strutturale, base per parete esterna |
| **Infill** | Arancione | Reticolo interno, rigidità a compressione |
| **Sparse Infill** | Giallo chiaro | Strutture interne a basso consumo |
| **Internal Solid Infill** | Viola / Magenta | Layer densi di transizione (sopra sparse, sotto top surface) |
| **Top Surface** | Giallo | Layer finale superiore, ottimizzato per smoothness |
| **Bottom Surface** | Blu scuro | Layer iniziali a contatto col letto o piani interni |
| **Bridge** | Azzurro chiaro | Stampa in aria tra due sponde supportate |
| **Gap Fill** | Bianco | Micro-tracce per colmare voids dove le pareti normali non entrano |
| **Support** | Verde scuro / Teal | Strutture di supporto sacrificali |
| **Support Interface** | Verde chiaro | Layer di interfaccia densa tra supporto e modello |
| **Skirt / Brim** | Verde scuro / Blu | Priming nozzle (skirt) o aumento superficie adesione (brim) |

---

## Checklist Pre-Stampa — 5 Audit in Sequenza

### Audit 1 — Struttura Layer (Line Type)

Usare il cursore verticale per scorrere layer per layer. Verificare:

- **Primo layer**: Bottom Surface + Brim coprono uniformemente tutta la base. Nessuna isola disconnessa.
- **Interfacce supporto**: Support Interface (verde chiaro) è presente sotto OGNI superficie in overhang che ne necessita.
- **Internal Solid Infill**: presente come base adeguata per le Top Surface layer.
- **Gap Fill bianco**: se abbondante su pareti strette → modello con features < 0.8 mm, considerare nozzle 0.2 mm o ridisegnare.

### Audit 2 — Velocità e Flusso (Speed + Flow)

- **No zone rosse al massimo**: verificare che il flusso volumetrico non superi il limite del filamento (PLA Basic A1: ~18 mm³/s a 0.4mm nozzle).
- **Gradiente overhang smooth**: la velocità deve calare gradualmente sulle zone in overhang. Con BS v1.9.1+ è automatico. Se si vedono gradini bruschi → abilitare "Smooth Overhang Transition Speed".
- **Outer Wall speed uniforme**: variazioni di velocità sulla outer wall producono variazioni di gloss ("fishscale"). Per PLA Silk: outer wall a 40–60 mm/s costante.

### Audit 3 — Cooling e Layer Time

Formula flusso volumetrico: `V_flow = larghezza_linea × altezza_layer × velocità`

- **Layer Time view**: identificare layer molto brevi (< 3 secondi). Bambu Studio aumenta automaticamente il fan. Verificare che la funzione "Slow down for better cooling" sia attiva.
- **Soglie cooling A1+PLA**:
  - Layer < 3s → fan 100% + rallentamento velocità
  - Layer 3–30s → interpolazione lineare fan speed
  - Layer > 30s → fan speed base (50–70%)
- **Torri alte e sottili**: verificare che i layer time siano ≥ 5s — altrimenti il PLA non ha tempo di solidificare prima del prossimo deposito.

### Audit 4 — Travel Moves (Stringing)

- Travel moves = linee azzurre sottili nel preview "Travel".
- **High-risk**: travel che attraversa un void in aria lunga > 10 mm.
- **Verifica "Avoid Crossing Walls"**: le linee travel devono restare dentro il perimetro del modello, non tagliare attraverso il centro. Se escono fuori → feature di routing attivata correttamente.
- **"Reduce Infill Retraction"**: se attivo, disabilita Z-hop durante travel sull'infill. Rischioso per modelli alti e sottili (il nozzle può colpire l'infill già stampato). Disabilitare se il modello ha altezza > 50 mm e base < 15×15 mm.

### Audit 5 — Overhangs (Speed + Line Type combinati)

La velocità ridotta sugli overhang si legge dal gradiente di colore nella modalità Speed.

**Categorizzazione overhang gradi in BS**:
- 10–25% unsupported width: leggero rallentamento
- 25–50%: rallentamento significativo
- 50–75%: approccio ai limiti di auto-supporto
- 75–100%: logica Bridge (azzurro in Line Type, velocità e flow distinti)

Verificare che tutti i ponti (bridge, azzurro chiaro) abbiano:
- Velocità ridotta (< 80 mm/s per PLA A1)
- Fan speed alta (80–100%) per rapida solidificazione

---

## Parametri Critici da Non Ignorare

### Seam Position
- La seam (punto start/end di ogni perimetro) crea un piccolo blob.
- Non deve cadere su superfici di accoppiamento meccaniche.
- **Back** o **Aligned** → prevedibile e controllato.
- **Scarf Seam (v2.x)**: distribuisce la giuntura su una pendenza → meno visibile. Con overhang detection automatica.

### Wall Order
- **Outer-Inner** (outer wall first): maggiore accuratezza dimensionale, rischio lieve su overhangs.
- **Inner-Outer** (default): più stabile su overhangs ma minor precisione della superficie esterna.

### Precise Z Height (BS 2.x)
Se il modello deve rispettare un'altezza esatta (es. parte di un assieme): abilitare. BS regola gli ultimi 5 strati per compensare l'arrotondamento `altezza_totale / layer_height`.

---

## Lettura del Tempo Stimato

La timeline in basso mostra il tempo per ogni fase:
1. First layer (spesso il più lungo per bassa velocità)
2. Infill (velocità massima, non critico)
3. Support (se presente)
4. Outer wall (qualità)

Se il tempo totale è inaccettabile: aumentare layer height (da 0.12 a 0.20 mm riduce ~40% del tempo) o aumentare outer wall speed. Non ridurre mai sotto 30 mm/s outer wall per PLA.

---

## Segnali di Allarme nel Preview

| Cosa vedi | Problema | Fix |
|---|---|---|
| Abbondante Gap Fill (bianco) su pareti | Feature < 0.8 mm | Rimappare mesh in Blender o usare nozzle 0.2mm |
| Bridge azzurro senza Interface verde sotto | Overhang senza supporto rilevato | Aggiungere supporto manuale con Support Painting |
| Travel (blu) che tagliano l'aria tra oggetti | Stringing quasi certo | Abilita "Avoid Crossing Walls", aumenta retraction |
| Layer Time < 3s su feature alta sottile | Rischio crollo termico | Abilita "Slow down", aggiungere oggetto fittizio accanto (ruba layer time) |
| Outer Wall speed variabile su figurine | Gloss non uniforme | Ridurre velocità outer wall a valore fisso basso (60 mm/s) |

---

## Relazioni con altri doc KB

- `bambu_studio_settings.md` → parametri dettagliati per ogni setting
- `bambu_studio_workflow.md` → come arrivare al preview nel workflow completo
- `print_quality_issues.md` → se i problemi del preview diventano problemi nella stampa reale
- `slicing_profiles.md` → profili preconfigurati per uso specifico
- `support_strategy.md` → come leggere le zone supporto nel preview
