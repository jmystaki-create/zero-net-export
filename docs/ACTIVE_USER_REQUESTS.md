# ACTIVE_USER_REQUESTS.md

This is the current project steering source of truth.

`docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md` are deprecated. Do not use them to choose work, defend old release scopes, or override current user-highlighted bugs and feature requests.

## Current user-highlighted scope

Focus only on the concrete bugs/features Riley has flagged in the Home Assistant thread:

1. **Managed-device list must be managed-only**
   - The Zero Net Export native integration/device list must not show unmanaged candidates as peer rows beside managed devices.
   - Existing/stale `Un Managed — ...` device-registry rows should be removed/suppressed.

2. **Managed rows need the settings gear in the native right-side action location / visible right-side action location**
   - Managed device rows/surfaces must expose settings/configuration access through a visible right-side clickable gear affordance.
   - Do not fake the gear by embedding `⚙ Settings` inside the left-side device row name. Riley rejected that placement on 2026-04-29.
   - Do not treat hidden native `configuration_url` metadata as sufficient if the screenshoted Home Assistant surface does not show the designed gear.
   - Managed child row labels should stay clean, e.g. `Managed Devices — Coffee machine`, while settings/action entities may still use settings-oriented labels/icons where Home Assistant renders them as actual controls.
   - Clicking the right-side settings/configuration affordance should lead to editing the settings captured when the managed device was first provisioned.

3. **Unmanaged candidates stay behind workflow/backlog surfaces**
   - Unmanaged devices/candidates should remain discoverable through Managed Devices workflow/backlog/review surfaces.
   - They should not appear as peer `Un Managed — ...` rows in the same integration/device list as managed devices.

4. **No release-readiness claim without proof**
   - Do not tag, release, deploy, restart Home Assistant, or claim the next release is ready without explicit approval.
   - Required proof before release/deploy approval: tests pass and PNG evidence shows clean managed rows with the settings affordance on the native right side and no peer `Un Managed — ...` rows.

5. **No direct Home Assistant updates outside release management**
   - No features, bug fixes, or component updates should be pushed directly to the live Home Assistant install outside the GitHub release-management process.
   - Live changes must flow through committed code, pushed GitHub main/tag, published GitHub release, HACS refresh/upgrade, restart, and validation per `RELEASE_MANAGEMENT.md`.
   - Manual install writes are only acceptable as an explicitly approved release-management recovery step for the exact published release artifact, not as ad-hoc deployment.

## Operating rule

When project docs, tests, old release plans, cron prompts, or watchdog/supervisor guidance conflict with this file, this file wins until Riley changes the scope again.
