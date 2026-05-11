# Pre-Print Validation — Go/No-Go prima dell'export STL

## Contesto

Ultima CALL della pipeline, prima di `wm.stl_export`. Raccoglie tutte le verifiche sparse in `[mesh_quality_assessment]`, `[workflow_patterns]#qa_pipeline`, `[measurement_toolkit]` in **un unico validatore** che produce:

1. **Un dict strutturato** (JSON-serializzabile) con metriche e verdetti per categoria
2. **Una decisione binaria**: `PASS`, `WARN`, `FAIL` → determina se si può procedere all'export
3. **Lista di issue** con severità e suggerimento di fix

La differenza con `[workflow_patterns]#qa_pipeline` (che è diagnostico) è che **qui c'è una decisione go/no-go**: l'agente non deve esportare se `FAIL`.

Prerequisito: `scale_length=0.001`; oggetto con `transform_apply` già fatto; nozzle 0.4 mm, A1 build volume 256³ mm, PLA.

---

## 1. Categorie di validazione

| Categoria | Cosa verifica | Severità max |
|---|---|---|
| `scene_setup` | scale_length, unit system | FAIL |
| `transforms` | scale applicata, no shear, origin coerente | WARN/FAIL |
| `manifold` | non-manifold edges, boundary, wire, duplicati, zero-area | FAIL |
| `bounds` | dimensioni entro 256×256×256 mm | FAIL |
| `min_feature` | dimensione minima, spessore pareti, feature sotto nozzle | WARN/FAIL |
| `orientation` | Z_min=0, X/Y centrati, bottom flatness | WARN |
| `overhangs` | % facce con tilt >45° | WARN |
| `poly_count` | tra 5k e 500k polys | WARN |
| `normals` | normali consistenti e verso l'esterno | FAIL |
| `multi_object` | scena ha 1 oggetto mesh attivo | WARN/FAIL |

---

## 2. Soglie — matrice decisionale

```python
THRESHOLDS = {
    # Unit system
    "scale_length_ok": 0.001,            # 1 BU = 1 mm
    
    # Manifold
    "non_manifold_edges_max": 0,
    "boundary_edges_max": 0,
    "zero_area_faces_max": 0,
    "wire_edges_max": 0,
    "duplicate_verts_max": 0,
    
    # Bounds
    "bed_x_mm": 256.0,
    "bed_y_mm": 256.0,
    "bed_z_mm": 256.0,
    "bed_margin_mm": 0.0,    # setta a 2mm se vuoi margine di sicurezza
    
    # Min feature
    "nozzle_mm": 0.4,
    "wall_min_mm": 0.8,          # 2 perimetri
    "wall_recommended_mm": 1.2,  # 3 perimetri
    "thickness_p10_min_mm": 0.8,
    "smallest_dim_mm": 3.0,      # oggetto troppo piccolo sotto 3mm
    
    # Orientation
    "z_min_tolerance_mm": 0.5,   # tolleranza bbox Z_min = 0
    "xy_off_center_warn_mm": 5.0,    # soglia di warning se non centrato
    
    # Overhangs
    "overhang_angle_deg": 45.0,
    "overhang_pct_warn": 15.0,
    "overhang_pct_fail": 40.0,
    
    # Poly count
    "poly_min": 100,
    "poly_max_warn": 500000,
    "poly_max_fail": 1500000,
    
    # Normals
    "flipped_normals_max_pct": 1.0,
}
```

---

## 3. Validatore — implementazione

