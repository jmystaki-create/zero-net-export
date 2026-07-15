# Zero Net Export Workboard

Last updated: 2026-07-15

This workboard is the operational project view for Zero Net Export. It summarizes what exists, what is broken, what is next, and how far the project is from a useful Home Assistant application MVP.

## Operating Rule

The OpenClaw Workboard is wired into the Zero Net Export project and must be checked and updated on every ZNE work turn. If project state, validation state, blockers, next actions, or release readiness change, update the relevant OpenClaw Workboard card and keep these repo workboard files, `PROJECT_STATUS.md`, and `ROADMAP.md` aligned. If no Workboard card update is needed, the turn summary must say why.

## Project Scope

Zero Net Export is a Home Assistant application backed by the existing `zero_net_export` custom integration backend.

In scope:
- Home Assistant sidebar application/panel as the primary operator UI.
- Integration backend for config entries, coordinator/runtime state, source validation, planner/executor control logic, managed-device model, entities, services, repairs, notifications, diagnostics, and install validation.
- App workflows for overview/readiness, sources, managed devices, controls, runtime, diagnostics/support, install validation, and multi-plan/service separation.
- GitHub/HACS-only release and live validation path.

Primary references:
- `CONSTRAINTS.md`
- `PROJECT_STATUS.md`
- `ROADMAP.md`
- `docs/ZNE_APPLICATION_DIRECTION.md`
- `docs/ZNE_APP_MILESTONE_2_SOURCES_PLAN.md`
- `validation/0.2.5-release-validation.md`

## Goals And Objectives

- Make Zero Net Export usable as an app, not a collection of Home Assistant native device pages.
- Make source readiness visible and repairable inside the app.
- Keep all writes scoped to the selected Zero Net Export config entry.
- Preserve source/original Home Assistant devices and entities when managing or removing ZNE records.
- Prove every release through repo validation, HACS install/update, Home Assistant restart, fingerprint checks, route checks, browser proof, and targeted logs.

## Non-Goals

- No Home Assistant core/frontend patching.
- No native Home Assistant page/card/row injection for primary workflows.
- No external web UI outside Home Assistant.
- No direct live Home Assistant storage mutation for validation.
- No runtime-control readiness claim while source-health and managed-device readiness blockers remain unresolved.
- No revival of superseded native-device-page-first roadmap work unless it directly supports the app direction.

## Architecture / Current State

Current release: `v0.4.15` (`ZNE-599` Managed Devices promotion regression
fix, installed through HACS and live validated 2026-07-15).
Next: capture the focused installed `ZNE-597` Battery Power/source-reading unit
proof, then choose the next app workflow slice.

Current state:
- `v0.2.3` delivered the app-native Sources workflow and `zero_net_export.update_source_roles`.
- `v0.2.4` fixed ZNE-594 next-step sensor state overflow and is live-validated.
- `v0.2.5` delivered ZNE-APP-003 Managed Devices fleet filters, sorting,
  enhanced columns, row selection, and confirmation-gated bulk enable/disable
  actions.
- Source-role write proof passed through the supported backend service path.
- Browser proof for ZNE-APP-002 is captured on installed `0.2.4` with desktop and narrow/mobile viewport artifacts.
- Managed Devices browser proof is captured on installed `0.2.5` for both
  empty-fleet and populated `light.7th` states, including UI-driven bulk
  enable/disable with final disabled state.
- `v0.2.9` completed Milestone 4 source-health/runtime readiness: the live
  validation target now reports `ready`, validated sources, one usable managed
  device, acceptable reconciliation, and clean installed app browser proof.
- `v0.3.0` completed Milestone 5 runtime visibility and manual override.
- `v0.3.3` supersedes `v0.3.1-fix` for Milestone 6 diagnostics/support polish.
  HACS/app browser validation passed: app header shows `Version 0.3.3 - 1
  plan`, backend connected, Overview ready, Diagnostics tab renders, installed
  version is `0.3.3`, and diagnostics service/action validation passed through
  the Home Assistant REST API.
