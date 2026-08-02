# project_status.md

project_name: zero-net-export
status: released_operator_tabs_uiux
last_modified: 2026-08-02

## Active Scope

Operator tab UI/UX redesign is released as v0.4.20 and live-validated through GitHub/HACS install, HA restart, API state checks, and desktop/mobile browser proof.

The approved tab order is:

`Overview -> Managed Devices -> Sources -> Controls -> Runtime -> Diagnostics -> Settings`

Sources should explain measurement trust and control impact. Controls should explain what Zero Net Export is allowed to do and show safety guards. Runtime should explain what the controller is doing now and what it just did.

Managed Devices watt dashboard/workflows from the previous release candidate must be preserved.

## Current Baseline

- Latest public release: `v0.4.20`
- Current development scope: operator tabs UI/UX redesign
- Live Home Assistant/HACS installed version after this scope: `v0.4.20`
- Delivery path: GitHub release and HACS install
- Primary product surface: Home Assistant application sidebar app/custom panel
- Previous Overview UI/UX batch: completed/released/live validated
- Previous Managed Devices UI/UX batch: completed/released/live validated enough to be the current baseline

## Active Workboard

- Workboard: `docs/workboard/README.md`
- Active cards: `WB-ZNE-TABUX-001` through `WB-ZNE-TABUX-007`
- Feasibility: `validation/zne-operator-tabs-redesign-feasibility.md`
- Repo validation: `validation/zne-operator-tabs-redesign-implementation.md`

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
- Focused frontend/workflow tests
- Full unit test discovery before release
- Browser proof after HACS install/restart for desktop and narrow layouts covering tab order, Sources, Controls, Runtime, and preserved Managed Devices dashboard
- Live API/entity proof for installed version and current source/runtime/managed-load data

## Repo Validation Evidence

- Frontend syntax check passed.
- Focused frontend/workflow tests passed: `31 passed`.
- Full unittest discovery passed: `Ran 647 tests ... OK`.
- `git diff --check` passed.

Release validation complete: GitHub release v0.4.20 published, HACS update installed, Home Assistant restarted, installed-version sensor reports 0.4.20, and desktop/mobile browser proof was captured.

## Risks

- Must label measured vs estimated watts clearly.
- Must not change planner/control behavior in the first UI pass.
- Must preserve bulk/per-row controls, confirmation gates, candidate review/promotion, plan context, and Diagnostics.
- Backend aggregate sensors were reviewed and are not needed for this release because the sidebar app can derive the dashboard from existing payloads without adding recorder-visible entities.
- Must avoid making sparse tabs denser by adding raw diagnostics; operator tabs should summarize, and Diagnostics should retain raw details.
