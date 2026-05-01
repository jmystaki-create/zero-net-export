# project_status.md

project_name: zero-net-export
status: active
last_modified: 2026-05-01 11:55

## Current focus
ZNE-583 is reopened after Riley's screenshot showed `Invalid flow specified` still visible in Home Assistant `0.1.99`; the previous validation only checked that the form content appeared and missed that the returned config-flow payload had `flow_id`/`handler` set to `null`. Repo fix is in progress to preserve the active config-flow identity when delegating to the service options flow. Do not deploy, restart Home Assistant, tag, publish, or claim a replacement release is ready until the fix is committed, pushed, released through HACS, restarted, and revalidated on the live UI.

## Active bugs
- ZNE-584 — setup warning is too wordy and unclear. Fixed and live-validated: warning starts with impact and the primary action, lists missing setup, and no longer duplicates fallback guidance in the primary action. Status: validated.
- ZNE-583 — service-row `Reconfigure` opens with `Invalid flow specified`. Reopened 2026-05-01: Riley screenshot from `0.1.99` proves the invalid-flow banner is still visible. Root cause found: the config-flow wrapper delegated to an options-flow form whose `flow_id` and `handler` remained `null`, so Home Assistant could render fields while still reporting an invalid flow. Status: fixing.
- ZNE-578 — native managed-row gear beside the pencil is not supported by current Home Assistant frontend. Closest supported path is implemented and live-validated: managed child-device `configuration_url` opens the Home Assistant device-detail cog/deep-link into the `ZNE Managed Devices` editor. Exact native-row placement requires upstream HA frontend work if still required.
- ZNE-579 — Add service wrongly aborted as `already_configured`. Fixed and live-validated; unique ids are now scoped to the submitted service/system name.
- ZNE-580 — multiple services looked like duplicated generic controllers. Fixed and live-validated; Summer/Winter plan controller rows and managed-device scoping are separated.
- ZNE-581 — no obvious per-service Configure service action. Released in `0.1.98`; Home Assistant's native per-service row actions are visible on the live Zero Net Export integration detail page.
- ZNE-582 — no obvious per-service Add Managed Devices action. Released in `0.1.98`; Home Assistant's native per-service row actions and top-level Add Managed Devices action are visible on the live Zero Net Export integration detail page.

## Active feature scope
- ZNE-FR-001 — managed-device settings should reopen first-provisioned settings. Supported device-detail cog/deep-link path is live-validated; exact native-row gear remains upstream-blocked.
- ZNE-FR-002 — controller identity must be plan-specific. Live-validated fixed.
- ZNE-FR-003 — controller config must be isolated per plan. Tracked; needs validation through the per-service Configure service flow.
- ZNE-FR-004 — managed devices must be isolated per plan. Live-validated fixed for Winter/Summer managed-device scoping.
- ZNE-FR-005 — controller runtime/brain state must be isolated per plan. Tracked pending validation.
- ZNE-FR-006 — multi-plan validation evidence. Live-validated for controller identity and managed-device assignment.

## Validation evidence
- ZNE-584: repo validation passed with focused copy tests `python3 -m unittest -q tests.test_setup_notice_copy tests.test_repairs_copy tests.test_translation_sync tests.test_bug_tracker_ids` (10 tests OK), full test discovery `python3 -m unittest discover -s tests` (600 tests OK), and `git diff --check`. Follow-up duplication guard committed as `8c4b4b7` and revalidated with the same focused/full test suite plus `git diff --check`. Live validation deployed the repo build, fingerprint-matched it (`overall_match=true`), restarted HA with API recovery after 22s, and captured browser proof `bug-evidence/zne-584-final-live-repair-detail.png` / `.json` showing action-first repair copy and fallback guidance present once.
- ZNE-583: previous validation is superseded by Riley's 2026-05-01 screenshot. It proved the validation was incomplete: it checked DOM text after clicking `Reconfigure` but did not assert the raw Home Assistant config-flow identity. New regression coverage now asserts the reconfigure wrapper preserves non-null `flow_id` and `handler` while keeping the first step id as `reconfigure` and the submit transition as `configure_service_sources`. Focused repo validation passed with `python3 -m py_compile custom_components/zero_net_export/config_flow.py` and `python3 -m unittest -q tests.test_config_flow_device_runtime_overlay` (88 tests OK). Full validation/release/live evidence is pending.
- ZNE-578: focused tests passed and live Home Assistant proof captured for the supported device-detail cog/deep-link path.
- ZNE-579: focused config-flow tests passed; live Home Assistant add-service validation succeeded without `already_configured` and cleanup was completed.
- ZNE-580: focused multi-entry tests passed; live Home Assistant screenshots and registry evidence show separate Summer/Winter rows with Coffee machine scoped to Winter only.
- ZNE-581/ZNE-582: repo implementation committed as `32796d8 Add per-service HA entry actions`; release validation passed with `python3 -m py_compile custom_components/zero_net_export/config_flow.py`, `python3 -m unittest discover -s tests` (599 tests OK), HACS install fingerprint match, Home Assistant restart, entity-state checks, logs scan, and live browser screenshot.
- Release `0.1.98`: GitHub release `v0.1.98` published from commit `4140c1d930fcc6370ec99c108b424042574a0c42`; HACS installed `v0.1.98`; Home Assistant restarted and reported `sensor.zero_net_export_installed_version = 0.1.98`, `sensor.zero_net_export_previous_installed_version = 0.1.97`, and `update.zero_net_export_update` installed/latest `v0.1.98`.
- Release `0.1.99`: GitHub release `v0.1.99` published; HACS repository refresh succeeded; HACS installed `v0.1.99`; install fingerprint matched (`overall_match=true`); Home Assistant restarted and reported `update.zero_net_export_update` installed/latest `v0.1.99`, `sensor.zero_net_export_installed_version = 0.1.99`, `sensor.zero_net_export_previous_installed_version = 0.1.98`; Winter Plan and Summer Plan config entries are `loaded`; 136 Zero Net Export entities are present.
- Release validation records: `validation/0.1.98-release-validation.md`, `validation/0.1.99-release-validation.md`.
- Browser evidence: `bug-evidence/zne-0.1.98-live-integrations.png`.

## Blockers / approvals
- Exact native managed-row gear placement for ZNE-578 requires an upstream Home Assistant frontend feature request/PR if Riley still wants that exact UI location.
- Runtime control remains blocked in the validation Home Assistant instance until required source roles are configured; this is expected and not a release-install failure.

## Next best action
Finish ZNE-583 fix validation, commit it, then release/deploy through the approved release-management path and revalidate the exact UI path that showed `Invalid flow specified`.
