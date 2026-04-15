# Zero Net Export Bug Tracker

This document is the single source of truth for active bugs, regressions, validation status, and bug closure in this project.

If another project document appears to disagree about whether a bug is still open, whether it was validated, or whether it is actually closed, follow this file.

## How to use this file

Use this file for all of the following:
- logging a newly discovered bug or regression
- recording how the bug shows up in the real product
- tracking whether the bug is only in the repo, only in the live install, or both
- recording the fix commit or release candidate that should contain the fix
- tracking validation status
- closing the bug only after the right evidence exists

This file is for real bug state, not vague ideas.

## Bug workflow

### 1. Post a bug
When a new bug is discovered, add an entry with:
- bug id
- title
- status
- severity
- area
- where seen
- current observed behavior
- expected behavior
- evidence
- suspected cause if known
- next action

### 2. Work a bug
While fixing a bug, keep the entry updated with:
- current owner/workstream if helpful
- relevant branch/commit
- what changed
- whether the bug is believed fixed only in repo or also validated live

### 3. Validate a bug
A bug is not considered truly fixed just because code changed.
Validation should state:
- where validation happened
- what exact evidence was checked
- what version/build/commit was involved
- whether the bug is resolved in live Home Assistant or only in repo state

### 4. Close a bug
Only close a bug when the fix has the right evidence for that bug.
If the bug affects live Home Assistant behavior, closure should normally require live validation, not just repo confidence.

## Status values

Use these values:
- `open` — bug is confirmed and not yet fixed
- `in_progress` — active fix work is underway
- `fixed_pending_validation` — a fix exists in repo or candidate build, but closure evidence is still missing
- `validated` — fix has been validated with the right evidence
- `closed` — bug is complete and can be treated as done
- `deferred` — known but intentionally not the current priority

## Severity values

Use these values:
- `critical` — blocks load, setup, or the core product path
- `high` — major user-visible breakage or strong regression
- `medium` — important but not fully blocking
- `low` — minor issue, cleanup, or polish-level defect

## Bug areas

Suggested area labels:
- `runtime`
- `config_flow`
- `managed_devices`
- `source_mapping`
- `controls`
- `sensors`
- `diagnostics`
- `release`
- `docs`
- `process`

## Current active bugs

## ZNE-001 — Repairs platform contract breaks integration recovery
- **status:** `validated`
- **severity:** `critical`
- **area:** `runtime`
- **where seen:** live Home Assistant after `0.1.82` deploy/restart
- **current observed behavior:** Zero Net Export entities restore as unavailable, and logs show `HomeAssistantError: Invalid repairs platform <module 'custom_components.zero_net_export.repairs' ...>`
- **expected behavior:** Repairs platform loads cleanly and the integration recovers with live entities instead of staying restored/unavailable
- **evidence:** live HA logs after the `0.1.82` restart; affected entities included `sensor.zero_net_export_status`, `sensor.zero_net_export_command_center_status`, `sensor.zero_net_export_stale_source_count`, `binary_sensor.zero_net_export_safe_mode`, and `sensor.zero_net_export_reason`
- **suspected cause:** missing Repairs flow contract in `custom_components/zero_net_export/repairs.py`
- **repo fix:** `ad44fc1` — `fix: add repairs platform entry flow`
- **validation status:** validated against the live `0.1.83` deploy on 2026-04-15. Fresh post-restart log review no longer showed `Invalid repairs platform`, and the earlier `build_release_info()` setup-retry traceback also did not reappear. This clears the original hard-load failure even though broader entity recovery is still unresolved.
- **next action:** keep ZNE-002 open as the follow-on runtime recovery bug, because the hard repairs-platform failure is gone but the integration/entities still are not fully present live

## ZNE-002 — Main Zero Net Export entities stay restored/unavailable after restart
- **status:** `fixed_pending_validation`
- **severity:** `critical`
- **area:** `runtime`
- **where seen:** live Home Assistant after the `0.1.82` deploy/restart, and still unresolved after the exact `0.1.83` repo build was deployed to Home Assistant
- **current observed behavior:** earlier live inspection showed no active `zero_net_export` config entry and no controller device/entities after restart. That exact condition is still not present in the current live install: the config entry exists again and core Zero Net Export entities are live through the API, but another explicit restart/reload proof is still missing, so restart persistence is not yet re-validated.
- **expected behavior:** the live Home Assistant install should retain or recreate an active `zero_net_export` config entry so the controller device and core runtime entities load normally after restart
- **evidence:** earlier live SSH/API inspection showed `0` `zero_net_export` config entries, `0` Zero Net Export devices, and only `update.zero_net_export_update` visible. In this run, documented HA SSH access on `root@192.168.86.200:2222` succeeded again and direct inspection of `/config/.storage/core.config_entries` still shows one `zero_net_export` entry (`01KP8MW539MQ724BBFZX2EF6S2`, title `Zero Net Export`, created `2026-04-15T13:21:46.601855+00:00`). Direct Home Assistant API inspection in this run also returns 145 live `zero_net_export` entities, including `sensor.zero_net_export_status`, `sensor.zero_net_export_command_center_status`, `sensor.zero_net_export_unmanaged_candidate_overview`, and `button.zero_net_export_show_fleet_console`.
- **suspected cause:** the earlier missing-config-entry state was real, but the live system has since recovered past that blocker, likely via successful Add Integration. The remaining runtime/configure failures are now narrower follow-on bugs rather than absence of the entry itself.
- **validation status:** improved materially but not yet closed. The exact missing-config-entry condition is no longer reproducible live and the entity surface is back, but restart persistence still needs re-validation before this bug can be closed confidently.
- **next action:** keep this bug at `fixed_pending_validation`, then re-test restart/reload persistence after the current exact-build drift is cleared so the entry/device/entity set is proven stable across another live restart

## ZNE-003 — Requested native UI outcome still not visibly delivered
- **status:** `fixed_pending_validation`
- **severity:** `high`
- **area:** `managed_devices`
- **where seen:** product-level review against live/native UI expectations
- **current observed behavior:** some UI scaffolding exists, but the requested visible native UI outcome still does not feel complete to James
- **expected behavior:** the product visibly delivers:
  1. clear managed vs unmanaged device experience
  2. clear promote / vet / review flow
  3. clear separation of Controls / Sensors / Managed Devices / Diagnostics
