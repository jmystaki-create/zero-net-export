# Roadmap

Last updated: 2026-08-02

## Status

Active: Operator tabs UI/UX redesign browser/live validation.

## Current Roadmap Item

### Operator Tabs Console Redesign

Goal: make the sidebar app tabs follow operator priority and turn the sparse Sources, Controls, and Runtime tabs into useful monitoring/control surfaces.

Implementation status: repo-validated, pending browser/live proof before release closeout.

Scope:

- Reorder tabs to `Overview -> Managed Devices -> Sources -> Controls -> Runtime -> Diagnostics -> Settings`.
- Redesign Sources as a measurement trust/source-health workspace.
- Redesign Controls as a control-policy workspace with safety guards and next-action preview.
- Redesign Runtime as an execution/activity workspace.
- Preserve Managed Devices watt dashboard, measured/estimated semantics, disabled-active alert, bulk/per-row controls, candidate review/promotion, and confirmation gates.
- Preserve plan context, service scoping, Diagnostics, and release validation discipline.
- Use existing frontend-visible entities first; avoid backend aggregate sensors unless validation proves a data gap.

Workboard cards: `WB-ZNE-TABUX-001` through `WB-ZNE-TABUX-007`.

## Completed Baseline

- `v0.4.19` is the latest public release and installed Home Assistant/HACS baseline before this operator-tabs scope.
- The Overview UI/UX command-center refactor is released and live validated.
- The Managed Devices load-aware fleet console is the current baseline and must be preserved.
- Historical app milestones, bug fixes, feature requests, release validation, and browser proof remain preserved in project documentation and git history.

## Evidence

- Workboard: `docs/workboard/README.md`
- Review: `ui_ux_review.md`
- Feasibility: `validation/zne-operator-tabs-redesign-feasibility.md`
- Repo validation: `validation/zne-operator-tabs-redesign-implementation.md`
