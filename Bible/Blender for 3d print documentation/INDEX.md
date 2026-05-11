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

## [texture_displacement]
**Texture procedurali e DisplaceModifier: Clouds, Voronoi, Musgrave, Marble, Wood, Image + surface detail + Sculpt+Stencil**
Quando usarlo: vuoi aggiungere dettaglio superficiale a una mesh (buccia d'arancia, texture organica, rugosità, pattern), usare DisplaceModifier con texture procedurale o immagine, oppure applicare texture interattiva via Sculpt Mode con stencil
File: `docs/texture_displacement.md`

Contenuto: bpy.types.Texture (base class, proprietà comuni, evaluate()), 8 tipi di texture (CloudsTexture/NoiseTexture/VoronoiTexture/MarbleTexture/WoodTexture/StucciTexture/MusgraveTexture/ImageTexture) con parametri chiave per effetti stampa 3D, tabella noise_basis (9 algoritmi), DisplaceModifier (strength, mid_level, texture_coords, direction, space), bpy.types.Image (load/access/pixels), creazione texture via bpy.data.textures.new(), tradeoff procedurale vs immagine, requisiti densità mesh. **Sculpt Mode + Multi-Resolution + Stencil**: pipeline interattiva alternativa (Sculpt Mode → Multi-Resolution modifier 5 livelli → pennello Stencil con immagine overlay → Front Faces Only + Constant falloff) per texture mattoni/roccia/organica; codice Python per setup Multi-Res via script; nota: scultura stencil non automatizzabile via MCP, richiede interazione manuale.

## [geometry_nodes]
**Geometry Nodes: NodeTree, GeometryNodeTree, Node, NodeSocket, NodeLink — modellazione procedurale**
Quando usarlo: devi fare modellazione procedurale non-distruttiva (distribuire elementi, ripetere pattern, operazioni parametriche), configurare un setup GeoNodes via Python
File: `docs/geometry_nodes.md`

Contenuto: Architettura a 2 livelli (modifier NODES + NodeTree), GeometryNodeTree vs NodeTree, bpy.types.Node (bl_idname, inputs/outputs, default_value), NodeSocket (tipi, default_value, is_linked), NodeLinks.new(from_socket, to_socket), NodeGroupInput/Output, 15+ bl_idname per nodi GeoNodes rilevanti alla stampa (MeshBoolean, SubdivisionSurface, SetPosition, JoinGeometry, DistributePointsOnFaces, InstanceOnPoints, RealizeInstances, ecc.), accesso a input modifier via mod["Input_X"], tradeoff GeoNodes vs bmesh vs modifier.

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

## [shapekey_vertexgroup]
**ShapeKey, Key, VertexGroup — deformazioni vertex e maschere per modifier**
Quando usarlo: devi usare vertex groups come maschera di peso per modifier (es. Displace solo su alcune facce), gestire shape keys per deformazioni parametriche
File: `docs/shapekey_vertexgroup.md`

Contenuto: VertexGroup (name, index, add/remove/weight get/set), VertexGroups collection (new/remove/active), VertexGroupElement (group/weight), come usare vertex groups come maschera nei modifier (vertex_group property), ShapeKey (name, value 0-1, data/co per ogni vertice, relative_key), Key (use_relative, reference_key, key_blocks), creazione shape key via obj.shape_key_add(), applicazione shape key permanente via mesh data.

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

## [curve_and_text]
**Curve Objects e Text Geometry: pipe/tube parametrici, testo 3D, bevel, extrude, conversione a mesh**
Quando usarlo: devi creare tubi/cavi/pipe via Curve, aggiungere testo 3D emboss/deboss, creare profili estrusi, convertire curve in mesh per export STL
File: `docs/curve_and_text.md`

Contenuto: `bpy.data.curves.new(type='CURVE'/'FONT')`, dimensioni 2D/3D; **Spline Bezier** (bezier_points, handle_left/right/type AUTO/VECTOR/FREE, use_cyclic_u); **Spline POLY** (points con co Vector4 w=1, segmenti retti, loops chiusi); **bevel_depth** (raggio circolare in BU → FDM minimo 0.4mm=0.0004BU, pratico ≥0.8mm; `bevel_resolution` 4=ottogono/12=liscio; `use_fill_caps=True` chiude estremità); **bevel con profilo custom** (bevel_mode='OBJECT', curva 2D come profilo); **extrude** su curve 2D (extrude, offset, fill_mode); **bpy.types.TextCurve** (body, size, extrude, offset, align_x/y, space_character/word/line); font loading via `bpy.data.fonts.load()`; **conversione obbligatoria a mesh** (`bpy.ops.object.convert(target='MESH')` + transform_apply) prima di export STL; **Pattern FDM**: testo emboss su base (size ≥4mm, extrude 0.6–1.2mm), tubo parametrico `create_tube()` con path points; **tabella limiti FDM** (altezza testo min 4mm, emboss min 0.4mm, raggio bevel min 0.4mm, note die swell offset=-0.0001 per testo ≤6mm).

## [parametric_design_patterns]
**Pattern design parametrico from-scratch: box/enclosure, bracket, piastra fori, gusset, chamfer/fillet**
Quando usarlo: devi progettare geometria stampabile da zero via Python (non modificare mesh esistenti), creare contenitori/case, mensole a L, piastre di montaggio, nervature di rinforzo, chamfer FDM
File: `docs/parametric_design_patterns.md`

Contenuto: utility `mm()` e `new_mesh_obj()` e `apply_all_transforms()`; **Pattern 1 Box Enclosure** parametrico (width/depth/height/wall_mm, open_top, Solidify modifier per shell + rimozione faccia top via normale Z); **Pattern 2 L-Bracket** (flange orizzontale + parete verticale + gusset triangolare, stampa verticale per massima resistenza a flessione); **Pattern 3 Piastra con fori** in griglia (hole_diameter_mm regola FDM: nominale+0.4mm; fori via Boolean DIFFERENCE con cilindro; M3=3.4mm, M4=4.4mm); **Pattern 4 Gusset/Rib** triangolare parametrico (axis X/Y, width/height/depth mm); **Pattern 5 Chamfer** via Bevel modifier (width_mm, segments=1 chamfer / 3-5 fillet; limit_method ANGLE; regola anti-elephant-foot 0.4–0.5mm); **SubSurf fillet** approssimato (crease + livello 2); **tabella regole FDM design parametrico** (spessore parete min 0.8mm/raccomandato 2.4mm; boss vite 2.5–3× diametro; foro M3 inserto 4.0mm; overhang <40°; bridge <25mm).

## [fbx_import_guide]
**FBX Import da generatori AI: parametri bpy.ops.import_scene.fbx, scala, asse up, normali, mesh multipli**
Quando usarlo: hai ricevuto un FBX da un generatore AI (Rodin, HunyuanVideo, Meshy) e devi importarlo in Blender, hai problemi di scala, asse ruotato, normali corrotte, armatura embedded, mesh separate
File: `docs/fbx_import_guide.md`

Contenuto: firma completa `bpy.ops.import_scene.fbx()` con tutti i parametri (global_scale, use_manual_orientation, axis_forward/up, use_custom_normals, use_anim, ignore_leaf_bones); **Problema 1 Scala cm** (diagnostica via obj.dimensions in mm; fix reimport con global_scale=0.01 o scala post-import ×0.01); **Problema 2 Asse up** (Y-up AI vs Z-up Blender → use_manual_orientation=True + axis_up='Y'; fix post-import rotation_euler.x = -90°); **Problema 3 Normali custom corrotte** (use_custom_normals=False + customdata_custom_splitnormals_clear() dopo import); **Problema 4 Mesh multipli** (`collect_fbx_meshes()` — identifica e join di tutte le MESH); **Problema 5 Armatura embedded** (`remove_armatures()` e `remove_modifiers_armature()`); **CALL_1 FBX AI completo** — script di import + fix automatici (asse Y-up, no custom normals, no anim, join mesh, remove armature, fix normali, apply transforms, auto-correzione scala vs EXPECTED_SIZE_MM); **tabella comportamento generatori AI** (Rodin/HunyuanVideo/Meshy/CSM — unità, asse up, normali, struttura); confronto FBX vs STL per workflow stampa 3D.

## [image_to_mesh]
**Pipeline input 2D → mesh FDM: lithophane, heightmap terrain, SVG-to-3D (logo/keychain/badge)**
Quando usarlo: l'utente fornisce un'immagine raster (JPG/PNG grayscale) o un vettoriale SVG e vuole ottenere un STL stampabile — casi tipici: lithophane retro-illuminata, heightmap topografica, logo estruso con foro keyring
File: `docs/image_to_mesh_recipes.md`

Contenuto: 4 pipeline complete. (1) **Lithophane**: piano subdiviso + Displace(UV, mid_level=1, strength negativo per inversione) + Solidify back_plate, regole FDM (back 0.8mm, max 3.2mm, layer 0.08–0.12mm, 100% infill, stampa verticale); codice CALL completo con parametri WIDTH_MM/HEIGHT_MM/BACK_THICK/MAX_THICK/SUBDIV_RES/INVERT. (2) **Heightmap terrain**: simile ma mid_level=0 con LaplacianSmooth post. (3) **SVG→3D**: `bpy.ops.wm.svg_import` nativo Blender 5.1 (con fallback a io_curve_svg addon), join curve, rescale al TARGET_WIDTH_MM, `curve.dimensions='2D'` + `fill_mode='BOTH'`, convert to mesh, Solidify, foro keyring con Boolean DIFFERENCE + regola margine anti-coplanarità; tabella trade-off SVG e regole FDM per estrusioni (stroke min 0.8mm, extrusion min 0.6mm). (4) Quick reference input 2D con pipeline di riferimento.

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

## [functional_patterns]
**Libreria oggetti funzionali parametrici: spur gear, pin hinge, box with lid friction-fit, knurled knob, cable clip**
Quando usarlo: l'utente chiede di progettare da zero un ingranaggio, una cerniera, una scatola con coperchio, una manopola, una clip — estensione della libreria base di [parametric_design_patterns]
File: `docs/functional_patterns_library.md`

Contenuto: **Spur gear**: teoria modulo m/N teeth/addendum/dedendum/pressure_angle 20°, denti trapezoidali (approssimazione, non involute), regole stampabilità FDM (m≥1.5mm, N≥10); `create_spur_gear(module_mm, n_teeth, thickness_mm, bore_diameter_mm)` via bmesh con 4 punti per dente + extrude + Boolean bore; tabella quick ref per applicazione (toys/mechanism/torque/heavy); nota accoppiamento (stesso modulo, center_distance=(D1+D2)/2 + 0.3–0.5mm clearance); caveat per true-involute (usare FreeCAD plugin). **Pin hinge**: topologia knuckles alternati + pin commerciale Ø3mm, parametri (knuckle_od=pin+2×wall 1.5mm, bore=pin+0.4mm clearance, n_knuckles dispari, gap 0.2mm); `create_pin_hinge()` con loop per half_idx, UNION knuckle esterno + DIFFERENCE pin bore; note orientamento stampa (halves piatti sul bed, Tree support sotto knuckles). **Box with lid**: estensione di Box Enclosure con lid+lip friction-fit; parametri (lip_height 4–6mm, clearance 0.20–0.35mm); `create_box_with_lid()` con Boolean hollow + lid UNION con lip; tabella clearance/fit (press/friction/slip). **Knurled knob**: cilindro + shaft bore + N flute radiali (cilindri piccoli a flute_orbit_radius=D/2) + Bevel chamfer top; varianti D-shaft/set-screw/hexagonal. **Cable clip**: anello a C con apertura snap-fit, DIFFERENCE inner cylinder + DIFFERENCE gap cube. Quick reference richieste utente → pattern.

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
