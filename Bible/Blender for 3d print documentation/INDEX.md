# Blender MCP — Knowledge Base Index

Contesto: Blender MCP (blender-mcp v1.5.5), Python API Blender 5.x (testato su 5.1), focus stampa 3D FDM su Bambu A1.
Carica questo file sempre nel contesto. Usa il tag [topic_id] per richiedere il documento specifico.

> **KB Bambu** — Per specifiche hardware A1, regole design FDM (spessori, tolleranze, viti, materiali, calibrazione, profili Bambu Studio), consultare la KB separata in `Bambu Wiki documentation/INDEX.md` se la root del progetto è `Bible/`. I dati hardware fondamentali (build volume 256³mm, nozzle 0.4mm, layer range 0.08–0.28mm) sono riassunti anche in [fdm_printing_constraints].

## [fdm_printing_constraints]
**Vincoli fisici FDM: Bambu A1 specifiche, layer height, wall thickness, overhangs, bridges, materiali**
Quando usarlo: devi sapere cosa può stampare il Bambu A1, quali sono i limiti fisici (spessore minimo, angolo overhang, lunghezza bridge), come orientare il modello, quale materiale per cosa
File: `docs/fdm_printing_constraints.md`

Contenuto: Specs hardware A1 (256×256×256mm, nozzle 0.4mm, temp max 300°C/100°C), layer height range 0.08–0.28mm, wall thickness per nozzle size (0.45mm/0.9mm/1.35mm/1.8mm per 1-4 perimeters), regola critica "between 1-2 perimeters = not printable", overhang 45° safe/60° con cooling, bridge affidabile ≤30mm, tabella nozzle 0.2/0.4/0.6/0.8mm, materiali supportati (PLA/PETG/TPU), anisotropia FDM (XY più forte di Z), infill 10–15% tipico, feature minima 0.8mm.

## [source_mesh_characteristics]
**Caratteristiche mesh AI-generated e fotogrammetria: difetti tipici, cause, effetti sulla stampa**
Quando usarlo: hai ricevuto un mesh da generatore AI (TripoSG, Hunyuan3D) o fotogrammetria e devi capire cosa aspettarti, quali problemi tipicamente ha, perché fallisce in slicer
File: `docs/source_mesh_characteristics.md`

Contenuto: TripoSG (GLB, SDF-based, --faces configurabile, artefatti da estrazione), Hunyuan3D (trimesh/GLB, no manifold guarantee), caratteristiche generali AI (triangle soup, non-manifold, thin walls, no flat surfaces, scala arbitraria, geometria da foto = bumps), pipeline fotogrammetria (milioni triangoli, background noise, buchi, surface roughness, scaling), tabella tipi non-manifold (T-junction/vertex fan/self-intersection/flipped normals/open boundary/duplicati/zero-area), detection programmatica in bmesh, profilo tipico AI vs fotogrammetria, perché ogni difetto rompe FDM.

## [mesh_quality_assessment]
**Analisi qualità mesh in Blender: 3D Print Toolbox, bmesh metrics, priorità di valutazione**
Quando usarlo: hai una mesh e devi valutare se è print-ready, quali problemi ha, quanto sono gravi, da dove partire
File: `docs/mesh_quality_assessment.md`

Contenuto: 3D Print Toolbox operators (print3d_check_solid/intersect/thick/sharp/overhang/all, print3d_clean_non_manifold/distorted, print3d_info_volume/area, print3d_scale_to_bounds), scene.print_3d properties (thickness_min, overhang_angle), bmesh inspection (non-manifold edges, boundary edges, find_doubles, zero-area faces, dimensions), tabella metriche (come estrarle, soglia, significato), verifica scale (scale_length, length_unit), ordine di priorità assessment (1.scale → 2.non-manifold → 3.dimensions → 4.wall thickness → 5.poly count → 6.overhangs → 7.surface noise).

## [ai_generators_field_kit]
**Field kit per generatori AI 2024-2026: Meshy, TripoSG, Hunyuan3D, Rodin, TRELLIS, Zero123 — output, axis, scale, artifact, playbook iniziale**
Quando usarlo: hai ricevuto un file da un generator AI specifico (o non sai quale), devi sapere artefatti tipici, axis convention (Y-up), scale (~1.0 BU unit-cube), playbook iniziale di repair
File: `docs/ai_generators_field_kit.md`

Contenuto: pattern universali AI mesh (GLB Y-up, unit-cube normalized, MC seam artifacts, no print-aware preprocessing, texture-as-geometry), tabella per-generator (Meshy v4-v6, TripoSR/SG, Hunyuan3D 2.0/2.1, Rodin Gen-1/2 con Quad mode virtuoso, TRELLIS v1/v2 con script hole-fill, Zero123/Zero123++, Step1X-3D, UltraShape 1.0), heuristica detect-and-route (estensione + bbox + face_count + materials + topology hint), workflow consigliato per generator, ranking 2026 per print-readiness (Step1X-3D/UltraShape > Rodin Quad > Hunyuan3D 2.1 > Meshy > TripoSG > TRELLIS > TripoSR > Zero123).

## [blender_3d_print_toolbox]
**Reference completa operator object_print3d_utils: 7 check, 2 clean, transform, hollow VDB, scene properties, report._data, pattern idiomatici, quirks**
Quando usarlo: hai 3D Print Toolbox installato e devi conoscere bl_idname esatto di ogni operator, parametri, side effects, failure modes; come leggere risultati programmatically via report._data
File: `docs/blender_3d_print_toolbox.md`

Contenuto: enable programmatico via addon_utils, lettura risultati via `from object_print3d_utils import report; report.info()`, scene.print_3d properties (thickness_min/threshold_zero/angle_distort/angle_sharp/angle_overhang/export_*), info ops (volume/area), check ops (solid/intersect/degenerate/distort/thick/sharp/overhang/all) - tutti i check NON modificano selezione, salvano in report._data globale, recuperabile via `select_report(index)`, clean_non_manifold pipeline interna (delete_loose → remove_doubles → dissolve_degenerate → fill_holes → make_normals_consistent) con bug noto T48565, clean_distorted, clean_thin STUB vuoto, transform (scale_to_volume/scale_to_bounds/align_to_xy + use_alignxy_face_area), hollow VDB pyopenvdb-based, 7 pattern idiomatici (set threshold prima di check_thick, check+select_report+edit, check_all triage, repair iterativo R005, scale to A1 bounds 256mm, auto-orient face piatta, overhang assessment per orientation), confronto con analyze_mesh_for_print (complementarità routing vs investigation), 10 quirks (check_thick undercount su mesh aperta, check_overhang object-local space, clean_non_manifold introduce nuovi non-manifold, clean_thin stub, Bad Contiguous Edges = flipped normals).

## [addon_threemf_io]
**threemf-io Blender addon (import/export 3MF, Ghostkeeper + LeeGillie fork): bug Blender 4.5+ TypeError, operator API, Production Extension limits, scale_length workaround**
Quando usarlo: stai per chiamare `import_mesh.threemf` o `export_mesh.threemf`, vuoi sapere quale fork installare per Blender version, capire perché Bambu Studio scarta certi 3MF
File: `docs/addon_threemf_io.md`

Contenuto: 2 operator (import_mesh.threemf + export_mesh.threemf, solo OBJECT mode), tabella params completi con types/defaults/ranges, spec coverage Core 1.2.3 (Ghostkeeper) vs 1.4.0 (LeeGillie), materials solo Principled BSDF Base Color → basematerials displaycolor (NO texture roundtrip), **Multi-plate via Parent Empty NON è feature reale** (Empty diventa parentless item group, plate config Bambu non scritta), units handling con scale_length quirk #89, 6 quirks con citazioni GitHub (#89 tiny exports, #61 file rejection, #81/84/87/92 Blender 4.5 TypeError, #91 hide_render ignored, #76 import names fix), 7 patterns idiomatici, comparison Ghostkeeper vs LeeGillie (Blender 4.5+ obbligatorio LeeGillie).

## [addon_bool_tool]
**Bool Tool addon (nickberckley): brush=non-destructive + auto=destructive, solver in prefs, cutter library management**
Quando usarlo: serve cutter library reversibile (toggle/apply/remove), single cutter interactive workflow, brush ops mantengono modifier sticky vs auto applies immediato
File: `docs/addon_bool_tool.md`

Contenuto: nomenclatura confusa (brush=non-destr, auto=destr counter-intuitive), 4 brush ops + 4 auto ops + 6 cutter management ops (toggle/remove/apply/toggle_all/remove_all/apply_all), selection contract (active=canvas, others=cutters), shared mixin params (material_mode INDEX/TRANSFER, use_self, use_hole_tolerant, double_threshold 1e-6), solver NON parametro per-call (letto da add-on prefs globali: FLOAT default, EXACT, MANIFOLD), side effects (collection boolean_cutters, parent, wireframe display), 5 patterns (cutter library reversibile, quick destructive, MANIFOLD solver setup, pre-flight transform_apply, toggle off temporary), bug Blender 5.0 #148829, comparison vs Booltron (preferisci per interactive single cutter).

