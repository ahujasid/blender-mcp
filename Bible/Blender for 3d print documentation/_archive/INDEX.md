# Archived Topics — Out of Scope for STL Print-Prep Workflow

Questi topic sono stati spostati dalla KB attiva perché fuori scope per il
workflow corrente (importa STL AI-generato → pulisci → esporta per FDM). Non
vengono caricati da `kb_list_topics` o `kb_search` di default — usa
`include_archived=True` se ti servono per casi una tantum.

Motivo dell'archiviazione: ognuno di questi topic riguarda **modellazione da
zero** (parametric design, gear, hinge, lithophane, SVG, geometry nodes,
sculpting texture) o **rigging** (shape keys, vertex group come weight mask)
che non sono parte della pipeline cleanup di mesh esistenti.

I file sono ancora qui in `_archive/docs/` se servono come reference.

## [texture_displacement]
**Texture procedurali e DisplaceModifier**
File: `_archive/docs/texture_displacement.md`
Motivo archive: surface detail / sculpting, non per cleanup di STL AI.

## [geometry_nodes]
**Geometry Nodes per modellazione procedurale**
File: `_archive/docs/geometry_nodes.md`
Motivo archive: modellazione parametrica from-scratch, non per cleanup.

## [shapekey_vertexgroup]
**ShapeKey, VertexGroup — deformazioni e maschere modifier**
File: `_archive/docs/shapekey_vertexgroup.md`
Motivo archive: rigging/animazione, irrilevante per FDM.

## [curve_and_text]
**Curve Objects e Text Geometry: tubi parametrici, testo 3D**
File: `_archive/docs/curve_and_text.md`
Motivo archive: creazione da zero, non cleanup.

## [parametric_design_patterns]
**Box, bracket, piastra fori, gusset, chamfer FDM da zero**
File: `_archive/docs/parametric_design_patterns.md`
Motivo archive: design from-scratch.

## [image_to_mesh]
**Lithophane, heightmap, SVG→3D**
File: `_archive/docs/image_to_mesh_recipes.md`
Motivo archive: input 2D → mesh, pipeline indipendente dal workflow STL cleanup.

## [functional_patterns]
**Spur gear, pin hinge, box with lid, knob, cable clip da zero**
File: `_archive/docs/functional_patterns_library.md`
Motivo archive: estensione di parametric_design_patterns, design from-scratch.
