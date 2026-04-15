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
- **status:** `in_progress`
- **severity:** `critical`
- **area:** `runtime`
- **where seen:** live Home Assistant after the `0.1.82` deploy/restart, and still unresolved after the exact `0.1.83` repo build was deployed to Home Assistant
- **current observed behavior:** Zero Net Export is no longer failing with the earlier repairs-platform or `build_release_info()` tracebacks, but the live install still has no active `zero_net_export` config entry. API state listing now shows only `update.zero_net_export_update`, while the core runtime entities such as `sensor.zero_net_export_status`, `sensor.zero_net_export_command_center_status`, and `binary_sensor.zero_net_export_safe_mode` are absent.
- **expected behavior:** the live Home Assistant install should retain or recreate an active `zero_net_export` config entry so the controller device and core runtime entities load normally after restart
- **evidence:** in this run, documented HA SSH access on `root@192.168.86.200:2222` succeeded and `python3 scripts/validate_install_fingerprint.py /config/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222` confirmed the installed component is now the exact intended `0.1.83` build from commit `5fe1c93` with `overall_match=true`. Fresh remote inspection of `/config/.storage/core.config_entries` then showed `0` entries for domain `zero_net_export`, `/config/.storage/core.device_registry` showed `0` Zero Net Export devices, and the HA API `/api/states` returned only `update.zero_net_export_update` for `zero_net_export` entities.
- **suspected cause:** the release/deploy mismatch is no longer the blocker; the live install now appears to be missing or dropping the Zero Net Export config entry itself, which leaves the update entity behind but prevents the actual integration device and runtime entities from loading
- **validation status:** not resolved; exact-build deployment is now validated live, and the active blocker has narrowed to missing config-entry registration rather than stale package contents
- **next action:** the earlier backup-path pollution now appears absent live, so the immediate follow-up is to re-test Add Integration and confirm whether a new `zero_net_export` config entry can be created. If config entry creation still fails, capture the current traceback/log path and treat that as the next narrowed blocker keeping entities orphaned

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
- **evidence:** direct user feedback plus repo/design audit captured in `docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md`; repo inspection on 2026-04-15 also confirmed the managed-fleet workspace sensors and fleet-console helper were still marked diagnostic, which buried Managed Devices review under diagnostic-style entity presentation instead of treating it as a first-class fleet workspace; later same-day repo inspection also found the new managed/unmanaged and promotion-flow copy had landed in `custom_components/zero_net_export/strings.json` but not in `custom_components/zero_net_export/translations/en.json`, leaving the shipped English UI text behind the intended native flow wording; additional repo inspection in this run confirmed the Configure -> Managed Devices snapshot was still deriving `usable` counts from parse-only config data, so fleets with healthy runtime devices still displayed `usable: 0` and the edit/remove selectors hid real runtime readiness behind config-only labels; further repo inspection this run confirmed the native integration device page still lacked a dedicated first-class managed-device deep-review action, leaving per-device runtime review implicit across scattered entities rather than a single obvious native handoff
- **suspected cause:** implementation is still too scaffold/text-heavy and not yet sufficiently productized in live HA, translation artifacts can drift when native flow copy changes land without the matching `translations/en.json` update, some Configure fleet summaries were still built from parsed config inventory without overlaying live `device_details` readiness/status, and the device-page deep-review path was still implied rather than surfaced as its own obvious action
- **repo fix:** `2603de9`, `f804286`, `827530c`, `5c4ff5c`, `0acb62e`, `96fe3d2`, `28c1834`, `45c61ec`, `55c68bd`, `e9e0189`, `a0046ee`, `7cd6c35` — promote managed-fleet workspace sensors and the fleet-console helper out of diagnostics-only presentation, sync the updated managed-device flow copy into `translations/en.json` with a regression test that keeps the English translation file aligned to `strings.json`, route candidate discovery through a shared ranking helper so Managed Devices surfaces recommend stronger promotion targets before helper-style fallbacks, overlay live runtime `device_details` into Configure fleet summaries so Managed Devices shows real usable/status state instead of config-only placeholders, order the Managed Devices fleet-review, edit, and remove selectors by actionable runtime state so enabled-and-usable devices surface ahead of blocked or disabled entries while the fleet summary now shows usable counts explicitly, add a dedicated native device-page `Show managed-device review` action that summarizes per-device runtime status, guards, planned actions, and the deep-review handoff from the Zero Net Export device page, now emit a native persistent-notification success landing after managed-device promote/edit/remove or enablement-review saves so the operator gets an explicit what-changed plus next-step handoff instead of a cold form exit, extend that native managed-device review with an unmanaged-candidate backlog snapshot plus top promotion targets, fix the structured command-center summary plus shipped English translation so the new control-board copy does not crash on sparse runtime state or drift behind `strings.json`, keep unmanaged-candidate fit/warning guidance consistent across candidate discovery, candidate review, and the native managed-device review action, upgrade the primary fleet-console device-page action so it also shows managed/unmanaged snapshots, top candidate fit and warnings, runtime-ranked managed-device detail, and an explicit promotion handoff back into Configure -> Managed Devices, now make the device-page command-center guide itself use the shared full guide text so the native command-center handoff includes the recommended-section reason, explicit section ownership, common operator paths, blocker detail, and managed-device deep-review path instead of a shorter partial summary, and now make the command-center headline decision-first while expanding the top Energy state board with battery charge and discharge telemetry so the opening native console reads more like an operator surface than a raw status dump
- **what changed:** repo-side UI cleanup in this run promotes the managed-fleet workspace sensors out of `EntityCategory.DIAGNOSTIC`, the fleet-console button is no longer diagnostic-only, the shipped English translation now includes the managed/unmanaged snapshots and explicit promotion-path wording added to the source strings, `tests/test_translation_sync.py` now fails if `translations/en.json` drifts from `strings.json`, the Configure Managed Devices screen, fleet console, and managed-device workspace sensors now share one ranked unmanaged-candidate order so the top candidate and shortlist no longer default to alphabetical entity order, the Managed Devices Configure, fleet-review, edit, and remove screens now overlay live runtime `device_details` so usable counts, enabled-state ordering, and per-device labels reflect actual runtime readiness/status instead of always reporting config-only `usable: 0`, this run further tightens the native fleet workspace by sorting managed-device selectors with enabled-and-usable devices first, keeping blocked/disabled devices lower in the list, adding usable counts to the top fleet summary line so operators can see actionable fleet state at a glance, exposing a first-class `Show managed-device review` action plus diagnostics metadata that explicitly advertises that deeper review entry point, now posting a native managed-device update notification after fleet saves so promotion/edit/remove flows land with a clear success summary and explicit next path back into Managed Devices or deeper native device review, now extends the device-page managed-device review itself with an unmanaged-candidate snapshot plus top promotion targets so operators can compare the live fleet and remaining promotion backlog from one native handoff, now keeps the new structured command-center control board stable when runtime fields are absent while shipping the matching English command-center copy from `strings.json`, in this run aligns unmanaged-candidate fit and warning signals behind one shared assessment helper so the device-page review, fleet sensors, and promotion review stop drifting on helper-risk and variable-unit guidance, now upgrades Configure candidate snapshots, the full unmanaged pick list, and the managed-device review notification so unmanaged candidates show likely usefulness plus the top warning inline instead of just raw entity names, now upgrades the primary fleet-console device-page action so its notification matches that native fleet workspace with managed/unmanaged snapshots, runtime-ranked managed-device rows, top promotion fit/warning guidance, and a more explicit promote-next handoff back into Configure -> Managed Devices, now upgrades the device-page command-center guide notification plus button metadata so the native command-center handoff exposes the recommended-section reason, unavailable/stale mapped-role context, and managed-device deep-review path instead of a shorter summary that left the four-bucket operator model less visible from the device page, and in this run reshapes the command-center headline into decision-first operator language so Configure and the device-page guide now say things like export too high / near target / battery reserve protected rather than echoing raw backend reason strings while the top Energy state block now also includes battery charge and discharge telemetry
- **validation status:** repo-side UI changes remain covered by `python3 -m unittest discover -s tests`, which passed again in this run. This run also adds focused command-center regression coverage so the decision-first headline and richer energy-state board stay pinned for guarded-action, export-high, and near-target runtime states. Live validation status changed materially in this run: documented HA SSH access now confirms Home Assistant is serving the exact intended `0.1.83` build from commit `5fe1c93`, so package-version drift is no longer blocking UI validation. However, this bug still cannot be validated live because ZNE-002 remains open and the live install currently has no active `zero_net_export` config entry, no Zero Net Export device, and only the update entity visible through the HA API.
- **next action:** keep this bug in `fixed_pending_validation`, but move the immediate priority to ZNE-015 and ZNE-002. Deploy the latest repo fixes, restart Home Assistant, confirm Configure opens cleanly again, then re-check the native Managed Devices and four-bucket UI outcome against the exact installed `0.1.83` build

