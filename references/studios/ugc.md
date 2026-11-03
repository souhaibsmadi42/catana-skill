# UGC Studio — creator-style video

Realistic user-generated content: AI spokesperson, product demos, talking heads, influencer-style clips, social ads
built from several short scenes. The goal is *believable*, not polished — phone camera, real home, natural speech.

Use for `/catana:ugc-video`, and for any request mentioning UGC, creator, influencer style, testimonial-style, unboxing,
"get ready with me", review video, talking head. Domain preset: **`ugc`** (wins over product keywords: "UGC review
of a serum" is UGC). Default output 9:16 — pass `--platform tiktok|instagram_reels|youtube_shorts` so the ratio is set
(UGC and social default to 9:16 when no platform is given).

## Inputs (ask only what you can't infer)

| Need | Why | Default if not given |
|---|---|---|
| Product + 1–3 real benefits | the script makes claims; never invent results | ask — required |
| Platform | ratio, length, hook timing | TikTok, 9:16, 15–30 s |
| Persona (age range, vibe, setting) | casting + environment | matched to the product's audience, stated as an assumption |
| Product photos | label/packaging preservation | none → generic packaging, labelled illustrative |
| Voice | VO casting | a natural conversational voice in VoiceStudio |

**Disclosure and ethics.** AI spokespeople are fictional people: never recreate a real creator, celebrity or
customer, never write fake testimonials with invented numbers ("I lost 10 kg"), and recommend the platform's
AI-generated / paid-partnership labels. Results claims must come from the user.

## Workflow

1. **Script** (you write it) on the UGC arc — one line per beat, spoken, contractions, 2.5 words/s max:

   | Beat | Job | Seconds | Example line |
   |---|---|---|---|
   | hook | stop the scroll in ≤ 1.5 s | 2–3 | "Okay, I need to talk about this jar." |
   | problem | the relatable pain | 2–4 | "My mornings were coffee, crash, repeat." |
   | product | introduce it naturally, label to camera | 2–3 | "Then I switched to this matcha." |
   | demo | show it working (hands, pour, apply) | 3–5 | "Half a spoon, hot water, whisk — done." |
   | result | honest outcome the user stated | 2–4 | "Steady energy till lunch. No jitters." |
   | cta | one action | 2 | "Link's in my bio." |

2. **Plan:**
   ```bash
   python <skill>/scripts/catana.py plan new "UGC review of <product> by <persona> at home" --platform tiktok --out plan.json
   ```
   Every shot is `handheld` (the engine keeps UGC handheld). Fill `subject`/`action`/`environment` per shot and put the
   script lines in `vo`. Define the spokesperson in `bible.characters` (`@creator`) and the product in
   `bible.products` (`@product`) so every scene describes them identically.
3. **Compile and check VO fit:** `catana.py plan compile plan.json --out build/ugc`. Lines flagged `fits: false` are
   too long for their slot — cut words before anything else.
4. **Voiceover (free):** `catana.py voice plan build/ugc/compiled.json --out-dir build` (VoiceStudio). Direction in
   `sound.vo_direction`, e.g. "casual, a little excited, slight laugh on the hook, conversational pace".
   Pick a voice with `catana.py voice archetypes "young casual female"` or `voice describe "<description>"`.
5. **Picture:** generate a keyframe per scene with the creator + product (multi_ref_image), animate each (i2v or
   multi_ref_video). Talking to camera with synced lips needs `lipsync` — a paid operation (Higgsfield `sync_so`):
   quote it and run only with explicit approval; otherwise deliver b-roll + VO (works well for UGC voice-over style).
6. **Assemble** per `compiled.edl`: hard cuts, burned-in captions (most viewers watch muted), keep text inside the
   platform safe zone (`catana.py platforms`).

## Verified prompt patterns (`catana.py enhance`, QC A 100)

```text
UGC video of a young woman in her kitchen holding a jar of matcha powder to the camera, talking about her morning routine, 8 seconds   (--platform tiktok → 9:16)
UGC talking head video of a man in his car explaining why he switched to an electric toothbrush, 6 seconds, vertical
UGC unboxing video of wireless earbuds on a bedroom desk, hands opening the box, 9:16, 7 seconds
```

The first renders to (excerpt): *"Handheld camera with subtle natural shake and organic reframing: a young woman in
her kitchen holding a jar of matcha powder to the camera … Vertical selfie framing, face in the upper third, product
held toward camera in the lower third … smartphone front camera, 26mm-equivalent wide lens, deep focus. Natural
window daylight from the side, a little uneven … Authentic user-generated smartphone video, unpolished and
believable, natural smartphone color …"* with negatives *studio lighting, cinematic color grade, perfect skin
retouching, stock-photo look, lip-sync mismatch, warped product label*.

Pattern: `UGC <format> of <persona> in <real place> <doing one thing with the product>, <duration>, <ratio>`.
Keep one action per shot; put the second action in the next scene.

## Camera

`handheld` (default, all shots) · `push_in` for a "lean in" reveal (handheld + push reads as a selfie lean) ·
`whip_pan` between scenes for energy · `zoom_in` (crash zoom) on the punchline · `static` for a propped-up phone.
Avoid steadicam, crane, orbit, aerial — nothing a creator owns.

## Provider routing

| Step | Operation | Options (verify with the provider's discovery tool first) |
|---|---|---|
| Creator + product keyframe | multi_ref_image | Higgsfield `soul_2` (realistic UGC/character), `nano_banana_pro`, `flux_3_image` |
| Scene video | i2v / multi_ref_video | Higgsfield `seedance_2_0` (identity + product consistency), `kling_o3_image_reference` (up to 7 refs, multi-shot) |
| One-click UGC ad | t2v / i2v | Higgsfield `marketing_studio_video` (12–15 s, UGC/unboxing/review formats, avatars + products) |
| Voiceover | tts | **VoiceStudio (free, default)** — paid voices only on request |
| Lip-sync | lipsync | Higgsfield `sync_so` — paid, explicit approval |

`catana.py select --op multi_ref_video --duration 5 --aspect 9:16 --available higgsfield` ranks them; paid options come
back with `requires_approval: true` — quote (`get_cost: true` / `ads_studio_quote`) and ask. Check credits with
`balance` first; with 0 credits deliver the prompt pack (`catana.py pack`).

## QC checklist

- [ ] Hook line ≤ 1.5 s and the product visible by second 3
- [ ] Every VO line `fits` its slot; total ≈ platform `ideal_seconds`
- [ ] One action per shot; hands interacting with the product look natural (negatives include distorted hands)
- [ ] Product label preserved (product reference with a `preserve` list: label artwork, colours, shape)
- [ ] Same creator in every scene (`@creator` from the bible, same wardrobe)
- [ ] No cinematic grade, no studio light, no perfect skin
- [ ] Captions inside the safe zone; CTA visible on the last frame
- [ ] No fabricated claims; AI-generated disclosure recommended

## Failure modes → fixes

| Symptom | Fix |
|---|---|
| Looks like an ad, not a creator | remove polish words; keep the `ugc` preset's smartphone lens and window light; add "slightly messy real home" |
| Face changes between scenes | bible description + the same reference image in every scene; one model for the whole video |
| Label garbled | product reference with `preserve: ["label artwork", "logo", "colours"]`; keep the label large and frontal |
| Lips don't match VO | don't show mouths without lipsync; cut to hands/product during VO, or get approval for `sync_so` |
| Script too long | trust the `fits` flag; cut adjectives, not the CTA |

## Deliverables

Script (beat table) · `storyboard.md` · per-scene keyframe + video prompts · VoiceStudio VO files (`build/vo_*.wav`)
· caption text per line · EDL · run log of anything generated · 2–3 alternative hooks for testing.
