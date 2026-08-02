# Zero Net Export Main Page UI/UX Review

Date: 2026-08-02
Scope: Zero Net Export main Overview page in Home Assistant
Review type: Expert product/UI/UX assessment, validated against the live page

## Live Access Validation

Live access was confirmed before finalising this review.

- Canonical access inventory checked: `/root/.openclaw/workspace/TOOLS.md`
- Slave browser node SSH check succeeded: `openclaw@192.168.86.198` returned hostname `Slave`
- Home Assistant SSH check succeeded: `root@192.168.86.200:2222` returned Home Assistant core info
- Home Assistant version observed: `2026.7.4`
- Home Assistant HTTP check succeeded: `http://192.168.86.200:8123/manifest.json`
- Managed OpenClaw browser on the Slave Debian Browser Node opened the live `/zero-net-export` page
- Browser screenshot captured: `/root/.openclaw/media/outbound/9f258816-8611-4c45-b30c-5423de51db3a---b824a374-143d-4836-9ce1-950853807d71.png`

The existing user browser profile was not attachable via CDP during validation, but the managed OpenClaw browser profile was logged in and able to render the Home Assistant UI and Zero Net Export page.

## Live Page Observations

The live Overview page currently shows:

- Page title: `Zero Net Export`
- Version: `0.4.16`
- Plan count: `1 plan`
- HA connection state: `Connected to Home Assistant`
- App-visible entities: `189`
- Selected plan: `Zero Net Export (01KWC2HX12V4P0Q82A0WM69EHV)`
- Overview status chips: `Status: ready`, `Safe mode: off`, `Source mismatch: off`
- Readiness card: `Ready`, with no blocking readiness issue
- Action prompt: `Review managed-device queue`
- Managed-device queue details:
  - `32 unmanaged candidates are waiting`
  - `16 need review`
  - `16 are ready to promote`
  - First review item: `Lounge Room Heated Floor (variable)`
- Reconciliation values:
  - Home Load: `460 W`
  - Source Power: `2420 W`
  - Battery Power: `-1960 W`
  - Surplus/Deficit: `0 W`
  - Reconciliation Error: `0 W`
  - Confidence: `high`
  - Executor State: `running`
- Plan status: `ConfigEntryState.SETUP_IN_PROGRESS`
- Executor controls shown simultaneously: `Pause Executor` and `Resume Executor`

## Product Judgment

The page is not broken. It is functionally rich and the underlying data is useful. The issue is that the Overview behaves more like a diagnostics surface than an operator-facing control page.

The proposed changes are not cosmetic changes for their own sake. They are warranted because the current hierarchy makes the operator work too hard to answer four high-value questions:

1. Is Zero Net Export controlling safely right now?
2. Is the system importing, exporting, balanced, charging, or curtailing?
3. Is there anything I need to fix?
4. What is the next safest action?

The current page contains the answers, but distributes them across equally weighted cards, raw internal state, status chips, and secondary text. That slows comprehension and risks misinterpretation.

## Learnings Summary

These are the main conclusions from the live review and product reassessment.

1. The page has useful data, but the Overview mixes operator guidance and diagnostics too heavily.
2. `Ready` is currently too broad as a user-facing state because runtime readiness, setup completeness, review work, and blocking faults are different product concepts.
3. The managed-device review queue is the most important current action and should be promoted when it exists.
4. The reconciliation data appears coherent and valuable; the recommendation is to preserve the data and improve scannability.
5. Executor controls should reflect the current executor state so users are not shown equally weighted Pause and Resume actions at the same time.
6. The Home Assistant sidebar app/custom panel remains the right primary product surface.
7. Native Home Assistant entities, device pages, and diagnostics remain important secondary surfaces and should not be removed.
8. Multi-plan support, editable workflows, selected plan context, and plan switching must be preserved.
9. Destructive actions must continue requiring strong confirmation.
10. Readiness must keep explaining both what is wrong and how to resolve it.
11. The biggest implementation risk is misclassifying the new top-level health summary.
12. The safest path is an Overview-only presentation refactor with no backend behaviour change unless feasibility proves a data gap.

