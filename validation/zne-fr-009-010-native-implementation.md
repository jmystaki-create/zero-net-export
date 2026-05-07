# ZNE-FR-009 / ZNE-FR-010 native implementation validation

Date: 2026-05-07
Status: repo validated; live Home Assistant/browser validation pending release approval
Scope: Implement Riley-approved Home Assistant-native direction after feasibility acceptance.

## Implemented

- ZNE-FR-009: added `async_remove_config_entry_device` in `custom_components/zero_net_export/__init__.py` so Home Assistant can expose its native `supports_remove_device` / row-overflow Delete path for ZNE managed-load child devices.
- The native remove hook maps the selected HA device-registry row back to the owning ZNE config entry and managed-device key, removes only that managed-device inventory payload, updates the selected entry options, reloads that entry, and leaves the original/source Home Assistant device/entity untouched.
- ZNE-FR-010: added managed-device subentry reconfigure flow support in `ZeroNetExportManagedDeviceSubentryFlow`, with native forms to pick an existing managed load and edit the captured add-time settings.
- Kept custom frontend/sidebar/card/overflow injection out of scope.

## Validation run

Commands run from `/root/.openclaw/workspace/projects/zero-net-export`:

```bash
python3 -m unittest -q tests.test_config_flow_device_runtime_overlay tests.test_managed_devices_panel
python3 -m py_compile custom_components/zero_net_export/__init__.py custom_components/zero_net_export/config_flow.py
git diff --check
python3 -m unittest discover -s tests
python3 -m py_compile custom_components/zero_net_export/__init__.py custom_components/zero_net_export/config_flow.py
git diff --check
```

## Evidence

- Focused tests: `Ran 97 tests`, `OK`.
- Full discovery: `Ran 610 tests`, `OK`.
- `py_compile` completed without errors for changed component files.
- `git diff --check` completed without whitespace errors.

Expected negative test output remains present inside the full discovery stream for release/deploy guard tests; those tests intentionally print ERROR lines while asserting guard failures and the suite still finished `OK`.

## Remaining validation

- Live Home Assistant install/restart/browser proof is pending release approval.
- Browser proof should show the native row-overflow Delete path is exposed by Home Assistant for ZNE managed-load rows and that removing a disposable managed load leaves the original HA device/entity intact.
- Browser proof should show the native managed-device reconfigure/edit form with captured settings and a safe edit affecting only the selected managed device.
