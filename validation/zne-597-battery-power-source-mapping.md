# ZNE-597 Battery Power Source Mapping

Date: 2026-07-08

## Scope

Riley reported that Overview Battery Power looked wrong because the live system
has a `20000 Wh` battery at about `50%` state of charge. This validation record
covers the live source-role repair plus the repo-side unit-presentation fix.

## Target Environment Feasibility

- **Supported:** source-role repair through the existing
  `zero_net_export.update_source_roles` service.
- **Supported:** source-reading unit presentation fix inside the ZNE-owned
  integration backend/sensor entities.
- **Unsupported/excluded:** direct Home Assistant storage mutation and direct
  live custom-component file deployment.
- **Unknown:** whether the upstream Anker total-style entity can be corrected by
  the source integration. ZNE now avoids using it for Battery Power.

## Live Diagnosis

Before repair, Home Assistant state showed:

- `number.x1_p6k_us_s_battery_capacity=20000 Wh`
- `sensor.x1_p6k_us_s_state_of_charge=49%`
- `sensor.anker_battery_discharge_power=29.97 kW`
- `sensor.anker_battery_discharge_power state_class=total`
- `sensor.zero_net_export_battery_discharge_power_reading=29970.0`
- `sensor.zero_net_export_battery_discharge_power_reading unit=kW`
- `sensor.zero_net_export_status=degraded`
- `sensor.zero_net_export_reason=Validation degraded: battery_discharge_power state_class is total; expected measurement`

Candidate inspection found the trustworthy instantaneous source:

- `sensor.x1_p6k_us_s_discharge_power=0.42 kW`
- `device_class=power`
- `state_class=measurement`

## Live Repair

Called the supported service:

```json
{
  "entry_id": "01KWC2HX12V4P0Q82A0WM69EHV",
  "battery_discharge_power_entity": "sensor.x1_p6k_us_s_discharge_power"
}
```

Post-repair Home Assistant state showed:

- `sensor.zero_net_export_battery_discharge_power_status=ok`
- binding `sensor.x1_p6k_us_s_discharge_power`
- raw value `0.42`
- normalized value `420`
- source metadata `device_class=power`, `state_class=measurement`
- `binary_sensor.zero_net_export_battery_discharge_power_stale=off`
- `sensor.zero_net_export_status=ready`
- `sensor.zero_net_export_reason=Sources validated; 1 controllable device is ready`
- `sensor.zero_net_export_surplus=0.0 W`
- `sensor.zero_net_export_last_reconciliation_error=0.0 W`

## Repo Fix

- `custom_components/zero_net_export/coordinator.py`
  - added source-unit normalization so power readings converted from `kW` to W
    expose unit `W`.
- `custom_components/zero_net_export/validation.py`
  - preserved the original source unit as `raw_unit` in source diagnostics.
- `tests/test_source_freshness_probes.py`
  - added focused regression coverage for kW-to-W value and unit normalization.

## Validation

- `python3 -m py_compile custom_components/zero_net_export/coordinator.py custom_components/zero_net_export/validation.py tests/test_source_freshness_probes.py`
  - passed
- `python3 -m unittest tests.test_source_freshness_probes tests.test_sensor_issue_count_state_class tests.test_managed_devices_panel tests.test_operator_docs_consistency -v`
  - passed, `Ran 39 tests`
- `python3 -m unittest discover -s tests -v`
  - passed, `Ran 630 tests`
- `git diff --check`
  - passed

## Release State

Repo-validated and shipped in public GitHub release `v0.4.4`; later installed
validation advanced the live system to `v0.4.12`.

Remaining validation gap: no dedicated release validation record captures the
installed Overview Battery Power/source-reading unit display after the
unit-presentation fix. Perform a focused read-only installed check and close
`ZNE-597` only if normalized watt readings display with unit `W`.
