# AI Mesh Generators — Field Kit (2024–2026)

Quick-reference per generatore: come riconoscerlo dall'output, quali parametri di import usare, quale playbook di repair attivare. Estende [source_mesh_characteristics] con focus operativo.

**Pattern universali** (validi per il 95% degli STL/GLB ricevuti):
1. **Y-up GLB** (spec glTF). Blender è Z-up → rotate `-90°` su X all'import o `axis_up='Y'` in `import_scene.gltf`.
2. **Unit-cube normalization**: bounding box ≈ 1.0 BU. Stampa direttamente = 1mm. Rescale 25–100× tipico per target reale (vedi [scale_detection]).
3. **Marching Cubes seam artifacts**: ogni pipeline SDF→MC (TripoSG, Hunyuan3D, TRELLIS, Zero123-SDS) produce staircase deterministico su sfere/superfici curve e tiny floaters dentro/fuori dal volume principale.
4. **Nessun print-aware preprocessing**: nessun generatore enforce wall ≥0.45mm o feature ≥0.2mm. Tutto downstream.
5. **Texture-as-geometry confusion**: bumps geometrici dove l'immagine sorgente aveva texture ad alta frequenza (universale per image-conditioned).

## Tabella per-generator

| Generator | Output | Polycount default | Axis | Scale | Artefatto signature | Playbook iniziale |
|---|---|---|---|---|---|---|
| **Meshy v4-v6** (meshy.ai) | GLB (PBR, baked textures) — anche FBX/OBJ/STL/USDZ/BLEND/3MF | 50k–600k | Y-up | ≈1.0 BU | Texture-baked bumps, occasional non-watertight su concavi profondi | `repair_basic` poi `decimate_to_target(target=150000)` |
| **TripoSR** (VAST-AI) | GLB senza color (v1, issue #10) | 10k–25k | Y-up | ≈1.0 BU | NeRF artifacts, lati piatti hallucinati, density irregolare | `repair_basic` o Voxel Remesh se severo |
| **TripoSG** (VAST-AI / Stability) | GLB | 5k–50k (configurabile `--faces`) | Y-up | unit-sphere normalized | MC staircasing, qualità migliore di TripoSR | `repair_basic`, raramente decimate |
| **Hunyuan3D 2.0/2.1** (Tencent) | GLB / OBJ (trimesh) | ~100k–300k @ `octree_resolution=256`; ~500k–1M @ 512 | Y-up | ≈1.0 BU | Quantization staircase a octree basso, tiny feature lost; PBR ok in 2.1 | `decimate_to_target` aggressivo (10× ratio), poi `repair_basic` |
| **Rodin Gen-1/Gen-2** (Hyper3D) | GLB/FBX/OBJ/USDZ | 4k / 8k / 18k / 50k (tier) | Y-up | normalized | **Quad mode = near-print-ready**; Raw mode = MC standard | Quad mode: skip repair, scale+orient. Raw mode: `repair_basic` |
| **TRELLIS v1/v2** (Microsoft) | GLB (simplified, post-FlexiCubes) | ~30k–150k post-simplify | Y-up | normalized | Small holes documentati, ships con hole-fill scripts | Run script hole-fill prima di STL, poi `repair_basic` |
| **Zero123 / Zero123-XL / Zero123++** | mesh estratta da NeRF MC | 50k–200k | Y-up | normalized | Worst manifold: ghost geometry, double surfaces, NeRF fog | Voxel Remesh **prima** di tutto il resto |
| **Step1X-3D** (May 2025) | GLB con watertight + hole-fill stage interno | varia | Y-up | normalized | Già pulito alla fonte | Skip repair, vai a scale + orient |
| **UltraShape 1.0** (Dec 2025) | GLB con thin-structure thickening | varia | Y-up | normalized | Già print-aware in generation | Skip repair |

## Heuristica detect-and-route

Quando ricevi un file senza sapere il generator:

```
1. Estensione:
   .stl → solo geometria, perdita info; tratta come "unknown AI mesh" → repair_basic
   .glb/.gltf → Y-up garantito (spec), check materials/textures via bpy.data.materials
   .fbx → axis ambiguo, leggi axis_up nel binary header se possibile
   .usdz → Apple/photogrammetry, Z-up tipico

2. Bounding box max dim post-import:
   < 5 BU → unit-cube normalized (tutti i generator AI) → rescale needed
   5–50 BU → forse FBX da Rodin con scala interna o photogrammetry
   > 100 BU → photogrammetry GPS-scaled o tool in metri

3. Face count:
   < 10k → TripoSR o Rodin extra-low/low tier
   10k–50k → TripoSG, Rodin medium, Trellis post-simplify
   50k–200k → Meshy standard, Hunyuan3D @ octree=256, TRELLIS v2
   > 200k → Meshy HD, Hunyuan3D @ octree=512, photogrammetry

4. Material count:
   0 → STL puro, TripoSR senza color
   1 PBR → Meshy/Hunyuan3D/Rodin Quad mode
   2+ → multi-material (rare per AI mesh, comune per Bambu 3MF)

5. Topology hint (post-import, pre-cleanup):
   tutti quad o quad-dominant → Rodin Quad mode → minimal repair needed
   tutti tri, dense, uniform → Voxel/MC pipeline → repair + decimate
   tutti tri, density irregolare → NeRF-based (Zero123, TripoSR) → Voxel Remesh prima
```

## Workflow consigliato per generator

### Meshy (caso più comune)

```python
# CALL 1 — import + axis fix + scale
bpy.ops.import_scene.gltf(filepath="/path/meshy_output.glb")
obj = bpy.context.selected_objects[0]
obj.rotation_euler.x = -1.5708  # -90° per Y-up → Z-up
bpy.ops.object.transform_apply(rotation=True)

# CALL 2 — scale a TARGET_MM (vedi scale_detection.md)
# CALL 3 — analyze_mesh_for_print + kb_route → tipicamente parte R001+R004
```

### Rodin Quad mode (caso virtuoso)

```python
# Skip repair se la mesh è già quad. Importa, scala, orient, export.
# Solo verifica via analyze_mesh_for_print che non ci siano shells multiple
# (Rodin a volte include support floor come oggetto separato).
```

### Zero123 / NeRF-based (caso peggiore)

```python
# Voxel Remesh PRIMA di tutto il resto.
# voxel_size = max(0.0005, bbox_max_dim / 200)
# Poi repair_basic, poi decimate_to_target.
# Aspettati di perdere il 30-50% del dettaglio fine — è inevitabile.
```

### TRELLIS

```python
# Cerca nello stesso folder degli output script chiamati come
# "post_process.py" o "fill_holes.py" — TRELLIS li spedisce.
# Eseguili PRIMA di importare in Blender. Poi repair_basic standard.
```

## Generatori da preferire (ranking 2026)

Se l'utente può scegliere il generator, ordine di preferenza per print-readiness:

1. **Step1X-3D / UltraShape 1.0** — bake watertight + hole-fill nella generazione. Minimal downstream.
2. **Rodin Gen-1/2 in Quad mode** — output retopologizzato, near-print-ready, no MC artifacts.
3. **Hunyuan3D 2.1 @ octree_resolution≥256** — manifold per costruzione, PBR pulito, polycount gestibile.
4. **Meshy v6 Standard** — workflow consolidato, ampia documentazione, supporta retopologia tramite remesh API.
5. **TripoSG con `--faces` controllato** — leggero, qualità OK ma deps installazione.
6. **TRELLIS** — qualità geometrica buona ma richiede post-process scripts.
7. **TripoSR** — solo se serve generazione istantanea single-image; qualità inferiore.
8. **Zero123 / NeRF-based** — evita se possibile; ghost geometry frequente.

## Cross-reference

- [source_mesh_characteristics] — base teorica difetti AI per classe
- [ai_mesh_recipe] — pipeline 8-CALL end-to-end (usa questa tabella per CALL 1-2)
- [scale_detection] — rescale dopo unit-cube normalization
- [decimation_remesh] — Voxel Remesh, QuadriFlow, decimate dei modelli ad alto polycount
- [import_export] — parametri import per ogni formato

## Riferimenti

- Meshy formats: [help.meshy.ai/9991884](https://help.meshy.ai/en/articles/9991884-what-3d-file-formats-do-you-support)
- Hunyuan3D-2: [github.com/Tencent-Hunyuan/Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2)
- Rodin API: [developer.hyper3d.ai](https://developer.hyper3d.ai/api-specification/rodin-generation)
- TRELLIS: [github.com/microsoft/TRELLIS](https://github.com/microsoft/TRELLIS)
- TripoSG: [github.com/VAST-AI-Research/TripoSG](https://github.com/VAST-AI-Research/TripoSG)
- Step1X-3D paper: [arXiv 2505.07747](https://arxiv.org/html/2505.07747v1)
- UltraShape paper: [arXiv 2512.21185](https://arxiv.org/html/2512.21185v2)
