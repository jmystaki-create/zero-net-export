# WB-ZNE-TABUX-002 Tab Order

Status: done
Priority: urgent
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md` / Approved Operator Tabs Redesign

## Outcome

The sidebar app tab order makes Managed Devices the second tab.

## Acceptance Criteria

- [x] Tab order is `Overview`, `Managed Devices`, `Sources`, `Controls`, `Runtime`, `Diagnostics`, `Settings`.
- [x] Active-section routing continues to work for all existing tabs.
- [x] Existing tab labels are preserved.

## Validation

- [x] Focused frontend source test verifies ordering.
- [ ] Browser proof is captured before release closeout.

## Implementation Note

Implemented in `zero-net-export-app.js`; browser proof remains tracked by `WB-ZNE-TABUX-007`.
