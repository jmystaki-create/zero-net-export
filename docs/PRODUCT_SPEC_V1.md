# Product Spec v1 — Zero Net Export

## Product statement

Zero Net Export is a Home Assistant custom integration that keeps grid export near a configured target, ideally **0 W**, using battery-aware logic and controllable loads.

## Product goals

- reduce or eliminate grid export
- improve self-consumption
- keep operator control and visibility high
- validate source entities before acting
- explain every control decision
- make native Home Assistant surfaces sufficient for setup and troubleshooting
- reduce operator exposure to raw inventory JSON, even if JSON-backed persistence still exists internally for now
- keep installation stable so the integration does not negatively affect the wider Home Assistant UI
- stay honest that real-world validation is still in progress and treat confirmed install/operator friction as the main release driver

## Product reality for the current release line

The HA-first direction is correct, but the shipped implementation is still transitional:
- managed devices still persist through `device_inventory_json` under the hood
- native Configure can still become clumsy for larger or more heterogeneous fleets
- diagnostics/support are stronger than before but still span notifications, device buttons, entities, and Configure steps
- real-install validation is still incomplete and must continue to shape the roadmap

## Non-goals for v1

- full forecasting optimization
- deep tariff arbitrage
- vendor-specific inverter control integrations beyond generic abstractions
- reintroducing a custom sidebar/panel route as the supported setup UX
- full standalone add-on rewrite

## Core user stories

1. As an operator, I want to set a target export value in watts.
2. As an operator, I want to see current solar, home load, battery, and grid flow.
3. As an operator, I want the system to soak surplus via flexible loads without flapping devices.
4. As an operator, I want to know why the controller turned something on or off.
5. As an operator, I want warnings when the mapped energy sources do not reconcile.
6. As an operator, I want to disable or override devices manually.
7. As an operator, I want normal setup to succeed through Home Assistant's built-in Configure path.
8. As an operator, I want to add common managed devices without hand-authoring raw JSON.
9. As an operator, I want support/checklist/diagnostics guidance to feel like one coherent native workflow.

## Primary modes

- **Zero Export** — target 0 W export with configurable deadband
- **Soft Zero Export** — small allowed export margin
- **Self-Consumption Max** — absorb surplus aggressively
- **Import Min** — prefer lower import over perfect export control
- **Manual / Hold** — pause active control

## Device classes

### Fixed load
- on/off only
- nominal power known

### Variable load
- adjustable power level
- min / max / step power known

### Future classes
- direct export limiter
- battery policy endpoint
- inverter mode endpoint

## Control principles

- never act without validated source mapping
- prefer variable loads before toggling fixed loads
- enforce min on and min off durations
- respect battery reserve / policy limits
- degrade safely when source confidence is low
- keep actions explainable

## Key differentiators vs existing solutions

- source reconciliation and confidence scoring
- explicit export-target control
- operator dashboard and status model
- action explanation as a first-class feature
- health and mismatch reporting
- native Home Assistant setup/troubleshooting path

## MVP deliverables

- bootstrap-only config flow for fast entry creation
- native Configure workflow for source mapping and managed devices
- native add/remove managed-device flow for common fixed and variable devices, with JSON reserved for recovery/bulk edits
- source validation and confidence model
- controller with fixed + variable loads
- mode select + target export setting
- explanation / status sensors
- native diagnostics/support surfaces inside Home Assistant, including a combined support-center summary
- daily action/reporting skeleton
