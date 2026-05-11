# Bambu Studio — Settings e tricks non documentati

Settings di Bambu Studio che sono in UI ma poco documentati, o community trick consolidati.

## Wall printing order — Outer/Inner > default

**Default**: Inner walls first, then outer walls. Logica: il muro interno ancora prima, poi l'outer si appoggia per posizione precisa.

**Community canon**: per **cosmetic surface quality** switcha a **Outer/Inner**:
- L'outer wall viene stampato per primo, prima che il bead interno influenzi la temperatura.
- Risultato: meno variazione di larghezza visibile sull'esterno, surface più uniforme.
- **Trade-off**: marginalmente meno preciso dimensionalmente per inner cavities (1-2 layer di "settling" del muro outer non ancora ancorato).

**Quando usare quale**:
- Cosmetic prints (figurine, modelli display) → Outer/Inner
- Dimensional accuracy critica (mech parts, snap-fit) → Inner/Outer (default)
- Heavy overhangs → **Inner/Outer/Inner** (3-pass), supporta meglio l'outer

UI location: `Process → Quality → Wall printing order`.

**Source**: [forum.bambulab.com/t/wall-printing-order-is-important/110212](https://forum.bambulab.com/t/wall-printing-order-is-important/110212), [forum.bambulab.com/t/understanding-wall-order/84649](https://forum.bambulab.com/t/understanding-wall-order/84649).

## Force solid layers per reinforcement parziale

**Use case**: vuoi aumentare resistenza meccanica in una zona specifica (es. fondo di un contenitore che porterà peso) senza aumentare global infill.

**Trick**: in 3MF/UI, applica un **modifier mesh** alla zona target con `top_solid_layers = 8` e `bottom_solid_layers = 8`. Sovrascrive il default (3) localmente.

UI location: Right-click modifier object → `Per-Object Settings` → enable specific layer override.

**Risultato**: zona piena di plastica per N layer, resto del modello rimane a infill 15-20%. Risparmio materiale + resistenza locale.

## Smooth Spiral Vase + Traditional Timelapse — BUG

**Sintomo**: Smooth Spiral (1.9+, arc-fitting per vase mode senza seam) combinato con **Traditional Timelapse** crea una **pausa per ogni layer** che ricrea il seam che Smooth Spiral dovrebbe eliminare.

**Workaround**:
- Disable Timelapse, OR
- Use **Smooth Timelapse** mode (senza pause per layer)

**Source**: [GitHub bambulab/BambuStudio#9166](https://github.com/bambulab/BambuStudio/issues/9166), [forum.bambulab.com/t/spiral-vase-seam-artifacts/181319](https://forum.bambulab.com/t/spiral-vase-seam-artifacts/181319).

## Bridge speed override

Default bridge speed: 50 mm/s. **Troppo veloce** per bridges >20mm su PLA.

**Community-tested**:
- Bridge ≤20mm: 50 mm/s (default ok)
- Bridge 20-40mm: 25-30 mm/s
- Bridge >40mm: 20 mm/s (slow)

UI: `Process → Speed → Bridge speed`.

Inoltre **bridge fan speed** dovrebbe essere a 100% indipendentemente dal fan profile globale (forza il bead a solidificare prima di sag).

## Outer wall speed per surface quality

Outer wall printato a velocità più alta = surface quality degrade. Default Bambu A1: 200 mm/s. Per cosmetic prints:

- Cosmetic detail visible: 60-80 mm/s
- Standard quality: 100-150 mm/s
- Drafting/prototyping: 200+ mm/s (default)

Più importante di Inner wall speed perché influenza solo la superficie visibile.

UI: `Process → Speed → Outer wall speed`.

## Custom G-code injection at layer

**Use case**: pause per filament swap, modificare temperature/fan/speed a layer specifici.

**Procedura**:
1. Slice il modello.
2. Right-click sul layer slider (preview pane).
3. `Add Custom G-code at layer N`.
4. Inserisci G-code (es. `M600` per filament change, `M104 S210` per temp override).

**Casi tipici**:
- `M600` a layer 30 per inserire PETG interface support (vedi [tree_support_tuning]).
- `M104 S220` a layer alti su modelli tall (compensate heat creep).
- `M106 S255` a layer overhang specifici per fan max.

**Source**: [github.com/eukatree/Bambu_CustomGCode](https://github.com/eukatree/Bambu_CustomGCode), [github.com/avatorl/bambu-a1-g-code](https://github.com/avatorl/bambu-a1-g-code/blob/main/change-filament/README.md).

## Adaptive Layer Height — quando NON usarla

Adaptive Layer Height varia il layer height nel modello: layer fini su curve, layer alti su flat. **Risparmia tempo significativo**.

**Quando funziona**: modelli pure-organic, dove non importano specifiche dimensioni.

**Quando fallisce / non usare**:
- Modelli con feature dimensionali precise (snap-fit, gear teeth): adaptive cambia layer alle quote critiche.
- Modelli con Tree Hybrid supports (vedi [tree_support_tuning] — bug noto).
- Modelli con bridge: bridge speed è layer-height-dependent, adaptive cambia ratio incorrectly.
- Modelli con threading / fasteners: vincola dimensione thread pitch.

**Default**: disable. Enable solo per cosmetic organic.

## Negative volume parts via modifier (3MF only)

3MF Bambu supporta **modifier objects** che fungono da **negative volume** (boolean cutout dinamico al slice-time, non geometricamente in mesh).

**Workflow**:
1. Importa main object in Bambu Studio.
2. Right-click → `Add Negative Part` → `Load…` → seleziona STL cutter.
3. Posiziona il cutter sopra il main.
4. Slice — il cutter NON viene stampato, ma crea il void nel main.

**Vantaggio vs Boolean DIFFERENCE in Blender**: il cutter rimane editabile post-slice. Cambiare posizione/scala del cutter re-slice senza tornare in Blender.

**Limit**: solo dentro Bambu Studio. STL non supporta. Generic 3MF da Blender non preserva il `part_type` (vedi [bambu_3mf_export]).

## Per-object overrides via 3MF

In Bambu Studio puoi setting **diverso process** per **diverso object** nella stessa plate:
- Right-click object → `Add Process` → seleziona profile diverso.
- Different infill %, support yes/no, wall count.

**Use case**: stampare una parte funzionale + una decorativa nella stessa plate. La decorativa ha infill 10%, la funzionale 40%.

UI location: dopo aver slizato, vedi nella `Object List` il process assignment per oggetto.

## Spiral Vase quirks

Spiral Vase (modello cavo, 1 perimetro continuo a spirale) ha caveats:
- **NO top layers** (è cavo per design).
- **Bottom layers**: 3-5 solid (settable).
- **Infill = 0** (forzato).
- **Wall count = 1** (forzato).
- **Z hop disabilitato** (continuous spiral).
- **Bridge speed**: irrilevante (no horizontal flat).

Quando funziona: vasi, lampshade, contenitori decorativi.

**Quando NON usare**:
- Modelli con holes attraverso pareti.
- Modelli con multiple disconnected shells.
- Modelli con bottom non-flat (es. fondo emisferico).

## Cross-reference

- [bambu_studio_settings] — base settings documentati ufficialmente
- [bambu_studio_workflow] — overall flow
- [tree_support_tuning] — settings supports avanzati
- [bambu_3mf_export] — quali features sono preservate dall'import 3MF Blender
- [slicing_profiles] — profili pre-impostati per casi tipici

## Source

- [forum.bambulab.com/t/wall-printing-order-is-important/110212](https://forum.bambulab.com/t/wall-printing-order-is-important/110212)
- [forum.bambulab.com/t/understanding-wall-order/84649](https://forum.bambulab.com/t/understanding-wall-order/84649)
- [GitHub bambulab/BambuStudio#9166](https://github.com/bambulab/BambuStudio/issues/9166)
- [forum.bambulab.com/t/spiral-vase-seam-artifacts/181319](https://forum.bambulab.com/t/spiral-vase-seam-artifacts/181319)
- [github.com/eukatree/Bambu_CustomGCode](https://github.com/eukatree/Bambu_CustomGCode)
- [Bambu Wiki — Modifier](https://wiki.bambulab.com/en/software/bambu-studio/modifier)
- [Bambu Wiki — Print by object](https://wiki.bambulab.com/en/software/bambu-studio/sequent-print)
