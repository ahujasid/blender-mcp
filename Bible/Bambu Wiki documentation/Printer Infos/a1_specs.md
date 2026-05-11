# A1 Specs — Bambu Lab A1

## Specifiche Base

**Tipo:** Stampante FDM Cartesiana (bed-slinger)
**Volume di stampa:** 256 × 256 × 256 mm³
**Temperatura massima heatbed:** 100 °C
**Temperatura massima nozzle (A1 Series):** 300 °C
**Temperatura raccomandata ambiente:** 10–30 °C
**Umidità raccomandata:** sotto 85%
**Memoria:** MicroSD 32 GB (pre-installata), supporta fino a 2 TB

**Sistema di movimento:**
- X-axis: guida lineare in metallo + toolhead su slider
- Y-axis: guide orizzontali ad alta precisione + heatbed come componente Y
- Z-axis: doppio albero filettato + cinghia sincrona + tensionatore automatico, guidato da binari ottici duali

**Bed Leveling automatico:**
- Probing nozzle-touch su griglia 7×7 (49 punti) per leveling rapido
- Griglia 21×21 per calibrazione completa da menu Maintenance
- Partial bed leveling supportato da firmware 1.03 + Bambu Studio 1.9

**Funzioni automatiche:**
- Risonanza/vibrazione compensation (accelerometro su X e Y)
- Flow Dynamics Calibration (equivalente a Pressure Advance)
- Motor Noise Canceling
- Belt Tension Monitor (BTM)
- Filament Runout Detection
- Power Loss Recovery
- Camera integrata (monitoraggio remoto + timelapse)

**Connettività:** Wi-Fi, LAN Mode (stampa offline), USB-C (toolhead), MicroSD

**Wiper nozzle:** La pulizia fine include il movimento del nozzle di 1–2 mm sulla superficie della piastra — normale usura nell'area di wiping.

**Spazio richiesto:**
- Almeno 10 cm liberi su ogni lato per raffreddamento/ventilazione
- Spazio Y (heatbed in movimento): ~695 mm (410 + 90 + 195 mm)

## Nozzle

**Nozzle standard incluso:** 0.4 mm stainless steel (acciaio inox)

**Nozzle A1 Series compatibili:**
- Diametri: 0.2 mm, 0.4 mm, 0.6 mm, 0.8 mm
- Materiali: hardened steel (nero) o stainless steel (grigio)
- Temperatura max: 300 °C
- Design quick-release: si rimuove dal heating assembly senza connettori

**Guida scelta nozzle per PLA con A1:**

| Diametro | Stainless steel | Hardened steel | Uso per PLA |
|----------|----------------|----------------|-------------|
| 0.2 mm | OK per PLA Basic/Matte/Translucent | N/A | Dettaglio estremo, miniature |
| 0.4 mm | OK (standard) | OK | Uso generale |
| 0.6 mm | OK | OK | Prototipazione rapida, pezzi grandi |
| 0.8 mm | OK | OK | Stampe rapide, grandi volumi |

**Stainless steel vs Hardened steel:**
- Stainless: filamenti non abrasivi (PLA Basic, PETG, TPU) — non usare con CF/GF, Glow, Sparkle
- Hardened: filamenti abrasivi (PLA-CF, PLA-Glow) — obbligatorio per questi tipi

**Nota 0.2 mm:** Non usare con PLA Silk, PLA Galaxy, PLA Marble, PLA Sparkle, PLA Glow (contengono particolati). Solo PLA Basic/Matte/Translucent/Tough+. Rischio clog alto — tenere filamento pulito e asciutto.

**Layer height range per nozzle 0.4 mm:** 0.08–0.28 mm (20–70% del diametro)
**First layer height default:** nozzle diameter × 50% → 0.2 mm per nozzle 0.4 mm

## Limiti Fisici

**Volume di stampa nominale vs effettivo:**
- Il volume 256×256×256 mm³ è il limite fisico degli assi
- In Bambu Studio il volume utile è leggermente ridotto per:
  - Z-hop durante retraction (buffer anti-collisione)
  - Area cutter in basso a sinistra: 18×28 mm² riservata (rilevante solo con AMS)
- Con single filament/no AMS: volume pieno accessibile senza modifiche

**Temperatura PLA e rischi:**
- Heat Deflection Temperature PLA: 57 °C
- Se la temperatura ambiente supera i 30 °C o il heatbed è a >55 °C a lungo, la camera interna può superare i 57 °C causando softening del filamento nell'estrusore (heat creep)
- Raccomandato: ambienti ben ventilati, heatbed PLA a 55 °C (riducibile a 45–50 °C in estate)

**Accessories inclusi (non-combo):**
- Textured PEI Plate (entrambi i lati usabili)
- PTFE tube 600 mm × 1 (per spool esterno)
- Purge Wiper + screws
- Spool Holder
- Unclogging Pin Tool (per nozzle 0.4 mm)
- Allen keys H2 e H1.5
- Lubricant Oil (binari X e Y, rulli folli)
- Lubricant Grease (vite senza fine Z, ruota dentata estrusore)
- MicroSD 32 GB pre-installata

**Importante lubrificanti:**
- Lubricant Oil: binario X, binario Y, rulli folli
- Lubricant Grease: vite senza fine (lead screw), ruota dentata estrusore
- **VIETATO** usare grease sul binario X-axis
