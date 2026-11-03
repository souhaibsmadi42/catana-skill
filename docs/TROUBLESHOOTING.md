# Troubleshooting

Symptom → cause → fix. Related: [PROVIDERS.md](PROVIDERS.md) · [PROMPT_ENGINEERING.md](PROMPT_ENGINEERING.md) ·
[VIDEO_GENERATION.md](VIDEO_GENERATION.md) · [IMAGE_GENERATION.md](IMAGE_GENERATION.md) ·
[CAMERA_MOVEMENTS.md](CAMERA_MOVEMENTS.md)

## Motion engine (code-rendered films)

| Symptom | Cause | Fix |
|---|---|---|
| `Chrome not found: install Chrome/Chromium/Edge or set CHROME=/path/to/chrome` | No browser in the standard locations or `/opt/pw-browsers` | Install Chrome / Chromium / Edge, or `export CHROME=/path/to/chrome` |
| `npm not found — install Node.js 18+, then run npm install in <dir>` from `new_film.py` | Node missing | Install Node 18+, then `npm install` in the project (or rerun without `--no-install`) |
| `<ext> music needs ffmpeg to convert` | mp3/m4a/aac music without ffmpeg available | Install ffmpeg, run `npm install` first (it brings `ffmpeg-static`), or pass a `.wav` |
| `<dir> exists and is not empty — pick a new folder` | `new_film.py` never overwrites | Choose a new target folder |
| `ModuleNotFoundError: scipy / soundfile / pyloudnorm` | Python audio dependencies missing | `pip install numpy scipy soundfile pyloudnorm pillow` (matplotlib optional) |
| A whole section renders black | Shot timing overwritten (stored as `S.t0`-style short names), or beats mixed with seconds | Keep timing in `_t0/_t1`; write cues as `B(k)`; offsets in seconds use `BEAT/2`, `BEAT/4`. Check with `EXPR="window.__dbg(t)" node tools/evalfx.mjs <t>` |
| All shots' text visible at once | Containers hidden with `visibility` instead of `display` | Use `shot()` containers (they toggle `display`) |
| An effect or flash lands between beats / a 1-frame pop in QC | Cue registered at the wrong time | `node tools/evalfx.mjs <t>` to read post parameters; `python tools/qc.py out/x.mp4` lists pops and blips |
| 9:16 / 1:1 / 4:5 layout clipped or squashed | Format not set at scaffold, or scenes laid out in fixed 1920-px values | `new_film.py --format 9:16` (or set `FILM.W/H` in `src/lib.js`). Lay out with `W/H`, `vx()/vy()`, `px()` and `fit()`; use a stacked layout when `W/H < 1.3` |
| Flash length wrong at 24/30 fps | (fixed) `flash()` used to assume 60 fps | Update the template; `flash` now uses `FILM.FPS` |
| `music_scan: track is X s — too short to read a tempo (need >= 4 s)` | Clip under 4 s | Use a longer track, or set `BPM`/`OFFSET` in `src/lib.js` by hand |
| `note: only X s of audio — downbeat and section guesses are unreliable` | Under about 16 s (fewer than ~8 bars) | Trust BPM and offset only; set `OFFSET` by ear or with `--offset` |
| Downbeat off by a beat (drops land between bars) | The bar-phase guess is the weakest step | Check `qa/music_scan.png` and the bar table; rerun `new_film.py … --offset <s>` or edit `OFFSET` |
| `mix.py: build/events.json is missing - dump the cue list first` | The mix ran before the cue dump | `node tools/page.mjs "src/index.html?dump=1" build/events.json`, then `python audio/mix.py` |
| `WARNING: no music at … - SFX only` | `FILM.MUSIC` path wrong or no track given | Put the track in `assets/` and fix `MUSIC` in `src/lib.js` |
| `WARNING: missing VO clip …` | `build/vo.json` points at a file that doesn't exist | Re-run `catana.py voice plan compiled.json --out-dir build` from the project, or fix the paths |
| Renders are slow | About 3 fps per worker with the post pass | More `--workers`; render ranges with `--from/--to`; check stills before video |

## VoiceStudio (free local voice)

| Symptom | Cause | Fix |
|---|---|---|
| `VoiceStudio is not reachable at http://127.0.0.1:3900 … A cloud session cannot reach your computer's localhost.` (exit 3) | The app isn't running, or CATANA runs in a cloud session / another machine | Start VoiceStudio. Run CATANA in Claude Code **on the same computer**, or point `CATANA_VOICE_STUDIO_URL` at a reachable address. Meanwhile CATANA delivers a script pack (free), never fake audio |
| HTTP 401 / 403 → category `auth` | Remote / LAN access needs a token | `export OMNIVOICE_API_KEY=…` (bearer). Loopback needs none |
| HTTP 422 → `invalid_input` | Empty input, an over-length single request, or an invalid field | The client splits scripts over 4096 characters automatically when the output is `.wav`. Long scripts need a `.wav` output, and a target `--duration` only works for a single chunk |
| HTTP 409 → `invalid_input` | The voice name matches several profiles | Pass the profile **id** (`catana.py voice voices` / `GET /profiles`) |
| `VoiceStudio returned no audio (Content-Type 'application/json')` → `server_error` | The engine returned a JSON status instead of audio | Check the app's notifications and logs; retry once the model is ready |
| First request very slow or timing out | The TTS model is cold-loading | Check `GET /model/status` (idle / loading / ready) or warm up with `POST /setup/warmup`, then retry |
| VO doesn't fit its shot | Too many words for the slot | `catana.py voice fit "<text>" --seconds <slot>`. The Director flags lines over about 2.5 words/s with a word budget |

