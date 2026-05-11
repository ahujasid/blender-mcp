# Blender 4.5 → 5.1 — Migrazione API e breaking changes

Fonte: ricerca tecnica "Analisi Tecnica dell'Evoluzione dell'Architettura Blender 4.5 → 5.1".
Uso: scrivere script MCP che sopravvivano alla transizione 4.x → 5.x, evitare chiamate deprecate, sfruttare le API native C++20.

Blender 5.0–5.1 non è un aggiornamento incrementale: molte funzioni critiche di I/O e modellazione sono state migrate da add-on Python a operatori nativi C++20. L'effetto pratico per lo scripting è eliminazione dell'"API drift" tra UI e API, prestazioni significative, ma rottura di pattern basati sui vecchi namespace.

---

## 1. Fondamenta: C++20, hardware e performance

### Cosa è cambiato nel core

- **C++20 obbligatorio:** riscritture profonde di renderer e gestione memoria
- **Rimosso supporto:** Intel Mac, architetture Big Endian → solo Apple Silicon + x86_64
- **Volumetrici:** nuovo "unbiased null-scattering", elimina `step_size` manuale e artefatti di sovrapposizione
- **Data-block name:** esteso a 255 byte (era 63)
- **Compressione .blend:** abilitata di default

### Tabella performance 5.1

| Area | Incremento | Note |
|---|---|---|
| Rendering GPU | +10% | HIP RT default per AMD |
| CPU Windows | +20% | SIMD C++20 |
| Undo mesh edit | +30% | Riscrittura statesystem |
| Compositor (Glare/Blur) | 2× | Hardware-accelerated |
| Geometria | +30% | Buffer dati più grandi |

Implicazione MCP: script che ricaricavano `depsgraph` per workaround di performance possono essere semplificati.

---

## 2. Eliminazione API drift: operatori nativi

### STL — la transizione più importante

| Versione | API | Namespace | Tipo |
|---|---|---|---|
| ≤ 4.1 | `bpy.ops.import_mesh.stl(...)` | Python add-on `io_mesh_stl` | Deprecato |
| 4.2+ (LTS) | `bpy.ops.wm.stl_import(...)` | Native C++ operator | **Preferito** |
| 5.1 | `bpy.ops.wm.stl_import(...)` | Native C++20 | Standard |

**Numeri:** import nativo ≈ 11.92 ms per file medio (vs 80–120 ms via add-on Python).

**Export equivalente:** `bpy.ops.wm.stl_export(...)` (già coperto in `import_export.md`).

**Bug noti del vecchio add-on risolti nel nativo:**
- `TypeError` su `files` collection con tipi RNA complessi
- Corruption su binary STL con endianness non standard
- Crash su mesh non-manifold durante import

**Regola MCP:** sempre `bpy.ops.wm.stl_import` / `bpy.ops.wm.stl_export`. Mai `bpy.ops.import_mesh.stl`.

### SVG — workflow "fills" GP3

`bpy.ops.import_curve.svg` ancora riferibile ma logica migrata. Il nuovo sistema:
- Preserva la view box originale → proporzioni matematicamente fedeli
- Genera `fills` + `strokes` nativi (non poligoni sovrapposti)
- Interfaccia con Grease Pencil 3.0 per supporto "buchi" reali

### 3MF — estensione ibrida

Diversamente da STL/OBJ, 3MF **non è hard-coded** nel binario. È una "Core Extension" (mantenuta da Blender Foundation, repository separato):

| Aspetto | STL/OBJ | 3MF |
|---|---|---|
| Posizione | Core binario | Extension `threemf-io` |
| Disponibilità | Sempre | Dopo install + enable |
| API | `bpy.ops.wm.stl_*` | `bpy.ops.export_mesh.threemf` |
| Aggiornamenti | Ciclo rilascio Blender | Ciclo estensione (più rapido) |

**Abilitazione programmatica in CALL_0:**

```python
import addon_utils
addon_utils.enable("threemf-io", default_set=True, persistent=True)
```

**Features supportate 3MF 5.1:**
- Face Sets Blender → Triangle Sets 3MF (riconoscimento zone colore/supporto in Bambu Studio)
- Slicer profiles: metadati profili (infill, support, temp) stashati, ri-esportabili senza perdita
- PBR: Principled BSDF → estensioni materiali PBR 3MF native

