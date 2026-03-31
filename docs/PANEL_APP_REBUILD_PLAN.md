# Panel-App Rebuild Plan

## Why this rebuild exists

The current backend logic is valuable, but the current delivery shape is too integration-centric for the intended operator experience.

Observed problems:
- install/runtime polish issues need tightening
- the current setup experience is too dependent on Devices & Services forms
- the operator experience feels like a collection of entities and YAML instead of a coherent app
- the product should feel closer to an in-Home-Assistant app or control center

## New product direction

Zero Net Export should evolve into a:

- **custom integration backend** for runtime state, validation, planning, and execution
- **custom panel frontend** for onboarding, control, diagnostics, and operator workflow

This preserves the backend work already completed while replacing the operator-facing UX with an app-like experience.

## New goals

1. Stabilize install/runtime behavior in Home Assistant
2. Prevent the integration from negatively affecting broader HA UI rendering
3. Replace the current integration-first operator workflow with a panel-first workflow
4. Keep setup guided and visual instead of JSON-heavy wherever possible
5. Preserve explainability, source validation, and safe control behavior
6. Maintain release discipline while the rebuild is underway

## What stays

Keep these backend pieces:
- source mapping and validation engine
- confidence / mismatch / stale-data logic
- device model and adapters
- planner and control policy logic
- guarded executor
- diagnostics export and action history
- persisted runtime state

## What changes

Replace or significantly reduce reliance on:
- config-entry-first setup as the primary operator path
- plain Lovelace YAML as the main product UI
- raw JSON device inventory as the main operator configuration tool

Add / rebuild:
- panel route and panel frontend
- guided setup wizard
- guided device onboarding
- source-mapping UI with inline validation
- operator dashboard optimized for daily use
- diagnostics / history / explanation views inside the panel

## Phases

### Phase 1 — Stabilization
- remove risky manifest/icon behavior
- verify HA install does not break broader UI
- fix runtime compatibility issues revealed by real install
- keep HACS/manual install path working

### Phase 2 — App shell
- create panel registration
- establish frontend asset structure
- define backend-to-panel API or websocket contract
- ship first panel shell with placeholder sections

### Phase 3 — Guided setup
- source role mapping UI
- validation feedback in-panel
- operator-safe defaults
- options editing without raw JSON as the primary path

### Phase 4 — Operator workflow
- live overview
- controller mode/target controls
- managed device list
- warnings and diagnostics
- action history / explanation timeline

### Phase 5 — Completion
- confirm panel is the primary operator surface
- keep backend entities for automation and power users
- update docs and release notes to reflect app-first delivery

## Completion criteria

The rebuild can be considered complete when:
- install no longer causes broader HA UI regressions
- a usable panel exists in Home Assistant sidebar/navigation
- source setup and device setup can be completed through the app surface
- operator workflow no longer depends on raw YAML or JSON-first interaction
- docs and release notes reflect the new app-first product shape
