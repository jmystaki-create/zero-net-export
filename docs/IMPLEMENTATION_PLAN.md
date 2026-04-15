# Implementation Plan

> Historical implementation note: `docs/SUPERVISOR.md` remains the active steering layer, `docs/UI_DESIGN.md` is now the active UI design source of truth, and `docs/UI_IMPLEMENTATION_MAP.md` is now the active UI implementation / phase / status source of truth. This file remains the longer historical implementation trail.

## Purpose of this file

This file is now the historical implementation trail for how the integration was built before the UI-source-of-truth consolidation.

Do not use this file as the main place to decide current UI work.
Use:
- `docs/UI_DESIGN.md` for the intended product/UI design
- `docs/UI_IMPLEMENTATION_MAP.md` for completed work, remaining work, phases, and features
- `docs/SUPERVISOR.md` for current steering and next actions

## Historical build summary

The project progressed through these broad stages:
1. repo scaffold and entity model
2. Home Assistant integration skeleton
3. source mapping and validation model
4. controller / planner / runtime control engine
5. UX entities and optional dashboard scaffolding
6. diagnostics, reporting, and hardening
7. native-surface consolidation after removing the custom panel route

## Durable implementation lesson

The project accumulated substantial backend capability before the visible native UI became coherent enough.
That is why current UI delivery should be judged through `docs/UI_IMPLEMENTATION_MAP.md`, which separates:
- what exists in code
- what is only partial/scaffolded
- what still is not visibly delivered in Home Assistant
