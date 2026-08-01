# WB-ZNE-UIUX-004 State-Aware Executor Controls

Status: todo
Priority: high
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md`

## Outcome

Executor controls show only the valid primary action for the current executor state, with a safe fallback for unknown state.

## Review Coverage

- Live Page Observations: executor running with Pause and Resume
- Learnings Summary item 5
- Key UX Finding 4
- Recommended Direction 4
- Functionality Risk Review: hiding an available executor action

## Acceptance Criteria

- [ ] When executor state is `running`, Pause is the primary action and Resume is hidden, disabled, or clearly unavailable.
- [ ] When executor state is `paused`, Resume is the primary action and Pause is hidden, disabled, or clearly unavailable.
- [ ] When executor state is unknown or stale, the UI does not trap the user and clearly explains the uncertainty.
- [ ] Underlying pause/resume service wiring remains unchanged.

## Validation

- [ ] Browser proof for the current running state.
- [ ] If safely available, proof for paused state; otherwise document as pending/manual.
- [ ] No pause/resume service call in live HA unless explicitly approved.

## Functional Safety

- Preserve existing tabs, data sources, service wiring, plan context, Diagnostics access, and confirmation gates unless a separate accepted design changes them.

## Implementation Note

Repo implementation is complete for this card as part of the 2026-08-02 Overview UI/UX refactor. Live HACS/browser proof remains tracked by `WB-ZNE-UIUX-010`.
