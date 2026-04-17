# UI Design for Zero Net Export

This document is the single source of truth for the **product design** of the native Home Assistant UI.

If another project document appears to disagree about UI direction, supported operator surfaces, or section ownership, follow this file.

The implementation plan, delivery phases, completed work, and remaining work now live in `docs/UI_IMPLEMENTATION_MAP.md`.
Research inputs, external pattern synthesis, and the full redesign-question trail now live in `docs/UI_RESEARCH.md`.

## Product intent

Zero Net Export is a **native Home Assistant integration**.

Its supported operator UX is limited to native Home Assistant surfaces.
There is no supported custom sidebar, custom panel, external web UI, or parallel product UI.

The design goal is not to expose all backend capability.
The design goal is to make the operator path inside Home Assistant feel like a **serious, high-legibility operator console** that is still fully native to Home Assistant.

The product should feel:
- industrial
- crisp
- dense
- serious
- trustworthy
- operationally legible at a glance

It should not feel like:
- a decorative dashboard first
- a text-heavy guidance layer
- a pseudo-app awkwardly forced into Home Assistant
- a pile of entities that happens to contain an optimizer

## Supported operator surfaces

### 1. Configure flow
This is the primary operator workspace.

Configure should be the place where an operator can:
- understand what the optimizer is doing right now
- see the current energy state it is reacting to
- inspect the controller’s current decision and outcome
- manage the controlled device fleet
- review unmanaged candidates
- promote devices into the managed fleet
- access deeper telemetry, health, and troubleshooting paths

The Configure experience should behave like a **main landing flow with clear jump-off entries**, not a flat list of loosely related settings.

### 2. Native integration device path
Primary support, detail, and troubleshooting path:
- `Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device`

This path should expose:
- setup checklist
- diagnostics actions
- diagnostics snapshot access
- detailed runtime visibility
- repair guidance and next-step clues
- deeper device/diagnostics detail that does not belong in the primary landing console

### 3. Entities, notifications, automations/scripts, and Repairs
These remain valid native Home Assistant surfaces for runtime, support, and automation workflows.

They support the operator path, but should not replace the need for a coherent Configure experience.

### 4. Optional dashboards
Dashboards are optional supplemental visibility inside native Home Assistant, not part of the required operator path and not part of the current release gate.

Optional dashboards may still help with additional visibility, but they must remain clearly secondary to the native operator path.
They must not become:
- a required setup path
- the main product UI
- a workaround for weak native Configure / Managed Devices design

## Explicit non-goals

These are out of scope unless the project direction changes explicitly:
- reintroducing a custom sidebar or panel
- restoring `/zero-net-export` as a required route
- relying on custom frontend assets for core setup or troubleshooting
- treating optional dashboards as the supported operator surface
- solving native-HA UX weakness by shifting the real experience into dashboards

## Core UI problem to solve

The project already has substantial backend capability and meaningful native UI scaffolding, but the visible operator experience still does not feel fully productized.

The design problem is no longer just “make it clearer.”
The design problem is to make the native Home Assistant UI behave like a real operator product that clearly communicates:
- what the optimizer is doing right now
- what energy conditions it is reacting to
- what result it is currently producing
- what devices are already managed
- what devices are still unmanaged
- what warnings or blockers matter now
- where the operator should go next for control, fleet work, telemetry, or diagnostics

## Design intent for the primary landing experience

The opening experience should be a **dense native operator console**.

It should not be a minimal summary.
It should not hide core operating information one click deeper.
It should not rely on explanatory prose to create understanding.

The operator should first understand, in this order:
1. what the optimizer is doing right now
2. the current energy state it is reacting to

### Tone of the opening experience

The opening experience should feel like:
- a control console
- balanced and information-rich
- dense but grouped
- operational rather than decorative

It should not feel like:
- a single oversized hero card
- a lightweight summary page
- a narrative explainer

## Primary landing structure

The top of the Configure experience should be structured like this:

### 1. Headline decision summary
A clear, decision-oriented summary should appear above the structured board.

This summary should communicate what the optimizer is doing in operational language, for example:
- export too high, engaging load
- near target, holding
- battery reserve protected, not engaging
- no eligible device available
- source data stale, control paused

