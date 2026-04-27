# Changelog

All notable changes to **Zero Net Export** will be documented in this file.

This project follows a practical Keep a Changelog style and uses semantic versioning for tagged releases where possible.

## [Unreleased]

Target release: `0.1.89`

### Fixed
- Replaced the stale archived `docs/UI_DESIGN-old.md` snapshot body with a source-of-truth pointer so retired release-target and source terminology can no longer masquerade as current UI direction.
- Reworded promotion fallback preset copy from generic custom-configuration language to `Manual native settings`, replaced empty-shortlist recommendation wording with neutral `surfaced candidates`, and changed promotion review/preset/default-value labels to surfaced-review wording, keeping unmanaged-to-managed review/promotion wording explicitly inside Home Assistant's native Managed Devices workflow.
- Removed helper-ish source-role-step fallback wording and hardened legacy Source blockers, source-role/path normalization, Configure bucket paths, setup notifications, runtime Repairs open lists, command-center summaries, device-page guides, and setup-check handoffs before cached or fallback text reaches Home Assistant.
- Added Managed Devices status to the command-center setup check and clarified Configure Fleet activity so managed inventory/action signals stay grouped ahead of unmanaged backlog across older count labels, zero-managed fallbacks, delimiter variants, and compact native Home Assistant surfaces.
- Tightened Managed Devices workspace handoffs, device-page promotion handoff copy, manual-add/edit/enablement/remove next steps, review snapshots, managed review notification labels, and promotion review/preset/save leads so unmanaged review and ready promotion stay workspace-first instead of reading like detached secondary actions.
- Tightened the Managed Devices, Configure -> Sensors, and Controls opening copy so native Home Assistant workspaces start as fleet, source-role, and controller homes instead of helper-style self-introductions or older tuning-bucket phrasing.
- Aligned Home Assistant source-role, command-center validation, and current-focus wording across UI docs, product/validation docs, README setup/restart guidance, entity-model diagnostics notes, optional dashboard support notes, bootstrap copy, validation boundary order, Sensors headings, Controls readiness, setup checklist, setup notifications, and native readiness copy.
- Reworded Sensors and Diagnostics selector/fallback/opening copy so native setup/support surfaces describe primary source-role ownership, choices, current selections, Diagnostics ownership, support evidence, install validation, and exact native paths without reviving picker-bug or workaround narration.
- Kept Diagnostics and operator-ready handoffs anchored to the exact native Configure and device Diagnostics paths, and capped installed-release metadata highlights so Home Assistant support surfaces stay compact even when historical changelog sections are long.

### Planning
- Kept supervisor steering and the `0.1.89` release plan aligned with current native bucket wording, the clean follow-up line after the already-published `v0.1.88` release, and James's direct approval as an explicit freeze prerequisite.

## [0.1.88]

### Fixed
- Trimmed the remaining verbose Diagnostics guide labels across Home Assistant Configure and the device-page Diagnostics path so Workstream F support surfaces stay blocker-first and secondary instead of reading like long helper narration.
- Aligned the device-page Diagnostics guide with the Configure Diagnostics bucket wording, keeping install-validation evidence and native bucket ownership explicit instead of reverting to weaker install-trust shorthand.
- Extended the legacy discovery cleanup helper so it now removes nested `backup_*` artifacts and matching `backup_*.pyc` files from inside `custom_components/zero_net_export`, covering the newer `custom_components.zero_net_export.backup_*` import-failure variant that sibling-only cleanup missed.
- Hardened the Home Assistant command-center guide and diagnostics snapshot against shorthand `Open Configure > ...` drift by expanding those prompts back to the exact native Configure paths in the rendered operator copy.
- Tightened the Home Assistant command-center operator board copy so the setup surface stays more compact and clearly setup-first instead of drifting back into a broader support-heavy console.
- Tightened Home Assistant Diagnostics bucket wording and aligned diagnostics guide, snapshot, and runtime-attention copy so the native IA split stays clearer between operator workflow and troubleshooting surfaces.
- Realigned the detailed Home Assistant managed-device review path wording so the secondary review/audit path supports the primary Managed Devices workspace instead of competing with it.
- Froze the repo candidate onto the `0.1.88` release line by bumping shipped metadata and version-coupled test expectations together, so Workstream G can move forward from repeated A/B microcopy churn into exact-build validation against one explicit release target.
- Warm the installed-package provenance cache from Home Assistant's executor during entry setup before native support, repairs, or diagnostics helpers read it, so release/install fingerprint metadata no longer performs its first manifest/hash disk scan on the event loop during startup.
- Committed the pending `docs/UI_DESIGN.md` build checklist, implementation-gap analysis, and explicit `1A` headline-decision-summary execution slice so the shipped UI design source of truth no longer trails the working-tree steering.
- Added `scripts/clean_legacy_discovery_artifacts.py` plus regression coverage so the repo now has a safe cleanup path for old `zero_net_export.backup_*` directories and stale `zero_net_export.*.pyc` artifacts that can still poison Home Assistant custom-component discovery after earlier deploys.
- Moved the exact-build deploy helper's default backups out of Home Assistant's `custom_components` discovery root and into `<config>/.openclaw_backups/custom_components/`, so backup copies can no longer masquerade as `zero_net_export.*` modules and break the Add Integration config flow.
- Upgraded the native managed-device workspace action on the device page so it now shows managed and unmanaged snapshots, runtime-aware managed-device status, surfaced-candidate fit and warnings, and an explicit promotion handoff to the full Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices path instead of a thinner raw-entity list.
- Ignored the repo-local `tmp-ha-config/` scratch Home Assistant tree so exact-build release guards can still use `--require-clean` without tripping over local validation debris.
- Wired the device-page command-center guide button to the shared full guide builder, so the native command-center handoff now shows the recommended section reason, common operator paths, section ownership, source-role blocker detail, and managed-device secondary review/audit path instead of a shorter partial summary.
- Stopped slow-moving required energy totals from holding runtime safe mode on their own, while still surfacing them as stale source diagnostics, so live control does not get re-blocked just because a total-increasing energy sensor has not ticked recently.
- Updated the native command-center blocker logic to treat those non-blocking stale energy totals as visible diagnostics instead of active blockers, so healthy power-path installs are steered toward the real next operator path again.
- Documented the required Home Assistant SSH fallback path in `TOOLS.md`, including the `/config` check and rerun-discovery step the supervisor should try before declaring live deploy or restart validation blocked.
- Strengthened the exact-build config-path discovery helper so it now reports Docker and Podman runtime status, inspects running Home Assistant container mounts for host-side `/config` paths, and prints an explicit container-runtime follow-up when discovery still cannot see the live install from the current shell.
- Realigned release-line metadata across the manifest, changelog, README, and install-helper regression expectations during stabilization so exact-build tooling no longer followed older rollback candidates; the current `0.1.88` candidate now owns the UI rollout boundary.
- Replaced the remaining vague `integration/device surfaces` wording in README, product spec, and optional dashboard follow-up docs with the exact native Configure plus device-path guidance, so operator-path docs stop drifting behind the source-of-truth UI design.
- Corrected the remaining README install/operator-path shorthand plus the bootstrap validation checklist so they now point to the exact `Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure` path instead of generic `Configure` wording.
- Removed stale pre-`0.1.88` release-target drift from shipped metadata and test expectations, so exact-build tooling follows the current UI rollout candidate instead of an older rollback line.

