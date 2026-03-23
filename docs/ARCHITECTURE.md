# Architecture

## High-level layers

### 1. Source Mapping and Validation Layer
Responsible for:
- mapping HA entities to logical energy roles
- validating availability, numeric state, units, device/state classes, and consistency
- rejecting obviously bad mappings during config flow before the entry is created
- reconciling solar/load/grid/battery power flows within a tolerance band
- exposing confidence / mismatch / safe-mode indicators plus issue details, diagnostic summaries, per-source diagnostics, remediation hints, and source-freshness health state

### 2. State Model Layer
Builds a normalized runtime model:
- solar power / energy
- grid import / export power and energy
- home load
- battery SOC / charge / discharge
- surplus / deficit relative to export target

### 3. Device Inventory Layer
Responsible for:
- parsing an operator-managed JSON inventory of controllable devices
- distinguishing fixed vs variable devices
- validating structural constraints such as min/max/step power
- evaluating runtime usability based on source validation and entity availability
- publishing per-device explainability before any live control actions are attempted

### 4. Control Engine Layer
Responsible for:
- applying control mode rules
- deadband / hysteresis
- battery reserve policy gating
- allocating power to devices
- scheduling on/off decisions
- emitting explanation state

### 5. Device Adapter Layer
Wraps supported device classes:
- fixed load adapters
- variable load adapters
- future battery / inverter adapters

Current v1 adapter boundary:
- devices can declare an explicit `adapter`, or let the integration infer one only for known-safe cases
- `fixed_toggle` supports `switch` / `input_boolean` entities via `<entity domain>.turn_on` / `<entity domain>.turn_off`
- `variable_number` supports `number` / `input_number` entities via `set_value`
- unsupported domains fail closed with explicit runtime adapter status instead of guessing service behavior

### 6. Entity / UX Layer
Exposes:
- switches
- selects
- numbers
- sensors
- binary sensors
- device-level entities
- dashboard-supporting state
- persisted operator-facing control memory such as controller enable/mode/target/deadband overrides, per-device enable/priority overrides, last requested/applied power, and recent action history
- Home Assistant diagnostics export that redacts mapped entity ids / names while preserving the runtime state needed for troubleshooting

---

## Data flow

1. Fetch mapped entity states
2. Normalize values and signs
3. Reconcile and score confidence
4. Parse and validate device inventory
5. Evaluate device usability and policy constraints
6. Compute current export / import error to target
7. Choose control actions
8. Apply actions
9. Publish explanation and health state

---

## Failure behavior

### Confidence degraded
- stop aggressive control
- switch to monitor-only or conservative mode
- expose warning entities
- mark all configured devices non-usable with an explicit reason

### Stale source data
- if a required mapped source stops updating for longer than the freshness threshold (currently max of 120 s or 3 refresh intervals), hold the controller in safe mode
- expose stale-data health entities plus per-source freshness details
- let control resume automatically once the required source timestamps become fresh again

### Required source missing
- no active optimization
- surface explicit error state

### Device inventory invalid
- surface validation warning explaining the parse/shape problem
- keep controller in monitor-only behavior until the inventory is corrected

### Device action failure
- mark device degraded for cycle / retry window
- surface a command-failure health indicator until a newer successful action clears it or the retry window expires
- emit event
- continue with remaining controllable devices
