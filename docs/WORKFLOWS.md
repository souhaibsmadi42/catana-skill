# Workflows

End-to-end recipes. `catana.py` = `python <skill>/scripts/catana.py` (in a plugin `<skill>` = `${CLAUDE_PLUGIN_ROOT}`).
Every workflow follows the same spine: SKILL.md's nine steps — objective → output type → references → workflow →
provider → prompts → **QC gate** → execute (or prompt pack) → validate and offer improvements.

## 0. The intelligent workflow, in one picture

```
request ─► objective / output / references / constraints   (ask only what's essential)
        ─► mode (routing table in SKILL.md)  ─► reference doc for that mode
        ─► spec(s):  catana.py enhance … --json   → refine with real specifics, references + preserve lists
        ─► QC:       catana.py lint spec.json [--provider p --model m]     (plans: catana.py plan compile)
        ─► provider: catana.py select --op <op> --available <connectors>   (local ones auto-detected)
        ─► execute:  quote → approval → connector call / VoiceStudio / motion engine → verify asset → catana.py log
                     failure → catana.py next → retry | fallback | ask | fix input | prompt pack
        ─► deliver:  assets + settings + what's verified + 2–3 next moves
```

## 1. Single image (hero shot, editorial, concept art, style transfer)
1. `catana.py enhance "<request>" --json > spec.json`. Check that the detected domain and aspect ratio are right (override with
   `--domain` or `--aspect`).
2. Edit spec.json: concrete subject (material, finish, colour, details), environment, light source and direction, lens,
   brand colours. Add `references`: `{"source": "...", "role": "product|subject|style|composition|geometry", "preserve": [...]}`.
3. `catana.py lint spec.json` until `ready` and grade A/B.
4. Operation = t2i, i2i, multi_ref_image or style_transfer (`qc.needed_operation`). Then `catana.py select --op <op>`.
5. Paid connector: preflight the cost (Higgsfield `generate_image` with `get_cost:true`), ask, then generate 2–4
   variations and verify each against the spec (text, logo, anatomy, geometry). Log every asset.
6. No provider: `catana.py pack spec.json --out out/pack`. Say clearly that this is a prompt pack.

Details: [IMAGE_GENERATION.md](IMAGE_GENERATION.md).

## 2. Single video shot (text-to-video, image-to-video, first/last frame)
1. `catana.py enhance "<request>" --modality video --duration <s> --json`.
2. One primary camera move (+ at most one secondary). Check it with `catana.py camera check <ids> --duration <s>`. Plan one action
   per ~2.5 s. Set `technical.motion_intensity` to low for architecture and products.
3. References: `first_frame` (i2v), `first_frame` + `last_frame` (first_last), several `subject`/`product`/`character`
   refs (multi_ref_video), with preserve lists.
4. Lint with the target model: `catana.py lint spec.json --provider higgsfield --model seedance_2_0` checks duration range,
   aspect ratio and operation support.
5. Quote, get approval, execute, wait, verify the motion: did the camera do what was asked, is the geometry stable, does
   the subject stay on model? Log it.

Details: [VIDEO_GENERATION.md](VIDEO_GENERATION.md), [CAMERA_MOVEMENTS.md](CAMERA_MOVEMENTS.md).

## 3. AI Director: idea → full production (`/catana:video-director`, `/catana:storyboard`, `/catana:scene-builder`)
1. `catana.py plan new "<idea>" --duration <s> [--platform p] [--domain d] --out plan.json`. This sizes the shots to the
   duration and to each camera move's minimum length, follows the domain's beat structure, and varies the moves.
2. Fill the creative fields: concept, visual direction, logline, bible (characters/products/locations as `@id`, palette,
   grade, lens package, lighting), and per shot subject, action, environment, VO, SFX, transition, and optionally a
   lighting/time-of-day override for deliberate changes.
3. `catana.py plan compile plan.json --out build/plan`. Output: `compiled.json` plus `storyboard.md`, with a keyframe prompt and a
   video prompt per shot, the EDL, the VO plan with slot-fit warnings, per-shot QC and sequence continuity QC.
4. Fix every error. Show the storyboard. Storyboard-only requests stop here.
5. Execute: generate keyframes (images) first and approve them, then animate each keyframe (i2v) so continuity holds. Quote
   the whole batch first.
