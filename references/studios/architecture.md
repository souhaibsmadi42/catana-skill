# Architecture Studio — architectural visualization and cinematics

Exterior and interior visualization, architectural films, drone sequences, day-to-night, weather and material
transformations, construction-to-completion, landscape cinematics. Use for `/catana:architecture-film` and any building,
interior, real-estate, hospitality or masterplan request. Preset: **`architecture`** (two-point perspective, eye level
1.6 m, 24mm tilt-shift f/8, corrected verticals, golden-hour raking sun, physically accurate materials, geometry
negatives). For a code-rendered film of a 3D model (GLB/IFC) use the local motion engine: `references/3d-world.md`.

## Inputs

Renders, photos, drawings or a 3D model; what must stay exact (geometry, materials, view); location and orientation
(where the sun can be); time of day; use (marketing film, competition board, social reel); length and ratio.
Ask for references whenever the building is real — without them you are designing, not visualizing.

## Geometry and reference preservation — the rules

1. Every render/photo reference gets a role and a preserve list:
   ```json
   {"source": "render_front.png", "role": "first_frame",
    "preserve": ["building massing and footprint", "number of floors", "window and opening layout", "roof form", "materials", "camera position and composition of the reference"]}
   ```
   (`role: "geometry"` for a reference that is not the start frame.) The linter warns when an architectural
   reference has no geometry preservation.
2. Animate **from** the render (`first_frame`, i2v) rather than generating the building from text.
3. **Low motion intensity**, slow moves, 4–8 s per shot. Fast moves and long clips warp façades.
4. Verticals: tilt-shift / "verticals perfectly corrected"; prefer `pedestal` over `tilt_up` when lines must stay
   parallel; avoid `dutch_angle`, `fpv_drone` close passes and `orbit_360` on complex buildings unless the back is
   designed.
5. People small and secondary; negatives already ban distorted faces.

## Shot types and moves

| Shot | Camera ids | Notes |
|---|---|---|
| Aerial establishing | `aerial_reveal`, `crane_up`, `top_down` | start behind a foreground (dune, trees) for the reveal |
| Approach | `dolly_in`, `steadicam` | toward the entrance at eye level |
| Threshold / interior flow | `steadicam`, `dolly_in`, `parallax` | set an interior `environment` |
| Façade / elevation | `pedestal`, `tracking` (lateral) | level lens, parallel verticals |
| Detail / materials | `push_in`, `rack_focus` | one junction or texture |
| Lifestyle | `tracking`, `parallax` | small human moment |
| Hero | `crane_up`, `dolly_out`, `arc` | whole property |
| Energetic tour (social) | `fpv_drone` | only for simple massing; short clips |

## Transformations

| Transformation | How |
|---|---|
| **Day → night** | Two keyframes from the same camera (day render + night render/edit) → `first_last` generation. In a plan: per-shot `lighting` + `time_of_day: "blue_hour"` and `notes: "transition: day to night"` (the sequence linter accepts marked transitions). |
| Weather (clear → rain/snow/fog) | same camera, `first_last` or a single shot whose `action` describes the change ("rain begins, the terrace darkens and reflections appear"); keep the time of day fixed |
| Construction → completion | keyframes per stage (site, structure, envelope, complete) from one camera; chain `first_last` shots; or a timelapse in one shot (`action`: "time-lapse: the frame rises floor by floor") |
| Material change | `first_last` between two material renders; describe "a sweep of light wipes across the façade, revealing <new material>" (linter warns on transformations without a described transition) |
| Seasons / landscape growth | same camera, foliage and light change; one change per shot |

## Workflow

1. Film: `python <skill>/scripts/catana.py plan new "<project> architectural film" --domain architecture --duration 40 --out plan.json`
   (beats: establish → approach → threshold → flow → detail → life → hero → end_card).
2. Bible: `locations.<id>` with massing, materials, roof, site; `lighting` matched to orientation; palette from the
   real materials. Attach renders per shot (`first_frame` + preserve).
3. Compile, fix, present. Generate keyframes only where no render exists (match the reference camera); animate with i2v.
4. Single still: `catana.py enhance "<exterior|interior> architectural photo of …" --json`, add references, lint.

## Verified prompt patterns (`catana.py enhance`, QC A 100)

```text
architectural video of a modern concrete villa with an infinity pool at golden hour, aerial reveal, 8 seconds
interior architectural photo of a double-height living room with floor-to-ceiling windows overlooking the sea, morning light
architectural video of a glass office tower at blue hour, slow crane up, 6 seconds
```

The first renders to (excerpt): *"Slow aerial drone reveal, gliding up and over the foreground to reveal the location
at scale: a modern concrete villa with an infinity pool, subtle environmental motion: palm fronds swaying, water
rippling in the pool, clouds drifting slowly … Two-point perspective … 24mm tilt-shift lens, f/8, straight
converging-free verticals. Golden hour sunlight, low warm sun raking across surfaces … honed travertine, board-formed
concrete, bronze-tinted glazing with real reflections …"*. Replace the preset materials with the project's real ones.

## Provider routing

| Need | Operation | Options (verify first) |
|---|---|---|
| Animate a render | i2v | Higgsfield `kling4_0`, `seedance_2_0`, `minimax_h3`, `cinematic_studio_video_4_0` |
| Day→night, before→after | first_last | `kling4_0`, `kling_o3_flf`, `seedance_2_0`, `minimax_h3` |
| Several views kept consistent | multi_ref_video | `seedance_2_0`, `kling_o3_image_reference` |
| New camera angles of the same building | i2i / 3D | Higgsfield 3D scene tools (`/3d-jutsu` preset instructions) — paid, verify first |
| Retouch / sky / season on a still | i2i | `flux_kontext`, `nano_banana_pro`, `seedream_v4_5` |
| Upscale for print | upscale_image / upscale_video | `upscale_image`, `topaz_video` |
| Code-rendered film from a GLB/IFC | motion_graphics | CATANA motion engine (free) — `references/3d-world.md` |

## QC checklist

- [ ] Every reference has role + preserve (massing, floors, openings, roof, materials, camera)
- [ ] Verticals corrected; moves slow; motion intensity low; shots 4–8 s
- [ ] Sun direction plausible for the site; one time of day per scene (or marked transition)
- [ ] Interior shots have interior environments
- [ ] Materials named from the real project
- [ ] People secondary; no invented amenities or views the site doesn't have

## Failure modes → fixes

| Symptom | Fix |
|---|---|
| Façade bends / windows multiply | i2v from the render, lower intensity, shorter shot, stronger preserve list |
| Extra floors | "number of floors: N" in preserve and subject |
| Converging verticals | tilt-shift lens text; `pedestal` instead of `tilt_up` |
| Day→night flicker | `first_last` with both frames from the same camera; describe the transition |
| Interior looks like exterior | set `environment` per interior shot |

## Deliverables

Shot list + storyboard · keyframes/renders per shot · i2v clips · transformation clips · VO (free) + music bed
choice · EDL · stills for print (upscaled) · run log / prompt pack.
