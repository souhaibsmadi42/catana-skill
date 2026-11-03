// Shared helpers for the Node tools: read FILM (format + music grid) from src/lib.js without a browser,
// and serve the project root over HTTP for headless Chrome. Every tool sizes its viewport from FILM, so
// 16:9, 9:16, 1:1 and 4:5 films all render at their real size.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

export function readFilm(root, page = process.env.PAGE || 'src') {
  const file = path.join(root, page, 'lib.js');
  const film = { W: 1920, H: 1080, FPS: 60, DURATION: 12, BPM: 120, OFFSET: 0 };
  if (!fs.existsSync(file)) return film;
  const src = fs.readFileSync(file, 'utf8');
  for (const k of Object.keys(film)) {
    const m = src.match(new RegExp('(^|[^A-Za-z_])' + k + ':[ ]*([0-9.]+)'));
    if (m) film[k] = parseFloat(m[2]);
  }
  return film;
}

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2', '.woff': 'font/woff',
  '.ttf': 'font/ttf', '.json': 'application/json', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.mp4': 'video/mp4',
};

// static file server rooted at `root`; resolves to a listening http.Server on a free port
export function serve(root) {
  return new Promise(res => {
    const srv = http.createServer((req, rsp) => {
      const p = path.join(root, decodeURIComponent(new URL(req.url, 'http://x').pathname));
      if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { rsp.writeHead(404); rsp.end(); return; }
      rsp.writeHead(200, { 'Content-Type': TYPES[path.extname(p).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'max-age=3600' });
      fs.createReadStream(p).pipe(rsp);
    });
    srv.listen(0, '127.0.0.1', () => res(srv));
  });
}
