# Session Kickoff — come l'MCP interpreta il template

Il file `Bible/templates/session_kickoff.{md,jsonc}` è il prompt strutturato che l'utente fornisce all'inizio di ogni sessione print-prep. Questo doc spiega **come l'MCP lo interpreta**: campi vitali, default fallback, validation, e missing-field policy.

Il template ha 5 sezioni: `object`, `target`, `printer`, `policies`, `output`, più note libere.

## Campi vitali (blocca-pipeline se mancanti)

L'MCP **chiede all'utente** se uno di questi tre non è inferibile dal context:

| Campo | Perché vitale | Comportamento se mancante |
|---|---|---|
| `object.name` | Senza, MCP non sa quale mesh trattare | Se `auto`: scan scene, se >1 MESH ask user; se 1 solo → use it. Se mancante esplicito → ask immediatamente |
| `target.use_case` | Determina decision tree default | Ask con menu: display/mech/snap_fit/container/test/tool_print |
| `target.dimension` | Mesh AI è ~1.0 BU = 1m, deve sapere target reale | Ask `axis + mm`. Solo se `axis=preserve` skip |

Tutti gli altri campi hanno default. Se vuoti, MCP procede.

## Parsing dei due formati

Il template esiste in markdown e JSONC. Il parsing MCP è permissivo:

### Markdown (`session_kickoff.md`)

L'utente può lasciare:
- `campo: <placeholder>` non sostituito → MCP tratta come mancante.
- `campo: <>` o `campo:` vuoto → mancante (usa default).
- Commenti `#` (incluso il template stesso) → ignorati.
- Valore con quote (`"valore"`) o senza → entrambi accettati.

Parsing minimalista:
```python
def parse_md_kickoff(text):
    """Parse session_kickoff.md, returns dict of section.field -> value."""
    import re
    out = {}
    section = None
    section_re = re.compile(r"^##\s+([A-Z][A-Z _-]*)")
    field_re = re.compile(r"^([a-z_]+):\s*(.*)$")
    for line in text.splitlines():
        line = line.rstrip()
        if line.startswith("#"):
            continue
        if not line.strip():
            continue
        m_sec = section_re.match(line)
        if m_sec:
            section = m_sec.group(1).strip().lower().split()[0]
            continue
        m_f = field_re.match(line)
        if m_f and section:
            key = f"{section}.{m_f.group(1)}"
            val = m_f.group(2).strip().strip('"\'')
            # Treat unmodified placeholder as empty
            if val.startswith("<") and val.endswith(">"):
                val = ""
            out[key] = val
    return out
```

### JSONC (`session_kickoff.jsonc`)

Stripping dei commenti `//` prima di `json.loads`:
```python
import re, json
def parse_jsonc(text):
    stripped = re.sub(r"//[^\n]*", "", text)
    return json.loads(stripped)
```

Per campi con placeholder non sostituito (es. `"<auto>"`): MCP riconosce il pattern `<...>` come "non compilato" e tratta come empty.

## Tabella semantica per campo

### object.*

| Campo | Default | Comportamento |
|---|---|---|
| `name` | `"auto"` | Se `"auto"` o vuoto: `get_scene_info()`, identifica unico MESH non-default. Se >1 MESH: ask user con menu. |
| `source_generator` | `"unknown"` | Se compilato: applica pre-flight da `ai_generators_field_kit` (axis flip, scale, playbook iniziale). Se `"unknown"`: parte da analysis grezza. |
| `source_file` | `""` | Solo logging. Stampato in summary report finale. |

### target.*

| Campo | Default | Comportamento |
|---|---|---|
| `use_case` | **VITALE** | Mappa a tabella default → `use_case_taxonomy`. |
| `dimension` | **VITALE** (eccetto `axis=preserve`) | `axis ∈ {height, width, diagonal, longest, preserve}`. Scala uniforme post-import. |
| `orientation` | `"auto"` | `auto`: lancia `find_best_orientation` (vedi orientation_strategy). Valori espliciti = skip search. |
| `show_side_or_load` | `""` | Stringa libera. Se contiene `"load:"`, l'asse di load influenza orient policy (vedi P1 anisotropia). |

