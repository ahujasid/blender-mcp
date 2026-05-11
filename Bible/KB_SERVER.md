# blender-kb — Knowledge Base MCP Server

Secondo MCP server, separato da `blender-mcp`, che espone il contenuto di `Bible/`
come tool MCP così l'assistente può consultare la documentazione on-demand senza
caricarla tutta nel context.

## Tool esposti

| Tool | Descrizione |
| --- | --- |
| `kb_status()` | Mostra root KB rilevata, sub-KBs trovate, numero topic, duplicati. Usalo per debug se i tool falliscono. |
| `kb_list_topics(kb_name?, band?, solves_symptom?)` | Elenca topic con metadata (titolo, "Quando usarlo", band, solves_symptoms, related). `band="A"` per i topic core del workflow STL print-prep; `band="B"` per gli adiacenti. `solves_symptom="non_manifold_edges"` filtra ai topic che risolvono quel sintomo specifico. |
| `kb_get_topic(topic_id, max_chars?)` | Markdown completo del doc associato a un `[topic_id]` (es. `mesh_repair`, `fdm_printing_constraints`, `analyze_to_action`). |
| `kb_search(query, kb_name?, max_results?, context_lines?)` | Grep substring case-insensitive sui doc indicizzati. Per ricerca strutturata su sintomo preferisci `kb_list_topics(solves_symptom=...)`. |
| `kb_read(relative_path, max_chars?)` | Escape hatch per file non indicizzati per topic_id (es. `FIELD_NOTES.md`, `SYSTEM_PROMPT.md`, `Printer Infos/*.md`). Path containment-checked. |
| `kb_route(analysis_json)` | **Decision tree** sopra l'output di `analyze_mesh_for_print`. Restituisce le regole matchate (ordinate per priority) e `next_action` direttamente eseguibile (`kb_get_playbook`, `kb_get_topic`, `ask_user`, `ready`). Vedi `Blender for 3d print documentation/docs/analyze_to_action.md` per l'elenco completo delle 9 regole R001-R009. |
| `kb_list_playbooks()` | Elenca i playbook disponibili (`repair_basic`, `recalc_normals`, `repair_aggressive`, `decimate_to_target`) con `step_count` e `when_to_use`. |
| `kb_get_playbook(playbook_id)` | Restituisce il JSON completo di un playbook: `params`, `steps[]` (con `tool`+`code`), `verification` (re-analyze + expected delta), `topic_refs`. L'**esecuzione** spetta all'assistente tramite `blender-mcp` (`execute_blender_code`); il server `blender-kb` non esegue nulla. |

## Prompt

- `kb_bootstrap()` — restituisce `CLAUDE.md` + `SYSTEM_PROMPT.md` + tabella sintetica di tutti i topic_id. Da invocare come primo messaggio di sessione invece di copia-incollare manualmente `INITIAL_PROMPT.md`.

## Workflow consigliato

Per ogni STL Meshy in input:

```
1. import_stl(path)                                  # → blender-mcp
2. analysis = analyze_mesh_for_print(name)           # → blender-mcp
3. route = kb_route(analysis)                        # → blender-kb
4. for step in route.matched_rules (in order):
       if step.needs_user_input:
           chiedi → applica decisione
       elif step.playbook:
           pb = kb_get_playbook(step.playbook)
           sostituisci {param} in pb.steps[*].code
           execute_blender_code(rendered)            # → blender-mcp
       else:
           kb_get_topic(step.topic_id) e improvvisa
       analysis = analyze_mesh_for_print(name)       # verifica delta
5. preprint_validation + export_stl                  # → blender-mcp
```

## Come si trova la KB

Ordine di risoluzione della root:
1. variabile env `BLENDER_KB_PATH`
2. `$CWD/Bible`
3. la `$CWD` stessa, se contiene `CLAUDE.md` + sub-folder con `INDEX.md`
4. walk-up dalla CWD per max 6 livelli, provando ogni `<parent>/Bible` e ogni `<parent>`

Una directory è considerata "KB root" valida se contiene `CLAUDE.md` E almeno una sub-folder con `INDEX.md` (oggi: `Blender for 3d print documentation/` e `Bambu Wiki documentation/`).

## Setup in `.mcp.json`

