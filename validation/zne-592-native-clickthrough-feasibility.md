# ZNE-592 native managed-load click-through feasibility

## Task
Correct the managed-load device-page edit/remove workflow after `0.1.108` showed that visible button rows open generic Home Assistant button more-info dialogs instead of a meaningful selected-load edit or remove-confirmation workflow.

## Target environment
Home Assistant frontend native device and integration pages, specifically:

- managed-load device page actions rendered by `ha-config-device-page`
- standard entity rows / button-entity more-info behavior
- integration config-entry configure/options flow rendered by `ha-config-entry-row`

## Authoritative evidence checked

1. Home Assistant frontend source: `/tmp/ha-frontend-zne592/src/panels/config/devices/ha-config-device-page.ts`
   - Device-page actions are assembled in `_getDeviceActions()`.
   - A device action is added when `device.configuration_url` exists.
   - `homeassistant://...` configuration URLs are converted to internal `/...` routes.
   - The action label is Home Assistant's built-in `Open configuration URL` and uses a cog icon.

2. Home Assistant frontend source: `/tmp/ha-frontend-zne592/src/panels/config/integrations/ha-config-entry-row.ts`
   - A config-entry cog opens the integration options flow when `item.supports_options` is true.
   - The options flow is opened by frontend code via `showOptionsFlowDialog(this, this.data.entry, ...)`.
   - Reconfigure is similarly a frontend dialog action, not a route that a device entity row can launch directly.

3. Zero Net Export config flow source: `custom_components/zero_net_export/config_flow.py`
   - `ZeroNetExportConfigFlow.async_get_options_flow()` returns `ZeroNetExportOptionsFlow`.
   - The existing options flow contains the Managed Devices workspace, including edit and remove steps.

4. Live validation evidence: `validation/zne-592-clickthrough-workflow-audit.md`
   - Clicking `Edit Zero Net Export configuration` on `0.1.108` opened the generic button entity more-info dialog.
   - Clicking `Remove from Zero Net Export` opened the generic button entity more-info dialog.
   - Neither click opened selected-load edit or confirmation workflow.

## Supported findings

- **Supported:** A native Home Assistant device can expose a device-page action through `device.configuration_url`.
- **Supported:** If `configuration_url` starts with `homeassistant://`, Home Assistant frontend converts it to an internal path rather than opening an external tab.
- **Supported:** Linking a managed-load child device to `homeassistant://config/integrations/integration/zero_net_export` gives the operator a native click-through path from the device page to the Zero Net Export integration page.
- **Supported:** From the integration page, Home Assistant's native config-entry Configure cog opens the Zero Net Export options flow when the entry supports options.
- **Supported:** The existing Zero Net Export options flow owns the Managed Devices workspace and remove confirmation step.

## Unsupported findings

- **Unsupported:** A custom integration cannot make a normal Home Assistant button entity row directly open a selected config-flow/options-flow step from the device page.
- **Unsupported:** A button entity more-info dialog is not a meaningful selected-load edit workflow. It is a generic button entity control surface.
- **Unsupported:** A button entity row cannot provide the required remove-before-confirm native workflow without first opening the generic more-info dialog and requiring a generic `Press` action.
- **Unsupported:** Injecting custom overflow-menu actions or custom frontend/sidebar/panel is outside the approved scope.

## Unknowns / not relied on

- Whether future Home Assistant frontend versions will add custom-integration device-page action hooks. This implementation must not depend on that.
- Whether a deep link can open a specific options-flow step for a specific managed device. No supported route/API was found, so this is not relied on.

## Feasibility decision

A direct native device-page row/button that launches a selected managed-load edit step or remove-confirmation step is **not feasible** with supported Home Assistant surfaces.

The feasible correction is:

1. Stop exposing misleading per-managed-load edit/remove button rows on managed-load device pages.
2. Keep the guarded backend `zero_net_export.remove_managed_device` service for advanced/manual/scripted use.
3. Add a supported `configuration_url` to managed-load child devices so the native device page exposes Home Assistant's built-in `Open configuration URL` action.
4. Point that URL to the Zero Net Export integration page, where the native Configure cog opens the supported options flow and Managed Devices workspace.
5. Clean up stale registry entries for the removed misleading button entities on upgrade.

## Acceptance impact

This does not claim one-click selected edit/remove from the device page. It replaces misleading non-working rows with a supported native route into the existing managed-device workspace and preserves safe remove confirmation inside the options flow.