## [0.1.82] - 2026-04-14

### Fixed
- Made the exact deploy helper and installed-package fingerprint summary print an explicit post-restart validation checklist that sends operators back to **Configure -> Sensors and source mapping** before trusting live control, so the manual install and live-repair path stays aligned with the native command-center workflow.
- Aligned the remaining native operator wording from `Configured devices` to `Managed devices` across setup/repairs copy, command-center support snapshot text, status/reason summaries, core sensor names, and the optional in-HA debug dashboard so the shipped Home Assistant surfaces reinforce one consistent device-management path.
- Corrected the remaining planning and optional-dashboard wording that still said `integration device page`, so those docs now point to the exact native Home Assistant device path used elsewhere in the shipped support guidance.
- Tightened the native Repairs runtime-attention issue so it now includes blocking source-validation details alongside unavailable/stale mapped roles and the existing selector-fallback guidance, making the Home Assistant-native troubleshooting path clearer before deeper runtime validation.
- Added installed-package fingerprint details to the native Configure command center and Health/support screen, so mixed-build diagnosis now shows the live component path, code-versus-manifest version state, and tracked-file hashes before operators drop into full diagnostics.
- Clarified install-summary remediation so operators can see the exact upstream-sync next step and discovery rerun guidance before attempting another exact-copy deploy.
- Corrected project automation steering so Home Assistant access must be checked through the documented TOOLS.md SSH path before supervisor/watchdog runs claim live validation is blocked.

## [0.1.81] - 2026-04-13

### Fixed
- Shortened the shipped command-center and mapped-source blocker sensor states so Home Assistant no longer drops those entity states to `unknown` when stale or unavailable mapped sources produce long runtime summaries.
- Simplified the native runtime-attention next-step text so the Home Assistant popup and diagnostic sensors stop repeating the same stale-source detail across multiple fields while still pointing operators to the exact Configure -> Sources path.
- Cached installed-package provenance reads inside the runtime helper so the fingerprint summary no longer performs repeated synchronous manifest/hash file reads on the Home Assistant event loop during sensor rendering.

## [0.1.80] - 2026-04-12

### Fixed
- Corrected the startup native setup notification so it now names all four Configure command-center sections, including **Diagnostics**, instead of implying the live operator path ends at sensors, managed devices, and policy.
- Corrected the native command-center recommendation logic so runtime-readiness and safe-mode blockers now send operators to **Diagnostics** with the live readiness next step, instead of incorrectly steering fully mapped installs toward policy tuning while runtime attention is still the real blocker.
- Renamed the native Configure source step from plain `Sources` to `Sensors and source mapping` so the actual command-center screen matches the landing guidance and keeps the main source-management path easier to recognize in Home Assistant.
- Made the command-center landing screen and command-center guide show the current mapped source roles inline, and tightened live source-health summarising so healthy mappings no longer fall back to unrelated device/runtime reasons when operators are trying to understand source state.
- Stopped the command-center and source-mapping screens from echoing whole-integration health summaries in the source-health slot once mappings were valid, so the native source row now stays source-specific instead of misleading operators about where remaining runtime issues live.
- Wired the native Diagnostics screen, `Review diagnostics`, `Review diagnostics snapshot`, and setup checklist back to the command-center's recommended Configure section and exact path, so diagnostics-first triage now keeps pointing operators to the right native setup surface instead of dead-ending on generic health wording.
- Tightened the remaining source-mapping remediation copy so Configure now points operators back to the exact **Sensors and source mapping** path instead of vague `here` or `reopen Configure` wording while source validation is still blocking progress.
- Tightened native command-center, fleet-console, diagnostics, support-center, and checklist path guidance so those shipped Home Assistant surfaces now point to the exact Configure section they belong to instead of leaking the generic root Configure path during operator triage.
- Broadened the native combined-grid energy and battery-SOC dropdown matching so Configure now lists compatible sensors that expose the right units or state class even when vendors omit the ideal Home Assistant device_class, reducing fallback-field friction in real installs.
- Tightened the remaining native support and Repairs recovery wording so runtime-attention and invalid-managed-device issues now name the exact Configure, managed-device, and advanced JSON recovery paths instead of vague `open the native Configure flow` guidance.
- Added native device-page diagnostic sensors for mapped-source blocker summary and mapped-source next step, so operators can see the current source blocker and the exact Configure -> Sensors and source mapping remediation path directly from the integration's entity surface while safe mode is holding control.
- Corrected the new full managed-device candidate picker wording so it no longer implies the dropdown itself accepts a typed manual path, and instead tells operators to choose the explicit manual-selection option when the right entity is not listed.
- Replaced the remaining vague `integration device page` runtime wording with the full native Home Assistant device path for Mode, diagnostics, and diagnostics actions, so command-center guidance no longer leaks a fuzzy non-path while the supervisor is pushing exact native operator discoverability.
- Replaced the last shorthand `Open Configure` operator next-step prompts in Repairs, support readiness, and fleet guidance with exact native Home Assistant paths, so the shipped runtime surfaces stay aligned with the command-center discoverability push.
- Fixed the native source-mapping validation redisplay so the Configure screen now always supplies the **Affected mapped sources** summary when blocking source errors send operators back through the form, instead of dropping that command-center guidance right at the point of failure.
- Fixed the native command-center diagnostic sensor so **Command center status** now reports the current status of the recommended native section instead of incorrectly echoing the section name, and made the managed-device status read from live runtime usability when available.
- Made the native Configure policy screen name the exact native paths back to sensors, managed devices, and diagnostics, so operators do not have to infer where to go next from the command center once they start adjusting controller behaviour.
- Made the native Configure source/support screens and startup setup notice name the exact mapped source roles and entity ids that are unavailable or stale, so live Home Assistant installs can see which source binding is holding safe mode without digging through raw diagnostics.
- Made the native Configure copy more explicit about where to start after install and where device management versus policy tuning live, reducing the current operator-discoverability gap without adding any new surfaces.
- Aligned the implementation trail with the supervisor's native-HA-only release stance so optional Lovelace/dashboard work is no longer presented as a near-term priority ahead of Configure, native diagnostics, and real-install validation.
- Aligned the native diagnostics-path wording so the Configure command center and README both point operators to the full **Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Diagnostics** path before deeper device-page and Repairs triage.
- Tightened the README native device/support guidance so it names the exact integration device path instead of the vague `integration device page` shorthand.
- Clarified the README native Configure walkthrough so the main managed-device workspace is described once, in sequence, instead of splitting device management guidance across duplicated steps that obscured the intended operator flow.
- Made the native managed-device edit and remove pickers self-orienting by showing the current fleet, the main Configure path, and the recommended next device action instead of dropping operators into bare selector-only screens.
- Corrected the release-process background doc so it no longer claims the first formal GitHub release may still be unpublished, and instead reflects the current tagged-release line plus the requirement to complete the full `RELEASE_MANAGEMENT.md` ship path before calling work shipped.
- Normalized the remaining native operator next-step guidance so notifications, repairs, sensors, and Configure screens now point to the full Home Assistant path for Sources, Managed devices, and Policy instead of shorthand `Open Configure -> ...` wording that made the command-center path less discoverable in live installs.
- Fixed section-level Configure screens that were still showing the generic root Configure path instead of the exact Sensors, Managed devices, Policy, Diagnostics, or Advanced recovery route, so operators can tell where they are inside the native command center without backtracking.

