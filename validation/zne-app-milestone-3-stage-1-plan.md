# ZNE-APP-003 Stage 1: Fleet List with Basic Summary

Date: 2026-07-01
Status: implementation

## Scope

Implement the first slice of Milestone 3 (Managed Devices Fleet Control):
- **Fleet list** showing all managed devices with key fields
- **Fleet summary counts** (total, enabled, disabled, blocked, stale)
- **Basic filter controls** (plan, status)
- **Drill-down detail view** for individual devices

## Acceptance Criteria

### Functional
- Managed Devices section shows a table/list of all managed devices.
- Each row displays: device key, plan (entry_id), enabled status, priority, readiness state.
- Fleet summary shows counts: total, enabled, disabled, blocked, stale.
- Filter dropdowns exist for plan and status.
- Clicking a device row shows a detail view with captured settings and runtime state.
- Existing single-device actions (enable/disable/remove) remain functional.

### Validation
- JavaScript syntax check passes.
- Changed Python files compile.
- Focused tests pass.
- Full unittest discovery passes.
- `git diff --check` is clean.
- Browser proof captured (desktop and narrow).

## Implementation Plan

1. **Read fleet data** from `sensor.managed_devices_overview` attributes.
2. **Compute summary counts** (total, enabled, disabled, blocked, stale).
3. **Render fleet table** with sortable columns.
4. **Add filter controls** for plan and status.
5. **Implement drill-down** detail view for device rows.
6. **Preserve existing** single-device action controls.

## Files to Change

- `custom_components/zero_net_export/frontend/zero-net-export-app.js`
  - Replace `_managedDevicesSection()` with enhanced fleet view.
  - Add `_fleetSummary()` helper.
  - Add `_fleetRow()` and `_fleetDetail()` helpers.
  - Add filter state management.

## Risk Assessment

- **Low risk**: Reading existing `managed_devices_overview` sensor data.
- **Low risk**: UI-only changes; no backend service modifications.
- **Medium risk**: Filter logic must handle edge cases (empty fleet, missing attributes).

## Next Steps After Stage 1

- Add priority and readiness filters.
- Add bulk action controls (enable/disable multiple devices).
- Add fleet sorting (by priority, status, last-seen).
- Add "last-seen age" and "runtime blockers" columns.
