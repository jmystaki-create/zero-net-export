# UI Implementation Map for the current Zero Net Export UI release line

This document is the single source of truth for the **implementation strategy and delivery status** of the native Home Assistant UI work.

If another project document appears to disagree about what has been completed, what remains, how the UI work is phased, or what the next UI milestone should contain, follow this file.

The intended product design now lives in `docs/UI_DESIGN.md`.

## Scope

The current live/UI correction history includes published `v0.1.88`, `v0.1.89`, and `v0.1.90` releases. `0.1.89` installed successfully and matched the deployed fingerprint, but live Home Assistant evidence showed it did **not** satisfy James's device-page Managed Devices expectation. The active UI validation target is therefore the published `v0.1.90` build at `d94436a`, not another attempt to defend or reword `0.1.89` or to reopen the completed `0.1.90` freeze/publication boundary.

Treat this document as the UI-shaping checklist for `0.1.90`, and do not use stale `0.1.83`, `0.1.85`, `0.1.86`, published-but-superseded `0.1.88`, or already-failed `0.1.89` wording as if those were still the future UI target.

`0.1.90` should focus on the concrete native-UI outcome James's screenshot proved missing:
1. a clear **Managed Devices surface on the Zero Net Export device page**
2. a clear **managed vs unmanaged** device experience visible without relying on Activity history
3. a clear **promote / vet / review** native flow for bringing unmanaged devices into the managed fleet
4. a clear native information architecture split between **Controls**, **Sensors**, **Managed Devices**, and **Diagnostics**

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
- Candidate shortlist and full-list pick flows exist, and they now share the same fit/warning signals plus the stronger review-first plus ready-candidate surfaced guidance.
- Candidate vetting/review now includes an explicit balanced review shape covering control suitability, safety/confidence, and operational value.
- Unmanaged backlog summaries now carry explicit ready-to-promote counts across the opening operator console, Managed Devices snapshots, and fleet-workspace overview surfaces instead of only naming review debt plus one ready candidate.
- Managed-device save flows now land on a native success summary with what changed plus the next Managed Devices or secondary review/audit path.
- Managed Devices selector labels and device-page promotion handoffs now use explicit promotion-workflow wording plus neutral ready-candidate handoffs instead of generic add-device helper wording or over-ranked next-pick phrasing when surfaced candidates are available.
- Managed Devices row labels now lead with `blocked`, `planned`, `attention`, or `active` when that higher-value state exists, so attention-first fleet rows scan more clearly than generic runtime text.
- Fleet review / bulk enable-disable scaffolding exists.
- The Zero Net Export device page now exposes a first-class managed-device review action, per-device managed review buttons for each configured load, and keeps the command-center guide in the main device surface rather than burying it under diagnostics-only categorization.
- Native Diagnostics/snapshot/checklist surfaces exist.
- The four-bucket IA language already exists in project wording: Controls, Sensors, Managed Devices, Diagnostics.

### Implemented but not yet delivered as a finished UI outcome
- Managed versus unmanaged is stronger in the repo candidate, but it is not yet proven visually crisp enough in the lived native HA experience.
- The promote / vet / review path is now materially more coherent in repo state, but still lacks live HA proof that it feels first-class instead of scaffolded.
- The four-bucket IA is more visible in the repo candidate, but it is still not yet proven in the installed product.
- Diagnostics text carries less UX burden than before, but live validation still needs to confirm the main operator burden really moved into Configure and Managed Devices.