```python
import bpy
import bmesh
import math
import random
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _bm_world(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return bm


def _score(severity, issues, msg, suggestion=""):
    """Appende issue con severità 'info' | 'warn' | 'fail'."""
    issues.append({"severity": severity, "message": msg, "suggestion": suggestion})


def validate_for_print(obj, thresholds=None, verbose=True):
    """
    Validator completo per export FDM.
    Ritorna dict con:
      - decision: 'PASS' | 'WARN' | 'FAIL'
      - issues: lista di {severity, message, suggestion}
      - metrics: dict di metriche numeriche
    """
    if thresholds is None:
        thresholds = THRESHOLDS
    
    assert obj.type == 'MESH', f"{obj.name} is not a MESH"
    
    issues = []
    metrics = {"object_name": obj.name}
    
    # === 1. Scene setup ===
    scene = bpy.context.scene
    scale_len = scene.unit_settings.scale_length
    metrics["scale_length"] = scale_len
    if abs(scale_len - thresholds["scale_length_ok"]) > 1e-6:
        _score("fail", issues,
               f"scale_length={scale_len} (expected {thresholds['scale_length_ok']})",
               "Set scene.unit_settings.scale_length = 0.001 (see [utils_units] CALL_0)")
    
    if scene.unit_settings.system != 'METRIC':
        _score("fail", issues, f"unit_system={scene.unit_settings.system} (expected METRIC)",
               "scene.unit_settings.system = 'METRIC'")
    
    # === 2. Transforms ===
    loc_scale = obj.scale
    metrics["obj_scale"] = tuple(loc_scale)
    if any(abs(s - 1.0) > 1e-6 for s in loc_scale):
        _score("fail", issues,
               f"scale not applied: {tuple(round(s,4) for s in loc_scale)}",
               "bpy.ops.object.transform_apply(scale=True)")
    
    # Check shear (matrice non ortogonale)
    mw = obj.matrix_world
    x_axis = mw.col[0].xyz.normalized()
    y_axis = mw.col[1].xyz.normalized()
    z_axis = mw.col[2].xyz.normalized()
    orth_xy = abs(x_axis.dot(y_axis))
    orth_xz = abs(x_axis.dot(z_axis))
    orth_yz = abs(y_axis.dot(z_axis))
    if max(orth_xy, orth_xz, orth_yz) > 1e-4:
        _score("warn", issues, f"matrix_world non-orthogonal (shear detected)",
               "apply transforms then check object matrix")
    
    # === 3. Manifold & geometry quality ===
    bm = _bm_world(obj)
    n_verts = len(bm.verts)
    n_edges = len(bm.edges)
    n_faces = len(bm.faces)
    
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    wire = sum(1 for e in bm.edges if e.is_wire)
    zero_area = sum(1 for f in bm.faces if f.calc_area() < 1e-12)
    
    # Duplicati (rough: cerca vertici con distanza < epsilon)
    # Veloce via KDTree
    from mathutils.kdtree import KDTree
    kd = KDTree(n_verts)
    for i, v in enumerate(bm.verts):
        kd.insert(v.co, i)
    kd.balance()
    duplicates = 0
    checked = set()
    for i, v in enumerate(bm.verts):
        if i in checked:
            continue
        for co, idx, d in kd.find_range(v.co, 1e-7):
            if idx != i and idx not in checked:
                duplicates += 1
                checked.add(idx)
    
    metrics["verts"] = n_verts
    metrics["edges"] = n_edges
    metrics["faces"] = n_faces
    metrics["non_manifold_edges"] = non_manifold
    metrics["boundary_edges"] = boundary
    metrics["wire_edges"] = wire
    metrics["zero_area_faces"] = zero_area
    metrics["duplicate_verts"] = duplicates
    
    if non_manifold > thresholds["non_manifold_edges_max"]:
        _score("fail", issues, f"non-manifold edges: {non_manifold}",
               "print3d_clean_non_manifold + holes_fill (see [mesh_repair])")
    if boundary > thresholds["boundary_edges_max"]:
        _score("fail", issues, f"boundary (open) edges: {boundary}",
               "fill_holes or bridge_edge_loops")
    if wire > thresholds["wire_edges_max"]:
        _score("fail", issues, f"wire edges (no faces): {wire}",
               "bmesh.ops.delete(bm, geom=wire_edges, context='EDGES')")
    if zero_area > thresholds["zero_area_faces_max"]:
        _score("fail", issues, f"zero-area faces: {zero_area}",
               "dissolve_degenerate")
    if duplicates > thresholds["duplicate_verts_max"]:
        _score("fail", issues, f"duplicate vertices: {duplicates}",
               "remove_doubles(threshold=0.0001)")
    
    # === 4. Bounds ===
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    x_min_mm = min(xs) * 1000
    x_max_mm = max(xs) * 1000
    y_min_mm = min(ys) * 1000
    y_max_mm = max(ys) * 1000
    z_min_mm = min(zs) * 1000
    z_max_mm = max(zs) * 1000
    dims_mm = Vector((x_max_mm - x_min_mm, y_max_mm - y_min_mm, z_max_mm - z_min_mm))
    
    metrics["bbox_min_mm"] = (x_min_mm, y_min_mm, z_min_mm)
    metrics["bbox_max_mm"] = (x_max_mm, y_max_mm, z_max_mm)
    metrics["dims_mm"] = tuple(dims_mm)
    
    bed_x = thresholds["bed_x_mm"] - 2 * thresholds["bed_margin_mm"]
    bed_y = thresholds["bed_y_mm"] - 2 * thresholds["bed_margin_mm"]
    bed_z = thresholds["bed_z_mm"]
    
    if dims_mm.x > bed_x or dims_mm.y > bed_y or dims_mm.z > bed_z:
        _score("fail", issues,
               f"dimensions {dims_mm.x:.1f}×{dims_mm.y:.1f}×{dims_mm.z:.1f}mm "
               f"exceed bed {bed_x:.0f}×{bed_y:.0f}×{bed_z:.0f}mm",
               "split model (see [bisect_splitting]) or scale down")
    
    smallest_dim = min(dims_mm)
    metrics["smallest_dim_mm"] = smallest_dim
    if smallest_dim < thresholds["smallest_dim_mm"]:
        _score("warn", issues,
               f"smallest dimension {smallest_dim:.2f}mm too small for FDM",
               f"scale up to at least {thresholds['smallest_dim_mm']}mm smallest dim")
    
    # === 5. Orientation ===
    xy_off = math.hypot((x_min_mm + x_max_mm) / 2, (y_min_mm + y_max_mm) / 2)
    metrics["xy_offset_from_origin_mm"] = xy_off
    if xy_off > thresholds["xy_off_center_warn_mm"]:
        _score("warn", issues,
               f"XY center offset {xy_off:.2f}mm from world origin",
               "center_xy_and_snap_bed(obj) (see [object_placement])")
    
    if abs(z_min_mm) > thresholds["z_min_tolerance_mm"]:
        _score("warn", issues,
               f"Z_min={z_min_mm:.2f}mm (expected ~0)",
               "snap_to_bed(obj) (see [object_placement])")
    
    # === 6. Overhangs ===
    n_overhang = 0
    overhang_rad = math.radians(180 - thresholds["overhang_angle_deg"])
    # Overhang = faccia la cui normale è sotto il piano orizzontale e ha tilt < (180 - angle)° da -Z
    # Più semplice: faccia ha componente Z negativa della normale e angolo con -Z < (90 - overhang_angle)
    for f in bm.faces:
        # Normale in world (già trasformata via bm.transform)
        n = f.normal
        # angolo con asse -Z (down)
        ang = math.degrees(n.angle(Vector((0, 0, -1))))
        if ang < (90 - thresholds["overhang_angle_deg"]):
            n_overhang += 1
    pct_overhang = 100.0 * n_overhang / max(n_faces, 1)
    metrics["overhang_pct"] = pct_overhang
    
    if pct_overhang > thresholds["overhang_pct_fail"]:
        _score("fail", issues,
               f"overhangs {pct_overhang:.1f}% of faces (>{thresholds['overhang_pct_fail']}%)",
               "reorient or split (see [orientation_strategy] + [bisect_splitting])")
    elif pct_overhang > thresholds["overhang_pct_warn"]:
        _score("warn", issues,
               f"overhangs {pct_overhang:.1f}% of faces (>{thresholds['overhang_pct_warn']}%)",
               "enable supports in slicer (see [support_strategy])")
    
    # === 7. Poly count ===
    if n_faces < thresholds["poly_min"]:
        _score("warn", issues,
               f"poly count {n_faces} below minimum (mesh too simple?)")
    if n_faces > thresholds["poly_max_fail"]:
        _score("fail", issues,
               f"poly count {n_faces} > {thresholds['poly_max_fail']}",
               "decimate (see [decimation_remesh])")
    elif n_faces > thresholds["poly_max_warn"]:
        _score("warn", issues,
               f"poly count {n_faces} > {thresholds['poly_max_warn']}",
               "decimate to speed up slicer")
    
    # === 8. Normals ===
    # Euristica: proporzione di facce con normale che punta "dentro"
    # Usiamo ray-casting dal centro di ogni faccia lungo la normale: se colpisce subito la mesh, normale flipped
    if non_manifold == 0 and boundary == 0:
        bvh = BVHTree.FromBMesh(bm)
        n_sampled = min(200, n_faces)
        sampled = random.sample(list(bm.faces), n_sampled)
        flipped_count = 0
        for f in sampled:
            origin = f.calc_center_median() + f.normal * 0.00001
            loc, _, _, _ = bvh.ray_cast(origin, f.normal)
            if loc is not None:
                # Hit sulla stessa mesh lungo la normale → normale è flipped
                flipped_count += 1
        flipped_pct = 100.0 * flipped_count / n_sampled
        metrics["flipped_normals_pct"] = flipped_pct
        if flipped_pct > thresholds["flipped_normals_max_pct"]:
            _score("fail", issues,
                   f"~{flipped_pct:.1f}% of sampled faces have flipped normals",
                   "bpy.ops.mesh.normals_make_consistent(inside=False)")
    else:
        metrics["flipped_normals_pct"] = None   # non affidabile su mesh non-manifold
    
    # === 9. Multi-object check ===
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_viewport]
    metrics["scene_mesh_count"] = len(mesh_objs)
    if len(mesh_objs) > 1:
        _score("warn", issues,
               f"scene has {len(mesh_objs)} visible MESH objects",
               "consider join() or export 3MF multi-part")
    
    bm.free()
    
    # === Decision ===
    fails = [i for i in issues if i["severity"] == "fail"]
    warns = [i for i in issues if i["severity"] == "warn"]
    if fails:
        decision = "FAIL"
    elif warns:
        decision = "WARN"
    else:
        decision = "PASS"
    
    result = {
        "decision": decision,
        "n_fails": len(fails),
        "n_warns": len(warns),
        "issues": issues,
        "metrics": metrics,
    }
    
    if verbose:
        print(f"[VALIDATE] {obj.name} decision={decision}")
        print(f"[VALIDATE] metrics: dims={metrics['dims_mm']} verts={metrics['verts']} polys={metrics['faces']}")
        print(f"[VALIDATE] non_manifold={metrics['non_manifold_edges']} boundary={metrics['boundary_edges']} zero_area={metrics['zero_area_faces']}")
        print(f"[VALIDATE] overhang={metrics['overhang_pct']:.1f}% flipped_normals={metrics.get('flipped_normals_pct')}")
        for iss in issues:
            print(f"  [{iss['severity'].upper()}] {iss['message']}"
                  + (f"  → {iss['suggestion']}" if iss['suggestion'] else ""))
    
    return result
```

