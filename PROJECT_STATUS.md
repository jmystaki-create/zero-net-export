# project_status.md

project_name: zero-net-export
status: active
last_modified: 2026-07-08

## Current Focus

**Milestone 7: Multi-Plan And Service Separation** (status: `released_live_validated_api_static`, target: `v0.4.0`)
- Workboard card: `ZNE: Milestone 7 Multi-Plan And Service Separation`
- Feasibility: ACCEPTED (see `validation/zne-app-milestone-7-multi-plan-feasibility.md`)
- Implementation plan: defined (see `docs/ZNE_APP_MILESTONE_7_PLAN.md`)
- Implementation validation: passed (see `validation/zne-app-milestone-7-implementation.md`)
- Release/live validation: passed for API/static/service scope (see `validation/0.4.0-release-validation.md`)
- User outcome: operators can see and act within an explicit selected plan/service context, preventing cross-plan confusion as Zero Net Export grows beyond one plan.
- Implemented: shared entry resolver, app selected-plan context header/selector, selected `entry_id` payloads for source-role saves, managed-device changes, executor pause/resume, diagnostics export, and repair. Ambiguous multi-entry service calls now fail safely.
- Release: v0.4.0 published, installed through HACS, restarted, and live validated with Home Assistant API/static route checks. Browser proof is pending because the OpenClaw managed browser host is unavailable.
- Follow-up risk: post-release logs show many Zero Net Export entity attributes exceeding Home Assistant's 16 KB recorder attribute limit. A separate user-visible Sources app SOC display regression was fixed and live-validated as ZNE-596 in `v0.4.1`; return to the broader recorder attribute cleanup next.
- New user-requested Overview console polish: `ZNE-FR-011` and `ZNE-FR-012` are released/live validated in `v0.4.2`. The Overview Reconciliation Status card now shows local freshness, Source Power, Battery Power, Confidence, and stale/source-blocker context. Evidence: `validation/zne-fr-011-012-overview-console-live-metrics.md`, `validation/0.4.2-release-validation.md`, and `validation/artifacts/v0.4.2-overview-console-live.png`.

**Milestone 6: Diagnostics & Support Polish** (status: `released_live_validated`, target: `v0.3.3`)
- Workboard card: `zne-app-006`
- Feasibility: ACCEPTED (see `docs/MILESTONE_6_DIAGNOSTICS_SUPPORT_FEASIBILITY.md`)
- Implementation plan: defined (see `docs/MILESTONE_6_IMPLEMENTATION_PLAN.md`)
- Release: v0.3.3 published and installed via HACS (2026-07-07), superseding v0.3.1-fix
- Live validation: HACS repository page showed Zero Net Export downloaded at `v0.3.3`; Home Assistant app opened; header showed `Version 0.3.3 - 1 plan`; backend status showed connected; Diagnostics tab rendered; `zero_net_export.export_diagnostics` and `zero_net_export.repair_issue` were registered and returned successfully through the Home Assistant REST API; `export_diagnostics` created `/config/zne-diagnostics-20260707-192929.json`; installed version sensor shows `0.3.3`.
- Runtime note: current `sensor.zero_net_export_status` is `degraded` because power sources do not reconcile cleanly; this is product/runtime state, not a Milestone 6 service failure.

**Milestone 5: Runtime Visibility & Manual Override** - **COMPLETED** (v0.3.0)
- Released: v0.3.0 (GitHub Release, HACS validated)
- Validation: `validation/milestone-5-runtime-visibility-validation.md`
- Features: `executor_state` sensor, `pause_executor`/`resume_executor` services, Reconciliation card, Pause/Resume buttons

---

Project direction changed on 2026-06-26: Zero Net Export is now a Home Assistant application backed by the existing integration backend. The old native-device-page-led direction is superseded because validation showed Home Assistant's native device/config-entry/button surfaces cannot carry the full Zero Net Export product scope. Current steering lives in `CONSTRAINTS.md` and `docs/ZNE_APPLICATION_DIRECTION.md`.

