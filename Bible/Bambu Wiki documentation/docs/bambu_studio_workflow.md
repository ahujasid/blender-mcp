# Bambu Studio Workflow — Da Blender ad A1


### Architettura dei preset
BS usa un sistema a tre livelli:

| Livello | Cosa contiene | Esempio |
|---------|--------------|---------|
| **Printer Preset** | Hardware: velocità massima assi, area stampa, diametro nozzle | "Bambu Lab A1 0.4 nozzle" |
| **Filament Preset** | Temperatura, heatbed, flow ratio, cooling, retraction | "Bambu PLA Basic @A1" |
| **Process Preset** | Layer height, pareti, infill, supporti, seam | "0.20mm Standard @A1" |

- I **System Preset** non sono modificabili direttamente — creare una copia come **User Preset**
- I **Project Preset** sono salvati nel file .3mf — visibili solo in quel progetto

### Workflow Blender → A1
1. **In Blender:** modellare, verificare geometria manifold, esportare come STL o 3MF
2. **In Bambu Studio:**
   - Import file (drag & drop o File → Import)
   - Selezionare Printer Preset (A1 + nozzle)
   - Selezionare Filament Preset (PLA Basic/Bambu o filamento usato)
   - Selezionare Process Preset (layer height)
   - Verificare orientamento modello per resistenza e overhangs
   - Configurare supporti se necessario
   - Slice
   - Verificare con le viste slicing
   - Inviare alla stampante via Wi-Fi o SD

## Parametri Chiave

### Layer Height — Selezione rapida
Con nozzle 0.4 mm, i preset disponibili:
- 0.08 mm: ultra-fine (miniature, dettaglio estremo)
- 0.12 mm: fine
- 0.16 mm: high quality
- **0.20 mm: standard** — uso quotidiano, bilanciamento qualità/velocità
- 0.24 mm: draft
- 0.28 mm: extra draft (rapid)

**Adaptive Layer Height:** utile per modelli con superfici curve. BS varia automaticamente il layer height tra 0.08 e 0.28 mm in base alla geometria. Attivare per sfere, cilindri, superfici organiche.

### Velocità — Preset da schermo
Durante la stampa è possibile cambiare modalità velocità dal touchscreen o da BS:
- **Silent:** 50% della velocità normale
- **Standard:** velocità normale
- **Sport:** 140% — raccomandato aumentare temperatura nozzle +5–10 °C
- **Ludicrous:** 166% — aumentare nozzle temperature +10 °C

### First Layer
- First layer height default: 0.2 mm (50% del diametro nozzle)
- First layer speed: ridotta automaticamente (20–30% della velocità normale)
- Fan cooling: disabilitato sul primo layer per favorire adesione

### Caricamento filamento (external spool)
1. Inserire il filamento nel PTFE tube e spingerlo nel toolhead fino a stop meccanico
2. Dal touchscreen: Filament → External Spool → Edit (verificare tipo) → Load
3. Quando il nozzle raggiunge ~250 °C: spingere manualmente il filamento ancora
4. Osservare estrusione → quando fluisce regolare → "Done"

## Slicing e Invio

### Processo di slicing
1. Modello importato nella build plate virtuale
2. Posizionare (orientamento, posizione, scala)
3. Verificare con Object List (pannello sinistro) la struttura del progetto
4. Slice (Ctrl+R o bottone Slice)

### Vista slicing — Strumenti di verifica
Dopo lo slicing, verificare:
- **Line type:** colori diversi per outer wall, inner wall, infill, bridge, support — identificare zone anomale
- **Speed:** verificare che non ci siano zone con velocità molto diverse (causa variazioni gloss)
- **Layer time:** layer molto rapidi (<3s) attiveranno raffreddamento massimo e rallentamento
- **Flow:** verificare che non superi il MVS del filamento in nessun layer
- **Fan speed:** verifica del profilo di raffreddamento