## [addon_booltron]
**Booltron addon (mrachinskiy): pre-op sanitize automatico, MANIFOLD per-side, multi-cutter batch join, coplanar jitter**
Quando usarlo: STL imports non puliti da AI/scan/CAD, batch boolean N cutters, serve solver MANIFOLD differenziato primary/secondary, mesh con coplanarità rischiose
File: `docs/addon_booltron.md`

Contenuto: 4 destructive + 3 nondestructive ops (geometry-nodes based), killer feature `meshlib.prepare()` (remove_doubles + dissolve_degenerate + delete_loose + holes_fill automatici), settings via WindowManager.booltron.destructive/.nondestructive (solver per primary+secondary, merge_distance 3e-4, dissolve_distance 1e-4, use_loc_rnd + loc_offset 0.005 per coplanar jitter), multi-cutter batch join in 1 mesh poi 1 modifier (vs N modifier di Bool Tool), is_nonmanifold post-op check (reports ma no auto-fix), failure modes MANIFOLD requires watertight both sides + tiny merge collassa hole <0.3mm, 7 patterns (mounting hole array N→1 modifier, flatten bottom Z=0, snap-fit shrunk cutter, multi-shell UNION MANIFOLD, slice con overlap_distance per glue lap, coplanar jitter setup, batch pipeline config).

## [addon_looptools]
**LoopTools addon (8 ops mesh repair): bridge, circle, flatten, relax (string iterations!), space, curve. Workflow canonico repair AI mesh post-decimate**
Quando usarlo: riparare buchi grandi/irregolari su AI mesh, bridge 2 shells, circolarizzare hole distorto, distribute vertices, flatten loop su build plate
File: `docs/addon_looptools.md`

Contenuto: 8 operator sotto bpy.ops.mesh.looptools_* (EDIT mode), bridge con shortest matching + mode hidden in UI ma callable + auto normals_make_consistent line 3419, circle best-fit + flatten in uno shot, flatten con plane=best_fit/normal/view + lock_x/y/z lowercase, **relax iterations è STRING enum '1'/'3'/'5'/'10'/'25' NON int** (silent failure tipico), space per equalize spacing pre-bridge, curve/loft/gstretch (skip per FDM), quirks (iterations string typo, lock lowercase, cache invalidation via undo_push, bridge unequal vertex counts greedy match, relax volume loss con linear), workflow canonico repair (select_non_manifold → relax cubic 3 iter → circle → flatten → fill_holes/bridge/f2 → normals_make_consistent), comparison vs built-in (per hole repair sempre LoopTools, per smooth profile-shaped bridge built-in).

## [addon_f2]
**F2 addon (quad fill da 1 vertex/edge): autograb=False obbligatorio per MCP, INVOKE_DEFAULT required**
Quando usarlo: gap 3-5 vertex post-decimate dove built-in F non infera quad, fill consistent con flow surrounding
File: `docs/addon_f2.md`

Contenuto: 1 solo operator mesh.f2, **quirk killer per MCP** (solo invoke() no execute(), autograb=True stalla in modal grab → bug T52506), set autograb=False + 'INVOKE_DEFAULT' obbligatorio, 5 branches in invoke() (≥3 verts → edge_face_add, 2 verts same edge → quad_from_edge, 2 verts not same edge → fallback, 1 vert con 2 boundary edges → quad_from_vertex, 1 vert con extendvert → expand_vert), addon preferences (adjustuv/autograb/extendvert/material_inherit flags), failure modes (selezione errata su gap concavo, vertex con non-2 boundary edges → fallback), 4 patterns (setup MCP obbligatorio, fill 1 vertex gap, loop N vertices multi-quad, fill irregular boundary chain), comparison vs built-in F (F2 inventa 4° vertex da topology, F solo bridge selection).

## [addon_mesh_repair_tools]
**Mesh Repair Tools (SineWave): mega-op fix_mesh_global con properties group, hole-fill più robusto del built-in, smart normal recalc**
Quando usarlo: AI mesh decimata con buchi irregolari, serve cleanup multi-pass configurable, recalc normals con auto-flip, fix self-intersection actually (non solo report come PT3D)
File: `docs/addon_mesh_repair_tools.md`

Contenuto: N-panel Local Fix (EDIT) + Global Fix (OBJ/EDIT), 7 operator (object.fix_mesh_global mega-op + 6 locali), properties da scene.meshfixtool_properties (tri_boolean, face_normal_boolean, minor_parts_boolean + threshold 1%, spikes_boolean + angle 10°, intersection_boolean + angle, holes_boolean, volume_intersection_boolean DANGEROUS clear modifiers + drop vgroups, wiz_boolean Fix Wizard paid), pipeline fix_mesh_global (remove_doubles → tris/quads → recalc normals → spikes dissolve → intersection smooth → loose parts → volume union opt → custom holes_fill edgeloop su ogni boundary → final remove_doubles), local_face_normal smart auto-flip, remesh_local_v2 (subdiv+laplacian+decimate), smooth_local_v2, flatten_local (requires LoopTools), reduce_local, refind_local (typo nel bl_idname), 4 patterns (AutoFix completo, AutoFix + PT3D QC chained, smart recalc post-boolean, volume_intersection con backup), comparison vs PT3D (MRT actually fixes intersections + spikes, PT3D solo reports + ottimo per QC finale).

## [addon_extra_mesh_objects]
**Extra Mesh Objects: primitive parametriche utili come Boolean cutter (round_cube bevellato, pipe joints, gear, diamond countersink, beam profile, honeycomb)**
Quando usarlo: serve cutter Boolean parametrico complesso (chamfered hole, channel routing, countersink), primitive print-ready (spur gear, beam strutturale), pattern infill (honeycomb)
File: `docs/addon_extra_mesh_objects.md`

Contenuto: tutti gli operator creano nuovo object al 3D cursor + active+selected (mixin AddObjectHelper), primitive_round_cube_add (bevelled cube cutter chamfered holes), pipe joint family (elbow/tee/wye/cross/n_joint per cable channel cutters), primitive_gear (spur gear con vertex groups Tips+Valleys, negative radius → crown gear), primitive_worm_gear, primitive_diamond_add (countersink cutter), primitive_steppyramid_add (overhang test calibration), primitive_solid_add (Platonic/Archimedean/Catalan con vTrunc/eTrunc/snub/dual), add_beam (C/I/L/T/U/rectangular profile structural), honeycomb_add (infill pattern), failure modes (arc_div alto senza no_limit aborts, xyz_function_surface security warning), 7 patterns (chamfered mounting hole cutter, cable channel elbow, print-ready spur gear M=1.5mm 20 denti, diamond countersink M3, honeycomb infill, test staircase overhang, I-beam structural), comparison vs built-in primitives (Extra è estensione non sostituzione di cube/sphere/cylinder built-in).

## [blender_addons_recommended]
**Addon raccomandati per print-prep workflow: 3D Print Toolbox, threemf-io, Booltron, Bool Tool, LoopTools, F2, Mesh Repair Tools, Extra Mesh Objects + install order + 3MF fork decision**
Quando usarlo: vuoi sapere quali addon installare oltre i bundled, decidere quale fork 3MF usare (threemf-io vs LeeGillie), capire quale builtin sottoutilizzato c'è (voxel_remesh/quadriflow_remesh callable diretti, solver MANIFOLD)
File: `docs/blender_addons_recommended.md`

Contenuto: 7 addon Tier 1 con MCP API completi e workflow value (3MF I/O bambu, Booltron con solver MANIFOLD 4.5+, Bool Tool interactive, LoopTools bridge_edge_loops per buchi grandi post-decimate, F2 quad fill 3-5 vertex gap, Mesh Repair Tools fill_holes più robusto, Extra Mesh Objects round_cube per cutter); Tier 2 Extra Mesh Objects; NON raccomandati con motivo (MeasureIt pure UI, Quad Remesher ridondante con QuadriFlow built-in, MeshLint abbandonato, Tweaker-3 GPL virale); builtin sottoutilizzati (wm.stl_import/export moderni, voxel_remesh/quadriflow_remesh callable, solver MANIFOLD); decisione 3MF fork (threemf-io primary, LeeGillie per Blender 5.x, evita Korchy/shusain); install order one-shot via Extensions Platform; verifica caricamento programmatica; conflitti & coesistenza (Bool Tool + Booltron complementari); MCP wrapper consigliato (export_3mf_bambu, bridge_open_loops, safe_boolean_difference).

## [analyze_to_action]
**Decision tree: dall'output JSON di analyze_mesh_for_print alla sequenza di azioni di cleanup**
Quando usarlo: hai appena eseguito analyze_mesh_for_print e devi decidere cosa fare; vuoi capire le regole che il tool MCP kb_route applica; vuoi aggiungere o modificare regole di routing
File: `docs/analyze_to_action.md`

