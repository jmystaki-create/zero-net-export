# WB-ZNE-008 Weekly Status Report

Status: Ready
Priority: Normal
Labels: status, reporting, release, roadmap

## Purpose

Provide a concise weekly project status that shows progress, current focus, blockers, validation state, and next action.

## Current Status Snapshot

Date: 2026-07-01

Done:
- `v0.2.5` released and live-validated.
- ZNE-594 fixed and validated in installed Home Assistant.
- Sources backend write proof passed and was restored safely.
- OpenClaw Workboard UI is populated with the ZNE operating cards, and a dedicated card now tracks installed Sources browser proof.
- Installed Sources browser proof captured on desktop and narrow viewport.
- Milestone 3 Stage 2 is live-validated with Managed Devices fleet filters,
  sorting, enhanced columns, row selection, and confirmation-gated bulk
  enable/disable actions.
- Populated `light.7th` proof is captured; final ZNE managed record remains
  disabled.

In progress / pending:
- Workboard must be checked and updated every ZNE turn.
- Milestone 4 source-health work is active. Live API auth is restored and the
  baseline shows `sensor.zero_net_export_status=degraded` because
  `sensor.anker_battery_discharge_power` exposes `state_class=total`.
- Bulk priority adjustment is deferred to a later milestone.

Risks:
- Runtime control readiness remains limited by source-health until the battery
  discharge source is corrected and reconciliation is rechecked.
- Browser proof path is proven through the OpenClaw browser CLI and should remain part of future app-facing validation.
- Future app work must not drift into unsupported native HA UI injection.

Recommended next action:
- Apply or guide the Milestone 4 template sensor workaround, point ZNE at the
  fixed battery discharge source, and capture live proof that runtime status
  returns to `ok`.

## Acceptance Criteria

- Weekly report includes completed work, current focus, blockers, validation gaps, and next action.
- Report matches `PROJECT_STATUS.md`, `ROADMAP.md`, and validation records.
- Any release readiness claim links evidence.

## Evidence Needed To Mark Done

- This card is updated weekly or after major release milestones.
- Project state files match the report.
- Any completed validation is linked from `validation/`.
- OpenClaw Workboard state matches the report or the report explains any CLI limitation.
