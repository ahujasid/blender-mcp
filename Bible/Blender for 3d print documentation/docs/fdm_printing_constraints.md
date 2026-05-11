# FDM Printing Constraints — Bambu A1

This document describes the physical and mechanical constraints of FDM printing on a Bambu A1. Use it to understand what properties a mesh must have to be printable, and what tradeoffs govern decisions about geometry modification.

---

## Hardware Specifications

| Parameter | Value |
|-----------|-------|
| Build volume | 256 × 256 × 256 mm |
| Default nozzle | 0.4 mm stainless steel |
| Available nozzles | 0.2 mm, 0.6 mm, 0.8 mm hardened steel |
| Max hotend temperature | 300 °C |
| Max bed temperature | 100 °C |
| Filament diameter | 1.75 mm |

The build volume is the hard boundary for any single print. Parts exceeding 256 mm on any axis must be split. The Bambu A1 is an open-frame printer, which constrains viable materials.

**Supported materials (open frame):** PLA, PETG, TPU, PLA-CF/GF, PETG-CF/GF

**Not recommended without enclosure:** ABS, ASA, PC, PA, PA-CF/GF, PET-CF/GF — these require enclosure-level ambient temperature control for adequate interlayer adhesion.

---

## Print Orientation — Geometry Implications

Before modifying a mesh, the intended print orientation should be determined, because orientation governs which constraints apply to which faces.

The orientation decision involves several competing factors:

| Factor | Preferred Orientation |
|---|---|
| Maximize XY strength | Align primary load axis horizontal |
| Minimize support volume | Orient so fewest faces exceed 45° overhang |
| Maximize surface quality on visible face | Place that face upward or vertical |
| Maximize dimensional accuracy | Place fit-critical features in XY plane |
| Maximize bed adhesion | Maximize flat contact area at Z = 0 |

These goals conflict. A face that has best surface quality when printed upward (top of the print) requires maximum support if it has complex geometry. A part oriented for minimum supports may have its primary load axis in Z, making it structurally weak.

The base face (the face resting on the print bed) must be flat or nearly flat. AI-generated and photogrammetry meshes rarely have a natural flat base — this must be created by cutting a flat plane through the mesh at the intended print orientation. A rounded or uneven base rocks on the bed and produces inconsistent first-layer adhesion.

---

## Layer Height

Layer height is the primary determinant of vertical resolution. It is always measured relative to nozzle diameter.

**Valid range for 0.4 mm nozzle:** 0.08 mm minimum — 0.28 mm maximum
- Rule of thumb: 20–70% of nozzle diameter; absolute upper limit is 80%
- First layer is always printed at 0.20 mm regardless of the rest of the profile — this increases contact area and bed adhesion

| Layer Height | Character |
|---|---|
| 0.08–0.12 mm | High detail, long print time; below 0.10 mm the improvement is minimal and rarely worth the cost |
| 0.16–0.20 mm | Balanced — default for most prints |
| 0.24–0.28 mm | Fast, coarser vertical surface; acceptable for structural or hidden parts |

Layer height affects only Z-axis resolution. XY resolution is determined by nozzle diameter and extrusion width. Thicker layers also improve interlayer adhesion because the nozzle squishes material further into the previous layer.

---

## Wall Thickness

The slicer places perimeters (walls) in multiples of the extrusion width. For a 0.4 mm nozzle the default extrusion width is approximately 0.45 mm.

**Critical rule:** Any wall thinner than one nozzle diameter (0.4 mm) is not printable. The slicer silently omits geometry below this threshold — those features simply do not appear in the print.

| Perimeter Count | Nominal Wall Thickness | Structural Character |
|---|---|---|
| 1 | 0.45 mm | Printable but fragile; single-shell surfaces crack easily |
| — | 0.45–0.90 mm | NOT printable — slicer skips partial perimeters |
| 2 | 0.90 mm | Minimum for structural integrity in most use cases |
| 3 | 1.35 mm | Solid general-purpose wall |
| 4 | 1.80 mm | Robust; recommended for load-bearing features |

Part strength comes primarily from perimeter count, not infill density. Increasing infill from 15% to 40% adds modest strength; adding a perimeter has a larger effect. The practical minimum wall for objects that will be handled or stressed is 0.8–1.2 mm (two to three perimeters).

Walls that fall between multiples — for example, a mesh wall of 0.65 mm — will be treated as a single perimeter. The slicer cannot produce a partial second perimeter. This is the most common source of invisible missing geometry in FDM prints of AI-generated models.

---

## Overhangs

