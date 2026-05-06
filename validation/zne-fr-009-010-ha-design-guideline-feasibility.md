# ZNE-FR-009 / ZNE-FR-010 Home Assistant design-guideline feasibility

Date: 2026-05-06
Status: feasibility complete; no implementation started
Scope: Validate whether Riley's two requested managed-load features fit Home Assistant native design/developer surfaces.

## Requests checked

- **ZNE-FR-009:** Add `Delete device` to the managed-load row three-dot menu, removing the selected managed device from the owning Zero Net Export service/plan while preserving the original HA device/entity.
- **ZNE-FR-010:** Add a configuration card/surface that shows all add-time managed-device settings with editable fields next to each label.

## Authoritative evidence consulted

### Home Assistant developer docs

- Device registry docs define devices, child devices via `via_device`, `configuration_url`, `config_entries`, and `config_entries_subentries`. The docs explicitly allow `configuration_url` to link to Home Assistant UI paths using `homeassistant://<path>`.
- Config flow docs define UI-managed config entries, reconfigure steps, and data-entry forms.
- Options flow docs define native editable options forms, suggested values, validation, and reload behavior.

### Home Assistant frontend source inspected

- `/tmp/ha-frontend-zne592/src/panels/config/integrations/ha-config-entry-device-row.ts`
  - Renders the native integration-page device row overflow menu.
  - Shows a `Delete` device menu item only when `entry.supports_remove_device` is true.
  - The native delete path confirms destructively, then calls `removeConfigEntryFromDevice(hass, device.id, entry.entry_id)`.
- `/tmp/ha-frontend-zne592/src/panels/config/integrations/ha-config-sub-entry-row.ts`
  - Renders native config subentry rows.
  - Shows a reconfigure cog only when `supported_subentry_types[type].supports_reconfigure` is true.
  - Shows native subentry `Delete` in the row overflow and calls `deleteSubEntry(hass, entry_id, subentry_id)` after confirmation.
- `/tmp/ha-frontend-zne592/src/panels/config/devices/ha-config-device-page.ts`
  - Device page supports a `configuration_url` action and converts `homeassistant://...` to an internal route.
  - Device page imports integration-specific device actions only for built-in/frontend-owned integrations (`mqtt`, `zha`, `zwave_js`, `esphome`, `matter`) plus selected built-in behavior; it does not expose a general custom-integration hook for arbitrary device-page cards/actions.
- HA Core `config_entries.py` source from `home-assistant/core` dev branch:
  - `support_remove_from_device()` returns true when an integration component defines `async_remove_config_entry_device`.
  - Config entries expose `supports_remove_device` based on that component hook.

### Zero Net Export source inspected

- `custom_components/zero_net_export/config_flow.py`
  - Already exposes `managed_device` config subentries through `async_get_supported_subentry_types`.
  - Current `ZeroNetExportManagedDeviceSubentryFlow` supports adding managed devices via native HA subentry flow forms.
  - Current subentry support does not yet expose `async_step_reconfigure`, so the native subentry reconfigure cog is not currently available.

## Findings

### ZNE-FR-009 — native managed-load row overflow `Delete device`

**Supported, with a precise implementation path.**

Home Assistant already has the exact native row-overflow pattern Riley requested on `ha-config-entry-device-row`: when `entry.supports_remove_device` is true, the device row overflow includes a destructive `Delete` item. The built-in handler shows a confirmation dialog and calls `removeConfigEntryFromDevice` for the selected device and config entry.

To fit HA design guidelines, Zero Net Export should not inject a custom overflow item. Instead it should implement the backend integration hook that makes Home Assistant expose its native item:

- add integration component support for `async_remove_config_entry_device`;
- make the hook remove only the selected managed-device association/config from the owning ZNE config entry/subentry;
- preserve the original Home Assistant device/entity owned by the source integration;
- ensure stale ZNE managed entities/device rows are removed/reloaded;
- rely on HA's native confirmation and row menu rendering.

**Important constraint:** this is supported only if the target row is a ZNE-managed child device associated with the ZNE config entry. It is not a license to add arbitrary custom items to Home Assistant row overflow menus.

Verdict: **Fits Home Assistant guidelines if implemented through `async_remove_config_entry_device` / native `supports_remove_device`, not through frontend injection.**

### ZNE-FR-010 — editable managed-load configuration card

**Partially supported, depending on exact interpretation.**

The exact requested visual — an arbitrary custom card inserted into the native Home Assistant device page with custom labels and editable fields — is **not supported** for custom integrations by the current HA frontend source inspected. `ha-config-device-page.ts` supports:

- native entity cards grouped by entity category;
- a device info card action generated from `device.configuration_url`;
- integration-specific custom device actions only for selected HA frontend-owned integrations (`mqtt`, `zha`, `zwave_js`, `esphome`, `matter`).

It does **not** expose a general custom integration extension point to place a bespoke editable configuration card on the native device page.

However, the user outcome does fit Home Assistant design if implemented as one of these native patterns:

1. **Native config subentry reconfigure flow — recommended.**
   - Model each managed load as a HA config subentry.
   - Implement `async_step_reconfigure` on `ZeroNetExportManagedDeviceSubentryFlow`.
   - HA will expose a native reconfigure cog on that managed-device subentry row.
   - The flow can show all captured add-time settings with suggested current values, editable fields, validation errors, and save behavior.
   - This is the closest HA-native equivalent to “configuration card with editable fields”.

2. **Native device `configuration_url` to a supported HA configuration route.**
   - Keep the managed-load device-page configuration action pointing to the ZNE integration/configuration route.
   - That route can surface the subentry reconfigure flow and managed-device list using native HA components.

3. **Native config entities for selected frequently edited settings.**
   - Expose safe settings as `number`, `switch`, or similar config-category entities on the managed-load device page.
   - This can create adjacent labels/controls in HA entity rows, but it should not be used for every complex add-time setting if that creates noisy or misleading device pages.

Verdict: **The outcome fits HA guidelines; the exact arbitrary device-page card does not.** The compliant implementation should be a native subentry reconfigure/options flow and/or config entities, not a custom frontend card unless Riley explicitly approves custom/upstream frontend work.

## Recommendation

Proceed with a HA-native design, but keep these boundaries firm:

- **ZNE-FR-009:** implement the native remove-device backend hook so Home Assistant itself displays `Delete` in the existing row overflow.
- **ZNE-FR-010:** implement managed-device reconfiguration through a native config subentry reconfigure flow, optionally linked from the device page via `configuration_url`; use config entities only for high-value live-tweak settings.
- Do **not** build or promise arbitrary custom native device-page card insertion.
- Do **not** reintroduce custom sidebar/panel/frontend work unless explicitly approved.

## Acceptance criteria for implementation phase

- Written design maps each requested UI behavior to one of the supported HA-native surfaces above.
- Repo tests prove selected managed-device delete/reconfigure affects only the owning ZNE config entry/subentry.
- Repo tests prove original source HA device/entity remains intact.
- Live browser proof shows:
  - the native row overflow `Delete` appears only through HA's supported `supports_remove_device` path;
  - deleting removes the selected ZNE managed load only;
  - reconfigure/edit form shows captured settings with editable current values;
  - invalid values show HA-native validation feedback.

## Final feasibility decision

- **ZNE-FR-009:** feasible and guideline-compliant via HA's native remove-device support.
- **ZNE-FR-010:** feasible and guideline-compliant for the user outcome via HA-native subentry reconfigure/options/config entities; **not** feasible as an arbitrary custom card inserted into the native device page without custom/upstream frontend work.