- **evidence:** direct user feedback plus repo/design audit captured in `docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md`; repo inspection on 2026-04-15 also confirmed the managed-fleet workspace sensors and fleet-console helper were still marked diagnostic, which buried Managed Devices review under diagnostic-style entity presentation instead of treating it as a first-class fleet workspace; later same-day repo inspection also found the new managed/unmanaged and promotion-flow copy had landed in `custom_components/zero_net_export/strings.json` but not in `custom_components/zero_net_export/translations/en.json`, leaving the shipped English UI text behind the intended native flow wording; additional repo inspection in this run confirmed the Configure -> Managed Devices snapshot was still deriving `usable` counts from parse-only config data, so fleets with healthy runtime devices still displayed `usable: 0` and the edit/remove selectors hid real runtime readiness behind config-only labels; further repo inspection in this run confirmed the native integration device page still lacked a dedicated first-class managed-device deep-review action, leaving per-device runtime review implicit across scattered entities rather than a single obvious native handoff; repo inspection in this run also confirmed install-provenance uncertainty was still only exposed as secondary Diagnostics detail instead of a top-level command-center alert/recommended-path blocker, which weakened the intended global-plus-local problem-signal model; repo inspection after `a67acdc` also confirmed the device-page deep-review path has now advanced again with per-device managed review buttons for each configured load, so the source-of-truth bug state needed to be refreshed to match the shipped repo candidate before the next release-approval handoff; repo plus live-API corpus inspection in this run also confirmed the unmanaged promotion shortlist still needed stronger filtering because replaying the current Home Assistant entity set through repo candidate discovery was still surfacing obvious media-feature toggles such as speech enhancement/subwoofer controls and even `switch.zero_net_export_enabled` as promotable Managed Devices candidates
- **suspected cause:** implementation is still too scaffold/text-heavy and not yet sufficiently productized in live HA, translation artifacts can drift when native flow copy changes land without the matching `translations/en.json` update, some Configure fleet summaries were still built from parsed config inventory without overlaying live `device_details` readiness/status, the device-page deep-review path was still implied rather than surfaced as its own obvious action, install-provenance blockers were not yet treated as first-class command-center alerts even though exact-build trust is part of the operator workflow, and the shared unmanaged-candidate heuristics were still permissive enough to treat internal Zero Net Export controls plus media-feature toggles as credible promotion targets
- **repo fix:** `2603de9`, `f804286`, `827530c`, `5c4ff5c`, `0acb62e`, `96fe3d2`, `28c1834`, `45c61ec`, `55c68bd`, `e9e0189`, `a0046ee`, `7cd6c35`, `b6ddcd2`, `c41929c`, `23f2e9c`, `8ad2e88`, `9e25578`, `469825e`, `f45618c`, `a67acdc` — promote managed-fleet workspace sensors and the fleet-console helper out of diagnostics-only presentation, sync the updated managed-device flow copy into `translations/en.json` with a regression test that keeps the English translation file aligned to `strings.json`, route candidate discovery through a shared ranking helper so Managed Devices surfaces recommend stronger promotion targets before helper-style fallbacks, overlay live runtime `device_details` into Configure fleet summaries so Managed Devices shows real usable/status state instead of config-only placeholders, order the Managed Devices fleet-review, edit, and remove selectors by actionable runtime state so enabled-and-usable devices surface ahead of blocked or disabled entries while the fleet summary now shows usable counts explicitly, add a dedicated native device-page `Show managed-device review` action that summarizes per-device runtime status, guards, planned actions, and the deep-review handoff from the Zero Net Export device page, emit a native persistent-notification success landing after managed-device promote/edit/remove or enablement-review saves so the operator gets an explicit what-changed plus next-step handoff instead of a cold form exit, extend that native managed-device review with an unmanaged-candidate backlog snapshot plus top promotion targets, fix the structured command-center summary plus shipped English translation so the new control-board copy does not crash on sparse runtime state or drift behind `strings.json`, keep unmanaged-candidate fit/warning guidance consistent across candidate discovery, candidate review, and the native managed-device review action, upgrade the primary fleet-console device-page action so it also shows managed/unmanaged snapshots, top candidate fit and warnings, runtime-ranked managed-device detail, and an explicit promotion handoff back into Configure -> Managed Devices, make the device-page command-center guide itself use the shared full guide text so the native command-center handoff includes the recommended-section reason, explicit section ownership, common operator paths, blocker detail, and managed-device deep-review path instead of a shorter partial summary, make the command-center headline decision-first while expanding the top Energy state board with battery charge and discharge telemetry so the opening native console reads more like an operator surface than a raw status dump, keep the device-page command-center guide itself in the main device surface instead of burying that operator handoff under diagnostics-only categorization, surface per-device guard state, planned action, and last action status directly in the Configure Managed Devices fleet rows while the fleet summary now calls out blocked devices and active planned actions at a glance, add an explicit balanced candidate-review block so promote / vet / review now spells out control suitability, safety/confidence, and operational value before the operator saves into Managed Devices, add a top-level native alert summary to the Configure command center and device-path guide so source blockers, managed-device repair needs, and runtime-readiness issues show up globally before the local section detail, promote install-provenance refresh/version-mismatch blockers into that same command-center alert and recommended-path lane instead of burying exact-build trust only in Diagnostics detail, demote obvious software-, service-, or media-style toggles like crossfade or AdGuard controls below more appliance-like candidates so Managed Devices surfaces recommend more credible first promotion targets, add per-device managed review buttons on the Zero Net Export device page so each configured load now has its own native deep-review entry alongside the shared fleet review path, and prefill empty required separate-grid source fields in Configure -> Sensors from strong live candidates so operators land on likely solar/grid mappings instead of a blank required form.
- **what changed:** repo-side UI cleanup promotes the managed-fleet workspace sensors out of `EntityCategory.DIAGNOSTIC`, the fleet-console button is no longer diagnostic-only, the shipped English translation now includes the managed/unmanaged snapshots and explicit promotion-path wording added to the source strings, `tests/test_translation_sync.py` now fails if `translations/en.json` drifts from `strings.json`, the Configure Managed Devices screen, fleet console, and managed-device workspace sensors now share one ranked unmanaged-candidate order so the top candidate and shortlist no longer default to alphabetical entity order, the Managed Devices Configure, fleet-review, edit, and remove screens now overlay live runtime `device_details` so usable counts, enabled-state ordering, and per-device labels reflect actual runtime readiness/status instead of always reporting config-only `usable: 0`, the native fleet workspace sorts managed-device selectors with enabled-and-usable devices first while keeping blocked/disabled devices lower in the list and adding usable counts to the top fleet summary line, the device page now exposes a first-class `Show managed-device review` action plus diagnostics metadata that advertises that deeper review entry point, managed-device save flows now land on a native success notification with the next Managed Devices or deeper review path, the managed-device review now includes an unmanaged-candidate snapshot plus top promotion targets, the structured command-center control board now stays stable when runtime fields are absent while shipping the matching English command-center copy from `strings.json`, unmanaged-candidate fit and warning signals are aligned behind one shared assessment helper, Configure candidate snapshots plus the full unmanaged pick list now show likely usefulness and the top warning inline, the fleet-console device-page action now matches that native fleet workspace, `b6ddcd2` keeps `Show command center guide` in the main device surface instead of diagnostics-only categorization, `23f2e9c` makes the Configure Managed Devices fleet rows more operational by surfacing per-device guard state, planned action, and last action status directly in the managed-device labels while the fleet summary now calls out blocked devices and active planned actions at a glance, the candidate vetting screen now uses a balanced native review that explicitly calls out control suitability, safety/confidence, and operational value before promotion, the command center now has a concise top-level alert summary plus shared device-path command-center/support text so source blockers, managed-device repair needs, and runtime-readiness issues show up globally before the local section detail, install-provenance refresh/version-mismatch blockers now land in that same top-level alert lane so the command center recommends Diagnostics and the exact-build repair step instead of burying install trust only in secondary support text, this run further hardens candidate discovery so internal `zero_net_export_*` control entities are never offered as unmanaged promotion targets while media-feature toggles like speech enhancement, subwoofer, bass, treble, balance, audio-delay, and `_none` service wrappers are pushed below more appliance-like outlets, heaters, chargers, plugs, and relays in the native promotion shortlist, `a67acdc` now adds per-device managed review buttons so the native device page offers a direct deep-review action for each configured load instead of forcing operators back through the shared fleet review alone, and this run also makes Configure -> Sensors prefill empty required separate-grid mappings when live scoring finds a clear best candidate so source repair starts from likely solar/grid entities instead of all-empty required selectors.
- **validation status:** repo-side UI changes remain covered by `python3 -m unittest discover -s tests`, which passed again in this run, including focused regression coverage in `tests/test_candidate_utils.py` for the balanced candidate-review summaries, the internal-entity exclusion guard, and the new media-feature demotion cases, the top-alert command-center coverage in `tests/test_command_center_summary.py`, the install-provenance alert/recommended-section regression in `tests/test_command_center_summary.py`, plus the existing command-center device action coverage staying out of `EntityCategory.DIAGNOSTIC`, the managed-device runtime label assertions in `tests/test_config_flow_device_runtime_overlay.py`, the new source-default ranking coverage in `tests/test_config_flow_device_runtime_overlay.py`, and the new per-device button coverage in `tests/test_button_entity_categories.py`. This run also replayed the current live Home Assistant state corpus through the updated repo source-candidate logic over the documented API path, which identifies clear separate-mode defaults for the currently blocked install such as `sensor.x1_p6k_us_s_solar_power`, `sensor.system_rome_yield_total`, `sensor.x1_p6k_us_s_grid_import`, `sensor.x1_p6k_us_s_grid_export`, `sensor.shellypro3em_0cb815fc6154_total_active_energy`, and `sensor.shellypro3em_0cb815fc6154_total_active_returned_energy` instead of leaving the required source form blank. Install drift remains: `python3 scripts/validate_install_fingerprint.py /config/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222` still reports `overall_match=false` against the shipped-component candidate, so this source-prefill improvement is repo-valid but not yet live-validated in Home Assistant.
- **next action:** keep this bug in `fixed_pending_validation`, ask James directly for release approval to redeploy the exact current repo candidate, rerun fingerprint validation until it reports `overall_match=true`, then re-check the managed/unmanaged workspace, command-center/device-path visibility, and four-bucket UI outcome against the exact installed `0.1.83` build

