# MCP Blind Operating Protocol — come ragionare senza vedere

L'assistente MCP è **cieco**. Non vede la viewport. Non vede il modello che sta processando. Tutto quello che sa lo deduce da:

1. **Output JSON di `analyze_mesh_for_print`** — metriche strutturate sulla mesh.
2. **`object_print3d_utils.report._data`** — risultati dei check 3D Print Toolbox letti via `report.info()`.
3. **`get_viewport_screenshot`** — l'unica forma di "vista" effettiva. Costosa, va usata strategicamente.
4. **Python query dirette** (`bpy.data.objects[...]`, `bmesh` ispezione) — read-only inspection del data block.

Questo documento codifica il protocollo operativo da seguire perché il workflow funzioni nonostante la cecità.

## Principio fondamentale: trust metrics, not the viewport

**Regola**: ogni decisione operativa (orientation, choice di playbook, scelta di solver Boolean) deve essere supportata da una **metrica numerica**, non da un'assunzione visiva. Le metriche sono riproducibili; le assunzioni visive sono ciecate.

**Esempio applicato**:
- ❌ "La mesh sembra ok, procediamo all'export" — non hai visto niente.
- ✅ "`analyze_mesh_for_print` ritorna `ready_to_slice: true`, `wall_thickness_p10_mm: 1.2`, `aspect_ratio_p95: 3.8`, `inverted_face_pct: 0.0`. Tutti i criteri rispettati. Export."

## I tre sensi dell'MCP

### Senso 1 — `analyze_mesh_for_print` (JSON strutturato)

**Uso**: snapshot completo dello stato mesh in 1 chiamata. È il **default first move** quando vuoi sapere "cosa c'è davanti a me".

**Quando**:
- **Sempre** prima di decidere un'azione (input per `kb_route`).
- **Sempre** dopo un'azione mutativa (verifica delta).
- Per validazione finale prima di `export_stl`.

**Output proxies per visual checks** (vedi docstring del tool):

| Domanda visiva che non puoi fare | Proxy metrico |
|---|---|
| "Ci sono triangoli sliver?" | `aspect_ratio_p95 > 10` |
| "Le normali sono tutte verso fuori?" | `normals == "consistent"` AND `inverted_face_pct < 1` |
| "C'è abbastanza superficie a contatto col piatto?" | `bottom_contact_area_mm2 / (dim_x * dim_y) > 0.15` |
| "Il modello è massiccio o spiky?" | `convex_hull_volume_ratio > 0.7` = blob; `< 0.4` = spiky |
| "Quanto peserà in PLA?" | `surface_area_mm2 * 0.0008 * 1.24` ≈ grams di shell-only |
| "Si ribalta sul piatto?" | confronta `center_of_mass_mm[0:2]` con bbox della bottom_contact area |
| "Ci sono spigoli netti visibili?" | `dihedral_angle_p90_deg > 60` |
| "Quanto è ad alta risoluzione?" | `face_count` + `dimensions_mm` → density |

**Costo**: O(N) sulle facce, ~0.1-2s su mesh fino a 500k. Sampling 5000 face per metriche raycast (wall_thickness, inverted_face_pct, aspect_ratio).

### Senso 2 — 3D Print Toolbox `report._data`

**Uso**: drill-down su una categoria specifica di problema. È **selezionabile** (i risultati possono essere convertiti in selection EDIT mode via `print3d_select_report`).

**Quando**:
- Dopo `analyze_mesh_for_print` ha flaggato un problema specifico (es. `non_manifold_edges > 10`).
- Per ottenere **gli indici esatti** della geometria problematica (vs solo il count).
- Per categorie che `analyze_mesh_for_print` non copre (sharp edges, overhang count, distortion).