FDM deposits material onto previously printed material. Faces that overhang empty space must either be supported by support structures or be within the self-supporting angle range.

**Safe threshold (support-free):** 45° from vertical (equivalently: 45° from horizontal)
**With aggressive part cooling:** up to ~60° — tested on the Bambu A1 at full fan speed

Above the threshold, the outer edge of each layer hangs unsupported over increasing air. Surface quality degrades progressively: the outer perimeter droops, creating a rough underside and potentially causing layer delamination in severe cases.

Design considerations:
- Chamfers print better than fillets for horizontal transitions — a 45° chamfer is self-supporting, a round fillet passes through all angles including >60°
- Smaller nozzles (0.2 mm) may require steeper than 45° because the thinner extrusion has less material to bridge the gap
- The angle threshold applies per-face: a surface that starts at 30° and curves to 70° will begin degrading at the 45° inflection point

---

## Bridges

A bridge is a horizontal span printed across open air between two supported anchor points. FDM can bridge short gaps without support using fan cooling to solidify filament before it sags.

**Reliable bridge length:** up to ~30 mm on PLA without significant sagging
**Risk zone:** 30–60 mm — quality depends heavily on cooling and speed
**High risk:** >60 mm — sagging is probable; support structures should be used

Bridge quality is primarily governed by:
- Fan speed (higher is better — solidifies filament faster)
- Print speed (lower is better — less momentum, more cooling time)
- Flow ratio (slightly reduced flow prevents over-deposition)
- Orientation — bridges perpendicular to the print head travel direction sag less because the filament is tensioned as it is laid

When evaluating a mesh for printing, spans between two faces that drop below horizontal are bridges. If the span exceeds 30 mm and support-free printing is desired, the geometry should either be split, redesigned with a chamfered underside, or accepted with a support structure.

---

## Supports

Support structures are auto-generated by the slicer for overhanging geometry beyond the threshold angle. They are temporary scaffolding removed after printing.

Supports always leave artifacts on the contacted surface. The quality of the interface is controlled by two parameters:

- **Z contact distance:** 50–75% of layer height. Smaller = better surface quality, harder removal. Larger = easier removal, rougher contact surface.
- **XY separation:** controls horizontal gap between support and part wall. Larger = easier removal, less lateral contamination.

| Support Type | Character | Best For |
|---|---|---|
| Grid | Dense, stable, predictable | Simple geometry, large flat overhangs |
| Snug | Follows part contour, no wall leakage | Organic shapes, tight spaces |
| Organic (tree) | Branching structure, minimal contact | Complex geometry, external overhangs |

The key decision is whether a surface that will receive supports is visible/functional. If it is, design the part to avoid supports at that location — reorienting the print or adding a 45° chamfer is preferable. If supports are unavoidable, organic supports minimize contact area.

---

## Layer Adhesion and Print Orientation

FDM is mechanically anisotropic. Strength is not equal in all directions.

| Direction | Strength Level | Reason |
|---|---|---|
| XY plane (horizontal) | High | Material is continuous within a layer |
| Z axis (between layers) | Low | Bond between layers is weaker than bond within a layer |

A part loaded in tension along the Z axis (i.e., the force tries to pull layers apart) will fail at a much lower load than the same part loaded in XY. For any functional part, the primary stress axis should lie in the XY plane.

Factors that improve interlayer adhesion:
- Thicker layer height (more squish, more contact area)
- Higher print temperature (better fusion)
- Lower print speed (more heat soak time)
- Reduced cooling (allows longer reflow time between layers)

These factors trade off against surface quality and print time. Cooling that is optimal for overhang quality degrades interlayer adhesion.

---

## Infill

Infill fills the interior volume of a solid mesh. It is structural scaffolding for the outer walls and top/bottom surfaces.

**Practical range:**
- 10–15%: sufficient for most non-structural, decorative, or light-duty parts
- 15–30%: functional parts subject to moderate loads
- >30%: rarely beneficial; strength gains plateau
- 100%: not meaningfully stronger than 3–4 perimeters with 20% infill for most load types

The dominant contributor to part strength is perimeter count. Infill primarily prevents surface collapse on top layers and provides lateral support for walls.

| Infill Pattern | Strength Character | Best For |
|---|---|---|
| Gyroid | Isotropic (equal in all directions) | Functional parts with uncertain load direction |
| Cubic | Isotropic | Functional parts |
| Grid / Lines | Anisotropic, fast | Decorative or single-axis load |
| Lightning | Minimal, top-surface support only | Fast prints, purely decorative |

