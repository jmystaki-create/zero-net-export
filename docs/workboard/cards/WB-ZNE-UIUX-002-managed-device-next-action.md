# WB-ZNE-UIUX-002 Managed Device Review Primary Action

Status: ready
Priority: high
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md`

## Outcome

When managed devices need review, the Overview promotes that work as the primary next action.

## Review Coverage

- Live Page Observations: managed-device queue
- Learnings Summary item 3
- Key UX Finding 2
- Recommended Direction 2
- Validation Plan: managed-device review proof

## Acceptance Criteria

- [ ] If review items exist, show a prominent `Review managed devices` action near the top of Overview.
- [ ] Show counts for devices needing review and ready to promote.
- [ ] Primary action opens the Managed Devices app section or equivalent in-app workflow.
- [ ] The detailed Readiness explanation remains available and is not collapsed away.

## Validation

- [ ] Browser proof with the current live queue showing the promoted action.
- [ ] Browser proof that activating the action reaches Managed Devices without changing live device state.
- [ ] No destructive or live-control service calls during validation unless explicitly approved.

## Functional Safety

- Preserve existing tabs, data sources, service wiring, plan context, Diagnostics access, and confirmation gates unless a separate accepted design changes them.

## Implementation Note

Repo implementation is complete for this card as part of the 2026-08-02 Overview UI/UX refactor. Live HACS/browser proof remains tracked by `WB-ZNE-UIUX-010`.
