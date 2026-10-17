# Render, audio, QC, delivery

Requirements: Node 18+, Python 3 with numpy, scipy, soundfile, pyloudnorm, Pillow (matplotlib optional), Chrome/Edge
(auto-detected; `CHROME=/path` to override). `ffmpeg-static` comes with `npm install`.
`pip install numpy scipy soundfile pyloudnorm pillow matplotlib` if any is missing.

## Stills
```bash
node render.mjs stills 2.1 4.6 8.2            # out/stills/t_002.100.png … (final look, post pass included)
NOPOST=1 node render.mjs stills 8.2           # clean frame (debug layout without shake/grain)
python tools/sheet.py qa/s1.jpg 3 out/stills/*.png   # contact sheet to look at (2 or 3 columns)
```
Clear `out/stills` between batches (`rm -f out/stills/*.png`) so sheets only show the current batch.
Preview in a browser: serve the project root and open `src/index.html?t=12.5` or `?play`.

## Video
```bash
node render.mjs video --workers 6 --crf 15 --name master_noaudio.mp4      # whole film
node render.mjs video --from 30 --to 45 --workers 4 --name part.mp4       # a range
```
Speed: ~3 fps per worker for a DOM + 3D page with the post pass (2-minute film ≈ 7–9 min on 6 workers). Run long
renders in the background and wait on the log (`out/*.log`), don't poll in a tight loop.
Each worker is a separate Chrome; segments are concatenated with stream copy (frame-exact).

## Audio
```bash
node tools/page.mjs "src/index.html?dump=1" build/events.json     # cue list from scenes.js
python audio/mix.py                                               # out/soundtrack.wav, -14 LUFS, -1 dBFS
```
Re-dump and re-mix whenever cue times change. The music is used unedited (cut the picture to the music, not the
reverse). The SFX are procedural — say so on delivery; if the user has recorded SFX, load them in mix.py with
`sf.read` and `add(sfx, t, x)`.

## Mux, web copy, QC
```bash
FF=node_modules/ffmpeg-static/ffmpeg.exe     # (ffmpeg on mac/linux)
$FF -y -v error -i out/master_noaudio.mp4 -i out/soundtrack.wav -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart ../Film_1080p60.mp4
$FF -y -v error -i ../Film_1080p60.mp4 -c:v libx264 -preset slow -crf 25 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart ../Film_1080p60_web.mp4
python tools/qc.py ../Film_1080p60.mp4 qa/final      # per-frame pop/blip scan, near-black frames, 1 fps contact sheets
```
Grain makes CRF-15 masters big (~70 Mbit/s); the CRF-25 web copy is ~8 Mbit/s.
QC reading: isolated 1-frame pops on beat times are your flashes (intended); pops *between* beats or on shot
boundaries are bugs (a shot showing one frame early/late, a missing hold). "Hard changes" are your cuts. Look at the
`qa/final_*.png` sheets (1 frame per second) end to end before delivering.

## Debugging
- `EXPR="window.__dbg(t)" node tools/evalfx.mjs 26.4` — which shots are active at t (empty = a timing bug).
- `node tools/evalfx.mjs 15.3` — post parameters at t (unexpected `inv`, `bx`, `glitch` = an event at the wrong time).
- Page errors print as `[pageerror]` during renders; a thrown error inside `update` stops that frame's later shots.
- Everything black for a section → shot timing overwritten (see the `_t0/_t1` gotcha) or wrong beat→second maths.
- All shots' text visible at once → containers toggled by visibility instead of display.

## Delivery message
State: files + sizes, length/format, the section structure in one line each, what's real (data, UI, model) vs
illustrative, what was verified (stills, QC sheets, loudness) and what wasn't (real-time viewing/listening), and
how to change things (edit scenes.js → stills → re-render ~N min).
