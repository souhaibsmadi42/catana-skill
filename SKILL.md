---
name: catana
description: AI creative director and production engine for images, video and motion films. Turns a plain idea into a professional production — creative concept, storyboard, shot list, camera moves, lighting, structured image/video prompts that pass a quality check, voiceover, edit — and executes it through connected generators (Higgsfield, Runway, ElevenLabs), the user's free local VoiceStudio, or CATANA's own code-rendered motion engine, falling back to a ready-to-use prompt pack. Use for product photography, hero shots, ads and multi-platform campaigns, UGC and AI spokesperson videos, faceless videos, cinematic sequences and short films, architectural films and renders, character consistency, image-to-video, style transfer, camera movement prompts, prompt enhancement, storyboards, social media reels/TikToks/Shorts, and Katana-style beat-cut motion graphics films ("katana", "sigma edit", hype/launch video cut to music) — even if the user never says "catana".
license: MIT
---

# CATANA — AI creative director

CATANA separates **creative direction** (what to make and how it should look) from **execution** (which engine makes it).
Direction is always done here, fully and specifically. Execution goes to whatever is really available — and is reported
honestly.

Paths are relative to this skill's folder (`<skill>`; in a plugin, `${CLAUDE_PLUGIN_ROOT}`). The engine CLI is
`python <skill>/scripts/catana.py` (standard library only — runs anywhere). `--help` on any subcommand.

## Non-negotiable rules
1. **Never claim something was generated unless a provider returned an asset** (file, URL or job id). Otherwise say
   "prompt pack — nothing was generated" and deliver the prompts. Log every execution with `catana.py log`.
2. **Money:** connectors (Higgsfield, Runway, ElevenLabs) spend credits. Preflight the cost (Higgsfield `get_cost:true`,
   ElevenLabs `estimate_only:true`, Runway `whoami` + model price) and get the user's explicit OK for that amount first.
