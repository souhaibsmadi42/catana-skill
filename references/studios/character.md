# Character Studio — consistent AI characters

Create a character once and keep them identical across images, shots and videos: spokespeople, mascots, story
protagonists, recurring creators. Use for `/catana:character-studio` and whenever the same person/creature must appear more
than once. Preset: **`character`** (85mm f/1.8, Rembrandt key, natural skin texture, identity-drift negatives).

## Ethics first

Only fictional characters, or real people who gave consent (the user themselves, or with documented permission).
Never recreate a celebrity, public figure, private individual or a "lookalike" from a description designed to evoke
them; no minors in sexualized or harmful contexts. Recommend AI-generated labels where the content is published.

## Character bible template

Write this into `plan.bible.characters.<id>` (one paragraph, concrete, ≤ 70 words — it is pasted into every shot):

| Field | Example |
|---|---|
| Identity | Maya, 30, documentary photographer |
| Face | oval face, olive skin, dark brown almond eyes, straight thick eyebrows, small scar over the left eyebrow |
| Hair | short black bob with a blunt fringe |
| Body | 1.68 m, slim, upright posture |
| Wardrobe (default) | mustard wool coat over a black roll-neck, dark jeans, worn brown boots |
| Distinguishing marks | silver hoop in the right ear, scar over left eyebrow |
| Voice | low, calm, slight rasp; VoiceStudio voice id/profile |

Wardrobe changes = a new bible entry (`maya_evening`), never ad-hoc per shot.

## Workflow

1. **Bible** (above). Keep a short version for prompts and the long version in notes.
2. **Character sheet / turnaround** — generate one reference set with the same seed/model where supported:
   front, three-quarter left, profile, back, three-quarter right; plus 4–6 expressions (neutral, smile, laugh, anger,
   concern, surprise) as head-and-shoulders. Plain light-grey background, even soft light, full-length for the body
   views. Pick the most accurate frame as the **master reference**.
3. **Register the reference:** save the master and sheet with the project; on Higgsfield, optionally create a Soul
   ID or reference element (`manage_reference_elements`, `show_characters`; Soul models accept `soul_id`) — paid and
   account-specific, verify first.
4. **Use in shots:** `@maya` tokens in `subject`, `characters: ["maya"]`, and a `character` reference on every shot:
   ```json
   {"source": "maya_master.png", "role": "character", "preserve": ["face identity and proportions", "hairstyle and hair colour", "skin tone", "scar over left eyebrow", "wardrobe"]}
   ```
   `apply_bible` pastes the identical description and adds identity-drift negatives; the sequence linter errors if a
   shot that lists the character lacks the locked text.
5. **Video:** keyframe per shot with the master reference (multi_ref_image) → animate (i2v) or use a multi-reference
   video model. Keep 3–6 s per shot; one character action per shot.
6. **Voice:** a VoiceStudio profile (`catana.py voice archetypes` / `voice describe`) reused for every line.

```bash
python <skill>/scripts/catana.py enhance "<character portrait request>" --json > maya.json   # add references, lint
python <skill>/scripts/catana.py plan new "short film with Maya, a documentary photographer" --domain character --duration 30 --out plan.json
```

## Verified prompt patterns (`catana.py enhance`, QC A 100)

```text
cinematic portrait of a woman in her thirties with a short black bob and a scar over her left eyebrow, wearing a mustard wool coat, standing on a rainy train platform
character video of a young male chef with curly red hair and freckles tasting a sauce in a busy kitchen, slow push in, 5 seconds
```

Pattern: `<portrait|character video> of <age> <defining face/hair features> <wardrobe> <in place> <one action>, <move>, <duration>`.
The defining features go first so models weight them; keep them identical in every prompt.

## Camera

Portraits and emotion: `push_in`, `rack_focus`, `static`, `arc` (hero) · movement: `tracking`, `steadicam` ·
avoid fast `whip_pan`/`fpv_drone` on faces (identity smears). Keep the same focal length for a character within a scene.

## Provider routing

| Need | Operation | Options (verify first; paid → quote + approval) |
|---|---|---|
| Sheet / turnaround | t2i, multi_ref_image | Higgsfield `soul_2` / `soul_cinematic` (+ Soul ID), `nano_banana_pro`, `flux_3_image` |
| Persistent identity | — | Soul ID / reference elements; `soul_cast` (consistent cinematic identity) |
| Shots with identity | multi_ref_video, i2v | `seedance_2_0` (consistent identity), `kling_o3_image_reference` (up to 7 refs, multi-shot), `kling4_0` (elements) |
| Motion from real footage | motion_transfer | `hf_mult_motion_control` (single character recast) |
| AI influencer flow | — | `ai_influencer_prepare` → `ai_influencer_generate` (quote first) |
| Talking | tts + lipsync | VoiceStudio (free) + `sync_so` (paid, approval) |

## Consistency QC

- [ ] Bible entry concrete (face, hair, marks, wardrobe) and ≤ 70 words
- [ ] Master reference attached with a `preserve` list on every shot
- [ ] `characters` set on every shot the person appears in; sequence lint passes
- [ ] Same model family for all shots of a sequence
- [ ] Expressions and angles covered by the sheet before animating
- [ ] Hands visible only when needed; one action per shot
- [ ] Consent / fictional status recorded

## Failure modes → fixes

| Symptom | Fix |
|---|---|
| Face drifts between shots | re-anchor each shot on the master keyframe (i2v), not text-to-video; shorter shots |
| Hair/wardrobe changes | wardrobe in the bible only; add to preserve list |
| Profile view off-model | include profile in the sheet and use it as the reference for profile shots |
| Two characters merge | one character per half of frame; separate references; avoid crossing paths |
| Uncanny smile/eyes | neutral expressions; natural skin texture text; avoid extreme close-ups in motion |

## Deliverables

Character bible · turnaround + expression sheet · master reference(s) · voice profile · per-shot prompts with
references · consistency report (sequence lint) · run log.
