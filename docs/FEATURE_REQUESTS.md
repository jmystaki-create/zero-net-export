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

## ZNE-FR-013 - Overview Readiness should explain errors and resolution steps

- **status:** `released_live_validated_in_v0.4.3`
- **area:** `application / overview / readiness`
- **requested by:** Riley, 2026-07-08
- **request:** The Overview Readiness section is not clear and the formatting is poor. Structurally fix the formatting and explain the errors plus what needs to be done to resolve them.
- **user outcome:** operators can understand why the controller is not ready directly from Overview, without decoding long command-center strings.
- **acceptance target:** Readiness shows compact status chips, current focus, and separate issue cards with `What is wrong` and `How to resolve`; long text wraps cleanly on desktop and narrow screens; source blockers, reconciliation mismatch, controls readiness, and managed-device queue context are shown when present.
- **target-environment result:** supported in the existing ZNE-owned Home Assistant custom panel using current `hass.states` data. No Home Assistant frontend patch, native page injection, or new recorder-backed attributes are required. Evidence: `validation/zne-fr-013-overview-readiness-clarity.md`.
- **implementation status:** app frontend has a dedicated Readiness model and CSS layout. Released and live-validated in `v0.4.3`.
- **release validation:** `validation/0.4.3-release-validation.md` confirms GitHub release, HACS install, Home Assistant restart, install fingerprint match, installed version sensor `0.4.3`, and live browser proof that desktop/narrow layouts show `Current focus`, `What is wrong`, and `How to resolve`.
- **validation plan:** frontend syntax check, focused app tests, `git diff --check`, then HACS/restart/browser proof in the release path.

## ZNE-FR-014 - Overview Readiness should use plain action-oriented messages

- **status:** `released_live_validated_v0.4.5`
- **area:** `application / overview / readiness`
- **requested by:** Riley, 2026-07-08
- **request:** The v0.4.3 Readiness section is still poor and hard to understand; review the design and messages.
- **user outcome:** operators see a short readiness verdict, the first action to take, and concise issue facts instead of raw command-center text or long right-aligned setup strings.
- **acceptance target:** Readiness does not render raw command-center/device queue strings as label/value rows; it converts source and managed-device state into compact issue facts and ordered actions; narrow cards remain readable without clipped or right-aligned paragraphs.
- **target-environment result:** supported in the existing ZNE-owned Home Assistant custom panel using current `hass.states` data and CSS only. No Home Assistant frontend patch, native page injection, direct live install write, or new recorder-backed attributes are required. Evidence: `validation/zne-fr-014-readiness-message-design.md`.
- **implementation status:** app frontend shows a summary verdict, `Do this first`, plain issue titles, and bullet/numbered guidance for source readings, reconciliation, controls, and managed-device queue work. Released in `v0.4.4`; corrective live validation of the Readiness behavior passed in `v0.4.5`.
- **validation result:** `validation/0.4.5-release-validation.md` confirms GitHub release, HACS install, Home Assistant restart/recovery, install fingerprint match, installed version sensor `0.4.5`, and browser proof that the Overview Readiness summary showed `Ready` with no blocking readiness issue.

## ZNE-FR-015 - Managed Devices Fleet Summary layout polish

- **status:** `released_live_validated_v0.4.9`
- **area:** `application / managed_devices / layout`
- **requested by:** Riley, 2026-07-13
- **request:** The Managed Devices Fleet Summary layout looks odd when `0 Stale` wraps underneath the other summary chips.
- **user outcome:** operators can scan total, enabled, disabled, blocked, and stale counts without cramped `0Stale` text or uneven ad hoc wrapping.
- **acceptance target:** Fleet Summary counts and labels have clear spacing; the status chips wrap in an even compact layout on desktop and narrow widths; existing counts remain unchanged.
- **target-environment result:** supported in the existing Zero Net Export Home Assistant custom panel with CSS/DOM changes only. No new Home Assistant API, frontend patch, or backend entity changes are required.
- **implementation status:** released in `v0.4.9`; the installed app uses a dedicated compact grid class for Fleet Summary stats and spacing between the numeric count and label. Evidence: `validation/zne-fr-015-016-managed-devices-layout-order.md`, `validation/0.4.9-release-validation.md`.
- **validation result:** released through GitHub/HACS, restarted, and live browser-validated on desktop and narrow viewport.

## ZNE-FR-016 - Managed Devices page should list unmanaged candidates after managed devices

- **status:** `released_live_validated_v0.4.9`
- **area:** `application / managed_devices / page_sequence`
- **requested by:** Riley, 2026-07-13
- **request:** Unmanaged Devices should come after Managed Devices in the page sequence.
- **user outcome:** the Managed Devices tab reads in priority order: managed fleet controls first, then unmanaged candidates to review/promote.
- **acceptance target:** the Fleet List section renders before the Unmanaged Candidate Queue; unmanaged candidate counts and rows remain visible and unchanged.
- **target-environment result:** supported in the existing Zero Net Export Home Assistant custom panel with DOM ordering only. No new Home Assistant API, frontend patch, or backend entity changes are required.
- **implementation status:** released in `v0.4.9`; the installed app renders the Unmanaged Candidate Queue below the Fleet List. Evidence: `validation/zne-fr-015-016-managed-devices-layout-order.md`, `validation/0.4.9-release-validation.md`.
- **validation result:** released through GitHub/HACS, restarted, and live browser-validated on desktop and narrow viewport.

