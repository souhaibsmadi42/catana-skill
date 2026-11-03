# AI Director — idea to production plan

Use when the user gives an idea ("a luxury cinematic commercial for a modern villa in Abu Dhabi") and wants a whole
production, not a single prompt: `/catana:video-director`, `/catana:storyboard`, `/catana:scene-builder`, `/catana:cinematic-video`,
`/catana:architecture-film`, `/catana:product-commercial`, `/catana:campaign-studio`, `/catana:ugc-video` all run through this workflow.

The engine (`engine/catana_core/director.py`) guarantees structure: beats and pacing from the domain, timing maths,
camera variety, continuity wording through the bible, per-shot and sequence QC. **You** write the creative content:
concept, visual direction, the bible, and each shot's subject, action, VO and SFX.

`<skill>` below = the skill root (in a plugin: `${CLAUDE_PLUGIN_ROOT}`).

## Workflow

1. **Understand the objective.** What is it for (sell, launch, brand, tell a story)? Platform? Length? Real assets
   (logo, product photos, renders, a music track)? Ask only for what you cannot infer — usually platform/length and
   any reference images. Say what you assumed.
2. **Write the creative concept** in 2–3 sentences, a **logline** (one sentence) and the **visual direction** (pace,
   palette, lens feel, how light behaves, what the camera never does).
3. **Create the plan skeleton:**
   ```bash
   python <skill>/scripts/catana.py plan new "<idea>" --duration 40 [--platform instagram_reels] [--domain architecture] [--aspect 16:9] --out plan.json
   ```
   Domain is auto-detected from the idea (`general, product, architecture, fashion, character, cinematic, ugc, social,
   concept_art, automotive, food`); `--platform` sets aspect ratio, fps and default length from `data/platforms.json`.
   Shot count = duration ÷ the domain's average shot length; beats come from the domain template (table below). Short
   durations drop later beats — check the skeleton covers the story you want and add/remove shots if not.
4. **Fill the plan** (edit the JSON): `title`, `logline`, `concept`, `visual_direction`, the `bible`, `sound`, and for
   every shot `subject`, `action`, `environment`, `vo`, `sfx`, `transition_out` (+ `lighting`, `time_of_day`,
   `references`, `characters`, `notes` where needed). Refer to recurring things with `@id` tokens defined in the bible.
5. **Compile:**
   ```bash
   python <skill>/scripts/catana.py plan compile plan.json --out build/plan
   ```
   Writes `compiled.json` (prompts, VO plan, EDL, QC) and `storyboard.md`. Exit code 1 = some shot or the sequence
   is not ready.
6. **Fix every QC error and warning** (each issue carries a `fix`), recompile until "shots needing fixes: none" and
   "sequence ready: True".
7. **Present** the storyboard: concept, bible, shot list table, then per shot keyframe + video prompt. Keep it scannable.
8. **Execute** (see `docs/PROVIDERS.md`): select a provider per operation —
   `python <skill>/scripts/catana.py select --op t2v --duration 5 --aspect 16:9 --available higgsfield,runway`.
   Typical order: generate each shot's **keyframe image** (t2i / multi_ref_image) → approve → **animate it** (i2v with the
   keyframe as `first_frame`) → assemble per the EDL. Paid connectors: quote the cost first and run only after the user
   explicitly approves. No provider available, or the user declines: `catana.py pack plan.json --out build/pack`.
9. **Sound:** music is the user's own track (CATANA never generates music). Voiceover is free through VoiceStudio:
   ```bash
   python <skill>/scripts/catana.py voice plan build/plan/compiled.json --out-dir build   # writes build/vo_*.wav + build/vo.json
   ```
   For a CATANA motion film, `audio/mix.py` reads `build/vo.json`, places the lines and ducks music/SFX under them.
   SFX: the motion engine's procedural mixer (cue kinds in `references/api.md`) or the per-shot `sfx` descriptions for
   the editor. Paid voice/sound providers only if the user explicitly asks for one.
10. **Validate and report**: what was generated (with asset paths/URLs from the run log), what is prompt-only, what
    was not verified. Offer variations (other routes, alt hooks, platform cut-downs).

**Hard rules.** Never say an image/video/voice was generated unless a provider returned an asset (path, URL or job id)
and it is in the run log (`catana.py log …`). Paid providers need a quoted cost and the user's explicit OK. Audio is
free-only by default. Never fabricate metrics or testimonials; label illustrative content.

## Beat templates (from `director.py`)

