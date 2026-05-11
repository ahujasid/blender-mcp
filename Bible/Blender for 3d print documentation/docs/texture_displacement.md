# Texture & Displacement — Blender Python API

These are Blender's **legacy procedural textures** (`bpy.types.Texture` subclasses), distinct from shader node textures. They operate directly with modifiers like `DisplaceModifier`, making them the primary tool for adding surface detail to 3D print meshes without destructive mesh editing.

---

## bpy.types.Texture (base class)

All texture types inherit from `Texture(ID)`. Key shared properties:

| Property | Type | Default | Notes |
|---|---|---|---|
| `type` | enum str | `'IMAGE'` | Read-only after creation; set via `bpy.data.textures.new(name, type)` |
| `use_color_ramp` | bool | `False` | Maps intensity to a color ramp |
| `color_ramp` | `ColorRamp` | readonly | Only meaningful when `use_color_ramp` is True |
| `use_nodes` | bool | `False` | Makes texture node-based; exposes `node_tree` |
| `node_tree` | `NodeTree` | readonly | Active only when `use_nodes=True` |
| `intensity` | float [0, 2] | `1.0` | Brightness multiplier |
| `contrast` | float [0, 5] | `1.0` | Contrast multiplier |
| `use_clamp` | bool | `False` | Clamps negative RGB/intensity to zero. For displacement, set `False` to allow negative values (inward displacement) |

**Creating a texture:**
```python
tex = bpy.data.textures.new("MyTex", type='CLOUDS')
# type string must match one of: 'CLOUDS', 'WOOD', 'MARBLE', 'MAGIC', 'BLEND',
# 'STUCCI', 'NOISE', 'IMAGE', 'MUSGRAVE', 'VORONOI', 'DISTORTED_NOISE'
```

**Evaluating a texture at a point (returns RGBA vector):**
```python
result = tex.evaluate(mathutils.Vector((x, y, z)))
# result[3] = intensity, result[0:3] = RGB
```

---

## Procedural Texture Subclasses

### CloudsTexture — organic, bumpy noise

`bpy.types.CloudsTexture(Texture)` — procedural noise producing smooth or sharp cloud-like patterns.

| Property | Type | Range / Values | Default |
|---|---|---|---|
| `noise_basis` | enum | See noise basis table below | `'BLENDER_ORIGINAL'` |
| `noise_scale` | float | [0.0001, ∞) | `0.25` |
| `noise_depth` | int | [0, 30] | `2` |
| `noise_type` | enum | `'SOFT_NOISE'`, `'HARD_NOISE'` | `'SOFT_NOISE'` |
| `cloud_type` | enum | `'GRAYSCALE'`, `'COLOR'` | `'GRAYSCALE'` |
| `nabla` | float | [0.001, 0.1] | `0.025` |

`noise_depth` adds octaves of detail — higher values produce finer surface texture but at a computation cost. `HARD_NOISE` produces sharp, crinkled transitions; `SOFT_NOISE` is smooth. For displacement, `GRAYSCALE` is the relevant output mode (intensity channel drives displacement).

### NoiseTexture — pure random

`bpy.types.NoiseTexture(Texture)` — entirely random per-pixel noise with no parameters beyond the base `Texture` class. Produces maximum randomness with no spatial coherence. Rarely useful for 3D printing displacement as the result is chaotic and doesn't scale with mesh resolution meaningfully.

### VoronoiTexture — cell/crystal patterns

`bpy.types.VoronoiTexture(Texture)` — generates Voronoi cellular patterns (distance-to-feature-point fields).

| Property | Type | Range / Values | Default |
|---|---|---|---|
| `color_mode` | enum | `'INTENSITY'`, `'POSITION'`, `'POSITION_OUTLINE'`, `'POSITION_OUTLINE_INTENSITY'` | `'INTENSITY'` |
| `distance_metric` | enum | `'DISTANCE'`, `'DISTANCE_SQUARED'`, `'MANHATTAN'`, `'CHEBYCHEV'`, `'MINKOVSKY_HALF'`, `'MINKOVSKY_FOUR'`, `'MINKOVSKY'` | `'DISTANCE'` |
| `minkovsky_exponent` | float | [0.01, 10] | `2.5` |
| `noise_intensity` | float | [0.01, 10] | `1.0` |
| `noise_scale` | float | [0.0001, ∞) | `0.25` |
| `weight_1` | float | [-2, 2] | `1.0` |
| `weight_2` | float | [-2, 2] | `0.0` |
| `weight_3` | float | [-2, 2] | `0.0` |
| `weight_4` | float | [-2, 2] | `0.0` |
| `nabla` | float | [0.001, 0.1] | `0.025` |

