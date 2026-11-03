# Examples

Real sessions with the engine. Outputs are pasted from actual runs of `python scripts/catana.py …` (`C` = that command),
trimmed with `…` where long; in sections 6 and 9 some steps show the command sequence only. Generation steps through paid
connectors are described, not shown: CATANA only runs them after the user approves a quoted cost.

## 1. Prompt enhancer: weak to production-ready (`/catana:prompt-enhancer`)

A weak spec, `{"subject": "nice car", "style": "amazing, 8k, masterpiece", "modality": "video"}`:

```
$ C lint weak.json
0 D  ready=False
  error   | motion is empty -> fill motion
  error   | subject is too thin: 'nice car' -> name the subject concretely: what it is, material/finish, size, colour, distinguishing details, action
  warning | environment is empty / composition is empty / camera is empty / ...
  warning | generic filler words carry no visual information: 8k, amazing, masterpiece, nice -> replace each with a concrete instruction
```

The same idea, said like a director:

```
$ C enhance "a vintage red Porsche 911 driving along a coastal cliff road, aerial reveal, 8 seconds"
[video · automotive · 16:9 · 8s]  QC A (100)
PROMPT
Slow aerial drone reveal, gliding up and over the foreground to reveal the location at scale: a vintage red Porsche 911
driving along a coastal cliff road, the car glides forward with wheels turning, reflections sliding across the bodywork.
Sweeping open road through dramatic landscape. Low three-quarter front view, … 35mm lens, f/4, slight motion blur on wheels
and background. Low raking sun skimming the bodywork, long specular highlights tracing the body lines … Premium automotive
commercial cinematography, rich contrast, deep blacks … Medium motion intensity, temporally consistent, no flicker,
stable identity and geometry from first to last frame, 8-second shot.
NEGATIVE  … warped body panels, mismatched or melting wheels, wrong badge or logo, wheels not touching the road …
```

## 2. Hero shot (`/catana:hero-shot`)

```
$ C enhance "matte black perfume bottle on wet basalt, moody, 4:5"
[image · product · 4:5]  QC A (100)
PROMPT
Matte black perfume bottle on wet basalt, moody, seamless gradient studio sweep. Centered hero composition, product filling
about 60% of the frame, generous clean negative space for copy, slightly low three-quarter angle that gives the product
presence, 100mm macro lens, f/8 for edge-to-edge sharpness. Large softbox key at 45 degrees, strip-light rim tracing the
silhouette, white bounce fill, controlled specular highlights. Accurate materials: crisp label print, true metal and glass
reflections, micro surface texture. Premium commercial studio photography, clean neutral grade, true-to-brand colors, deep
but not crushed blacks.
```
Next, Claude swaps in the brand's real bottle (as a `product` reference with `preserve: ["bottle shape", "cap", "label
artwork"]`), replaces the studio sweep with the basalt set, lints again, quotes the image cost and generates on approval.

## 3. Camera movement (`/catana:camera-movement`)

```
$ C camera check orbit_360 crane_up --duration 8      → ok: true, issues: []
$ C camera check orbit_360 tracking handheld --duration 4
  error   'Orbit 360' conflicts with 'Tracking Shot' -> keep one of them; good partners for Orbit 360: crane_up, bullet_time
  warning 3 simultaneous camera moves — video models follow one or two reliably
  warning 'Orbit 360' needs about 6 s to read; clip is 4 s
$ C camera phrase rack_focus
Rack focus from the nearest element in the foreground to the main subject in the background, shallow depth of field
```

## 4. AI Director: luxury villa commercial, Abu Dhabi (`/catana:video-director`)

```
$ C plan new "Create a luxury cinematic commercial for a modern villa in Abu Dhabi" --duration 40 --out plan.json
wrote plan.json: 8 shots, 40 s, 16:9 — fill the creative fields, then `plan compile`
$ C plan compile plan.json --out build/villa
wrote build/villa/compiled.json and storyboard.md — 8 shots, 40 s; shots needing fixes: none; sequence ready: True
```

| # | Beat | Time | Camera | Transition |
|---|---|---|---|---|
| S01 | establish | 0–5 s | aerial_reveal | fade in from black |
| S02 | approach | 5–10 s | dolly_in | cut on action |
| S03 | threshold | 10–15 s | steadicam | cut on action |
| S04 | flow | 15–20 s | parallax | cut on action |
| S05 | detail | 20–25 s | push_in | cut on action |
| S06 | life | 25–30 s | tracking | cut on action |
| S07 | hero | 30–35 s | crane_up | match cut |
| S08 | end_card | 35–40 s | static | dip to brand colour |

