# Real-Installation Validation Checklist

Use this checklist to validate Zero Net Export in a real Home Assistant environment before considering v1 complete.

Supervisor note: this document is the evidence ledger for the release gates defined in `docs/SUPERVISOR.md`.

## Next validation boundary

Supervisor note: this checklist is a validation ledger for the approved `0.1.91` / release `1.91` scope only.

Current release-boundary order:
1. `v0.1.89` and `v0.1.90` are historical. Do not reopen or defend them as satisfying the new requested UI.
2. James's latest screenshots clarified the target surface: the Zero Net Export **main integration page**, like the HomeKit integration examples, not the individual Zero Net Export device-info page.
3. The next approved scope is `0.1.91` / release `1.91`: show a `Managed Devices` list under Zero Net Export and an `Un Managed` list underneath it.
4. Managed loads and unmanaged candidates must appear as individual Home Assistant device rows in those lists.
5. The repo later froze `4c0d071` / `v0.1.94` after the earlier `db5c246` / `v0.1.92` and `026f189` / `v0.1.93` freezes while this checklist still belongs to the documented `0.1.91` scope; before any Home Assistant install, restart, fingerprint validation, or screenshot claim, ask James directly whether `v0.1.94` replaces the documented `0.1.91` release target or whether release execution returns to the approved `0.1.91` boundary.
6. Only after that release-target decision should the project ask James to accept or reject the closest native child-device representation, then approve exact release/deploy/restart validation for the chosen target.
7. No release/deploy validation is approved by this documentation update alone; implementation and later release work must stay inside this exact scope.

Repo-side helper for mixed-build checks:
- Run `python3 scripts/validate_install_fingerprint.py /path/to/home-assistant/config/custom_components` in this repo before trusting deploy or validation results. It captures `tmp/expected-install-fingerprint.json`, compares the live install, saves `tmp/install-fingerprint-compare.json`, and exits non-zero on mismatch. You can point it at the Home Assistant config directory, the `custom_components` directory, or the installed `custom_components/zero_net_export` directory itself, as long as that install path is outside this repo. If the remote Home Assistant shell does not expose `python3`, keep running the validator from this repo and add `--ssh-host <user@host>` plus `--ssh-port <port>` so the live install path is inspected over SSH without remote Python. For release/deploy boundaries, the helper now keeps `expected_commit`, `expected_component_commit`, and `preferred_validation_commit` aligned on the latest component-changing commit, while exposing full repo HEAD separately as `repo_head_commit`, so doc-only or bug-tracker-only commits do not create false deploy-candidate drift. Compare that component anchor, tracked-file hashes, and match verdict against the installed package details shown in Zero Net Export Configure or the device-page Review diagnostics / Review diagnostics snapshot actions.
- If you need to overwrite a mixed manual install from one exact repo build first, ask James directly to approve deploy/restart before using deploy commands. After approval, run `python3 scripts/deploy_exact_repo_build.py /path/to/home-assistant/config` (or point it at the live Home Assistant `custom_components` or installed `custom_components/zero_net_export` path outside this repo). If you want to sanity-check the resolved destination first, add `--dry-run`. The deploy helper replaces the destination component directory instead of layering files onto an older copy, keeps a timestamped backup by default, and then runs the same fingerprint validation against the deployed path before restart. If repo-only docs moved since the last component change, pin the deploy with `--expected-component-commit <commit>` instead of treating repo HEAD as the shipped target.
- If you need the split steps for debugging, run `python3 scripts/print_expected_install_fingerprint.py --write-json tmp/expected-install-fingerprint.json`, then `python3 scripts/compare_install_fingerprint.py /path/to/home-assistant/config/custom_components --expected-json tmp/expected-install-fingerprint.json --write-json tmp/install-fingerprint-compare.json`. The compare script exits non-zero on mismatch, fails fast if the path does not actually contain `zero_net_export/manifest.json`, refuses repo-local paths so a repo copy cannot be mistaken for live validation, and can save the full comparison verdict as validation evidence.

For `0.1.91`, validation is only about the main integration page device lists:

1. Open `Settings -> Devices & Services -> Integrations -> Zero Net Export`.
2. Confirm a visible `Managed Devices` group/list appears under Zero Net Export.
3. Confirm managed loads appear as individual Home Assistant device rows in that group/list.
4. Confirm a visible `Un Managed` group/list appears below Managed Devices.
5. Confirm unmanaged candidates appear as individual Home Assistant device rows in that group/list.
6. Capture screenshot-grade evidence from the live installed build.

This is the live validation path for the `0.1.91` corrective release. Activity-history-only evidence, generic button rows, Configure-only screens, persistent notifications, API-only state, and screenshots of the individual device-info page do not count.

## Pre-Installation Checks

- [ ] Home Assistant version >= 2024.6.0
- [ ] HACS installed (if using HACS install path)
- [ ] Real solar/grid source entities available for native source-role setup; Energy dashboard setup is optional evidence only and is not required for the supported operator path
- [ ] At least one controllable load available (switch, light, or number entity)
- [ ] Battery system available (optional but recommended for full validation)

## Installation Validation

### HACS Install Path
- [ ] Repository added to HACS custom repositories
- [ ] Integration downloaded without errors
- [ ] Home Assistant restart completes successfully
- [ ] Integration appears in Settings → Devices & Services
- [ ] HACS shows the expected new version/tag before upgrade
- [ ] `python3 scripts/validate_install_fingerprint.py /path/to/home-assistant/config/custom_components` was run for the intended repo build before validation, producing `tmp/expected-install-fingerprint.json` and `tmp/install-fingerprint-compare.json`
- [ ] The saved comparison payload, or the equivalent split-step `print_expected_install_fingerprint.py` plus `compare_install_fingerprint.py` run, reports a full match for the install being tested, using a path that actually resolves to the live `custom_components/zero_net_export` component
- [ ] The installed package contents match the expected release (not an older cached/raw form-first build)

