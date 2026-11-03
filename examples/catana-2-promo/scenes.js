// CATANA 2.0 — 15 s sample film (120 BPM grid, SFX only). Real numbers from the repo: 27 camera moves, 17 commands,
// 11 domain presets, 48 tests; the storyboard rows are the actual `catana.py plan compile` output for the villa brief.
// Format-independent: the same file renders 16:9, 9:16, 1:1 and 4:5 (W/H, vx/vy, px, fit, STACK).
import { W, H, PORTRAIT, px, vx, vy, h, s, show, tf, txt, Ease, clamp, lerp } from './lib.js';
import { B, BEAT, shot, runShots, drift, T, fit, slam, maskLine, rise, track, echo, counter, typed, drawOn, initSlash, addSlashLine, drawSlash, SLASHES, initHud, hud } from './kit.js';
import { hit, flash, whip, slash, glitch, invert, punch, rumble, caRamp } from './post.js';

const ER = [];
const ev = (t, kind, k = 1) => ER.push({ t: +t.toFixed(4), kind, k });
const full = { left: '0', width: W + 'px', textAlign: 'center' };
const STACK = W / H < 1.3;
const mono = (n) => ({ fontSize: px(n), color: 'var(--ink)', letterSpacing: '.22em' });

export function gradeAt(t) {
  if (t < B(4)) return { grain: 0.07, vig: 0.42 };
  return {};
}

