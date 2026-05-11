# CLAUDE.md — Repository Operating Guide
> Purpose: explain the repository layout, key documents, and reading order.
> Use it when: files move, new docs are added, or Claude needs repo-specific navigation context.

Questo file descrive **come è organizzato il repository** e **quali file leggere**. Le regole di comportamento dell'assistente stanno in `SYSTEM_PROMPT.md`.

## Contesto progetto
- Dominio: preparazione mesh 3D per stampa FDM su **Bambu A1**
- Tool principale: **Blender Python API via MCP** (`blender-mcp v1.5.5`)
- Flusso tipico: import mesh → analisi → repair/ottimizzazione → validazione → export per Bambu Studio

## Dove si trova la documentazione

```text
./
  CLAUDE.md
  SYSTEM_PROMPT.md
  KB_SERVER.md          # guida ai tool MCP blender-kb (kb_route, kb_get_topic, ecc.)
  .claudeignore
  .mcp.json             # registra blender (Blender control) + blender-kb (questa KB)

  playbooks/            # JSON eseguibili (repair_basic, recalc_normals, ...)
    README.md
    repair_basic.json
    repair_aggressive.json
    recalc_normals.json
    decimate_to_target.json

  eval/                 # eval harness per misurare l'effetto di modifiche KB
    README.md
    eval_cases.yaml

  scripts/              # tooling sulla KB (validate_kb.py, eval_dry.py)

  Blender for 3d print documentation/
    INDEX.md            # umano: titolo + "Quando usarlo" + File:
    INDEX.yaml          # macchina: band + solves_symptoms + related
    FIELD_NOTES.md
    routing_rules.yaml  # regole di kb_route (analyze_mesh_for_print → topic)
    docs/
    _archive/           # topic fuori scope (modellazione from-scratch, ecc.)

  Bambu Wiki documentation/
    INDEX.md
    INDEX.yaml
    docs/
    Printer Infos/
```

## Accesso alla KB via MCP (blender-kb)

Oltre alla lettura via filesystem, il server `blender-kb` espone la KB come
tool (setup in `KB_SERVER.md`):

| Tool | Quando usarlo |
| --- | --- |
| `kb_route(analysis_json)` | **PRIMO step** dopo `analyze_mesh_for_print`. Restituisce la regola top-priority + il `next_action` direttamente eseguibile (playbook, topic, o ask_user). |
| `kb_list_topics(kb_name?, band?, solves_symptom?)` | Scopri topic; filtra per band ("A"=core, "B"=adiacente) o per sintomo (es. "non_manifold_edges"). |
| `kb_get_topic(topic_id)` | Markdown completo di un topic. Usalo quando `kb_route` ti indirizza qui. |
| `kb_search(query)` | Grep substring sui doc. Per ricerca strutturata preferisci `kb_list_topics(solves_symptom=...)`. |
| `kb_read(relative_path)` | File non indicizzati: `FIELD_NOTES.md`, `SYSTEM_PROMPT.md`, `Printer Infos/*.md`. |
| `kb_list_playbooks()` / `kb_get_playbook(id)` | Sequenze deterministiche di step (repair_basic, recalc_normals, decimate_to_target, repair_aggressive). L'esecuzione spetta a `blender-mcp` via `execute_blender_code`. |
| prompt `kb_bootstrap` | CLAUDE.md + SYSTEM_PROMPT.md + tabella topic_id, da invocare a inizio sessione. |

**Pipeline tipica**:
1. `import_stl` → 2. `analyze_mesh_for_print` → 3. `kb_route(analysis_json)` →
4. Segui `next_action.tool`: di solito `kb_get_playbook(playbook_id)`, poi
   esegui gli step via `execute_blender_code`, poi 5. ri-`analyze_mesh_for_print`
   per verificare il delta atteso.

## Come orientarsi
- `Blender for 3d print documentation/INDEX.md`
  Indice principale per workflow Blender, repair mesh, scripting, export, validazione.
- `Bambu Wiki documentation/INDEX.md`
  Indice per slicer, profili Bambu Studio, materiali, tolleranze e vincoli macchina.
- `Blender for 3d print documentation/FIELD_NOTES.md`
  Registro delle scoperte pratiche emerse durante test reali.
- `SYSTEM_PROMPT.md`
  Regole di comportamento, safety e metodo di lavoro per Claude.
- `CLAUDE.md`
  Mappa operativa del progetto e ordine di lettura.

## Sequenza di lettura consigliata

Per un task di cleanup STL (workflow principale):
1. `import_stl(...)` → `analyze_mesh_for_print(...)` via `blender-mcp`
2. `kb_route(analysis_json)` via `blender-kb` per ottenere la prossima azione
3. Segui `next_action`: di solito un `kb_get_playbook(id)`
4. Re-`analyze_mesh_for_print` e confronta con `verification.expect` del playbook
5. Itera o concludi con `preprint_validation` + `export_stl`

Per un task fuori dalla pipeline standard (capire un concetto, debug):
1. `Blender for 3d print documentation/INDEX.md`
2. `Bambu Wiki documentation/INDEX.md` se serve hardware/slicer/materiali
3. I documenti specifici richiamati dagli index
4. `FIELD_NOTES.md` se il task tocca aree già esplorate o problematiche

Per onboarding o manutenzione del progetto:
1. `SYSTEM_PROMPT.md`
2. `CLAUDE.md`
3. `KB_SERVER.md` (tool MCP + workflow)
4. `Blender for 3d print documentation/docs/analyze_to_action.md` (decision tree)

## Convenzioni utili
- I percorsi nei prompt sono relativi alla root del progetto Claude. Se il progetto aperto è `Bible/`, non anteporre `Bible/`.
- Il KB va caricato in modo selettivo: prima gli index, poi solo i doc rilevanti.
- `.claudeignore` nasconde a Claude materiale grezzo e artefatti di build non utili a runtime.
- `Scraping/` e `Research materials/` esistono come sorgenti, ma non fanno parte del contesto operativo normale.

## Quando aggiornare cosa
- Aggiorna `FIELD_NOTES.md` quando emerge un comportamento pratico nuovo o inatteso.
- Aggiorna i doc in `docs/` quando una conoscenza diventa stabile e riusabile.
- Aggiorna i documenti di workflow del repository quando cambia il bootstrap o il processo operativo umano.
- Aggiorna `SYSTEM_PROMPT.md` solo se cambiano regole, priorità o comportamento desiderato dell'assistente.
