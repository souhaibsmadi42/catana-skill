// Run a page in headless Chrome and save window.RESULT.  node tools/page.mjs "src/index.html?dump=1" build/events.json [shot.png]
import fs from 'node:fs'; import path from 'node:path'; import puppeteer from 'puppeteer-core';
import { fileURLToPath } from 'node:url';
import { requireChrome } from './chrome.mjs';
import { readFilm, serve } from './film.mjs';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
if (!process.argv[2]) { console.log('usage: node tools/page.mjs "src/index.html?dump=1" build/events.json [screenshot.png]'); process.exit(2); }
const FILM = readFilm(ROOT);
const srv = await serve(ROOT);
const b = await puppeteer.launch({ executablePath: requireChrome(), headless: true, args: ['--ignore-gpu-blocklist', '--enable-gpu-rasterization'], protocolTimeout: 900000 });
const pg = await b.newPage(); await pg.setViewport({ width: FILM.W, height: FILM.H });
pg.on('pageerror', e => console.log('ERR', e.message)); pg.on('console', m => { if (m.type() === 'error') console.log('[page]', m.text()); });
await pg.goto(`http://127.0.0.1:${srv.address().port}/${process.argv[2]}`, { timeout: 300000 });
await pg.waitForFunction(() => window.RESULT !== undefined, { timeout: 900000, polling: 500 });
const res = await pg.evaluate(() => JSON.stringify(window.RESULT));
if (process.argv[3]) {
  const out = path.join(ROOT, process.argv[3]);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, res); console.log('wrote', process.argv[3], res.length);
} else console.log(res);
if (process.argv[4]) { await pg.screenshot({ path: path.join(ROOT, process.argv[4]) }); console.log('shot', process.argv[4]); }
await b.close(); srv.close();
