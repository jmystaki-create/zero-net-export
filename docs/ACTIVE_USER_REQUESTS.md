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

4. **Per-service service-card actions for multi-plan operation**
   - Each service/plan card needs an obvious per-service path to configure core parameters/source bindings such as solar, home load, and grid.
   - Each service/plan card needs an obvious per-service path to add managed devices/loads to that specific service only.
   - Preferred design is service-card three-dot actions labelled `Configure service` and `Add Managed Devices`; if Home Assistant does not allow custom integration actions in that exact overflow menu, use the nearest supported HA-native entry point while preserving the wording, scope, and outcome.
   - Implementation note: Home Assistant supports custom config-subentry overflow actions, so `Add Managed Devices` can appear with exact wording in the selected service overflow. Home Assistant's built-in entry reconfigure row is labelled by HA as `Reconfigure`, but the opened flow is titled `Configure service` and remains selected-entry scoped.
   - These actions must be entry-scoped so Summer/Winter plans cannot cross-edit each other's source bindings or managed-device fleets.

5. **Managed-load row three-dot delete action**
   - Riley requested a `Delete device` action in the managed-load row three-dot overflow menu on 2026-05-06.
   - Pressing it should remove that selected managed device from the owning Zero Net Export service/plan.
   - It must not remove the original Home Assistant device/entity.
   - This requires a fresh Home Assistant frontend/source feasibility check before design/code because prior ZNE-591/ZNE-592 work found arbitrary native managed-load row/device overflow action injection unsupported.

6. **No release-readiness claim without proof**
   - Do not tag, release, deploy, restart Home Assistant, or claim the next release is ready without explicit approval.
   - Required proof before release/deploy approval: tests pass and PNG evidence shows clean managed rows with the settings affordance on the native right side and no peer `Un Managed — ...` rows.

7. **No direct Home Assistant updates outside release management**
   - No features, bug fixes, or component updates should be pushed directly to the live Home Assistant install outside the GitHub release-management process.
   - Live changes must flow through committed code, pushed GitHub main/tag, published GitHub release, HACS refresh/upgrade, restart, and validation per `RELEASE_MANAGEMENT.md`.
   - Manual install writes are only acceptable as an explicitly approved release-management recovery step for the exact published release artifact, not as ad-hoc deployment.

## Operating rule

When project docs, tests, old release plans, cron prompts, or watchdog/supervisor guidance conflict with this file, this file wins until Riley changes the scope again.
