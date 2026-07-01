# Roadmap

Last updated: 2026-07-01

## Workboard

The maintained project Workboard lives at `docs/workboard/README.md`.
Initial cards are under `docs/workboard/cards/` and cover project charter,
architecture inventory, bug register, MVP definition, next 10 implementation
tasks, blockers/unknowns, testing/validation plan, and weekly status report.
The OpenClaw Workboard UI is the active visible board for ZNE. Check and update
it every ZNE work turn when status, validation evidence, blockers, next actions,
or release readiness changes. Current relevant UI cards:
`72ed354f` - `ZNE: Sources browser proof captured` (done),
`7f983131` - `ZNE: Define next app milestone` (stale ready; superseded),
`a42c2107` - `ZNE: Milestone 3 Stage 2 repo validated` (done).
Milestone 3 (Managed Devices Fleet Control) feasibility check and plan are written
awaiting acceptance: `validation/zne-app-milestone-3-feasibility.md` and
`docs/ZNE_APP_MILESTONE_3_PLAN.md`. Repo Workboard card:
`WB-ZNE-009-milestone-3-managed-devices-fleet-control.md` (Ready).

**Updated:** Milestone 3 feasibility check accepted. Moving card `7f983131` to done; card `WB-ZNE-009` status updated to Doing.

**Latest:** Stage 2 (priority/readiness filters, sorting, Last Seen and Blockers columns, visible-row selection, and confirmation-gated bulk enable/disable actions) is implemented and repo-validated. Evidence: `validation/zne-app-milestone-3-stage-2-validation.md`. Live validation and browser proof are pending.

## Current milestone

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

Next gate:
- ~~Accept the Milestone 3 feasibility check in `validation/zne-app-milestone-3-feasibility.md`.~~ (Done)
- ~~Approve starting Milestone 3 (Managed Devices Fleet Control) implementation.~~ (Done)
- ~~Proceed with minimal design and implementation within the accepted feasible path.~~ (Stage 1 complete)
- Proceed with live validation and browser proof for the complete Stage 1+2 Managed Devices fleet workflow.

## Release path

Completed:
- Published `v0.2.3` from the repo-validated ZNE-APP-002 implementation.
- Published corrective `v0.2.4` for ZNE-594.
- Installed/updated through HACS.
- Restarted Home Assistant.
- Verified installed/latest version, fingerprint match, app/static routes, targeted logs, and HACS metadata.
- Verified next-step sensor states are under Home Assistant's 255-character
  state limit and post-restart logs contain no new ZNE next-step length errors.
- Validated the reversible app-native source-role write path through
  `zero_net_export.update_source_roles` using optional `battery_soc_entity`,
  then restored it to unset.
- Recorded validation evidence and updated release status.

Remaining:
- Live-validate the complete Milestone 3 Managed Devices fleet workflow and keep the OpenClaw Workboard aligned every turn.

## Risks

- Runtime control remains limited until source-health warnings and managed
  device readiness are resolved in the validation Home Assistant instance.
- ZNE-594 is released/live-validated in `0.2.4`; continue watching logs for
  recurrence while broader app workflow validation proceeds.
- Live validation must not use direct Home Assistant file-backend deployment.
- Future app work must stay inside the accepted Home Assistant app/custom-panel feasibility path.
