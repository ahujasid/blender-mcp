# Bambu A1 — Knowledge Base Index

Contesto: Bambu A1, solo PLA, single filament, no AMS.
Carica questo file sempre nel contesto. Usa il tag [topic_id] per richiedere il documento specifico quando serve.

## [a1_specs]
**Specifiche hardware A1: dimensioni, nozzle, velocità, temperature**
Quando usarlo: devi sapere build volume, nozzle disponibili, velocità max, limiti fisici
File: `Printer Infos/a1_specs.md`

Contenuto: Volume 256×256×256 mm³, nozzle 0.2/0.4/0.6/0.8 mm (stainless/hardened), max 300 °C nozzle / 100 °C heatbed, auto bed leveling 7×7, vibration compensation, accessori inclusi, regole lubrificanti.

## [a1_screen_workflow]
**Operazioni da touchscreen: menu, calibrazione, avvio stampa**
Quando usarlo: devi capire come si avvia o gestisce una stampa dalla stampante
File: `Printer Infos/a1_screen_workflow.md`

Contenuto: Menu principale (Print Files, Filament, Control, Setting, Assistant), caricamento external spool, modalità velocità (Silent/Standard/Sport/Ludicrous), calibrazioni da schermo (Motor Noise, Vibration, Bed Leveling), print options.

## [bambu_studio_workflow]
**Workflow completo Bambu Studio: import, slice, export, invio stampa**
Quando usarlo: devi capire come si passa da Blender a stampa fisica, cosa fa lo slicer
File: `docs/bambu_studio_workflow.md`

Contenuto: Setup BS, architettura preset (Printer/Filament/Process), checklist Blender→BS, processo di slicing, vista slicing (speed/flow/line type), invio via Wi-Fi/LAN/SD, caricamento filamento external spool, features utili (Object List, override, adaptive layer height).

## [bambu_studio_settings]
**Impostazioni slicer: layer height, walls, infill, speed, supports, seam, Cut Tool, Fuzzy Skin**
Quando usarlo: devi sapere quali parametri di stampa esistono e come influenzano il risultato, configurare supporti con pennello, scegliere tipo di seam, tagliare modello nello slicer, aggiungere texture Fuzzy Skin
File: `docs/bambu_studio_settings.md`

Contenuto: **Support Painting** arricchito (Sphere Tool — supporto in raggio 3D, Fill Tool — Smart Fill Angle propagation per aree complesse, Gap Fill — chiusura isole automatica; workflow efficiente con Sphere poi Gap Fill); **Scarf Seam** avanzato (Inner/Outer/Inner order, overlap 20mm, velocità pareti 50–75mm/s, Overhang Detection auto-disable); **Cut Tool** (Planar, Plug, Dowel — migliore per resistenza, Dovetail — autobloccante, Snap — solo materiali flessibili; tolleranza punto di partenza 0.1mm); **Fuzzy Skin** (Point Distance 0.1mm fine → 0.8mm grossolano, Thickness 0.1–0.5mm; non applicare su superfici con tolleranze critiche); seam (Nearest/Aligned/Back/Scarf), cooling (fan speed, slow down for overhang), compensazioni geometriche (Elephant Foot, XY Hole/Contour, Shrinkage), strength (walls, infill density/pattern, overlap), parametri avanzati (retraction, line width, bridge, spiral vase, brim, adaptive layer height).

## [design_rules_fdm]
**Regole di design per FDM: overhang, bridge, tolleranze, spessori minimi**
Quando usarlo: stai modellando e devi sapere se qualcosa è stampabile o come progettarlo
File: `docs/design_rules_fdm.md`

Contenuto: Spessori minimi (0.4 mm con nozzle 0.4 mm), layer height range, shrinkage PLA formula, elephant foot, XY compensation, volumetric speed (MVS), orientamento per resistenza (anisotropia FDM), overhang <45° senza supporto, bridge PLA fino a ~60 mm.

