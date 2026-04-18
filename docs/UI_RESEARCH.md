# UI_RESEARCH.md

This document captures the research base for a refreshed Zero Net Export UI design.

It is intended to synthesize:
1. the current local UI design document
2. relevant external reference patterns, including solar optimizer / energy-management integrations in the Home Assistant ecosystem
3. historical discussion and user feedback already captured in project memory and review notes
4. general product-design best practice for a solar optimizer control panel
5. the current UI implementation/status document
6. the design constraints imposed by native Home Assistant surfaces, especially the current device/configure format

This is a research and synthesis document, not yet the new design itself.

## Goal

Use this document to:
- collect the best available inputs before rewriting the design
- separate validated constraints from preferences
- identify where the current design is already strong
- identify where the current design is still too abstract or too text-heavy
- define the key open design questions that need James’s answers before a final redesign

---

## Input 1. Current local UI design document

Source:
- `docs/UI_DESIGN.md`

### What it already establishes well

The current design document already makes several strong decisions:
- Zero Net Export must remain a **native Home Assistant integration**.
- No custom sidebar, parallel app, or external web UI should be the supported path.
- **Configure** is the primary operator workspace.
- The integration device path is the main support and troubleshooting path.
- The product must be organized into four buckets:
  - Controls
  - Sensors
  - Managed Devices
  - Diagnostics
- The next visible milestone is a UI release centered on:
  - managed vs unmanaged clarity
  - promote / vet / review clarity
  - clear section ownership

### Strengths of the current design doc

- Clear product direction
- Strong anti-drift guardrails
- Explicit non-goals
- Good ownership model for the four buckets
- Strong insistence that visible native HA experience matters more than repo-local elegance

### Gaps in the current design doc

The current design doc is strong on principles, but still light on some concrete UX shape:
- It defines **what the UI must communicate**, but less concretely **how each screen should feel**.
- It says Managed Devices must feel like a real workspace, but does not yet define a decisive layout pattern for that workspace.
- It describes section ownership, but does not yet fully define the exact operator journey through Configure and device detail surfaces.
- It does not yet clearly separate:
  - top-level operational summary
  - next-best action guidance
  - fleet workspace tasks
  - troubleshooting/escalation tasks

### Research conclusion from input 1

The existing design is directionally right.
The redesign should build on it, not replace its core stance.
The main need is to turn principle-level guidance into a more specific, operator-shaped design.

---

## Input 2. Solar optimizer / related Home Assistant ecosystem patterns

Source basis:
- external ecosystem scan of Home Assistant solar / energy / battery / EV optimization integrations
- representative patterns surfaced by GitHub/HACS search results

### Patterns repeatedly seen in the ecosystem

Across energy-management and solar-optimization integrations, the common UI patterns are:
- a strong emphasis on **current energy state visibility**
- clear presentation of **grid / solar / battery / load inputs**
- operator focus on **what the controller is doing right now**
- explicit tuning controls for:
  - export/import targets
  - battery behavior
  - charging/discharging preferences
  - device participation / enablement
- clear distinction between:
  - observed telemetry
  - optimization policy
  - controllable devices / sinks
  - recommendations or interventions

### Useful lessons from that pattern set

1. **State summary matters first**
   Operators want to know quickly:
   - Are we exporting?
   - Are we importing?
   - Is the controller active?
   - Is battery state constraining behavior?
   - Which loads are currently engaged?

2. **Optimization UI works best when it separates “system state” from “things I can configure”**
   Mixing telemetry, policy, and device management into one undifferentiated surface creates cognitive drag.

3. **Device participation is critical**
   Solar optimizer value depends heavily on what loads are actually controllable, how suitable they are, and whether they are currently enabled.

4. **Warnings and constraints should be explicit**
   Operators need to know when control is blocked because of:
   - stale sensors
   - missing mappings
   - battery reserve constraints
   - disabled devices
   - invalid candidate setup

### Research conclusion from input 2

The external pattern set reinforces the current Zero Net Export direction:
- keep telemetry separate from policy
- give device participation its own strong surface
- make current system state and current constraints obvious

It also suggests the redesign should probably include a stronger “current state / current action / current blocker” layer than the current design doc spells out.

---

## Input 3. Historical discussion and user feedback

Source basis:
- project memory
- existing durable feedback already captured in local docs and notes
- thread-level recovery done during this session

### Recovered durable UI feedback

