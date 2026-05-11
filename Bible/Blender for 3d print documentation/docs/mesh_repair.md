# Riparazione Mesh per Stampa 3D

## Problemi comuni che bloccano il slicer

| Problema | Causa tipica | Effetto sullo slicer |
|---|---|---|
| **Non-manifold** | Edge condivisi da ≠ 2 face (buchi, T-junctions) | Perimetri sbagliati, geometria aperta |
| **Normali invertite** | Face con normale verso l'interno | Il slicer non distingue dentro/fuori |
| **Geometria degenere** | Edge o face con lunghezza/area = 0 | Artefatti, errori di slicing |
| **Face distorte** | Quad/ngon non planari | Triangolazione imprevedibile in export |
| **Doppi vertici** | Vertici sovrapposti nello stesso punto | Geometria fantasma, edge non-manifold |

---

## 1. Analisi e rilevamento

### `bpy.ops.mesh.print3d_check_all()`
Operatore del 3D Print Toolbox addon che esegue una suite completa di controlli (non-manifold, normali, spessori, distorsione). I risultati appaiono nel pannello N → 3D-Print. Richiede che l'addon `object_print3d_utils` sia abilitato. Utile come punto di partenza prima di intervenire manualmente.

```python
import addon_utils
addon_utils.enable("object_print3d_utils", default_set=True)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.mesh.print3d_check_all()
```

### `bpy.ops.mesh.select_non_manifold()`
Seleziona in Edit Mode gli edge e i vertici che violano la condizione manifold. Tre parametri booleani permettono di filtrare la tipologia di problema:

- `use_wire=True` — edge senza alcuna face associata
- `use_boundary=True` — edge con una sola face (bordi aperti, buchi)
- `use_multi_face=True` — edge condivisi da più di 2 face (T-junction)

Dopo l'esecuzione i problemi sono visibili nel viewport e contabili via BMesh. Non modifica la geometria; serve esclusivamente per ispezione o come preludio a operazioni di selezione.

```python
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_non_manifold(
    use_wire=True,
    use_boundary=True,
    use_multi_face=True
)
```

### Pattern: `check_manifold(obj)`
La funzione seguente restituisce quanti edge non-manifold esistono nella mesh, sfruttando l'attributo `e.is_manifold` di BMesh. Utile per confrontare la mesh prima e dopo la riparazione, o per decidere se applicare operazioni aggiuntive.

```python
import bmesh

def check_manifold(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    non_manifold = [e for e in bm.edges if not e.is_manifold]
    bm.free()
    return len(non_manifold) == 0, len(non_manifold)

is_ok, count = check_manifold(bpy.context.active_object)
print(f"Manifold: {is_ok}, edge non-manifold: {count}")
```

---

## 2. Operatori di riparazione

### `bpy.ops.mesh.print3d_clean_non_manifold()`
Fix automatico del 3D Print Toolbox: riempie buchi, corregge normali e rimuove edge/face degeneri in un'unica chiamata. È il punto di partenza più rapido per mesh importate da CAD o scan. Va eseguito in Object Mode con l'oggetto attivo.

```python
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.mesh.print3d_clean_non_manifold()
```

### `bpy.ops.mesh.remove_doubles(threshold=0.0001)`
Unisce (merge) i vertici che si trovano entro la distanza `threshold` l'uno dall'altro. Elimina doppi vertici che causano edge non-manifold nascosti. Il valore di soglia va scelto in base all'unità della scena: 0.0001 corrisponde a 0.1 mm se l'unità è il metro, oppure a 0.1 µm se l'unità è il millimetro. Richiede Edit Mode con i vertici target selezionati.

```python
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0001)
```

### `bpy.ops.mesh.dissolve_limited(angle_limit=0.0017)`
Collassa facce coplanari o quasi-coplanari in un'unica face più grande, rimuovendo gli edge ridondanti che le separano. Il parametro `angle_limit` è in **radianti** (0.0017 rad ≈ 0.1°, 0.0175 rad ≈ 1°). Più il valore è piccolo, più rigoroso il criterio di coplanarità.

**Uso principale per stampa 3D:** pulire STL importati con superfici piane over-tessellate (pareti di architetture, griglie piatte, facce di CAD esportati come triangoli) riducendo drasticamente il numero di facce senza alterare la forma. Eseguire subito dopo l'import, prima di qualsiasi operazione di repair.

```python
import bpy

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
# 0.0017 rad ≈ 0.1° — conservativo, solo facce praticamente piatte
bpy.ops.mesh.dissolve_limited(angle_limit=0.0017)
bpy.ops.object.mode_set(mode='OBJECT')

print(f"Facce dopo dissolve_limited: {len(bpy.context.active_object.data.polygons)}")
```

