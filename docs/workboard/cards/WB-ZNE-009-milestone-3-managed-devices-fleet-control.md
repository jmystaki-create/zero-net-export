# WB-ZNE-009 Milestone 3: Managed Devices Fleet Control

Status: Ready
Priority: High
Labels: milestone, feature, app, fleet-control, validation

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

## Next steps

1. Accept the feasibility check in `validation/zne-app-milestone-3-feasibility.md`.
2. Approve starting Milestone 3 implementation.
3. Proceed with minimal design and implementation within the accepted feasible path.
4. Validate with repo tests, HACS install, HA restart, browser proof, and logs.
5. Release as the next app feature release after validation.
