# Product Spec v1 — Zero Net Export

## Product statement

Zero Net Export is a Home Assistant custom integration / mini app that controls a solar+battery home to keep grid export near a configured target, ideally **0 W**, using battery-aware logic and controllable loads.

## Product goals

- reduce or eliminate grid export
- improve self-consumption
- keep operator control and visibility high
- validate source entities before acting
- explain every control decision
- expose a useful dashboard and control surface inside Home Assistant

## Non-goals for v1

- full forecasting optimization
- deep tariff arbitrage
- vendor-specific inverter control integrations beyond generic abstractions
- fancy custom frontend from day one

## Core user stories

1. As an operator, I want to set a target export value in watts.
2. As an operator, I want to see current solar, home load, battery, and grid flow.
3. As an operator, I want the system to soak surplus via flexible loads without flapping devices.
4. As an operator, I want to know why the controller turned something on or off.
5. As an operator, I want warnings when the mapped energy sources do not reconcile.
6. As an operator, I want to disable or override devices manually.

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

## MVP deliverables

- config flow for source mapping
- source validation and confidence model
- controller with fixed + variable loads
- mode select + target export setting
- explanation / status sensors
- simple dashboard view / panel definition
- daily action/reporting skeleton
