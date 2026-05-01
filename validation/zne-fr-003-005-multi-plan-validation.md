# ZNE-FR-003 / ZNE-FR-005 multi-plan isolation validation

Date: 2026-05-01
Status: read-only validation plus focused repo coverage completed; live reversible write-path proof pending approval if required

## Scope

Validate the remaining multi-plan isolation requests:

- ZNE-FR-003 — controller config must be isolated per plan.
- ZNE-FR-005 — controller brain/runtime must be isolated per plan.

## Acceptance criteria

### ZNE-FR-003 — config/options isolation

- Summer Plan and Winter Plan have distinct Home Assistant config entry ids.
- Source bindings, policy values, target export, deadband, refresh cadence, grid layout, and options are stored per selected config entry.
- Saving through the selected service's Configure service/Reconfigure flow updates only that selected config entry.
- Evidence includes before/after config-entry snapshots if live write validation is approved.

### ZNE-FR-005 — runtime/brain isolation

- Runtime store keys are scoped by config entry id.
- Runtime controller state, mode/enabled state, action history, daily metrics, per-device runtime memory, and release metadata are read from/written to the selected entry's own runtime store.
- Runtime evidence shows Summer and Winter do not share the same persisted runtime device keys/history.
- If live runtime mutation is needed, service calls or entity toggles are approved before execution and before/after evidence is captured.

## Read-only evidence collected

Evidence files:

- `bug-evidence/zne-fr-003-005-readonly-storage-summary.json`
- `bug-evidence/zne-fr-003-005-readonly-state-summary.json`

Read-only Home Assistant storage/API inspection found two live Zero Net Export entries:

- Winter Plan — `01KQES4HMYAXXXSF6TQCAC8V28`
- Summer Plan — `01KQES5GS0B2XTEAK1SDHEK7KX`

Initial checks from `bug-evidence/zne-fr-003-005-readonly-storage-summary.json`:

```json
{
  "two_live_entries": true,
  "runtime_store_per_entry": true,
  "runtime_store_keys_are_entry_scoped": true,
  "titles": ["Winter Plan", "Summer Plan"],
  "inventory_names_by_entry": {
    "Winter Plan": ["7th - test light"],
    "Summer Plan": ["7th test list"]
  }
}
```

Runtime store evidence:

- Winter runtime key: `zero_net_export_runtime_01KQES4HMYAXXXSF6TQCAC8V28`
- Summer runtime key: `zero_net_export_runtime_01KQES5GS0B2XTEAK1SDHEK7KX`
- Winter daily metric device keys: `7th_test_light`
- Summer daily metric device keys: `7th_test_list`
- Both runtime stores record release `0.1.100` and previous installed version `0.1.99` independently.

## Current finding

Read-only evidence supports the architecture claim that the two live plans have separate config entries, separate managed-device inventory names, and separate entry-id-scoped runtime stores. This is useful but not yet sufficient to close ZNE-FR-003/ZNE-FR-005, because it does not prove the write paths cannot cross-edit the other entry.

## Repo validation completed

Focused regression coverage now directly checks:

- `tests.test_config_flow_device_runtime_overlay.ConfigFlowDeviceRuntimeOverlayTests.test_configure_service_sources_updates_selected_entry_only`: submitting Configure service source bindings updates/reloads only the selected entry (`summer-entry`) and does not touch a second `winter-entry` object.
- `tests.test_source_freshness_probes.SourceFreshnessProbeTests.test_runtime_store_key_is_scoped_to_config_entry_id`: two coordinator instances create separate runtime storage keys, `zero_net_export_runtime_summer-entry` and `zero_net_export_runtime_winter-entry`, instead of using a shared domain-level runtime store.

Validation commands passed:

```bash
python3 -m unittest -q tests.test_config_flow_device_runtime_overlay tests.test_source_freshness_probes
python3 -m unittest discover -s tests
git diff --check
```

Evidence:

- Focused tests: 95 tests OK.
- Full discovery: 602 tests OK.
- `git diff --check`: no whitespace errors.

### Live write-path validation — requires approval

Only after approval, perform a minimal reversible write test:

1. Capture before snapshots for both config entries and runtime stores.
2. Change a harmless selected-entry option on Summer Plan through the supported Configure service/Reconfigure path.
3. Re-read both entries and prove Winter Plan did not change.
4. Revert Summer Plan to its previous value if the change is not intended to remain.
5. Capture after/revert evidence.

If runtime mutation proof is needed, use the least risky supported action and avoid controlling real loads unless Riley explicitly approves that specific action.

## Decision

Status is `repo_and_readonly_validated_pending_live_write_decision`: read-only live evidence plus focused repo tests now cover the intended isolation architecture and selected-entry write path. If Riley requires live write-path proof, perform the minimal reversible test below only after explicit approval.
