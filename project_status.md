# project_status.md

project_name: zero-net-export
status: active
last_modified: 2026-04-30 19:35

## Current focus
Reset to today's active Riley-reported Zero Net Export work only. Older release-plan/UI-map history is intentionally cleared from this status document.

## Active bugs
- ZNE-578 — native managed-row gear beside the pencil is not supported by current Home Assistant frontend. Closest supported path is implemented and live-validated: managed child-device `configuration_url` opens the Home Assistant device-detail cog/deep-link into the `ZNE Managed Devices` editor. Exact native-row placement requires upstream HA frontend work if still required.
- ZNE-579 — Add service wrongly aborted as `already_configured`. Fixed and live-validated; unique ids are now scoped to the submitted service/system name.
- ZNE-580 — multiple services looked like duplicated generic controllers. Fixed and live-validated; Summer/Winter plan controller rows and managed-device scoping are separated.
- ZNE-581 — no obvious per-service Configure service action. Implemented pending live validation; Home Assistant's native `Reconfigure` overflow opens the selected-entry `Configure service` flow.
- ZNE-582 — no obvious per-service Add Managed Devices action. Implemented pending live validation; Home Assistant config-subentry overflow exposes `Add Managed Devices` for the selected service/config entry.

## Active feature scope
- ZNE-FR-001 — managed-device settings should reopen first-provisioned settings. Supported device-detail cog/deep-link path is live-validated; exact native-row gear remains upstream-blocked.
- ZNE-FR-002 — controller identity must be plan-specific. Live-validated fixed.
- ZNE-FR-003 — controller config must be isolated per plan. Tracked; needs validation through the per-service Configure service flow.
- ZNE-FR-004 — managed devices must be isolated per plan. Live-validated fixed for Winter/Summer managed-device scoping.
- ZNE-FR-005 — controller runtime/brain state must be isolated per plan. Tracked pending validation.
- ZNE-FR-006 — multi-plan validation evidence. Live-validated for controller identity and managed-device assignment.

## Validation evidence
- ZNE-578: focused tests passed and live Home Assistant proof captured for the supported device-detail cog/deep-link path.
- ZNE-579: focused config-flow tests passed; live Home Assistant add-service validation succeeded without `already_configured` and cleanup was completed.
- ZNE-580: focused multi-entry tests passed; live Home Assistant screenshots and registry evidence show separate Summer/Winter rows with Coffee machine scoped to Winter only.
- ZNE-581/ZNE-582: repo implementation committed as `32796d8 Add per-service HA entry actions`; validation reported passing with `python3 -m py_compile custom_components/zero_net_export/config_flow.py` and `python3 -m unittest discover -s tests` (599 tests OK). Live Home Assistant screenshot/release validation remains approval-gated.

## Blockers / approvals
- Do not deploy, restart Home Assistant, tag, publish, or claim release readiness without explicit approval.
- Release metadata/changelog/tag changes require explicit approval. Recommended next candidate version: `0.1.98`.
- Exact native managed-row gear placement for ZNE-578 requires an upstream Home Assistant frontend feature request/PR if Riley still wants that exact UI location.

## Next best action
Ask Riley to approve preparing the `0.1.98` release metadata/changelog/tag for today's validated fixes and implemented per-service actions. After approval: bump version metadata, rerun validation, stage/commit, then request separate formal release execution approval per `RELEASE_MANAGEMENT.md`.
