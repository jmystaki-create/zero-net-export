# project_status.md

project_name: zero-net-export
status: active
last_modified: 2026-05-01 12:45

## Current focus
ZNE-587 is fixed and repo-validated from Riley's Add Managed Devices screenshot feedback: climate devices such as ACs and heated floors were missing from the fixed-load control entity picker. The repo fix adds `climate` as an eligible fixed managed-device domain and is ready for release packaging/live validation if requested.

## Active bugs
- ZNE-587 — climate devices missing from Add Managed Devices selector. Fixed and repo-validated: `climate` entities are now fixed-load candidates, shown by the Add Managed Devices entity selector, and supported by fixed-toggle adapter inference. Status: validated_pending_release.
- ZNE-586 — Configure service source-selection step is still too wordy. Fixed and repo-validated: source-selection copy is now a short missing/progress/issues block with one fallback sentence and no role guide, repair essay, repeated paths, or bucket ownership text. Status: validated_pending_release.
- ZNE-585 — Configure service modal copy is too wordy. Fixed and repo-validated: initial grid-layout step now shows only a short status block, removes repeated path/bucket ownership guidance, and keeps detailed help out of the first modal. Status: validated_pending_release.
- ZNE-584 — setup warning is too wordy and unclear. Fixed and live-validated: warning starts with impact and the primary action, lists missing setup, and no longer duplicates fallback guidance in the primary action. Status: validated.
- ZNE-583 — service-row `Reconfigure` opened with `Invalid flow specified`. Fixed and release-validated in `0.1.100`: HACS installed the release, fingerprint matched, Home Assistant restarted, and Slave browser proof shows the service-row `Reconfigure` dialog opens with grid sensor choices and `invalidFlowCount=0`. Status: released_live_validated.
- ZNE-578 — native managed-row gear beside the pencil is not supported by current Home Assistant frontend. Closest supported path is implemented and live-validated: managed child-device `configuration_url` opens the Home Assistant device-detail cog/deep-link into the `ZNE Managed Devices` editor. Exact native-row placement requires upstream HA frontend work if still required.
- ZNE-579 — Add service wrongly aborted as `already_configured`. Fixed and live-validated; unique ids are now scoped to the submitted service/system name.
- ZNE-580 — multiple services looked like duplicated generic controllers. Fixed and live-validated; Summer/Winter plan controller rows and managed-device scoping are separated.
- ZNE-581 — no obvious per-service Configure service action. Released in `0.1.98`; Home Assistant's native per-service row actions are visible on the live Zero Net Export integration detail page.
- ZNE-582 — no obvious per-service Add Managed Devices action. Released in `0.1.98`; Home Assistant's native per-service row actions and top-level Add Managed Devices action are visible on the live Zero Net Export integration detail page.

## Active feature scope
- ZNE-FR-001 — managed-device settings should reopen first-provisioned settings. Supported device-detail cog/deep-link path is live-validated; exact native-row gear remains upstream-blocked.
- ZNE-FR-002 — controller identity must be plan-specific. Live-validated fixed.
- ZNE-FR-003 — controller config must be isolated per plan. Read-only live evidence plus focused repo coverage now confirms distinct Summer/Winter config entries and selected-entry source binding saves; optional live reversible write-path proof still requires approval if Riley wants closure at live-write level.
- ZNE-FR-004 — managed devices must be isolated per plan. Live-validated fixed for Winter/Summer managed-device scoping.
- ZNE-FR-005 — controller runtime/brain state must be isolated per plan. Read-only live evidence plus focused repo coverage now confirms entry-id-scoped runtime stores with separate daily metric device keys; optional live runtime mutation proof still requires approval if Riley wants closure at live-write level.
- ZNE-FR-006 — multi-plan validation evidence. Live-validated for controller identity and managed-device assignment.