**Pattern canonico**:
```python
import bpy
# Setup
obj = bpy.data.objects['<name>']
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')

# Esegui check
bpy.ops.mesh.print3d_check_solid()

# Leggi risultati programmaticamente
from object_print3d_utils import report
results = report.info()
for label, (etype, indices) in results:
    print(f"{label}: {len(indices)} {etype}")
    # es: 'Non Manifold Edge: 12 EDGES'

# (Opzionale) seleziona per follow-up edit
bpy.ops.mesh.print3d_select_report(index=0)
```

Vedi [blender_3d_print_toolbox] per la lista completa dei check + Pattern idiomatici.

### Senso 3 — `get_viewport_screenshot` (l'occhio vero)

**Uso**: l'**unico** modo per verificare qualcosa che le metriche non catturano. Costoso in token. Usalo con parsimonia ma **non averne paura** quando serve.

**Quando giustifica il costo**:

| Situazione | Perché serve lo screenshot |
|---|---|
| Orientation choice complessa | Metric `bottom_contact_area_mm2` + `overhang count` ti dicono se è meccanicamente OK, lo screenshot ti dice se la silhouette visibile post-print sarà accettabile per l'utente |
| Post-Voxel Remesh su feature critiche | `analyze` ti dice manifold+watertight ma non se la feature ≤1mm è sopravvissuta |
| Post-Sculpt manuale (workflow ibrido) | Sculpt richiede iterazione visiva — pre-/post-screenshot per confermare effetto |
| Boolean DIFFERENCE complesso | Verifica che il foro/cut sia nella posizione attesa (non solo che il volume sia diminuito) |
| Support placement | Vedere dove tree branches finiscono, identificare gap non-supportati |
| "Sanity check" prima di un'azione irreversibile | Tipicamente prima di `export_stl` finale: 1 screenshot iso + 1 top |
| Conferma user request | Quando l'utente dice "sembra storto" o "il foro è troppo grande" → screenshot per confermare ipotesi |

**Quando NON serve lo screenshot** (cost > value):
- Verificare counts/metric numerici → usa `analyze_mesh_for_print`
- Verificare manifold/watertight → metric già lo dice
- Decisioni di routing automatico → `kb_route` non guarda lo screenshot, usa metriche
- Loop iterativo di tuning numerico (es. cercare il `voxel_size` giusto)

**Setup PRIMA dello screenshot**: la viewport non è configurata per QA di default. Vedi [camera_verification] per il "screenshot decision matrix" — quale view + overlay per quale situazione.

### Senso 4 — Python introspection diretta

Per cose che nessuno dei tre sensi sopra fornisce, usa `execute_blender_code` per fare query Python direttamente:

```python
# Esempi:
len(bpy.data.objects)  # quanti object nella scena
[o.name for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.data.objects['<name>'].matrix_world  # transform matrix
bpy.data.objects['<name>'].data.materials[:]  # material slots
bpy.context.scene.unit_settings.scale_length  # critical per global_scale
```

**Quando**: scene-level introspection, transform/material/state queries che non sono mesh-geometry.

## Pre-flight checklist (PRIMA di qualsiasi azione mutativa)

Senza vedere, devi assumere il MINIMO sullo stato. Verifica esplicitamente prima di agire:

```python
def pre_flight_check(object_name):
    """Verify assumptions BEFORE running any mutating op."""
    import bpy

    # 1. Object exists
    obj = bpy.data.objects.get(object_name)
    assert obj is not None, f"Object '{object_name}' not found in scene"

    # 2. Type is MESH (not curve / empty / armature)
    assert obj.type == 'MESH', f"'{object_name}' is type {obj.type}, expected MESH"

    # 3. Has geometry
    assert len(obj.data.vertices) > 0, f"'{object_name}' has no vertices"

    # 4. Is in OBJECT mode (most ops require this; EDIT mode ops will fail differently)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # 5. Active + selected (most ops use context.active_object)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # 6. Scene unit_settings — critical for scale-sensitive ops (Boolean, export)
    sl = bpy.context.scene.unit_settings.scale_length
    print(f"scale_length={sl} (1 BU = {sl}m = {sl * 1000}mm)")

    # 7. Modifier stack — apply or note pending modifiers
    if obj.modifiers:
        print(f"WARNING: '{object_name}' has {len(obj.modifiers)} unapplied modifiers")
        # Decide: apply now, or use evaluated mesh for downstream
```

