# Native Surface Technical Direction

> Historical technical-direction note: UI design direction now lives in `docs/UI_DESIGN.md`, and implementation status / delivery phasing now lives in `docs/UI_IMPLEMENTATION_MAP.md`. Use this file as supporting background only.

## Purpose of this file

This file is now a compact technical background note.
It should not be the main location for current UI design or current UI implementation planning.

Use instead:
- `docs/UI_DESIGN.md` for the intended native Home Assistant UI design
- `docs/UI_IMPLEMENTATION_MAP.md` for implementation status, remaining work, and phase planning

## Durable technical direction

- Zero Net Export keeps the Home Assistant integration backend.
- The supported operator UX is limited to native Home Assistant surfaces.
- There is no supported custom sidebar, custom panel, or external UI path.
- If a workflow is required for normal install, setup, or troubleshooting, it should land in native Home Assistant surfaces.

## Durable technical non-goals

- reintroducing panel registration
- restoring `/zero-net-export` as a required route
- building core setup/troubleshooting flows that depend on custom frontend assets
