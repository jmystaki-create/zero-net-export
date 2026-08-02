# WB-ZNE-UIUX-008 Destructive Confirmation Guardrails

Status: done
Priority: high
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md`

## Outcome

The cleaner Overview does not make dangerous actions feel routine or bypass confirmations.

## Review Coverage

- Product Constraints To Preserve
- Learnings Summary item 9
- What I Would Not Change Yet
- Functionality Risk Review: destructive action ambiguity

## Acceptance Criteria

- [x] No destructive action is introduced into the main fast path without explicit design approval.
- [x] Existing destructive confirmations are preserved.
- [x] Dangerous actions use clear consequence copy before execution.
- [x] Validation does not perform destructive or live-control actions without explicit approval.

## Validation

- [x] Static/frontend review of any action added to Overview.
- [x] Browser proof of confirmation affordance if a destructive action is present.
- [x] No destructive service calls during validation unless explicitly approved.

## Functional Safety

- Preserve existing tabs, data sources, service wiring, plan context, Diagnostics access, and confirmation gates unless a separate accepted design changes them.

## Implementation Note

Repo implementation is complete for this card as part of the 2026-08-02 Overview UI/UX refactor. Live HACS/browser proof remains tracked by `WB-ZNE-UIUX-010`.