## Product Constraints To Preserve

These constraints are important because they prevent the refactor from becoming a broad redesign or accidentally removing expected functionality.

- The Home Assistant sidebar app/custom panel is the primary product surface.
- Native Home Assistant device/entity pages remain useful secondary visibility and automation surfaces, but they should not drive the main UX.
- The frontend delivery model should remain HACS-only unless a separate feasibility decision changes that.
- Multi-plan support must remain first-class. The plan selector and selected plan context should stay available.
- Editable workflows must remain available from the app.
- Destructive actions require strong confirmation. This applies especially to removing managed devices, deleting plans, resetting setup state, clearing learned mappings, or any action that can affect live control behaviour.
- Readiness UX must continue explaining each issue and the resolution path, not just show a high-level warning.
- Diagnostics must continue exposing the raw details needed for troubleshooting.
- Browser proof should be collected for meaningful UI changes.

## Key UX Findings

### 1. The health model is ambiguous

The live page says `Ready`, but also shows `ConfigEntryState.SETUP_IN_PROGRESS` and a managed-device review queue. This is the most important issue.

From a product perspective, this does not mean the backend is wrong. It means the UI needs a clearer distinction between:

- runtime/control readiness
- setup completeness
- recommended optimisation or review work
- blocking faults

Without that distinction, users may read `Ready` as "fully configured and no action needed", while the page is also asking them to review devices.

### 2. The next action is under-promoted

The managed-device review queue is a meaningful piece of work: 32 candidates, 16 needing review, and 16 ready to promote. That is not just supporting detail. It is the main actionable item on the page.

It should be visually promoted when present.

### 3. The power snapshot is correct but too slow to scan

The reconciliation values are valuable, and the current live values appear coherent:

`460 W home load + 1960 W battery charging = 2420 W source power`, with `0 W` surplus and `0 W` reconciliation error.

That supports keeping the data, but changing its presentation. The operator should be able to read the page at a glance and understand that the system is balanced, the battery is charging, and confidence is high.

### 4. Executor controls should be state-aware

Executor state is `running`, but both `Pause Executor` and `Resume Executor` are shown. This creates avoidable uncertainty.

Only the valid primary action should be prominent. In the current state, that means showing `Pause Executor` as the main action and hiding or disabling `Resume Executor`.

### 5. Internal implementation language leaks into the Overview

Terms and values such as `ConfigEntryState.SETUP_IN_PROGRESS`, full source entity IDs, and detailed source-role language are useful for diagnostics, but they should not be first-class Overview content.

The Overview should translate internal state into operator language, with raw details still available in Diagnostics.

## Recommended Direction

Refactor the Overview into an operator command center while preserving the existing tabs and underlying data.

### 1. Add a single top health summary

Recommended pattern:

`Attention required · Executor running · Balanced at 0 W · Updated 3m ago`

The exact status should be derived from a clear hierarchy:

- blocking fault
- safe mode
- paused
- setup attention required
- review recommended
- running normally

This would prevent `Ready` from appearing to contradict setup or review work.

### 2. Promote the highest-value next action

When managed devices need review, show a prominent action panel near the top:

`Review managed devices`
`16 devices need review. 16 more are ready to promote.`
Primary action: `Open Managed Devices`

This change makes sense because the live page already knows the work exists. The UI should not make the user hunt for it.

### 3. Convert reconciliation into a live power snapshot

Keep the same data, but make it more scannable:

- Home Load: `460 W`
- Solar/Source: `2420 W`
- Battery: `1960 W charging`
- Grid/Surplus: `0 W balanced`
- Error: `0 W`
- Confidence: `High`

This is a presentation change, not a model change.

### 4. Make executor controls stateful

When running:

- Show state: `Running`
- Show primary action: `Pause`
- Do not show `Resume` as an enabled peer action

When paused:

- Show state: `Paused`
- Show primary action: `Resume`
- Do not show `Pause` as an enabled peer action

This improves confidence and reduces accidental action ambiguity.

### 5. Move raw technical details down a level

Move these to Diagnostics, details drawers, or secondary metadata:

