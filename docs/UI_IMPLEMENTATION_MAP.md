# UI Implementation Map for 0.1.83

This document is the single source of truth for the **implementation strategy and delivery status** of the native Home Assistant UI work.

If another project document appears to disagree about what has been completed, what remains, how the UI work is phased, or what the next UI milestone should contain, follow this file.

The intended product design now lives in `docs/UI_DESIGN.md`.

## Scope

`0.1.83` is the **UI release**.

This release should focus on the three native-UI outcomes James explicitly asked for:
1. a clear **managed vs unmanaged** device experience
2. a clear **promote / vet / review** native flow for bringing unmanaged devices into the managed fleet
3. a clear native information architecture split between **Controls**, **Sensors**, **Managed Devices**, and **Diagnostics**

If a change does not materially improve one of those visible outcomes, it should not displace this work unless it is required to keep the integration loading or to unblock live UI validation.

## Status summary

### Completed enough to build on
- Native-only product direction is established. There is no supported custom panel/sidebar/external UI path.
- Configure is already the intended primary operator path.
- The integration device path already exists as the native support and diagnostics path.
- Managed-device add/edit/remove flows exist.
- Unmanaged-candidate discovery exists.
- Candidate shortlist and full-list pick flows exist.
- Candidate vetting/review scaffolding exists.
- Fleet review / bulk enable-disable scaffolding exists.
- Native support/snapshot/checklist surfaces exist.
- The four-bucket IA language already exists in project wording: Controls, Sensors, Managed Devices, Diagnostics.

### Implemented but not yet delivered as a finished UI outcome
- Managed versus unmanaged is present in code and copy, but not yet visually crisp enough in the lived native HA experience.
- The promote / vet / review path exists in pieces, but still feels scaffolded instead of productized.
- The four-bucket IA is described more than it is felt.
- Diagnostics/support text currently carries too much of the product UX burden.

### Still blocked or incomplete
- Live runtime stability still needs to be strong enough that the UI can be judged honestly in Home Assistant.
- The native Managed Devices path still does not visibly feel like the strong central workspace James asked for.
- Screenshot-grade proof of the requested UI outcome does not yet exist.

## What counts as success for 0.1.83

`0.1.83` should not be called the UI release unless all of the following are true:

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

### Phase 0. Baseline and source-of-truth consolidation
Purpose:
- stop direction drift
- centralize design and implementation planning

Completed:
- established `docs/UI_DESIGN.md` as the design source of truth
- established `docs/UI_IMPLEMENTATION_MAP.md` as the implementation source of truth
- updated steering so `0.1.83` is explicitly the UI release

Remaining:
- repoint older project documents so they defer to these two files
- repoint cron prompts so they explicitly use these two files for UI steering

### Phase 1. Runtime stability required for honest UI validation
Purpose:
- ensure the integration loads cleanly enough that visible UI work can actually be judged

Completed:
- major startup-crash and release/runtime stabilization work has already happened in earlier corrective releases
- repairs-platform root cause was identified and a repo fix was added

Remaining:
- verify the current corrective path is sufficient for the integration to load cleanly in live HA
- make sure the visible UI is not being masked by restored/unavailable entity failure states
- keep only the minimum required stability work in scope here so UI delivery stays primary

Features:
- repairs-platform correctness
- entity recovery after restart
- clean enough load path for UI inspection

### Phase 2. Optional dashboard cleanup
Purpose:
- keep optional dashboard assets aligned with the native-only product direction
- prevent optional dashboard work from being mistaken for the `0.1.83` UI release itself

Completed:
- baseline Lovelace/dashboard assets already exist in the repo for reuse/reference

Remaining:
- keep optional dashboard docs/examples explicitly secondary to the supported native operator path
- trim or refresh optional assets only when they help debug visibility inside Home Assistant without changing product direction
- avoid letting optional dashboard work displace Configure, Managed Devices, Diagnostics, or live validation work

Features:
- optional System Dashboard example
- optional Managed Elements Dashboard example
- alignment of existing Lovelace/dashboard assets to the native-only design

### Phase 3. Managed Devices landing experience
Purpose:
- make the Managed Devices path feel like the obvious home for fleet work

Completed:
- managed-device flows and candidate discovery scaffolding exist
- fleet summary and candidate-summary text exists

Remaining:
- make the landing experience clearly separate:
  - current managed fleet
  - unmanaged candidates ready for promotion
- make the next recommended fleet action obvious at a glance
- reduce reliance on long descriptive paragraphs

Features:
- managed fleet summary block
- unmanaged candidate summary block
- at-a-glance next promotion target
- clearer visual ordering and ownership of fleet actions

### Phase 4. Promote / vet / review flow
Purpose:
- make unmanaged-to-managed promotion feel like a first-class native product flow

Completed:
- shortlist path exists
- full candidate list exists
- candidate vetting step exists
- template-selection and save path exist

Remaining:
- tighten candidate quality signalling
- improve the coherence of the pick -> review -> promote journey
- make post-vetting handoff into the managed fleet feel explicit and confident

Features:
- short opinionated candidate shortlist
- full candidate list fallback
- candidate fit summary and warnings
- explicit promotion handoff into managed fleet state

### Phase 5. Four-bucket IA cleanup
Purpose:
- make Controls, Sensors, Managed Devices, and Diagnostics feel like distinct homes instead of overlapping narrative sections

Completed:
- section labels and path language already exist
- high-level ownership direction already exists

Remaining:
- move or reframe any leaking content so each area has one clear purpose
- reduce duplication between support wording and normal operator surfaces
- make where-to-go-next obvious from the installed UI itself

Features:
- Controls owns controller brain/settings only
- Sensors owns telemetry/source health only
- Managed Devices owns fleet operations only
- Diagnostics owns troubleshooting/support only

### Phase 6. Detailed management path
Purpose:
- provide a deeper review path for richer per-device and fleet-level inspection without bloating the top-level workflow

Completed:
- concept and requirement are documented

Remaining:
- define the concrete native entry path
- define what detail belongs there versus on the top-level Managed Devices path
- make sure it supports richer device review without diluting the top-level fleet workflow

Features:
- deeper fleet review
- per-device operational detail
- spreadsheet-style or audit-style fleet inspection

### Phase 7. Live validation and release gate
Purpose:
- prove the UI release with real Home Assistant evidence

Completed:
- release discipline and approval rules already exist elsewhere in project steering

Remaining:
- verify the exact build in live HA
- gather screenshot-visible proof of the UI outcome
- only then ask James for formal release approval for the full release flow

Features:
- exact-build validation
- live HA inspection
- screenshot-grade acceptance evidence
- formal release approval boundary

## Non-goals for 0.1.83 unless required to unblock UI delivery

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
- phase-complete movement toward the `0.1.83` UI release

Do not let text-heavy guidance, diagnostics wording, release mechanics, or backend scaffolding masquerade as delivered UI.
