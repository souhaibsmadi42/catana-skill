# Test report — CATANA 2.0.0

**Run:** 2026-11-03 in a Linux cloud container (Python 3.13, Node 22, Chromium). Command:
`CATANA_INTEGRATION=1 python -m unittest discover tests -v`

**Result: 48 tests, 48 passed, 0 failed, 0 skipped** (21 s). Without `CATANA_INTEGRATION=1` the render test is skipped.

## Coverage by area

| Suite | Tests | What it proves |
|---|---|---|
| `test_scenarios.py` | 15 | The 15 required scenarios, end to end through the engine (table below) |
| `test_voice_studio.py` | 15 | VoiceStudio client, adapter, orchestrator and CLI against a mock server built from the user's OpenAPI v0.5.7: speech, 8 000-char script chunked and rejoined, invalid input, HTTP 500 retried twice (4 s, 15 s) then prompt pack, no-audio responses, unreachable server reported as `unavailable` (never success), bearer auth, env configuration, rate-fit, voice design, the VO cue list for the mixer |
| `test_commands.py` | 10 | Every proposed command exists; each command file is well-formed, user-invoked and routed to its mode and reference docs; the SKILL.md routing table covers every command; every referenced file exists; SKILL.md frontmatter is claude.ai-compatible; plugin and marketplace manifests agree; generated docs match their data (regenerated in a scratch copy and compared); every command documents purpose, syntax, parameters, examples, behaviour and limitations; CLI exit codes |
| `test_motion_engine.py` | 8 | No hard-coded frame size; fps-correct flash; voiceover ducking present; FILM reader; scaffold with `--music` (crashed before 2.0) at 9:16 / 30 fps with tempo detected at 124 ± 0.5 BPM; bad inputs rejected; short-track music scan; **real Chrome renders of stills at 16:9, 9:16 and 1:1 at the exact pixel sizes** |

## The 15 required scenarios

| # | Scenario | Test | Checks |
|---|---|---|---|
| 1 | Basic image generation | `test_01` | every field filled specifically, real lens, negatives, QC ready |
| 2 | Advanced image generation | `test_02` | fashion domain, time of day detected, product + style references, preservation clause, `multi_ref_image` |
| 3 | Image-to-video | `test_03` | first-frame reference → `i2v`; camera move leads the prompt; paid provider requires approval; first_frame on a still is an error |
| 4 | Text-to-video | `test_04` | duration and tracking move parsed; move phrase and duration in the prompt; QC ready |
| 5 | Multi-scene video | `test_05` | 60 s plan sums to 60 s; two scenes compile; EDL ends at total; camera variety; storyboard sections |
| 6 | Character consistency | `test_06` | `@maya` bible text identical in 3 shots; identity negatives; style locked; drift detected when a shot paraphrases |
| 7 | Product advertisement | `test_07` | product domain; hook first and end card last (even when shots are dropped to fit move durations); label negatives; all shots ready |
| 8 | UGC production | `test_08` | UGC wins over product keywords; 9:16; handheld throughout; VO slot overflow flagged; tts routed free-only to VoiceStudio |
| 9 | Architectural cinematic | `test_09` | geometry preservation required and then satisfied; vertical-warp negatives; preservation clause in the prompt |
| 10 | Camera movement | `test_10` | all 26 required moves (+ static) with the 7 required fields; combos and conflicts valid and disjoint; text detection with clause-local speed; conflict detection; phrasing |
| 11 | Prompt enhancement | `test_11` | weak spec scores < 40 with a fix for every issue; enhanced request ≥ 90 and ≥ 4× richer |
| 12 | Provider failure | `test_12` | 503 → fallback; timeout → retry with 4 s backoff, then fallback after 2 retries; insufficient credits → stop and ask |
| 13 | Missing API keys | `test_13` | 401 classified `auth`; next paid provider → ask approval; all failed → prompt pack; run log refuses success without an asset |
| 14 | Invalid inputs | `test_14` | bad modality, ratio, duration, reference role, camera move, unknown field, empty request, unknown domain, operation and platform; 422 → `fix_input` |
| 15 | Workflow fallback | `test_15` | free-only with nothing available → prompt pack written with "nothing was generated"; an un-executable connector is skipped, never reported as success |

## Manual verification (beyond the unit tests)

| Check | Result |
|---|---|
| Original 12 s demo: stills, 4-worker video, audio mix, QC (baseline before any change) | worked: 2.8 min render, −14.3 LUFS |
| After the fixes: full 9:16 at 30 fps video, mix and QC | 1080×1920, 30 fps, exactly 360 frames; the only flagged pops are the demo's intended on-beat strobes |
| Contact sheets at 16:9, 9:16, 1:1 (looked at) | layouts fit after two fixes (label/counter overlap; side-by-side lockup overflowing at 1:1) |
| Free voiceover end to end: mock VoiceStudio → `voice plan` → `vo.json` → `mix.py` | 2 cues mixed, −14.1 LUFS, −1.0 dBFS peak |
| MP3 music → scaffold | converted to WAV, 124.04 BPM detected, 9:16 / 30 fps written |
| `claude plugin validate .` | passes with no warnings |
| Local plugin install + `claude plugin details catana` | 18 components discovered (skill `catana` + 17 commands) |
| AI Director on 5 briefs (villa 40 s, SUV 20 s, earbuds 15 s, tacos 18 s, UGC TikTok) | every shot grade A; sequences ready; shot lengths respect each move's minimum |
| 21 studio example prompts and ~20 doc examples run through `catana.py enhance` | all QC A as documented |

