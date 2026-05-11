# Max Volumetric Speed (MVS) — Tabella per filament brand

I default Bambu Studio per MVS divergono significativamente dai valori che la community ha testato in pratica. Questo doc raccoglie i valori community-dialed per i filamenti più diffusi sull'A1.

**Reminder fisico**: MVS misura quanto materiale puoi fondere ed estrudere al secondo. Spingerlo troppo alto causa under-extrusion (il nozzle non riesce a fondere abbastanza filament rapidly). Più basso del necessario rallenta la stampa senza guadagno.

A1 nozzle 0.4mm: limite hardware nominale 28 mm³/s. **Real-world ceiling per arbitrario PLA**: 18 mm³/s. Solo PLA Bambu-brand verificato regge 21.

## Tabella per brand/tipo (A1, nozzle 0.4mm hardened)

| Filament | Bambu default | Community-dialed | Note |
|---|---|---|---|
| **Bambu Basic PLA** | 21 mm³/s | 18–21 OK | Bambu QA controlled, default è realistico |
| **Bambu PLA Matte** | 18 mm³/s | 18 OK | Pigmento più alto, viscosità maggiore |
| **Bambu PLA Silk** | 14 mm³/s | 12–14 | Heat-sensitive, easily over-extrudes |
| **Bambu PLA Silk Dual Color** | 14 mm³/s | 12 | Persistent over-extrusion reported, dial flow_ratio a 0.95-0.98 |
| **Bambu PLA Marble** | 14 mm³/s | 12 | Texture additives ridotti |
| **PolyTerra PLA** | 22 mm³/s | 22 OK | Polymaker QA |
| **Polymaker PolyLite PLA** | 22 mm³/s | 22 OK | Default profile ok |
| **eSun PLA+** | 21 mm³/s | **filed bug, troppo aggressivo per nozzle 0.2** | Issue [#3233](https://github.com/bambulab/BambuStudio/issues/3233). Per nozzle 0.4 ok a 18-21. |
| **Sunlu PLA+** | generic 12 | 18–20 | Sotto-stimato dal default generico |
| **Sunlu PLA Meta** | generic 12 | **24 @ 230°C** | **NON è high-speed nonostante il marketing**. Sopra 28 mm³/s burns. |
| **Sunlu PLA Silk** | generic 12 | 12–14 | Heat creep frequente, cap to 12 |
| **Overture PLA** | generic 12 | 18 OK | Stabile |
| **Overture PLA Matte** | generic 12 | 14–16 | Pigmento alto, viscosità più alta |
| **Hatchbox PLA** | generic 12 | 14–18 | Variabilità lot-to-lot, parti dal basso |
| **Generic PLA (sconosciuto)** | 12 mm³/s | **Avvia da 12, calibra incrementale** | Vedi sezione "Calibrazione manuale" sotto |
| **Generic PLA+** | 12 mm³/s | 14–18 (incrementale) | PLA+ ha melt più alto, tendenzialmente regge meglio |

## Misconception comune: PLA Meta = high-speed

Sunlu PLA Meta è marketata come "high-speed PLA". La community testing su A1:
- **Default Bambu Studio**: 12 mm³/s (generic PLA).
- **Sicuro stabile**: 22-24 mm³/s @ 230°C nozzle.
- **Sopra 28 mm³/s**: under-extrusion, eventually burns.

Errore tipico: l'utente vede il marketing "high speed", imposta 35-40 mm³/s, stampa fallisce con stringing severo + gaps. La marketing è relativa ad altri PLA standard, NON al limite hardware A1.

**Source**: [forum.bambulab.com/t/sunlu-pla-meta-help/137724/10](https://forum.bambulab.com/t/sunlu-pla-meta-help/137724/10).

## Calibrazione manuale incrementale (per filament generico)

Quando hai un filament non in tabella:

```
1. Stampa il Bambu Studio MVS test tower:
   - Calibration → Max Volumetric Speed → Calibrate
2. Verifica visualmente il punto di under-extrusion (gaps, stringing severo)
3. Subtract 2 mm³/s dal valore osservato come safety margin
4. Persisti nel filament profile custom
```

In alternativa, manual progression:
- Start: 12 mm³/s
- Increment: 2 mm³/s per print di test (Voronoi vase 50×50mm)
- Stop quando vedi gaps o stringing aumenta visibilmente
- Subtract 2 mm³/s

## Auto-calibration limits su A1

L'A1 non ha LIDAR (a differenza X1). La flow dynamics calibration usa Force Sensor pressure readings.

**Limite**: la auto-cal funziona bene per **PLA Bambu** ma può sottostimare per filament generici. Per cosmetic prints (vasi, statue) la community raccomanda **manual flow + manual PA** anche su A1.

**Bambu PLA Silk Dual Color, AliExpress generics**: spesso necessitano `flow_ratio = 0.93–0.98` (sotto-extrusion required) — auto-cal stima 1.00.

## MVS vs Print Speed — non confondere

- **MVS** = quanto materiale al secondo (mm³/s)
- **Print speed** = quanto veloce si muove la testa (mm/s)
- **Line width** = quanto largo è l'extrusion bead (mm)
- **Layer height** = quanto alto è l'extrusion bead (mm)

Relazione:
```
volumetric_flow = print_speed × line_width × layer_height
```

Esempio: print_speed=200mm/s, line_width=0.42mm, layer_height=0.20mm → 16.8 mm³/s.

Se MVS=12 ma vuoi stampare 200mm/s con quei valori, lo slicer **scala automaticamente** print_speed a `12 / (0.42 × 0.20) = 142 mm/s`. NON ottieni 200 mm/s reali.

Per stampare davvero 200 mm/s su PLA generic devi:
- Calibrare MVS verso 17-18+
- OPPURE accettare che lo slicer rallenti silently

## Cross-reference

- [filament_materials] — proprietà PLA generali
- [bambu_studio_settings] — speed parameters layout
- [calibration] — flow dynamics auto-cal procedure
- [slicing_profiles] — quali profili spingono MVS
- [print_quality_issues] — sintomi under-extrusion (causa principale MVS troppo alto)
- [a1_field_kit] — heat creep mitigations per filament conducting alto

## Source

- [forum.bambulab.com/t/volumemetric-speed-by-filament-type-and-brand/9626](https://forum.bambulab.com/t/volumemetric-speed-by-filament-type-and-brand/9626)
- [forum.bambulab.com/t/max-volumetric-speed-limit/3688](https://forum.bambulab.com/t/max-volumetric-speed-limit-how-to-find-the-maximum-optimum-value/3688)
- [wiki.bambulab.com/en/knowledge-sharing/volumetric-speed](https://wiki.bambulab.com/en/knowledge-sharing/volumetric-speed)
- [forum.bambulab.com/t/sunlu-pla-meta-help/137724](https://forum.bambulab.com/t/sunlu-pla-meta-help/137724)
- [GitHub bambulab/BambuStudio#3233](https://github.com/bambulab/BambuStudio/issues/3233)
