# Learning Loop — imparare con la pratica

L'MCP non è statico. Ogni sessione produce dati strutturati (session log) che diventano carburante per migliorare la KB. Questo doc codifica il protocollo: cosa scrivere, quando, come fare review periodica, come tradurre pattern in fix concreti.

## Tre livelli di feedback

Separazione netta per non essere fastidioso:

### Livello 1 — In-flight (zero overhead, opzionale)

L'unico friction in-flight è già esistente: gli `ask_user` legittimi (oversize_policy, shells multiple, scale ambigua). NON aggiungiamo altre domande durante l'esecuzione.

C'è un campo `user_tag` opzionale per ogni `ask_user` step (vedi schema in `Bible/templates/session_log_example.yaml`). L'utente può aggiungere un tag se vuole flaggare la domanda stessa (es. "wrong_question", "ambiguous_options") — ma è zero-friction: se non lo usa, il campo resta `null`.

### Livello 2 — End-of-session (3 domande, opzionale)

A fine workflow l'MCP scrive il session log con `feedback.satisfaction: unanswered`, poi chiede in **un solo messaggio**:

```
Sessione completata in 202s. Output: ~/print_ready/dragon.stl
(148k tris, ~18g PLA, ~2.3h print).

Per il learning loop (tutto opzionale — premi invio per accettare i default):
1. Soddisfatto? (positive / neutral / negative — default: positive)
2. Step problematici? (es. "8, 13" oppure vuoto)
3. Note brevi? (free text — vai in feedback.notes)

Per note lunghe / sensibili: scrivile in Bible/sessions/_private/<session_id>.md
(gitignored) e indicami il path.
```

Se l'utente risponde, MCP aggiorna il file con i valori. Se non risponde (passa al prompt successivo senza rispondere), MCP mantiene `unanswered` e NON insiste.

### Livello 3 — Cross-session review (on-demand)

Quando vuoi, lanci un prompt esplicito:

> "Review ultime 10 sessioni in Bible/sessions/ e identifica pattern."

L'MCP legge i log, aggrega, ti propone fix. Vedi sezione "Review protocol" sotto.

## Schema del session log

Vedi `Bible/templates/session_log_example.yaml` per il riferimento completo. Sezioni essenziali:

| Sezione | Chi scrive | Quando |
|---|---|---|
| `session.id`, `started`, `ended`, `status`, `blender_version` | MCP | Continuo durante esecuzione |
| `kickoff` | MCP (echo) | T+0 dal kickoff template |
| `scene_initial` | MCP | T+0 dopo `get_scene_info` |
| `steps[]` | MCP | Append a ogni step |
| `final_analysis`, `output` | MCP | Dopo `export_stl` |
| `feedback` | Utente | Post-mortem (3 domande) |
| `introspection.metrics`, `observations` | MCP | A fine sessione, automatic |
| `introspection.suggested_kb_updates` | MCP | Solo se pattern chiaro su singola sessione (raro) |

## Lifecycle

### Creazione del log

A fine pipeline (dopo `export_stl` o failure), MCP scrive il YAML:

```python
# Eseguito via execute_blender_code dal MCP
import yaml, datetime, os, pathlib

# session_dict è accumulato durante la pipeline come variabile in-memory
# Schema: vedi Bible/templates/session_log_example.yaml

bible_root = os.environ.get("BLENDER_KB_PATH")  # noto al server MCP
if bible_root:
    sessions_dir = pathlib.Path(bible_root) / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    session_id = session_dict["session"]["id"]
    out_path = sessions_dir / f"{session_id}.yaml"

    with open(out_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            session_dict, f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
    print(f"Session log written: {out_path}")
else:
    print("BLENDER_KB_PATH not set, skipping session log")
```

Path target convention: `<BIBLE_ROOT>/sessions/<YYYY-MM-DD>_<short_name>.yaml`.

`short_name` = `kickoff.object.name` sanitized (lowercase, no special chars). Se omonimi nella stessa giornata, append `_v2`, `_v3`, ecc.

### Update feedback post-mortem

Dopo scrittura iniziale, MCP chiede 3 domande all'utente. La risposta arriva nel turn successivo. MCP rilegge il YAML, aggiorna `feedback.*`, riscrive.

```python
# Read-modify-write
with open(out_path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

data["session"]["feedback"] = {
    "satisfaction": user_satisfaction,  # da parsing risposta utente
    "flagged_steps": user_flagged_steps,
    "notes": user_notes_short,
    "private_notes_ref": private_path_or_null,
}

with open(out_path, "w", encoding="utf-8") as f:
    yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
```

### Note private opzionali

