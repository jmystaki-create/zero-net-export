# ZNE-578 live validation

- **date:** 2026-04-30 12:56 AEST
- **scope:** Verify the supported Home Assistant path for managed-device settings after confirming native integration rows cannot accept a custom gear beside the pencil.
- **approval:** Riley approved proceeding after reviewing the PNG mockup.

## Deployment

- Deployed current repo `custom_components/zero_net_export` to `/config/custom_components/zero_net_export` over SSH.
- Backup created under `/config/.openclaw_backups/custom_components/zero_net_export.backup-*-zne578`.
- Fingerprint validation after deploy reported:
  - `overall_match: true`
  - `all_tracked_files_match: true`
  - `manifest_version_matches: true`
  - no legacy artifacts

## Restart / health

- Restarted Home Assistant with `ha core restart`.
- API health check returned HTTP 200 with `{"message":"API running."}` after restart.
- Error log scan for `zero_net_export` / `Zero Net Export` returned no matching errors after restart.

## Device registry proof

Managed child device registry entry now contains:

```json
{
  "id": "73ebd7416d51c9feae737c9eb7ff7fa8",
  "name": "Managed Devices — Coffee machine",
  "model": "Managed Devices — Fixed managed load",
  "configuration_url": "homeassistant://zero-net-export-managed-devices?managed_device=01KP8MW539MQ724BBFZX2EF6S2%3Acoffee_machine",
  "identifiers": [["zero_net_export", "01KP8MW539MQ724BBFZX2EF6S2:managed-device:coffee_machine"]],
  "config_entries": ["01KP8MW539MQ724BBFZX2EF6S2"]
}
```

## Screenshot proof

- Before-click PNG screenshot: `bug-evidence/zne-578-before-click-managed-row.png`
  - Vision inspection confirmed this shows the Home Assistant Zero Net Export integration screen before clicking into the managed device.
  - Visible managed row: `Managed Devices — Coffee machine` with supporting text `Managed Devices — Fixed managed load · 19 entities`.
  - Visible native actions: chevron/open arrow, pencil edit icon, and three-dot overflow menu; no custom gear beside the pencil.
- Deep-link PNG screenshot: `bug-evidence/zne-578-live-deeplink-proof.png`
- Vision inspection confirmed the deep-link screenshot shows the `Managed Devices` panel with the `Coffee machine` editor open, not a loading/auth screen.

## Result

- **Passed for supported path:** Home Assistant's supported device-detail configuration cog can route through `configuration_url` to `ZNE Managed Devices` and open the selected managed-device editor.
- **Not changed:** Home Assistant's native integration row still cannot show a custom integration-provided gear beside the built-in pencil without an upstream Home Assistant frontend change.