---

## 4. Politica di export in base al verdetto

```python
def validate_and_maybe_export(obj, stl_path, allow_warn=True):
    """
    Valida + export STL se il verdetto lo permette.
    allow_warn: se True, esporta anche con WARN; se False, esporta solo su PASS.
    """
    result = validate_for_print(obj, verbose=True)
    
    if result["decision"] == "FAIL":
        print(f"[EXPORT] BLOCKED — decision=FAIL, {result['n_fails']} critical issues")
        return {"exported": False, "validation": result}
    
    if result["decision"] == "WARN" and not allow_warn:
        print(f"[EXPORT] BLOCKED — decision=WARN and allow_warn=False")
        return {"exported": False, "validation": result}
    
    # Export
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    bpy.ops.wm.stl_export(
        filepath=stl_path,
        export_selected_objects=True,
        global_scale=1000.0,
        use_scene_unit=False,
        apply_modifiers=True,
        ascii_format=False,
    )
    print(f"[EXPORT] OK → {stl_path} (decision={result['decision']})")
    return {"exported": True, "path": stl_path, "validation": result}
```

**Regola MCP**: in contesto agentico, su decisione `FAIL` mostrare all'utente il report con la lista di issue e il fix suggerito. Su `WARN` chiedere approvazione prima di procedere (a meno che l'utente abbia già dichiarato `allow_warn=True`).