- full entity IDs
- config entry enum strings
- source-role internals
- low-level reconciliation source labels

Keep a short translated version in Overview.

## What I Would Not Change Yet

I would not redesign the whole application.

I would not remove the tabs.

I would not remove or weaken multi-plan support.

I would not remove the selected plan context or plan selector.

I would not remove editable setup/review workflows.

I would not make destructive workflows faster at the expense of confirmation.

I would not remove Diagnostics or the detailed source data.

I would not introduce a dramatically different visual style. The current Home Assistant-native look is appropriate.

I would not add decorative visuals or marketing-style layout. This is an operational tool, not a landing page.

I would not change backend behaviour as part of this UI refactor unless the existing frontend data cannot support the proposed health summary.

## Proposed Implementation Scope

This should be a focused Overview-only UX refactor.

High priority:

1. Define one computed Overview health state.
2. Promote managed-device review when review work exists.
3. Rework reconciliation into a compact live power snapshot.
4. Make executor controls state-aware.
5. Translate raw plan/setup state into user-facing language.

Medium priority:

1. Improve responsive layout so cards stack by importance, not arbitrary equal columns.
2. Reduce repeated timestamps and source labels in the Overview.
3. Keep exact internals available through Diagnostics.

## Approved Operator Tabs Redesign

Date: 2026-08-02
Scope: tab order plus Sources, Controls, and Runtime tabs
Status: approved for implementation

The user reviewed the current tab order and sparse operator tabs and approved a broader follow-up UX batch. The Managed Devices tab should move directly after Overview because the fleet/load console is now the primary operator workspace after the high-level status page.

Approved tab order:

`Overview -> Managed Devices -> Sources -> Controls -> Runtime -> Diagnostics -> Settings`

Rationale:

- Overview answers what needs attention.
- Managed Devices is the next highest-value operator surface because it controls the managed load fleet and now exposes watts.
- Sources is a dependency/readiness surface for measurement trust.
- Controls is a policy/permission surface for what the controller is allowed to do.
- Runtime is execution evidence and recent activity, not the place for setup or raw diagnostics.
- Diagnostics stays available for raw internals and support/debug evidence.
- Settings remains last.

### Sources Tab Redesign

Purpose: answer "Are the measurements trustworthy enough to control?"

The Sources tab should be redesigned from sparse cards plus raw role rows into a source-health workspace.

Required layout:

- Top health strip showing source health: ready, blocked, stale, missing, or unknown.
- Last update/freshness summary.
- Source blocker and stale-source summaries promoted near the top.
- Required source checklist covering grid/surplus, solar/source power, battery power, battery SOC, and home/load power where available.
- Per-source rows showing role, requirement level, status, live value, freshness/age, issue count, and bound entity.
- Source edit field remains available per role.
- "Control impact" panel explaining whether current source issues block runtime control or only reduce confidence.
- Plan selector remains available and saves stay scoped to the selected plan.
- Raw/long entity IDs remain visible but de-emphasized compared with role, live value, and status.

Remove or de-emphasize:

- One-card tabs with only two or three rows.
- Raw issue counts as the main visual hierarchy.
- Long source entity IDs in the primary reading position.

### Controls Tab Redesign

Purpose: answer "What is Zero Net Export allowed to do?"

The Controls tab should become a control-policy surface rather than a sparse set of equally weighted inputs.

Required layout:

- Top command bar with current control enabled state, current mode, and one state-aware primary action: enable or disable control.
- Policy card containing target export, deadband, battery reserve, and live mode.
- Policy values should be grouped together as a single operator task. The existing backend services may still apply values individually, but the UI should read as one policy surface rather than three disconnected mini-actions.
- Safety guard card showing what prevents action right now: source blockers, stale readings, safe mode, and control guard summary.
- "What will happen next?" preview using planned power delta, active controlled power, surplus/grid state, mode, and enabled state.
- Preserve existing mode, number, and enable/disable service wiring.

Remove or de-emphasize:

- Multiple peer actions when only one action is valid.
- Tiny isolated Apply buttons that make control changes feel unrelated.
- Raw enum/internal states as primary operator copy.

