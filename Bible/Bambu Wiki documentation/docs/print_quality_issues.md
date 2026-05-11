# Print Quality Issues — Problemi di Qualità Stampa

## Stringing/Oozing

**Definizione:** fili sottili di filamento tra le parti del modello, causati da oozing del nozzle durante i movimenti di viaggio.

**Cause e soluzioni (PLA):**

1. **Filamento umido** → essiccare il filamento prima dell'uso (PLA Basic normalmente non serve, ma Silk/Wood/CF sì)

2. **Temperatura nozzle troppo alta** → ridurre di 5–10 °C (PLA è più fluido a temperatura alta)

3. **Retraction insufficiente** → aumentare lunghezza retraction. Limite: non superare 2 mm (rischio clog). Aumentare anche la velocità di retraction.

4. **Long travel path** → abilitare "Avoid crossing walls" in BS; ridurre distanza tra modelli sulla piastra

5. **Nozzle troppo grande** → più materiale = più probabilità di oozing a parità di condizioni

6. **Seam position = Random** → causa puntini/zits sulla superficie, non veri stringing — cambiare in Aligned o Back

**Parametri BS da verificare:**
- Filament Settings → Retraction → Length (default A1: ~0.8–1 mm)
- Process → Quality → Avoid crossing walls: ON

## Warping

**Definizione:** sollevamento dei bordi del pezzo dalla piastra durante o dopo la stampa.

PLA ha warping minimo, ma può verificarsi su pezzi grandi, geometrie sottili/alte o in condizioni ambientali sfavorevoli.

**Soluzioni:**

1. **Pulire la piastra** con acqua calda e detergente prima di stampare

2. **Verificare heatbed temperature corretta** per la piastra:
   - Textured PEI + PLA: 55–65 °C
   - Cool Plate + PLA: ~35 °C

3. **Aggiungere Brim** (Process → Other → Brim): aggiunge un bordo piatto intorno al modello per aumentare l'adesione

4. **Dischi anti-warping** (tasto destro in BS → Add part → Disc): applicare ai bordi critici del modello

5. **Evitare correnti d'aria** durante la stampa (ventilatori, finestre aperte)

6. **Aumentare temperatura heatbed** di 5 °C se il problema persiste

**Modello che si stacca durante stampa (troppo alto/sottile):**
- Attivare supporti
- Ridurre velocità e accelerazione (Silent mode)
- Riprogettare il pezzo in posizione più stabile (coricato)

## Layer Adhesion

### Interlayer cracking
PLA ha buona adesione tra layer. Cracking si verifica principalmente con:
- Temperatura nozzle troppo bassa per la velocità impostata
- Velocità troppo alta senza aumentare la temperatura

**Soluzioni PLA:**
- Aumentare temperatura nozzle di 5–10 °C
- Ridurre velocità stampa
- Aumentare numero di pareti (wall loops)
- Aumentare infill density

### Layer artifacts (righe orizzontali visibili)
Cause principali:
1. **Zona di transizione sezione trasversale** (es. fondo di una scatola): bridging che tocca la parete esterna causa stress di ritiro → aggiungere raccordi/chamfer interni in Blender per evitare che il bridge tocchi la parete
2. **Cambio flow rate** dopo bridging: velocità diverse causano gloss diverso (più visibile su Silk)
3. **Variazione velocità tra sezioni**: verificare il grafico velocità in BS prima di stampare

## Clogging/Heat Creep

### Heat Creep (tipico PLA sull'A1)
**Definizione:** il calore del hotend risale nel cold end, ammorbidendo il filamento prima che raggiunga la zona di fusione.

**Perché il PLA è il più vulnerabile:** glass transition temperature ~57 °C — la più bassa tra i materiali comuni.

**Sintomi:** clog progressivo, estrusione irregolare, rumore di "click" dall'estrusore.

**Cause su A1:**
- Temperatura ambiente > 30 °C (estate) + heatbed caldo
- Fan del hotend cooling ostruito o guasto
- Velocità stampa molto bassa (il filamento staziona troppo a lungo nella zona calda)

**Prevenzione:**
- Mantenere ambiente ventilato, temperatura 10–30 °C
- Ridurre heatbed temperature in estate (45–50 °C invece di 55 °C per PLA)
- Verificare funzionamento fan del hotend cooling (settimanale)
- NON usare PLA con printer chiuso/surriscaldato

**Soluzione se avvenuto:**
- Riscaldare a 220 °C e spingere filamento PLA manualmente nel nozzle per verificare fluidità
- Se ostruzione: cold pull + procedura di unclogging

### Clog estrusore
**Sintomi:** click dell'estrusore, sotto-estrusione, stampa si interrompe.

**Cause:**
1. Heat creep (vedi sopra)
2. Gear dell'estrusore bloccato da detriti filamento
3. Filamento deformato all'interno del gear

**Soluzioni:**
- Riscaldare a 220 °C, estrudere filamento PLA e osservare: se il filamento esce dritto, fluido e lungo = interno OK; se corto/ruvido = clog parziale
- Pulire l'estrusore con pinzette e air blower
- Se il gear è usurato → sostituire

