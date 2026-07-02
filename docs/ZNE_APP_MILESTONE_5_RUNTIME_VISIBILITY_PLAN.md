# Milestone 5: Runtime Visibility & Manual Override

**Status**: Ready for Implementation
**Target Release**: `v0.3.0` (or `v0.2.10` if strictly patch)
**Parent**: Milestone 4 (Source Health & Runtime Blocker Resolution)

---

## 1. User Outcome
The operator can see exactly how the system is reconciling (Surplus vs. Load vs. Battery) in real-time within the app, and can instantly pause or resume the automated executor if the system behaves unexpectedly, without needing to restart Home Assistant or edit YAML.

---

## 2. Acceptance Criteria (The "Done" Bar)

### 2.1 Live Reconciliation Card
- [ ] The App Overview card displays a dedicated "Reconciliation Status" section.
- [ ] **Data Points**:
  - `Home Load` (W)
  - `Source Power` (W)
  - `Battery Power` (W)
  - `Surplus/Deficit` (W) (calculated)
  - `Reconciliation Error` (W) (calculated difference)
  - `Confidence` (High/Medium/Low)
- [ ] **Refresh**: Updates every 10 seconds (or on coordinator refresh) without page reload.
- [ ] **Visuals**: Clear numeric display with unit labels; color-coded confidence indicator.

### 2.2 Executor Control
- [ ] A single "Pause/Resume Executor" toggle is visible on the Overview card.
- [ ] **Pause**: Stops the planner/executor from sending *new* control actions. Existing device states remain unchanged.
- [ ] **Resume**: Restarts the planner/executor loop.
- [ ] **State Sync**: The toggle reflects the actual runtime state (`running` vs `paused`) immediately.
- [ ] **Safety**: No control actions are sent while `paused`.

### 2.3 Safety & Logging
- [ ] Pausing the executor logs a clear `info` message: "Executor paused by user."
- [ ] Resuming logs: "Executor resumed by user."
- [ ] A new `sensor.zero_net_export_executor_state` is exposed with state `running` or `paused`.

### 2.4 Validation Proof
- [ ] Live browser screenshot showing the Reconciliation Card with live numbers.
- [ ] Live browser screenshot showing the "Pause" toggle being clicked and the executor stopping (verified by log: no new actions for 30s).
- [ ] Log proof: `sensor.zero_net_export_executor_state` updates to `paused`/`running`.

---

## 3. Feasibility Check (Pre-Implementation)

### 3.1 Backend (Custom Integration)
- **Feasibility**: **Supported**
- **Evidence**:
  - The `RuntimeState` class likely already tracks coordinator state.
  - Adding a `executor_state` attribute to the coordinator is trivial.
  - New services `zero_net_export.pause_executor` and `zero_net_export.resume_executor` can be registered in `services.py`.
  - A new sensor `sensor.zero_net_export_executor_state` can be added to the `SensorEntity` list.
- **Constraint**: Must not interfere with the source-health logic (Milestone 4). The pause flag must be checked *before* any control action is dispatched in the executor loop.

### 3.2 Frontend (App)
- **Feasibility**: **Supported**
- **Evidence**:
  - The app already subscribes to `sensor` entities for data display.
  - The `lit` framework supports reactive state updates on sensor changes.
  - A toggle button can trigger a service call via `this.hass.callService(...)`.
- **Constraint**: Must ensure the toggle state updates immediately on click (optimistic UI) and corrects if the backend state differs.

### 3.3 Integration
- **Feasibility**: **Supported**
- **Evidence**:
  - The coordinator loop can check a `self._paused` flag before executing the `planner` or `executor` steps.
  - The flag can be set by the service call handler.

---

## 4. Implementation Plan

### 4.1 Backend Changes
1.  **`coordinator.py`**:
    - Add `_paused: bool = False` attribute to `ZeroNetExportCoordinator`.
    - Modify `_async_update_data` or the executor loop to check `_paused` before dispatching actions.
    - Add `async_pause_executor()` and `async_resume_executor()` methods.
2.  **`services.py`**:
    - Register `zero_net_export.pause_executor` and `zero_net_export.resume_executor`.
    - Call coordinator methods from service handlers.
3.  **`sensor.py`**:
    - Add `ZeroNetExportExecutorStateSensor` exposing `running` or `paused`.
    - Update `sensor.zero_net_export_status` attributes to include executor state.
4.  **`manifest.json`**:
    - Bump version (e.g., `0.3.0` or `0.2.10`).

### 4.2 Frontend Changes
1.  **`zero-net-export-app.js`**:
    - Add "Reconciliation Status" section to the Overview card.
    - Subscribe to `sensor.zero_net_export_*` entities for live data.
    - Add "Pause/Resume" toggle button.
    - Bind toggle to `hass.callService('zero_net_export', 'pause_executor')` / `resume_executor`.
    - Ensure reactive updates on sensor state changes.

### 4.3 Tests
1.  **Unit Tests**:
    - Test `pause_executor` sets `_paused = True`.
    - Test `resume_executor` sets `_paused = False`.
    - Test executor loop skips actions when `_paused`.
    - Test sensor state updates correctly.
2.  **Integration Tests**:
    - Verify service calls succeed.
    - Verify no actions are dispatched while paused.

---

## 5. Validation Plan

### 5.1 Repo Validation
- [ ] Run `python3 -m unittest discover -s tests` (expect all tests to pass).
- [ ] Run `py_compile` on all changed files.
- [ ] Run `git diff --check`.

### 5.2 Live Validation (HACS Path)
1.  **Release**: Create GitHub Release `v0.3.0` (or `v0.2.10`).
2.  **Install**: Trigger HACS download on target HA instance.
3.  **Restart**: Restart Home Assistant.
4.  **Fingerprint**: Verify `overall_match=true`.
5.  **App Check**:
    - Open App Overview.
    - Verify Reconciliation numbers update live.
    - Verify `executor_state` sensor exists and is `running`.
6.  **Control Test**:
    - Click "Pause".
    - Verify toggle shows `Paused`.
    - Verify `sensor.zero_net_export_executor_state` becomes `paused`.
    - Verify logs: "Executor paused by user."
    - Wait 30s: Verify no new control actions in logs.
    - Click "Resume".
    - Verify toggle shows `Running`.
    - Verify logs: "Executor resumed by user."
    - Verify control actions resume.
7.  **Artifacts**:
    - Capture screenshots of Reconciliation Card (live).
    - Capture screenshots of Pause/Resume toggle.
    - Capture log snippets.

---

## 6. Risks & Mitigations
- **Risk**: Pausing leaves devices in an unsafe state.
  - **Mitigation**: Pause only stops *new* actions; existing states remain. Add a warning in the UI: "Pausing stops new actions. Existing device states remain unchanged."
- **Risk**: UI lag in state updates.
  - **Mitigation**: Use optimistic UI update on click, then correct if backend confirms.
- **Risk**: Version bump confusion.
  - **Mitigation**: Use `v0.3.0` for feature release, or `v0.2.10` if strictly patch. Document in CHANGELOG.

---

## 7. Release Impact
- **User-Facing**: New Overview card section, new Pause/Resume toggle, new `executor_state` sensor.
- **CHANGELOG**: Add "Added Runtime Visibility & Manual Override" section.

---

**Next Step**: Await approval to proceed with implementation.
