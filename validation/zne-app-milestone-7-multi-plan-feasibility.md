# ZNE-APP-007 Multi-Plan And Service Separation Feasibility

Date: 2026-07-07

Status: ACCEPTED

## Target Environment

- Runtime: Home Assistant 2026.6.x validation instance.
- Delivery: GitHub release installed through HACS.
- Backend: existing Zero Net Export custom integration, config entries, coordinator, entities, and services.
- Frontend: existing Home Assistant sidebar custom panel served from `custom_components/zero_net_export/frontend/`.

## Feasibility Findings

### App Can Read Multiple Config Entries

Finding: Supported.

Evidence:

- The current app panel is already registered through the integration and receives Home Assistant state plus panel bootstrap data.
- Existing backend code stores coordinators under `hass.data[DOMAIN][entry.entry_id]`.
- Existing service patterns can select an entry-specific coordinator from `hass.data[DOMAIN]`.

Constraint:

- If more than one Zero Net Export config entry exists, the app must expose the selected plan/service context explicitly instead of relying on a single implicit entry.

### Backend Can Scope Actions To A Selected Entry

Finding: Supported with implementation discipline.

Evidence:

- `services.yaml` already defines optional `entry_id` for `export_diagnostics`.
- Existing services such as source-role updates and managed-device updates use Home Assistant service calls and can be extended or normalized to require/select a target entry.
- Existing coordinator state is already entry-specific.

Constraint:

- Any write action must resolve exactly one entry before changing sources, managed devices, executor state, diagnostics, or repair state. Ambiguous multi-entry requests must fail safely.

### Frontend Can Expose Plan/Service Context

Finding: Supported.

Evidence:

- The current app shell already renders navigation tabs and shows `Version 0.3.3 - 1 plan`.
- Existing tab rendering can add a plan selector/header context without changing the delivery surface.
- The app can filter displayed state by entry metadata once backend state exposes plan/service identity consistently.

Constraint:

- The app must avoid implying that global status applies to every plan when only one selected plan is being viewed.

### Validation Can Prove Isolation

Finding: Supported.

Evidence:

- Existing release validation already uses HA API, HACS install, restart, app route checks, browser proof, and targeted logs.
- Service/action proof can be run through the Home Assistant REST API with the stored validation token.

Constraint:

- Live multi-plan isolation proof requires either two existing ZNE config entries or a safe temporary second entry created through supported Home Assistant config/subentry flow. If a second live plan is not available, repo tests must cover multi-entry behavior and live validation should explicitly record the limitation.

## Unsupported Paths

- Direct Home Assistant storage mutation for creating or editing plans.
- Any direct file deployment to the live integration for validation.
- Global app actions that silently choose the first config entry when multiple entries exist.

## Acceptance Criteria For Implementation

- The app shows the selected plan/service context.
- If multiple ZNE entries exist, the operator can switch context.
- Sources, managed devices, controls, runtime state, diagnostics, and repair/export actions are scoped to the selected entry.
- Write actions fail with a clear message when no entry or multiple entries are ambiguous.
- Validation proves no cross-entry source/device/control mutation for at least repo-level tests, and live proof if a safe second entry exists.

## Decision

Milestone 7 is feasible within the current Home Assistant app/custom-panel and integration service architecture.
