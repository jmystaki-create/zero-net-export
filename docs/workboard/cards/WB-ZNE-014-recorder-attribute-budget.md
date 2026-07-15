# WB-ZNE-014 Recorder Attribute Budget

Status: Done
Priority: High
Labels: recorder, attributes, diagnostics, release, validation

## Purpose

Track `ZNE-595`, the corrective cleanup for Zero Net Export entity attributes
that exceeded Home Assistant's 16 KB recorder attribute limit.

## Linked Bug

- `ZNE-595` - recorder-backed entity attributes exceed Home Assistant's 16 KB
  limit.

## Acceptance Criteria

- Recorder-backed entities expose concise dashboard-safe attributes.
- Bulky action history, source diagnostics, source freshness, daily metrics,
  calibration hints, managed-device runtime detail, and long candidate queues
  stay off frequently recorded entity attributes.
- Full detail remains available through diagnostics/app surfaces.
- Tests cover representative attribute-size trimming.
- Installed Home Assistant validation shows no ZNE recorder attribute-size
  warnings in the reviewed post-restart log window.

## Evidence

- Repo validation: `validation/zne-595-recorder-attribute-budget.md`
- Release validation: `validation/0.4.12-release-validation.md`
- GitHub release: `v0.4.12`
- Home Assistant/HACS installed/latest: `v0.4.12`
- Post-restart max observed ZNE attribute payload: `10483` bytes
- Reviewed post-restart log window: `0` ZNE recorder attribute-size warnings

## Next Actions

No remaining action for `ZNE-595`. Keep recorder warning scans in the standard
release validation checklist so recurrence is caught after future changes.
