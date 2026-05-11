# Boolean Troubleshooting — Diagnosi e Recovery

## Contesto

Il BooleanModifier è il punto di fallimento più frequente della pipeline FDM dell'agente: mesh AI con non-manifold, mesh importate con scala non applicata, cutter coplanari, self-intersection. Il fallimento è **silenzioso** — il modifier si applica ma produce geometria errata (buchi, facce doppie, topologia frammentata) senza sollevare eccezioni.

Questo documento copre:
1. Le 5 cause reali di fallimento di Boolean EXACT in Blender 5.1
2. Checklist di sanitizzazione **pre-boolean** obbligatoria
3. Pattern diagnostico post-boolean (detect se il risultato è valido)
4. Strategia di recovery e fallback su `bmesh.ops.boolean` e `bmesh.ops.split_edges`
5. Workarounds per casi patologici (coplanarità, geometria a filo)

Prerequisito: `scale_length=0.001` (1 BU = 1 mm), scale applicate su entrambi gli operandi, nozzle 0.4 mm.

---

## 1. Le 5 cause reali di fallimento Boolean EXACT

### 1.1 Scale non applicata

Causa più frequente e più subdola. L'operatore applica il boolean **dopo** la trasformazione world, ma la precisione float32 del solver degrada se la base e il cutter hanno scale ≠ 1. Sintomi: buchi errati (troppo grandi, spostati), facce flipped intorno al taglio.

Fix sempre: `transform_apply(scale=True)` su **entrambi** base e cutter prima del boolean.

### 1.2 Coplanarità cutter ↔ mesh

Se una faccia del cutter giace esattamente sul piano di una faccia della base (o del bordo), EXACT restituisce topologia indefinita. Caso classico: cutter cubo per "flatten bottom" a Z=0 con la base che tocca Z=0 → `{'FINISHED'}` ma la mesh risultante ha self-intersection.

Fix: margine ±0.001 mm (0.000001 BU) oppure 1 mm se la geometria lo permette. Regola d'oro: il cutter deve **attraversare completamente** la mesh base con un eccesso di ≥1 mm per lato.

### 1.3 Non-manifold su uno dei due operandi

Con mesh AI, il cutter potrebbe essere pulito ma la base contiene boundary edges, T-junction, self-intersection. EXACT in Blender 5.x ha un flag `use_self=True` per gestire self-intersection nello **stesso** operando, ma se c'è geometria aperta (buchi) il risultato è non definito — spesso il boolean taglia "attraverso il buco" lasciando flap di facce libere.

Fix sistematico pre-boolean: `print3d_clean_non_manifold()` + `remove_doubles(threshold=0.0001)` + `fill_holes(sides=0)` + `normals_make_consistent(inside=False)`.

### 1.4 Zero-area faces e duplicate vertices

EXACT calcola plane equations per ogni faccia. Facce degenere (3 vertici collineari, area=0) generano plane degenerate e mandano in stallo il solver o producono crash silenziosi (Blender continua ma il modifier non produce output).

Fix: `bpy.ops.mesh.delete_loose()` + `bmesh.ops.dissolve_degenerate()` + `remove_doubles`.

### 1.5 FAST solver su geometria non-convessa con self-intersection

FAST è solver BSP-based, rapido ma intollerante a self-intersection. Sintomi: facce girate, buchi. Su mesh AI con self-intersection, FAST **silenziosamente** produce soup.

Fix: switchare a EXACT. FAST va usato solo su primitive (cubi, cilindri generati da bpy.ops.mesh.primitive_*).

---

## 2. Checklist di sanitizzazione pre-boolean

Funzione idempotente da eseguire su **ogni** operando prima di qualsiasi Boolean. Non è distruttiva in senso MCP: opera su geometria già nel documento, ma normalizza lo stato.