This summary should be concise, visible immediately, and interruption-capable when something important changes.

### 2. Structured control board
Below the headline decision summary, the main control board should show the full operating picture.

The control board should be grouped into four blocks:
- **Energy state**
- **Control decision**
- **Control outcome**
- **Fleet activity**

This grouping should carry the main legibility burden.
The product should prefer strong grouping over simplification by omission.

### Required top-board visibility

The top board should remain the real operational console.
It should not be reduced to only a few teaser metrics.

The intended top-board operating picture includes:
- decision summary
- solar power
- grid import/export
- home load
- battery SOC
- battery charge/discharge
- active managed load total
- target export
- current error vs target
- controller mode

These fields do not all need equal visual weight, but they should remain visible in the opening operator console.

## Managed Devices workspace

Managed Devices should appear directly below the top control board.

This section is the main fleet workspace, but it is intentionally secondary to live operational state.
The product should first show how the optimizer is behaving, then show the fleet that behavior depends on.

### Managed Devices layout

Managed Devices should be a **vertically split workspace**, not a side-by-side split.

Order:
1. **Managed devices on top**
2. **Unmanaged devices on bottom**

This structure is important because it makes managed vs unmanaged visually obvious while still preserving a clear scan order inside native Home Assistant constraints.

### Managed device rows

Each managed device should show operational detail at a glance, including:
- name
- type
- enabled/disabled
- priority
- current power or impact
- current state/action

Managed rows should feel operational, not skeletal, but they should not turn into a wall of deep per-device troubleshooting detail.

### Unmanaged candidate rows

Each unmanaged candidate should show a concise shortlist-style preview, including:
- name
- type
- likely usefulness
- key warning, if any

The product should not over-rank candidates or pretend it knows the one correct next choice.
The unmanaged section should be useful and review-friendly, but neutral in posture.

## Promotion workflow

Promotion must feel like a first-class workflow, not scattered scaffolding.

The intended promotion sequence is:
1. identify a candidate from the unmanaged section
2. open a balanced candidate review
3. understand fit, warnings, and likely operational value
4. promote into the managed fleet
5. receive a success summary with the next sensible action

### Candidate review requirements

Candidate review should be **balanced**, combining:
- control suitability
- safety / confidence
- operational value

It should help the operator answer:
- can this be controlled well?
- is it safe/confident enough to add?
- will it actually matter operationally?

### Post-promotion behavior

After promotion, the product should not dump the operator back cold.
It should show:
- success
- what changed
- the next sensible action

## Sensors and telemetry placement

The product still needs a clear telemetry model, but not all sensor detail should compete equally for top-level attention.

### Top-level telemetry
The most important sensors should remain visible in the control board.
These are the values required to understand live optimizer behavior.

### Deeper telemetry
Additional sensor detail should live below or around the Managed Devices area, or in deeper supporting paths, rather than becoming an oversized destination that competes with the main operator console.

The design intent is:
- critical telemetry in the console
- deeper telemetry available
- telemetry not over-elevated into a separate dominant experience

## Diagnostics and health posture

Diagnostics should be **always visible but secondary**.

Diagnostics is not a hidden basement that appears only when things are broken.
Health is part of the product’s normal posture.

Diagnostics should provide:
- health summary
- blocker summary
- diagnostics snapshot
- setup checklist
- repair guidance
- install provenance / package validation
- deeper troubleshooting path

But Diagnostics should not become the primary place where the product explains what it is or how to do normal work.

## Problem-signal behavior

When something is wrong, the signal should appear in two places:
1. **globally**, as a top-level alert summary
2. **locally**, in the relevant block or section

This is important because the operator should both:
- notice the problem quickly
- and understand its local context without hunting

Examples:
- source problem appears in the global alert summary and also in the relevant telemetry/control area
- fleet/configuration problem appears in the global alert summary and also in Managed Devices

## Required information architecture

The product still uses four conceptual buckets, but they should now be understood through the new design shape rather than as abstract labels alone.

### Controls
Controls owns the Zero Net Export brain and its current decision-making posture.

It should contain:
- controller mode
- target export
- deadband
- reserve and similar policy settings
- current decision summary
- controller state and outcome-related control context

