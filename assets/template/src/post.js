// Katana finishing pass. The page renders a clean frame, the renderer screenshots it and hands it back here;
// one full-screen shader then applies the camera shake / punch, whip blur, slash split, glitch slices,
// chromatic aberration, flash, invert, grade, vignette and grain — all values are pure functions of t.
import { FILM, clamp, lerp, Ease, rng } from './lib.js';
const WW = FILM.W, HH = FILM.H;

// ------------------------------------------------------------------ event list (filled by scenes.js at init)
// hit(t,k)            shake + chromatic spike + small zoom kick        — every hard accent
// punch(t,k,dur)      zoom kick only                                    — offbeats, counters
// flash(t,frames,k,c) white (or colour) frames                          — drops, impacts
// whip(t,dur,ang,len) film-strip slide with speed blur; cut at t+dur/2  — scene changes
// slash(t,ang,k)      frame splits along a line, gap glows              — section transitions (pair with kit.addSlashLine)
// glitch(t,dur,k)     horizontal slice displacement                     — fills, errors, hand-offs
// invert(t,dur)       negative frames                                   — strobes (2 frames)
// rumble(t,dur,k)     growing shake + zoom creep                        — risers before a drop
// zoomBlur(t,dur,k)   radial blur pulse                                 — spins, reveals
// caRamp(t,dur,k)     chromatic aberration build                        — tension
// tilt(t,dur,ang)     roll kick that settles                            — accents
export const FX = [];
export const hit = (t, k = 1) => FX.push({ type: 'hit', t, k });
export const flash = (t, frames = 2, k = 1, col = [1, 1, 1]) => FX.push({ type: 'flash', t, d: frames / 60, k, col });
export const whip = (t, dur, ang, len = 1, wrap = true) => FX.push({ type: 'whip', t, d: dur, ang, len, wrap });
export const slash = (t, ang = -0.42, k = 1, px = WW / 2, py = HH / 2) => FX.push({ type: 'slash', t, ang, k, px, py });
export const glitch = (t, dur, k = 1) => FX.push({ type: 'glitch', t, d: dur, k });
export const invert = (t, dur) => FX.push({ type: 'invert', t, d: dur });
export const punch = (t, k = 0.06, dur = 0.42) => FX.push({ type: 'punch', t, k, d: dur });
export const rumble = (t, dur, k = 1) => FX.push({ type: 'rumble', t, d: dur, k });
export const zoomBlur = (t, dur, k = 1) => FX.push({ type: 'zblur', t, d: dur, k });
export const caRamp = (t, dur, k = 1) => FX.push({ type: 'ca', t, d: dur, k });
export const tilt = (t, dur, ang) => FX.push({ type: 'tilt', t, d: dur, ang });

// smooth seeded noise for shake
const NZ = (() => { const r = rng(77); const a = new Float32Array(4096); for (let i = 0; i < a.length; i++) a[i] = r() * 2 - 1; return a; })();
const noise = x => { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(NZ[i & 4095], NZ[(i + 1) & 4095], u); };

