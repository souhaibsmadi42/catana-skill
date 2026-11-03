// Evaluate an expression in the loaded film page at given times (debugging).
//   node tools/evalfx.mjs 15.3 16                     -> post-FX parameters at those times
//   EXPR="window.__dbg(t)" node tools/evalfx.mjs 26.4  -> active shots
import path from 'node:path'; import puppeteer from 'puppeteer-core';
import { fileURLToPath } from 'node:url';
import { requireChrome } from './chrome.mjs';
import { readFilm, serve } from './film.mjs';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const times = process.argv.slice(2).map(Number);
if (!times.length || times.some(t => !Number.isFinite(t))) { console.log('usage: node tools/evalfx.mjs <t seconds> [...]'); process.exit(2); }
const FILM = readFilm(ROOT);
const srv = await serve(ROOT);
const b = await puppeteer.launch({ executablePath: requireChrome(), headless: true, defaultViewport: { width: FILM.W, height: FILM.H }, protocolTimeout: 900000 });
const pg = await b.newPage(); pg.on('pageerror', e => console.log('ERR', e.message));
await pg.goto(`http://127.0.0.1:${srv.address().port}/src/index.html?render=1`);
await pg.waitForFunction(() => window.renderReady !== undefined, { timeout: 600000 }); await pg.evaluate(() => window.renderReady);
const expr = process.env.EXPR || 'window.__fxAt(t)';
for (const t of times) console.log(t, JSON.stringify(await pg.evaluate(new Function('t', 'return (' + expr + ')'), t)));
await b.close(); srv.close();
