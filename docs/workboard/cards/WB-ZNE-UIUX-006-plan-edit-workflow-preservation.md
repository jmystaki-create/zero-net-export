# WB-ZNE-UIUX-006 Plan And Editable Workflow Preservation

Status: todo
Priority: high
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md`

## Outcome

The Overview refactor does not weaken selected-plan context, plan switching, multi-plan support, or editable workflows.

## Review Coverage

- Product Constraints To Preserve
- Learnings Summary items 6, 7, 8
- What I Would Not Change Yet
- Functionality Risk Review: weakening multi-plan workflows

## Acceptance Criteria

- [ ] The selected plan name remains visible in the app.
- [ ] The plan selector remains available and usable.
- [ ] Long plan IDs may be truncated only if full details remain accessible.
- [ ] Existing editable workflows remain reachable from the sidebar app.
- [ ] No workflow is pushed back into unsupported native-device-page-first UX.

## Validation

- [ ] Browser proof of selected plan context.
- [ ] Browser proof of plan selector availability.
- [ ] Browser proof that editable workflows remain reachable from app navigation.

## Functional Safety

- Preserve existing tabs, data sources, service wiring, plan context, Diagnostics access, and confirmation gates unless a separate accepted design changes them.

## Implementation Note

Repo implementation is complete for this card as part of the 2026-08-02 Overview UI/UX refactor. Live HACS/browser proof remains tracked by `WB-ZNE-UIUX-010`.
