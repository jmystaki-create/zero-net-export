# project_status.md

project_name: zero-net-export
status: active
last_modified: 2026-04-30 20:02

## Current focus
ZNE-584 is the active copy/UX bug: the setup warning is too wordy and unclear. Repo copy simplification and automated validation are complete alongside the already-fixed-pending-live-validation ZNE-583 Reconfigure regression; live deploy/restart/browser validation remains approval-gated.

## Active bugs
- ZNE-584 — setup warning is too wordy and unclear. User screenshot confirms the copy needs a radical simplification; repo fix is validated to make the warning action-first: impact, do this first, missing items, useful paths, fallback only if needed. Status: fixed pending approved live validation.
- ZNE-583 — service-row `Reconfigure` opens with `Invalid flow specified`. User screenshot confirms the regression in `0.1.98`; repo fix is validated to keep the initial HA reconfigure step id as `reconfigure` while still advancing to the selected service's Configure service source-binding flow. Status: fixed pending approved live validation.
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
- ZNE-584: repo validation passed with focused copy tests `python3 -m unittest -q tests.test_setup_notice_copy tests.test_repairs_copy tests.test_translation_sync tests.test_bug_tracker_ids` (10 tests OK), full test discovery `python3 -m unittest discover -s tests` (600 tests OK), and `git diff --check`.
- ZNE-583: repo validation passed with `python3 -m py_compile custom_components/zero_net_export/config_flow.py`, focused regression tests `python3 -m unittest -q tests.test_config_flow_device_runtime_overlay tests.test_translation_sync tests.test_bug_tracker_ids` (91 tests OK), full test discovery `python3 -m unittest discover -s tests` (600 tests OK), and `git diff --check`.
- ZNE-578: focused tests passed and live Home Assistant proof captured for the supported device-detail cog/deep-link path.
- ZNE-579: focused config-flow tests passed; live Home Assistant add-service validation succeeded without `already_configured` and cleanup was completed.
- ZNE-580: focused multi-entry tests passed; live Home Assistant screenshots and registry evidence show separate Summer/Winter rows with Coffee machine scoped to Winter only.
- ZNE-581/ZNE-582: repo implementation committed as `32796d8 Add per-service HA entry actions`; release validation passed with `python3 -m py_compile custom_components/zero_net_export/config_flow.py`, `python3 -m unittest discover -s tests` (599 tests OK), HACS install fingerprint match, Home Assistant restart, entity-state checks, logs scan, and live browser screenshot.
- Release `0.1.98`: GitHub release `v0.1.98` published from commit `4140c1d930fcc6370ec99c108b424042574a0c42`; HACS installed `v0.1.98`; Home Assistant restarted and reported `sensor.zero_net_export_installed_version = 0.1.98`, `sensor.zero_net_export_previous_installed_version = 0.1.97`, and `update.zero_net_export_update` installed/latest `v0.1.98`.
- Release validation record: `validation/0.1.98-release-validation.md`.
- Browser evidence: `bug-evidence/zne-0.1.98-live-integrations.png`.

## Blockers / approvals
- ZNE-583 blocks treating the live `0.1.98` service-row Reconfigure path as healthy until approved live validation passes.
- Do not deploy, restart Home Assistant, tag, publish, or claim future release readiness without explicit approval and evidence.
- Exact native managed-row gear placement for ZNE-578 requires an upstream Home Assistant frontend feature request/PR if Riley still wants that exact UI location.
- Runtime control remains blocked in the validation Home Assistant instance until required source roles are configured; this is expected and not a release-install failure.

## Next best action
Ask Riley for approval before deploying/restarting Home Assistant for combined ZNE-583/ZNE-584 live validation. If approved, install the repo build, restart HA, and capture browser proof that Reconfigure has no invalid-flow banner and the setup warning is concise/action-first.
