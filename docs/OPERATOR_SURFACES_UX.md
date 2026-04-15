# Operator Surfaces and UX

> Historical UX note: the active UI design source of truth is now `docs/UI_DESIGN.md`, and the active implementation/phase/status source of truth is `docs/UI_IMPLEMENTATION_MAP.md`. This file is retained as supporting background so older UX notes do not silently drift.

## Purpose of this file

This is now a short background note about the operator-UX intent behind the native Home Assistant direction.

Use instead:
- `docs/UI_DESIGN.md` for the current UI design
- `docs/UI_IMPLEMENTATION_MAP.md` for the current implementation strategy and delivery status

## Durable UX principles

- operator-first
- exception-first
- never hide active constraints
- every action should be explainable
- device setup should feel like a product workflow, not a developer JSON workflow
- native Home Assistant should be sufficient for setup, configuration, operation, and diagnostics

## Durable IA lesson

The product UX should keep one clear ownership boundary for each of these areas:
- Controls
- Sensors
- Managed Devices
- Diagnostics

Those boundaries are now defined in `docs/UI_DESIGN.md` and delivered through the plan in `docs/UI_IMPLEMENTATION_MAP.md`.