### Still blocked or incomplete
- Live install drift is no longer the explanation for the current failure: `0.1.89` was deployed, restarted, and fingerprint-verified, and the device page still lacked the requested Managed Devices surface. Treat this as a product/UI gap, not an install-cache gap.
- Release execution now has a clean follow-up decision: do not rewrite the already-published `v0.1.89` tag, and do not reopen the completed `v0.1.90` freeze/tag/GitHub publication/install/fingerprint boundary. The installed Home Assistant package now reports `0.1.90` and matches `d94436a`; the remaining `0.1.90` gate is screenshot-grade device-page evidence and Managed Devices action drill-down validation.
- Treat the exact deploy boundary as the current component-changing build reported by `scripts/print_expected_install_fingerprint.py`, not as a hash that needs to be recopied into source-of-truth docs every time another UI commit lands.
- Repeated doc-only release-boundary refresh commits are process drift, not product progress. The helper-resolved component boundary must come from `scripts/print_expected_install_fingerprint.py` at deploy/validation time; later docs-only commits still do not create a new release target and should not displace the mapped Workstream A-D/F gap or a plain no-change report.
- Keep the ranking lesson intact: unchanged live exact-build mismatch is still real release drift, but it does not outrank the mapped visible UI gap. For `0.1.90`, do not spend watchdog or supervisor runs rephrasing release-boundary state unless live evidence, the helper-resolved component boundary, or operator instruction materially changes. If a repo inspection does not produce a device-page Managed Devices surface that can be proven in live HA, the work is not done.
- Live runtime stability still needs to be strong enough that the UI can be judged honestly in Home Assistant.
- The native Managed Devices path, promotion flow, and four-bucket IA still do not feel proven until the exact current helper-resolved build is reviewed in live Home Assistant.
- Screenshot-grade proof of the requested UI outcome does not yet exist.

## Historical 0.1.89 success criteria (failed on device-page evidence)

`0.1.89` was intended to count as a successful UI release only if all of the following were true, but James's live installed screenshot proved the device-page Managed Devices outcome was still missing. Keep this section as historical evidence for why `0.1.90` exists; do not use it as the active success gate or next release target.

1. **Managed vs unmanaged is visually obvious**
   - the Managed Devices path clearly shows the current managed fleet
   - the same path clearly shows unmanaged candidates ready for review or promotion, with review-first items easy to spot
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

## What counts as success for 0.1.90

`0.1.90` is successful only if the actual Zero Net Export device info page visibly shows Managed Devices state. A generic button row, Activity history, or a Configure-only explanation is not enough.

Required live evidence:

1. **Device-page Managed Devices surface is obvious**
   - the page visibly names Managed Devices as a current surface/cluster
   - the operator does not need to infer it from candidate Activity rows

2. **Managed/unmanaged state appears at a glance**
   - current managed fleet count/status is visible
   - unmanaged backlog/candidate state is visible
   - review-first or ready-next state is visible when candidates exist

3. **Current fleet action is visible before pressing a button**
   - blocker or next fleet action appears as current state, not only inside a persistent notification opened after pressing a button

4. **Deep workflow handoff is clear**
   - Configure -> Managed Devices remains the edit/promote workspace
   - the device page explains that handoff from current state rather than hiding the feature elsewhere

5. **Screenshot-grade proof exists**
   - a live HA screenshot/browser capture shows the above on the installed `0.1.90` build

See `docs/RELEASE_0.1.90_PLAN.md` for the detailed gap analysis and release plan.

## Phase plan

This section is now the explicit staged delivery map. Each phase should be implemented, validated, and then advanced rather than treated as one vague UI bucket.

## Detailed remaining work map

This is the detailed remaining-step map for finishing the full `docs/UI_DESIGN.md` scope and getting the corrective `0.1.90` device-page Managed Devices release out. The already-published and live-failed `0.1.89` line is historical evidence, not the active release target.
Use this list to decide what still has to be built, what has to be proven live, and what order the remaining work should happen in.

### Workstream A. Finish the opening operator console
**Goal**
- make Configure open as a dense, screenshot-grade operator console that clearly explains what the optimizer is doing now, what energy state it is reacting to, and what fleet state matters next

**Still to do**
1. Confirm the top board reads as one coherent operator console in the installed UI, not just in repo previews.
2. Tighten any remaining weak spots in the `Fleet activity` block so it tells the same managed/unmanaged story as the Managed Devices workspace below it.
3. Make sure the top board uses grouped operational signals, not helper-text narration, to carry the main legibility burden.
4. Verify the command-center modal and the device-page command-center guide stay compact and setup-first in live HA.

