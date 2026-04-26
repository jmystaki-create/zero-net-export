# UI_IMPLEMENTATION_SPEC.md

This document translates the current `UI_DESIGN.md` into a screen-by-screen implementation specification for the native Home Assistant UI.

It is intended to answer:
- what the operator should see
- in what order they should see it
- what belongs at a glance versus one level deeper
- what the main Configure landing flow should contain
- what the Managed Devices workspace should contain
- what secondary review, telemetry, and Diagnostics paths should contain

This is an implementation-facing UI spec, not the higher-level design rationale.

## Relationship to other docs

- `docs/UI_DESIGN.md` = product design source of truth
- `docs/UI_RESEARCH.md` = research base and redesign-session decisions
- `docs/UI_IMPLEMENTATION_MAP.md` = delivery phases and status
- `docs/UI_IMPLEMENTATION_SPEC.md` = concrete screen/flow spec

---

## Screen 1. Configure landing screen

This is the main operator landing surface.

### Purpose

The operator should understand, in order:
1. what the optimizer is doing right now
2. the current energy state it is reacting to
3. the current control result
4. the current fleet state
5. whether there are any important health/blocker signals
6. where to go next for secondary review, telemetry, or Diagnostics work

### Visual posture

The landing screen should feel like:
- a dense operator console
- industrial and serious
- grouped, not decorative
- high signal, low fluff

It should not feel like:
- a tutorial page
- a wall of prose
- a sparse summary card
- a fake custom app squeezed into HA

---

## Screen 1A. Headline decision summary

This is the first element on the landing screen.

### Purpose

Instantly answer:
- what is the optimizer doing right now?
- why?

### Content

A concise decision-oriented line, for example:
- Export too high, engaging load
- Near target, holding
- Battery reserve protected, not engaging
- No eligible device available
- Source data stale, control paused

### Requirements

- always visible at the top
- short enough to scan immediately
- operational, not decorative
- should support interruption when conditions are abnormal

### When problems exist

If there is an active issue, the headline area may include a short alert summary above or adjacent to the decision summary.

---

## Screen 1B. Structured control board

This is the main high-density operator board below the headline summary.

### Purpose

Present the full operating picture without requiring drill-down.

### Board structure

The control board is grouped into four blocks:
1. **Energy state**
2. **Control decision**
3. **Control outcome**
4. **Fleet activity**

### Required visible fields

The board should keep these visible in the main console:
- solar power
- grid import/export
- home load
- battery SOC
- battery charge/discharge
- active managed load total
- target export
- current error vs target
- controller mode
- decision summary context/details

### Block details

#### Energy state block
Should show the operator what the system is seeing now.

Required fields:
- solar power
- grid import/export
- home load
- battery SOC
- battery charge/discharge

Optional but compatible additions if they help legibility:
- freshness indicator for critical sources
- source health indicator

#### Control decision block
Should show what the controller has decided and why.

Required fields:
- controller mode
- decision summary details
- relevant blocking reason, if any
- reserve / policy condition if it is the active reason for no action

This block is where structured decision context lives.

#### Control outcome block
Should show what result the controller is currently producing relative to the goal.

Required fields:
- target export
- current error vs target
- current action/result summary

This block should answer:
- are we close to target?
- is the controller succeeding?
- if not, how far off are we?

#### Fleet activity block
Should show what the managed fleet is currently contributing.

Required fields:
- active managed load total
- concise fleet activity summary

Optional additions if they remain legible:
- number of active managed devices
- shorthand current fleet state

---

## Screen 1C. Global alert / health summary

This is a visible but secondary health layer on the landing screen.

### Purpose

Ensure important issues are noticeable immediately without making diagnostics the main product surface.

### Content

Examples:
- source stale
- missing source roles
- battery reserve preventing action
- no eligible managed device
- fleet configuration issue

### Requirements

- must be visible on the landing screen when relevant
- must be concise
- must point toward the relevant local section, secondary review path, or Diagnostics path
- must not become a long explanatory essay

### Problem signal rule

Every important problem should appear in two places:
1. globally on the landing screen
2. locally in the relevant section/block

---

## Screen 1D. Managed Devices workspace summary block

This sits directly below the control board.

### Purpose

Provide the main fleet workspace directly after the live operating console.

### Structure

The Managed Devices workspace is vertically split into:
1. **Managed devices**
2. **Unmanaged candidates**

This is intentionally vertical, not side-by-side.

---

