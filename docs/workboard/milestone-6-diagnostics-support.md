# Workboard Card: Milestone 6 - Diagnostics & Support Polish

**ID**: `zne-app-006`  
**Type**: `FEATURE`  
**Status**: `ready`  
**Priority**: `high`  
**Created**: 2026-07-02  
**Target Release**: `v0.3.1`

---

## User Outcome

When something goes wrong or the system is in a degraded state, the operator can immediately see *what* is broken, *why* it's broken, and *how* to fix it—without needing to SSH into the server, read raw logs, or guess at entity mappings.

---

## Acceptance Criteria

### 1. Diagnostics Card (New Tab)
- [ ] A new "Diagnostics" tab in the app (next to Overview, Sources, Managed Devices).
- [ ] Shows last 20 log entries (filtered to `zero_net_export` only) with timestamps and severity.
- [ ] Shows current source health summary (which sources are missing/stale/invalid).
- [ ] Shows current executor state (running/paused) and last action timestamp.
- [ ] Shows reconciliation trend (last 10 reconciliation errors, listed).
- [ ] Auto-refreshes every 30 seconds.

### 2. Error Context & Repair Guidance
- [ ] When `sensor.zero_net_export_status` is `blocked` or `error`:
  - [ ] Overview card shows a prominent error banner with:
    - [ ] Error code (e.g., `SOURCE_MISSING`, `RECONCILIATION_HIGH`).
    - [ ] Human-readable message.
    - [ ] **Repair link/button** that opens the correct HA config page.
- [ ] When `binary_sensor.zero_net_export_source_mismatch` is `on`:
  - [ ] Shows which source roles have mismatched readings and suggests the correct binding.

### 3. Export & Share Diagnostics
- [ ] A "Download Diagnostics" button that exports:
  - [ ] Current sensor states (all `zero_net_export_*` entities).
  - [ ] Last 50 log entries.
  - [ ] Current config entry state.
  - [ ] Reconciliation history (last 100 entries).
- [ ] Output format: JSON file named `zne-diagnostics-YYYYMMDD-HHMMSS.json`.

### 4. Validation Proof
- [ ] Live browser screenshot of the Diagnostics tab showing log entries and health summary.
- [ ] Live browser screenshot of an error banner (triggered by temporarily breaking a source).
- [ ] Downloaded diagnostics JSON file validated for structure and content.
- [ ] Log proof: "Diagnostics exported" message when button clicked.

---

## Implementation Plan

See `docs/MILESTONE_6_IMPLEMENTATION_PLAN.md` for detailed backend and frontend changes.

---

## Feasibility Check

See `docs/MILESTONE_6_DIAGNOSTICS_SUPPORT_FEASIBILITY.md` - **ACCEPTED**.

---

## Validation Plan

1. **Repo Validation**:
   - `python3 -m unittest discover -s tests` (expect all tests to pass).
   - `py_compile` on all changed files.
   - `git diff --check`.

2. **Live Validation (HACS Path)**:
   - Release `v0.3.1`.
   - Install via HACS, restart HA.
   - Open Diagnostics tab: Verify log entries, health summary, trend.
   - Trigger error (break a source): Verify error banner and repair guidance.
   - Click "Download Diagnostics": Verify file downloads and contains expected data.
   - Capture screenshots and log snippets.

---

## Risks & Mitigations

- **Risk**: Log exposure of sensitive data.
  - **Mitigation**: Filter logs for tokens, passwords, and entity IDs before export.
- **Risk**: Performance impact of frequent log polling.
  - **Mitigation**: Poll every 30 seconds max.
- **Risk**: Large diagnostics file.
  - **Mitigation**: Limit log entries to 50, reconciliation history to 100.

---

## Dependencies

- None (self-contained feature).

---

## Notes

- Internal log buffer will only capture `zero_net_export` logs (not full HA logs).
- Error banners will link to HA config pages for quick repair.