Questo blocco DEVE essere il primo step di ogni playbook che muta la mesh. È documentato in [error_handling_mcp] §call_precheck.

## Post-flight verification (DOPO ogni azione mutativa)

L'azione è andata? Le metriche aggiornate lo dicono. Confronto sempre input vs output:

```python
import json

# 1. Salva stato pre-op
analysis_before = json.loads(analyze_mesh_for_print(object_name))

# 2. Esegui op (es. playbook step)
# ... execute_blender_code(...) ...

# 3. Ri-analizza
analysis_after = json.loads(analyze_mesh_for_print(object_name))

# 4. Verifica delta atteso (dal verification.expect del playbook)
delta_non_manifold = analysis_after['non_manifold_edges'] - analysis_before['non_manifold_edges']
delta_face_count = analysis_after['face_count'] - analysis_before['face_count']

print(f"Δ non_manifold_edges: {delta_non_manifold}")
print(f"Δ face_count: {delta_face_count}")

# 5. Se delta opposto all'atteso → l'op ha fallito silently. NON proseguire.
if delta_non_manifold > 0:
    print("WARN: op INTRODUCED new non-manifold edges. Investigate.")
```

Ogni playbook in `Bible/playbooks/` ha il proprio `verification.expect` — usa quello come truth.

## Decision matrix: quale senso usare quando

| Domanda dell'utente / step pipeline | Senso |
|---|---|
| "Cos'è questa mesh?" (post-import) | Senso 1 (`analyze_mesh_for_print`) |
| "Quali edge sono non-manifold?" | Senso 2 (`print3d_check_solid` + `report.info()` + `select_report`) |
| "Posso esportare?" | Senso 1 + check `ready_to_slice == true` |
| "Quale orientamento è meglio?" | Senso 1 (`bottom_contact_area_mm2`, `dimensions_mm[2]`, `convex_hull_volume_ratio`) + Senso 3 finale per silhouette visibile |
| "Il foro è nella posizione giusta?" | Senso 3 (screenshot top + side) |
| "L'operazione ha funzionato?" | Senso 1 confronto pre/post (mai Senso 3 per metriche, sempre) |
| "Quanto peserà?" | Senso 1 (`surface_area_mm2` per shell) + Python (volume per infill estimate) |
| "Si ribalta sul piatto?" | Senso 1 (`center_of_mass_mm[0:2]` vs bottom_contact bbox) |
| "Quanto sono fini i dettagli?" | Senso 1 (`wall_thickness_p10_mm`, `dihedral_angle_p90_deg`) |
| "La sculpt session ha cambiato la silhouette?" | Senso 3 (screenshot pre/post sculpt, è uno dei pochi casi in cui screenshot è obbligatorio) |
| "Qual è la versione di Blender?" | Senso 4 (`bpy.app.version`) |

## Error handling: cosa fare quando un senso "non risponde"

### `analyze_mesh_for_print` ritorna campi `null`

- `wall_thickness_*` null → mesh non watertight. Devi prima ripararla (R004/R005/R007), poi ri-analizzare.
- `inverted_face_pct` null → stessa causa.
- `convex_hull_volume_ratio` null → mesh non chiusa o convex hull failure. Probabilmente non-manifold severo.
- `bottom_contact_area_mm2` null → mesh vuota.

### `print3d_check_*` ritorna lista vuota in `report._data`

- Probabilmente non sei in EDIT mode al momento del check (alcuni check assumono il context).
- O hai chiamato `report.info()` prima di `bpy.context.update()` — re-call dopo l'op.

