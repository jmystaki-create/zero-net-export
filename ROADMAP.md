# Roadmap

Last updated: 2026-08-02

## Workboard

The maintained project Workboard lives at `docs/workboard/README.md`.

The workboard was reset on 2026-08-02 to remove stale historical cards and track only the current Zero Net Export main Overview UI/UX refactor derived from `ui_ux_review.md`.

Current state: released/live validated in `v0.4.17`. Evidence:
`validation/zne-uiux-overview-refactor-feasibility.md` and
`validation/zne-uiux-overview-refactor-implementation.md`,
`validation/0.4.17-release-validation.md`, and browser artifacts under
`validation/artifacts/zne-uiux-v0.4.17-overview-*`.

Active workboard scope:
- `WB-ZNE-UIUX-001` Health State Model
- `WB-ZNE-UIUX-002` Managed Device Review Primary Action
- `WB-ZNE-UIUX-003` Live Power Snapshot
- `WB-ZNE-UIUX-004` State-Aware Executor Controls
- `WB-ZNE-UIUX-005` Diagnostics And Raw Detail Preservation
- `WB-ZNE-UIUX-006` Plan And Editable Workflow Preservation
- `WB-ZNE-UIUX-007` Readiness Explanation Preservation
- `WB-ZNE-UIUX-008` Destructive Confirmation Guardrails
- `WB-ZNE-UIUX-009` Responsive Overview Layout
- `WB-ZNE-UIUX-010` Validation And Release Readiness
- `WB-ZNE-UIUX-011` Target Feasibility And Implementation Plan

Historical release and validation records remain in `validation/`, `CHANGELOG.md`, `docs/BUGS.md`, `docs/FEATURE_REQUESTS.md`, and earlier roadmap/project-status history, but they are no longer active workboard cards.

## Current milestone

### ZNE-APP-007 - Multi-Plan And Service Separation

Status: released/live validated via API/static/service checks as `v0.4.0`.

Outcome:
- Operators can see and work inside an explicit Zero Net Export plan/service context.
- Reads and writes for sources, managed devices, controls, runtime, diagnostics,
  export, and repair are scoped to the selected context.
- Ambiguous multi-entry write requests fail safely instead of silently choosing
  the first entry.

Evidence:
- Feasibility: `validation/zne-app-milestone-7-multi-plan-feasibility.md`
- Plan: `docs/ZNE_APP_MILESTONE_7_PLAN.md`
- Implementation: `validation/zne-app-milestone-7-implementation.md`
- Release/live validation: `validation/0.4.0-release-validation.md`

Next gate:
- Capture app/browser visual proof for the remaining product slices where it is
  still missing, and define the next accepted app workflow milestone before
  implementation.

### ZNE-APP-006 - Diagnostics & Support Polish

Status: released/live validated as `v0.3.3`. Implementation and corrective
releases are published; browser validation proves the installed app renders, and
service/action validation proves diagnostics export and repair services run.

Outcome:
- Operators can view recent ZNE logs, system health summary, and reconciliation
trend in the app.
- Operators can see error banners with repair guidance when sources are blocked
or mismatched.
- Operators can download a JSON diagnostics file with filtered sensitive data.

Evidence:
- Plan: `docs/MILESTONE_6_IMPLEMENTATION_PLAN.md`
- Feasibility: `docs/MILESTONE_6_DIAGNOSTICS_SUPPORT_FEASIBILITY.md`
- Implementation validation: `validation/milestone-6-implementation-validation.md`
- Release validation: `validation/0.3.3-release-validation.md`
- Previous corrective note: `validation/v0.3.1-fix-validation.md`

Next gate:
- Track runtime degraded state separately from Milestone 6 service validation.

## Completed App Milestones

### ZNE-APP-005 - Runtime Visibility & Manual Override

Status: released as `v0.3.0`; live-validated with API tests and sensor checks.

Outcome:
- Operators can view live reconciliation data (home load, source power, battery
power, surplus/deficit, reconciliation error).
- Operators can pause/resume the executor via services and frontend buttons.
- Safety logging and executor pause flag implemented.

Evidence:
- Plan: `docs/ZNE_APP_MILESTONE_5_PLAN.md` (to be created if not exists)
- Live baseline: `validation/milestone-5-runtime-visibility-validation.md`
- Release validation: `validation/0.3.0-release-validation.md` (to be created)

### ZNE-APP-004 - Source Health & Runtime Blocker Resolution

Status: released/live-validated as `v0.2.9`. Milestone 4 plan and
source-health fix guide are written, the approved Home Assistant template sensor
workaround is applied, and the installed validation target reports ready runtime
state.

Outcome:
- Operators can resolve source-health blockers that keep ZNE runtime status
  degraded.
- Operators can use a corrected battery discharge power source with
  measurement semantics.