The weights control the combination of F1–F4 (nearest to 4th-nearest feature point distances). `MANHATTAN` and `CHEBYCHEV` metrics produce more angular/blocky cell shapes versus the default Euclidean `DISTANCE`. For displacement on 3D prints, Voronoi produces reptile-scale or cobblestone surface textures.

### MarbleTexture — layered wave + noise

`bpy.types.MarbleTexture(Texture)` — sinusoidal band pattern perturbed by noise, producing marble-like or wood-grain patterns.

| Property | Type | Range / Values | Default |
|---|---|---|---|
| `marble_type` | enum | `'SOFT'`, `'SHARP'`, `'SHARPER'` | `'SOFT'` |
| `noise_basis` | enum | See noise basis table | `'BLENDER_ORIGINAL'` |
| `noise_basis_2` | enum | `'SIN'`, `'SAW'`, `'TRI'` | `'SIN'` |
| `noise_scale` | float | [0.0001, ∞) | `0.25` |
| `noise_depth` | int | [0, 30] | `2` |
| `noise_type` | enum | `'SOFT_NOISE'`, `'HARD_NOISE'` | `'SOFT_NOISE'` |
| `turbulence` | float | [0.0001, ∞) | `5.0` |
| `nabla` | float | [0.001, 0.1] | `0.025` |

`noise_basis_2` controls the wave shape: `SIN` = sinusoidal bands, `SAW` = sharp bands (good for layered prints), `TRI` = triangular wave. `turbulence` controls how much noise distorts the bands — high values produce a chaotic pattern, low values produce clean bands.

### WoodTexture — concentric rings or straight bands

`bpy.types.WoodTexture(Texture)` — produces wood-grain-like concentric rings or parallel bands.

| Property | Type | Range / Values | Default |
|---|---|---|---|
| `wood_type` | enum | `'BANDS'`, `'RINGS'`, `'BANDNOISE'`, `'RINGNOISE'` | `'BANDS'` |
| `noise_basis` | enum | See noise basis table | `'BLENDER_ORIGINAL'` |
| `noise_basis_2` | enum | `'SIN'`, `'SAW'`, `'TRI'` | `'SIN'` |
| `noise_scale` | float | [0.0001, ∞) | `0.25` |
| `noise_type` | enum | `'SOFT_NOISE'`, `'HARD_NOISE'` | `'SOFT_NOISE'` |
| `turbulence` | float | [0.0001, ∞) | `5.0` |
| `nabla` | float | [0.001, 0.1] | `0.025` |

`BANDS`/`RINGS` are pure patterns with no noise; `BANDNOISE`/`RINGNOISE` add turbulence. `RINGS` produces cylindrical-coordinate concentric rings useful for simulating turned/lathe surface patterns. `turbulence` only applies to the `NOISE` variants.

### StucciTexture — bumpy/stippled noise

`bpy.types.StucciTexture(Texture)` — produces a bump-mapped stucco effect.

| Property | Type | Range / Values | Default |
|---|---|---|---|
| `stucci_type` | enum | `'PLASTIC'`, `'WALL_IN'`, `'WALL_OUT'` | `'PLASTIC'` |
| `noise_basis` | enum | See noise basis table | `'BLENDER_ORIGINAL'` |
| `noise_scale` | float | [0.0001, ∞) | `0.25` |
| `noise_type` | enum | `'SOFT_NOISE'`, `'HARD_NOISE'` | `'SOFT_NOISE'` |
| `turbulence` | float | [0.0001, ∞) | `5.0` |

`PLASTIC` = standard stucci bumps; `WALL_IN` = dimples (inward); `WALL_OUT` = ridges (outward). The directional nature of `WALL_IN`/`WALL_OUT` can interact with `DisplaceModifier.mid_level` to produce consistent directional displacement. Note: this texture historically operated differently in the normal map context; for pure intensity displacement, all three `stucci_type` values produce similar results — the distinction is more visible in material/bump mapping.

### MusgraveTexture — fractal terrain

`bpy.types.MusgraveTexture(Texture)` — multi-octave fractal noise with the most control over frequency spectrum. Best for organic/terrain-like surfaces.

