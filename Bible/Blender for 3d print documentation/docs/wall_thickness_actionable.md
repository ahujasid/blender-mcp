# Wall Thickness — Actionable Decision Tree

Quando `analyze_mesh_for_print` riporta:
- `wall_thickness_p10_mm` — il 10° percentile (10% delle facce ha spessore ≤ questo valore)
- `wall_thickness_p50_mm` — mediana
- `wall_thickness_under_min_pct` — % di facce con spessore < 0.8mm (FDM A1, 2 perimetri nozzle 0.4mm)

Questa pagina mappa le soglie alle azioni concrete. Triggered da rule R010 in `routing_rules.yaml`.

## Soglie fisiche FDM Bambu A1

Riferimento (vedi anche [fdm_printing_constraints]):

| Spessore | Conseguenza slicer |
|---|---|
| `< 0.21 mm` | < line_width 0.42mm. Lo slicer **non genera traccia**. Stamperà come buco. |
| `0.21–0.45 mm` | 1 perimetro forzato. Funziona ma fragile, no infill possibile. |
| `0.45–0.80 mm` | 1 perimetro robusto (parete singola). OK per gusci decorativi, non per parti funzionali. |
| `0.80–1.20 mm` | 2 perimetri (sweet spot per la maggior parte degli oggetti FDM). |
| `> 1.20 mm` | 3+ perimetri. Resistenza meccanica progressivamente migliore. |

## Decision tree

### Caso A — `wall_thickness_p10_mm >= 0.8` AND `wall_thickness_under_min_pct < 1.0`

**Stato**: nessuna azione. La mesh è ben dimensionata per FDM A1. La rule R010 non scatta.

### Caso B — `wall_thickness_p10_mm < 0.8` AND `wall_thickness_under_min_pct < 5.0`

**Diagnosi**: alcune zone marginali. Tipicamente bordi sottili (es. orecchie, dita, antenne).

**Opzioni** (in ordine di preferenza):

1. **Solidify globale +0.3mm**:
   ```python
   import bpy
   obj = bpy.data.objects['<name>']
   mod = obj.modifiers.new(name="AutoSolidify", type='SOLIDIFY')
   mod.thickness = 0.0003  # 0.3mm con scale_length=1.0
   mod.offset = 0           # spessore aggiunto simmetricamente
   mod.use_even_offset = True
   mod.use_rim_only = False
   bpy.context.view_layer.objects.active = obj
   bpy.ops.object.modifier_apply(modifier="AutoSolidify")
   ```
   Pro: rapido, deterministico. Contro: gonfia tutto il modello, non solo le aree sottili.

2. **Solidify selettivo via vertex group** (se hai accesso manuale):
   selezionare facce thin nel viewport → assegnare a vertex group → Solidify con `vertex_group="thin"` e `offset=0`.
   Non scriptabile via MCP senza intervento utente; richiede ask_user.

3. **Accetta e flagga al slicer**: documenta nel report di export che ci sono `X%` di facce sotto soglia. Bambu Studio applicherà 1-perimetro automaticamente. Funziona per gusci decorativi.

### Caso C — `wall_thickness_p10_mm < 0.45` OR `wall_thickness_under_min_pct >= 5.0`

**Diagnosi**: problema strutturale. Una porzione significativa della mesh non è stampabile com'è.

**Opzioni**:

1. **Solidify aggressivo +0.5mm** (analogo al Caso B punto 1, `thickness=0.0005`). Verifica visiva richiesta perché può cambiare significativamente la silhouette.

2. **Re-design / split**: chiedi all'utente. Casi tipici:
   - **Figurine con appendici sottili** (capelli, dita, accessori): l'autore AI ha generato dettagli troppo fini per FDM. Decidere se ingrandire l'intero modello (scala +30%) o accettare la perdita di alcuni dettagli.
   - **Parti meccaniche con flange sottili**: ingrossare le flange tramite Solidify mirato (non globale).
   - **Modelli da scalare**: spesso `wall_thickness < 0.45mm` è solo conseguenza di `dimensions_mm` troppo piccolo. Verificare prima con [scale_detection].

3. **Stampa con 0.2mm nozzle**: cambia hardware. Il Bambu A1 supporta nozzle 0.2mm — la soglia minima scende a 0.21mm, e Caso C diventa Caso B. Costo: stampa molto più lenta, richiede hardened nozzle per filamenti compositi.

### Caso D — `wall_thickness_p10_mm is null`

**Diagnosi**: la mesh non è watertight. Il calcolo di wall thickness è disabilitato perché su mesh aperta i raggi escono dai buchi e producono falsi positivi.

**Azione**: prima ripara la mesh (rule R004 / R005 / Voxel Remesh), poi ri-`analyze`, poi valuta wall thickness.

## Caveat sul sampling

Il calcolo è raycast su massimo 5000 face centroids (sampling deterministico, seed=42). Conseguenze:

- **Falsi negativi**: una feature sottile rappresentata da poche facce può essere mancata. Per zone critiche specifiche usa `measurement_toolkit.wall_thickness_at_point()` con punti scelti dall'utente.
- **p10 vs minimo**: usiamo il 10° percentile, non il minimo. Il minimo è dominato da outlier (1-2 facce sliver post-decimate). Se ti serve il vero minimo, esegui un secondo pass con `max_samples = len(faces)`.
- **Convex parts**: superfici esterne di solidi convessi non hanno "wall" — il raycast attraversa l'intero solido. La metrica wall thickness ha senso solo su parti con cavità interne / pareti definite. Su un cubo pieno `p10` sarà la dimensione minore del cubo.

## Relazione con altri topic

- [measurement_toolkit] — `wall_thickness_at_point`, `wall_thickness_distribution`: versioni puntuali / massive per analisi più dettagliate.
- [fdm_printing_constraints] §Wall Thickness — tabella completa nozzle/perimetri.
- [bambu_a1_physical_constants] — line_width 0.42mm, regola "CAD thickness = N × line_width".
- [preprint_validation] — wall thickness è uno dei 10 check del validatore finale.