- Operators can verify runtime source reconciliation is acceptable before
  relying on control decisions.

Evidence:
- Plan: `docs/ZNE_APP_MILESTONE_4_PLAN.md`
- Fix guide: `docs/SOURCE_HEALTH_FIX_GUIDE.md`
- Live baseline: `validation/zne-app-milestone-4-live-baseline.md`
- Release/live validation: `validation/0.2.9-release-validation.md`

### ZNE-APP-003 - Managed Devices Fleet Control

Status: released as `v0.2.5`; installed empty-fleet workflow and populated
`light.7th` fleet workflow live-validated. Final `7th_validation_load` ZNE
record remains present and disabled. Bulk priority adjustment is deferred to a
later milestone.

Evidence:
- Plan: `docs/ZNE_APP_MILESTONE_3_PLAN.md`
- Feasibility: `validation/zne-app-milestone-3-feasibility.md`
- Stage 1 plan: `validation/zne-app-milestone-3-stage-1-plan.md`
- Stage 1 repo validation: `validation/zne-app-milestone-3-stage-1-validation.md`
- Stage 2 plan: `validation/zne-app-milestone-3-stage-2-plan.md`
- Stage 2 repo validation: `validation/zne-app-milestone-3-stage-2-validation.md`
- Release/live validation: `validation/0.2.5-release-validation.md`

### ZNE-APP-002 - App-native Sources workflow

Status: released as `v0.2.3`; GitHub/HACS install live-validated. Desktop and narrow browser proof captured on installed `v0.2.4`.

Outcome:
- Operators can review source-role bindings, status, readings, age, and issues in the Zero Net Export app.
- Operators can save source-role bindings through the supported backend service path.
- Runtime setup blockers become visible and repairable from the app.

Evidence:
- Plan: `docs/ZNE_APP_MILESTONE_2_SOURCES_PLAN.md`
- Feasibility: `validation/zne-app-milestone-2-sources-feasibility.md`
- Repo validation: `validation/zne-app-milestone-2-sources-implementation.md`
- Release validation: `validation/0.2.3-release-validation.md`
- Corrective release validation: `validation/0.2.4-release-validation.md`
- Browser proof:
  `validation/artifacts/zne-0.2.4-sources-desktop.png`,
  `validation/artifacts/zne-0.2.4-sources-desktop-snapshot.json`,
  `validation/artifacts/zne-0.2.4-sources-narrow.png`,
  `validation/artifacts/zne-0.2.4-sources-narrow-snapshot.json`

## Release path

Completed:
- Published `v0.2.3` from the repo-validated ZNE-APP-002 implementation.
- Published corrective `v0.2.4` for ZNE-594.
- Published `v0.2.5` for ZNE-APP-003 (Milestone 3).
- Published `v0.2.9` for ZNE-APP-004 (Milestone 4).
- Published `v0.3.0` for ZNE-APP-005 (Milestone 5).
- Published and installed `v0.3.3` for ZNE-APP-006 (Milestone 6 corrective line).
- Published and installed `v0.4.0` for ZNE-APP-007 (Milestone 7).
- Published and installed `v0.4.17` for the Overview UI/UX command-center refactor.
- Installed/updated through HACS.
- Restarted Home Assistant.
- Verified installed/latest version, fingerprint match, app/static routes, targeted logs, and HACS metadata.
- Validated the reversible app-native source-role write path through
  `zero_net_export.update_source_roles` using optional `battery_soc_entity`,
  then restored it to unset.
- Recorded validation evidence and updated release status.

Remaining:
- Capture focused installed proof that `ZNE-597` Battery Power/source-reading
  units display normalized watts as `W`.
- Capture v0.4.0 browser proof if that historical evidence is still useful;
  later app browser proof exists for subsequent releases.
- Define the next app workflow slice and acceptance criteria before new design
  or code.
- Keep the OpenClaw Workboard aligned every turn.

## Risks

- Runtime/source-health state should be rechecked before each workflow slice;
  `v0.4.15` validation observed transient/source availability blockers during
  restart recovery windows, separate from the promotion fix.
- ZNE-595 recorder attribute warnings are fixed and live validated in `v0.4.12`;
  keep scanning logs after future releases for recurrence.
- ZNE-599 unmanaged-candidate promotion is fixed and live validated in
  `v0.4.15`.
- ZNE-596 Sources app SOC display is fixed and live validated in `v0.4.1`.
- ZNE-594 is released/live-validated in `0.2.4`; continue watching logs for
  recurrence while broader app workflow validation proceeds.
- Live validation must not use direct Home Assistant file-backend deployment.
- Future app work must stay inside the accepted Home Assistant app/custom-panel feasibility path.
- Milestone 6 implementation requires careful handling of log capture (either
  wrapping logger calls or using a custom handler) and sensitive data filtering.