### Clog nozzle
**Cause per PLA:**
- Detriti nel filamento (filamento di bassa qualità o esposto a polvere)
- Residui da filamenti ad alta temperatura usati in precedenza (es. cambio da ABS a PLA senza cold pull)
- Nozzle 0.2 mm con filamenti contenenti particolati

**Unclogging nozzle 0.4 mm:**
Usare lo unclogging pin tool incluso. Oppure procedura hot pull (riscaldare a 250 °C e spingere delicatamente).

**Unclogging nozzle 0.2 mm:**
- NON usare pin tool (foro troppo piccolo)
- Metodo: wrench caldo + cold pull ripetuti
- NO torcia/fiamma diretta (danneggia il hotend in modo irreparabile)

## Superfici

### Under-extrusion (globale o locale)
**Sintomi:** linee rade, zone del modello prive di materiale.

**Cause e soluzioni:**

1. **Spool aggrovigliato o PTFE tube piegato** → verificare prima di stampare
2. **Velocità > MVS** → ridurre velocità o aumentare temperatura nozzle
3. **Estrusore gear sporco** → pulire
4. **Clog parziale nozzle** → cold pull + pulizia
5. **PA value errato** → angoli con poco materiale indicano PA non calibrato correttamente
6. **Flow ratio insufficiente** → per filamenti terze parti, aumentare leggermente (se Bambu ufficiale, non toccare)

### Bridging scadente
**Definizione:** i "ponti" (filamenti sospesi tra due punti di appoggio) si abbassano o si deformano.

**Miglioramenti:**
- Aumentare raffreddamento (part cooling fan al massimo durante bridging)
- Ridurre velocità bridging in BS (Process → Quality → Bridge settings)
- Orientare il modello in modo che i bridge siano più corti
- Bridge PLA: regge bene fino a ~50–60 mm con raffreddamento adeguato

### Overhang scadente
**Quando si verifica:** angolo di overhang > 45° dalla superficie heatbed.

**Soluzioni:**
1. Aggiungere supporti (overhang > 45°)
2. Abilitare "Slow down for overhangs" in BS — riduce velocità nelle zone a sbalzo
3. Aumentare raffreddamento
4. Ottimizzare orientamento in Blender per ridurre overhang

### Variazione gloss/finitura
**Causa:** velocità diverse tra sezioni causano diverso tempo di permanenza del filamento nel hotend → gloss differente (tipico su PLA Silk).

**Soluzione:** normalizzare la velocità outer wall; stampare più oggetti insieme per evitare rallentamenti da minimum layer time.

### Dots/Zits sulla superficie
**Causa principale:** Seam Position impostata su "Random" → cambiare in "Aligned" o "Back".
**Seconda causa:** filamento umido → piccole bolle di vapore durante l'estrusione.

### Seam (giunzione dei layer)
Il seam è inevitabile in FDM. Opzioni in BS (Process → Quality → Seam):
- **Nearest:** nasconde il seam negli angoli concavi/convessi del modello (ottimo per forme irregolari)
- **Aligned:** seam allineato verticalmente (più visibile ma ordinato)
- **Back:** seam nel retro del modello
- **Random:** distribuisce il seam casualmente (NO — causa dots)
- **Scarf seam:** opzione avanzata che sfuma il seam (disponibile nelle versioni recenti di BS)

### Finitura diversa tra inner e outer walls
Normale in caso di velocità molto diverse. Impostare velocità outer wall uguale o vicina alle velocità più lente presenti nel modello.

## Primo Layer

### Primo layer non aderisce
Vedere documento build_plates.md — sezione Troubleshooting Adesione.

### Primo layer con superficie non uniforme
- Eseguire bed leveling completo
- Verificare pulizia piastra
- Verificare che il nozzle sia pulito (wiper può non rimuovere tutti i residui se sono blobbing)

### Filament tangles e filamento sciolto
**Filamento aggrovigliato nella bobina:**
- Non rimuovere il nastro adesivo finché pronto all'uso
- Se aggrovigliato esternamente: riavvolgere manualmente, reinserire
- Se aggrovigliato internamente nella bobina riutilizzabile Bambu: aprire bobina, localizzare il punto bloccato, liberare con cura, richiudere

**Bobina sfaldata (filamento sciolto):**
- Stampare il fixing tool (disponibile su MakerWorld)
- Inserire nella bobina e stringere
- Se la bobina non entra nel spool holder: stampare un filament holder esterno

### Heatbed non si scalda
**Sintomi:** temperatura heatbed mostra 0 °C o non raggiunge la temperatura impostata.

**Cause frequenti:**
1. Cavo del heatbed scollegato o danneggiato (noto problema su alcune unità A1 → controllare stato cavo)
2. Connessione al mainboard allentata

**Procedura:** verificare connessioni cavo heatbed e cavo segnale come descritto nella guida A1 Heatbed Disassembly. Power off prima di qualsiasi intervento elettrico.