Se l'utente vuole scrivere note lunghe/sensibili, le mette in `Bible/sessions/_private/<session_id>.md` (gitignored). MCP riferisce dal log: `feedback.private_notes_ref: "_private/<id>.md"`. Non legge il content del file private a meno che l'utente non lo chieda esplicitamente.

## Review protocol — cross-session pattern detection

### Trigger

L'utente lancia un prompt esplicito tipo:

- "Review ultime 10 sessioni."
- "Quali rule sbagliano spesso?"
- "Dimmi se ci sono default da aggiornare."

### Sequenza MCP

1. **Discover**: lista file YAML in `Bible/sessions/` ordinati per data, prendi ultimi N (default 10).
   ```python
   kb_read("sessions/")  # NB: kb_read è su file, per listing usa execute_blender_code con pathlib.glob
   ```

2. **Load**: leggi tutti i YAML in memoria. Skip file con `status: abandoned` o malformati.

3. **Aggregate metrics**:
   - Rule match frequency: quante volte ogni `rule_id` è apparso in `matched_rules` o `priority_order`.
   - Rule success rate: per ogni rule, % di volte che `expected_after` è stato met.
   - User override frequency: per ogni `kickoff` field, % di volte che valore non-default è stato usato.
   - Ask_user frequency: quale `rule_id` triggera ask più spesso.
   - Pipeline duration distribution per `use_case`.
   - Failure modes ricorrenti (assessment != ok).

4. **Pattern detection** (vedi sezione successiva).

5. **Report**: messaggio testuale strutturato con osservazioni e `suggested_kb_updates`.

6. **Utente decide**: per ogni fix proposto, l'utente conferma "applica" / "skip" / "modifica". L'MCP genera il diff (markdown edit, routing rule change, taxonomy update) ma **non committa autonomamente**.

### Pattern tipici da cercare

| Pattern | Detection condition | Suggested fix |
|---|---|---|
| Rule che match ma raramente porta a delta atteso | `success_rate < 0.6` per N >= 3 match | Tightening della soglia OR rimozione rule |
| Default che viene sovrascritto frequentemente | `kickoff.X.Y != default` in > 60% delle sessioni | Aggiornare default in `use_case_taxonomy` o `session_kickoff_template` |
| Ask_user pattern con risposta uniforme | Stesso rule_id → ask_user → utente risponde sempre uguale (es. sempre "union") | Trasformare la rule da `needs_user_input` ad auto-action |
| Topic referenced ma assente | Utente nel `feedback.notes` o `flagged_steps` menziona concetto non in INDEX | Topic gap → proporre creazione nuovo doc |
| Failure mode ricorrente | Stesso `assessment: failed` su step con stesso playbook | Bug nel playbook OR pre-flight insufficiente |
| Time outlier | Pipeline duration anomalmente alta per use_case | Profiling: quale step è lento? Possibile ottimizzazione |
| Pre-flight gap | Step 1 risolto via kickoff in > 80% sessioni | Promuovere quel campo a default-vital nel template |

### Esempio output review

Dopo "Review ultime 10 sessioni":

```yaml
review:
  period: [2026-05-01, 2026-05-11]
  n_sessions: 10
  n_by_use_case:
    display: 6
    mech: 3
    test: 1
  n_by_status:
    completed: 9
    partial_user_required: 1

  rule_stats:
    R013:
      matched: 7
      success_rate: 0.43          # solo 3/7 hanno raggiunto aspect_ratio_p95 < 8 dopo playbook
      observation: |
        aspect_ratio_p95 soglia 10 sembra troppo permissiva — match anche quando
        il playbook produce miglioramento marginale (-1.2 a -2.0).

  default_override_stats:
    printer.layer_height (use_case=display):
      default: 0.16mm
      sovrascritto: 5/6 sessioni
      sovrascritto_a: ["0.12mm" x4, "0.08mm" x1]
      observation: |
        Quasi sempre l'utente preferisce 0.12mm per display. Considera
        cambiare default in use_case_taxonomy.

  topic_gap_signals:
    - mentioned_in: [session 2026-05-04_bracket, session 2026-05-07_clip]
      keyword: "snap-fit clearance per inserti filettati M3"
      observation: |
        Non c'è topic dedicato a tolerance per inserti filettati. Vedi
        bambu_a1_physical_constants §Tolleranze ma manca decision tree
        per inserto heat-set vs press-fit.

  suggested_kb_updates:
    - id: U1
      severity: medium
      target: Bible/Blender for 3d print documentation/routing_rules.yaml
      change: |
        Modificare R013: aspect_ratio_p95 "> 10" → "> 12".
        Rationale: success_rate 0.43 indica match troppo permissivo.
        Eval check: rifai eval_dry, deve continuare a pass su
        synthetic_aspect_ratio_only (current p95=13.2 ancora dentro > 12).
    - id: U2
      severity: high
      target: Bible/Blender for 3d print documentation/docs/use_case_taxonomy.md
      change: |
        Tabella sinottica, riga "layer_height (medio)" colonna "display":
        cambiare 0.16mm → 0.12mm.
        Rationale: 5/6 sessioni display l'utente sovrascrive a 0.12.
    - id: U3
      severity: medium
      target: nuovo topic Bible/Blender for 3d print documentation/docs/threaded_inserts.md
      change: |
        Creare topic dedicato a snap-fit / press-fit / heat-set inserto M3.
        Sezioni: tolerance recommended (heat-set: bore +0.2mm; press-fit:
        bore -0.1mm vs nominal), depth, wall thickness intorno all'inserto.

next_action_for_user: |
  Per ogni suggested_kb_update sopra, conferma con:
  - applica U1
  - applica U2
  - skip U3 (lo facciamo dopo)
  Oppure: applica tutti / skip tutti.
```