---

## 5. Verdetti tipici per caso d'uso

| Scenario | Decision attesa | Azione consigliata |
|---|---|---|
| Mesh AI post-pipeline 8-CALL ben eseguita | PASS o WARN (overhang tipico) | Export con supporti in slicer |
| Mesh AI importata raw (pre-repair) | FAIL (non-manifold) | Passare da [ai_mesh_recipe] |
| Mesh da parametric_design_pattern appena creata | PASS | Export diretto |
| Photogrammetria senza decimate | WARN (poly count) / PASS se manifold | Decimate consigliata |
| Modello alto >256 mm | FAIL (bounds) | Split via [bisect_splitting] |
| Lithophane appena costruita | PASS (generalmente) | Export |
| Assembly unito male | FAIL (non-manifold da boolean) | Passare da [boolean_troubleshooting] |

---

## 6. Report serializzato (JSON)

Il dict `result` è JSON-serializzabile (tutte le metriche sono primitive). Per loggare o mostrare all'utente:

```python
import json

def print_validation_report(result):
    print(json.dumps(result, indent=2, default=str))

# Oppure export su file
def save_validation_report(result, filepath):
    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2, default=str)
```

**Nota**: il dict contiene `Vector` solo se qualcuno li aggiunge — le metriche base qui sono tuple/int/float. `default=str` è una safety net.