## [0.1.79] - 2026-04-11

### Added
- Native fleet-promotion workflow improvements inside Home Assistant, including unmanaged candidate discovery, device-page fleet-console summaries, candidate pick/vetting steps, fit warnings, and smarter defaults carried into managed-device setup.
- Device-page candidate guidance now surfaces top-candidate fit, warnings, and a shortlist to guide promotion from unmanaged to managed devices.

## [0.1.78] - 2026-04-11

### Added
- Expanded the optional Lovelace debug dashboard scaffold inside Home Assistant with controller intent, battery/grid/solar telemetry, fleet planning, guard/support actions, and recent control activity, while keeping it outside the supported operator path.

### Fixed
- Made the native policy screen self-orienting by showing whether policy tuning is actionable yet, or whether source mapping or managed-device repair still needs attention first, instead of making operators infer that from other screens.
- Made the native Zero Net Export command center self-orienting by showing current source status, managed-device status, policy summary, and the recommended next section directly on the Configure landing screen instead of making operators infer where to go first.
- Added a native manual fallback field for the combined / net grid energy entity in Configure, so operators can still finish source mapping by pasting the same entity ID when Home Assistant's energy picker trips the known `valid entity ID or valid UUID` validation bug.
- Fixed the new source-remediation guidance pass so native support/checklist code safely reads `source_diagnostics` from validation details before building unavailable/stale role lists, avoiding a runtime `NameError` in the operator-readiness path while preserving the clearer Configure -> Sensors and source mapping remediation messaging.
- Made stale-source remediation more explicit in native support surfaces by naming the affected mapped source roles and backing entity ids in the stale summary, then reusing that exact summary in the checklist and next-step guidance so live HA installs point operators at the specific stale sources to fix.
- Finished the remaining null-safety pass for native support and diagnostics helpers so helper surfaces no longer dereference `state.validation_details` while coordinator state is still unavailable during startup or reload.
- Hardened the native support checklist and snapshot surfaces against startup windows where coordinator state is still `None`, targeting the live Home Assistant `setup_retry` crash `'NoneType' object has no attribute 'stale_data'`.
- Expanded fixed-load onboarding so native managed-device add/edit now accepts `light` entities alongside `switch` and `input_boolean`, matching ordinary controllable Home Assistant loads that operators expect to see in the picker.
- Hardened native platform setup and entity attribute access against startup windows where `coordinator.data` is still `None`, preventing Zero Net Export from crashing early in Home Assistant with `'NoneType' object has no attribute 'validation_details'` before entities can finish loading.
- Normalized combined-grid entity selector payload handling more defensively, including nested `*.entity_id` option-flow payloads, to target the still-open Home Assistant combined/net grid energy submit bug.
- Reverted README and dashboard docs that had drifted into presenting Lovelace as a supported operator surface. The supervisor-aligned position is again explicit: the supported operator path is native Home Assistant integration/device surfaces only, with Lovelace kept optional for debug visibility.
- Tightened IMPLEMENTATION_PLAN and REFERENCE_MATRIX language so roadmap/reference docs no longer describe a Home Assistant mini-app or operator dashboard as the supported direction.
- Taught release metadata helpers to fall back to the current `Unreleased` changelog notes when the manifest version advances ahead of a tagged changelog heading, so native support/release surfaces stop showing a false "no changelog entry matched" warning during active stabilization.
- Normalized native selector values before validation so Home Assistant picker payloads that arrive as structured objects no longer trip fake "valid entity ID or valid UUID" errors on submit.
- Restored native entity pickers after the temporary text-field workaround regressed selection UX; picker-based mapping is available again while deeper HA selector issues continue to be investigated.
- Switched native source mapping fields to plain text entity-id inputs to bypass a Home Assistant selector validation bug that was rejecting valid selected entities with misleading "valid entity ID or valid UUID" errors.
- Tightened native source selectors so combined grid energy only accepts energy-class sensors and power-only slots reject energy sensors, preventing invalid mixed-type selections from failing late with confusing entity-id errors.
- Made the native home-load power sensor optional when solar and grid sources are already mapped. Native Configure no longer blocks combined/net-grid installs that can infer household load from solar, grid, and battery flows.
- Taught runtime validation to derive effective home load from solar, grid import/export, and battery charge/discharge when no dedicated whole-home load sensor exists, avoiding unnecessary setup dead-ends for common real-world installs.
- Added an up-front native source-mapping selector for combined versus separate grid sensors. The Configure flow now defaults to combined/net mapping, stores the combined selection, and derives import/export bindings from one signed grid power and one signed grid energy entity instead of forcing four separate grid fields.
- Reworded native source-mapping helper text so combined/net grid hardware is a first-class path in product, not a detour through external split helpers.
- Stopped the native **Controller tuning** Configure step from overwriting the entire options payload. Saving target/deadband/reserve settings now preserves the managed-device inventory and reloads the integration, instead of silently dropping devices from the native operator path.
- Tightened the native support snapshot so per-device lines now include real runtime usability, status, planned action, and guard state from the coordinator instead of reporting misleading `usable=None` placeholders.
- Reworded runtime reason and recommendation text to keep the operator path native-first: Home Assistant now points people back to **Configure** for managed-device repair instead of prematurely talking about internal inventory JSON.
- Reworded readiness and device-status summaries so native support surfaces now describe parse failures as managed-device configuration issues instead of internal inventory problems.
- Reworded the startup/setup notification so managed-device parse problems are described as native Configure issues first, with JSON called out only as an advanced recovery fallback.
- Reworded Repairs and options-flow error labels so the user-facing title/error now says managed-device configuration, not managed-device inventory.
- Reworded the managed-device removal and advanced JSON editor copy so native Configure keeps talking about managed-device configuration first, with JSON reserved for recovery and bulk edits.
- Tightened README and native-surface planning docs so Lovelace is described only as optional debug visibility, not as part of the supported operator path.
- Updated the validation checklist so real-install source-mapping validation now explicitly covers combined/net versus separate grid sensor layouts.
- Updated ENTITY_MODEL and ARCHITECTURE docs so source-role descriptions now reflect the combined/net grid mapping path instead of assuming separate import/export entities only.
- Updated README, native setup field copy, and validation checklist so the optional home-load sensor path now matches the shipped native setup behavior.
- Updated the validation checklist to point at the shipped README configuration guidance instead of the removed `CONFIG_FLOW.md` file.

## [0.1.73] - 2026-04-10

### Changed
- Reworked the native Configure flow into a clearer command-center layout with explicit Sources, Policy, Managed devices, and Advanced recovery sections.
- Improved managed-device summaries and wording so the installed UI better explains where operators tag controllable loads and where controller policy is tuned.

## [0.1.72] - 2026-04-10

### Fixed
- Stopped Zero Net Export runtime sensor, diagnostics, and native-support surfaces from parsing `CHANGELOG.md` on hot paths by using deferred release metadata outside diagnostics-heavy contexts.

## [0.1.71] - 2026-04-10

### Fixed
- Deferred changelog parsing out of the coordinator startup path so Zero Net Export no longer reads `CHANGELOG.md` synchronously during first refresh while Home Assistant is setting up the config entry.