It should not own:
- managed-device promotion as the primary path
- fleet inventory as the main content
- per-device management as the main interaction model

### Sensors
Sensors owns telemetry and source health.

It should contain:
- solar power and energy
- home load power
- grid import/export power and energy
- battery state of charge and charge/discharge
- source-health and freshness signals
- source mapping status and blocker visibility

The most critical subset belongs in the top console.
Deeper telemetry can live further down or behind deeper entries.

### Managed Devices
Managed Devices owns the controllable fleet.

It should contain:
- the current managed fleet
- unmanaged candidates ready for review
- promotion into the managed fleet
- enablement / disablement
- priority
- per-device overrides
- fleet review
- deeper device-management entry points

This must feel like a real native workspace.
It must not feel like a fallback helper section.

### Diagnostics
Diagnostics owns health, troubleshooting, and support.

It should contain:
- health summary
- blocker summary
- diagnostics snapshot
- setup checklist
- repair guidance
- install provenance / package validation
- the clearest next-step troubleshooting path

It should stay visible, but secondary.

## Navigation model

The preferred navigation model is **hybrid**:
- one main landing flow
- clear jump-off entries to deeper sections

The product should avoid both extremes:
- one giant unstructured flow
- or a fragmented maze of disconnected sections

## The three required visible outcomes for the current UI correction line

The current release line, now beyond `0.1.83`, is where the UI correction work must visibly land. Do not treat stale `0.1.83` wording as the active release target.

It must focus on these three visible outcomes:

### 1. Managed vs unmanaged must be visually obvious
An operator should immediately be able to tell:
- what is already managed
- what is still unmanaged
- where to review candidates next

The vertical split of Managed Devices is part of making this obvious.

### 2. Promote / vet / review must feel first-class
The promotion flow must feel like a coherent workflow inside the native product.

It must clearly support:
- choose a candidate
- review that candidate
- understand fit and warnings
- promote the candidate into the managed fleet
- receive a meaningful success landing

### 3. The product structure must be clearly felt
The operator should not have to guess where something lives.

The landing flow should make it obvious:
- where the system’s current decision is shown
- where live energy context is shown
- where the fleet is managed
- where health and troubleshooting live

## UX principles

- operator-first
- decision-first
- exception-visible
- never hide active constraints
- every action should be explainable
- manual intervention should be obvious when needed
- strong grouping beats shallow simplification
- device setup should feel like a product workflow, not a developer JSON workflow
- visibility in real Home Assistant matters more than repo-local elegance
- support wording should support the UX, not substitute for it

## Design rules for future decisions

When a field or action could live in more than one place:
- choose the section that best matches operator intent
- avoid duplication unless duplication is deliberately used for visibility plus context, as with problem signals
- prefer one strong obvious home over multiple weak homes

When deciding whether something counts as UI progress:
- it does not count unless it improves what James can actually see and use in native Home Assistant
- support copy, plumbing, release mechanics, or backend cleanup do not count as delivered UI on their own

When considering reductions in visible information:
- prefer grouping and hierarchy before hiding data
- this product should behave like an operator console, not a minimalist summary card

## Build checklist for the new design

This checklist translates the current design into implementation work buckets.

### A. Configure landing console
- [ ] Add or refine the headline decision summary so it always communicates the optimizer’s current action in decision-oriented language
- [ ] Reshape the landing surface into a dense grouped control board rather than a sparse summary or text-led screen
- [ ] Ensure the control board is grouped into:
  - [ ] Energy state
  - [ ] Control decision
  - [ ] Control outcome
  - [ ] Fleet activity
- [ ] Ensure the main operating fields remain visible in the top console:
  - [ ] solar power
  - [ ] grid import/export
  - [ ] home load
  - [ ] battery SOC
  - [ ] battery charge/discharge
  - [ ] active managed load total
  - [ ] target export
  - [ ] current error vs target
  - [ ] controller mode
- [ ] Make the top console feel like a real operator board, not a teaser summary

### B. Problem and health visibility
- [ ] Add or refine a top-level health / alert summary on the landing flow
- [ ] Ensure important problems surface both globally and locally in the relevant section
- [ ] Keep health visible but secondary, not hidden and not dominant

