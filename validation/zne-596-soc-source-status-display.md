# ZNE-596 SOC Source Status Display Validation

Date: 2026-07-08
Status: released and live validated in v0.4.1

## Bug

The Zero Net Export Sources app showed Battery state of charge as missing even
though Home Assistant had a valid backend SOC source binding.

## Live Evidence Before Fix

Read-only Home Assistant API check on installed `v0.4.0`:

- `sensor.zero_net_export_battery_state_of_charge_status`: `ok`
- Binding: `sensor.x1_p6k_us_s_state_of_charge`
- `binary_sensor.zero_net_export_battery_state_of_charge_stale`: `off`
- Source entity: `sensor.x1_p6k_us_s_state_of_charge`
- Source reading: `39 %`

User screenshot showed the Sources app SOC row as:

- `status: missing`
- `Binding: Not configured`
- input placeholder/value path showing `sensor.example`

## Root Cause

The app derived source status entity IDs by stripping `_entity` from each
source-role key. For `battery_soc_entity`, that produced
`sensor.zero_net_export_battery_soc_status`, but the integration exposes
`sensor.zero_net_export_battery_state_of_charge_status`.

## Fix

Added an explicit app frontend source slug map:

- `battery_soc_entity` -> `battery_state_of_charge`

The generic `_entity` stripping remains for source roles whose config keys
already match the exposed entity slug.

## Repo Validation

Passed:

```text
python3 -m unittest tests.test_managed_devices_panel -q
Ran 17 tests in 0.003s
OK
```

Passed:

```text
node --check custom_components/zero_net_export/frontend/zero-net-export-app.js
```

Passed:

```text
python3 -m unittest discover -s tests -q
Ran 627 tests in 1.741s
OK
```

Passed:

```text
python3 -m py_compile $(find custom_components/zero_net_export -name '*.py' -print)
```

Passed:

```text
git diff --check
```

## Release Validation

Corrective release `v0.4.1` was published from commit `f985ad3`,
installed through HACS, fingerprint-matched against the intended repo build,
and validated after a Home Assistant restart.

Live API proof after restart:

- `sensor.zero_net_export_installed_version`: `0.4.1`
- `update.zero_net_export_update`: installed/latest `v0.4.1`
- `sensor.zero_net_export_battery_state_of_charge_status`: `ok`
- Binding: `sensor.x1_p6k_us_s_state_of_charge`
- `binary_sensor.zero_net_export_battery_state_of_charge_stale`: `off`
- Source reading: `61 %`

Browser proof from the installed `v0.4.1` app Sources tab showed:

- `Battery state of charge`
- `status: ok`
- `Binding: sensor.x1_p6k_us_s_state_of_charge`
- `Reading: 62.0 | Age: unknown s | Issues: 0`

Evidence: `validation/0.4.1-release-validation.md`.
