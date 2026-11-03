# Prompt engineering engine

CATANA never sends a one-line idea to a generator. Every request becomes a **ShotSpec**, a structured production spec
with 13 fields. The spec is filled from the request and the domain preset, checked by the QC linter, and only then
rendered into a provider-ready prompt.

```
request ──enhance()──▶ ShotSpec ──apply_bible()──▶ ShotSpec (continuity) ──lint()──▶ ready? ──render()──▶ prompt + negative + params
```

Code: `engine/catana_core/spec.py`, `prompt_engine.py` and `qc.py`. Data: `data/presets.json`. CLI: `scripts/catana.py`.
The engine guarantees structure, specific defaults, ordering and consistency. **Claude writes the creative content.**
Treat `enhance()` output as a strong first draft: overwrite fields with real art direction before you generate.

Related: [IMAGE_GENERATION.md](IMAGE_GENERATION.md) · [VIDEO_GENERATION.md](VIDEO_GENERATION.md) ·
[CAMERA_MOVEMENTS.md](CAMERA_MOVEMENTS.md) · [PROVIDERS.md](PROVIDERS.md) · [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 1. The 13 fields

| # | Field | What it must say | Weak | Strong |
|---|---|---|---|---|
| 1 | `objective` | What the asset is for, the medium and the audience | "a nice image" | "Image — Product photography / commercial for Instagram feed: frosted glass serum bottle" |
| 2 | `subject` | The concrete subject: material, finish, colour, size, distinguishing details, action | "nice car" | "a vintage red Porsche 911 driving along a coastal cliff road" |
| 3 | `environment` | Where it is, plus scale cues | "outside" | "sweeping open road through dramatic landscape" |
| 4 | `composition` | Shot size, placement, negative space, leading lines | "good composition" | "low three-quarter front view, car occupying the lower two thirds with the road leading into the frame" |
| 5 | `camera` | Angle and height, or the camera move for video | "cool angle" | "low camera at bumper height on a tracking vehicle" |
| 6 | `lens` | Focal length, aperture, lens character | "HD" | "35mm lens, f/4, slight motion blur on wheels and background" |
| 7 | `lighting` | Key source, direction, quality, fill, rim, time of day | "stunning lighting" | "low raking sun skimming the bodywork, long specular highlights tracing the body lines" |
| 8 | `materials` | Surfaces, textures and how they react to light | "realistic" | "deep multi-layer paint with clear-coat reflections, machined alloy wheels, real tyre rubber" |
| 9 | `motion` | Video only: what moves, how and how fast | "moving" | "the car glides forward with wheels turning, reflections sliding across the bodywork" |
| 10 | `style` | Rendering family and artistic direction | "8k masterpiece" | "premium automotive commercial cinematography" |
| 11 | `color` | Grade and palette | "vibrant" | "rich contrast, deep blacks, glossy highlights, cool shadows against warm sunlight" |
| 12 | `technical` | `aspect_ratio`, `duration`, `fps`, `resolution`, `seed`, `platform`, `motion_intensity` (low / medium / high), `time_of_day` | — | `{"aspect_ratio": "16:9", "duration": 8.0, "motion_intensity": "low"}` |
| 13 | `negative` | Artifacts this model and domain tend to produce | "bad quality" | "warped body panels, mismatched or melting wheels, wrong badge or logo, wheels not touching the road" |

The spec also carries these fields, all validated by `ShotSpec.validate()`:
- `modality`: `image` or `video`.
- `domain`: one of the presets below.
- `camera_moves`: `[{"id": "dolly_in", "speed": "slow|medium|fast", "direction", "from", "to"}]`.
- `references`: `[{"source", "role", "preserve": [...]}]`.
- `characters`: bible ids used in this shot.
- `id` and `notes`.

Valid reference roles are `subject`, `character`, `product`, `style`, `composition`, `geometry`, `environment`,
`first_frame`, `last_frame` and `motion`. Aspect ratios are `16:9 9:16 1:1 4:5 5:4 4:3 3:4 3:2 2:3 21:9`.
Durations must be between 0 and 600 s. Unknown fields are rejected:

```
$ python scripts/catana.py lint bad.json      # {"subject": "x", "colour": "red"}
error: unknown spec fields: colour            (exit 2)
```

## 2. How `render()` orders a prompt

Models weight the start of a prompt most. `render()` therefore leads with what matters most for each modality.

**Image** (`modality: image`):
1. subject, environment
2. composition, camera, lens
3. lighting
4. materials
5. style, color
6. reference preservation clauses

**Video** (`modality: video`):
1. **camera move phrase(s)** (from the camera library): subject, motion
2. environment
3. composition, camera (only when a move is set), lens
4. lighting
5. materials
6. style, color
7. `<intensity> motion intensity, temporally consistent, no flicker, stable identity and geometry from first to last frame, <N>-second shot`
8. reference preservation clauses

Negatives are returned separately as `negative_prompt` for providers that have a negative field. Use
`--inline-negative` (`negative_mode="inline"`) for providers that don't: the prompt then ends with `Avoid: …`.
`params` carries `aspect_ratio`, `duration`, `resolution`, `fps`, `seed` and the reference list.

Reference clauses, generated from `references[]`:

| Role | Clause appended |
|---|---|
| any role with `preserve: [...]` | "Keep <preserve list> exactly as in the <role> reference." |
| `first_frame` (no preserve) | "Start from the first-frame image without altering its composition." |
| `last_frame` (no preserve) | "End exactly on the last-frame image." |
| `style` | "Match the color, lighting and texture style of the style reference without copying its subject." |

## 3. Domain presets (`data/presets.json`)

Presets fill only the fields the request leaves empty. Every default is deliberately specific. The `general` preset
supplies the base, and the domain overrides it.

| Domain | Defaults (abridged) | Domain negatives (examples) | Shot length |
|---|---|---|---|
| `general` | rule-of-thirds, eye-level, 35mm f/4, soft key from camera left + fill + rim, photorealistic | blurry, extra fingers, warped text, watermark | 3–5 s |
| `product` | centred hero, 60% of frame, low three-quarter angle, 100mm macro f/8, softbox key 45° + strip rim, gradient studio sweep | misspelled label text, extra/missing parts, fingerprints, floating shadows | 2–4 s |
| `architecture` | two-point perspective, eye level 1.6 m, verticals corrected, 24mm tilt-shift f/8, golden hour raking sun, travertine/concrete/glazing, landscaped site | bent verticals, impossible geometry, extra floors, fisheye | 4–6 s |
| `fashion` | full-length/¾ figure off-centre, 85mm f/2.8, hard sun + bounce or beauty dish, fabric weave and drape | distorted hands, malformed garments, plastic skin, warped logos | 2–4 s |
| `character` | medium close-up, 85mm f/1.8, Rembrandt key + hair light, pores and hair strands | waxy skin, identity drift, changing hairstyle/wardrobe | 3–5 s |
| `cinematic` | widescreen depth layers, anamorphic 40mm f/2.8, motivated practicals + haze, 35mm film still, teal/amber grade with grain | video-game look, flat lighting, inconsistent characters | 3–6 s |
| `ugc` | vertical selfie framing, handheld phone at arm's length, 26mm-equivalent, window daylight, lived-in home, no cinematic grade | studio lighting, cinematic grade, stock-photo look, lip-sync mismatch | 2–4 s |
| `social` | 9:16 safe-zone framing, dynamic opening move, 24mm, high-key, high-contrast mobile grade | slow start, content in caption zones, letterboxing | 1–3 s |
| `concept_art` | epic wide, strong silhouettes, 18mm deep focus, volumetric shafts, painterly but believable | muddy values, cluttered silhouettes, text | 4–6 s |
| `automotive` | low ¾ front view, bumper-height tracking camera, 35mm f/4 with wheel blur, raking sun on body lines, clear-coat paint | warped panels, melting wheels, wrong badge, floating car | 2–4 s |
| `food` | 45° hero angle, 100mm macro f/4, backlight for glow + front bounce, steam and condensation, rustic tabletop | grey tones, plastic food, floating food | 2–4 s |

`product`, `architecture`, `fashion`, `character` and `automotive` also list `preserve_on_reference`: the items to
put in a reference's `preserve` list. See [IMAGE_GENERATION.md](IMAGE_GENERATION.md).

```
$ python scripts/catana.py presets
```

## 4. Natural-language parsing (`enhance()`)

```
$ python scripts/catana.py enhance "8 second video of a red Porsche 911 on a coastal road, aerial reveal"
[video · automotive · 16:9 · 8s]  QC A (100)

PROMPT
Slow aerial drone reveal, gliding up and over the foreground to reveal the location at scale: a red Porsche 911 on a coastal road, the car glides forward with wheels turning, reflections sliding across the bodywork. …
```

What `enhance()` detects from the request:

| Signal | How it is detected | Effect |
|---|---|---|
| **Domain** | Keyword scores from each preset; a UGC keyword (`ugc`, `testimonial`, `unboxing`, `grwm`…) always wins | Picks the preset. "UGC review of a serum" is `ugc`, not `product` |
| **Platform** | Aliases in `data/platforms.json` (`reel`, `tiktok`, `shorts`, `linkedin`, `story`, `ad`…) | Sets `technical.platform` and its aspect ratio. A general request for a 9:16 platform becomes `social` |
| **Aspect ratio** | Explicit `16:9` / `9:16` / `4:5`…, or the words `vertical`, `square`, `widescreen`/`horizontal` | `technical.aspect_ratio` |
| **Duration** | `8 second`, `10s`, `2 minutes` | `technical.duration`. It also forces video modality |
| **Modality** | Video words (video, clip, reel, commercial, animate…) + duration + dynamic camera moves vs. image words (photo, still, poster, packshot…) | `image` or `video` |
| **Camera moves** | Any alias in the camera library, longest match first; a speed word (slow, gentle, fast, rapid…) in the 30 characters before it | `camera_moves` with speed |
| **Lighting cue** | golden hour, sunset, sunrise, blue hour, twilight, dusk, night, moonlight, neon, candlelight, overcast, midday, noon, studio, backlit, low key, high key | Replaces the preset lighting with a full description and sets `technical.time_of_day` |

Defaults when the request doesn't say:
- **Aspect:** platform ratio, else 16:9 for video / cinematic / architecture, 4:5 for fashion, 1:1 for product, else 16:9.
- **Video duration:** max(5, the preset's longest shot).
- **Motion intensity:** `high` for fast moves or social; `low` for architecture, product and cinematic; else `medium`.
- **Camera move** (marked `"auto": true`):

| Domain | Default move |
|---|---|
| product | `orbit_360` if ≥ 6 s, else `push_in` |
| architecture | `dolly_in` |
| ugc | `handheld` |
| social | `push_in` |
| fashion | `tracking` |
| character | `push_in` |
| cinematic | `dolly_in` |
| concept_art | `aerial_reveal` |
| others | `push_in` |

**Subject cleaning.** The subject keeps the user's words but drops everything already captured elsewhere:
- request verbs ("create a…")
- leading format adjectives ("luxury cinematic 8 second")
- format nouns ("product photo of", "UGC tiktok of")
- aspect, duration, camera-move phrases and the lighting cue

So "luxury cinematic 8 second video of a modern villa in Abu Dhabi at golden hour, slow dolly in, 16:9" becomes the
subject "a modern villa in Abu Dhabi". The golden hour moves into `lighting`, and the dolly into `camera_moves`.

Overrides: `--domain`, `--modality`, `--aspect`, `--duration`, `--platform` (validated against `catana.py platforms`).
`--json` prints `{spec, render, qc}`.

## 5. Continuity bible and `@id` tokens (`apply_bible()`)

Every shot of a sequence must describe recurring things with **identical words**, or models drift. Put the locked
descriptions in a bible:

```json
{"characters": {"maya": "Maya, a 30-year-old woman with a short black bob and a mustard wool coat"},
 "products": {}, "locations": {},
 "style": "cinematic film still, 35mm", "grade": "teal and amber", "palette": "mustard, teal, slate",
 "lens_package": "", "lighting": "", "negative": []}
```

`apply_bible(spec, bible)` does the following:
- Replaces `@maya` (any `@id` from characters, products or locations) in subject, environment, motion and composition
  with the locked text.
- Appends the description of every id in `spec.characters` that isn't already in the subject.
- Forces `style` to the bible style, and `color` to "grade, palette: …".
- Fills `lens` and `lighting` from the bible only when the shot left them empty. A per-shot lighting override survives.
- Merges bible negatives, and adds `identity drift, changing face or hairstyle, changing wardrobe` when characters are
  used.

Verified output:

```
subject: Maya, a 30-year-old woman with a short black bob and a mustard wool coat waits on a rainy platform
color:   teal and amber, palette: mustard, teal, slate
```

`qc.lint_sequence(shots, bible=…)` fails (error) if a shot that lists a character doesn't contain its exact bible
text. The AI Director (`catana.py plan compile`) applies the bible to every shot automatically.

## 6. Specialised engines per domain

A "specialised engine" is a domain preset plus a studio playbook. The playbooks live in `references/` (maintained
separately from these docs).

| Engine | Preset | What it adds |
|---|---|---|
| Image | `general` + subject domain | still-image ordering, angle instead of move ([IMAGE_GENERATION.md](IMAGE_GENERATION.md)) |
| Video | any + camera library | move-first ordering, motion intensity, temporal clause ([VIDEO_GENERATION.md](VIDEO_GENERATION.md)) |
| Character | `character` + bible | identity preservation, character negatives, `@id` tokens |
| Product advertising | `product`, `automotive`, `food` | packshot lighting, label/badge fidelity, product preserve list |
| Architecture | `architecture` | corrected verticals, geometry preservation, reference camera position |
| Fashion | `fashion` | garment fidelity, fabric behaviour, hands |
| UGC | `ugc` | handheld phone realism, no cinematic grade, VO via VoiceStudio |
| Cinematic storytelling | `cinematic` + Director | beats, motivated light, continuity bible, EDL |
| Social media | `social` + `data/platforms.json` | safe zones, hook in the first 1–2 s, platform ratio and length |

## 7. Quality control checklist (`qc.lint()`)

Run before every generation: `python scripts/catana.py lint spec.json [--provider p --model m --platform p]`.
Exit code 0 means ready, 1 means there are errors.

| Check | Severity | Fires when |
|---|---|---|
| completeness | error | `subject` empty, or video `motion` empty |
| completeness | warning | objective, environment, composition, camera, lens, lighting, materials, style or color empty. Environment is skipped when the subject already places itself ("in / at / on / along / near …") |
| specificity | error | subject has fewer than 3 meaningful words after removing filler |
| specificity | warning | filler words (beautiful, amazing, stunning, 8k, 4k, masterpiece, hyperrealistic, award-winning…) anywhere |
| lighting | warning | lighting names no source or direction (key, rim, softbox, sun, window, neon, golden hour…) |
| camera | warning | lens has no focal length or lens type |
| composition | warning | composition gives no framing (close-up, medium, wide, thirds, negative space…) |
| camera | info | still with no angle or height |
| camera | warning | video with no camera move and no explicit static camera |
| camera | error / warning | conflicting moves (library `conflicts`); > 2 simultaneous moves; a clip shorter than the move's `min_seconds` |
| camera | info | camera moves on a still (ignored) |
| motion | warning | motion has no concrete action verb |
| motion | warning | more actions than ~1 per 2.5 s (counted as clauses containing an action verb; parentheses ignored) |
| motion | info | high intensity on a ≥ 8 s architecture or product shot (geometry warps) |
| temporal | info | "morphs / transforms into / becomes" without a described transition |
| lighting | error | conflicting times of day (golden hour, blue hour, night, midday) |
| realism | warning | style mixes photoreal and illustrated vocabularies |
| technical | warning | no aspect ratio; unknown platform |
| composition | warning | aspect ≠ platform ratio; panoramic composition in a vertical frame |
| technical | info | duration far from the platform's usual length |
| reference | error | `first_frame` / `last_frame` reference on a still |
| reference | warning | subject / character / product / geometry / composition reference without `preserve` |
| reference | warning | architecture reference without geometry items (massing, floors, windows, façade…) |
| reference | info | last frame without a first frame; several recurring characters in one shot |
| technical | warning | video without duration |
| technical | info | video longer than 15 s (split it) |
| technical (provider) | error | the provider doesn't support the needed operation; the duration is outside the model's range or the provider max |
| technical (provider) | warning | aspect ratio not in the provider's list |
| negative | warning | no negatives; a term both requested and forbidden |

**Scoring.** Start at 100, then subtract 20 per error, 8 per warning and 2 per info, floored at 0.
Grades: **A** ≥ 90, **B** ≥ 75, **C** ≥ 60, **D** below. `ready` = no errors.
`lint_sequence()` adds continuity checks across shots:
- one aspect ratio per sequence
- identical style and grade wording
- time-of-day jumps not marked as a transition
- the same move three shots in a row
- bible character text
- total duration within ±15% of the target

### Worked example: weak → strong

`weak.json`:

```json
{"subject": "nice car", "style": "amazing, 8k, masterpiece", "modality": "video", "technical": {"duration": 4}}
```

```
$ python scripts/catana.py lint weak.json          # exit 1
score 0  grade D  ready False  {'error': 2, 'warning': 12, 'info': 0}
  error   completeness motion       | motion is empty
  error   specificity  subject      | subject is too thin: 'nice car' -> name the subject concretely: what it is, material/finish, size, colour, distinguishing details, action
  warning completeness objective / environment / composition / camera / lens / lighting / materials / color | … is empty
  warning specificity  *            | generic filler words carry no visual information: 8k, amazing, masterpiece, nice
  warning camera       camera_moves | video has no camera movement or explicit 'static' camera
  warning technical    aspect_ratio | no aspect ratio
  warning negative     negative     | no negatives
```

Rewrite the request concretely and let the engine fill the rest:

```
$ python scripts/catana.py enhance "8 second video of a vintage red Porsche 911 driving along a coastal cliff road at golden hour, aerial reveal" --json > strong_full.json
# take .spec into strong.json
$ python scripts/catana.py lint strong.json        # exit 0
{"score": 100, "grade": "A", "ready": true, …}
```

The same spec checked against a model's limits:

```
$ python scripts/catana.py lint long.json --provider higgsfield --model seedance_2_0     # duration 20 s
error  seedance_2_0 accepts 4–15 s, spec asks 20 s
info   20 s in one generation — consistency drops on long clips
```
