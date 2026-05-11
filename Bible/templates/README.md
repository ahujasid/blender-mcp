# Templates — guida d'uso

Template per iniziare una sessione MCP con tutto il context necessario. Compili UNA volta per progetto, l'MCP minimizza gli stop "domande iniziali".

## Quale formato usare

Due file equivalenti, scegli quello che ti è più comodo:

- **`session_kickoff.md`** — Markdown. Visivamente più chiaro per editing manuale. Più tollerante a errori di sintassi (campi mancanti = MCP parsa comunque).
- **`session_kickoff.jsonc`** — JSON con commenti `//`. Strutturato, può essere parsato programmaticamente da uno script tuo per generare prompt automatici. Se ti serve solo JSON puro, rimuovi i commenti `//` a mano (oppure il tuo parser supporta JSONC).

Entrambi contengono **identici** campi e semantica. L'MCP riconosce entrambi.

## Workflow tipico

1. Importi STL/GLB in Blender manualmente.
2. **Copia** uno dei due template fuori da `Bible/templates/` (es. in `~/projects/dragon_v1/kickoff.md`).
3. Compila i placeholder `<...>`. Lascia "auto" o stringa vuota dove vuoi che decida l'MCP.
4. Apri il tuo client MCP (Claude Desktop / Cursor / Claude Code).
5. Incolla il contenuto come **primo messaggio** della sessione, prefissato da una riga tipo:
   ```
   Esegui il workflow STL print-prep secondo questo kickoff:
   [paste template]
   ```
6. L'MCP parsa, identifica campi vitali mancanti (se ce ne sono), chiede solo quelli in un singolo round, poi procede.

## Campi vitali — cosa serve sempre

L'MCP **bloccherà chiedendo** se i seguenti mancano e non sono inferibili:

| Campo | Cosa serve sapere |
|---|---|
| `object.name` (o `auto`) | Quale mesh trattare nella scena |
| `target.use_case` | Per scegliere defaults di orient/support/infill/walls |
| `target.dimension` | Per scalare correttamente (mesh AI è normalizzata) |

Tutto il resto ha default sensati. Vedi [docs/session_kickoff_template.md] e [docs/use_case_taxonomy.md] per come l'MCP interpreta ogni campo.

## Convenzione placeholder

In **markdown**:
```
campo: <valore>
```
Sostituisci `<valore>` con quello che vuoi. Le righe `#` sotto sono commenti — restano nel file ma vengono ignorati dal parser.

In **JSONC**:
```jsonc
"campo": "<valore>"
```
Sostituisci `"<valore>"` (incluse le virgolette esterne) con un nuovo string/number/null secondo il tipo aspettato.

**Default**: stringa vuota `""` o `null` significano "MCP decida".

## Esempi di kickoff già compilati

Per casi tipici:

### Figurina display 80mm in PLA Basic

```yaml
object.name: dragon
object.source_generator: meshy
target.use_case: display
target.dimension: { axis: height, mm: 80 }
target.orientation: auto
target.show_side_or_load: "front + 3/4"
printer.filament: pla_basic
printer.layer_height: 0.12mm
policies.sculpt_manual_allowed: no
policies.thin_walls_policy: auto_fix
output.path: ~/print_ready/dragon.stl
```

### Parte meccanica snap-fit M3 con tolerance

```yaml
object.name: bracket
object.source_generator: cad
target.use_case: snap_fit
target.dimension: { axis: longest, mm: 60 }
target.orientation: flat-bottom
target.show_side_or_load: "load: Y"
printer.filament: pla_basic
printer.layer_height: 0.16mm
printer.time_budget: qualita
policies.poly_count_target: preserve
policies.thin_walls_policy: ask
output.path: ~/print_ready/bracket_v2.stl
output.format: 3mf
```

### Test rapido calibrazione

```yaml
object.name: auto
target.use_case: test
target.dimension: { axis: preserve }
target.orientation: preserve-current
printer.time_budget: rapido
policies.poly_count_target: 50000
policies.thin_walls_policy: accept_warn
policies.destructive_ops_policy: auto
output.pre_export_qa: no
```

## Aggiornamento template

Quando aggiungiamo nuovi campi vitali (es. dopo le prime prove), aggiorniamo i template qui mantenendo backward-compat: i campi nuovi hanno sempre default sensati, sessioni vecchie continuano a funzionare.

Se vedi nel template campi che non capisci, vedi:
- [docs/session_kickoff_template.md] — semantica per ogni campo
- [docs/use_case_taxonomy.md] — tutti i defaults derivati da `use_case`
- [docs/mcp_blind_operating_protocol.md] — il protocollo MCP che consuma questo kickoff
