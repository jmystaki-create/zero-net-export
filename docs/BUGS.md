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
- **status:** `fixed_pending_validation`
- **severity:** `critical`
- **area:** `runtime`
- **where seen:** live Home Assistant after `0.1.82` deploy/restart
- **current observed behavior:** Zero Net Export entities restore as unavailable, and logs show `HomeAssistantError: Invalid repairs platform <module 'custom_components.zero_net_export.repairs' ...>`
- **expected behavior:** Repairs platform loads cleanly and the integration recovers with live entities instead of staying restored/unavailable
- **evidence:** live HA logs after the `0.1.82` restart; affected entities included `sensor.zero_net_export_status`, `sensor.zero_net_export_command_center_status`, `sensor.zero_net_export_stale_source_count`, `binary_sensor.zero_net_export_safe_mode`, and `sensor.zero_net_export_reason`
- **suspected cause:** missing Repairs flow contract in `custom_components/zero_net_export/repairs.py`
- **repo fix:** `ad44fc1` — `fix: add repairs platform entry flow`
- **validation status:** repo-level fix exists and `py_compile` passed, but live post-fix validation is still missing; repo-side SSH fingerprint validation on 2026-04-15 showed the live HA install path still serving `0.1.81`, so the corrective repo build containing `ad44fc1` is not yet the installed build being validated
- **next action:** deploy a corrective build newer than the current live `0.1.81` install, restart Home Assistant, and verify the repairs-platform error is gone and entities recover live

