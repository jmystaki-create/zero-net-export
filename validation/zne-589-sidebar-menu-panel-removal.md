# ZNE-589 sidebar menu panel removal validation

Date: 2026-05-06

## Scope

Remove the custom Home Assistant left-sidebar/menu entry labelled `ZNE Managed Devices` while preserving supported native Home Assistant managed-device workflows.

## Feasibility

Riley accepted `docs/ZNE-589_HOME_ASSISTANT_MENU_PANEL_FEASIBILITY.md` on 2026-05-06 before implementation.

## Repo changes under validation

- Removed `panel_custom.async_register_panel(...)` registration from integration setup.
- Removed `frontend`, `http`, and `panel_custom` manifest dependencies.
- Removed the shipped `custom_components/zero_net_export/frontend/managed-devices-panel.js` asset.
- Removed managed-device surface attributes pointing to `/zero-net-export-managed-devices`.
- Stopped writing managed child-device `configuration_url` links to the removed custom panel.
- Added registry sync behavior to clear stale installed managed-device `configuration_url` values.

## Repo validation

Focused command:

```bash
python3 -m unittest -q tests.test_managed_devices_panel tests.test_integration_page_device_lists
```

Result:

- `Ran 46 tests in 0.079s`
- `OK`

Additional command:

```bash
python3 -m py_compile custom_components/zero_net_export/__init__.py custom_components/zero_net_export/entity.py custom_components/zero_net_export/sensor.py && python3 -m unittest discover -s tests && git diff --check
```

Result:

- `py_compile` passed for changed Python files.
- `Ran 606 tests in 1.733s`
- `OK`
- `git diff --check` clean

Expected negative-path messages from install-helper tests were printed during full discovery.

## Remaining validation

Live Home Assistant release-managed install/restart and browser screenshot proof are still pending. ZNE-589 must not be closed until the installed HA sidebar no longer shows `ZNE Managed Devices`.
