# Prompt template — Ottimizzazione immagine-reference per AI image-to-3D

Uso: incollare questo prompt in Gemini (o analogo image-to-image / nano-banana / Flux Kontext / SeedReam) **insieme all'immagine di riferimento**. Compilare gli slot `[…]` prima dell'invio.

Output atteso: una singola immagine riottimizzata, pronta per essere data in pasto a TripoSG, Hunyuan3D, TripoSR, Tripo, Rodin/Hyper3D o Meshy.

---

## Prompt (copiare e incollare sotto l'immagine)

```
Regenerate the reference image as a clean, studio-style product shot optimized as input for an AI image-to-3D generator (TripoSG / Hunyuan3D / Rodin / Meshy). The downstream goal is FDM 3D printing on a Bambu Lab A1 (nozzle 0.4 mm, PLA). Preserve the subject identity, proportions and main color palette of the reference. Do NOT invent details that are not present in the reference.

SUBJECT: [describe subject briefly — e.g. "small dragon figurine, coiled tail, wings half-open"]
INTENDED FINAL PRINT SIZE: [e.g. 80 mm tall]
STYLE CONSISTENCY: [match reference / stylized / realistic PBR / anime / hard-surface mech / organic creature]

=== MANDATORY CONSTRAINTS ===

[CAMERA & FRAMING]
- Single subject, perfectly centered in frame.
- Three-quarter front view: front-facing with a ~25° rotation around the vertical axis so the AI can see both the front and one side.
- Slight downward tilt of the camera (~10°) so the top of the head/body is visible.
- Full subject in frame with ~10% padding on every side. No cropping of any limb, appendage, tail, wing, base.
- Square aspect ratio, 1:1. Render at the highest resolution possible (1024×1024 minimum, 2048×2048 preferred).

[BACKGROUND]
- Pure flat neutral background, seamless. Use medium grey (#B0B0B0) if the subject has any white/bright areas; otherwise use pure white (#FFFFFF).
- Zero gradient, zero texture, zero patterns, zero props. No floor line, no horizon, no shadow on the background.
- The silhouette of the subject must be unambiguously separable from the background. If any part of the subject is the same color as the background, shift the background to the complementary neutral.

[LIGHTING]
- Soft omnidirectional studio lighting as if inside a lightbox / softbox dome. Diffuse, low-contrast.
- No hard cast shadows on the subject or the ground. A very faint ambient occlusion contact shadow directly under the base is acceptable but must not be a long projected shadow.
- No strong specular highlights, no rim light, no backlight. Materials should read as matte or semi-matte.
- Even exposure: no blown-out highlights, no crushed blacks. The whole subject must be clearly readable in shading.

[SUBJECT POSE & GEOMETRY]
- Pose must be stable and self-supporting on a flat base. Avoid any pose that relies on a single thin contact point, balancing on tiptoe, leaning, or mid-jump.
- No limbs floating detached from the body. No elements hovering in mid-air.
- All appendages (arms, legs, tail, wings, weapons) must be attached to the main body with a clear solid junction.
- Symmetry: if the subject is naturally symmetric, present it symmetrically. If asymmetric, ensure the asymmetry is clearly visible from the chosen 3/4 view.
- Arms/limbs should be slightly separated from the torso (2–4° from body) so the AI reconstructor can resolve the gap; but not in an extreme T-pose unless the subject is a humanoid that requires it.

[FDM-PRINT READINESS — critical]
- THICKEN all thin features so they correspond to at least 2 mm of physical thickness at the intended final print size [FILL SIZE]. Anything thinner than 2 mm at print scale will fail on a 0.4 mm nozzle and will also be lost in the AI mesh generation step.
  Examples to thicken or simplify: thin sword blades, hair strands, whiskers, antennas, thin wire-like details, spider legs, fins, ears, eyelashes.
  If a feature cannot be thickened without destroying the look, simplify it into a single solid volume (e.g. fused hair chunk instead of individual strands).
- REMOVE or MERGE any floating / disconnected geometry. If the reference shows accessories floating detached (magic orbs, orbiting particles, separate petals), either attach them to the body or remove them.
- OVERHANGS: where possible, arrange the pose so that no surface sits at more than 45° from vertical without being supported by another part of the body. Prefer poses that naturally tuck limbs close to the torso if the reference allows.
- BASE: if the subject does not naturally have a flat base, show it resting on an implicit flat ground plane at the bottom of the frame. Do NOT add a decorative base plate, pedestal, terrain, or rock unless the reference shows one. The bottom of the subject must have a contact area of at least ~15% of its footprint.
- No transparent, glass, or clear materials. Render everything as opaque (glass/gems → opaque colored plastic look).
- No hair/fur as individual strands — render as solid stylized volumes.

[COLORS & TEXTURES]
- Flat, readable coloring. Preserve the reference's main color palette.
- Remove heavy photographic texture, scratches, dirt, noise, grunge overlays. The AI-to-3D model reads these as geometric detail and produces bumpy surfaces.
- Keep large color regions clean and solid; small decorative patterns are OK but should be painted-on, not embossed.
- No reflections of the environment on the subject. No chrome / mirror materials — if the reference has them, matte them out.

[DO-NOT LIST]
- NO text, NO logos, NO watermarks, NO UI elements, NO caption.
- NO multiple subjects, NO background characters, NO duplicated copies in the same frame.
- NO depth-of-field blur. The whole subject must be in sharp focus.
- NO motion blur, NO lens flare, NO bokeh.
- NO extra views / turnaround sheet / multi-panel composition — output a SINGLE image.
- NO artistic effects (painterly, watercolor, pencil, ink lines) unless the reference is explicitly in that style AND [STYLE CONSISTENCY] asks for it.

=== OPTIONAL OVERRIDES (delete if unused) ===
- SUBJECT ORIENTATION OVERRIDE: [e.g. "side view" / "front only" / "top-down"] — only if the standard 3/4 view cannot capture the essential features.
- BACKGROUND OVERRIDE: [e.g. "pure black #000000"] — only if the subject is very light colored and pure white/grey both fail.
- ELEMENTS TO ADD: [only things visibly hinted at but unclear in the reference]
- ELEMENTS TO REMOVE: [e.g. "remove the floating magic aura", "remove the text banner"]

=== DELIVERABLE ===
Output: 1 single square image, the subject in a clean 3/4 front view on a neutral seamless background, optimized for downstream image-to-3D generation and FDM 3D printing. Do not return multiple images, contact sheets, or variants.
```