**Confronto con altri dissolve:**
| Operatore | Rimuove | Quando usarlo |
|---|---|---|
| `dissolve_limited` | Edge tra facce coplanari | STL con piane iper-tessellate (post-import) |
| `dissolve_degenerate` | Edge lunghi zero / facce area zero | Geometria degenerata post-boolean |
| `remove_doubles` / `merge_by_distance` | Vertici sovrapposti | Vertici duplicati da import |

> ⚠ **Non usare valori alti** (> 0.1 rad / 6°) su mesh organiche: collassa facce curved che sembrano coplanari a bassa risoluzione, deformando la geometria.

### `bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)`
Rimuove edge di lunghezza zero e face di area zero che rimangono dopo operazioni booleane o import da altri software. Il parametro `threshold` definisce la soglia sotto la quale un elemento è considerato degenere. Da preferire a `delete` manuale perché mantiene la topologia circostante intatta.

```python
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)
```

### `bpy.ops.mesh.normals_make_consistent(inside=False)`
Ricalcola le normali di tutte le face selezionate rendendole coerenti tra loro. Con `inside=False` (default consigliato per stampa 3D) le normali puntano verso l'esterno del volume. Con `inside=True` si invertono verso l'interno. L'operatore funziona per propagazione: se una parte della mesh è disconnessa, il risultato su ciascun componente separato è indipendente.

```python
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
```

### `bpy.ops.mesh.fill_holes(sides=0)`
Chiude i boundary loop aperti (buchi nella mesh) inserendo nuove face. Il parametro `sides` limita quali buchi vengono riempiti in base al numero di lati del bordo: `sides=0` riempie tutti i buchi indipendentemente dalla complessità, `sides=4` riempie solo quelli con 4 lati o meno. Produce face planari semplici; per buchi complessi il risultato può richiedere ritopologia manuale.

```python
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.fill_holes(sides=0)
```

### `bpy.ops.mesh.quads_convert_to_tris(quad_method, ngon_method)`
Triangolarizza tutta la mesh. Alcuni slicer (e il formato STL stesso) richiedono mesh interamente triangolata. I parametri `quad_method` e `ngon_method` controllano l'algoritmo di suddivisione: `'BEAUTY'` minimizza la distorsione cercando la diagonale più corta, `'FIXED'` è deterministico e più veloce. Da applicare come ultima operazione prima dell'export, per non complicare le operazioni di riparazione precedenti.

```python
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(
    quad_method='BEAUTY',
    ngon_method='BEAUTY'
)
bpy.ops.object.mode_set(mode='OBJECT')
```

---

## 3. Equivalenti BMesh

Le API BMesh operano direttamente sulla struttura dati della mesh senza passare per il contesto UI, rendendole più robuste in script non interattivi e nei casi in cui l'oggetto non è attivo nel viewport. La sequenza tipica è: creare un BMesh dalla mesh, applicare le operazioni, riscrivere i dati, liberare il BMesh.

| Operazione | API BMesh |
|---|---|
| Rimuovi doppi | `bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)` |
| Ricalcola normali | `bmesh.ops.recalc_face_normals(bm, faces=bm.faces)` |
| Riempi buchi | `bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)` |
| Triangolarizza | `bmesh.ops.triangulate(bm, faces=bm.faces)` |

```python
import bmesh

obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='OBJECT')

bm = bmesh.new()
bm.from_mesh(obj.data)

bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)
# triangolarizza solo se necessario per l'export
bmesh.ops.triangulate(bm, faces=bm.faces)

bm.to_mesh(obj.data)
bm.free()
obj.data.update()
```

---

## 4. Operatori aggiuntivi per mesh AI-generated

### `bpy.ops.mesh.customdata_custom_splitnormals_clear()`

Rimuove le custom split normals salvate nella mesh. I modelli AI (specialmente FBX da Hyper3D, Tripo, Meshy) includono spesso custom normals generate dal loro pipeline interno. Queste **interferiscono** con Voxel Remesh, sculpting, e `normals_make_consistent`: la mesh sembra corretta nel viewport ma produce errori nel slicer.

Da eseguire in Edit Mode, prima di qualsiasi operazione di sculpting o remesh su modelli AI-generati.

```python
import bpy

obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.mode_set(mode='OBJECT')
print("Custom split normals rimossi — mesh pronta per sculpting/remesh")
```

> ⚠ **Eseguire PRIMA di Voxel Remesh e PRIMA di sculpting**. Senza questo step le custom normals vengono ereditate nella nuova topologia e causano shading artifacts non risolvibili con normals_make_consistent.

---

### `bpy.ops.mesh.tris_convert_to_quads()`

