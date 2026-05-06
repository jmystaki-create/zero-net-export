# ZNE-591 managed-device edit/remove actions validation

Date: 2026-05-06
Status: repo_validated

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

## Pending live validation

Release/live validation is still pending. Before marking ZNE-591 fixed, publish/install the next release in Home Assistant, restart, verify installed fingerprint, check logs, and capture browser proof that the managed-load page exposes the new native edit/remove rows and that removal does not delete the original Home Assistant device/entity.
