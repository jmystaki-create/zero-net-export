# Implementation Plan

> Historical implementation note: current steering lives in `CONSTRAINTS.md`, `docs/ZNE_APPLICATION_DIRECTION.md`, `docs/ACTIVE_USER_REQUESTS.md`, `docs/BUGS.md`, `docs/SUPERVISOR.md`, and `docs/WATCHDOG.md`. `docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md` are deprecated and are not active source-of-truth documents.

## Purpose of this file

This file is now the historical implementation trail for how the integration was built before the UI-source-of-truth consolidation.

Do not use this file as the main place to decide current UI work.
Use:
- `docs/ZNE_APPLICATION_DIRECTION.md` for the Home Assistant application direction
- `docs/ACTIVE_USER_REQUESTS.md` for current Riley-flagged bugs/features
- `docs/BUGS.md` for active bug state
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
8. application-port pivot after native-device-page constraints proved too limiting

## Durable implementation lesson

The project accumulated substantial backend capability before the visible native UI became coherent enough.
The native-device-page route then proved too constrained for the full product scope.
Current UI delivery should be judged against the Home Assistant application direction in `docs/ZNE_APPLICATION_DIRECTION.md`, with bug state tracked in `docs/BUGS.md`.

## Next implementation trail

The next implementation plan should start from a minimal Home Assistant
application/panel milestone:

1. create or restore a supported app/panel route
2. render a nonblank Overview on desktop and mobile
3. display at least one real backend/runtime value
4. keep native Configure/device pages as fallback/support surfaces
5. validate with repo tests, browser proof, and logs before release claims
