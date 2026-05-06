# ZNE-590 managed climate device page cleanup validation

Date: 2026-05-06
Status: repo_validated_pending_live_release_validation

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

## Pending validation

Before closing ZNE-590, release-managed live validation is still required:

1. Bump/package/release the next version.
2. Install through the Home Assistant update/HACS path.
3. Confirm install fingerprint matches the intended repo build.
4. Restart Home Assistant and wait for API recovery.
5. Capture browser proof that:
   - the original `climate.lounge_room_thermostat` device page is preserved;
   - the ZNE managed-load page exposes `Zero Net Export enabled`, `Test load`, `Priority`, `Zero Net Export configuration`, and `Zero Net Export status`;
   - confusing `Settings — Test ...` rows are absent.
6. Check Zero Net Export logs after restart.

## Current closure decision

Do not close ZNE-590 yet. The repo fix is validated, but the bug affects live Home Assistant UI behavior and needs installed-build browser proof before closure.