## ZNE-005 — `build_release_info()` missing required `current_version` argument
- **status:** `validated`
- **severity:** `critical`
- **area:** `runtime`
- **where seen:** live Home Assistant integration page during setup/retry
- **current observed behavior:** historical bug. Earlier live Home Assistant runs showed `Failed setup, will retry: build_release_info() missing 1 required positional argument: 'current_version'`.
- **expected behavior:** Zero Net Export setup should complete without this runtime error
- **evidence:** user screenshot of the Home Assistant integration page showing the exact setup error; repo/HA SSH inspection on 2026-04-15 confirmed the live `0.1.81` install still had `coordinator.py` calling `build_release_info(include_changelog=False)` at line 223 without the required version argument. In this run, documented HA SSH/API access confirmed the live install now has one active `zero_net_export` config entry and 145 live Zero Net Export entities, `scripts/validate_install_fingerprint.py` shows `coordinator.py` matches the repo candidate exactly, and fresh `ha core logs` review no longer shows the earlier `build_release_info()` missing-argument retry.
- **suspected cause:** coordinator release-update metadata called `build_release_info()` without the required `current_version`, causing setup to fail while building validation details
- **repo fix:** `48a9d45` — pass `INTEGRATION_VERSION` from `coordinator.py` into `build_release_info()` and cover the call contract with a coordinator unit test; this run adds `tests/test_release_update_details.py` so the release-update path has its own focused regression coverage for the missing-argument contract
- **validation status:** repo-side fix remains covered by `python3 -m unittest tests.test_source_freshness_probes tests.test_release_info_install_guidance tests.test_release_update_details` plus `python3 -m py_compile custom_components/zero_net_export/coordinator.py`. Live validation is now good enough for this bug specifically: the fixed `coordinator.py` is present in the live install, the integration has an active config entry again, and the earlier missing-argument setup retry is no longer present in current log review.
- **next action:** no further action for this specific bug beyond keeping future coordinator/release-info changes under regression coverage

## ZNE-026 — Integration overview/device page still shows stale 0.1.83 version after 0.1.84 install
- **status:** `fixed_pending_validation`
- **severity:** `high`
- **area:** `release`
- **where seen:** live Home Assistant UI after `0.1.84` deploy
- **current observed behavior:** the integration overview and device info screenshots still show `Version 0.1.83` / `Firmware: 0.1.83` even though the release and deploy were executed as `0.1.84`
- **expected behavior:** the Home Assistant integration and device surfaces should show the currently installed `0.1.84` version, not the previous release
- **evidence:** user screenshots on 2026-04-16 show the integration header and device info card both rendering `Version 0.1.83` / `Firmware: 0.1.83` after the `0.1.84` release/deploy. Earlier live shell checks in the same run showed conflicting file states, including one post-release command still reporting remote manifest `0.1.83`, so the stale-version UI is consistent with unresolved live install/version-fidelity drift. In this run, the documented HA SSH/API path worked again: `python3 scripts/validate_install_fingerprint.py /config/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222` still reports `overall_match=false`, and one of the current mismatches is `custom_components/zero_net_export/entity.py`, which means the live install is still missing the later repo-side device-surface version fix.
- **suspected cause:** the original stale version was partly a real live mixed-build problem, and repo inspection in this run confirmed the bug-tracker state had drifted behind the shipped candidate because `custom_components/zero_net_export/entity.py` now reads the packaged `manifest.json` version for the Home Assistant device surface instead of blindly using an older imported constant.
- **repo fix:** `057fcf5` — make the device surface version read the packaged `manifest.json` so Home Assistant device firmware/version labels follow the installed component tree, with regression coverage in `tests/test_device_surface_version.py`
- **validation status:** repo-side fix is now present and covered by `python3 -m unittest tests.test_device_surface_version -q`, but live Home Assistant validation is still pending because the exact current repo candidate is not installed yet. This bug should not stay `open` in the tracker because a repo fix now exists; the remaining work is redeploy plus post-install device-surface verification.
- **next action:** redeploy the exact current `0.1.83` repo candidate, rerun fingerprint validation until `overall_match=true`, then confirm the integration overview and Zero Net Export device page both read the installed package version from the deployed manifest

## ZNE-032 — Release summary incorrectly reports a rollback as a normal update
- **status:** `fixed_pending_validation`
- **severity:** `medium`
- **area:** `release`
- **where seen:** live Home Assistant `sensor.zero_net_export_release_summary` in this run
- **current observed behavior:** the native release summary currently says `Updated from 0.1.84 to 0.1.83`, which reads like a normal upgrade even though the version moved backwards after the repo working-version revert to the documented `0.1.83` UI target
- **expected behavior:** when the recorded previous version is higher than the current installed version, the native release summary should flag that as a rollback or mixed version history instead of claiming a normal update
- **evidence:** in this run, the documented HA API path returned `sensor.zero_net_export_release_summary` with `state: Release notes deferred until diagnostics/support surfaces request them.` and `summary: Updated from 0.1.84 to 0.1.83. ...`, while the same run's repo/source-of-truth inspection confirmed `custom_components/zero_net_export/manifest.json` is intentionally back on `0.1.83`
- **suspected cause:** `_release_update_details()` treated any version change as an upgrade and never compared version direction, so a rollback or version-history correction produced misleading release wording
- **repo fix:** this run updates `custom_components/zero_net_export/coordinator.py` so release summaries compare previous versus current version direction and call out rollback or mixed version history explicitly when the version goes backwards; `tests/test_release_update_details.py` now covers both rollback and normal upgrade wording
- **validation status:** repo-side fix implemented in this run and covered by `python3 -m unittest tests.test_release_update_details -q`. Live Home Assistant validation is still pending on the next exact-build redeploy because the current install fingerprint remains behind repo HEAD.
- **next action:** redeploy the exact current repo candidate, rerun fingerprint validation until `overall_match=true`, then confirm `sensor.zero_net_export_release_summary` no longer says `Updated from 0.1.84 to 0.1.83` and instead flags the rollback/version-history mismatch clearly

## ZNE-027 — Command center still lets diagnostics/release plumbing dominate the primary operator surface
- **status:** `fixed_pending_validation`
- **severity:** `high`
- **area:** `diagnostics`
- **where seen:** live Home Assistant command-center modal after `0.1.84` deploy
- **current observed behavior:** the live `0.1.84` command-center modal still shows dense release-fingerprint/install-validation/debug text and long repair-path prose high in the modal, so diagnostics/support detail is visually carrying too much of the primary operator experience.
- **expected behavior:** per `docs/UI_DESIGN.md`, Configure should remain the primary operator workspace with the decision summary, grouped control board, and clear jump-off entries, while Diagnostics stays visible but secondary rather than dominating the landing surface.
- **evidence:** user screenshot on 2026-04-16 shows the modal headed `Zero Net Export command center` with install-fingerprint details and long repair-path prose before the main setup/operator sections, which matched the repo strings that embedded an `Installed package details:` block directly in the primary command-center description. This run updates that shipped options-flow copy in `custom_components/zero_net_export/strings.json` and `custom_components/zero_net_export/translations/en.json` so the init modal is explicitly framed as a basic setup and current-operating-picture surface, keeps the structured control board, keeps source/control/runtime summaries, and moves managed-device and deep install-validation work into a trailing `Not here` handoff instead of leading with diagnostics plumbing.
- **suspected cause:** the options-flow init description was still mixing install validation, diagnostics, and operational troubleshooting directly into the primary landing description instead of demoting that material behind Diagnostics/support paths and lighter alert summaries.
- **repo fix:** this run refocuses the command-center init modal copy in `custom_components/zero_net_export/strings.json` and `custom_components/zero_net_export/translations/en.json`, and adds `tests/test_command_center_modal_copy.py` so the primary modal cannot regress back to `Installed package details` or the older release-plumbing-heavy wording without test failures.
- **validation status:** repo-side copy fix implemented in this run and verified with `python3 -m unittest tests.test_command_center_modal_copy tests.test_translation_sync -q` plus `python3 -m unittest discover -s tests -q`. Live Home Assistant validation is still pending on the next exact-build redeploy.
- **next action:** redeploy the current repo candidate, then confirm the command-center modal now reads as a setup-first operator surface with diagnostics/install-validation detail demoted behind the Diagnostics path instead of leading the modal

