# ZNE-APP-002 Sources workflow implementation validation

Date: 2026-06-30
Status: repo validated; live GitHub/HACS validation pending release approval

## Scope implemented

- Added app-native source-role editing in the Zero Net Export sidebar app.
- Added richer Sources rows for all source roles:
  - required/optional role label
  - current binding label
  - live status
  - reading
  - age
  - issue count
  - editable source binding input
- Added plan selection for source-role saves.
- Added backend service `zero_net_export.update_source_roles`.
- The service:
  - scopes updates to the selected config entry
  - updates source bindings through `hass.config_entries.async_update_entry`
  - validates proposed source-role settings before saving
  - reloads the selected entry after save
  - avoids native Home Assistant page/card/row injection
- Added service metadata in `services.yaml`.
- Added focused regression coverage for the app Sources workflow and backend
  service contract.

## Repo validation

Passed:

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- `python3 -m py_compile custom_components/zero_net_export/__init__.py`
- `python3 -m unittest -q tests.test_managed_devices_panel`
  - `Ran 13 tests`
  - `OK`
- `python3 -m unittest -q tests.test_config_flow_device_runtime_overlay`
  - `Ran 92 tests`
  - `OK`
- `python3 -m unittest -q tests.test_bucket_ownership_copy tests.test_source_repair_guidance tests.test_setup_notice_copy`
  - `Ran 50 tests`
  - `OK`
- `python3 -m unittest discover -s tests`
  - `Ran 618 tests`
  - `OK`
- `git diff --check`

## Notes

The full test run prints expected negative-path messages from release/deploy
guard tests, then finishes `OK`.

## Remaining validation

Live validation is pending because the approved project rule requires changes to
flow through GitHub and HACS, not direct Home Assistant file-backend deployment.

Recommended live path:

1. Commit and push this implementation.
2. Prepare a corrective/feature release candidate, likely `v0.2.3`, after
   explicit release-version approval.
3. Install through HACS.
4. Restart Home Assistant.
5. Confirm install fingerprint and app/static routes.
6. Capture desktop and narrow Sources screenshots.
7. Perform a reversible source-role write only after identifying and approving a
   safe mapping to modify and restore.
8. Check targeted Zero Net Export logs.