**Done when**
- James can open Configure and immediately understand decision, energy state, control outcome, and fleet posture without needing to read long prose.

### Workstream B. Finish the Managed Devices workspace
**Goal**
- make `Configure -> Managed Devices` feel like the unquestionable primary fleet workspace

**Still to do**
1. Make the managed-on-top / unmanaged-below split visually obvious on the exact deployed build.
2. Make managed summaries show enough operational detail that the top of the workspace feels active, not skeletal.
3. Validate on the exact deployed build that unmanaged summaries now read as actionable backlog mix, with review burden, ready-to-promote count, and first surfaced candidate quality all visible at a glance.
4. Remove any remaining wording, ordering, or summary behavior that makes Configure -> Managed Devices feel like a thin helper layer instead of the real fleet workspace.
5. Confirm blocked or review-first items are easy to spot at a glance.

**Done when**
- the workspace reads as a real managed/unmanaged fleet console in screenshots, not just a list of entities plus helper text.

### Workstream C. Finish the full promotion flow
**Goal**
- make shortlist -> review -> promote -> success feel like one native workflow

**Still to do**
1. Verify the shortlist and full-list selection screens still preserve enough managed/unmanaged context on the exact deployed build.
2. Verify candidate review clearly communicates usefulness, warnings, and operational value in real HA rendering.
3. Verify the exact deployed build keeps the new preset/save `Promotion path` context visible instead of regressing back into isolated forms.
4. Verify success landing clearly says what changed and what the next sensible action is.
5. Remove any remaining raw-id, helper-ish, or ambiguous wording that weakens trust in the promotion path.

**Done when**
- an operator can move from unmanaged discovery to successful promotion without losing context or wondering what to do next.

### Workstream D. Finish the four-bucket information architecture
**Goal**
- make Controls, Sensors, Managed Devices, and Diagnostics feel like distinct native homes

**Still to do**
1. Audit and remove any remaining content leakage between Controls, Sensors, Managed Devices, and Diagnostics.
2. Keep Controls focused on the controller brain and outcome, not fleet inventory.
3. Keep Sensors focused on telemetry and source health, not fleet management.
4. Keep Managed Devices focused on fleet operations and promotion flow.
5. Keep Diagnostics focused on troubleshooting, checklists, repairs, and install/package trust.
6. Recheck all jump-off text and section ownership text so the buckets reinforce one another instead of overlapping.

**Done when**
- an operator can tell where to go next without guessing, and the live UI no longer feels like overlapping narrative sections.

### Workstream E. Finish the secondary device-page review/audit path
**Goal**
- make the device page a genuinely useful secondary review/audit path without competing with Configure -> Managed Devices

**Still to do**
1. Validate live that the device-page managed review actions are clearly secondary to Configure -> Managed Devices.
2. Confirm the richer per-device audit rows, save feedback, and handoff text render clearly on the exact deployed build.
3. Make sure the installed device-page review path supports secondary review/audit inspection without diluting Configure -> Managed Devices as the primary workspace.

**Done when**
- the device page is clearly the secondary review/audit path, not a competing workspace.

### Workstream F. Finish notification and support-surface cleanup
**Goal**
- make runtime/setup/support signals compact, scannable, and consistent with the stronger UI design

**Still to do**
1. Validate the tightened runtime-attention notifications in the exact installed HA UI.
2. Validate the tightened setup-finished/setup-warning notifications in the exact installed HA UI.
3. Confirm spacing, headings, and next-step wording stay readable in real HA rendering.
4. Remove any remaining overly wordy support or diagnostics surfaces that still feel like walls of text.

**Done when**
- runtime and setup problems feel crisp, not noisy, and they point to the correct local/native path.

### Workstream G. Exact-build validation and release execution
**Goal**
- convert the published `v0.1.90` corrective release into a real installed and validated Home Assistant build for the device-page Managed Devices surface

