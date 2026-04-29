# Zero Net Export Feature Requests

This file tracks user-requested product enhancements separately from confirmed bugs.

## ZNE-FR-001 - Right-side managed-device settings action should reopen first-provisioned settings

- **status:** `candidate_0.1.97`
- **area:** `managed_devices`
- **requested by:** Riley, 2026-04-29
- **request:** On managed child rows, the settings/gear affordance should live on the right side as a visible clickable action, and clicking it should let the operator edit the settings captured when the device was first provisioned.
- **acceptance target:** managed row text remains clean (`Managed Devices — Coffee machine`), each visible managed-device row has a right-side gear button, and the edit path opens/saves the managed-device settings rather than treating the gear as decorative text or hidden `configuration_url` metadata.
- **candidate implementation:** `0.1.97` adds a `ZNE Managed Devices` custom panel with right-side gear buttons and an inline first-provisioned settings editor backed by the `zero_net_export.update_managed_device` service.
- **validation:** pending PNG proof before release/deploy approval; live HA validation only after the approved GitHub/HACS/restart path.
