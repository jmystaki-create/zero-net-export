# WB-ZNE-UIUX-009 Responsive Overview Layout

Status: todo
Priority: normal
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md`

## Outcome

The redesigned Overview stacks information by importance across desktop and narrow/mobile Home Assistant widths.

## Review Coverage

- Main UX Problems: unused space and scan rhythm
- Recommended Direction
- Proposed Implementation Scope: medium priority
- Functionality Risk Review: responsive regression

## Acceptance Criteria

- [ ] Desktop layout prioritizes health summary, next action, power snapshot, and executor control.
- [ ] Narrow/mobile layout stacks in the same priority order.
- [ ] Text does not overlap, truncate critical values, or resize controls unexpectedly.
- [ ] Avoid equal-width grids for unequal-priority information.

## Validation

- [ ] Desktop browser screenshot.
- [ ] Narrow/mobile browser screenshot.
- [ ] Visual check for overlap, truncation, and action visibility.

## Functional Safety

- Preserve existing tabs, data sources, service wiring, plan context, Diagnostics access, and confirmation gates unless a separate accepted design changes them.

## Implementation Note

Repo implementation is complete for this card as part of the 2026-08-02 Overview UI/UX refactor. Live HACS/browser proof remains tracked by `WB-ZNE-UIUX-010`.
