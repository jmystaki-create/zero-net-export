# ZNE UI/UX Overview Refactor Feasibility

Date: 2026-08-02
Scope: Overview-only frontend refactor for the Home Assistant sidebar app/custom panel.
Source review: `ui_ux_review.md`
Workboard cards: `WB-ZNE-UIUX-001` through `WB-ZNE-UIUX-011`

## Target Environment

- Home Assistant sidebar app/custom panel provided by `panel_custom.async_register_panel(...)`.
- Frontend asset: `custom_components/zero_net_export/frontend/zero-net-export-app.js`.
- Delivery path remains GitHub/HACS-only for release; no direct HA file deployment is part of this implementation step.

## Supported Findings

- The Overview is rendered in `_overviewSection()` in `zero-net-export-app.js`.
- Existing helpers expose live reconciliation metrics through `_reconciliationMetrics()`.
- Existing helpers expose readiness structure through `_readinessModel(...)` and `_readinessItemTemplate(...)`.
- Existing selected-plan context is available through `_selectedEntry()`, `_selectedEntryId()`, `_entryOptions()`, and `_entryServiceData()`.
- Existing pause/resume service calls are already wired to `zero_net_export.pause_executor` and `zero_net_export.resume_executor`.
- Diagnostics remains a separate app section through `_diagnosticsSection()`.
- Managed Devices remains a separate app section through `_managedDevicesSection()` with Fleet Summary, Fleet List, and Unmanaged Candidate Queue order preserved.

## Unsupported / Excluded

- No backend control-loop behaviour change is required for this UI/UX refactor.
- No destructive live action is required for implementation validation.
- No Home Assistant core/frontend patching is required.
- No native device-page-first workflow is required.

## Unknowns / Validation Needs

- Exact live executor paused-state visual proof may require either a safe approved pause/resume action or a mocked/unit-level proof if live control action is not approved.
- Live mobile/narrow rendering must be validated with browser screenshots after implementation.
- Targeted Home Assistant logs should be collected after frontend load if live browser proof shows frontend errors or blank rendering.

## Feasibility Decision

Supported. Proceed with a scoped frontend presentation refactor plus tests. Preserve backend service semantics, tabs, plan selection, editable workflows, Diagnostics access, readiness explanations, and destructive confirmation gates.
