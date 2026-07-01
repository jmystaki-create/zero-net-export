# WB-ZNE-009 Milestone 3: Managed Devices Fleet Control

Status: Validating
Priority: High
Labels: milestone, feature, app, fleet-control, validation, in-progress

## Purpose

Define and implement ZNE-APP-003: Managed Devices Fleet Control, the next app
milestone after Sources workflow (ZNE-APP-002).

## User outcome

An operator can use the Zero Net Export app to:
- See the complete fleet of managed devices across all plans/services.
- Filter by plan, status, priority, or readiness.
- Review device health, last-seen age, and runtime blockers.
- Perform bulk actions (enable/disable, priority adjustment) with strong confirmation.
- Drill into individual device details, edit captured settings, and remove from ZNE.
- Understand why specific devices are not participating in runtime control.

## Acceptance criteria

- The Managed Devices tab in the app shows a complete fleet list across all plans.
- Each row displays: device name, plan/service context, status (enabled/disabled),
  priority, last-seen age, and readiness state.
- Filter controls exist for plan, status, priority, and readiness.
- Bulk action controls exist for enable/disable and priority adjustment.
- Bulk actions require strong confirmation (e.g., typing "CONFIRM" or selecting
  a confirmation checkbox plus explicit action button).
- Drill-down detail view shows captured settings, runtime state, and blockers.
- Edit captured settings uses a supported HA reconfigure/options flow scoped to
  the owning config entry.
- Remove from ZNE uses the supported backend service path and preserves the
  original HA device/entity.
- Fleet summary shows counts: total, enabled, disabled, blocked, stale.
- Desktop and narrow browser proof are captured before release.
- Repo validation passes JavaScript syntax check, changed Python compile check,
  focused fleet-control tests, full test discovery, and `git diff --check`.
- Live validation passes HACS install/update, Home Assistant restart, install
  fingerprint match, app/static route checks, targeted log review, browser proof,
  and a reversible managed-device add/remove or edit proof if a safe disposable
  device is available.
- No native Home Assistant device-page/card/row injection is introduced.
- No direct Home Assistant file-backend deployment is used for release or live
  validation.

## Evidence needed to mark done

- Feasibility check `validation/zne-app-milestone-3-feasibility.md` is accepted.
- Milestone plan `docs/ZNE_APP_MILESTONE_3_PLAN.md` is updated with acceptance.
- Repo validation passes (JS check, py_compile, focused tests, full discovery,
  `git diff --check`).
- GitHub/HACS release published and installed.
- Home Assistant restart and fingerprint match verified.
- Desktop and narrow browser proof captured in `validation/artifacts/`.
- Targeted log scan shows no ZNE errors/warnings/tracebacks.
- Fleet summary counts, filters, bulk actions, and drill-down proof exist.
- `ROADMAP.md` and `PROJECT_STATUS.md` reflect Milestone 3 completion.

## Current estimate

Milestone 3 is in draft. Feasibility check is written but not yet accepted.
No design or code work has started.

**Status:** Feasibility check accepted on 2026-07-01 16:35 AEST. Ready to proceed with implementation.

**Updated:** Stage 1 (fleet list with summary, filters, and drill-down) implemented and committed. Repo validation passed (620 tests OK, `git diff --check` clean, JS syntax valid).

**Latest:** `v0.2.5` is published and installed through the approved
GitHub/HACS path. Home Assistant restarted, install fingerprint matched before
and after restart, app/static routes returned HTTP 200, targeted ZNE logs showed
no project-specific errors, and desktop/narrow Managed Devices browser proof was
captured. Evidence: `validation/0.2.5-release-validation.md`.

Remaining validation gap: the live validation instance currently has
`sensor.zero_net_export_managed_devices_count=0`, so populated row proof for
Blockers and reversible bulk enable/disable mutation need a safe disposable
managed device before this card can move to Done.

## Next steps

1. ~~Accept the feasibility check in `validation/zne-app-milestone-3-feasibility.md`.~~ (Done)
2. ~~Approve starting Milestone 3 implementation.~~ (Done)
3. ~~Begin minimal design and implementation of the Managed Devices Fleet Control workflow within the accepted feasible path.~~ (Stage 1 complete)
4. ~~Implement the smallest next app workflow slice (e.g., fleet list with filters and summary).~~ (Stage 1 complete)
5. ~~Validate Stage 1 with repo tests.~~ (Done; live validation pending)
6. ~~Implement Stage 2 priority/readiness filters, bulk actions, and sorting.~~ (Done)
7. ~~Proceed with live validation and browser proof for the complete Stage 1+2 Managed Devices fleet workflow.~~ (Done for installed empty-fleet workflow in `v0.2.5`)
8. Add or identify a safe disposable managed device, then capture populated-row and reversible bulk-action proof.