### Runtime Tab Redesign

Purpose: answer "What is the controller doing right now, and what did it just do?"

The Runtime tab should become an execution monitor rather than two sparse cards.

Required layout:

- Live execution header showing running/paused/blocked/active state, executor state, active controlled power, planned delta, and latest update.
- Power flow snapshot using Home Load, Source, Battery, Grid/Surplus, Managed Load, and Confidence where available.
- Decision panel showing current decision: hold, enable load, disable load, blocked, paused, or waiting; include reason and next/last evaluation context when available.
- Activity timeline/counts showing actions today, successful today, total failed, last failure reason, and command failure state.
- Keep low-level logs and raw diagnostics in Diagnostics, not Runtime.

Remove or de-emphasize:

- Raw two-card layout with only three power rows and three action rows.
- Support/debug log material that belongs in Diagnostics.

### Implementation Constraints

- Do not change backend control behavior in this batch.
- Preserve Managed Devices watt dashboard, measured/estimated semantics, disabled-active alert, and existing per-device and bulk workflows.
- Preserve plan context and selected-plan service scoping.
- Preserve Diagnostics as the raw detail/debug surface.
- Preserve destructive confirmations.
- Use frontend-derived views from existing entities first; add backend entities only if live validation proves a data gap.
- Browser proof is required for desktop and narrow layouts before release closeout.

## Functionality Risk Review

These changes should not remove or break functionality if implemented as an Overview-only presentation refactor. The safe implementation approach is to preserve existing data sources, service calls, tabs, plan selection, and detailed diagnostic views.

### Risk: health state misclassification

If a new top-level health summary is computed incorrectly, the page could understate a blocking problem or overstate a non-blocking setup task.

Control:

- Define a clear status priority order before implementation.
- Separate runtime/control readiness from setup completeness and recommended review work.
- Validate against live states where `Ready`, `SETUP_IN_PROGRESS`, and managed-device review coexist.

### Risk: hiding an available executor action

Making Pause/Resume state-aware is correct, but the UI must not trap the user if executor state detection is stale or unknown.

Control:

- If executor state is known `running`, show Pause as primary.
- If executor state is known `paused`, show Resume as primary.
- If executor state is unknown/stale, show both actions with disabled/guarded affordances or an explicit state warning.
- Keep the underlying service/action wiring unchanged.

### Risk: losing troubleshooting detail

Moving raw details out of Overview could make support/debugging harder if the details are removed entirely.

Control:

- Move raw details to Diagnostics or expandable details.
- Keep entity IDs, config-entry states, timestamps, and source names accessible.
- Validate that Diagnostics still exposes the raw values after the refactor.

### Risk: weakening multi-plan workflows

Simplifying the header could accidentally make the active plan less visible or make plan switching harder.

Control:

- Preserve the plan selector.
- Preserve selected plan identity.
- Avoid truncating the plan name where it is the main context.
- Truncate only long IDs, with copy/details access where appropriate.

### Risk: weakening readiness explanations

Promoting a single action panel must not collapse away the detailed explanation of what is wrong and how to resolve it.

Control:

- Keep the prominent next action near the top.
- Keep per-issue explanation and resolution details in Readiness.
- Make sure the Overview still answers both "what is wrong" and "what do I do next".

### Risk: destructive action ambiguity

If future Overview actions include destructive workflows, a cleaner UI could accidentally make dangerous actions feel routine.

Control:

- Keep destructive actions out of the main fast path unless explicitly needed.
- Require strong confirmation for destructive actions.
- Use clear consequence copy before execution.

### Risk: responsive regression

Changing the card hierarchy could make the page better on desktop but worse on mobile or narrow Home Assistant panels.

Control:

- Validate desktop and narrow/mobile screenshots.
- Ensure the action panel, power snapshot, and executor control stack in priority order.
- Avoid equal-width grids for unequal-priority information.

## Validation Plan For Any Future Implementation

If these changes are implemented, validation should include:

