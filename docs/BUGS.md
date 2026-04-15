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
- **status:** `open`
- **severity:** `high`
- **area:** `managed_devices`
- **where seen:** product-level review against live/native UI expectations
- **current observed behavior:** some UI scaffolding exists, but the requested visible native UI outcome still does not feel complete to James
- **expected behavior:** the product visibly delivers:
  1. clear managed vs unmanaged device experience
  2. clear promote / vet / review flow
  3. clear separation of Controls / Sensors / Managed Devices / Diagnostics
- **evidence:** direct user feedback plus repo/design audit captured in `docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md`
- **suspected cause:** implementation is still too scaffold/text-heavy and not yet sufficiently productized in live HA
- **validation status:** still open; `0.1.83` is now the explicit UI release intended to resolve this
- **next action:** progress the `0.1.83` UI phases in `docs/UI_IMPLEMENTATION_MAP.md` and require live HA evidence before closing

## ZNE-004 — Deploy helper CLI drift from documented release flow
- **status:** `open`
- **severity:** `medium`
- **area:** `release`
- **where seen:** formal `0.1.82` deploy attempt
- **current observed behavior:** `scripts/deploy_exact_repo_build.py` rejected flags used by the intended exact-build workflow, including `--expected-commit`, `--require-clean`, and `--require-upstream-sync`
- **expected behavior:** deploy tooling should match the documented/operator release workflow or the docs should be corrected to match the actual CLI
- **evidence:** live command failure during release execution
- **validation status:** unresolved
- **next action:** either align the script CLI with the intended workflow or rewrite the docs and operator commands around the actual supported interface

## Recently validated or closed bugs

## ZNE-005 — Validation workflow awkward against remote HA environment
- **closed on:** 2026-04-15
- **repo fix:** `f3388cf` — `release: add ssh-backed HA fingerprint validation`
- **closure evidence:** repo-side SSH validation now works against the documented HA path without remote Python, and a live run against `root@192.168.86.200:2222` returned the installed component fingerprint from `/homeassistant/custom_components/zero_net_export`


## Closure rule

Do not mark a bug `closed` just because a commit exists.
If the bug affects the user-visible product or live Home Assistant behavior, closure should usually require live validation evidence.
