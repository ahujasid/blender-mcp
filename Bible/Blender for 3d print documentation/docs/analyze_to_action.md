# Analyze → Action Decision Tree

Mappa diretta dall'output JSON di `analyze_mesh_for_print` (tool MCP esposto da
`blender-mcp`) alle azioni di cleanup da eseguire. È la "central nervous system"
della pipeline: invece di leggere la KB e improvvisare, l'assistente esegue
`kb_route(analysis_json)` e ottiene la sequenza ordinata di topic + playbook
da applicare.

Le regole sono codificate machine-readable in `routing_rules.yaml`. Questo
documento è il corrispettivo umano: spiega ogni regola, perché esiste, e cosa
aspettarsi dopo l'azione.

## Chiavi dell'analysis JSON

Riferimento delle chiavi prodotte da `analyze_mesh_for_print`:

| Chiave | Tipo | Significato |
| --- | --- | --- |
| `vertex_count` / `edge_count` / `face_count` | int | Conteggi base della mesh |
| `dimensions_mm` | `[x, y, z]` | Bounding box in millimetri |
| `non_manifold_edges` | int | Edge non-manifold (mesh non chiusa o T-junction) |
| `boundary_edges` | int | Edge sul bordo (mesh aperta) |
| `boundary_loops` | int | Numero di "buchi" topologici |
| `disconnected_shells` | int | Numero di isole separate |
| `degenerate_faces` | int | Facce con area sotto soglia (~1e-12 m²) |
| `watertight` | bool | True sse `non_manifold_edges == 0` |
| `normals` | `consistent` \| `all_inverted` \| `unknown_open_mesh` | Stato normali |
| `signed_volume_mm3` | float \| null | Volume con segno (null se aperta) |
| `ready_to_slice` | bool | watertight ∧ degenerate==0 ∧ shells==1 ∧ normals==consistent |

## Regole

Ordine: priorità decrescente. La routing engine restituisce tutte le regole che
fanno match, in ordine. L'assistente le applica in sequenza, ri-eseguendo
`analyze_mesh_for_print` tra ogni step per verificare il delta.

### R001 — `degenerate_faces > 0` → `mesh_repair#dissolve_degenerate`
**Priority**: 110
**Topic**: `mesh_repair` (sezione: dissolve_degenerate / remove_doubles)
**Playbook**: `repair_basic`
**Perché prima di tutto**: facce degeneri sabotano Boolean, Remesh, e il
calcolo del volume signed. Vanno rimosse all'inizio.
**Atteso dopo**: `degenerate_faces == 0`. Se `non_manifold_edges` aumenta è
normale (dissolvere facce zero-area può lasciare edge esposti che vanno
chiusi dalla regola successiva).

### R002 — `normals == all_inverted` → `mesh_repair#recalc_normals`
**Priority**: 100
**Topic**: `mesh_repair` (normals_make_consistent)
**Playbook**: `recalc_normals`
**Perché**: la mesh è chiusa ma stampabile "al rovescio". Il fix è 1 chiamata
e va fatto prima di qualsiasi misurazione di volume/spessore.
**Atteso dopo**: `normals == consistent`, `signed_volume_mm3 > 0`.

### R003 — `disconnected_shells > 1` → `multi_object_management#split_then_decide`
**Priority**: 95
**Topic**: `multi_object_management`
**Playbook**: nessuno (richiede decisione)
**Perché**: la mesh contiene più isole. Tre casi:
1. **Tutte le shell tranne una sono < 1% del volume totale**: artefatti
   floating, rimuovere con `remove_small_objects(threshold_mm=1.0)`.
2. **Shell multiple di dimensione comparabile**: due o più parti fisicamente
   distinte. Possibili azioni:
   a. Unirle con `boolean_union_all` (se devono diventare un unico solido).
   b. Esportarle come STL separati (se vanno stampate come pezzi distinti).
   c. Lasciarle al slicer (Bambu Studio gestisce multi-object).
**Decisione**: chiedere all'utente quando il rapporto
`max_shell_volume / total_volume < 0.95`. Sotto soglia, applicare opzione 1
automaticamente.

### R004 — `non_manifold_edges > 0 AND boundary_loops > 0` → `mesh_repair#fill_holes`
**Priority**: 90
**Topic**: `mesh_repair` (fill_holes, remove_doubles)
**Playbook**: `repair_basic`
**Perché**: mesh con buchi topologici. Il fill_holes chiude loop fino a
`sides=N` (default 8). Per loop più grandi serve intervento manuale o
Voxel Remesh fallback (R007).
**Atteso dopo**: `boundary_loops == 0`, `non_manifold_edges` ridotto.

