# Tree Support Tuning — decision matrix e community settings

Bambu Studio offre **tre style** di Tree Support: Default (Normal), Hybrid, e Organic. La community ha consenso su quale usare quando, e su settings tuned beyond i default per A1 + PLA.

## Style decision matrix

| Style | Quando usarlo | Pro | Contro |
|---|---|---|---|
| **Normal/Default** | Modelli flat-bottom con overhang isolati uniformi (es. parti meccaniche box-style) | Veloce da slicare, removal facile su flat | Material-heavy, scarso per organic |
| **Tree Hybrid** | Mix mech + organic (figurine con base flat, scatole con dettagli sporgenti) | **Default Bambu Studio 1.9+**, balance tra Normal e Organic | Regression bug post-update: **alcuni utenti riportano peggior performance** rispetto a Tree Organic |
| **Tree Organic** | Figurine, busti, modelli pure-organic con overhang complessi | Branch generation aggressivo, merging intelligente, **best per figurine** | Lento da slicare su mesh >500k faces |
| **Tree Strong** | Funzionali pesanti con load durante print (parti che si flettono) | Più materiale, removal auto facile | **Material-heavy**, lento |

**Source**: [GitHub Issue #5974](https://github.com/bambulab/BambuStudio/issues/5974), [forum thread "Tree support generation changed - it's BAD"](https://forum.bambulab.com/t/tree-support-generation-changed-its-bad/168346).

## Tree Hybrid regression post-1.9

Multipli utenti report che **Tree Hybrid post-update** produce supporti meno robusti rispetto al precedente "Tree Default" (rinominato in 1.9+). Specifico:
- Branch più sottili che collassano durante print.
- Mix di Tree + Normal in adaptive layer height fallisce su layer fini.
- Peggior bridging tra knuckles supportati.

**Workaround community**:
- Rollback al Tree Organic se hai un modello che Tree Default precedente gestiva.
- Disable adaptive layer height + use fixed 0.20mm se mantieni Tree Hybrid.

**Source**: [forum.bambulab.com/t/tree-support-generation-changed-its-bad/168346](https://forum.bambulab.com/t/tree-support-generation-changed-its-bad/168346), [forum.bambulab.com/t/adaptive-layer-height-and-support-problems/183043](https://forum.bambulab.com/t/adaptive-layer-height-and-support-problems/183043).

## Easy-removal settings (PLA-on-PLA, no PETG interface)

Default Bambu è **conservativo per adesione**. Per **easy removal** (cosa che vuoi se non distruggi il modello):

```
Top Z Distance     : 0.20 mm     (default 0.10-0.16)
                     0.16 mm @ layer_height=0.12
Top Interface Z    : 0.10 mm     (sintered nicely al modello)
Support/Object XY  : 0.35 mm     (default 0.20)
Top Interface      : Concentric  (vs Rectilinear default)
Interface lines    : 3-4
Interface spacing  : 0.2 mm
Pattern angle      : 90° (perpendicular to model orientation)
```

**Verifica**: la prima superficie del modello sopra il support deve avere texture visibile delle interface lines. Se è perfettamente liscia, il distance è troppo piccolo (supporto fuso al modello). Se ci sono buchi, distance troppo grande.

**Source**: [corb3d.com/best-bambu-lab-a1-mini-support-settings-easy-removal/](https://corb3d.com/best-bambu-lab-a1-mini-support-settings-easy-removal/), [forum.bambulab.com/t/.../13401](https://forum.bambulab.com/t/what-to-adjust-for-easier-support-removal/13401).

## PETG interface trick

Per **parts that literally fall off**: usa **PETG come interface** su PLA modello (no AMS necessario — single filament swap manuale durante print).

```
Modello             : PLA
Interface filament  : PETG
Top Z Distance      : 0.00 mm     (zero — PLA non aderisce a PETG)
Top Interface lines : 3-5
```

**Result**: superficie del modello sopra l'interface è **glass-smooth** (no texture). Il PETG si distacca con una leggera pressione laterale, lasciando finitura più pulita di qualsiasi sanding.

**Caveat**: richiede manual filament swap a metà print (M600 G-code injection o pause-and-replace). Su A1 single-filament richiede attenzione. Su A1 mini con AMS lite automatico.

## Branch parameters (Tree Organic / Hybrid)

| Parameter | Default | Community range | Note |
|---|---|---|---|
| **Branch angle** | 40° | 35-45° | Più aggressivo = meno materiale ma più collapse risk |
| **Branch diameter** | 5 mm | 4-7 mm | Più piccolo per figurine fini; più grande per parti pesanti |
| **Branch density** | 5% | 5-10% | Default è ok; aumenta se collapse |
| **Tip diameter** | 0.4 mm | 0.4 mm (nozzle) | NON ridurre — finisce in 1 perimetro single-bead fragile |
| **Layers above tip** | 5 | 3-7 | Hybrid layers fra punta e modello |

## Adaptive Layer Height + Tree — known incompat

Bug noto Bambu Studio 1.9+: **Adaptive Layer Height + Tree Hybrid** può produrre support con layer di altezza variabile che NON corrispondono al modello. Branch saltano layer e collassano.

**Workaround**: se usi Adaptive Layer Height, forza Tree Organic (più robusto al variable layer) o disable Tree e usa Normal supports.

**Source**: [forum.bambulab.com/t/adaptive-layer-height-and-support-problems/183043](https://forum.bambulab.com/t/adaptive-layer-height-and-support-problems/183043).

## Support Painting integration

Per geometrie complesse, il community workflow è:
1. **Auto-generate** supports con Tree Organic (overhang threshold 45-50°).
2. **Inspect** layer-by-layer nel preview.
3. **Sphere Tool** per AGGIUNGERE support manualmente in aree critiche missed da auto.
4. **Gap Fill** per close isolated bridges sotto-supportate.
5. **Fill Tool** per support density override in aree visible-quality.

L'ordine **importa**: Sphere prima di Fill, perché Fill propaga via smart angle e Sphere è puntuale.

Tempo medio: 5-10 min per modello complesso. Tempo risparmiato in cleanup post-print: 30+ min.

## Cross-reference

- [bambu_studio_settings] — UI location di questi settings
- [bambu_studio_workflow] — overall flow incluso supports
- [support_strategy] (Blender KB) — decisione SE servono supports da orientation strategy
- [orientation_strategy] (Blender KB) — minimize support requirements via reorientation

## Source

- [GitHub bambulab/BambuStudio#5974](https://github.com/bambulab/BambuStudio/issues/5974)
- [forum.bambulab.com/t/tree-support-generation-changed-its-bad/168346](https://forum.bambulab.com/t/tree-support-generation-changed-its-bad/168346)
- [forum.bambulab.com/t/adaptive-layer-height-and-support-problems/183043](https://forum.bambulab.com/t/adaptive-layer-height-and-support-problems/183043)
- [corb3d.com — Easy Removal Settings A1](https://corb3d.com/best-bambu-lab-a1-mini-support-settings-easy-removal/)
- [forum.bambulab.com/t/.../13401 — Adjust for easier support removal](https://forum.bambulab.com/t/what-to-adjust-for-easier-support-removal/13401)
