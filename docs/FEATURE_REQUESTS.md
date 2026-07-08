# Zero Net Export Feature Requests

This file tracks user-requested product enhancements separately from confirmed bugs.

## ZNE-APP-001 - Home Assistant application port

- **status:** `0.2.1_released_live_validated_with_managed_remove_gap`
- **area:** `application / frontend / architecture`
- **requested by:** Riley, 2026-06-26
- **request:** Port Zero Net Export from a Home Assistant "device" implementation into a Home Assistant application that captures the full Zero Net Export scope.
- **acceptance target:** Zero Net Export has a Home Assistant-hosted application/panel as the primary operator experience, backed by the existing integration backend. The app covers overview/readiness, source mapping, managed devices, controls, runtime visibility, diagnostics/support, install validation, and multi-plan/service separation. Native device/config-entry/entity surfaces remain supporting/fallback/automation surfaces.
- **target-environment result:** Feasible. Home Assistant supports panels as full-screen sidebar-linked pages with JavaScript `hass` access, and custom panels can be registered. Repo evidence shows native device/config-entry surfaces cannot carry the full scope without misleading or unsupported UI behavior. Evidence: `validation/zne-application-feasibility.md`.
- **documentation update:** `CONSTRAINTS.md`, `PROJECT_STATUS.md`, `README.md`, `docs/ZNE_APPLICATION_DIRECTION.md`, `docs/ACTIVE_USER_REQUESTS.md`, `docs/SUPERVISOR.md`, `docs/WATCHDOG.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/NATIVE_OPERATOR_PLAN.md`, `docs/NATIVE_SURFACE_TECHNICAL_DIRECTION.md`, and `docs/OPERATOR_SURFACES_UX.md`.
- **product decisions:** sidebar by default; app name `Zero Net Export`; first release should include editable workflows; multi-plan/service support from day one; use a conservative vanilla/Lit-style frontend default unless feasibility proves otherwise; first acceptance path should cover core app workflows; destructive actions need strong confirmation; keep optional Lovelace examples; HACS-only frontend delivery is acceptable; minimum Home Assistant version is `2026.6.4+`.
- **milestone 1 plan:** `docs/ZNE_APP_MILESTONE_1_PLAN.md`; milestone feasibility: `validation/zne-app-milestone-1-feasibility.md`.
- **implementation status:** `0.2.0` is repo-validated, published as a GitHub Release, and installed in the live Home Assistant validation target with matching install fingerprint, HTTP 200 static/app shell route checks, clean targeted log review, and desktop/narrow screenshot-grade sidebar/browser proof. The second workflow slice is released as `v0.2.1` through GitHub and HACS only: HACS installed the release, Home Assistant restarted, install fingerprint matched before/after restart, app/static routes returned HTTP 200, desktop/narrow browser proof showed the `0.2.1` app shell, and a reversible `switch.zero_net_export_enabled` write/restore proof passed. Managed-device strong-confirmation removal remains pending because the live validation instance currently has zero managed devices and no disposable managed load to remove. Evidence: `validation/0.2.0-release-validation.md`, `validation/0.2.1-release-validation.md`, `validation/artifacts/zne-0.2.0-app-desktop.png`, `validation/artifacts/zne-0.2.0-app-narrow.png`, `validation/artifacts/zne-0.2.1-app-desktop.png`, `validation/artifacts/zne-0.2.1-app-narrow.png`, `validation/zne-app-milestone-1-stage-2.md`.

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

- **status:** `repo_validated_pending_live_release_validation`
- **area:** `managed_devices / native_integration_page`
- **requested by:** Riley, 2026-05-06
- **request:** On the Zero Net Export integration page, each managed-load row three-dot menu should expose a `Delete device` action. Pressing it should immediately remove that managed device from the owning Zero Net Export service/plan.
- **source screenshot:** `/root/.openclaw/media/inbound/image---e2ac28c5-bc32-4ac8-b564-06a4232cdd9a.png` shows the current native row overflow menu for `Managed Devices — 7th test list` with only `20 entities` and `Disable device`.
- **acceptance target:** the selected managed-load row overflow exposes a clear delete/remove action; activating it removes only that selected managed-load record from the owning service/plan; the original Home Assistant device/entity remains intact; stale ZNE entities/device rows are removed after reload; tests and live browser proof validate the path.
- **target-environment result:** Home Assistant frontend/source feasibility in `validation/zne-fr-009-010-ha-design-guideline-feasibility.md` found the exact native row-overflow `Delete` placement is supported when the integration exposes HA's native `async_remove_config_entry_device` / `supports_remove_device` backend path. No frontend injection is needed or approved.
- **implementation:** repo implementation adds `async_remove_config_entry_device` so Home Assistant can expose native `supports_remove_device` for ZNE managed-load child devices. The hook removes only the selected managed-device inventory payload from the owning ZNE entry, reloads that entry, and leaves the original/source HA device/entity untouched.
- **validation:** repo validation passed focused tests (`Ran 97 tests`, OK), full discovery (`Ran 610 tests`, OK), `py_compile` for changed component files, and `git diff --check`. Evidence: `validation/zne-fr-009-010-native-implementation.md`. Live HA/browser proof remains pending release approval.

## ZNE-FR-010 - Managed-load configuration card with editable captured settings

