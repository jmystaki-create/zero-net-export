# Roadmap

Last updated: 2026-07-01

## Current milestone

### ZNE-APP-002 - App-native Sources workflow

Status: repo validated, pending GitHub/HACS live validation.

Outcome:
- Operators can review source-role bindings, status, readings, age, and issues in the Zero Net Export app.
- Operators can save source-role bindings through the supported backend service path.
- Runtime setup blockers become visible and repairable from the app.

Evidence:
- Plan: `docs/ZNE_APP_MILESTONE_2_SOURCES_PLAN.md`
- Feasibility: `validation/zne-app-milestone-2-sources-feasibility.md`
- Repo validation: `validation/zne-app-milestone-2-sources-implementation.md`

Next gate:
- Release and live-validate as `v0.2.3` through GitHub/HACS only.
- Validate Home Assistant install version, fingerprint, logs, app routes, browser UI, and a safe reversible source-role write if a safe mapping is approved.

## Release path

1. Publish `v0.2.3` from the repo-validated ZNE-APP-002 implementation.
2. Install/update through HACS.
3. Restart Home Assistant.
4. Verify installed/latest version, fingerprint match, app/static routes, and targeted logs.
5. Capture desktop and narrow browser proof for the Sources workflow.
6. Record validation evidence and update release status.

## Risks

- Runtime control remains blocked until required source roles are configured.
- Live validation must not use direct Home Assistant file-backend deployment.
- Future app work must stay inside the accepted Home Assistant app/custom-panel feasibility path.