- ZNE-APP-007 is released/live validated as `v0.4.0`: shared backend entry resolver, app selected
  plan context, and selected `entry_id` payloads for source, managed-device,
  executor, diagnostics, and repair actions are implemented.
- v0.4.0 live validation confirmed installed/latest HACS metadata, installed
  version sensor `0.4.0`, app/static routes returning HTTP 200, `entry_id`
  service fields, and explicit scoped service calls for export, repair,
  pause, and resume.
- `v0.4.1` fixed and live-validated the Sources app Battery state of charge row.
- `ZNE-FR-011` and `ZNE-FR-012` are released/live validated in `v0.4.2`: the Overview
  Reconciliation Status card now has local freshness re-rendering, resolves
  Source Power/Battery Power/Confidence from existing runtime/source entities,
  and shows stale/source-blocker context. GitHub release, HACS install, restart,
  fingerprint, browser proof, and log review are recorded in
  `validation/0.4.2-release-validation.md`.
- `ZNE-FR-013` is released/live validated in `v0.4.3`: the Overview
  Readiness card now has dedicated formatting, current-focus context, and
  issue cards that explain what is wrong and how to resolve it.
- `ZNE-FR-014` is released/live validated in `v0.4.5`: the Overview
  Readiness card now replaces dense command-center/device queue strings with a
  short verdict, `Do this first`, concise issue facts, and ordered resolution
  steps.
- `ZNE-597` is released in `v0.4.4` with a focused validation follow-up: live Battery discharge power mapping was repaired
  from the cumulative Anker total sensor to `sensor.x1_p6k_us_s_discharge_power`;
  repo-side normalized source-reading unit presentation passed validation and
  still needs a dedicated installed UI/unit proof.
- `v0.4.11` fixed and live-validated the Managed Devices `Review & promote`
  visible workflow regression.
- `ZNE-595` is released/live validated in `v0.4.12`: recorder-backed entity
  attributes now expose compact summaries while bulky action history/source
  diagnostics remain on diagnostics/app surfaces. Post-restart max observed ZNE
  attribute payload was `10483` bytes, and the reviewed post-restart log window
  had no ZNE recorder attribute-size warnings.
- `ZNE-599` is released/live validated in `v0.4.15`: the unmanaged-candidate
  promotion workflow now preserves confirmation state across app re-renders,
  accepts UI numeric service payloads, promotes through
  `zero_net_export.promote_managed_device`, and renders the promoted numeric
  priority in the Fleet List without frontend errors. Evidence:
  `validation/0.4.15-release-validation.md`.

## Known Bugs

Active/high-signal items:
- ZNE-599: released/live-validated in `v0.4.15`; Managed Devices
  `Review & promote` now commits a confirmed unmanaged candidate into the
  managed Fleet List through the supported promotion service. Live proof
  promoted `switch.ac_outlet_1` to managed key `lounge_room_heated_floor` with
  `enabled: false`, preserved the original entity, removed it from the
  unmanaged queue, and showed a clean fresh browser console.
- ZNE-597: released in `v0.4.4` with focused unit-display proof pending; Battery Power used a cumulative Anker total sensor and
  displayed normalized watts as kW. Live source-role repair now binds discharge
  power to `sensor.x1_p6k_us_s_discharge_power`, with ZNE status `ready` and
  reconciliation error `0 W`; code shipped in `v0.4.4`, and the remaining
  action is focused installed proof that units display as normalized watts.
- ZNE-596: released_live_validated in `v0.4.1`; the Sources app
  showed Battery state of charge as missing because the frontend derived
  `battery_soc_status` while the backend exposes `battery_state_of_charge_status`.
  Live API/browser validation confirmed the app now shows `status: ok`, binding
  `sensor.x1_p6k_us_s_state_of_charge`, and the current reading.
