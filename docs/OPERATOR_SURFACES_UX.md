# Operator Surfaces and UX

> Historical UX note: this file is supporting background only. Current steering lives in `docs/ACTIVE_USER_REQUESTS.md` and `docs/BUGS.md`; `docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md` are deprecated and must not override user-flagged bugs/features.

## Purpose of this file

This is now a short background note about the operator-UX intent behind the native Home Assistant direction.

Use instead:
- `docs/ACTIVE_USER_REQUESTS.md` for current Riley-flagged bugs/features
- `docs/BUGS.md` for active bug state

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

Those boundaries are now constrained by current user-flagged bugs/features in `docs/ACTIVE_USER_REQUESTS.md` and tracked in `docs/BUGS.md`.
