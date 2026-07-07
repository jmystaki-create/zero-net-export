# ZNE-APP-007 Multi-Plan And Service Separation Implementation

Date: 2026-07-07

Status: repo validated; release/live validation pending

## Summary

Implemented the first Milestone 7 slice: explicit app plan context and entry-scoped backend service calls.

## Implementation

Backend:

- Added shared `_entry_from_service_call(hass, call)` resolver.
- Resolver allows implicit fallback only when exactly one Zero Net Export entry exists.
- Resolver raises a clear error when multiple entries exist and a service call omits `entry_id`.
- Added `_coordinator_from_service_call(hass, call)` for coordinator-backed services.
- Registered `pause_executor`, `resume_executor`, `export_diagnostics`, and `repair_issue` as global entry-scoped services instead of per-entry closures.
- Kept `update_managed_device`, `remove_managed_device`, and `update_source_roles` using the same entry resolver.
- Added service schemas and `services.yaml` fields for entry-scoped pause/resume/repair/export calls.

Frontend:

- Added persistent selected plan context state.
- Added visible app-wide selected plan context header/selector.
- Added change handling for plan selection.
- Added `_entryServiceData()` to require explicit plan selection when multiple entries are exposed.
- Passed selected `entry_id` into source-role saves, managed-device updates/removals, executor pause/resume, diagnostics export, and repair actions.
- Diagnostics download now also triggers the backend `export_diagnostics` service for the selected plan.

Tests:

- Added static regression coverage for selected plan context UI and payload use.
- Added static regression coverage for ambiguous multi-entry service guardrails.
- Updated diagnostics logger expectation after entry-specific repair logging.
- Updated manifest release-version assertion to current `0.3.3`.

## Validation

Commands run:

```bash
python3 -m unittest tests.test_managed_devices_panel tests.test_diagnostics_export_service -q
python3 -m unittest discover -s tests -q
python3 -m py_compile custom_components/zero_net_export/__init__.py custom_components/zero_net_export/app_api.py
node --check custom_components/zero_net_export/frontend/zero-net-export-app.js
git diff --check
```

Results:

- Focused tests: `Ran 19 tests`, `OK`.
- Full test discovery: `Ran 627 tests`, `OK`.
- Python compile: passed.
- JavaScript syntax check: passed.
- `git diff --check`: passed.

## Remaining Gate

Release/live validation is pending:

- Run full test discovery before release.
- Publish as `v0.4.0` or chosen release tag.
- Install/update through HACS.
- Restart Home Assistant.
- Validate single-plan app context on the live instance.
- If a safe second ZNE entry exists, validate multi-plan selector and no cross-entry writes. If not, record single-plan live proof plus repo-level multi-entry guardrail proof.
