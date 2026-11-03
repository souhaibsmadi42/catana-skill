---
description: Authentic creator-style video: AI spokesperson, talking head, unboxing, review, demo, testimonial — scripted, multi-scene.
argument-hint: <product/offer> [platform] [length] [persona] [hook idea]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **ugc** mode (UGC video) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/references/studios/ugc.md`, `${CLAUDE_PLUGIN_ROOT}/references/director.md`.
2. Do this:
   - Write the script with the UGC beats (hook, problem, product, demo, result, CTA) and voiceover direction
   - Plan shots with `catana.py plan new --domain ugc` (handheld phone language), fill bible (persona @id, product)
   - Voiceover free via VoiceStudio; spokesperson video via a connector only with approval (lip-sync is a paid step)
   - Compile, lint, execute or deliver the prompt pack + script
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: product or offer.

Limitations to state when relevant: Never impersonate a real person; AI spokespeople are fictional or consented; Lip-synced talking heads need a paid connector.
