---
name: catana
description: Make Katana-style motion graphics films — high-energy promo, launch, product or hype videos (10 s to 3 min) for a website, app, brand or product — built entirely in code and rendered frame-exact to MP4 with a soundtrack. Beat-locked hard cuts, huge slam typography, slash transitions, shake / punch-in / whip / glitch / strobe / flash post effects, real product UI and data, a procedural SFX mix on top of a real music track. Use this skill whenever the user asks for "katana", "katana motion", a "sigma edit", a hype or kinetic edit, a motion graphic video / promo film / launch video for their site or product, a video "cut to the beat", or wants an existing film redone in that punchy style — even if they never say "katana". No AI video generation or credits needed.
---

# catana — Katana-style motion films

Katana is an edit language: the picture obeys the music. Every cut, word, flash and camera hit lands on a beat;
the energy follows the track's sections (calm intro → build → drop → breakdown → silence → bigger drop → outro);
type is huge and blunt; one transition motif (the *slash*) ties the film together; texture (grain, chromatic
fringing, motion blur) is added last. This skill builds that as a deterministic web page — `render(t)` draws any
frame from its time alone — and renders it with headless Chrome, then mixes sound on the page's own cue list.

The engine is a template in `assets/template/`; its `src/scenes.js` is a 12-second demo that uses every primitive.

## What to read when

| Moment | Read |
|---|---|
| Before planning the film | `references/motion-language.md` — the craft: section treatments, effect rates, type rules, copy, restraint |
| Writing shots | `references/api.md` — kit / post / lib API with snippets |
| Rendering, audio, QC, delivery, debugging | `references/pipeline.md` |
| The film needs a 3D model (GLB/IFC/product) | `references/3d-world.md` |

## Workflow

### 1. Gather the real material (don't start without it)
Ask for — or find in the project / website — what makes it *their* film:
- **Subject**: product name, what it does, the 3–6 claims worth making, real numbers (counts, versions, speeds, prices) that are verifiable. Never invent metrics; illustrative visuals get labelled or kept generic.
- **Visuals**: logo (SVG ideal), brand palette, fonts, screenshots or live URLs of the UI, any 3D model, photos. Prefer rebuilding UI panels as HTML/CSS from screenshots (crisp under 2× punch-ins) over pasting low-res captures; crop/blur private data (client names, emails, people).
- **Music**: a real recorded track the user has rights to. The cut is built on it, so it comes first. No track → ask; don't synthesize music.
- **Format**: length (default = the music's natural ending, often 60–120 s), 16:9 1920×1080 60 fps unless told otherwise (9:16 = 1080×1920: change FILM.W/H and the CSS stage size).
If the user said "just do it", infer from the website/project and say what you assumed.

### 2. Scaffold and read the music
```bash
python <skill>/scripts/new_film.py <project_dir> --music <track.wav> --duration <s>
```
This copies the template, runs `npm install`, and scans the track (`tools/music_scan.py`): tempo, beat-0 offset,
a per-bar table of kick / hat energy with a section guess, and `qa/music_scan.png`. Then **verify the downbeat**
(the weakest guess): drops and silences must start on a bar line in the table; fix `OFFSET` in `src/lib.js` if not
(`--offset` re-scans). Write the section map in beats, e.g. `intro 0–31 · drop 32–63 · break 64–79 · silence 112–117 · drop 120–179 · outro 220–239`.

### 3. Plan the film (write it down before coding)
- **Concept + one motif** in a sentence — e.g. "The Cut: a blade slices the model into its quantities". The slash (or your motif) marks every section change.
- **Copy deck**: short, declarative, one idea per beat ("6,393 ELEMENTS." / "EVERY ONE" / "IS A COST."). Sentences only in quiet sections.
- **Shot plan table** in beats: `beats | section | picture | type | FX | SFX`. Match energy to the section (see motion-language.md): drops cut every 1–2 beats, breakdowns breathe, the silence is nearly empty, the outro holds.
- Map real data to moments (a counter on a build, a big number on a drop).
Show the user the concept + section map + a few lines of the plan when the brief was vague; otherwise proceed.

### 4. Build the shots
Edit `src/scenes.js` (the template contains a 12-second demo of every primitive — replace it). Pattern:
```js
const S = shot(B(32), B(36), { ui: true });                 // container lives only for these beats
S.word = T(S.root, 'EXPORT.', { left: '110px', top: '760px', fontSize: '250px', color: 'var(--ink)' });
S.update = (t, lt) => { slam(S.word, t, B(32), B(36), { s0: 1.25 }); };
slash(B(32), -0.42, 1.3); addSlashLine(B(32)); flash(B(32), 2); hit(B(32), 1.2); ev(B(32), 'slash', 1.2);
```
Every cue is in beats via `B(k)`; post effects and audio cues are registered once at init next to the shot that
owns them, so picture, FX and sound can never drift apart.

### 5. Look, fix, repeat (stills before video)
```bash
node render.mjs stills 4.1 8.2 16.6 …        # pick moments inside each shot (just after a cue, mid-hold)
python tools/sheet.py qa/s1.jpg 3 out/stills/*.png
```
Read the contact sheet image. Check per still: is the right shot showing (nothing from other shots leaking)? text inside
frame, not clipped, not colliding with UI? text readable against what's behind it (white on white, cyan on cyan)?
camera framing the subject? Fix and re-render only those stills. Work section by section; it is much faster than
rendering video.

### 6. Render, sound, deliver
```bash
node render.mjs video --workers 6 --crf 15 --name master_noaudio.mp4
node tools/page.mjs "src/index.html?dump=1" build/events.json && python audio/mix.py
# mux + web copy + QC: see references/pipeline.md
```
Deliver the master and a web copy (CRF ~25), say what was verified (stills, QC scan) and what wasn't (nobody has
watched it in real time; SFX are procedural; any illustrative visuals). Offer the next iteration rather than asking
open questions.

## Gotchas that cost hours last time
- Shot timing lives in `_t0/_t1`. Scenes attach elements as `S.a`, `S.b`, `S.t1`… — never store timing under short names.
- Shot containers toggle `display`, not `visibility` (a `visibility:visible` child shows through a hidden parent).
- `B(k)` is beats; offsets like `i * 0.25` are **seconds**. At 120 BPM 0.25 s is an eighth note — at other tempos use `BEAT/2`, `BEAT/4`. Mixing the two silently pushes cues into the next section.
- Anton is very wide at big sizes: estimate width ≈ chars × 0.45 × font-size and keep it under ~1700 px.
- Text over a coloured element: give it a contrasting colour or a dark text-shadow; check stills.
- Whip transitions cut at `t + dur/2` — put the shot boundary there.
- Registering a uniform/array value into a THREE.Vector3 slot replaces the object (see 3d-world.md `uni()`).
- If the user mentions Higgsfield's Katana: that is a paid reference-remix pipeline (AI footage). This skill reproduces the *style* locally; only use paid generation if the user explicitly asks.
