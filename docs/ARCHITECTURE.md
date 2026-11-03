# Architecture

CATANA is a Claude skill (and Claude Code plugin) that acts as an AI creative director. It is built around one idea:
**creative direction is separate from execution.** Claude plus the reference docs decide *what* to make; a small,
tested Python engine makes the direction structured, specific and consistent; and a provider layer decides *who*
makes it: a connected generator, the user's free local VoiceStudio, CATANA's own motion engine, or a prompt pack.

```
                    user request (plain language, or /catana:<command>)
                                   │
                    ┌──────────────▼──────────────┐
                    │  SKILL.md  — router + rules │  workflow steps 1–9, routing table, honesty rules
                    └──────────────┬──────────────┘
           reads ┌─────────────────┼──────────────────────────────┐
                 ▼                 ▼                              ▼
     references/studios/*   references/director.md        references/motion-film.md
     (UGC, ads, cinematic,  (AI Director)                  (+ motion-language, api,
      product, architecture,                                pipeline, 3d-world)
      social, character)
                 │                 │                              │
                 └────────┬────────┘                              │
                          ▼                                       ▼
        scripts/catana.py  ──  engine/catana_core/        scripts/new_film.py
        (CLI, stdlib only)     spec · prompt_engine ·     assets/template/  (motion engine:
                               camera · qc · director ·   render.mjs, src/*, audio/mix.py,
                               providers · voice_studio    tools/*)
                          │            ▲
                          ▼            │ data/  (single source of truth)
                  provider layer       │ camera_movements.json · presets.json ·
                          │            │ platforms.json · providers.json · commands.json
     ┌──────────────┬─────┴───────┬─────────────────┬──────────────────┐
     ▼              ▼             ▼                 ▼                  ▼
 Higgsfield      Runway       ElevenLabs       VoiceStudio        CATANA motion     prompt_only
 (MCP, credits)  (MCP)        (MCP)            (local HTTP, free) (local, free)     (export, free)
```

## Layers

| Layer | Files | Responsibility |
|---|---|---|
| Router and rules | `SKILL.md` | Classify the request, choose the workflow, enforce the honesty and cost rules, run QC before execution |
| Commands | `commands/*.md` (generated from `data/commands.json`) | 17 user-invoked entry points (`/catana:<name>`), each routing to one mode |
| Creative knowledge | `references/` | Studios, Director, the motion-film craft; read on demand (progressive disclosure keeps SKILL.md short) |
| Data | `data/*.json` | Camera library, domain presets, platform specs, provider capability manifest, command catalogue |
| Engine | `engine/catana_core/` | Deterministic, tested logic Claude calls through the CLI |
| Execution | connectors (MCP), `voice_studio.py`, `assets/template/`, `PromptOnlyAdapter` | Make the asset, or say why not |
| Docs | `docs/` | Human and Claude reference; `CAMERA_MOVEMENTS.md` and `COMMANDS.md` are generated |
| Tests | `tests/` | The 15 Phase-10 scenarios, VoiceStudio against a mock server, command routing, motion engine |

## Engine modules (`engine/catana_core/`, Python 3.9+, standard library only)

| Module | Role | Key functions |
|---|---|---|
| `spec.py` | `ShotSpec`: the 13 prompt fields + modality, domain, camera moves, references (`role`, `preserve`), characters | `from_dict`, `validate`, `hash` |
| `prompt_engine.py` | Natural language → spec → prompt; continuity bible | `enhance`, `render`, `apply_bible`, `detect_*` |
| `camera.py` | Camera library lookups, text detection, phrasing, combination checks | `get`, `find_in_text`, `phrase`, `check_combo` |
| `qc.py` | Validation checklist with actionable fixes; sequence continuity | `lint`, `lint_sequence`, `needed_operation` |
| `providers.py` | Capability matching, cost policy, retry/fallback, run log, local adapters, orchestrator | `select`, `classify_error`, `next_action`, `RunLog`, `Orchestrator` |
| `voice_studio.py` | Client for the user's free local VoiceStudio (OpenAPI v0.5.7) | `speech`, `voices`, `rate_fit`, `describe_voice` |
| `director.py` | Idea → plan → compiled prompts, VO plan, EDL, storyboard | `new_plan`, `compile_plan`, `to_markdown` |
| `data.py` | Loads `data/*.json` (override folder with `CATANA_DATA`) | `load` |

Why the standard library only: the skill is installed by cloning or uploading a folder. Nothing may need `pip install`
before CATANA can plan, prompt and lint. Only the motion engine has dependencies (Node, Chrome, numpy/scipy for audio),
and only when a film is rendered.