## [0.1.70] - 2026-04-10

### Fixed
- Hardened the native support checklist and snapshot surfaces against startup windows where coordinator state is still `None`, targeting the live Home Assistant `setup_retry` crash `'NoneType' object has no attribute 'stale_data'`.
- Expanded fixed-load onboarding so native managed-device add/edit now accepts `light` entities alongside `switch` and `input_boolean`, matching ordinary controllable Home Assistant loads that operators expect to see in the picker.

## [0.1.69] - 2026-04-10

### Fixed
- Finished the remaining null-safety pass for native support and diagnostics helpers so helper surfaces no longer dereference `state.validation_details` while coordinator state is still unavailable during startup or reload.

## [0.1.68] - 2026-04-10

### Fixed
- Hardened native platform setup and entity attribute access against startup windows where `coordinator.data` is still `None`, preventing Zero Net Export from crashing early in Home Assistant with `'NoneType' object has no attribute 'validation_details'` before entities can finish loading.

## [0.1.67] - 2026-04-10

### Fixed
- Normalized combined-grid entity selector payload handling more defensively, including nested `*.entity_id` option-flow payloads, to target the still-open Home Assistant combined/net grid energy submit bug.
- Kept the Lovelace dashboard explicitly outside the supported operator path in README, dashboard docs, and roadmap/reference docs so the shipped product stays aligned to native Home Assistant integration/device surfaces only.

## [0.1.58] - 2026-04-08

### Added
- Added a native managed-device fleet review step in Configure so larger installs can quickly toggle which devices stay enabled for control without editing raw inventory JSON.

### Changed
- Expanded the managed-device workspace summaries and picker labels to show enabled state, priority, kind, and entity id, making bigger mixed-device fleets easier to audit from native Home Assistant selectors.
- README guidance now points operators at the new native fleet-staging path for larger installs.
- Integration version advanced to `0.1.58` for the native fleet review and staging pass.

## [0.1.57] - 2026-04-08

### Added
- Added a native managed-device preset picker before the add-device form, so common Home Assistant loads can start from safer defaults instead of every operator rebuilding timings and power settings from scratch.
- Shipped built-in presets for generic fixed/variable loads plus hot water, pool pump, smart plug, EV charger, and battery charge sink workflows.

### Changed
- The native add-device form now shows which preset seeded the defaults, keeping the Configure workspace more coherent for larger mixed-device fleets while still allowing manual edits before save.
- Integration version advanced to `0.1.57` for the native managed-device preset pass.

## [0.1.56] - 2026-04-08

### Added
- Added native Home Assistant Repairs issues for the highest-friction operator states, so incomplete setup, invalid managed-device inventory, and runtime attention conditions now surface in HA's built-in issue workflow instead of relying only on scattered notifications and diagnostics.

### Changed
- Wired Repairs issue syncing into setup, migration, unload, and coordinator refresh cycles so the native operator guidance stays current as sources recover, devices become usable, or setup blockers are fixed.
- Integration version advanced to `0.1.56` for the native Repairs and operator-coherence pass.

## [0.1.55] - 2026-04-08

### Added
- Added a native managed-device edit-in-place path in Configure, including a picker for existing devices and prefilled fixed/variable forms so operators can change entity bindings and runtime limits without dropping into JSON.

### Changed
- Reused the native managed-device form for both add and edit flows, preserving stable device keys during edits so existing per-device runtime state and overrides remain attached.
- Integration version advanced to `0.1.55` for the native managed-device edit-in-place pass.

## [0.1.54] - 2026-04-08

### Added
- Added a native managed-device add/remove flow in Configure for common fixed and variable devices, so normal onboarding no longer requires hand-editing `device_inventory_json`.
- Added a native **Review diagnostics** device-page action that publishes one combined readiness/checklist/diagnostics snapshot notification for faster operator triage.

### Changed
- Reframed README, product spec, implementation plan, and validation guidance around the current reality: the HA-first path is correct but still transitional, managed-device JSON still exists under the hood, and real-world validation remains in progress.
- Repositioned the raw managed-device JSON editor as an advanced recovery/bulk-edit path instead of the default Configure experience.
- Tightened native support messaging so setup notices point operators at the combined support-center/checklist/diagnostics surfaces.
- Integration version advanced to `0.1.54` for the native managed-device UX and support-surface coherence pass.

## [0.1.53] - 2026-04-08

### Changed
- Removed the shipped custom panel route and its related launcher/frontend code. Zero Net Export no longer registers the `/zero-net-export` sidebar/custom-panel path or ships the panel websocket/bootstrap layer.
- Simplified the supported operator path to native Home Assistant surfaces only: **Configure** for source mapping, managed devices, and controller tuning, plus the integration device page for setup checklist and diagnostics snapshot actions.
- Rewrote active project guidance and validation/docs around the new native-first goal, replacing panel-first rebuild direction with native-surface consolidation guidance.
- Integration version advanced to `0.1.53` for the panel-route removal and native-surface consolidation pass.

## [0.1.52] - 2026-04-08

### Changed
- Moved the primary setup path into native Home Assistant surfaces. The integration Configure flow now exposes a native source-mapping step, a native managed-devices step, and a controller-tuning step, so normal onboarding no longer depends on `/zero-net-export` loading successfully.
- Reframed the custom panel as optional. Configure text, onboarding notifications, and native diagnostic/checklist buttons now point operators to Home Assistant's normal Configure path first, with the panel route kept only as an optional extra surface.
- Updated README and validation/docs wording to match the new product direction: native HA configuration is the required path, while the panel remains optional when available.
- Integration version advanced to `0.1.52` for the native-configuration product pivot.

## [0.1.51] - 2026-04-08

### Fixed
- Hardened panel registration across partial setup and reload paths by tracking static-path, custom-panel, and websocket registration separately instead of treating the whole panel stack as a single one-shot flag. This is the main backend-side fix for live installs where `/zero-net-export` could still fall back to 404 after a stale or partial registration state.
- Reclassified the main health, action-history, and per-source diagnostic sensors into native Home Assistant diagnostic categories so the existing device and entity surfaces expose troubleshooting data more prominently without adding a new interface.

### Changed
- Integration version advanced to `0.1.51` for the backend route and diagnostics wiring hardening pass.

## [0.1.50] - 2026-04-08

### Added
- Added an explicit recommended validation run order to the validation checklist so the next project push stays focused on real Home Assistant install proof, panel-first onboarding, and Configure -> setup handoff verification.
- Added a new overview-level **Diagnostics at a glance** section plus direct jumps into **Diagnostics** and **Setup**, so runtime health and troubleshooting are visible from the main operator surface instead of being easy to miss.
- Added a diagnostics-tab **Support Snapshot** block with in-place copy action, so setup/runtime evidence is easier to grab without hunting through Settings first.
- Added native Home Assistant diagnostic buttons on the integration device page, **Review diagnostics snapshot** and **Show setup checklist**, so operators can surface troubleshooting state without relying on the custom `/zero-net-export` route.
- Added native-surface operator-readiness detail to the config-entry diagnostics export, so exported diagnostics now reflect the same next-step guidance exposed by the device-page fallback path.