## [filament_materials]
**Materiali PLA — tutti i tipi, parametri, conservazione, problemi**
Quando usarlo: hai dubbi su un tipo di PLA, parametri di stampa o problemi tipici del materiale
File: `docs/filament_materials.md`

Contenuto: Parametri PLA (190–240 °C nozzle, 35–65 °C heatbed), tipi PLA (Basic/Silk/CF/Wood/Galaxy/Glow/Aero) con requisiti nozzle e restrizioni, essiccazione (PLA Silk/Wood/CF: 55 °C × 8h), conservazione, problemi comuni (stringing, heat creep, gloss Silk).

## [calibration]
**Calibrazione: bed leveling, flow rate, pressure advance, primo layer**
Quando usarlo: ci sono problemi di qualità stampa o devi ottimizzare parametri
File: `Printer Infos/calibration.md`

Contenuto: Tipi bed leveling (rapido, partial, completo 21×21), manual bed tramming step-by-step, Flow Dynamics Calibration (quando e come), flow rate manuale (over/under-extrusion), checklist primo layer perfetto, Z-offset.

## [print_quality_issues]
**Problemi di qualità: stringing, warping, layer separation, clogging**
Quando usarlo: la stampa ha difetti visibili o problemi durante la stampa
File: `docs/print_quality_issues.md`

Contenuto: Stringing (umidità, temperatura, retraction), warping PLA (pulizia, brim, dischi), interlayer cracking, heat creep (PLA HTD 57 °C), clog estrusore/nozzle, under-extrusion, bridging, overhang, seam, dots/zits, variazione gloss, heatbed non si scalda.

## [a1_maintenance_relevant]
**Manutenzione A1: lubrificazione assi, hotend, frequenze**
Quando usarlo: la qualità stampa degrada nel tempo o ci sono rumori anomali
File: `Printer Infos/a1_maintenance_relevant.md`

Contenuto: Oil su X/Y binari e rulli folli; Grease su lead screw Z e gear estrusore (MAI grease su X-axis). Frequenze: X/Y mensile, Z ogni 3 mesi, gear ogni 5 bobine PLA. Pulizia hotend con alcool, cinghie su notifica HMS, fans settimanale.

## [build_plates]
**Piastre di stampa: tipi, PLA su ogni piastra, pulizia, troubleshooting**
Quando usarlo: devi scegliere la piastra giusta o risolvere problemi di adesione
File: `Printer Infos/build_plates.md`

Contenuto: Textured PEI (inclusa, PLA senza colla, 55–65 °C, superficie rugosa), Cool Plate SuperTack (PLA senza colla, bassa T, liscia/matte), Smooth PEI, Engineering Plate legacy. Pulizia Textured PEI: acqua+detergente (NO acetone). Troubleshooting: piastra sbagliata in BS, piastra sporca, temperatura errata.

## [faq_glossary]
**FAQ A1 + Glossario termini tecnici**
Quando usarlo: hai dubbi su terminologia o domande comuni sulla A1 e Bambu Studio
File: `docs/faq_glossary.md`

Contenuto: Glossario componenti A1 (toolhead, hotend, extruder, heatbed, ecc.) e terminologia FDM (layer height, infill, seam, retraction, heat creep, MVS, flow dynamics, manifold, G-code). FAQ specifiche A1 (volume stampa, nozzle, rumore, consumo, SD card), FAQ Bambu Studio (preset, override, bed leveling).

## [slicing_profiles]
**Preset operativi Bambu Studio per PLA su A1: 6 ricette per caso d'uso**
Quando usarlo: devi configurare Bambu Studio per un tipo specifico di modello, cerchi valori consigliati per layer height, pareti, infill, velocità, raffreddamento, supporti
File: `docs/slicing_profiles.md`

