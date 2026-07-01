# Roadmap

Last updated: 2026-07-01

## Current milestone

### ZNE-APP-002 - App-native Sources workflow

Status: released as `v0.2.3`; GitHub/HACS install live-validated with browser/write proof gaps.

Outcome:
- Operators can review source-role bindings, status, readings, age, and issues in the Zero Net Export app.
- Operators can save source-role bindings through the supported backend service path.
- Runtime setup blockers become visible and repairable from the app.

Evidence:
- Plan: `docs/ZNE_APP_MILESTONE_2_SOURCES_PLAN.md`
- Feasibility: `validation/zne-app-milestone-2-sources-feasibility.md`
- Repo validation: `validation/zne-app-milestone-2-sources-implementation.md`
- Release validation: `validation/0.2.3-release-validation.md`

Next gate:
- Capture browser proof for the installed `0.2.3` Sources workflow.
- With approval, perform the safe reversible source-role write proof using
  optional `battery_soc_entity` on config entry `01KWC2HX12V4P0Q82A0WM69EHV`
  and candidate `sensor.x1_p6k_us_s_state_of_charge`, then restore it to
  unset.

## Release path

Completed:
- Published `v0.2.3` from the repo-validated ZNE-APP-002 implementation.
- Installed/updated through HACS.
- Restarted Home Assistant.
- Verified installed/latest version, fingerprint match, app/static routes, targeted logs, and HACS metadata.
- Recorded validation evidence and updated release status.

Remaining:
- Capture desktop and narrow browser proof for the Sources workflow.
- Perform the approved reversible source-role write proof for optional
  `battery_soc_entity`, then restore the previous unset state.

## Risks

- Runtime control remains blocked until required source roles are configured.
- Live validation must not use direct Home Assistant file-backend deployment.
- Future app work must stay inside the accepted Home Assistant app/custom-panel feasibility path.
