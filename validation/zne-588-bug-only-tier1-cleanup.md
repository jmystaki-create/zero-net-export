# ZNE-588 bug-only Tier 1 cleanup validation

Date: 2026-05-01 19:52 AEST

## Scope

ZNE-588 is limited to the native Home Assistant Tier 1 device page. The broader Tier 2 guided workflow is not active scope.

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

## Live release validation

`0.1.105` was rejected/superseded for ZNE-588 because browser proof showed stale Home Assistant entity-registry rows still displaying the retired launcher buttons on the upgraded Winter Plan device page.

`0.1.106` adds upgrade/setup cleanup for those stale registry rows and passed live release-managed validation.

Evidence:

- Superseded release record: `validation/0.1.105-release-validation.md`
- Passing release record: `validation/0.1.106-release-validation.md`
- Device-page proof PNG: `validation/artifacts/zne-588-tier1-device-v0.1.106.png`
- Device-page proof JSON: `validation/artifacts/zne-588-tier1-device-v0.1.106.json`

Installed Winter Plan native device-page proof:

- `Open Sensors setup`: absent / count 0
- `Open Controls setup`: absent / count 0
- `Open Managed Devices setup`: absent / count 0
- `Open Diagnostics setup`: absent / count 0
- `Review diagnostics`: present
- `Connected devices`: present
- `Diagnostic`: present
- `Firmware: 0.1.106`: present

Runtime state API also returned `404` for the retired Winter Plan button entity IDs after restart.

## Decision

ZNE-588 bug-only Tier 1 cleanup is live-validated fixed in `0.1.106`.