---

## Minimum Feature Size

The nozzle diameter sets the physical lower bound for printable geometry.

| Feature | Minimum | Notes |
|---|---|---|
| Wall / protrusion | 0.4 mm | Absolute minimum (1 nozzle width); unreliable |
| Wall / protrusion (reliable) | 0.8 mm | 2 nozzle widths; consistent output |
| Hole diameter | nominal + 0.1–0.2 mm | FDM prints holes slightly undersized due to inward perimeter overlap |
| Moving part clearance | 0.3 mm | Below this, parts fuse during printing |
| Text / emboss depth | 0.8 mm | Minimum for legibility |
| Printer XY accuracy | ±0.2 mm | Tolerance budget for fit-critical features |

Features smaller than 0.4 mm will be silently dropped by the slicer. Features between 0.4 and 0.8 mm may print inconsistently. When evaluating a mesh, any detail below 0.8 mm should be either thickened or accepted as non-printing.

Holes specifically require oversizing to compensate for the inward curl of the inner perimeter. A hole designed at exactly 5.0 mm will typically print at 4.8–4.9 mm. Add 0.1–0.2 mm to the nominal diameter for clearance fits.

---

## Material Properties — Relevance to Mesh Decisions

Material choice constrains what geometry is viable. The following properties are relevant when preparing a mesh, not when selecting a filament.

| Material | Stiffness | Warping Risk | Relevant Mesh Considerations |
|---|---|---|---|
| PLA | High (brittle) | Very low | Good for sharp detail; thin flexible features will snap, not bend |
| PETG | Medium (tougher) | Low | Better for snap-fits and functional parts; slight stringing can fill fine gaps |
| TPU | Low (elastic) | Negligible | Requires wall thickness ≥ 1.2 mm to print reliably; supports are problematic (hard to remove from flexible part); avoid internal cavities |

PLA's brittleness means thin protrusions (< 1.5 mm) on a PLA print will fracture under minor mechanical stress regardless of print quality. Geometry that depends on flexibility for function (clips, springs, living hinges) is not suited to PLA.

TPU's elasticity means the slicer must produce walls thick enough to extrude consistently — at 0.45 mm extrusion width, a 0.9 mm wall is marginal for TPU because soft materials compress and spread unpredictably.

---

## Nozzle Size — Effect on Mesh Requirements

While the default is 0.4 mm, nozzle choice changes the minimum feature sizes and the wall thickness multiples the slicer will produce.

| Nozzle | Min Wall (1 perimeter) | Reliable Min Feature | Max Layer Height | Character |
|---|---|---|---|---|
| 0.2 mm | 0.22 mm | 0.44 mm | 0.16 mm | Maximum detail; very slow; fragile thin features possible |
| 0.4 mm | 0.45 mm | 0.80 mm | 0.32 mm | General purpose; default |
| 0.6 mm | 0.68 mm | 1.20 mm | 0.48 mm | Faster; coarser detail; stronger walls per perimeter |
| 0.8 mm | 0.90 mm | 1.60 mm | 0.64 mm | High-speed large parts; fine detail lost |

When the target nozzle is not 0.4 mm, all wall thickness calculations must be recalculated. A mesh wall that is adequate for a 0.4 mm nozzle may be skipped by a 0.6 mm nozzle if it falls below that nozzle's extrusion width.

The 0.2 mm nozzle inverts one common assumption: it can print features that a 0.4 mm nozzle skips, but it also requires steeper overhang angles to self-support because each extrusion deposits less material per layer width.

---

## Mesh Properties Required for Slicing

For the slicer to produce a valid toolpath, a mesh must satisfy a set of geometric requirements. These are properties of the mesh itself, not slicer settings.

| Required Property | Why It Matters |
|---|---|
| Watertight (closed shell) | Slicer must have a definite inside and outside to fill with infill and walls |
| Manifold edges | Every edge shared by exactly 2 faces — no T-junctions, no open boundaries |
| Consistent normals | All face normals pointing outward — slicer uses normals to determine surface orientation |
| No self-intersections | Intersecting faces create ambiguous interior/exterior regions |
| Correct scale (mm) | Bambu Studio interprets units as millimeters; 1 Blender unit = 1 mm when units are set correctly |
| Within build volume | 256 × 256 × 256 mm hard limit |

A mesh that fails any of these conditions may still be sliced — most modern slicers attempt repairs — but the result is unpredictable. Slicer auto-repair is non-deterministic and may close holes in geometrically incorrect ways. Repair should happen at the mesh level before importing into the slicer.
