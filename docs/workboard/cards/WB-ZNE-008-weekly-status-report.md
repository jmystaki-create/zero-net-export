# WB-ZNE-008 Weekly Status Report

Status: Validating
Priority: Normal
Labels: status, reporting, release, roadmap

## Purpose

Provide a concise weekly project status that shows progress, current focus, blockers, validation state, and next action.

## Current Status Snapshot

Date: 2026-07-15

Done:
- `v0.4.1` released and live/browser validated for ZNE-596 Sources SOC display.
- `v0.4.2` released and live/browser validated for `ZNE-FR-011` /
  `ZNE-FR-012` Overview console live metrics.
- `v0.4.3` released and live/browser validated for `ZNE-FR-013`
  Overview Readiness clarity.
- `v0.4.5` released and live/browser validated the action-oriented Readiness
  behavior for `ZNE-FR-014`.
- `v0.4.11` released and live/browser validated the Managed Devices
  `Review & promote` visible workflow.
- `v0.4.12` released and live validated `ZNE-595` recorder-backed attribute
  cleanup; post-restart log review found no ZNE recorder attribute-size
  warnings in the reviewed window.
- Milestone 7 multi-plan/service separation is released/live validated for
  API/static/service scope in `v0.4.0`.
- Sources app Battery state of charge now shows the correct backend binding and
  current reading in the installed app.

In progress / pending:
- Workboard must be checked and updated every ZNE turn.
- `ZNE-599` is open/high: unmanaged candidate promotion confirmation does not
  stay checked and the candidate is not added to the managed Fleet List.
- `ZNE-597` Battery Power/unit presentation needs a focused installed UI/unit
  proof because the exact display check was not captured in a release validation
  record.
- Bulk priority adjustment remains deferred to a later milestone.

Risks:
- Browser proof path is proven through the OpenClaw browser CLI and should remain part of future app-facing validation.
- Future app work must not drift into unsupported native HA UI injection.
- Multi-plan live proof for app-visible runtime metrics still needs a real
  multi-entry validation pass before claiming complete multi-plan UI telemetry.
- Multi-plan live proof for app-visible runtime metrics still needs a real
  multi-entry validation pass before claiming complete multi-plan UI telemetry.

Recommended next action:
- Fix and live-validate `ZNE-599`, then capture focused installed `ZNE-597`
  Battery Power/unit proof and choose the next app workflow slice.

## Acceptance Criteria

- Weekly report includes completed work, current focus, blockers, validation gaps, and next action.
- Report matches `PROJECT_STATUS.md`, `ROADMAP.md`, and validation records.
- Any release readiness claim links evidence.

## Evidence Needed To Mark Done

- This card is updated weekly or after major release milestones.
- Project state files match the report.
- Any completed validation is linked from `validation/`.
- OpenClaw Workboard state matches the report or the report explains any CLI limitation.
