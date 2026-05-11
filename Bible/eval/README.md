# Evaluation Harness — STL Print-Prep

Scopo: misurare se modifiche alla KB (regole di routing, playbook, topic) migliorano
o peggiorano il workflow su STL reali. Senza un eval set, ogni modifica è speranza,
non misura.

## Cosa serve da te (utente)

Per ogni caso reale che incontri durante l'uso (vedi prossima sezione sul logging):

1. **STL di input**: copia il file in `eval/cases/<short_name>/input.stl` e
   committalo (o tieni una copia locale e referenzialo via path assoluto se
   è privato/grande).
2. **Una entry in `eval/eval_cases.yaml`** con:
   - `name`: identificatore breve (`tripos_dragon_v1`, `meshy_chess_pawn`, ...)
   - `description`: come è stato generato il modello (tool AI, prompt, ecc.)
   - `expected_initial_analysis`: l'output di `analyze_mesh_for_print` prima del
     cleanup. **Lo prendi semplicemente eseguendolo la prima volta.**
   - `expected_pipeline`: la sequenza di azioni che hai effettivamente eseguito
     (rule_id o playbook_id), nell'ordine.
   - `expected_final_analysis`: l'output dopo il cleanup, copiato dal log.

Non serve scrivere a mano: il workflow normale produce tutti questi dati;
basta copincollare i JSON in `eval_cases.yaml`.

## Cosa non c'è ancora (e perché)

**Un runner automatico.** Il runner ideale farebbe:
1. Avvia Blender headless con l'addon `blender-mcp` caricato.
2. Per ogni caso: import_stl → analyze → kb_route → segui next_action →
   re-analyze → confronta con `expected_final_analysis`.
3. Riporta pass/fail per caso e diff per regressioni.

Non è scritto perché richiede:
- Blender installato e in PATH (`blender --background --python ...`).
- L'addon registrato nella build di Blender che usi (path-dipendente).
- STL reali tuoi (la KB non può inventarli).

Lo scaffolding qui è il file YAML + un dry-run mode (`eval_dry.py`) che
verifica che `kb_route` produca il `next_action` atteso per ogni
`expected_initial_analysis`, senza toccare Blender. Quello che puoi misurare
**oggi**, senza Blender vivo, è la "decisione" della routing engine.

## Come usarlo (oggi, dry-run)

```bash
cd Bible
BLENDER_KB_PATH=$PWD python scripts/eval_dry.py
```

Il dry-run esegue per ogni caso:
- `kb_route(expected_initial_analysis)`
- Confronta `next_action.tool` con `expected_pipeline[0]` (primo step atteso)
- Riporta diff

Quando avrai Blender + STL, il prossimo step è scrivere `scripts/eval_full.py`
che lancia il runner completo.

## Struttura file

```
eval/
  README.md             # questo file
  eval_cases.yaml       # casi di test (vuoto / con 2 esempi sintetici)
  cases/                # opzionale: STL di input (puoi tenerli fuori repo)
    <short_name>/
      input.stl
      notes.md          # cosa hai imparato sul caso
```