- ZNE-595: released/live-validated in `v0.4.12`; many recorder-backed entity
  attributes exceeded Home Assistant's 16 KB attribute limit after `v0.4.0`.
- ZNE-594: released/live-validated fixed in `0.2.4`; continue watching logs for recurrence.
- ZNE-APP-002: released/live-validated; installed desktop/narrow browser proof is captured.
- Runtime control readiness is now proven on the validation Home Assistant
  instance with one disposable managed device. Broader product readiness still
  depends on future workflow scope and real-fleet validation.

Historical fixed bugs remain tracked in `docs/BUGS.md`.

## Feature Backlog

Near-term:
- Capture the focused installed `ZNE-597` Battery Power/unit proof.
- Choose the next app workflow slice.
- Capture v0.4.0 browser visual proof once the OpenClaw managed browser host is available.
- Define deferred bulk priority adjustment scope in a later milestone.
- Continue app milestones for managed-device onboarding/editing, controls, runtime visibility, diagnostics/support, and multi-plan separation.

Deferred / not current focus:
- ZNE-FR-009 and ZNE-FR-010 native managed-device work were repo/release-prepped for `0.1.110` but are no longer the primary roadmap while app work is active.

## Next Development Steps

**Immediate**: Capture the read-only installed `ZNE-597` Battery
Power/source-reading unit proof on `v0.4.15`.

1. Capture the focused installed `ZNE-597` Battery Power/unit proof.
2. Decide when to scope deferred bulk priority adjustment.
3. Continue app workflow slices for diagnostics/support, runtime visibility,
   controls, and multi-plan separation.

## Blockers And Risks

- Browser/node navigation path is currently working through the OpenClaw browser
  node and was used for `v0.4.2` browser proof. Browser visual proof for
  `v0.4.0` remains historically pending.
- The current OpenClaw Workboard CLI can create/list/show cards, but this build does not expose an edit command for existing cards; detailed state updates may need repo Workboard docs plus new focused UI cards until card editing is available.
- Current runtime status is `degraded` due to power-source reconciliation; track
  separately from Milestone 6 diagnostics service validation.
- ZNE-595 recorder attribute warnings are fixed and live validated in `v0.4.12`;
  continue scanning logs after future releases for recurrence.
- ZNE-599 is fixed/live validated in `v0.4.15`; keep watching the
  unmanaged-candidate onboarding path during future app workflow work.
- Keep using GitHub/HACS-only validation for releases; no direct component
  deployment.
- Live validation must continue through GitHub/HACS, not direct file deployment.
- Future app work must stay inside the accepted Home Assistant app/custom-panel feasibility path.
- Project docs are large and historical; stale native-device-page docs can mislead future work if `CONSTRAINTS.md` source-of-truth order is ignored.

## Definition Of Done

A Workboard card is done only when:
- Acceptance criteria are met.
- Required evidence exists and is linked.
- Repo or live validation was actually run when required.
- Project status and roadmap are updated if project state changed.
- Release impact is reflected in `CHANGELOG.md` when user-facing behavior changed.

## Completion Estimate

Current Milestone 7 completion: released/live validated via API/static/service
checks as `v0.4.0`; browser visual proof pending because browser tooling is
unavailable.

Application MVP completion: about 88%. The app shell, managed-device slices,
controls slice, Sources workflow, release path, backend write proof, installed
Sources browser proof, live-validated Managed Devices fleet controls, and
Milestone 4 source-health/runtime readiness exist. Milestone 6 diagnostics UI
is installed and smoke validated. Remaining MVP work is mainly service/action
validation, completing the next app workflow slices, broader real-fleet/runtime
validation, and later bulk-priority scope definition.

Full product completion: not yet estimable from current evidence because runtime control readiness and future app milestone scope still need tighter acceptance criteria.

## Cards

