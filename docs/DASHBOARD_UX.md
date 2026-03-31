# Dashboard and UX

## Primary dashboard goals
- show current energy picture clearly
- show controller state clearly
- show active decisions clearly
- keep operator override simple

## Main dashboard sections

### 1. Live Overview
- solar now
- home load now
- battery SOC and charge/discharge
- grid import/export now
- current target export
- current mode

### 2. Controller Status
- enabled / disabled
- active / idle / safe mode
- current explanation
- source confidence
- clear configured-vs-effective controller tuning visibility
- one-tap reset back to config defaults for controller tuning and per-device operator overrides

### 3. Managed Devices
For each device:
- current state
- current power or nominal power
- priority
- runtime today
- enable / disable control
- reason for current state

### 4. Warnings
- source mismatch
- stale data
- missing mapped sensors
- device command failures
- health summary showing whether the current top issue is stale data, safe mode, or a recent command failure

### 5. Reporting Widgets
- export avoided today
- actions taken today
- runtime by device ✅ current active runtime and active-runtime-today sensors now exposed per managed device
- confidence trend (future)

## UX principles
- operator-first
- exception-first
- never hide active constraints
- every action should be explainable
- manual override must be obvious

## Current scaffold status

A first importable Lovelace scaffold now exists at `examples/lovelace/zero_net_export_dashboard.yaml`.

It currently provides:
- a live overview card set for solar / home / grid / battery / surplus
- controller state and recommendation grouping
- validation and recent action diagnostics grouping
- fleet summary metrics
- example fixed-load and variable-load device cards

This plain YAML dashboard is now considered a transitional operator surface only. The project direction has shifted toward a custom panel / app-like frontend, with the YAML dashboard retained as a fallback and debugging surface until the panel experience is ready.
