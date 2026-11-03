---
description: Architectural cinematics and visualization: exteriors, interiors, drone, day-to-night, weather, construction-to-completion.
argument-hint: <project> [length] [platform] [renders/plans as refs] [special: day-to-night|weather|construction]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **architecture** mode (Architecture film) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/references/studios/architecture.md`, `${CLAUDE_PLUGIN_ROOT}/references/director.md`.
2. Do this:
   - Plan with the architecture beats (establish, approach, threshold, flow, detail, life, hero, end card)
   - Preserve massing, floors, openings, roof and camera position from references; low motion intensity; corrected verticals
   - Day-to-night/weather/construction as per-shot lighting overrides + transition notes or first/last frames
   - Compile, lint, execute or deliver the pack
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: project.

Limitations to state when relevant: AI video can still bend geometry — always check verticals and window counts.