### C. Managed Devices workspace
- [ ] Reshape Managed Devices into a vertically split workspace
- [ ] Make the order explicit:
  - [ ] managed devices first
  - [ ] unmanaged candidates second
- [ ] Make managed vs unmanaged visually obvious without relying on long explanatory text

### D. Managed device row redesign
- [ ] Ensure each managed device row/card shows at a glance:
  - [ ] name
  - [ ] type
  - [ ] enabled/disabled
  - [ ] priority
  - [ ] current power or impact
  - [ ] current state/action
- [ ] Keep rows operational and scanable without collapsing into deep troubleshooting detail

### E. Unmanaged candidate shortlist redesign
- [ ] Ensure each unmanaged candidate row/card shows at a glance:
  - [ ] name
  - [ ] type
  - [ ] likely usefulness
  - [ ] key warning, if any
- [ ] Keep candidate surfacing neutral rather than strongly ranked
- [ ] Make review entry obvious from the shortlist row

### F. Candidate review and promotion flow
- [ ] Ensure candidate review presents a balanced view of:
  - [ ] control suitability
  - [ ] safety / confidence
  - [ ] operational value
- [ ] Ensure promotion feels like a coherent first-class workflow rather than scattered steps
- [ ] Add or refine a post-promotion landing that shows:
  - [ ] success
  - [ ] what changed
  - [ ] the next sensible action

### G. Telemetry and deeper sensor detail
- [ ] Keep critical telemetry in the top control board
- [ ] Move or preserve deeper telemetry in a secondary supporting path
- [ ] Avoid making deeper sensor detail compete with the main landing console

### H. Diagnostics path
- [ ] Preserve a deeper diagnostics path for:
  - [ ] health summary
  - [ ] blocker summary
  - [ ] diagnostics snapshot
  - [ ] setup checklist
  - [ ] repair guidance
  - [ ] install provenance / package validation
- [ ] Ensure Diagnostics remains visible in posture but secondary in hierarchy

### I. Navigation and flow coherence
- [ ] Keep one main landing flow
- [ ] Add or refine clear jump-off entries to deeper sections
- [ ] Avoid both a flat giant flow and a fragmented maze

## Gap analysis against current implementation state

This section compares the new design against the current known implementation state from `docs/UI_IMPLEMENTATION_MAP.md`.

### Already present enough to build on
These are already present in some meaningful form and should be refined rather than invented from zero:
- native-only product direction
- Configure as the primary operator path
- integration device path for support/diagnostics
- managed-device add/edit/remove flows
- unmanaged candidate discovery
- shortlist and full-list pick flows
- candidate vetting/review scaffolding
- fleet review / bulk enable-disable scaffolding
- native diagnostics/snapshot/checklist surfaces
- high-level four-bucket IA language

### Partially present but not yet delivered in the new design shape
These appear to exist in code/copy/scaffolding, but not yet in the stronger productized form required by the new design:

#### 1. Top landing console
Current state:
- the product already has native Configure direction and runtime/support surfaces
- but the implementation map says the UI is still described more than it is felt

Gap:
- the new design requires a dense operator console with a headline decision summary and four grouped blocks
- this specific control-board shape is not yet confirmed as delivered

#### 2. Managed vs unmanaged workspace clarity
Current state:
- managed-device flows exist
- unmanaged discovery exists
- summary text exists

Gap:
- the new design requires a vertically split workspace with managed on top and unmanaged on bottom
- the implementation map explicitly says managed vs unmanaged is not yet visually crisp enough in live HA

#### 3. Promotion flow coherence
Current state:
- shortlist exists
- full list exists
- vetting step exists
- save path exists

Gap:
- the implementation map says the flow still feels scaffolded instead of productized
- the new design now requires a clearly coherent review-first promotion sequence plus a post-promotion success landing

#### 4. Candidate review shape
Current state:
- review scaffolding exists

Gap:
- the new design now requires the review to explicitly balance suitability, safety/confidence, and operational value
- this exact balanced review shape is not yet confirmed as delivered

#### 5. Managed row density
Current state:
- fleet review and managed-device flows exist

Gap:
- the new design now requires a specific at-a-glance operational row shape for managed devices
- this exact row spec is not yet confirmed as delivered in the lived UI

