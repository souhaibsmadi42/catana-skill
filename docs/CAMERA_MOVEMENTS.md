# Camera movement library

> Generated from `data/camera_movements.json` by `python scripts/catana.py docs` — edit the JSON, not this file.

Every move lists its definition, best use, camera and subject behaviour, an example prompt, common mistakes and
recommended combinations. `min` is the shortest clip in which the move reads cleanly. The engine uses the same data
to phrase moves in prompts (`catana.py camera phrase dolly_in`) and to reject conflicting combinations
(`catana.py camera check orbit_360 tracking`).

| Move | Id | Category | Min | Best for |
|---|---|---|---|---|
| [Static (locked-off)](#static) | `static` | baseline | 2 s | dialogue and talking heads |
| [Dolly In](#dolly-in) | `dolly_in` | translation | 3 s | revealing importance |
| [Dolly Out](#dolly-out) | `dolly_out` | translation | 3 s | revealing context or scale |
| [Push In](#push-in) | `push_in` | translation | 3 s | emotional beats |
| [Pull Out](#pull-out) | `pull_out` | translation | 3 s | detail-to-context reveals |
| [Tracking Shot](#tracking) | `tracking` | translation | 3 s | walking or running subjects |
| [Orbit 360](#orbit-360) | `orbit_360` | rotation | 6 s | products and sculptures |
| [Arc Shot](#arc) | `arc` | rotation | 3 s | dramatic character moments |
| [Crane Up](#crane-up) | `crane_up` | vertical | 3 s | establishing shots |
| [Crane Down](#crane-down) | `crane_down` | vertical | 3 s | openings that land on a character |
| [Pedestal Movement](#pedestal) | `pedestal` | vertical | 3 s | revealing tall products or façades level-on |
| [Tilt Up](#tilt-up) | `tilt_up` | rotation | 2 s | revealing height (towers, trees, people) |
| [Tilt Down](#tilt-down) | `tilt_down` | rotation | 2 s | openings from sky to scene |
| [Pan Left](#pan-left) | `pan_left` | rotation | 2 s | following lateral action |
| [Pan Right](#pan-right) | `pan_right` | rotation | 2 s | following lateral action |
| [Whip Pan](#whip-pan) | `whip_pan` | rotation | 1 s | transitions |
| [Zoom In](#zoom-in) | `zoom_in` | optical | 2 s | documentary or vintage looks |
| [Zoom Out](#zoom-out) | `zoom_out` | optical | 2 s | reveals in documentary style |
| [FPV Drone](#fpv-drone) | `fpv_drone` | aerial | 4 s | energetic real estate tours |
| [Aerial Reveal](#aerial-reveal) | `aerial_reveal` | aerial | 4 s | establishing shots |
| [Top-Down](#top-down) | `top_down` | aerial | 2 s | flat lays and food |
| [Handheld](#handheld) | `handheld` | style | 2 s | UGC and social content |
| [Steadicam](#steadicam) | `steadicam` | style | 3 s | long walkthroughs |
| [Bullet Time](#bullet-time) | `bullet_time` | special | 3 s | action peaks |
| [Dutch Angle](#dutch-angle) | `dutch_angle` | framing | 1 s | tension, disorientation |
| [Rack Focus](#rack-focus) | `rack_focus` | focus | 2 s | linking foreground and background subjects |
| [Parallax Movement](#parallax) | `parallax` | translation | 3 s | showing depth in interiors and landscapes |

<a id="static"></a>
## Static (locked-off) (`static`)

**Definition.** The camera does not move; all motion comes from the subject or the scene.

**Best use cases.** dialogue and talking heads; product turntables; letting a performance or action carry the shot; graphic compositions.

**Camera behaviour.** Fixed position, fixed framing, no drift, no zoom.

**Subject behaviour.** Provides all the motion: gestures, walking through frame, liquids, fabric, light changes.

**Example prompt.**

> Locked-off static camera on a tripod, medium shot of a barista pouring latte art, steam curling up, warm window light from camera left.

**Common mistakes.**

- asking for a static camera and a camera move in the same prompt
- static shots with no subject motion read as frozen stills

**Recommended combinations.** `rack_focus` · **Conflicts with:** `dolly_in`, `dolly_out`, `push_in`, `pull_out`, `tracking`, `orbit_360`, `arc`, `crane_up`, `crane_down`, `pedestal`, `tilt_up`, `tilt_down`, `pan_left`, `pan_right`, `whip_pan`, `zoom_in`, `zoom_out`, `fpv_drone`, `aerial_reveal`, `handheld`, `steadicam`, `bullet_time`, `parallax`

Aliases the engine recognises: locked off, locked-off, static shot, tripod, still camera, no camera movement.

<a id="dolly-in"></a>
## Dolly In (`dolly_in`)

**Definition.** The whole camera travels forward on a track toward the subject; perspective and parallax change as distance closes.

**Best use cases.** revealing importance; entering a space; product hero moments; architectural approach to an entrance.

**Camera behaviour.** Smooth constant-speed forward travel at fixed height, lens unchanged; background shifts with real parallax.

**Subject behaviour.** Usually holds position or makes one small action so the move does the storytelling.

**Example prompt.**

> Slow dolly in toward a matte-black wristwatch on a basalt plinth, constant height, softbox key from the left, background studio haze drifting with parallax.

**Common mistakes.**

- calling a zoom a dolly (a zoom has no parallax)
- combining with dolly out or pull out
- too fast for a short clip so the subject blows past the frame

**Recommended combinations.** `rack_focus`, `crane_up`, `tilt_up` · **Conflicts with:** `static`, `dolly_out`, `pull_out`, `zoom_out`

Aliases the engine recognises: dolly in, dolly-in, track in, dolly forward, move in.

<a id="dolly-out"></a>
## Dolly Out (`dolly_out`)

**Definition.** The camera travels backward away from the subject on a track, widening the frame and revealing surroundings with parallax.

**Best use cases.** revealing context or scale; endings and isolation; showing a product in its environment.

**Camera behaviour.** Smooth constant-speed backward travel at fixed height; foreground elements may enter frame edges.

**Subject behaviour.** Holds or recedes in relative size; the environment becomes the story.

**Example prompt.**

> Slow dolly out from a woman standing at a floor-to-ceiling window at blue hour, revealing the empty penthouse living room around her.

**Common mistakes.**

- combining with dolly in
- revealing nothing new: the wider frame must add information

**Recommended combinations.** `crane_up`, `tilt_down` · **Conflicts with:** `static`, `dolly_in`, `push_in`, `zoom_in`

Aliases the engine recognises: dolly out, dolly-out, track out, dolly back, move back.

<a id="push-in"></a>
## Push In (`push_in`)

**Definition.** A slow, subtle forward creep, smaller than a dolly in, used to build tension or intimacy.

**Best use cases.** emotional beats; close-ups and reactions; suspense; luxury product details.

**Camera behaviour.** Very slow forward movement, barely perceptible, ending a little tighter than it started.

**Subject behaviour.** Minimal: a breath, a glance, a slight turn of the head.

**Example prompt.**

> Subtle slow push in on the face of an elderly fisherman as he looks out to sea, overcast soft light, shallow depth of field.

**Common mistakes.**

- making it fast (then it is a dolly in)
- pairing with large subject motion that hides the move

**Recommended combinations.** `rack_focus`, `static` · **Conflicts with:** `dolly_out`, `pull_out`, `zoom_out`, `whip_pan`

Aliases the engine recognises: push in, push-in, slow push, creep in, slow creep.

<a id="pull-out"></a>
## Pull Out (`pull_out`)

**Definition.** The camera eases backward from a detail to a wider view, often ending on a reveal.

**Best use cases.** detail-to-context reveals; openings that start on texture; endings.

**Camera behaviour.** Starts tight on a detail and eases back; speed may ramp slightly at the start or end.

**Subject behaviour.** The detail stays readable as it becomes part of the larger picture.

**Example prompt.**

> Slow pull out from a macro of hand-stitched leather to reveal the full handbag on a travertine counter in a sunlit boutique.

**Common mistakes.**

- starting too wide so nothing is revealed
- combining with a push in

**Recommended combinations.** `crane_up`, `aerial_reveal` · **Conflicts with:** `static`, `dolly_in`, `push_in`, `zoom_in`

Aliases the engine recognises: pull out, pull-out, pull back, pullback, slow pull back.

<a id="tracking"></a>
## Tracking Shot (`tracking`)

**Definition.** The camera travels alongside, ahead of or behind a moving subject, keeping pace with it.

**Best use cases.** walking or running subjects; vehicles; following a character through a space; fashion walks.

**Camera behaviour.** Matches the subject's speed and direction, keeping framing consistent; background streams past.

**Subject behaviour.** Moves continuously in one clear direction.

**Example prompt.**

> Side tracking shot moving alongside a model walking down a sunlit concrete colonnade, camera matching her pace, shadows of columns sliding across her.

**Common mistakes.**

- a static subject (nothing to track)
- changing the subject's direction mid-shot
- mixing with orbit

**Recommended combinations.** `steadicam`, `handheld`, `parallax` · **Conflicts with:** `static`, `orbit_360`, `top_down`

Aliases the engine recognises: tracking shot, tracking, truck left, truck right, lateral track, follow shot, side tracking.

<a id="orbit-360"></a>
## Orbit 360 (`orbit_360`)

**Definition.** The camera circles the subject a full 360 degrees at constant distance and height, keeping it centred.

**Best use cases.** products and sculptures; hero character reveals; showing a building from every side.

**Camera behaviour.** Constant radius and height, smooth angular speed, subject locked in centre frame.

**Subject behaviour.** Mostly stationary so the orbit reads; small idle motion is fine.

**Example prompt.**

> Smooth 360-degree orbit around a ceramic perfume bottle on a mirrored plinth, constant distance, soft gradient backdrop, caustic reflections sweeping across the glass.

**Common mistakes.**

- clips under ~6 s (a full orbit becomes a blur)
- moving subjects that drift off-centre
- the back of the subject never designed (models invent geometry)

**Recommended combinations.** `crane_up`, `bullet_time` · **Conflicts with:** `static`, `tracking`, `pan_left`, `pan_right`, `whip_pan`, `top_down`

Aliases the engine recognises: orbit 360, 360 orbit, full orbit, circle around, 360 degree, 360°, turntable camera.

<a id="arc"></a>
## Arc Shot (`arc`)

**Definition.** A partial orbit (roughly 30–180 degrees) around the subject, changing the viewing angle with a sense of reveal.

**Best use cases.** dramatic character moments; revealing a product's profile; two-person scenes.

**Camera behaviour.** Curved path at constant distance, typically 45–120 degrees; may finish with a slight push.

**Subject behaviour.** Holds a pose or turns slightly against the arc for energy.

**Example prompt.**

> Slow arc shot curving 90 degrees around a boxer taping his hands in a dim locker room, single overhead tungsten bulb, dust in the light.

**Common mistakes.**

- not stating the angle (models over-rotate)
- combining with a full orbit

**Recommended combinations.** `push_in`, `crane_up` · **Conflicts with:** `static`, `orbit_360`, `whip_pan`

Aliases the engine recognises: arc shot, arc, partial orbit, half orbit, semi-circle, arc around.

<a id="crane-up"></a>
## Crane Up (`crane_up`)

**Definition.** The camera rises on a crane or jib arm, usually tilting down to keep the subject in frame, opening up the space.

**Best use cases.** establishing shots; endings; revealing crowds or landscapes; architecture.

**Camera behaviour.** Rises smoothly in an arc, often with a compensating tilt down.

**Subject behaviour.** Becomes smaller in frame as the environment opens.

**Example prompt.**

> Slow crane up from a couple at a candlelit table on a rooftop terrace, rising to reveal the city skyline at dusk.

**Common mistakes.**

- confusing with tilt up (a tilt does not change height)
- combining with crane down

**Recommended combinations.** `dolly_out`, `aerial_reveal`, `tilt_down` · **Conflicts with:** `static`, `crane_down`, `top_down`

Aliases the engine recognises: crane up, jib up, boom up, rising crane, crane shot up.

<a id="crane-down"></a>
## Crane Down (`crane_down`)

**Definition.** The camera descends on a crane or jib, moving from an overview into the scene.

**Best use cases.** openings that land on a character; arrivals; entering a space from above.

**Camera behaviour.** Descends smoothly, often tilting up to stay on the subject.

**Subject behaviour.** Grows in frame; often begins an action as the camera lands.

**Example prompt.**

> Slow crane down from above a desert courtyard, descending past palm fronds to settle on a woman opening a carved wooden door.

**Common mistakes.**

- landing on nothing in particular
- combining with crane up

**Recommended combinations.** `dolly_in`, `tilt_up` · **Conflicts with:** `static`, `crane_up`

Aliases the engine recognises: crane down, jib down, boom down, descending crane.

<a id="pedestal"></a>
## Pedestal Movement (`pedestal`)

**Definition.** The camera moves straight up or down without tilting, keeping the lens level; framing slides vertically.

**Best use cases.** revealing tall products or façades level-on; scanning a figure head to toe; architectural elevations.

**Camera behaviour.** Pure vertical translation, lens stays level, verticals stay parallel.

**Subject behaviour.** Static; the framing slides along it.

**Example prompt.**

> Slow pedestal up along the façade of a white stone villa, lens kept level, verticals perfectly parallel, midday shadows under each balcony.

**Common mistakes.**

- models add a tilt unless 'no tilt' and 'lens level' are stated
- combining with crane in the same direction

**Recommended combinations.** `dolly_in` · **Conflicts with:** `static`, `tilt_up`, `tilt_down`

Aliases the engine recognises: pedestal, pedestal up, pedestal down, ped up, ped down, vertical slide, elevator shot.

<a id="tilt-up"></a>
## Tilt Up (`tilt_up`)

**Definition.** The camera pivots upward on a fixed point, revealing what is above.

**Best use cases.** revealing height (towers, trees, people); awe and power; ending on a sky or logo.

**Camera behaviour.** Fixed position, rotates upward around the horizontal axis.

**Subject behaviour.** Usually static so the reveal reads.

**Example prompt.**

> Slow tilt up from the marble entrance steps to the top of a glass tower against a cloudless sky.

**Common mistakes.**

- calling it 'pan up'
- verticals converge on buildings: if geometry must stay straight use pedestal

**Recommended combinations.** `dolly_in`, `crane_down` · **Conflicts with:** `static`, `tilt_down`, `pedestal`, `top_down`

Aliases the engine recognises: tilt up, tilt-up, pan up.

<a id="tilt-down"></a>
## Tilt Down (`tilt_down`)

**Definition.** The camera pivots downward on a fixed point, moving from sky or high detail to the subject.

**Best use cases.** openings from sky to scene; revealing a subject below; landing on a product.

**Camera behaviour.** Fixed position, rotates downward around the horizontal axis.

**Subject behaviour.** Revealed at the end of the move.

**Example prompt.**

> Slow tilt down from swaying palm crowns to a turquoise infinity pool where a swimmer surfaces.

**Common mistakes.**

- combining with tilt up
- starting on empty sky for too long in a short clip

**Recommended combinations.** `crane_up`, `dolly_out` · **Conflicts with:** `static`, `tilt_up`, `pedestal`

Aliases the engine recognises: tilt down, tilt-down, pan down.

<a id="pan-left"></a>
## Pan Left (`pan_left`)

**Definition.** The camera rotates horizontally to the left from a fixed position.

**Best use cases.** following lateral action; surveying a landscape or room; linking two subjects.

**Camera behaviour.** Fixed position, rotates left around the vertical axis at even speed.

**Subject behaviour.** Moves left or is revealed by the pan.

**Example prompt.**

> Slow pan left across a misty tea plantation at sunrise, pickers moving between the rows.

**Common mistakes.**

- combining pan left and pan right
- fast pans judder: use whip pan or slow down

**Recommended combinations.** `tracking` · **Conflicts with:** `static`, `pan_right`, `orbit_360`

Aliases the engine recognises: pan left, pan-left, panning left.

<a id="pan-right"></a>
## Pan Right (`pan_right`)

**Definition.** The camera rotates horizontally to the right from a fixed position.

**Best use cases.** following lateral action; surveying a space; revealing a second subject.

**Camera behaviour.** Fixed position, rotates right around the vertical axis at even speed.

**Subject behaviour.** Moves right or is revealed by the pan.

**Example prompt.**

> Slow pan right along a sunlit kitchen island to reveal a family laughing at the breakfast table.

**Common mistakes.**

- combining pan right and pan left
- too fast for the clip length

**Recommended combinations.** `tracking` · **Conflicts with:** `static`, `pan_left`, `orbit_360`

Aliases the engine recognises: pan right, pan-right, panning right.

<a id="whip-pan"></a>
## Whip Pan (`whip_pan`)

**Definition.** An extremely fast pan that blurs the frame, used as an energetic transition between moments.

**Best use cases.** transitions; high-energy edits; comedy timing; social video pacing.

**Camera behaviour.** Snaps horizontally in a fraction of a second with heavy motion blur, settling on a new framing.

**Subject behaviour.** Before and after the whip, subjects are clearly framed; during it everything streaks.

**Example prompt.**

> Medium shot of a chef plating a dish, then a sudden whip pan with heavy motion blur snapping to the diner taking the first bite.

**Common mistakes.**

- using it inside slow luxury pieces
- asking for it with a slow push in
- no clear frame to land on

**Recommended combinations.** `handheld` · **Conflicts with:** `static`, `push_in`, `arc`, `orbit_360`

Aliases the engine recognises: whip pan, swish pan, whip-pan, flash pan.

<a id="zoom-in"></a>
## Zoom In (`zoom_in`)

**Definition.** The focal length lengthens so the frame tightens without the camera moving; no parallax change.

**Best use cases.** documentary or vintage looks; comedic or dramatic emphasis (crash zoom); surveillance feel.

**Camera behaviour.** Camera fixed, field of view narrows, background compresses.

**Subject behaviour.** Grows in frame with flat perspective.

**Example prompt.**

> Slow optical zoom in on a lone lighthouse on a cliff in a storm, camera fixed, 1970s documentary look.

**Common mistakes.**

- asking for a 'zoom' when you want a dolly's parallax
- combining zoom in and dolly out without saying 'dolly zoom'

**Recommended combinations.** `static`, `handheld` · **Conflicts with:** `zoom_out`, `dolly_out`, `pull_out`

Aliases the engine recognises: zoom in, zoom-in, punch in, crash zoom, snap zoom.

<a id="zoom-out"></a>
## Zoom Out (`zoom_out`)

**Definition.** The focal length shortens so the frame widens without the camera moving.

**Best use cases.** reveals in documentary style; comic reveals; showing isolation.

**Camera behaviour.** Camera fixed, field of view widens, perspective stays flat.

**Subject behaviour.** Shrinks in frame as context appears.

**Example prompt.**

> Slow optical zoom out from a hiker on a ridge to reveal the vast glacier valley below.

**Common mistakes.**

- expecting parallax (use dolly out)
- combining with zoom in

**Recommended combinations.** `static`, `crane_up` · **Conflicts with:** `zoom_in`, `dolly_in`, `push_in`

Aliases the engine recognises: zoom out, zoom-out.

<a id="fpv-drone"></a>
## FPV Drone (`fpv_drone`)

**Definition.** A fast, agile first-person-view drone flight that dives, banks and threads through gaps.

**Best use cases.** energetic real estate tours; action sports; threading through architecture; travel and events.

**Camera behaviour.** Fast forward flight with banking rolls, dives and close passes; slight wide-angle distortion.

**Subject behaviour.** Environment rushes past; people stay small or are passed by.

**Example prompt.**

> Fast FPV drone flight diving from the sky over a modern villa, banking through the open living room doors, skimming the pool surface and rising over the palm garden.

**Common mistakes.**

- too many waypoints for the clip length
- using it where calm and luxury is the brief
- combining with a locked-off tripod

**Recommended combinations.** `aerial_reveal` · **Conflicts with:** `static`, `steadicam`, `top_down`, `handheld`

Aliases the engine recognises: fpv, fpv drone, first person drone, drone dive, racing drone.

<a id="aerial-reveal"></a>
## Aerial Reveal (`aerial_reveal`)

**Definition.** A smooth drone move (rising, pulling back or flying over an obstacle) that reveals a location at scale.

**Best use cases.** establishing shots; real estate; travel; endings.

**Camera behaviour.** Slow, stable aerial travel; often starts behind a foreground element and rises or glides past it.

**Subject behaviour.** The location is the subject; small figures or vehicles give scale.

**Example prompt.**

> Slow aerial drone reveal rising over a dune ridge to reveal a contemporary desert resort glowing at golden hour.

**Common mistakes.**

- no foreground element to reveal from
- too fast (reads as FPV)

**Recommended combinations.** `crane_up`, `pull_out`, `dolly_out` · **Conflicts with:** `static`, `handheld`, `top_down`

Aliases the engine recognises: aerial reveal, drone reveal, aerial establishing, drone rise reveal, flyover.

<a id="top-down"></a>
## Top-Down (`top_down`)

**Definition.** The camera looks straight down at 90 degrees, flattening the scene into a graphic plan.

**Best use cases.** flat lays and food; patterns of crowds or traffic; architectural plans and rooftops; pools and landscapes.

**Camera behaviour.** Lens pointing straight down; may drift, rotate slowly or rise straight up.

**Subject behaviour.** Reads as shapes and patterns; motion across the frame is strongest.

**Example prompt.**

> Top-down overhead view of a breakfast flat lay on a linen tablecloth, camera pointing straight down, hands entering frame to pour coffee.

**Common mistakes.**

- also asking for eye-level framing
- tracking or orbit moves that break the straight-down axis

**Recommended combinations.** `static`, `zoom_out` · **Conflicts with:** `tracking`, `orbit_360`, `tilt_up`, `crane_up`, `fpv_drone`, `aerial_reveal`, `dutch_angle`

Aliases the engine recognises: top-down, top down, overhead, bird's eye, birds eye, god's eye, flat lay, 90 degree overhead.

<a id="handheld"></a>
## Handheld (`handheld`)

**Definition.** The camera is held by an operator, with natural micro-shake and reactive reframing.

**Best use cases.** UGC and social content; documentary realism; tension and chaos; intimate moments.

**Camera behaviour.** Small organic shake, breathing drift, reactive reframes; never mechanical.

**Subject behaviour.** Natural, unposed behaviour; the camera reacts to it.

**Example prompt.**

> Handheld camera with subtle natural shake following a young woman unboxing sneakers on her bedroom floor, daylight from a window, phone-camera realism.

**Common mistakes.**

- combining with steadicam, gimbal or locked-off
- exaggerated shake that makes viewers ill

**Recommended combinations.** `tracking`, `zoom_in`, `whip_pan` · **Conflicts with:** `static`, `steadicam`, `fpv_drone`, `aerial_reveal`

Aliases the engine recognises: handheld, hand-held, shaky cam, documentary camera, run and gun.

<a id="steadicam"></a>
## Steadicam (`steadicam`)

**Definition.** A stabilised, floating camera that moves freely through space with fluid motion.

**Best use cases.** long walkthroughs; following characters through rooms; real estate interiors; oners.

**Camera behaviour.** Smooth, floating travel with gentle curves; no shake, no track lines.

**Subject behaviour.** Leads the camera through the space or is circled gently.

**Example prompt.**

> Smooth steadicam move gliding from the entrance hall into a double-height living room, following a host who gestures toward the garden view.

**Common mistakes.**

- combining with handheld
- using it for a locked composition

**Recommended combinations.** `tracking`, `dolly_in`, `arc` · **Conflicts with:** `static`, `handheld`, `fpv_drone`

Aliases the engine recognises: steadicam, gimbal, stabilized, floating camera, smooth follow.

<a id="bullet-time"></a>
## Bullet Time (`bullet_time`)

**Definition.** Time freezes or slows to near-zero while the camera keeps moving around the subject.

**Best use cases.** action peaks; splashes and explosions; product impact moments; sports.

**Camera behaviour.** Arcs around the subject at normal speed while the scene is frozen or ultra-slow.

**Subject behaviour.** Frozen mid-action: droplets, debris and hair suspended in the air.

**Example prompt.**

> Bullet time: a sneaker frozen mid-splash in a puddle, droplets suspended in the air, the camera arcing slowly around it, neon reflections.

**Common mistakes.**

- subject still moving at normal speed
- clips shorter than 3 s
- too many frozen elements for the model to keep stable

**Recommended combinations.** `arc`, `orbit_360` · **Conflicts with:** `static`, `handheld`, `whip_pan`

Aliases the engine recognises: bullet time, bullet-time, frozen moment, time slice, matrix shot.

<a id="dutch-angle"></a>
## Dutch Angle (`dutch_angle`)

**Definition.** The camera is rolled on its axis so the horizon is tilted, creating unease or energy.

**Best use cases.** tension, disorientation; villains and thrillers; music videos; dynamic fashion.

**Camera behaviour.** Rolled 10–30 degrees; can be static or combined with a move.

**Subject behaviour.** Any; the tilt reframes it.

**Example prompt.**

> Dutch angle, camera rolled 20 degrees, a detective in a rain-soaked alley under a flickering neon sign.

**Common mistakes.**

- using it on architecture that must look straight
- rolling so far it reads as an error

**Recommended combinations.** `static`, `push_in`, `handheld` · **Conflicts with:** `top_down`

Aliases the engine recognises: dutch angle, dutch tilt, canted angle, canted frame, oblique angle.

<a id="rack-focus"></a>
## Rack Focus (`rack_focus`)

**Definition.** Focus shifts from one plane to another within the shot, redirecting attention.

**Best use cases.** linking foreground and background subjects; reveals; product details; dialogue.

**Camera behaviour.** Usually static or slow-moving; shallow depth of field; focus transitions smoothly between planes.

**Subject behaviour.** Two clear subjects at different depths.

**Example prompt.**

> Static shot, rack focus from raindrops on a café window in the foreground to a woman reading inside, shallow depth of field, 85mm.

**Common mistakes.**

- deep depth of field (nothing to rack)
- only one subject plane
- not naming both focus targets

**Recommended combinations.** `static`, `push_in`, `dolly_in`

Aliases the engine recognises: rack focus, focus pull, pull focus, focus shift, rack-focus.

<a id="parallax"></a>
## Parallax Movement (`parallax`)

**Definition.** A lateral or diagonal move past layered foreground, midground and background so depth separates visibly.

**Best use cases.** showing depth in interiors and landscapes; product shots through foreground elements; 2.5D animation of stills.

**Camera behaviour.** Slow sideways slide; near objects move faster than far ones.

**Subject behaviour.** Static or slow; the depth layers do the work.

**Example prompt.**

> Slow lateral parallax slide past blurred olive branches in the foreground, revealing a white villa terrace in the midground and the sea beyond.

**Common mistakes.**

- no foreground layer (no parallax to see)
- combining with a locked-off camera

**Recommended combinations.** `tracking`, `rack_focus` · **Conflicts with:** `static`

Aliases the engine recognises: parallax, parallax movement, parallax shot, lateral parallax, layered slide.
