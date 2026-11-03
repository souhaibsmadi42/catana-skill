# Commands

> Generated from `data/commands.json` by `python scripts/catana.py docs` — edit the JSON, not this file.

CATANA ships as a Claude Code plugin. Its slash commands are namespaced **`/catana:<command>`**; `/catana:catana`
is the skill itself (the intelligent router). Installed as a plain skill or uploaded to claude.ai, there are no
extra commands — say the mode in words ("catana storyboard: …") and the skill routes the same way.

| Command | Mode | Purpose |
|---|---|---|
| `/catana:catana` | router | Main assistant: understands the request and routes to the right workflow |
| [`/catana:hero-shot`](#hero-shot) | image | Premium cinematic still: product hero, packshot, key visual, editorial or portrait image. |
| [`/catana:ugc-video`](#ugc-video) | ugc | Authentic creator-style video: AI spokesperson, talking head, unboxing, review, demo, testimonial — scripted, multi-scene. |
| [`/catana:faceless-video`](#faceless-video) | faceless | Narrated video without an on-camera person: b-roll or kinetic typography with voiceover and captions. |
| [`/catana:ad-multiplier`](#ad-multiplier) | ad-variations | Many ad concepts and variations from one product: hooks × angles × formats × platforms, named for A/B testing. |
| [`/catana:cinematic-video`](#cinematic-video) | cinematic | Film-grade sequence: scene planning, characters, storyboard, camera direction, lighting, grade and continuity. |
| [`/catana:image-to-video`](#image-to-video) | i2v | Turn a reference image into a directed video shot (optionally to a last frame). |
| [`/catana:character-studio`](#character-studio) | character | Create a consistent AI character: bible, turnaround sheet, expressions, and reuse across shots. |
| [`/catana:product-commercial`](#product-commercial) | product | Product advertising film: hook, hero reveal, macro details, use, benefit, packshot, end card. |
| [`/catana:storyboard`](#storyboard) | storyboard | A complete storyboard and shot list from an idea — no generation. |
| [`/catana:camera-movement`](#camera-movement) | camera | Build a professional camera-movement prompt (or explain a move) from the 27-move library. |
| [`/catana:architecture-film`](#architecture-film) | architecture | Architectural cinematics and visualization: exteriors, interiors, drone, day-to-night, weather, construction-to-completion. |
| [`/catana:scene-builder`](#scene-builder) | scenes | Build a multi-scene sequence with continuity: scenes, shots, transitions and consistent prompts. |
| [`/catana:prompt-enhancer`](#prompt-enhancer) | enhance | Turn a basic prompt into a structured, specific production prompt with a QC report. |
| [`/catana:campaign-studio`](#campaign-studio) | campaign | Complete multi-platform campaign: concept, key visual, video spots, platform cuts, copy and a production plan. |
| [`/catana:style-transfer`](#style-transfer) | style | Apply a visual style to an image while preserving its subject and composition. |
| [`/catana:video-director`](#video-director) | director | Direct a complete production from one idea: concept to final edit, with execution through available providers. |
| [`/catana:motion-film`](#motion-film) | motion | CATANA's original engine: a beat-locked, code-rendered motion graphics film cut to a music track, rendered locally to MP4. |

## /catana:catana

**Purpose.** The main assistant and router (SKILL.md). Accepts any creative request, identifies the
output type, references and constraints, picks the workflow and provider, builds and lints the prompts, executes
through what is available and reports honestly.

**Syntax.** `/catana:catana <anything>` — or just describe the job; the skill
triggers on creative production requests.

<a id="hero-shot"></a>
## /catana:hero-shot — Hero shot

**Purpose.** Premium cinematic still: product hero, packshot, key visual, editorial or portrait image.

**Syntax.** `/catana:hero-shot <subject> [for <platform>] [aspect] [ref: image] [style notes]`

**Parameters.**

- subject (required): what to shoot, with material/colour/finish
- platform or aspect ratio (optional; default by domain)
- reference image(s) and what to preserve (optional)
- style/brand notes (optional)

**Examples.**

- `/catana:hero-shot matte black perfume bottle on wet basalt, moody, 4:5`
- `/catana:hero-shot our sneaker from ref shoe.jpg floating over a neon city, keep the logo and colourway`

**Expected behaviour.**

1. Build the 13-field spec with `catana.py enhance` (product/fashion/food/automotive presets), add references with preserve lists
2. Lint (grade A/B required), pick an image provider with `catana.py select --op t2i|i2i|multi_ref_image`
3. Quote cost and get approval for paid connectors; generate 2–4 variations; verify and log every asset
4. Without a usable provider: deliver the prompt pack and say nothing was generated

**Limitations.**

- Exact label/logo text depends on the model; check every output and regenerate or fix in post
- Paid generation needs a connector with credits

**Reads.** `docs/IMAGE_GENERATION.md`, `references/studios/product.md`

<a id="ugc-video"></a>
## /catana:ugc-video — UGC video

**Purpose.** Authentic creator-style video: AI spokesperson, talking head, unboxing, review, demo, testimonial — scripted, multi-scene.

**Syntax.** `/catana:ugc-video <product/offer> [platform] [length] [persona] [hook idea]`

**Parameters.**

- product or offer (required)
- platform (default TikTok 9:16)
- length in seconds
- persona / spokesperson description
- hook or angle

**Examples.**

- `/catana:ugc-video vitamin C serum, TikTok, 25s, 28-year-old skincare creator, hook: dark spots in 2 weeks`
- `/catana:ugc-video our budgeting app, Reels, testimonial from a freelance designer`

**Expected behaviour.**

1. Write the script with the UGC beats (hook, problem, product, demo, result, CTA) and voiceover direction
2. Plan shots with `catana.py plan new --domain ugc` (handheld phone language), fill bible (persona @id, product)
3. Voiceover free via VoiceStudio; spokesperson video via a connector only with approval (lip-sync is a paid step)
4. Compile, lint, execute or deliver the prompt pack + script

**Limitations.**

- Never impersonate a real person; AI spokespeople are fictional or consented
- Lip-synced talking heads need a paid connector

**Reads.** `references/studios/ugc.md`, `references/director.md`

<a id="faceless-video"></a>
## /catana:faceless-video — Faceless video

**Purpose.** Narrated video without an on-camera person: b-roll or kinetic typography with voiceover and captions.

**Syntax.** `/catana:faceless-video <topic/script> [platform] [length] [visual style: b-roll|kinetic|mixed]`

**Parameters.**

- topic or script (required)
- platform (default YouTube Shorts 9:16)
- length
- visual style: AI b-roll, kinetic type (motion engine), or mixed

**Examples.**

- `/catana:faceless-video 5 money habits of first-time founders, Shorts, 45s, kinetic`
- `/catana:faceless-video history of the Burj Khalifa, YouTube 16:9, 90s, b-roll`

**Expected behaviour.**

1. Write the narration (hook in the first 1.5 s) and split it into timed lines
2. Kinetic: build with the local motion engine (free) at the platform format; b-roll: plan shots and prompts per line
3. Render the narration with VoiceStudio (free) and mix it under the picture with ducking
4. Burn-in captions recommended for muted autoplay

**Limitations.**

- AI b-roll shots need a connector (paid); kinetic/motion versions are free and local
- The motion engine needs Node, Python and Chrome on the machine

**Reads.** `references/studios/social.md`, `references/motion-film.md`

<a id="ad-multiplier"></a>
## /catana:ad-multiplier — Ad multiplier

**Purpose.** Many ad concepts and variations from one product: hooks × angles × formats × platforms, named for A/B testing.

**Syntax.** `/catana:ad-multiplier <product/offer> [n variations] [platforms] [audience]`

**Parameters.**

- product/offer (required)
- number of variations (default 6)
- platforms
- audience / objective

**Examples.**

- `/catana:ad-multiplier Aurora earbuds, 9 variations, TikTok + Reels, commuters`
- `/catana:ad-multiplier spring menu at our café, 6 variations, Instagram feed`

**Expected behaviour.**

1. Define 2–3 creative angles and 3+ hooks; build the variation matrix with a naming scheme
2. One spec per variation via the prompt engine; lint each
3. Execute the approved subset (quote the total first) or deliver the matrix as a prompt pack
4. Return a test plan: which variable each pair isolates

**Limitations.**

- Total cost scales with variations — always quote the batch before generating

**Reads.** `references/studios/advertising.md`, `references/studios/social.md`

<a id="cinematic-video"></a>
## /catana:cinematic-video — Cinematic video

**Purpose.** Film-grade sequence: scene planning, characters, storyboard, camera direction, lighting, grade and continuity.

**Syntax.** `/catana:cinematic-video <story/idea> [length] [genre] [aspect]`

**Parameters.**

- story or idea (required)
- length
- genre / tone
- aspect (default 16:9 or 21:9 for scope)

**Examples.**

- `/catana:cinematic-video a lighthouse keeper's last night before automation, 60s, melancholic`
- `/catana:cinematic-video neo-noir chase through a rain-soaked Dubai Marina, 30s`

**Expected behaviour.**

1. Logline, beats, characters in the bible (@id), named grade and lens package
2. `catana.py plan new --domain cinematic`, fill shots with continuity (screen direction, eyelines, motivated light)
3. Compile → keyframe + video prompts per shot, QC, sequence continuity
4. Execute shot by shot (reference the previous frame for continuity) or deliver the pack

**Limitations.**

- Character consistency across many AI shots needs reference images and multi-reference models

**Reads.** `references/studios/cinematic.md`, `references/director.md`

<a id="image-to-video"></a>
## /catana:image-to-video — Image to video

**Purpose.** Turn a reference image into a directed video shot (optionally to a last frame).

**Syntax.** `/catana:image-to-video <image> [what moves] [camera move] [duration] [last frame image]`

**Parameters.**

- start image (required)
- subject/scene motion
- camera move (library id or words)
- duration (default by domain)
- last frame image (optional → first/last frame)

**Examples.**

- `/catana:image-to-video villa.png slow dolly in, palms sway, 6s, keep the architecture exact`
- `/catana:image-to-video day.png to night.png, timelapse day-to-night, 8s`

**Expected behaviour.**

1. Spec with a first_frame reference (and last_frame if given) and an explicit preserve list
2. Choose one primary camera move that fits the duration; one action per ~2.5 s
3. Lint, select provider (i2v or first_last), quote, execute, verify against the start frame
4. Fallback: prompt pack

**Limitations.**

- Geometry and text can drift at high motion intensity — keep it low for architecture/products

**Reads.** `docs/VIDEO_GENERATION.md`, `docs/CAMERA_MOVEMENTS.md`

<a id="character-studio"></a>
## /catana:character-studio — Character studio

**Purpose.** Create a consistent AI character: bible, turnaround sheet, expressions, and reuse across shots.

**Syntax.** `/catana:character-studio <character description> [style] [uses: ad|film|ugc]`

**Parameters.**

- character description (required)
- visual style
- intended uses

**Examples.**

- `/catana:character-studio Layla, 30s Emirati architect, short curly hair, linen abaya, warm confident`
- `/catana:character-studio a small orange robot mascot for a kids' coding app, 3D animated look`

**Expected behaviour.**

1. Write the bible entry (identity, face, hair, body, wardrobe, marks, voice) as one locked description
2. Generate a turnaround/expression sheet (with approval) and save references
3. Reuse via @id tokens + references in every later shot; lint sequences for drift

**Limitations.**

- No real-person likeness without consent
- Perfect identity lock depends on the model's reference support

**Reads.** `references/studios/character.md`

<a id="product-commercial"></a>
## /catana:product-commercial — Product commercial

**Purpose.** Product advertising film: hook, hero reveal, macro details, use, benefit, packshot, end card.

**Syntax.** `/catana:product-commercial <product> [length] [platform] [mood] [ref images]`

**Parameters.**

- product (required)
- length (default 15–20 s)
- platform
- mood / brand notes
- product reference images (strongly recommended)

**Examples.**

- `/catana:product-commercial Aurora earbuds, 15s, Reels, sleek night city`
- `/catana:product-commercial hand-made olive oil soap, 20s, warm rustic, ref soap.jpg`

**Expected behaviour.**

1. Plan with the product beats; lighting recipes (rim+strip, backlit liquid, gradient sweep)
2. Preserve product shape/label/colour from references in every shot
3. Compile, lint, execute (multi-reference models for identity) or deliver the pack; VO free via VoiceStudio

**Limitations.**

- Label text accuracy varies by model — verify every shot

**Reads.** `references/studios/product.md`, `references/director.md`

<a id="storyboard"></a>
## /catana:storyboard — Storyboard

**Purpose.** A complete storyboard and shot list from an idea — no generation.

**Syntax.** `/catana:storyboard <idea> [length] [platform] [domain]`

**Parameters.**

- idea (required)
- length
- platform
- domain (auto-detected)

**Examples.**

- `/catana:storyboard 40s luxury villa commercial in Abu Dhabi`
- `/catana:storyboard 30s TikTok launch for a fitness app`

**Expected behaviour.**

1. `catana.py plan new`, fill concept, bible and every shot
2. `catana.py plan compile --out dir` → storyboard.md (keyframe + video prompt per shot, timing, camera, transitions, sound, edit sequence, QC)
3. Offer to execute any shot or the whole board next

**Limitations.**

- Text storyboard; keyframe images only if the user then asks to generate them

**Reads.** `references/director.md`

<a id="camera-movement"></a>
## /catana:camera-movement — Camera movement

**Purpose.** Build a professional camera-movement prompt (or explain a move) from the 27-move library.

**Syntax.** `/catana:camera-movement <move or description> [subject] [duration] [speed]`

**Parameters.**

- move id/name or a description (required)
- subject/scene
- duration
- speed: slow | medium | fast

**Examples.**

- `/catana:camera-movement orbit 360 around a perfume bottle, 8s`
- `/catana:camera-movement what's the difference between push in and dolly in?`

**Expected behaviour.**

1. Look the move up (`catana.py camera show|find`), check combinations and minimum duration (`camera check`)
2. Phrase it with `camera phrase` and place it first in the video prompt
3. Explain best use, subject behaviour, mistakes and good combinations

**Limitations.**

- Models follow one or two simultaneous moves reliably; more are flagged

**Reads.** `docs/CAMERA_MOVEMENTS.md`

<a id="architecture-film"></a>
## /catana:architecture-film — Architecture film

**Purpose.** Architectural cinematics and visualization: exteriors, interiors, drone, day-to-night, weather, construction-to-completion.

**Syntax.** `/catana:architecture-film <project> [length] [platform] [renders/plans as refs] [special: day-to-night|weather|construction]`

**Parameters.**

- project (required)
- length
- platform
- reference renders/photos (preserve geometry)
- special sequences

**Examples.**

- `/catana:architecture-film modern villa in Abu Dhabi, 40s, from renders in ./renders, day-to-night ending`
- `/catana:architecture-film office tower, construction to completion, 20s, LinkedIn`

**Expected behaviour.**

1. Plan with the architecture beats (establish, approach, threshold, flow, detail, life, hero, end card)
2. Preserve massing, floors, openings, roof and camera position from references; low motion intensity; corrected verticals
3. Day-to-night/weather/construction as per-shot lighting overrides + transition notes or first/last frames
4. Compile, lint, execute or deliver the pack

**Limitations.**

- AI video can still bend geometry — always check verticals and window counts

**Reads.** `references/studios/architecture.md`, `references/director.md`

<a id="scene-builder"></a>
## /catana:scene-builder — Scene builder

**Purpose.** Build a multi-scene sequence with continuity: scenes, shots, transitions and consistent prompts.

**Syntax.** `/catana:scene-builder <sequence description or plan.json> [scenes] [length]`

**Parameters.**

- sequence description or an existing plan.json (required)
- scene breakdown
- length

**Examples.**

- `/catana:scene-builder three scenes: dawn market, noon chase, night rooftop — 45s`
- `/catana:scene-builder plan.json`

**Expected behaviour.**

1. Split into scenes, each with its own location/time of day; shots inherit the bible
2. Mark deliberate lighting changes as transitions; vary camera moves
3. Compile and run sequence QC (aspect, style, grade, time of day, character wording, total length)

**Limitations.**

- Generation of each shot follows the provider rules (quote + approval)

**Reads.** `references/director.md`

<a id="prompt-enhancer"></a>
## /catana:prompt-enhancer — Prompt enhancer

**Purpose.** Turn a basic prompt into a structured, specific production prompt with a QC report.

**Syntax.** `/catana:prompt-enhancer <prompt> [image|video] [provider]`

**Parameters.**

- prompt (required)
- modality (auto)
- target provider/model (checks its limits)

**Examples.**

- `/catana:prompt-enhancer a car on a road at sunset`
- `/catana:prompt-enhancer cinematic shot of a woman in a cafe, video, higgsfield`

**Expected behaviour.**

1. `catana.py enhance "<prompt>" --json`, then replace defaults with specifics the user implied
2. Show the before/after, the 13-field breakdown, negatives and the lint report with fixes

**Limitations.**

- Defaults are good starting points, not the user's brand; ask for brand specifics when they matter

**Reads.** `docs/PROMPT_ENGINEERING.md`

<a id="campaign-studio"></a>
## /catana:campaign-studio — Campaign studio

**Purpose.** Complete multi-platform campaign: concept, key visual, video spots, platform cuts, copy and a production plan.

**Syntax.** `/catana:campaign-studio <brand/product> [objective] [platforms] [budget/scope]`

**Parameters.**

- brand/product (required)
- objective (awareness, sales, leads…)
- platforms
- scope / budget

**Examples.**

- `/catana:campaign-studio Aurora earbuds launch, awareness, TikTok + Reels + YouTube + LinkedIn`
- `/catana:campaign-studio Ramadan offer for our restaurant, Instagram + Snapchat`

**Expected behaviour.**

1. Big idea + 2–3 routes; key visual specs; hero spot plan; per-platform cuts from data/platforms.json (ratio, length, hook, safe zones)
2. Variation matrix for testing; copy per placement
3. Quote the full production before generating; otherwise deliver the campaign pack

**Limitations.**

- Platform limits change — confirm paid-placement specs before trafficking

**Reads.** `references/studios/advertising.md`, `references/studios/social.md`, `references/director.md`

<a id="style-transfer"></a>
## /catana:style-transfer — Style transfer

**Purpose.** Apply a visual style to an image while preserving its subject and composition.

**Syntax.** `/catana:style-transfer <subject image> <style image or description> [strength]`

**Parameters.**

- subject image (required)
- style reference image or description (required)
- how much to change

**Examples.**

- `/catana:style-transfer villa.jpg in the style of moody.jpg, keep the building exact`
- `/catana:style-transfer portrait.png as a 1970s Kodachrome editorial`

**Expected behaviour.**

1. Spec with a subject reference (preserve list) and a style reference/description
2. Operation style_transfer (one style ref) or multi_ref_image; lint; select provider; execute with approval
3. Compare output to the subject reference for drift

**Limitations.**

- Strong styles can alter identity/geometry — iterate with a stricter preserve list

**Reads.** `docs/IMAGE_GENERATION.md`

<a id="video-director"></a>
## /catana:video-director — Video director

**Purpose.** Direct a complete production from one idea: concept to final edit, with execution through available providers.

**Syntax.** `/catana:video-director <idea> [length] [platform] [references] [budget]`

**Parameters.**

- idea (required)
- length
- platform
- references
- budget / approval scope

**Examples.**

- `/catana:video-director luxury cinematic commercial for a modern villa in Abu Dhabi, 40s`
- `/catana:video-director 20s launch film for our AI note-taking app, with a voiceover`

**Expected behaviour.**

1. Deliver the 12 Director outputs: concept, visual direction, storyboard, shot list, camera moves, lighting, scene descriptions, image prompts, video prompts, transitions, sound design, edit sequence
2. Compile + QC; quote; execute approved shots; VO free via VoiceStudio; assemble via the edit list
3. Report generated vs prompt-only shots honestly

**Limitations.**

- Final assembly of AI clips is an edit step (EDL provided); the motion engine can assemble type/graphics locally

**Reads.** `references/director.md`

<a id="motion-film"></a>
## /catana:motion-film — Motion film (Katana style)

**Purpose.** CATANA's original engine: a beat-locked, code-rendered motion graphics film cut to a music track, rendered locally to MP4.

**Syntax.** `/catana:motion-film <product/site> [music file] [length] [format 16:9|9:16|1:1|4:5]`

**Parameters.**

- subject: product, site or brand (required)
- music track the user has rights to
- length
- format

**Examples.**

- `/catana:motion-film 30s katana promo for my app Inkwell, track song.wav`
- `/catana:motion-film vertical 9:16 hype reel of our dashboard, music ./track.mp3`

**Expected behaviour.**

1. Follow references/motion-film.md: scaffold, read the music, plan in beats, build shots, stills QC, render, mix, deliver
2. Optional free voiceover via VoiceStudio, ducked under music

**Limitations.**

- No AI footage (by design); needs Node 18+, Python 3 audio packages and Chrome
- Bring your own music; SFX are procedural

**Reads.** `references/motion-film.md`

## Engine CLI (`python scripts/catana.py …`)

| Subcommand | What it does |
|---|---|
| `enhance "<request>" [--domain] [--modality] [--aspect] [--duration] [--platform] [--provider] [--json]` | plain request → 13-field spec → prompt + negative + params + QC |
| `lint <spec.json> [--provider] [--model] [--platform]` | QC checklist with fixes; exit 1 when not ready |
| `camera list | show <move> | find "<text>" | check <moves…> [--duration] | phrase <move> [--speed]` | camera library |
| `select --op <op> [--available a,b] [--duration] [--aspect] [--policy] [--approved-paid] [--prefer]` | rank providers for an operation |
| `next --attempts <attempts.json> --op <op> [--available]` | after a failure: retry / fallback / ask / fix input / prompt pack |
| `classify-error "<message>"` | map a provider error to a category |
| `log --file runs.jsonl --provider --op --status [--asset] [--job-id] [--error]` | append to the run log (refuses success without an asset) |
| `pack <spec.json|plan.json> --out <dir>` | write a prompt pack (nothing generated) |
| `plan new "<idea>" [--duration] [--platform] [--domain] [--aspect] --out plan.json` | AI Director plan skeleton |
| `plan compile <plan.json> [--out dir]` | keyframe + video prompts, VO plan, EDL, storyboard.md, QC |
| `voice health | voices | archetypes | describe | fit | speak | plan` | VoiceStudio (free, local): voiceover and voice tools |
| `providers [--detect] · platforms · presets` | manifests |
| `docs` | regenerate docs/CAMERA_MOVEMENTS.md, docs/COMMANDS.md and commands/*.md from data/ |

Exit codes: 0 ok · 1 QC errors / not ready · 2 usage or input error · 3 provider unavailable.