export async function initScenes() {
  initSlash(document.getElementById('ov'));
  initHud(document.getElementById('hud'), { title: `CATANA <span style="color:var(--hot)">▸</span> 2.0`, right: 'AI CREATIVE DIRECTOR' });

  // ---- 1. cold open (beats 0–3): the brief is typed, then one word lands
  {
    const S = shot(0, B(4));
    S.line = h('div', null, S.root, { position: 'absolute', left: vx(0.5), top: vy(0.62), height: '1px', width: '0', background: 'var(--hot)' });
    S.lab = T(S.root, '', { ...full, top: vy(0.66), ...mono(STACK ? 18 : 20) }, 'kmono');
    S.w = T(S.root, 'ONE IDEA.', { ...full, top: vy(0.42), fontSize: fit('ONE IDEA.', 360), color: 'var(--ink)' });
    S.update = (t, lt) => {
      const w = (0.04 + 0.5 * Ease.outQ(clamp(lt / 1.6))) * W;
      S.line.style.left = (W - w) / 2 + 'px'; S.line.style.width = w + 'px';
      typed(S.lab, t, 0.15, STACK ? 'BRIEF: VILLA FILM, ABU DHABI' : 'BRIEF: LUXURY VILLA COMMERCIAL, ABU DHABI', 0.03);
      slam(S.w, t, B(2), B(4), { s0: 1.3, d: 0.18, base: 'translateY(-50%)' });
    };
    for (let i = 0; i < 28; i += 3) ev(0.15 + i * 0.03, 'type', 0.5);
    hit(B(2), 0.9); ev(B(2), 'hitS', 0.9);
    for (let i = 0; i < 4; i++) invert(B(3.5) + i * (BEAT / 8), 1 / 30);
    rumble(B(3), BEAT, 1); ev(B(3), 'riser', 0.8);
    addSlashLine(B(4), -0.42);
  }
  // ---- 2. slash -> wordmark (beats 4–7)
  {
    const S = shot(B(4), B(8));
    const size = Math.round(Math.min(300 * Math.min(1, W / 1500), W * 0.17));
    S.word = T(S.root, `<span class="kgrad">CATANA</span>`, { ...full, top: (H / 2 - size * 0.62) + 'px', fontSize: size + 'px', fontFamily: 'Inter', fontWeight: 800, letterSpacing: '-0.03em', lineHeight: '1.1' }, 'k');
    S.sub = T(S.root, 'AI CREATIVE DIRECTOR', { ...full, top: (H / 2 + size * 0.62) + 'px', ...mono(STACK ? 22 : 26), letterSpacing: '.4em' }, 'kmono');
    S.update = (t, lt) => {
      drift(S.root, lt, 1, 1.05, 0, 0, 2);
      track(S.word, t, B(4), B(8), 0.6, 0.45);
      slam(S.sub, t, B(5), B(8), { s0: 1.06, dy: 12 });
    };
    slash(B(4), -0.42, 1.3); flash(B(4), 2, 1); hit(B(4), 1.2); ev(B(4), 'slash', 1.2);
    punch(B(5), 0.03); ev(B(5), 'hitS', 0.5);
    whip(B(8) - 0.14, 0.28, PORTRAIT ? Math.PI / 2 : 0, 1); ev(B(8) - 0.14, 'whoosh', 1);
  }
  // ---- 3. what it directs, one word per beat (beats 8–11)
  {
    const S = shot(B(8), B(12));
    const words = ['CONCEPT.', 'STORYBOARD.', 'CAMERA.', 'PROMPTS.'];
    const fs = fit('STORYBOARD.', 330);
    S.w = words.map(w => T(S.root, w, { ...full, top: vy(0.5), fontSize: fs, color: 'var(--ink)' }));
    S.e = words.map(w => T(S.root, w, { ...full, top: vy(0.5), fontSize: fs }, 'k anton outline hot'));
    S.update = (t) => S.w.forEach((e, i) => {
      slam(e, t, B(8 + i), B(9 + i), { s0: 1.22, d: 0.16, base: 'translateY(-50%)' });
      if (t >= B(8 + i) && t < B(9 + i)) { show(S.e[i], 0.7 * (1 - (t - B(8 + i)) / 0.22)); tf(S.e[i], `translateY(-50%) scale(${(1 + 0.25 * clamp((t - B(8 + i)) / 0.22)).toFixed(3)})`); }
      else show(S.e[i], 0);
    });
    for (let i = 0; i < 4; i++) { hit(B(8 + i), 0.6 + 0.1 * i); ev(B(8 + i), 'hitS', 0.7); }
    invert(B(11), 2 / 30);
    glitch(B(11.5), 0.2, 0.8); ev(B(11.5), 'glitch', 0.8);
  }
  // ---- 4. the real storyboard (beats 12–15): `catana.py plan compile` output for the villa brief
  {
    const S = shot(B(12), B(16), { ui: true });
    const rows = [['S01', 'establish', 'aerial_reveal'], ['S02', 'approach', 'dolly_in'], ['S03', 'threshold', 'steadicam'], ['S04', 'flow', 'parallax'],
                  ['S05', 'detail', 'push_in'], ['S06', 'life', 'tracking'], ['S07', 'hero', 'crane_up'], ['S08', 'end_card', 'static']];
    const cw = STACK ? W * 0.86 : W * 0.5, fz = STACK ? Math.round(Math.min(W * 0.03, H * 0.026)) : 24;
    const tfs = Math.min(parseInt(fit('EVERY SHOT', 170)), Math.round(H * 0.11)), cardTop = STACK ? H * 0.08 + 1.8 * tfs + 40 : H * 0.16;
    S.card = h('div', 'ui', S.ui, { left: STACK ? ((W - cw) / 2) + 'px' : vx(0.44), top: cardTop + 'px', width: cw + 'px', padding: '30px 34px', background: '#11111B', border: '1px solid #2A2A3E', borderRadius: '18px', fontFamily: 'Mono', fontSize: fz + 'px', color: '#C9CCDA' },
      `<div style="color:#8A90A8;letter-spacing:.18em;font-size:${Math.round(fz * 0.7)}px;margin-bottom:16px">STORYBOARD · 8 SHOTS · 40 S · 16:9</div>` +
      rows.map((r, i) => `<div data-r="${i}" style="display:flex;justify-content:space-between;padding:${Math.round(fz * 0.38)}px 0;border-top:1px solid #23233A;opacity:0">
        <span style="color:#F4F5FA">${r[0]}</span><span style="flex:1;margin-left:${fz}px">${r[1]}</span><span style="color:#00C6FF">${r[2]}</span><span style="margin-left:${fz}px;color:#4ADE80">A</span></div>`).join(''));
    S.rows = [...S.card.querySelectorAll('[data-r]')];
    S.title = maskLine(S.root, 'EVERY SHOT<br>PLANNED.', STACK ? { ...full, top: vy(0.08), fontSize: tfs + 'px', color: 'var(--ink)', lineHeight: '.9' }
      : { left: vx(0.06), top: vy(0.3), fontSize: fit('EVERY SHOT', 190, 0.36), color: 'var(--ink)', lineHeight: '.9' });
    S.update = (t, lt) => {
      tf(S.ui, `scale(${lerp(1, 1.05, lt / 2).toFixed(4)})`);
      S.rows.forEach((r, i) => { const a = clamp((t - (B(12) + i * BEAT / 2)) / 0.12); if (r._a !== a) { r.style.opacity = a.toFixed(2); r._a = a; } });
      rise(S.title, t, B(12), B(16));
    };
    hit(B(12), 0.8); ev(B(12), 'impact', 0.8);
    for (let i = 0; i < 8; i++) ev(B(12) + i * BEAT / 2, 'blip', 0.5);
    whip(B(16) - 0.14, 0.28, PORTRAIT ? Math.PI / 2 : 0, 1); ev(B(16) - 0.14, 'whoosh', 1);
  }
  // ---- 5. proof numbers (beats 16–21)
  {
    const S = shot(B(16), B(22));
    const nums = [[27, 'CAMERA MOVES'], [17, 'COMMANDS'], [11, 'DOMAIN PRESETS']];
    const nfs = parseInt(fit('27', 560, 0.5));
    S.n = T(S.root, '0', { ...full, top: vy(0.46), fontSize: nfs + 'px', color: 'var(--ink)' });
    S.l = T(S.root, '', { ...full, top: (H * 0.46 + nfs * 0.52 + 30) + 'px', ...mono(STACK ? 24 : 26), letterSpacing: '.35em' }, 'kmono');
    S.update = (t) => {
      const i = clamp(Math.floor((t - B(16)) / (2 * BEAT)), 0, 2), a = B(16 + 2 * i);
      counter(S.n, t, a, a + 0.45, 0, nums[i][0], Ease.outQ, v => String(Math.round(v)));
      slam(S.n, t, a, a + 2 * BEAT, { s0: 1.25, base: 'translateY(-50%)' });
      txt(S.l, nums[i][1]);
      slam(S.l, t, a + BEAT / 2, a + 2 * BEAT, { s0: 1.05 });
      S.n.style.color = i === 1 ? 'var(--hot)' : 'var(--ink)';
    };
    for (let i = 0; i < 3; i++) { hit(B(16 + 2 * i), 1); ev(B(16 + 2 * i), 'impact', 0.8); punch(B(17 + 2 * i), 0.03); ev(B(17 + 2 * i), 'tick', 0.5); }
  }
  // ---- 6. QC: weak prompt -> A 100 (beats 22–25)
  {
    const S = shot(B(22), B(26), { ui: true });
    const cw = STACK ? W * 0.86 : W * 0.62, fz = STACK ? Math.round(W * 0.032) : 28;
    S.card = h('div', 'ui', S.ui, { left: ((W - cw) / 2) + 'px', top: STACK ? vy(0.22) : vy(0.2), width: cw + 'px', padding: '34px 38px', background: '#11111B', border: '1px solid #2A2A3E', borderRadius: '18px', fontFamily: 'Mono', fontSize: fz + 'px', lineHeight: '1.45', color: '#C9CCDA', whiteSpace: 'normal' },
      `<div style="color:#8A90A8;letter-spacing:.18em;font-size:${Math.round(fz * 0.68)}px">PROMPT</div>
       <div data-weak style="margin-top:12px;color:#F87171">“nice car, amazing, 8k”</div>
       <div data-good style="margin-top:12px;color:#F4F5FA"></div>`);
    S.weak = S.card.querySelector('[data-weak]'); S.good = S.card.querySelector('[data-good]');
    S.grade = T(S.root, 'D · 0', { ...full, top: STACK ? vy(0.72) : vy(0.6), fontSize: fit('QC  A · 100', 200), color: '#F87171' });
    const good = 'Slow aerial drone reveal: a vintage red Porsche 911 on a coastal cliff road, low raking sun on the bodywork, 35mm, f/4…';
    S.update = (t, lt) => {
      const flip = t >= B(24);
      S.weak.style.textDecoration = t >= B(23) ? 'line-through' : 'none';
      S.weak.style.opacity = t >= B(23) ? '0.45' : '1';
      typed(S.good, t, B(23), good, 0.012);
      txt(S.grade, flip ? 'QC  A · 100' : 'QC  D · 0');
      S.grade.style.color = flip ? '#4ADE80' : '#F87171';
      slam(S.grade, t, flip ? B(24) : B(22), flip ? B(26) : B(24), { s0: 1.18 });
    };
    hit(B(22), 0.7); ev(B(22), 'hitS', 0.7); glitch(B(23), 0.15, 0.6); ev(B(23), 'glitch', 0.6);
    for (let i = 0; i < 18; i++) ev(B(23) + i * 0.06, 'type', 0.4);
    hit(B(24), 1.1); flash(B(24), 1, 0.6, [0.29, 0.87, 0.5]); ev(B(24), 'impact', 1);
    addSlashLine(B(26), 0.38); caRamp(B(25), BEAT, 0.8); ev(B(25), 'riser', 0.7);
  }
  // ---- 7. outro lockup (beats 26–30)
  {
    const S = shot(B(26), 99);
    const size = Math.round(Math.min(260 * Math.min(1, W / 1500), W * 0.16));
    S.word = T(S.root, `<span class="kgrad">CATANA</span>`, { ...full, top: (H * 0.44 - size * 0.6) + 'px', fontSize: size + 'px', fontFamily: 'Inter', fontWeight: 800, letterSpacing: '-0.03em', lineHeight: '1.1' }, 'k');
    S.cmd = T(S.root, '/catana:video-director', { ...full, top: (H * 0.44 + size * 0.62) + 'px', fontSize: px(STACK ? 30 : 34), color: 'var(--hot)', letterSpacing: '.06em', textTransform: 'none' }, 'kmono');
    S.foot = T(S.root, 'IMAGES · VIDEO · MOTION FILMS · 48/48 TESTS', { ...full, top: (H * 0.44 + size * 0.62 + 70) + 'px', ...mono(STACK ? 15 : 18), letterSpacing: '.3em' }, 'kmono');
    S.blk = h('div', null, S.root, { position: 'absolute', inset: '0', background: '#000', opacity: '0' });
    S.update = (t, lt) => {
      drift(S.root, lt, 1, 1.03, 0, 0, 3);
      track(S.word, t, B(26), 99, 0.5, 0.5);
      typed(S.cmd, t, B(27), '/catana:video-director', 0.035, true);
      slam(S.foot, t, B(28), 99, { s0: 1.04, fade: 0.3 });
      S.blk.style.opacity = Ease.inOut(clamp((t - (15 - 0.9)) / 0.85)).toFixed(3);
    };
    slash(B(26), 0.38, 1.2); flash(B(26), 2, 0.8); hit(B(26), 1.1); ev(B(26), 'slash', 1.1); ev(B(26), 'outro', 1);
    for (let i = 0; i < 22; i += 3) ev(B(27) + i * 0.035, 'type', 0.4);
  }
}

export function updateScenes(t) {
  runShots(t);
  drawSlash(t);
  const ch = t < B(8) ? '00 — BRIEF' : t < B(16) ? '01 — DIRECTION' : t < B(22) ? '02 — LIBRARY' : '03 — QUALITY';
  hud(t, t >= 0.3 && !(t >= B(4) && t < B(8)) && t < B(26) ? 1 : 0, ch);
}
export function sceneEvents() { return { events: ER.slice().sort((a, b) => a.t - b.t), slashes: SLASHES.map(s => s.t) }; }
