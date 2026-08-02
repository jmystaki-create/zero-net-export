# project_status.md

project_name: zero-net-export
status: active_managed_devices_uiux
last_modified: 2026-08-02

## Active Scope

Managed Devices UI/UX load-dashboard refactor is repo-validated and approved for release/live validation.

The user requirement is that managed devices should publish/display the watts they consume, and the Managed Devices tab should include a dashboard covering net load, total managed load, enabled managed load, disabled managed load, active managed load, and load currently available to ZNE control.

## Current Baseline

- Latest public release: `v0.4.17`
- Current release candidate: `v0.4.18`
- Live Home Assistant/HACS installed version before this new scope: `v0.4.17`
- Delivery path: GitHub release and HACS install
- Primary product surface: Home Assistant application sidebar app/custom panel
- Previous Overview UI/UX batch: completed/released/live validated

## Active Workboard

- Workboard: `docs/workboard/README.md`
- Active cards: `WB-ZNE-MDUIUX-001` through `WB-ZNE-MDUIUX-010`
- Feasibility: `validation/zne-managed-devices-load-dashboard-feasibility.md`
- Repo validation: `validation/zne-managed-devices-load-dashboard-implementation.md`

## Live Evidence

Fresh API evidence from `sensor.managed_devices_overview` showed 2 managed devices, 1 enabled, 1 disabled, 2405 W nominal managed load, and a disabled active `Lounge Room - Heated Floor` with 2400 W nominal power and no measured current watt reading.


## Historical Baseline Continuity

- Milestone 7: Multi-Plan And Service Separation remains completed release history.
- Last milestone baseline status before this Managed Devices UI/UX scope: `repo_validated`.
- Multi-plan services continue using selected `entry_id` payloads.
- The previous milestone release baseline includes `v0.3.3`.
- Delivery remains GitHub/HACS.

## Validation Plan

- Frontend syntax check
- Focused managed-devices tests
- Full unit test discovery before release
- Browser proof after HACS install/restart for desktop and narrow Managed Devices layouts
- Live API/entity proof for installed version and managed load data

## Repo Validation Evidence

- Frontend syntax check passed.
- Focused Managed Devices panel tests passed: `28 passed`.
- Python compile check passed.
- Full unittest discovery passed: `Ran 644 tests ... OK`.
- `git diff --check` passed.

Remaining validation is release/HACS install, Home Assistant restart, live desktop/narrow browser proof, and logs/API proof for installed `v0.4.18`.

## Risks

- Must label measured vs estimated watts clearly.
- Must not change planner/control behavior in the first UI pass.
- Must preserve bulk/per-row controls, confirmation gates, candidate review/promotion, plan context, and Diagnostics.
- Backend aggregate sensors were reviewed and are not needed for this release because the sidebar app can derive the dashboard from existing payloads without adding recorder-visible entities.
