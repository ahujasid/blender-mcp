# Use Case Taxonomy — mapping use_case → defaults

Quando l'utente specifica `target.use_case` nel kickoff template, l'MCP deriva una serie di defaults operativi (orient, support, infill, walls, speed, post-process) senza chiedere conferma. Questo doc è la **tabella di verità** di quei defaults.

I default qui valgono **solo se non sovrascritti** da altri campi del kickoff (es. utente specifica `printer.layer_height: 0.08mm` → ignora il default da use_case).

## Tabella sinottica

| Aspect | `display` | `mech` | `snap_fit` | `container` | `test` | `tool_print` |
|---|---|---|---|---|---|---|
| Priority | finitura | strength | tolerance | rapido + waterproof | rapido | strength |
| layer_height (medio) | 0.16mm | 0.20mm | 0.16mm | 0.20mm | 0.28mm | 0.20mm |
| layer_height (qualita) | 0.12mm | 0.16mm | 0.12mm | 0.16mm | 0.20mm | 0.16mm |
| walls | 3 | 4 | 4 | 3 | 2 | 4-5 |
| infill % | 15 | 25-40 | 100 (in load zone) | 5-10 | 10 | 30-50 |
| infill pattern | Gyroid | Cubic / Grid | Grid | Lightning | Lightning | Cubic |
| support | tree_organic | normal | nessuno (riorient invece) | nessuno (spiral mode option) | nessuno | tree_organic |
| seam | scarf | nearest | hidden | aligned | nearest | aligned |
| wall_order | Outer/Inner | Inner/Outer | Inner/Outer | Inner/Outer | Inner/Outer | Inner/Outer |
| poly_count target | 200k | 100k | preserve | 50k | 50k | 100k |
| brim | auto | conditional | conditional | required | no | required |
| post_decimate_cleanup auto | yes | yes | yes | yes | no (skip QA) | yes |
| pre_export_qa | yes | yes | yes | yes | no | yes |
| accept thin walls < 0.8mm | flag | no, ask | reject | no, ask | yes (test only) | no, ask |
| thin_walls_policy default | auto_fix | ask | reject | ask | accept_warn | ask |
| oversize_policy default | ask | ask | reject | ask | scale_down | ask |
| time bias | qualita | medio | qualita | rapido | rapido | medio |

## Dettaglio per use_case

### `display` — figurina, busto, modello decorativo

**Priority**: finitura visibile, silhouette pulita, no support marks su show side.

**Decisioni derivate**:
- `orientation`: maximizza `bottom_contact_area_mm2` su lato non-show. Penalty alto su overhang area visibile (non solo sopra il piatto).
- `support`: `tree_organic` (branch merging aggressivo, removal facile). Top Z distance 0.20mm per easy removal.
- `walls`: 3 (default Bambu Studio profile estetico). Outer/Inner per surface quality.
- `infill`: 15% Gyroid (isotropic, decorativo).
- `seam`: Scarf (eliminata da vista).
- `layer_height`: 0.16mm medio / 0.12mm qualità. Mai 0.20mm+ per display.
- `post_process_hint`: "sanding ladder 240→400 wet + primer + paint" — nel summary report.

**Pitfalls comuni**:
- AI mesh con feature 0.3-0.6mm (capelli, dita, accessori) sotto soglia FDM. → R010/R010b ask_user.
- Tree support penetra detail fine → support_painting manuale raccomandato (vedi tree_support_tuning).

### `mech` — parte meccanica, load-bearing

**Priority**: strength, dimensional accuracy, anisotropy.

**Decisioni derivate**:
- `orientation`: load axis in XY (52% Z-strength penalty per anisotropia, vedi P1 in fdm_printing_constraints). Se utente fornisce `show_side_or_load: "load: X"` → forza orient per asse.
- `walls`: 4 (resistenza superiore a infill % alto).
- `infill`: 25-40% Cubic o Grid (anisotropic = OK qui).
- `support`: normal support con angle 45° default.
- `seam`: nearest (non visibile, no overhead computational).
- `layer_height`: 0.20mm medio / 0.16mm qualità. 0.28mm draft rapido.
- `decimate`: target 100k (mech non richiede 200k display detail).

**Pitfalls comuni**:
- Z-asymmetric stress → orient sbagliato → failure precoce. Sempre forza `show_side_or_load: "load: <axis>"`.
- Hole tolerance: applica `+0.10mm` standard ma vedi 1/r scaling in bambu_a1_physical_constants per fori < 5mm.

### `snap_fit` — incastri, tolerance critica

**Priority**: dimensional tolerance, clearance corretta tra parti mating.

**Decisioni derivate**:
- `orientation`: rispetta `preserve-current` se l'utente l'ha già orientato per fits. Auto solo se richiesto.
- `walls`: 4 minimo, top_solid_layers=8 per surface piana di mating.
- `infill`: 100% in zone load (via modifier mesh Bambu Studio, vedi hidden_bambu_studio_settings), 25% altrove.
- `support`: **NESSUNO** se possibile (un brutto support su mating surface rovina la fit). Se necessario, riorienta invece di aggiungere.
- `layer_height`: 0.16mm medio / 0.12mm qualità. 0.20mm può fallire fits sotto 0.3mm clearance.
- `decimate`: **preserve** (decimate change dimensions sotto soglia tolerance).
- `thin_walls_policy`: **reject** (snap_fit con muro < 0.8mm spacca al primo test).

**Pitfalls comuni**:
- XY hole compensation: applica 1/r scaling (vedi bambu_a1_physical_constants).
- Clearance 0.20mm tra male/female. Sotto 0.15mm prints stuck.