L'utente legge, decide. L'MCP applica solo quello che è stato confermato.

## Triage del review — quando lanciarlo

Suggerimenti operativi:
- **Dopo ogni 5 sessioni** se sei in fase di tuning attivo. Pattern emergono.
- **Dopo ogni rilascio di modifica significativa alla KB** (es. nuovo playbook, nuova rule). Verifica che il cambio non abbia regressioni.
- **Quando senti "fa sempre lo stesso errore"**. Il review oggettivizza il sospetto.
- **Mai automatico**: lanciare review è una scelta deliberata. L'MCP non ti propone "vuoi fare review?" — saresti fastidiato.

## Schema YAML — minimal vs full

L'esempio in `Bible/templates/session_log_example.yaml` è "full" (15 step, tutti i campi optional valorizzati). Una sessione minimal reale potrebbe essere così:

```yaml
session:
  id: 2026-05-12_test_cube
  started: 2026-05-12T09:15:00Z
  ended: 2026-05-12T09:15:42Z
  duration_s: 42
  status: completed
  kickoff:
    object: { name: Cube }
    target: { use_case: test, dimension: { axis: preserve } }
  scene_initial:
    objects: [{ name: Cube, type: MESH }]
    unit_scale_length: 1.0
  steps:
    - { id: 1, action: analyze_mesh_for_print,
        result_summary: { face_count: 12, ready_to_slice: true }, assessment: ok }
    - { id: 2, action: kb_route,
        result_summary: { matched_rules: [], next_action: { tool: ready } }, assessment: ok }
    - { id: 3, action: export_stl,
        args: { filepath: ~/test/cube.stl }, assessment: ok }
  final_analysis: { face_count: 12, ready_to_slice: true, dimensions_mm: [2.0, 2.0, 2.0] }
  output:
    files: [{ path: ~/test/cube.stl, size_bytes: 684 }]
  feedback: { satisfaction: unanswered }
  introspection:
    metrics: { all_expected_after_met: true, ask_user_count: 0 }
    observations: ["Test cube, nothing to do, ready_to_slice immediato."]
```

Schema flessibile: omettere field opzionali è OK. L'MCP scrive solo quello che ha. Il review code aggrega solo quello che trova.

## Storage growth & rotazione

YAML è human-readable ma cresce. Stime rough:
- Session log medio (10-20 step): 5-15KB.
- Dopo 100 sessioni: ~1MB. Manageable.
- Dopo 1000+ sessioni: ~10MB. Considera rotazione (`Bible/sessions/_archive/2026/`).

Per ora: nessuna rotazione automatica. Se il volume cresce, archive manuale.

## Privacy summary

- `Bible/sessions/*.yaml` → **versionato in repo**. Contiene metric/decisioni/ma NON note personali.
- `Bible/sessions/_private/*.md` → **gitignored**. Free text personale dell'utente.
- `feedback.notes` (dentro il YAML) → max 1-2 righe, comunque scarica nel repo. Per note lunghe/sensibili usa `_private/`.

Se cambi idea e vuoi che ANCHE i YAML siano privati, sposta `Bible/sessions/` a gitignore. Tutto il sistema continua a funzionare locale.

## Cross-reference

- `Bible/sessions/README.md` — directory layout + naming convention
- `Bible/templates/session_log_example.yaml` — schema YAML completo
- [session_kickoff_template] — input al protocollo (kickoff template)
- [mcp_blind_operating_protocol] §"Session kickoff protocol" — T+0 workflow
- [use_case_taxonomy] — target per default tuning via review
- [analyze_to_action] — routing rules target per tuning via review
