# Roadmap

Last updated: 2026-07-01

## Workboard

The maintained project Workboard lives at `docs/workboard/README.md`.
Initial cards are under `docs/workboard/cards/` and cover project charter,
architecture inventory, bug register, MVP definition, next 10 implementation
tasks, blockers/unknowns, testing/validation plan, and weekly status report.

## Current milestone

### ZNE-APP-002 - App-native Sources workflow

Status: released as `v0.2.3`; GitHub/HACS install live-validated with browser proof gap.

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

Next gate:
- Capture browser proof for the installed `0.2.3` Sources workflow.

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
- Capture desktop and narrow browser proof for the Sources workflow.

## Risks

- Runtime control remains limited until source-health warnings and managed
  device readiness are resolved in the validation Home Assistant instance.
- ZNE-594 is released/live-validated in `0.2.4`; continue watching logs for
  recurrence while broader app workflow validation proceeds.
- Live validation must not use direct Home Assistant file-backend deployment.
- Future app work must stay inside the accepted Home Assistant app/custom-panel feasibility path.
