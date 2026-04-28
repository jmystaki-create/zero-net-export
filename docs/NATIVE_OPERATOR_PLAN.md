# Native Home Assistant Operator Plan

> Historical-direction note: this document is background context only. Current steering lives in `docs/ACTIVE_USER_REQUESTS.md`, `docs/BUGS.md`, `docs/SUPERVISOR.md`, and `docs/WATCHDOG.md`. `docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md` are deprecated and are not active source-of-truth documents.

## Purpose of this file

This file remains as a short historical record of the project's pivot to native Home Assistant surfaces.

Do not use this file as the primary source of truth for current UI design or current UI implementation planning.
Use:
- `docs/ACTIVE_USER_REQUESTS.md` for current Riley-flagged bugs/features
- `docs/BUGS.md` for active bug state
- `docs/SUPERVISOR.md` for current steering and release posture

## Historical summary

The custom Zero Net Export panel route was removed.

The supported operator path became native Home Assistant only:
- Configure flow
- the integration device path at `Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device`
- entities, notifications, automations/scripts, and Repairs

## Durable project lesson

The native Home Assistant direction is the product direction.
The project should solve operator clarity and workflow quality inside native Home Assistant rather than by creating a parallel custom UI.