## ZNE-028 — Device page still lacks the managed-device structure required by the UI design
- **status:** `open`
- **severity:** `high`
- **area:** `managed_devices`
- **where seen:** live Home Assistant device page after `0.1.84` deploy
- **current observed behavior:** the device page is still mostly generic cards plus buttons/sensors, with little visible managed-device structure. Managed-device workflow is not yet clearly centered on the device info page as the user requested.
- **expected behavior:** the device page should visibly evolve toward the `docs/UI_DESIGN.md` target, with managed-device structure and review paths feeling first-class on the native device page rather than reading mainly as generic controls plus helper buttons.
- **evidence:** user screenshot on 2026-04-16 shows the device page still dominated by generic Controls/Sensors/Activity cards and button entities like `Show fleet console` / `Show managed-device review`, while the user explicitly stated that managed devices should be on the device info page and that the page has not really progressed enough toward the design.
- **suspected cause:** managed-device UX remains implemented mainly as button-triggered review flows and supporting entities rather than as a clearly shaped native device-page experience aligned with the design doc.
- **validation status:** confirmed live, not fixed
- **next action:** move the next visible UI work toward stronger managed-device structure on the device page instead of relying mainly on button-triggered helper flows

## ZNE-029 — Runtime attention notification is overloaded and poorly formatted
- **status:** `fixed_pending_validation`
- **severity:** `medium`
- **area:** `ui`
- **where seen:** live Home Assistant runtime attention notification/modal on 2026-04-16
- **current observed behavior:** the `Runtime attention needed` surface is a dense wall of text with weak visual hierarchy. The headings are not visually separated enough, spacing is poor, and the content is too long and repetitive, making the error harder to act on quickly.
- **expected behavior:** the runtime attention surface should use tighter content, clearer grouping, and stronger heading emphasis so the operator can scan the problem, cause, and next step quickly
- **evidence:** user screenshot on 2026-04-16 shows the runtime attention modal with long repeated validation details, weak spacing, and overloaded instructions. User explicitly requested bolded headings, better spacing, and tighter content.
- **suspected cause:** the current runtime/support notification text is generated as a long plain-text dump of support fields rather than being edited into a compact operator-facing alert format
- **repo fix:** this run tightens the Repairs/runtime-attention notification copy in `custom_components/zero_net_export/strings.json` and `custom_components/zero_net_export/translations/en.json`, replacing the long paragraph-style dump with short `Now`, `Mapped-source blockers`, `Do next`, and `Open` sections so the primary signal and repair path scan cleanly in Home Assistant's native modal
- **validation status:** repo-side copy fix implemented and covered in this run by `python3 -m unittest tests.test_repairs_copy tests.test_translation_sync -q` plus `python3 -m unittest discover -s tests -q`. Live Home Assistant validation is still pending on the next exact-build redeploy.
- **next action:** redeploy the current repo candidate, then confirm the `Runtime attention needed` modal now reads as a compact sectioned alert instead of a wall of text

## ZNE-030 — Setup-finished/setup-warning notification is also overloaded and poorly formatted
- **status:** `fixed_pending_validation`
- **severity:** `medium`
- **area:** `ui`
- **where seen:** live Home Assistant `Finish native Zero Net Export setup` notification/modal on 2026-04-16
- **current observed behavior:** the setup notification is still a dense block of text with weak visual hierarchy, long repeated prose, and too much instruction text packed into a single alert surface
- **expected behavior:** the setup notification should be short, structured, and easy to scan, with stronger heading separation and a tighter summary/next-step layout
- **evidence:** user screenshot on 2026-04-16 shows the `Finish native Zero Net Export setup` warning with long repeated setup/selector-workaround prose. User explicitly called it poorly formatted in the same way as the runtime-attention notification.
- **suspected cause:** the setup guidance text is still generated as a long support-style narrative instead of a compact notification-specific layout
- **repo fix:** this run also tightens the `Finish native Zero Net Export setup` Repairs copy in `custom_components/zero_net_export/strings.json` and `custom_components/zero_net_export/translations/en.json`, reshaping it into short `Status`, `Do next`, and `Open` blocks so the native setup warning points operators at Configure without the earlier prose dump
- **validation status:** repo-side copy fix implemented and covered in this run by `python3 -m unittest tests.test_repairs_copy tests.test_translation_sync -q` plus `python3 -m unittest discover -s tests -q`. Live Home Assistant validation is still pending on the next exact-build redeploy.
- **next action:** redeploy the current repo candidate, then confirm the `Finish native Zero Net Export setup` warning renders as a concise sectioned checklist instead of a dense paragraph

## ZNE-031 — Source issue-count sensors are generating HA statistics/state-class cleanup notifications
- **status:** `fixed_pending_validation`
- **severity:** `high`
- **area:** `sensors`
- **where seen:** live Home Assistant notifications on 2026-04-16
- **current observed behavior:** Home Assistant is showing more than 10 cleanup/statistics warnings such as `The entity no longer has a state class` for Zero Net Export issue-count sensors like `sensor.zero_net_export_solar_power_issue_count`
- **expected behavior:** these sensors should not create a flood of HA statistics-cleanup warnings. The issue-count sensors should keep a stable numeric state-class posture so Home Assistant does not keep creating and then invalidating statistics metadata for them.
- **evidence:** user screenshot on 2026-04-16 shows an HA dialog for `sensor.zero_net_export_solar_power_issue_count` stating long-term statistics were previously generated but the entity no longer has a supported state class. User also reported there are over 10 similar notifications in Home Assistant.
- **suspected cause:** the diagnostic issue-count entities are still present with the same entity ids, but the current `ZeroNetExportSourceIssueCountSensor` definition did not set an explicit state class, so Home Assistant treats the historical statistics metadata as a cleanup problem and keeps surfacing warning notifications.
- **repo fix:** this run restores a stable explicit numeric posture by setting `ZeroNetExportSourceIssueCountSensor._attr_state_class = SensorStateClass.MEASUREMENT` in `custom_components/zero_net_export/sensor.py`, with focused regression coverage in `tests/test_sensor_issue_count_state_class.py`.
- **validation status:** repo-side fix implemented in this run and verified with `python3 -m unittest tests.test_sensor_issue_count_state_class -q` plus `python3 -m unittest discover -s tests -q`. Live Home Assistant validation is still pending on the next exact-build redeploy and post-restart notification review.
- **next action:** redeploy the current repo candidate, restart Home Assistant, then confirm the statistics/state-class cleanup notifications for the `*_issue_count` sensors stop reappearing