Vedi `cad_import_workflow.md` per parametri operativi `export_mesh.threemf`.

---

## 3. BMesh: `bisect_plane` chiarito

L'ambiguità sulle chiavi restituite da `bmesh.ops.bisect_plane` è stata risolta in 5.x. Struttura certa:

```python
result = bmesh.ops.bisect_plane(
    bm,
    geom=geom_input,
    plane_co=origin,
    plane_no=normal,
    clear_outer=False,
    clear_inner=False,
)
# result è dict con:
# - "geom_cut": SOLO nuovi verts + edges SULLA intersezione (per creare caps)
# - "geom": TUTTA la geometria influenzata (per ricalcoli normali/pesi)
```

**Pattern "chiudi il taglio":** iterare `result["geom_cut"]` filtrando `BMEdge`, poi `bmesh.ops.edgenet_fill` o `edgeloop_fill` per generare il cap. Vedi `bisect_and_splitting.md` per esempi completi.

---

## 4. Boolean modifier — rename e `use_hole_tolerant`

### Rename solver "Fast" → "Float"

| Vecchio (≤ 4.2) | Nuovo (5.x) | Significato |
|---|---|---|
| `FAST` | `FLOAT` | Float arithmetic, rapido ma non gestisce complanari |
| `EXACT` | `EXACT` | Invariato — geometrie complesse e complanari |
| — | `MANIFOLD` | **Nuovo** — ottimizzato per solidi chiusi, velocità massima |

**Scripting cross-version:** l'enum `FAST` è ancora accettato come alias in 5.1 ma deprecato. Preferire `FLOAT`.

### Proprietà `use_hole_tolerant`

Stato chiarito nella 5.1:
- **Esiste ancora** nella struct `BooleanModifier` (contrariamente a note preliminari)
- **Default `False`** (performance)
- **Esclusiva del solver `EXACT`** — ignorata con `FLOAT` e `MANIFOLD`
- **Attivare solo se:** l'Exact solver fallisce su geometria non-chiusa / non-manifold

```python
mod = obj.modifiers.new("bool", type="BOOLEAN")
mod.operation = "DIFFERENCE"
mod.object = cutter
mod.solver = "EXACT"
mod.use_hole_tolerant = True   # solo quando serve, rallenta
```

Vedi `boolean_troubleshooting.md` per pattern di escalation FLOAT → EXACT → EXACT+hole_tolerant.

### Solver MANIFOLD — quando usarlo

Condizione: **entrambi gli operandi devono essere chiusi (manifold)**.

| Caso | Solver consigliato |
|---|---|
| Due solidi chiusi semplici | `MANIFOLD` (più veloce) |
| Uno degli operandi ha buchi/edge aperti | `EXACT` |
| Facce complanari esatte | `EXACT` |
| Mesh AI / fotogrammetria | `EXACT` (spesso non manifold) |

---

## 5. Custom split normals — approccio dichiarativo

### Vecchio workflow (imperativo)

```python
bpy.ops.mesh.customdata_custom_splitnormals_clear()  # ancora disponibile
```

Usato per rimuovere layer di normali orfani da import FBX/CAD che corrompevano sculpt/remesh.

### Nuovo workflow 5.x (dichiarativo via modifier)

Preferire modifier **"Smooth by Angle"** (introdotto 4.1, consolidato 5.x):
- Normali gestite come attributi `float` su dominio faces/loops
- Manipolabili via Geometry Nodes
- Niente corruzione in join/separate

L'operatore di clear rimane utile per rimuovere dati orfani ereditati da versioni precedenti o CAD esterni, ma non è più il pattern primario.

Vedi `mesh_repair.md` per il contesto "rimuovi custom normals prima di remesh AI".

---

## 6. Grease Pencil 3.0 — rewrite completo

**Breaking change massimo.** Script GP ≤ 4.x **non funzionano** in 5.x senza rewrite.

Cambiamenti architettural:

| Aspetto | GP 2.x | GP 3.0 |
|---|---|---|
| Data structure | Custom GP | Geometry nodes stack (stessa di mesh) |
| Material binding | Dedicato stroke *o* fill | Entrambi per punto |
| Auto-trace | Poligoni sovrapposti (fake holes) | Buchi reali |
| Performance stroke lunghi | Rinfresco scena per punto | Buffer GPU incrementale (≈ 10× più fluido) |