## Screen 2. Managed Devices, managed section

This is the top half of the Managed Devices workspace.

### Purpose

Let the operator see what is already under control.

### Each managed device row/card should show

At a glance:
- name
- type
- enabled/disabled
- priority
- current power or impact
- current state/action

### Design intent

This section should feel:
- active
- operational
- scanable
- like a real fleet workspace

It should not feel like:
- a static inventory list
- a deep diagnostics page
- a text-heavy settings list

### Secondary review/audit path

From each managed device, the operator should be able to reach secondary review/audit detail, such as:
- overrides
- more detailed state
- richer per-device review
- other advanced per-device operations

Those secondary audit details do not all belong in the main row.

---

## Screen 3. Managed Devices, unmanaged section

This is the bottom half of the Managed Devices workspace.

### Purpose

Let the operator see which unmanaged devices are candidates for promotion.

### Each unmanaged candidate row/card should show

At a glance:
- name
- type
- likely usefulness
- key warning, if any

### Design intent

This section should feel:
- concise
- review-friendly
- neutral in posture

It should not:
- over-rank the best candidate
- pretend the system knows the one correct answer
- overwhelm the operator with near-full detail before review

### Required interaction

From each unmanaged row, the operator should be able to open a full candidate review.

---

## Screen 4. Candidate review screen

This is the review screen opened from an unmanaged candidate.

### Purpose

Help the operator decide whether a candidate should be promoted.

### Review must balance three dimensions

1. **Control suitability**
   - can this device be controlled well?

2. **Safety / confidence**
   - is there ambiguity, missing information, or any reason to hesitate?

3. **Operational value**
   - will this actually help with export control in a meaningful way?

### Review outcome

From this screen the operator should be able to:
- understand the candidate
- understand the warnings
- promote the candidate
- back out without ambiguity

### Tone

This should feel like a product review step, not raw configuration data entry.

---

## Screen 5. Post-promotion success landing

This is shown after successful promotion.

### Purpose

Avoid dropping the operator back cold after a meaningful action.

### Must show

- success confirmation
- what changed
- the next sensible action

### Examples of next sensible actions

- review new managed device details
- tune priority
- check enablement
- return to the Managed Devices workspace

The product should give a clean landing, not a contextless bounce.

---

## Screen 6. Sensors telemetry/source-health detail

This is the Sensors-owned telemetry/source-health path beyond the top control board.

### Purpose

Expose more telemetry and source detail without overcrowding the primary landing console.

### Contains

- richer source-health detail
- mapping status
- freshness detail
- additional sensor detail beyond the top-level operating subset

### Design rule

Critical telemetry belongs in the control board.
Additional telemetry belongs here or in nearby secondary native paths.

This should not become the dominant primary experience.

---

## Screen 7. Diagnostics / health / troubleshooting path

This is the Diagnostics-owned troubleshooting path.

### Purpose

Diagnostics investigation, diagnostics capture, and explicit troubleshooting without carrying the entire meaning of the product.

### Contains

- health summary
- blocker summary
- diagnostics snapshot
- setup checklist
- repair guidance
- install provenance / package validation
- deeper troubleshooting routes

### Design rule

Diagnostics should remain visible in the overall product posture, but this secondary native path should be where richer troubleshooting lives.

It should not become the place where ordinary control or fleet work is primarily performed.

---

## Navigation behavior

### Preferred model

A hybrid navigation model:
- one main landing flow
- clear jump-off entries to deeper sections

### In practice

The user should be able to:
- land on the main console
- understand live state immediately
- scroll naturally into Managed Devices
- jump into candidate review or secondary device-page review/audit detail
- jump into Sensors telemetry or Diagnostics troubleshooting when needed

### Avoid

- one giant unstructured page with weak hierarchy
- many disconnected sections with no obvious primary path

---

## What should remain one level deeper

The following should generally remain one level deeper rather than crowd the main landing console:
- advanced per-device overrides
- richer secondary per-device audit detail
- full troubleshooting and diagnostics capture detail
- full sensor/source detail beyond the critical operating subset
- advanced provenance / install validation detail

---

## Acceptance shape for implementation

This implementation spec is on track when the delivered UI visibly demonstrates:
- a strong decision-oriented landing console
- a dense but grouped top board
- immediate managed vs unmanaged clarity
- a coherent review/promotion flow
- visible but secondary health/troubleshooting
- a credible native HA operator experience rather than a pile of supporting text
