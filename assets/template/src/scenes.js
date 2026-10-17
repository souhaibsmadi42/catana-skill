// DEMO EDIT (12 s @ 120 BPM = 24 beats). Replace with the real shot plan; keep the patterns:
//   * every cue in beats via B(k)        * one shot = one container, built in init, animated in update(t, lt)
//   * post FX + audio events pushed at init (hit/slash/whip... + ev())   * gradeAt(t) for per-section grade
import { h, s, attr, show, tf, txt, Ease, clamp, lerp, kf, fmtN } from './lib.js';
import { B, shot, runShots, drift, T, slam, maskLine, rise, track, echo, counter, typed, drawOn, initSlash, addSlashLine, drawSlash, SLASHES, initHud, hud } from './kit.js';
import { hit, flash, whip, slash, glitch, invert, punch, rumble, caRamp } from './post.js';

const BRAND = 'BRAND';                      // the real wordmark text
const ER = [];                              // audio cue list -> build/events.json -> audio/mix.py
const ev = (t, kind, k = 1) => ER.push({ t: +t.toFixed(4), kind, k });

export function gradeAt(t) {                // base values for the finishing pass (grain, vignette, contrast, sat, bx...)
  return {};
}

export async function initScenes() {
  initSlash(document.getElementById('ov'));
  initHud(document.getElementById('hud'), { title: `${BRAND} <span style="color:var(--hot)">▸</span> THE FILM`, right: 'V1 · 2026' });

  // ---- cold open: hairline + staccato words (beats 0–7)
  {
    const S = shot(0, B(8));
    S.line = h('div', null, S.root, { position: 'absolute', left: '960px', top: '540px', height: '1px', width: '0', background: 'var(--ink)' });
    S.w = ['ONE', 'PRODUCT.', 'ZERO', 'FRICTION.'].map((w, i) => T(S.root, w, { left: '0', top: '360px', width: '1920px', textAlign: 'center', fontSize: i % 2 ? '330px' : '420px', color: 'var(--ink)' }));
    S.lab = T(S.root, '', { left: '0', top: '760px', width: '1920px', textAlign: 'center' }, 'kmono');
    S.update = (t, lt) => {
      const w = 40 + 600 * Ease.outQ(clamp(lt / 1.9));
      S.line.style.left = (960 - w / 2) + 'px'; S.line.style.width = w + 'px';
      show(S.line, t < B(2) ? 1 : 0);
      [2, 3, 5, 6].forEach((k, i) => slam(S.w[i], t, B(k), B(k + 1), { s0: 1.25, d: 0.18 }));
      typed(S.lab, t, B(1), 'LOADING THE STORY…', 0.06);
    };
    [2, 3, 5, 6].forEach(k => { hit(B(k), 0.7); ev(B(k), 'hitS', 0.7); });
    for (let i = 0; i < 4; i++) invert(B(7) + i * 0.125, 2 / 60);
    rumble(B(7), BEAT_(1), 1.2); ev(B(7), 'riser', 1);
    addSlashLine(B(8));
  }
  // ---- slash -> logo lockup (beats 8–11)
  {
    const S = shot(B(8), B(12), { svg: 'ov' });
    const mark = s('rect', { x: 510, y: 440, width: 200, height: 200, rx: 40, fill: 'none', stroke: 'url(#slg)', 'stroke-width': 18, pathLength: 1, 'stroke-dasharray': '1 1' }, S.svg);
    S.word = T(S.root, `<span class="kgrad">${BRAND}</span>`, { left: '760px', top: '430px', fontSize: '200px', fontFamily: 'Inter', fontWeight: 800, letterSpacing: '-0.03em', lineHeight: '1.1' }, 'k');
    S.sub = T(S.root, 'THE TAGLINE GOES HERE', { left: '770px', top: '680px', fontSize: '22px', color: 'var(--ink)', letterSpacing: '.3em' }, 'kmono');
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
    S.n = T(S.root, '0', { left: '0', top: '250px', width: '1920px', textAlign: 'center', fontSize: '480px', color: 'var(--ink)' });
    S.l = T(S.root, 'THINGS COUNTED AUTOMATICALLY', { left: '0', top: '720px', width: '1920px', textAlign: 'center', color: 'var(--ink)', fontSize: '20px' }, 'kmono');
    S.update = (t, lt) => {
      slam(S.n, t, B(12), B(16), { s0: 1.2 });
      counter(S.n, t, B(12), B(12) + 0.6, 0, 12480);
      tf(S.n, `scale(${(1 + 0.04 * (1 - clamp(((t - B(12)) % 0.5) / 0.3))).toFixed(3)})`);
      slam(S.l, t, B(13), B(16), { s0: 1.05 });
    };
    hit(B(12), 1); ev(B(12), 'impact', 1); for (let k = 13; k < 16; k++) { punch(B(k), 0.02); ev(B(k), 'tick', 0.5); }
    whip(B(16) - 0.16, 0.32, 0, 1); ev(B(16) - 0.16, 'whoosh', 1);
  }
  // ---- feature stack + UI card (beats 16–19)
  {
    const S = shot(B(16), B(20), { ui: true });
    S.card = h('div', 'ui', S.ui, { left: '1080px', top: '300px', width: '640px', padding: '28px', background: '#14141F', border: '1px solid #2A2A3E', borderRadius: '14px' },
      `<div class="kmono" style="position:static">FEATURE</div><div style="font-size:34px;font-weight:700;margin-top:10px">Real UI goes here</div>
       <div style="margin-top:22px;height:8px;border-radius:4px;background:#26263A"><div data-bar style="height:8px;width:0;border-radius:4px;background:linear-gradient(90deg,var(--hot),var(--hot2))"></div></div>`);
    S.bar = S.card.querySelector('[data-bar]');
    S.m = ['FAST.', 'CLEAR.', '<span class="kgrad">YOURS.</span>'].map((w, i) => maskLine(S.root, w, { left: '110px', top: `${170 + i * 250}px`, fontSize: '250px', color: 'var(--ink)' }));
    S.e = T(S.root, 'YOURS.', { left: '110px', top: '670px', fontSize: '250px' }, 'k anton outline hot');
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
    S.w = T(S.root, `<span class="kgrad">${BRAND}</span>`, { left: '0', top: '400px', width: '1920px', textAlign: 'center', fontSize: '220px', fontFamily: 'Inter', fontWeight: 800, letterSpacing: '-0.03em', lineHeight: '1.1' }, 'k');
    S.blk = h('div', null, S.root, { position: 'absolute', inset: '0', background: '#000', opacity: '0' });
    S.update = (t, lt) => {
      drift(S.root, lt, 1, 1.03, 0, 0, 2);
      track(S.w, t, B(20), 99, 0.5, 0.5);
      S.blk.style.opacity = Ease.inOut(clamp((t - (B(24) - 0.9)) / 0.85)).toFixed(3);
    };
    hit(B(20), 0.8); flash(B(20), 2, 0.7); ev(B(20), 'impact', 0.9); ev(B(20), 'outro', 1);
  }
}
function BEAT_(n) { return B(n) - B(0); }

export function updateScenes(t) {
  runShots(t);
  drawSlash(t);
  hud(t, t >= 0.2 && !(t >= B(8) && t < B(12)) && t < B(20) ? 1 : 0, t < B(8) ? '00 — OPEN' : t < B(16) ? '01 — PROOF' : '02 — FEATURES');
}
export function sceneEvents() { return { events: ER.slice().sort((a, b) => a.t - b.t), slashes: SLASHES.map(s => s.t) }; }