---

## 7. Estensioni opzionali (fuori default)

Se l'utente chiede verifiche più approfondite, attivabili come flag:

### 7.1 Wall thickness distribution (raycast)

Aggiunge `p10`, `p50`, `p90` dello spessore parete. Costoso (~200–500 raycast). Usa `measurement_toolkit.wall_thickness_distribution()`.

```python
def validate_with_thickness(obj, thresholds=None, samples=300):
    from measurement_toolkit import wall_thickness_distribution   # se modulare
    result = validate_for_print(obj, thresholds=thresholds)
    th = wall_thickness_distribution(obj, samples=samples)
    result["metrics"]["thickness_distribution"] = th
    
    if th["p10"] is not None and th["p10"] < thresholds["thickness_p10_min_mm"]:
        result["issues"].append({
            "severity": "warn",
            "message": f"p10 wall thickness {th['p10']:.2f}mm < {thresholds['thickness_p10_min_mm']}mm",
            "suggestion": "Solidify modifier or thicken walls manually",
        })
        if result["decision"] == "PASS":
            result["decision"] = "WARN"
    return result
```

### 7.2 PLA mass estimate

Aggiunge stima peso filamento (da `measurement_toolkit.estimate_pla_mass_g`). Utile per planning consumabili.

### 7.3 Cost estimate

Con `cost_per_kg_eur=25` (PLA standard) → stima costo. Puramente indicativo.

---

## 8. Integrazione nella pipeline

Ogni recipe (`ai_mesh_recipe`, `photogrammetry_recipe`, `image_to_mesh_recipes`, `functional_patterns_library`) dovrebbe concludere con:

```python
# CALL FINALE
result = validate_and_maybe_export(
    obj=model,
    stl_path="/path/to/output.stl",
    allow_warn=True,
)
print(f"[FINAL] exported={result['exported']}")
```

Questo è il **punto di terminazione** della pipeline. Dopo questa CALL, l'agente ha un STL pronto (o una lista di motivi per cui non lo è).

---

## 9. Caveat

- Le soglie sono calibrate per **A1 PLA nozzle 0.4 mm**. Per altro nozzle (0.2/0.6/0.8 mm) aggiornare `wall_min_mm` e `wall_recommended_mm` proporzionalmente (2× e 3× nozzle).
- La detection di normali flipped via raycast è **euristica** — funziona su mesh manifold, è inaffidabile su non-manifold (ragione per cui il check è skippato in quel caso).
- Il conteggio duplicati via KDTree con raggio 1e-7 BU è una heuristic per evitare falsi negativi post-operator Blender; se il test produce falsi positivi (mesh intenzionalmente densa), alzare il raggio.
- **Non** controlla accoppiamenti meccanici (clearance, fit): per quello vedere `[tolerances_and_fits]` e `[assembly_design]`.
- **Non** simula il gcode: la verifica finale di stampabilità è sempre `[gcode_inspection_basics]` nello slicer.

---

## 10. Checklist pre-commit della pipeline

L'agente, prima di concludere la risposta all'utente, deve:

1. Aver chiamato `validate_for_print(obj)` e ricevuto `decision != 'FAIL'`
2. Aver scritto il JSON del result in log (print)
3. Aver mostrato all'utente le issue con severity >= warn
4. Aver proceduto all'export solo se decision == PASS, o con approvazione esplicita se WARN
5. Aver stampato path STL finale con dimensioni e mass estimate
