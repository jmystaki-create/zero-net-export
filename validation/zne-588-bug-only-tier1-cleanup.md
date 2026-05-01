# ZNE-588 bug-only Tier 1 cleanup validation

Date: 2026-05-01 19:52 AEST

## Scope

ZNE-588 is limited to the native Home Assistant Tier 1 device page. The broader Tier 2 guided workflow is split to `ZNE-FR-008`.

This patch removes the misleading native device-page button entities that looked like direct navigation controls but only fired Home Assistant `button.press` actions:

- `Open Sensors setup`
- `Open Controls setup`
- `Open Managed Devices setup`
- `Open Diagnostics setup`

Existing truthful/native actions remain, including command-center guide, diagnostics review/snapshot/checklist, managed-device review, fleet console, and reset actions.

## Repo validation

Focused command:

```bash
python3 -m unittest -q tests.test_button_entity_categories tests.test_sensor_entity_categories tests.test_device_page_managed_settings && git diff --check
```

Result:

- `Ran 115 tests in 0.295s`
- `OK`
- `git diff --check` clean

Full discovery command:

```bash
python3 -m unittest discover -s tests
```

Result:

- `Ran 607 tests in 1.660s`
- `OK`

Expected negative-path messages from install-helper tests were printed during full discovery.

Additional syntax check:

```bash
python3 -m py_compile custom_components/zero_net_export/button.py
```

Result: passed.

## Remaining validation

Live Home Assistant deployment and browser screenshots are still pending approval. Do not close ZNE-588 until the installed native device page is screenshot-validated and accepted.
