# ZNE-576 / ZNE-577 live validation plan

Date prepared: 2026-04-30

## Scope

Validate the managed-device right-gear save flow after the repository fixes for:

- ZNE-576 — right-gear panel could update the wrong entry in multi-entry installs.
- ZNE-577 — right-gear panel save button could miss the open editor.

## Approval boundary

Do not execute the Home Assistant live validation steps below until Riley explicitly approves live validation.

No direct component writes should be made to the live Home Assistant install. If a new build is required, use the release-management path: committed code → pushed main/tag → GitHub Release → HACS refresh/upgrade → Home Assistant restart → validation.

## Acceptance criteria

1. The native Zero Net Export managed-device rows remain clean managed-only rows.
2. No peer `Un Managed — ...` rows appear beside managed devices.
3. The visible right-side settings/gear path opens the `ZNE Managed Devices` editor for the selected managed device.
4. Saving from the open editor persists a harmless settings change for the selected device.
5. In a multi-entry install, saving includes the owning config-entry id and does not update the wrong plan/service.
6. Unmanaged candidates remain available through workflow/backlog/review surfaces, not as peer rows.
7. Home Assistant logs show no Zero Net Export setup traceback or save-service traceback during the validation window.

## Pre-live repo validation

Run before any live validation:

```bash
python3 -m unittest tests.test_managed_devices_panel tests.test_integration_page_device_lists -q
python3 -m py_compile \
  custom_components/zero_net_export/entity.py \
  custom_components/zero_net_export/sensor.py \
  custom_components/zero_net_export/native_support.py
python3 -m unittest discover -s tests
git diff --check
```

## Live validation steps after approval

1. Confirm the installed Home Assistant release is the intended validated release.
2. Capture the Zero Net Export integration/device list before editing.
3. Confirm managed rows are clean and no peer `Un Managed — ...` rows are visible.
4. Open the right-side settings/gear path for a known managed device.
5. Capture the opened `ZNE Managed Devices` editor and record the owning entry id/device key if visible through API/state attributes.
6. Apply a harmless reversible edit to a non-critical managed-device setting.
7. Save from the visible editor.
8. Re-read the relevant Home Assistant state/options/config-entry evidence and confirm only the selected entry/device changed.
9. Revert the harmless edit if needed.
10. Capture logs for the validation window and scan Zero Net Export-specific messages.

## Evidence to collect

- PNG evidence of clean managed rows / no peer unmanaged rows.
- PNG evidence of the right-side settings/gear path opening the intended editor.
- API/state evidence showing the saved setting belongs to the selected entry/device.
- Log excerpt or command output showing no Zero Net Export traceback during the validation window.
- Final result: pass/fail for ZNE-576 and ZNE-577 separately.

## Current status

Prepared only. Live validation is pending explicit Riley approval.
