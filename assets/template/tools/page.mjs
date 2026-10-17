// Run a page in headless Chrome and save window.RESULT.  node tools/page.mjs "src/index.html?dump=1" build/events.json
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import puppeteer from 'puppeteer-core';
import { fileURLToPath } from 'node:url';
import { CHROME } from './chrome.mjs';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.woff2': 'font/woff2', '.ttf': 'font/ttf' };
const srv = http.createServer((q, r) => { const p = path.join(ROOT, decodeURIComponent(new URL(q.url, 'http://x').pathname)); if (!fs.existsSync(p) || fs.statSync(p).isDirectory()) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(r); }).listen(0);
const b = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--ignore-gpu-blocklist', '--enable-gpu-rasterization'], protocolTimeout: 900000 });
const pg = await b.newPage(); await pg.setViewport({ width: 1920, height: 1080 }); pg.on('pageerror', e => console.log('ERR', e.message)); pg.on('console', m => console.log('[page]', m.text()));
await pg.goto(`http://127.0.0.1:${srv.address().port}/${process.argv[2]}`, { timeout: 300000 });
await pg.waitForFunction(() => window.RESULT !== undefined, { timeout: 900000, polling: 500 });
const res = await pg.evaluate(() => JSON.stringify(window.RESULT));
if (process.argv[3]) { fs.writeFileSync(path.join(ROOT, process.argv[3]), res); console.log('wrote', process.argv[3], res.length); } else console.log(res);
if (process.argv[4]) { await pg.screenshot({ path: path.join(ROOT, process.argv[4]) }); console.log('shot', process.argv[4]); }
await b.close(); srv.close();
