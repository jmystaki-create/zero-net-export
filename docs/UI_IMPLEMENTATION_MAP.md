# UI Implementation Map for the current Zero Net Export UI release line

This document is the single source of truth for the **implementation strategy and delivery status** of the native Home Assistant UI work.

If another project document appears to disagree about what has been completed, what remains, how the UI work is phased, or what the next UI milestone should contain, follow this file.

The intended product design now lives in `docs/UI_DESIGN.md`.

## Scope

The current live/UI correction line is now `0.1.86`, and `0.1.87` is the next UI-focused release line.
Treat this document as the UI-shaping checklist for `0.1.87`, and do not use stale `0.1.83`, `0.1.85`, or `0.1.86` wording as if those were still the future UI target.

`0.1.87` should focus on the three native-UI outcomes James explicitly asked for:
1. a clear **managed vs unmanaged** device experience
2. a clear **promote / vet / review** native flow for bringing unmanaged devices into the managed fleet
3. a clear native information architecture split between **Controls**, **Sensors**, **Managed Devices**, and **Diagnostics**

If a change does not materially improve one of those visible outcomes, it should not displace this work unless it is required to keep the integration loading or to unblock live UI validation.

## Status summary

### Completed enough to build on
- Native-only product direction is established. There is no supported custom panel/sidebar/external UI path.
- Configure is already the intended primary operator path.
- The integration device path already exists as the native support and diagnostics path.
- The command center now opens with a headline decision summary, a structured control board, and a top-level alert summary instead of only a looser helper-style status surface.
- Managed-device add/edit/remove flows exist.
- Managed Devices now overlays live runtime readiness/detail into fleet summaries and selector labels instead of showing config-only inventory placeholders.
- Unmanaged-candidate discovery exists.
- Candidate shortlist and full-list pick flows exist, and they now share the same fit/warning signals and stronger runtime ranking helpers.
- Candidate vetting/review now includes an explicit balanced review shape covering control suitability, safety/confidence, and operational value.
- Managed-device save flows now land on a native success summary with what changed plus the next Managed Devices or deep-review path.
- Fleet review / bulk enable-disable scaffolding exists.
- The Zero Net Export device page now exposes a first-class managed-device review action, per-device managed review buttons for each configured load, and keeps the command-center guide in the main device surface rather than burying it under diagnostics-only categorization.
- Native support/snapshot/checklist surfaces exist.
- The four-bucket IA language already exists in project wording: Controls, Sensors, Managed Devices, Diagnostics.

### Implemented but not yet delivered as a finished UI outcome
- Managed versus unmanaged is stronger in the repo candidate, but it is not yet proven visually crisp enough in the lived native HA experience.
- The promote / vet / review path is now materially more coherent in repo state, but still lacks live HA proof that it feels first-class instead of scaffolded.
- The four-bucket IA is more visible in the repo candidate, but it is still not yet proven in the installed product.
- Diagnostics/support text carries less UX burden than before, but live validation still needs to confirm the main operator burden really moved into Configure and Managed Devices.

### Still blocked or incomplete
- The live Home Assistant install no longer matches the current repo candidate, so exact-build redeploy plus fingerprint revalidation is blocking honest UI judgment.
- Live runtime stability still needs to be strong enough that the UI can be judged honestly in Home Assistant.
- The native Managed Devices path still does not visibly feel proven as the strong central workspace James asked for until the exact current build is reinstalled and reviewed.
- Screenshot-grade proof of the requested UI outcome does not yet exist.

## What counts as success for 0.1.87

`0.1.87` should not be called a successful UI release unless all of the following are true:

1. **Managed vs unmanaged is visually obvious**
   - the Managed Devices path clearly shows the current managed fleet
   - the same path clearly shows unmanaged candidates ready for promotion
   - the difference is obvious without depending on long explanatory text

2. **Promote / vet / review is visibly first-class**
   - the operator can clearly choose a candidate, review it, understand fit/warnings, and promote it into the managed fleet
   - the flow feels coherent in live HA rather than spread across helper text

3. **Controls / Sensors / Managed Devices / Diagnostics are clearly separated**
   - each bucket has one clear job
   - duplication and leakage across the four buckets is reduced
   - an operator can tell where to go next without guessing

4. **The result is visible in live Home Assistant**
   - James can inspect the live UI and see the intended outcome directly
   - repo code, docs, or wording alone do not count as UI completion

## Phase plan

This section is now the explicit staged delivery map. Each phase should be implemented, validated, and then advanced rather than treated as one vague UI bucket.

### Stage 0. Baseline and source-of-truth consolidation
**Purpose**
- stop direction drift
- centralize design and implementation planning

**Completed**
- established `docs/UI_DESIGN.md` as the design source of truth
- established `docs/UI_IMPLEMENTATION_MAP.md` as the implementation source of truth
- updated steering so the active release line, not stale `0.1.83` wording, is explicitly treated as the current UI correction target