Contenuto: tabella chiavi dell'analysis JSON, 9 regole numerate (R001-R009) ognuna con priority/when/then/expected_after/rationale: R001 degenerate_faces→dissolve_degenerate (priority 110, primo step), R002 normals=all_inverted→recalc_normals, R003 disconnected_shells>1→split_then_decide (needs_user_input), R004 non_manifold+holes→fill_holes (playbook repair_basic), R005 non_manifold senza holes→clean_non_manifold (playbook repair_aggressive), R006 face_count>500k→decimate_collapse (playbook decimate_to_target), R007 voxel remesh fallback, R008 dimension>256mm→bisect_splitting, R009 scale errata→scale_detection. Convenzione output kb_route (input_summary, matched_rules, next_action). Le regole sono machine-readable in `routing_rules.yaml` ed eseguibili via tool MCP kb_route(analysis_json).

## [wall_thickness_actionable]
**Decision tree dimensionale: dato wall_thickness_p10_mm / under_min_pct, scegli Solidify globale / Solidify selettivo / re-scale / accetta-e-flagga**
Quando usarlo: kb_route ha matched R010 o R010b, hai numeri di wall thickness sotto le soglie FDM A1, devi decidere se solidificare globalmente, mirato, o riprogettare
File: `docs/wall_thickness_actionable.md`

Contenuto: 4 casi A/B/C/D mappati a thresholds (>=0.8 OK, 0.45–0.8 marginale con 3 opzioni, <0.45 strutturale con 3 opzioni, null=mesh aperta), tabella conseguenze slicer (0.21/0.45/0.8/1.20mm), codice Solidify +0.3/+0.5mm con `use_even_offset`, opzioni "Solidify selettivo via vertex group" (richiede utente), "accetta-e-flagga al slicer", "re-design/split", "0.2mm nozzle hardware change". Caveat sul sampling (max 5000 face centroids, p10 vs minimo, falsi negativi su feature poco campionate, solidi convessi pieni). Rule trigger: R010 (priority 65) per p10<0.8, R010b (priority 80) per p10<0.45.

## [problem_to_tool_map]
**Mappa problema → strumento Blender: quale tool per quale difetto, tradeoff, quando usare quale**
Quando usarlo: hai identificato un problema specifico (non-manifold, troppi poligoni, rumore superficiale, scala sbagliata, pareti sottili, overhangs, geometria disconnessa, normali invertite) e devi scegliere lo strumento giusto
File: `docs/problem_to_tool_map.md`

Contenuto: 8 categorie problema con tutti gli strumenti disponibili, parametri chiave, tabelle tradeoff: (1) Non-manifold → fill_holes/remove_doubles/normals_consistent/RemeshVOXEL, (2) High poly → Decimate(COLLAPSE/DISSOLVE)/Remesh, (3) Surface noise → LaplacianSmooth/CorrectiveSmooth/Remesh, (4) Wrong scale → obj.scale+transform_apply, (5) Thin walls → SolidifyModifier, (6) Overhangs → reorient/slicer supports, (7) Disconnected → Separate+Boolean UNION, (8) Flipped normals → normals_make_consistent. Tabella decisionale riassuntiva.

## [multi_object_management]
**Gestione oggetti multipli: inventario scena, isole disconnesse, separazione, filtraggio artefatti, unione**
Quando usarlo: dopo import STL trovi più oggetti o geometrie disconnesse, vuoi rimuovere floating artifacts, devi unire più parti in un singolo mesh stampabile, devi identificare qual è la geometria principale
File: `docs/multi_object_management.md`

Contenuto: inventario scena (loop su scene.objects con dimensioni/poligoni), rilevamento isole via BFS (count_islands()), separate(type='LOOSE') per separare in oggetti distinti, remove_small_objects() per filtrare artefatti sotto soglia mm, join() vs Boolean UNION (quando usare quale), boolean_union_all() iterativo, clean_import() pattern (separa → tieni il più grande), tabella proprietà Object rilevanti (type/name/dimensions/select/hide/remove).

## [decimation_remesh]
**Decimazione e remeshing: ridurre poligoni per stampa FDM, parametri quantitativi, tradeoff**
Quando usarlo: mesh ha troppi poligoni (> 500k), vuoi ridurre prima dello slicing, devi scegliere tra Decimate e Remesh, hai bisogno di valori pratici per voxel_size o ratio
File: `docs/decimation_remesh.md`

Contenuto: target poligoni per FDM (50k–200k), DecimateModifier (COLLAPSE ratio, DISSOLVE angle_limit, UNSUBDIV iterations — tradeoff e limiti), RemeshModifier VOXEL (voxel_size in BU/mm, formula voxel_size=feature_size/2, stima face count), stima programmatica voxel_size da area superficiale, stima ratio Decimate da target faces, tabella comparativa casi d'uso, ordine operazioni. **Tabella calibrazione pratica voxel_size** (7 categorie: miniatura 30–50mm → 0.3–0.5mm; figurina 50–100mm → 0.5–1mm; oggetto decorativo → 1–2mm; parte funzionale → 2mm; meccanica con incastri → 0.5–1mm; oggetto grande → 3–5mm; test → 5–10mm; con stima face count e RAM picco per categoria); **sweet spot pratico FDM**: voxel_size=0.001 (1mm); regola: sotto 0.5mm voxel il dettaglio non è stampabile con nozzle 0.4mm; avviso RAM critico per voxel_size <0.0003.

## [scale_detection]
**Rilevamento e correzione scala mesh importato: diagnosi, soglie euristiche, rescale a mm target**
Quando usarlo: hai importato un STL e le dimensioni sembrano sbagliate (troppo piccolo, troppo grande, non in mm), devi portare un mesh a dimensioni reali note, devi verificare che un oggetto entri nel volume A1
File: `docs/scale_detection.md`

Contenuto: perché STL non ha metadata di unità, tabella origini scale sbagliate (AI normalizzati/fotogrammetria/tool in metres), come leggere obj.dimensions in mm, soglie euristiche diagnosi (< 0.1mm = too_small, > 1000mm = too_large), funzione diagnose_scale(), funzione rescale_to_target_mm() con transform_apply obbligatorio, stima da contesto semantico, parametri STL import (use_scene_unit, global_scale).

## [mcp_tools]
**Tool MCP disponibili + REGOLE OPERATIVE OBBLIGATORIE: execute_blender_code, screenshot, pattern base**
Quando usarlo: devi sapere quali tool MCP esistono, come usare execute_blender_code, pattern base di selezione oggetti e cambio modalità, e le regole operative che OGNI script MCP deve rispettare
File: `docs/mcp_tools.md`

Contenuto: Lista completa tool MCP (execute_blender_code principale, get_viewport_screenshot per verifica visiva), pattern base: seleziona oggetto per nome, cambia mode (OBJECT/EDIT), accedi a mesh data, bpy.context/bpy.data. **⚠ REGOLE OPERATIVE MCP — OBBLIGATORIE** (leggere prima di scrivere qualsiasi script): (1) bpy.ops.ed.undo() è VIETATO — in contesto stateless causa comportamento imprevedibile; alternativa: duplicate-before-operate; (2) operazioni distruttive (bisect su originale, apply modifier, delete, boolean su originale) richiedono approvazione esplicita utente prima dell'esecuzione; (3) verifiche non devono modificare la mesh originale — duplicare, operare su copia, screenshot, rimuovere copia; (4) posizionare camera prima di ogni screenshot; (5) usare solo algoritmi da KB o metriche certe, mai euristiche inventate; (6) ogni CALL deve essere autonoma e stateless — nessuna variabile Python persiste tra chiamate.

## [mesh_repair]
**Riparazione mesh: operatori e strumenti per non-manifold, normali, buchi, duplicati, triangolazione**
Quando usarlo: mesh presenta edge non-manifold, normali invertite, buchi, geometria degenere, vertici doppi; devi eseguire boolean union/difference
File: `docs/mesh_repair.md`

Contenuto: tabella problemi mesh (causa + effetto sullo slicer), operatori di analisi (select_non_manifold con parametri use_wire/use_boundary/use_multi_face, check_manifold utility), operatori di riparazione (**dissolve_limited** angle_limit radianti — collassa facce coplanari, usare post-import STL iper-tessellati prima di repair, tabella confronto dissolve_limited vs dissolve_degenerate vs remove_doubles, warning angoli alti su mesh organiche; remove_doubles, fill_holes, normals_make_consistent, dissolve_degenerate — parametri e tradeoff di ciascuno), equivalenti BMesh (remove_doubles/holes_fill/recalc_face_normals/triangulate), triangolazione per STL, boolean UNION/DIFFERENCE via modifier. **Operatori aggiuntivi per mesh AI** (sezione 4): `customdata_custom_splitnormals_clear()` — rimuovere custom normals da FBX AI prima di sculpt/remesh (interferiscono con normals_make_consistent); `tris_convert_to_quads()` con parametri face_threshold/shape_threshold/uvs/seam; **merge_by_distance PRIMA di Voxel Remesh** — critico per mesh AI (loose vertices invisibili corrompono il remesh); **Inflate+Remesh per fusione geometria intersecante** (workflow manuale, non MCP-scriptabile); **chiusura buco circolare via scale-to-zero + merge** (`resize(value=(1,1,0))` per buco sul piano XY, varianti per altri assi). **Note 3D Print Toolbox avanzate**: Bad Contiguous Edges = normali flipped (fix: normals_make_consistent); Non-flat Faces soglia 0.1° per precision modeling; Thin Faces FDM threshold 0.86mm = 2 pareti nozzle 0.4mm; Sharp Edges >160° = pareti mancanti in slicer; **bug phantom thin faces >2000mm dall'origine**; Cleanup panel — Make Manifold e Distort distruttivi, preferire fix manuale.