Contenuto: Profilo 1 Figurina Estetica (0.12mm, 4 pareti, Gyroid 15%, Tree support, seam=Back, brim 5mm), Profilo 2 Parte Funzionale (0.20mm, 4 pareti, Grid 40%, XY compensation), Profilo 3 Alta Resistenza (0.20mm, 6 pareti, Cubic 60–80%, fan 60%), Profilo 4 Miniatura <50mm (0.08–0.12mm, Tree support threshold 40°, velocità 80mm/s), Profilo 5 Oggetto Grande >200mm (0.28mm, Lightning 10%, brim 10mm, fan slow-down), Profilo 6 Parete Sottile (0.16mm, 2 pareti, 0% infill, fan 100%). Quick reference tabella scenario→profilo.

## [tolerances_and_fits]
**Accoppiamenti dimensionali PLA su A1: clearance misurata, XY compensation, tabelle fit**
Quando usarlo: stai progettando parti che si incastrano (press-fit, slip-fit, running-fit), devi impostare XY Hole/Contour Compensation in Bambu Studio, hai bisogno di clearance numerica per fori e pin
File: `docs/tolerances_and_fits.md`

Contenuto: precisione baseline A1 (±0.10–0.20mm), perché i fori escono undersized (poligonalizzazione + filament tension + die swell), XY Hole Compensation (+0.1mm baseline) e Contour Compensation (−0.05 a −0.1mm), tabella fit empirica (0.05–0.40mm clearance con risultati A1 default vs calibrata), caso 608 bearing, Wall Order Outer-First per accuratezza, Elephant's Foot compensation, Slice Gap Closing Radius, Shrinkage Compensation formula, caveat calibri digitali.

## [threads_and_fasteners]
**Inserti termici, viti autofilettanti, filettature stampate, dadi prigionieri — PLA A1**
Quando usarlo: devi fissare parti con viti, scegliere tra inserto termico/autofilettante/filettatura stampata, hai bisogno dei diametri foro pilota per PLA
File: `docs/threads_and_fasteners.md`

Contenuto: gerarchia sistemi fissaggio (captive nut > inserto termico > maschiatura > autofilettante > filettatura stampata), tabella inserti termici M2–M8 con diametro foro CAD e parete minima (M3 standard: foro 4.0mm; M3 Voron: 4.4mm), temperatura installazione 220–230°C, tabella viti autofilettanti M2–M5 con foro pilota e torque, regola boss 2.5× diametro vite, tabella maschiatura post-stampa M3–M6, tabella dadi prigionieri con tolleranza tasca (+0.2mm), filettature stampate (solo ≥M6, layer height < P/4, asse verticale). **Orientamento di stampa bulloni FDM**: bulloni stampati in orizzontale (gambo steso sul bed) → layer lines parallele all'asse di trazione → resistenza pull-out massima; orientamento verticale → layer lines ⊥ alla forza → delaminazione facile; sotto M6 usare inserto termico + vite commerciale.

## [assembly_design]
**Design per assemblaggio FDM PLA: snap-fit, dovetail, registration pin, living hinge**
Quando usarlo: devi progettare giunzioni meccaniche stampabili (snap-fit, coda di rondine, allineamento pin), calcolare la deflessione di un cantilever, scegliere tolleranze per accoppiamento
File: `docs/assembly_design.md`

Contenuto: proprietà meccaniche PLA FDM (E=3500 MPa, elongation 3–8%, anisotropia asse Z −20–30%), formula snap-fit ε=1.5·t·Y/(L²·Q) con tabella Q factor, strain massima PLA (4–6% singolo uso, 2–3% riuso, 1–2% asse Z), forza assemblaggio formula (P e W), dovetail (angolo 60–65°, clearance 0.1–0.5mm, chamfer 0.5mm), registration pin fit classificati (press/slip/running), "Hole Undersize Rule" con compensazioni, living hinge (0.5–0.8mm, asse XY), chamfer alla base per Elephant's Foot, infill per giunzioni (≥4 perimetri), adesivi (CA/epossidico/solvent welding).

## [post_processing]
**Post-processing PLA: sanding, filler, primer, vernici, coating epossidico**
Quando usarlo: devi rifinire una stampa PLA per uso decorativo o professionale, scegliere primer/vernici compatibili, applicare filler per le layer lines, fare smoothing
File: `docs/post_processing.md`

