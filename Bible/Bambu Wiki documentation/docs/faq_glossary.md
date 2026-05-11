# FAQ & Glossary — A1 e Stampa 3D

## Glossario Termini Chiave

### Componenti A1

**Toolhead:** Il componente mobile sull'asse X che contiene l'estrusore, l'hotend, i fan, la cutter unit, il filament hub e il sensore filamento.

**Hotend / Nozzle:** Componente che scalda e fonde il filamento prima dell'estrusione. Il "nozzle" è la parte terminale con il foro di uscita. Su A1 è un design integrato (nozzle + heat sink in uno) con rilascio rapido (quick-release buckle).

**Hotend Heating Assembly:** Fornisce calore all'hotend. Abilita quick-swap per sostituzione facile.

**Extruder Unit:** Componente che controlla il movimento del filamento e lo spinge attraverso l'hotend. Comprende il motore, il gear assembly e il lever.

**Extruder Idler Lever:** Applica pressione contro il rullo folle dell'estrusore per mantenere la presa sul filamento.

**Hotend Fan:** Raffredda il hotend e il heating assembly (cold end cooling — previene heat creep).

**Part Cooling Fan:** Raffredda il filamento appena deposto sul pezzo (5015 centrifugal fan con 2 uscite opposte per coprire 360°).

**Filament Hub:** Connette i PTFE tube al toolhead. Contiene il sensore filamento. Su A1 con single filament: 1 PTFE tube entra dall'external spool holder.

**Filament Sensor:** Sensore hall dentro il filament hub — rileva presenza e movimento del filamento.

**Filament Cutter Lever:** Leva meccanica che aziona la cutter blade. Rilevante per AMS (non usato in single filament normale).

**Heatbed:** Piano riscaldato che si muove sull'asse Y. Raggiunge max 100 °C. Mantiene la piastra in posizione magnetica.

**Build Plate:** Piastra di stampa che aderisce magneticamente al heatbed. Modello stampato sopra.

**Nozzle Wiper (silicone):** Componente in silicone sul heatbed — pulisce il nozzle (coarse wipe) prima di ogni stampa.

**Purge Wiper:** Raccoglie e smaltisce il filamento di spurgo durante cambio filamento.

**X-axis Linear Rail:** Guida lineare in metallo per il toolhead sull'asse X.

**Y-axis Linear Rail:** Guida per il heatbed sull'asse Y (ruote metalliche).

**Z-axis:** Movimento verticale — doppio lead screw + cinghia sincrona + Z motor.

**Belt Tensioner (X/Y/Z):** Tensionatori delle cinghie, ajustabili manualmente. Il BTM monitora la tensione.

**Camera:** Camera integrata per monitoraggio remoto, timelapse, rilevamento difetti.