**Remaining**
- repoint older project documents so they defer to these two files
- repoint cron prompts so they explicitly use these two files for UI steering

**Features in this stage**
- source-of-truth docs aligned
- project steering aligned
- automation prompts aligned

### Stage 1. Runtime stability required for honest UI validation
**Purpose**
- ensure the integration loads cleanly enough that visible UI work can actually be judged

**Completed**
- major startup-crash and release/runtime stabilization work has already happened in earlier corrective releases
- repairs-platform root cause was identified and a repo fix was added
- integration/entity load is no longer in the earlier hard-crash state

**Remaining**
- remove the current blocking-I/O version-surface regression from `entity.py`
- keep startup clean enough that the live UI can be judged without runtime noise dominating the result
- make sure the visible UI is not being masked by restored/unavailable entity failure states

**Features in this stage**
- repairs-platform correctness
- entity recovery after restart
- non-blocking version/reporting path
- clean enough load path for UI inspection

### Stage 2. Command center reduction to true setup-only scope
**Purpose**
- make the command center a short, high-legibility setup surface instead of a support dump

**Completed**
- the command-center guide has been trimmed repo-side toward setup-only posture
- the opening summary/board structure now exists in repo state

**Remaining**
- reduce command-center content further so it only covers setup, control posture, and next step
- remove release/install/debug clutter from the primary command-center experience
- tighten the wording and hierarchy so the surface feels like a basic setup console rather than a text-heavy helper

**Features in this stage**
- headline decision summary
- compact top alert / next step
- setup-only board content
- clear jump-off to Sensors / Controls / Diagnostics

### Stage 3. Top control board completion
**Purpose**
- make the opening experience feel like a serious operator console

**Completed**
- the command center now opens with a headline decision summary, a structured control board, and a top-level alert summary instead of only a looser helper-style status surface

**Remaining**
- ensure the four top-board groups are actually visible and legible in the installed UI
- keep the board dense but grouped, not narrative
- make sure the top board carries the required operational picture before the fleet workspace begins

**Features in this stage**
- Headline decision summary
- Energy state block
- Control decision block
- Control outcome block
- Fleet activity block

### Stage 4. Managed Devices workspace redesign
**Purpose**
- make Managed Devices feel like the obvious home for fleet work

**Completed**
- managed-device flows and candidate discovery scaffolding exist
- fleet summary and candidate-summary text exists
- Configure Managed Devices now overlays live runtime readiness/status into fleet summaries, usable counts, and selector labels
- managed-device rows now surface guard state, planned action, and last action status directly in the native fleet view
- selector ordering now surfaces blocked managed devices first, then actively planned loads, then healthy enabled/usable rows so the first exception stays visible in native fleet workflows
- the device page now exposes first-class `Review managed devices workspace` and `Review managed devices` handoffs for deeper fleet review without competing with Configure -> Managed Devices

**Remaining**
- make the managed-on-top / unmanaged-below structure visually obvious in live HA
- make the device-page deeper-review path feel clearly secondary to Configure -> Managed Devices, so it supports richer per-device inspection without competing with the primary fleet workspace
- confirm the next recommended fleet action is obvious at a glance in the installed UI, not just in repo copy

**Features in this stage**
- managed fleet summary block
- unmanaged candidate summary block
- vertically split workspace
- runtime-aware managed-device row detail
- clearer visual ordering and ownership of fleet actions

### Stage 5. Promote / vet / review flow completion
**Purpose**
- make unmanaged-to-managed promotion feel like a first-class native product flow

**Completed**
- shortlist path exists
- full candidate list exists
- candidate vetting step exists
- template-selection and save path exist
- managed-device save flows now post a native success landing with what changed plus the next Managed Devices and deep-review path
- candidate review now uses a balanced native summary of control suitability, safety/confidence, and operational value
- candidate discovery, shortlist, review, and managed-device review now share the same fit/warning guidance and stronger ranking helpers

**Remaining**
- validate the full pick -> review -> promote journey in live HA so it feels first-class in the installed product rather than only coherent in repo state
- confirm the post-vetting handoff and success landing read clearly on the exact deployed build
- make promotion feel like an obvious workflow, not a scaffold of helper buttons and summaries

**Features in this stage**
- shortlist and full candidate selection
- balanced candidate review
- explicit promotion handoff into managed fleet state
- native success landing after save

### Stage 6. Four-bucket IA cleanup
**Purpose**
- make Controls, Sensors, Managed Devices, and Diagnostics feel like distinct homes instead of overlapping narrative sections

**Completed**
- section labels and path language already exist
- high-level ownership direction already exists
- the shared command-center/device-path guide now carries explicit recommended-section and section-ownership handoff text

**Remaining**
- keep moving any leaking content so each area has one clear purpose
- confirm in live HA that the installed UI itself, not just the wording, makes where-to-go-next obvious
- stop treating button naming and popup text as equivalent to true IA delivery