Contenuto: regola NO acetone su PLA, sequenza workflow 10 step, tabella progressione grit (120→220→400→600→2000), wet sanding da 400 grit, filler comparati (Bondo/Vallejo/Milliput — pro/contro), solventi compatibili (Etil Acetato sì, acetone no, DCM per welding), tabella primer (Rust-Oleum/Tamiya/Vallejo), acrilici vs smalti vs lacche, XTC-3D epossidico (mix ratio 2A:1B, pot life 10 min, cure 4h), tabella tempi dry vs cure, friction welding e solvent welding, waterproofing.

## [gcode_inspection_basics]
**Lettura preview G-code Bambu Studio: colori line type, speed/flow, layer time, travel**
Quando usarlo: devi verificare uno slice prima di stampare, interpretare i colori del preview, eseguire l'audit pre-stampa
File: `docs/gcode_inspection_basics.md`

Contenuto: 7 modalità preview (Line Type/Speed/Flow/Layer Time/Fan Speed/Travel/Filament), tabella mappa colori Line Type (outer wall rosso, bridge azzurro, support interface verde chiaro, ecc.), formula flusso volumetrico V=w·h·v, checklist 5-step (struttura layer, velocità/flusso, cooling, travel, overhangs), soglie cooling A1+PLA (< 3s → fan 100%, 3–30s → interpolazione), Reduce Infill Retraction risks, tabella segnali di allarme con fix.

## [text_and_engravings]
**Testo e incisioni FDM: dimensioni minime, emboss/deboss, font, orientamento, slicer**
Quando usarlo: vuoi aggiungere testo o pattern incisi/in rilievo a un modello, scegliere il font giusto, sapere la profondità minima funzionale, configurare il slicer per testo nitido
File: `docs/text_and_engravings.md`

Contenuto: limiti fisici nozzle 0.4mm (min stroke 0.4mm, altezza min 4mm, die swell +0.1–0.2mm per lato), tabella font size (< 3mm illeggibile, 4mm leggibile bold, 6mm molto chiaro), font consigliati (Arial Black, Liberation Sans Bold — no serif/script), emboss 0.4–0.6mm vs deboss 0.4–0.6mm con problema isole (≥0.8mm), orientamento orizzontale/verticale/fondo con pro/contro, Arachne obbligatorio per stroke variabili, Ironing per top surface, Z-hop per testo embossato piccolo, multi-color via filament change (≥1mm depth), magic numbers layer height (0.12/0.16mm).

## [bambu_3mf_export]
**Blender → Bambu Studio handoff via 3MF: 3 fork addon (threemf-io/LeeGillie/eki), Production Extension gap, pre-export checklist, Parent Empty multi-plate trick, Issues #7775/#6976/#3316**
Quando usarlo: vuoi capire come esportare da Blender a Bambu Studio in modo robusto, decidere quale fork 3MF installare, conoscere cosa si perde nel roundtrip, fare multi-plate da Blender
File: `docs/bambu_3mf_export.md`

Contenuto: comparazione STL vs Generic 3MF vs Bambu Production Extension (units/multi-object/modifier_part/profile metadata/round-trip/file size), 3 fork addon (threemf-io Jan 2026 primary, LeeGillie Blender 5.x, eki stale), pre-export pipeline obbligatoria (transform_apply + origin lowest-Z + recalc normals + triangulate + naming), export call con global_scale correlato a scene unit_settings, Parent Empty trick per multi-plate, cosa si perde all'import in Bambu (material colors, per-object slicer settings, modifier flags, AMS filament_ids), Issue #7775 (color discarded) #6976 (Bambu-to-Bambu lose settings) #3316 (Bambu 3MF non apre in PrusaSlicer/Cura), OrcaSlicer alternative.

## [a1_field_kit]
**Community knowledge A1 oltre docs ufficiali: belt tension drift, ABL HMS 0300 fix, hotend unclog hex wrench, heat creep mitigations, Blob of Doom recovery, layer shift causes**
Quando usarlo: hai un sintomo A1 e i docs ufficiali non hanno la soluzione completa, vuoi sapere maintenance schedule community-revised
File: `docs/a1_field_kit.md`