### `container` — vasi, scatole, gusci

**Priority**: rapido, waterproof (se richiesto), no support interno.

**Decisioni derivate**:
- `orientation`: bottom-flat sempre. No discussion.
- `walls`: 3 per waterproof; 2 per decorativo non-waterproof.
- `infill`: 5-10% Lightning (decorative); 0% se Spiral Vase mode.
- `support`: **NESSUNO**. Se geometry richiede support interno, è il caso sbagliato (split + glue, non container).
- `seam`: aligned (lato meno visibile).
- `wall_order`: Inner/Outer (waterproof: deve essere preciso lateralmente).
- `layer_height`: 0.20mm default. Spiral mode richiede speed adjusted.
- `brim`: required (bottom singolo layer è soggetto a peel su geometry tall+thin).
- **Considera Spiral Vase mode** se `walls=1` accettabile (decorativo lampshade): triggera quirks (vedi hidden_bambu_studio_settings §Spiral Vase quirks).

**Pitfalls comuni**:
- Waterproof richiede 3+ walls minimum + 5+ top/bottom layers + 100% infill nei layer di transizione. Spiral mode è single-layer wall → NON waterproof.

### `test` — calibrazione, prototipo rapido

**Priority**: rapido, qualità accettabile per validation.

**Decisioni derivate**:
- `orientation`: preserve-current (utente l'ha settata di solito).
- `walls`: 2 minimo.
- `infill`: 10% Lightning.
- `support`: nessuno (test non vale support, riorienta o ristampa).
- `layer_height`: 0.28mm draft sempre.
- `decimate`: target 50k aggressivo.
- `support`: nessuno.
- `pre_export_qa`: **no** (test non merita screenshot pre-export).
- `thin_walls_policy`: accept_warn (test, non ti importa).

**Pitfalls comuni**:
- Spesso il "test" si trasforma in finale. Se l'utente cambia mente, ri-stampa con use_case più appropriato.

### `tool_print` — utensile, jig, supporto funzionale

**Priority**: strength sotto load ripetuto, dimensional stability nel tempo.

**Decisioni derivate**:
- `orientation`: load axis in XY (come `mech`).
- `walls`: 4-5 (più di mech generico per durabilità ripetuta).
- `infill`: 30-50% Cubic (Cubic ha distribuzione isotropic-ish per FDM, vs Gyroid che è veramente isotropic ma più lento).
- `support`: tree_organic (jig spesso ha overhang funzionale).
- `layer_height`: 0.20mm medio / 0.16mm qualità.
- `brim`: required (jig spesso tall+thin, soggetto a vibration).
- **Annealing post-print** raccomandato (vedi pla_post_processing_field_data §Annealing). Aggiungi nota nel summary report con curve temperatura.

**Pitfalls comuni**:
- PLA non è adatto a tool che vedono >50°C ambient (Tg=60°C). Per quei casi, consigliare PETG o materiale alternativo (ma fuori scope A1 senza enclosure).

## Override logico

Se il kickoff template specifica:
- `policies.thin_walls_policy` esplicito → vince sopra default da use_case.
- `printer.layer_height` esplicito → vince sopra default da use_case + time_budget.
- `policies.poly_count_target` esplicito → vince sopra default.
- `policies.destructive_ops_policy = "auto"` → vince anche su `use_case=snap_fit` (rischio: snap_fit con auto-destructive può rovinare fits, ma è utente choice).

Order of precedence: **utente explicit > use_case derived > MCP fallback**.

## Custom use_case (non in lista)

Se l'utente specifica un use_case non riconosciuto (es. `target.use_case: jewelry`), MCP:
1. Match il più vicino per similarità lessicale (jewelry → display).
2. **Avvisa** l'utente nel summary report: "use_case 'jewelry' non in taxonomy, ho usato defaults 'display'. Verificare."
3. Procede.

Per aggiungere un nuovo use_case stabile, aggiungere riga alla tabella sinottica + sezione dedicata + commit.

## Tabella default mapping per playbook

Riferimento veloce: quali playbook tipicamente l'MCP attiva per use_case?

| use_case | playbook tipici nell'ordine |
|---|---|
| `display` | repair_basic → decimate_to_target(200k) → repair_basic (post-decimate) |
| `mech` | repair_basic → decimate_to_target(100k) → repair_basic (post-decimate) |
| `snap_fit` | repair_basic (preserve poly count, NO decimate) |
| `container` | repair_basic → decimate_to_target(50k) → repair_basic |
| `test` | repair_basic light (no normals recalc se non serve), decimate_to_target(50k) |
| `tool_print` | repair_basic → decimate_to_target(100k) → repair_basic |

Le routing rules (R001..R013) si applicano comunque sopra questi default — se la mesh ha problemi specifici, le rule scattano regardless di use_case.

## Cross-reference

- [session_kickoff_template] — come MCP parsa il kickoff e applica questi defaults
- [orientation_strategy] — algoritmo orient per ogni policy
- [support_strategy] — decisione support type
- [mvs_filament_table] (Bambu) — per filament-driven defaults
- [slicing_profiles] (Bambu) — profili Bambu Studio corrispondenti a ogni use_case
- [tree_support_tuning] (Bambu) — settings per use_case=display/tool_print con tree_organic
- [hidden_bambu_studio_settings] (Bambu) — modifier mesh per use_case=snap_fit (infill 100% zonale)
- [pla_post_processing_field_data] (Bambu) — post-process consigliato per display + tool_print
