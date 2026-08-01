# Zero Net Export Workboard

Last updated: 2026-08-02

This workboard has been reset to track only the Zero Net Export main Overview UI/UX refactor described in `ui_ux_review.md`.

Historical workboard cards and stale OpenClaw UI card references were intentionally removed from the active workboard. Completed release history remains in the project validation, changelog, roadmap history, and bug/feature documents; it is no longer represented as active workboard state.

## Current Objective

Implement a focused Overview-only UX refactor that improves product clarity without removing functionality or changing backend control behaviour unless a separately validated data gap requires it.

The intended outcome is one truthful health state, one obvious next action, and one fast live power snapshot while preserving multi-plan support, editable workflows, Diagnostics, readiness explanations, and destructive-action confirmations.

## Source Review

- Review document: `ui_ux_review.md`
- Live page reviewed: Home Assistant `/zero-net-export`
- Live version observed in review: `0.4.16`
- Browser proof captured during review: `/root/.openclaw/media/outbound/9f258816-8611-4c45-b30c-5423de51db3a---b824a374-143d-4836-9ce1-950853807d71.png`

## Product Constraints

- The Home Assistant sidebar app/custom panel is the primary product surface.
- Native Home Assistant entities, device pages, and diagnostics remain secondary support surfaces.
- HACS-only delivery remains the release path.
- Multi-plan support, selected plan context, plan switching, and editable workflows must be preserved.
- Destructive actions require strong confirmation.
- Readiness must explain each issue and how to resolve it.
- Diagnostics must keep raw troubleshooting detail available.
- Browser proof is required for meaningful UI changes.

## Coverage Matrix

| Review requirement | Workboard coverage |
| --- | --- |
| Live access and proof discipline | WB-ZNE-UIUX-010 |
| One truthful health state and status-priority logic | WB-ZNE-UIUX-001, WB-ZNE-UIUX-011 |
| Promote managed-device review as the primary next action | WB-ZNE-UIUX-002 |
| Preserve and improve reconciliation/power snapshot data | WB-ZNE-UIUX-003 |
| Make Pause/Resume state-aware without breaking service semantics | WB-ZNE-UIUX-004, WB-ZNE-UIUX-011 |
| Move raw internals out of Overview but keep Diagnostics detail | WB-ZNE-UIUX-005 |
| Preserve multi-plan support and editable app workflows | WB-ZNE-UIUX-006 |
| Keep readiness explanations and resolution guidance | WB-ZNE-UIUX-007 |
| Preserve destructive confirmations and avoid unsafe fast paths | WB-ZNE-UIUX-008 |
| Responsive desktop/narrow layout proof | WB-ZNE-UIUX-009, WB-ZNE-UIUX-010 |
| Feasibility before code and implementation planning | WB-ZNE-UIUX-011 |

## Active Cards

- [WB-ZNE-UIUX-001 Health State Model](cards/WB-ZNE-UIUX-001-health-state-model.md) - done / urgent
- [WB-ZNE-UIUX-002 Managed Device Review Primary Action](cards/WB-ZNE-UIUX-002-managed-device-next-action.md) - done / high
- [WB-ZNE-UIUX-003 Live Power Snapshot](cards/WB-ZNE-UIUX-003-live-power-snapshot.md) - done / high
- [WB-ZNE-UIUX-004 State-Aware Executor Controls](cards/WB-ZNE-UIUX-004-state-aware-executor-controls.md) - done / high
- [WB-ZNE-UIUX-005 Diagnostics And Raw Detail Preservation](cards/WB-ZNE-UIUX-005-diagnostics-detail-preservation.md) - done / high
- [WB-ZNE-UIUX-006 Plan And Editable Workflow Preservation](cards/WB-ZNE-UIUX-006-plan-edit-workflow-preservation.md) - done / high
- [WB-ZNE-UIUX-007 Readiness Explanation Preservation](cards/WB-ZNE-UIUX-007-readiness-explanations.md) - done / high
- [WB-ZNE-UIUX-008 Destructive Confirmation Guardrails](cards/WB-ZNE-UIUX-008-destructive-confirmation-guardrails.md) - done / high
- [WB-ZNE-UIUX-009 Responsive Overview Layout](cards/WB-ZNE-UIUX-009-responsive-overview-layout.md) - done / normal
- [WB-ZNE-UIUX-010 Validation And Release Readiness](cards/WB-ZNE-UIUX-010-validation-release-readiness.md) - done / high
- [WB-ZNE-UIUX-011 Target Feasibility And Implementation Plan](cards/WB-ZNE-UIUX-011-target-feasibility-and-implementation-plan.md) - done / high

## Definition Of Done

- Every active card has acceptance criteria met or is explicitly closed as superseded by user decision.
- Browser proof exists for desktop and narrow/mobile Overview rendering.
- Plan selection, selected plan context, editable workflows, readiness details, Diagnostics, and executor controls are proven still reachable.
- No destructive or live-control action is performed without explicit user approval.
- Validation evidence is recorded in `validation/` for implementation work.
- `PROJECT_STATUS.md`, `ROADMAP.md`, and this workboard remain aligned.
