# WB-ZNE-004 MVP Definition

Status: Ready
Priority: High
Labels: mvp, product, acceptance-criteria, release

## Purpose

Define the minimum useful Zero Net Export app MVP so development can measure progress against a product outcome rather than a stream of release fixes.

## MVP Candidate

The MVP is a Home Assistant app that lets an operator:
- See overall Zero Net Export readiness.
- Select the relevant plan/service context.
- Review and repair source-role bindings.
- Review managed devices and perform safe enabled/remove actions.
- Review and edit core controls.
- Understand why runtime control is blocked.
- Access diagnostics/support evidence.
- Trust that all writes are scoped to the selected config entry.

## Acceptance Criteria

- MVP workflows are listed with pass/fail validation requirements.
- Required live browser proof includes desktop and narrow/mobile viewport screenshots.
- Runtime readiness gaps are explicitly separated from release-install success.
- Destructive actions require strong confirmation.
- Multi-plan/service state remains entry-scoped.

## Evidence Needed To Mark Done

- MVP definition is agreed and reflected in `ROADMAP.md`.
- Each MVP workflow has validation records or an explicit remaining gap.
- Browser proof exists for primary app workflows.
- Runtime readiness evidence exists or runtime limitations are documented as non-MVP.

## Current Estimate

Application MVP is about 76% complete. The app shell, Sources workflow,
managed-device fleet workflow, controls slice, release path, backend write
proof, and installed browser proof for Sources and Managed Devices are in place.

**Updated:** Milestone 3 feasibility check accepted on 2026-07-01 16:35 AEST.

**Latest:** Milestone 3 Stage 2 is released and live-validated as `v0.2.5`
with Managed Devices fleet filters, sorting, enhanced columns, row selection,
and confirmation-gated bulk enable/disable actions. Empty-fleet and populated
`light.7th` browser proof are recorded in `validation/0.2.5-release-validation.md`.
Bulk priority adjustment is deferred to a later milestone. The current MVP gap
is Milestone 4 source-health/runtime readiness: live API proof shows
`sensor.zero_net_export_status=degraded` until the battery discharge source is
corrected and reconciliation is rechecked.
