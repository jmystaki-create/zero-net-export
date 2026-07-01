# Milestone 4: Source Health & Runtime Blocker Resolution

**Status**: Ready  
**Priority**: High  
**Labels**: milestone, feature, app, source-health, blocker  
**Workboard Card**: `8b148624`  

---

## Purpose

Define and implement ZNE-APP-004: Source Health & Runtime Blocker Resolution, the next app milestone after Managed Devices Fleet Control (ZNE-APP-003).

## User Outcome

An operator can:
- See a clear, actionable status for ZNE runtime health (`sensor.zero_net_export_status` reports `ok` instead of `degraded`).
- Understand and resolve the root cause of the battery discharge power `state_class` mismatch.
- Verify that power reconciliation errors are within acceptable tolerance (< 5% of home load).
- Trust that ZNE's power source data is accurate and usable for runtime control decisions.

## Acceptance Criteria

1. **Status Resolution**: `sensor.zero_net_export_status` reports `ok` (not `degraded`).
2. **Reason Field**: `sensor.zero_net_export_reason` is empty or reports a non-blocking informational message.
3. **Reconciliation Accuracy**: `sensor.zero_net_export_last_reconciliation_error` magnitude is < 5% of `sensor.zero_net_export_home_load_power`.
4. **Documentation**: A fix record exists explaining:
   - The root cause of the `state_class` mismatch.
   - The implemented workaround (e.g., template sensor or ZNE adaptation).
   - Any required HA config changes for future installs.
5. **Validation Evidence**: Live API proof showing resolved status and reconciliation accuracy.

## Target Environment Feasibility Check

### Identified Issue
- **Entity**: `sensor.anker_battery_discharge_power`
- **Current State**: `state_class=total`
- **Expected State**: `state_class=measurement` (required for real-time power reconciliation).
- **Root Cause**: The source sensor (likely from an Anker/EcoFlow integration) exposes `total` instead of `measurement`.

### Feasibility Options
1. **Option A: Template Sensor Workaround** (Recommended)
   - Create a HA template sensor that wraps `sensor.anker_battery_discharge_power` and forces `state_class=measurement`.
   - ZNE config is updated to use the template sensor as the battery discharge source.
   - **Pros**: Non-invasive, reversible, no ZNE code changes.
   - **Cons**: Requires user to add a template sensor to their HA config.

2. **Option B: ZNE Adaptation**
   - Modify ZNE to accept `state_class=total` for battery discharge power and treat it as a measurement.
   - **Pros**: No user config changes required.
   - **Cons**: May violate HA best practices; could mask other data quality issues.

3. **Option C: Integration Fix**
   - Report the issue to the Anker/EcoFlow integration maintainers.
   - **Pros**: Fixes the root cause for all users.
   - **Cons**: Long timeline; not actionable for immediate release.

### Decision
**Option A (Template Sensor Workaround)** is the recommended path for Milestone 4:
- Fastest to implement and validate.
- Preserves HA data quality standards.
- Provides a clear migration path for users.

## Implementation Plan

### Stage 1: Documentation & User Guidance
1. Create a `docs/SOURCE_HEALTH_FIX_GUIDE.md` with:
   - Explanation of the `state_class` mismatch.
   - Step-by-step instructions for creating the template sensor.
   - Example YAML configuration.
2. Update `README.md` and `CONSTRAINTS.md` to reference the guide.

### Stage 2: ZNE Adaptation (Optional Fallback)
1. If users cannot or will not add a template sensor, implement a ZNE-side adaptation:
   - Detect `state_class=total` for battery discharge power.
   - Log a warning but proceed with reconciliation.
   - Update `sensor.zero_net_export_status` to `ok` if the error is within tolerance.

### Stage 3: Validation
1. Live API check for `sensor.zero_net_export_status=ok`.
2. Verify reconciliation error < 5%.
3. Browser proof of the Diagnostics tab showing resolved status.

## Validation Plan

1. **Live API Check**: Query `sensor.zero_net_export_status`, `sensor.zero_net_export_reason`, and `sensor.zero_net_export_last_reconciliation_error`.
2. **Reconciliation Error Check**: Confirm magnitude < 5% of home load.
3. **Browser Proof**: Capture the Diagnostics tab showing `status=ok`.
4. **Test Suite**: Ensure no regressions in existing tests.

## Risks

- **User Adoption**: Users may not add the template sensor, leaving ZNE in `degraded` state.
- **Data Quality**: Masking `state_class` issues could hide other data quality problems.
- **Timeline**: If Option B is required, additional development time is needed.

## Next Steps

1. **Create `SOURCE_HEALTH_FIX_GUIDE.md`** with template sensor instructions.
2. **Update `README.md`** to reference the guide.
3. **Implement Option B (if needed)** as a fallback.
4. **Validate** with live HA API and browser proof.
5. **Release** as `v0.2.6` (or patch version).

---

**Feasibility Check Accepted**: 2026-07-01 22:55 GMT+10  
**Decision**: Proceed with Option A (Template Sensor Workaround) as the primary path, with Option B as a fallback.

**Status Update**: Milestone 4 moved to **Doing** on 2026-07-01 22:55 GMT+10.