```python
import bpy
import bmesh

def sanitize_for_boolean(obj, verbose=True):
    """
    Prepara un oggetto per Boolean EXACT:
      1. apply scale (previene drift precisione)
      2. rimuove loose verts/edges
      3. merge doubles
      4. dissolve degenerate (zero-area)
      5. fill holes non-manifold
      6. make normals consistent
    Ritorna dict con le correzioni applicate.
    """
    report = {"name": obj.name, "fixes": []}
    
    if obj.type != 'MESH':
        raise TypeError(f"{obj.name} is not MESH")
    
    # 1. Apply scale
    scale_vec = obj.scale
    if any(abs(s - 1.0) > 1e-6 for s in scale_vec):
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        report["fixes"].append(f"apply_scale {tuple(round(s,4) for s in scale_vec)}")
    
    # 2-5 in bmesh (più performante e stabile di bpy.ops.mesh in batch)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    
    # Loose geometry
    loose_verts = [v for v in bm.verts if not v.link_edges]
    loose_edges = [e for e in bm.edges if not e.link_faces]
    if loose_verts or loose_edges:
        bmesh.ops.delete(bm, geom=loose_verts, context='VERTS')
        bmesh.ops.delete(bm, geom=loose_edges, context='EDGES')
        report["fixes"].append(f"loose: v={len(loose_verts)} e={len(loose_edges)}")
    
    # Merge doubles
    before_v = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)  # 0.1 μm @ scale_length=0.001
    merged = before_v - len(bm.verts)
    if merged:
        report["fixes"].append(f"merge_doubles={merged}")
    
    # Dissolve degenerate
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    
    # Fill non-manifold holes (solo fori piccoli)
    bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)  # sides=0 = no limit
    
    # Recalc normals
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Count manifold edges residui
    bm2 = bmesh.new()
    bm2.from_mesh(obj.data)
    non_manifold = sum(1 for e in bm2.edges if not e.is_manifold)
    zero_area = sum(1 for f in bm2.faces if f.calc_area() < 1e-12)
    bm2.free()
    
    report["non_manifold_edges_remaining"] = non_manifold
    report["zero_area_faces_remaining"] = zero_area
    report["verts"] = len(obj.data.vertices)
    report["polys"] = len(obj.data.polygons)
    
    if verbose:
        print(f"[SANITIZE] {obj.name}: {report}")
    return report
```

### Tabella di ammissibilità per Boolean EXACT

| Metrica | Soglia OK | Azione se fuori soglia |
|---|---|---|
| scale applicata | tutte ≈ 1.0 | `transform_apply(scale=True)` |
| non-manifold edges | 0 | `print3d_clean_non_manifold` + `holes_fill` |
| zero-area faces | 0 | `dissolve_degenerate` |
| duplicate verts | < 0.1% del totale | `remove_doubles(0.0001)` |
| self-intersecting | 0 | `bool_mod.use_self=True` o bmesh fallback |
| coplanar con cutter | false | offset ±0.001 mm |

---

## 3. Pattern diagnostico post-boolean

Applicato subito dopo il Boolean per verificare che il risultato sia valido:

```python
import bmesh

def verify_boolean_result(obj, operation='DIFFERENCE'):
    """
    Post-boolean sanity check.
    Ritorna (ok: bool, report: dict).
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    non_manifold_edges = sum(1 for e in bm.edges if not e.is_manifold)
    boundary_edges = sum(1 for e in bm.edges if e.is_boundary)
    zero_area = sum(1 for f in bm.faces if f.calc_area() < 1e-12)
    wire_edges = sum(1 for e in bm.edges if e.is_wire)
    
    # Controllo volume — su DIFFERENCE deve essere > 0 e finito
    try:
        vol = bm.calc_volume(signed=False)
    except Exception:
        vol = None
    
    bm.free()
    
    report = {
        "non_manifold": non_manifold_edges,
        "boundary": boundary_edges,
        "zero_area": zero_area,
        "wire": wire_edges,
        "volume_bu3": vol,
    }
    
    ok = (
        non_manifold_edges == 0
        and boundary_edges == 0
        and zero_area == 0
        and wire_edges == 0
        and vol is not None and vol > 0
    )
    
    print(f"[BOOL-VERIFY] {obj.name} op={operation} ok={ok} {report}")
    return ok, report
```

