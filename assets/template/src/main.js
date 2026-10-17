// Frame driver. window.setTime(t) renders the clean frame at time t; window.postFX(jpegBase64) runs the finishing
// pass on it (the renderer screenshots twice). A three.js world (world3d.js) is optional: scenes.js imports it.
import { FILM } from './lib.js';
import { initPost, drawPost, fxAt } from './post.js';
import { initScenes, updateScenes, sceneEvents, gradeAt } from './scenes.js';

window.FILM = FILM;
await initScenes();
const WD = window.WORLD;   // set by world3d.js if a scene imported it
const postCanvas = document.getElementById('post');
initPost(postCanvas);
let curT = 0;

window.setTime = function (t) {
  curT = t;
  postCanvas.style.display = 'none';
  if (WD) { WD.reset(); WD.modelOn = false; }
  updateScenes(t);
  if (WD) {
    const gl = document.getElementById('gl');
    if (WD.modelOn) { gl.style.visibility = 'visible'; WD.render(); } else gl.style.visibility = 'hidden';
  }
  window.__t = t;
  return true;
};
window.postFX = async function (b64) {
  const blob = await (await fetch('data:image/jpeg;base64,' + b64)).blob();
  const bmp = await createImageBitmap(blob);
  drawPost(bmp, fxAt(curT, gradeAt(curT)), Math.round(curT * FILM.FPS));
  bmp.close();
  postCanvas.style.display = 'block';
  return true;
};
// debugging: window.__fxAt(t) -> post parameters; window.__dbg(t) -> active shots
window.__fxAt = t => fxAt(t, gradeAt(t));
window.__dbg = async t => { window.setTime(t); const m = await import('./kit.js'); return m.SHOTS.filter(s => t >= s._t0 && t < s._t1).map(s => [s._t0, s._t1]); };

window.renderReady = (async () => {
  await Promise.all([400, 600, 700, 800].map(w => document.fonts.load(`${w} 40px Inter`)));
  await Promise.all(['40px Anton', '500 40px Mono', '700 40px Mono'].map(f => document.fonts.load(f)));
  await document.fonts.ready;
  for (let t = 0; t < FILM.DURATION; t += 1) window.setTime(t);   // warm every shot once (shaders, layout)
  window.setTime(0);
  return 1;
})();

(function preview() {
  const q = new URLSearchParams(location.search);
  if (q.has('dump')) { window.renderReady.then(() => { window.RESULT = sceneEvents(); }); return; }
  if (q.has('render')) return;
  window.renderReady.then(() => {
    const t = parseFloat(q.get('t') || '0');
    if (q.has('play')) {
      const t0 = performance.now() - t * 1000;
      const loop = () => { window.setTime(((performance.now() - t0) / 1000) % FILM.DURATION); requestAnimationFrame(loop); };
      requestAnimationFrame(loop);
    } else window.setTime(t);
  });
})();