6. Voiceover (free): `catana.py voice plan build/plan/compiled.json --out-dir build/vo`.
7. Assemble from the EDL (any editor), or in the motion engine for type, graphics and the end card.

Details: [../references/director.md](../references/director.md).

## 4. Studios
| Studio | Command(s) | Reference |
|---|---|---|
| UGC | `/catana:ugc-video` | [../references/studios/ugc.md](../references/studios/ugc.md) |
| Advertising | `/catana:ad-multiplier`, `/catana:campaign-studio` | [../references/studios/advertising.md](../references/studios/advertising.md) |
| Cinematic | `/catana:cinematic-video` | [../references/studios/cinematic.md](../references/studios/cinematic.md) |
| Product | `/catana:product-commercial`, `/catana:hero-shot` | [../references/studios/product.md](../references/studios/product.md) |
| Architecture | `/catana:architecture-film` | [../references/studios/architecture.md](../references/studios/architecture.md) |
| Social + faceless | `/catana:faceless-video`, `/catana:campaign-studio` | [../references/studios/social.md](../references/studios/social.md) |
| Character | `/catana:character-studio` | [../references/studios/character.md](../references/studios/character.md) |

## 5. Character consistency
1. Write one bible entry per character: identity, face, hair, build, wardrobe, distinguishing marks, voice. The text is
   locked: never paraphrase it.
2. Generate a turnaround and expression sheet (with approval) and keep the images as `character` references.
3. In every shot, add `"characters": ["maya"]` or an `@maya` token in the subject, plus the reference image. `apply_bible`
   inserts the locked text and identity negatives.
4. `plan compile` / `lint_sequence` fails when a shot drifts from the bible wording.

## 6. Campaigns and variations
1. Big idea → 2–3 creative routes → a matrix of hooks × angles × formats × platforms (`data/platforms.json` gives each
   platform's ratio, length, hook window and safe zones).
2. Name the variations systematically (`<brand>_<route>_<hook>_<platform>_v1`) so tests are readable.
3. One spec per variation, lint all of them, and quote the batch total before generating anything.

## 7. Motion film, Katana style (`/catana:motion-film`)
The original CATANA workflow, unchanged in spirit: [../references/motion-film.md](../references/motion-film.md).
Scaffold (`scripts/new_film.py … --format 9:16`) → read the music → plan in beats → build shots → stills QC → render →
mix (procedural SFX on the user's track, optional free VoiceStudio VO, ducked) → QC → deliver.

## 8. Voiceover (always free)
- Single line or script: `catana.py voice speak "<text>" --out vo.wav [--voice v] [--instructions "warm, unhurried"]`.
  Scripts over 4,096 characters are split and joined automatically, in WAV.
- Plan: `catana.py voice plan compiled.json --out-dir build/vo` writes one clip per line plus `vo.json` cues for the mixer.
- Fit a line to its slot: `catana.py voice fit "<line>" --seconds 3.2`.
- VoiceStudio unreachable (cloud session, or app closed): deliver the script with timings and direction in the prompt pack,
  and say so.

## 9. Execution protocol for connectors (Higgsfield, Runway, ElevenLabs)
1. Discover: `models_explore` (Higgsfield), `whoami` (Runway), `creative_get_flow_node_types` (ElevenLabs). Confirm the model
   supports the operation, duration and ratio.
2. Preflight the cost (Higgsfield `get_cost:true`, ElevenLabs `estimate_only:true`), show the exact amount, and get approval.
3. Submit once. Never resubmit to "retry" a job whose outcome is unknown; check its status instead.
4. Wait with the provider's wait/poll tool, then verify the returned asset against the spec.
5. `catana.py log --file catana_runs.jsonl --provider … --op … --status succeeded --asset <url|id> --prompt "…"`.
6. On error: `catana.py classify-error "<msg>"`, then `catana.py next --attempts attempts.json --op …`.

Details: [PROVIDERS.md](PROVIDERS.md).

## 10. Fallback (always available)
`catana.py pack spec.json|plan.json --out out/pack` writes per-shot Markdown and JSON (prompt, negative prompt, settings,
VO script) and a storyboard. Status `prompt_only`: tell the user nothing was generated, and where to paste each prompt.