| Property | Type | Range / Values | Default |
|---|---|---|---|
| `musgrave_type` | enum | `'MULTIFRACTAL'`, `'RIDGED_MULTIFRACTAL'`, `'HYBRID_MULTIFRACTAL'`, `'FBM'`, `'HETERO_TERRAIN'` | `'MULTIFRACTAL'` |
| `noise_basis` | enum | See noise basis table | `'BLENDER_ORIGINAL'` |
| `noise_scale` | float | [0.0001, ∞) | `0.25` |
| `octaves` | float | [0, 8] | `2.0` |
| `dimension_max` | float | [0.0001, 2] | `1.0` |
| `lacunarity` | float | [0, 6] | `2.0` |
| `gain` | float | [0, 6] | `1.0` |
| `offset` | float | [0, 6] | `1.0` |
| `noise_intensity` | float | [0, 10] | `1.0` |
| `nabla` | float | [0.001, 0.1] | `0.025` |

- `octaves`: number of frequency layers — higher = more fine detail
- `lacunarity`: frequency gap between octaves (2.0 = each octave twice the previous frequency)
- `dimension_max`: fractal dimension; lower = rougher (more high-frequency content)
- `gain`: amplitude scaling per octave (affects `RIDGED_MULTIFRACTAL` and `HYBRID_MULTIFRACTAL`)
- `offset`: shifts the base signal — affects how ridges vs valleys are distributed in `RIDGED_MULTIFRACTAL`
- `FBM` (fractal Brownian Motion) is the most mathematically standard and predictable
- `RIDGED_MULTIFRACTAL` produces sharp mountain-ridge-like features, useful for rocky surface textures

### ImageTexture — image-based displacement map

`bpy.types.ImageTexture(Texture)` — uses a `bpy.types.Image` as the texture source.

| Property | Type | Range / Values | Default |
|---|---|---|---|
| `image` | `Image` | object reference | `None` |
| `extension` | enum | `'EXTEND'`, `'CLIP'`, `'CLIP_CUBE'`, `'REPEAT'`, `'CHECKER'` | `'REPEAT'` |
| `repeat_x` | int | [1, 512] | `1` |
| `repeat_y` | int | [1, 512] | `1` |
| `crop_min_x/y` | float | [-10, 10] | `0.0` |
| `crop_max_x/y` | float | [-10, 10] | `1.0` |
| `use_interpolation` | bool | — | `True` |
| `filter_size` | float | [0.1, 50] | `1.0` |
| `use_alpha` | bool | — | `True` |
| `use_flip_axis` | bool | — | `False` |
| `use_mirror_x/y` | bool | — | `False` |

`EXTEND` (repeat edge pixel) is better than `CLIP` for displacement maps to avoid hard seam artifacts at boundaries. `REPEAT` tiles seamlessly. For displacement maps, grayscale images work directly (intensity = displacement amount); the `use_normal_map` flag should remain `False` for displacement use.

---

## Noise Basis Options (shared across procedural textures)

| Value | Description |
|---|---|
| `'BLENDER_ORIGINAL'` | Default smoothed interpolated noise |
| `'ORIGINAL_PERLIN'` | Classic Perlin noise |
| `'IMPROVED_PERLIN'` | Improved Perlin (less directional artifacts) |
| `'VORONOI_F1'` | Distance to closest feature point |
| `'VORONOI_F2'` | Distance to 2nd closest |
| `'VORONOI_F2_F1'` | F2 minus F1 (produces sharp cell edges) |
| `'VORONOI_CRACKLE'` | Sharp Voronoi tessellation |
| `'CELL_NOISE'` | Square cell tessellation |

`IMPROVED_PERLIN` is generally the most visually neutral; `VORONOI_CRACKLE` as a noise basis produces sharply segmented, cracked-surface patterns.

---

## bpy.types.Image

`bpy.types.Image(ID)` — image data block for use with ImageTexture.

Key properties:

| Property | Type | Notes |
|---|---|---|
| `filepath` | str | Path to external file; blend-relative `//` prefix supported |
| `size` | `bpy_prop_array[int]` | `[width, height]` in pixels, readonly |
| `pixels` | float array | Flat RGBA float array, length = `width * height * 4` |
| `channels` | int | Number of channels (readonly) |
| `colorspace_settings` | `ColorManagedInputColorspaceSettings` | Input color space; set `name` to `'Non-Color'` for displacement maps |
| `source` | enum | `'FILE'`, `'SEQUENCE'`, `'MOVIE'`, `'GENERATED'`, `'VIEWER'`, `'TILED'` |
| `has_data` | bool | True if image buffer is loaded into memory (readonly) |
| `is_dirty` | bool | Unsaved changes exist (readonly) |

