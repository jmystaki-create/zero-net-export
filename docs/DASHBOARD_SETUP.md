# Optional Lovelace Debug Dashboard Setup

This project includes an optional Lovelace dashboard scaffold at:

- `examples/lovelace/zero_net_export_dashboard.yaml`

It is intentionally plain Lovelace YAML, not a custom frontend. It lives fully inside Home Assistant and is supplementary debug visibility for operators who want to see controller, battery, grid, and managed-load state in one place.

This dashboard complements, rather than replaces, the integration's native Configure, Repairs, device-page entities, and support buttons. It is not part of the supported operator path.

## What this scaffold covers

The dashboard is structured as optional debug visibility around the native operator workflow:

1. **Live power picture** — solar, home load, grid import/export, battery SOC, controlled load, surplus, export error
2. **Controller intent and overrides** — enable switch, mode, target export, deadband, battery reserve, override visibility, and controller reasoning
3. **Health, guards, and support** — safe mode, source mismatch, stale data, command failure, reserve gating, health summary, and native support buttons
4. **Source-level diagnostics** — mapped source status, readings, age, and staleness
5. **Fleet and planning summary** — configured/usable devices and current planned vs blocked control state
6. **Action and failure timeline** — last action, last success, recent failure, and cycle totals
7. **Daily impact** — daily action counts and redirected-energy estimate
8. **Managed-load card template** — how to add one serious per-device control card per configured load using the existing per-device entities

## Importing it into Home Assistant

### Option A — Manual dashboard YAML mode

1. Copy `examples/lovelace/zero_net_export_dashboard.yaml` into your Home Assistant config, for example:
   - `/config/lovelace/zero_net_export_dashboard.yaml`
2. In Home Assistant, create a dashboard in YAML mode or add a new view that references this file.
3. Adjust entity ids so they match the entity ids created by your integration entry.

### Option B — Copy cards into an existing dashboard

1. Open the example YAML.
2. Copy the cards or whole view into your existing Lovelace dashboard.
3. Add one per-device card section for each real managed load using that device's actual entity ids.

## Important entity-id note

Home Assistant entity ids can vary depending on the integration entry title and any entity-id normalization that happens when the entities are created.

Because of that, treat the example YAML as a scaffold:

- verify the controller entity ids in **Developer Tools → States**
- replace any ids that differ from the example
- duplicate or trim the per-device cards to match your actual inventory

## Runtime override behavior

The controller cards can be used as an optional debug/control surface inside Home Assistant, not just a read-only demo.

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
- current active runtime sensor
- active runtime today sensor
- target power sensor for variable devices
- last action status sensor
- last action at timestamp sensor
- last applied at timestamp sensor
- last action result sensor

Per-device state now also includes runtime-cap visibility in attributes such as `max_active_seconds`, `current_active_seconds`, and `planned_action_policy`, so operators can distinguish ordinary balancing from protective runtime-cap shedding.

The scaffold no longer hardcodes fake example device cards because real installs differ too much.

Instead, add one serious per-device control section/card per configured load using your real device keys derived from the managed-device inventory.

Common examples might look like:

- `hot_water`
- `ev_charger`
- `pool_pump`
- `battery_sink`

## Reporting caveat

`energy_redirected_today_kwh` is an operator-focused estimate based on observed active managed-device power over time. It is useful for spotting whether the controller is doing meaningful work, but it should not be treated as a billing-grade or inverter-grade energy total.

Per-device `active_runtime_today_seconds` is likewise operational telemetry derived from coordinator refresh intervals while a device appears active. It is useful for runtime-cap review and operator dashboards, but it is not a compliance-grade runtime ledger.

## Why this milestone matters

The guarded planner and executor already produce explanation-rich state, but that state is hard to use until it is grouped into an operator-first control surface.

This scaffold turns the current backend work into optional in-Home-Assistant debug visibility, without reviving the removed external panel path or changing the supported native operator path.

## Troubleshooting support

When this integration is installed in a real Home Assistant instance, you can now also use the standard Home Assistant **Download diagnostics** flow for the config entry.

That diagnostics payload is designed to help review:
- controller mode, safe-mode, health, and plan summary
- per-source validation/freshness details
- per-device runtime status and recent action outcomes
- daily metrics and recent control history

Mapped entity ids, device entity ids, and operator-facing names are redacted in the diagnostics export so the payload is easier to share during debugging.

## Next likely follow-up

After this scaffold, the next useful increment is not more packaged dashboard surface area. The higher-value follow-up is to keep the native Home Assistant operator path clearer and easier to validate:

- make Configure, Repairs, and the integration/device surfaces more self-explanatory as the command center for sources, policy, managed devices, and support
- keep validating that native path in real Home Assistant installs, then turn confirmed operator friction into targeted fixes
- only revisit optional dashboard ergonomics later if real installs show a specific debug-visibility gap that native surfaces still do not cover