### R005 — `non_manifold_edges > 0 AND boundary_loops == 0` → `mesh_repair#clean_non_manifold`
**Priority**: 85
**Topic**: `mesh_repair` (print3d_clean_non_manifold via 3D Print Toolbox)
**Playbook**: `repair_aggressive`
**Perché**: non-manifold senza buchi indica T-junction, vertex fan, o edge
condivisi da 3+ facce. Il `print3d_clean_non_manifold` opera euristicamente
ed è l'opzione più sicura prima di scalare.
**Atteso dopo**: `non_manifold_edges` significativamente ridotto.

### R006 — `face_count > 500_000` → `decimation_remesh#decimate_collapse`
**Priority**: 70
**Topic**: `decimation_remesh`
**Playbook**: `decimate_to_target`
**Perché**: oltre 500k facce il slicing rallenta sensibilmente senza
beneficio visibile su FDM 0.4mm. Target tipico: 100-200k facce.
**Atteso dopo**: `face_count` nel range desiderato, geometria preservata.
**Parametri**: `ratio` calcolato come `target_faces / face_count`.

### R007 — `non_manifold_edges > 50 AND ratio_non_manifold > 0.01` → `decimation_remesh#voxel_remesh_fallback`
**Priority**: 60
**Topic**: `decimation_remesh` (Voxel Remesh)
**Playbook**: `voxel_remesh_rescue` (TODO — non ancora scritto)
**Perché**: quando il repair classico non basta (>50 edge non-manifold dopo
R004/R005 e oltre 1% delle facce coinvolte), Voxel Remesh è l'opzione
"nucleare". Distrugge i dettagli fini ma garantisce manifold.
**Atteso dopo**: `non_manifold_edges == 0`, mesh ricostruita.
**Cautela**: irreversibile sulla geometria originale; duplicare prima.

### R008 — `max(dimensions_mm) > 256` → `bisect_splitting#split_for_bambu_a1`
**Priority**: 50
**Topic**: `bisect_splitting`
**Playbook**: nessuno (richiede parametri utente: asse di taglio, numero pezzi)
**Perché**: il volume di stampa Bambu A1 è 256³ mm. Oggetti più grandi
vanno divisi con `split_n_horizontal` o con registration pin per
riassemblaggio.
**Atteso dopo**: nessuna dimensione > 256mm su nessun pezzo.

### R009 — `max(dimensions_mm) < 1.0 OR min(dimensions_mm) > 1000` → `scale_detection#diagnose_and_rescale`
**Priority**: 95
**Topic**: `scale_detection`
**Playbook**: nessuno (richiede target_mm utente)
**Perché**: l'STL non porta unità; mesh sotto 1mm o sopra 1m hanno quasi
certamente scala sbagliata (AI normalizzata a unit cube, o tool in metri).
**Atteso dopo**: dimensioni nel range plausibile (10-300mm tipico).
**Decisione**: chiedere all'utente la dimensione target se non specificata.

### R999 — Nessuna regola match → ready
Se `ready_to_slice == True` e nessuna regola precedente match: la mesh è
pulita, suggerire `preprint_validation` per il gate finale + `export_stl`.

## Convenzione output di `kb_route`

```json
{
  "input_summary": { ... echo dell'analysis ricevuta ... },
  "matched_rules": [
    {
      "id": "R002",
      "priority": 100,
      "topic_id": "mesh_repair",
      "section": "recalc_normals",
      "playbook": "recalc_normals",
      "rationale": "...",
      "expected_after": {"normals": "consistent"},
      "needs_user_input": false
    },
    ...
  ],
  "next_action": {
    "tool": "kb_get_playbook" | "kb_get_topic" | "ask_user" | "ready",
    "args": { ... }
  }
}
```

`next_action` è la regola di priorità massima tra quelle matchate, esposta in
forma direttamente eseguibile per l'assistente.

## Estendere le regole

Aggiungere una regola in 3 step:
1. Definire la regola in `routing_rules.yaml` (vedi schema in alto al file).
2. Documentarla qui sotto la sezione "Regole" con codice `Rxxx`.
3. Se richiede un playbook nuovo, crearlo in `Bible/playbooks/<id>.json`.

`validate_kb.py` controlla che ogni `playbook:` referenziato in
`routing_rules.yaml` esista in `playbooks/`, e che ogni `topic_id:` esista
nella KB attiva.
