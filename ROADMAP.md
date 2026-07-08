# Roadmap

Last updated: 2026-07-08

## Workboard

The maintained project Workboard lives at `docs/workboard/README.md`.
Initial cards are under `docs/workboard/cards/` and cover project charter,
architecture inventory, bug register, MVP definition, next 10 implementation
tasks, blockers/unknowns, testing/validation plan, and weekly status report.
The OpenClaw Workboard UI is the active visible board for ZNE. Check and update
it every ZNE work turn when status, validation state, blockers, next actions,
or release readiness changes. Current relevant UI cards:
`72ed354f` - `ZNE: Sources browser proof captured` (done),
`7f983131` - `ZNE: Define next app milestone` (done),
`a42c2107` - `ZNE: Milestone 3 Stage 2 repo validated` (done),
`a8048485` - `ZNE: Milestone 3 populated fleet live proof` (done),
`fe67044b-fd94-4529-b8f4-455e94f0639a` -
`ZNE: Decide Milestone 3 bulk priority scope` (superseded; deferred),
`348000d4` - `ZNE: Milestone 3 closed` (done),
`06b5d15f` - `ZNE: Define bulk priority adjustment scope for later milestone` (ready),
`8b148624` - `ZNE: Source Health & Runtime Blocker Resolution` (done),
`f8d93513-ed96-4228-b1c8-0885e608544d` -
`ZNE: Milestone 4 live baseline captured` (done),
`a1b2c3d4` - `ZNE: Milestone 5 Runtime Visibility - Manual Override` (done),
`zne-app-006` - `ZNE: Milestone 6 Diagnostics & Support Polish` (released/live smoke validated),
`workboard-focused` - `ZNE: v0.3.3 HACS/browser validation passed` (done),
`workboard-focused` - `ZNE: complete v0.3.3 service/action validation` (done),
`workboard-focused` - `ZNE: Milestone 7 Multi-Plan And Service Separation` (released/live validated via API/static/service checks),
`36a26d60` - `ZNE: Fix SOC source status display in Sources app` (done; released/live validated in `v0.4.1`),
`workboard-focused` - `ZNE: Overview console live metrics` (done; released/live validated in `v0.4.2`),
`workboard-focused` - `ZNE: Fix oversized recorder-backed entity attributes after v0.4.0` (ready; next).
Milestone 3 (Managed Devices Fleet Control) feasibility is accepted, Stage 2 is
released as `v0.2.5`, and installed empty-fleet plus populated `light.7th`
browser proof is recorded. References:
`validation/zne-app-milestone-3-feasibility.md`,
`docs/ZNE_APP_MILESTONE_3_PLAN.md`,
`validation/zne-app-milestone-3-stage-2-validation.md`,
`validation/0.2.5-release-validation.md`, and repo Workboard card
`WB-ZNE-009-milestone-3-managed-devices-fleet-control.md` (Done).

**Latest**: `v0.4.2` is published, installed through HACS, restarted, and
live/browser validated for the Overview console live-metrics slice. The
installed version sensor reports `0.4.2`; the Overview Reconciliation Status
card shows live freshness, Source Power, Battery Power, Confidence, and
stale/source-blocker context. Evidence:
`validation/0.4.2-release-validation.md` and
`validation/artifacts/v0.4.2-overview-console-live.png`.

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
- Fix oversized recorder-backed entity attributes found in the v0.4.0 and
  v0.4.2 log reviews.

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
- Installed/updated through HACS.
- Restarted Home Assistant.
- Verified installed/latest version, fingerprint match, app/static routes, targeted logs, and HACS metadata.
- Validated the reversible app-native source-role write path through
  `zero_net_export.update_source_roles` using optional `battery_soc_entity`,
  then restored it to unset.
- Recorded validation evidence and updated release status.

Remaining:
- Fix post-v0.4.0 recorder attribute-size warnings.
- Capture v0.4.0 browser proof when browser tooling is available.
- Keep the OpenClaw Workboard aligned every turn.

## Risks

- Runtime control remains limited until source-health warnings and managed
  device readiness are resolved in the validation Home Assistant instance.
- v0.4.0 log review found many Zero Net Export entity attributes exceeding Home
  Assistant's 16 KB recorder attribute limit; trim recorder-backed attributes
  and move bulky detail to diagnostics/app API surfaces.
- v0.4.0 Sources app display had a SOC slug mismatch: backend status is exposed
  as `battery_state_of_charge`, while the frontend derived `battery_soc`. Repo
  fix exists as ZNE-596; live validation is pending.
- ZNE-594 is released/live-validated in `0.2.4`; continue watching logs for
  recurrence while broader app workflow validation proceeds.
- Live validation must not use direct Home Assistant file-backend deployment.
- Future app work must stay inside the accepted Home Assistant app/custom-panel feasibility path.
- Milestone 6 implementation requires careful handling of log capture (either
  wrapping logger calls or using a custom handler) and sensitive data filtering.
