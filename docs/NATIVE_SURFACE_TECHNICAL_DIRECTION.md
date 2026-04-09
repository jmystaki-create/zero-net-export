# Native Surface Technical Direction

## Current design decision

Zero Net Export keeps the Home Assistant integration backend, and its supported operator UX is limited to native Home Assistant surfaces. There is no supported custom sidebar, custom panel, or external UI path.

## Supported surfaces

### 1. Configure flow
Primary configuration path for:
- source mapping
- refresh interval
- managed device inventory
- controller defaults and tuning

### 2. Integration device page
Primary troubleshooting path for:
- setup checklist
- native diagnostics snapshot
- normal entity/status inspection

### 3. Dashboard examples
Optional debug visibility for people who want Lovelace cards inside Home Assistant. These are supplementary and explicitly not part of the supported operator path.

## Backend contract that still matters

The backend should continue to provide:
- validated source state
- explainable controller/runtime state
- redacted diagnostics export
- support snapshot generation for native notifications
- readiness/checklist generation for native notifications and diagnostics

## Explicit non-goals

- reintroducing custom panel registration
- restoring `/zero-net-export` as a required or supported onboarding route
- building new core setup flows that depend on custom frontend assets

## Practical implication for future work

If a workflow is required for normal install, setup, or troubleshooting, it should land in native Home Assistant surfaces. Custom UI work is out of scope unless the project direction changes again with fresh evidence.
