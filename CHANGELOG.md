# Changelog

All notable changes to CATANA. Dates are UTC.

## 2.0.0 — 2026-11-03

CATANA grows from a single-purpose motion-film skill into an AI creative director, keeping the motion engine intact.

### Added
- **Router skill.** `SKILL.md` rewritten as the intelligent router: a 9-step workflow, routing table, honesty and cost
  rules, a QC gate before any generation, and frontmatter compatible with claude.ai uploads.
- **Plugin packaging.** `.claude-plugin/plugin.json`, a marketplace manifest and an icon. `claude plugin validate`
  passes, and the plugin installs and discovers the skill plus 17 commands.
- **17 slash commands** (`/catana:<name>`):
  - hero-shot, ugc-video, faceless-video, ad-multiplier
  - cinematic-video, image-to-video, character-studio, product-commercial
  - storyboard, camera-movement, architecture-film, scene-builder
  - prompt-enhancer, campaign-studio, style-transfer, video-director
  - motion-film (the original capability)

  They are generated from `data/commands.json`, together with `docs/COMMANDS.md`.
- **Engine** (`engine/catana_core/`, Python standard library only):
  - **ShotSpec:** the 13 prompt fields.
  - **Prompt engine:** domain, modality, platform, aspect ratio, duration, camera move, speed and lighting detection;
    domain presets; continuity bible with `@id` tokens.
  - **QC linter:** actionable fixes plus sequence continuity checks.
  - **Provider layer:** capability matching, cost policies, retry and fallback decisions, an honest run log, adapters,
    an orchestrator.
  - **AI Director:** plan, compile and storyboard.
- **Data** (`data/`):
  - camera library (27 moves × definition, use, behaviour, example, mistakes, combinations, conflicts, minimum duration)
  - 11 domain presets (general, product, architecture, fashion, character, cinematic, UGC, social, concept art,
    automotive, food)
  - delivery specs for 11 platforms
  - provider capability manifest
- **Providers:**
  - **VoiceStudio:** client for the user's free local voice app (OpenAPI v0.5.7): speech with chunking, voices,
    voice design, fitting lines to their slots. Audio defaults to free-only.
  - **Connector recipes:** Higgsfield, Runway and ElevenLabs, each with discovery, cost preflight, approval,
    verification and logging.
  - **Prompt-pack fallback:** export only, nothing generated.
- **References:**
  - `references/director.md`
  - studios: UGC, advertising, cinematic, product, architecture, social (incl. faceless), character
- **Docs:** ARCHITECTURE, WORKFLOWS, COMMANDS, IMAGE_GENERATION, VIDEO_GENERATION, CAMERA_MOVEMENTS (generated),
  PROMPT_ENGINEERING, PROVIDERS, TROUBLESHOOTING, EXAMPLES, TEST_REPORT.
- **Tests:**
  - the 15 Phase-10 scenarios
  - VoiceStudio against a mock server built from its OpenAPI
  - command discoverability, routing and generated-doc sync
  - motion engine static checks and scaffolding
  - opt-in render integration in three formats
- **Motion engine:**
  - optional free voiceover track (`build/vo.json`), with music and SFX ducked under the voice
  - layout helpers `fit()`, `vx/vy/px`, `PORTRAIT`
  - `new_film.py --format 16:9|9:16|1:1|4:5 --fps --offset`
  - MP3/M4A music conversion

### Fixed (motion engine)
- `new_film.py --music` crashed on every run: the template had no `assets/` folder.
- Vertical and square films were broken: 1920×1080 was hard-coded in CSS, HTML, the page tool and the eval tool.
  Format now comes from `FILM` everywhere.
- `flash()` assumed 60 fps, so flashes had the wrong length at 24/25/30 fps.
- `music_scan.py` crashed with `ZeroDivisionError` on tracks shorter than about 8 bars.
- `qc.py` assumed 60 fps and 16:9; it now reads frame rate and size from the video. `sheet.py` keeps portrait aspect.
- `mix.py` printed a raw traceback when `build/events.json` was missing.
- `render.mjs` had a duplicated usage header and Chrome finder; it now uses the shared helpers and validates still times.
- The Chrome finder now also finds pre-installed Playwright Chromium.

### Changed
- The original SKILL.md workflow moved verbatim to `references/motion-film.md`, updated only for the new formats, flags
  and voiceover.
- The demo `scenes.js` lays itself out for any format.

## 1.0.0

- `catana`: Katana-style motion films built in code. Deterministic `render(t)` page, beat grid, kinetic type, slash
  motif, WebGL finishing pass, parallel Puppeteer renderer, procedural SFX mixer, music analyser, QC tools, guides.