**Still to do**
1. ~~Deploy/install the exact published `v0.1.90` build at `d94436a` to Home Assistant or verify HACS installs it.~~ Done: Home Assistant reports `sensor.zero_net_export_installed_version = 0.1.90`.
2. ~~Restart/reload Home Assistant and confirm the installed package matches `d94436a` with the fingerprint helper.~~ Done: documented SSH fingerprint validation reported `overall_match: true`.
3. Capture screenshot-grade live evidence that the device page visibly shows the Managed Devices surface.
4. Verify pressing the Managed Devices action opens the expected notification/review/window with current state.
5. If live evidence fails, log the exact installed UI gap before doing more wording or release-bookkeeping work.

**Done when**
- the published `v0.1.90` build is deployed, fingerprint-verified, and live-validated with screenshot-grade device-page Managed Devices evidence.

### Order of execution from here
1. Do not reopen completed `0.1.90` repo implementation, version bump, tag, push, or GitHub publication work unless new evidence proves the published artifact is wrong.
2. Do not repeat the now-completed `v0.1.90` install/update/restart/fingerprint loop unless new evidence changes the installed package state.
3. Perform live screenshot-grade acceptance review on the installed and fingerprint-matched `0.1.90` build.
4. If live review reveals real remaining gaps, log them explicitly and treat them as post-`0.1.90` work instead of silently rolling the cut line forever.
5. Only resume earlier A-D/F polish if live validation identifies a concrete native-HA UI gap or if installation/runtime blockers prevent judging the UI honestly.

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
- the repo-side blocking-I/O version-surface regression in `entity.py` has been removed, so the remaining work is now exact-build redeploy plus live log confirmation rather than another repo-side runtime patch

**Remaining**
- keep startup clean enough on the exact deployed build that the live UI can be judged without runtime noise dominating the result
- make sure the visible UI is not being masked by restored/unavailable entity failure states
- re-validate restart and reload persistence on the exact deployed build before treating the runtime correction line as closed

**Features in this stage**
- repairs-platform correctness
- entity recovery after restart
- non-blocking version/reporting path
- clean enough load path for UI inspection

### Stage 2. Setup-first command-center cleanup
**Purpose**
- make the command center a short, high-legibility setup-first operator surface instead of a support dump

**Completed**
- the command-center guide has been trimmed repo-side away from release/debug-heavy support posture and toward setup-first operator use
- the opening summary/board structure now exists in repo state
- the shared device-page command-center guide has also been realigned repo-side to the same setup-first `Now` / `Structured control board` / `Setup check` / `Basic setup paths` / `Bucket ownership` hierarchy, so this stage is no longer primarily blocked on more repo-side wording churn

**Remaining**
- verify on the exact deployed build that command-center content now reads as setup-first rather than release/debug-first
- confirm the installed modal hierarchy stays compact and scannable in real Home Assistant

**Features in this stage**
- headline decision summary
- compact top alert / next step
- setup-first board content plus the current operating picture
- clear jump-off to Sensors / Controls / Managed Devices / Diagnostics

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
- Configure -> Managed Devices summary blocks now split `Managed devices needing attention first` from `Other managed devices`, so blocked or actively planned rows stay visually ahead of steady-state rows throughout the native fleet forms
- the device page now exposes first-class `Open Managed Devices workspace` and `Open Managed Devices review` handoffs for secondary fleet review/audit without competing with Configure -> Managed Devices

**Remaining**
- make the managed-on-top / unmanaged-below structure visually obvious in live HA
- confirm on the exact deployed build that the device-page review/audit path reads clearly as secondary to Configure -> Managed Devices, rather than relying on repo copy alone
- confirm the current fleet action is obvious at a glance in the installed UI, not just in repo copy

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
- managed-device save flows now post a native success landing with what changed plus the next Managed Devices and secondary review/audit path
- candidate review now uses a balanced native summary of control suitability, safety/confidence, and operational value
- candidate discovery, shortlist, review, and managed-device review now share the same fit/warning guidance plus the stronger review-first plus ready-candidate surfaced cues

