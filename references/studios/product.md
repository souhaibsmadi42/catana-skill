# Product Studio — product visualization

Product hero shots, rotating product videos, macro, exploded views, floating products, material transformations,
commercial lighting. Use for `/catana:hero-shot`, `/catana:product-commercial` (with `studios/advertising.md`), e-commerce and
launch visuals. Preset: **`product`** (centred hero, 100mm macro f/8, softbox key + strip rim, gradient sweep,
label/part negatives). Food and automotive have their own presets (`food`, `automotive`).

## Inputs

The product's exact name, shape, materials, colours and finish; packshots (strongly preferred — the label and form
must survive); the use (marketplace listing, hero banner, ad, launch video); background preference; ratio. Ask for
photos if the product is real and specific.

## Reference preservation (always, for a real product)

Attach the packshot as a reference and list what must not change:

```json
{"source": "packshot_front.png", "role": "product",
 "preserve": ["exact product shape and proportions", "logo and label artwork", "brand colours", "material finish", "cap and nozzle design"]}
```

Put the same text in `bible.products.<id>` for sequences. Generated text on labels is unreliable: keep labels large
and frontal, or composite the real label/logo in post. Never invent features or certifications.

## Shot types

| Shot | Spec moves / notes | Camera ids |
|---|---|---|
| Hero still | centred or rule-of-thirds, low three-quarter angle, negative space for copy | — |
| Rotating product (turntable) | **`orbit_360` needs ≥ 6 s**; product stationary, constant distance; describe the back of the product too | `orbit_360` (+ `crane_up`) |
| Macro detail | 100mm macro, shallow depth; one material story (brushed metal, droplet, stitching) | `push_in`, `rack_focus` |
| Exploded view | components separated along one axis, equal gaps, floating in studio space, labels added in post | `static`, `arc`, slow `dolly_out` |
| Floating product | levitating above a backdrop, soft contact shadow below, slight rotation | `static`, `push_in`, `orbit_360` |
| Material transformation | one material becomes another (glass → liquid, wireframe → final); describe the transition explicitly | `static`, `push_in` |
| In-use | hands or a person using it; product stays the hero | `tracking`, `rack_focus` |
| Flat lay / range | top-down grid of variants | `top_down` |
| Impact moment | splash, crush, burst frozen | `bullet_time` |

## Lighting setups (write into `lighting`)

- **Gradient sweep:** product on a seamless sweep lit to a vertical gradient, large overhead softbox, two strip
  rims tracing the silhouette, white bounce fill.
- **Rim + strip (dark):** black background, two strip softboxes behind left and right for edge lines, small top
  key, no fill — premium electronics, bottles.
- **Clamshell:** soft key above and fill below the product axis — even, shadowless beauty light for cosmetics.
- **Backlit liquid:** light panel behind translucent liquid/glass for glow and colour, black flags at the sides for
  dark edges, small front kick for the label.
- **Hard sun:** single hard source with crisp shadow shapes (gobo leaves, blinds) — lifestyle/summer.
- **Specular control (metal/glass):** large diffused sources with black flags to shape reflections; mention
  "controlled reflections, no hot spots".

## Workflow

1. Single image: `python <skill>/scripts/catana.py enhance "<product photo request>" --json` → add `references`,
   choose a lighting setup, `catana.py lint spec.json`, then generate (i2i / multi_ref_image with the packshot) or pack.
2. Product video: same spec with `--modality video`; turntables ≥ 6 s, macro moves 3–5 s, low motion intensity.
3. Product film/commercial: `plan new "<product> launch film" --domain product --duration 15`, bible product, compile.
4. Variants (colours, backgrounds): copy the spec and change one field; same seed if the provider supports it.

## Verified prompt patterns (`catana.py enhance`, QC A 100)

```text
product video of a matte black wireless headphone rotating on a mirrored plinth, orbit 360, 8 seconds
macro product photo of a skincare serum dropper releasing a golden droplet over the bottle
product photo of a sneaker floating above a pastel gradient backdrop with its laces drifting
```

The first renders to (excerpt): *"Slow 360-degree orbit around the subject at constant distance and height, subject
held in centre frame: a matte black wireless headphone rotating on a mirrored plinth, the product turns slowly on its
axis while highlights glide across its surface. Seamless gradient studio sweep … 100mm macro lens, f/8 … Large
softbox key at 45 degrees, strip-light rim tracing the silhouette …"* Note: orbit + the product also rotating doubles
the apparent speed — for a clean turntable choose one (camera orbit **or** product rotation; with `static` camera).

Pattern: `product <photo|video> of <product: finish + colour + material> <on/above surface> <one action>, <move>, <duration>`.

## Provider routing

| Need | Operation | Options (verify first) |
|---|---|---|
| Packshot-faithful still | i2i, multi_ref_image | Higgsfield `nano_banana_pro`, `flux_3_image`, `seedream_v4_5`, `gpt_image_2` |
| Background swap / extension | i2i, outpaint | `flux_kontext`, `flux_2_pro_outpaint`, `remove_background` |
| Product video, identity kept | i2v, multi_ref_video | `seedance_2_0` (product consistency, multi-SKU), `kling4_0`, `minimax_h3` |
| Ad formats | t2v | `marketing_studio_video`, Ads Studio for image ads |
| Upscale for print/marketplace | upscale_image | `upscale_image` / `topaz_image` |
| Data/feature callouts animation | motion_graphics | CATANA motion engine (free) |

## QC checklist

- [ ] Product reference attached with a `preserve` list; nothing invented
- [ ] One lighting setup named with sources and directions
- [ ] Turntable ≥ 6 s, camera or product rotates (not both)
- [ ] Label legible or planned for post compositing
- [ ] Background clean; negative space for copy where needed
- [ ] Contact shadow present (no floating unless intended)

## Failure modes → fixes

| Symptom | Fix |
|---|---|
| Shape drifts during rotation | shorter orbit (half turn = `arc`), lower motion intensity, product-consistency model |
| Extra parts / missing buttons | `preserve` list + negatives "extra or missing product parts"; frontal reference |
| Plastic look | name real materials and micro texture; specular control lighting |
| Floating shadow | "soft contact shadow directly beneath" in environment |
| Garbled text | composite real artwork in post |

## Deliverables

Hero still(s) per ratio · turntable/macro clips · lighting setup notes · variant set · prompt pack / run log ·
marketplace crops (1:1, 4:5) when requested.