| Domain | Beats (default camera move) |
|---|---|
| architecture | establish (aerial_reveal) → approach (dolly_in) → threshold (steadicam) → flow (parallax) → detail (push_in) → life (tracking) → hero (crane_up) → end_card (static) |
| product, automotive, food* | hook (whip_pan) → reveal (orbit_360) → detail (push_in) → use (tracking) → benefit (rack_focus) → hero (dolly_out) → end_card (static) |
| ugc | hook → problem → product → demo → result → cta (all handheld) |
| social | hook (push_in) → payoff (whip_pan) → proof (tracking) → cta (static) |
| cinematic | opening_image (aerial_reveal) → setup (dolly_in) → inciting (push_in) → escalation (tracking) → climax (arc) → resolution (crane_up) |
| fashion | hook (tracking) → look (arc) → detail (push_in) → attitude (handheld) → hero (dolly_out) → end_card (static) |
| character | intro (push_in) → action (tracking) → emotion (push_in) → hero (arc) |
| concept_art | establish (aerial_reveal) → explore (parallax) → wonder (crane_up) |
| general | open (dolly_in) → develop (tracking) → highlight (arc) → close (dolly_out) |

\* automotive and food have no template of their own yet and use `general`; pass `--domain product` for the product
arc or edit the beats. When two consecutive shots share a beat the engine swaps in one of the move's recommended
partners (UGC stays handheld). Default transitions: hook → hard cut on the beat, reveal → light flash / whip, hero →
match cut, establish/opening → fade in from black, end_card → dip to brand colour, cta → hard cut, otherwise cut on action.

## Plan schema (`plan.json`)

```jsonc
{
  "title": "Villa Saadiyat — Light on Stone",   // defaults to the subject
  "idea": "...",                                 // the original request (used to rebuild domain defaults)
  "domain": "architecture",                      // preset in data/presets.json
  "platform": null,                              // key in data/platforms.json or null
  "aspect_ratio": "16:9", "duration": 40, "fps": 30,
  "logline": "", "concept": "", "visual_direction": "",
  "bible": {
    "characters": {"host": "full locked description"},   // referenced as @host, or listed in shot.characters
    "products":   {"aurora": "..."},                     // @aurora
    "locations":  {"villa": "..."},                      // @villa
    "style": "...", "grade": "...", "palette": "...",    // style/grade override every shot's style/colour
    "lens_package": "...", "lighting": "...",            // defaults for every shot (shot.lens / shot.lighting override)
    "negative": ["..."]                                  // merged into every shot
  },
  "sound": {"music": "", "sfx_style": "", "vo_voice": "", "vo_direction": "", "provider": "voice_studio"},
  "scenes": [{"id": "SC1", "name": "main", "shots": [
    {"id": "S01", "beat": "establish", "purpose": "the location at scale", "duration": 5.0,
     "subject": "...", "action": "...", "environment": "",
     "camera_moves": [{"id": "aerial_reveal", "speed": "slow"}],   // ids from data/camera_movements.json; speed slow|medium|fast
     "characters": [], "references": [],                           // [{"source": "render.png", "role": "first_frame", "preserve": [...]}]
     "vo": "", "sfx": "", "transition_out": "fade in from black",
     "lens": "", "lighting": "", "time_of_day": "", "notes": ""}    // optional per-shot overrides
  ]}],
  "edit": {"sequence": ["S01", "..."], "notes": ""}
}
```

Split shots into several scenes when locations or time change — compile keeps edit order across scenes.
`@id` tokens are replaced in `subject`, `environment`, `action` and `composition`. Reference roles: `subject, character,
product, style, composition, geometry, environment, first_frame, last_frame, motion`; give every subject/character/
product/geometry reference a `preserve` list.

## Compiled output (`compiled.json`)

`title, aspect_ratio, total_seconds`, `shots[]` with `id, scene, beat, start, duration, camera[], keyframe_prompt,
video_prompt, negative_prompt, params, vo, sfx, transition_out, qc{score, grade, ready, issues}`,
`sequence_qc{ready, total_seconds, issues}`, `voiceover{provider, voice, direction, lines[{shot, start, slot, text, words,
estimated_seconds, fits, fix}], script}`, `edl[{id, in, out, transition}]`. VO fit is estimated at 2.5 words/s;
`catana.py voice fit "<line>" --seconds 4` asks VoiceStudio for the exact fit when it is running.

## The 12 deliverables

