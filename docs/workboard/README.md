# Zero Net Export Workboard

Last updated: 2026-08-02

Status: validating. Operator tab redesign is implemented and repo-validated; browser/live proof remains.

## Active Scope

This workboard batch covers the approved tab-order and sparse-tab redesign in `ui_ux_review.md`. The goal is to make the sidebar app read as an operator console:

`Overview -> Managed Devices -> Sources -> Controls -> Runtime -> Diagnostics -> Settings`

Sources should explain measurement trust, Controls should explain what Zero Net Export is allowed to do, and Runtime should explain current execution and recent activity. Managed Devices remains the second tab and its watt dashboard/workflows must be preserved.

## Active Cards

- [WB-ZNE-TABUX-001 Approved Scope And Feasibility](cards/WB-ZNE-TABUX-001-approved-scope-and-feasibility.md) - done / urgent
- [WB-ZNE-TABUX-002 Tab Order](cards/WB-ZNE-TABUX-002-tab-order.md) - done / urgent
- [WB-ZNE-TABUX-003 Sources Health Workspace](cards/WB-ZNE-TABUX-003-sources-health-workspace.md) - done / high
- [WB-ZNE-TABUX-004 Control Policy Workspace](cards/WB-ZNE-TABUX-004-control-policy-workspace.md) - done / high
- [WB-ZNE-TABUX-005 Runtime Activity Workspace](cards/WB-ZNE-TABUX-005-runtime-activity-workspace.md) - done / high
- [WB-ZNE-TABUX-006 Workflow Preservation](cards/WB-ZNE-TABUX-006-workflow-preservation.md) - done / high
- [WB-ZNE-TABUX-007 Validation And Release Readiness](cards/WB-ZNE-TABUX-007-validation-release-readiness.md) - validating / high

## Coverage

- Approved tab order with Managed Devices second
- Sources source-health and control-impact redesign
- Controls command bar, grouped policy surface, safety guard, and next-action preview
- Runtime execution header, power flow snapshot, decision panel, and activity evidence
- Managed Devices watt dashboard and workflows preserved
- Plan context, service scoping, Diagnostics, and destructive confirmations preserved
- Desktop/narrow browser proof before release closeout

## Evidence

- Review: `ui_ux_review.md`
- Feasibility: `validation/zne-operator-tabs-redesign-feasibility.md`
- Implementation validation: `validation/zne-operator-tabs-redesign-implementation.md`
- Existing Managed Devices baseline: `validation/zne-managed-devices-load-dashboard-implementation.md`

## Completed Historical Scope

The previous Overview UI/UX workboard batch `WB-ZNE-UIUX-001` through `WB-ZNE-UIUX-011` remains completed and released in `v0.4.17`.

The Managed Devices UI/UX workboard batch `WB-ZNE-MDUIUX-001` through `WB-ZNE-MDUIUX-010` remains completed/release history for the load-aware fleet console. Future work must preserve its watt dashboard, measured/estimated semantics, disabled-active alert, and existing workflows.
