# A1 Community Field Kit — Quirks oltre la documentazione ufficiale

Knowledge accumulato dalla community Bambu Lab A1 (forum.bambulab.com, GitHub Bambu Studio issues, Reddit r/BambuLab) tra 2024-2026. Sono cose che il manuale ufficiale NON copre ma sono ricorrenti abbastanza da fare parte del "field knowledge" di proprietari A1.

## X-belt tension warning drift

**Sintomo**: il warning di tensione X-axis ricompare a settimane/mesi di distanza dal setup iniziale.

**Cause documentate** dalla community (non in docs ufficiali):
1. La procedura ufficiale "loosen → slide carriage 3 times by hand → retighten" va **ripetuta più frequentemente** di quanto i docs implichino — alcuni utenti la fanno mensilmente.
2. Over-tightening: chasing il warning con tensione crescente **danneggia la belt** e accelera la failure.

**Procedure consigliata community**:
- Quando appare il warning, esegui sempre la frequency-scan flow built-in (Settings → Calibrations → Belt Tension) PRIMA di toccare hardware.
- Se la calibrazione non risolve, esegui la procedura manuale standard una sola volta, non iterare.
- Sostituisci la belt se il warning ricompare entro 3 giorni dopo retension.

**Source**: [forum.bambulab.com/t/a1-x-axis-tension-warning-keeps-happening/108874](https://forum.bambulab.com/t/a1-x-axis-tension-warning-keeps-happening/108874), [104831](https://forum.bambulab.com/t/issue-with-a1-x-axis-tension-warning/104831).

## Auto Bed Leveling failures — HMS 0300 1800 0001 0003

Il community ha tracciato il "Force Extrusion Sensor and Auto Bed Leveling Failure" a 3 cause **NON nella troubleshooting ufficiale**:

1. **USB connector sotto la stampante non perfettamente seated**. Riformare l'innesto risolve.
2. **Cooling fin del top hotend piegato** verso il basso nel tempo (urto durante print removal, ecc.). Causa contatto intermittente.
3. **TH board sensor screw allentato**. Re-tighten con coppia leggera (non over-tighten).

**Diagnosi rapida**: se hai HMS 0300 1800 0001 0003 e la calibrazione bed leveling fallisce, NON sostituire subito il force sensor — controlla prima questi 3 punti.

**Source**: [forum.bambulab.com/t/.../147729](https://forum.bambulab.com/t/a1-force-extrusion-sensor-and-auto-bed-leveling-failures/147729) (17+ posts, multiple independent confirmations).

## Hotend cold-pull technique — A1-specific

L'A1 unclog procedure ufficiale (heated hex wrench inserito attraverso il top del heatsink) **differisce** da quella X1/P1 (pin dal nozzle tip).

**Procedura corretta A1**:
1. Heat nozzle a 240°C.
2. Insert hex wrench (4mm A1 / 3mm A1 mini) **dall'alto**, attraverso il heatsink, fino a fondo.
3. Ruota leggermente per rompere il clog.
4. Estrai senza ruotare.

**Causa primaria clog A1 specifica**: **heat creep** dovuto a **mancanza di enclosure / active chamber control**. Più pronunciato con:
- Filamenti Silk
- PLA metal-filled (heat capacity più alta)
- PLA Glow-in-the-dark (additivi conducono calore meglio)

**Source**: [wiki.bambulab.com/en/a1-mini/troubleshooting/nozzle-clog](https://wiki.bambulab.com/en/a1-mini/troubleshooting/nozzle-clog), [forum.bambulab.com/t/clogging-constantly-a1-mini/76258](https://forum.bambulab.com/t/clogging-constantly-a1-mini/76258), [forum.bambulab.com/t/glow-or-metal-filled-pla-and-heat-creep/81741](https://forum.bambulab.com/t/glow-or-metal-filled-pla-and-heat-creep/81741).

## Heat creep mitigations (PLA highly-conductive)

Quando stampi PLA conduttivo (silk, metal-filled, glow) sull'A1:

1. **Reduce nozzle temp** a 195–200°C (vs 215–220°C default Bambu Basic).
2. **Increase retraction speed** a 60mm/s (vs 30 default A1 direct drive).
3. **Reduce retraction distance** a 0.5–0.8mm (vs 0.8mm default) — paradosso: troppo retraction permette al filament di salire nel heatsink dove cuoce.
4. **Higher fan speed dal layer 2** (90–100% vs default scaling) per cooling più aggressivo.
5. **Lower max volumetric speed** a 12–14 mm³/s (vs 21 default per Bambu Basic PLA).

## Blob of Doom recovery

**Sintomo**: extrusione fuoriuscita catastrofica che incapsula nozzle + heatblock + cooling fan in una palla di plastica.

**Recovery community-tested** (non in docs ufficiali per A1):
1. **NON spegnere subito** — heat il nozzle a 250°C per ammorbidire il blob.
2. Mentre è morbido, **strip via** quanto più possibile con pliers (proteggi con guanti termici).
3. Una volta freddato: smonta hotend assembly completo (heatblock + thermistor + heater cartridge).
4. Soak in DMSO o acetone (per ABS), oppure **scrape mechanically** per PLA.
5. **Sostituisci il sock/silicone** (irreversibilmente danneggiato).
6. **Test thermistor** prima di rimontare — heat creep severo può aver danneggiato la calibrazione.

**Source**: [forum.bambulab.com/t/a1-mini-issues-after-blob-of-doom/244866](https://forum.bambulab.com/t/a1-mini-issues-after-blob-of-doom/244866).

## Power loss recovery quirks

**Comportamento documentato A1**:
- Power Loss Recovery FUNZIONA su A1 e A1 mini (a differenza di voci confuse online).
- Si attiva automaticamente se la stampa era >10% completata e il file è ancora su SD/cache.

**Failure mode community**: PLR può saltare se:
- Power loss avviene durante "Layer Change" pause
- Bed temperature è scesa sotto 35°C prima del restart (bed dechorpera la prima prossima layer)
- Il filament si è ritirato dal nozzle (heat creep nel cooldown)

**Mitigation**: pre-heat manualmente bed + nozzle PRIMA di confermare Resume nel UI.

**Source**: [wiki.bambulab.com/en/knowledge-sharing/power-loss-recovery](https://wiki.bambulab.com/en/knowledge-sharing/power-loss-recovery), [forum.bambulab.com/t/.../188172](https://forum.bambulab.com/t/power-outage-feature-not-working/188172).

## Layer shift X-axis A1

**Cause community-tracked** (in ordine di frequenza):
1. **Belt tension drift** (vedi sopra) — non sufficient torque transmission.
2. **Vibration compensation drift** — re-run input shaper calibration ogni 3 mesi.
3. **Motor current settings** (firmware) reset a default dopo update — il community spinge la community per esposizione di questi.
4. **Speed/acceleration troppo aggressivi** su modelli tall+thin (vedi P6 bedslinger I_eff in [bambu_a1_physical_constants]).

**Source**: [forum.bambulab.com/t/layer-shift-x-axis-in-bambu-lab-a1-mini/76193](https://forum.bambulab.com/t/layer-shift-x-axis-in-bambu-lab-a1-mini/76193).

## Build plate quirks specifici A1

Beyond docs ufficiali:

**Textured PEI** (incluso A1):
- **NON pulire con acetone** — distrugge la finitura testurizzata.
- **Pulizia consigliata**: acqua tiepida + detergente per piatti → asciuga → opzionale alcool isopropilico solo sulle aree ad adesione bassa.
- Lifetime tipica: 100-300 print prima di adesione degradata.

**Cool Plate SuperTack** (alternative):
- Migliore per PLA Silk e PLA Marble (basse temperature).
- **Non adatta** a PETG (over-adesione, distrugge la plate al removal).

**Engineering Plate legacy** (non più venduta):
- Se hai una unit vecchia, non usare PLA su questa — sufficient adesione solo con colla stick.

## Maintenance schedule community-revised

Bambu official: X/Y mensile, Z trimestrale, gear ogni 5kg PLA.

Community A1 (più conservativo basato su print failure data):
- **X/Y rails**: lubrificazione mensile, ispezione belt visiva settimanale.
- **Z screw**: grease ogni 6 settimane (non 3 mesi).
- **Extruder gear**: pulizia + grease ogni 3kg PLA, non 5kg (filament composite shed più powder).
- **Hotend sock/silicone**: ispeziona ogni 50 ore, sostituisci se cracked.
- **Belt tension calibration**: ogni 2 settimane se stampi >40 ore/settimana.

## Cross-reference

- [bambu_a1_physical_constants] §6 — input shaping + acceleration vs Z
- [print_quality_issues] — sintomi visibili da queste cause
- [filament_materials] — characteristics PLA per heat creep
- [calibration] — procedure ufficiali (community ritocca le frequenze)

## Source consolidato

Tutti i link in questo doc sono al `forum.bambulab.com`, `wiki.bambulab.com`, o GitHub `bambulab/BambuStudio`. Re-verifica le date — la community evolve rapidamente.
