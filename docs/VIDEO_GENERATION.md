# Video generation

How CATANA directs AI video: a single clip, a multi-shot sequence, or a full production. A video spec is an image
spec plus **motion, camera movement, duration and continuity**. Two engines can make video:
- **AI video providers** (connectors, credits, approval first)
- the **CATANA motion engine** (local, free, code-rendered motion graphics; see the `catana` skill workflow)

Related: [PROMPT_ENGINEERING.md](PROMPT_ENGINEERING.md) · [CAMERA_MOVEMENTS.md](CAMERA_MOVEMENTS.md) ·
[IMAGE_GENERATION.md](IMAGE_GENERATION.md) · [PROVIDERS.md](PROVIDERS.md) · [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Rules that hold for every clip

These rules match what `qc.lint()` enforces:

| Rule | Why | QC |
|---|---|---|
| **4–10 s per generation**; split anything longer into shots | identity and geometry drift grows with length | info above 15 s; error if outside the model's range |
| **About one action per 2.5 s**, written in `motion` | models rush or drop actions | warning: "N actions in a D s clip" |
| **At most 2 simultaneous camera moves** (rack focus and dutch angle don't count) | models follow one or two moves reliably | warning above 2; error on library conflicts (e.g. dolly in + dolly out) |
| **Clip ≥ the move's `min_seconds`** (orbit 360 needs about 6 s, aerial reveal and FPV 4 s, dolly 3 s) | short clips blur the move | warning |
| **A camera move or an explicit static camera** | otherwise models invent wobble | warning |
| **One time of day per shot**; day-to-night only as a described transition or across shots | lighting continuity | error within a shot; sequence warning for unmarked jumps |
| **Describe transformations** ("a wipe of light sweeps across, revealing…") | bare "morphs into" flickers | info |
| **Duration within the model's range** | the request fails otherwise | `lint --provider p --model m` error |

### Controls (where each one lives in the spec)

| Control | Field | Notes |
|---|---|---|
| Camera movement | `camera_moves: [{"id", "speed"}]` | ids from the [camera library](CAMERA_MOVEMENTS.md). `render()` leads the prompt with the canonical phrase |
| Camera direction | `camera_moves[].direction` (pedestal, pan), `from` / `to` (rack focus), `camera` (angle and height) | e.g. `catana.py camera phrase pedestal` → "Slow pedestal up, camera rising straight vertically with the lens kept level, no tilt" |
| Subject movement | `motion` | concrete verbs: walks, pours, turns, rises… |
| Scene movement | `motion` / `environment` | wind, water, steam, traffic, clouds |
| Motion intensity | `technical.motion_intensity`: `low` / `medium` / `high` | becomes "low motion intensity" in the prompt. Keep architecture and product low |
| Duration | `technical.duration` | check against the model range below |
| Frame composition | `composition`, `technical.aspect_ratio`, `technical.platform` | vertical frames need vertical composition (stack layers, tilt or pedestal) |
| Temporal consistency | added automatically | "temporally consistent, no flicker, stable identity and geometry from first to last frame" |
| Lighting continuity | `lighting`, `technical.time_of_day`, bible `lighting` | `lint_sequence` flags unmarked time-of-day jumps |
| Visual continuity | continuity bible (`style`, `grade`, `palette`, `lens_package`, characters) | `apply_bible()` makes the wording identical in every shot |

### Model durations (Higgsfield snapshot 2026-11-03, `data/providers.json` `known_models`)

Re-verify with `models_explore(action:"get", model_id:…)` before you generate. Pass `--model` to `lint` to enforce
the range.

| Model | Operations | Seconds | Notes |
|---|---|---|---|
| `seedance_2_5` | t2v, multi-ref, v2v edit, extension | 4–30 | image, video and audio references |
| `seedance_2_0` | t2v, i2v, first/last, multi-ref | 4–15 | identity and product consistency |
| `kling4_0` | t2v, i2v, first/last, multi-ref, v2v | 3–30 | |
| `kling_o3_image_reference` | t2v, multi-ref, multi-shot | 3–15 | up to 7 images |
| `cinematic_studio_video_4_0` | t2v, multi-ref, v2v, extension | 4–30 | camera body, lens, aperture, lighting-rig controls |
| `minimax_h3` | t2v, i2v, first/last, multi-ref | 4–15 | |
| `marketing_studio_video` | t2v, i2v | 12–15 | UGC / product ad formats with avatars |
| `hf_mult_motion_control` | motion transfer | — | |
| `sync_so` | lip-sync | — | |

Runway (`generate_video`, `generate_multishot_video`, `generate_product_marketing_video`, `edit_video`,
`expand_video`) and ElevenLabs (`creative_generate_video`) are snapshotted from tool schemas. Confirm models with
`whoami()` / `creative_get_flow_node_types()`.

### Operation from references (`qc.needed_operation`, video)

| References | Operation |
|---|---|
| none | `t2v` |
| `first_frame` | `i2v` |
| `first_frame` + `last_frame` | `first_last` |
| `motion` (a reference video) | `motion_transfer` |
| any other reference(s) | `multi_ref_video` |
| editing / extending an existing clip | select `v2v` / `extend_video` / `multi_shot` explicitly with `catana.py select --op …` |

---

## Workflows

The grades shown come from the command next to them.

### 1. Text-to-video
- **Example:**
  `catana.py enhance "10 second cinematic video of a lone astronaut walking across red dunes, tracking shot"` →
  `[video · cinematic · 16:9 · 10s] QC A (100)`. The prompt opens "Slow tracking shot moving alongside the subject at
  matching speed, background streaming past: …" and ends "…, 10-second shot."

### 2. Image-to-video
- **When:** a still (yours or a generated keyframe) must start the clip.
- **Spec:** a `first_frame` reference. The prompt gets "Start from the first-frame image without altering its
  composition."
- **Operation:** `i2v`. A `first_frame` reference on a still is a QC error.
- **Example:** `catana.py enhance "animate this photo of a sailboat at sunset, slow push in" --modality video` plus the
  reference. Then `catana.py select --op i2v --available higgsfield,runway --duration 5 --aspect 16:9` ranks Higgsfield
  first, Runway second, prompt pack last, with `requires_approval: true` on both paid options.

### 3. Video-to-video (restyle / edit a clip)
- **Operation:** `v2v`. Providers: Higgsfield `seedance_2_5` / `kling4_0` / `kling_video_edit`, Runway `edit_video`.
- **Spec:** describe only what changes. Preserve identity and layout through a `subject` or `geometry` reference with
  a preserve list.

### 4. First-frame and last-frame
- **Spec:** `first_frame` + `last_frame` references give `first_last`. The prompt ends "Start from the first-frame
  image… End exactly on the last-frame image."
- **Use:** controlled transitions (day → night, construction → completion, product open → closed).
- **Keep:** the camera move compatible with both frames: a slow push or a static camera.

### 5. Multi-reference video
- **Operation:** `multi_ref_video`. Give each reference a role (`character`, `product`, `environment`) and a preserve
  list.
- **Models:** `seedance_2_0` / `2_5`, `kling_o3_image_reference` (up to 7 images), `minimax_h3`.

### 6. Character consistency across shots
- Write the bible once (`characters: {"maya": "…"}`), use `@maya` plus `characters: ["maya"]` in every shot, and pass
  a `character` reference.
- `apply_bible()` makes the description identical and adds identity negatives. `lint_sequence` fails a shot whose
  character text drifted.
- Higgsfield reference elements or Soul IDs give the strongest identity lock.

### 7. Scene continuation
- Use the **last frame of shot N as the `first_frame` of shot N+1** and keep bible lighting and grade.
- Mark deliberate changes in the shot's `notes`/`motion` with the word "transition". Otherwise `lint_sequence` warns
  "time of day jumps…".

### 8. Video extension
- **Operation:** `extend_video` (Higgsfield `seedance_2_5` / `cinematic_studio_video_4_0` with
  `extension_mode: forward|backward`; Runway `expand_video`).
- Prompt only the continuation: what happens next, with the same camera move and speed.

### 9. Video transformation
- **Example:** day-to-night, season change, material swap.
- Write the transition explicitly. Lint gives info when a "morph" has none:

  ```
  ['a transformation without a described transition tends to flicker']
  ```

- Prefer `first_last` with two keyframes. Keep the camera static or slow, and intensity low.

### 10. Cinematic sequences and short films
- **AI Director:**

  ```
  $ python scripts/catana.py plan new "cinematic short film about a lighthouse keeper's last night" --duration 60 --domain cinematic --out film.json
  wrote film.json: 13 shots, 60 s, 16:9 — fill the creative fields, then `plan compile`
  $ python scripts/catana.py plan compile film.json --out film_out
  wrote film_out/compiled.json and storyboard.md — 13 shots, 60.06 s; shots needing fixes: none; sequence ready: True
  ```

- Beats: opening image → setup → inciting → escalation → climax → resolution. Camera moves vary within a beat.
- **Fill in before compiling:** the concept, the bible, and each shot's subject, action, VO and SFX.
- `compiled.json` holds a keyframe image prompt and a video prompt per shot, the VO plan and the EDL.
  `storyboard.md` is the human document.

### 11. Product commercials
- **Presets:** `product` (default move: `orbit_360` when ≥ 6 s, else `push_in`), `automotive`, `food`.
- **Example (warning shown):**
  `enhance "4 second product video of a brushed steel espresso machine, slow orbit 360"` →
  `QC A (92)`, warning "'Orbit 360' needs about 6 s to read; clip is 4 s". Lengthen the clip to 6 s or use `push_in`.
- **Director beats:** hook → reveal → detail → use → benefit → hero → end card.

### 12. UGC videos
- **Preset:** `ugc`. Handheld phone at arm's length, 26mm-equivalent, window daylight, no cinematic grade, 9:16.
  The Director keeps every UGC shot `handheld`.
- **Example:** `enhance "UGC tiktok of a girl unboxing sneakers"` → `[video · ugc · 9:16 · 5s] QC A (100)`.
- **Voice:** free via VoiceStudio (`catana.py voice speak` / `voice plan`); see [PROVIDERS.md](PROVIDERS.md).
  Higgsfield `marketing_studio_video` (12–15 s, avatars) is the paid alternative.

### 13. Social media videos
- **Preset:** `social`. Use `--platform` (`instagram_reels`, `tiktok`, `youtube_shorts`, `linkedin`…) for ratio, safe
  zones and length.
- **Examples:**
  - `enhance "instagram reel of a barista pouring latte art, fast whip pan"` → `[video · social · 9:16 · 5s] QC A (100)`
  - `enhance "8 second video of a red Porsche 911 on a coastal road, aerial reveal" --platform tiktok` →
    `[video · automotive · 9:16 · 8s] QC A (100)`
- Hook in the first 1–2 s (platform `hook_seconds`). Keep text out of the caption safe zones.

### 14. Architectural cinematic videos
- **Preset:** `architecture` (default move `dolly_in`, low intensity, environmental motion only).
- **Example:**

  ```
  $ python scripts/catana.py enhance "8 second video of the villa at golden hour, slow dolly in"
  [video · architecture · 16:9 · 8s]  QC B (80)
    error   specificity: subject is too thin: 'the villa' -> name the subject concretely: what it is, material/finish, size, colour, distinguishing details, action
  ```

  Name the building: "a two-storey white concrete villa with bronze glazing and a cantilevered roof".
- **References:** `first_frame` (the render) plus `geometry` with `building massing`, `number of floors`,
  `window layout`, `roof form`.
- **Director beats:** establish (aerial reveal) → approach (dolly in) → threshold (steadicam) → flow (parallax) →
  detail (push in) → life (tracking) → hero (crane up) → end card.
- **Day-to-night / construction-to-completion:** use `first_last`, or a per-shot `lighting` + `time_of_day` override
  with "transition" in notes.

### 15. Multi-action clips (what not to do)

```python
s.motion = "she spins, then jumps, then lands, then bows, then walks off stage"   # 6 s clip
# lint → warning: 4 actions in a 6 s clip — models rush or drop actions
s.motion = "she completes one slow pirouette and settles into a bow"             # → 100
```

---

## Sound for video

| What | Free path |
|---|---|
| Voiceover | VoiceStudio: `catana.py voice plan compiled.json --out-dir build` writes `vo_<shot>.wav` and `vo.json` |
| SFX | the CATANA motion mixer (procedural, mixed to picture cues) |
| Music | the user's own track |

With a motion-engine project, `audio/mix.py` places the VO cues and ducks the music about 8 dB and the SFX about 3 dB
under the voice. Paid audio (ElevenLabs, Runway, Higgsfield) never runs by default: audio is `free_only` (see
[PROVIDERS.md](PROVIDERS.md)).