## ZNE-002 — Main Zero Net Export entities stay restored/unavailable after restart
- **status:** `open`
- **severity:** `critical`
- **area:** `runtime`
- **where seen:** live Home Assistant after the `0.1.82` deploy/restart
- **current observed behavior:** key entities remained `restored: true` / `unavailable`
- **expected behavior:** core Zero Net Export entities recover live after restart
- **evidence:** live checks after restart showed `sensor.zero_net_export_status`, `sensor.zero_net_export_command_center_status`, `sensor.zero_net_export_stale_source_count`, `binary_sensor.zero_net_export_safe_mode`, and `sensor.zero_net_export_reason` unavailable while source entities such as `sensor.system_rome_yield_total` were present
- **suspected cause:** may be downstream of ZNE-001 or another runtime-loading issue replacing it
- **validation status:** not resolved yet; repo-side SSH fingerprint validation on 2026-04-15 showed the live HA install path still serving `0.1.81`, so this runtime recovery bug still cannot be re-validated against the repaired repo build yet
- **next action:** deploy a corrective build newer than the current live `0.1.81` install, then re-validate after restart; if the entities still remain restored/unavailable, capture the replacement traceback and split into a more specific bug entry if needed

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
- **repo fix:** `2603de9`, `f804286`, `827530c`, `5c4ff5c`, `0acb62e`, `96fe3d2`, `28c1834`, `45c61ec`, `55c68bd`, `e9e0189`, plus this run's candidate-assessment alignment work — promote managed-fleet workspace sensors and the fleet-console helper out of diagnostics-only presentation, sync the updated managed-device flow copy into `translations/en.json` with a regression test that keeps the English translation file aligned to `strings.json`, route candidate discovery through a shared ranking helper so Managed Devices surfaces recommend stronger promotion targets before helper-style fallbacks, overlay live runtime `device_details` into Configure fleet summaries so Managed Devices shows real usable/status state instead of config-only placeholders, order the Managed Devices fleet-review, edit, and remove selectors by actionable runtime state so enabled-and-usable devices surface ahead of blocked or disabled entries while the fleet summary now shows usable counts explicitly, add a dedicated native device-page `Show managed-device review` action that summarizes per-device runtime status, guards, planned actions, and the deep-review handoff from the Zero Net Export device page, now emit a native persistent-notification success landing after managed-device promote/edit/remove or enablement-review saves so the operator gets an explicit what-changed plus next-step handoff instead of a cold form exit, extend that native managed-device review with an unmanaged-candidate backlog snapshot plus top promotion targets, fix the structured command-center summary plus shipped English translation so the new control-board copy does not crash on sparse runtime state or drift behind `strings.json`, and now keep unmanaged-candidate fit/warning guidance consistent across candidate discovery, candidate review, and the native managed-device review action
- **what changed:** repo-side UI cleanup in this run promotes the managed-fleet workspace sensors out of `EntityCategory.DIAGNOSTIC`, the fleet-console button is no longer diagnostic-only, the shipped English translation now includes the managed/unmanaged snapshots and explicit promotion-path wording added to the source strings, `tests/test_translation_sync.py` now fails if `translations/en.json` drifts from `strings.json`, the Configure Managed Devices screen, fleet console, and managed-device workspace sensors now share one ranked unmanaged-candidate order so the top candidate and shortlist no longer default to alphabetical entity order, the Managed Devices Configure, fleet-review, edit, and remove screens now overlay live runtime `device_details` so usable counts, enabled-state ordering, and per-device labels reflect actual runtime readiness/status instead of always reporting config-only `usable: 0`, this run further tightens the native fleet workspace by sorting managed-device selectors with enabled-and-usable devices first, keeping blocked/disabled devices lower in the list, adding usable counts to the top fleet summary line so operators can see actionable fleet state at a glance, exposing a first-class `Show managed-device review` action plus diagnostics metadata that explicitly advertises that deeper review entry point, now posting a native managed-device update notification after fleet saves so promotion/edit/remove flows land with a clear success summary and explicit next path back into Managed Devices or deeper native device review, now extends the device-page managed-device review itself with an unmanaged-candidate snapshot plus top promotion targets so operators can compare the live fleet and remaining promotion backlog from one native handoff, now keeps the new structured command-center control board stable when runtime fields are absent while shipping the matching English command-center copy from `strings.json`, in this run aligns unmanaged-candidate fit and warning signals behind one shared assessment helper so the device-page review, fleet sensors, and promotion review stop drifting on helper-risk and variable-unit guidance, and now upgrades Configure candidate snapshots, the full unmanaged pick list, and the managed-device review notification so unmanaged candidates show likely usefulness plus the top warning inline instead of just raw entity names
- **validation status:** repo-side change verified again on 2026-04-15 with `python3 -m unittest tests.test_candidate_utils tests.test_sensor_entity_categories tests.test_button_entity_categories tests.test_translation_sync tests.test_config_flow_device_runtime_overlay tests.test_source_repair_guidance` plus `python3 -m py_compile custom_components/zero_net_export/candidate_utils.py custom_components/zero_net_export/sensor.py custom_components/zero_net_export/button.py custom_components/zero_net_export/config_flow.py custom_components/zero_net_export/diagnostics.py tests/test_config_flow_device_runtime_overlay.py`; later same day, a repo-wide verification run exposed that `tests.test_button_entity_categories` no longer matched the current `button.py` Home Assistant import path because the stubbed `homeassistant` package root was missing, and that repo-only regression is now corrected with the full `python3 -m unittest discover -s tests` suite passing again. This run also caught a fresh repo-only regression from `902a145` where the new structured command-center summaries raised `TypeError` on sparse runtime state and `translations/en.json` no longer matched the updated command-center copy in `strings.json`; both are now corrected, and `python3 -m unittest discover -s tests` plus `python3 -m py_compile custom_components/zero_net_export/native_support.py` pass again. This run further verified the candidate-assessment alignment and the new inline unmanaged-candidate usefulness/warning previews with `python3 -m unittest discover -s tests` plus `python3 -m py_compile custom_components/zero_net_export/candidate_utils.py custom_components/zero_net_export/sensor.py custom_components/zero_net_export/button.py custom_components/zero_net_export/config_flow.py`. Documented HA SSH access was re-tried again in this run via `python3 scripts/validate_install_fingerprint.py /homeassistant/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222`, which still reports live manifest `0.1.81` and `overall_match=false` against the current repo candidate in this workspace, so the repo fix is not yet validated in the live install and this bug should stay `fixed_pending_validation` until the newer build is deployed and checked in Home Assistant
- **next action:** deploy this candidate to Home Assistant, restart or reload the integration, and verify the live Managed Devices workspace now shows the updated managed/unmanaged copy, ranked promotion candidates, and runtime-backed usable/status state instead of the older `0.1.81` behavior

