# ZNE-FR-018 Managed Devices on/off traffic light validation

Date: 2026-07-17
Status: repo validated, pending release/live validation

## Request

Riley requested a per-item traffic light in the Managed Devices Fleet List showing whether each managed device is currently on or off, using green for on and red for off.

## Acceptance Criteria

- Each managed Fleet List row includes a current on/off indicator.
- Active rows use a green `On` traffic light.
- Inactive rows use a red `Off` traffic light.
- The indicator is derived from existing backend runtime state, not a new ad hoc field.
- Color is not the only signal; the row also exposes text and accessible/title labels.
- Existing fleet enablement status, filters, sorting, bulk controls, actions, and unmanaged candidate queue ordering remain intact.

## Target-Environment Feasibility

- Supported: the Zero Net Export Home Assistant app already renders Fleet List rows in `custom_components/zero_net_export/frontend/zero-net-export-app.js`.
- Supported: `sensor.managed_devices_overview` already provides per-row managed-device details, and `recorder_safe_managed_detail(...)` includes `observed_active`.
- Supported: this can be implemented as a custom-panel DOM/CSS rendering change.
- Unsupported/not used: Home Assistant native frontend row injection, custom native device-row overflow injection, direct live install writes, or a new backend API just for this indicator.

## Implementation Summary

- Added `_deviceActivityIndicator(device)` to map `observed_active` to `On`/`Off`.
- Added a compact `Power` column to the managed Fleet List.
- Added `zne-traffic-light` CSS using the existing success/error color variables.
- Added focused regression coverage in `tests/test_managed_devices_panel.py`.

## Validation Evidence

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
  - Result: passed.
- `python3 -m unittest tests.test_managed_devices_panel`
  - Result: passed.
  - Evidence: `Ran 26 tests in 0.005s`, `OK`.
- `git diff --check`
  - Result: passed.

## Notes

- `pytest` and `python -m pytest` could not be used in this shell because `pytest` is not installed and `python` is not available on PATH. The focused test file is standard-library `unittest`, so it was validated directly with `python3 -m unittest`.
- Live Home Assistant browser validation remains pending the normal release path.
