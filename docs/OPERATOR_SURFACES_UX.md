# Operator Surfaces and UX

## Primary operator-surface goals
- show current energy picture clearly
- show controller state clearly
- show active decisions clearly
- keep operator override simple
- make native Home Assistant surfaces sufficient for setup, configuration, operation, and diagnostics
- eliminate dependence on poor raw device configuration UX for normal operators
- avoid any requirement for a separate custom or external UI
- give each native section one clear ownership boundary so Controls, Sensors, Managed Devices, and Diagnostics do not blur together

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

## Current target information architecture

### 1. Controls
This should contain the Zero Net Export brain only:
- controller mode
- target export / deadband / reserve and similar control settings
- controller state and current decision summary
- top-level operator actions that affect the brain as a whole

This area should not own managed-device enablement, priority, or per-device overrides.

### 2. Sensors
This should contain source and system telemetry only:
- solar power / energy
- home load power
- grid import / export power and energy
- battery state of charge / charge / discharge
- other mapped source-health and freshness signals

This area should not be a mixed surface for managed-device controls.

### 3. Managed Devices
This should be the explicit fleet workspace for devices tagged into Zero Net Export control:
- device promotion from unmanaged to managed
- enablement / disablement
- priority
- per-device overrides
- fleet review and status

Managed-device controls should move here and out of the generic brain/control section.

### 4. Diagnostics
This should carry support and troubleshooting material:
- health summary
- blocker summary
- support snapshot
- checklist / repair guidance
- install provenance / package validation

### 5. Detailed Management
A deeper managed-device detail surface should exist behind Managed Devices, reachable from the native device view or a button/action path. This is the right place for a spreadsheet-style review of the whole managed fleet and for richer per-device detail.

### 6. Device detail view
From the native device view, operators should be able to select a managed device and inspect its detailed telemetry and runtime fields, such as runtime today, guard status, last action, planned action, planned delta, usable state, and other per-device operational fields.

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