## ZNE-014 — Post-install log review confirms the live 0.1.83 install is still not healthy
- **status:** `fixed_pending_validation`
- **severity:** `high`
- **area:** `runtime`
- **where seen:** live Home Assistant `0.1.83` after user install and manual log review request
- **current observed behavior:** the earlier broken-config-flow and missing-entity install state is no longer the current live symptom. The live system still appears materially healthier than before, with no fresh `zero_net_export`-specific log lines in the latest `ha core logs -n 220 | grep -i zero_net_export` pass from this run, but the install is still a mixed older build so exact-build trust is not back yet.
- **expected behavior:** after install, Zero Net Export should load cleanly, allow Add Integration, avoid integration-specific live errors in Home Assistant logs, and match the exact repo candidate under review
- **evidence:** live HA review on 2026-04-15 originally confirmed remote manifest `0.1.83` plus `homeassistant.config_entries` errors and the missing-config-entry/orphaned-entity condition tracked elsewhere in this file. In this run, documented HA SSH access on `root@192.168.86.200:2222` succeeded, `ha core logs -n 220 | grep -i zero_net_export` returned no current Zero Net Export lines, and `scripts/validate_install_fingerprint.py /config/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222` still reports `overall_match=false`, so the install-health blocker is now primarily exact-build drift rather than a freshly visible integration traceback.
- **suspected cause:** the original install-health failure overlapped ZNE-002 and ZNE-011; the remaining live-health concern now overlaps ZNE-020 and ZNE-022 because the installed component tree is still behind the repo candidate
- **validation status:** materially improved again in this run. Current live logs are quiet enough that the old setup failure no longer looks like the immediate blocker, but this umbrella bug should stay open until the exact repo candidate is redeployed and a post-restart log review shows the live install is both healthy and fingerprint-aligned.
- **next action:** treat exact-build redeploy and post-restart validation under ZNE-022 as the real remaining work, then close this umbrella bug once the live install matches the repo candidate and the stale `release_info.py` warning is gone

## ZNE-011 — Config flow cannot load because backup folder names pollute Home Assistant module discovery
- **status:** `fixed_pending_validation`
- **severity:** `critical`
- **area:** `config_flow`
- **where seen:** live Home Assistant `0.1.83` install while adding the integration
- **current observed behavior:** the Add Integration flow fails with `Config flow could not be loaded: {"message":"Invalid handler specified"}` and the HA log shows `Error occurred loading flow for integration zero_net_export: No module named 'custom_components.zero_net_export.backup_openclaw_20260415_220427'`
- **expected behavior:** selecting Zero Net Export in Add Integration should load `custom_components.zero_net_export.config_flow` normally and open the setup flow
- **evidence:** user screenshots from 2026-04-15 show the exact popup and log detail. Live HA inspection confirmed multiple backup directories still exist under `/config/custom_components/`, including `zero_net_export.backup_openclaw_20260415_220427` and `zero_net_export.backup_openclaw_20260415_220522`, matching the module path mentioned in the traceback.
- **suspected cause:** the deploy backup strategy leaves backup directories under `/config/custom_components/` with names that still begin with `zero_net_export`, polluting Home Assistant custom-component discovery and causing config-flow import resolution to point at a backup pseudo-module path instead of the real integration package
- **repo fix:** this run updates `scripts/deploy_exact_repo_build.py` so default backups are now written outside Home Assistant discovery under `<config>/.openclaw_backups/custom_components/zero_net_export.backup-<timestamp>` instead of as sibling directories inside `/config/custom_components/`; `tests/test_install_helper_scripts.py` now covers the new backup path and verifies the copied backup stays outside the discovery root. This run also adds `scripts/clean_legacy_discovery_artifacts.py` plus extra `tests/test_install_helper_scripts.py` coverage so older `zero_net_export.backup_*` directories and matching stale `zero_net_export.*.pyc` artifacts can be detected and removed safely from an existing Home Assistant `custom_components` tree.
- **validation status:** repo-side fix and cleanup helper are implemented and verified with `python3 -m unittest tests.test_install_helper_scripts` and `python3 -m unittest discover -s tests`. Live state changed materially in this run: documented HA SSH inspection now shows `/config/custom_components` no longer contains any `zero_net_export.backup*` sibling directories, so the earlier discovery-pollution evidence is gone. The user later got past Add Integration and reached the integration card, which is another sign that the original backup-module import failure is likely cleared. However, Configure is still failing with a different 500 error, so this bug remains `fixed_pending_validation` rather than closed until the whole config-flow path is revalidated cleanly.
- **next action:** treat the original backup-discovery root cause as likely mitigated, and focus immediate debugging on the new Configure 500 error and setup traceback. Once that new failure is fixed, re-verify Add Integration and Configure end to end before closing this bug

## ZNE-015 — Configure gear action fails with 500 because runtime setup still crashes on missing `build_source_attention_brief`
- **status:** `validated`
- **severity:** `critical`
- **area:** `config_flow`
- **where seen:** live Home Assistant `0.1.83` after the user successfully added the integration and then clicked the gear/configure icon
- **current observed behavior:** the integration card shows `Failed to set up`, and clicking the gear/configure icon raises `Config flow could not be loaded: 500 Internal Server Error Server got itself in trouble`
- **expected behavior:** once the integration is added, clicking Configure should open the native Zero Net Export options/config flow instead of surfacing a server-side 500
- **evidence:** user screenshot from 2026-04-15 shows the integration card in Home Assistant with `Failed to set up` and the exact 500 popup after clicking the gear icon. Live HA logs from the same run show the real traceback: `ImportError: cannot import name 'build_source_attention_brief' from 'custom_components.zero_net_export.native_support'` while loading `custom_components.zero_net_export.sensor`, followed by `homeassistant.config_entries` setup failure for the Zero Net Export entry and an aiohttp server error path through `config_flow.py`.
- **suspected cause:** repo/runtime drift left `sensor.py` importing `build_source_attention_brief` even though that helper no longer existed in `native_support.py`, so entry setup fails and the later Configure request surfaces as a generic 500
- **repo fix:** this run restores `build_source_attention_brief(...)` in `custom_components/zero_net_export/native_support.py` and adds focused regression coverage in `tests/test_source_attention_brief.py`; commit `37777cd` — `fix: restore source attention brief helper`
- **validation status:** repo-side fix implemented and earlier verified with `python3 -m unittest tests.test_source_attention_brief tests.test_install_helper_scripts tests.test_command_center_summary tests.test_release_update_details tests.test_source_freshness_probes tests.test_release_info_install_guidance -q` and `python3 -m py_compile custom_components/zero_net_export/native_support.py custom_components/zero_net_export/sensor.py`. Live validation changed materially in this run: documented HA SSH access now shows an active `zero_net_export` config entry and live Zero Net Export sensors are updating often enough to emit new candidate-shortlist state-length errors, which would not happen if `sensor.py` were still failing to import `build_source_attention_brief`. The Configure path still fails, but with a different traceback (`KeyError: 'source_repair_step'`) rather than the old import error.
- **next action:** treat the original missing-helper crash as validated fixed, and continue the current Configure 500 work under ZNE-018 instead of keeping this older root cause open

## ZNE-018 — Configure init crashes with `KeyError: 'source_repair_step'`
- **status:** `fixed_pending_validation`
- **severity:** `high`
- **area:** `config_flow`
- **where seen:** live Home Assistant `0.1.83` after re-adding the integration and opening Configure
- **current observed behavior:** clicking Configure still raises a server-side 500 because `async_step_init` expects `command_center["source_repair_step"]`, but `build_native_command_center_summary(...)` does not always populate that key
- **expected behavior:** Configure should open even when the command-center summary omits optional source-repair detail; the options flow should fall back to a generic source-repair step instead of crashing
- **evidence:** documented HA SSH access on `root@192.168.86.200:2222` succeeded in this run, and `ha core logs -n 240` shows `File "/config/custom_components/zero_net_export/config_flow.py", line 1431, in async_step_init` followed by `"source_repair_step": command_center["source_repair_step"],` and `KeyError: 'source_repair_step'`
- **suspected cause:** the options-flow handoff assumed the command-center summary always carried `source_repair_step`, but some runtime states only emit `next_action_summary` and related fields
- **repo fix:** `209665e` — this run updates `custom_components/zero_net_export/native_support.py` so the command-center summary always emits `source_repair_step`, and also hardens `custom_components/zero_net_export/config_flow.py` with a fallback `build_source_repair_step()` default if the key is ever absent again
- **validation status:** repo-side fix implemented and covered by `python3 -m unittest tests.test_command_center_summary -q`, `python3 -m unittest discover -s tests -q`, and `python3 -m py_compile custom_components/zero_net_export/config_flow.py custom_components/zero_net_export/native_support.py`. In this run, the exact `209665e` repo build was also copied to `/config/custom_components/zero_net_export`, `scripts/validate_install_fingerprint.py /config/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222` returned `overall_match=true`, and Home Assistant core was restarted cleanly. However, Configure itself still needs a post-deploy click test before this bug can be closed.
- **next action:** re-open Configure in live Home Assistant and confirm the 500 is gone on the deployed `209665e` build