#### 6. Unmanaged shortlist density
Current state:
- shortlist exists

Gap:
- the new design requires concise operational shortlist rows with usefulness plus key warning
- it also requires neutral posture rather than strong candidate ranking
- this exact shortlist presentation is not yet confirmed as delivered

#### 7. Problem signal behavior
Current state:
- support/checklist/diagnostics/Repairs surfaces exist
- support wording currently carries too much UX burden

Gap:
- the new design requires problems to appear both globally and locally
- this specific two-layer signal model is not yet confirmed as delivered

#### 8. Top-board telemetry visibility
Current state:
- telemetry and runtime visibility exist in some form

Gap:
- the new design explicitly requires the opening experience to show the full operating picture at the top
- this degree of visible density is not yet confirmed as delivered

#### 9. Diagnostics posture
Current state:
- diagnostics/support surfaces exist
- implementation map says diagnostics/support text carries too much UX burden

Gap:
- the new design requires diagnostics to remain visible but secondary
- this means some existing support burden likely needs to be redistributed into the landing console and Managed Devices workspace

### Still clearly not proven
These are the parts the implementation map already warns are not yet proven in the live product:
- screenshot-grade proof of the requested UI outcome
- live HA-visible evidence that the Managed Devices path feels like the central workspace
- live HA-visible evidence that the four-bucket structure is felt rather than merely described
- live HA-visible evidence that the promotion flow now feels first-class

### Practical implementation conclusion
The project is not starting from zero.
The likely work shape is:
1. keep the existing native scaffolding
2. reshape the landing flow into the new dense control-board model
3. strengthen Managed Devices into the new vertically split workspace
4. strengthen review/promotion into the new coherent workflow
5. reduce the amount of UX burden currently being carried by support/diagnostics wording
6. validate in live HA with screenshot-grade evidence

## Prioritized execution order

This section provides a prioritized build order from the checklist above.

### 1A. Highest-priority first implementation slice: headline decision summary

Start here first.

#### Why this slice is first
This is the single smallest slice that most directly changes what the operator understands immediately when opening the product.

It also aligns with the strongest design decisions already made:
- decision-first UX
- native operator-console posture
- top-level live-state clarity
- less dependence on explanatory prose

#### Goal of 1A
Add or refine the top-level headline decision summary so the product immediately tells the operator:
- what the optimizer is doing right now
- why it is doing that

#### What 1A should deliver
- a clearly visible top-of-screen decision summary on the Configure landing flow
- decision-oriented language rather than plain generic state labels
- wording that can represent normal operation and abnormal cases
- a summary that works as the operator’s first read before the rest of the control board

#### Example target language
The summary style should support patterns like:
- Export too high, engaging load
- Near target, holding
- Battery reserve protected, not engaging
- No eligible device available
- Source data stale, control paused

#### What should be true when 1A is done
- the first thing the operator sees is no longer vague or generic
- the product immediately communicates its current operating decision
- the landing experience feels more like an operator product and less like a loose settings surface
- this improvement is visible in live Home Assistant even before the rest of the full control board is completed

#### What 1A should not try to do
To keep the slice tight, 1A should not also try to complete:
- the full grouped control board
- the Managed Devices workspace redesign
- the full global/local problem-signal model
- the full promotion workflow redesign

It should be a narrow, visible, decision-first improvement.

#### Likely follow-on after 1A
Once 1A is working and visible, the next logical slice would be 1B, the structured control board beneath it.

## Relationship to other documents

- `docs/UI_DESIGN.md` is the source of truth for the intended product design.
- `docs/UI_DESIGN-old.md` preserves the previous version of this design document.
- `docs/UI_RESEARCH.md` captures the research base, external pattern synthesis, and redesign-session answers used to shape this version.
- `docs/UI_IMPLEMENTATION_MAP.md` is the source of truth for implementation status, completed work, remaining work, phases, and delivery strategy.
- `docs/UI_IMPLEMENTATION_SPEC.md` translates this design into a screen-by-screen implementation spec.
- `docs/UI_DESIGN_REVIEW.md` is the place for critique, review notes, screenshot-driven observations, and design feedback.
- `docs/SUPERVISOR.md` should reference these files rather than re-explaining the full UI design.