The clearest user feedback recovered so far is:
- keep this native to Home Assistant
- do not treat repo-side wording/plumbing as delivered UI
- make the next release the UI release
- make the UI visibly better in real Home Assistant
- make **managed vs unmanaged** visually obvious
- make **promote / vet / review** feel first-class
- make the four-bucket structure actually felt, not just described
- keep the add-integration/bootstrap path minimal
- if bootstrap/setup fields remain, explain them clearly in plain language next to the control

### Important interpretation of that feedback

The user is pushing against “design by explanation.”
That means:
- long paragraphs are not the answer
- support wording is not the answer
- diagnostics wording is not the answer
- visible operator flow is the answer

### Research conclusion from input 3

The redesign must reduce dependency on explanatory prose and increase structural clarity.
The operator should understand the product mostly by layout, grouping, status, and next actions, not by reading long descriptions.

---

## Input 4. Best practice for a solar optimizer control panel

This section is a product-design synthesis rather than a direct quote from one source.

### Best-practice principles

A strong solar optimizer control panel should make these things obvious in order:

1. **What is happening now**
- exporting/importing state
- battery state and role
- current controller mode/state
- whether the optimizer is acting, waiting, blocked, or degraded

2. **Why that is happening**
- source availability/health
- reserve/deadband/policy constraints
- no eligible managed load
- candidate/device configuration gaps

3. **What can be changed safely**
- policy knobs
- device enablement
- promotion of new controllable loads
- mapping fixes for missing sources

4. **What should happen next**
- next recommended corrective action
- next best promotion candidate
- next blocker to resolve

### Strong control-panel design characteristics

- compact top-level status summary
- clear separation between live telemetry and configuration
- exception-first guidance
- low ambiguity around device eligibility and participation
- obvious drill-downs for deeper detail
- plain language around constraints and side effects
- minimal need for operators to infer relationships from raw entities

### Anti-patterns

- mixing every type of object into one long Configure menu
- explaining the product mostly through long text blocks
- hiding blockers in diagnostics only
- making device onboarding feel like data entry rather than review/promotion
- making the operator hunt across multiple sections to answer one question

### Research conclusion from input 4

The redesign should probably be organized around three recurring operator questions:
- What is the optimizer seeing and doing right now?
- What is stopping it from doing better?
- Which controllable devices are available, managed, or worth promoting?

---

## Input 5. Current UI implementation/status document

Source:
- `docs/UI_IMPLEMENTATION_MAP.md`

### What it tells us about reality

The current implementation map is valuable because it distinguishes:
- what is already implemented enough to build on
- what exists only as scaffolding
- what is still incomplete in the lived HA experience

### Key implementation realities

Already present in some form:
- native-only direction
- configure as primary workspace
- integration device path
- managed-device add/edit/remove
- unmanaged discovery
- shortlist/full-list selection
- vetting/review scaffolding
- fleet review scaffolding
- support/checklist/snapshot surfaces

Not yet truly delivered:
- visually crisp managed vs unmanaged experience
- coherent first-class promote/vet/review experience
- four-bucket IA that is felt rather than described
- a Managed Devices surface that feels like the strong central workspace

### Research conclusion from input 5

The redesign should not pretend to start from zero.
It should assume there is already useful scaffolding and ask:
- what should be strengthened,
- what should be simplified,
- what should be promoted to first-class,
- and what should be removed or demoted because it is carrying too much explanatory burden.

---

## Input 6. Design constraints from native Home Assistant device/configure format

Source basis:
- current project constraints
- Home Assistant developer docs on device registry and native surface model
- known practical constraints from the project’s own current architecture

### Key native HA constraints

1. **A Home Assistant device is an entity grouping concept, not a custom app canvas**
   The device page can group entities, buttons, diagnostics, and related metadata, but it is not a blank-slate product screen.

2. **Configure flows are form/menu driven**
   The native Configure path is strongest when it provides:
   - clear section choices
   - short structured forms
   - review steps
   - next actions
   It is weaker when asked to behave like a fully custom wizard with rich visual composition.

3. **Entities and diagnostics surfaces are powerful but fragmented**
   They are useful supporting surfaces, but cannot substitute for a coherent top-level operator flow.

4. **User cognition depends heavily on naming, grouping, and menu hierarchy**
   In native HA, much of the UX quality comes from:
   - the labels used
   - the ordering of steps
   - the separation of concerns
   - the clarity of summaries
   - the confidence of the next-step wording

5. **The device format rewards a clean mental model more than a visually elaborate one**
   Because native HA surfaces are constrained, success depends more on information architecture and flow design than on visual ornament.

### Important practical implication