**Semantica delle metriche nel contesto boolean:**

- `non_manifold > 0` post-DIFFERENCE → cutter non ha chiuso il foro correttamente (spesso per coplanarità); oppure base aveva non-manifold non corretto pre-boolean.
- `boundary > 0` → buchi creati dal boolean (faccia del cutter lasciata aperta). Causa tipica: cutter non passante.
- `wire > 0` → edge senza facce collegate. Indica flap di facce lasciate libere. Quasi sempre segno di self-intersection non gestita.
- `vol == 0 or None` → mesh collassata, boolean completamente fallito.

---

## 4. Strategia di recovery

Albero decisionale:

```
Boolean fallito (verify_boolean_result → ok=False)
 ├── non_manifold > 0 OR boundary > 0
 │    ├── cutter era a filo? → sposta cutter ±0.001 mm, retry
 │    ├── base aveva non-manifold pre-boolean? → sanitize base + retry
 │    └── altrimenti → attiva use_self=True, retry
 ├── zero_area o wire edges
 │    └── dissolve_degenerate + remove_doubles post-boolean, re-verify
 ├── volume == 0
 │    └── boolean completamente rotto → fallback bmesh (sezione 5)
 └── solver era FAST?
      └── switch a EXACT, retry
```

Pattern applicato automaticamente (wrapper):

```python
import bpy

def safe_boolean(base, cutter, operation='DIFFERENCE', max_attempts=3):
    """
    Boolean EXACT con recovery automatico.
    Ritorna (ok, report).
    """
    assert base.type == 'MESH' and cutter.type == 'MESH'
    
    sanitize_for_boolean(base, verbose=False)
    sanitize_for_boolean(cutter, verbose=False)
    
    last_report = None
    
    for attempt in range(max_attempts):
        # Seleziona base come active
        bpy.ops.object.select_all(action='DESELECT')
        base.select_set(True)
        bpy.context.view_layer.objects.active = base
        
        mod_name = f"_boolean_{attempt}"
        mod = base.modifiers.new(mod_name, type='BOOLEAN')
        mod.operation = operation
        mod.solver = 'EXACT'
        mod.object = cutter
        
        # attempt 1: senza use_self
        # attempt 2: con use_self
        # attempt 3: con offset cutter
        if attempt >= 1:
            mod.use_self = True
        if attempt >= 2:
            # Offset cutter ±0.001 mm in X (rompe coplanarità)
            cutter.location.x += 0.000001   # 0.001 mm in BU
        
        result = bpy.ops.object.modifier_apply(modifier=mod_name)
        if 'FINISHED' not in result:
            print(f"[BOOL] attempt {attempt}: modifier_apply CANCELLED")
            # Rimuovi modifier se ancora presente
            if mod_name in base.modifiers:
                base.modifiers.remove(base.modifiers[mod_name])
            continue
        
        ok, report = verify_boolean_result(base, operation=operation)
        last_report = report
        if ok:
            print(f"[BOOL] success at attempt {attempt}")
            return True, report
        
        # Post-cleanup prima di retry
        post_boolean_cleanup(base)
        ok2, report2 = verify_boolean_result(base, operation=operation)
        if ok2:
            print(f"[BOOL] success at attempt {attempt} after cleanup")
            return True, report2
        last_report = report2
    
    return False, last_report


def post_boolean_cleanup(obj):
    import bmesh
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.holes_fill(bm, edges=bm.edges, sides=4)  # solo buchi piccoli
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
```

---

## 5. Fallback bmesh — `bmesh.ops.boolean`

Quando anche Boolean EXACT con recovery fallisce (mesh AI estremamente corrotte, self-intersection non risolvibile), esiste un'alternativa a basso livello: `bmesh.ops.intersect` + split manuale. È più verboso ma più controllabile.