## ZNE-005 — `build_release_info()` missing required `current_version` argument
- **status:** `fixed_pending_validation`
- **severity:** `critical`
- **area:** `runtime`
- **where seen:** live Home Assistant integration page during setup/retry
- **current observed behavior:** Home Assistant shows `Failed setup, will retry: build_release_info() missing 1 required positional argument: 'current_version'`
- **expected behavior:** Zero Net Export setup should complete without this runtime error
- **evidence:** user screenshot of the Home Assistant integration page showing the exact setup error; repo/HA SSH inspection on 2026-04-15 confirmed the live `0.1.81` install still has `coordinator.py` calling `build_release_info(include_changelog=False)` at line 223 without the required version argument
- **suspected cause:** coordinator release-update metadata calls `build_release_info()` without the required `current_version`, causing setup to fail while building validation details
- **repo fix:** `48a9d45` — pass `INTEGRATION_VERSION` from `coordinator.py` into `build_release_info()` and cover the call contract with a coordinator unit test; this run adds `tests/test_release_update_details.py` so the release-update path has its own focused regression coverage for the missing-argument contract
- **validation status:** repo-side fix is implemented and verified with `python3 -m unittest tests.test_source_freshness_probes tests.test_release_info_install_guidance tests.test_release_update_details` plus `python3 -m py_compile custom_components/zero_net_export/coordinator.py`. In this run, documented HA SSH access also confirmed the exact intended `0.1.83` build is now installed live with `overall_match=true`, and fresh log grep no longer shows the earlier `build_release_info()` missing-argument retry. However, live setup-path validation is still incomplete because ZNE-002 now shows the integration has no active config entry to exercise normal setup/reload behavior.
- **next action:** once ZNE-002 is resolved and a live `zero_net_export` config entry exists again, re-verify that setup no longer retries with the missing-argument error on the exact installed build