## [scripting_guide]
**Guida scripting Blender Python: pattern fondamentali, operatori, context override, temp_override**
Quando usarlo: inizi a scrivere script Python per Blender, devi capire come funziona l'API, pattern idiomatici, gestione errori, sovrascrivere il contesto di un operatore in Blender 5.x
File: `docs/scripting_guide.md`

Contenuto: Struttura bpy (context/data/ops/types), data-blocks vs runtime data, Edit/Object Mode sync, BMesh to_mesh/free, bpy.ops poll() failures, foreach_get/foreach_set numpy, misura dimensioni, workflow mesh per print, debug e tips. **`bpy.context.temp_override()` — Blender 4.0+**: sostituisce il vecchio dict context override (deprecato in 5.x); pattern `get_view3d_context()` per trovare area VIEW_3D; `with bpy.context.temp_override(area, region):` per qualsiasi op che richiede viewport; tabella parametri disponibili (area/region/space_data/active_object/selected_objects/edit_object); nota background mode (MCP = UI attiva, temp_override funziona sempre); tabella errori aggiornata con `RuntimeError: poll() con ops viewport → temp_override`.

## [bpy_basics]
**bpy.ops, bpy.context, bpy.data: accesso base all'API Blender**
Quando usarlo: devi richiamare operatori Blender, accedere a dati scena, capire differenza tra ops/context/data/types
File: `docs/bpy_basics.md`

Contenuto: bpy.ops (operatori, polling, context requirements), bpy.context (active_object, selected_objects, mode, scene, view_layer), bpy.data (collezioni globali, new/remove), bpy.types (riferimento tipi), pattern idiomatici comuni.

## [mesh_ops]
**Operazioni mesh: edit mode, selezione, modifica geometria, UV, normali**
Quando usarlo: devi modificare geometria in edit mode, selezionare vertici/edge/face, eseguire operazioni (extrude, inset, bevel), gestire UV
File: `docs/mesh_ops.md`

Contenuto: bpy.ops.mesh.* (select_all, extrude_faces, inset_faces, loop_cut, bevel, subdivide, dissolve_*, fill, bridge_edge_loops), accesso mesh dati in editmode con BMesh, selezione per normale/posizione, gestione UV layers.

## [object_ops]
**Operazioni oggetti: aggiunta, rimozione, duplicazione, join, parent, apply transforms**
Quando usarlo: devi creare/eliminare/duplicare/unire oggetti, impostare parent-child, applicare trasformazioni
File: `docs/object_ops.md`

Contenuto: bpy.ops.object.* (add, delete, duplicate, join, parent_set, parent_clear), transform_apply (location/rotation/scale), origin_set, convert, make_single_user, link/unlink da collection.

## [import_export]
**Import/Export STL e 3MF: parametri bpy.ops per stampa 3D**
Quando usarlo: devi importare un STL in Blender, esportare per Bambu Studio/slicer, usare il formato 3MF per assembly multi-oggetto o unità esplicite
File: `docs/import_export.md`

Contenuto: bpy.ops.wm.stl_export (tutti i parametri: filepath, ascii_format, use_scene_unit, apply_modifiers, global_scale, assi), bpy.ops.wm.stl_import (global_scale, use_scene_unit, use_mesh_validate), scale e unità (use_scene_unit=True con scale_length=0.001), binary vs ASCII, assi di orientamento. **3MF Export** (sezione completa): tabella STL vs 3MF (unità esplicite mm, multi-oggetto, metadati, compattezza); `bpy.ops.export_mesh.threemf()` — parametri filepath/use_selection/use_mesh_modifiers/global_scale=1000.0; addon io_mesh_3mf built-in in Blender 5.1, abilitazione via addon_utils; export multi-oggetto; distinzione Bambu Project File vs Standard 3MF (Blender genera Standard, Bambu Studio importa correttamente); helper `export_for_print()` parametrico STL|3MF; regola: preferire 3MF per assembly, STL per singolo oggetto.

## [bmesh_scripting]
**BMesh API: accesso mesh programmativo, modifica diretta geometria, più robusto di bpy.ops**
Quando usarlo: devi modificare mesh programmaticamente (non tramite operatori), fare operazioni custom su vertici/edge/facce, analisi topologia
File: `docs/bmesh_scripting.md`

Contenuto: bmesh.new(), bm.from_mesh(mesh), bm.to_mesh(mesh), accesso a verts/edges/faces, selezione, iteratori, operatori BMesh (bmesh.ops.*), ensure_lookup_table(), layers (UV, vertex color, custom), BVH da BMesh.

## [modifiers_generate]
**Modificatori generativi: Array, Mirror, Solidify, Screw, Skin, Subdivision Surface, Boolean**
Quando usarlo: devi aggiungere pattern ripetuto (Array), specchiare (Mirror), dare spessore (Solidify), creare forme di rivoluzione (Screw), fare operazioni booleane UNION/DIFFERENCE/INTERSECT (Boolean), aggiungere dettaglio (SubSurf)
File: `docs/modifiers_generate.md`

Contenuto: **BooleanModifier** (operation UNION/DIFFERENCE/INTERSECT, object, solver FAST/EXACT — usare EXACT per geometrie precise, cutter deve estendersi oltre la mesh base, non usare su geometria non-manifold), Solidify (thickness, offset, use_even_offset, use_quality_normals), Mirror (use_axis, use_clip, merge_threshold), Array (fit_type, count, relative_offset_displace, use_object_offset), SubSurf (levels, render_levels, use_limit_surface), Screw (steps, iterations, angle, axis), Skin, parametri e pattern per stampa 3D.

## [modifiers_deform]
**Modificatori deformazione e cleanup: Decimate, SubsurfModifier, Bevel, Shrinkwrap, LaplacianSmooth, CorrectiveSmooth, Triangulate, Weld, Displace, EdgeSplit, NormalEdit, WeightedNormal, SimpleDeform, Cast**
Quando usarlo: devi smussare edge (Bevel), ridurre poligoni (Decimate), rimuovere rumore (LaplacianSmooth/CorrectiveSmooth), adattare a superficie (Shrinkwrap), unire vertici sovrapposti (Weld), aggiungere texture superficiale (Displace), triangolizzare per STL (Triangulate), deformare shape (SimpleDeform/Cast)
File: `docs/modifiers_deform.md`

Contenuto: DecimateModifier (COLLAPSE ratio, UNSUBDIV iterations, DISSOLVE angle_limit, use_collapse_triangulate), SubsurfModifier (levels, render_levels, use_limit_surface, use_creases), BevelModifier (width, segments, limit_method=ANGLE, angle_limit, profile, miter_outer/inner, use_clamp_overlap, harden_normals), ShrinkwrapModifier (target, wrap_method, offset), LaplacianSmoothModifier (iterations, lambda_factor, use_volume_preserve), CorrectiveSmoothModifier (factor, iterations, smooth_type), TriangulateModifier (quad_method SHORTEST_DIAGONAL, ngon_method BEAUTY, min_vertices), **WeldModifier** (merge_threshold, mode ALL/CONNECTED — alternativa non-distruttiva a bpy.ops.mesh.merge_by_distance(), preferire in MCP), DisplaceModifier (texture, strength, mid_level, direction NORMAL/XYZ, texture_coords UV/LOCAL), EdgeSplitModifier, NormalEditModifier, WeightedNormalModifier, SimpleDeformModifier (TWIST/BEND/TAPER/STRETCH, deform_axis, angle, limits), CastModifier (SPHERE/CYLINDER/CUBOID, factor, radius).

## [mesh_types]
**Struttura dati mesh Blender: Mesh, MeshVertex, MeshEdge, MeshPolygon, MeshLoop**
Quando usarlo: devi accedere direttamente ai dati mesh (vertici, facce, normali, aree), usare foreach_get per performance, analizzare geometria a basso livello
File: `docs/mesh_types.md`

Contenuto: Mesh (proprietà: vertices, edges, polygons, loops, materials, attributi; metodi: update, from_pydata, validate, clear_geometry), MeshVertex (co, normal, index, select, hide, groups), MeshEdge (vertices[2], index, select, is_loose, use_edge_sharp, use_seam), MeshPolygon (vertices, loop_start, loop_total, normal, center, area, material_index, use_smooth, flip()), MeshLoop (vertex_index, edge_index, normal, tangent, bitangent). Pattern pratici con foreach_get numpy, bounding box, overhang detection, area superficiale.

## [object_scene_types]
**Struttura dati scena Blender: Object, Scene, BlendData, Context, UnitSettings, Collection, Material**
Quando usarlo: devi capire le proprietà di Object (matrix_world, bound_box, dimensions, modifiers), accedere alla scena (objects, unit_settings, cursor), gestire collezioni, creare/modificare materiali
File: `docs/object_scene_types.md`

