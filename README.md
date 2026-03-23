# Zero Net Export

A Home Assistant custom integration / mini app for controlling solar, battery, grid, and flexible loads to keep export near a configured target — ideally **0 W**.

## Status

Scaffold plus runtime source validation, config-flow source checks, the first controllable-device inventory model, an explanation-first advisory planner, and a new control-guard layer that tracks per-device runtime eligibility for future actuation.

This project currently contains:
- product specification
- architecture notes
- entity model
- control loop outline
- dashboard / UX notes
- implementation roadmap
- Home Assistant integration scaffold with config flow and coordinator
- source validation with confidence scoring, reconciliation checks, safe-mode gating, and setup-time entity checks
- operator-facing validation recommendation state plus diagnostic summary, per-source diagnostics, and calibration hints for explainable remediation
- initial controllable device inventory parsing, usability evaluation, and per-device status entities
- explicit safe device-adapter resolution, so each device now records whether it is using an explicit adapter, an inferred supported adapter, or no safe adapter at all
- advisory control planning that converts export/import error plus usable devices into explainable per-cycle planned actions before guarded execution
- mode-aware planning semantics so Zero Export, Soft Zero Export, Self-Consumption Max, Import Min, and Manual / Hold now produce materially different control behavior instead of sharing one generic target rule
- a first battery reserve threshold now feeds the control loop: when battery SOC is below reserve, discretionary surplus-absorption actions are held so solar can recover the battery before extra controllable loads are enabled
- runtime anti-flap guard evaluation that tracks observed device state, min-on / min-off timing, cooldown timing, and whether each planned action is currently executable
- operator-facing action-history diagnostics, including recent action / failure summary sensors and per-device last-action-status sensors for cleaner dashboards
- persistent daily reporting metrics for actions today, success/failure today, active controlled power now, and estimated energy redirected today
- initial battery-reserve policy control, including a configurable reserve SOC threshold, operator-facing reserve state, and safe surplus-absorption hold behavior while the battery is below reserve
- explicit stale-data and command-failure health surfaces, including source-freshness tracking and safe-mode hold behavior when required mapped sources stop updating

## Product intent

Zero Net Export is designed to be:
- a **Home Assistant integration**, not just a YAML package
- a **mini app** with controls and dashboard surfaces
- **source-aware**, validating solar / grid / battery / load sensors before acting
- **explainable**, exposing what it is doing and why
- **safe**, with deadbands, hysteresis, minimum on/off times, and degraded modes

## Core capabilities

- keep export near a target wattage
- manage fixed and variable loads
- integrate battery-aware behavior
- expose entities for status, mode, confidence, and decisions
- support operator-facing controls and reporting

## Device inventory

The options flow now accepts a JSON array describing controllable devices. This is intentionally simple for the first milestone so the integration can reason about fixed and variable devices before it starts issuing actions.

Example:

```json
[
  {
    "name": "Hot Water",
    "kind": "fixed",
    "entity_id": "switch.hot_water",
    "adapter": "fixed_toggle",
    "nominal_power_w": 2400,
    "priority": 100,
    "enabled": true,
    "min_on_seconds": 900,
    "min_off_seconds": 900,
    "cooldown_seconds": 60
  },
  {
    "name": "EV Charger",
    "kind": "variable",
    "entity_id": "number.ev_charger_current_limit",
    "adapter": "variable_number",
    "min_power_w": 1400,
    "max_power_w": 7200,
    "step_w": 100,
    "nominal_power_w": 7200,
    "priority": 50,
    "enabled": true,
    "min_on_seconds": 300,
    "min_off_seconds": 60,
    "cooldown_seconds": 30
  }
]
```

Supported adapters right now:
- `fixed_toggle` → `switch.*` / `input_boolean.*` with `turn_on` / `turn_off`
- `variable_number` → `number.*` / `input_number.*` with `set_value`
- `adapter` is optional; when omitted, the integration safely infers one only for these known cases and blocks everything else with an explicit reason

