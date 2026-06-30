# ZNE-APP-001 stage 2 application workflow slice

Date: 2026-06-29
Status: implemented locally; unreleased; live Home Assistant validation pending

## Scope

This stage moves the `0.2.0` sidebar app beyond a static nonblank shell. The
app remains backed by the existing Home Assistant integration backend, but now
acts as the primary operator surface for the first workflow slice.

## Implemented

- Added in-app section navigation for Overview, Sources, Managed Devices,
  Controls, Runtime, Diagnostics, and Settings.
- Overview reads real Home Assistant entity state for controller status, safe
  mode, source mismatch, command center status, and exposed plan/config-entry
  context.
- Sources shows required source-role status entities and source blocker summary,
  with a Home Assistant configure handoff until app-native source mapping is
  implemented.
- Managed Devices shows fleet summary entities and adds entry-scoped service
  actions for enabling/disabling a managed record by key.
- Managed Devices includes a destructive remove action guarded by the typed
  confirmation phrase `REMOVE FROM ZNE`; the service removes only the Zero Net
  Export managed record and leaves the original Home Assistant entity intact.
- Controls can request safe existing Home Assistant service writes for:
  - controller enabled switch
  - live mode select
  - target export number
  - deadband number
  - battery reserve number
- Runtime surfaces core power/action entities.
- Diagnostics surfaces installed version/update/support status and adds a
  copyable support summary.

## Validation

Passed:

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- `python3 -m py_compile custom_components/zero_net_export/__init__.py custom_components/zero_net_export/app_api.py custom_components/zero_net_export/const.py`
- `python3 -m unittest -q tests.test_managed_devices_panel`
  - `Ran 8 tests`
  - `OK`
- `python3 -m unittest -q tests.test_managed_devices_panel tests.test_operator_docs_consistency tests.test_bucket_ownership_copy`
  - `Ran 26 tests`
  - `OK`
- `python3 -m unittest discover -s tests -q`
  - `Ran 613 tests`
  - `OK`
  - Output includes expected negative-path `ERROR:` lines from deploy/release
    guard tests.
- `git diff --check`

## Remaining before release claim

- Version/changelog/release notes for the next release candidate.
- Explicit release approval before HACS/live Home Assistant deployment.
- Live browser proof that the sidebar app renders correctly on desktop and
  narrow/mobile.
- Live write-path proof for one safe control edit.
- Live strong-confirmation proof for managed-device remove using a disposable
  managed load, confirming the original Home Assistant entity remains present.
