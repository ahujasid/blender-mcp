# A1 Maintenance — Manutenzione Rilevante

## Manutenzione Assi

### Lubrificanti: quale usare dove

| Lubrificante | Dove usare | Dove NON usare |
|-------------|-----------|----------------|
| Lubricant Oil | Binario X, binario Y, rulli folli (idler pulley) X e Y | Vite senza fine (lead screw) |
| Lubricant Grease | Vite senza fine (lead screw Z), ruota dentata estrusore | **MAI sul binario X-axis** |

### X-axis (binario lineare)
**Frequenza:** Ogni mese
**Materiali:** panno senza pelucchi (dust-free cloth), lubricant oil
**Procedura:**
- Pulire residui filamentosi e granulosi con panno dry
- Applicare oil sul binario X
- Muovere il toolhead avanti/indietro per distribuire uniformemente

**Importante:** Mai usare grease sul binario X — attira polvere e residui.

### Y-axis (guide a ruote metalliche)
**Frequenza:** Ogni mese (oppure quando arriva notifica lubrificazione)
**Materiali:** tessuto non tessuto (non-woven fabric), lubricant oil
**Procedura:**
- Pulire le guide Y da residui e sporco
- Applicare oil sulle guide Y (entrambi i lati)
- Muovere il heatbed avanti/indietro per distribuire il lubrificante su tutta la lunghezza del binario
- Passare alla lubricant oil se in precedenza era stata usata grease (la grease attira polvere)

**Note:** La stampante viene lubrificata in fabbrica ma con quantità minima (per evitare gocciolamenti durante trasporto). Verificare lubrificazione dopo il primo unboxing.

### Z-axis (vite senza fine / lead screw)
**Frequenza:** Ogni 3 mesi
**Materiali:** lubricant grease
**Procedura:**
- Posizionare il toolhead sopra il purge wiper
- Applicare grease nell'area di lavoro delle 2 viti senza fine
- Muovere manualmente l'X-axis su e giù per distribuire la grease su tutto il range

### Cinghie (X, Y, Z belts)
**Frequenza:** Su notifica HMS (sistema di monitoraggio)
**Procedura re-tensioning:**
- **X Belt:** allentare vite di tensionamento dietro il toolhead, muovere toolhead 2–3 volte lungo X, ristrignere
- **Y Belt:** rimuovere cover tensionatore Y, allentare 2 viti, muovere heatbed 2–3 volte, ristrignere e rimettere cover
- **Z Belt:** allentare 2 viti tensionamento, far alzare/abbassare X-axis 2 volte tramite printer, ristrignere

**Attenzione:** Non allentare completamente le viti del tensionatore Y o sarà necessario rimontare il tensionatore.

### Idler pulley (rulli folli X e Y)
**Frequenza:** Ogni 3 mesi
**Materiali:** lubricant oil, hex key
**Procedura X:** rimuovere purge wiper (2 viti), rimuovere cover sinistra (1 vite), spostare toolhead fino a quando la cinghia si allontana dal bordo del rullo, applicare 1 goccia di oil
**Procedura Y:** rimuovere cover superiore Y-axis, applicare oil tra cinghia e rullo folle

## Pulizia Hotend e Filament Path

### Estrusore (extruder gear)
**Quando:** under-extrusion, clog estrusore
**Materiali:** pinzette, chiave hex, air blower
**Procedura base:**
- Rimuovere il blocco di pressione filamento
- Allentare la leva del cutter
- Usare pinzette per rimuovere residui filamentosi interni
- Soffiare con air blower per rimuovere polvere

**Procedura profonda (gear assembly):**
- PLA standard: ogni 5 bobine
- Filamenti CF: ogni 2 bobine
- Se il gear è chiaramente usurato e la pulizia non migliora l'estrusione → sostituire il gear assembly

### Hotend
**Frequenza:** Ogni mese (ogni 5 bobine per non-CF, ogni 2 bobine per CF)
**Materiali:** guanti, panno lint-free, alcool assoluto, pinzette
**Procedura:**
- Rimuovere silicone sock dall'hotend
- Pulire i residui sulla superficie dell'hotend
- Rimuovere il hotend (quick-release buckle sull'A1)
- Con pinzette arrotolare un panno lint-free imbevuto di alcool assoluto
- Pulire la superficie del heating assembly

**Sostituzione hotend:** quando si nota usura/perdite dal nozzle che non migliorano con la pulizia.

### Nozzle Wiper (silicone sul heatbed)
**Frequenza:** Controllo periodico — sostituire se danneggiato
Il wiper in silicone esegue la pulizia grezza del nozzle prima di ogni stampa. Con l'usura, la pulizia diventa meno efficace aumentando il rischio di blob o nozzle clumping.

### Purge Wiper
**Frequenza:** Se intasato o deformato
**Procedura:** allontanare toolhead dal wiper, usare pinzette per rimuovere eccessi, soffiare con air blower
Sostituire se il meccanismo è deformato (causa lost steps o errori di filament change).

### Filament Hub (per single filament, meno rilevante)
Il filament hub connette il PTFE tube al toolhead. Se si accumulano detriti:
- Sintomi: resistenza al caricamento manuale, la spia verde del sensore filamento non si accende anche con filamento inserito (o si accende sempre senza filamento)
- Procedura: smontare il hub con pinzette, rimuovere il AMS Internal Hub Unit, pulire il canale interno

### Sensore filamento
**Quando:** false alarms (sensore mostra filamento anche quando non c'è, o non lo rileva)
**Procedura:** rimuovere 2 viti, estrarre il bracket del sensore, pulire con air blower
**Attenzione:** non tirare troppo il cavo del sensore durante lo smontaggio

### Fan
**Frequenza:** Ogni settimana — ispezione visiva
- **Part cooling fan:** verificare ostruzioni nel canale aria, pulire con panno e pinzette
- **Hotend cooling fan:** allentare 4 viti inferiori, aprire alloggiamento inferiore, verificare e pulire

## Frequenza Consigliata

| Componente | Frequenza | Azione |
|-----------|-----------|--------|
| Part cooling fan | Ogni settimana | Pulizia ispezione visiva |
| Hotend cooling fan | Ogni settimana | Pulizia ispezione visiva |
| X-axis binario | Ogni mese | Oil + pulizia |
| Y-axis guida | Ogni mese | Oil + pulizia |
| Hotend / Nozzle | Ogni mese (5 bobine) | Pulizia + ispezione usura |
| Lead screw Z | Ogni 3 mesi | Grease |
| Idler pulley X/Y | Ogni 3 mesi | Oil |
| Extruder gear | Ogni 5 bobine PLA | Pulizia |
| Extruder gear | Ogni 2 bobine CF | Pulizia |
| Cinghie X/Y/Z | Su notifica HMS | Re-tensioning |
| Silicone sock hotend | Quando danneggiato | Sostituzione |

### Calibrazioni periodiche
Dopo qualsiasi intervento di manutenzione meccanica significativo (sostituzione parti, pulizia profonda), eseguire:
1. Motor Noise Cancellation
2. Vibration Compensation
3. Auto Bed Leveling

percorso: Setting → Maintenance → Calibration