## ZNE-019 — Candidate overview and shortlist sensors overflow Home Assistant state length
- **status:** `validated`
- **severity:** `medium`
- **area:** `sensors`
- **where seen:** live Home Assistant `0.1.83` with a larger unmanaged-candidate backlog
- **current observed behavior:** `sensor.zero_net_export_unmanaged_candidate_overview` and `sensor.zero_net_export_candidate_shortlist` emit long usefulness/warning strings that exceed Home Assistant's 255-character sensor-state limit, so HA logs repeated errors and falls those states back to `unknown`
- **expected behavior:** Managed Devices candidate summary sensors should stay compact enough to remain valid HA state strings while still giving operators a useful at-a-glance snapshot
- **evidence:** documented HA SSH access on `root@192.168.86.200:2222` succeeded in this run, and `ha core logs -n 120` shows repeated errors such as `State AC Outlet 2 (fixed) | strong match | key warning: No immediate warnings; ... for sensor.zero_net_export_unmanaged_candidate_overview is longer than 255, falling back to unknown` and `State 3rd Bedroom Crossfade (switch.bedroom_crossfade, fixed) | ... for sensor.zero_net_export_candidate_shortlist is longer than 255, falling back to unknown`
- **suspected cause:** the candidate summary sensors were reusing verbose review-preview strings that are suitable for notifications or attributes, but too long for HA state payload limits once multiple candidates are concatenated
- **repo fix:** `209665e` — this run adds `build_candidate_name_summary(...)` in `custom_components/zero_net_export/candidate_utils.py` and switches the candidate overview/shortlist sensor states to compact name-list summaries, keeping the richer fit/warning detail in attributes and deeper review paths instead of the state string itself
- **validation status:** repo-side fix implemented and covered by `python3 -m unittest tests.test_candidate_utils -q`, `python3 -m unittest discover -s tests -q`, and `python3 -m py_compile custom_components/zero_net_export/candidate_utils.py custom_components/zero_net_export/sensor.py`. Live validation succeeded in this run: the exact `209665e` repo build was copied to `/config/custom_components/zero_net_export`, `scripts/validate_install_fingerprint.py /config/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222` returned `overall_match=true`, Home Assistant core was restarted, and a follow-up `ha core logs` pass after the next coordinator cycles no longer showed the earlier `longer than 255, falling back to unknown` errors for `sensor.zero_net_export_unmanaged_candidate_overview` or `sensor.zero_net_export_candidate_shortlist`.
- **next action:** keep candidate detail richness in attributes/notifications/deeper review paths so future summary expansions do not regress back into overlong HA state strings

## ZNE-020 — Install provenance fingerprinting performs blocking file I/O in the event loop
- **status:** `fixed_pending_validation`
- **severity:** `medium`
- **area:** `runtime`
- **where seen:** live Home Assistant on the older installed `0.1.83` component build, plus earlier exact-build validation of commit `e1dcef8`
- **current observed behavior:** the repo fix exists, but the currently installed Home Assistant copy is still old enough to emit blocking `read_bytes` and `open` warnings from `release_info.py` while building install-provenance metadata from `manifest.json`
- **expected behavior:** install-provenance and release-info helpers should avoid synchronous filesystem reads on the event loop during coordinator/update paths
- **evidence:** documented HA SSH access on `root@192.168.86.200:2222` succeeded again in this run. `ha core logs -n 400 | grep -i zero_net_export` still shows `Detected blocking call to read_bytes ... at custom_components/zero_net_export/release_info.py, line 62: sha256_12 = hashlib.sha256(path.read_bytes()).hexdigest()[:12]` plus the matching blocking `open` warning at `2026-04-16 00:09:48`. The earlier exact-build validation against commit `e1dcef8` had cleared those warnings after restart, so this run's renewed warning is consistent with the current live fingerprint drift rather than a newly disproven repo fix.
- **suspected cause:** `build_install_provenance()` ultimately called `_cached_install_provenance()`, which still fell back to synchronous manifest/hash reads from `release_info.py` when the earlier warmup path had not produced a stable shared snapshot for later sync consumers on the event loop; the current live symptom persists because Home Assistant is still running an older `release_info.py` than repo HEAD
- **repo fix:** `e1dcef8` — replace the install-provenance warmup with an explicit async-primed snapshot in `custom_components/zero_net_export/release_info.py`, make synchronous callers fall back to a non-blocking pending snapshot instead of doing file I/O on the event loop, and refresh that snapshot during both setup-entry and migrate-entry startup in `custom_components/zero_net_export/__init__.py`; `tests/test_release_info_install_guidance.py` now covers the pending-snapshot fallback plus the new executor priming path
- **validation status:** repo-side fix remains verified with `python3 -m unittest tests.test_release_info_install_guidance -q`, `python3 -m unittest discover -s tests -q`, and `python3 -m py_compile custom_components/zero_net_export/release_info.py custom_components/zero_net_export/__init__.py`. Earlier live validation on the exact fixed build had also succeeded. However, this bug cannot stay `validated` as the current live state because the installed component fingerprint has drifted again and the old blocking-call warning is presently visible in Home Assistant logs.
- **next action:** treat exact-build redeploy as the immediate prerequisite under ZNE-022, then rerun post-restart log review and close this only after the current installed build no longer emits the blocking `release_info.py` warnings

## ZNE-022 — Live HA install no longer matches the current repo candidate after fingerprint coverage widened
- **status:** `fixed_pending_validation`
- **severity:** `medium`
- **area:** `release`
- **where seen:** repo-versus-live fingerprint validation on 2026-04-16 against repo HEAD from this run
- **current observed behavior:** `python3 scripts/validate_install_fingerprint.py /config/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222` still reports `overall_match=false` against the current repo candidate from this run. The live Home Assistant install is behind the current repo candidate across multiple shipped UI/runtime files, so the exact installed package is still not the exact code under review.
- **expected behavior:** before trusting further live validation, the Home Assistant install should match the current repo candidate exactly across the full shipped component surface, including every Python and JSON file that can change native Home Assistant behavior or text.
- **evidence:** documented HA SSH access on `root@192.168.86.200:2222` succeeded again in this run. `python3 scripts/validate_install_fingerprint.py /config/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222` still reports live manifest `0.1.83` with `overall_match=false`, with mismatches now present in shipped files including `button.py`, `candidate_utils.py`, `config_flow.py`, `diagnostics.py`, `native_support.py`, `release_info.py`, `strings.json`, and `translations/en.json`. Repo inspection in this run confirmed the source-of-truth bug entry had drifted again on repo-state detail after `a67acdc` landed: `git log --oneline -1 -- custom_components/zero_net_export` now reports `a67acdc feat: add per-device managed review buttons`, and `python3 scripts/print_expected_install_fingerprint.py` now emits both `expected_commit` and `expected_component_commit` as `a67acdc`. The release target therefore moved forward with the shipped component tree, not just docs-only repo HEAD.
- **suspected cause:** repo HEAD advanced after the earlier live deploy/restart cycle, and the live Home Assistant component tree still has an older mixed build even though the manifest version remains `0.1.83`.
- **repo fix:** `afbbd71`, `cf46eac`, `b9766aa`, `f45aef9` — widen exact-build fingerprint coverage beyond the old hand-maintained subset, then derive tracked files from the actual shipped component tree in `scripts/print_expected_install_fingerprint.py`, `scripts/compare_install_fingerprint.py`, and `custom_components/zero_net_export/release_info.py`, skipping only `__pycache__`; tests now assert coverage for active shipped files like `button.py`, `candidate_utils.py`, `binary_sensor.py`, `repairs.py`, and `select.py` so future UI/runtime files cannot silently fall outside exact-build validation, and this run adds explicit repo-head versus shipped-component commit reporting so release validation output no longer blurs docs-only HEAD movement with the actual redeploy target.
- **validation status:** repo-side fix remains implemented and verified, and live drift is re-confirmed in this run against the widened shipped-file fingerprint. This watchdog run also caught fresh repo-state drift in the release metadata: manifest/changelog had been bumped prematurely to `0.1.84` while the source-of-truth UI docs still define `0.1.83` as the active UI release, and `project_status.md` was still naming an older redeploy commit. Those repo-state drifts were corrected in the same run so release approval now points back at the exact current shipped-component `0.1.83` candidate instead of a stale or prematurely renumbered target. The real boundary is still explicit release approval to redeploy the shipped candidate and rerun fingerprint validation until it returns `overall_match=true`.
- **next action:** ask James directly for release approval to redeploy the exact current shipped-component `0.1.83` candidate, rerun fingerprint validation until it reports `overall_match=true`, then restart Home Assistant and continue Configure/native-UI validation on the exact installed candidate

