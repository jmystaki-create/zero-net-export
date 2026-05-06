# Zero Net Export Feature Requests

This file tracks user-requested product enhancements separately from confirmed bugs.

## ZNE-FR-001 - Right-side managed-device settings action should reopen first-provisioned settings

- **status:** `live_validated_supported_path`
- **area:** `managed_devices`
- **requested by:** Riley, 2026-04-29
- **request:** On managed child rows, the settings/gear affordance should live on the right side as a visible clickable action, and clicking it should let the operator edit the settings captured when the device was first provisioned.
- **acceptance target:** managed row text remains clean (`Managed Devices — Coffee machine`), each visible managed-device row has a right-side gear button, and the edit path opens/saves the managed-device settings rather than treating the gear as decorative text or hidden `configuration_url` metadata.
- **native-row finding:** repo investigation under `ZNE-578` found Home Assistant's native `ha-config-entry-device-row` does not expose a supported custom-integration hook for adding a gear beside the native pencil; exact placement would require an upstream Home Assistant frontend change.
- **candidate implementation:** `0.1.97` adds a `ZNE Managed Devices` custom panel with right-side gear buttons and an inline first-provisioned settings editor backed by the `zero_net_export.update_managed_device` service. This run adds the closest supported native Home Assistant path: the managed child device `configuration_url` now routes the Home Assistant device-detail-page cog directly to that panel and opens the selected managed-device editor from the `managed_device` deep link.
- **validation:** Riley's 2026-04-30 screenshots show `0.1.97` provides a separate Managed Devices gear/editor surface, but the native integration managed-device row still lacks the requested gear beside the pencil. Focused repo tests pass for the supported deep-link path; approved live deploy/restart/screenshot proof now passes for the supported device-detail cog path. Track implementation details under `ZNE-578`.

## ZNE-FR-002 - Controller identity must be plan-specific

- **status:** `live_validated_fixed`
- **area:** `multi_entry_controller_separation`
- **requested by:** Riley, 2026-04-30
- **request:** each Zero Net Export controller/service row should identify itself as its own named plan, not as a generic duplicated controller.
- **acceptance target:** native HA device/service rows for `Summer Plan` and `Winter Plan` show distinct plan titles for their controller devices.
- **implementation:** setup refreshes the entry-scoped primary controller device-registry metadata to the config entry title.
- **validation:** live HA evidence in `bug-evidence/ZNE-580-live-validation.md` shows distinct `Summer Plan` and `Winter Plan` controller rows.

## ZNE-FR-003 - Controller config must be isolated per plan

- **status:** `repo_and_readonly_validated_pending_live_write_decision`
- **area:** `multi_entry_controller_separation`
- **requested by:** Riley, 2026-04-30
- **request:** each controller plan has its own source roles, policy, target export/deadband, refresh cadence, and options.
- **acceptance target:** changing Summer Plan config does not alter Winter Plan config, and vice versa.
- **validation progress:** read-only live inspection confirms Summer/Winter are distinct config entries and have separate options/inventory snapshots. Focused repo coverage now proves Configure service source binding saves update/reload only the selected entry. Optional live reversible write-path proof remains pending Riley's decision/approval. Evidence: `validation/zne-fr-003-005-multi-plan-validation.md`.

## ZNE-FR-004 - Managed devices must be isolated per plan

- **status:** `live_validated_fixed`
- **area:** `managed_devices`
- **requested by:** Riley, 2026-04-30
- **request:** each controller plan has its own managed-device fleet, so Winter can control heated floors while Summer controls air-conditioning.
- **acceptance target:** managed-device rows, deep links, and save calls include the owning entry id and update only that plan's inventory.
- **implementation:** managed-device identifiers, configuration URLs, panel payloads, and update service targeting are entry-scoped.
- **validation:** live HA evidence in `bug-evidence/ZNE-580-live-validation.md` shows `Managed Devices — Coffee machine` scoped to `Winter Plan` and absent from `Summer Plan`.

## ZNE-FR-005 - Controller brain/runtime must be isolated per plan

- **status:** `repo_and_readonly_validated_pending_live_write_decision`
- **area:** `coordinator_runtime`
- **requested by:** Riley, 2026-04-30
- **request:** each controller has its own runtime brain: mode, enable state, guard state, action history, daily metrics, and persisted runtime memory.
- **acceptance target:** runtime store keys and emitted events are entry-scoped; one plan's decisions/history do not bleed into another plan.
- **validation progress:** read-only live inspection confirms each plan has an entry-id-scoped runtime store, with separate daily metric device keys (`7th_test_light` for Winter and `7th_test_list` for Summer). Focused repo coverage now proves coordinators create runtime store keys from their config entry id. Optional live runtime mutation proof remains pending Riley's decision/approval. Evidence: `validation/zne-fr-003-005-multi-plan-validation.md`.

## ZNE-FR-006 - Multi-plan validation evidence

- **status:** `live_validated_fixed`
- **area:** `qa`
- **requested by:** Riley, 2026-04-30
- **request:** prove separation with live HA evidence, not just code claims.
- **acceptance target:** PNG evidence shows distinct Summer/Winter controller rows and managed-device assignment, plus tests proving entry-scoped identity/update paths.
- **validation:** `bug-evidence/ZNE-580-live-validation.md` records passing focused tests, fingerprint-matched live deploy/restart, API recovery, log scan, registry evidence, and PNG proof.

## ZNE-FR-009 - Managed-load three-dot Delete device action

- **status:** `backlog_feasibility_required`
- **area:** `managed_devices / native_integration_page`
- **requested by:** Riley, 2026-05-06
- **request:** On the Zero Net Export integration page, each managed-load row three-dot menu should expose a `Delete device` action. Pressing it should immediately remove that managed device from the owning Zero Net Export service/plan.
- **source screenshot:** `/root/.openclaw/media/inbound/image---e2ac28c5-bc32-4ac8-b564-06a4232cdd9a.png` shows the current native row overflow menu for `Managed Devices — 7th test list` with only `20 entities` and `Disable device`.
- **acceptance target:** the selected managed-load row overflow exposes a clear delete/remove action; activating it removes only that selected managed-load record from the owning service/plan; the original Home Assistant device/entity remains intact; stale ZNE entities/device rows are removed after reload; tests and live browser proof validate the path.
- **target-environment gate:** do not design or implement until a fresh Home Assistant frontend/source feasibility check is written and accepted for custom integration actions in this exact managed-load row overflow menu. Prior ZNE-591/ZNE-592 evidence found arbitrary device-page/row overflow injection unsupported; if Home Assistant does not support this exact placement, Riley must choose between the closest supported native path or explicitly approving custom/upstream frontend work.
- **validation plan:** frontend/source feasibility evidence; repo tests for selected-entry managed-device removal and stale registry/entity cleanup; live HA browser proof that the action is visible in the row overflow and that pressing it removes only the ZNE managed-load record without removing the underlying Home Assistant device/entity.
