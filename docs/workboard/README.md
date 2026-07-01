# Zero Net Export Workboard

Last updated: 2026-07-01

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

Current release: `v0.2.5`.

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
- Repo `main` is synced with `origin/main`.

## Known Bugs

Active/high-signal items:
- ZNE-594: released/live-validated fixed in `0.2.4`; continue watching logs for recurrence.
- ZNE-APP-002: released/live-validated; installed desktop/narrow browser proof is captured.
- Runtime control limitation: validation Home Assistant instance still has source-health warnings and managed-device readiness gaps, so runtime control is not yet fully product-ready.

Historical fixed bugs remain tracked in `docs/BUGS.md`.

## Feature Backlog

Near-term:
- Decide whether Milestone 3 still requires bulk priority adjustment, or move
  it to a later milestone.
- Resolve source-health warnings enough to make runtime readiness actionable.
- Continue app milestones for managed-device onboarding/editing, controls, runtime visibility, diagnostics/support, and multi-plan separation.

Deferred / not current focus:
- ZNE-FR-009 and ZNE-FR-010 native managed-device work were repo/release-prepped for `0.1.110` but are no longer the primary roadmap while app work is active.

## Next Development Steps

1. Decide whether bulk priority adjustment remains required before closing
   Milestone 3, or move it to a later milestone.
2. Read-only inspect current live source-health warnings and managed-device readiness blockers.
3. Use the live evidence to select the next app milestone or corrective release.

## Blockers And Risks

- Browser/node navigation path was previously unavailable, blocking Sources screenshot proof.
- Browser proof path is now working through the OpenClaw browser CLI; keep using screenshot/snapshot evidence for app-facing workflow changes.
- The current OpenClaw Workboard CLI can create/list/show cards, but this build does not expose an edit command for existing cards; detailed state updates may need repo Workboard docs plus new focused UI cards until card editing is available.
- Runtime control remains limited until source-health warnings and managed-device readiness are resolved.
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

Current Sources milestone completion: complete for the accepted `ZNE-APP-002` scope.

Application MVP completion: about 76%. The app shell, managed-device slices,
controls slice, Sources workflow, release path, backend write proof, installed
Sources browser proof, and live-validated Managed Devices fleet controls exist.
Remaining MVP work is mainly the Milestone 3 bulk-priority scope decision,
runtime/source-health readiness, diagnostics/support polish, and completing the
next app workflow slices.

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

## OpenClaw UI Cards

- `72ed354f` - `ZNE: Sources browser proof captured` - done.
- `7f983131` - `ZNE: Define next app milestone` - ready.
- `a42c2107` - `ZNE: Milestone 3 Stage 2 repo validated` - done.
- `a8048485` - `ZNE: Milestone 3 populated fleet live proof` - ready; proof now recorded in repo docs.
- `fe67044b-fd94-4529-b8f4-455e94f0639a` - `ZNE: Decide Milestone 3 bulk priority scope` - ready.
