# Zero Net Export Feature Requests

This file tracks user-requested product enhancements separately from confirmed bugs.

## ZNE-FR-001 - Right-side managed-device settings action should reopen first-provisioned settings

- **status:** `candidate_0.1.96`
- **area:** `managed_devices`
- **requested by:** Riley, 2026-04-29
- **request:** On managed child rows, the settings/gear affordance should live on the right side as the native clickable configuration action, and clicking it should let the operator edit the settings captured when the device was first provisioned.
- **acceptance target:** managed child row text remains clean (`Managed Devices — Coffee machine`), the row keeps a native right-side settings/configuration action via `configuration_url`, and the edit path opens the managed-device settings/options flow rather than treating the gear as decorative text.
- **candidate implementation:** `0.1.96` removes the inline gear from managed child device names/models and preserves the native configuration URL used by Home Assistant for the row-level configuration action.
- **validation:** pending PNG proof before release/deploy approval; live HA validation only after the approved GitHub/HACS/restart path.
