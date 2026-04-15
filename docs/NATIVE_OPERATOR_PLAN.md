# Native Home Assistant Operator Plan

> Historical-direction note: this document is now background context only. The current UI design source of truth is `docs/UI_DESIGN.md`, the current UI implementation/status source of truth is `docs/UI_IMPLEMENTATION_MAP.md`, and `docs/SUPERVISOR.md` remains the active steering layer for goals, risks, release gates, and next actions.

## Purpose of this file

This file remains as a short historical record of the project's pivot to native Home Assistant surfaces.

Do not use this file as the primary source of truth for current UI design or current UI implementation planning.
Use:
- `docs/UI_DESIGN.md` for intended UI design
- `docs/UI_IMPLEMENTATION_MAP.md` for completed work, remaining work, phases, and features
- `docs/SUPERVISOR.md` for current steering and release posture

## Historical summary

The custom Zero Net Export panel route was removed.

The supported operator path became native Home Assistant only:
- Configure flow
- the integration device path at `Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device`
- entities, notifications, automations/scripts, and Repairs
- optional Lovelace dashboards only as supplementary debug visibility

## Durable project lesson

The native Home Assistant direction is the product direction.
The project should solve operator clarity and workflow quality inside native Home Assistant rather than by creating a parallel custom UI.