**Features in this stage**
- Controls owns controller brain/settings only
- Sensors owns telemetry/source health only
- Managed Devices owns fleet operations only
- Diagnostics owns troubleshooting/support only
- top-level alert visibility with local follow-through

### Stage 7. Notification and support-surface cleanup
**Purpose**
- make warnings, setup prompts, and runtime-attention surfaces compact and scannable

**Completed**
- the runtime-attention notification copy has been tightened repo-side into shorter `Now`, `Mapped-source blockers`, `Do next`, and `Open` sections instead of the earlier wall of text
- the setup-finished/setup-warning notification copy has been tightened repo-side into shorter `Status`, `Do next`, `Fallback`, and `Open` sections instead of the earlier prose dump
- translation sync and repairs-copy regression coverage now keep those notification surfaces aligned between `strings.json` and `translations/en.json`

**Remaining**
- verify those tightened notification layouts on the exact installed build in live Home Assistant
- confirm Home Assistant's rendered modal spacing and heading hierarchy stay readable enough in the real UI

**Features in this stage**
- compact runtime-attention alerts
- compact setup alerts
- stronger section hierarchy
- shorter next-step wording

### Stage 8. Device-page detailed management path
**Purpose**
- provide a deeper review path for richer per-device and fleet-level inspection without bloating the top-level workflow

**Completed**
- concept and requirement are documented
- the Zero Net Export device page now exposes first-class `Review managed devices workspace` and `Review managed devices` entry points
- the device page now also exposes per-device managed review buttons for each configured load, alongside the paired per-device status/reset actions
- the deep-review handoff is now referenced directly from managed-device save feedback

**Remaining**
- validate the concrete native entry path in live HA, including the new per-device review buttons on the Zero Net Export device page
- refine what detail belongs there versus on the top-level Managed Devices path
- make sure it supports richer device review without diluting the top-level fleet workflow

**Features in this stage**
- deeper fleet review
- per-device review buttons from the native device page
- per-device operational detail
- spreadsheet-style or audit-style fleet inspection

### Stage 9. Live validation and release gate
**Purpose**
- prove the UI release with real Home Assistant evidence

**Completed**
- release discipline and approval rules already exist elsewhere in project steering

**Remaining**
- verify the exact current build in live HA
- gather screenshot-visible proof of the UI outcome during live validation
- make sure the installed product, not just repo wording, reflects the design intent

**Features in this stage**
- exact-build validation
- live HA inspection
- screenshot-grade acceptance evidence
- release-by-release validation discipline

## 0.1.87 release rollout view

This is the explicit `0.1.87` rollout target James asked for. It converts the staged design work above into the release feature set.

### 0.1.87 must include
1. **Command center reduction**
   - basic setup only
   - short top alert / next step
   - no release/install/debug clutter dominating the primary surface

2. **Top control board visibility**
   - headline decision summary
   - Energy state / Control decision / Control outcome / Fleet activity grouping
   - required operational metrics visible in the opening experience

3. **Managed Devices workspace redesign**
   - managed devices clearly on top
   - unmanaged candidates clearly below
   - visually obvious managed vs unmanaged split
   - Configure -> Managed Devices clearly feels like the primary fleet workspace, with the device page supporting deeper review

4. **Promotion workflow completion**
   - shortlist -> review -> promote path reads as one coherent native flow
   - balanced candidate review remains visible and understandable
   - promotion success gives a clear next action

5. **Four-bucket IA clarity**
   - Controls / Sensors / Managed Devices / Diagnostics visibly feel distinct
   - less cross-bucket leakage and duplication

6. **Notification cleanup**
   - runtime attention notification tightened and reformatted
   - setup-finished/setup-warning notification tightened and reformatted

### 0.1.87 should avoid being derailed by
- non-UI release churn unless required to keep HA loading
- optional dashboard work
- backend-only cleanup presented as shipped UI
- wording tweaks that do not produce a visible HA change

### 0.1.87 acceptance test
`0.1.87` is only successful if James can open the live HA surfaces and see:
- command center behaving like setup only
- Configure -> Managed Devices clearly functioning as the managed-devices workspace, with the device page acting as the deeper review path
- managed vs unmanaged visually obvious
- promotion/review workflow clearly visible
- notifications noticeably cleaner and tighter
- Controls / Sensors / Managed Devices / Diagnostics easier to distinguish at a glance

## Non-goals for the current UI release line unless required to unblock UI delivery

These should not displace UI work unless they are required to keep the integration loading or to make live UI validation possible:
- additional release-plumbing polish
- dashboard work that is outside the strategy defined in `docs/UI_DESIGN.md`
- support-text expansion without visible UX gain
- backend reshuffling that does not materially improve the requested native UI outcomes

## Working rule for future progress reports

Do not count work as UI progress unless it fits one of these categories:
- completed enough to build on
- implemented but not yet delivered as a finished UI outcome
- still blocked or incomplete
- phase-complete movement toward the current UI release line

Do not let text-heavy guidance, diagnostics wording, release mechanics, or backend scaffolding masquerade as delivered UI.
