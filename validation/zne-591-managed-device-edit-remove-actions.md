# ZNE-591 managed-device edit/remove actions validation

Date: 2026-05-06
Status: released_live_validated

## Scope

ZNE-591 adds Home Assistant-native edit/remove affordances for Zero Net Export managed-load devices without custom frontend/sidebar/panel code and without unsupported device overflow-menu injection.

## Implemented path

- Added native managed-load button rows:
  - `Edit Zero Net Export configuration`
  - `Remove from Zero Net Export`
- Added backend service/action:
  - `zero_net_export.remove_managed_device`
- Kept `zero_net_export.update_managed_device` available.
- Removal mutates only the Zero Net Export managed-device inventory for the selected config entry, reloads that ZNE entry, and leaves the original Home Assistant device/entity untouched.
- Edit action points the operator to the supported Zero Net Export Configure flow path instead of inventing custom navigation or unsupported overflow-menu injection.

## Repo validation

Commands run from `/root/.openclaw/workspace/projects/zero-net-export`:

```text
python3 -m unittest tests.test_device_page_managed_settings -v
```

Result:

```text
Ran 13 tests in 0.007s
OK
```

```text
python3 -m unittest tests.test_managed_devices_panel -v
```

Result:

```text
Ran 4 tests in 0.000s
OK
```

```text
python3 -m unittest discover -v
```

Result:

```text
Ran 607 tests in 1.680s
OK
```

## Live validation

Release `0.1.108` was published and installed through the Home Assistant update entity. Home Assistant restarted and recovered; install fingerprint matched before and after restart (`overall_match=true`, `manifest_version=0.1.108`, all tracked files matched, no legacy artifacts). Post-restart state reported `update.zero_net_export_update` installed/latest `v0.1.108` and `sensor.zero_net_export_installed_version=0.1.108`; log tail showed no Zero Net Export tracebacks/errors/warnings.

Browser proof confirmed the managed-load page exposes the new native rows:

- `Edit Zero Net Export configuration`
- `Remove from Zero Net Export`
- existing operator rows including `Zero Net Export enabled`, `Test load`, `Priority`, `Zero Net Export configuration`, `Zero Net Export status`, and `Current power`

Removal proof used disposable managed load `Managed Devices — 7th - test light` (`device_key=7th_test_light`). Calling `zero_net_export.remove_managed_device` with `confirm=true` removed the ZNE managed-device row/entities while leaving the original Home Assistant light device/entity untouched (`light.7th` remained present and `on`).

Evidence:

- Release validation: `validation/0.1.108-release-validation.md`
- Managed-load browser proof: `validation/artifacts/zne-591-heated-floor-managed-device-v0.1.108.png` / `.json`
- Original thermostat proof: `validation/artifacts/zne-591-original-thermostat-device-v0.1.108.png` / `.json`
- Original light after remove proof: `validation/artifacts/zne-591-original-light-after-remove-v0.1.108.png` / `.json`

## Closure

ZNE-591 is live-validated fixed in `0.1.108`. The implemented path stays inside supported Home Assistant-native integration surfaces; unsupported arbitrary injection into Home Assistant's native device overflow menu was not implemented.
