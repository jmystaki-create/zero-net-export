# ZNE-APP-007: Multi-Plan And Service Separation

Date: 2026-07-07

Status: READY

Release target: `v0.4.0`

## Outcome

Operators can see and work inside an explicit Zero Net Export plan/service context. The app no longer behaves like all state and actions belong to one implicit plan when the product direction requires multi-plan support.

## Scope

In scope:

- Plan/service selector or context header in the Zero Net Export app.
- Backend summary data for configured ZNE entries/plans.
- Entry-scoped reads for Overview, Sources, Managed Devices, Controls, Runtime, and Diagnostics.
- Entry-scoped service/action calls for source updates, managed-device updates, pause/resume, diagnostics export, and repair.
- Clear empty/single/multi-plan states.
- Safe failure for ambiguous write actions.

Out of scope:

- Full plan creation wizard.
- Complex scheduling or seasonal automation.
- Runtime-control algorithm changes.
- Bulk priority adjustment.
- Native Home Assistant device-page UX polish.

## Acceptance Criteria

- App header shows current plan/service context.
- With one ZNE plan, the app behaves as it does today but labels the selected context clearly.
- With multiple ZNE plans, the operator can switch selected context.
- Overview values are scoped to the selected context.
- Sources workflow reads and writes only the selected context.
- Managed Devices workflow reads and writes only the selected context.
- Controls and Runtime actions affect only the selected context.
- Diagnostics export and repair actions target only the selected context.
- Ambiguous write calls fail safely with a clear message.
- Repo tests cover multi-entry selection and no cross-entry mutation.
- Live validation records whether the HA target has one or multiple ZNE entries; if only one exists, live proof covers single-plan behavior and repo tests cover multi-plan behavior.

## Implementation Plan

1. Inventory current entry identity flow.
   - Identify where panel bootstrap data lists entries.
   - Identify all frontend service calls missing explicit `entry_id`.
   - Identify backend services that need explicit entry resolution.

2. Add a shared backend entry resolver.
   - Resolve explicit `entry_id`.
   - If one entry exists, allow fallback for backward compatibility.
   - If multiple entries exist and no `entry_id` is supplied, fail safely.

3. Extend app bootstrap/state summary.
   - Include entry id, title/name, version, status, and availability per plan.
   - Keep sensitive details out of frontend bootstrap.

4. Add app plan context UI.
   - Single-plan state: clear context label.
   - Multi-plan state: selector using existing app styling.
   - Persist selected context in memory/local storage only after safe fallback is defined.

5. Scope frontend reads and actions.
   - Overview, Sources, Managed Devices, Controls, Runtime, Diagnostics.
   - Include selected `entry_id` in service calls.
   - Render explicit error state if selected entry disappears.

6. Add validation.
   - Focused unit tests for entry resolver.
   - Frontend/static tests for context selection and service payloads.
   - Full test discovery.
   - HACS release/install validation.
   - Browser proof on desktop and narrow layouts.
   - HA service/action proof for selected-context writes.

## Validation Plan

- `python3 -m py_compile` for changed Python files.
- Focused tests for entry resolver and service scoping.
- Existing app/frontend tests covering selected context payloads.
- `python3 -m unittest discover -s tests -q`.
- `git diff --check`.
- GitHub release and HACS install/update.
- Home Assistant restart/load check.
- HA API version/state check.
- Targeted `ha core logs` review.
- Browser proof for single-plan context and multi-plan selector if available.

## Workboard

OpenClaw Workboard card:

- `ZNE: Milestone 7 Multi-Plan And Service Separation` - ready
