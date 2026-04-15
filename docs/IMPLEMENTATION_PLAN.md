# Implementation Plan

> Historical implementation note: `docs/SUPERVISOR.md` remains the active steering layer, `docs/UI_DESIGN.md` is now the active UI design source of truth, and `docs/UI_IMPLEMENTATION_MAP.md` is now the active UI implementation / phase / status source of truth. This file remains the longer historical implementation trail.

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
- guarded HA service executor ✅ guard-approved plans now attempt narrow live HA service calls for supported switch/light/number devices only
- explicit adapter metadata ✅ devices now resolve to a safe fixed/variable adapter model instead of relying only on raw entity-domain inference
- action outcome reporting ✅ controller state now reports last execution status/summary plus recent action-history attributes
- durable runtime control memory ✅ per-device last requested / last applied control targets plus cumulative action counters now persist across reloads
- richer diagnostics entities ✅ controller and per-device diagnostics now expose last-action / last-failure timing plus per-device last-result sensors, and runtime events fire for safe-mode and source-mismatch transitions
- action-history diagnostics slice ✅ controller now exposes recent action / recent failure / last successful action summary sensors, and each device now gets a dedicated last-action-status sensor so dashboards do not need to mine raw attributes for common operator checks
- variable target-aware planning ✅ variable-device increase/decrease planning now uses observed current target power as the baseline, respects configured min/max/step limits, and sheds conservatively toward configured minimums instead of blindly jumping to zero
- mode-specific control semantics ✅ Zero Export / Soft Zero Export / Self-Consumption Max / Import Min now alter effective target and absorption policy instead of sharing one generic planner path
- initial battery reserve policy ✅ a configurable battery reserve SOC threshold now blocks discretionary surplus-absorption actions whenever battery SOC is below reserve, while still allowing import-pressure shedding
- max-runtime safety preemption ✅ optional per-device `max_active_seconds` limits now let the planner pre-empt normal balancing to wind back overrunning variable devices or turn off overrunning fixed loads, with explainable runtime-cap policy metadata exposed through device state
- next: validate the new mode semantics, runtime-cap safety preemption, and battery-reserve gating against a real Home Assistant install, then keep strengthening the native diagnostics/support path around the operators' most useful troubleshooting signals

## Phase 5 — UX entities and optional dashboard scaffolding
- controller entities
- per-device entities ✅ initial status / usability / power entities from configured inventory
- per-device operator controls ✅ runtime-persisted device enable switches and priority numbers now let operators tune planner participation from Home Assistant
- basic Lovelace dashboard example ✅ first optional debug dashboard scaffold added under `examples/lovelace/zero_net_export_dashboard.yaml` with setup notes in `docs/DASHBOARD_SETUP.md`
- controller runtime overrides ✅ dashboard-facing enable/mode/target-export/deadband controls now persist through the integration runtime store instead of relying on in-memory state only
- dashboard reset controls ✅ controller and per-device override-reset buttons now provide an explicit path back to config defaults, and the main controller controls expose configured-vs-effective attributes for clearer operator UX
- next: validate the override UX and entity discoverability on a real Home Assistant install, while keeping the dashboard scaffold clearly optional and outside the supported operator path

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
- next: validate the packaged HACS/manual install path plus these health surfaces against a real Home Assistant install, confirm the new per-device runtime telemetry is trustworthy enough, and keep shifting operator-facing guidance into native Home Assistant surfaces where it improves reliability

## Phase 7 — Native-surface consolidation
- stabilize install/runtime behavior in Home Assistant ✅ live HA now reaches a loaded state on the current `0.1.80` repo release line, with native entities present again after the startup crash chain was narrowed and deferred release-metadata reads were fixed on hot paths
- remove the custom sidebar/panel route from the shipped integration ✅ `/zero-net-export` route, launcher assets, and panel registration removed
- keep bootstrap onboarding minimal ✅ add-integration flow still creates the backend entry with safe defaults
- keep Configure as the supported setup path ✅ source mapping, managed devices, and controller tuning stay in native Configure
- reduce native-flow JSON leakage ✅ managed-device Configure now supports native add/edit/remove flows for fixed and variable devices, with the raw inventory editor kept as an advanced recovery path
- improve support-surface coherence ✅ device-page support actions now include a combined support-center notification alongside setup checklist and detailed diagnostics snapshot actions
- be explicit about project maturity ✅ current guidance now treats the HA-first approach as correct but still transitional pending broader real-world validation
- reduce custom frontend dependency for normal operation ✅ no custom panel assets are required for setup or troubleshooting
- update repo guidance and validation docs ✅ active planning/docs now center native Home Assistant surfaces instead of the removed panel route
- command-center discoverability improved ✅ the Configure landing screen now summarizes source status, managed-device status, policy summary, and the recommended next section so operators no longer have to infer where to start
- policy-path discoverability improved ✅ the native policy screen now states whether policy tuning is actionable yet, or whether operators should fix source mapping or managed-device issues first
- known combined-grid energy and battery-SOC options-flow bug ⚠️ partially mitigated: `0.1.80` ships native picker-plus-manual-fallback paths for both combined/net grid energy and battery SOC, plus a clearer command-center summary, policy-readiness guidance, and stronger managed-device promotion guidance, so operators can paste the same entity ID when either selector still throws a field-level `Entity is neither a valid entity ID nor a valid UUID` error; next step is to validate both fallback paths in real Home Assistant, then keep simplifying the field-to-binding path until the picker no longer misfires

## Phase 8 — Future enhancements
- keep tightening native fleet management next, especially around validating the new unmanaged-candidate promotion flow in larger mixed-device installs and removing any remaining cases that still push operators back into raw JSON
- restructure the native surface model around clearer ownership boundaries: Controls, Sensors, Managed Devices, and Diagnostics
- move managed-device enablement, priority, and overrides fully into the Managed Devices workspace instead of leaking them into controller/brain surfaces
- introduce a deeper managed-device detailed-management path for spreadsheet-style fleet review and richer per-device inspection
- converge setup, diagnostics, support, and policy management into fewer clearer native operator surfaces as real-user feedback shows which notifications/entities remain redundant
- only revisit optional Lovelace/dashboard ergonomics later if real installs still expose a specific debug-visibility gap after Configure and the main native operator paths are clear
- forecast-aware optimization
- tariff-aware strategy
- direct inverter/export-limiter adapters
- richer analytics within native Home Assistant surfaces or optional Lovelace assets, not a separate supported UI

## Current execution note

If this file and `docs/SUPERVISOR.md` appear to disagree, follow the supervisor document for what should happen next and use this file to understand how the repo got here.
