# WB-ZNE-UIUX-001 Health State Model

Status: ready
Priority: urgent
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md`

## Outcome

The Overview shows one truthful operator-facing health state instead of conflicting `Ready`, setup, and review signals.

## Review Coverage

- Product Judgment
- Learnings Summary items 1, 2, 11, 12
- Key UX Finding 1
- Recommended Direction 1
- Functionality Risk Review: health state misclassification

## Acceptance Criteria

- [ ] Define a documented health-state priority order: blocking fault, safe mode, paused, setup attention required, review recommended, running normally.
- [ ] Separate runtime/control readiness from setup completeness, managed-device review work, and blocking faults.
- [ ] Live state where `Ready`, `SETUP_IN_PROGRESS`, and managed-device review coexist renders without contradiction.
- [ ] No backend control behaviour changes are introduced unless a data gap is separately proven and approved.

## Validation

- [ ] Unit or frontend logic test for the health-state priority order if implementation adds code.
- [ ] Browser proof of the live Overview showing the computed health summary.
- [ ] Browser proof for at least one attention/review state.
- [ ] Targeted HA frontend logs if the app load or health rendering errors.

## Functional Safety

- Preserve existing tabs, data sources, service wiring, plan context, Diagnostics access, and confirmation gates unless a separate accepted design changes them.

## Implementation Note

Repo implementation is complete for this card as part of the 2026-08-02 Overview UI/UX refactor. Live HACS/browser proof remains tracked by `WB-ZNE-UIUX-010`.