### `get_viewport_screenshot` produce immagine vuota / wrong angle

- Camera non posizionata. Vedi [camera_verification] §`setup_qa_view()`.
- Object non selected/active → `view_selected` non fa il frame corretto.
- Viewport in modalità wrong (Material Preview vs Solid). Forza Solid prima del cap.

## Il workflow standard end-to-end

Combinando i tre sensi:

```
1. import_stl(filepath)                                # Senso 4: introspection scene
2. analysis = analyze_mesh_for_print(name)             # Senso 1: snapshot iniziale
3. route = kb_route(analysis)                          # Decision basata su Senso 1
4. for step in route.matched_rules:
     if step.playbook:
       playbook = kb_get_playbook(step.playbook)
       execute_blender_code(rendered_steps)            # Pre-flight + step + post-flight
       new_analysis = analyze_mesh_for_print(name)     # Senso 1: verifica delta
       compare(new_analysis, step.expected_after)
     elif step.needs_user_input:
       ask_user(...)                                   # Esci dal protocollo automatico
5. # PRE-EXPORT VISUAL VERIFICATION (uno dei pochi casi obbligatori per Senso 3)
   get_viewport_screenshot(max_size=800)               # Senso 3: iso view + selection framing
6. preprint_validation()                               # Senso 1: gate finale
7. export_stl(filepath)                                # Output
```

I 6 punti sono il "happy path". Le deviazioni (failure mode di un playbook, ask_user, rule conflitto) sono codificate altrove.

## Session kickoff protocol — T+0 first moves

L'utente importa STL manualmente in Blender e poi apre il client MCP. Il primo messaggio della sessione è (idealmente) il **session kickoff template** compilato — vedi `Bible/templates/session_kickoff.{md,jsonc}` e [session_kickoff_template] per come parsarlo.

**Sequenza T+0 obbligatoria** (PRIMA di qualsiasi op mutativa):

### Step 1 — Parse del kickoff template

Se il messaggio dell'utente contiene un blocco riconoscibile come kickoff (markdown con `## OGGETTO` etc, o JSONC), parsalo. Estrai:
- 3 campi vitali (`object.name`, `target.use_case`, `target.dimension`)
- Tutti gli altri campi (con default fallback se vuoti)

Se NON c'è kickoff (utente ha scritto solo "pulisci questo modello"), non panicare: assumi tutti i default ma chiedi i 3 vitali al primo round.

### Step 2 — Scene discovery (sempre, anche con kickoff completo)

```python
import bpy
# Snapshot scene state — questo PRECEDE qualsiasi azione mutativa
get_scene_info()
# Output JSON: nomi tutti object, type, location.
# Filtra MESH non default:
mesh_objects = [o for o in bpy.context.scene.objects
                if o.type == 'MESH' and o.name not in ('Cube',)]  # default cube
```

Se `object.name == "auto"`:
- 1 solo MESH → usa quello.
- 0 MESH → blocca con error "Scena vuota o solo non-mesh".
- >1 MESH → ask user "Quale di: [name_1, name_2, name_3]?"

### Step 3 — Sanity check `unit_settings.scale_length` (CRITICO)

Tutta la pipeline cambia comportamento in base a questo. **Verifica esplicitamente prima di toccare la mesh**.

```python
sl = bpy.context.scene.unit_settings.scale_length
print(f"scale_length={sl} (1 BU = {sl}m = {sl * 1000}mm)")
# Default Blender = 1.0 (1 BU = 1m)
# Profilo "Millimeters" preset = 0.001 (1 BU = 1mm)
```

Implicazioni:
- `scale_length=1.0` (1 BU = 1m): un cubo Blender 1.0 = 1000mm. AI mesh importate sono ~1 BU = 1m. Devi rescale.
- `scale_length=0.001` (1 BU = 1mm): un cubo Blender 1.0 = 1mm. AI mesh importate sono ~1 BU = 1mm. Diverso threshold per `remove_doubles`, `merge_distance`, eccc.

