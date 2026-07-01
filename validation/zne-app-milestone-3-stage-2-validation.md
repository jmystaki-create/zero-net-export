# ZNE-APP-003 Stage 2 repo validation

Date: 2026-07-01
Status: repo validated; live validation pending

## Scope

Stage 2 extends the app-native Managed Devices fleet view with:

- Priority and readiness filters.
- Sorting by priority, status, and last-seen age.
- Last Seen and Blockers columns.
- Bulk visible-row selection controls.
- Bulk enable/disable actions guarded by a confirmation checkbox.

## Fixes during validation

Validation review found two bulk-action issues before release:

- `Select All` and `Clear Selection` were unreachable when no device was
  already selected because selection-length validation ran first.
- Bulk enable/disable did not have the required explicit confirmation control.

The frontend now handles `Select All` and `Clear Selection` before selected-row
validation, clears the confirmation checkbox when clearing selection, and keeps
bulk enable/disable disabled until at least one visible device is selected and
the confirmation checkbox is checked.

## Repo validation

Passed:

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- `python3 -m py_compile custom_components/zero_net_export/__init__.py custom_components/zero_net_export/app_api.py custom_components/zero_net_export/sensor.py custom_components/zero_net_export/config_flow.py`
- `python3 -m unittest discover -s tests`
  - `Ran 620 tests`
  - `OK`
  - Output includes expected negative-path `ERROR:` lines from release/deploy
    guard tests.
- `git diff --check`

## Remaining validation

Live validation is still required before marking Stage 2 done:

- Release/install through the approved GitHub/HACS path only.
- Restart Home Assistant and wait for API recovery.
- Verify installed version and install fingerprint.
- Verify `/zero-net-export` and static app asset routes.
- Capture desktop and narrow browser proof for the Managed Devices tab.
- Confirm filters, sorting, Last Seen, Blockers, selection, confirmation, and
  bulk enable/disable behavior in the installed app.
- Scan targeted Home Assistant logs for Zero Net Export errors/warnings.