Loading images:
```python
img = bpy.data.images.load("/path/to/heightmap.png")
# or load with auto-relative path:
img = bpy.data.images.load(bpy.path.abspath("//heightmap.png"))
```

For displacement maps, set the color space to non-color data to avoid gamma correction affecting values:
```python
img.colorspace_settings.name = 'Non-Color'
```

---

## DisplaceModifier — connecting textures to geometry

`bpy.types.DisplaceModifier(Modifier)` bridges a `Texture` to mesh vertex displacement.

| Property | Type | Range / Values | Default |
|---|---|---|---|
| `texture` | `Texture` | object reference | `None` |
| `strength` | float | (-∞, ∞) | `1.0` |
| `mid_level` | float | (-∞, ∞) | `0.5` |
| `direction` | enum | `'X'`, `'Y'`, `'Z'`, `'NORMAL'`, `'CUSTOM_NORMAL'`, `'RGB_TO_XYZ'` | `'NORMAL'` |
| `texture_coords` | enum | `'LOCAL'`, `'GLOBAL'`, `'OBJECT'`, `'UV'` | `'LOCAL'` |
| `texture_coords_object` | `Object` | only for `texture_coords='OBJECT'` | `None` |
| `uv_layer` | str | UV map name, only for `texture_coords='UV'` | `''` |
| `vertex_group` | str | Limits effect by vertex group | `''` |
| `space` | enum | `'LOCAL'`, `'GLOBAL'` | `'LOCAL'` |

**Key semantics:**

- `mid_level=0.5` means a texture value of 0.5 produces zero displacement. Values above 0.5 push out, below 0.5 push in. Set `use_clamp=False` on the texture to allow negative displacement.
- `mid_level=0.0` means the texture's full range [0, 1] maps to outward displacement only (useful for additive surface bumps).
- `strength` is in Blender Units (BU). With `scene.unit_settings.scale_length=0.001`, 1 BU = 1mm, so `strength=0.002` = 2mm of maximum displacement.
- `direction='NORMAL'` displaces along vertex normals — most natural for surface bumps on curved surfaces.
- `direction='RGB_TO_XYZ'` uses the texture's RGB channels as XYZ displacement vectors — primarily useful with `ImageTexture` that encodes directional data.
- `texture_coords='UV'` requires the mesh to have UV coordinates and `uv_layer` to name the correct map; gives the most precise, art-directed control.
- `texture_coords='LOCAL'` uses the object's local 3D coordinates — procedural textures tile based on object size; a 1m cube will sample one full period of `noise_scale=1.0`.

**Connecting a texture:**
```python
mod = obj.modifiers.new("Displace", type='DISPLACE')
tex = bpy.data.textures.new("SurfaceTex", type='CLOUDS')
tex.noise_scale = 0.1  # in BU; with scale_length=0.001, this = 100mm feature size
mod.texture = tex
mod.strength = 0.005   # 5mm displacement with scale_length=0.001
mod.mid_level = 0.5
mod.direction = 'NORMAL'
mod.texture_coords = 'LOCAL'
```

---

## Procedural vs Image Texture — Design Choices

| Criterion | Procedural (Clouds, Voronoi, Musgrave…) | ImageTexture |
|---|---|---|
| File dependency | None — fully self-contained | Requires external file or packed data |
| Parametric control | Yes — all properties adjustable in Python | Limited (crop, repeat, flip) |
| Infinite resolution | Yes — scales to any mesh density | Limited by image resolution |
| Precise custom shapes | No | Yes — paint or generate exact patterns |
| Reproduciblity | Deterministic from parameters | Tied to file content |
| 3D tiling | Natural (3D noise) | Only XY tiling; `texture_coords='LOCAL'` causes Z-projection artifacts |

For 3D printing surface detail, procedural textures are preferable when the goal is consistent organic texture across arbitrary geometry. ImageTexture is better when the displacement pattern is designed/measured externally (e.g., from a real texture scan or a mathematically precise height map).

