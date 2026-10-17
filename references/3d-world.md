# Adding a 3D subject (three.js world)

A 3D model makes drops hit harder: hard camera cuts between angles, explode, isolate categories, x-ray, section cuts.
Build it as one module (`src/world.js`) that loads the GLB with three.js `GLTFLoader`, splits it into parts
`{ geom, center, size, category, id, name }` (classify by mesh / material / node names), merges faces into a few large
buffers with a per-vertex element index, and drives looks from a small set of uniforms (explode, per-category visibility,
highlight flag, clip height, colours). A per-element data texture (centre, category, random, flags) lets one shader do
explode / isolate / highlight / colour-by-category for thousands of elements.

## Wiring
1. Import it from scenes.js (`import './world.js'`) — it sets `window.WORLD` (WD); main.js then calls
   `WD.reset()` each frame, `WD.modelOn = false` until a shot asks for the model, and `WD.render()` when it did.
2. The canvas goes in `#gl` (bottom layer), so DOM type and UI sit on top; post effects apply to everything.
3. In a shot's update: set the camera and the look, every frame (reset clears them):
```js
function uni(o) { const U = WD.U; for (const k in o) { const v = o[k], u = U[k]; if (!u) continue;
  if (u.value && u.value.isColor) u.value.set(v);
  else if (u.value && u.value.isVector3) u.value.set(v[0], v[1], v[2]);      // never assign arrays over a Vector3
  else if (Array.isArray(u.value) && Array.isArray(v)) v.forEach((x, i) => (u.value[i] = x));
  else u.value = v; } }
function cam(o) { WD.modelOn = true; WD.cam = Object.assign({ target: CTR, az: 45, el: 30, size: 12, shiftX: 0, shiftY: 0, fov: 0, roll: 0 }, o); }
```
`fov: 0` = orthographic (isometric graphic look), `fov: 35–70` = perspective (dives, worm's-eye). `size` = half frame
height at the target in metres. `shiftX/Y` move the subject on screen to leave room for type.

## Looks that work with Katana type
- **solid**: dark fill `#0C0F1D` + white edges 0.85 — default, reads at any cut speed.
- **xray**: fills off, lines additive 0.4–0.6 — openings, "complexity", silence/outro ghosts at 0.04–0.1.
- **white/paper**: light fill, black lines, light background — inverted strobe frames, "elevation" angle.
- **category colours**: fill + lines by category (brand-gradient steps) — the drop / "explode into parts".
- **isolate one category**: build mode with one-hot visibility, others as faint ghost lines — one per 2 beats on a drop.
- **highlight one element** (hero flag) others ghosted — drill-downs, big numbers.
- **clip plane** descending with a coloured poché on cut faces — breakdown move.

## Camera grammar
Hard cuts between very different angles on beats (top 89°, elevation 0.5°, worm's-eye −8° with wide fov, iso 35.26°).
Within a shot: slow push (size × 0.92 over 2 beats) + small orbit (8–15° per shot). Accelerating orbit for builds
(az = a + b·lt + c·lt^2.6) with speed blur from `gradeAt().bx`. Explode with outExpo on the drop downbeat.

## Performance
Large models: merge faces into chunks (~3M vertices), compute edges once at load (EdgesGeometry, threshold ~28°),
skip edges for tiny/high-poly parts. Warm-up in `renderReady` compiles shaders. Expect ~3 fps per render worker.
