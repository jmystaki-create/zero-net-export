# ZNE-589 Home Assistant sidebar panel feasibility check

Date: 2026-05-06
Status: Accepted by Riley on 2026-05-06; implementation completed in repo, live validation pending release-managed install.

## Question

Can Zero Net Export remove the `ZNE Managed Devices` item from the Home Assistant left sidebar/menu without breaking supported native Home Assistant managed-device workflows?

## Target environment

- Home Assistant native Settings/sidebar shell.
- Zero Net Export custom integration installed through HACS.
- Current repo code in `custom_components/zero_net_export`.

## Evidence consulted

- User screenshot from 2026-05-06 shows `ZNE Managed Devices` as a Home Assistant left sidebar item with a gear icon below `Terminal`.
- Repo source `custom_components/zero_net_export/__init__.py` registers a custom frontend panel through `homeassistant.components.panel_custom.async_register_panel` with `sidebar_title="ZNE Managed Devices"`, `sidebar_icon="mdi:cog-outline"`, and `frontend_url_path="zero-net-export-managed-devices"`.
- Repo manifest currently declares frontend/panel dependencies: `frontend`, `http`, and `panel_custom`.
- Project technical direction in `docs/NATIVE_SURFACE_TECHNICAL_DIRECTION.md` says supported operator UX is native HA surfaces and there is no supported custom sidebar, custom panel, or external UI path.
- Existing Tier 1 feasibility in `docs/ZNE-TIER1_NATIVE_DEVICE_PAGE_FEASIBILITY.md` treats the current scope as native Home Assistant surfaces, not a custom frontend panel.

## Supported / controllable by ZNE

1. ZNE can stop registering the custom panel by removing or disabling the `async_register_panel(...)` call that supplies the sidebar title/path/icon.
2. ZNE can stop serving the panel static asset path if no other supported route requires `managed-devices-panel.js`.
3. ZNE can remove `panel_custom` / `frontend` manifest dependencies if no remaining code path needs them.
4. ZNE can keep backend-native managed-device services and config/subentry flows if those are still used by supported Home Assistant-native surfaces.

## Unsupported / should be excluded

1. Keeping the sidebar item hidden by CSS or frontend monkey patching. That would depend on unsupported HA frontend behavior.
2. Continuing to rely on `/zero-net-export-managed-devices` as a normal setup/troubleshooting path while claiming the custom menu/panel is removed.
3. Replacing the sidebar with another custom frontend route as part of this bug.

## Unknown / requires implementation inspection

1. Whether any current `configuration_url` or device-detail cog deep link still targets `/zero-net-export-managed-devices`; those links must be removed or retargeted to a supported native flow before the panel is removed.
2. Whether tests intentionally require the custom panel. Existing `tests/test_managed_devices_panel.py` currently asserts panel registration and will need to be updated or removed to match the new desired behavior.
3. Whether static frontend assets become unused after panel removal and should be deleted now or in a follow-up cleanup.

## Feasible bug-fix boundary

A safe ZNE-589 fix is feasible if it stays limited to removing the custom Home Assistant sidebar/menu panel and any direct links to it, while preserving native Home Assistant managed-device workflows such as service-card `Add Managed Devices`, Configure/options/subentry flows, device registry rows, diagnostics, and backend services.

## Acceptance criteria

- `ZNE Managed Devices` no longer appears in the Home Assistant left sidebar/menu after installing the fixed release and restarting HA.
- The integration no longer registers a custom panel with `sidebar_title="ZNE Managed Devices"`.
- No shipped ZNE device/configuration URL points to the removed custom panel route.
- Native Home Assistant managed-device flows still work from supported native entry points.
- Regression tests prove the panel is not registered and supported managed-device paths remain available.
- Live validation captures screenshot/browser evidence showing the sidebar item is gone.

## Acceptance decision

Riley accepted this feasibility boundary on 2026-05-06.

## Implemented repo path

- Removed custom panel registration from `async_setup`; the integration no longer calls `panel_custom.async_register_panel`.
- Removed `frontend`, `http`, and `panel_custom` manifest dependencies.
- Removed the shipped `managed-devices-panel.js` frontend asset.
- Stopped adding `/zero-net-export-managed-devices` metadata to managed-device surface attributes.
- Stopped pointing managed child-device `configuration_url` values to the removed custom panel and added registry sync behavior to clear stale installed `configuration_url` values.

## Remaining validation

Release-managed Home Assistant install/restart plus browser screenshot proof is still required before closing ZNE-589 as live-validated.