**Importante**: `bmesh.ops` non ha un'operazione "boolean UNION/DIFFERENCE" diretta come bpy.ops; fornisce `intersect` (taglia le facce lungo l'intersezione) e poi si deve decidere manualmente quale geometria tenere.

### Pattern — intersect + classify

```python
import bpy
import bmesh
from mathutils import Vector

def bmesh_boolean_difference(base_obj, cutter_obj):
    """
    Fallback bmesh per DIFFERENCE quando Boolean EXACT fallisce.
    Funziona integrando le mesh e poi rimuovendo le facce interne al cutter.
    
    Preconditions:
      - base_obj e cutter_obj applied (transform_apply)
      - cutter_obj è manifold, chiuso
    """
    # Lavora su una copia di base per non distruggere l'originale (regola MCP)
    bpy.ops.object.select_all(action='DESELECT')
    base_obj.select_set(True)
    bpy.context.view_layer.objects.active = base_obj
    bpy.ops.object.duplicate()
    result = bpy.context.active_object
    result.name = base_obj.name + "_diff"
    
    # Integra la cutter mesh nel result
    bm = bmesh.new()
    bm.from_mesh(result.data)
    
    # Append cutter (con trasformazione world)
    cutter_bm = bmesh.new()
    cutter_bm.from_mesh(cutter_obj.data)
    cutter_bm.transform(cutter_obj.matrix_world)
    # Poi trasla in spazio locale del result
    cutter_bm.transform(result.matrix_world.inverted())
    
    # Copia cutter in bm
    verts_map = {}
    for v in cutter_bm.verts:
        nv = bm.verts.new(v.co)
        verts_map[v] = nv
    bm.verts.index_update()
    cutter_faces_new = []
    for f in cutter_bm.faces:
        try:
            nf = bm.faces.new([verts_map[v] for v in f.verts])
            cutter_faces_new.append(nf)
        except ValueError:
            pass  # faccia duplicata, ignora
    cutter_bm.free()
    
    # Intersect: taglia le facce base lungo le facce cutter
    bmesh.ops.intersect(
        bm,
        geom=list(bm.faces) + list(bm.edges) + list(bm.verts),
        use_separate_all=True,
    )
    
    # Classifica: per ogni faccia del result, è dentro o fuori dal cutter?
    # Usa BVHTree sul cutter per ray-cast inside test
    from mathutils.bvhtree import BVHTree
    cutter_bvh = BVHTree.FromObject(cutter_obj, bpy.context.evaluated_depsgraph_get())
    
    faces_to_remove = []
    for f in bm.faces:
        center = f.calc_center_median()
        # Ray-cast in una direzione qualsiasi (es. +Z); conta hit
        # Numero hit dispari = dentro, pari = fuori
        loc, normal, idx, dist = cutter_bvh.ray_cast(center, Vector((0, 0, 1)))
        hits = 0
        origin = center.copy()
        while loc is not None:
            hits += 1
            origin = loc + Vector((0, 0, 0.00001))
            loc, normal, idx, dist = cutter_bvh.ray_cast(origin, Vector((0, 0, 1)))
        inside = (hits % 2) == 1
        if inside:
            faces_to_remove.append(f)
    
    # Rimuovi facce dentro + le facce del cutter stesso
    bmesh.ops.delete(bm, geom=faces_to_remove + cutter_faces_new, context='FACES')
    
    # Cleanup
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    bm.to_mesh(result.data)
    result.data.update()
    bm.free()
    
    print(f"[BMESH-BOOL] DIFFERENCE done: {len(faces_to_remove)} inner faces removed")
    return result
```

Questo pattern è più lento (O(n·m) per intersect) ed è da usare **solo quando il modifier Boolean ha esaurito i retry**. Per mesh >500k poly è impraticabile.

---

## 6. Casi patologici specifici e workaround

### 6.1 Flatten bottom con Z=0 a filo

