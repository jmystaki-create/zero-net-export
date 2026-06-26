# Native Surface Technical Direction

> Historical technical-direction note: this file is supporting background only. Current steering lives in `CONSTRAINTS.md`, `docs/ZNE_APPLICATION_DIRECTION.md`, `docs/ACTIVE_USER_REQUESTS.md`, and `docs/BUGS.md`; `docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md` are deprecated.

## Purpose of this file

This file is now a compact technical background note.
It should not be the main location for current UI design or current UI implementation planning.

Use instead:
- `docs/ZNE_APPLICATION_DIRECTION.md` for the current Home Assistant application direction
- `docs/ACTIVE_USER_REQUESTS.md` for current Riley-flagged bugs/features
- `docs/BUGS.md` for active bug state

## Superseded technical direction

- Zero Net Export keeps the Home Assistant integration backend.
- The old supported operator UX was limited to native Home Assistant surfaces.
- That native-only direction is superseded as of 2026-06-26.
- The current direction is a Home Assistant application/panel backed by the existing integration backend.

## Retired non-goals

- reintroducing panel registration
- restoring `/zero-net-export` as a required route
- building core setup/troubleshooting flows that depend on custom frontend assets

These were valid non-goals under the native-only direction. They are no longer
valid blockers for the approved application port.
