# ZNE-590 managed climate device page cleanup validation

Date: 2026-05-06
Status: live_validated_fixed_in_0.1.107

## Scope

Riley accepted Option A for ZNE-590: preserve the original Home Assistant climate/thermostat device page and clean up the Zero Net Export-owned managed-load device page using native Home Assistant integration surfaces only.

## Implementation summary

- Renamed ZNE managed-load rows so the native device page no longer shows confusing/internal labels such as `Settings — Test enabled`, `Settings — Test current power`, `Test review`, or `Test reset...`.
- Kept the original thermostat/climate device page untouched; no cross-integration device registry merge was introduced.
- Added a native `Test load` button for each managed load. Pressing it calls Home Assistant `turn_on` for the captured managed-load entity and creates a persistent notification with the result.
- Kept `Zero Net Export enabled` and `Priority` as operator configuration rows.
- Changed primary ZNE managed-load sensors to concise operator labels/states:
  - `Zero Net Export configuration`
  - `Zero Net Export status`
  - `Current power` as diagnostic detail
- Moved review/reset style actions to Diagnostic category so they are not presented as primary configuration controls.
- Preserved Home Assistant-native surfaces only: entities, device registry rows, services, persistent notifications. No custom frontend, sidebar panel, external UI, or Home Assistant frontend patch was added.

## Repo validation completed

- Focused ZNE-590/native managed-device tests:
  - Command: `python3 -m unittest -q tests.test_device_page_managed_settings tests.test_sensor_entity_categories tests.test_button_entity_categories tests.test_binary_sensor_entity_categories tests.test_integration_page_device_lists`
  - Result: `Ran 161 tests in 0.345s`, `OK`
- Full repo gate:
  - Command: `python3 -m py_compile custom_components/zero_net_export/*.py && python3 -m unittest discover -s tests && git diff --check`
  - Result: `Ran 607 tests in 1.772s`, `OK`; `py_compile` passed; `git diff --check` passed.

## Release-managed live validation completed

Release `0.1.107` was published, installed through the Home Assistant update entity, fingerprint-checked, restarted, log-checked, and browser-validated.

Evidence:

- Release validation: `validation/0.1.107-release-validation.md`
- Managed-load page screenshot: `validation/artifacts/zne-590-managed-climate-device-v0.1.107.png`
- Managed-load page extracted proof: `validation/artifacts/zne-590-managed-climate-device-v0.1.107.json`
- Original thermostat page screenshot: `validation/artifacts/zne-590-original-thermostat-device-v0.1.107.png`
- Original thermostat page extracted proof: `validation/artifacts/zne-590-original-thermostat-device-v0.1.107.json`

Result:

- Installed build fingerprint matched repo commit `dbb9bf2` before and after restart.
- Home Assistant API recovered after restart.
- `update.zero_net_export_update` reported installed/latest `v0.1.107`.
- `sensor.zero_net_export_installed_version` reported `0.1.107`.
- Post-restart log tail showed no Zero Net Export errors/warnings/tracebacks.
- Browser proof confirmed the ZNE managed-load page shows `Zero Net Export enabled`, `Test load`, `Priority`, `Zero Net Export configuration`, `Zero Net Export status`, and `Current power`, while confusing `Settings — Test ...` rows are absent.
- Browser proof confirmed the original Tuya/Tuya Local thermostat device page remains a thermostat page and does not expose ZNE managed-load controls.

## Current closure decision

ZNE-590 is live-validated fixed in `0.1.107`.