- Browser screenshot of the Overview at desktop width
- Browser screenshot of the Overview at a narrow/mobile width
- Browser proof that only the valid executor action is prominent for the current executor state
- Browser proof that managed-device review is promoted when review items exist
- Browser proof that plan selection and selected plan context remain available
- Browser proof that Readiness still explains each issue and its resolution
- Browser proof that the Diagnostics tab still exposes raw details
- Browser proof that editable workflows remain reachable from the app
- Targeted Home Assistant logs after frontend load if frontend errors are suspected
- No destructive or live-control service calls unless explicitly approved

## Final Recommendation

Proceed with a small, targeted Overview redesign.

The strongest change is not visual polish. It is product clarity: one truthful health state, one obvious next action, and one fast live power snapshot.

That is enough to materially improve the page without creating churn or redesigning the broader Zero Net Export experience.

---

# Managed Devices Tab UI/UX Review

Date: 2026-08-02
Scope: Zero Net Export Managed Devices tab in the Home Assistant sidebar app
Review type: Expert product/UI/UX assessment, validated against live Home Assistant API data

## Live Managed Devices Validation

The Managed Devices review was checked against live `v0.4.17` Home Assistant API data from `sensor.managed_devices_overview`.

Observed live state:

- Managed devices: `2`
- Enabled managed devices: `1`
- Disabled managed devices: `1`
- Usable managed devices: `1`
- Total managed nominal power: `2405 W`
- Active managed device count: `1`
- Active managed measured power: `0 W`
- Unmanaged candidate backlog: `31`
- Need review: `16`
- Ready to promote: `15`

Important live device evidence:

- `Lounge Room - Heated Floor`
  - Entity: `switch.ac_outlet_1`
  - Kind: fixed
  - Enabled in ZNE: `false`
  - Usable by ZNE: `false`
  - Observed active: `true`
  - Nominal power: `2400 W`
  - Current measured power: `null`
- `The 7th`
  - Entity: `light.7th`
  - Kind: fixed
  - Enabled in ZNE: `true`
  - Usable by ZNE: `true`
  - Observed active: `false`
  - Nominal power: `5 W`
  - Current measured power: `null`

This is the exact condition the Managed Devices UX must make obvious: a large load is active in the home but disabled for Zero Net Export control.

## Product Judgment

The Managed Devices tab has the right broad structure:

1. Fleet Summary
2. Fleet List
3. Unmanaged Candidate Queue

That order should be preserved. The page also contains valuable controls: filtering, sorting, bulk enable/disable, per-device enable/disable, candidate review, and candidate promotion. These functions should not be removed.

The main product issue is that the tab still behaves more like an inventory manager than an energy-control dashboard. In Zero Net Export, a managed device is not only an item in a list. It is controllable load, measured or estimated in watts. The Managed Devices tab needs to show load impact first.

## Additional User Requirement

Managed devices should publish and display the watts they consume.

The Managed Devices tab should also include a dashboard that considers:

- Net load
- Total load of all managed devices
- Total load of enabled managed devices
- Total load of disabled managed devices
- Total load of managed devices that are active but disabled
- Total load currently available to Zero Net Export control

Where exact measured current power is unavailable, the UI must label any watt value derived from `observed_active` plus `nominal_power_w` as an estimate. The live system currently has this case: the heated floor is observed active, but `current_power_w` is `null`, so the best available load-impact value is an estimated `2400 W`.

## Key Managed Devices UX Findings

### 1. The current `Power` column is misleading

The fleet table currently uses the label `Power` for an on/off traffic-light indicator. That indicator is useful, but it is not power. It tells the operator whether the device appears active, not how many watts the device consumes or contributes to controllable load.

This should be split into:

- `Load`: measured current watts when available, otherwise estimated active watts or nominal watts
- `State`: on/off activity indicator

### 2. Counts are not enough for this product surface

Fleet counts such as Total, Enabled, Disabled, Blocked, and Stale are useful, but they do not answer the Zero Net Export operator's primary question:

How many watts are controllable, active, enabled, disabled, or unavailable?

The live page already has enough data to show a load dashboard. The UI should not make the operator infer load impact from device counts.

