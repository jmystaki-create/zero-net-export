# Zero Net Export Workboard

Last updated: 2026-08-02

Status: active. Managed Devices UI/UX load-dashboard implementation is repo-validated; release and live browser validation remain.

## Active Scope

This workboard batch covers the Managed Devices tab critique in `ui_ux_review.md`. The goal is to turn Managed Devices from an inventory-heavy page into a load-aware fleet console while preserving all existing safe workflows.

## Active Cards

- [WB-ZNE-MDUIUX-001 Target Feasibility And Data Semantics](cards/WB-ZNE-MDUIUX-001-target-feasibility-and-data-semantics.md) - done / urgent
- [WB-ZNE-MDUIUX-002 Managed Load Dashboard](cards/WB-ZNE-MDUIUX-002-managed-load-dashboard.md) - done / urgent
- [WB-ZNE-MDUIUX-003 Per-Device Watt Display](cards/WB-ZNE-MDUIUX-003-per-device-watt-display.md) - done / high
- [WB-ZNE-MDUIUX-004 Disabled Active Load Alert](cards/WB-ZNE-MDUIUX-004-disabled-active-alert.md) - done / high
- [WB-ZNE-MDUIUX-005 Table Hierarchy And Column Rename](cards/WB-ZNE-MDUIUX-005-table-hierarchy-and-column-rename.md) - done / high
- [WB-ZNE-MDUIUX-006 Candidate Queue Load Awareness](cards/WB-ZNE-MDUIUX-006-candidate-queue-load-awareness.md) - done / normal
- [WB-ZNE-MDUIUX-007 Existing Workflow Preservation](cards/WB-ZNE-MDUIUX-007-workflow-preservation.md) - done / high
- [WB-ZNE-MDUIUX-008 Responsive Browser Validation](cards/WB-ZNE-MDUIUX-008-responsive-browser-validation.md) - ready / high
- [WB-ZNE-MDUIUX-009 Optional Backend Aggregate Sensors](cards/WB-ZNE-MDUIUX-009-optional-backend-aggregate-sensors.md) - done / normal
- [WB-ZNE-MDUIUX-010 Release And Live Validation](cards/WB-ZNE-MDUIUX-010-release-live-validation.md) - ready / high

## Coverage

- Managed Devices load dashboard
- Per-device watt display
- Measured vs estimated watt semantics
- Disabled-active load alert
- Table hierarchy and `Power` column correction
- Candidate queue load-awareness assessment
- Backend aggregate sensors resolved as unnecessary for this release
- Workflow preservation and destructive confirmation protection
- Responsive/browser validation
- Optional backend aggregate sensors if frontend derivation is insufficient
- HACS/release/live validation

## Evidence

- Review: `ui_ux_review.md`
- Feasibility: `validation/zne-managed-devices-load-dashboard-feasibility.md`
- Implementation validation: `validation/zne-managed-devices-load-dashboard-implementation.md`
- Live API snapshot basis: `sensor.managed_devices_overview` on 2026-08-02

## Completed Historical Scope

The previous Overview UI/UX workboard batch `WB-ZNE-UIUX-001` through `WB-ZNE-UIUX-011` remains completed and released in `v0.4.17`.
