// DEMO EDIT (12 s @ 120 BPM = 24 beats). Replace with the real shot plan; keep the patterns:
//   * every cue in beats via B(k)        * one shot = one container, built in init, animated in update(t, lt)
//   * post FX + audio events pushed at init (hit/slash/whip... + ev())   * gradeAt(t) for per-section grade
//   * layout through W/H, vx/vy (fraction of frame), px (scaled px) and fit() so any FILM format works
import { W, H, PORTRAIT, px, vx, vy, h, s, show, tf, Ease, clamp, lerp } from './lib.js';
import { B, BEAT, shot, runShots, drift, T, fit, slam, maskLine, rise, track, echo, counter, typed, drawOn, initSlash, addSlashLine, drawSlash, SLASHES, initHud, hud } from './kit.js';
import { hit, flash, whip, slash, glitch, invert, punch, rumble } from './post.js';

const BRAND = 'BRAND';                      // the real wordmark text
const ER = [];                              // audio cue list -> build/events.json -> audio/mix.py
const ev = (t, kind, k = 1) => ER.push({ t: +t.toFixed(4), kind, k });
const full = { left: '0', width: W + 'px', textAlign: 'center' };   // a centred full-width line
const STACK = W / H < 1.3;                  // 1:1, 4:5, 9:16 -> stack side-by-side layouts vertically

export function gradeAt(t) {                // base values for the finishing pass (grain, vignette, contrast, sat, bx...)
  return {};
}