### Invio stampa
- **Via Wi-Fi:** Device tab → selezionare printer → Send (richiede Network Plugin e printer connessa alla stessa rete)
- **Via LAN Mode:** stessa procedura ma senza accesso internet
- **Via SD:** esportare .gcode su MicroSD, inserire nella stampante

**Prerequisiti per invio:**
- Selezionare il tipo di piastra corretto (influisce su temperatura heatbed e Z-offset)
- Abilitare/disabilitare Bed Leveling e Flow Calibration a seconda del bisogno

### Pausa e layer custom
Nella vista slicing è possibile:
- Aggiungere pause a layer specifici (per inserire magneti, inserti, ecc.)
- Inserire G-code custom a layer specifici
- Cambiare filamento a layer specifici

## Features Utili

### Object List (pannello sinistro)
Vista gerarchica: Plates → Objects → Parts → Modifiers.
- Click su un oggetto per vedere/modificare i parametri specifici a livello Object
- Override locali: cambiano il comportamento solo per quell'oggetto senza alterare il preset globale
- Icona lucchetto arancione = parametri modificati rispetto al global

### Parametri a livello Object e Part
BS supporta tre livelli di override:
- **Global:** si applica a tutto il progetto
- **Object:** si applica all'oggetto selezionato
- **Part:** si applica alla parte selezionata (quando un oggetto è composto da più parti)

Utile per: stampare parti dello stesso modello con densità infill diverse, o con seam position diversa.

### Modificatori (Modifier Mesh)
Possibilità di importare un mesh ausiliario in BS per applicare parametri diversi solo alla zona coperta da quel mesh. Esempio: aumentare infill in una zona critica di un pezzo senza modificare il resto.

### Support Painting
Tool per dipingere manualmente dove aggiungere o rimuovere supporti. Accessibile dopo import modello.

### Color Painting
Permette di assegnare filamenti diversi a zone diverse dello stesso modello per stampe multicolore. Non rilevante per single filament.

### Timelapse
Setting → Camera Option → Timelapse: registra la stampa. Ogni layer viene fotografato.

### 3MF compatibility
BS salva i progetti come .3mf — formato che contiene sia il modello 3D che tutti i parametri di stampa. Aprire un .3mf precedentemente creato ripristina l'intera configurazione.

## Workflow Blender → A1

### Checklist pre-export da Blender
- [ ] Verificare che la mesh sia manifold (senza buchi, faces interne, normali invertite)
- [ ] Applicare tutte le trasformazioni (Apply Scale, Rotation, Location)
- [ ] Verificare dimensioni in mm (Blender default è metro — verificare scale)
- [ ] Esportare come STL o 3MF (File → Export → STL)
- [ ] Niente parti troppo sottili (<0.4 mm) che verrebbero ignorate dallo slicer

### Checklist in Bambu Studio
- [ ] Selezionare A1 + nozzle corretto come Printer Preset
- [ ] Selezionare filamento corretto (es. "Bambu PLA Basic @A1")
- [ ] Orientare il modello per minimizzare overhang e massimizzare resistenza
- [ ] Scegliere layer height adeguato al dettaglio richiesto
- [ ] Verificare supporti necessari (angoli > 45°)
- [ ] Verificare seam position
- [ ] Controllare la vista Speed e Flow prima di inviare
- [ ] Selezionare tipo piastra corretto (Textured PEI per uso standard)
- [ ] Attivare Bed Leveling per le prime stampe o dopo cambio piastra

### Suggerimenti pratici
- Salvare sempre il progetto come .3mf prima di inviare (conserva tutta la configurazione)
- Per pezzi con accoppiamenti precisi: stampare un test piccolo prima con le stesse impostazioni
- Per pezzi alti e stretti: usare Silent mode o aggiungere dischi anti-warping agli angoli
- Se si cambia nozzle: aggiornare Printer Preset in BS per riflettere il nuovo diametro
