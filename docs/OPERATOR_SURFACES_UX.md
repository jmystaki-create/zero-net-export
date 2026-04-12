# Operator Surfaces and UX

## Primary operator-surface goals
- show current energy picture clearly
- show controller state clearly
- show active decisions clearly
- keep operator override simple
- make native Home Assistant surfaces sufficient for setup, configuration, operation, and diagnostics
- eliminate dependence on poor raw device configuration UX for normal operators
- avoid any requirement for a separate custom or external UI

## Optional Lovelace fallback sections

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
- native source diagnostics and recent action history for operator troubleshooting ✅ first native diagnostics milestone delivered

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

The shipped operator product now uses only native Home Assistant integration and device surfaces for the supported path:

- Configure for source setup, managed devices, and controller tuning
- the integration device at **Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device** for diagnostics and setup/support buttons
- entities, notifications, automations/scripts, and Repairs for runtime and support workflows

Lovelace/dashboard views remain optional debug visibility inside Home Assistant, but they are not part of the supported operator path.

The native setup path now publishes an explicit readiness phase, checklist, and recommended next step so operators can tell whether they are blocked on source mapping, source health, device onboarding, or runtime eligibility without mentally stitching together multiple diagnostics sections.

The device inventory path is still JSON-backed today, but it is now intentionally framed as a native Configure workflow rather than any custom panel or external workflow.

The support snapshot remains available as a native device-page action that condenses release metadata, readiness, mapped-source health, configured-device state, and recent validation issues into one operator-facing text block for support and validation triage.

A first importable Lovelace scaffold now exists at `examples/lovelace/zero_net_export_dashboard.yaml`.

It currently provides:
- a live overview card set for solar / home / grid / battery / surplus
- controller state and recommendation grouping
- validation and recent action diagnostics grouping
- fleet summary metrics
- example fixed-load and variable-load device cards

This plain YAML dashboard is now considered optional debug visibility, not a supported operator surface. The project direction is explicitly native-only: reliable Home Assistant integration/device setup and troubleshooting surfaces are the supported UX, with Lovelace retained only as supplementary visibility rather than a separate supported UI path.