## Not tested here (and why)

| Item | Why | How to test |
|---|---|---|
| Live generation through Higgsfield / Runway / ElevenLabs | Spends credits. The user asked for free usage; the Higgsfield account has 0 credits; a paid ElevenLabs call was declined | With credits: run one `/catana:hero-shot` and one 5 s `/catana:image-to-video`, approve the quoted cost, check the run log |
| Live VoiceStudio | It runs on the user's computer; a cloud session can't reach its localhost | On that computer: `python scripts/catana.py voice health`, then `voice speak "test" --out t.wav` |
| Slash commands invoked inside a live Claude session | Discovery verified (`plugin details`); invoking needs an interactive session | `/catana:storyboard 30s launch film for my app` |
| Listening to the audio and real-time viewing | No human playback here | Watch the rendered MP4s |

## Before / after

| Area | 1.0 (before) | 2.0 (after) |
|---|---|---|
| Scope | Katana-style motion films only | AI creative director: images, video, campaigns, storyboards, characters, UGC, architecture, social, plus motion films |
| Entry points | `/catana` (one skill) | Router skill + 17 namespaced commands, plugin and marketplace, still usable as a plain skill or on claude.ai |
| Prompting | none | 13-field spec, 11 domain presets, natural-language parsing, continuity bible, provider-ready rendering |
| Camera | slash/whip/shake post FX inside the engine | 27-move library × 7 fields, conflict and duration checks, prompt phrasing, generated doc |
| Quality control | video QC (pops, blips, black frames) | plus a prompt validation checklist with fixes, grades, sequence continuity, provider limit checks |
| AI generation | none (by design) | provider layer over Higgsfield / Runway / ElevenLabs with discovery, quote, approval, retry, fallback, logging |
| Voice | none | free local VoiceStudio: TTS, voices, design, slot fitting; ducked into films |
| Formats | 16:9 only in practice (9:16 needed manual CSS edits that broke tools) | 16:9, 9:16, 1:1, 4:5 everywhere; any fps |
| Known bugs | scaffold crash with `--music`; flash length wrong off 60 fps; music scan crash on short tracks; QC assumed 60 fps 16:9 | fixed, with regression tests |
| Docs | SKILL.md + 4 references + README | + ARCHITECTURE, WORKFLOWS, COMMANDS, IMAGE/VIDEO_GENERATION, CAMERA_MOVEMENTS, PROMPT_ENGINEERING, PROVIDERS, TROUBLESHOOTING, EXAMPLES, TEST_REPORT, CHANGELOG; director + 7 studio references |
| Tests | none | 48 automated tests |

## Implemented features
- Router skill with the 9-step intelligent workflow, routing table, honesty and cost rules.
- 17 slash commands (16 proposed + `motion-film`), generated from one data file together with their documentation.
- AI Director: plan, compile, storyboard, keyframe and video prompts, VO plan with slot checks, EDL.
- Seven studios: UGC, advertising, cinematic, product, architecture, social/faceless, character.
- Prompt engine, camera library, QC linter, sequence continuity.
- Provider architecture: manifest, cost policies, capability checks, retry/backoff, fallback, run log, adapters, orchestrator.
- VoiceStudio integration (free voice) and voiceover mixing in the motion engine.
- Motion engine: any format and fps, layout helpers, scaffold fixes, MP3 input.
- Plugin packaging: validated, installable, discoverable.

## Remaining limitations
1. **Paid generation is untested live.** The connector recipes follow the tools' own schemas, but no paid image or video
   was generated (by the user's choice and a 0-credit account).
2. **VoiceStudio is mock-tested only.** The client is built from the user's OpenAPI and tested against a faithful mock,
   not against the real app.
3. **Capability data is a snapshot.** Connector models and limits change. CATANA re-verifies at run time, but
   `data/providers.json` needs occasional refreshing.
4. **Heuristic parsing.** `enhance()` detects domain and cues by keywords. Ambiguous requests can pick the wrong preset
   (e.g. "founder presenting the product" → product); `--domain` overrides, and Claude refines every spec anyway.
5. **No automatic assembly of AI clips.** The Director outputs an edit list (EDL). Joining generated clips is a manual
   edit step; the motion engine can assemble graphics and type locally.
6. **No sound effects or music generation for free.** VoiceStudio is voice-only. SFX are procedural and music must be
   the user's own track. Paid SFX and music exist (Runway, ElevenLabs, Higgsfield) only with explicit consent.
7. **Plugin command namespace.** Commands are `/catana:<name>`; bare `/hero-shot` is not guaranteed by Claude Code.
8. **Motion engine dependencies.** Rendering needs Node, Chrome and Python audio packages on the machine.
