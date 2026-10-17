// Katana kit: beat grid, shot containers, slam type, counters, slash line, HUD. Everything is a pure function of t.
import { FILM, h, s, attr, show, tf, txt, Ease, clamp, lerp, fmtN } from './lib.js';

// ------------------------------------------------------------------ beat grid
// B(k) = start time of beat k (fractional beats allowed: B(12.5) is the "and" of beat 12). Write every cue in beats.
export const BEAT = 60 / FILM.BPM;
export const B = k => FILM.OFFSET + BEAT * k;
export const BAR = k => B(4 * k);

// ------------------------------------------------------------------ shots
// A shot owns DOM containers that exist only while it is active. Timing lives in _t0/_t1 because scenes freely
// attach elements to the shot object (S.a, S.b, S.t1 ...) — never store timing in short names.
export const SHOTS = [];
export function shot(a, b, opt = {}) {
  const sh = { ...opt, _t0: a, _t1: b };
  sh.root = h('div', 'shot', opt.parent || document.getElementById('kt'));
  sh.root.style.display = 'none';
  if (opt.ui) { sh.ui = h('div', 'shot', document.getElementById('ui')); sh.ui.style.display = 'none'; }
  if (opt.svg) { sh.svg = s('g', null, document.getElementById(opt.svg === true ? 'dw' : opt.svg)); sh.svg.style.display = 'none'; }
  SHOTS.push(sh);
  return sh;
}
// containers are toggled with display (a visibility:visible child would show through a hidden parent)
export function runShots(t) {
  for (const sh of SHOTS) {
    const on = t >= sh._t0 && t < sh._t1;
    if (sh._on !== on) {
      sh._on = on;
      const d = on ? '' : 'none';
      sh.root.style.display = d;
      if (sh.ui) sh.ui.style.display = d;
      if (sh.svg) sh.svg.style.display = d;
    }
  }
  for (const sh of SHOTS) if (t >= sh._t0 && t < sh._t1 && sh.update) sh.update(t, t - sh._t0, (t - sh._t0) / (sh._t1 - sh._t0));
}
// slow constant push on a container (Katana shots never sit perfectly still)
export function drift(el, lt, z0 = 1, z1 = 1.05, dx = 0, dy = 0, dur = 2) {
  const p = clamp(lt / dur);
  tf(el, `translate(${(dx * p).toFixed(2)}px,${(dy * p).toFixed(2)}px) scale(${lerp(z0, z1, p).toFixed(4)})`);
}

// ------------------------------------------------------------------ type
export function T(parent, html, css = {}, cls = 'k anton') {
  const e = h('div', cls, parent, Object.assign({ left: '0', top: '0' }, css), html);
  e.style.visibility = 'hidden';
  return e;
}
// slam: hard cut in at a (scale s0 -> 1, outExpo over d), hold, hard cut out at b (or slide out over od)
// o: { s0, d, dx, dy, ox, oy, od, ofade, rot, base, fade, grow }
export function slam(e, t, a, b, o = {}) {
  if (t < a || t >= b) { show(e, 0); return 0; }
  const d = o.d ?? 0.22, p = Ease.outExpo(clamp((t - a) / d));
  const sc = lerp(o.s0 ?? 1.16, 1, p) * (o.grow ? 1 + o.grow * (t - a) : 1);
  let x = (o.dx || 0) * (1 - p), y = (o.dy || 0) * (1 - p), op = o.fade ? Ease.out(clamp((t - a) / o.fade)) : 1;
  if (o.od) { const q = Ease.inExpo(clamp((t - (b - o.od)) / o.od)); x += (o.ox || 0) * q; y += (o.oy || 0) * q; if (o.ofade) op *= 1 - q; }
  show(e, op);
  tf(e, `${o.base || ''} translate(${x.toFixed(1)}px,${y.toFixed(1)}px) scale(${sc.toFixed(4)})${o.rot ? ` rotate(${o.rot}deg)` : ''}`);
  return p;
}
// mask reveal: a line rises out of a clip
export function maskLine(parent, html, css, cls = 'k anton') {
  const e = T(parent, '', Object.assign({ overflow: 'hidden', paddingBottom: '0.04em' }, css), cls);
  const inner = h('div', null, e, { display: 'inline-block', willChange: 'transform' }, html);
  return { e, inner };
}
export function rise(m, t, a, b, d = 0.18) {
  if (t < a || t >= b) { show(m.e, 0); return; }
  show(m.e, 1);
  tf(m.inner, `translateY(${((1 - Ease.outExpo(clamp((t - a) / d))) * 105).toFixed(2)}%)`);
}
// wide tracking snapping shut (good for wordmarks — never reveal a brand name letter by letter)
export function track(e, t, a, b, from = 0.5, d = 0.3) {
  if (t < a || t >= b) { show(e, 0); return; }
  show(e, 1);
  const v = lerp(from, 0, Ease.outExpo(clamp((t - a) / d))).toFixed(4) + 'em';
  if (e._ls !== v) { e.style.letterSpacing = v; e._ls = v; }
}
// stutter echo: outline ghost that scales out over the first `d` seconds of a slam
export function echo(e, t, a, d = 0.22, k = 0.25) {
  if (t >= a && t < a + d) { show(e, 0.7 * (1 - (t - a) / d)); tf(e, `scale(${(1 + k * (t - a) / d).toFixed(3)})`); } else show(e, 0);
}
export function counter(e, t, a, b, v0, v1, ease = Ease.outQ, fmt = fmtN) { txt(e, fmt(lerp(v0, v1, ease(clamp((t - a) / (b - a)))))); }
// typed text, one character per step seconds
export function typed(e, t, a, str, step = 0.0625, cursor = true) {
  const n = clamp(Math.floor((t - a) / step), 0, str.length);
  txt(e, str.slice(0, n) + (cursor && n < str.length && Math.floor(t * 8) % 2 ? '▍' : ''));
  show(e, t >= a ? 1 : 0);
}
// SVG stroke draw-on: give paths pathLength=1 and stroke-dasharray="1 1"
export function drawOn(path, p) { attr(path, 'stroke-dashoffset', (1 - clamp(p)).toFixed(4)); }

