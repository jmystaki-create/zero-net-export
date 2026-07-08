# ACTIVE_USER_REQUESTS.md

This is the current project steering source of truth.

`docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md` are deprecated. Do not use them to choose work, defend old release scopes, or override current user-highlighted bugs and feature requests.

## Current user-highlighted scope

The current highest-priority request is the 2026-06-26 direction change:

1. **Port Zero Net Export into a Home Assistant application**
   - Zero Net Export should be developed as an application for Home Assistant, backed by the existing integration backend.
   - The application must capture the full Zero Net Export scope: overview, source mapping, managed devices, controls, runtime visibility, diagnostics/support, install validation, and multi-plan/service separation.
   - The native device-page/config-entry approach is superseded as the primary product shell.
   - Native Home Assistant surfaces remain supporting/fallback/automation surfaces.
   - Current direction and open decisions are tracked in `docs/ZNE_APPLICATION_DIRECTION.md`.
   - Feasibility evidence is recorded in `validation/zne-application-feasibility.md`.
   - Milestone 1 is planned in `docs/ZNE_APP_MILESTONE_1_PLAN.md` with milestone feasibility in `validation/zne-app-milestone-1-feasibility.md`.
   - Initial Riley decisions are recorded: sidebar by default, app name `Zero Net Export`, editable first release, multi-plan/service support from day one, conservative frontend stack default, core workflow coverage, strong destructive-action confirmation, keep Lovelace examples, HACS-only frontend delivery, and minimum Home Assistant version `2026.6.4+`.
   - Riley approved the GitHub/HACS-only pathway on 2026-06-26: changes should be pushed through GitHub, released as `0.2.0`, downloaded through HACS into Home Assistant, and then tested live.

2. **Overview console should feel alive**
   - Riley requested on 2026-07-08 that the Overview Reconciliation Status card become more realtime.
   - The console should expose meaningful current values for Source Power, Battery Power, and Confidence instead of blank/unit-only/unknown fields.
   - Freshness, stale data, and missing source blockers should be visible from the Overview card.
   - Tracked as `ZNE-FR-011` and `ZNE-FR-012` in `docs/FEATURE_REQUESTS.md`.
   - Current state: released and live-validated in `v0.4.2`. Evidence is recorded in `validation/zne-fr-011-012-overview-console-live-metrics.md`, `validation/0.4.2-release-validation.md`, and `validation/artifacts/v0.4.2-overview-console-live.png`.

3. **Overview Readiness must explain what is wrong**
   - Riley requested on 2026-07-08 that the Readiness section be structurally reformatted and explain the current errors plus what needs to be done to resolve them.
   - Tracked as `ZNE-FR-013` in `docs/FEATURE_REQUESTS.md`.
   - Current state: repo-validated pending release/live validation. Evidence is recorded in `validation/zne-fr-013-overview-readiness-clarity.md`.

Older native-surface bugs/features below remain evidence and stabilization context, but they should not drive new work unless Riley explicitly asks to finish a native release or the work directly supports the application port:

4. **Managed-device list must be managed-only**
   - The Zero Net Export native integration/device list must not show unmanaged candidates as peer rows beside managed devices.
   - Existing/stale `Un Managed — ...` device-registry rows should be removed/suppressed.

5. **Managed rows need the settings gear in the native right-side action location / visible right-side action location**
   - Managed device rows/surfaces must expose settings/configuration access through a visible right-side clickable gear affordance.
   - Do not fake the gear by embedding `⚙ Settings` inside the left-side device row name. Riley rejected that placement on 2026-04-29.
   - Do not treat hidden native `configuration_url` metadata as sufficient if the screenshoted Home Assistant surface does not show the designed gear.
   - Managed child row labels should stay clean, e.g. `Managed Devices — Coffee machine`, while settings/action entities may still use settings-oriented labels/icons where Home Assistant renders them as actual controls.
   - Clicking the right-side settings/configuration affordance should lead to editing the settings captured when the managed device was first provisioned.

6. **Unmanaged candidates stay behind workflow/backlog surfaces**
   - Unmanaged devices/candidates should remain discoverable through Managed Devices workflow/backlog/review surfaces.
   - They should not appear as peer `Un Managed — ...` rows in the same integration/device list as managed devices.

7. **Per-service service-card actions for multi-plan operation**
   - Each service/plan card needs an obvious per-service path to configure core parameters/source bindings such as solar, home load, and grid.
   - Each service/plan card needs an obvious per-service path to add managed devices/loads to that specific service only.
   - Preferred design is service-card three-dot actions labelled `Configure service` and `Add Managed Devices`; if Home Assistant does not allow custom integration actions in that exact overflow menu, use the nearest supported HA-native entry point while preserving the wording, scope, and outcome.
   - Implementation note: Home Assistant supports custom config-subentry overflow actions, so `Add Managed Devices` can appear with exact wording in the selected service overflow. Home Assistant's built-in entry reconfigure row is labelled by HA as `Reconfigure`, but the opened flow is titled `Configure service` and remains selected-entry scoped.
   - These actions must be entry-scoped so Summer/Winter plans cannot cross-edit each other's source bindings or managed-device fleets.

8. **Managed-load row three-dot delete action**
   - Riley requested a `Delete device` action in the managed-load row three-dot overflow menu on 2026-05-06.
   - Pressing it should remove that selected managed device from the owning Zero Net Export service/plan.
   - It must not remove the original Home Assistant device/entity.
   - This requires a fresh Home Assistant frontend/source feasibility check before design/code because prior ZNE-591/ZNE-592 work found arbitrary native managed-load row/device overflow action injection unsupported.

9. **Managed-load configuration card with editable captured settings**
   - Riley requested a configuration card on 2026-05-06 for the managed-load device surface.
   - The card should show all settings captured when the device was added.
   - Next to each label, there should be a field/control to modify the configuration relevant to that setting.
   - Saving must update only the selected managed device in the owning service/plan and must not mutate the original Home Assistant device/entity.
   - This requires a fresh Home Assistant target-environment feasibility check before design/code for the exact placement and editable-field behavior.

10. **No release-readiness claim without proof**
   - Do not tag, release, deploy, restart Home Assistant, or claim the next release is ready without explicit approval.
   - Required proof before release/deploy approval: tests pass and PNG evidence shows clean managed rows with the settings affordance on the native right side and no peer `Un Managed — ...` rows.

11. **No direct Home Assistant updates outside release management**
   - No features, bug fixes, or component updates should be pushed directly to the live Home Assistant install outside the GitHub release-management process.
   - Live changes must flow through committed code, pushed GitHub main/tag, published GitHub release, HACS refresh/upgrade, restart, and validation per `RELEASE_MANAGEMENT.md`.
   - Manual install writes are only acceptable as an explicitly approved release-management recovery step for the exact published release artifact, not as ad-hoc deployment.

## Operating rule

When project docs, tests, old release plans, cron prompts, or watchdog/supervisor guidance conflict with this file, this file wins until Riley changes the scope again.