Converte triangoli in quad dove la geometria lo consente. L'equivalente Python del shortcut Alt+J in Edit Mode. I modelli AI esportano quasi sempre in triangoli (GLB/FBX triangolato); questa operazione recupera la struttura a quad per una topologia più pulita prima di editing o rigging.

```python
import bpy

obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.tris_convert_to_quads(
    face_threshold=0.698,    # 40° — angolo massimo tra facce adiacenti per merge (in radianti)
    shape_threshold=0.698,   # 40° — angolo massimo di forma del quad risultante
    uvs=True,                # rispetta seams UV nel merge
    vcols=True,              # rispetta vertex colors
    seam=True,               # non unire attraverso seams
    sharp=True,              # non unire attraverso edge sharp
    materials=True           # non unire tra materiali diversi
)
bpy.ops.object.mode_set(mode='OBJECT')
n_faces = len(obj.data.polygons)
print(f"Tris → Quads completato. Face count: {n_faces}")
```

**Limiti:** non garantisce la conversione completa — solo i triangle pair che formano un quad planare valido vengono uniti. Per mesh completamente triangolate (STL, AI low-poly), la maggior parte dei triangoli resterà tale. La conversione totale richiede retopologia manuale o Voxel Remesh.

---

### Pattern: merge_by_distance PRIMA di Voxel Remesh

> ⚠ **Critico per mesh AI**: i modelli generati da AI contengono frequentemente vertici sovrapposti ("loose vertices") invisibili nel viewport ma che **corrompono il Voxel Remesh**. Il risultato è una mesh caotica o completamente degradata.

**Sequenza obbligatoria prima di qualsiasi Voxel Remesh su mesh AI:**

```python
import bpy

obj = bpy.context.active_object
bpy.context.view_layer.objects.active = obj

# STEP 1: merge_by_distance per eliminare vertici sovrapposti
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0001)  # 0.1 µm — non rimuove dettaglio reale
bpy.ops.object.mode_set(mode='OBJECT')
n_verts_after_merge = len(obj.data.vertices)
print(f"Vertici dopo merge_by_distance: {n_verts_after_merge}")

# STEP 2: solo ora è sicuro applicare Voxel Remesh
mod = obj.modifiers.new(name="Remesh_Voxel", type='REMESH')
mod.mode = 'VOXEL'
mod.voxel_size = 0.001  # 1mm — regolare in base al dettaglio richiesto
bpy.ops.object.modifier_apply(modifier="Remesh_Voxel")
print(f"Voxel Remesh completato. Verts: {len(obj.data.vertices)}")
```

Se si salta il merge_by_distance e il remesh produce una mesh completamente distrutta: annullare (la mesh originale è al sicuro non essendo stata applicata nessuna modifica sui dati), eseguire il merge, e riprovare.

---

### Pattern: Inflate + Remesh per fusione geometria intersecante

Quando due parti di una mesh si intersecano senza essere connesse (gap, buchi, parti che si "sfiorano") il Voxel Remesh non le fonde automaticamente se tra le superfici c'è spazio vuoto. La sequenza Inflate → Remesh chiude prima il gap e poi unifica la topologia.

**Non scriptabile via MCP** — il brush Inflate richiede interazione in Sculpt Mode. Documentato come workflow manuale.

**Workflow manuale in Sculpt Mode:**
1. Selezionare l'oggetto → Tab non serve, andare in Sculpt Mode
2. Brush: **Inflate/Deflate** (tasto I o cerca nella brush list)
3. Dipingere l'area del gap: il brush "gonfia" le superfici verso l'esterno, chiudendo il vuoto
4. Quando il gap visivo è chiuso, tornare in Object Mode
5. Applicare Voxel Remesh (vedi CALL 5b in ai_mesh_recipe.md) — il remesh fonde le geometrie ora contigue in un unico volume manifold
6. Tornare in Sculpt Mode → Smooth brush per levigare l'area unificata

**Quando è necessario:**
- Neck-hair gap nei personaggi AI-generated (spazio tra collo e capelli)
- Vestiti che non toccano il corpo sottostante
- Appendici (code, corna, dettagli) con mesh non connessa al body principale
- Buchi chiusi con Inflate ma topologie ancora distinte → remesh le unisce

**Verifica post-remesh**: enable Face Orientation overlay (viewport → Overlays → Face Orientation). Tutto blu (esterno) = mesh unificata corretta. Rosso all'interno = doppio layer ancora presente, ripetere inflate + remesh con voxel_size più piccolo.

---

### Chiusura buco circolare: Scale-to-zero su asse + merge_by_distance

Tecnica per chiudere rapidamente un buco circolare (es. foro aperto su un cilindro, apertura superiore di un vaso) collassando tutti i vertici del bordo in un punto centrale.

