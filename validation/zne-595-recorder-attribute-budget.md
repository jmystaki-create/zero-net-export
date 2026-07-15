# ZNE-595 Recorder Attribute Budget Validation

Date: 2026-07-15
Status: released/live-validated in `v0.4.12`

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

## Release Validation

Release `v0.4.12` was published through GitHub, installed through the Home
Assistant/HACS update entity, restarted, and live-validated.

Evidence:

- GitHub release: `https://github.com/jmystaki-create/zero-net-export/releases/tag/v0.4.12`
- Release commit: `94215e4`
- HACS/Home Assistant update entity reported installed/latest `v0.4.12`.
- Install fingerprint matched before and after restart:
  - `tmp/install-fingerprint-compare-v0.4.12-before-restart.json`
  - `tmp/install-fingerprint-compare-v0.4.12-after-restart.json`
- Post-restart Home Assistant state:
  - `sensor.zero_net_export_installed_version=0.4.12`
  - `sensor.zero_net_export_previous_installed_version=0.4.11`
  - `update.zero_net_export_update` installed/latest `v0.4.12`
- Post-restart attribute-size check covered 167 ZNE entities; maximum observed
  ZNE attribute payload was `10483` bytes.
- Post-restart log scan found `0` Zero Net Export recorder attribute-size
  warnings in the reviewed window after the `17:50` restart boot messages.
