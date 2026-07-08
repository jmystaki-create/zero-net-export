# ZNE-FR-013 Overview Readiness Clarity

Date: 2026-07-08
Status: repo-validated pending release/live validation

## Request

Riley reported that the Overview Readiness section is unclear and poorly
formatted. The requested outcomes are:

- Structurally fix the Readiness formatting.
- Explain what the current errors are and what needs to be done to resolve them.

## Classification

Feature / UX clarity improvement for the Home Assistant application Overview.

## Target Environment Feasibility

Target environment: the existing Zero Net Export Home Assistant custom panel,
served through the already-supported `panel_custom` / static frontend path.

Supported:

- The app can restructure its own Overview HTML/CSS because it is a ZNE-owned
  custom panel.
- The app can read existing Home Assistant state and attributes through the
  provided `hass.states` object.
- Existing command-center, source-blocker, stale-source, and guard-summary
  entities already carry the error and resolution text needed for this slice.

Unsupported / excluded:

- No Home Assistant core/frontend patching.
- No native Home Assistant device-page/card injection.
- No new recorder-backed diagnostic attributes for this UX slice.

Result: feasible within the already-accepted Home Assistant app/custom-panel
architecture. No new platform capability is required.

## Acceptance Criteria

- Readiness no longer squeezes long command-center text into a narrow value
  column.
- Readiness shows concise health chips for Controller, Safe mode, and Source
  mismatch.
- Readiness has a clear current-focus area.
- Readiness lists each active issue with `What is wrong` and `How to resolve`.
- Current source blockers, source mismatch/reconciliation guidance, controls
  readiness, and managed-device queue context are visible when present.
- Desktop and narrow layouts wrap text without overlap.

## Implementation Notes

- Added a dedicated `_readinessModel()` frontend model that reads existing
  command-center/source/guard entities.
- Added `_readinessItemTemplate()` and dedicated `.zne-readiness-*` CSS.
- Kept all data sourced from existing entities; no backend schema change.
- Current live errors identified during intake:
  - `sensor.zero_net_export_status` is `degraded`.
  - `binary_sensor.zero_net_export_source_mismatch` is `on`.
  - Source blockers are active for `solar_energy` and
    `battery_discharge_power`.
  - `battery_discharge_power` is bound to
    `sensor.anker_battery_discharge_power`, which reports
    `state_class=total`; power readings should use `measurement`.
  - Reconciliation diagnostics report that power sources do not reconcile
    cleanly, with guidance to compare source signs/semantics during an obvious
    export period.

## Validation Plan

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- `python3 -m unittest tests.test_managed_devices_panel -v`
- `git diff --check`
- Browser proof after release/live install.

## Repo Validation

```text
node --check custom_components/zero_net_export/frontend/zero-net-export-app.js
OK

python3 -m unittest tests.test_managed_devices_panel -v
Ran 19 tests in 0.003s
OK
```