export async function initScenes() {
  initSlash(document.getElementById('ov'));
  initHud(document.getElementById('hud'), { title: `${BRAND} <span style="color:var(--hot)">▸</span> THE FILM`, right: 'V1 · 2026' });

  // ---- cold open: hairline + staccato words (beats 0–7)
  {
    const S = shot(0, B(8));
    S.line = h('div', null, S.root, { position: 'absolute', left: vx(0.5), top: vy(0.5), height: '1px', width: '0', background: 'var(--ink)' });
    S.w = ['ONE', 'PRODUCT.', 'ZERO', 'FRICTION.'].map(w => T(S.root, w, { ...full, top: vy(0.5), fontSize: fit(w, 420), color: 'var(--ink)' }));
    S.w.forEach(e => (e.style.transform = 'translateY(-50%)'));
    S.lab = T(S.root, '', { ...full, top: vy(0.72) }, 'kmono');
    S.update = (t, lt) => {
      const w = (0.02 + 0.31 * Ease.outQ(clamp(lt / 1.9))) * W;
      S.line.style.left = (W - w) / 2 + 'px'; S.line.style.width = w + 'px';
      show(S.line, t < B(2) ? 1 : 0);
      [2, 3, 5, 6].forEach((k, i) => slam(S.w[i], t, B(k), B(k + 1), { s0: 1.25, d: 0.18, base: 'translateY(-50%)' }));
      typed(S.lab, t, B(1), 'LOADING THE STORY…', 0.06);
    };
    [2, 3, 5, 6].forEach(k => { hit(B(k), 0.7); ev(B(k), 'hitS', 0.7); });
    for (let i = 0; i < 4; i++) invert(B(7) + i * (BEAT / 4), 2 / 60);
    rumble(B(7), BEAT, 1.2); ev(B(7), 'riser', 1);
    addSlashLine(B(8));
  }
  // ---- slash -> logo lockup (beats 8–11): mark beside the wordmark (wide frames) or above it (STACK)
  {
    const S = shot(B(8), B(12), { svg: 'ov' });
    const m = 200 * Math.min(1, W / 1080);
    const mx = STACK ? (W - m) / 2 : W * 0.27, my = STACK ? H * 0.3 : (H - m) / 2;
    const mark = s('rect', { x: mx, y: my, width: m, height: m, rx: m / 5, fill: 'none', stroke: 'url(#slg)', 'stroke-width': m * 0.09, pathLength: 1, 'stroke-dasharray': '1 1' }, S.svg);
    const wcss = STACK ? { ...full, top: px(0) } : { left: (mx + m + 50) + 'px', top: '0' };
    S.word = T(S.root, `<span class="kgrad">${BRAND}</span>`, { ...wcss, top: STACK ? (my + m + 60) + 'px' : (H / 2 - 110 * Math.min(1, W / 1920)) + 'px', fontSize: Math.round(200 * Math.min(1, W / 1300)) + 'px', fontFamily: 'Inter', fontWeight: 800, letterSpacing: '-0.03em', lineHeight: '1.1' }, 'k');
    S.sub = T(S.root, 'THE TAGLINE GOES HERE', STACK ? { ...full, top: (my + m + 320) + 'px', fontSize: px(22), color: 'var(--ink)', letterSpacing: '.3em' }
      : { left: (mx + m + 60) + 'px', top: (H / 2 + 140) + 'px', fontSize: px(22), color: 'var(--ink)', letterSpacing: '.3em' }, 'kmono');
    S.update = (t, lt) => {
      drift(S.root, lt, 1, 1.04, 0, 0, 2);
      drawOn(mark, Ease.outQ(clamp(lt / 0.35)));
      track(S.word, t, B(8), B(12), 0.55, 0.42);
      slam(S.sub, t, B(10), B(12), { s0: 1.06, dy: 10 });
    };
    slash(B(8), -0.42, 1.3); flash(B(8), 2, 1); hit(B(8), 1.2); ev(B(8), 'slash', 1.2);
    punch(B(10), 0.04); ev(B(10), 'hitS', 0.6);
  }
  // ---- proof number (beats 12–15)
  {
    const S = shot(B(12), B(16));
    const nfs = parseInt(fit('12,480', 480)), cy = H * 0.45;          // label sits under the number at any format
    S.n = T(S.root, '0', { ...full, top: cy + 'px', fontSize: nfs + 'px', color: 'var(--ink)' });
    S.l = T(S.root, 'THINGS COUNTED AUTOMATICALLY', { ...full, top: (cy + nfs * 0.5 + 60) + 'px', color: 'var(--ink)', fontSize: px(20) }, 'kmono');
    S.update = (t) => {
      counter(S.n, t, B(12), B(12) + 0.6, 0, 12480);
      const kick = 1 + 0.04 * (1 - clamp(((t - B(12)) % 0.5) / 0.3));
      slam(S.n, t, B(12), B(16), { s0: 1.2, base: `translateY(-50%) scale(${kick.toFixed(3)})` });
      slam(S.l, t, B(13), B(16), { s0: 1.05 });
    };
    hit(B(12), 1); ev(B(12), 'impact', 1); for (let k = 13; k < 16; k++) { punch(B(k), 0.02); ev(B(k), 'tick', 0.5); }
    whip(B(16) - 0.16, 0.32, PORTRAIT ? Math.PI / 2 : 0, 1); ev(B(16) - 0.16, 'whoosh', 1);
  }
  // ---- feature stack + UI card (beats 16–19): words left / card right, or words top / card bottom (STACK)
  {
    const S = shot(B(16), B(20), { ui: true });
    const fs = Math.min(parseInt(fit('CLEAR.', 250, STACK ? 0.8 : 0.45)), Math.round(H * 0.2)) + 'px';
    const x0 = STACK ? vx(0.1) : vx(0.057), lh = parseInt(fs), y0 = STACK ? H * 0.12 : H * 0.16;
    const cw = Math.min(640, W * 0.82);
    S.card = h('div', 'ui', S.ui, { left: STACK ? ((W - cw) / 2) + 'px' : vx(0.56), top: STACK ? (y0 + 3 * lh + 40) + 'px' : vy(0.28), width: cw + 'px', padding: '28px', background: '#14141F', border: '1px solid #2A2A3E', borderRadius: '14px' },
      `<div class="kmono" style="position:static">FEATURE</div><div style="font-size:34px;font-weight:700;margin-top:10px">Real UI goes here</div>
       <div style="margin-top:22px;height:8px;border-radius:4px;background:#26263A"><div data-bar style="height:8px;width:0;border-radius:4px;background:linear-gradient(90deg,var(--hot),var(--hot2))"></div></div>`);
    S.bar = S.card.querySelector('[data-bar]');
    S.m = ['FAST.', 'CLEAR.', '<span class="kgrad">YOURS.</span>'].map((w, i) => maskLine(S.root, w, { left: x0, top: (y0 + i * lh) + 'px', fontSize: fs, color: 'var(--ink)' }));
    S.e = T(S.root, 'YOURS.', { left: x0, top: (y0 + 2 * lh) + 'px', fontSize: fs }, 'k anton outline hot');
    S.update = (t, lt) => {
      tf(S.ui, `scale(${lerp(1, 1.06, lt / 2).toFixed(4)})`);
      S.bar.style.width = (100 * Ease.inOut(clamp(lt / 1.8))) + '%';
      S.m.forEach((m, i) => rise(m, t, B(16 + i), B(20)));
      echo(S.e, t, B(18));
    };
    for (let k = 16; k < 19; k++) { hit(B(k), 0.6); ev(B(k), 'hitS', 0.6); }
    glitch(B(19.5), 0.2, 0.8); ev(B(19.5), 'glitch', 0.8);
  }
  // ---- outro (beats 20–23)
  {
    const S = shot(B(20), 99);
    S.w = T(S.root, `<span class="kgrad">${BRAND}</span>`, { ...full, top: (H / 2 - 120 * Math.min(1, W / 1300)) + 'px', fontSize: Math.round(220 * Math.min(1, W / 1300)) + 'px', fontFamily: 'Inter', fontWeight: 800, letterSpacing: '-0.03em', lineHeight: '1.1' }, 'k');
    S.blk = h('div', null, S.root, { position: 'absolute', inset: '0', background: '#000', opacity: '0' });
    S.update = (t, lt) => {
      drift(S.root, lt, 1, 1.03, 0, 0, 2);
      track(S.w, t, B(20), 99, 0.5, 0.5);
      S.blk.style.opacity = Ease.inOut(clamp((t - (B(24) - 0.9)) / 0.85)).toFixed(3);
    };
    hit(B(20), 0.8); flash(B(20), 2, 0.7); ev(B(20), 'impact', 0.9); ev(B(20), 'outro', 1);
  }
}

export function updateScenes(t) {
  runShots(t);
  drawSlash(t);
  hud(t, t >= 0.2 && !(t >= B(8) && t < B(12)) && t < B(20) ? 1 : 0, t < B(8) ? '00 — OPEN' : t < B(16) ? '01 — PROOF' : '02 — FEATURES');
}
export function sceneEvents() { return { events: ER.slice().sort((a, b) => a.t - b.t), slashes: SLASHES.map(s => s.t) }; }
