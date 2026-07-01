# ZNE-APP-004 Live Baseline

Date: 2026-07-02

## Scope

Read-only Home Assistant API baseline for Milestone 4: Source Health & Runtime
Blocker Resolution.

## API Access

- Home Assistant API auth check returned HTTP `200`.
- `/api/` returned `{"message":"API running."}`.
- No secrets are recorded in this validation file.

## Live State Snapshot

Snapshot file, local only:

- `/tmp/zne_m4_live_state_20260702_000032.json`

Relevant state values:

- `sensor.zero_net_export_status=degraded`
- `sensor.zero_net_export_reason=Validation degraded: battery_discharge_power state_class is <SensorStateClass.TOTAL: 'total'>; expected 'measurement'`
- `sensor.zero_net_export_last_reconciliation_error=300.0 W`
- `sensor.zero_net_export_home_load_power=300.0 W`
- `sensor.zero_net_export_surplus=-300.0 W`
- `sensor.anker_battery_discharge_power=0`
- `sensor.anker_battery_discharge_power.attributes.state_class=total`
- `sensor.anker_battery_discharge_power.attributes.unit_of_measurement=kW`

## Findings

Supported:

- Milestone 4 can proceed because HA API access is restored.
- The current live blocker is reproducible through read-only API proof.
- The metadata mismatch is specific and actionable:
  `battery_discharge_power` is exposed as `state_class=total` while ZNE expects
  measurement semantics for a real-time power source.

Needs follow-up:

- The guide must convert the live Anker sensor from kW to W when building the
  template sensor. Relabeling the source as W without conversion would create a
  scaling error.
- Reconciliation must be rechecked after the source fix. The latest baseline
  shows a `300 W` reconciliation error against `300 W` home load; the earlier
  larger gap was not present in this snapshot.

## Result

Milestone 4 is unblocked for implementation and validation planning. The next
safe action is to apply or guide the template-sensor workaround, point ZNE at
the fixed source, then capture live API and browser proof showing
`sensor.zero_net_export_status=ok` and acceptable reconciliation.