### 3. Disabled-but-active loads need primary attention

The live heated-floor state should be escalated:

`2400 W active but disabled`

This means the load exists in the home but is not available to ZNE control. That is more operationally important than its priority number or raw device key.

### 4. The table is metadata-first

The current row hierarchy is too focused on internal identifiers:

`Power, Device Key, Plan, Status, Priority, Readiness, Last Seen, Blockers, Actions`

The operator-first hierarchy should be:

`Device, Load, State, ZNE availability, Priority, Last Seen, Issue, Action`

Plan and key details should remain visible, but subordinate to device name and load impact.

### 5. The candidate queue remains useful but should become more load-aware

The Unmanaged Candidate Queue is valuable and should be preserved. Promotion decisions would improve if candidate rows expose estimated/configured watts where available, confidence, warnings, and action.

This can follow the managed-fleet dashboard work. It should not block the first pass if candidate watt estimation is not already reliable.

## Recommended Managed Devices Direction

Refactor the Managed Devices tab into a load-aware fleet console while preserving existing workflows.

### 1. Add a Managed Load Dashboard

Add a dashboard strip near the top of the tab:

- `Net Load`
- `Managed Load`
- `Enabled Managed Load`
- `Disabled Managed Load`
- `Active Managed Load`
- `ZNE Available Load`

Use measured watts where available. Use clearly labelled estimated watts when only nominal power and activity state are known.

### 2. Add a disabled-active alert

When any managed device is observed active but disabled, show a primary alert:

`Attention: 2400 W is active but disabled`

Example detail:

`Lounge Room - Heated Floor is consuming estimated load but is not available to Zero Net Export control.`

Primary action should be review/enable through the existing safe managed-device workflow. It must not bypass existing confirmation or service guards.

### 3. Publish/display per-device watt impact

Every managed row should show watt impact:

- `current_power_w` when available
- estimated active load from `observed_active ? nominal_power_w : 0`
- `nominal_power_w`
- enabled/disabled contribution

Existing per-device Home Assistant sensors for `current_power_w` and nominal watt metadata should be preserved. If additional aggregate entities are needed later, they should be added as a separate backend card.

### 4. Rename and split table columns

Replace the misleading `Power` traffic-light column with separate `Load` and `State` columns.

The `Load` column should make the live heated-floor case obvious:

`~2400 W active`

The `State` column should retain the on/off traffic light.

### 5. Preserve all existing controls and safety

Do not remove:

- plan selector/context
- filters
- sorting
- bulk enable/disable confirmation
- per-device enable/disable
- remove confirmation
- candidate review and promotion
- Diagnostics/raw attributes
- HACS delivery path

## Managed Devices Implementation Risks

1. **Measured vs estimated watts**
   The UI must not present nominal-power estimates as exact measured consumption. Use labels such as `estimated`, `nominal`, or `measured`.

2. **Disabled-active interpretation**
   A disabled device that is observed active may be manually on, externally controlled, or stale. The UI should warn without implying ZNE caused the state.

3. **Backend aggregate semantics**
   If aggregate load sensors are added, their definitions must be explicit: measured active load, estimated active load, nominal controllable load, enabled nominal load, and disabled nominal load are different metrics.

4. **No control behavior change**
   The first implementation should be a presentation/data-surfacing refactor. It must not change planner behavior, device enablement semantics, or service calls.

5. **Responsive table risk**
   Adding columns can make the fleet table harder to use on narrow screens. The dashboard and row layout must be validated on desktop and mobile/narrow widths.

6. **Recorder attribute budget**
   Additional per-device attributes must not exceed Home Assistant recorder state attribute limits. Prefer deriving frontend display values from existing compact attributes where possible.

## Managed Devices Workboard Coverage Required

The new workboard scope should cover:

1. Target feasibility and data semantics
2. Managed load dashboard
3. Per-device watt display
4. Disabled-active alert
5. Table hierarchy and column rename
6. Candidate queue load-awareness
7. Existing workflow preservation
8. Responsive/browser validation
9. Optional backend aggregate sensors, only if frontend derivation is insufficient
10. Release/live validation