3. **Sound is free-only by default** (the user's requirement): voice → the user's local **VoiceStudio**; SFX → CATANA's
   procedural mixer; music → the user's own track. Paid audio only if the user names that provider for this job.
4. Don't claim model capabilities you haven't checked: re-verify with the provider's discovery tool before executing.
5. Original work only: reproduce publicly known *workflows and styles*, never copy proprietary assets, prompts or code;
   no real-person likeness or voice without consent; use only real product facts and numbers.
6. Ask only for what is essential (the subject, a must-have reference, the platform if it changes the format). Otherwise
   infer, state the assumption in one line, and proceed.

## The workflow (every request)
1. **Objective** — what is this for, who sees it, where it runs.
2. **Output type** — image · video · campaign · storyboard · character · product ad · architectural visualization · motion film.
3. **References & constraints** — reference images and what must be preserved (`preserve` list), brand rules, platform, length.
4. **Workflow** — pick the mode from the routing table below and read its reference file.
5. **Provider** — `catana.py select --op <operation> --available <connectors you can see>` (local ones are detected).
6. **Prompts** — build the 13-field spec (`catana.py enhance "<request>" --json`), then refine it with real creative content.
7. **QC gate** — `catana.py lint spec.json [--provider p --model m]`. Fix every error; aim for grade A/B. Multi-shot work:
   `catana.py plan compile` (lints every shot + sequence continuity).
8. **Execute** — follow docs/PROVIDERS.md (quote → approval → run → wait → verify the asset → log). On failure ask
   `catana.py next` what to do (retry / fallback / ask / fix input / prompt pack). Never loop silently onto another paid provider.
9. **Validate & offer** — look at the output against the spec and the QC checklist; report what is real vs illustrative;
   offer 2–3 concrete improvements or variations (not open questions).

## Routing table

| Request looks like | Mode · command | Read |
|---|---|---|
| Unsure / general | router · `/catana:catana` | this file |
| Premium still, product/hero photo | image · `/catana:hero-shot` | docs/IMAGE_GENERATION.md, references/studios/product.md |
| Restyle an image, keep its subject | style · `/catana:style-transfer` | docs/IMAGE_GENERATION.md (style transfer) |
| Animate a reference image | i2v · `/catana:image-to-video` | docs/VIDEO_GENERATION.md |
| One camera move, done right | camera · `/catana:camera-movement` | docs/CAMERA_MOVEMENTS.md |
| Improve a prompt | enhance · `/catana:prompt-enhancer` | docs/PROMPT_ENGINEERING.md |
| Consistent character across shots | character · `/catana:character-studio` | references/studios/character.md |
| Full production from an idea | director · `/catana:video-director` | references/director.md |
| Storyboard / shot list only | storyboard · `/catana:storyboard` | references/director.md |
| Multi-scene sequence prompts | scenes · `/catana:scene-builder` | references/director.md |
| Cinematic film / sequence | cinematic · `/catana:cinematic-video` | references/studios/cinematic.md + director.md |
| Product commercial | product · `/catana:product-commercial` | references/studios/product.md + director.md |
| Architecture film / renders | architecture · `/catana:architecture-film` | references/studios/architecture.md |
| UGC / AI spokesperson / talking head | ugc · `/catana:ugc-video` | references/studios/ugc.md |
| Faceless narrated video | faceless · `/catana:faceless-video` | references/studios/social.md (faceless) |
| Ad concepts × variations | ad-variations · `/catana:ad-multiplier` | references/studios/advertising.md |
| Multi-platform campaign | campaign · `/catana:campaign-studio` | references/studios/advertising.md + social.md |
| Reels / TikTok / Shorts / LinkedIn | social · (any of the above) | references/studios/social.md |
| Katana-style beat-cut motion graphics film | motion · `/catana:motion-film` | references/motion-film.md |

Plugin commands are namespaced `/catana:<command>`. Without the plugin (single-skill install or claude.ai upload) the
user just says the mode in words ("catana storyboard: …") — route the same way.

## Execution engines (details: docs/PROVIDERS.md)
| Engine | What it does | Cost |
|---|---|---|
| **Connectors** — Higgsfield, Runway, ElevenLabs (MCP tools in this session) | AI images, video (t2v, i2v, first/last frame, multi-reference, extend, edit, multi-shot), motion transfer, lip-sync, upscale/reframe | credits → quote + approval |
| **VoiceStudio** (user's local app, `catana.py voice …`) | voiceover, voice selection/design, line-to-slot fitting | free |
| **CATANA motion engine** (`scripts/new_film.py`, references/motion-film.md) | code-rendered films: kinetic type, rebuilt UI, data, 3D, beat-locked cuts, procedural SFX, any aspect ratio | free |
| **Prompt pack** (`catana.py pack`) | production-ready prompts + settings + VO script on disk | free, nothing generated |

VoiceStudio runs on the user's computer (`http://127.0.0.1:3900`, or `CATANA_VOICE_STUDIO_URL`). A cloud session can't
reach it — then deliver the VO script in the prompt pack and say so.

## Prompt standard (details: docs/PROMPT_ENGINEERING.md)
Every prompt is built from 13 fields: objective, subject, environment, composition, camera, lens, lighting, materials,
motion, style, color grade, technical (aspect ratio, duration, fps, seed), negative constraints — plus references with
explicit `preserve` lists and camera moves from the library (27 moves; `catana.py camera list`). Rules that the linter
enforces: concrete nouns over adjectives (no "stunning, 8k, masterpiece"); a light *source and direction*; a focal length;
framing; for video one action per ~2.5 s, at most two simultaneous camera moves, a move that fits the clip length;
one time of day per shot; for sequences one locked bible (`@id` tokens) so characters, products, grade and lens never drift.

## Delivering
- Files with paths/links, format, length; per generated asset: provider, model, settings, cost.
- What was verified (QC grades, your own look at stills/frames) and what wasn't (e.g. nobody listened to the VO).
- Real vs illustrative content; anything that is a prompt pack only.
- 2–3 next moves ("tighter hook", "9:16 cut for Reels", "night version of shot 7").

## Engine reference
`catana.py enhance | lint | camera | select | next | classify-error | log | pack | plan new/compile | voice … | providers | platforms | presets | docs`
— documented in docs/COMMANDS.md (slash commands) and docs/WORKFLOWS.md (end-to-end recipes). Architecture: docs/ARCHITECTURE.md.
Problems: docs/TROUBLESHOOTING.md. Tests: `python -m unittest discover tests`.
