# Providers and model orchestration

CATANA separates **creative direction** (spec, prompt, QC: the same for every provider) from **execution** (a
provider chosen per operation). Providers are declared as data, so adding one never restructures CATANA.

Code: `engine/catana_core/providers.py`, `voice_studio.py`. Manifest: `data/providers.json`. CLI:
`scripts/catana.py select | next | classify-error | log | pack | providers | voice`.

Related: [PROMPT_ENGINEERING.md](PROMPT_ENGINEERING.md) · [IMAGE_GENERATION.md](IMAGE_GENERATION.md) ·
[VIDEO_GENERATION.md](VIDEO_GENERATION.md) · [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 1. Architecture

```
            ShotSpec ─ lint ─▶ prompt + params
                                   │
   catana.py select --op <op> --available <present>   (capability · limits · cost policy · preference)
                                   │ ranked list
   ┌───────────────────────────────┼─────────────────────────────────────────┐
   │ connector (MCP)               │ http_local / local                      │ export
   │ Higgsfield · Runway ·         │ VoiceStudio (free) · CATANA motion      │ prompt_only (free,
   │ ElevenLabs  — Claude calls    │ engine (free) — adapters execute        │ always available)
   │ the tools; credits; approval  │ directly via Orchestrator               │ status 'prompt_only'
   └───────────────────────────────┴─────────────────────────────────────────┘
                                   │
                RunLog (JSONL) ◀── every attempt · next_action() decides retry / fallback / ask / stop
```

### Manifest (`data/providers.json`)

| Key | Meaning |
|---|---|
| `operations` | the vocabulary: `t2i i2i multi_ref_image style_transfer upscale_image outpaint t2v i2v first_last multi_ref_video v2v extend_video multi_shot motion_transfer lipsync upscale_video reframe tts voice_design sfx music motion_graphics prompt_pack voice_convert transcribe dub` |
| `providers.<name>.kind` | `connector` (MCP tool Claude calls), `http_local` (a local HTTP service), `local` (runs on this machine), `export` (writes files only) |
| `cost` | `free`, `user_reports_free` or `credits` |
| `operations` | what this provider can do |
| `limits` | `video_seconds_max`, `aspect_ratios`, `duration_seconds`, … (used by `select` and `lint --provider`) |
| `known_models` | per-model operations and second ranges (a snapshot; `lint --model` enforces it) |
| `verified`, `snapshot`, `discovery` | how the data was obtained and how to re-verify it at run time |
| `policy` | cost policies, audio preference, retry / backoff, never-auto-fallback categories, success rule |

### Cost policies

| Policy | Behaviour |
|---|---|
| `free_first` (default for images and video) | Free providers rank first among executors. Paid connectors are offered with `requires_approval: true`. `prompt_only` is always last |
| `free_only` (**default for every audio op**: `tts voice_design sfx music voice_convert transcribe dub`) | Paid providers are excluded. Sound must be free: VoiceStudio, the CATANA SFX mixer, or a script pack |
| `best_quality` | Rank by capability and verification regardless of cost. Approval is still required before any spend |

Override with `--policy`. Paid audio runs only if the user explicitly asks for that provider.

```
$ python scripts/catana.py select --op tts --available voice_studio,elevenlabs
free_only ['voice_studio', 'prompt_only']
$ python scripts/catana.py select --op i2v --available higgsfield,runway --duration 8 --aspect 9:16
free_first [('higgsfield', True), ('runway', True), ('prompt_only', False)]     # (provider, requires_approval)
$ python scripts/catana.py select --op t2v --available higgsfield --duration 40
['prompt_only']   rejected: higgsfield — max 30 s per generation
```

`--available` lists the connectors Claude can see in this session. Local providers are always detected
automatically and added to it:
- VoiceStudio health check on localhost
- Node + Chrome for the motion engine

```
$ python scripts/catana.py providers --detect      # policy free_first
voice_studio  http_local free     detected_here=False
catana_motion local      free     detected_here=True
prompt_only   export     free     detected_here=True
higgsfield    connector  credits  detected_here=False   (connectors are seen by Claude, not by the script)
```

## 2. Providers

### VoiceStudio: the user's free, local voice engine (preferred for all sound)

- **What:** the VoiceStudio desktop app's local API (OpenAPI **v0.5.7**, snapshot 2026-11-03).
- **Cost:** free.
- **Can do:**
  - text-to-speech
  - voice selection and voice design
  - voice conversion, transcription, dubbing
- **Can't do:** sound effects or music generation. SFX come from the CATANA motion mixer; music is the user's own
  track.
- **Base URL:** `$CATANA_VOICE_STUDIO_URL`, default `http://127.0.0.1:3900`.
- **Auth:** none on loopback. A remote or LAN instance needs `Authorization: Bearer $OMNIVOICE_API_KEY`, read from
  the environment and never written into files.
- **Reachability:** only where VoiceStudio runs, i.e. Claude Code on the same computer. A cloud session cannot reach
  the user's localhost. The client then reports `unavailable` (CLI exit code 3), and CATANA falls back to a script
  pack. It never claims audio was made.

Endpoints the client uses (`engine/catana_core/voice_studio.py`):

| Purpose | Endpoint | CLI |
|---|---|---|
| health | `GET /health` | `catana.py voice health` |
| voices | `GET /v1/audio/voices`, `GET /archetypes?q=…`, `GET /profiles` | `voice voices`, `voice archetypes <q>` |
| voice design | `POST /design/describe {description}` | `voice describe "deep calm british male"` |
| fit a line to a slot | `POST /tools/rate-fit {text, slot_seconds, target_lang}` | `voice fit "<text>" --seconds 3` |
| speech | `POST /v1/audio/speech {model, input ≤ 4096, voice, instructions, instruct, response_format, speed 0.25–4, language, duration, seed}` | `voice speak "<text>" --out vo.wav [--voice v --instructions "…" --speed 1.0 --language en --duration s --log runs.jsonl]` |
| all VO lines of a plan | (speech per line) | `voice plan compiled.json --out-dir build` → `build/vo_<shot>.wav` + `build/vo.json` |

Scripts over 4096 characters are split on sentence boundaries and joined as WAV, so use a `.wav` output. Failures map
to categories: 401/403 → `auth`; 400/404/409/413/422 → `invalid_input`; 5xx → `server_error`; refused → `unavailable`;
timeout → `timeout`. In a motion project, `audio/mix.py` reads `build/vo.json`, places each clip and ducks the music
under the voice.

Unreachable, as verified from this cloud session:

```
$ python scripts/catana.py voice health        # exit 3
{"error": "VoiceStudio is not reachable at http://127.0.0.1:3900 ([Errno 111] Connection refused). Start the VoiceStudio app, or set CATANA_VOICE_STUDIO_URL. A cloud session cannot reach your computer's localhost.", "category": "unavailable"}
```

### CATANA motion engine (local, free)

- **What:** code-rendered motion-graphics films: kinetic type, rebuilt UI, data, 3D, with procedural SFX on the user's
  music.
- **Operations:** `motion_graphics`, `sfx`, `reframe`.
- **Limits:** 1–600 s, 16:9 / 9:16 / 1:1 / 4:5, 24–60 fps.
- **Requires:** Node 18+, Chrome/Chromium, and Python with numpy, scipy, soundfile, pyloudnorm and pillow.
- **Not supported:** AI footage and voice synthesis.
- Workflow: `scripts/new_film.py` and the main skill's motion-film workflow. `providers.render_motion(project)` renders
  a project and returns the MP4.

### prompt_only (export, always available)

- **What:** writes `<id>.md` + `<id>.json`: prompt, negative, settings and VO script. For a plan it also writes
  `storyboard.md`.
- **Status:** always `prompt_only`, never `succeeded`.

```
$ python scripts/catana.py pack spec.json --out prompts/
{"status": "prompt_only", "files": ["prompts/shot.md", "prompts/shot.json"], "note": "nothing was generated"}
```

### Higgsfield (connector, credits): snapshot 2026-11-03 via `models_explore(list)`

| Step | Tool |
|---|---|
| discover | `models_explore(action:"recommend", query:…)` / `(action:"get", model_id:…)`; `balance()` for credits and plan |
| cost preflight | `generate_image` / `generate_video` / `generate_audio` with `params.get_cost: true` (nothing is submitted) |
| references | `media_upload` → PUT the bytes → `media_confirm`; pass the media ids in `params.medias` with the model's roles (`start_image`, `end_image`, `image_references`, `video_references`, …) |
| generate | `generate_image`, `generate_video`, `generate_audio`; batch variants for several independent jobs |
| wait / show | `jobs_wait` (short timeouts), then `show_generation_by_ids` |
| edit | `upscale_image`, `upscale_video`, `reframe`, `outpaint_image`, `remove_background`, `motion_control` |
| studios | `show_marketing_studio_v2` / `ads_studio_*` (UGC, ads), `ai_influencer_prepare` → `ai_influencer_generate` |

Notes:
- Limits: video up to 30 s; aspect ratios 21:9, 16:9, 4:3, 1:1, 3:4, 9:16.
- Known models: see [VIDEO_GENERATION.md](VIDEO_GENERATION.md) and [IMAGE_GENERATION.md](IMAGE_GENERATION.md).
- In the reference session the account was on the free plan with 0 credits. Generation needs credits, or the user's
  explicit request to use free generations.

### Runway (connector, credits): snapshot from tool schemas, not yet `whoami`-verified

| Step | Tool |
|---|---|
| discover | `whoami()`: workspace and the models it can run. Video, speech and SFX need a paid workspace |
| generate | `generate_image`, `generate_video`, `generate_multishot_video`, `generate_product_marketing_video`, `edit_video`, `expand_video`, `upscale_image`, `upscale_video` |
| audio (excluded by `free_only` unless asked) | `generate_speech`, `generate_sound_effect`, `generate_music` |
| status | `get_task` |

On `paid_plan_required`, call `show_plans_and_credits`, then stop and tell the user.

### ElevenLabs creative (connector, credits): snapshot from tool schemas

| Step | Tool |
|---|---|
| discover | `creative_get_flow_node_types()`; `creative_get_model_guide` before prompting an unfamiliar model |
| cost preflight | `estimate_only: true` on generate calls that offer it (e.g. `creative_generate_speech`) |
| generate | `creative_generate_image`, `creative_edit_image`, `creative_generate_video` (and `creative_generate_speech`, excluded by `free_only`) |
| wait | poll `creative_get_flow_run_status(flow_id, session_ids)` every `poll_after_seconds` until `all_completed` or `has_failures` |
| chained work | `creative_create_flow` first, then pass `flow_id` to every related call |

The user declined a paid ElevenLabs call in the reference session. Use it only with explicit approval.

## 3. Execution protocol (Claude follows this exactly)

1. **Spec + lint.** Build the spec and run `catana.py lint spec.json --provider <p> --model <m>`. Fix errors.
2. **Select.** `catana.py select --op <op> --available <present providers>`, with `--policy` if the user set one.
3. **Re-verify.** Run the provider's discovery tool and confirm the model supports the op, duration and ratio.
4. **Quote.** Use the provider's cost preflight (`get_cost: true` / `estimate_only: true`).
5. **Approval.** If `requires_approval`, show provider, model, count and cost, and get an explicit yes. Approval of one
   quote doesn't cover another.
6. **Execute.** Call the tool once. Never re-submit to retry a timeout before the first job's outcome is known.
7. **Wait.** `jobs_wait` / `get_task` / `creative_get_flow_run_status`.
8. **Verify the asset.** A URL, path or asset id must exist. Look at it (or its preview) before reporting.
9. **Log.**
   `catana.py log --file catana_runs.jsonl --provider p --op o --status succeeded --asset <url> --job-id <id> --model m --prompt "…" --run-id <same id for every attempt of this job>`
10. **On failure.** Classify the error, record the attempt, and ask for the next step:

    ```
    $ python scripts/catana.py classify-error "Insufficient credits for this generation"   → insufficient_credits
    $ python scripts/catana.py next --attempts attempts.json --op t2v --available higgsfield,runway
    {"action": "retry", "provider": "higgsfield", "wait": 4, "reason": "timeout: transient, retry 1/2"}
    {"action": "stop", ... "reason": "insufficient_credits: tell the user and ask how to proceed — never silently switch to another paid provider"}
    ```

    `attempts.json` is `[{"provider", "status": "failed"|"succeeded"|"prompt_only", "error_category"}]`, oldest
    first. Actions:
    - `run`
    - `retry` (after `wait` s)
    - `fallback` (next free or approved provider)
    - `ask_approval` (next option is paid)
    - `fix_input` (rejected request: fix the prompt, don't switch)
    - `stop` (tell the user)
    - `prompt_only` (deliver the pack and say nothing was generated)
    - `done`

### Retry and fallback policy (`policy` in the manifest)

| Setting | Value |
|---|---|
| retryable categories | `timeout`, `rate_limited`, `server_error`, `network` |
| max retries per provider | 2 |
| backoff | 4 s, then 15 s |
| never auto-fallback (stop and ask) | `insufficient_credits`, `paid_plan_required`, `content_policy`, `invalid_input` (`invalid_input` → `fix_input`) |
| `auth`, `unavailable`, `unknown` | fall back to the next ranked provider; a paid next option means `ask_approval` |
| nothing left | `prompt_only` |

Error categories (`classify_error`, matched in order):
`insufficient_credits`, `paid_plan_required`, `content_policy`, `auth`, `rate_limited`, `timeout`, `unavailable`,
`server_error`, `network`, `invalid_input`, `unknown`.

`Orchestrator.run(job, ranked)` applies the same loop automatically for locally executable adapters (VoiceStudio,
prompt pack). A connector in the ranked list is recorded as `unavailable` there, because only Claude can call MCP
tools, and the loop moves on.

### Run log (JSONL, one line per attempt)

```json
{"ts": "2026-11-03T00:29:30Z", "run_id": "ba26ab1afb", "provider": "higgsfield", "model": "seedance_2_0", "operation": "t2v",
 "status": "succeeded", "assets": ["https://…/v.mp4"], "job_id": "job_123", "prompt": "…", "params": {}, "spec_hash": null,
 "cost": null, "error": null, "error_category": null, "note": null}
```

Statuses are `succeeded`, `failed`, `prompt_only` and `submitted`. The log **refuses**:
- `succeeded` without an asset or job id
- `submitted` without a job id
- `failed` without an error message

```
$ python scripts/catana.py log --file runs.jsonl --provider higgsfield --op t2v --status succeeded
error: refusing to log 'succeeded' without an asset path/URL or provider job id        (exit 2)
```

Each `log` call gets a fresh `run_id` unless `--run-id` is passed. Pass the same id for every attempt of one job.

## 4. Honesty rules

- Never say an image, video or voice was generated unless a provider returned an asset and it was checked.
- `prompt_only` deliveries say "nothing was generated".
- Never spend credits without an explicit approval of the quoted cost. Never switch to another paid provider after
  a billing error.
- Don't claim capabilities from memory. Use the manifest snapshot, then re-verify with the provider's discovery tool.
- API keys come only from connectors or environment variables (`OMNIVOICE_API_KEY`, `CATANA_VOICE_STUDIO_URL`,
  `CHROME`). Never write them into files, prompts, logs or commits.

## 5. Adding a provider (no restructuring)

1. **Manifest entry** in `data/providers.json` → `providers.<name>`:
   - `label`, `kind`, `available_when`, `cost`, `operations` (only names from `operations`; add new ones there first)
   - `verified`, `snapshot`, `discovery`
   - `tools` or `endpoints`, `limits`, and optionally `known_models`

   `select`, `next`, `lint --provider` and `providers` pick it up immediately.
2. **Connector providers** need nothing else. Claude calls the tools and records attempts with `catana.py log`.
3. **Locally executable providers** (HTTP service, CLI): subclass `providers.Adapter` with `execute(job) -> Result(status, assets, error, job_id)`.
   - Return `failed` with a message whose wording `classify_error` understands.
   - Return `succeeded` only with assets.
   - Detect it in `local_available()` if it can be probed.
4. **Tests** (`tests/`): selection (supported op, limits, cost policy), adapter success / failure / unavailable
   against a mock (see `tests/helpers.MockVoiceStudio`), and that the run log never records a success without an
   asset. Run `python -m unittest discover tests`.
5. **Keys:** read from an environment variable named in the manifest's `available_when` / `auth`. Never hard-code them.
