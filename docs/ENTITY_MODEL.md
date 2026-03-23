# Entity Model

## Controller entities

### Switches
- `switch.zero_net_export_enabled`
  - persists operator on/off intent across reloads

### Selects
- `select.zero_net_export_mode`
  - persists the operator-selected runtime control mode across reloads

### Numbers
- `number.zero_net_export_target_export`
  - runtime override over the configured target-export default, persisted across reloads
  - now exposes controller-setting attributes so dashboards can show configured vs effective value and whether an override is active
- `number.zero_net_export_deadband`
  - runtime override over the configured deadband default, persisted across reloads
  - now exposes controller-setting attributes so dashboards can show configured vs effective value and whether an override is active

### Buttons
- `button.zero_net_export_reset_controller_overrides`
  - clears persisted target-export and deadband runtime overrides so the controller falls back to the options-flow defaults
- `button.zero_net_export_<device_key>_reset_overrides`
  - clears persisted per-device enable / priority overrides so a device falls back to its JSON-defined defaults

Configuration-only via options flow:
- `refresh_seconds`

### Sensors
- `sensor.zero_net_export_status`
- `sensor.zero_net_export_reason`
- `sensor.zero_net_export_recommendation`
- `sensor.zero_net_export_diagnostic_summary`
- `sensor.zero_net_export_surplus_w`
- `sensor.zero_net_export_grid_export_w`
- `sensor.zero_net_export_grid_import_w`
- `sensor.zero_net_export_confidence`
- `sensor.zero_net_export_last_reconciliation_error_w`
- `sensor.zero_net_export_actions_today`
- `sensor.zero_net_export_successful_actions_today`
- `sensor.zero_net_export_failed_actions_today`
- `sensor.zero_net_export_energy_redirected_today_kwh`
- `sensor.zero_net_export_active_controlled_power_w`
- `sensor.zero_net_export_configured_devices`
- `sensor.zero_net_export_enabled_devices`
- `sensor.zero_net_export_usable_devices`
- `sensor.zero_net_export_fixed_devices`
- `sensor.zero_net_export_variable_devices`
- `sensor.zero_net_export_configured_controllable_power`
- `sensor.zero_net_export_usable_controllable_power`
- `sensor.zero_net_export_device_status_summary`
- `sensor.zero_net_export_control_status`
- `sensor.zero_net_export_control_summary`
- `sensor.zero_net_export_control_reason`
- `sensor.zero_net_export_control_guard_summary`
- `sensor.zero_net_export_last_action_status`
- `sensor.zero_net_export_last_action_summary`
- `sensor.zero_net_export_last_action_at`
- `sensor.zero_net_export_last_successful_action_at`
- `sensor.zero_net_export_last_failed_action_at`
- `sensor.zero_net_export_last_action_device`
- `sensor.zero_net_export_last_failed_action_device`
- `sensor.zero_net_export_last_failed_action_message`
- `sensor.zero_net_export_recent_action_summary`
- `sensor.zero_net_export_recent_failure_summary`
- `sensor.zero_net_export_last_successful_action_summary`
- `sensor.zero_net_export_action_history_count`
- `sensor.zero_net_export_successful_action_count`
- `sensor.zero_net_export_failed_action_count`
- `sensor.zero_net_export_export_error_w`
- `sensor.zero_net_export_planned_action_count`
- `sensor.zero_net_export_executable_action_count`
- `sensor.zero_net_export_blocked_planned_action_count`
- `sensor.zero_net_export_planned_power_delta_w`
- `sensor.zero_net_export_variable_planned_power_delta_w`
- `sensor.zero_net_export_fixed_planned_power_delta_w`

Per-source diagnostic entities now also exist for each mapped source role, including:
- `sensor.zero_net_export_source_<source_key>_status`
- `sensor.zero_net_export_source_<source_key>_reading`
- `sensor.zero_net_export_source_<source_key>_age_seconds`
- `sensor.zero_net_export_source_<source_key>_issue_count`
- `binary_sensor.zero_net_export_source_<source_key>_stale`

Examples:
- `sensor.zero_net_export_source_grid_export_power_status`
- `sensor.zero_net_export_source_grid_export_power_reading`
- `sensor.zero_net_export_source_grid_export_power_age_seconds`
- `binary_sensor.zero_net_export_source_grid_export_power_stale`

Planner semantics note:
- variable-device `planned_action` / `last_requested_power` now represent the next requested target derived from the device's current observed target, not a reset-to-zero/rebuild-from-scratch assumption each cycle
- import-side variable shedding is conservative in v1 and currently trims toward configured minimum power before resorting to fixed-load turn-off

### Binary sensors
- `binary_sensor.zero_net_export_active`
- `binary_sensor.zero_net_export_source_mismatch`
- `binary_sensor.zero_net_export_safe_mode`

## Per-device entities

Each managed device now gets:
- usability binary sensor
- enable switch
- priority number
- status sensor with reason / config attributes
- current power sensor
- planned action sensor
- guard status sensor
- planned power delta sensor
- current active runtime sensor
- active runtime today sensor
- optional current target power sensor for variable loads

Per-device attributes now include:
- observed active state
- configured vs resolved adapter metadata
- adapter status / adapter reason / supported actions
- min-on / min-off / cooldown settings
- planned action reason and policy (`balance` vs `runtime_cap`)
- guard status and guard reason
- whether the current planned action is executable
- last actual action and age
- last action status as a dedicated sensor
- last action result message / service details
- last action timestamp and last applied timestamp as dedicated sensors

Daily reporting notes:
- `actions_today` is the combined successful + failed action count for the current local day
- `energy_redirected_today_kwh` is an operational estimate derived from observed active managed-device power integrated over coordinator refresh time, not a revenue-grade meter reading
- `active_controlled_power_w` shows the current estimated managed load contribution from active devices
- each device now also exposes `current_active_seconds` and `active_runtime_today_seconds` so runtime-cap safety and dashboard review do not depend on digging through raw attributes

Planned next:
- richer last-action diagnostics entity set beyond the current daily/reporting slice
- longer-horizon reporting once live installs prove which aggregates are actually useful
- optional packaged dashboard assets or a bespoke panel once real installs confirm which controls deserve first-class UI treatment

## Config entities / options

Mapped logical roles should include:
- solar power sensor
- solar energy sensor
- grid import power sensor
- grid export power sensor
- grid import energy sensor
- grid export energy sensor
- home load / net consumption sensor
- battery SOC sensor
- battery charge power sensor
- battery discharge power sensor

Options now also include:
- device inventory JSON for fixed / variable controllable devices
- optional per-device anti-flap settings inside that JSON:
  - `min_on_seconds`
  - `min_off_seconds`
  - `cooldown_seconds`
  - `max_active_seconds`

## Diagnostics

The integration now also supports Home Assistant config-entry diagnostics download.

Current diagnostics payload includes:
- redacted config-entry data and options
- controller runtime state and planning summary
- source readings, validation details, and per-source freshness/issue diagnostics
- fleet/device runtime details with entity ids and operator-facing names redacted
- recent action history and daily metrics for support/debugging

This is intended to make real-install validation easier without requiring operators to manually copy raw entity attributes from Developer Tools.

## Events

Runtime event domain:
- `zero_net_export.action_applied`
- `zero_net_export.source_mismatch`
- `zero_net_export.source_mismatch_cleared`
- `zero_net_export.safe_mode_entered`
- `zero_net_export.safe_mode_exited`
