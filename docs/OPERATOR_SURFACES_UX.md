# Operator Surfaces and UX

> Historical UX note: this file is supporting background only. Current steering lives in `CONSTRAINTS.md`, `docs/ZNE_APPLICATION_DIRECTION.md`, `docs/ACTIVE_USER_REQUESTS.md`, and `docs/BUGS.md`; `docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md` are deprecated and must not override user-flagged bugs/features.

## Purpose of this file

This is now a short background note about the operator-UX intent behind the earlier native Home Assistant direction and the current application direction.

Use instead:
- `docs/ZNE_APPLICATION_DIRECTION.md` for the current Home Assistant application direction
- `docs/ACTIVE_USER_REQUESTS.md` for current Riley-flagged bugs/features
- `docs/BUGS.md` for active bug state

## Durable UX principles

- operator-first
- exception-first
- never hide active constraints
- every action should be explainable
- device setup should feel like a product workflow, not a developer JSON workflow
- the Zero Net Export Home Assistant application should be sufficient for setup, configuration, operation, and diagnostics
- native Home Assistant surfaces should remain useful fallback, automation, and recovery surfaces

## Durable IA lesson

The product UX should keep one clear ownership boundary for each of these areas:
- Controls
- Sensors
- Managed Devices
- Diagnostics

Those boundaries should now be expressed first in the Home Assistant application, with native surfaces used for support/fallback where appropriate.
