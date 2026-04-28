# Native Surface Technical Direction

> Historical technical-direction note: this file is supporting background only. Current steering lives in `docs/ACTIVE_USER_REQUESTS.md` and `docs/BUGS.md`; `docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md` are deprecated.

## Purpose of this file

This file is now a compact technical background note.
It should not be the main location for current UI design or current UI implementation planning.

Use instead:
- `docs/ACTIVE_USER_REQUESTS.md` for current Riley-flagged bugs/features
- `docs/BUGS.md` for active bug state

## Durable technical direction

- Zero Net Export keeps the Home Assistant integration backend.
- The supported operator UX is limited to native Home Assistant surfaces.
- There is no supported custom sidebar, custom panel, or external UI path.
- If a workflow is required for normal install, setup, or troubleshooting, it should land in native Home Assistant surfaces.

## Durable technical non-goals

- reintroducing panel registration
- restoring `/zero-net-export` as a required route
- building core setup/troubleshooting flows that depend on custom frontend assets
