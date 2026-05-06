# ZNE-592 click-through workflow audit

Date: 2026-05-06
Status: failed_clickthrough_validated

## Purpose

Review all ZNE-591 / `0.1.108` edit/remove changes and validate the actual Home Assistant browser click-through workflow, not just row visibility or backend service behavior.

## Change review

ZNE-591 implementation commit: `3f0bb35 Fix ZNE managed device edit remove actions`

Changed files reviewed:

- `custom_components/zero_net_export/button.py`
  - Added `ZeroNetExportEditManagedDeviceButton`.
  - Added `ZeroNetExportRemoveManagedDeviceButton`.
  - Added both button entities to managed-load child devices.
- `custom_components/zero_net_export/__init__.py`
  - Added `zero_net_export.remove_managed_device` service/action.
  - Refactored managed-device update helpers.
  - Remove service mutates only the ZNE managed-device inventory, reloads the selected ZNE config entry, and leaves original Home Assistant devices/entities untouched.
- `custom_components/zero_net_export/entity.py`
  - Added managed-load settings action labels for `edit` and `remove`.
- `custom_components/zero_net_export/services.yaml`
  - Documented `remove_managed_device` service/action with required `confirm` field.
- Tests/docs/release files
  - Added tests for entity names/attributes/service availability and release text.
  - Release `0.1.108` validation proved install fingerprint, row visibility, and backend remove service behavior.

## Audit finding

The implementation exposed **Home Assistant button entities**. In Home Assistant's device page, clicking a button entity row opens the button entity more-info dialog. It does not navigate to a custom integration config flow, and it does not provide a custom confirmation workflow.

### Edit button behavior in code

`ZeroNetExportEditManagedDeviceButton.async_press()` only creates a persistent notification with manual instructions:

- Path: `Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices`
- Instruction: choose edit managed device manually.

It does not open or launch the selected managed-load edit flow.

### Remove button behavior in code

`ZeroNetExportRemoveManagedDeviceButton.async_press()` immediately calls `zero_net_export.remove_managed_device` with `confirm=True` and then creates a persistent notification.

There is no Home Assistant-native confirmation dialog in the visible click path before the removal action.

## Live click-through validation

Target device page:

- `http://192.168.86.200:8123/config/devices/device/479dc80f06b5e449440539ab8c9ebb96`
- Device: `Managed Devices — 7th test list`
- Firmware shown on page: `0.1.108`

Validation artifact:

- `validation/artifacts/zne-592-7th-test-list-clickthrough-ax-v0.1.108-rerun.json`
- `validation/artifacts/zne-592-7th-test-list-clickthrough-ax-v0.1.108-rerun-before.png`
- `validation/artifacts/zne-592-7th-test-list-clickthrough-ax-v0.1.108-rerun-after-edit-click.png`
- `validation/artifacts/zne-592-7th-test-list-clickthrough-ax-v0.1.108-rerun-after-close-edit-dialog.png`
- `validation/artifacts/zne-592-7th-test-list-clickthrough-ax-v0.1.108-rerun-after-remove-click.png`

Automation clicked the visible row/accessibility targets only. It did **not** press the more-info `Press` button for removal because that mutates live Home Assistant state without a confirmation workflow.

### Result: Edit row

Click target:

- `Managed Devices — 7th test list Edit Zero Net Export configuration`

Observed after click:

- URL remained the device page.
- Home Assistant opened a more-info dialog for the button entity.
- Dialog exposed `History`, `Activity`, and generic `Press`.
- No actual managed-load configuration flow opened.
- No selected-load edit form was reached.

Machine result:

```json
{
  "clicked": true,
  "hasEditDialog": true,
  "hasActualConfigureFlow": false
}
```

### Result: Remove row

Click target:

- `Remove from Zero Net Export`

Observed after click:

- URL remained the device page.
- Home Assistant opened a more-info dialog for the button entity.
- Dialog exposed `History`, `Activity`, and generic `Press`.
- No remove/unmanage confirmation workflow opened.

Machine result:

```json
{
  "clicked": true,
  "hasRemoveDialog": true,
  "hasRemoveConfirmation": false
}
```

## Validation conclusion

ZNE-591 / `0.1.108` does **not** meet the operator click-through brief.

What was valid:

- Rows are visible on the managed-load device page.
- Backend `zero_net_export.remove_managed_device` can remove a managed-load record while preserving the original Home Assistant entity/device.

What failed:

- `Edit Zero Net Export configuration` does not take the operator to a selected-load edit workflow.
- `Remove from Zero Net Export` does not take the operator to a confirmation workflow.
- The UI presents generic Home Assistant button more-info dialogs, which are not meaningful edit/remove workflows.

## Required next step

Before code changes, complete a fresh Home Assistant target-environment feasibility check for **direct, meaningful, native click-through edit/remove workflows** from a device page.

If Home Assistant does not support a direct native workflow from device-page entity rows, remove or replace the misleading button rows rather than claiming them as edit/remove actions.
