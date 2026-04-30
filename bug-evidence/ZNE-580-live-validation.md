# ZNE-580 live validation — multi-plan controller separation

Date: 2026-04-30

## Scope
Validate that multiple Zero Net Export services/plans remain visually and registry-separated after deploy/restart.

## Repo validation

```text
python3 -m unittest -q tests.test_integration_page_device_lists tests.test_managed_devices_panel tests.test_config_flow_device_runtime_overlay
----------------------------------------------------------------------
Ran 132 tests in 0.158s

OK
```

## Live deploy / restart evidence

- Deployed `custom_components/zero_net_export` from the repo to Home Assistant `/config/custom_components/zero_net_export` with a pre-deploy backup under `/config/.openclaw_backups/custom_components/`.
- Install fingerprint validation: `overall_match=True`, `mismatches=[]`.
- Restart command: `ha core restart` over SSH.
- API recovery: `{"message":"API running."}`.
- Recent log scan: no Zero Net Export errors in the checked post-restart log window.

## Live registry evidence

Saved JSONL: `bug-evidence/zne-580-live-device-registry.jsonl`

```jsonl
{"id":"ba17fc1f3e0f652e0305e1df0b199b3a","name_by_user":null,"name":"Winter Plan","model":"Zero Net Export","identifiers":[["zero_net_export","01KP8MW539MQ724BBFZX2EF6S2"]],"config_entries":["01KP8MW539MQ724BBFZX2EF6S2"],"configuration_url":null}
{"id":"73ebd7416d51c9feae737c9eb7ff7fa8","name_by_user":null,"name":"Managed Devices — Coffee machine","model":"Managed Devices — Fixed managed load","identifiers":[["zero_net_export","01KP8MW539MQ724BBFZX2EF6S2:managed-device:coffee_machine"]],"config_entries":["01KP8MW539MQ724BBFZX2EF6S2"],"configuration_url":"homeassistant://zero-net-export-managed-devices?managed_device=01KP8MW539MQ724BBFZX2EF6S2%3Acoffee_machine"}
{"id":"e33126d67fca1421567b4aa2854255a3","name_by_user":null,"name":"Summer Plan","model":"Zero Net Export","identifiers":[["zero_net_export","01KQE7AHV2KSQB545QCJZTTBM1"]],"config_entries":["01KQE7AHV2KSQB545QCJZTTBM1"],"configuration_url":null}
```

## Browser screenshot evidence

- `bug-evidence/zne-580-live-ha-integrations.png` shows separate Home Assistant service cards/rows for `Summer Plan` and `Winter Plan`, with `Managed Devices — Coffee machine` listed only under `Winter Plan`.
- `bug-evidence/zne-580-live-ha-managed-devices-panel.png` shows the managed-device editor opened for `Coffee machine` via the Winter entry deep link.

## Result
Pass. ZNE-580 is live-validated fixed. The native Home Assistant integration page now presents distinct Summer/Winter controller rows and keeps the managed Coffee machine device scoped to the Winter plan entry.