- [WB-ZNE-001 Project charter](cards/WB-ZNE-001-project-charter.md)
- [WB-ZNE-002 Architecture inventory](cards/WB-ZNE-002-architecture-inventory.md)
- [WB-ZNE-003 Bug register](cards/WB-ZNE-003-bug-register.md)
- [WB-ZNE-004 MVP definition](cards/WB-ZNE-004-mvp-definition.md)
- [WB-ZNE-005 Next 10 implementation tasks](cards/WB-ZNE-005-next-10-implementation-tasks.md)
- [WB-ZNE-006 Blockers and unknowns](cards/WB-ZNE-006-blockers-and-unknowns.md)
- [WB-ZNE-007 Testing and validation plan](cards/WB-ZNE-007-testing-and-validation-plan.md)
- [WB-ZNE-008 Weekly status report](cards/WB-ZNE-008-weekly-status-report.md)
- [WB-ZNE-010 Overview console live metrics](cards/WB-ZNE-010-overview-console-live-metrics.md)
- [WB-ZNE-011 Overview Readiness clarity](cards/WB-ZNE-011-overview-readiness-clarity.md)
- [WB-ZNE-012 Battery Power source mapping](cards/WB-ZNE-012-battery-power-source-mapping.md)
- [WB-ZNE-013 Overview Readiness message design](cards/WB-ZNE-013-overview-readiness-message-design.md)
- [WB-ZNE-014 Recorder attribute budget](cards/WB-ZNE-014-recorder-attribute-budget.md)
- [WB-ZNE-015 Promotion confirmation regression](cards/WB-ZNE-015-promotion-confirmation-regression.md)

## OpenClaw UI Cards

- `72ed354f` - `ZNE: Sources browser proof captured` - done.
- `7f983131` - `ZNE: Define next app milestone` - done.
- `a1b2c3d4` - `ZNE: Milestone 5 Runtime Visibility - `7f983131` - `ZNE: Define next app milestone` - ready. Manual Override` - ready.
- `a42c2107` - `ZNE: Milestone 3 Stage 2 repo validated` - done.
- `a8048485` - `ZNE: Milestone 3 populated fleet live proof` - ready; proof now recorded in repo docs.
- `fe67044b-fd94-4529-b8f4-455e94f0639a` - `ZNE: Decide Milestone 3 bulk priority scope` - superseded; deferred.
- `348000d4` - `ZNE: Milestone 3 closed` - done.
- `06b5d15f` - `ZNE: Define bulk priority adjustment scope for later milestone` - ready.
- `8b148624` - `ZNE: Source Health & Runtime Blocker Resolution` - done.
- `f8d93513-ed96-4228-b1c8-0885e608544d` - `ZNE: Milestone 4 live baseline captured` - done.
- `workboard-focused` - `ZNE: v0.3.3 HACS/browser validation passed` - done.
- `workboard-focused` - `ZNE: complete v0.3.3 service/action validation` - done.
- `workboard-focused` - `ZNE: Milestone 7 Multi-Plan And Service Separation` - released/live validated via API/static/service checks.
- `workboard-focused` - `ZNE: Overview console live metrics` - done; released/live validated in `v0.4.2`.
- `workboard-focused` - `ZNE: Overview Readiness clarity` - done; released/live validated in `v0.4.3`.
- `workboard-focused` - `ZNE: Battery Power source mapping` - released in `v0.4.4`; focused installed unit-display proof still needed.
- `2fbac9e1-3c0c-4198-80ba-396b729f2f9e` - `ZNE: Fix unmanaged candidate promotion confirmation` - done; released/live validated in `v0.4.15`; tracked as `ZNE-599`.
- `workboard-focused` - `ZNE: Overview Readiness message design` - done; released/live validated in `v0.4.5`.
- `workboard-focused` - `ZNE: Fix oversized recorder-backed entity attributes after v0.4.0` - done; released/live validated in `v0.4.12`.
