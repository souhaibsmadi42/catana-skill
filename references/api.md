# Engine API

Project layout (from `assets/template`):
```
render.mjs            two-pass renderer (clean frame -> post shader -> final)
src/lib.js            FILM config (W,H,FPS,DURATION,BPM,OFFSET,MUSIC) + easing, kf, rng, DOM helpers
src/kit.js            beat grid, shots, type primitives, slash line, HUD
src/post.js           FX event list + WebGL finishing shader
src/scenes.js         YOUR FILM: initScenes(), updateScenes(t), gradeAt(t), sceneEvents()
src/main.js           frame driver (setTime / postFX / renderReady / ?dump=1 / ?t= / ?play)
src/style.css         palette tokens + type roles (.k .anton .kmono .outline .hot .kgrad)
audio/mix.py          music + procedural SFX on build/events.json
tools/                music_scan.py, sheet.py, qc.py, page.mjs, evalfx.mjs, chrome.mjs
```
Layers (back to front): `#gl` 3D · `#dw` SVG drawings · `#ui` HTML UI · `#kt` type · `#ov` overlay SVG (slash, logo strokes) · `#hud`.

## Determinism contract
Every visible value is computed from `t`. No `Math.random`, `Date`, timers or running CSS animations; use `rng(seed)`.
Helpers cache last values (`show`, `tf`, `txt`, `attr`), so setting them every frame is cheap.

## lib.js
- `FILM` — format + music grid. `render.mjs` and `audio/mix.py` read it from the file.
- `Ease.{lin,in,out,inOut,outQ,inQ,inOutQ,outExpo,inExpo,inOutExpo,sine,outBack}`
- `kf(t, [[t0, v0], [t1, v1, ease], …])` — numbers or arrays.
- `clamp, lerp, inv(t,a,b)`, `rng(seed)`, `fmtN(n)` → "12,480".
- DOM: `h(tag, cls, parent, css, html)`, `s(svgTag, attrs, parent)`, `show(el, opacity)`, `tf(el, transform)`, `txt(el, str)`, `attr(el, k, v)`.

## kit.js
- `B(k)` beat k start (fractional ok), `BEAT` seconds per beat, `BAR(n)`.
- `shot(a, b, {ui, svg, parent})` → `S` with `S.root` (in #kt), `S.ui` (in #ui) if `ui:true`, `S.svg` (`<g>` in #dw, or in `#ov` with `svg:'ov'`). Set `S.update = (t, lt, p) => {…}`; `lt` = local time, `p` = 0..1.
- `runShots(t)` — call in `updateScenes`.
- `drift(el, lt, z0, z1, dx, dy, dur)` — slow push on a container.
- `T(parent, html, css, cls='k anton')` → hidden absolutely-positioned element. `cls: 'kmono'` for labels, `'k'` for free styling, `'k anton outline hot'` for outline echoes.
- `slam(e, t, a, b, {s0, d, dx, dy, od, ox, oy, ofade, rot, grow, fade, base})` — visible only in [a, b).
- `maskLine(parent, html, css)` + `rise(m, t, a, b, d)` — line rises out of a clip.
- `track(e, t, a, b, from, d)` — letter-spacing collapse (wordmarks).
- `echo(e, t, a, d, k)` — outline ghost scaling out after a slam (put an outline copy behind the word).
- `counter(e, t, a, b, v0, v1, ease, fmt)` — rolling number; `fmt` e.g. `v => v.toFixed(2) + ' M³'`.
- `typed(e, t, a, str, step, cursor)` — typewriter (step 1/16 note = `BEAT/4`).
- `drawOn(path, p)` — needs `pathLength=1` and `stroke-dasharray="1 1"`.
- `initSlash(ovSvg, colors)`, `addSlashLine(t, ang, px, py, lead)`, `drawSlash(t)` (call in updateScenes).
- `initHud(el, {title, right, accent})`, `hud(t, opacity, chapterText, invertForLightFrames)`.

## post.js (register at init; evaluated per frame by `fxAt`)
`hit(t,k)` · `punch(t,k,dur)` · `flash(t,frames,k,[r,g,b])` · `whip(t,dur,ang,len,wrap)` · `slash(t,ang,k,px,py)` ·
`glitch(t,dur,k)` · `invert(t,dur)` · `rumble(t,dur,k)` · `zoomBlur(t,dur,k)` · `caRamp(t,dur,k)` · `tilt(t,dur,ang)`.
`gradeAt(t)` (in scenes.js) returns base overrides merged before events: `{grain, vig, contrast, bright, sat, bx, by, ca}`.
Shader stages: slash split → shake/zoom/roll → glitch slices → directional + radial blur (24 taps) with chromatic
aberration → grade → invert → slash gap glow → flash → vignette → grain. `NOPOST=1` renders clean frames.

## Audio cues
In scenes.js: `ev(t, kind, k)` (template defines it). Kinds understood by `audio/mix.py`:
`impact` (k>0.85 = big) · `boom` · `hitS` (short hit) · `slash` (shing + rip + sub) · `tick` · `blip` · `glitch` ·
`pen` · `whoosh` (put at the whip start) · `whooshL` · `scroll` (1.8 s tick run) · `swell` · `click` · `type` ·
`toggle` · `step` · `drop` · `riser` (ends one beat later; push `{t, kind:'riser', k, d}` for other lengths) · `outro`.
Add instruments in `audio/mix.py` (filtered_noise, impact, whoosh, riser, suck, shimmer, blip, click, knock, clink, pad_chord… are there).

## Snippets
Staccato words, one per beat, last one inverted:
```js
const S = shot(B(8), B(16));
S.w = ['EVERY', 'ONE', 'IS A', 'COST.'].map(w => T(S.root, w, { left: '0', top: '330px', width: '1920px', textAlign: 'center', fontSize: '400px', color: 'var(--ink)' }));
S.update = t => S.w.forEach((e, i) => slam(e, t, B(12 + i), B(13 + i), { s0: 1.3, d: 0.18 }));
for (let i = 0; i < 4; i++) { hit(B(12 + i), 0.6); ev(B(12 + i), 'hitS', 0.6); }
invert(B(15), 0.5);
```
One item per 2 beats, alternating sides:
```js
S.update = (t) => {
  const i = clamp(Math.floor((t - B(124)) / (2 * BEAT)), 0, items.length - 1), right = i % 2 === 1;
  [S.code, S.name].forEach(e => { e.style.left = right ? 'auto' : '110px'; e.style.right = right ? '110px' : 'auto'; e.style.textAlign = right ? 'right' : 'left'; });
  txt(S.code, items[i].code); slam(S.code, t, B(124 + 2 * i), B(126 + 2 * i), { s0: 1.28, dx: right ? 60 : -60 });
};
```
UI camera (explicit origin keeps the maths predictable): to put panel point (px, py) at screen (X, Y) with zoom z:
```js
S.ui.style.transformOrigin = '0 0';
tf(S.ui, `translate(${X - z * px}px, ${Y - z * py}px) scale(${z})`);
```
Build strobe on 16ths: `if (t >= B(28) && Math.floor((t - B(28)) / (BEAT / 4)) % 2) { /* alternate look */ }`.