**Problema**: vuoi appiattire la base a Z=0 con un cutter cubo che va da Z=-10 a Z=0. Il cutter è coplanare col piano XY del mondo — se la mesh ha vertici esattamente a Z=0, EXACT fallisce.

**Fix**: cutter da Z=-10 a Z=+0.001 (1 μm di intersezione garantita). Dopo il boolean, vertici a Z≈0 vanno snappati con `merge_by_distance(0.0001)` + shift di tutto il mesh a Z=0 esatto.

### 6.2 Cutter fori multipli a griglia

**Problema**: cutter composto da N cilindri (pattern piastra fori) — EXACT va in stallo (N×M face intersections). 

**Fix**: non creare un cutter unico; iterare cilindro per cilindro con Boolean separati **oppure** usare `Array Modifier` sul cutter base ma applicarlo prima del boolean, poi eseguire **un solo** boolean.

### 6.3 UNION su mesh AI "assembly" con self-intersection

**Problema**: due mesh AI che si intersecano e vanno unite. Entrambe hanno micro-self-intersection. EXACT restituisce geometria con buchi interni.

**Fix**: attivare `use_self=True` (Blender 4.x+) sul modifier. Se ancora fallisce: Voxel Remesh entrambe separatamente a `voxel_size=0.5 mm` (0.0005 BU), poi UNION.

```python
# UNION robusta su mesh AI
def robust_union_ai_meshes(obj_a, obj_b, voxel_size_mm=0.5):
    # Remesh voxel entrambe
    for obj in [obj_a, obj_b]:
        rm = obj.modifiers.new("_remesh", type='REMESH')
        rm.mode = 'VOXEL'
        rm.voxel_size = voxel_size_mm * 0.001
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier="_remesh")
    # Poi union
    return safe_boolean(obj_a, obj_b, operation='UNION')
```

### 6.4 DIFFERENCE su parte del mesh (non tutto)

**Problema**: vuoi fare un foro solo su una zona della mesh, ma il cutter è grande e genera self-intersection con geometrie lontane.

**Fix**: usare Vertex Group per limitare l'area. `bool_mod.object = cutter` + `bool_mod.use_hole_tolerant = True` (Blender 3.2+) per bordi non-manifold vicini.

### 6.5 Mesh con shape keys

**Problema**: Boolean silenziosamente fallisce (CANCELLED) se la mesh base ha shape keys attive.

**Fix**: rimuovere shape keys prima del boolean: `bpy.ops.object.shape_key_remove(all=True)`.

---

## 7. Quick reference — parametri Boolean modifier in 5.1

| Parametro | Default | Note |
|---|---|---|
| `operation` | 'INTERSECT' | Serve 'UNION'/'DIFFERENCE'/'INTERSECT' |
| `solver` | 'EXACT' | Usare EXACT; FAST solo per primitive |
| `object` | None | L'altra mesh |
| `use_self` | False | Gestisce self-intersection nell'operando — abilitare su mesh AI |
| `use_hole_tolerant` | False | Blender 3.2+ — tollera piccoli buchi; abilitare su mesh AI |
| `double_threshold` | 1e-6 | Tolleranza merge (non cambiare) |
| `material_mode` | 'INDEX' | Irrilevante per FDM single-material |

**Pattern preferito per mesh AI**:

```python
mod = obj.modifiers.new("Bool", type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.solver = 'EXACT'
mod.use_self = True
mod.use_hole_tolerant = True
mod.object = cutter
```

---

## 8. Log consigliato nelle CALL MCP

Ogni operazione boolean in una CALL deve printare:

```
[BOOL] base={name} cutter={name} op={op} solver={solver}
[BOOL] base-pre: verts={v} polys={p} non_manifold={nm} scale_applied={bool}
[BOOL] cutter-pre: verts={v} polys={p} non_manifold={nm} scale_applied={bool}
[BOOL] result: ok={bool} non_manifold={nm} boundary={b} volume_mm3={vol}
```

Senza questo log l'agente non può diagnosticare cosa è andato storto senza rieseguire l'operazione.