**MicroSD:** Memoria 32 GB pre-installata (necessaria — l'A1 non ha memoria interna).

**Eddy Current Sensor:** Sensore sopra l'hotend — rileva il contatto nozzle-heatbed durante il bed leveling.

### Terminologia di Stampa 3D

**FDM (Fused Deposition Modeling):** Tecnologia di stampa che estrude filamento fuso layer per layer.

**Layer Height:** Altezza di ogni strato. Più basso = più dettaglio, più tempo.

**Line Width:** Larghezza del filamento estruso. Solitamente pari al diametro del nozzle.

**Infill:** Struttura interna del pezzo. Densità (%) e pattern (gyroid, grid, cubic, ecc.).

**Wall / Perimeter:** Pareti esterne del pezzo. Più pareti = più resistente.

**Seam:** Giunzione tra inizio e fine di ogni perimetro — inevitabile in FDM.

**Retraction:** Il filamento viene ritratto nel nozzle prima di un travel move per ridurre lo stringing.

**Z-hop:** Sollevamento del nozzle durante il travel move per evitare di sfregare sul pezzo.

**Travel Move:** Movimento del toolhead senza estrusione (da un punto all'altro).

**Overhang:** Parte del modello che sporge senza supporto sottostante. Sopra 45° richiedono supporti.

**Bridge:** Filamento esteso in aria tra due punti di appoggio. Funziona bene con buon raffreddamento.

**Support:** Struttura temporanea aggiunta dallo slicer per sostenere overhang e bridge critici.

**Brim:** Bordo piatto a singolo layer intorno alla base del pezzo — migliora adesione, riduce warping.

**Elephant Foot:** Espansione del primo layer oltre il contorno desiderato — correggi con Elephant Foot Compensation.

**Heat Creep:** Risalita del calore dal hotend verso il cold end → ammorbidimento prematuro del filamento → clog.

**Warping:** Sollevamento dei bordi del pezzo dalla piastra durante o dopo la stampa.

**Under-extrusion:** Il nozzle estrude meno materiale del dovuto → linee rade, zone mancanti.

**Over-extrusion:** Il nozzle estrude troppo materiale → blob, superficie irregolare.

**Volumetric Speed (mm³/s):** Volume di filamento estruso per secondo. Limit fisico dell'hotend.

**Maximum Volumetric Speed (MVS):** Limite massimo del hotend — superarlo causa under-extrusion.

**Flow Dynamics Calibration:** Equivalente a Pressure Advance/Linear Advance — compensa il lag della pressione nel nozzle per angoli puliti e assenza di oozing.

**Flow Ratio / Flow Rate:** Moltiplicatore della quantità di filamento estruso. 1.0 = 100% del valore calcolato.

**Cold Pull:** Tecnica di pulizia: riscaldare il nozzle, inserire filamento, far solidificare parzialmente, poi estrarre di forza per rimuovere residui.

**HTD (Heat Deflection Temperature):** Temperatura alla quale un materiale comincia a deformarsi sotto carico. PLA: ~57 °C.

**Shrinkage:** Contrazione del materiale durante il raffreddamento dopo l'estrusione.

**Manifold:** Mesh 3D "chiusa" e corretta senza buchi, normali invertite o geometrie problematiche — necessaria per lo slicing corretto.

**G-code:** Linguaggio di istruzioni che controlla la stampante (posizione, temperatura, velocità).

**3MF:** Formato file che contiene sia il modello 3D che tutti i parametri di stampa di BS.

**Slicer:** Software che converte un modello 3D in G-code (es. Bambu Studio).

**HMS (Health Management System):** Sistema di monitoraggio della stampante che notifica manutenzione necessaria (es. lubrificazione, tensionamento cinghie).

## FAQ A1

### Specifiche
**Volume di stampa A1:** 256 × 256 × 256 mm³
**Temperatura max nozzle A1:** 300 °C
**Temperatura max heatbed A1:** 100 °C
**Nozzle di default:** 0.4 mm stainless steel
**Rumore in Silent mode:** ~48 dB
**Consumo in stampa PLA (220V):** ~95 W medi
**Consumo in idle:** 5 W

**L'A1 ha bisogno della MicroSD?** Sì — non ha memoria interna. Deve essere inserita per stampare (anche quando si invia via Wi-Fi, la stampa viene salvata sulla SD).

**Posso stampare ABS/ASA su A1?** Non è raccomandato per pezzi grandi o ad alta densità infill — A1 è open-frame, rischio warping e riduzione resistenza interlayer. Piccoli pezzi a basso infill possono funzionare ma non è garantito. ABS emette fumi — ventilare bene.

**Posso stampare PLA-CF su A1?** Sì, ma richiede nozzle in hardened steel (non stainless). Il nozzle stainless incluso si usura rapidamente con filamenti abrasivi.

### Funzionamento

**Come si cambia la velocità durante la stampa?** Dal touchscreen (Control → Speed), da Bambu Handy o da Bambu Studio durante la stampa. Le modalità sono: Silent, Standard, Sport, Ludicrous.

**L'A1 supporta il power loss recovery?** Sì — dopo il riavvio si può scegliere di riprendere la stampa interrotta.

**Come funziona il filament runout?** Il sensore hall nel filament hub rileva l'assenza di filamento e mette in pausa la stampa. Con external spool: pausa e notifica.

**Il LED bianco vicino allo schermo?** Lampeggiante = messaggi pendenti dell'Assistant (diagnostica); fisso = stato sistema normale.

**Posso stampare offline (senza internet)?** Sì, via MicroSD o via LAN Mode.

**L'A1 supporta autoShutdown?** No — entra in low power mode a fine stampa ma non si spegne completamente.

**I timelapse sono supportati?** Sì — salvati sulla MicroSD.

### Manutenzione e Calibrazione

**Quando eseguire il Bed Leveling?** Automatico prima di ogni stampa (con opzione attiva). Leveling completo da schermo dopo sostituzione heatbed o problemi persistenti al primo layer.

**Lubricant Oil o Grease sul binario Y?** Oil — la grease attira polvere e detriti sulle guide Y. Se precedentemente usata grease, toglierla e sostituire con oil.

**Ogni quanto lubrificare?** Y-axis: mensile. X-axis: mensile. Lead screw Z: ogni 3 mesi.

**Il wiper area della piastra si usura?** Sì, è normale. L'area dove il nozzle pulisce si graffia nel tempo — non influenza la qualità di stampa.

## FAQ Bambu Studio

**Che differenza c'è tra Filament Preset e Process Preset?** Il Filament Preset contiene impostazioni specifiche del filamento (temperatura, cooling, retraction). Il Process Preset contiene parametri di stampa (layer height, pareti, infill, supporti). Selezionare entrambi prima di fare slice.

**Come si aggiunge un Override a un singolo oggetto?** In BS, selezionare l'oggetto nell'Object List → modificare i parametri nel pannello inferiore sinistro. Un'icona lucchetto arancione indica che quel parametro è stato modificato rispetto al global.

**Cosa fa "Bed Leveling" nell'interfaccia di invio stampa?** Esegue il leveling adattivo (parziale, solo sull'area del modello) prima di iniziare la stampa. Raccomandato lasciarlo sempre attivo.

**Cosa fa "Dynamic Flow Calibration" nell'interfaccia di invio?** Esegue la calibrazione della risposta del flusso (Flow Dynamics/Pressure Advance) prima della stampa. Utile con filamenti nuovi o dopo sostituzione nozzle. Può essere disabilitato per stampe successive con lo stesso filamento.

**Posso stampare senza account?** Sì — si può usare la SD card o LAN Mode senza login. Il login è necessario per sync preset e print history su cloud.