Current behavior:
- invalid JSON is rejected in options flow
- fixed vs variable devices are validated structurally
- devices are marked usable only when source validation is healthy and the referenced entity exists
- each coordinator cycle produces an advisory control plan, including controller summary, export error, planned power delta, and per-device planned actions
- variable-device planning now uses each device's current target as its baseline, so increase/decrease actions are incremental and explain the requested new target rather than pretending every cycle starts from zero
- planner modes now alter control policy directly:
  - `zero_export` uses the configured export target directly
  - `soft_zero_export` tolerates a small export margin before responding
  - `self_consumption_max` biases slightly toward absorbing extra surplus
  - `import_min` avoids turning on coarse fixed loads just to chase small exports, while still shedding discretionary load on import pressure
- each planned action is checked against observed device state plus min-on / min-off / cooldown guards
- each configured device now also exposes an operator-facing enable switch and priority number so the planner can be tuned device-by-device from Home Assistant without rewriting the inventory JSON
- the main controller enable/mode/target-export/deadband controls now persist as operator runtime overrides, so dashboard tuning survives integration reloads while keeping config-flow values as the baseline defaults
- controller target/deadband tuning and per-device enable/priority overrides now also have explicit reset buttons, so operators can safely fall back to config defaults instead of treating runtime overrides as write-only
- guard-approved actions are now executed only through a narrow supported path:
  - fixed devices: `<entity domain>.turn_on` / `<entity domain>.turn_off`
  - variable devices: `number.set_value` or `input_number.set_value`
- unsupported variable entity types remain blocked with explicit per-device reason state rather than unsafe best-guess control
- controller state now includes last action status, last action summary, success/failure counts, recent action history attributes, explicit last-action / last-failure timestamps and device names, and persisted per-device last requested / last applied control targets across reloads
- runtime events now fire when safe mode enters/exits and when source mismatch appears/clears, so Home Assistant automations can react to validation-state changes without scraping attributes
- controller diagnostics now also expose concise recent-action, recent-failure, and last-successful-action summaries so operators can see control outcomes without opening raw history attributes
- daily reporting sensors now track actions today, success/failure split, active controlled power, and an estimated energy redirected today value based on observed active managed-device power integrated over refresh time; this is intentionally operational telemetry, not a revenue-grade energy meter
- required mapped sources are now checked for freshness; if a source stops updating for longer than about three refresh intervals (minimum 120 s), the controller raises stale-data health state and holds safe mode until live values resume
- a command-failure health indicator now stays active for a short retry window after the most recent failed guarded action, unless a newer successful action clears it
- per-source diagnostic entities now expose each mapped source's current validation status, latest reading, issue count, freshness age, and stale flag directly in Home Assistant without forcing operators to inspect raw coordinator attributes
- Home Assistant diagnostics export now provides a support-friendly redacted snapshot of controller state, validation state, per-source freshness, device runtime details, and recent action history

## Reference inspirations

Primary existing references identified during research:
- `jmcollin78/solar_optimizer` — strongest direct Home Assistant reference
- `springfall2008/batpred` — battery / optimization strategy inspiration
- `reptilex/tesla-style-solar-power-card` — dashboard ideas
- `Giorgio866/lumina-energy-card` — dashboard ideas
- `chrismelba/solar-optimiser` — adjacent concept

## Docs in this project

- `docs/REFERENCE_MATRIX.md`
- `docs/PRODUCT_SPEC_V1.md`
- `docs/ARCHITECTURE.md`
- `docs/ENTITY_MODEL.md`
- `docs/CONTROL_LOOP.md`
- `docs/DASHBOARD_UX.md`
- `docs/DASHBOARD_SETUP.md`
- `docs/IMPLEMENTATION_PLAN.md`

## Dashboard scaffold

A first plain-Lovelace operator dashboard scaffold now lives at:

- `examples/lovelace/zero_net_export_dashboard.yaml`

Use it as a starting point for:
- live solar / load / grid / battery overview
- controller status, reason, and recommendation
- validation and guard diagnostics
- fleet summary and per-device action visibility

Because Home Assistant entity ids can vary by integration entry naming, treat the YAML as a template and adjust the entity ids to match your actual installation.

## Recommended next step

Tighten the operator surface around the current backend:
- wire the new daily reporting sensors into the dashboard scaffold
- validate the stale-data / command-failure health surfaces against a real Home Assistant install
- expand supported variable/fixed device types carefully, only with clear service semantics
- validate the current entity ids and reporting semantics against a real Home Assistant install
