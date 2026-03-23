# Dashboard Setup

This project now includes a first operator dashboard scaffold at:

- `examples/lovelace/zero_net_export_dashboard.yaml`

It is intentionally plain Lovelace YAML, not a custom frontend, so the integration can ship a useful operator surface before any bespoke panel work.

## What this scaffold covers

The dashboard is structured around the v1 operator workflow:

1. **Live overview** — solar, home load, grid import/export, battery SOC, surplus, export error
2. **Controller** — enable switch, mode, target export, deadband, controller reason/summary
3. **Validation and diagnostics** — confidence, source mismatch, safe mode, battery reserve state, reconciliation error, recent action outcome state
4. **Device fleet summary** — configured/usable devices and current planned vs blocked control state
5. **Managed devices** — example per-device cards for one fixed load and one variable load

## Importing it into Home Assistant

### Option A — Manual dashboard YAML mode

1. Copy `examples/lovelace/zero_net_export_dashboard.yaml` into your Home Assistant config, for example:
   - `/config/lovelace/zero_net_export_dashboard.yaml`
2. In Home Assistant, create a dashboard in YAML mode or add a new view that references this file.
3. Adjust entity ids so they match the entity ids created by your integration entry.

### Option B — Copy cards into an existing dashboard

1. Open the example YAML.
2. Copy the cards or whole view into your existing Lovelace dashboard.
3. Replace the example device cards with cards for your actual configured devices.

## Important entity-id note

Home Assistant entity ids can vary depending on the integration entry title and any entity-id normalization that happens when the entities are created.

Because of that, treat the example YAML as a scaffold:

- verify the controller entity ids in **Developer Tools → States**
- replace any ids that differ from the example
- duplicate or trim the per-device cards to match your actual inventory

## Runtime override behavior

The controller cards are now intended to be used as a real operator surface, not just a read-only demo.

From the dashboard:
- the main **Enabled** switch persists across reloads
- the main **Mode** select persists across reloads
- the main **Target export**, **Deadband**, and **Battery reserve SOC** numbers now act as runtime overrides that persist across reloads
- the main controller entities now expose attributes showing configured vs effective values and whether an override is active
- `button.zero_net_export_reset_controller_overrides` clears the persisted target/deadband/battery-reserve tuning overrides and falls back to the options-flow defaults
- each configured device now also exposes a `button.zero_net_export_<device_key>_reset_overrides` control that clears persisted enable / priority overrides and restores the JSON-defined defaults

This gives operators a safe way to tune the controller live without having to reopen the options flow for every adjustment, while still leaving a clean path back to the baseline config.

## Expected controller entities

The scaffold assumes the main controller exposes entities equivalent to:

- `switch.zero_net_export_enabled`
- `select.zero_net_export_mode`
- `number.zero_net_export_target_export`
- `number.zero_net_export_deadband`
- `number.zero_net_export_battery_reserve_soc`
- `button.zero_net_export_reset_controller_overrides`
- `sensor.zero_net_export_status`
- `sensor.zero_net_export_reason`
- `sensor.zero_net_export_recommendation`
- `sensor.zero_net_export_confidence`
- `sensor.zero_net_export_control_status`
- `sensor.zero_net_export_control_summary`
- `sensor.zero_net_export_control_reason`
- `sensor.zero_net_export_control_guard_summary`
- `binary_sensor.zero_net_export_active`
- `binary_sensor.zero_net_export_source_mismatch`
- `binary_sensor.zero_net_export_safe_mode`
- `binary_sensor.zero_net_export_battery_below_reserve`

And supporting telemetry such as solar/home/grid/battery, planned action counts, last action state, the new recent-action / recent-failure summary sensors, the last-action / last-failure timing sensors, the daily reporting slice (`actions_today`, `successful_actions_today`, `failed_actions_today`, `active_controlled_power_w`, and `energy_redirected_today_kwh`), plus the stale-data / command-failure health slice (`binary_sensor.zero_net_export_stale_data`, `binary_sensor.zero_net_export_command_failure`, `sensor.zero_net_export_health_status`, `sensor.zero_net_export_health_summary`, `sensor.zero_net_export_stale_source_count`, and `sensor.zero_net_export_stale_source_summary`).

The integration now also exposes a first-class per-source diagnostics slice for each mapped role:
- `sensor.zero_net_export_source_<source_key>_status`
- `sensor.zero_net_export_source_<source_key>_reading`
- `sensor.zero_net_export_source_<source_key>_age_seconds`
- `sensor.zero_net_export_source_<source_key>_issue_count`
- `binary_sensor.zero_net_export_source_<source_key>_stale`

These entities make it much easier to build dashboard rows for specific sources without expanding the controller entity's raw attributes.

## Expected per-device entities

For each configured device, the current integration exposes a per-device set including:

- usability binary sensor
- enable switch
- priority number
- reset-overrides button
- status sensor
- planned action sensor
- guard status sensor
- current power sensor
- planned power delta sensor
- last requested power sensor
- last applied power sensor
- target power sensor for variable devices
- last action status sensor
- last action at timestamp sensor
- last applied at timestamp sensor
- last action result sensor

The example YAML uses two sample device keys:

- `hot_water`
- `ev_charger`

Replace those with the real device keys derived from your device inventory JSON.

## Reporting caveat

`energy_redirected_today_kwh` is an operator-focused estimate based on observed active managed-device power over time. It is useful for spotting whether the controller is doing meaningful work, but it should not be treated as a billing-grade or inverter-grade energy total.

## Why this milestone matters

The guarded planner and executor already produce explanation-rich state, but that state is hard to use until it is grouped into an operator-first control surface.

This scaffold turns the current backend work into something installable and reviewable inside Home Assistant now, while leaving room for a richer future panel.

## Troubleshooting support

When this integration is installed in a real Home Assistant instance, you can now also use the standard Home Assistant **Download diagnostics** flow for the config entry.

That diagnostics payload is designed to help review:
- controller mode, safe-mode, health, and plan summary
- per-source validation/freshness details
- per-device runtime status and recent action outcomes
- daily metrics and recent control history

Mapped entity ids, device entity ids, and operator-facing names are redacted in the diagnostics export so the payload is easier to share during debugging.

## Next likely dashboard step

After this scaffold, the next useful UX increment is:

- a more compact action-history / failure timeline card once real installations show what operators actually watch most
- optional packaged dashboard assets or a custom panel when the entity model stabilizes