Contenuto: X-belt tension warning drift (procedura corretta, over-tightening danni), ABL failures HMS 0300 1800 0001 0003 con 3 fix non-ufficiali (USB connector, cooling fin, TH board screw), hotend unclog A1-specific (hex dall'alto vs pin dal nozzle), heat creep mitigations per PLA conduttivo (Silk/Metal/Glow: 195-200°C, retraction 60mm/s 0.5-0.8mm, fan max, MVS 12-14), Blob of Doom recovery (NON spegnere, heat 250 strip mechanical, sostituisci sock), Power Loss Recovery quirks (functionality OK ma fallisce su layer change pause / bed cold / filament retracted), layer shift X causes (belt drift, vibration compensation drift, motor current reset), build plate quirks (Textured PEI NO acetone, Cool Plate non per PETG), maintenance schedule community-revised (X/Y mensile, Z 6 settimane, gear ogni 3kg, sock 50h, belt cal 2 settimane).

## [mvs_filament_table]
**Max Volumetric Speed (MVS) per brand: tabella community-dialed Bambu/Polymaker/eSun/Sunlu/Overture/Hatchbox, calibrazione manuale, MVS vs print speed**
Quando usarlo: hai un filament generico o branded, vuoi sapere MVS effettivo testato beyond default, evitare misconception PLA Meta = high-speed
File: `docs/mvs_filament_table.md`

Contenuto: A1 hardware ceiling 28 mm³/s, real-world per arbitrario PLA 18 mm³/s, tabella per brand (Bambu Basic 21, Matte 18, Silk 12-14, PolyTerra 22, eSun PLA+ 18-21 bug #3233, Sunlu Meta 24 @ 230°C NON 35-40 come marketing implies), misconception PLA Meta confutata, calibrazione manuale incrementale 2 mm³/s per print, auto-cal A1 senza LIDAR sotto-stima per generic filaments (manual flow + manual PA per cosmetic), formula volumetric_flow = print_speed × line_width × layer_height (lo slicer scala silently se MVS limitante).

## [tree_support_tuning]
**Tree Support style decision matrix Normal/Hybrid/Organic/Strong, regression Hybrid post-1.9, easy-removal settings, PETG interface trick, branch parameters, Adaptive Layer Height incompat**
Quando usarlo: hai supports difficili da rimuovere o falliti, vuoi sapere quale style usare, configurare per cosmetic surface vs functional removal
File: `docs/tree_support_tuning.md`

Contenuto: 4-style decision matrix (Normal per flat-bottom mech, Hybrid default 1.9+ con regression bug, Organic per figurine, Strong per loaded prints), bug Hybrid post-update con workaround rollback Organic + disable adaptive, easy-removal settings PLA-on-PLA (Top Z 0.20/0.16, XY 0.35, Top Interface Concentric, Interface spacing 0.2), PETG interface trick per glass-smooth top surface (Top Z 0.00, fall-off removal), branch parameters (angle 35-45, diameter 4-7mm, density 5-10%, tip 0.4mm nozzle-bound, layers above tip 3-7), Adaptive Layer Height + Tree Hybrid incompat (workaround Tree Organic o disable adaptive), Support Painting workflow integration (Sphere → Gap Fill → Fill order).

## [hidden_bambu_studio_settings]
**Bambu Studio tricks: wall order Outer/Inner per cosmetic, force solid layers per reinforcement, Smooth Spiral + Timelapse bug, bridge speed override, custom G-code injection, adaptive layer height when NOT to use, negative volume modifier, per-object overrides**
Quando usarlo: vuoi spingere oltre i defaults Bambu Studio, capire trick community per quality/speed tradeoff, evitare bug noti
File: `docs/hidden_bambu_studio_settings.md`

Contenuto: wall order Outer/Inner per cosmetic surface vs Inner/Outer default per dim accuracy vs Inner/Outer/Inner per heavy overhang, force solid layers per modifier mesh (top_solid_layers=8 zonale), Smooth Spiral + Traditional Timelapse bug #9166 (pause per layer ricrea seam) workaround disable o Smooth Timelapse, bridge speed override per length (>20mm 25-30, >40mm 20), outer wall speed per cosmetic (60-80 vs 200 default), custom G-code injection at layer (right-click slider, M600/M104/M106), adaptive layer height NON usare su mech parts/Tree Hybrid/bridge/threading, negative volume parts via 3MF modifier (editable post-slice vs Boolean DIFFERENCE in Blender), per-object process overrides (different infill same plate), Spiral Vase quirks (no top, no infill, 1 wall forced, no Z hop).

## [pla_post_processing_field_data]
**Post-processing PLA con dati testati: annealing curva temp/tempo/shrinkage XY+Z, sanding grit progression, primer+paint workflow, heat gun smoothing caveat, filler putty, XTC-3D**
Quando usarlo: vuoi finire un modello stampato con qualità cosmetic, capire annealing trade-off dimensionali, scegliere tra sanding manuale vs epoxy coating
File: `docs/pla_post_processing_field_data.md`

Contenuto: annealing curva (60-70°C safe +20% strength <1% shrink, 85°C sweet spot +80% strength 4-5% XY shrink, 100°+ warping severo), shrinkage anisotropa XY contrae 4-5% Z cresce 1-3% (CAD compensation), procedura forno con sabbia bed + cooldown lento, annealing NON adatto a feature ≤1mm/bordi sottili/metallic embed/dim critical, acetone vapor smoothing NON funziona su PLA, A1 NON adatto a ABS (no enclosure), sanding grit progression 120→180→240→400→800→1500 con wet sanding da 400, primer+paint workflow (sand 240 → filler primer → sand 400 wet → second primer → color → top coat) tempo 4-8h, heat gun smoothing per massive walls only NON per pareti sottili/feature fini, Bondo/Tamiya putty per gap fill, XTC-3D epoxy alternative ma aggiunge 0.1-0.3mm.

## [advanced_slicing_params]
**Parametri slicing avanzati Bambu Studio: wall optimization, Arachne, thick bridges, ironing, modificatori locali, ricette specifiche**
Quando usarlo: vuoi ottimizzare resistenza meccanica oltre i profili base, configurare Ironing, capire Arachne vs Classic, usare modificatori locali per rinforzi, stampare contenitori impermeabili, gestire modelli alti su A1
File: `docs/advanced_slicing_params.md`

Contenuto: Arachne vs Classic (tabella con quando usare quale — Arachne per organico/testo, Classic per incastri meccanici), wall loop optimization (principio "6 pareti / 15% infill > 2 pareti / 100% infill" con dati CNC Kitchen, formula S_guscio = N_pareti × larghezza, trick 999 wall loops per pseudo-solidi), Thick Bridges (flow ratio 1.4–1.6 PLA, speed 20–40mm/s, fan 100%, quando usare vs standard), Top Surface Flow Ratio + Only One Wall on Top + Top Area Threshold, Smooth Speed Discontinuity + coefficient 30–50 per A1, Infill Combination (multi-height), Minimum Sparse Infill Threshold (15–30mm²), Ironing (speed 30–100mm/s, flow 10–20%, spaziatura 0.10–0.15mm, thermal creep risk PLA), Variable Layer Height (color coding verde/giallo, Smooth, Precise Z Height), Modificatori Locali in BS (rinforzo fori viti 8–10 wall loops, snap-fits 100% infill base, inserti filettati), Infill/Wall Overlap (default 15%, max 50%), Ensure Vertical Shell Thickness, ricette specifiche (impermeabilità/alto impatto/precisione incastri), nota A1 bed-slinger su Gyroid (vibrazioni armoniche → preferire Cubic), parametri modelli alti (accel <3000 mm/s², speed <400, layer time >10s), Reduce Infill Retraction (disabilitare per stampe critiche).
