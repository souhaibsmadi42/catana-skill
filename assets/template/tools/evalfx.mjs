// Evaluate an expression in the loaded film page at given times (debugging).
//   node tools/evalfx.mjs 15.3 16                     -> post-FX parameters at those times
//   EXPR="window.__dbg(t)" node tools/evalfx.mjs 26.4  -> active shots
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import puppeteer from 'puppeteer-core';
import { fileURLToPath } from 'node:url';
import { CHROME } from './chrome.mjs';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.woff2': 'font/woff2' };
const srv = http.createServer((q, r) => { const p = path.join(ROOT, decodeURIComponent(new URL(q.url, 'http://x').pathname)); if (!fs.existsSync(p) || fs.statSync(p).isDirectory()) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(r); }).listen(0);
await new Promise(r => srv.on('listening', r));
const b = await puppeteer.launch({ executablePath: CHROME, headless: true, defaultViewport: { width: 1920, height: 1080 }, protocolTimeout: 900000 });
const pg = await b.newPage(); pg.on('pageerror', e => console.log('ERR', e.message));
await pg.goto(`http://127.0.0.1:${srv.address().port}/src/index.html?render=1`);
await pg.waitForFunction(() => window.renderReady !== undefined, { timeout: 600000 }); await pg.evaluate(() => window.renderReady);
const expr = process.env.EXPR || 'window.__fxAt(t)';
for (const t of process.argv.slice(2).map(Number)) console.log(t, JSON.stringify(await pg.evaluate(new Function('t', 'return (' + expr + ')'), t)));
await b.close(); srv.close();
