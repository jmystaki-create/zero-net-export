# Implementation Plan

## Phase 1 — Spec and scaffold
- create repo scaffold
- freeze v1 product scope
- define entity model
- define mapped source roles

## Phase 2 — HA integration skeleton
- `custom_components/zero_net_export/manifest.json`
- config flow
- constants
- coordinator skeleton
- base entities

## Phase 3 — Source model
- mapping persistence
- source validation ✅ initial runtime layer implemented
- confidence scoring ✅ high / medium / low with safe-mode gating
- mismatch diagnostics ✅ reconciliation error and validation issue reporting
- config-flow validation UX ✅ setup now blocks missing/duplicate/non-numeric entity mappings
- operator remediation hints ✅ recommendation state now explains the most likely next fix
- richer calibration hints ✅ validation now emits a diagnostic summary, per-source diagnostics, and operator-facing calibration hints for sign / role / metadata debugging
- next: use those diagnostics to drive even smarter sign-learning once more live installs exist

## Phase 4 — Control engine
- controller loop ✅ initial explanation-first advisory planner now computes export error, holds inside deadband, and derives per-cycle device actions without actuating them yet
- deadband / hysteresis ✅ initial deadband hold behavior implemented
- fixed-load support ✅ advisory fixed-load turn-on / turn-off planning implemented
- variable-load support ✅ advisory variable-load increase / decrease planning implemented
- explanation state ✅ controller summary, controller reason, export error, and per-device planned action state now exposed
- controllable device inventory ✅ JSON-backed fixed/variable device model with runtime usability evaluation
- per-device explainability ✅ device status and usability entities now reflect why a device is or is not eligible
- runtime control guards ✅ per-device observed state, min-on / min-off timing, cooldown timing, and guard-approved-vs-blocked planned action state are now tracked and exposed
- guarded HA service executor ✅ guard-approved plans now attempt narrow live HA service calls for supported switch/number devices only
- explicit adapter metadata ✅ devices now resolve to a safe fixed/variable adapter model instead of relying only on raw entity-domain inference
- action outcome reporting ✅ controller state now reports last execution status/summary plus recent action-history attributes
- durable runtime control memory ✅ per-device last requested / last applied control targets plus cumulative action counters now persist across reloads
- richer diagnostics entities ✅ controller and per-device diagnostics now expose last-action / last-failure timing plus per-device last-result sensors, and runtime events fire for safe-mode and source-mismatch transitions
- action-history diagnostics slice ✅ controller now exposes recent action / recent failure / last successful action summary sensors, and each device now gets a dedicated last-action-status sensor so dashboards do not need to mine raw attributes for common operator checks
- variable target-aware planning ✅ variable-device increase/decrease planning now uses observed current target power as the baseline, respects configured min/max/step limits, and sheds conservatively toward configured minimums instead of blindly jumping to zero
- mode-specific control semantics ✅ Zero Export / Soft Zero Export / Self-Consumption Max / Import Min now alter effective target and absorption policy instead of sharing one generic planner path
- initial battery reserve policy ✅ a configurable battery reserve SOC threshold now blocks discretionary surplus-absorption actions whenever battery SOC is below reserve, while still allowing import-pressure shedding
- max-runtime safety preemption ✅ optional per-device `max_active_seconds` limits now let the planner pre-empt normal balancing to wind back overrunning variable devices or turn off overrunning fixed loads, with explainable runtime-cap policy metadata exposed through device state
- next: validate the new mode semantics, runtime-cap safety preemption, and battery-reserve gating against a real Home Assistant install, then tighten the dashboard around the operators' most useful diagnostics

## Phase 5 — UX entities and dashboard
- controller entities
- per-device entities ✅ initial status / usability / power entities from configured inventory
- per-device operator controls ✅ runtime-persisted device enable switches and priority numbers now let operators tune planner participation from Home Assistant
- basic Lovelace dashboard example ✅ first operator dashboard scaffold added under `examples/lovelace/zero_net_export_dashboard.yaml` with setup notes in `docs/DASHBOARD_SETUP.md`
- controller runtime overrides ✅ dashboard-facing enable/mode/target-export/deadband controls now persist through the integration runtime store instead of relying on in-memory state only
- dashboard reset controls ✅ controller and per-device override-reset buttons now provide an explicit path back to config defaults, and the main controller controls expose configured-vs-effective attributes for clearer operator UX
- next: tighten the dashboard against real installed entity ids and validate the override UX on a real Home Assistant install

## Phase 6 — Reporting and hardening
- packaging metadata ✅ manifest documentation/issue links now point at the real repository and `hacs.json` has been added so the project is easier to install/test as a real custom integration
- action history ✅ recent action history, last-success / last-failure summaries, and persistent action counters implemented
- daily summary metrics ✅ actions-today, success/failure-today, active-controlled-power-now, and estimated energy-redirected-today metrics now persist across reloads
- health / warning events ✅ safe-mode and source-mismatch transition events implemented
- safe mode handling ✅ degraded validation blocks control and leaves an explainable operator trail
- stale-data / command-failure health surfaces ✅ required-source freshness now drives explicit stale-data health entities plus safe-mode hold behavior, and recent failed commands now surface as an active health condition
- per-source diagnostics entity slice ✅ each mapped source now exposes direct status/reading/age/issue-count sensors plus a stale binary sensor, so dashboard work no longer depends on digging through controller attributes
- Home Assistant diagnostics export ✅ redacted config-entry diagnostics now capture controller/runtime/validation/device state for support and real-install debugging
- per-device runtime reporting ✅ current active runtime plus active-runtime-today telemetry now persist through the daily metrics store and surface as first-class per-device sensors for dashboards and runtime-cap review
- next: validate the packaged HACS/manual install path plus these health surfaces against a real Home Assistant install, and confirm the new per-device runtime telemetry is trustworthy enough before expanding longer-horizon reporting

## Phase 7 — Panel-app rebuild
- stabilize install/runtime behavior in Home Assistant
- remove UI-breaking integration packaging behaviors ✅ manifest icon packaging issue removed
- add panel registration and frontend shell ✅ first sidebar panel shell and websocket bootstrap state delivered
- add runtime operator mutations in-panel ✅ controller runtime overrides and per-device enable/priority overrides now flow through panel websocket commands instead of staying read-only
- create guided source/device setup UX ✅ initial panel source-mapping save flow now validates and persists source entities plus refresh interval from the Setup tab
- guided source remediation detail ✅ Setup now also surfaces mapped-source readings, units, device/state class metadata, and validation issues so operators can debug bad mappings inside the panel
- replace raw device inventory JSON for normal setup ✅ first panel-side add/edit/remove device inventory management now persists validated fixed/variable devices through structured panel forms
- add operator diagnostics/explanation UX ✅ panel diagnostics now exposes recent action history, source health, calibration hints, and per-device guard/result explanations from the existing backend state
- add operator settings/release UX ✅ Settings tab now exposes configured defaults, fleet health summary, panel-first workflow guidance, and direct docs/release/support links
- replace JSON/YAML-first operator workflow with panel-first workflow
- retain YAML dashboard as fallback/debugging surface

## Phase 8 — Future enhancements
- forecast-aware optimization
- tariff-aware strategy
- direct inverter/export-limiter adapters
- richer analytics UI
