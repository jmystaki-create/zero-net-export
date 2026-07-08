# ZNE-FR-011 / ZNE-FR-012 Overview Console Live Metrics

Date: 2026-07-08
Status: repo validated pending release/live validation

## Task Classification

- Type: feature
- Scope: Zero Net Export Home Assistant application Overview console
- Requests:
  - `ZNE-FR-011`: Reconciliation Status should feel more realtime.
  - `ZNE-FR-012`: Source Power, Battery Power, and Confidence should be meaningful and visible.

## Acceptance Criteria

- Reconciliation Status refreshes predictably without excessive Home Assistant API load.
- The card shows freshness/last-updated information.
- Source Power, Battery Power, and Confidence resolve from real runtime/source state where available.
- Missing or stale values explain the source blocker rather than showing blank/unit-only values.
- Existing Home Load, Surplus/Deficit, Reconciliation Error, and Executor State remain visible.
- Repo validation proves JavaScript syntax and focused frontend coverage.
- Live validation through HACS/restart/browser proof remains a separate release-management step.

## Target Environment Feasibility

Target environment: Home Assistant `2026.6.4+` custom panel served by the Zero Net Export integration.

Supported:

- The existing app panel receives Home Assistant state through the frontend `hass` property.
- The current static JavaScript module can re-render locally without new backend routes.
- Existing ZNE coordinator/sensor surfaces expose the needed runtime values:
  - `sensor.zero_net_export_home_load_power_w`
  - `sensor.zero_net_export_solar_power_w`
  - `sensor.zero_net_export_surplus_w`
  - `sensor.zero_net_export_last_reconciliation_error_w`
  - `sensor.zero_net_export_confidence`
  - per-source reading/status sensors such as `sensor.zero_net_export_source_battery_discharge_power_reading`
- Source freshness and blocker details are already present in existing source sensor attributes and blocker summary sensors.

Unsupported / excluded:

- No Home Assistant frontend patching.
- No custom polling endpoint in this slice.
- No direct live Home Assistant install outside release management.

Unknown / follow-up:

- Browser/live proof must confirm exact rendered values after the next approved HACS release.
- Multi-entry entity naming should be reassessed if more than one ZNE plan is installed and HA app-visible entity IDs are suffixed.

## Implementation Notes

- Added a lightweight local re-render timer to keep relative freshness text moving every 10 seconds.
- Resolved the Overview rows against actual generated ZNE entity IDs with `_w` suffixes and per-source reading fallbacks.
- Derived Battery Power as discharge minus charge when charge/discharge source readings are available.
- Moved Confidence to the real `sensor.zero_net_export_confidence` value with status-attribute fallback.
- Added stale/source-blocker messages inside the Reconciliation Status card.

## Validation Plan

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- `python3 -m unittest tests.test_managed_devices_panel -v`
- `git diff --check`
- Before release: full unit discovery and release-management validation.
- After release: HACS install, Home Assistant restart, browser proof for desktop/narrow Overview console, installed-version/fingerprint checks, and targeted log review.

## Repo Validation Evidence

Ran on 2026-07-08:

```text
node --check custom_components/zero_net_export/frontend/zero-net-export-app.js
OK

python3 -m unittest tests.test_managed_devices_panel -v
Ran 18 tests in 0.003s
OK

git diff --check
OK

python3 -m unittest discover -s tests -v
Ran 628 tests in 1.736s
OK

python3 -m py_compile tests/test_managed_devices_panel.py
OK
```

## Release / Live Validation Pending

- No version bump, GitHub release, HACS install, Home Assistant restart, or live browser proof has been performed in this implementation pass.
- Release/live validation remains pending explicit approval through the established release-management path.
