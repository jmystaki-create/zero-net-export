# Real-Installation Validation Checklist

Use this checklist to validate Zero Net Export in a real Home Assistant environment before considering v1 complete.

## Pre-Installation Checks

- [ ] Home Assistant version >= 2024.6.0
- [ ] HACS installed (if using HACS install path)
- [ ] Energy dashboard configured with solar/grid entities
- [ ] At least one controllable load available (switch or number entity)
- [ ] Battery system available (optional but recommended for full validation)

## Installation Validation

### HACS Install Path
- [ ] Repository added to HACS custom repositories
- [ ] Integration downloaded without errors
- [ ] Home Assistant restart completes successfully
- [ ] Integration appears in Settings → Devices & Services

### Manual Install Path
- [ ] `custom_components/zero_net_export` copied to HA config
- [ ] Home Assistant restart completes successfully
- [ ] Integration appears in Settings → Devices & Services

## Configuration Flow Validation

- [ ] Config flow opens when adding integration
- [ ] Source entity mapping UI displays correctly
- [ ] Validation blocks incomplete mappings (missing required entities)
- [ ] Validation blocks duplicate entity mappings
- [ ] Validation blocks non-numeric entities for power roles
- [ ] Device inventory JSON accepts valid device configurations
- [ ] Options flow allows re-mapping sources and devices
- [ ] Entity normalization creates expected entity IDs

## Source Validation Layer

- [ ] Solar power entity shows valid reading
- [ ] Grid export power entity shows valid reading
- [ ] Grid import power entity shows valid reading
- [ ] Home load power entity shows valid reading
- [ ] Battery SOC entity shows valid reading (if configured)
- [ ] Confidence sensor reports "high" when all sources valid
- [ ] Safe mode activates when required source missing
- [ ] Safe mode activates when source data stale (>120s)
- [ ] Source mismatch detected when reconciliation fails
- [ ] Per-source diagnostics show status/reading/age/issue_count
- [ ] Stale source binary sensor triggers correctly
- [ ] Calibration hints appear in validation diagnostics

## Device Model Validation

- [ ] Fixed device (switch/input_boolean) parses correctly
- [ ] Variable device (number/input_number) parses correctly
- [ ] Device adapter resolves automatically for known domains
- [ ] Invalid entity domains fail closed with clear error
- [ ] Min/max/step power validation works
- [ ] Priority ordering applies correctly
- [ ] Enable/disable override persists across reloads
- [ ] Priority override persists across reloads
- [ ] Reset overrides button restores defaults

## Control Loop Validation

### Mode Behavior
- [ ] Zero Export mode targets configured export value
- [ ] Soft Zero Export mode allows small export margin
- [ ] Self Consumption Max mode absorbs surplus aggressively
- [ ] Import Min mode avoids turning on coarse loads for small exports
- [ ] Manual Hold mode stops all control actions

### Deadband Behavior
- [ ] Controller holds state within deadband
- [ ] Controller exits deadband when error exceeds threshold
- [ ] Deadband override persists across reloads

### Battery Reserve Policy
- [ ] Battery reserve SOC threshold blocks discretionary absorption
- [ ] Import-pressure shedding still works when below reserve
- [ ] Battery reserve override persists across reloads

### Runtime Cap Safety
- [ ] `max_active_seconds` triggers preemption when exceeded
- [ ] Fixed loads turn off on runtime cap breach
- [ ] Variable loads wind back to minimum on runtime cap breach
- [ ] Runtime cap actions bypass normal min-on/cooldown blocks
- [ ] Current active runtime tracks correctly
- [ ] Active runtime today resets daily

### Guard Layer
- [ ] Min-on time prevents rapid cycling
- [ ] Min-off time prevents rapid cycling
- [ ] Cooldown time prevents rapid cycling
- [ ] Guard status shows why action blocked
- [ ] Planned vs guard-approved action counts differ correctly

## Executor Validation

- [ ] Switch devices respond to turn_on/turn_off
- [ ] Input boolean devices respond to turn_on/turn_off
- [ ] Number devices respond to set_value
- [ ] Input number devices respond to set_value
- [ ] Service call failures recorded in action history
- [ ] Successful actions recorded in action history
- [ ] Last action status sensor updates
- [ ] Last action result sensor shows service/data

## Entity Model Validation

### Controller Entities
- [ ] `switch.zero_net_export_enabled` toggles control
- [ ] `select.zero_net_export_mode` changes mode
- [ ] `number.zero_net_export_target_export` sets target
- [ ] `number.zero_net_export_deadband` sets deadband
- [ ] `number.zero_net_export_battery_reserve_soc` sets reserve
- [ ] `sensor.zero_net_export_status` shows current status
- [ ] `sensor.zero_net_export_reason` explains current state
- [ ] `sensor.zero_net_export_recommendation` suggests next action
- [ ] `sensor.zero_net_export_confidence` shows validation confidence
- [ ] `binary_sensor.zero_net_export_safe_mode` indicates safe mode
- [ ] `binary_sensor.zero_net_export_source_mismatch` indicates mismatch
- [ ] `binary_sensor.zero_net_export_stale_data` indicates stale sources
- [ ] `binary_sensor.zero_net_export_command_failure` indicates failures
- [ ] `binary_sensor.zero_net_export_battery_below_reserve` indicates reserve state

