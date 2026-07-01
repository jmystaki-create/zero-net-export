# ZNE-APP-003 Stage 2: Enhanced Fleet Controls

Date: 2026-07-01
Status: implementation

## Scope

Implement Stage 2 enhancements to the Managed Devices Fleet Control:
- **Priority and Readiness filters** - Filter fleet by priority level and readiness state
- **Bulk actions** - Select multiple devices and enable/disable them in one action
- **Sorting** - Sort fleet by priority, status, last-seen age
- **Enhanced columns** - Add "Last-seen age" and "Runtime blockers" columns to fleet table

## Acceptance Criteria

### Functional
- Priority filter dropdown shows unique priority values from fleet.
- Readiness filter dropdown shows unique readiness states from fleet.
- Bulk selection checkbox exists in fleet table header.
- Individual row checkboxes exist for device selection.
- Bulk action buttons (Enable Selected, Disable Selected) appear when devices are selected.
- Bulk actions require confirmation.
- Sort controls exist for Priority (high/medium/low), Status (enabled/disabled), and Last-seen (newest/oldest).
- Fleet table shows Last-seen age column (e.g., "5 min ago", "2 hours ago").
- Fleet table shows Runtime blockers column (e.g., "Blocked: X reason(s)").
- Sorting and filtering work together (filter first, then sort).

### Validation
- JavaScript syntax check passes.
- Changed Python files compile.
- Focused tests pass.
- Full unittest discovery passes.
- `git diff --check` is clean.

## Implementation Plan

1. **Add Priority and Readiness filters** - Extend filter dropdowns to include priority and readiness options.
2. **Add bulk selection** - Add checkboxes to fleet rows and header.
3. **Add bulk action handlers** - Implement `fleet-bulk-enable` and `fleet-bulk-disable` actions.
4. **Add sorting logic** - Implement sort by priority, status, and last-seen age.
5. **Add enhanced columns** - Add Last-seen age and Runtime blockers columns to fleet table.
6. **Update CSS** - Add styles for checkboxes, bulk action buttons, and new columns.

## Risk Assessment

- **Low risk**: Adding filter options and sorting logic.
- **Medium risk**: Bulk actions must handle edge cases (no selection, mixed states).
- **Low risk**: Adding columns is UI-only.

## Next Steps After Stage 2

- Live validation on Home Assistant instance.
- Browser proof capture (desktop and narrow).
- Release as next app feature release.