### Changed
- Clarified in the README that the highest-value next step is a real Home Assistant validation pass followed by a release, not more speculative UI churn.
- Simplified the Configure -> setup handoff path back to the real `/zero-net-export?...` panel route instead of the launcher trampoline, because the launcher was triggering bad `open website` UX on real clients and its iframe fallback was visibly failing with a 404.
- Normalized the panel tab labels so **Diagnostics** is surfaced with a clean operator-facing label instead of a lowercase internal tab key.
- Updated project docs to explicitly reflect the new live-install reality: native Home Assistant diagnostics and fallback HA surfaces must be treated as first-class operator paths whenever the custom panel route is unreliable in real environments.
- Integration version advanced to `0.1.50` for the native diagnostics-surface shift.

## [0.1.49] - 2026-04-08

### Fixed
- Removed the broken Configure -> setup launcher trampoline and sent Home Assistant back to the real in-app Zero Net Export setup route, avoiding the bad `Open website` flow and the failing 404 fallback launcher surface seen in real testing.
- Promoted diagnostics visibility inside the panel with an overview summary block, direct navigation actions, and an in-tab support snapshot section for faster troubleshooting.

### Changed
- Integration version advanced to `0.1.49` for the real-world setup handoff and diagnostics discoverability follow-up.

## [0.1.48] - 2026-04-07

### Fixed
- Wired the Configure -> setup launcher path through a real Home Assistant external-step completion handler, so the options flow can close cleanly after opening the panel instead of leaving the operator stranded in a half-finished Configure state.

### Changed
- Integration version advanced to `0.1.48` for the Configure external-step completion repair.

## [0.1.47] - 2026-04-06

### Fixed
- Upgraded the Configure -> setup launcher from a thin redirect page into a real last-mile fallback surface that embeds the actual `/zero-net-export?tab=setup...` panel, so the mapping UI stays visibly reachable even when Home Assistant's external-step/top-window navigation is awkward or partially blocked.
- Added a stronger operator-facing retry path that explicitly re-attempts top-window navigation while keeping the real setup panel loaded below, instead of leaving the operator stranded on a launcher page with only a dead-end explanation.

### Changed
- Integration version advanced to `0.1.47` for the live Configure -> real mapping-panel visibility/reachability repair.

## [0.1.46] - 2026-04-06

### Fixed
- Hardened the Configure -> setup launcher so it now tries Home Assistant router navigation first, then falls back to full top-window navigation, instead of only relying on a simpler location handoff that could leave the operator stranded on the launcher page or in an unclear intermediate surface.
- Updated the launcher CTA to explicitly open the real Zero Net Export setup panel in the top Home Assistant window, making the last-mile Configure -> mapping-panel path more visible and usable when the browser or HA external-step context is awkward.

### Changed
- Panel schema advanced to `30` and integration version advanced to `0.1.46` for the stronger Configure -> real panel landing repair.

## [0.1.45] - 2026-04-06

### Fixed
- Replaced the Configure/options external handoff target with a dedicated same-origin launcher page that force-navigates Home Assistant into the real Zero Net Export Setup tab for the active config entry, instead of relying on the options-flow external step to open the custom panel route directly.
- Added a visible in-browser fallback button on that launcher page so the operator still gets a clean panel-first path even if Home Assistant/browser popup behavior blocks the automatic redirect.
- Switched onboarding notifications to the same launcher path so the main operator CTA and the Configure CTA now land on the same real setup surface.

### Changed
- Integration version advanced to `0.1.45` for the launcher-based Configure -> panel landing repair.

## [0.1.44] - 2026-04-06

### Fixed
- Changed the Configure -> **Open setup & mapping panel** handoff to deep-link the active config entry itself, not just the generic panel route, so Home Assistant lands on the real mapping surface for the exact integration the operator is configuring.
- Added an in-panel Configure-launch banner on the Setup tab so operators can immediately tell they have reached the real setup and mapping interface, not a fallback recovery form.

### Changed
- Panel schema advanced to `29` and integration version advanced to `0.1.44` for the entry-specific Configure -> panel landing repair.

## [0.1.43] - 2026-04-06

### Fixed
- Changed the Configure -> **Open setup & mapping panel** path from a dead-end explanatory abort into a real Home Assistant external-step handoff that targets the actual panel route.
- Deep-linked the panel-first onboarding path to the **Setup** tab and persisted `tab` and `entry` URL state inside the panel app, so operators land on the real mapping interface instead of a generic overview tab and can reopen/share the exact setup surface reliably.
- Updated onboarding notifications to point straight at the setup/mapping route for the active config entry instead of the panel root.

### Changed
- Panel schema advanced to `28` and integration version advanced to `0.1.43` for the setup-tab deep-link routing repair.

## [0.1.42] - 2026-04-06

### Fixed
- Fixed the shipped Home Assistant options flow wiring so the advanced recovery step now renders as the real `advanced` step instead of incorrectly reusing `init`, which could leave the Configure/options UI with blank or broken menu labels.
- Added a runtime `translations/en.json` payload for the custom integration so Home Assistant can resolve the actual options-flow labels, descriptions, and abort text in the installed package instead of falling back to raw keys like `panel_only`.
- Replaced operator-facing onboarding/support text that previously leaked raw internal mapping keys such as `solar_power_entity` and `grid_import_power_entity` with plain-language source-role names.
- Hardened the shared entity base by removing custom-entity translation-key wiring and the relative `configuration_url` from device info, reducing the chance of cross-platform entity-registration failures in the real Home Assistant entity-add path.

### Changed
- Integration version advanced to `0.1.42` for the real Home Assistant labels/runtime hardening repair release.

## [0.1.41] - 2026-04-06

### Fixed
- Rewired the real Home Assistant Configure/options path so it no longer drops operators directly into raw internal backend fields as the primary setup surface. Configure now lands on a panel-first menu, with a dedicated operator step that points setup to the Zero Net Export panel.
- Added an in-Home Assistant onboarding notification with a direct `/zero-net-export` link whenever required source mappings or device onboarding are still incomplete, so the intended mapping workflow stays visibly reachable after install/reload.

### Changed
- Moved raw backend controls (`target_export_w`, `deadband_w`, `battery_reserve_soc`, `refresh_seconds`, `device_inventory_json`) behind an explicit **Advanced defaults / recovery** path instead of presenting them as the default operator-facing configure experience.
- Integration version advanced to `0.1.41` for the panel-first operator-path restoration follow-up.

## [0.1.40] - 2026-04-06

### Added
- Added end-to-end support for required grid import/export mapping from signed net-grid sensors in the panel/backend flow, so operators can complete the required power and energy roles in-product even when Home Assistant exposes one bidirectional grid sensor instead of separate import/export entities.

### Changed
- The Setup tab now suggests signed-split mappings for likely net-grid sensors and explains when a suggestion derives import/export from a signed source rather than requiring a separate native entity.
- Source validation/runtime diagnostics now preserve both the underlying entity and the derived binding label, and stale-data tracking now follows the real underlying entity for derived mappings.
- Panel schema advanced to `27` and integration version advanced to `0.1.40` for the signed grid-split mapping completion step.

## [0.1.39] - 2026-04-06

### Fixed
- Fixed the main backend gating bug in source validation: warning-level source issues no longer force controller safe mode. Required mapping can now progress from installed -> mapped -> operational once the required sources are present and there are no blocking errors or stale required sensors.

