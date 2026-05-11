# blender-kb — Knowledge Base MCP Server

Secondo MCP server, separato da `blender-mcp`, che espone il contenuto di `Bible/`
come tool MCP così l'assistente può consultare la documentazione on-demand senza
caricarla tutta nel context.

## Tool esposti

| Tool | Descrizione |
| --- | --- |
| `kb_status()` | Mostra root KB rilevata, sub-KBs trovate, numero topic. Usalo per debug se i tool falliscono. |
| `kb_list_topics(kb_name?)` | Elenca tutti i topic indicizzati (con titolo + "Quando usarlo"). Filtra opzionalmente per sub-KB. |
| `kb_get_topic(topic_id, max_chars?)` | Restituisce il markdown completo del doc associato a un `[topic_id]` (es. `mesh_repair`, `fdm_printing_constraints`). |
| `kb_search(query, kb_name?, max_results?, context_lines?)` | Grep case-insensitive su tutti i doc indicizzati. Ritorna snippet con riga e topic. |
| `kb_read(relative_path, max_chars?)` | Escape hatch per file non indicizzati per topic_id (es. `FIELD_NOTES.md`, `SYSTEM_PROMPT.md`, `Printer Infos/*.md`). Path containment-checked. |

## Prompt

- `kb_bootstrap()` — restituisce `CLAUDE.md` + `SYSTEM_PROMPT.md` + tabella sintetica di tutti i topic_id. Da invocare come primo messaggio di sessione invece di copia-incollare manualmente `INITIAL_PROMPT.md`.

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
KB loaded: root=.../Bible, sub-KBs=['Bambu Wiki documentation', 'Blender for 3d print documentation'], topics=66
```

Poi il server resta in attesa su stdio.

## Limiti noti

- `kb_search` è un grep substring case-insensitive, non semantico. Per ricerca semantica servirebbe embedding + indice vettoriale (out of scope per ora).
- Topic_id devono essere unici tra sub-KB; collisioni vengono registrate in `kb_status` ma il secondo viene ignorato.
- Il parser di `INDEX.md` riconosce solo blocchi che iniziano con `## [topic_id]` e che contengono una riga `File: \`path\``. Heading non conformi vengono saltati silenziosamente.
- L'index viene caricato una sola volta all'avvio del server. Se modifichi `INDEX.md` riavvia il server MCP.