The immediate work is release readiness for the Home Assistant application path. Riley answered the initial application direction questions on 2026-06-26: sidebar by default, app name `Zero Net Export`, editable first release, multi-plan/service support from day one, conservative frontend stack default, core workflow coverage, strong destructive-action confirmation, keep Lovelace examples, HACS-only frontend delivery, and minimum Home Assistant version `2026.6.4+` based on the live validation target. Riley then approved the GitHub/HACS-only release pathway and `0.2.0` version on 2026-06-26. Milestone 1 is planned in `docs/ZNE_APP_MILESTONE_1_PLAN.md` with feasibility recorded in `validation/zne-app-milestone-1-feasibility.md`. Home Assistant `2026.6.4` source/live proof supports the app implementation path: serve frontend assets with `StaticPathConfig` / `hass.http.async_register_static_paths(...)`, then register the sidebar app with `panel_custom.async_register_panel(...)`. Releases `0.2.0` and `0.2.1` were published through the approved GitHub/HACS path and live-validated. Corrective `0.2.2` is now published as GitHub Release `v0.2.2` from commit `9c3f886`; HACS downloaded `v0.2.2`, Home Assistant restarted, install fingerprint matched before and after restart, `sensor.zero_net_export_installed_version=0.2.2`, `update.zero_net_export_update` reports installed/latest `v0.2.2`, app/static routes return HTTP 200, and no targeted Zero Net Export log errors/warnings were found. Live validation added a temporary disabled `light.7th` managed record through the supported HA subentry flow, captured desktop/narrow Managed Devices formatting proof with `any_overlap=false`, removed the record through the installed app `REMOVE FROM ZNE` confirmation path, and confirmed `sensor.zero_net_export_managed_devices_count=0`, no `7th_validation_load` entities remain, and original `light.7th` remains present/off. Evidence: `validation/0.2.0-release-validation.md`, `validation/0.2.1-release-validation.md`, `validation/0.2.2-release-validation.md`, `validation/artifacts/zne-0.2.2-managed-devices-desktop.png`, `validation/artifacts/zne-0.2.2-managed-devices-narrow.png`, and `validation/artifacts/zne-0.2.2-managed-devices-remove-after.png`. The existing backend/control engine remains the foundation: config entries, coordinator/runtime state, source validation, planner/executor logic, managed-device model, entities, services/actions, repairs, notifications, diagnostics, and install validation helpers.

A repo-tracked Workboard now exists in `docs/workboard/README.md` with eight initial cards under `docs/workboard/cards/`: project charter, architecture inventory, bug register, MVP definition, next 10 implementation tasks, blockers and unknowns, testing and validation plan, and weekly status report. The OpenClaw Workboard UI is also populated on board `main` with the same operating cards plus focused cards for completed Sources, Milestone 3, Milestone 4, Milestone 5, and Milestone 6 work. Treat the OpenClaw Workboard as wired into the Zero Net Export project: every ZNE work turn must check and update relevant Workboard state when project state, validation state, blockers, next actions, or release readiness change. If the current Workboard CLI cannot edit an existing card, create a focused card when needed and keep repo Workboard docs aligned.

Native Home Assistant surfaces are now supporting/fallback surfaces. The primary operator workflow should move into a Zero Net Export-owned Home Assistant application/panel covering overview, sources, managed devices, controls, runtime, diagnostics, support, and multi-plan/service separation. Riley approved starting the next milestone on 2026-06-30, then accepted `ZNE-APP-002` for implementation. `ZNE-APP-002` is documented as the app-native Sources workflow milestone with acceptance criteria in `docs/ZNE_APP_MILESTONE_2_SOURCES_PLAN.md`, feasibility in `validation/zne-app-milestone-2-sources-feasibility.md`, and repo validation in `validation/zne-app-milestone-2-sources-implementation.md`. Release `0.2.3` is now published as GitHub Release `v0.2.3` from commit `d619a00`, installed through HACS, restarted, fingerprint-matched before and after restart, route/static/state/log checked, and HACS metadata reports installed/latest `v0.2.3`. Reversible source-role write proof is live-validated through the supported `zero_net_export.update_source_roles` service using optional `battery_soc_entity`; it was restored to unset. Browser screenshot proof for the installed Sources workflow was captured on installed `0.2.4` with desktop/narrow artifacts. Evidence: `validation/0.2.3-release-validation.md`, `validation/artifacts/zne-0.2.4-sources-desktop.png`, `validation/artifacts/zne-0.2.4-sources-narrow.png`.

Corrective release `0.2.4` is now published as GitHub Release `v0.2.4` from commit `63c2568`, installed through HACS, restarted, fingerprint-matched before and after restart, route/static/state/log checked, and HACS metadata reports installed/latest `v0.2.4`. ZNE-594 is released/live-validated: post-restart state proof shows `sensor.zero_net_export_source_blocker_next_step` length `156` and `sensor.zero_net_export_command_center_next_step` length `147`, and the post-restart log scan found `0` Zero Net Export next-step state length errors. Evidence: `validation/0.2.4-release-validation.md`.