- **status:** `repo_validated_pending_live_release_validation`
- **area:** `managed_devices / native_device_page / configuration_surface`
- **requested by:** Riley, 2026-05-06
- **request:** Add a configuration card for a managed-load device that shows all settings captured when the device was added. Next to each label, show a field/control that lets the operator modify the relevant configuration value for that setting.
- **source screenshot:** `/root/.openclaw/media/inbound/image---79d3e841-74de-4b05-8966-25c7c7eb37db.png` marks the intended configuration-card area on the managed-load device page.
- **acceptance target:** the managed-load configuration surface lists the add-time captured settings with clear labels; each editable setting has an adjacent field/control; saving updates only the selected managed device in the owning service/plan; read-only settings are clearly read-only; invalid values show validation feedback; the original Home Assistant device/entity remains untouched.
- **target-environment result:** Home Assistant frontend/source feasibility in `validation/zne-fr-009-010-ha-design-guideline-feasibility.md` found the user outcome fits HA guidelines through native config subentry reconfigure/options/config-entity surfaces, but arbitrary custom card insertion into the native device page is not supported without custom/upstream frontend work. Recommended path: native managed-device subentry reconfigure flow, optionally linked by `configuration_url`, with config entities only for high-value live-tweak settings.
- **implementation:** repo implementation adds a managed-device subentry reconfigure flow that uses native Home Assistant forms to pick an existing managed load and edit the captured add-time settings. Saving updates only the selected managed-device payload in the owning entry options and reloads that entry.
- **validation:** repo validation passed focused tests (`Ran 97 tests`, OK), full discovery (`Ran 610 tests`, OK), `py_compile` for changed component files, and `git diff --check`. Evidence: `validation/zne-fr-009-010-native-implementation.md`. Live HA/browser proof remains pending release approval.

## ZNE-FR-011 - Reconciliation status should feel realtime

- **status:** `released_live_validated_in_v0.4.2`
- **area:** `application / overview / runtime_visibility`
- **requested by:** Riley, 2026-07-08
- **request:** The Overview reconciliation status should update more realtime so the operator can watch the controller state change without the console feeling stale.
- **source screenshot:** Riley's 2026-07-08 Overview screenshot shows the Reconciliation Status card with static-looking readings while the app header reports `Version 0.4.1 - 1 plan`.
- **user outcome:** the Overview console should feel alive: reconciliation readings should refresh predictably, show when they were last updated, and make stale or unavailable data obvious.
- **acceptance target:** the Reconciliation Status card refreshes from the selected plan/service runtime data at a clearly defined cadence; it shows a last-updated/freshness indicator; stale values are visually distinct from live values; refresh behavior does not create excessive Home Assistant API load; desktop and narrow browser validation prove the card updates after backend state changes.
- **target-environment result:** supported for repo implementation through the existing Home Assistant custom-panel `hass` state path plus local re-rendering for freshness text. No new API polling endpoint or Home Assistant frontend patch is required. Evidence: `validation/zne-fr-011-012-overview-console-live-metrics.md`.
- **implementation status:** app frontend now refreshes the Overview card locally every 10 seconds, resolves realtime rows against current ZNE entity state, and shows last-update/stale/source-blocker context. Released and live-validated in `v0.4.2`.
- **release validation:** `validation/0.4.2-release-validation.md` confirms GitHub release, HACS install, Home Assistant restart, install fingerprint match, installed version sensor `0.4.2`, and browser proof showing live freshness plus stale/source-blocker context.
- **validation plan:** repo tests for the selected-plan runtime payload and frontend rendering; live Home Assistant proof that reconciliation values update after runtime/source changes; browser screenshot or trace evidence showing freshness state; targeted log review for API errors.

## ZNE-FR-012 - Overview console should include source power, battery power, and confidence

- **status:** `released_live_validated_in_v0.4.2`
- **area:** `application / overview / reconciliation_status`
- **requested by:** Riley, 2026-07-08
- **request:** Source Power, Battery Power, and Confidence are missing or unhelpful in the Overview Reconciliation Status card; the console should come alive with meaningful runtime signals.
- **source screenshot:** Riley's 2026-07-08 Overview screenshot shows `Source Power` and `Battery Power` with unit-only/missing values and `Confidence` as `unknown`.
- **user outcome:** operators should be able to understand the controller's current power picture and trust level from the Overview card without switching tabs.
- **acceptance target:** Source Power, Battery Power, and Confidence display populated values when the selected plan has valid source bindings and readings; missing/unavailable values explain the blocker or source role causing the gap; confidence includes a meaningful state or score tied to reconciliation quality; Home Load, Surplus/Deficit, Reconciliation Error, and Executor State remain visible and selected-plan scoped.
- **target-environment result:** supported for repo implementation using existing recorder-safe entity states and source diagnostic attributes. The app can read `*_w` runtime sensors and per-source reading/status sensors already generated by the integration. No bulky new recorder-backed attributes are introduced. Evidence: `validation/zne-fr-011-012-overview-console-live-metrics.md`.
- **implementation status:** app frontend now maps Source Power to the solar/source power runtime reading, derives Battery Power from discharge minus charge where available, uses the real confidence sensor, and explains stale/missing source blockers. Released and live-validated in `v0.4.2`.
- **release validation:** `validation/0.4.2-release-validation.md` confirms the installed app shows Source Power, Battery Power, and Confidence with current live values and source context.
- **validation plan:** backend/API tests for source power, battery power, and confidence payloads; frontend rendering tests or static validation for populated and missing states; live Home Assistant proof on the installed app showing the three fields populated or explaining blockers; targeted log review.
