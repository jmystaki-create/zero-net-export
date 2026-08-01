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
