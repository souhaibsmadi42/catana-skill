# Examples

| Example | What it shows | Files |
|---|---|---|
| [villa-commercial](villa-commercial/) | **AI Director output** for "a luxury cinematic commercial for a modern villa in Abu Dhabi": filled plan (concept, visual direction, continuity bible, 8 shots), compiled keyframe and video prompts, VO plan, edit list, QC (all shots grade A) | `plan.json`, `compiled.json`, `storyboard.md` |
| [catana-2-promo](catana-2-promo/) | **Motion engine film**, one scene file rendered at 16:9, 9:16 and 1:1 | `scenes.js`, MP4s in `media/` |

The villa example is a production pack: nothing was generated with a paid provider. To produce it, run
`/catana:video-director` with the plan, or take `storyboard.md` shot by shot into your generator.
