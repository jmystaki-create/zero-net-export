# WB-ZNE-TABUX-004 Control Policy Workspace

Status: done
Priority: high
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md` / Approved Operator Tabs Redesign

## Outcome

Controls becomes a policy and permission surface that explains what Zero Net Export is allowed to do.

## Acceptance Criteria

- [x] Add a command bar with enabled state, live mode, and one state-aware enable/disable action.
- [x] Group target export, deadband, battery reserve, and mode into a policy surface.
- [x] Add a safety guard card for source blockers, stale readings, safe mode, and control guard summary.
- [x] Add a "What will happen next?" preview using live/planned runtime values.
- [x] Preserve existing enable, mode, and number service wiring.

## Validation

- [x] Focused frontend source test verifies the new control-policy workspace markers.
- [ ] Browser proof is captured before release closeout.

## Implementation Note

Implemented as a frontend presentation redesign; existing service actions are unchanged.