```python
import bpy
import bmesh

# PREREQUISITO: entrare in Edit Mode e selezionare SOLO i vertici del bordo del buco
# (manualmente o con: bpy.ops.mesh.select_non_manifold(use_boundary=True))

# Una volta selezionato il loop del bordo:
obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')

# Seleziona bordi del buco (boundary edges)
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_non_manifold(use_wire=False, use_boundary=True, use_multi_face=False)

# Per buco su piano XY: scala a 0 su Z (collassa tutti i vertici al centro in Z)
# Modificare l'asse in base all'orientamento del buco
bpy.ops.transform.resize(value=(1, 1, 0))  # equivalente S → Z → 0

# Unisci i vertici ora sovrapposti
bpy.ops.mesh.merge_by_distance(threshold=0.001)

bpy.ops.object.mode_set(mode='OBJECT')
print("Buco chiuso: vertici collassati al centro")
```

**Variante con asse singolo (per buchi non nel piano XY):**
- Buco perpendicolare a X: `resize(value=(0, 1, 1))` → S → X → 0
- Buco perpendicolare a Y: `resize(value=(1, 0, 1))` → S → Y → 0  
- Buco perpendicolare a Z: `resize(value=(1, 1, 0))` → S → Z → 0

**Alternativa**: `bpy.ops.mesh.fill_holes(sides=0)` per buchi semplici (vedi sezione 2). Scale-to-zero è preferibile per buchi circolari grandi dove fill_holes produce ngon non planare.

---

### Note sul 3D Print Toolbox: interpretazione avanzata dei check

Il toolbox `print3d_check_all()` produce check che richiedono interpretazione corretta:

**Bad Contiguous Edges** — non è un problema di edge geometry ma di **normali flipped**. Seleziona gli edge ai confini tra zone con normali discordanti. Fix: `bpy.ops.mesh.select_all(action='SELECT')` + `bpy.ops.mesh.normals_make_consistent(inside=False)`.

**Non-flat Faces** — il valore di soglia di default è 45°, troppo permissivo per precision modeling. Impostare a **0.1°** (in Blender UI: pannello N → 3D-Print → Checks → Non-flat Faces → 0.1). A questa soglia seleziona qualsiasi ngon/quad con curvatura percepibile, essenziale per identificare face che genereranno triangolazione imprevedibile in STL.

**Thin Faces** — threshold FDM: `0.86mm` (= ~2 linee × nozzle 0.4mm). Per resin: `0.05mm`. Questo valore corrisponde al muro più sottile fisicamente stampabile in modo affidabile sulla tecnologia target.

**Sharp Edges** — edge con angolo di piegatura > 160° (quasi inverso di piatto). Si manifestano nel slicer come pareti mancanti o linee singole. Fix: smussare l'edge o aggiungere geometria di transizione.

> ⚠ **Bug 3D Print Toolbox**: oggetti posizionati a **più di 2000mm dall'origine** generano falsi positivi "Thin Faces" anche su geometry perfettamente valida. Questo colpisce qualsiasi workflow che non mantiene il modello vicino all'origine prima del check. Fix: spostare il modello vicino all'origine (object location ≈ 0,0,0) prima di eseguire `print3d_check_all()`.

**Cleanup panel — ATTENZIONE**: i tool "Make Manifold" e "Distort" del pannello Cleanup sono automatizzati ma distruttivi. "Make Manifold" può collassare geometria valida, "Distort" applica la diagonale della triangolazione in modo casuale (non deterministico). **Preferire sempre il fix manuale** sui problemi individuati dai check. Usare il Cleanup solo su mesh di scarso valore dove la velocità conta più della qualità.

---

## 4. Boolean union per geometrie sovrapposte

Il modificatore Boolean con `operation='UNION'` fonde due oggetti sovrapposti in un unico volume manifold, eliminando le intersezioni interne. Il solver `'EXACT'` garantisce precisione geometrica ma è più lento; `'FAST'` è adatto a mesh semplici o preview. Dopo l'applicazione, `obj_B` va rimosso esplicitamente dalla scena perché il modificatore non lo elimina automaticamente.

```python
obj_A = bpy.data.objects['BaseObject']
obj_B = bpy.data.objects['AddObject']

bpy.context.view_layer.objects.active = obj_A

mod = obj_A.modifiers.new(name="Bool_Union", type='BOOLEAN')
mod.operation = 'UNION'   # oppure 'DIFFERENCE' o 'INTERSECT'
mod.object = obj_B
mod.solver = 'EXACT'      # 'EXACT' = preciso, 'FAST' = veloce

bpy.ops.object.modifier_apply(modifier="Bool_Union")
bpy.data.objects.remove(obj_B, do_unlink=True)
```
