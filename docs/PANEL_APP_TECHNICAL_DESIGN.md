# Panel App Technical Design

## Purpose

This document turns the panel-app decision into a concrete implementation blueprint.

Zero Net Export will keep its Home Assistant integration backend, but the primary operator experience will move into a custom panel app inside Home Assistant.

## Design goals

- make the panel the primary operator surface
- keep backend entities/services available for power users and automation
- remove the need for JSON-first device configuration during normal use
- make setup, diagnostics, and ongoing operation feel like one coherent product
- preserve explainability and safe-control behavior

## App sections

The panel should be organized into clear operator-facing sections.

### 1. Overview
Purpose:
- current energy picture
- controller state
- top warnings
- quick actions

Content:
- solar / home / battery / grid cards
- current mode and target export
- active/safe-mode state
- top recommendation / explanation summary
- quick enable/disable and hold controls

### 2. Setup
Purpose:
- first-run onboarding
- source mapping
- validation remediation

Content:
- source role picker UI
- validation status per mapped source
- unit / device class / state class hints
- reconciliation health summary
- save/test flow

### 3. Devices
Purpose:
- first-class device onboarding and management

Content:
- device list table/cards
- add device flow
- fixed vs variable templates
- editable fields for:
  - name
  - entity
  - adapter
  - nominal/min/max/step power
  - priority
  - enable/disable
  - min on/off
  - cooldown
  - max active runtime
- per-device validation and capability status
- per-device current status and last action summary

### 4. Live Control
Purpose:
- real-time operation and intervention

Content:
- controller mode and target controls
- deadband and reserve controls
- active device participation
- current plan / blocked actions / executable actions
- operator overrides and reset actions

### 5. Diagnostics
Purpose:
- explainability and troubleshooting

Content:
- source diagnostics
- stale data indicators
- mismatch diagnostics
- command failure history
- action history timeline
- recent successful / failed action summaries
- support/download diagnostics affordance

### 6. Settings
Purpose:
- advanced controller and product settings

Content:
- refresh interval
- policy defaults
- release/version information
- links to changelog / docs
- advanced/debug toggles if needed

## Navigation model

The first panel shell can start as a single page with tabbed or segmented navigation:
- Overview
- Setup
- Devices
- Diagnostics
- Settings

Later it may evolve into nested routes if needed.

## Backend contract

The panel should not scrape entities ad hoc as its primary integration pattern.

Preferred model:
- backend exposes a structured API / websocket contract for app state
- panel reads one normalized payload for overview, setup state, devices, and diagnostics
- backend exposes targeted mutation endpoints for:
  - update controller settings
  - save source mappings
  - add/edit/remove devices
  - reset overrides
  - acknowledge or inspect validation issues

## Suggested backend payload groups

### App bootstrap payload
- integration version
- panel schema version
- install state
- whether setup is complete
- whether safe mode is active
- top health summary

### Overview payload
- solar / home / battery / grid summary
- mode / target / deadband / reserve
- explanation summary
- top warnings

### Setup payload
- mapped sources
- validation results by role
- freshness / metadata state
- reconciliation state
- remediation hints

### Devices payload
- normalized device list
- adapter status
- usability
- runtime constraints
- current state
- last action/result
- edit model for UI forms

### Diagnostics payload
- source diagnostics
- action history
- failure summaries
- health summary
- exported diagnostics availability

## Suggested backend mutations

- `zero_net_export/panel/get_state`
- `zero_net_export/panel/save_sources`
- `zero_net_export/panel/save_controller_settings`
- `zero_net_export/panel/add_device`
- `zero_net_export/panel/update_device`
- `zero_net_export/panel/delete_device`
- `zero_net_export/panel/reset_controller_overrides`
- `zero_net_export/panel/reset_device_overrides`

Names may change during implementation, but the panel should use explicit app-level mutations rather than forcing the operator through raw config-entry options.

## Delivery sequence

### Milestone 1 — Panel shell
- register panel ✅
- static shell with tabs/sections ✅
- placeholder content sourced from current backend state ✅ via `zero_net_export/panel/get_state`

### Milestone 2 — Overview + diagnostics
- show real current controller state ✅
- show top warnings and explanations ✅
- show fleet summary and recent actions ✅
- allow common runtime controller and device override mutations ✅ first panel websocket save/reset flows now wired to coordinator runtime overrides

### Milestone 3 — Setup UX
- source mapping UI ✅
- validation summaries and remediation ✅ first freshness and validation summaries now surface in-panel
- save/apply path ✅ source mapping saves now validate then reload the entry

### Milestone 4 — Device management UX
- add/edit/remove devices ✅ first panel-side CRUD editor now persists the device inventory without using the options-form JSON field
- guided templates ✅ fixed and variable device editor defaults now drive adapter/entity suggestions
- no raw JSON required for ordinary use ✅ for normal add/edit/remove device workflows

### Milestone 5 — Daily operator workflow
- live control page
- overrides, reset actions, per-device details
- settings/release surface ✅ Settings now exposes configured defaults, fleet health, workflow guidance, and support links
- complete app-first workflow

## Relationship to existing entities

Existing entities remain useful for:
- automation
- dashboards
- debugging
- HA-native power-user control

But they are no longer the primary intended operator interface.

## Completion signal

The panel-app architecture is successful when a normal operator can:
- install the backend safely
- configure sources through the app
- configure devices through the app
- monitor and control the system through the app
- understand warnings and actions without digging through raw entity attributes or JSON