Release `v0.2.5` delivered ZNE-APP-003 (Milestone 3) with managed device fleet controls. Release `v0.2.9` delivered ZNE-APP-004 (Milestone 4) with source health and runtime blocker resolution. Release `v0.3.0` delivered ZNE-APP-005 (Milestone 5) with runtime visibility and manual override.

Previous release state remains relevant but is no longer the primary roadmap: ZNE-FR-009/ZNE-FR-010 are release-prepped as `0.1.110` but the public GitHub Release object is not published; `v0.3.0` is now the latest visible GitHub Release. Future release work should not continue polishing native device-page UX unless it directly supports the application port.

Rejected Tier 1 mockup `d9a0fd1` must not be used. The native guided Tier 2 workflow is superseded by the application direction.

## Active Bugs

- ZNE-596 — Sources app shows Battery state of charge as missing despite valid backend binding. Status: repo_validated/released_live_validated in `v0.4.1`. Evidence: `docs/BUGS.md`, `validation/zne-596-soc-source-status-display.md`, `validation/0.4.1-release-validation.md`.
- ZNE-595 — recorder-backed entity attributes exceed Home Assistant's 16 KB limit. Status: open/high. Evidence: `docs/BUGS.md`, `validation/0.4.0-release-validation.md`. Next action: trim large source/action-history/diagnostic details from recorder-backed attributes and keep bulky detail in diagnostics/app API surfaces.
- ZNE-594 — next-step sensors can exceed Home Assistant's 255-character state limit. Status: released_live_validated in `0.2.4`. Evidence: `docs/BUGS.md`, `validation/zne-594-state-length-implementation.md`, `validation/0.2.4-release-validation.md`.
- ZNE-593 — Managed Devices app summary formatting is broken. Status: validated in installed `0.2.2`. Evidence: `validation/0.2.2-release-validation.md`, `validation/artifacts/zne-593-managed-devices-formatting-broken-v0.2.1.png`, `validation/artifacts/zne-0.2.2-managed-devices-desktop.png`, `validation/artifacts/zne-0.2.2-managed-devices-narrow.png`.
- ZNE-592 — managed-load edit/remove button rows open unhelpful more-info dialogs. Status: live_validated_fixed in `0.1.109`. Evidence: `validation/zne-592-clickthrough-workflow-audit.md`, `validation/zne-592-native-clickthrough-feasibility.md`, `validation/0.1.109-release-validation.md`, `docs/BUGS.md`.
- ZNE-591 — managed-load device overflow lacks configure/delete actions. Status: released_live_validated in `0.1.108`. Evidence: `docs/BUGS.md`, `validation/zne-591-managed-device-edit-remove-actions.md`, `validation/0.1.108-release-validation.md`.
- ZNE-590 — managed climate device ZNE settings are confusing and do not preserve the original device experience. Status: released_live_validated in `0.1.107`. Evidence: `docs/BUGS.md`, `validation/zne-590-managed-climate-device-page-cleanup.md`, `validation/0.1.107-release-validation.md`.
- ZNE-589 — remove `ZNE Managed Devices` from the Home Assistant sidebar/menu. Status: released_live_validated in `0.1.106`. Evidence: `validation/zne-589-sidebar-menu-panel-removal.md`, `validation/0.1.106-release-validation.md`.
- ZNE-588 — Tier 1 setup buttons do not open visible Tier 2 targets and diagnostics overfill the device page. Status: released_live_validated in `0.1.106`. Evidence: `validation/zne-588-bug-only-tier1-cleanup.md`, `validation/0.1.106-release-validation.md`.

## Active Feature Work

- ZNE-FR-011 — Reconciliation Status should feel realtime. Status: released_live_validated in `v0.4.2`. Evidence: `docs/FEATURE_REQUESTS.md`, `validation/zne-fr-011-012-overview-console-live-metrics.md`, `validation/0.4.2-release-validation.md`.
- ZNE-FR-012 — Overview console should include Source Power, Battery Power, and Confidence. Status: released_live_validated in `v0.4.2`. Evidence: `docs/FEATURE_REQUESTS.md`, `validation/zne-fr-011-012-overview-console-live-metrics.md`, `validation/0.4.2-release-validation.md`.
