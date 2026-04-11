# Real-Installation Validation Checklist

Use this checklist to validate Zero Net Export in a real Home Assistant environment before considering v1 complete.

Supervisor note: this document is the evidence ledger for the release gates defined in `docs/SUPERVISOR.md`.

## Recommended next validation run

If you are progressing the project right now, do this in order:

1. Install or upgrade the currently shipped package in a real Home Assistant instance.
2. Verify the intended operator path still works end-to-end:
   - add integration
   - complete bootstrap-only config flow
   - open Configure from the integration card
   - confirm it is obvious where sources live, where policy/settings live, and where managed-device work lives
   - map required sources in native setup, including the correct combined-versus-separate grid sensor layout
   - add at least one managed device through the native add/edit/remove flow in Configure, then edit it in place once
   - verify the JSON editor is no longer required for a normal single-device onboarding path
   - confirm readiness moves from installed -> mapped -> operational
3. Use at least one real controllable device and verify a real control loop decision/action path.
4. Test the **Configure** gear path from Home Assistant again and confirm it cleanly opens the native setup surface without any custom panel, sidebar, or external UI handoff.
5. If the install is good, package the result as the next release. If not, capture the exact failure surface and fix that before doing more UX expansion.

This is the current highest-value path because native onboarding is now the only supported product path.

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
- [ ] HACS shows the expected new version/tag before upgrade
- [ ] The installed package contents match the expected release (not an older cached/raw form-first build)

### Manual Install Path
- [ ] `custom_components/zero_net_export` copied to HA config
- [ ] Home Assistant restart completes successfully
- [ ] Integration appears in Settings → Devices & Services

## Configuration Flow Validation

- [ ] Config flow opens when adding integration
- [ ] The config flow shown in the real HA install matches the currently tagged/published package
- [ ] Config flow is reduced to the intended bootstrap-only step rather than a giant raw source-mapping form
- [ ] Bootstrap step clearly explains that source mapping and onboarding continue in the native Configure flow
- [ ] Any remaining bootstrap field(s) have plain-language in-context help
- [ ] Entry can be created without mapping sources during the initial config flow
- [ ] Clicking the integration gear/configure path no longer throws `Config flow could not be loaded: 500 Internal Server Error`
- [ ] Options flow descriptions clearly explain the native setup, managed-device, and controller-tuning paths
- [ ] Command-center landing screen shows current source status, managed-device status, policy summary, and a recommended next section that matches the real entry state
- [ ] Native setup clearly supports both combined/net grid sensors and separate import/export grid entities
- [ ] Known deferred bug tracked: in at least one real HA install, the combined/net grid energy field can still throw `Entity is neither a valid entity ID nor a valid UUID` even when a valid entity is selected; validate that the native manual fallback field shipped in `0.1.78` lets the same entity ID complete setup while broader validation continues
- [ ] Managed-device flow supports adding a common fixed load without pasting JSON
- [ ] Managed-device flow supports adding a common variable load without pasting JSON
- [ ] Managed-device flow makes it obvious where to review, edit, enable/disable, and remove devices
- [ ] Policy/settings flow makes it obvious where to tune mode, target export, deadband, reserve, and related behavior
- [ ] Policy/settings flow states whether policy tuning is actionable yet, or whether sources/devices need attention first
- [ ] Advanced JSON editor remains available for recovery or bulk edits
- [ ] Entity normalization creates expected entity IDs

## Source Validation Layer

- [ ] Solar power entity shows valid reading
- [ ] Grid source layout selection matches the real install, combined/net or separate import/export
- [ ] If combined/net grid energy selection still throws the known HA field-level entity/UUID error, record the exact screenshot and then retry using the new native manual fallback field with the same entity ID before continuing broader validation
- [ ] Grid export power reading is valid, whether derived from a combined/net source or mapped from a separate export entity
- [ ] Grid import power reading is valid, whether derived from a combined/net source or mapped from a separate import entity
- [ ] Home load power entity shows valid reading when configured, or inferred home load behaves plausibly when no dedicated home-load sensor is mapped
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

## Optional Lovelace / Native Surface Validation

- [ ] Configure opens and saves without any custom panel, sidebar, or external UI handoff
- [ ] Configure clearly communicates where sources, policy, managed devices, and support actions live
- [ ] Device-page diagnostic buttons create the expected native notifications
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

## Release / Distribution Validation

- [ ] `origin/main` contains the user-visible release commit
- [ ] Remote git tags include the intended release version
- [ ] GitHub release exists for the same version when using release-based HACS visibility
- [ ] `manifest.json`, `CHANGELOG.md`, git tag, and GitHub release version all agree
- [ ] The Home Assistant install path being tested is confirmed to be serving that same released package

## Documentation Validation

- [ ] README installation steps work
- [ ] README configuration guidance matches the actual Configure UI
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

**Note:** This checklist should be completed at least once on a real Home Assistant installation before marking v1 complete. Treat the associated release as blocked until the supervisor release gates in `docs/SUPERVISOR.md` are satisfied.