Claude then writes the concept, the bible (palette, grade, lens package, golden-hour lighting, the villa as `@villa` with
its real materials) and per-shot actions and VO, compiles again, and presents `storyboard.md`. That file has a keyframe image
prompt and a video prompt for each shot, the sound plan and the edit sequence. A night ending is a per-shot `lighting` and
`time_of_day` override on S07, plus a transition note; without the note, sequence QC flags the time-of-day jump.

## 5. Other domains, same command

```
commercial for a new electric SUV (20 s)       → fpv_drone 4s · tracking 3s · arc 3s · push_in 3s · steadicam 3s · aerial_reveal 4s   all A
launch film for Aurora wireless earbuds (15 s) → whip_pan 2.1s · orbit_360 6.4s · tracking 3.2s · dolly_out 3.2s                    all A
street food tacos at a night market (18 s)     → push_in · top_down · tracking · rack_focus · arc · static                          all A
UGC review of a vitamin C serum (TikTok)       → 11 × handheld 3.1s, 9:16, 34 s                                                   all A
```
Shots are sized to the duration and to each camera move's minimum length. When a short spot can't fit every beat, the hook
and the end card are always kept.

## 6. UGC with a free voiceover (`/catana:ugc-video`)

```
$ C plan new "UGC review of a vitamin C serum by a young woman at home" --platform tiktok --out ugc.json
# Claude writes the script into the shots' "vo" fields, then:
$ C plan compile ugc.json --out build/ugc
# voiceover lines are checked against their slots, e.g.
#   S01 @0s: "Okay I was not expecting this serum to …" (~6.8s / slot 3.1s) ⚠ trim to about 7 words or lengthen the shot
$ C voice plan build/ugc/compiled.json --out-dir build/vo      # VoiceStudio on your computer — free
```
Talking-head lip-sync (Higgsfield `sync_so`) is a paid step: CATANA quotes it and asks first.

## 7. Choosing a provider and handling failure

```
$ C select --op i2v --available higgsfield,runway --duration 8 --aspect 9:16
[('higgsfield', 'credits', requires_approval=True), ('runway', 'credits', requires_approval=True), ('prompt_only', 'free', False)]

$ C select --op tts --available higgsfield,runway,elevenlabs
policy free_only → ranked ['prompt_only'] here (VoiceStudio not running); ['voice_studio', 'prompt_only'] when it is

$ echo '[{"provider":"higgsfield","status":"failed","error_category":"rate_limited"}]' > attempts.json
$ C next --attempts attempts.json --op i2v --available higgsfield,runway
{"action": "retry", "provider": "higgsfield", "wait": 4, "reason": "rate_limited: transient, retry 1/2"}
```
Insufficient credits, a paid plan requirement or a content-policy refusal returns `stop` (ask the user). Invalid input
returns `fix_input`. Auth or unavailable moves to the next provider, asking first if it's paid, and finally to `prompt_only`.

## 8. VoiceStudio from a cloud session

```
$ C voice health
{"error": "VoiceStudio is not reachable at http://127.0.0.1:3900 ([Errno 111] Connection refused). Start the VoiceStudio
app, or set CATANA_VOICE_STUDIO_URL. A cloud session cannot reach your computer's localhost.", "category": "unavailable"}
exit=3
```
On your own computer with VoiceStudio open, the same command returns its health, and `voice speak` / `voice plan` write WAV
files.

## 9. Motion film (`/catana:motion-film`)

```
$ python scripts/new_film.py inkwell-reel --music track.mp3 --duration 30 --format 9:16 --fps 30
template -> …/inkwell-reel
converted track.mp3 -> assets/music.wav
set BPM 124.04, OFFSET 1.071 (verify the downbeat in qa/music_scan.png)
format 9:16 1080x1920 @ 30 fps
$ node render.mjs stills 4.6 9.3 && python tools/sheet.py qa/s1.jpg 3 out/stills/*.png
$ node render.mjs video --workers 6 --name master_noaudio.mp4
$ node tools/page.mjs "src/index.html?dump=1" build/events.json && python audio/mix.py
```
The 12-second demo was verified in this repo at 16:9, 9:16 and 1:1 (stills), and at 9:16 30 fps (full video: 360 frames,
mixed to −14 LUFS). A VoiceStudio voiceover cue list (`build/vo.json`) is mixed in with music ducked under the voice.

## 10. Fallback prompt pack

```
$ C pack plan.json --out out/pack
{"status": "prompt_only", "files": ["out/pack/s01.md", "out/pack/s01.json", …, "out/pack/storyboard.md"], "note": "nothing was generated"}
```