### Changed
- Validation recommendations now distinguish between true blocking conditions and non-blocking warnings, so the save/apply path better matches the intended operator workflow instead of treating every metadata quirk as a hard stop.
- Integration version advanced to `0.1.39` for the safe-mode gating fix on the source-mapping backend path.

## [0.1.38] - 2026-04-06

### Fixed
- Fixed the panel mapping bridge so runtime validation/freshness payloads are normalized back onto the saved config-entry source-role keys (`solar_power_entity`, `grid_import_power_entity`, etc.) before reaching the UI. This makes saved mappings reflect back onto the exact required roles the operator edited instead of showing misleading blank or mismatched per-role health after reload.

### Changed
- The Setup and Diagnostics tabs now render source-health/freshness rows with operator-facing role labels rather than internal runtime keys, making it much clearer which required mapping is healthy, stale, blocked, or still needs attention.
- Saving source mappings now gives an explicit in-panel confirmation that the integration reloaded and that readiness/diagnostics should be reviewed to confirm the controller can leave blocked setup state.
- Panel schema advanced to `26` and integration version advanced to `0.1.38` for the source-mapping status/readiness alignment follow-up.

## [0.1.37] - 2026-04-06

### Added
- Added persisted in-product update visibility that remembers the previously installed integration version per config entry and publishes an operator-facing update summary such as `Updated from 0.1.36 to 0.1.37`, so upgrades feel explicit inside Home Assistant instead of opaque.
- Added new diagnostic update entities/surface data for `previous installed version` and `update summary`, making version/change context available from normal entity/device inspection, panel views, support snapshots, and diagnostics exports.

### Changed
- Expanded the Overview, Diagnostics, Settings, and support snapshot release sections to include update-state messaging alongside the installed version and changelog preview, so the operator can answer both `what version is installed?` and `what changed when this updated?` without leaving Home Assistant.
- Panel schema advanced to `25` and integration version advanced to `0.1.37` for the persisted in-product update-visibility follow-up.

## [0.1.36] - 2026-04-06

### Added
- Added diagnostic release entities for the integration device, including an installed-version sensor plus operator-facing release summary and change-preview sensors, so version/change visibility is available directly from normal Home Assistant entity/device surfaces rather than only inside HACS or GitHub.
- Added a concise installed-release panel section on the Overview tab so the operator can immediately see the installed version and top changes without digging through Settings.

### Changed
- Expanded parsed release metadata with a short `changes_preview`/headline summary that can be reused across panel, diagnostics, and entity attributes for consistent in-product update messaging.
- Panel schema advanced to `24` and integration version advanced to `0.1.36` for the in-product release-visibility follow-up.

## [0.1.35] - 2026-04-05

### Added
- Exposed the installed integration version directly on the Home Assistant device page via device info (`sw_version`), so operators can confirm what build is running without leaving Home Assistant.
- Added parsed release metadata from `CHANGELOG.md` to the panel and diagnostics payloads, creating an in-product "what changed in this release" summary plus previous-release context.

### Changed
- Expanded the panel Settings release/support section with current release summary, release date, previous documented version, and bullet highlights so the operator can answer "what changed in this update?" from inside Home Assistant.
- Support snapshots now include release-summary context, and panel schema advanced to `23` alongside integration version `0.1.35` for the in-product version/update visibility refresh.

## [0.1.34] - 2026-04-05

### Changed
- Added a guided required-role checklist at the top of the Setup tab so operators can immediately see which exact solar/grid/home mappings are still blocking readiness and apply a suggested entity per missing role without hunting through the full form first.
- Enriched source suggestion ranking with plain-language match reasons plus import/export conflict penalties, helping the panel explain *why* an entity is being suggested and reducing the chance of picking the wrong grid direction sensor.
- Source cards now show per-role mapping health more clearly with mapped/blocked/warning status pills and inline current-mapping context, making the install -> mapped -> operational transition less opaque.
- Panel schema advanced to `22` and integration version advanced to `0.1.34` for the guided required-mapping/operator-readiness refresh.

## [0.1.33] - 2026-04-05

### Changed
- Reworked the panel Setup tab into a more guided source-mapping flow by grouping required solar/grid/load roles separately from optional battery signals, adding inline plain-language role explanations, and surfacing per-group mapping progress so operators can see what is still blocking readiness.
- Added a one-click "Fill Empty Required Fields With Likely Matches" action plus stronger top-match presentation for each source role, making it easier to get from installed -> mapped without manually hunting raw entity ids for every required field.
- Added a setup-specific progress summary that explicitly calls out required-vs-optional mapping status and names the remaining missing required roles, so blocked safe-mode state is clearer and less overwhelming.
- Panel schema advanced to `21` and integration version advanced to `0.1.33` for the guided source-mapping UX release.

## [0.1.32] - 2026-04-05

### Fixed
- Fixed the Home Assistant options/gear flow regression by avoiding assignment to the read-only `config_entry` property in `OptionsFlow`, which previously crashed upgraded installs with `AttributeError: property 'config_entry' of 'ZeroNetExportOptionsFlow' object has no setter`.
- Fixed coordinator startup on Home Assistant by restoring a real module logger instead of `logger=None`, preventing `AttributeError: 'NoneType' object has no attribute 'isEnabledFor'` during the first refresh/setup path.

### Changed
- Integration version advanced to `0.1.32` for the real Home Assistant runtime repair release.

## [0.1.31] - 2026-04-05

### Fixed
- Hardened the shipped configure/options flow for upgraded installs by normalizing legacy entry defaults before building selectors, reducing the chance that missing, `None`, or stringly-typed stored values trigger a backend 500 when the operator clicks the integration gear/configure path.
- Added config-entry migration/normalization so older installs pick up safe numeric defaults and a string device-inventory payload even if earlier entry data was incomplete or loosely typed.

### Changed
- Integration version advanced to `0.1.31` for the real Home Assistant configure/options-flow crash fix.

## [0.1.30] - 2026-04-05

### Changed
- Formalized the HACS-visible release path for the bootstrap-onboarding package: the repository now ships a fresh integration version intended specifically to force a real remote update check instead of relying on local commits or manifest-only assumptions.
- Added explicit release/distribution verification guidance so shipping now requires pushed branch state, matching remote tags/releases, and confirmation that the real Home Assistant install path is serving the intended package instead of a stale older build.
- Integration version advanced to `0.1.30` so Home Assistant / HACS can surface a clearly newer package than the previously observed stale install path.

## [0.1.29] - 2026-04-05

### Changed
- Reduced the Home Assistant add-integration flow to a bootstrap-only step so operators can create the backend entry quickly, then complete real onboarding inside the Zero Net Export panel instead of a long raw source-mapping form.
- Added plain-language field help for the remaining bootstrap field and for the advanced options fields that still exist, including explicit guidance that device-inventory JSON is fallback/debug-only.
- Updated README, implementation docs, product spec, and validation checklist so the shipped project state now consistently describes the panel-first onboarding model.
- Integration version advanced to `0.1.29` for the bootstrap-onboarding UX rebuild milestone.

## [0.1.28] - 2026-04-05

### Fixed
- Fixed a panel state regression where the backend exposed validation details under `overview.controller_settings` instead of the actual configured/effective controller defaults and override flags, so the Settings workflow can once again show the operator which controller values are configured versus currently overridden.