Il file `Bible/.mcp.json` ha già due placeholder da sostituire (path assoluti):

```json
{
  "mcpServers": {
    "blender": { "command": "uvx", "args": ["--python", "3.12", "blender-mcp"] },
    "blender-kb": {
      "command": "uv",
      "args": [
        "run", "--python", "3.12",
        "--directory", "<ABS_PATH_TO_FORK_ROOT>",
        "blender-kb"
      ],
      "env": { "BLENDER_KB_PATH": "<ABS_PATH_TO_BIBLE_FOLDER>" }
    }
  }
}
```

Esempi:
- Windows: `"--directory", "C:/Users/emanu/blender-mcp"` e `"BLENDER_KB_PATH": "C:/Users/emanu/blender-mcp/Bible"`
- macOS/Linux: `"--directory", "/Users/me/blender-mcp"` e `"BLENDER_KB_PATH": "/Users/me/blender-mcp/Bible"`

`uv run --directory <fork>` installa le deps del fork in una venv locale al fork, e lancia il binario `blender-kb` registrato in `pyproject.toml`. Niente push su PyPI necessario.

Quando il branch verrà mergiato e pubblicato, si potrà semplificare in:
```json
"blender-kb": {
  "command": "uvx",
  "args": ["--python", "3.12", "--from", "git+https://github.com/emanueleiacca/blender-mcp", "blender-kb"],
  "env": { "BLENDER_KB_PATH": "<ABS_PATH_TO_BIBLE_FOLDER>" }
}
```

## Smoke test manuale

Dalla root del fork, con `Bible/` accanto:

```bash
BLENDER_KB_PATH="$PWD/Bible" uv run --python 3.12 blender-kb
```

Output atteso nel log:
```
KB loaded: root=.../Bible, sub-KBs=['Bambu Wiki documentation', 'Blender for 3d print documentation'], topics=60
```

Poi il server resta in attesa su stdio.

## Manutenzione KB

Due script in `Bible/scripts/`:

- `validate_kb.py` — controlla coerenza interna: ogni `[topic_id]` ha un file
  esistente, ogni `related:` punta a topic veri, ogni `routing_rules.yaml` rule
  referenzia topic + playbook esistenti, ogni playbook ha `id == filename`,
  ogni code block ```python parsa con `ast.parse`. Esegui dopo qualsiasi
  modifica alla KB:
  ```bash
  cd Bible && BLENDER_KB_PATH=$PWD uv run --project <fork> python scripts/validate_kb.py
  ```
- `eval_dry.py` — esegue `kb_route` su ogni caso in `eval/eval_cases.yaml` e
  confronta `next_action` con la pipeline attesa. Non serve Blender vivo.
  Usalo per detect regression dopo modifiche a `routing_rules.yaml` o ai
  playbook:
  ```bash
  cd Bible && BLENDER_KB_PATH=$PWD uv run --project <fork> python scripts/eval_dry.py
  ```

## Limiti noti

- `kb_search` è un grep substring case-insensitive, non semantico. Per ricerca
  strutturata su sintomi preferisci `kb_list_topics(solves_symptom=...)`.
  Embedding/RAG semantico è fuori scope (zero-dep).
- Topic_id devono essere unici tra sub-KB; collisioni vengono registrate in
  `kb_status.duplicate_topic_ids` ma il secondo viene ignorato.
- Il parser di `INDEX.md` riconosce solo blocchi che iniziano con `## [topic_id]`
  e che contengono una riga `File: \`path\``. Heading non conformi vengono
  saltati silenziosamente.
- L'index viene caricato una sola volta all'avvio del server. Se modifichi
  `INDEX.md`, `INDEX.yaml`, `routing_rules.yaml` o un playbook, riavvia il
  server MCP perché il KB sia ricaricato.
- I topic in `_archive/` non sono mai esposti via `kb_list_topics`/`kb_search`.
  Per leggerli usa `kb_read("Blender for 3d print documentation/_archive/docs/<file>.md")`.
- L'esecuzione dei playbook è responsabilità di `blender-mcp`
  (`execute_blender_code`). `blender-kb` non lancia codice Blender;
  questa separazione è intenzionale per permettere verifica step-by-step.
