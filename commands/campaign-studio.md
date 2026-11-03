---
description: Complete multi-platform campaign: concept, key visual, video spots, platform cuts, copy and a production plan.
argument-hint: <brand/product> [objective] [platforms] [budget/scope]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **campaign** mode (Campaign studio) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/references/studios/advertising.md`, `${CLAUDE_PLUGIN_ROOT}/references/studios/social.md`, `${CLAUDE_PLUGIN_ROOT}/references/director.md`.
2. Do this:
   - Big idea + 2–3 routes; key visual specs; hero spot plan; per-platform cuts from data/platforms.json (ratio, length, hook, safe zones)
   - Variation matrix for testing; copy per placement
   - Quote the full production before generating; otherwise deliver the campaign pack
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: brand/product.

Limitations to state when relevant: Platform limits change — confirm paid-placement specs before trafficking.
