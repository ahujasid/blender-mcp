# Calibration — Calibrazione A1

## Bed Leveling

### Tipi di leveling sull'A1

**Leveling rapido (pre-stampa):**
- Eseguito automaticamente prima di ogni stampa se "Bed Leveling" è attivo
- Con BS 1.8 o precedente: 5 punti + confronto con dati precedenti
- Con BS 1.9+ e firmware 1.03+: **partial bed leveling** — sonda solo l'area del modello (basata sui contorni), riduce significativamente il tempo di preparazione

**Leveling completo (da schermo):**
- Setting → Maintenance → Calibration → Auto Bed Leveling
- Griglia 21×21 per A1 (vs 18×18 per A1 mini)
- Più accurato, consigliato dopo: sostituzione heatbed, montaggio/smontaggio, prima di stampe critiche
- Prerequisito: nozzle pulito e privo di residui

### Come funziona il leveling su A1
Il nozzle scende fino a toccare il heatbed — il sensore eddy current sopra l'hotend rileva il contatto. Genera una mappa di altezza che viene usata per compensare le variazioni durante la stampa (il Z viene aggiustato dinamicamente in ogni punto XY).

### Manual Bed Tramming
Usato quando il leveling automatico fallisce o dopo sostituzione/smontaggio del heatbed.

**Procedura:**
1. Rimuovere silicone sock dal nozzle, assicurarsi che il nozzle sia pulito
2. Allentare completamente le 2 viti di bloccaggio heatbed sotto il heatbed
3. Rimuovere la piastra, pulire la superficie del heatbed
4. Stringere le 3 viti di livellamento di 1 giro ciascuna (o fino a sentirle a filo con il supporto inferiore)
5. Scaricare il file `a1_manual_bed_screws_adjust_assist.gcode` e copiarlo su MicroSD
6. Avviare il file come fosse una stampa normale
7. La stampante si posiziona su ogni angolo — regolare le viti: senso orario = aumenta distanza nozzle-bed, senso antiorario = riduce distanza
8. Usare un foglio di carta per verificare il contatto: il nozzle deve sfiorare senza premere

**Importante:** Non spegnere la stampante durante il tramming — spegnimento in posizione errata richiede ripristino.

### Cause comuni di leveling failure
- Nozzle sporco o con residui di filamento
- Heatbed non su superficie piana (controllare i 4 angoli del piano di appoggio)
- Piastra posizionata male o non magneticamente aderente
- Heatbed scollegato o danneggiato
- Sensore eddy current guasto

## Flow Rate

### Flow Dynamics Calibration (Pressure Advance)
Compensazione del lag della pressione di estrusione. Equivalente al "Pressure Advance" di Klipper.

**Cosa fa:** Durante accelerazione aumenta l'estrusione per anticipare la pressione; durante decelerazione la riduce per evitare oozing. Risultato: angoli più puliti, transizioni precise, meno stringing ad alta velocità.

**Quando eseguire:**
- Nuovo filamento di marca/tipo diverso
- Nozzle usurato
- Dopo sostituzione nozzle
- Dopo cambio di Maximum Volumetric Speed o temperatura nel profilo filamento

**Come eseguire (automatico):**
In Bambu Studio: Device → Calibrate → selezionare opzioni calibrazione
Oppure da schermo: le stampe eseguono calibrazione automatica per i filamenti configurati

**Limitazioni calibrazione automatica:**
- Filamento umido → risultati inaffidabili (essiccare prima)
- Filamento trasparente → può influenzare lettura lidar (su X1 — meno rilevante su A1)
- Piastra non aderente → calibration lines non si attaccano
- Materiali molli come TPU → alta probabilità di fallimento calibrazione

**Flow ratio manuale:**
Se il filamento richiede aggiustamenti manuali del flow ratio (filamenti speciali, terze parti):
- Aumentare se si notano spazi vuoti tra le linee
- Diminuire se si notano eccessi di materiale/blobbing
- Per filamenti Bambu ufficiali: non modificare il flow ratio di default

### Calibrazione Flow Rate manuale (microlidar)
Funzione avanzata in sviluppo (usare con cautela per utenti esperti). Misura il volume reale di estrusione tramite sensori. Utile per filamenti irregolari o speciali.

## Pressure Advance

Vedi sezione Flow Rate sopra — su Bambu Studio/A1 si chiama "Flow Dynamics Calibration" ed è il corrispettivo del Pressure Advance.

**Parametro PA in BS:** Process → Printer → Flow Dynamics (o nel preset filamento)
- Valore tipico PLA: varia per filamento, calibrato automaticamente
- Sintomi PA troppo alto: under-extrusion negli angoli
- Sintomi PA troppo basso: blobs/blobbing negli angoli, oozing

## Primo Layer

### Checklist primo layer perfetto
1. Piastra pulita con acqua calda e detergente (non toccare la superficie con le dita dopo)
2. Selezionare il tipo di piastra corretto in BS (ogni piastra ha Z-offset e temperatura diversi)
3. Nozzle pulito (il wiper pre-stampa effettua pulizia automatica)
4. Bed leveling recente e accurato
5. Prima layer height = 0.2 mm (default per nozzle 0.4 mm)
6. Heatbed alla temperatura corretta per piastra e filamento:
   - Textured PEI + PLA: 55–65 °C
   - Cool Plate + PLA: ~35 °C (richiede glue stick)

### Problemi e correzioni primo layer

**Primo layer non aderisce:**
- Verificare tipo piastra selezionato in BS (errore frequente)
- Lavare la piastra
- Eseguire bed leveling completo da schermo
- Verificare temperatura heatbed corretta per la combinazione piastra/filamento

**Primo layer troppo schiacciato (elephant foot):**
- Z-offset troppo basso
- Usare Elephant Foot Compensation in BS (Process → Quality)
- Valore tipico: 0.1–0.2 mm

**Primo layer con bolle o irregolarità:**
- Filamento umido → essiccare
- Nozzle parzialmente intasato
- Heatbed sporco o con residui di stampe precedenti

### Bed Leveling vs First Layer Quality
Il leveling automatico corregge la non-planarità del bed. Se il primo layer è pessimo nonostante il leveling, verificare:
1. Z-offset globale (nozzle troppo lontano o troppo vicino)
2. Pulizia piastra
3. Tipo di piastra selezionato in BS

Per ajustare il live Z-offset durante la stampa: disponibile da Bambu Studio durante la stampa (Device → live adjust Z).
