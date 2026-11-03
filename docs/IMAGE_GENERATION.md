# Image generation

How CATANA directs every kind of still: from a one-line request to a linted, provider-ready prompt, then (with the
user's approval for paid providers) to an executed generation that is logged honestly.

Related: [PROMPT_ENGINEERING.md](PROMPT_ENGINEERING.md) (spec fields, presets, QC) ·
[VIDEO_GENERATION.md](VIDEO_GENERATION.md) · [PROVIDERS.md](PROVIDERS.md) · [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## The loop (every image workflow)

1. **Spec.** `python scripts/catana.py enhance "<request>" [--domain d] [--aspect r] [--platform p] --json`, then
   overwrite fields with real art direction. Every image spec covers:
   - subject and environment
   - camera and lens
   - composition
   - lighting
   - materials
   - color grade (`color`)
   - artistic direction (`style`)
   - aspect ratio (`technical.aspect_ratio`)
   - negatives (`negative`)
   - reference preservation (`references[].preserve`)
2. **References.** Add `references: [{"source", "role", "preserve": [...]}]`. The roles decide the operation (table
   below).
3. **Lint.** `python scripts/catana.py lint spec.json --provider <p> [--model <m>]`. Fix every error. Grade A is the bar.
4. **Select.** `python scripts/catana.py select --op <op> --available <connectors present>`. Paid providers come back
   with `requires_approval: true`: quote the cost and ask first.
5. **Execute.** Run the connector tool (see [PROVIDERS.md](PROVIDERS.md)), verify the returned asset, and log it with
   `catana.py log`. With no provider, run `catana.py pack spec.json --out dir` to write a prompt pack. That status is
   always `prompt_only`, never "generated".

### Operation from references (`qc.needed_operation`)

| References | Operation |
|---|---|
| none | `t2i` |
| exactly one, role `style` | `style_transfer` |
| one (any other role) | `i2i` |
| two or more | `multi_ref_image` |
| enhancement of an existing image | `upscale_image` / `outpaint`. Select these explicitly (`select --op upscale_image`); they aren't inferred from a spec |

### Reference roles and what to preserve

| Role | Use for | `preserve` examples (from the domain presets' `preserve_on_reference`) |
|---|---|---|
| `product` | the exact item being advertised | exact product shape and proportions, logo and label artwork, brand colours, material finish |
| `character` / `subject` | a person or hero object that must stay identical | face identity and proportions, hairstyle and hair colour, skin tone, wardrobe, distinguishing marks |
| `geometry` | buildings, interiors, vehicles | building massing and footprint, number of floors, window and opening layout, roof form, materials, the reference camera position |
| `composition` | framing to copy | camera position, horizon height, subject placement |
| `style` | look only (palette, light, texture) | none needed; the engine adds "without copying its subject" |
| `environment` | a location plate | key landmarks, horizon, time of day |

A non-style reference without `preserve` is a QC **warning**: the model will reinterpret it.

### Providers and models (snapshot 2026-11-03, `data/providers.json`)

Re-verify before you generate: Higgsfield `models_explore(action:"recommend"|"get")`, Runway `whoami()`, ElevenLabs
`creative_get_flow_node_types()`. All three cost credits, so get the user's approval first. If none is available or
approved, deliver the prompt pack.

| Need | Higgsfield model (snapshot) | Also |
|---|---|---|
| general t2i / i2i | `nano_banana_pro` (strong text rendering), `flux_3_image` | Runway `generate_image`, ElevenLabs `creative_generate_image` |
| up to 10 references | `flux_3_image` | |
| realistic UGC / fashion / character | `soul_2` | |
| cinematic stills (up to 4K) | `cinematic_studio_2_5` | |
| style transfer / context edit | `flux_kontext` | ElevenLabs `creative_edit_image` |
| upscale | `upscale_image` tool | Runway `upscale_image` |
| outpaint | `outpaint_image` tool | |

---

## Workflows

Each workflow lists when to use it, which fields to emphasise, its references and a verified example. The grades
come from running the command shown.

### 1. Text-to-image
- **When:** no reference; a new image from words.
- **Emphasise:** subject specificity (≥ 3 concrete words), a lighting source and direction, a focal length.
- **Operation:** `t2i`.
- **Example:** `catana.py enhance "a ceramic coffee mug on a walnut table by a rainy window"` gives
  `[image · food · 16:9] QC A (100)`. "Coffee" selects the food preset: 45° hero angle, 100mm macro, a backlight
  window and steam.

### 2. Image-to-image (edit / restyle with the subject kept)
- **When:** the user supplies an image to change (background, season, materials).
- **Emphasise:** the `preserve` list first, then only the fields that change.
- **References:** one, role `subject` / `product` / `geometry`.
- **Operation:** `i2i`.
- Render a spec with `references` through `catana.py pack` or `render()`. The prompt ends with
  "Keep <preserve list> exactly as in the <role> reference."

### 3. Reference-image generation
- **When:** the subject must match a supplied photo (product, person, building).
- **Rule:** one reference per thing, each with its own preserve list. Lint warns when a list is missing:

  ```
  ["product reference has no 'preserve' list — the model may reinterpret it"]
  ```

### 4. Character consistency
- **When:** the same person appears across images (campaign, story, avatar).
- **Method:** describe the character once in a continuity bible (`characters: {"maya": "…"}`), write `@maya` in each
  shot, set `characters: ["maya"]`, and pass a `character` reference with
  `preserve: ["face identity", "hairstyle", "wardrobe"]`. `apply_bible()` injects the identical description and the
  negatives `identity drift, changing face or hairstyle, changing wardrobe`. `lint_sequence` fails any shot whose text
  drifted. See [PROMPT_ENGINEERING.md §5](PROMPT_ENGINEERING.md#5-continuity-bible-and-id-tokens-apply_bible).
- **Providers:** Higgsfield `soul_2` / `soul_cast` / reference elements, or a multi-reference model.

### 5. Product photography (hero shots)
- **Preset:** `product` (centred hero at about 60% of frame, low three-quarter angle, 100mm macro f/8, softbox key at
  45° plus strip rim, gradient sweep).
- **Emphasise:** materials (label print, glass, metal), controlled specular highlights, negative space for copy.
- **Negatives:** misspelled label text, extra/missing parts, fingerprints, floating shadows.
- **Example:** `catana.py enhance "product photo of a matte black perfume bottle on wet basalt"` gives
  `[image · product · 1:1] QC A (100)`.
- **With references:** a `product` reference with preserve
  `["exact bottle shape", "label artwork", "gold cap finish"]`, plus an optional `style` reference. The operation is
  then `multi_ref_image`, and the verified prompt ends:

  > … Keep exact bottle shape, label artwork, gold cap finish exactly as in the product reference. Match the color,
  > lighting and texture style of the style reference without copying its subject.

- A thin subject fails. `catana.py enhance "ceramic vase" --domain product --aspect 4:5` gives `QC B (80)` with an
  error: the subject is too thin. Add the material, colour, size and finish.

### 6. Architectural visualization (exterior and interior)
- **Preset:** `architecture` (two-point perspective, eye level at 1.6 m with verticals corrected, 24mm tilt-shift
  f/8, golden hour raking light, physically accurate materials).
- **Negatives:** bent verticals, impossible geometry, extra floors, fisheye.
- **References:** a render or photo as `geometry`, with preserve `building massing`, `number of floors`,
  `window layout`, `roof form`, and the reference camera position. Without geometry items, lint warns
  "architectural reference without geometry preservation".
- **Examples:**
  - `enhance "exterior render of a white concrete villa in Abu Dhabi at golden hour"` → `[image · architecture · 16:9] QC A (100)`
  - `enhance "interior of a minimalist Japanese living room with tatami floor and shoji screens"` → `QC A (100)`

### 7. Fashion photography
- **Preset:** `fashion` (full-length or ¾ figure off-centre, 85mm f/2.8, hard sun with bounce, fabric weave and
  drape, default aspect 4:5).
- **References:** `product` (the garment) with preserve `garment cut and silhouette`, `fabric pattern and color`,
  `logos and trims`. Add `character` for the model's identity.
- **Example:** `enhance "editorial fashion photo of a model in an oversized camel coat on a Paris rooftop"` →
  `[image · fashion · 4:5] QC A (100)`.

### 8. Cinematic portraits
- **Preset:** `character` (medium close-up, 85mm f/1.8, Rembrandt key plus hair light, pores and hair strands).
  Use the `cinematic` domain for a film-still look (anamorphic, haze, grain).
- **Lighting cues:** "low key", "neon", "candlelight" and "backlit" replace the preset light.
- **Examples:**
  - `enhance "cinematic portrait of an old fisherman in a storm, low key"` → `[image · character · 4:5] QC A (100)`
  - `enhance "magazine cover portrait of a jazz trumpeter in a smoky club, neon"` → `QC A (100)`
- **Portraits default to 4:5** (character domain). Pass `--aspect 2:3` or `--aspect 16:9` for other framings.

### 9. Commercial advertising (key visuals)
- **Presets:** `product`, `automotive` or `food`. Set `--platform` to get the delivery ratio.
- **Emphasise:** negative space for the headline (in `composition`), brand palette (in `color`), product fidelity
  (preserve list).
- **Examples:**
  - `enhance "luxury watch advertisement key visual, square"` → `[image · product · 1:1] QC A (100)`
  - `enhance "billboard key visual for an electric SUV on a salt flat at sunrise, 21:9"` → `[image · automotive · 21:9] QC A (100)`
  - `enhance "sneaker hero shot on a concrete plinth" --platform instagram_feed` → `[image · product · 4:5] QC A (100)`

### 10. Editorial photography
- **Presets:** `fashion` or `character`, with a narrative environment and a confident accent colour.
- **Emphasise:** environment storytelling and wardrobe, with headroom for masthead or copy when it's a cover.
- **Example:** `enhance "headshot of a confident female founder in a navy blazer, studio"` →
  `[image · character · 4:5] QC A (100)`. Use `--aspect 16:9` for a widescreen frame.

### 11. Concept art
- **Preset:** `concept_art` (epic wide, silhouette readability, 18mm deep focus, volumetric light, a limited palette
  with one accent hue).
- **Example:** `enhance "concept art of a floating city above a desert canyon"` →
  `[image · concept_art · 16:9] QC A (100)`.

### 12. Environment generation
- **When:** locations, backplates and worlds without a hero subject.
- **Presets:** `concept_art` for stylised work, `architecture` for built spaces.
- **Emphasise:** depth layers (foreground / mid / back), scale cues, time-of-day lighting.
- **Example:** `enhance "environment of a misty pine valley at sunrise with a wooden cabin by a lake"` →
  `[image · concept_art · 16:9] QC A (100)`. "Sunrise" set the lighting and `time_of_day: golden_hour`.

### 13. Multi-reference composition
- **When:** combining a product, a person and a location (or several products) in one frame.
- **Operation:** `multi_ref_image`, which needs ≥ 2 references, each with its own role and preserve list.
- **Providers:** Higgsfield `flux_3_image` (up to 10 references) or `nano_banana_pro`.
- **Rule:** name in the subject where each referenced element sits in the frame.

### 14. Style transfer
- **When:** a new image in the look of a reference, without its content.
- **Operation:** exactly one `style` reference gives `style_transfer`. Higgsfield `flux_kontext` or ElevenLabs
  `creative_edit_image` are options.
- To restyle the user's own image while keeping its subject, use two references, the subject (with preserve) plus the
  style. That becomes `multi_ref_image` and the subject stays protected.

### 15. Image enhancement (upscale / outpaint)
- **When:** the asset already exists and needs resolution, or an extended canvas for a new aspect ratio.
- **Select:** `python scripts/catana.py select --op upscale_image --available higgsfield,runway` or
  `--op outpaint --available higgsfield`.
- For outpainting, describe what the new area contains, keeping the same lighting and grade.

### 16. Variations
- **When:** options to choose from (A/B creatives, ad multiplier).
- **Method:** keep the spec and change one controlled axis per variant: `technical.seed`, background, palette,
  angle, or copy space. Set `id`s like `V1`, `V2`… so the run log and prompt packs stay traceable. Lint every variant;
  only the changed field should differ.
- For several independent generations, use the provider's batch tool where it has one (e.g. Higgsfield
  `generate_image_batch`) after a single cost quote.

---

## Delivering

- **Generated:** report the asset URL or path from the provider, the provider and model, and the cost, then log it
  (`catana.py log … --status succeeded --asset <url>`). The log refuses "succeeded" without an asset or job id.
- **Not generated** (no provider, or no approval): `catana.py pack spec.json --out prompts/`. This writes
  `<id>.md` + `<id>.json` and reports `"status": "prompt_only", "note": "nothing was generated"`. Say so plainly.