---

## Come compilarlo — guida rapida

| Slot | Cosa mettere | Esempio |
|---|---|---|
| `[SUBJECT]` | 1 frase neutra che descrive il soggetto senza stile | `"small wolf figurine in alert stance, tail down"` |
| `[INTENDED FINAL PRINT SIZE]` | altezza/lato più lungo in mm | `"90 mm tall"` |
| `[STYLE CONSISTENCY]` | scegliere tra: `match reference`, `stylized toy`, `realistic PBR`, `anime`, `hard-surface mech`, `organic creature` | `"stylized toy"` |
| `[FILL SIZE]` dentro FDM-PRINT | ripetere la stessa altezza | `"90 mm"` |
| Override opzionali | cancellare i blocchi non usati | — |

## Note operative

- **Se la reference ha già sfondo pulito e vista 3/4**, il prompt si limita a rinforzare: Gemini tenderà a lasciare quasi tutto uguale ma normalizza lighting e rimuove texture fotografica → ottimo.
- **Se la reference è una foto "wild"** (sfondo casuale, luce laterale, soggetto con cappotto texturato, occhi brillanti), il prompt forza una riregenerazione pesante — potresti dover iterare 2–3 volte.
- **Se il soggetto ha elementi che "non si toccano"** (bacchetta staccata dalla mano, occhio-gemma flottante), Gemini a volte li tiene staccati: aggiungere esplicito `"fuse [element] onto [body part] as a single solid"` nella sezione `ELEMENTS TO REMOVE`/`ADD`.
- **Reference fotografica di persona reale**: evitare richieste che violino consent/likeness. Usare solo per oggetti, personaggi di fantasia, action figure, giocattoli, prodotti.
- **Downstream**: dopo che Gemini ha ri-generato l'immagine, darla in pasto al tool image→3D (es. `mcp__blender__generate_hyper3d_model_via_images`). Il mesh che uscirà andrà comunque passato attraverso la pipeline `ai_mesh_recipe.md` (repair + decimazione + orientamento + validazione pre-export).

---

## Versione compatta (quando hai poco spazio / poca compliance del modello)

Per tool che tagliano prompt molto lunghi (es. Gemini mobile, tool web con limite 500 token), usare questa versione short:

```
Regenerate this image as a clean AI-to-3D input: single subject, 3/4 front view (~25° rotation), centered, 10% padding, 1:1 square 1024+, seamless neutral background (white or 18% grey, opposite of subject color), soft omnidirectional studio lighting, no hard shadows, no specular, no DOF, no text/logo. Preserve subject identity, proportions and main colors.
Thicken any feature thinner than 2 mm at [FINAL SIZE] scale print (no thin hair strands, no wires, no thin blades). Fuse any floating/detached element onto the main body. Pose must be stable with ≥15% flat contact base. Matte opaque materials only — no glass, chrome, transparent. Flat clean coloring, no photographic texture/noise/grunge. Output a SINGLE square image.
Subject: [SUBJECT]. Target print size: [SIZE mm]. Style: [STYLE].
```