export function fxAt(t, base = {}) {
  const o = { zoom: 1, rot: 0, sx: 0, sy: 0, ca: 1.2, bx: 0, by: 0, zb: 0, flash: 0, fc: [1, 1, 1], inv: 0, glitch: 0, slOn: 0, slx: WW / 2, sly: HH / 2, sla: 0, slo: 0, slg: 0,
    wx: 0, wy: 0, grain: 0.055, vig: 0.32, contrast: 1, bright: 0, sat: 1, ...base };
  let shake = 0;
  for (const e of FX) {
    const dt = t - e.t;
    if (dt < -0.6 || dt > 2) continue;
    switch (e.type) {
      case 'hit': if (dt >= 0) {
        const d = Math.exp(-dt * 9);
        shake += 26 * e.k * d;
        o.ca += 16 * e.k * Math.exp(-dt * 12);
        o.zoom += 0.035 * e.k * Ease.outExpo(clamp(1 - dt / 0.5));
      } break;
      case 'punch': if (dt >= 0 && dt < e.d) o.zoom += e.k * (1 - Ease.outQ(dt / e.d)); break;
      case 'flash': if (dt >= 0 && dt < e.d + 0.12) {
        const a = dt < e.d ? e.k : e.k * (1 - (dt - e.d) / 0.12) * 0.6;
        if (a > o.flash) { o.flash = a; o.fc = e.col; }
      } break;
      case 'whip': if (dt >= 0 && dt < e.d) {
        // outgoing half slides away, incoming half slides in: one continuous move with a blur that follows its speed
        const p = dt / e.d, s = Ease.inOutExpo(p);
        const L = e.len * (Math.abs(Math.cos(e.ang)) * WW + Math.abs(Math.sin(e.ang)) * HH);
        const off = (s < 0.5 ? s : s - 1) * L;
        o.wx += Math.cos(e.ang) * off; o.wy += Math.sin(e.ang) * off;
        const v = Math.abs(Ease.inOutExpo(Math.min(1, p + 0.02)) - Ease.inOutExpo(Math.max(0, p - 0.02))) / 0.04; // speed
        const bl = Math.min(260, v * L * 0.016);
        o.bx += Math.cos(e.ang) * bl; o.by += Math.sin(e.ang) * bl;
        o.ca += Math.min(14, v * 2);
      } break;
      case 'slash': if (dt >= -0.02 && dt < 0.5) {
        if (dt >= 0) {
          const p = dt / 0.5;
          o.slOn = 1; o.slx = e.px; o.sly = e.py; o.sla = e.ang;
          o.slo = 150 * e.k * Math.pow(1 - p, 2.6) * Ease.outExpo(clamp(dt / 0.035));
          o.slg = 26 * e.k * Math.pow(1 - p, 3);
          shake += 30 * e.k * Math.exp(-dt * 8);
          o.ca += 22 * e.k * Math.exp(-dt * 9);
        }
      } break;
      case 'glitch': if (dt >= 0 && dt < e.d) { const k = e.k * (0.55 + 0.45 * Math.sin(dt * 47)); o.glitch = Math.max(o.glitch, k); o.ca += 10 * k; } break;
      case 'invert': if (dt >= 0 && dt < e.d) o.inv = 1; break;
      case 'rumble': if (dt >= 0 && dt < e.d) { const p = dt / e.d; shake += 9 * e.k * p * p; o.ca += 6 * e.k * p * p; o.zoom += 0.05 * e.k * Ease.in(p); } break;
      case 'zblur': if (dt >= 0 && dt < e.d) { const p = dt / e.d; o.zb += 0.09 * e.k * Math.sin(Math.PI * p); } break;
      case 'ca': if (dt >= 0 && dt < e.d) o.ca += 14 * e.k * Ease.in(dt / e.d); break;
      case 'tilt': if (dt >= 0 && dt < e.d) o.rot += e.ang * (1 - Ease.outQ(dt / e.d)); break;
    }
  }
  if (shake > 0.05) {
    const f = t * 34;
    o.sx += noise(f) * shake; o.sy += noise(f + 911) * shake * 0.8; o.rot += noise(f + 377) * shake * 0.0009;
  }
  return o;
}