## ZNE-014 — Post-install log review confirms the live 0.1.83 install is still not healthy
- **status:** `open`
- **severity:** `high`
- **area:** `runtime`
- **where seen:** live Home Assistant `0.1.83` after user install and manual log review request
- **current observed behavior:** the installed package is present as `0.1.83`, but the overall live install is still not healthy enough to call successful because the config flow is broken and core runtime entities remain absent/orphaned
- **expected behavior:** after install, Zero Net Export should load cleanly, allow Add Integration, and avoid integration-specific live errors in Home Assistant logs
- **evidence:** live HA review on 2026-04-15 confirmed remote manifest `0.1.83`, but also confirmed `homeassistant.config_entries` errors for `zero_net_export` plus the still-open missing-config-entry/orphaned-entity condition tracked elsewhere in this file
- **suspected cause:** currently overlaps the more specific bugs ZNE-002 and ZNE-011
- **validation status:** confirmed as an umbrella live-review finding, not yet resolved
- **next action:** keep using this as the top-level install-review reminder, but drive actual fix work through the narrower config-flow and runtime-registration bugs

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
- **status:** `open`
- **severity:** `critical`
- **area:** `config_flow`
- **where seen:** live Home Assistant `0.1.83` after the user successfully added the integration and then clicked the gear/configure icon
- **current observed behavior:** the integration card shows `Failed to set up`, and clicking the gear/configure icon raises `Config flow could not be loaded: 500 Internal Server Error Server got itself in trouble`
- **expected behavior:** once the integration is added, clicking Configure should open the native Zero Net Export options/config flow instead of surfacing a server-side 500
- **evidence:** user screenshot from 2026-04-15 shows the integration card in Home Assistant with `Failed to set up` and the exact 500 popup after clicking the gear icon. Live HA logs from the same run show the real traceback: `ImportError: cannot import name 'build_source_attention_brief' from 'custom_components.zero_net_export.native_support'` while loading `custom_components.zero_net_export.sensor`, followed by `homeassistant.config_entries` setup failure for the Zero Net Export entry and an aiohttp server error path through `config_flow.py`.
- **suspected cause:** repo/runtime drift left `sensor.py` importing `build_source_attention_brief` even though that helper no longer existed in `native_support.py`, so entry setup fails and the later Configure request surfaces as a generic 500
- **repo fix:** this run restores `build_source_attention_brief(...)` in `custom_components/zero_net_export/native_support.py` and adds focused regression coverage in `tests/test_source_attention_brief.py`; commit `37777cd` — `fix: restore source attention brief helper`
- **validation status:** repo-side fix implemented, verified with `python3 -m unittest tests.test_source_attention_brief tests.test_install_helper_scripts tests.test_command_center_summary tests.test_release_update_details tests.test_source_freshness_probes tests.test_release_info_install_guidance -q` and `python3 -m py_compile custom_components/zero_net_export/native_support.py custom_components/zero_net_export/sensor.py`. Live validation is still pending until this fix is deployed to Home Assistant and the integration setup/configure path is re-tested.
- **next action:** deploy commit `37777cd` to the live HA install, restart Home Assistant, then re-test the integration card setup state and the gear/configure path to confirm the 500 is gone

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


## Closure rule

Do not mark a bug `closed` just because a commit exists.
If the bug affects the user-visible product or live Home Assistant behavior, closure should usually require live validation evidence.
