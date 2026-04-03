# Dashboard and UX

## Primary dashboard / app goals
- show current energy picture clearly
- show controller state clearly
- show active decisions clearly
- keep operator override simple
- provide a comprehensive UI for setup, configuration, operation, and diagnostics
- eliminate dependence on poor raw device configuration UX for normal operators

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
- in-panel source diagnostics and recent action history for operator troubleshooting ✅ first panel diagnostics milestone delivered

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
- configuration must be guided, visual, and recoverable
- device setup must feel like a proper product workflow, not a developer-only JSON editor

## Current scaffold status

The shipped operator product now centers on the custom Home Assistant panel app with the following primary sections:

- Overview
- Setup
- Devices
- Diagnostics
- Settings

Those tabs are now the intended normal operator workflow for source setup, device onboarding, daily operation, troubleshooting, and release/support context.

The panel now also publishes an explicit readiness phase, checklist, and recommended next step so operators can tell whether they are blocked on source mapping, source health, device onboarding, or runtime eligibility without mentally stitching together multiple diagnostics sections.

The Devices tab now also ranks likely switch/number entities for the currently selected device kind and onboarding template, so panel-first device setup is less dependent on scanning a long unstructured entity list.

The Settings tab now also provides a copyable support snapshot that condenses release metadata, readiness, mapped-source health, configured-device state, and recent validation issues into one operator-facing text block for support and validation triage.

A first importable Lovelace scaffold now exists at `examples/lovelace/zero_net_export_dashboard.yaml`.

It currently provides:
- a live overview card set for solar / home / grid / battery / surplus
- controller state and recommendation grouping
- validation and recent action diagnostics grouping
- fleet summary metrics
- example fixed-load and variable-load device cards

This plain YAML dashboard is now considered a transitional operator surface only. The project direction has shifted toward a custom panel / app-like frontend, with the YAML dashboard retained as a fallback and debugging surface while real-world panel validation and final runtime hardening continue.