**Rilevanza per stampa 3D:** GP è raramente nel workflow print, ma se si usa per tracce 2D da convertire in curve → mesh (es. logo estruso), il nuovo import SVG + GP3 è la via preferita.

---

## 7. VSE — rename proprietà strip

Non rilevante per stampa 3D ma può rompere script legacy che toccano scene/timeline:

| Vecchio 4.x | Nuovo 5.1+ | Note |
|---|---|---|
| `frame_final_start` | `start` | Frame assoluto timeline |
| `frame_final_duration` | `duration` | Durata strip |
| `frame_start` | `content_start` | Offset interno file |
| `frame_offset_start` | `content_offset_start` | Gap inizio strip ↔ inizio file |

Alias vecchi validi fino a Blender 6.0.

---

## 8. Brush — unificazione `stroke_method`

Molti booleani `brush.use_*` sono stati unificati in un enum `brush.stroke_method`.

| Vecchio flag | Nuovo enum value |
|---|---|
| `use_airbrush` | `AIRBRUSH` |
| `use_anchor` | `ANCHORED` |
| `use_space` | `SPACE` |
| `use_line` | `LINE` |
| `use_curve` | `CURVE` |
| `use_restore_mesh` | `DRAG_DOT` |

**Vantaggio:** stato impossibile da corrompere con flag multipli incompatibili.

**Operatore rimosso:** `sculpt.sample_color` → usare `paint.sample_color` (unificato pittura + scultura).

---

## 9. UI / data-block tracking

### Rimosso: `UILayout.template_list(columns=...)`

Il parametro `columns` è stato **rimosso** da 5.0+. Il layout di liste è ora auto-gestito dal widget engine in base a spazio e contenuto.

### Nuovo: `UILayout.template_ID_session_uid`

Campo di ricerca basato su session UID (non nome). Risolve il problema del tracking di data-block rinominati durante la sessione.

```python
layout.template_ID_session_uid(my_prop_owner, "target_object")
```

Utile per addon MCP che devono mantenere riferimenti a oggetti anche quando l'utente li rinomina.

---

## 10. macOS — accesso device nativo

Script Python 5.1 su macOS possono accedere (previa autorizzazione utente):
- Fotocamera device
- Microfono
- Audio di sistema

Apre strada a motion capture facciale real-time senza dipendenze esterne. Non rilevante per stampa 3D ma utile sapere esista per future integrazioni.

---

## 11. Checklist migrazione per script esistenti

Per ogni script Python/MCP scritto per Blender ≤ 4.1, verificare:

1. ✅ Sostituire `bpy.ops.import_mesh.stl` con `bpy.ops.wm.stl_import`
2. ✅ Sostituire `bpy.ops.export_mesh.stl` con `bpy.ops.wm.stl_export`
3. ✅ Enum boolean solver: `"FAST"` → `"FLOAT"` (alias valido ma deprecato)
4. ✅ Considerare solver `"MANIFOLD"` per solidi chiusi (nuovo, più veloce)
5. ✅ Verificare che `bisect_plane` usi `geom_cut` (non `geom`) per i cap
6. ✅ Rimuovere `UILayout.template_list(columns=...)`
7. ✅ GP2 scripts: rewrite completo per GP3
8. ✅ VSE scripts: aggiornare `frame_final_*` → `start`/`duration`
9. ✅ Brush scripts: `use_*` bool flags → `stroke_method` enum
10. ✅ Abilitare `threemf-io` extension per export 3MF (non più add-on built-in)

---

## Cross-reference

- `import_export.md` — parametri completi `wm.stl_import` / `wm.stl_export` / `export_mesh.threemf`
- `boolean_troubleshooting.md` — escalation FLOAT → EXACT → EXACT+hole_tolerant
- `bisect_and_splitting.md` — pattern `geom_cut` per chiusura taglio
- `mesh_repair.md` — `customdata_custom_splitnormals_clear` contesto AI/FBX
- `cad_import_workflow.md` — 3MF multi-materiale e opzioni `export_mesh.threemf`
