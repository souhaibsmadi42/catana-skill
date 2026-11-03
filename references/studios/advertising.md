# Advertising Studio — commercials and campaigns

Professional commercial production across categories, and complete campaigns with several creative routes and
systematic variations. Use for `/catana:product-commercial`, `/catana:campaign-studio`, `/catana:ad-multiplier`, `/catana:hero-shot` (single
frame) and any "ad / commercial / campaign / spot" request.

## Category → preset

| Category | Preset (`--domain`) | Look in one line |
|---|---|---|
| Product / packaged goods / tech | `product` | studio sweep, softbox key + strip rim, 100mm macro |
| Luxury (perfume, jewellery, watches) | `product` + bible grade | low-key, black marble/stone, gold or crystal speculars, slow moves |
| Fashion | `fashion` | 85mm, hard sun or beauty dish, fabric in motion |
| Automotive | `automotive` | bumper-height tracking, low raking sun on paint, road leading lines |
| Food & beverage | `food` | backlit glow, steam, drizzle, 100mm macro, warm grade |
| Brand / emotional | `cinematic` | motivated light, anamorphic 40mm, people and story first |
| Real estate / hospitality | `architecture` | see `studios/architecture.md` |

## Inputs

Brand + product, the single message, audience, platform(s) and lengths, mandatories (logo, legal line, offer),
real assets (packshots, logo SVG, brand colours, fonts), music track if any. Ask for the message and platforms; infer
the rest and state assumptions. Never invent claims, prices or reviews.

## Single commercial workflow

1. One-sentence message + concept + visual direction (see `references/director.md`).
2. `python <skill>/scripts/catana.py plan new "<category> commercial for <product>" --duration 15 --platform <p> --out plan.json`
   — product arc: hook → reveal → detail → use → benefit → hero → end_card. (Automotive/food use the general arc unless
   you pass `--domain product`.)
3. Lock the product in `bible.products` (`@product`: exact shape, material, colour, label) and attach the packshot as a
   `product` reference with a `preserve` list on every product shot.
4. Compile, fix QC, present storyboard, generate keyframes → approve → animate → assemble; end card with logo, offer, CTA.

## Campaign workflow (`/catana:campaign-studio`)

A campaign = **2–4 creative routes** × **variations** × **platform cuts**.

1. Write the routes (each a different idea, not a different colour): e.g. *Ritual* (product in a daily moment),
   *Proof* (macro + demo of the benefit), *World* (the brand's mood, product as hero at the end), *Voice* (UGC route,
   see `studios/ugc.md`).
2. One plan per route at the master length (e.g. 30 s 16:9), then cut-downs per platform: `plan new … --platform
   instagram_reels` (9:16, 7–30 s), `tiktok`, `youtube_shorts`, `linkedin` (1:1), `ads_vertical` (6–20 s, brand by s3).
3. Shared bible across routes: product, palette, grade, logo rules — routes differ in story, not identity.
4. Deliver a campaign sheet: route × platform matrix with status (prompt pack / generated + asset link).

## Ad Multiplier (`/catana:ad-multiplier`) — variation matrix

Generate variations systematically, not randomly. Axes:

| Axis | Values (pick 2–4 each) |
|---|---|
| Hook | question · bold claim · problem shot · pattern interrupt (whip / crash zoom) · result-first · price/offer |
| Angle | benefit · emotion · social proof (real only) · comparison · founder story · how-to |
| Format | product hero · UGC talking head · demo · kinetic type (CATANA motion engine) · before/after |
| Platform | reels · tiktok · shorts · feed 4:5 · linkedin 1:1 · ads_vertical |

Rules: change **one axis at a time** against a control so results are attributable; keep product, offer and CTA
identical across variants; cap the first batch (e.g. 3 hooks × 2 angles × 1 format = 6) and expand winners.

