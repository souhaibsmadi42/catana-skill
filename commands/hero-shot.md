---
description: Premium cinematic still: product hero, packshot, key visual, editorial or portrait image.
argument-hint: <subject> [for <platform>] [aspect] [ref: image] [style notes]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **image** mode (Hero shot) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/docs/IMAGE_GENERATION.md`, `${CLAUDE_PLUGIN_ROOT}/references/studios/product.md`.
2. Do this:
   - Build the 13-field spec with `catana.py enhance` (product/fashion/food/automotive presets), add references with preserve lists
   - Lint (grade A/B required), pick an image provider with `catana.py select --op t2i|i2i|multi_ref_image`
   - Quote cost and get approval for paid connectors; generate 2–4 variations; verify and log every asset
   - Without a usable provider: deliver the prompt pack and say nothing was generated
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: subject.

Limitations to state when relevant: Exact label/logo text depends on the model; check every output and regenerate or fix in post; Paid generation needs a connector with credits.