## ZNE-004 — Live install version stamp mismatched the intended `0.1.82` release
- **status:** `open`
- **severity:** `high`
- **area:** `release`
- **where seen:** live Home Assistant integration page during `0.1.82` release validation
- **current observed behavior:** GitHub/public release target was `0.1.82`, but the installed integration page still showed `Version 0.1.81`
- **expected behavior:** the live installed version stamp should match the intended shipped release version
- **evidence:** user screenshot of the Home Assistant integration page showing `Version 0.1.81` while validating the `0.1.82` release
- **suspected cause:** deploy/install artifact mismatch, incomplete copy, stale manifest, or other release-fingerprint drift
- **validation status:** unresolved; SSH-backed fingerprint validation re-run on 2026-04-15 with `python3 scripts/validate_install_fingerprint.py /homeassistant/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222` still reported live manifest `0.1.81`, tracked-file mismatches, and `overall_match=false` versus the current `0.1.83` workspace candidate, so live install/version alignment is still not verified
- **next action:** ask James directly for approval to execute the formal `0.1.83` release flow, then deploy one exact build to Home Assistant and re-run fingerprint validation until the installed manifest/version stamp matches the intended release

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
- **validation status:** repo-side fix is implemented and verified with `python3 -m unittest tests.test_source_freshness_probes tests.test_release_info_install_guidance tests.test_release_update_details` plus `python3 -m py_compile custom_components/zero_net_export/coordinator.py`; SSH-backed fingerprint validation re-run in this run still shows Home Assistant serving the older `0.1.81` install, so live validation remains pending until a newer exact build is deployed
- **next action:** deploy the current `0.1.83` candidate build to Home Assistant, restart/reload the integration, and verify setup no longer retries with the missing-argument error

## Recently validated or closed bugs

## ZNE-012 — Native-path docs still used vague `integration/device surfaces` wording after the source-of-truth path tightened
- **closed on:** 2026-04-15
- **severity:** `low`
- **area:** `docs`
- **historical behavior:** repo wording in `README.md`, `docs/DASHBOARD_SETUP.md`, and `docs/PRODUCT_SPEC_V1.md` still used the fuzzy phrase `integration/device surfaces` even though `docs/UI_DESIGN.md` and `docs/SUPERVISOR.md` now define the supported native path more precisely as Configure plus `Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device`. That wording drift weakened operator discoverability and contradicted the changelog claim that the remaining path wording had already been corrected.
- **repo fix:** this run's native-path wording alignment commit — replace the vague shorthand with the exact native Configure and device-path wording across the remaining repo docs, and record the correction in `CHANGELOG.md`.
- **closure evidence:** repo-side source-of-truth audit plus direct doc correction in the same run; `README.md`, `docs/DASHBOARD_SETUP.md`, and `docs/PRODUCT_SPEC_V1.md` now match the explicit native Home Assistant path language used by `docs/UI_DESIGN.md` and `docs/SUPERVISOR.md`

## ZNE-011 — Source-of-truth UI redesign existed only in a dirty working tree
- **closed on:** 2026-04-15
- **severity:** `medium`
- **area:** `docs`
- **historical behavior:** `docs/UI_DESIGN.md` had been locally rewritten to a denser native operator-console model and now referenced `docs/UI_RESEARCH.md`, `docs/UI_IMPLEMENTATION_SPEC.md`, `docs/UI_DESIGN_REVIEW.md`, and `docs/UI_DESIGN-old.md`, but those supporting files were still untracked. That left the repo's own source-of-truth chain half-landed: the active design doc pointed at documents that were not actually shipped in Git, and the redesign rationale/spec trail could disappear on the next clean checkout.
- **repo fix:** this run's UI source-of-truth doc commit — add the referenced redesign support docs to Git and keep the refreshed `docs/UI_DESIGN.md` as the committed design source of truth.
- **closure evidence:** repo-side audit plus direct doc correction in the same run; `git status` no longer reports the source-of-truth UI docs as modified/untracked once the commit lands, and the design document's referenced research/spec/review trail is now present in the repo

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