**Remaining**
- validate the full pick -> review -> promote journey in live HA so it feels first-class in the installed product rather than only coherent in repo state
- confirm the post-vetting handoff and success landing read clearly on the exact deployed build
- confirm the now-expanded blocker-first snapshots, managed/unmanaged context, and success landing feel like one obvious workflow in the installed UI rather than only in repo state

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
- the shared command-center/device-path guide now carries explicit current-focus and section-ownership handoff text

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
- the runtime-attention notification copy has been tightened repo-side into shorter `Now`, `Active blockers`, `Do next`, and `Open` sections instead of the earlier wall of text, so non-source runtime/install blockers no longer read like source-only repairs
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
- provide a secondary review/audit path for richer per-device and fleet-level inspection without bloating the top-level workflow

**Completed**
- concept and requirement are documented
- the Zero Net Export device page now exposes first-class `Open Managed Devices workspace` and `Open Managed Devices review` entry points
- the device page now also exposes per-device managed review buttons for each configured load, alongside the paired per-device status/reset actions
- the secondary review/audit handoff is now referenced directly from managed-device save feedback

**Remaining**
- validate the concrete native entry path in live HA, including the new per-device review buttons on the Zero Net Export device page
- confirm the richer per-device audit rows, save feedback, and handoff text render clearly on the exact deployed build
- make sure the installed device-page review path supports secondary review/audit inspection while keeping Configure -> Managed Devices as the clear primary fleet workflow

**Features in this stage**
- secondary fleet review/audit
- per-device review buttons from the native device page
- per-device operational detail
- spreadsheet-style or audit-style fleet inspection

### Stage 9. Live validation and release gate
**Purpose**
- prove the installed UI release with real Home Assistant device-page evidence

**Completed**
- release discipline and approval rules already exist elsewhere in project steering
- `v0.1.90` is frozen, tagged, pushed, and published at `d94436a`
- Home Assistant reports `sensor.zero_net_export_installed_version = 0.1.90`
- documented SSH fingerprint validation matched the installed package to `d94436a` with `overall_match: true`
- live API state exposes the `Managed Devices surface` row plus the Managed Devices device-page entity/action cluster
- documented API validation in this run pressed `button.zero_net_export_show_fleet_console` and `button.zero_net_export_show_managed_device_review`; both accepted `button.press` and updated current managed/unmanaged state attributes on installed `0.1.90`

**Remaining**
- capture screenshot-grade proof from the actual Zero Net Export device page showing the visible Managed Devices surface
- capture browser-visible proof that the Managed Devices action drill-down opens the expected native review/notification with current managed/unmanaged state; do not keep repeating API-only button.press checks as a substitute for screenshot-grade UI proof
- if the screenshot or drill-down fails, log the exact installed UI gap before doing more wording or release-bookkeeping work

**Features in this stage**
- exact-build validation
- live HA inspection
- screenshot-grade acceptance evidence
- release-by-release validation discipline

## Historical 0.1.89 release rollout view

This section records the already-published `0.1.89` rollout target after the earlier `v0.1.88` tag drifted behind later UI fixes. It is no longer the active release target: `0.1.89` was installed, restarted, fingerprint-verified, and then failed James's device-page Managed Devices screenshot expectation. Use it only as historical scope evidence; use the `0.1.90` sections above and `docs/RELEASE_0.1.90_PLAN.md` for current execution.

See `docs/RELEASE_0.1.89_PLAN.md` for the historical release execution record.

### 0.1.89 must include
1. **Command center reduction**
   - setup-first operator surface with the current operating picture still visible
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
   - Configure -> Managed Devices clearly feels like the primary fleet workspace, with the device page supporting secondary review/audit detail

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

### 0.1.89 should avoid being derailed by
- non-UI release churn unless required to keep HA loading
- optional dashboard work
- backend-only cleanup presented as shipped UI
- wording tweaks that do not produce a visible HA change

### 0.1.89 acceptance test (historical, failed on device-page evidence)
`0.1.89` was intended to be successful if James could open the live HA surfaces and see:
- the command center behaving like a setup-first operator console with the current operating picture obvious at the top, not like a setup-only helper screen
- Configure -> Managed Devices clearly functioning as the managed-devices workspace, with the device page acting as the secondary review/audit path
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
