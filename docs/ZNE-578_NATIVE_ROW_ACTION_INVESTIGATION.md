# ZNE-578 Native row action investigation

## Question
Can a custom Home Assistant integration add its own gear action directly beside the pencil on the native Settings -> Devices & services -> Integrations -> Zero Net Export device row?

## Finding
No supported frontend extension point was found for injecting a custom per-device action into `ha-config-entry-device-row`.

Home Assistant frontend source inspected from `home-assistant/frontend`:

- `src/panels/config/integrations/ha-config-entry-device-row.ts`
  - The native integration device row hardcodes its end-slot controls:
    - chevron/next icon
    - vertical divider
    - edit pencil
    - overflow menu
  - The row menu hardcodes these actions:
    - edit
    - entities
    - disable/enable
    - delete when `entry.supports_remove_device`
  - The component does not read `device.configuration_url` and does not expose a custom integration-provided row action list.

- `src/panels/config/devices/ha-config-device-page.ts`
  - `device.configuration_url` is consumed on the device detail page only.
  - When present, the frontend adds a device action with `mdiCog` labelled `open_configuration_url`.

Home Assistant developer docs confirm `configuration_url` is a device registry property for linking to a configuration URL, but the current frontend source shows it is not rendered as an extra action on the native integration device row.

## Product implication
The exact requested placement — a custom Zero Net Export gear immediately beside the native pencil on the integration device row — is not achievable from a custom integration without an upstream Home Assistant frontend change.

The previous `0.1.97` panel is useful, but it is not equivalent to the requested native row gear.

## Closest supported path implemented in repo
Use the supported `device.configuration_url` cog action on the Home Assistant device detail page and point it directly to the `ZNE Managed Devices` panel with a `managed_device=<entry_id>:<device_key>` deep link.

The panel now reads the deep link and opens the selected managed-device editor automatically.

User flow:

1. Open the native Zero Net Export integration row.
2. Click the managed device row to open the Home Assistant device detail page.
3. Use Home Assistant's supported configuration cog action.
4. Land in `ZNE Managed Devices` with that managed device's settings editor already open.

## Remaining exact-placement option
If the gear must appear beside the native pencil on the integration row, the required path is an upstream Home Assistant frontend feature/PR to let integrations contribute per-device row actions to `ha-config-entry-device-row`.