**Naming:** `<brand>_<route>_<hook>_<angle>_<format>_<ratio>_<len>s_v<n>` → `aurora_ritual_question_benefit_ugc_9x16_15s_v1`.
Use the name as the shot/plan id so prompt packs, run-log entries and files line up.

**A/B notes:** record per variant the hypothesis ("question hook beats claim hook on 3-s hold"), the primary metric
(hook rate / 3-s views, CTR, CVR), and the minimum spend or impressions before deciding. CATANA does not read ad
metrics; the user brings results back and you iterate on the winning axis.

Existing ads: Higgsfield `ad_multiplier_v2` can recreate a source ad for a new audience/product or regenerate only the
hook or CTA (paid; quote + approval; re-verify with `models_explore`).

## Verified prompt patterns (`catana.py enhance`, QC A 100)

```text
luxury perfume campaign image of a faceted crystal bottle on black marble with gold reflections
automotive commercial video of a white electric SUV driving along a desert highway at sunset, tracking shot, 8 seconds
food commercial video of melted chocolate drizzling over a stack of pancakes, slow push in, 5 seconds
```

Pattern: `<category> <image|video> of <exact product with material + colour> <on/in setting> <one action>, <camera move>, <duration>`.

## Camera by category

Product: `orbit_360` (≥ 6 s), `push_in`, `rack_focus`, `top_down`, `bullet_time` (impact). Luxury: `push_in`, `arc`,
`dolly_out`, `rack_focus` — slow only. Automotive: `tracking`, `fpv_drone`, `aerial_reveal`, `crane_up`, `whip_pan`.
Food: `push_in`, `top_down`, `rack_focus`, `bullet_time` (splash). Fashion: `tracking`, `arc`, `handheld`, `steadicam`.
Check combinations: `catana.py camera check tracking crane_up --duration 6`.

## Provider routing

| Need | Operation | Higgsfield models (snapshot — verify first) |
|---|---|---|
| Key visual / hero still | t2i, multi_ref_image | `nano_banana_pro` (text rendering), `gpt_image_2`, `cinematic_studio_2_5`, `flux_3_image` (up to 10 refs) |
| Product-consistent video | multi_ref_video, i2v | `seedance_2_0` (identity / multi-SKU), `kling4_0`, `minimax_h3` |
| Premium cinematic spot | t2v, multi_ref_video | `cinematic_studio_video_4_0` (camera/lens/lighting/palette controls) |
| Ready-made ad formats | t2v | `marketing_studio_video`, Ads Studio (`ads_studio_*`) for image ads |
| Voiceover | tts | VoiceStudio (free) |
| Kinetic type / data ad | motion_graphics | CATANA motion engine (free, local) — `references/motion-film.md` |

All paid: quote first (`get_cost`, `ads_studio_quote`), run after explicit approval, log every result.

## QC checklist

- [ ] Product identical in every shot (bible + reference `preserve`: shape, label, colour, finish)
- [ ] Brand visible by second 3 on paid social; end card holds ≥ 1.5 s
- [ ] No invented claims, prices, reviews; legal line present if required
- [ ] Platform ratio and safe zones per cut; captions on
- [ ] Each variant differs on one axis only and follows the naming scheme
- [ ] Lighting family consistent within a route (one time of day / one studio setup)

## Failure modes → fixes

| Symptom | Fix |
|---|---|
| Logo/label warped | shoot the label frontal and large; `preserve` list; add the logo in the edit instead of generating it |
| All variants feel the same | vary the hook/angle, not adjectives; check the matrix |
| Luxury looks cheap | fewer elements, darker key, slower moves, one material story (stone + metal) |
| Car wheels melt / float | `automotive` negatives; shorter clips (4–6 s); tracking at constant speed |
| Food looks plastic | backlight + steam/moisture in `materials`; macro lens; warm grade |

## Deliverables

Concept + routes · storyboard per route · variation matrix with names · keyframe + video prompts · platform cuts ·
VO (free) · end-card spec · run log / prompt packs · A/B test plan.
