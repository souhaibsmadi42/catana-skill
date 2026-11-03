// Katana frame renderer. Two screenshots per frame: clean frame -> window.postFX (finishing shader) -> final frame.
// Format (W, H, FPS, DURATION) comes from the page's FILM object (src/lib.js), so any aspect ratio renders at size.
//   node render.mjs stills 1.5 7 12.8                              -> out/stills/t_0001.500.png ...
//   node render.mjs video [--workers 6] [--from s] [--to s] [--crf 15] [--name x.mp4]
//                                                                  -> out/video_noaudio.mp4 (exact frame count)
//   NOPOST=1 node render.mjs stills 3                              -> clean frames without the finishing pass
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';
import ffmpegPath from 'ffmpeg-static';
import { requireChrome } from './tools/chrome.mjs';
import { readFilm, serve as serveRoot } from './tools/film.mjs';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(ROOT, 'out');
const CHROME = requireChrome();
const FILM = readFilm(ROOT);
const FPS = FILM.FPS, DURATION = FILM.DURATION, WIDTH = FILM.W, HEIGHT = FILM.H;
const PAGE = process.env.PAGE || 'src';
const HTML = process.env.HTML || 'index.html';
const serve = () => serveRoot(ROOT);

async function openPage(port) {
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: true,
    args: ['--hide-scrollbars', '--mute-audio', '--force-color-profile=srgb', '--disable-background-timer-throttling',
      '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows', '--enable-gpu-rasterization', '--ignore-gpu-blocklist'],
    defaultViewport: { width: WIDTH, height: HEIGHT, deviceScaleFactor: 1 }, protocolTimeout: 1800000,
  });
  const page = await browser.newPage();
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warn') console.log('[page]', m.text()); });
  page.on('requestfailed', r => console.log('[reqfail]', r.url()));
  page.on('response', r => { if (r.status() >= 400) console.log('[404]', r.url()); });
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.goto(`http://127.0.0.1:${port}/${PAGE}/${HTML}?render=1`, { waitUntil: 'load', timeout: 120000 });
  await page.waitForFunction(() => window.renderReady !== undefined, { timeout: 600000, polling: 250 });
  const n = await page.evaluate(() => window.renderReady);
  return { browser, page, n };
}

async function frame(page, t, type = 'jpeg') {
  const post = await page.evaluate(tt => window.setTime(tt), t);
  if (post && !process.env.NOPOST) {
    const clean = await page.screenshot({ type: 'jpeg', quality: 100, optimizeForSpeed: true });
    await page.evaluate(b64 => window.postFX(b64), clean.toString('base64'));
  }
  return page.screenshot(type === 'png' ? { type: 'png' } : { type: 'jpeg', quality: 95, optimizeForSpeed: true });
}

function args() {
  const a = process.argv.slice(3), o = { list: [] };
  for (let i = 0; i < a.length; i++) {
    if (a[i].startsWith('--')) { o[a[i].slice(2)] = a[i + 1]; i++; } else o.list.push(parseFloat(a[i]));
  }
  return o;
}

async function stills(o) {
  if (!o.list.length || o.list.some(t => !Number.isFinite(t) || t < 0 || t > DURATION)) {
    console.error(`stills: give times in seconds between 0 and ${DURATION}, e.g. node render.mjs stills 1.5 4`); process.exitCode = 2; return;
  }
  const srv = await serve();
  const { browser, page, n } = await openPage(srv.address().port);
  console.log(`loaded (${n} images)`);
  fs.mkdirSync(path.join(OUT, 'stills'), { recursive: true });
  for (const t of o.list) {
    const t0 = Date.now();
    const buf = await frame(page, t, 'png');
    const f = path.join(OUT, 'stills', `t_${t.toFixed(3).padStart(7, '0')}.png`);
    fs.writeFileSync(f, buf);
    console.log(f, `${Date.now() - t0} ms`);
  }
  await browser.close(); srv.close();
}

async function segment(port, f0, f1, file, crf) {
  const { browser, page } = await openPage(port);
  const ff = spawn(ffmpegPath, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-vf', 'scale=in_color_matrix=bt601:in_range=full:out_color_matrix=bt709:out_range=tv,format=yuv420p',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', String(crf), '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-tune', 'film',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-x264-params', 'keyint=120:min-keyint=60', '-r', String(FPS), file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg ' + c)))));
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    const buf = await frame(page, f / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 300 === 0) console.log(`  [${path.basename(file)}] frame ${f} (${((f - f0) / ((Date.now() - t0) / 1000)).toFixed(1)} fps)`);
  }
  ff.stdin.end();
  await done;
  await browser.close();
}

async function video(o) {
  const workers = parseInt(o.workers || '6'), crf = parseInt(o.crf || '15');
  const F0 = Math.round(parseFloat(o.from || '0') * FPS), F1 = Math.round(parseFloat(o.to || String(DURATION)) * FPS);
  const srv = await serve();
  const segDir = path.join(OUT, 'segments');
  fs.rmSync(segDir, { recursive: true, force: true });
  fs.mkdirSync(segDir, { recursive: true });
  const per = Math.ceil((F1 - F0) / workers);
  const jobs = [];
  const T = Date.now();
  for (let w = 0; w < workers; w++) {
    const a = F0 + w * per, b = Math.min(F1, a + per);
    if (a >= b) break;
    const file = path.join(segDir, `seg_${String(w).padStart(2, '0')}.mp4`);
    jobs.push(segment(srv.address().port, a, b, file, crf).then(() => file));
  }
  const files = await Promise.all(jobs);
  srv.close();
  const list = path.join(segDir, 'list.txt');
  fs.writeFileSync(list, files.map(f => `file '${f.replace(/\\/g, '/')}'`).join('\n'));
  const out = path.join(OUT, o.name || 'video_noaudio.mp4');
  await new Promise((res, rej) => spawn(ffmpegPath, ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out], { stdio: 'inherit' })
    .on('close', c => (c === 0 ? res() : rej(new Error('concat ' + c)))));
  console.log(`done ${out} in ${((Date.now() - T) / 60000).toFixed(1)} min`);
}

const mode = process.argv[2];
if (mode === 'stills') await stills(args());
else if (mode === 'video') await video(args());
else { console.log('usage: node render.mjs stills <t...> | video [--workers n] [--from s] [--to s] [--crf n] [--name file.mp4]'); process.exitCode = 2; }