Tutti i playbook esistenti gestiscono entrambi (vedono `unit_settings.scale_length` runtime). MA: **logga sempre** lo state al T+0 per future debug. Se l'utente lamenta "il modello è 1000× più piccolo del previsto", primo sospetto è scale_length mismatch.

### Step 4 — Pre-flight check sull'object identificato

Esegui il [Pre-flight checklist](#pre-flight-checklist-prima-di-qualsiasi-azione-mutativa) sopra.

### Step 5 — Initial analysis + routing

```python
analysis = analyze_mesh_for_print(object_name)
route = kb_route(analysis)
```

Confronta con il kickoff:
- Se `target.use_case` impone vincoli (es. snap_fit → preserve poly count), aggiungi quei vincoli alla decision tree.
- Se `target.dimension` richiede scaling pre-analysis (R009/R009b match), applica scaling PRIMA di rifare analyze.

### Step 6 — Ask user round (solo se necessario)

Se mancano campi vitali O routing rules hanno `needs_user_input=True`:
- **Raggruppa tutte le domande in UN messaggio**. Se l'utente deve rispondere 3 volte, è un fail UX.
- Format chiaro con numeri.

### Step 7 — Begin pipeline esecuzione

Vai al "workflow standard end-to-end" sopra.

### Esempio sessione completa

User: `[paste session_kickoff.md compilato per dragon, use_case display, height 80mm]`

MCP T+0:
1. Parse template → `object.name=dragon`, `use_case=display`, `dimension.axis=height, mm=80`.
2. `get_scene_info()` → `dragon` MESH confermato.
3. `scale_length=1.0` (default Blender). Log.
4. Pre-flight su `dragon`: passes.
5. `analyze_mesh_for_print("dragon")` → `dimensions_mm=[1003, 802, 1501]`, `non_manifold=234`, ecc.
6. `kb_route(analysis)` → matched R009 (dim suspect), R001, R004, R003.
7. R009 needs_user_input ma `dimension` è già nel kickoff → skip ask, applica rescale a height=80mm.
8. Re-analyze: `dimensions_mm=[53, 43, 80]`. Run rest of route.
9. Execute R001 → repair_basic playbook → verify delta.
10. Execute R004 → repair_basic → verify delta.
11. Execute R003 → "3 shells, max=99% of total volume → auto remove_small_objects" (no ask perché kickoff non specifica `policies.disconnected_shells`, default = ratio rule).
12. Continue fino a `ready_to_slice=true`.
13. Pre-export R5 screenshot (`pre_export_qa: si` dal kickoff).
14. `export_stl("~/print_ready/dragon.stl")`.
15. Output summary report (vedi [session_kickoff_template] §Output).

**0 ask_user round** se il kickoff è compilato bene. Tipicamente 1 round se l'utente lascia un campo vitale vuoto o se le shells multiple richiedono input.

## Cross-reference

- [analyze_to_action] — decision tree completo da analysis output
- [camera_verification] — setup viewport per screenshot mirati
- [blender_3d_print_toolbox] — reference completa di Senso 2
- [error_handling_mcp] — `call_precheck()`, retry logic, logging strutturato
- [mcp_tools] — regole operative MCP (no undo, duplicate-before-operate, ecc.)
- [problem_to_tool_map] §Failure modes — quick reference silent failure detection

## TL;DR

1. **Sei cieco**. Le metriche sono il tuo occhio. Usa `analyze_mesh_for_print` come default first move.
2. **Trust ma verify**: ogni op ha un expected delta. Confronta pre/post.
3. **Screenshot solo quando serve** (silhouette visibile, posizione cut, post-sculpt, pre-export final). MAI per metriche.
4. **Pre-flight check** sempre prima di mutare.
5. **Se un campo è null, sai cosa significa** (mesh non watertight → ripara prima). Non assumere.
