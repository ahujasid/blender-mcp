# A1 Screen Workflow — Operazioni da Touchscreen

## Menu Principale

Dalla homepage del touchscreen sono accessibili 5 sezioni:
1. **Print Files** — file .gcode/.3mf sulla MicroSD
2. **Filament** — gestione spool (External Spool per single filament)
3. **Control** — temperatura, velocità, fan, movimento manuale
4. **Setting** — account, rete, dispositivo, SD card, manutenzione, opzioni stampa
5. **Assistant** — diagnostica errori con soluzioni

Angolo in alto a destra: temperatura nozzle, temperatura heatbed, stato camera, stato rete.

## Gestione Stampa

### Avvio da Print Files
- Selezionare il file sulla MicroSD (include file inviati via Wi-Fi)
- Prima di avviare, opzioni disponibili:
  - **Timelapse:** registra ogni fase della stampa
  - **Bed Leveling:** leveling parziale basato sui contorni del modello (attivo automaticamente con firmware 1.03 + BS 1.9+, non serve abilitarlo manualmente)
  - **Dynamic Flow Calibration:** sincronizza risposta flusso con movimento — esegue prima della stampa

### Gestione Filament (External Spool)
- Sezione **External Spool** sotto Filament
- **Load / Unload:** bottone diretto
- **Edit:** selezione produttore, tipo, colore, dynamic pressure control
- **Extruder indicator:** pallino verde = sensore filamento ha rilevato filamento nell'estrusore

### Control durante stampa
**Temperatura:**
- Nozzle Temperature: inserire valore → imposta temperatura nozzle
- Heatbed Temperature: inserire valore → imposta temperatura heatbed

**Modalità velocità:**
- **Ludicrous:** 166% velocità e accelerazione normali
- **Sport:** 140% velocità e accelerazione normali
- **Standard:** velocità normale (default)
- **Silent:** 50% velocità e accelerazione normali

**Fan:** Attiva/disattiva Part Cooling Fan e imposta velocità

**LED:** on/off illuminazione camera

**Extruder manuale:** bottoni +/- per estrudere/ritrarre 1 cm di filamento

### Controllo XYZ
- Dial XY: muove toolhead su X o heatbed su Y
- Print Plate Lift: muove X-axis su/giù (Z)

## Calibrazioni da Schermo

Percorso: **Setting → Maintenance → Calibration**

Tre opzioni disponibili per A1:

1. **Motor Noise Cancellation**
   - Riduce rumore motori durante stampa
   - Utile dopo installazione/sostituzione parti
   - Migliora finitura superficiale specialmente ad alta velocità

2. **Vibration Compensation**
   - Corregge la posizione del toolhead in tempo reale in presenza di vibrazioni
   - Eseguire dopo modifiche meccaniche o peggioramento qualità superficiale

3. **Auto Bed Leveling**
   - Leveling completo 21×21 punti (A1)
   - Più accurato del leveling pre-stampa
   - Eseguire dopo: sostituzione/smontaggio heatbed, piastra cambiata, problemi primo layer persistenti
   - Prerequisito: nozzle pulito e libero da residui

### Nozzle Reset
**Setting → Maintenance → Nozzle**
- Dopo sostituzione nozzle o hotend, resettare per assicurare qualità stampa

### Print Options
**Setting → Print Options:**
- **Filament Tangle Detection:** pausa automatica se rilevato aggrovigliamento
- **Auto-Recovery from Step Loss:** homing e ripresa automatica dopo step loss su XYZ
- **Nozzle Clumping Detection:** stop automatico se filamento avvolge il nozzle
- **Build Plate Position Detection:** verifica presenza piastra prima della stampa
- **Sounds:** suoni all'accensione, inizio e fine stampa

### Camera Option
**Setting → Camera Option:**
- **Video:** registrazione durante stampa
- **Timelapse Fade on Mode:** effetto zoom-in/out sul primo layer

### Firmware
Visualizza versione corrente, note di rilascio, aggiornamento offline da MicroSD.

### LAN Only
Quando attivo: stampante accessibile solo da rete locale, non da internet.

### Factory Reset
Ripristina impostazioni di fabbrica — irreversibile.