Contenuto: Object (name, type, data, location, rotation_euler, scale, dimensions, bound_box, matrix_world, modifiers, material_slots, select_get/set, hide_get/set), Scene (objects, unit_settings, cursor, frame_current, collection), UnitSettings (system METRIC/IMPERIAL, scale_length, length_unit), BlendData/bpy.data (objects/meshes/materials/collections — new/remove/batch_remove), Context/bpy.context (active_object, selected_objects, scene, view_layer, mode), Collection (objects, children, hide_viewport, hide_render), Material (use_nodes, node_tree, diffuse_color, roughness, metallic).

## [mathutils]
**Math utilities Blender: Vector, Matrix, Euler, Quaternion, geometry, BVHTree, KDTree**
Quando usarlo: devi fare operazioni matematiche su vettori/matrici, intersezioni geometriche, ray casting su mesh, trovare vertici vicini, analizzare orientamento facce
File: `docs/mathutils.md`

Contenuto: Vector (costruzione, operatori +/-/*/@ dot/cross, .length, .normalized(), .dot(), .cross(), .angle(), .project(), .lerp(), .slerp(), .rotation_difference()), Matrix (Identity/Translation/Rotation/Scale/LocRotScale, matmul @, .decompose(), .to_euler(), .to_quaternion(), .inverted(), .transposed()), Euler (costruzione, .to_matrix(), conversioni, .rotate_axis()), mathutils.geometry (intersect_ray_tri, closest_point_on_tri, intersect_line_line, intersect_point_line, area_tri, normal, distance_point_to_plane, tessellate_polygon), BVHTree (FromMesh/FromObject/FromBMesh/FromPolygons, .ray_cast(), .find_nearest(), .find_nearest_range(), .overlap()), KDTree (costruzione size+insert+balance, .find(), .find_n(), .find_range()). Tabella recap uso/strumento per problemi stampa 3D.

## [utils_units]
**bpy.utils, bpy.utils.units, bpy.app, bl_math, idprop, save_homefile, viewport clipping — conversioni unità e utilities**
Quando usarlo: devi convertire mm↔Blender units, controllare versione Blender, attivare addon, lavorare con custom properties, fare calcoli matematici semplici, salvare impostazioni unità come startup default, correggere scomparsa oggetti nel viewport
File: `docs/utils_units.md`

Contenuto: bpy.utils.units.to_value/to_string (formula critica: 1 BU = 1m, scale_length=0.001 → 1 BU = 1mm), bpy.utils (resource_path, script_paths, blend_paths), addon_utils.enable() per 3D Print Toolbox, bpy.app (version, binary_path, tempdir, handlers), bl_math (clamp, lerp, smoothstep), idprop custom properties (Object["key"]=value, IDPropertyArray, IDPropertyGroup, id_properties_ui()), tabelle enum: modifier types, object types, mesh select modes, attribute domains. **bpy.ops.wm.save_homefile()**: salva lo stato corrente come startup file — usare in CALL_0 dopo configurazione unità per persistere scale_length=0.001 tra sessioni (attenzione: sovrascrive globale Blender). **Viewport Clipping End**: impostare space.clip_end=10000 via loop su screen.areas per evitare che oggetti grandi spariscano dal viewport con scale_length=0.001. **Grid Overlay Scale**: space.overlay.grid_scale=0.001 in CALL_0 — sincronizza la griglia del viewport con scale_length=0.001 (1 cella = 1mm); usare con grid_subdivisions=10 per tacche a 0.1mm; incluso nel snippet CALL_0 completo assieme a clip_end e save_homefile.

## [depsgraph_evaluated]
**Depsgraph: dependency graph, mesh valutata con modifier, DepsgraphObjectInstance**
Quando usarlo: devi ottenere la mesh con tutti i modifier applicati SENZA modificare l'originale, analizzare geometria risultante, iterare su tutte le istanze di scena incluse le dupli
File: `docs/depsgraph_evaluated.md`

Contenuto: differenza original vs evaluated data, 3 modi per ottenere depsgraph (evaluated_depsgraph_get, view_layer.depsgraph, view_layer.update()), pattern obj.evaluated_get(depsgraph) + to_mesh() + to_mesh_clear(), Depsgraph properties (scene_eval, updates, id_type_updated()), DepsgraphObjectInstance (object, matrix_world, is_instance, persistent_id), iterazione object_instances, DepsgraphUpdate (is_updated_transform/geometry/shading), tradeoff evaluated-vs-modifier_apply.

## [orientation_strategy]
**Scelta orientamento ottimale per stampa FDM: scoring, ricerca a griglia, criteri euristici, applicazione rotazione**
Quando usarlo: devi decidere come orientare un modello sul letto, vuoi minimizzare overhang e supporti, devi automatizzare la scelta dell'orientamento via Python
File: `docs/orientation_strategy.md`

Contenuto: principi fisici FDM (anisotropia, overhang 45°, superficie visibile, impronta), 4 metriche di scoring (overhang_area, support_footprint, z_height, bottom_flatness), score_orientation() con BVH+raycast su ogni orientamento, find_best_orientation() a griglia configurable (steps=8→64 campioni), apply_orientation() con transform_apply e Z=0 reset, criteri euristici manuali, caso speciale figurine organiche e teste (inclinazione 10–15° posteriore).

## [support_strategy]
**Decisione supporti FDM: quando servono, tipo (Normal vs Tree), parametri Bambu Studio, Support Painting avanzato**
Quando usarlo: devi decidere se il modello richiede supporti, quale tipo usare, come configurarli in Bambu Studio per PLA su A1, usare Support Painting (Sphere/Fill/Gap Fill) per controllo manuale preciso
File: `docs/support_strategy.md`

Contenuto: detect_overhang_faces() Python con soglia configurabile, decision tree (passo 1: identificare aree critiche, passo 2: valutare orientamento alternativo, passo 3: bridge length check), Normal vs Tree support (pro/contro/quando), tabella parametri Bambu Studio per supporti PLA A1 (threshold angle, top/bottom Z distance, interface layers, interface spacing, density, pattern), configurazione operativa Bambu Studio step-by-step, strategie alternative per overhang non eliminabili (organici, buchi, shelf), stima impatto supporti. **Support Painting avanzato**: tabella Sphere Tool (supporto in raggio 3D — per blocchi rapidi) / Fill Tool (Smart Fill Angle propagation — per aree piatte complesse) / Gap Fill (chiusura isole automatica — sempre usare dopo Sphere); workflow efficiente in 3 step: Sphere → Gap Fill → Fill per ritocchi; strumenti più rapidi per geometria organica complessa.

## [hollowing_and_lightening]
**Svuotamento e alleggerimento mesh: Solidify, Boolean Difference, scelta infill pattern**
Quando usarlo: vuoi ridurre peso/materiale, devi creare una shell da una mesh solida, devi scegliere tra hollowing in Blender e configurazione infill nello slicer
File: `docs/hollowing_and_lightening.md`

Contenuto: quando ha senso svuotare vs usare infill slicer (regola: per FDM non svuotare in Blender — usare infill), apply_solidify_for_print() (thickness mm→BU, offset -1.0 interno, use_even_offset, use_rim), hollow_solid_mesh() con Boolean Difference + cutter invertito + fori di scarico, tabella pattern infill (Grid/Gyroid/Honeycomb/Lightning/Cubic — resistenza/tempo/materiale), densità infill per caso d'uso (10–100%), Wall Count vs Infill Density tradeoff.

## [ai_mesh_recipe]
**Pipeline completa mesh AI-generated → STL FDM: 8 CALL Blender MCP, repair, decimazione, export**
Quando usarlo: hai ricevuto un mesh da generatore AI (TripoSG, Hunyuan3D, Rodin — GLB/OBJ), devi portarlo a STL stampabile su Bambu A1 con pipeline step-by-step eseguibile via execute_blender_code
File: `docs/ai_mesh_recipe.md`

Contenuto: 8-CALL pipeline stateless per Blender MCP (ogni call autonoma, risultati via print()), CALL 1 import GLB/OBJ/STL con scene cleanup, CALL 2 multi-object handling + isole disconnesse + artefatti, CALL 3 scale detection + rescale a TARGET_MM, CALL 4 quality assessment (manifold/dims/faces/normals), CALL 5 repair + decimazione a 150k target (Decimate COLLAPSE + print3d_clean_non_manifold + remove_doubles + fill_holes), CALL 5b Voxel Remesh fallback se manifold non risolvibile (voxel_size formula), CALL 7 smoothing LaplacianSmooth + wall thickness check, CALL 8 STL export (global_scale=1000.0, use_scene_unit=False — parametro critico), tabella profilo Bambu Studio consigliato per tipo di oggetto AI, troubleshooting quick reference. **Sculpt Mode Brush Reference per AI cleanup** (tabella 6 brush: Smooth/Elastic Grab/Inflate/Blob/Crease Sharp/Clay Strips con use cases e workflow tipo 7-step); **Strategie avanzate AI**: (1) generare parti separatamente per più dettaglio, assemblarle in sculpt mode → join → remesh; (2) double-sided mesh da buco → inflate to close → remesh; (3) **Bone heat weighting failure fix**: `remove_doubles(threshold=0.001)` prima di Rigify Automatic Weights — il threshold default 0.0001 è troppo basso per mesh AI dense.

## [photogrammetry_recipe]
**Pipeline mesh fotogrammetria → STL FDM: 8 CALL Blender MCP, background cleanup, decimazione massiva, smoothing aggressivo**
Quando usarlo: hai un mesh da Meshroom/RealityCapture/Polycam/MetaShape (OBJ/PLY) con milioni di poligoni, devi portarlo a STL stampabile differenziando il trattamento da mesh AI
File: `docs/photogrammetry_recipe.md`

Contenuto: 8-CALL pipeline fotogrammetria (CALL 1 import OBJ/PLY con asse Y-up, CALL 2 separazione geometria + rimozione background via separate(LOOSE) + filtraggio isole piccole, CALL 3 diagnosi scala GPS/marker/arbitraria + rescale, CALL 4 decimazione massiva immediata prima del repair — Decimate COLLAPSE o Voxel Remesh per >2M facce, CALL 5 repair fill_holes/remove_doubles/normals + 3D Print Toolbox, CALL 6 LaplacianSmooth aggressivo lambda=1.0–1.5 iter=5–8 + decimazione FDM finale, CALL 7 QA + orientamento + transform_apply, CALL 8 STL export identico AI recipe), tabella formati per software, fallback Voxel Remesh, tabella differenze vs AI recipe, profili Bambu Studio consigliati.

## [error_handling_mcp]
**Error handling per script MCP: bpy.ops silenzioso, try/except, call_precheck(), logging strutturato**
Quando usarlo: devi scrivere script MCP robusti, gestire errori bpy.ops che restituiscono CANCELLED silenziosamente, debuggare fallimenti difficili da diagnosticare, aggiungere logging strutturato a pipeline lunghe
File: `docs/error_handling_mcp.md`

Contenuto: **bpy.ops non solleva eccezioni per errori logici** — restituisce `{'CANCELLED'}` silenziosamente (parametro sbagliato, modifier non applicabile, geometria non valida); pattern `safe_op()` con verifica `'FINISHED' in result`; pattern `op_with_poll()` per check preventivo + logging; **`call_precheck()`** — utility pre-validazione contesto: 7 check (view_layer, active_object, tipo MESH, modalità, scala applicata, hidden, screen/background); **MCPLogger** — classe logging strutturata con timestamp, livelli info/warn/error/step, summary() finale; **tabella errori MCP** con causa, diagnosi rapida e fix (poll() failed, CANCELLED modifier, bm.to_mesh dimenticato, undo forbidden, voxel freeze); template script MCP robusto completo con try/except globale, finally restore mode.

## [camera_verification]
**Viewport e screenshot per QA: posizionamento viste standard, 4-view pattern, overlay wireframe/normali**
Quando usarlo: devi ispezionare un modello sistematicamente prima dell'export, posizionare il viewport su viste standard via Python, catturare screenshot per QA, abilitare overlay wireframe o normali
File: `docs/camera_verification.md`

Contenuto: `get_view3d_area()` — trova area VIEW_3D per temp_override; `bpy.ops.view3d.view_all()` e `view_selected()` via temp_override; `bpy.ops.view3d.view_axis(type=...)` per TOP/FRONT/RIGHT/BACK/BOTTOM; **vista isometrica** via quaternione manuale (q_z @ q_x con 45° azimuth + 35.264° elevation); **`screenshot_4views()`** — salva PNG Top/Front/Right/Iso in cartella; **`setup_qa_view()`** — configura viewport per viste standard + frame oggetto, usare prima di `get_viewport_screenshot` MCP; toggle overlay wireframe (`space.overlay.show_wireframes`); overlay normali (`show_face_normals`, `normals_length`); **checklist QA 6-step** (ISO → TOP → FRONT → RIGHT → ISO+wireframe → ISO+normali); tabella `bpy.ops.screen.screenshot` vs `get_viewport_screenshot` MCP.

## [fbx_import_guide]
**FBX Import da generatori AI: parametri bpy.ops.import_scene.fbx, scala, asse up, normali, mesh multipli**
Quando usarlo: hai ricevuto un FBX da un generatore AI (Rodin, HunyuanVideo, Meshy) e devi importarlo in Blender, hai problemi di scala, asse ruotato, normali corrotte, armatura embedded, mesh separate
File: `docs/fbx_import_guide.md`

Contenuto: firma completa `bpy.ops.import_scene.fbx()` con tutti i parametri (global_scale, use_manual_orientation, axis_forward/up, use_custom_normals, use_anim, ignore_leaf_bones); **Problema 1 Scala cm** (diagnostica via obj.dimensions in mm; fix reimport con global_scale=0.01 o scala post-import ×0.01); **Problema 2 Asse up** (Y-up AI vs Z-up Blender → use_manual_orientation=True + axis_up='Y'; fix post-import rotation_euler.x = -90°); **Problema 3 Normali custom corrotte** (use_custom_normals=False + customdata_custom_splitnormals_clear() dopo import); **Problema 4 Mesh multipli** (`collect_fbx_meshes()` — identifica e join di tutte le MESH); **Problema 5 Armatura embedded** (`remove_armatures()` e `remove_modifiers_armature()`); **CALL_1 FBX AI completo** — script di import + fix automatici (asse Y-up, no custom normals, no anim, join mesh, remove armature, fix normali, apply transforms, auto-correzione scala vs EXPECTED_SIZE_MM); **tabella comportamento generatori AI** (Rodin/HunyuanVideo/Meshy/CSM — unità, asse up, normali, struttura); confronto FBX vs STL per workflow stampa 3D.

## [boolean_troubleshooting]
**Diagnosi e recovery di Boolean EXACT falliti: cause, sanitize pre-boolean, retry automatico, fallback bmesh**
Quando usarlo: un Boolean ha prodotto mesh non-manifold o flipped, una operazione UNION/DIFFERENCE restituisce CANCELLED, stai per fare boolean su mesh AI con self-intersection, devi implementare retry/recovery automatico
File: `docs/boolean_troubleshooting.md`

Contenuto: **5 cause reali di fallimento EXACT**: (1) scale non applicata → transform_apply prima; (2) coplanarità cutter/base → margine ±0.001mm; (3) non-manifold su uno degli operandi → sanitize completo; (4) zero-area faces → dissolve_degenerate; (5) FAST solver su self-intersection → switch EXACT. **`sanitize_for_boolean()`** idempotente 6-step (apply_scale, loose geom, merge_doubles, dissolve_degenerate, holes_fill, recalc_normals) con report dict. Tabella ammissibilità per EXACT. **`verify_boolean_result()`** post-boolean (non_manifold/boundary/wire/zero_area/volume). **`safe_boolean()`** wrapper con 3 retry escalation (plain → use_self=True → offset cutter). Fallback `bmesh_boolean_difference()` via bmesh.ops.intersect + BVH inside-test (O(n·m), solo se EXACT esaurito). Casi patologici specifici: flatten-bottom a Z=0 coplanare, fori a griglia multi-cutter, UNION mesh AI con self-intersection (Voxel Remesh pre-union), DIFFERENCE parziale, mesh con shape keys. Tabella parametri modifier Boolean 5.1 (use_self, use_hole_tolerant) + pattern preferito per mesh AI. Log consigliato per ogni operazione.

## [measurement_toolkit]
**API unificata di misura: distance, bbox (AABB/OBB), thickness (raycast), volume, mass, CoM, area, cross-section, diameter foro, angoli**
Quando usarlo: devi rispondere a "quanto spesso è qui?", "che volume ha?", "quanto dista X da Y?", "l'asse è allineato?"; devi auto-diagnosticare mesh con metriche quantitative; devi validare feature FDM (parete min, diametro foro)
File: `docs/measurement_toolkit.md`

Contenuto: 12 categorie di misura con costo computazionale. Tutte le funzioni ritornano mm (non BU) e stampano log strutturato. **Distanze**: closest_distance_mm (BVH), bbox_world_mm (AABB), bbox_local_mm (obj.dimensions), obb_mm (PCA su vertici con numpy). **Wall thickness**: wall_thickness_at_point (raycast singolo), wall_thickness_distribution (sampling N facce, ritorna min/p10/p50/p90/max), interpretazione FDM con soglie (p10<0.4mm non stampabile, <0.8mm sotto 2 perimetri, ≥0.8mm OK). **Volume/area/mass**: volume_mm3 (bm.calc_volume + check closed), surface_area_mm2, estimate_pla_mass_g (shell+infill×density 1.24 g/cm³). **Center of mass**: center_of_volume_mm (tetra integration esatto), center_of_bbox_mm (fallback). **Cross-section**: bmesh.ops.bisect_plane + edgenet_fill per area su piano. **Hole detection**: detect_circular_holes via coefficient of variation sul raggio delle n-gon (limitazione: richiede mesh non-triangolata). **Angoli**: dihedral_angle_deg, tilt_from_z_deg. **Report sintetico**: `measure_object_full()` unica CALL con tutte le metriche pertinenti FDM. Caveat numerici float32, shape keys, modifier non applicati.

## [object_placement]
**Posizionamento e allineamento: snap-to-bed, centering, align tra oggetti, origin_set, 3D cursor, stacking, packing**
Quando usarlo: l'utente chiede "centralo sul letto", "allinea i fondi", "mettilo accanto", "pila questi pezzi", "pivot al centro di massa"; devi automatizzare il layout multi-oggetto sul build plate
File: `docs/object_placement_alignment.md`

Contenuto: **Convenzione coord** Blender (origine arbitraria) vs Bambu Studio bed (centro 128,128,0 o angolo) — regola esportabile: (bbox_center_x, bbox_center_y)=(0,0) e bbox_min_z=0. **4 modalità origin_set**: ORIGIN_GEOMETRY (default), ORIGIN_CENTER_OF_MASS (vertex-weighted), ORIGIN_CENTER_OF_VOLUME (per stabilità FDM), ORIGIN_CURSOR (pivot custom); variant center='BOUNDS' vs 'MEDIAN'. **snap_to_bed(obj)** (transform-apply-free, vertice-preciso) e variant snap_to_bed_fast (bound_box, 8 corner). **center_on_bed**, **center_xy_and_snap_bed** (convenzione export). **align_object_to(moving, ref, axis, mode=MIN/MAX/CENTER)** per allineare bbox su un asse. **place_adjacent** per edge-to-edge con gap_mm. **stack_vertically** per pila con gap. **3D cursor**: cursor_to(x,y,z), cursor_to_object, cursor_to_world_origin, cursor_to_selected_avg; use case primitive_add(location=cursor). **pack_on_bed** algoritmo shelf packing FFDH (non ottimale ma funzionale). Pattern MCP completo "centra sul letto". Tabella quick reference 10 richieste utente → funzione.

## [bisect_splitting]
**Cutting planare, angolato, puzzle cut con registration pin, split in N pezzi, cross-section, color change marker**
Quando usarlo: modello >256mm va diviso in N pezzi, vuoi taglio a 45° per rimuovere overhang, devi creare registration features per riassemblaggio, vuoi estrarre una silhouette 2D, vuoi marker per pause G-code
File: `docs/bisect_and_splitting.md`

Contenuto: **bisect_plane vs Boolean** (tabella: O(n) vs O(n·m), preservazione UV, output multi-pezzo, fill). **bisect_object(obj, plane_co_mm, plane_no, keep='POS'|'NEG'|'BOTH', fill_cut=True)** via bmesh.ops.bisect_plane + edgenet_fill su geom_cut; duplica prima (MCP-safe). **split_two_halves** e **split_n_horizontal** per suddivisione verticale. **cut_at_angle** piano inclinato attorno a X o Y. **split_with_registration_pins**: cut + UNION di N cilindri maschi su BOTTOM + DIFFERENCE di N fori femmina su TOP con clearance 0.10mm; default 2 pin asimmetrici Ø4mm; tabella alternative (cilindro/cono/dovetail/key/offset asimmetrico). **Color change marker** via custom property color_changes_mm (no split fisico — delegato al slicer). **extract_cross_section**: bisect + fill + Solidify per silhouette 2D stampabile. Tabella failure mode (buco non riempito, normali flipped, pin overhang, clearance stretta, n-gon non triangolato). Quick reference richieste utente.

## [preprint_validation]
**Validatore unificato pre-export STL: decisione go/no-go, metriche strutturate, report issue con severità**
Quando usarlo: ultima CALL prima di wm.stl_export, devi prendere una decisione binaria "esporto o no", vuoi un report JSON-serializzabile con tutte le metriche, devi bloccare l'export se il modello non è stampabile
File: `docs/preprint_validation.md`

Contenuto: **10 categorie** validazione (scene_setup, transforms, manifold, bounds, min_feature, orientation, overhangs, poly_count, normals, multi_object) con severità max. Matrice THRESHOLDS completa (scale_length=0.001, bed 256mm, nozzle 0.4mm, wall_min 0.8mm, overhang_angle 45°, overhang_pct_warn 15% / fail 40%, poly_max_warn 500k / fail 1.5M, flipped_normals_max 1%). **`validate_for_print(obj)`** core: scene unit check, scale+shear check, manifold (non-manifold/boundary/wire/zero_area/duplicati via KDTree), bounds vs A1, smallest_dim, Z_min tolerance, XY offset, overhang % via normali + angle con -Z, poly count, flipped normals via raycast sampled, multi-object scene check; ritorna dict con decision ∈ {PASS,WARN,FAIL} + issues[] + metrics. **`validate_and_maybe_export(obj, stl_path, allow_warn)`** integrato con wm.stl_export(global_scale=1000, use_scene_unit=False). Tabella verdetti per scenario tipico. Serializzazione JSON del report. Estensioni opzionali: thickness distribution (usa [measurement_toolkit]), mass/cost estimate. Regola MCP: FAIL → blocco + mostra fix suggerito; WARN → chiedi approvazione. Checklist pre-commit della pipeline.

## [workflow_patterns]
**Combinazioni di operazioni per stampa 3D: import+repair+export, boolean, solidify, scale, split, QA pipeline, regole critiche boolean**
Quando usarlo: devi capire come combinare più operazioni per un obiettivo specifico (importare e riparare, fare un foro, appiattire la base, aggiungere spessore, verificare dimensioni, dividere modello oversized, eseguire QA completo), cerchi esempi di codice funzionante, vuoi le regole di sicurezza per boolean
File: `docs/workflow_patterns.md`

Contenuto: 8 combinazioni descritte con effetti e condizioni di applicabilità: Import STL+Repair+Export, Scale (origin_set+formula BU+transform_apply), Boolean UNION (multi-body assemblies, EXACT solver), Boolean DIFFERENCE (cutter passante, conversione BU), Solidify (semantica offset, 1.2mm=3 pareti), Analisi dimensionale (obj.dimensions vs 256mm), **Split modello oversized** (cutter cubico Boolean DIFFERENCE per due metà + registration pin maschio 4mm su parte A + foro femmina clearance 0.10mm su parte B + STL export separato per metà), **QA Pipeline automatizzata** (run_qa_pipeline() — 7 check in sequenza: unità/dimensioni/manifold/poly count/normali/transforms/base Z, report testuale strutturato con ✓/⚠/✗, errori critici vs avvisi), **Regole critiche Boolean** (Regola 1 — coplanarità vietata: facce cutter mai a filo con mesh base, margine minimo 1mm, fori passanti devono emergere da entrambi i lati; Regola 2 — flatten-bottom: cutter cubo largo DIFFERENCE per base perfettamente piatta a Z=0, codice completo; **Regola 3 — scala-prima-boolean: apply_scale_safe() su base E cutter prima di ogni Boolean — scala non applicata causa boolean silenziosamente errato o fallito**), **Solidify come tolleranza FDM parametrica** (use_rim_only=True + use_even_offset=True su cutter per compensare over-extrusion stampante; offset=1 espande foro, offset=-1 contrae perno; TOLERANCE_MM configurabile, vertex group per Solidify selettivo solo sul filetto). Checklist pre-export.

## [bambu_a1_physical_constants]
**Costanti fisiche deterministiche Bambu Lab A1: passo Z 0.04mm, larghezza linea 0.42mm, keep-out zones, tolleranze accoppiamento, volumetria, accelerazione**
Quando usarlo: devi progettare parti funzionali dimensionalmente precise per Bambu A1 (hinge, press-fit, cerniere), scegliere layer height meccanicamente valido, evitare collisioni con cutter/probing, calibrare accelerazione per oggetti alti, capire perché Bambu Studio usa 0.42mm di default
File: `docs/bambu_a1_physical_constants.md`

Contenuto: **Asse Z** — passo fisico 0.04mm (lead vite 8mm / 200 step NEMA 17 a 1.8°), layer validi 0.08/0.12/0.16/0.20/0.24/0.28 come multipli interi, range lithophane 0.08–0.12mm, microstepping degrada coppia/precisione. **Nozzle 0.4mm geometria** — line_width 0.42 default per die swell+squish positivo → adesione inter-linea, range valido 0.30–0.60mm, regola "spessore CAD = multiplo line_width" per evitare gap fill. **Coordinate mondo** — origine angolo anteriore-sinistro (non centro). **Keep-out zones**: cutter zone X<18 Y<28 mm (meccanismo taglio filamento), probing point (X=128, Y=261) sensore eddy, rear clearance 140mm cavo, front 101mm, height 250mm; funzione `is_in_cutter_zone`. **Tolleranze PLA nozzle 0.4**: friction fit 0.10, slide 0.20, loose 0.30, press 0.05–0.08; compensazione fori +0.10mm (XY hole comp). **Overhang thresholds** vs angolo/sovrapposizione, trick line_width 0.6mm + layer 0.12mm per overhang critici. **Dinamica**: acc max 10000 mm/s² con scaling per altezza (10k→6k→4k→2k per 50/100/150 mm), flow max 28 mm³/s operativo 17–20 (60–70%), pressure advance auto con test forza. **Termica**: PLA 200–230°C, regola T≈200+0.005×v, cooling closed loop, minimum layer time 4–8s. **Ritiro materiali**: PLA 0.2–0.3%, PETG 0.5%, TPU variabile 1–2%. **8 costanti da ricordare** elencate in sintesi.

## [api_migration_5x]
**Blender 4.5 → 5.1 migrazione API: wm.stl_import nativo, solver Manifold/Float rename, geom_cut bisect, 3MF extension, GP 3.0 breaking, VSE rename, brush.stroke_method, custom splitnormals**
Quando usarlo: stai scrivendo script MCP che devono funzionare su Blender 5.1, hai script legacy da aggiornare, devi usare operatori nativi C++ al posto di add-on Python deprecati, devi capire lo stato di use_hole_tolerant e il nuovo solver Manifold
File: `docs/api_migration_5x.md`

Contenuto: **C++20 core**: Apple Silicon/x86_64 only, perf +10–30% GPU/CPU/undo, data-block name 255 byte, compressione .blend default. **STL**: `bpy.ops.import_mesh.stl` DEPRECATO → usare `bpy.ops.wm.stl_import` (nativo C++, ~12ms vs 80–120ms Python, risolve TypeError su `files` RNA, endianness bug, crash non-manifold). **SVG**: logica migrata a workflow GP3 fills. **3MF**: estensione ibrida `threemf-io` come Core Extension (non built-in, richiede `addon_utils.enable`), aggiornamenti disaccoppiati, face sets→triangle sets, slicer profile metadata stash, PBR Principled BSDF. **BMesh bisect_plane**: chiavi dict chiarite — `geom_cut` = solo nuovi verts+edges sul taglio (per cap), `geom` = tutta geometria influenzata; pattern edgeloop_fill. **Boolean**: rename FAST→FLOAT (alias deprecato), nuovo solver MANIFOLD per solidi chiusi (velocità max), use_hole_tolerant ESISTE ancora ma esclusivo di EXACT, default False. **Custom split normals**: `customdata_custom_splitnormals_clear()` disponibile ma deprecato come pattern primario → preferire modifier "Smooth by Angle" (attributi float per face/loop). **Grease Pencil 3.0**: rewrite completo, script GP2 NON funzionano, data structure=geometry nodes, material both stroke+fill, true holes, 10× performance stroke lunghi. **VSE rename**: frame_final_start→start, frame_final_duration→duration, frame_start→content_start (alias fino 6.0). **Brush**: use_airbrush/anchor/space/line/curve unificati in enum stroke_method; sculpt.sample_color rimosso → paint.sample_color. **UI**: UILayout.template_list(columns=) RIMOSSO; nuovo template_ID_session_uid per tracking data-block rinominati. **macOS**: accesso camera/mic/audio nativo. **Checklist migrazione** 10 punti per ogni script legacy.

## [cad_import_workflow]
**Workflow CAD e 3MF multi-materiale: import STEP/IGES via Mayo, Plasticity bridge, gerarchie assieme GLTF, 3MF Bambu Studio, T-junction/self-intersection detection, NumPy foreach_get/set, lattice LSTO, bin-packing 2D**
Quando usarlo: devi importare file B-Rep (STEP/IGES) da SolidWorks/Fusion360, esportare 3MF multi-materiale per AMS Bambu, riparare T-junction o auto-intersezioni post-import, vettorizzare operazioni su mesh grandi, generare lattici per alleggerimento, packare parti piatte su fogli per CNC/laser
File: `docs/cad_import_workflow.md`

Contenuto: **Import B-Rep**: add-on "Import CAD Model" basato su Mayo/OpenCascade per STEP/IGES/STP/IGS (parametri tassellazione Very Coarse→Very Precise), workflow FreeCAD→GLTF (preferibile a OBJ per gerarchie parent-child e nomi componenti), SimLab Soft plugin commerciale (Y-up→Z-up auto), **Plasticity bridge** con refacet N-gons per retopologia automatica. **Correzione post-import**: scala 1000×/0.001×, Y-up, fillet shading, normal flipped, gerarchie perse. **3MF multi-materiale**: extension threemf-io (setup via addon_utils.enable), mapping Blender→3MF (material slot→extruder index AMS, sculpt face set→triangle set, linked duplicate→shared component), API `bpy.ops.export_mesh.threemf(filepath, use_selection, global_scale=1.0, use_mesh_modifiers=True, coordinate_precision=6)`, workflow Bambu/Orca, fix "oggetti compressi sul piatto" (Ctrl+A Apply Transforms / parenting / join). **Automazione Gridfinity**: wrap parametrico `export_gridfinity(w,d,h)`. **Riparazione mesh CAD**: **T-junction detection** via KDTree+prossimità vertex-edge (epsilon 1e-5), fix con edge_split+weld_verts; **self-intersection** via BVHTree.overlap, strategie riparazione (bmesh.ops.intersect use_self, Boolean Union self-only, Voxel Remesh nuclear). **Volume-preserving smoothing**: LaplacianSmooth contrae 91.3% a 100 iter, preferire CorrectiveSmooth SIMPLE+bind_mode o Laplacian con use_volume_preserve=True, iterazioni ≤5 lambda≤0.5 per mesh CAD. **Vettorizzazione NumPy**: benchmark 25M vertici loop Python >100s vs foreach_get+NumPy ~1s (60× speedup), pattern canonico foreach_get/set con reshape/ravel. **LSTO**: SIMP formula E(ρ)=ρᵖE₀, export inp per CalculiX/OpenFOAM, Geometry Nodes DistributePointsOnFaces+InstanceOnPoints per lattici Voronoi. **G-code injection**: temp tower via regex su Z, M104 step per layer. **Bin-packing 2D**: rectpack library, algoritmi Skyline/Guillotine/MaxRects, integrazione con obj.dimensions per layout CNC/laser.

## [mechanical_algorithms]
**Algoritmi di ingegneria meccanica: ingranaggi ad evolvente (math nativo), ISO 286 tolleranze, escalation Boolean, wall thickness raycast/medial axis, calc_volume/center of mass, OBB rotating calipers, custom data layer BMesh**
Quando usarlo: devi generare ingranaggi proceduralmente con profilo corretto, applicare tolleranze ISO 286 programmaticamente, implementare Boolean robusti con fallback automatico, calcolare massa/centro di massa/OBB per simulazione fisica, misurare spessore parete, attaccare metadati meccanici alla geometria
File: `docs/mechanical_algorithms.md`

Contenuto: **Ingranaggi evolvente ISO 53**: teoria perché evolvente (rapporto velocità costante su variazioni interasse), tabella parametri (modulo m, pressure angle 20°, addendum 1.00m, dedendum 1.25m, rp=mZ/2, rb=rp·cos(α)), parametrizzazione x(t)=rb·(cos t + t·sin t) / y(t)=rb·(sin t - t·cos t), scheletro implementazione `generate_involute_gear(n_teeth, module, pressure_angle, width, samples)` con math nativo (no NumPy), gestione sottotaglio per Z<17 (linea radiale / curva trocoidale / profile shift). **Boolean escalation pattern**: `robust_boolean(base, cutter, op)` — tenta FLOAT → EXACT → EXACT+hole_tolerant → jitter geometrico ε=1e-6; validazione post-op via `_volume_sanity_check` (volume>0, non NaN); tabella solver aggiornata FLOAT/EXACT/MANIFOLD. **Wall thickness**: raycasting con BVHTree normal-inverted + epsilon offset (limite angoli acuti → cono stocastico 10°), Asse Mediale teorico (pro/contro, non implementato nativo, usare CGAL/subprocess). **Physical properties BMesh**: `compute_volume_mm3` con `calc_volume(signed=False)` + matrix_world, conversione BU→mm via scene_unit_scale, pitfall normali invertite (volume negativo); `compute_mass_grams` con tabella densità PLA 1.24 / PETG 1.27 / ABS 1.04 / TPU 1.21 / PA-CF 1.10; **`center_of_mass`** via somma pesata centroidi tetraedri (fan triangulation + v_tet = a·(b×c)/6). **OBB Rotating Calipers**: teorema Freeman-Shapira (lato collineare a edge hull), complessità 2D O(n) / 3D O(n³) O'Rourke; implementazione pratica `compute_obb_via_convex_hull(obj)` con proiezione vertici su frame locale di ogni hull face, minimizzazione volume; tabella metodi AABB/PCA/Calipers/O'Rourke. **ISO 286**: codifica H7/g6, tabella deviazione fondamentale (h/g/f/e zero/negative, k/m/p positive), tabella IT6/IT7/IT8/IT9 per range 1–80mm, `iso286_offset_shaft(obj, nominal_d, letter, grade)` con foreach_get/set e delta_radius = (fundamental_dev + IT/2)/1000 mm; pitfall normali mediate su spigoli vivi → usare MeshLoop.normal o Solidify use_even_offset; nota FDM ±100μm vs ISO ±10μm CNC → vedere bambu_a1_physical_constants per fits FDM. **BMesh custom data layers**: edge.layers.crease / vert.layers.deform / face.layers.int / face.layers.string per metadati meccanici, pattern `tag_load_zones` per export FEM. **Best practice BMesh**: try/finally con bm.free() obbligatorio tra CALL MCP, remove_doubles prima di to_mesh, selezione coerente verts+edges+faces.