## Providers (AI image / video connectors)

| Symptom / error | Category | What CATANA does | Fix |
|---|---|---|---|
| "Insufficient credits", 402, balance 0 | `insufficient_credits` | **stop**: never switches to another paid provider | Tell the user. Top up, use free generations if explicitly requested, or deliver the prompt pack |
| `paid_plan_required`, "upgrade your plan" | `paid_plan_required` | **stop** | Show the provider's plan card (Runway `show_plans_and_credits`); ask the user |
| 401 / 403 / missing API key / not authenticated | `auth` | fall back to the next ranked provider (asks first if it's paid) | Reconnect the connector in claude.ai settings; set env keys for local services |
| Moderation / content policy | `content_policy` | **stop** | Rephrase with the user; don't route around the policy via another provider |
| Timeout, 429, 5xx, network | `timeout`, `rate_limited`, `server_error`, `network` | **retry** after 4 s, then 15 s, then fall back | Never re-submit a paid job before the first job's outcome is known (check its job id) |
| 400 / 404 / 409 / 422 validation | `invalid_input` | **fix_input** | Run `catana.py lint spec.json --provider p --model m`; fix the duration / ratio / roles |
| Model rejects the duration | — | `lint --model` error, e.g. `seedance_2_0 accepts 4–15 s, spec asks 20 s` | Shorten the shot, split it, or choose a model with a longer range |
| A connector's tools are missing | — | `select` drops it: "not available in this session" | Check the connector in claude.ai settings; deliver the prompt pack meanwhile |
| `refusing to log 'succeeded' without an asset path/URL or provider job id` | — | — | Wait for the job, get the asset URL / id, then log it. No asset means no success |

## Prompt / QC issues

| Symptom in output | Cause | Fix |
|---|---|---|
| The face, hair or wardrobe changes between shots (identity drift) | The character is described differently per shot, or there's no reference | Bible + `@id` tokens + `characters: [...]`; a `character` reference with `preserve: ["face identity", "hairstyle", "wardrobe"]`; Higgsfield reference elements; `lint_sequence` must pass |
| Bent verticals, melting façades, extra floors | Wide lens, high motion, no geometry lock | `architecture` preset (24mm tilt-shift, verticals corrected); `motion_intensity: low`; a `geometry` reference preserving massing, floors, windows and roof; slow `dolly_in` / `pedestal` instead of `tilt_up` |
| Actions skipped or rushed; lint "N actions in a D s clip" | More than about one action per 2.5 s | One action per clip; split into shots; put actions in `motion` so the check sees them |
| Flicker or boiling textures | A transformation without a transition, high intensity, or a long clip | Describe the transition; use `first_last` keyframes; intensity low; 4–10 s clips |
| Lint error "conflicting times of day" | e.g. "golden hour" in the lighting and "twilight" in the subject | Pick one. For day-to-night use separate shots or a `first_last` transition, and mark "transition" in notes |
| Lint warning "'Orbit 360' needs about 6 s to read" | The clip is shorter than the move's `min_seconds` | Lengthen the clip or choose a shorter move (`catana.py camera list` shows `min`) |
| Lint error "'X' conflicts with 'Y'" | Incompatible simultaneous moves | `catana.py camera check a b`; keep one primary move plus at most one secondary |
| Lint error "subject is too thin" | Fewer than 3 concrete words | Add material, colour, size, finish and action |
| Lint warning "generic filler words" | beautiful / amazing / 8k / masterpiece… | Replace each with a visual instruction |
| Wrong preset chosen | Keyword overlap (e.g. "coffee mug" picks `food`) | Pass `--domain` explicitly |
| Portrait came out in the wrong ratio | Character images default to 4:5, video to 16:9 | Pass `--aspect` (e.g. `2:3`, `9:16`) or `--platform` |
| Reference reinterpreted | No `preserve` list | List exactly what must stay identical; lint warns until you do |

## Plugin / commands not showing

| Symptom | Cause | Fix |
|---|---|---|
| `/catana:hero-shot` not found | Plugin commands are namespaced | Use `/catana:hero-shot` (and so on); the main skill is `/catana:catana`. Plain `/catana` works for a direct skill install |
| Nothing new appears after install or update | Skills and commands load at startup | Restart Claude Code; check `/plugin` shows CATANA enabled |
| Plugin install fails or skips components | Manifest problem | `claude plugin validate <path-to-repo>`; the `name` in `.claude-plugin/plugin.json` must match the `marketplace.json` entry |
| Uploaded to claude.ai but only `/catana` works | claude.ai skill uploads have no commands | Ask in plain words or `/catana <mode> …`; the skill routes to the same workflows |
| Script paths not found from a command | Commands run with the plugin root, not the cwd | Commands reference `${CLAUDE_PLUGIN_ROOT}/scripts/catana.py`; for a direct install use the skill folder path |

## Tests

```
python -m unittest discover tests            # from the repo root; standard library only
cd tests && python -m unittest test_scenarios -v   # the 15 Phase-10 scenarios (run from tests/: helpers import by name)
```

The tests need no network, no keys and no credits: VoiceStudio runs against a local mock server, and connectors are
simulated. A failing test prints the scenario name. Run `python scripts/catana.py <cmd>` by hand with the same input
to see the full output.
