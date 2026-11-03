---
description: Many ad concepts and variations from one product: hooks × angles × formats × platforms, named for A/B testing.
argument-hint: <product/offer> [n variations] [platforms] [audience]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **ad-variations** mode (Ad multiplier) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/references/studios/advertising.md`, `${CLAUDE_PLUGIN_ROOT}/references/studios/social.md`.
2. Do this:
   - Define 2–3 creative angles and 3+ hooks; build the variation matrix with a naming scheme
   - One spec per variation via the prompt engine; lint each
   - Execute the approved subset (quote the total first) or deliver the matrix as a prompt pack
   - Return a test plan: which variable each pair isolates
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: product/offer.

Limitations to state when relevant: Total cost scales with variations — always quote the batch before generating.
