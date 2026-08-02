# ZNE Managed Devices Load Dashboard Implementation Validation

Date: 2026-08-02
Scope: Frontend implementation for Managed Devices UI/UX load-dashboard workboard before HACS/live validation

## Implemented Cards

- `WB-ZNE-MDUIUX-001` Target Feasibility And Data Semantics
- `WB-ZNE-MDUIUX-002` Managed Load Dashboard
- `WB-ZNE-MDUIUX-003` Per-Device Watt Display
- `WB-ZNE-MDUIUX-004` Disabled Active Load Alert
- `WB-ZNE-MDUIUX-005` Table Hierarchy And Column Rename
- `WB-ZNE-MDUIUX-006` Candidate Queue Load Awareness
- `WB-ZNE-MDUIUX-007` Existing Workflow Preservation
- `WB-ZNE-MDUIUX-009` Optional Backend Aggregate Sensors

## Implementation Summary

Frontend-only changes in `custom_components/zero_net_export/frontend/zero-net-export-app.js`:

- Added Managed Load Dashboard tiles for Net Load, Managed Load, Enabled Managed, Disabled Managed, Active Managed, and ZNE Available.
- Added per-device load modelling with measured, estimated, and nominal watt semantics.
- Added row-level watt display and retained the on/off activity indicator as a separate `State` column.
- Added disabled-active alert for observed active devices that are disabled in ZNE.
- Added conservative unmanaged-candidate load display. Candidate rows show measured/supplied watts when reliable metadata exists, convert W/kW candidate power states, and otherwise show `Set in review` rather than guessing.
- Preserved existing filters, sorting, bulk controls, per-row enable/disable, candidate review/promotion, selected plan context, Diagnostics, and service wiring.
- Resolved backend aggregate sensors as unnecessary for this release because existing app payloads provide enough data for frontend-derived dashboard metrics without adding recorder-visible entities.

## Live Data Basis

Live API proof from `sensor.managed_devices_overview` showed the primary target case:

- `Lounge Room - Heated Floor` is disabled and observed active.
- `nominal_power_w=2400`.
- `current_power_w=null`.

The UI therefore labels this as estimated load rather than measured consumption.

## Validation Evidence

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`: passed.
- `python3 -m pytest tests/test_managed_devices_panel.py -q`: `28 passed`.
- `python3 -B -m py_compile custom_components/zero_net_export/*.py`: passed.
- `python3 -B -m unittest discover -s tests -q`: `Ran 644 tests ... OK`.
- `git diff --check`: passed.

The full unittest command prints expected negative validation messages from install-helper tests; the final result was `OK`.

## Remaining Work

- `WB-ZNE-MDUIUX-008`: responsive/browser validation remains ready.
- `WB-ZNE-MDUIUX-010`: release/live validation remains ready and requires HACS/release approval.