// ------------------------------------------------------------------ slash line (drawn just before a cut lands)
let SL = null;
export const SLASHES = [];
export function initSlash(ov, colors = ['#00C6FF', '#FFFFFF', '#A855F7']) {
  const defs = s('defs', null, ov);
  const g = s('linearGradient', { id: 'slg', x1: '0', y1: '0', x2: '1', y2: '0' }, defs);
  colors.forEach((c, i) => s('stop', { offset: String(i / (colors.length - 1)), 'stop-color': c }, g));
  const f = s('filter', { id: 'slglow', x: '-20%', y: '-200%', width: '140%', height: '500%' }, defs);
  s('feGaussianBlur', { stdDeviation: '9' }, f);
  SL = { g: s('g', null, ov) };
  SL.glow = s('line', { stroke: 'url(#slg)', 'stroke-width': 14, filter: 'url(#slglow)', 'stroke-linecap': 'round' }, SL.g);
  SL.core = s('line', { stroke: '#FFFFFF', 'stroke-width': 3, 'stroke-linecap': 'round' }, SL.g);
  show(SL.g, 0);
}
// pair with post.slash(t, ang) at the same t: the line streaks across in `lead` s, the frame splits on impact
export const addSlashLine = (t, ang = -0.42, px = FILM.W / 2, py = FILM.H / 2, lead = 0.2) => SLASHES.push({ t, ang, px, py, lead });
export function drawSlash(t) {
  let any = false;
  for (const e of SLASHES) {
    const dt = t - e.t;
    if (dt < -e.lead || dt > 0.14) continue;
    any = true;
    const L = 2600, dx = Math.cos(e.ang), dy = Math.sin(e.ang);
    let a0 = -L / 2, a1;
    if (dt < 0) a1 = lerp(-L / 2, L / 2, Ease.inQ(clamp((dt + e.lead) / e.lead)));
    else { a1 = L / 2; a0 = lerp(-L / 2, L / 2, Ease.outQ(clamp(dt / 0.14))); }
    for (const ln of [SL.glow, SL.core]) {
      attr(ln, 'x1', (e.px + dx * a0).toFixed(1)); attr(ln, 'y1', (e.py + dy * a0).toFixed(1));
      attr(ln, 'x2', (e.px + dx * a1).toFixed(1)); attr(ln, 'y2', (e.py + dy * a1).toFixed(1));
    }
    attr(SL.core, 'stroke-width', (dt < 0 ? 2 + 3 * clamp((dt + e.lead) / e.lead) : 5 * (1 - dt / 0.14)).toFixed(2));
  }
  show(SL.g, any ? 1 : 0);
}

// ------------------------------------------------------------------ HUD (corner marks, title, timecode, chapter, progress)
let HD = null;
export function initHud(el, { title = 'BRAND ▸ FILM', right = '', accent = '#00C6FF' } = {}) {
  HD = { root: el };
  const m = 'position:absolute;width:26px;height:26px;border-color:rgba(244,245,250,.55);border-style:solid;border-width:0';
  el.innerHTML = `
    <div style="${m};left:40px;top:40px;border-left-width:2px;border-top-width:2px"></div>
    <div style="${m};right:40px;top:40px;border-right-width:2px;border-top-width:2px"></div>
    <div style="${m};left:40px;bottom:40px;border-left-width:2px;border-bottom-width:2px"></div>
    <div style="${m};right:40px;bottom:40px;border-right-width:2px;border-bottom-width:2px"></div>
    <div class="kmono" data-h="tl" style="left:80px;top:46px;color:#F4F5FA">${title}</div>
    <div class="kmono" data-h="tr" style="right:80px;top:46px;text-align:right">TC 00:00:00:00</div>
    <div class="kmono" data-h="bl" style="left:80px;bottom:46px;color:#F4F5FA"></div>
    <div class="kmono" data-h="br" style="right:80px;bottom:46px;text-align:right">${right}</div>
    <div style="position:absolute;left:80px;top:74px;width:120px;height:2px;background:rgba(244,245,250,.18)"><div data-h="bar" style="height:2px;width:0;background:${accent}"></div></div>`;
  el.querySelectorAll('[data-h]').forEach(e => { HD[e.dataset.h] = e; });
}
// a = opacity, ink = invert for light backgrounds
export function hud(t, a, chapter, ink = false) {
  show(HD.root, a);
  if (a <= 0) return;
  const f = Math.floor(t * FILM.FPS + 1e-6), ss = Math.floor(f / FILM.FPS), ff = f % FILM.FPS;
  txt(HD.tr, `TC 00:${String(Math.floor(ss / 60)).padStart(2, '0')}:${String(ss % 60).padStart(2, '0')}:${String(ff).padStart(2, '0')}`);
  if (chapter !== undefined) txt(HD.bl, chapter);
  HD.bar.style.width = (t / FILM.DURATION * 100).toFixed(2) + '%';
  if (HD._ink !== ink) { HD._ink = ink; HD.root.style.filter = ink ? 'invert(1)' : ''; }
}
