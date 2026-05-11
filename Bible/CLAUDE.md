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
  KB_SERVER.md          # come usare i tool MCP blender-kb (kb_search, kb_get_topic, ecc.)
  .claudeignore
  .mcp.json             # registra blender (Blender control) + blender-kb (questa KB)

  Blender for 3d print documentation/
    INDEX.md
    FIELD_NOTES.md
    docs/

  Bambu Wiki documentation/
    INDEX.md
    docs/
```

## Accesso alla KB via MCP (blender-kb)

Oltre alla lettura via filesystem, esiste un secondo MCP server `blender-kb`
(setup in `KB_SERVER.md`) che espone la KB come tool:

- `kb_list_topics()` per scoprire i `[topic_id]` disponibili
- `kb_get_topic(topic_id)` per caricare on-demand il doc associato
- `kb_search(query)` per grep substring sui doc indicizzati
- `kb_read(relative_path)` per file non indicizzati (FIELD_NOTES, SYSTEM_PROMPT, Printer Infos/*)
- prompt `kb_bootstrap` che restituisce CLAUDE.md + SYSTEM_PROMPT.md + lista topic_id

Preferisci questi tool quando il client MCP è configurato: caricano solo il doc rilevante invece dell'intero INDEX.

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

Per un nuovo task su mesh:
1. `Blender for 3d print documentation/INDEX.md`
2. `Bambu Wiki documentation/INDEX.md` se servono dettagli stampante/slicer/materiali
3. I documenti specifici richiamati dagli index
4. `FIELD_NOTES.md` se il task tocca aree già esplorate o problematiche

Per onboarding o manutenzione del progetto:
1. `SYSTEM_PROMPT.md`
2. `CLAUDE.md`
3. `Blender for 3d print documentation/INDEX.md`
4. `Bambu Wiki documentation/INDEX.md`

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
