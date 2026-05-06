# ZNE-590 — original thermostat device page feasibility

Date: 2026-05-06
Status: feasibility complete / implementation blocked for original-device attachment

## Question

Can Zero Net Export safely place its managed-load configuration entities directly on the existing Home Assistant device page for `climate.lounge_room_thermostat`, while staying inside `CONSTRAINTS.md` and without custom frontend/sidebar/panel work?

## Classification

- Native HA supported: exposing ZNE entities on a ZNE-owned managed-load device page.
- Entity/device registry technically possible but not acceptable as-is: merging ZNE entities onto another integration's existing thermostat device would require matching that device's identifiers.
- Exact placement inside the thermostat page/card: unsupported.
- Custom frontend/panel/card/sidebar: blocked unless Riley explicitly approves a project-direction change.

## Evidence checked

### Home Assistant developer docs

Home Assistant device registry documentation says a device is represented by one or more entities and that device `identifiers` uniquely define a device entry. It also notes devices from connected/read-only data sources should remain separate devices, and device merging is not currently a user feature.

### Home Assistant core source

`homeassistant.helpers.device_registry.DeviceRegistry.async_get_or_create` finds an existing device by `identifiers` or `connections`; if matched, it adds the calling config entry to that existing device. It validates that device info must include at least one identifier or connection. It does not expose a supported integration API to directly attach an entity to an arbitrary existing `device_id`.

Important source behavior observed from the current HA `dev` branch:

- `DeviceInfo` accepts `identifiers`, `connections`, and `via_device`.
- `async_get_or_create(...)` resolves `device = self.devices.get_entry(identifiers=identifiers, connections=connections)`.
- If the existing device is found, `_async_update_device(... add_config_entry_id=...)` adds the new config entry to that registry row.
- A primary config entry is only switched under specific conditions; nevertheless the device's `config_entries` set is modified.

### Live Home Assistant registry proof

Read-only registry inspection was performed by copying `/config/.storage/core.device_registry`, `/config/.storage/core.entity_registry`, and `/config/.storage/core.config_entries` from the validation HA host.

Current live thermostat device:

- Entity: `climate.lounge_room_thermostat`
- Device id: `d22826346da4887292ddc8031478e88d`
- Platform/config entry domain: `tuya_local`
- Device identifiers: `["tuya_local", "bfde93729769c94ee3mmd3"]`
- Device name/model/manufacturer: `Lounge Room` / `WIFI thermostat` / `Tuya`
- Existing entities on the device page include native Tuya entities such as climate, child lock, room temperature limit, temperature sensor/unit, and runtime.

Current live ZNE managed-load device for the user-reported page:

- Device id: `f4a50db1640e3aeb8bc77dcb222700bd`
- Platform/config entry domain: `zero_net_export`
- Config entry title: `Summer Plan`
- Device name by user: `Heated Floor - Lounge Room`
- Device identifier: `["zero_net_export", "01KQES5GS0B2XTEAK1SDHEK7KX:managed-device:test"]`
- Current confusing entities include `Settings — Test enabled`, `Settings — Test priority`, `Settings — Test review`, `Settings — Test reset overrides`, `Settings — Test Current power`, and long diagnostic/status rows.

## Finding

Zero Net Export can safely improve its own ZNE managed-load device page with native entities. That is supported and stays within `CONSTRAINTS.md`.

Zero Net Export should not attach entities directly to the original Tuya thermostat device page under the current constraints. The only proven native mechanism would be to make ZNE entity `device_info` match the Tuya device's identifiers/connections, which would effectively merge the ZNE config entry onto the Tuya-owned device registry row. That means ZNE would depend on another integration's identifiers and alter another integration's device ownership surface. This is fragile and outside the approved native operator path unless explicitly approved as experimental cross-integration device cohabitation.

Even if device merging were accepted, Home Assistant still would not let ZNE guarantee exact card/row placement inside the thermostat device page.

## Recommended decision

Proceed with Option A for ZNE-590:

- Preserve the original `climate.lounge_room_thermostat` page untouched.
- Clean up the ZNE managed-load device page using ZNE-owned native entities only.
- Rename/remove/hide confusing `Settings — Test ...` rows.
- Add clear entities such as `Zero Net Export enabled`, `Test load`, `Zero Net Export configuration`, and concise status/diagnostic rows.

Option B remains blocked unless Riley explicitly approves experimental cross-integration device registry merging and accepts that exact thermostat-card placement still cannot be guaranteed.

## Validation impact

Implementation can proceed only after Riley accepts Option A or explicitly approves the experimental Option B risk. Live validation for Option A must include browser proof of both:

1. The original thermostat page remains unchanged.
2. The ZNE managed-load page is concise and meaningful, with confusing `Settings — Test ...` clutter absent.