### Manual Install Path
- [ ] `custom_components/zero_net_export` copied to HA config
- [ ] Home Assistant restart completes successfully
- [ ] Integration appears in Settings → Devices & Services

### Restart / Reload Regression Check
- [ ] After a full Home Assistant core restart, the Zero Net Export config entry returns to a healthy loaded state instead of `failed_setup` / retrying setup
- [ ] Previously saved source roles are still present after restart
- [ ] Runtime source entities come back as normal Zero Net Export entities instead of disappearing behind a setup failure
- [ ] A config-entry reload after saving sources still succeeds when no code change is pending
- [ ] If a code fix was just installed, note whether only a full core restart, not a config-entry reload, was required to clear the failure

## Configuration Flow Validation

- [ ] Config flow opens when adding integration
- [ ] The config flow shown in the real HA install matches the currently tagged/published package
- [ ] Config flow is reduced to the intended bootstrap-only step rather than a giant raw source-role form
- [ ] Bootstrap step clearly explains that Sensors/source roles, Managed Devices onboarding, Controls policy/live mode, and Diagnostics continue at `Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure`
- [ ] Any remaining bootstrap field(s) have plain-language in-context help
- [ ] Entry can be created without choosing source roles during the initial config flow
- [ ] Clicking the integration gear/configure path no longer throws `Config flow could not be loaded: 500 Internal Server Error`
- [ ] Reopening Configure after restart still shows the previously saved source roles and current command-center guidance
- [ ] Options flow descriptions clearly explain the native setup, Managed Devices workspace, and Controls policy/live-mode paths
- [ ] Command-center landing screen shows headline decision, energy state, control decision/outcome, Fleet activity, and a current focus section that matches the real entry state
- [ ] Native setup clearly supports both combined/net grid sensors and separate import/export grid entities
- [ ] Selector fallback validation: if Home Assistant selector validation rejects a valid combined/net grid energy or battery SOC entity, capture the exact validation error or screenshot, then confirm the matching native manual fallback field lets the same entity ID complete setup while broader validation continues
- [ ] Managed-device flow supports adding a common fixed load without pasting JSON
- [ ] Managed-device flow supports adding a common variable load without pasting JSON
- [ ] Managed-device flow makes it obvious where to review, promote unmanaged candidates, edit, enable/disable, and remove devices
- [ ] Controls flow makes it obvious where to set mode, target export, deadband, reserve, and related behavior
- [ ] Controls flow states whether target export, reserve, deadband, and live mode are actionable yet, or whether sources/devices need attention first
- [ ] Advanced JSON editor remains available for recovery or bulk edits
- [ ] Entity normalization creates expected entity IDs

## Source Validation Layer

- [ ] Solar power entity shows valid reading
- [ ] Grid source layout selection matches the real install, combined/net or separate import/export
- [ ] If Home Assistant selector validation rejects a valid combined/net grid energy entity, record the exact screenshot or full validation text and then retry using the native manual fallback field with the same entity ID before continuing broader validation
- [ ] If Home Assistant selector validation rejects a valid battery SOC entity, record the exact screenshot or full validation text and then retry using the native manual fallback field with the same entity ID before continuing broader validation
- [ ] Record whether each fallback path actually saved successfully after the selector failed, so the next debugging pass can separate selector-only bugs from deeper source validation issues
- [ ] Grid export power reading is valid, whether derived from a combined/net source or mapped from a separate export entity
- [ ] Grid import power reading is valid, whether derived from a combined/net source or mapped from a separate import entity
- [ ] Home load power entity shows valid reading when configured, or inferred home load behaves plausibly when no dedicated home-load sensor is mapped
- [ ] Battery SOC entity shows valid reading (if configured)
- [ ] Confidence sensor reports "high" when all sources valid
- [ ] Once the coordinator loads after restart, required source roles recover as healthy runtime entities instead of staying stuck behind a setup failure
- [ ] Safe mode activates when required source missing
- [ ] Safe mode activates when source data stale (>120s)
- [ ] Source mismatch detected when reconciliation fails
- [ ] Per-source diagnostics show status/reading/age/issue_count
- [ ] Stale source binary sensor triggers correctly
- [ ] Calibration hints appear in validation diagnostics

## Device Model Validation

- [ ] Fixed device (switch/input_boolean/light) parses correctly
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
- [ ] `sensor.zero_net_export_recommendation` reports the current native next action
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
- [ ] Configure clearly communicates where Sensors/source roles, Controls, Managed Devices, and Diagnostics actions live
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
- [ ] The installed package fingerprint shown in Home Assistant matches the component-changing validation anchor (`expected_commit` / `expected_component_commit` / `preferred_validation_commit`) and tracked-file hashes from `python3 scripts/print_expected_install_fingerprint.py --write-json tmp/expected-install-fingerprint.json`
- [ ] The direct path check from `python3 scripts/compare_install_fingerprint.py /path/to/home-assistant/config/custom_components --expected-json tmp/expected-install-fingerprint.json --write-json tmp/install-fingerprint-compare.json` also agrees that the tested install is the intended build

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

### Final validation outcome

- [ ] Project ready for HACS community release
- [ ] Project needs additional validation
- [ ] Project needs specific fixes before release

---

**Note:** This checklist should be completed at least once on a real Home Assistant installation before marking v1 complete. Treat the associated release as blocked until the supervisor release gates in `docs/SUPERVISOR.md` are satisfied.
