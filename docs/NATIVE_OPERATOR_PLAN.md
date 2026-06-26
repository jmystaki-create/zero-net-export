# Native Home Assistant Operator Plan

> Historical-direction note: this document is background context only. Current steering lives in `CONSTRAINTS.md`, `docs/ZNE_APPLICATION_DIRECTION.md`, `docs/ACTIVE_USER_REQUESTS.md`, `docs/BUGS.md`, `docs/SUPERVISOR.md`, and `docs/WATCHDOG.md`. `docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md` are deprecated and are not active source-of-truth documents.

## Purpose of this file

This file remains as a short historical record of the project's earlier pivot to native Home Assistant surfaces.

Do not use this file as the primary source of truth for current UI design or current UI implementation planning.
Use:
- `docs/ACTIVE_USER_REQUESTS.md` for current Riley-flagged bugs/features
- `docs/ZNE_APPLICATION_DIRECTION.md` for the current Home Assistant application direction
- `docs/BUGS.md` for active bug state
- `docs/SUPERVISOR.md` for current steering and release posture

## Historical summary

The custom Zero Net Export panel route was removed.

The supported operator path became native Home Assistant only:
- Configure flow
- the integration device path at `Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device`
- entities, notifications, automations/scripts, and Repairs

## Durable project lesson

The native-only direction was tried and later superseded.
The project lesson is that the backend belongs in the Home Assistant integration, but the full operator workflow needs a Zero Net Export-owned Home Assistant application surface.
