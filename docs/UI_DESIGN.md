# UI Design for Zero Net Export

This document is the single source of truth for the **product design** of the native Home Assistant UI.

If another project document appears to disagree about UI direction, supported operator surfaces, or section ownership, follow this file.

The implementation plan, delivery phases, completed work, and remaining work now live in `docs/UI_IMPLEMENTATION_MAP.md`.

## Product intent

Zero Net Export is a **native Home Assistant integration**.

Its supported operator UX is limited to native Home Assistant surfaces.
There is no supported custom sidebar, custom panel, external web UI, or parallel product UI.

The design goal is not to expose all backend capability. The design goal is to make the operator path inside Home Assistant feel clear, boring, obvious, and trustworthy.

## Supported operator surfaces

### 1. Configure flow
This is the primary operator workspace.

Configure should be the place where an operator can:
- map sources
- understand source-health blockers
- manage the Zero Net Export policy/brain
- manage the controlled device fleet
- reach diagnostics and next-step guidance

### 2. Native integration device path
Primary support and troubleshooting path:
- `Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device`

This path should expose:
- setup checklist
- support and diagnostics actions
- support snapshot access
- detailed device/runtime visibility
- repair guidance and next-step clues

### 3. Entities, notifications, automations/scripts, and Repairs
These remain valid native Home Assistant surfaces for runtime, support, and automation workflows.

They support the operator path, but should not replace the need for a coherent Configure experience.

### 4. Optional dashboard examples
Lovelace/dashboard assets are optional debug visibility only.
They are not part of the supported operator path and should not become the primary UX answer.

## Explicit non-goals

These are out of scope unless the project direction changes explicitly:
- reintroducing a custom sidebar or panel
- restoring `/zero-net-export` as a required route
- relying on custom frontend assets for core setup or troubleshooting
- treating optional dashboards as the supported operator surface

## Core UI problem to solve

The project already has substantial backend capability and some native UI scaffolding, but the visible operator experience still does not feel complete.

The design problem is to make the native Home Assistant UI clearly communicate:
- what the system knows
- what is broken
- what the operator should do next
- what is already managed by Zero Net Export
- what is still unmanaged but promotable
- where each type of task belongs

## Required information architecture

The UI must be organized into four clear buckets.

### Controls
Controls owns the Zero Net Export brain only.

It should contain:
- controller mode
- target export
- deadband
- reserve and similar policy settings
- controller state and current decision summary
- top-level control actions affecting the controller as a whole

It should not own:
- managed-device promotion
- managed-device enablement
- managed-device priority
- per-device overrides as the primary management path

### Sensors
Sensors owns source and system telemetry only.

It should contain:
- solar power and energy
- home load power
- grid import/export power and energy
- battery state of charge and charge/discharge
- source-health and freshness signals
- source mapping status and blocker visibility

It should not become a mixed surface for fleet operations.

### Managed Devices
Managed Devices owns the controllable fleet.

It should contain:
- the current managed fleet
- unmanaged candidates ready for promotion
- promotion of unmanaged devices into the managed fleet
- device vetting and review before promotion
- enablement / disablement
- priority
- per-device overrides
- fleet review
- deeper device-management entry points

This must feel like a real native workspace, not a fallback or a text-heavy helper.

### Diagnostics
Diagnostics owns troubleshooting and support.

It should contain:
- health summary
- blocker summary
- support snapshot
- setup checklist
- repair guidance
- install provenance / package validation
- the clearest next-step troubleshooting path

It should not become the place where normal device onboarding or normal controller operation is explained away.

## The three required visible outcomes for 0.1.83

The next release, `0.1.83`, is the **UI release**.

It must focus on these three visible outcomes:

### 1. Managed vs unmanaged must be visually obvious
An operator should be able to open the native Managed Devices path and immediately tell:
- what is already managed
- what is still unmanaged
- what looks ready for promotion next

This must be obvious without depending on long paragraphs.

### 2. Promote / vet / review must feel first-class
The native promotion flow must feel like a product workflow.

It must clearly support:
- choose a candidate
- review that candidate
- understand fit and warnings
- promote the candidate into the managed fleet

The operator should not have to mentally stitch together helper text across multiple surfaces.

### 3. Controls / Sensors / Managed Devices / Diagnostics must be clearly separated
The operator should not have to guess where something lives.

The UI should make it obvious:
- where to tune the controller
- where to inspect source and mapping health
- where to manage controllable loads
- where to troubleshoot and collect support evidence

## UX principles

- operator-first
- exception-first
- never hide active constraints
- every action should be explainable
- manual intervention should be obvious when needed
- configuration should be guided and recoverable
- device setup should feel like a product workflow, not a developer JSON workflow
- visibility in real Home Assistant matters more than repo-local elegance

## Design rules for future decisions

When a field or action could live in more than one place:
- choose the section that best matches operator intent
- avoid duplication across the four UI buckets
- prefer one strong obvious home over multiple weak homes

When deciding whether something counts as UI progress:
- it does not count unless it improves what James can actually see and use in native Home Assistant
- support copy, plumbing, release mechanics, or backend cleanup do not count as delivered UI on their own

## Relationship to other documents

- `docs/UI_DESIGN.md` is the source of truth for the intended product design.
- `docs/UI_IMPLEMENTATION_MAP.md` is the source of truth for implementation status, completed work, remaining work, phases, and delivery strategy.
- `docs/SUPERVISOR.md` should reference these files rather than re-explaining the full UI design.
- Older design-direction documents should defer to these two files to avoid stale drift.