| Deliverable | Where it comes from |
|---|---|
| 1. Creative concept | `plan.concept` (+ `logline`) — you write it |
| 2. Visual direction | `plan.visual_direction` + `bible.style/grade/palette/lens_package` |
| 3. Storyboard | `storyboard.md` (per-shot keyframe + video prompt, VO, SFX, QC) |
| 4. Shot list | storyboard "Shot list" table (`compiled.shots`: beat, start, duration, camera, transition, QC) |
| 5. Camera movements | `shot.camera_moves` → phrased by the camera library inside each video prompt |
| 6. Lighting direction | `bible.lighting` (+ per-shot `lighting` / `time_of_day`) |
| 7. Scene descriptions | `shot.subject` + `action` + `environment` after bible substitution |
| 8. Image-generation prompts | `compiled.shots[].keyframe_prompt` (+ `negative_prompt`) |
| 9. Video-generation prompts | `compiled.shots[].video_prompt` (+ `params`: aspect, duration, fps, references) |
| 10. Transitions | `shot.transition_out` → `compiled.edl[].transition` |
| 11. Sound design | `plan.sound` + per-shot `sfx` + `compiled.voiceover` (lines, fit, script) |
| 12. Final editing sequence | `compiled.edl` (in/out per shot) + storyboard "Edit sequence" |

## Continuity rules

- Put every recurring character, product and location in the bible **once**, with concrete identifying detail, and
  reference it by `@id` — compile pastes identical wording into every shot (identity drift negatives are added).
- Style and grade live only in the bible. Mixed aspect ratios in one sequence are an error; deliver one ratio per cut.
- Keep one time of day per scene. A deliberate change (day → night) = per-shot `lighting` + `time_of_day` and the
  word "transition" in `notes`, ideally a first/last-frame shot (see `references/studios/architecture.md`).
- Interior shots need their own `environment`; otherwise the domain's exterior default leaks in.
- Vary the camera: the sequence linter flags the same move three shots in a row.
- One action per ~2.5 s of shot; long clips (> 15 s) are better split.

## Worked example — luxury villa commercial, Abu Dhabi (20 s, 16:9)

```bash
python <skill>/scripts/catana.py plan new "luxury cinematic commercial for a modern villa in Abu Dhabi" --duration 20 --out plan.json
# → 5 shots × 4 s: establish (aerial_reveal), approach (dolly_in), flow (parallax), detail (push_in), hero (crane_up)
```

Filled excerpt (verified: compiles with 0 shots needing fixes and a ready sequence):

```json
{
  "title": "Villa Saadiyat — Light on Stone",
  "logline": "A day of desert light moves across one house, ending as it glows at dusk.",
  "concept": "The sun is the protagonist: every shot follows light as it travels from the dunes, through the house, to the water.",
  "visual_direction": "Restrained, architectural, slow. Warm stone against cool sky. Lines kept straight; people small and unposed.",
  "bible": {
    "locations": {"villa": "a two-storey contemporary villa of honed travertine and bronze-tinted glass with a cantilevered roof, a 25 m infinity pool facing the Arabian Gulf, date palms on a raked-sand garden"},
    "characters": {"host": "a woman in her forties in a flowing ivory linen dress, dark hair in a low bun, barefoot"},
    "palette": "travertine beige, bronze, deep gulf turquoise, warm white",
    "negative": ["visible logos", "cars in the driveway"]
  },
  "sound": {"music": "user track: slow ambient piano, 70 BPM", "sfx_style": "wind, water lapping, distant birds",
            "vo_voice": "Warm narrator", "vo_direction": "calm, intimate, unhurried", "provider": "voice_studio"},
  "shots": [
    {"id": "S01", "beat": "establish", "subject": "@villa seen from above the dunes",
     "action": "wind lifts a fine veil of sand off the dune crest", "vo": "Some places are built.", "sfx": "wind over sand"},
    {"id": "S02", "beat": "approach", "subject": "the bronze entrance door of @villa",
     "action": "the heavy pivot door swings slowly open", "sfx": "door pivot, footsteps on stone"},
    {"id": "S03", "beat": "flow", "subject": "@host walks through the double-height living room of @villa", "characters": ["host"],
     "action": "she walks toward the glass wall, her dress moving softly", "vo": "Others are composed.", "sfx": "room tone, linen rustle"}
  ]
}
```

(The `shots` list lives in `scenes[0].shots` in the real file; style, grade, lens and lighting come from the
architecture preset unless you set them in the bible.) Compiled S03 video prompt begins:

> Slow lateral parallax slide past layered foreground elements, strong depth separation: a woman in her forties in a
> flowing ivory linen dress, dark hair in a low bun, barefoot walks through the double-height living room of a
> two-storey contemporary villa of honed travertine and bronze-tinted glass … 24mm tilt-shift lens, f/8 … Golden hour
> sun low from the west raking across the façade … palette: travertine beige, bronze, deep gulf turquoise, warm white.
> Low motion intensity, temporally consistent … 4-second shot.

Improve before generating: give S03 its own interior `environment` ("double-height living room, travertine floor,
floor-to-ceiling glass to the pool"), add an `end_card` shot for the logo, and add first-frame references if the
client has renders. VO lines fit (1.6 s and 1.2 s in 4 s slots); render them free with `catana.py voice plan`.