## Recently validated or closed bugs

## ZNE-004 — Live install version stamp mismatched the intended `0.1.82` release
- **closed on:** 2026-04-15
- **severity:** `high`
- **area:** `release`
- **historical behavior:** during `0.1.82` release validation, the live Home Assistant install still showed `Version 0.1.81`, so the installed component fingerprint did not match the intended shipped build.
- **repo fix:** earlier exact-build release/deploy work plus this run's live fingerprint re-check.
- **closure evidence:** in this run, documented HA SSH access on `root@192.168.86.200:2222` succeeded and `python3 scripts/validate_install_fingerprint.py /config/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222` reported live manifest `0.1.83`, all tracked files matching the repo candidate from commit `5fe1c93`, and `overall_match=true`. Release-fingerprint drift is no longer the blocker; the remaining live blocker is the missing Zero Net Export config entry tracked in ZNE-002.

## ZNE-013 — Repo-local `tmp-ha-config/` scratch tree tripped exact-build clean-state guards
- **closed on:** 2026-04-15
- **severity:** `low`
- **area:** `process`
- **historical behavior:** repo inspection in this run found an untracked `tmp-ha-config/` scratch Home Assistant component tree at the repo root. That local validation debris made `git status --short` report the repo dirty and would trip `scripts/deploy_exact_repo_build.py --require-clean`, creating release-gate noise unrelated to the actual `0.1.83` candidate contents.
- **repo fix:** this run's repo-cleanliness guard fix — ignore `tmp-ha-config/` in `.gitignore` and record the release-hygiene correction in `CHANGELOG.md`
- **closure evidence:** after the ignore rule landed, repo status no longer reports `tmp-ha-config/` as an untracked change, so exact-build flows can use `--require-clean` without local scratch-tree drift

## ZNE-012 — Native-path docs still used vague `integration/device surfaces` wording after the source-of-truth path tightened
- **closed on:** 2026-04-15
- **severity:** `low`
- **area:** `docs`
- **historical behavior:** repo wording in `README.md`, `docs/DASHBOARD_SETUP.md`, and `docs/PRODUCT_SPEC_V1.md` still used the fuzzy phrase `integration/device surfaces` even though `docs/UI_DESIGN.md` and `docs/SUPERVISOR.md` now define the supported native path more precisely as Configure plus `Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device`. That wording drift weakened operator discoverability and contradicted the changelog claim that the remaining path wording had already been corrected.
- **repo fix:** this run's native-path wording alignment commit — replace the vague shorthand with the exact native Configure and device-path wording across the remaining repo docs, and record the correction in `CHANGELOG.md`.
- **closure evidence:** repo-side source-of-truth audit plus direct doc correction in the same run; `README.md`, `docs/DASHBOARD_SETUP.md`, and `docs/PRODUCT_SPEC_V1.md` now match the explicit native Home Assistant path language used by `docs/UI_DESIGN.md` and `docs/SUPERVISOR.md`

## ZNE-017 — Source-of-truth UI redesign existed only in a dirty working tree
- **closed on:** 2026-04-15
- **severity:** `medium`
- **area:** `docs`
- **historical behavior:** `docs/UI_DESIGN.md` had been locally rewritten to a denser native operator-console model and now referenced `docs/UI_RESEARCH.md`, `docs/UI_IMPLEMENTATION_SPEC.md`, `docs/UI_DESIGN_REVIEW.md`, and `docs/UI_DESIGN-old.md`, but those supporting files were still untracked. That left the repo's own source-of-truth chain half-landed: the active design doc pointed at documents that were not actually shipped in Git, and the redesign rationale/spec trail could disappear on the next clean checkout.
- **repo fix:** this run's UI source-of-truth doc commit — add the referenced redesign support docs to Git and keep the refreshed `docs/UI_DESIGN.md` as the committed design source of truth.
- **closure evidence:** repo-side audit plus direct doc correction in the same run; `git status` no longer reports the source-of-truth UI docs as modified/untracked once the commit lands, and the design document's referenced research/spec/review trail is now present in the repo

## ZNE-016 — UI design checklist and 1A execution slice drifted out of the committed source of truth
- **closed on:** 2026-04-15
- **severity:** `medium`
- **area:** `docs`
- **historical behavior:** repo inspection in this run found `docs/UI_DESIGN.md` dirty again. The working tree had already added the new build checklist, implementation-gap analysis, and the explicit `1A` headline-decision-summary execution slice, but HEAD still ended at the older relationship section. That meant the committed source-of-truth design doc was materially behind the current steering and no longer matched the fuller design shape being used for watchdog/supervisor guidance.
- **repo fix:** this run's UI source-of-truth sync commit — commit the pending `docs/UI_DESIGN.md` checklist/gap-analysis/`1A` design sections so the repo-shipped design source matches the current steering.
- **closure evidence:** repo-side audit plus direct doc correction in the same run; after the sync commit, `git diff -- docs/UI_DESIGN.md` is empty and the committed design doc now carries the build checklist, implementation-gap analysis, `1A` priority slice, and `docs/UI_IMPLEMENTATION_SPEC.md` reference.

## ZNE-010 — Repo release metadata drifted behind the documented `0.1.83` UI target
- **closed on:** 2026-04-15
- **severity:** `medium`
- **area:** `release`
- **historical behavior:** `docs/SUPERVISOR.md`, `docs/UI_DESIGN.md`, and `docs/UI_IMPLEMENTATION_MAP.md` all defined `0.1.83` as the active UI release target, but the repo working version still advertised `0.1.82` in `custom_components/zero_net_export/manifest.json`, the top changelog section, and `project_status.md`. That left the current candidate version tracking behind the documented release target and risked another misleading release/deploy handoff.
- **repo fix:** this run's release-metadata alignment commit — bump the repo working version to `0.1.83` in the manifest, make the changelog's active `Unreleased` section explicitly target `0.1.83`, and refresh `project_status.md` so the next action/blocker reflect the real release boundary and the still-installed live `0.1.81` build.
- **closure evidence:** repo-side source-of-truth audit plus direct metadata correction in the same run; `custom_components/zero_net_export/manifest.json`, `CHANGELOG.md`, and `project_status.md` now all point at the active `0.1.83` candidate, while live HA version drift remains tracked separately under `ZNE-004`

## ZNE-009 — Repo-wide unit verification drifted from the current button import contract
- **closed on:** 2026-04-15
- **severity:** `low`
- **area:** `process`
- **historical behavior:** repo-side verification for the managed-devices UI work had been recorded as passing, but a full `python3 -m unittest discover -s tests` run still failed because `tests/test_button_entity_categories.py` stubbed `homeassistant.components.*` modules without creating the `homeassistant` package root now imported by `custom_components/zero_net_export/button.py`
- **repo fix:** this run's test-stub coverage fix commit — restore the test stub's `homeassistant` package hierarchy so the button entity-category test reflects the real import contract and the full repo suite passes again
- **closure evidence:** `python3 -m unittest tests.test_button_entity_categories` passed after the stub fix, followed by `python3 -m unittest discover -s tests` passing repo-wide on 2026-04-15

