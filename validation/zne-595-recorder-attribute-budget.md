# ZNE-595 Recorder Attribute Budget Validation

Date: 2026-07-15
Status: repo-validated; release/live validation pending

## Scope

Fix `ZNE-595`: recorder-backed Zero Net Export entity attributes exceeded Home
Assistant's 16 KB recorder attribute limit on the live `v0.4.11` install.

## Target Environment Feasibility

- Supported: Zero Net Export controls its entity `extra_state_attributes`, so it
  can trim recorder-backed attributes inside the integration.
- Supported: full detail remains available through diagnostics export and app
  runtime surfaces rather than frequent recorder state attributes.
- Unsupported: changing Home Assistant recorder's 16 KB attribute-size behavior
  from this integration.

## Implementation

- Added recorder-safe helpers for validation details, managed-device runtime
  details, unmanaged candidate rows, and final attribute-budget enforcement.
- Removed bulky `action_history`, `daily_metrics`, `source_diagnostics`,
  `source_freshness`, and `calibration_hints` payloads from recorder-backed
  entity attributes while preserving compact counts and status summaries.
- Applied compact attributes across sensors, binary sensors, switches, selects,
  numbers, and buttons.

## Repo Validation

Passed:

- `python3 -m py_compile custom_components/zero_net_export/entity.py custom_components/zero_net_export/sensor.py custom_components/zero_net_export/button.py custom_components/zero_net_export/switch.py custom_components/zero_net_export/select.py custom_components/zero_net_export/number.py custom_components/zero_net_export/binary_sensor.py tests/test_recorder_attribute_budget.py`
- `python3 -m unittest -v tests.test_recorder_attribute_budget tests.test_binary_sensor_entity_categories`
  - Result: PASS, 6 tests
- `python3 -m unittest discover -v`
  - Result: PASS, 639 tests
- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- `git diff --check`

## Release Validation Plan

1. Publish `v0.4.12` through GitHub.
2. Install `v0.4.12` through the Home Assistant/HACS update entity.
3. Restart Home Assistant.
4. Confirm install fingerprint match before and after restart.
5. Confirm installed/latest version reports `v0.4.12`.
6. Check representative ZNE entity attribute sizes stay below the 16 KB recorder
   ceiling.
7. Review Home Assistant logs for new Zero Net Export recorder attribute-size
   warnings.