This means the redesign must fit the medium.
The answer is not to imagine a bespoke SaaS control panel.
The answer is to design the best possible native HA operator workflow using:
- Configure menus/steps
- device entities and buttons
- diagnostics and Repairs
- optional dashboards only as a secondary supplement

### Research conclusion from input 6

The best redesign will be the one that most respects native HA constraints while still making the operator journey feel deliberate, opinionated, and clear.

---

## Cross-input synthesis

When the six inputs are combined, the strongest consistent conclusions are:

### 1. The design direction is fundamentally correct already
The project should remain:
- native Home Assistant only
- Configure-centered
- device-path-supported
- four-bucket organized

### 2. The real gap is not direction, it is productization
The UI is still too dependent on:
- wording
- scaffolding
- partial flows
- implied structure

The redesign needs to convert those into:
- stronger grouping
- clearer operator sequence
- clearer current-state summary
- stronger Managed Devices workspace
- more decisive review/promotion path

### 3. Managed Devices is the most critical surface to redesign well
This is where the operator needs the clearest answers to:
- What do I already manage?
- What can I promote next?
- Which candidate is best?
- What warnings matter?
- What happens after promotion?

### 4. The top-level operator model should likely be action-oriented
The current docs define the four buckets well, but the redesign should likely sharpen the UI around operator tasks:
- tune the controller
- inspect source health
- manage/promote devices
- troubleshoot blockers

### 5. Diagnostics should support, not compensate for, unclear normal UX
If Diagnostics is carrying too much meaning, normal surfaces are probably still too weak.

### 6. The redesign must optimize for live HA legibility, not document elegance
The acceptance standard is whether the UI feels obvious in Home Assistant itself.

---

## Candidate design implications for the next design pass

These are not final decisions yet, but they are strong research-driven candidates.

### Candidate implication A. Add a stronger top-level “current state” layer
Even inside native constraints, the operator likely needs a stronger summary of:
- controller state
- current action or no-action reason
- current blockers
- number of managed devices
- number of promotable candidates

### Candidate implication B. Make Managed Devices a two-zone workspace
The Managed Devices surface likely needs a stronger built-in split between:
- **Managed now**
- **Candidates to review / promote**

### Candidate implication C. Make promotion a review-first workflow
Promotion should likely feel like:
1. identify promising candidate
2. open concise review summary
3. confirm warnings / fit
4. promote into managed fleet
5. land back in managed state with obvious confirmation

### Candidate implication D. Use Diagnostics only for exception handling and support
Diagnostics should likely be the place for:
- install problems
- source blockers
- diagnostics snapshot
- repair guidance
- provenance/package validation
Not the place where the core product meaning lives.

### Candidate implication E. Keep optional dashboards secondary
Optional dashboards may still be useful for visibility, but they should not become the core answer to the native UI problem.

---

## Open questions to resolve with James

These are the questions that should drive the next design conversation.

### 1. What should the operator see first?
If a user opens Zero Net Export in normal operation, what is the most important first screen impression?
- controller state?
- current energy state?
- managed fleet state?
- current blocker / next action?

### 2. What is the primary home for fleet work?
Should Managed Devices be designed mainly as:
- a fleet dashboard/workspace,
- a review queue plus managed list,
- or a task-oriented menu with summaries?

### 3. How much summary belongs in Configure vs the device page?
Where should the strongest concise status summaries live?
- Configure only?
- device page only?
- split between both?

### 4. What should be visible at a glance versus one click deeper?
For example:
- candidate warnings
- device priority
- current enablement
- suitability score/fit
- last action or plan impact

### 5. What is the right tone for the UI?
Should the native UX feel more:
- operational/industrial,
- domestic/simple,
- technical but calm,
- or explicitly assistant-like?

### 6. How opinionated should promotion be?
Should the product:
- strongly recommend a best next candidate,
- offer a shortlist without ranking too hard,
- or stay neutral and only expose review data?

### 7. Should the product surface “next best action” globally?
Would it help if the top-level UX always highlighted one next recommended action, such as:
- map missing source
- review candidate
- enable managed device
- resolve stale source blocker

### 8. What belongs in the detailed management path?
What should only appear in the deeper per-device/fleet inspection path, rather than the top-level Managed Devices flow?

---

## Interactive design-session answers captured so far

These answers were gathered directly from James during the redesign session in the UI thread.

### Confirmed design choices

1. **Opening priority**
   - the operator should first understand:
     1. what the optimizer is doing right now
     2. the current energy state it is reacting to

2. **Status style**
   - status should be **decision-oriented**, not just a plain state label
   - examples of the intended style:
     - export too high, engaging load
     - near target, holding
     - battery reserve protected, not engaging
     - no eligible device available
     - source data stale, control paused

