// Motion toolkit — every value is a pure function of time t (seconds), so any frame renders in isolation.
// FILM is the single source of truth for format and music grid; render.mjs reads it from the page.
export const FILM = {
  W: 1920, H: 1080, FPS: 60,
  DURATION: 12,            // seconds (set to the edit length, e.g. 120)
  BPM: 120,                // from tools/music_scan.py
  OFFSET: 0.035,           // time of beat 0 in seconds (first downbeat)
  MUSIC: 'assets/music.wav',
};
export const W = FILM.W, H = FILM.H, FPS = FILM.FPS, DURATION = FILM.DURATION;

export const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
export const lerp = (a, b, t) => a + (b - a) * t;
export const inv = (t, a, b) => clamp((t - a) / (b - a));
export const smooth = t => t * t * (3 - 2 * t);
export const Ease = {
  lin: t => t,
  in: t => t * t * t,
  out: t => 1 - Math.pow(1 - t, 3),
  inOut: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  outQ: t => 1 - Math.pow(1 - t, 4),
  inQ: t => t * t * t * t,
  inOutQ: t => (t < 0.5 ? 8 * t ** 4 : 1 - Math.pow(-2 * t + 2, 4) / 2),
  outExpo: t => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  inExpo: t => (t <= 0 ? 0 : Math.pow(2, 10 * t - 10)),
  inOutExpo: t => (t <= 0 ? 0 : t >= 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2),
  sine: t => -(Math.cos(Math.PI * t) - 1) / 2,
  outBack: t => { const c1 = 1.5, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
};
// keyframes [[t, value, ease?], ...] — ease applies to the segment ending at that key; values may be arrays
export function kf(t, keys) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    const k1 = keys[i];
    if (t <= k1[0]) {
      const k0 = keys[i - 1];
      const p = (k1[2] || Ease.inOut)(inv(t, k0[0], k1[0]));
      const v0 = k0[1], v1 = k1[1];
      return Array.isArray(v0) ? v0.map((a, j) => lerp(a, v1[j], p)) : lerp(v0, v1, p);
    }
  }
  return keys[keys.length - 1][1];
}
export function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

// ---------------------------------------------------------------- DOM helpers (all cache their last value, so per-frame calls are cheap)
export function h(tag, cls, parent, css, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (css) Object.assign(e.style, css);
  if (html !== undefined) e.innerHTML = html;
  if (parent) parent.appendChild(e);
  return e;
}
export function show(el, o) {
  const v = o > 0.002;
  if (el._o !== o) { el.style.opacity = o >= 0.999 ? '' : o.toFixed(3); el._o = o; }
  if (el._v !== v) { el.style.visibility = v ? 'visible' : 'hidden'; el._v = v; }
  return v;
}
export function tf(el, s) { if (el._tf !== s) { el.style.transform = s; el._tf = s; } }
export function txt(el, s) { if (el._tx !== s) { el.textContent = s; el._tx = s; } }
export const SVGNS = 'http://www.w3.org/2000/svg';
export function s(tag, attrs, parent) {
  const e = document.createElementNS(SVGNS, tag);
  if (attrs) for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
export function attr(el, k, v) { const key = '_a' + k; if (el[key] !== v) { el.setAttribute(k, v); el[key] = v; } }
export const fmtN = n => Math.round(n).toLocaleString('en-US');