### Per-Device Entities
- [ ] Usable binary sensor reflects device readiness
- [ ] Enable switch controls device participation
- [ ] Priority number sets device priority
- [ ] Reset overrides button restores defaults
- [ ] Status sensor shows device state
- [ ] Planned action sensor shows intended action
- [ ] Guard status sensor shows why blocked/approved
- [ ] Planned power delta shows expected change
- [ ] Last requested power shows last target
- [ ] Last applied power shows last successful target
- [ ] Current active runtime tracks seconds
- [ ] Active runtime today tracks daily seconds
- [ ] Last action status shows recent outcome
- [ ] Last action result shows service/data details

### Diagnostics Entities
- [ ] Action history count updates
- [ ] Last action summary shows recent action
- [ ] Recent action summary shows last N actions
- [ ] Recent failure summary shows last N failures
- [ ] Last successful action summary shows last success
- [ ] Successful action count increments
- [ ] Failed action count increments
- [ ] Total successful count persists across reloads
- [ ] Total failed count persists across reloads
- [ ] Actions today resets daily
- [ ] Successful actions today resets daily
- [ ] Failed actions today resets daily
- [ ] Energy redirected today estimates correctly

## Dashboard Validation

- [ ] Zero Net Export panel opens from the Home Assistant sidebar without a websocket/bootstrap error
- [ ] Setup tab loads available source entities and ranked source suggestions
- [ ] Devices tab loads available device entities and guided entity suggestions
- [ ] Lovelace YAML imports without errors
- [ ] All entity IDs resolve to real entities
- [ ] Controller controls persist across reloads
- [ ] Per-device controls persist across reloads
- [ ] Override reset buttons work
- [ ] Attribute cards show configured vs effective values
- [ ] Dashboard is readable on mobile view

## Event Emission Validation

- [ ] `zero_net_export.action_applied` events fire on success
- [ ] `zero_net_export.safe_mode_entered` events fire on safe mode entry
- [ ] `zero_net_export.safe_mode_exited` events fire on safe mode exit
- [ ] `zero_net_export.source_mismatch` events fire on mismatch
- [ ] `zero_net_export.source_mismatch_cleared` events fire on recovery

## Diagnostics Export Validation

- [ ] Download diagnostics button works
- [ ] Payload includes controller state
- [ ] Payload includes validation state
- [ ] Payload includes device runtime state
- [ ] Payload includes action history
- [ ] Mapped entity IDs are redacted
- [ ] Device names are redacted
- [ ] Payload is valid JSON

## Persistence Validation

- [ ] Controller mode persists across reloads
- [ ] Controller enabled state persists across reloads
- [ ] Target export override persists across reloads
- [ ] Deadband override persists across reloads
- [ ] Battery reserve override persists across reloads
- [ ] Per-device enable override persists across reloads
- [ ] Per-device priority override persists across reloads
- [ ] Last requested/applied power persists across reloads
- [ ] Action counters persist across reloads
- [ ] Daily metrics reset at midnight (or persist correctly)

## Performance Validation

- [ ] Coordinator refresh interval configurable (default 30s)
- [ ] No excessive logging or spam
- [ ] No memory leaks over 24h operation
- [ ] No blocking operations on main thread
- [ ] Service calls complete within reasonable time

## Edge Cases

- [ ] Handles entity unavailable gracefully
- [ ] Handles entity unknown state gracefully
- [ ] Handles negative power values correctly
- [ ] Handles kW vs W unit conversion
- [ ] Handles missing battery entities (optional)
- [ ] Handles empty device inventory
- [ ] Handles single device inventory
- [ ] Handles many devices (10+) without performance degradation

## Documentation Validation

- [ ] README installation steps work
- [ ] CONFIG_FLOW.md matches actual UI
- [ ] CONTROL_LOOP.md matches actual behavior
- [ ] DASHBOARD_SETUP.md entity IDs are accurate
- [ ] ENTITY_MODEL.md lists all entities
- [ ] ARCHITECTURE.md matches actual code structure
- [ ] PRODUCT_SPEC_V1.md goals are met

## Sign-Off

| Validator | Date | Environment | Notes |
|-----------|------|-------------|-------|
|           |      |             |       |

### Issues Found

| Issue | Severity | Workaround | Fixed In |
|-------|----------|------------|----------|
|       |          |            |          |

### Final Recommendation

- [ ] Project ready for HACS community release
- [ ] Project needs additional validation
- [ ] Project needs specific fixes before release

---

**Note:** This checklist should be completed at least once on a real Home Assistant installation before marking v1 complete. The supervisor cron job can be disabled once validation confirms the project meets all MVP deliverables.