// ------------------------------------------------------------------ WebGL pass
let gl, prog, tex, U = {};
const VS = `#version 300 es
in vec2 p; void main(){ gl_Position = vec4(p, 0., 1.); }`;
const FS = `#version 300 es
precision highp float;
uniform sampler2D T; uniform vec2 R;
uniform float zoom, rot, ca, zb, flash, inv, glitch, seed, slOn, sla, slo, slg, grain, vig, contrast, bright, sat;
uniform vec2 sh, bl, sl, wr; uniform vec3 fc;
out vec4 o;
float h1(float n){ return fract(sin(n * 12.9898) * 43758.5453); }
float h2(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
vec3 tap(vec2 p){
  // whip offset wraps (film-strip), everything else is black outside the frame
  p += wr; p = mod(p, R);
  vec2 c = R * 0.5; vec2 d = (p - c) / R.y; vec2 off = d * ca;
  return vec3(texture(T, (p + off) / R).r, texture(T, p / R).g, texture(T, (p - off) / R).b);
}
void main(){
  vec2 p = vec2(gl_FragCoord.x, R.y - gl_FragCoord.y);
  vec2 c = R * 0.5;
  // slash split: the two halves slide apart along the cut, the gap glows
  float gapA = 0.0;
  if (slOn > 0.5) {
    vec2 dir = vec2(cos(sla), sin(sla)); vec2 n = vec2(-dir.y, dir.x);
    float sd = dot(p - sl, n);
    p -= dir * sign(sd) * slo * 0.5;
    gapA = 1.0 - smoothstep(slg * 0.25, slg * 0.5 + 1.5, abs(sd));
  }
  // camera: shake / punch / roll
  vec2 q = p - c - sh; float cr = cos(-rot), sr = sin(-rot);
  q = mat2(cr, sr, -sr, cr) * q / zoom + c;
  // glitch slices
  if (glitch > 0.001) {
    float bh = 6.0 + 60.0 * h1(floor(seed * 7.0));
    float band = floor(q.y / bh);
    float r = h1(band * 3.1 + seed * 17.0);
    if (r < glitch * 0.45) q.x += (h1(band * 7.7 + seed) - 0.5) * 380.0 * glitch;
    if (h1(band + seed * 3.0) < glitch * 0.12) q.y += (h1(band * 1.7) - 0.5) * 40.0;
  }
  vec3 col = vec3(0.0);
  float blen = length(bl);
  int N = (blen > 1.0 || zb > 0.001) ? 24 : 1;
  float wsum = 0.0;
  for (int i = 0; i < 24; i++) {
    if (i >= N) break;
    float f = N == 1 ? 0.0 : float(i) / float(N - 1) - 0.5;
    vec2 s = q + bl * f + (q - c) * zb * f;
    float w = 1.0 - abs(f) * 0.8;
    vec3 v = (s.x < 0.0 || s.y < 0.0 || s.x > R.x || s.y > R.y) && wr == vec2(0.0) ? vec3(0.027, 0.027, 0.047) : tap(s);
    col += v * w; wsum += w;
  }
  col /= wsum;
  // grade
  col = (col - 0.5) * contrast + 0.5 + bright;
  float l = dot(col, vec3(0.2126, 0.7152, 0.0722)); col = mix(vec3(l), col, sat);
  col = mix(col, 1.0 - col, inv);
  // slash gap light
  col = mix(col, vec3(0.92, 0.98, 1.0), gapA);
  col = mix(col, fc, flash);
  // vignette + grain
  vec2 uv = gl_FragCoord.xy / R; vec2 vv = uv - 0.5; vv.x *= R.x / R.y;
  col *= 1.0 - vig * smoothstep(0.35, 1.05, length(vv));
  float g = h2(floor(gl_FragCoord.xy * 0.75) + seed * 61.0) - 0.5;
  col += g * grain * (0.6 + 0.4 * (1.0 - l));
  o = vec4(clamp(col, 0.0, 1.0), 1.0);
}`;

export function initPost(canvas) {
  gl = canvas.getContext('webgl2', { preserveDrawingBuffer: true, antialias: false });
  const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
  prog = gl.createProgram();
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
  gl.useProgram(prog);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  for (const k of ['T', 'R', 'zoom', 'rot', 'ca', 'zb', 'flash', 'inv', 'glitch', 'seed', 'slOn', 'sla', 'slo', 'slg', 'grain', 'vig', 'contrast', 'bright', 'sat', 'sh', 'bl', 'sl', 'wr', 'fc']) U[k] = gl.getUniformLocation(prog, k);
  tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
}

export function drawPost(src, o, frameNo) {
  gl.viewport(0, 0, WW, HH);
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, src);
  gl.uniform1i(U.T, 0); gl.uniform2f(U.R, WW, HH);
  gl.uniform1f(U.zoom, o.zoom); gl.uniform1f(U.rot, o.rot); gl.uniform1f(U.ca, o.ca); gl.uniform1f(U.zb, o.zb);
  gl.uniform1f(U.flash, o.flash); gl.uniform3fv(U.fc, o.fc); gl.uniform1f(U.inv, o.inv); gl.uniform1f(U.glitch, o.glitch);
  gl.uniform1f(U.seed, (frameNo % 997) + 0.5);
  gl.uniform1f(U.slOn, o.slOn); gl.uniform1f(U.sla, o.sla); gl.uniform1f(U.slo, o.slo); gl.uniform1f(U.slg, o.slg); gl.uniform2f(U.sl, o.slx, o.sly);
  gl.uniform1f(U.grain, o.grain); gl.uniform1f(U.vig, o.vig); gl.uniform1f(U.contrast, o.contrast); gl.uniform1f(U.bright, o.bright); gl.uniform1f(U.sat, o.sat);
  gl.uniform2f(U.sh, o.sx, o.sy); gl.uniform2f(U.bl, o.bx, o.by); gl.uniform2f(U.wr, o.wx, o.wy);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
  gl.finish();
}
