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
- **status:** `in_progress`
- **severity:** `high`
- **area:** `managed_devices`
- **where seen:** product-level review against live/native UI expectations
- **current observed behavior:** some UI scaffolding exists, but the requested visible native UI outcome still does not feel complete to James
- **expected behavior:** the product visibly delivers:
  1. clear managed vs unmanaged device experience
  2. clear promote / vet / review flow
  3. clear separation of Controls / Sensors / Managed Devices / Diagnostics
- **evidence:** direct user feedback plus repo/design audit captured in `docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md`; repo inspection on 2026-04-15 also confirmed the managed-fleet workspace sensors and fleet-console helper were still marked diagnostic, which buried Managed Devices review under diagnostic-style entity presentation instead of treating it as a first-class fleet workspace
- **suspected cause:** implementation is still too scaffold/text-heavy and not yet sufficiently productized in live HA
- **repo fix:** current repo candidate in this run promotes managed-fleet workspace sensors and fleet-console helper out of diagnostics-only presentation
- **what changed:** repo-side UI cleanup in this run promotes the managed-fleet workspace sensors out of `EntityCategory.DIAGNOSTIC`, and the fleet-console button is no longer diagnostic-only, so the Managed Devices review surface is more visible from native entity/device views
- **validation status:** repo-side change verified with `python3 -m unittest tests.test_sensor_entity_categories tests.test_button_entity_categories` plus `python3 -m py_compile custom_components/zero_net_export/sensor.py custom_components/zero_net_export/button.py`; live Home Assistant validation is still required before closure
- **next action:** deploy this candidate to Home Assistant and verify the Managed Devices workspace now surfaces as a first-class native fleet review path rather than a diagnostics-only cluster

## ZNE-004 — Live install version stamp mismatched the intended `0.1.82` release
- **status:** `open`
- **severity:** `high`
- **area:** `release`
- **where seen:** live Home Assistant integration page during `0.1.82` release validation
- **current observed behavior:** GitHub/public release target was `0.1.82`, but the installed integration page still showed `Version 0.1.81`
- **expected behavior:** the live installed version stamp should match the intended shipped release version
- **evidence:** user screenshot of the Home Assistant integration page showing `Version 0.1.81` while validating the `0.1.82` release
- **suspected cause:** deploy/install artifact mismatch, incomplete copy, stale manifest, or other release-fingerprint drift
- **validation status:** unresolved; SSH-backed fingerprint validation re-run on 2026-04-15 against `root@192.168.86.200:2222` still reported live manifest `0.1.81` and `overall_match=false` versus current repo HEAD; this should only close once exact live install/version alignment is explicitly re-verified
- **next action:** re-run exact-build validation against the live HA install and confirm the installed manifest/version stamp matches the intended public release

## ZNE-005 — `build_release_info()` missing required `current_version` argument
- **status:** `fixed_pending_validation`
- **severity:** `critical`
- **area:** `runtime`
- **where seen:** live Home Assistant integration page during setup/retry
- **current observed behavior:** Home Assistant shows `Failed setup, will retry: build_release_info() missing 1 required positional argument: 'current_version'`
- **expected behavior:** Zero Net Export setup should complete without this runtime error
- **evidence:** user screenshot of the Home Assistant integration page showing the exact setup error; repo/HA SSH inspection on 2026-04-15 confirmed the live `0.1.81` install still has `coordinator.py` calling `build_release_info(include_changelog=False)` at line 223 without the required version argument
- **suspected cause:** coordinator release-update metadata calls `build_release_info()` without the required `current_version`, causing setup to fail while building validation details
- **repo fix:** `48a9d45` — pass `INTEGRATION_VERSION` from `coordinator.py` into `build_release_info()` and cover the call contract with a coordinator unit test
- **validation status:** repo-side fix is implemented and verified with `python3 -m unittest tests.test_source_freshness_probes tests.test_release_info_install_guidance` plus `python3 -m py_compile custom_components/zero_net_export/coordinator.py`; live validation is still pending because Home Assistant is still running the older `0.1.81` install over SSH
- **next action:** deploy this corrective build to Home Assistant, restart/reload the integration, and verify setup no longer retries with the missing-argument error

## Recently validated or closed bugs

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
