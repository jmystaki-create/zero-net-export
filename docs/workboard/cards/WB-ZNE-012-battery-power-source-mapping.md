# WB-ZNE-012 Battery Power Source Mapping

Status: Released Pending Focused Unit Proof
Priority: High
Labels: runtime, sources, overview, sensors, validation

## Purpose

Track Riley's 2026-07-08 report that Overview Battery Power looked wrong for a
`20000 Wh` battery at about `50%` state of charge.

## Linked Bug

- `ZNE-597` - Battery Power used a cumulative Anker total sensor and displayed
  normalized watts as kW.

## Acceptance Criteria

- Battery Power no longer uses `sensor.anker_battery_discharge_power` because it
  reports `state_class=total` and behaves like cumulative/period data.
- ZNE maps Battery discharge power to an instantaneous power `measurement`
  source, or leaves the optional role unset if no trustworthy source exists.
- `sensor.zero_net_export_battery_discharge_power_status` is `ok` with no
  state-class warning.
- Overview Battery Power is consistent with the live source reading and does not
  show cumulative energy/period values as instantaneous power.
- Source reading entities display normalized watt values with unit `W`, while
  diagnostics still preserve the raw source unit.
- Live Home Assistant evidence is recorded after release.

## Current State

- Target-environment feasibility: supported through existing
  `zero_net_export.update_source_roles`; no direct storage mutation required.
- Live repair: completed through the supported service path.
- Repo fix: coordinator now normalizes source-reading units alongside normalized
  values and preserves `raw_unit`.
- Repo validation: passed.
- Release state: shipped in public release `v0.4.4`; current installed release
  is `v0.4.12`.
- Remaining validation: focused installed proof that Overview Battery Power and
  source-reading entities display normalized watt values with unit `W`.

## Evidence

- Before repair:
  - `number.x1_p6k_us_s_battery_capacity=20000 Wh`
  - `sensor.x1_p6k_us_s_state_of_charge=49%`
  - `sensor.anker_battery_discharge_power=29.97 kW`
  - `sensor.anker_battery_discharge_power state_class=total`
  - `sensor.zero_net_export_battery_discharge_power_reading=29970.0` with unit
    `kW`
- After live service repair:
  - `battery_discharge_power_entity=sensor.x1_p6k_us_s_discharge_power`
  - `sensor.zero_net_export_battery_discharge_power_status=ok`
  - normalized discharge value `420 W`
  - `sensor.zero_net_export_status=ready`
  - `sensor.zero_net_export_last_reconciliation_error=0 W`

## Next Actions

1. Read-only verify Overview Battery Power and source-reading units on installed
   `v0.4.12`.
2. Record the focused evidence and close `ZNE-597` if units display normalized
   watts as `W`.
3. Use the result to inform the next app workflow slice.