**Useful combinations for FDM print surfaces:**
- `CloudsTexture` + `NORMAL` direction: general organic roughness/pebbling
- `VoronoiTexture` + `DISTANCE` metric: reptile scales, cobblestone
- `MusgraveTexture` `FBM` or `RIDGED_MULTIFRACTAL`: terrain/rocky texture
- `WoodTexture` `RINGS`: concentric ring patterns simulating turned/lathe marks
- `MarbleTexture` `SAW` + `BANDNOISE`: layered band patterns, hatching-like effects
- `ImageTexture` with grayscale height map: logo embossing, precise geometric patterns

**Important note on mesh density:** Displacement modifier operates on existing vertices — no new vertices are created. Fine surface detail requires adequate mesh resolution (use SubdivisionSurface modifier before DisplaceModifier). The rule of thumb: the smallest desired surface feature should be larger than the average edge length of the mesh at the point of displacement.

---

## Sculpt Mode + Multi-Resolution + Stencil — Alternativa interattiva

Questa tecnica è un'**alternativa non-procedurale** al Displacement Modifier: produce texture superficiali (mattoni, roccia, superfici organiche) sculturando direttamente la mesh con pennelli guidati da un'immagine stencil. Più adatta per prototipi visivi e mesh di output finale; meno adatta per workflow MCP automatizzati (richiede interazione manuale).

### Pipeline

1. **Suddividere la mesh base** in Edit Mode: `Mesh > Suddividi` con 10 cuts per aumentare la risoluzione prima della scultura.

2. **Aggiungere il Multi-Resolution Modifier** (non Subdivision Surface): il Multi-Resolution consente di sculturare su livelli di dettaglio separati senza modificare la topologia di base.
   - Aggiungere 5 livelli di suddivisione nel modifier per densità sufficiente.

3. **Entrare in Sculpt Mode** e configurare il pennello attivo:
   - `Active Tool > Advanced`: abilitare **Front Faces Only** (sculpta solo le facce visibili dalla camera).
   - `Texture`: selezionare la texture immagine caricata (stencil).
   - `Mapping`: cambiare da `Tiled` a **`Stencil`** — la texture appare come overlay nel viewport.
   - `Falloff`: cambiare da `Smooth` a **`Constant`** — il pennello applica forza uniforme, non degradata.

4. **Posizionare e scalare lo stencil** nel viewport:
   - Spostare: `tasto destro tenuto` (click + drag)
   - Scalare: `Shift + tasto destro tenuto`
   - Ruotare: `Ctrl + tasto destro tenuto`

5. **Applicare la texture**: aumentare il raggio del pennello (`]` per ingrandire) fino a coprire l'intera area desiderata, poi cliccare una o più volte per incidere la texture.

6. **Ripetere per ogni faccia** dell'oggetto cambiando vista e riposizionando lo stencil.

### Considerazioni per stampa 3D

- Il dettaglio ottenibile è limitato dalla risoluzione della mesh Multi-Resolution. Con 5 livelli su una mesh di partenza a 10 cut, si ottengono centinaia di migliaia di facce — sufficiente per texture fino a ~0.5mm.
- Il Multi-Resolution Modifier produce geometria reale esportabile in STL.
- **Texture stencil raccomandate**: immagini grayscale ad alto contrasto (bianco = rilievo, nero = rientranza). Stencil con sfondo neutro al 50% di grigio funzionano con `mid_level=0.5` del Displacement Modifier equivalente.
- Fonti di stencil gratuiti: poligon.co, ambientcg.com, textures.com (versione free).

### Codice Python — setup Multi-Resolution via script

Il Multi-Resolution Modifier può essere configurato via API, ma la scultura interattiva con stencil non è automatizzabile via `execute_blender_code`. Usare il codice sotto per preparare la mesh, poi proseguire manualmente in Sculpt Mode:

```python
import bpy

obj = bpy.context.active_object

# Suddividi in Edit Mode per base resolution
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=10)
bpy.ops.object.mode_set(mode='OBJECT')

# Aggiungi Multi-Resolution Modifier
mod = obj.modifiers.new(name="MultiRes", type='MULTIRES')

# Aggiungi 5 livelli di scultura
for _ in range(5):
    bpy.ops.object.multires_subdivide(modifier="MultiRes", mode='CATMULL_CLARK')

print(f"Multi-Resolution pronto: {mod.total_levels} livelli")
print("Entra in Sculpt Mode per applicare la texture stencil manualmente")
```