## ZNE-FR-017 - Promote unmanaged candidates from Managed Devices

- **status:** `released_live_validated_v0.4.10`
- **area:** `application / managed_devices / promotion_workflow`
- **requested by:** Riley, 2026-07-13
- **request:** From the Managed Devices screen, promote a device from the Unmanaged Candidate Queue into the managed Fleet List, including the workflow that adds the Zero Net Export managed-device property in Home Assistant.
- **user outcome:** operators can review an unmanaged candidate, confirm its ZNE managed-load settings, save it into the selected plan, and then see it move from the unmanaged queue into the managed fleet without leaving the Managed Devices app.
- **acceptance target:** each eligible unmanaged candidate exposes a clear `Review & promote` action; promotion shows candidate fit, warnings, suggested template, and editable add-time settings; saving creates a validated managed-device inventory payload for the selected ZNE entry; duplicates and invalid candidates are blocked; the original Home Assistant device/entity is not modified; after reload the row appears in Fleet List and the unmanaged queue updates; Home Assistant shows the promoted load as a Zero Net Export managed child device with `via_device` and `configuration_url` metadata.
- **target-environment result:** supported through the existing ZNE-owned Home Assistant custom panel, backend services/options inventory, existing config-flow candidate/template logic, and existing managed-load child `device_info`. Unsupported: injecting a custom promote action into another integration's original Home Assistant device page, or mutating another integration's original device registry row. Evidence and plan: `validation/zne-fr-017-managed-candidate-promotion.md`.
- **implementation status:** repo implementation adds `zero_net_export.promote_managed_device`, validates the live surfaced candidate server-side, rejects duplicates/invalid settings, writes selected-entry `CONF_DEVICE_INVENTORY_JSON`, reloads the entry, and leaves the original Home Assistant device/entity untouched. The Managed Devices app now adds `Review & promote`, a confirmation/settings panel, and service-call submission from the Unmanaged Candidate Queue.
- **validation result:** released in `v0.4.10` through GitHub/HACS, installed in Home Assistant, restarted, fingerprint matched, and Slave-browser validated. Live proof promoted `switch.ac_outlet_1` into a disabled ZNE managed record, verified it left the unmanaged queue, removed the validation record with `confirm:true`, and confirmed the original HA entity remained present and returned to the unmanaged queue. Repo validation passed `node --check`, Python compile for changed backend, focused Managed Devices tests, focused candidate/device tests, full discovery (`637` tests), and `git diff --check`. Evidence: `validation/zne-fr-017-managed-candidate-promotion.md`, `validation/0.4.10-release-validation.md`.

## ZNE-FR-018 - Managed Devices Fleet List on/off traffic light

- **status:** `released_live_validated`
- **area:** `application / managed_devices / runtime_visibility`
- **requested by:** Riley, 2026-07-17
- **request:** In the Managed Devices Fleet List, each item should show whether the device is currently on or off using a green/red traffic-light indicator.
- **user outcome:** operators can scan the managed fleet and immediately see which managed loads are currently active without opening a detail view or decoding runtime text.
- **acceptance target:** every Fleet List row renders a compact traffic-light indicator; active devices show green `On`; inactive devices show red `Off`; the indicator uses the existing backend runtime state and includes a text/accessible label so color is not the only signal; existing enable/disable status, sorting, filters, and candidate queue ordering remain unchanged.
- **target-environment result:** supported in the existing Zero Net Export Home Assistant custom panel using the backend-fed `sensor.managed_devices_overview` `managed_devices[*].observed_active` field. No Home Assistant frontend patch, native row injection, direct live install write, or new backend API field is required.
- **implementation status:** repo implementation adds a `Power` column to the Managed Devices Fleet List and renders a green/red `zne-traffic-light` from each managed device row's `observed_active` value.
- **validation result:** released in `v0.4.16` through GitHub/HACS, installed in Home Assistant, restarted, fingerprint matched before and after restart, and browser validated. Live proof showed the installed app header `Version 0.4.16`, the Managed Devices Fleet List `Power` column, and green `On` indicators for both current managed rows. Repo validation passed `node --check`, Python compile, focused release tests (`88` tests), full discovery (`642` tests), and `git diff --check`. Evidence: `validation/zne-fr-018-managed-devices-on-off-traffic-light.md`, `validation/0.4.16-release-validation.md`, `validation/artifacts/zne-fr-018-v0.4.16-managed-devices-traffic-light.png`.
