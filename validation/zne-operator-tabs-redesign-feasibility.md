# Zero Net Export Operator Tabs Redesign Feasibility

Date: 2026-08-02
Scope: tab order plus Sources, Controls, and Runtime tab redesign

## Decision

Supported for frontend implementation without backend behavior changes.

The approved redesign can use the existing Home Assistant custom panel/frontend delivery model and current app-visible entities. Backend aggregate entities are not required for the first implementation pass.

## Target Environment

- Primary runtime: Home Assistant custom sidebar panel served by the Zero Net Export integration.
- Frontend module: `custom_components/zero_net_export/frontend/zero-net-export-app.js`.
- Data source: `this._hass.states` entity state cache plus panel config entries.
- Delivery path: GitHub release -> HACS install -> Home Assistant restart/load.

## Supported Findings

- Tab order is frontend-only; nav buttons are rendered in `zero-net-export-app.js`.
- Managed Devices already renders a watt-based dashboard and must remain preserved.
- Sources tab already has access to source role definitions, status/reading/age/issue-count sensor lookup helpers, source-role update inputs, selected plan context, and `zero_net_export.update_source_roles`.
- Controls tab already has access to `switch.zero_net_export_enabled`, `select.zero_net_export_mode`, policy number entities, and the existing switch/select/number service calls.
- Runtime tab already has access to reconciliation metrics, active controlled power, planned power delta, activity counters, executor state, and command failure state.
- Diagnostics already exists as the raw/support detail surface.

## Unknowns For Live Validation

- Exact narrow/mobile behavior after the denser operator layout renders inside Home Assistant.
- Whether live entities populate every optional decision/detail field; missing values must render as unknown/waiting rather than breaking layout.
- Whether the current Home Assistant theme has sufficient contrast for all status tones across desktop and mobile.

## Constraints

- No backend control behavior changes in this batch.
- Preserve Managed Devices watt dashboard, measured/estimated semantics, disabled-active alert, per-row enable/disable, bulk controls, candidate review/promotion, and destructive confirmations.
- Preserve selected-plan context and entry-scoped service behavior.
- Preserve source-role update service wiring.
- Preserve control enable, mode, and policy value service wiring.
- Preserve executor pause/resume and Diagnostics.
- Browser proof is required before release closeout.

## Validation Plan

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- Focused frontend/source tests in `tests/test_managed_devices_panel.py`
- Broader unit validation before release if the change proceeds to HACS release
- Desktop and narrow browser proof after release candidate install

