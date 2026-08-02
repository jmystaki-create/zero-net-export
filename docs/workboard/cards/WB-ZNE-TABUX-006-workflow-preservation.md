# WB-ZNE-TABUX-006 Workflow Preservation

Status: done
Priority: high
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md` / Approved Operator Tabs Redesign

## Outcome

The operator tabs are redesigned without breaking existing workflows or safety boundaries.

## Acceptance Criteria

- [x] Preserve Managed Devices watt dashboard, measured/estimated semantics, disabled-active alert, and all current fleet/candidate workflows.
- [x] Preserve plan context and entry-scoped service calls.
- [x] Preserve source-role update service wiring.
- [x] Preserve control enable, mode, and policy value service wiring.
- [x] Preserve executor pause/resume, Diagnostics, and destructive confirmations.

## Validation

- [x] Focused frontend source test verifies preservation markers.
- [x] Existing managed-device focused test suite remains passing.

## Implementation Note

Preservation is covered by the focused frontend suite and unchanged service action handlers.