## Data flow for one shot
1. `enhance(text)` detects the domain (UGC wins over subject categories), modality, platform, aspect, duration, camera
   moves (+ speed), and lighting cue / time of day. It cleans the subject and fills every empty field from the domain preset.
2. Claude replaces defaults with real creative specifics and adds references with `preserve` lists.
3. `apply_bible(spec, bible)` swaps `@id` tokens for locked descriptions and enforces the style, grade and lens package.
4. `qc.lint(spec, provider, model)` returns a score, a grade, a `ready` flag and issues, each with a fix. Errors block execution.
5. `render(spec)` orders the prompt for the modality. Video leads with the camera move and action, then setting,
   framing, light, materials, style and grade, then the consistency constraints. It also returns the negative prompt and params.
6. `select(op, available)` ranks providers. `next_action(attempts, ranked)` decides what to do after a failure.
   `RunLog.append` records every attempt.

## Provider architecture
- **Manifest, not code.** `data/providers.json` declares, per provider: kind (`connector`, `http_local`, `local`,
  `export`), cost, supported operations (22-operation vocabulary), limits, discovery tool, snapshot date. Adding a
  provider is a manifest entry, plus an `Adapter` subclass only if CATANA can call it directly. Nothing else changes.
- **Capability checks:** `select` rejects providers that lack the operation, duration, aspect ratio or availability,
  and says why. Connectors' capabilities are a dated snapshot; Claude re-verifies with the provider's discovery tool.
- **Cost policy:** `free_first` (default for visuals: free options first, paid ones flagged `requires_approval`),
  `free_only` (default for audio, by the user's requirement), `best_quality`. Paid execution always needs a quoted
  cost and explicit approval.
- **Failure handling:** errors are classified (timeout, rate_limited, server_error, network, unavailable, auth,
  invalid_input, insufficient_credits, paid_plan_required, content_policy). Transient errors are retried twice with a
  4 s then 15 s backoff. Invalid input means fix the prompt. Billing and policy errors stop and ask the user. Anything
  else falls back to the next provider, asking first if it's paid, and finally to `prompt_only`.
- **Honest records:** `RunLog` (JSONL) refuses `succeeded` without an asset path, URL or job id, and keeps prompt,
  params, model, cost and error category so any result can be reproduced.
- **API keys:** only through environment variables (`OMNIVOICE_API_KEY`, `CATANA_VOICE_STUDIO_URL`) or the connectors' own
  sign-in. Nothing is hard-coded or written to disk.

## The motion engine (preserved, improved)
`assets/template/` is CATANA's original deterministic film engine: `render(t)` draws any frame from its time alone, so
renders are frame-exact and run in parallel. Version 2 keeps every primitive and workflow and adds:
- **Any format.** `FILM` drives the stage, layers, renderer and tools: 16:9, 9:16, 1:1, 4:5.
- **Format-aware layout helpers.** `fit`, `vx`, `vy`, `px`.
- **Correct timing at any frame rate.** Effects are timed from `FILM.FPS`.
- **Bug fixes.** The scaffold crash and the music-scan crash on short tracks.
- **Free voiceover.** VoiceStudio clips are mixed in, with music and SFX ducked under the voice.

## Packaging
- **Plugin:** `.claude-plugin/plugin.json` (`"skills": ["./"]` loads the root SKILL.md) plus `commands/`.
  `.claude-plugin/marketplace.json` makes the repo its own marketplace. Checked with `claude plugin validate`, which passes.
- **Plain skill:** clone into `~/.claude/skills/catana`. The root SKILL.md works alone; commands are optional.
- **claude.ai upload:** SKILL.md frontmatter uses only `name`, `description` and `license`, the keys the Skills API
  accepts. A test enforces this.

## Design decisions
| Decision | Why |
|---|---|
| One router skill + thin commands generated from data | No duplicated workflows; commands can't drift from docs (a test regenerates and compares) |
| Commands are `disable-model-invocation` | One auto-trigger (the router) instead of 18 competing ones |
| Camera library and presets as JSON | The same data drives prompts, lint rules and docs |
| Connectors decided in Python, executed by Claude | Only Claude can call MCP tools; the engine keeps decisions and records consistent and testable |
| Audio free-only default | The user requires free sound; VoiceStudio covers voice, the procedural mixer SFX, the user's track music |
| Prompt pack as the final fallback | The user always gets production-ready output, and it is never mislabelled as a generation |