### printer.*

| Campo | Default | Comportamento |
|---|---|---|
| `model` | `"bambu_a1"` | Determina build volume (256³), default profile, kinematics (bedslinger I_eff). |
| `filament` | `"pla_basic"` | Mappa a tabella MVS (vedi `mvs_filament_table` nel Bambu sub-KB). |
| `nozzle` | `"0.4mm"` | Cambia line_width (0.21/0.42/0.63/0.84mm), min wall, MVS ceiling. |
| `layer_height` | `"auto"` | `auto`: derivato da use_case + smallest_feature. Vedi tabella sotto. |
| `build_plate` | `"textured_pei"` | Influenza adhesion default settings (brim, bed temp). |
| `time_budget` | `"medio"` | Bias `rapido` → layer alto + speed alto; `qualita` → layer fine + outer wall slow. |

### policies.*

| Campo | Default | Comportamento |
|---|---|---|
| `sculpt_manual_allowed` | `"no"` | Se `no`: situazioni che richiederebbero Sculpt fanno fallback a Voxel Remesh / accept feature loss. Se `si`: MCP esce dal loop e chiede intervento. |
| `poly_count_target` | `"auto"` | `auto`: derivato da use_case (display=200k, mech=100k, test=50k). |
| `thin_walls_policy` | `"ask"` | Trigger su `wall_thickness_p10_mm < 0.8`. Vedi wall_thickness_actionable. |
| `oversize_policy` | `"ask"` | Trigger su `max(dimensions_mm) > 256`. Vedi bisect_splitting. |
| `destructive_ops_policy` | `"ask"` | Trigger su Boolean su original, modifier_apply, delete object. |

### output.*

| Campo | Default | Comportamento |
|---|---|---|
| `path` | `~/print_ready/<object_name>.<format>` | `<object_name>` sostituito a runtime. `~` expanded. |
| `format` | `"stl"` | `stl`: usa `bpy.ops.wm.stl_export`. `3mf`: usa `bpy.ops.export_mesh.threemf`. `both`: entrambi. |
| `pre_export_qa` | `"si"` | Se `si`: ultimo `analyze_mesh_for_print` + iso screenshot pre-export (recipe R5 in camera_verification). |

## Default `layer_height: auto` — come l'MCP decide

```
use_case      | time_budget   | layer_height auto-pick
─────────────────────────────────────────────────────────
display       | rapido        | 0.20mm
display       | medio         | 0.16mm
display       | qualita       | 0.12mm
mech          | rapido        | 0.28mm
mech          | medio         | 0.20mm
mech          | qualita       | 0.16mm
snap_fit      | *             | 0.16mm   (precisione dim più importante)
container     | rapido        | 0.28mm
container     | medio         | 0.20mm
container     | qualita       | 0.16mm
test          | *             | 0.28mm   (sempre draft)
tool_print    | medio         | 0.20mm
tool_print    | qualita       | 0.16mm
```

Override automatico se `wall_thickness_p10_mm < 0.45mm` AND `use_case = display`: forza `0.12mm` per preservare il detail residuo.

## Output — summary report al termine

A fine sessione, MCP risponde con un report strutturato:

```yaml
session_summary:
  status: completed | failed | partial_user_input_required
  duration_s: 142
  initial_analysis:                  # snapshot pre-cleanup
    face_count: 320000
    non_manifold_edges: 234
    boundary_loops: 7
    disconnected_shells: 3
    dimensions_mm: [1003.2, 802.1, 1501.4]
    ready_to_slice: false
  pipeline_executed:
    - rule_id: R009                 # con rationale incluso
      action: "rescale to height=80mm"
    - rule_id: R001
      playbook: post_decimate_cleanup
    - rule_id: R003
      action: "remove_small_objects, kept main shell"
    - rule_id: R004
      playbook: repair_basic
    - rule_id: R006
      playbook: decimate_to_target
      params: {target_faces: 150000}
  user_interventions:                # ask_user momenti
    - timestamp: T+45s
      question: "Tre shells separate. Tutte stampabili: union?"
      answer: "union"
  final_analysis:                    # snapshot pre-export
    face_count: 148332
    non_manifold_edges: 0
    boundary_loops: 0
    disconnected_shells: 1
    dimensions_mm: [53.4, 42.8, 80.0]
    ready_to_slice: true
    wall_thickness_p10_mm: 1.2
    inverted_face_pct: 0.0
  output_files:
    - path: ~/print_ready/dragon.stl
      size_bytes: 2843921
      triangle_count: 148332
  estimates:                         # da metric estesi
    pla_mass_g: 18.4                 # surface_area_mm2 * 0.0008 * 1.24
    print_time_h: 2.3                # da face_count + layer_height
  slicer_profile_reco:
    profile: "estetico"
    layer_height: 0.16
    walls: 4
    infill: 15
    support: tree_organic
    seam: scarf
  warnings:
    - "wall_thickness_under_min_pct=2.1% (3% del modello marginalmente sotto soglia, accettato)"
  fields_used:                       # tracking compilazione utente
    explicit:
      - target.use_case
      - target.dimension.mm
      - output.path
    defaulted:
      - printer.filament -> pla_basic
      - policies.poly_count_target -> auto -> 150000
```

Questo serve sia all'utente (sa cosa è successo) sia all'apprendimento iterativo (lessons learned per il prossimo print).

## Missing-field policy — esempi di rounds

### Caso A — kickoff minimale ma vitale completo

Utente compila solo:
```yaml
object.name: dragon
target.use_case: display
target.dimension: { axis: height, mm: 80 }
```

MCP procede senza chiedere nulla, usa tutti i default. **0 stop**.

### Caso B — kickoff con use_case mancante

MCP rileva `target.use_case == ""`. Risponde:

> Per scegliere defaults sensati ho bisogno del use_case. Tra:
> 1. display (figurina, busto, modello decorativo)
> 2. mech (parte meccanica, load-bearing)
> 3. snap_fit (incastri con tolerance critica)
> 4. container (vasi, scatole)
> 5. test (calibrazione, prototipo rapido)
> 6. tool_print (utensile/jig funzionale)
> Quale?

L'utente risponde "1" o "display". MCP procede. **1 stop**.

### Caso C — kickoff vuoto

Tutti i campi vuoti. MCP non parte alla cieca — chiede in **un singolo round** i 3 vitali:

> Prima di iniziare ho bisogno di tre info:
> 1. Quale object trattare (in scena vedo: `dragon`, `Camera`, `Light`) — confermo `dragon`?
> 2. Use case (display/mech/snap_fit/container/test/tool_print)?
> 3. Dimensione target (es. "height: 80mm")?

Risposta utente in 1 messaggio. MCP procede. **1 stop**.

## Cross-reference

- `Bible/templates/README.md` — guida d'uso pratica per l'utente
- `Bible/templates/session_kickoff.md` — il file da copiare
- `Bible/templates/session_kickoff.jsonc` — formato JSON equivalent
- [use_case_taxonomy] — tabella completa use_case → defaults
- [mcp_blind_operating_protocol] §"Session kickoff protocol" — come MCP parsa il template come primo move T+0
- [orientation_strategy] — semantica di `orientation: auto` vs valori espliciti
- [mvs_filament_table] (Bambu) — mapping `filament` field
- [wall_thickness_actionable] — semantica `thin_walls_policy`
- [bisect_splitting] — semantica `oversize_policy`