## ZNE-008 — Source-of-truth UI docs still treated dashboards as a required `0.1.83` deliverable
- **closed on:** 2026-04-15
- **severity:** `medium`
- **area:** `docs`
- **historical behavior:** `docs/UI_DESIGN.md` still said there should be two dashboards built around existing HACS or custom dashboard technologies, and `docs/UI_IMPLEMENTATION_MAP.md` still carried a dashboard-delivery phase as though those dashboards were required for the `0.1.83` UI release. That conflicted with the same docs' native-only operator path, with supervisor steering, and with the project rule that optional dashboards must not displace Configure and Managed Devices work.
- **repo fix:** `863cba8` — clarify dashboards as optional in-native supplemental visibility only, and remove them as a required `0.1.83` implementation phase
- **closure evidence:** repo-side source-of-truth audit plus direct doc correction in the same run; `docs/UI_DESIGN.md` now marks dashboards optional and secondary, and `docs/UI_IMPLEMENTATION_MAP.md` now reframes dashboard work as optional cleanup instead of a required release phase

## ZNE-006 — Deploy helper CLI drift from documented release flow
- **closed on:** 2026-04-15
- **severity:** `medium`
- **area:** `release`
- **historical behavior:** `scripts/deploy_exact_repo_build.py` had rejected flags used by the intended exact-build workflow, including `--expected-commit`, `--require-clean`, and `--require-upstream-sync`
- **repo fix:** `d6c80be` — `scripts/deploy_exact_repo_build.py` now accepts `--expected-commit`, `--require-clean`, and `--require-upstream-sync`, and `tests/test_install_helper_scripts.py` covers matching and failing cases for each guard
- **closure evidence:** this was closed with repo validation because the bug was a local release-helper CLI contract mismatch, not a live Home Assistant runtime defect; `python3 -m unittest tests.test_install_helper_scripts tests.test_release_info_install_guidance` passed on 2026-04-15 after the flag support and test coverage were added

## ZNE-007 — Validation workflow awkward against remote HA environment
- **closed on:** 2026-04-15
- **severity:** `medium`
- **area:** `release`
- **repo fix:** `f3388cf` — `release: add ssh-backed HA fingerprint validation`
- **closure evidence:** repo-side SSH validation now works against the documented HA path without remote Python, and a live run against `root@192.168.86.200:2222` returned the installed component fingerprint from `/homeassistant/custom_components/zero_net_export`

## ZNE-021 — Exact-build fingerprint validation skipped critical startup/provenance files
- **closed on:** 2026-04-16
- **severity:** `medium`
- **area:** `release`
- **historical behavior:** the exact-build validation helpers only tracked `manifest.json`, `config_flow.py`, `native_support.py`, `coordinator.py`, and translation files. That let `scripts/validate_install_fingerprint.py /config/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222` report `overall_match=true` even though important startup/provenance files like `__init__.py` and `release_info.py` were outside the comparison set.
- **repo fix:** this run's validation-coverage fix commit — expand the tracked-file set in `scripts/print_expected_install_fingerprint.py`, `scripts/compare_install_fingerprint.py`, and `custom_components/zero_net_export/release_info.py` to include `__init__.py` and `release_info.py`, with regression coverage in `tests/test_install_helper_scripts.py` and `tests/test_release_info_install_guidance.py`.
- **closure evidence:** in this run, documented HA SSH access on `root@192.168.86.200:2222` succeeded, fresh `ha core logs` review showed the earlier `release_info.py` startup path was a real validation concern, repo-side verification passed with `python3 -m unittest tests.test_install_helper_scripts tests.test_release_info_install_guidance -q`, `python3 -m unittest discover -s tests -q`, and `python3 -m py_compile scripts/print_expected_install_fingerprint.py scripts/compare_install_fingerprint.py scripts/validate_install_fingerprint.py custom_components/zero_net_export/release_info.py`, and a rerun of `python3 scripts/validate_install_fingerprint.py /config/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222` now correctly reports `release_info.py` drift and `overall_match=false` until the latest repo build is redeployed.

## ZNE-023 — Exact-build fingerprint validation skipped active native-UI Python files
- **closed on:** 2026-04-16
- **severity:** `medium`
- **area:** `release`
- **historical behavior:** repo inspection in this run confirmed the exact-build fingerprint helpers still ignored active native-UI Python files like `button.py` and `candidate_utils.py`, even though those files were now ahead of the live Home Assistant install (`button.py` local `36948a15c7a0` vs remote `cba2671c12c1`, `candidate_utils.py` local `b297807df1e4` vs remote `f6899919f5c8`). That meant fingerprint output could under-report real repo-versus-live drift during the `0.1.83` UI release gate.
- **repo fix:** this run's validation-coverage fix commit — expand the tracked-file set in `scripts/print_expected_install_fingerprint.py`, `scripts/compare_install_fingerprint.py`, and `custom_components/zero_net_export/release_info.py` to include `button.py`, `candidate_utils.py`, `diagnostics.py`, and `sensor.py`, with regression coverage in `tests/test_install_helper_scripts.py` and `tests/test_release_info_install_guidance.py`.
- **closure evidence:** `python3 -m unittest tests.test_install_helper_scripts tests.test_release_info_install_guidance -q`, `python3 -m unittest discover -s tests -q`, and `python3 -m py_compile scripts/print_expected_install_fingerprint.py scripts/compare_install_fingerprint.py custom_components/zero_net_export/release_info.py` all passed in this run. Live SSH hash checks also confirmed the previously untracked drift in `button.py` and `candidate_utils.py`, so the widened fingerprint set now covers the missing UI files instead of silently skipping them.

## ZNE-024 — UI implementation map drifted behind the current repo-native UI candidate
- **closed on:** 2026-04-16
- **severity:** `low`
- **area:** `docs`
- **historical behavior:** `docs/UI_IMPLEMENTATION_MAP.md` is the implementation source of truth for `0.1.83`, but it had fallen behind the actual repo candidate after recent native-UI work landed. The status summary and phase sections still described the command center, Managed Devices workspace, candidate review flow, and release gate in older terms that understated delivered repo-side progress and did not clearly surface the current explicit release-approval boundary.
- **repo fix:** this run's implementation-map sync commit — sync `docs/UI_IMPLEMENTATION_MAP.md` so the completed/remaining status and Phases 3, 4, 5, and 7 match the current repo-native UI candidate and state plainly that James must be asked directly for release approval before the next exact-build redeploy.
- **closure evidence:** repo-side source-of-truth audit plus direct doc correction in the same run; `docs/UI_IMPLEMENTATION_MAP.md` now reflects the shipped repo candidate's command-center alert/board work, runtime-aware Managed Devices state, balanced candidate review, device-page deep-review handoff, and the explicit formal release-approval boundary.

## ZNE-025 — Repo release metadata jumped ahead of the source-of-truth UI release gate
- **closed on:** 2026-04-16
- **severity:** `medium`
- **area:** `release`
- **historical behavior:** repo inspection in this run found `custom_components/zero_net_export/manifest.json` and the top `CHANGELOG.md` target bumped to `0.1.84` even though `docs/SUPERVISOR.md`, `docs/UI_DESIGN.md`, and `docs/UI_IMPLEMENTATION_MAP.md` still define `0.1.83` as the active UI release. `project_status.md` also still asked for redeploy approval using an older shipped-component commit, which made the release boundary misleading in two different ways at once.
- **repo fix:** this run's release-metadata sync commit — return the manifest and changelog target to `0.1.83`, add the correction to `CHANGELOG.md`, and remove the stale hard-coded redeploy commit from `project_status.md` so the approval ask points at the exact current shipped-component candidate instead of an outdated hash.
- **closure evidence:** repo-side source-of-truth audit plus direct metadata correction in the same run; `custom_components/zero_net_export/manifest.json` and the changelog target now match the `0.1.83` UI release docs again, and `project_status.md` no longer points release approval at stale commit `f45618c`.

## Closure rule

Do not mark a bug `closed` just because a commit exists.
If the bug affects the user-visible product or live Home Assistant behavior, closure should usually require live validation evidence.