3. **Opening data density**
   - the opening view should include the **full operating picture**, not a heavily reduced subset
   - desired top-level information includes:
     - solar power
     - grid import/export
     - home load
     - battery SOC
     - battery charge/discharge
     - active managed load total
     - target export / current error
     - controller mode

4. **Opening layout style**
   - the opening should be a **dense operational dashboard**, not a layered summary
   - the top-level feel should be a **balanced control board** rather than one oversized hero panel

5. **Visual tone**
   - the UI tone should be **industrial / operator console**
   - desired characteristics:
     - crisp
     - dense
     - serious

6. **Section ordering**
   - overall structure preference so far:
     - control board first
     - Managed Devices second
     - deeper sensor detail below/around that area
     - Diagnostics visible but secondary

7. **Managed Devices structure**
   - Managed Devices should be a **split workspace**
   - but not side-by-side
   - preferred order:
     - **Managed on top**
     - **Unmanaged on the bottom**

8. **Candidate ranking posture**
   - unmanaged candidates should be shown **neutrally**
   - the product should not over-rank or act like it knows the one correct candidate

9. **Candidate review shape**
   - review should be **balanced**, combining:
     - control suitability
     - safety / confidence
     - operational value

10. **After promotion**
   - after a candidate is promoted, the UX should show:
     - success
     - what changed
     - the next sensible action

11. **Sensors placement**
   - the most important sensors belong in the control board
   - additional sensor detail should live below/around Managed Devices rather than becoming a dominant separate destination

12. **Diagnostics posture**
   - Diagnostics should be **always visible but secondary**
   - health should remain part of the product posture, not hidden as a pure failure-only basement

13. **Navigation model**
   - preferred model is **hybrid**:
     - one main landing flow
     - clear jump-off entries to deeper sections

### Additional confirmed design choices from the next question round

14. **Top board field visibility**
   - all key operating fields should remain visible in the top control board
   - the top board is intended to be the real operational console, not a teaser or reduced summary layer

15. **Top board grouping model**
   - preferred grouping is a **mixed console** with these blocks:
     - Energy state
     - Control decision
     - Control outcome
     - Fleet activity

16. **Decision-summary placement**
   - preferred pattern is **both**:
     - a headline decision summary above the board
     - plus structured decision details within the Control Decision block

17. **Managed-device row density**
   - managed devices should use an **operational** density level
   - each managed device should show at a glance:
     - name
     - type
     - enabled/disabled
     - priority
     - current power or impact
     - current state/action

18. **Unmanaged candidate preview density**
   - unmanaged candidates should use an **operational shortlist** density level
   - each candidate should show at a glance:
     - name
     - type
     - likely usefulness
     - key warning, if any

19. **Problem-signal placement**
   - preferred pattern is **both**:
     - top-level alert summary
     - plus contextual warning inside the relevant block/section

### Emerging design direction from the answers

The emerging design is no longer a generic “clearer Configure flow.”
It is much more specific:

- a **dense native HA operator console** at the top
- organized as a **balanced control board**
- with **decision-oriented status language**
- showing the **full operating picture**, not a reduced summary
- grouped into:
  - Energy state
  - Control decision
  - Control outcome
  - Fleet activity
- with a **headline decision summary** above those structured blocks
- followed by a **Managed Devices workspace** with:
  - managed devices first
  - unmanaged candidates second
- with managed rows at operational density
- with unmanaged rows at shortlist density
- followed by deeper telemetry and visible-but-secondary health/diagnostics paths
- with problem signals shown both globally and contextually

This implies the redesign should optimize for:
- fast operational legibility
- high information density
- strong grouping rather than simplification by omission
- clear vertical section hierarchy
- low ambiguity around fleet state
- native HA realism rather than fake bespoke-app patterns
- visible status interruption when things are wrong, without losing local context
---

## Recommended next step

Use this research document as the input base for the next redesign round.

That redesign round should now focus on:
1. defining the exact top-level control-board composition
2. defining the exact contents of the Managed Devices workspace
3. defining how much detail belongs on the landing view versus one click deeper
4. producing a rewritten `docs/UI_DESIGN.md` that reflects the confirmed choices above

---

## Research summary in one sentence

The current Zero Net Export UI direction is conceptually correct, and James’s redesign answers now sharpen it into a dense, industrial-feeling native Home Assistant operator console with a decision-first control board, a vertically split Managed Devices workspace, and visible-but-secondary health and diagnostics.