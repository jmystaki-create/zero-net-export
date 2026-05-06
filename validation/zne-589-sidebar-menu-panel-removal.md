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

## Live release validation

Release-managed validation passed in `0.1.106` after the `0.1.105` ZNE-588 stale-registry follow-up was superseded.

Evidence:

- Release record: `validation/0.1.106-release-validation.md`
- Sidebar proof PNG: `validation/artifacts/zne-589-ha-sidebar-v0.1.106.png`
- Sidebar proof JSON: `validation/artifacts/zne-589-ha-sidebar-v0.1.106.json`

Proof JSON counts across browser text/accessibility text:

- `ZNE Managed Devices`: 0
- `zero-net-export-managed-devices`: 0

## Decision

ZNE-589 is live-validated fixed in `0.1.106`.
