// Locate a Chrome/Chromium/Edge binary (override with CHROME=/path).
import fs from 'node:fs';
import path from 'node:path';

function playwrightChromium() {
  // pre-installed Playwright browsers (e.g. /opt/pw-browsers/chromium-1234/chrome-linux/chrome)
  const roots = [process.env.PLAYWRIGHT_BROWSERS_PATH, '/opt/pw-browsers'].filter(Boolean);
  for (const r of roots) {
    if (!fs.existsSync(r)) continue;
    for (const d of fs.readdirSync(r).filter(n => /^chromium-\d+$/.test(n)).sort().reverse()) {
      for (const sub of ['chrome-linux/chrome', 'chrome-linux64/chrome']) {
        const p = path.join(r, d, sub);
        if (fs.existsSync(p)) return p;
      }
    }
  }
  return null;
}

export const CHROME = process.env.CHROME || [
  'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  (process.env.LOCALAPPDATA || '') + '/Google/Chrome/Application/chrome.exe', 'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
].find(p => p && fs.existsSync(p)) || playwrightChromium();

export function requireChrome() {
  if (!CHROME) {
    console.error('Chrome not found: install Chrome/Chromium/Edge or set CHROME=/path/to/chrome');
    process.exit(1);
  }
  return CHROME;
}