## Validation evidence
- ZNE-584: repo validation passed with focused copy tests `python3 -m unittest -q tests.test_setup_notice_copy tests.test_repairs_copy tests.test_translation_sync tests.test_bug_tracker_ids` (10 tests OK), full test discovery `python3 -m unittest discover -s tests` (600 tests OK), and `git diff --check`. Follow-up duplication guard committed as `8c4b4b7` and revalidated with the same focused/full test suite plus `git diff --check`. Live validation deployed the repo build, fingerprint-matched it (`overall_match=true`), restarted HA with API recovery after 22s, and captured browser proof `bug-evidence/zne-584-final-live-repair-detail.png` / `.json` showing action-first repair copy and fallback guidance present once.
- ZNE-583: previous validation is superseded by Riley's 2026-05-01 screenshot. It proved the validation was incomplete: it checked DOM text after clicking `Reconfigure` but did not assert the raw Home Assistant config-flow identity. Regression coverage now asserts the reconfigure wrapper preserves non-null `flow_id` and `handler` while keeping the first step id as `reconfigure` and the submit transition as `configure_service_sources`. Release `0.1.100` validation passed: repo py_compile/focused tests/full discovery (600 tests OK)/`git diff --check`; GitHub release `v0.1.100`; HACS install to `v0.1.100`; install fingerprint `overall_match=true`; Home Assistant API recovery after restart; installed-version sensor `0.1.100`; Slave browser service-row `Reconfigure` proof has grid sensor choices and `invalidFlowCount=0`. Evidence: `validation/0.1.100-release-validation.md`, `bug-evidence/zne-583-0.1.100-slave-reconfigure.txt`, `bug-evidence/zne-583-0.1.100-update-state.json`.
- ZNE-578: focused tests passed and live Home Assistant proof captured for the supported device-detail cog/deep-link path.
- ZNE-579: focused config-flow tests passed; live Home Assistant add-service validation succeeded without `already_configured` and cleanup was completed.
- ZNE-580: focused multi-entry tests passed; live Home Assistant screenshots and registry evidence show separate Summer/Winter rows with Coffee machine scoped to Winter only.
- ZNE-581/ZNE-582: repo implementation committed as `32796d8 Add per-service HA entry actions`; release validation passed with `python3 -m py_compile custom_components/zero_net_export/config_flow.py`, `python3 -m unittest discover -s tests` (599 tests OK), HACS install fingerprint match, Home Assistant restart, entity-state checks, logs scan, and live browser screenshot.
- Release `0.1.98`: GitHub release `v0.1.98` published from commit `4140c1d930fcc6370ec99c108b424042574a0c42`; HACS installed `v0.1.98`; Home Assistant restarted and reported `sensor.zero_net_export_installed_version = 0.1.98`, `sensor.zero_net_export_previous_installed_version = 0.1.97`, and `update.zero_net_export_update` installed/latest `v0.1.98`.
- Release `0.1.99`: GitHub release `v0.1.99` published; HACS repository refresh succeeded; HACS installed `v0.1.99`; install fingerprint matched (`overall_match=true`); Home Assistant restarted and reported `update.zero_net_export_update` installed/latest `v0.1.99`, `sensor.zero_net_export_installed_version = 0.1.99`, `sensor.zero_net_export_previous_installed_version = 0.1.98`; Winter Plan and Summer Plan config entries are `loaded`; 136 Zero Net Export entities are present.
- Release `0.1.100`: GitHub release `v0.1.100` published from release commit `9c14f39`; HACS installed `v0.1.100`; install fingerprint matched (`overall_match=true`); Home Assistant restarted and reported `update.zero_net_export_update` installed/latest `v0.1.100`, `sensor.zero_net_export_installed_version = 0.1.100`, and `sensor.zero_net_export_previous_installed_version = 0.1.99`; Slave browser validation confirmed the service-row `Reconfigure` dialog opens without `Invalid flow specified`.
- ZNE-FR-003/ZNE-FR-005 validation: `validation/zne-fr-003-005-multi-plan-validation.md` records live read-only storage/API evidence plus focused repo coverage. Summer and Winter have distinct config entry ids, `runtime_store_per_entry=true`, `runtime_store_keys_are_entry_scoped=true`, Winter runtime daily metric device key `7th_test_light`, and Summer runtime daily metric device key `7th_test_list`. New focused tests prove Configure service source binding saves update/reload only the selected entry and coordinator runtime stores are keyed by config entry id. Validation passed with focused tests (95 OK), full discovery (602 OK), and `git diff --check`. Optional live reversible write validation still requires approval.
- Release validation records: `validation/0.1.98-release-validation.md`, `validation/0.1.99-release-validation.md`, `validation/0.1.100-release-validation.md`.
- Browser evidence: `bug-evidence/zne-0.1.98-live-integrations.png`.

## Blockers / approvals
- Exact native managed-row gear placement for ZNE-578 requires an upstream Home Assistant frontend feature request/PR if Riley still wants that exact UI location.
- Runtime control remains blocked in the validation Home Assistant instance until required source roles are configured; this is expected and not a release-install failure.

## Next best action
Ask Riley whether the read-only live evidence plus focused repo write-path/runtime-store tests are sufficient to close ZNE-FR-003/ZNE-FR-005, or whether to proceed with an explicitly approved minimal reversible live write-path validation.