### Changed
- Integration version advanced to `0.1.28` for the panel controller-defaults payload fix.

## [0.1.27] - 2026-04-05

### Fixed
- Restricted the panel bootstrap websocket (`zero_net_export/panel/get_state`) to Home Assistant admin users so the admin-only sidebar app no longer leaves its read-side state, entity suggestions, and support snapshot available through a non-admin websocket call path.

### Changed
- Integration version advanced to `0.1.27` for the panel permission/runtime hardening follow-up.

## [0.1.26] - 2026-04-05

### Fixed
- Hardened the panel operator path for real Home Assistant permissions by restricting the Zero Net Export sidebar app and all panel-backed write/reload websocket actions to admin users, avoiding non-admin access to config-entry mutations that would otherwise fail mid-workflow.

### Changed
- Integration version advanced to `0.1.26` for the panel permission/runtime hardening refresh.

## [0.1.25] - 2026-04-05

### Fixed
- Hardened more panel render paths against HTML-breaking diagnostics, readiness text, workflow guidance, and selected-device summaries so unusual entity names or backend strings are less likely to corrupt the operator UI during real Home Assistant use.

### Changed
- Panel schema advanced to `20` and integration version advanced to `0.1.25` for the panel rendering hardening refresh.

## [0.1.24] - 2026-04-05

### Fixed
- Hardened the panel support-snapshot copy action for real Home Assistant/browser contexts by falling back to legacy clipboard copy when `navigator.clipboard` is unavailable or blocked, so operators can more reliably copy a diagnostics summary into Discord and issue reports from the panel.

### Changed
- Panel schema advanced to `19` and integration version advanced to `0.1.24` for the panel support-copy reliability refresh.

## [0.1.23] - 2026-04-04

### Fixed
- Hardened the panel frontend against HTML-breaking entity names, validation messages, device reasons, and support-snapshot content by escaping dynamic panel text before rendering it into the operator UI.

### Changed
- Panel schema advanced to `18` and integration version advanced to `0.1.23` for the panel rendering/runtime hardening refresh.

## [0.1.22] - 2026-04-04

### Added
- Expanded the panel Devices tab with a selected-device configuration summary that exposes entity binding, adapter, configured/effective enable + priority state, power model, and safety timing limits without falling back to raw JSON.

### Fixed
- Fixed Diagnostics source-issue rendering so structured validation issues now display as readable severity/message text instead of raw object placeholders.

### Changed
- Panel schema advanced to `17` and integration version advanced to `0.1.22` for the device-management clarity refresh.

## [0.1.21] - 2026-04-04

### Fixed
- Hardened panel-state bootstrap for startup/reload windows where a Zero Net Export config entry exists but its coordinator has not produced runtime state yet, preventing the panel shell from crashing while trying to summarize health before the backend is ready.

### Changed
- Integration version advanced to `0.1.21` for the panel bootstrap/loading-state stability fix.

## [0.1.20] - 2026-04-04

### Fixed
- Fixed a panel runtime regression in the backend bootstrap path: `zero_net_export/panel/get_state` now builds entry payloads with the active Home Assistant instance instead of throwing a `NameError` when assembling available entities and suggestions.

### Changed
- Integration version advanced to `0.1.20` for the panel websocket/bootstrap runtime stability fix.

## [0.1.19] - 2026-04-04

### Added
- Added template-aware device entity suggestions in the panel Devices editor so operators can pick likely switch/number targets for hot water, pool, EV charger, battery-charge, and smart-plug workflows without hunting through a flat entity list.

### Changed
- Device onboarding in the panel now ranks likely entity matches by device kind plus template keywords, making the panel-first add/edit flow more guided and reducing fallback to raw JSON/options spelunking.
- Panel schema advanced to `16` and integration version advanced to `0.1.19` for the guided device-entity suggestion refresh.

## [0.1.18] - 2026-04-04

### Added
- Added an in-panel support snapshot in Settings so operators can copy a concise release/runtime/setup summary for Discord or issue triage without reconstructing state from multiple diagnostics sections.

### Changed
- Settings now previews the generated support snapshot alongside release links, making the panel-first support path more practical during real-install validation and troubleshooting.
- Panel schema advanced to `15` and integration version advanced to `0.1.18` for the panel support-snapshot refresh.

## [0.1.17] - 2026-04-03

### Added
- Added an in-panel operator-readiness checklist and next-step summary so the Setup tab now tells operators whether they are blocked on source mapping, source remediation, device onboarding, device usability, or final runtime validation.

### Changed
- Settings now mirrors the same readiness phase/summary guidance so support and release triage can see the current panel-first onboarding state without inferring it from scattered diagnostics.
- Panel schema advanced to `14` and integration version advanced to `0.1.17` for the panel onboarding/readiness guidance refresh.

### Changed
- README and UX docs now describe the shipped Home Assistant panel as the primary operator path and demote the Lovelace dashboard to fallback/debug status so release-state documentation matches the current panel-app product shape.

## [0.1.16] - 2026-04-03

### Fixed
- Fixed panel and diagnostics release metadata so Zero Net Export now reports the packaged integration version instead of incorrectly showing the Home Assistant config-entry schema version as if it were the release version.

### Changed
- Panel Settings now shows both the packaged integration version and the Home Assistant config-entry version, making release support and runtime debugging less confusing during the panel-app rebuild.
- Panel schema advanced to `13` and integration version advanced to `0.1.16` for the release-metadata/runtime support fix.

## [0.1.15] - 2026-04-03

### Added
- Added role-specific source suggestions in the panel Setup tab so operators can apply likely solar/grid/home/battery mappings directly from guided chips instead of hunting through a flat sensor list.

### Changed
- Panel source suggestions now rank Home Assistant sensors by unit, metadata, and role-name hints to make panel-first onboarding faster and less error-prone.
- Panel schema advanced to `12` and integration version advanced to `0.1.15` for the guided source-suggestion setup refresh.

## [0.1.14] - 2026-04-03

### Added
- The panel app now auto-refreshes its live state every 15 seconds while visible and refreshes again when Home Assistant regains browser focus, reducing stale operator state during day-to-day use.

### Changed
- Panel schema advanced to `11` so Home Assistant will pick up the live-refresh panel bundle update reliably.
- Integration version advanced to `0.1.14` for the panel live-state usability refresh.

## [0.1.13] - 2026-04-03

### Added
- Added guided source-remediation detail to the panel Setup tab so operators can review each mapped source's live reading, unit, device class, state class, and validation issues without leaving the app.
- Added in-panel calibration hints during source setup so sign, metadata, and mapping problems are surfaced directly in the panel-first workflow.

### Changed
- Sensor suggestions in the panel source-mapping form now include richer metadata context to make it easier to choose the correct Home Assistant source entity.
- Panel schema advanced to `10` and integration version advanced to `0.1.13` for the guided source diagnostics/setup refresh.

## [0.1.12] - 2026-04-02

### Fixed
- Fixed a panel operator-path gap for installations with multiple Zero Net Export config entries: the frontend can now switch between configured entries instead of silently reading and mutating only the first returned entry.

### Changed
- Panel header now exposes the active configured system and resets device-editor context when operators switch entries so edits do not leak across systems.
- Panel schema advanced to `9` and integration version advanced to `0.1.12` for the multi-entry panel selection refresh.

