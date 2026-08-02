# Roadmap

Last updated: 2026-08-02

## Status

Active: Managed Devices UI/UX load-dashboard release/live validation.

## Current Roadmap Item

### Managed Devices Load-Aware Fleet Console

Goal: make the Managed Devices tab show controllable load impact in watts, not only inventory counts and status indicators.

Scope:

- Add a Managed Load Dashboard.
- Show per-device load watts with measured/estimated/nominal semantics.
- Escalate disabled-but-active managed loads.
- Split the misleading `Power` traffic-light column into `Load` and `State`.
- Show candidate load only when reliable watt metadata exists; otherwise require confirmation during promotion.
- Avoid backend aggregate sensors for this release because existing app payloads support frontend-derived metrics.
- Preserve all existing workflows and confirmation gates.
- Validate responsive desktop/narrow layouts and release through HACS only after approval.

Workboard cards: `WB-ZNE-MDUIUX-001` through `WB-ZNE-MDUIUX-010`.

## Completed Baseline

- `v0.4.17` is the latest public release and installed Home Assistant/HACS version before this release candidate.
- `v0.4.18` is the current release candidate.
- The Overview UI/UX command-center refactor is released and live validated.
- Historical app milestones, bug fixes, feature requests, release validation, and browser proof remain preserved in project documentation and git history.

## Evidence

- Workboard: `docs/workboard/README.md`
- Review: `ui_ux_review.md`
- Feasibility: `validation/zne-managed-devices-load-dashboard-feasibility.md`
- Repo validation: `validation/zne-managed-devices-load-dashboard-implementation.md`
