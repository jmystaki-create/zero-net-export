# WB-ZNE-UIUX-007 Readiness Explanation Preservation

Status: todo
Priority: high
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md`

## Outcome

Readiness continues to explain each issue and resolution while the Overview gains a stronger summary action.

## Review Coverage

- Product Constraints To Preserve
- Learnings Summary item 10
- Functionality Risk Review: weakening readiness explanations
- Validation Plan: Readiness proof

## Acceptance Criteria

- [ ] Each readiness issue still includes what is wrong.
- [ ] Each readiness issue still includes how to resolve it.
- [ ] A promoted next-action panel does not remove detailed readiness guidance.
- [ ] Readiness language remains operator-oriented rather than implementation-oriented.

## Validation

- [ ] Browser proof that the promoted action and detailed readiness explanation both appear when issues exist.
- [ ] Browser proof that no issue text overlaps or truncates on desktop and narrow/mobile widths.

## Functional Safety

- Preserve existing tabs, data sources, service wiring, plan context, Diagnostics access, and confirmation gates unless a separate accepted design changes them.

## Implementation Note

Repo implementation is complete for this card as part of the 2026-08-02 Overview UI/UX refactor. Live HACS/browser proof remains tracked by `WB-ZNE-UIUX-010`.