## [0.1.11] - 2026-04-02

### Added
- Added curated device onboarding templates in the panel for common fixed and variable operator workflows such as hot water, pool pumps, EV charging, and battery charge sinks.
- Added direct edit actions from the managed-device table plus a selected-device runtime summary so operators can move from diagnosis to configuration without falling back to raw JSON or hunting through entities.

### Changed
- Devices tab editing is now more guided: template selection prefills safer defaults, the form can be reset explicitly, and the editor keeps context about the currently selected device.
- Panel schema advanced to `8` and integration version advanced to `0.1.11` for the guided device-onboarding UX refresh.

## [0.1.10] - 2026-04-02

### Fixed
- Hardened panel frontend registration so repeated bundle imports during Home Assistant reload/update flows no longer throw a duplicate custom-element definition error.
- Added panel bundle cache-busting via the schema/versioned module URL so Home Assistant is less likely to keep serving a stale frontend bundle after panel updates.

### Changed
- Panel schema advanced to `7` to force the hardened panel bundle to refresh with this runtime stability update.
- Integration version advanced to `0.1.10` for the panel reload/cache stability fix.

## [0.1.9] - 2026-04-02

### Fixed
- Fixed the panel shell bootstrap lifecycle so the frontend now loads state correctly even when the custom element connects before Home Assistant injects `hass`, avoiding a permanent loading screen in real installs.

### Changed
- Integration version advanced to `0.1.9` for the panel bootstrap/runtime stability fix.

## [0.1.8] - 2026-04-02

### Fixed
- Fixed a panel backend runtime regression where the Settings payload referenced controller default constants that were not imported, which could break `zero_net_export/panel/get_state` and prevent the panel app from loading cleanly.

### Changed
- Integration version advanced to `0.1.8` for the panel runtime stability fix.

## [0.1.7] - 2026-04-02

### Added
- Added a real panel Settings payload with controller defaults, fleet health summary, panel-first workflow guidance, and direct documentation/release/support links.
- Expanded the Settings tab into an operator-facing release/support view instead of leaving it as a near-duplicate of runtime controls.

### Changed
- Panel schema advanced to `6` so the frontend can consume structured settings/release metadata.
- Integration version advanced to `0.1.7` for the first panel settings/release-management milestone.

## [0.1.6] - 2026-04-01

### Added
- Expanded the panel diagnostics payload with action history, source diagnostics, calibration hints, and per-device explanation data already available in the backend coordinator.
- Added an in-panel diagnostics view for recent action timeline, mapped-source health, and per-device planned-action/guard/result inspection.

### Changed
- Panel schema advanced to `5` so the frontend can consume richer diagnostics and explanation state.
- Integration version advanced to `0.1.6` for the first operator-grade diagnostics/explanation panel milestone.

## [0.1.5] - 2026-04-01

### Added
- Added explicit panel websocket mutations for `add_device` and `delete_device` so the sidebar app can manage the controllable device inventory directly.
- Added device-editor bootstrap payloads with configured device models, adapter choices, and Home Assistant entity suggestions for fixed and variable device templates.
- Added an in-panel device editor that supports add/edit/remove workflows for normal fixed and variable device onboarding.

### Changed
- Panel schema advanced to `4` and the Devices tab now treats structured device management as the primary operator path instead of deferring to raw JSON.
- Device inventory saves now validate through the existing backend parser before persisting updated options and reloading the integration.
- Integration version advanced to `0.1.5` for the first panel-side device management milestone.

## [0.1.4] - 2026-04-01

### Added
- Added panel source-mapping save support so operators can update the integration's mapped Home Assistant sensors directly from the sidebar app.
- Added source-mapping form inputs with sensor suggestions and refresh-interval editing in the Setup tab.

### Changed
- Panel schema advanced to `3` and Setup is now read/write for source mapping rather than diagnostics-only.
- Panel/backend flow now validates proposed source mappings before persisting them and reloads the config entry after a successful save.
- Integration version advanced to `0.1.4` for the first guided source-setup milestone.

## [0.1.3] - 2026-04-01

### Added
- Added panel websocket mutations for controller runtime settings and per-device operator overrides so the app can now perform common operator actions instead of staying read-only.
- Added in-panel controller controls for enable/disable, mode, target export, deadband, battery reserve, and reset-to-defaults.
- Added in-panel device controls for runtime enable/disable, priority override, and per-device override reset.

### Changed
- Panel schema advanced to `2` and the frontend now reflects saving/busy state during operator mutations.
- Panel docs now describe the current shell as read/write for runtime control while guided source and full device onboarding remain next.
- Integration version advanced to `0.1.3` for the first operator-mutation panel milestone.

## [0.1.2] - 2026-04-01

### Added
- Registered a real Home Assistant sidebar panel for Zero Net Export instead of leaving the app-first path as docs-only planning.
- Added a frontend panel bundle with tabbed shell sections for Overview, Setup, Devices, Diagnostics, and Settings.
- Added a normalized websocket payload at `zero_net_export/panel/get_state` so the panel can read structured overview, setup, device, and diagnostics state from the existing backend coordinator.

### Changed
- Integration startup now ensures the panel shell is registered alongside the existing backend coordinator/platform setup.
- README and implementation docs now reflect that the first panel shell milestone has been delivered.
- Integration version advanced to `0.1.2` for the panel-shell milestone.

### Fixed
- Removed the custom `icon` field from `manifest.json` as a likely contributor to wider Home Assistant UI/icon breakage during install.

## [0.1.1] - 2026-03-31

### Added
- `docs/NATIVE_OPERATOR_PLAN.md` defining the current native-operator direction (this later replaced the original app-first rebuild plan).
- `docs/NATIVE_SURFACE_TECHNICAL_DIRECTION.md` defining the current native-surface backend contract (this later replaced the original panel-oriented design doc).
- New project goals and implementation direction focused on a panel-style operator experience.
- A 4-hour supervision direction for finishing the project against the new app-first goals.
- Comprehensive UI goals covering setup, device management, operation, and diagnostics.
- Explicit architectural decision: panel app is now the chosen product path.

### Changed
- Design direction now explicitly rejects the original poor device configuration UX as a long-term operator workflow.
- Product documentation now treats the YAML dashboard as a transitional surface rather than the long-term primary UX.
- Implementation planning now includes stabilization plus panel-app rebuild phases.
- Integration version advanced toward `0.1.1` for stabilization work.

## [0.1.0] - 2026-03-31

### Added
- Release management structure for ongoing versioned maintenance.
- `CHANGELOG.md` to track user-visible changes by release.
- `docs/RELEASE_PROCESS.md` describing the release workflow.

### Added
- Initial Home Assistant custom integration scaffold for Zero Net Export.
- Config flow with source-of-truth validation.
- Device model for fixed and variable controllable loads.
- Guarded planner and executor for export-target control.
- Runtime safety controls including deadband, cooldown, min on/off, and battery reserve policy.
- Runtime-cap preemption support for managed devices.
- Diagnostics export, per-source diagnostics, action history, and daily reporting metrics.
- Lovelace dashboard scaffold and project documentation set.
- HACS metadata and MIT license.

### Notes
- `0.1.0` is the intended first public baseline, but it should only be treated as formally released once a matching git tag / GitHub release is created.
