# Cinematic Studio — film sequences and short films

Narrative filmmaking: scene planning, characters, storyboards, camera direction, cinematic lighting, film grading
and shot continuity. Use for `/catana:cinematic-video`, `/catana:storyboard`, `/catana:scene-builder`, short films, trailers, music-video
sequences and brand films with a story. Preset: **`cinematic`** (anamorphic 40mm, motivated practicals, haze,
teal-and-amber grade, 35mm grain, 24 fps default). For character-heavy work also read `studios/character.md`.

## Inputs

Premise or script, length, ratio (16:9 default; 2.39:1 look = 16:9 with letterbox in the edit; vertical for social),
genre/tone references (films, photographers — describe the qualities, don't name living artists as style
instructions), characters, locations, any reference images. Ask for premise + length if missing.

## Narrative development

1. **Logline** — protagonist + want + obstacle + stakes in one sentence.
2. **Beats** (engine template): opening_image → setup → inciting → escalation → climax → resolution. For 60–90 s use one
   scene per beat; for 15–30 s merge setup/inciting and escalation/climax.
3. **Scene list** — one location + one time of day per scene; split the plan into `scenes[]` accordingly.
4. **Shot design** per scene: establishing → medium → close → insert → reaction; give each shot one dramatic job.

```bash
python <skill>/scripts/catana.py plan new "<logline>" --domain cinematic --duration 60 --out plan.json
python <skill>/scripts/catana.py plan compile plan.json --out build/film
```

## Continuity grammar (apply when filling shots)

| Rule | How to write it into shots |
|---|---|
| 180° rule | note the axis in `notes` ("camera stays on the window side of the line"); keep screen direction words consistent ("walks left to right") |
| Screen direction | a character exiting frame right enters the next shot frame left |
| Eyeline | in shot/reverse-shot, A looks camera-left, B looks camera-right; same lens and height |
| Match cut | end shot N and start shot N+1 on the same shape/motion; set `transition_out: "match cut on <shape>"` |
| Lighting continuity | one `time_of_day` per scene; bible lighting; changes only as marked transitions |
| Wardrobe / props | in the bible character text, never per shot |
| Shot-size progression | don't cut between two shots of the same size and angle (jump cut) unless intended |

The sequence linter checks aspect ratio, style/grade wording, time-of-day jumps, repeated camera moves and duration.

## Lighting recipes (write into `bible.lighting` or per-shot `lighting`)

- **Noir night:** hard single practical through blinds, deep shadows, wet ground speculars, haze.
- **Golden-hour drama:** low warm sun behind subject as rim, negative fill on the shadow side, flares.
- **Overcast realism:** soft top light, low contrast, muted greens — for grounded drama.
- **Neon thriller:** magenta/cyan practicals, wet surfaces, faces lit by signage, cyan shadows.
- **Candle / firelight:** warm flickering key below eye level, surrounding darkness.
- **Moonlit exterior:** cool top-back light, silver rims, faces barely lit with soft fill.

## Grade recipes (write into `bible.grade`)

| Name | Description to use |
|---|---|
| Teal & amber | warm skin and highlights, teal shadows, rich contrast, soft highlight roll-off |
| Bleach bypass | desaturated colour, crushed contrast, silver highlights, gritty grain |
| Kodak 5219 night | deep inky blacks, warm practicals, cyan-green shadows, fine grain |
| Pastel nostalgia | lifted blacks, soft pastel palette, gentle halation, 16mm grain |
| High-contrast monochrome | black-and-white, deep blacks, bright highlights, strong grain |
| Cold Nordic | cool desaturated blues and greys, pale skin tones, low contrast |

## Verified prompt patterns (`catana.py enhance`, QC A 100)

```text
cinematic video of a detective walking down a rain-soaked alley at night under neon signs, slow tracking shot, 8 seconds
cinematic film still of an old fisherman mending nets in a wooden boat at dawn, close-up, 35mm film
cinematic video of two astronauts arguing inside a cramped spacecraft cockpit, slow push in, 6 seconds
```

The first renders to (excerpt): *"Slow tracking shot moving alongside the subject at matching speed, background
streaming past: a detective walking down a rain-soaked alley under neon signs … Widescreen composition with
deliberate depth: foreground element, subject in the midground … anamorphic 40mm lens, f/2.8, gentle oval bokeh …
Night scene, motivated practical lights … specular highlights on wet surfaces … filmic teal-and-amber grade … fine
film grain."*

Pattern: `cinematic <video|film still> of <character + one dramatic action> <in specific location> <time/light>, <move>, <duration>`.

## Camera direction by beat

opening_image: `aerial_reveal`, `crane_down`, `pull_out` · setup: `dolly_in`, `steadicam` · inciting: `push_in`,
`rack_focus`, `dutch_angle` · escalation: `tracking`, `handheld`, `whip_pan`, `fpv_drone` · climax: `arc`,
`bullet_time`, `push_in` · resolution: `crane_up`, `dolly_out`, `static`. Full library: `docs/CAMERA_MOVEMENTS.md`.

## Provider routing

| Need | Operation | Options (verify first) |
|---|---|---|
| Keyframes / storyboard frames | t2i, multi_ref_image | Higgsfield `soul_cinematic`, `cinematic_studio_2_5`, `nano_banana_pro` |
| Shots from keyframes | i2v, first_last | `cinematic_studio_video_4_0` (camera body, lens, aperture, lighting rig, palette, genre), `kling4_0`, `seedance_2_0` |
| Multi-shot scene in one pass | multi_shot | `kling_o3_image_reference` / `kling_o3_flf` (`multi_prompt`), `cinematic_studio_video_v2` (multi_shots) |
| Extend / continue a shot | extend_video | `seedance_2_5` / `cinematic_studio_video_4_0` (`video_extension`) |
| Performance from reference footage | motion_transfer | `hf_mult_motion_control` |
| Dialogue / narration | tts | VoiceStudio (free); lip-sync `sync_so` only with approval |

## QC checklist

- [ ] Logline and beats written; each shot has one dramatic job
- [ ] Characters only via bible `@id`; same wardrobe across shots
- [ ] One time of day per scene; 180° and screen direction noted
- [ ] Shot sizes progress; no accidental jump cuts; ≥ 1 insert per scene
- [ ] Grade and style only in the bible
- [ ] Shots 3–6 s; anything > 10 s planned as multi-shot or split

## Failure modes → fixes

| Symptom | Fix |
|---|---|
| "Video game" look | `cinematic` negatives; add haze, practical light sources, film grain, lens imperfection |
| Characters change between shots | keyframe per shot from the same character reference; `seedance_2_0`/multi-ref models |
| Flat lighting | name the motivated source and direction; add negative fill |
| Action rushed | one action per 2.5 s; split into shots |
| Geography confusing | add an establishing shot per scene; respect screen direction |

## Deliverables

Logline · beat sheet · scene list · bible (characters, locations, lighting, grade) · storyboard with keyframe + video
prompts · shot list with continuity notes · sound design (music cue, SFX per shot, dialogue/VO) · EDL.
