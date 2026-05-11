# Sessions — log delle sessioni MCP

Una sessione = un workflow completo dal kickoff template all'STL/3MF export. L'MCP scrive un file YAML qui per ogni sessione completata. È il **carburante** del learning loop: review cross-sessione, pattern detection, default tuning.

## Layout

```
Bible/sessions/
  README.md                                    # questo file
  2026-05-11_dragon_v1.yaml                    # log tecnico, versionato
  2026-05-11_dragon_v1_introspection.yaml      # opzionale, generato da review
  2026-05-12_bracket_snap.yaml
  _private/                                    # GITIGNORED — note personali
    2026-05-11_dragon_v1.md                    # note free-text utente
    .gitkeep
```

## Convenzione naming

`<YYYY-MM-DD>_<short_name>[_v<n>].yaml`

- Date in ISO 8601, formato locale dell'utente — non ISO time perché serve solo ordering.
- `short_name` deriva da `kickoff.object.name` se compilato, altrimenti `mesh` generico.
- Suffisso `_v<n>` solo per re-print dello stesso modello: `dragon_v1.yaml`, `dragon_v2.yaml`.

## Cosa c'è nel YAML

Vedi `Bible/templates/session_log_example.yaml` per il template completo. Sezioni principali:

| Sezione | Scritta da | Contenuto |
|---|---|---|
| `session.id`, `started`, `ended`, `duration_s`, `status` | MCP | metadata sessione |
| `kickoff` | MCP (echo) | il template kickoff compilato dall'utente |
| `scene_initial` | MCP | scene state pre-pipeline (objects, scale_length, blender version) |
| `steps[]` | MCP | ogni decisione/operazione con pre/post metrics |
| `final_analysis`, `output` | MCP | snapshot pre-export + file output + estimates |
| `feedback` | **Utente** | 3 campi post-mortem (satisfaction, flagged_steps, notes) |
| `introspection` | MCP | metriche aggregate + observations + suggested KB updates |

L'utente compila solo `feedback`. Tutto il resto è automatico.

## Privacy

- File `*.yaml` qui sono **versionati** nel repo per traceability + cross-session review.
- File `_private/<id>.md` sono **gitignored** (vedi `.gitignore` root). Servono per note testuali sensibili (commenti su clienti, business logic, ecc.).
- Riferimento dal log YAML al file private via `feedback.private_notes_ref: "_private/<id>.md"`.

Default: l'MCP NON scrive nulla in `_private/` di sua iniziativa. Lo crei tu se vuoi.

## Lifecycle di un session log

### Creazione (a fine sessione)

L'MCP, dopo `export_stl`, esegue (via `execute_blender_code`):

```python
import yaml, datetime, pathlib
session_dict = {...}  # accumulated durante la pipeline
out = pathlib.Path("<BIBLE_ROOT>/sessions/2026-05-11_dragon_v1.yaml")
out.write_text(yaml.safe_dump(session_dict, sort_keys=False, allow_unicode=True))
```

(Il path assoluto a `<BIBLE_ROOT>` deve essere noto all'MCP — vedi `BLENDER_KB_PATH` env var.)

### Feedback utente (post-mortem)

L'MCP scrive il YAML con `feedback.satisfaction: unanswered`, poi chiede all'utente max 3 domande in un solo messaggio:

> Sessione completata. Output: ~/print_ready/dragon.stl (148k tris, ~18g PLA, ~2.3h print).
>
> Per migliorare le sessioni future (opzionale, premi invio per accettare default):
> 1. Soddisfatto del risultato? (positive/neutral/negative)
> 2. Step problematici? (es. "3, 7" oppure lascia vuoto)
> 3. Note? (free text, opzionale — andrà in `feedback.notes`)

Se l'utente risponde, l'MCP aggiorna il file con i valori. Se non risponde entro il turno, mantiene `unanswered`.

### Cross-session review (on-demand)

Quando l'utente lancia un prompt tipo:

> "Review ultime 10 sessioni e identifica pattern."

L'MCP:
1. `kb_read("sessions/2026-05-*.yaml")` per ognuna delle ultime 10 (oppure tutte se < 10).
2. Aggrega in memoria.
3. Detecta pattern:
   - Routing rules che match ma il delta atteso non è raggiunto frequentemente.
   - Default `use_case` che l'utente sovrascrive ripetutamente (es. layer_height).
   - Ask_user pattern ricorrenti che potrebbero diventare rule automatiche.
   - Topic referenced che la KB non copre → gap detection.
4. Output: report testuale con `suggested_kb_updates` per ogni pattern.
5. L'utente **decide manualmente** quali fix applicare. L'MCP NON modifica autonomamente la KB.

## Quando NON viene scritto un log

L'MCP **non** scrive il file YAML se:
- Sessione abbandonata prima del primo `analyze_mesh_for_print` (niente da loggare).
- Errore fatale prima di qualsiasi step utile.
- L'utente lo richiede esplicitamente nel kickoff (`policies.session_logging: no` — campo opzionale futuro).

Negli altri casi (anche failure parziali), il log viene scritto con `status: failed` o `status: partial_user_required`.

## Cross-reference

- `Bible/templates/session_log_example.yaml` — schema YAML completo compilato
- [learning_loop] — protocollo completo end-to-end
- [mcp_blind_operating_protocol] §"End-of-session log" — quando MCP scrive il log
- [session_kickoff_template] — input al protocollo
