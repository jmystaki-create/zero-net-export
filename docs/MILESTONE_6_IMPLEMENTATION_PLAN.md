# Milestone 6: Diagnostics & Support Polish - Implementation Plan

**Date**: 2026-07-02  
**Release Target**: `v0.3.1` (patch) or `v0.4.0` (minor)  
**Status**: **READY TO IMPLEMENT**

---

## 1. Scope

**In Scope**:
- Internal log buffer (last 50 entries) in coordinator.
- `async_get_diagnostics()` method in coordinator.
- `zero_net_export.export_diagnostics` service.
- Diagnostics tab in frontend (log list, health summary, reconciliation trend).
- Error banners with repair guidance.
- "Download Diagnostics" button.
- Sensitive data filtering in export.

**Out of Scope**:
- Full HA log retrieval (only `zero_net_export` logs).
- Real-time log streaming (polling every 30s).
- Advanced charting for reconciliation trend (simple list first).

---

## 2. Backend Changes

### 2.1 `coordinator.py`

**Additions**:

1. **Internal Log Buffer**:
   ```python
   # In __init__:
   self._log_buffer: list[dict] = []  # Max 50 entries
   MAX_LOG_BUFFER_SIZE = 50
   ```

2. **Log Capture Helper**:
   ```python
   def _capture_log(self, level: str, message: str) -> None:
       """Capture a log entry in the internal buffer."""
       entry = {
           "timestamp": datetime.now(timezone.utc).isoformat(),
           "level": level,
           "message": message,
       }
       self._log_buffer.append(entry)
       if len(self._log_buffer) > MAX_LOG_BUFFER_SIZE:
           self._log_buffer.pop(0)
   ```

3. **Wrap Logger Calls** (or use a custom handler):
   - Option A: Replace `_LOGGER` calls with `self._capture_log()` + original `_LOGGER`.
   - Option B: Use a custom logging handler that captures messages.
   - **Decision**: Option A for simplicity (modify existing `_LOGGER.info/warning/error` calls to also call `_capture_log`).

4. **`async_get_diagnostics()` Method**:
   ```python
   async def async_get_diagnostics(self, hass: HomeAssistant) -> dict:
       """Return diagnostics data."""
       # Gather sensor states
       sensor_states = {}
       for entity_id in [
           "sensor.zero_net_export_status",
           "sensor.zero_net_export_executor_state",
           "sensor.zero_net_export_home_load_power",
           "sensor.zero_net_export_source_power",
           "sensor.zero_net_export_battery_power",
           "sensor.zero_net_export_surplus",
           "sensor.zero_net_export_last_reconciliation_error",
           "binary_sensor.zero_net_export_source_mismatch",
       ]:
           state = hass.states.get(entity_id)
           if state:
               sensor_states[entity_id] = {
                   "state": state.state,
                   "attributes": state.attributes,
               }

       # Gather config entry state
       config_entry = self.config_entry
       config_state = {
           "entry_id": config_entry.entry_id,
           "state": config_entry.state,
           "disabled_by": config_entry.disabled_by,
       }

       # Gather reconciliation history (from existing buffer)
       reconciliation_history = self._reconciliation_history[-100:]  # Last 100

       return {
           "log_buffer": self._log_buffer,
           "sensor_states": sensor_states,
           "config_entry": config_state,
           "reconciliation_history": reconciliation_history,
           "executor_paused": self._executor_paused,
           "last_action_timestamp": self._last_action_timestamp,
       }
   ```

5. **`async_export_diagnostics()` Method**:
   ```python
   async def async_export_diagnostics(self, hass: HomeAssistant) -> str:
       """Export diagnostics to a JSON file and return the path."""
       diagnostics = await self.async_get_diagnostics(hass)

       # Filter sensitive data
       def filter_sensitive(obj):
           if isinstance(obj, dict):
               return {
                   k: filter_sensitive(v)
                   for k, v in obj.items()
                   if k.lower() not in ["token", "password", "api_key", "secret"]
               }
           elif isinstance(obj, str):
               # Redact sensitive patterns
               return re.sub(r"(token|password|api_key|secret)=\S+", r"\1=REDACTED", obj)
           else:
               return obj

       diagnostics = filter_sensitive(diagnostics)

       # Write to file
       timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
       filename = f"zne-diagnostics-{timestamp}.json"
       filepath = hass.config.path(filename)

       with open(filepath, "w") as f:
           json.dump(diagnostics, f, indent=2)

       _LOGGER.info("Diagnostics exported to %s", filepath)
       return filename
   ```

### 2.2 `services.py`

**Additions**:

1. **Register Service**:
   ```python
   async def async_setup_services(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
       """Set up Zero Net Export services."""
       coordinator = hass.data[DOMAIN][config_entry.entry_id]

       async def handle_export_diagnostics(call: ServiceCall) -> None:
           filename = await coordinator.async_export_diagnostics(hass)
           # Return filename to caller (or store in hass.data for frontend to fetch)
           call.context.result = {"filename": filename}

       hass.services.async_register(
           DOMAIN,
           "export_diagnostics",
           handle_export_diagnostics,
       )
   ```

---

## 3. Frontend Changes

### 3.1 `zero-net-export-app.js`

**Additions**:

1. **New Tab Navigation**:
   ```javascript
   // In renderNavigation():
   <button
     class="tab-button ${this._activeTab === 'diagnostics' ? 'active' : ''}"
     @click=${() => (this._activeTab = 'diagnostics')}
   >
     Diagnostics
   </button>
   ```

2. **Diagnostics Tab Content**:
   ```javascript
   _renderDiagnosticsTab() {
     return html`
       <div class="diagnostics-section">
         <h2>Diagnostics</h2>
         
         <!-- Log Entries -->
         <div class="card">
           <h3>Recent Logs</h3>
           <ul class="log-list">
             ${this._diagnostics?.log_buffer.map(
               (entry) => html`\n                 <li class="log-entry level-${entry.level.toLowerCase()}">
                   <span class="timestamp">${entry.timestamp}</span>
                   <span class="message">${entry.message}</span>
                 </li>\`
             )}
           </ul>
         </div>

         <!-- Health Summary -->
         <div class="card">
           <h3>System Health</h3>
           <div class="health-summary">
             <div class="health-item">
               <span class="label">Status:</span>
               <span class="value">${this._diagnostics?.sensor_states["sensor.zero_net_export_status"]?.state}</span>
             </div>
             <div class="health-item">
               <span class="label">Executor:</span>
               <span class="value">${this._diagnostics?.sensor_states["sensor.zero_net_export_executor_state"]?.state}</span>
             </div>
             <div class="health-item">
               <span class="label">Last Action:</span>
               <span class="value">${this._diagnostics?.last_action_timestamp || "N/A"}</span>
             </div>
           </div>
         </div>

         <!-- Reconciliation Trend -->
         <div class="card">
           <h3>Reconciliation Trend (Last 100)</h3>
           <ul class="trend-list">
             ${this._diagnostics?.reconciliation_history.map(
               (entry) => html`\n                 <li class="trend-entry">
                   <span class="timestamp">${entry.timestamp}</span>
                   <span class="error">${entry.error_w} W</span>
                 </li>\`
             )}
           </ul>
         </div>

         <!-- Export Button -->
         <button class="export-button" @click=${this._handleExportDiagnostics}>
           Download Diagnostics
         </button>
       </div>
     `;
   }
   ```

3. **Error Banner**:
   ```javascript
   _renderErrorBanner() {
     const status = this._states?.["sensor.zero_net_export_status"]?.state;
     const mismatch = this._states?.["binary_sensor.zero_net_export_source_mismatch"]?.state;

     if (status === "blocked" || status === "error" || mismatch === "on") {
       return html`\n         <div class="error-banner">
           <div class="error-code">${status === "blocked" ? "SOURCE_BLOCKED" : "MISMATCH"}</div>
           <div class="error-message">
             ${status === "blocked" ? "One or more sources are missing or invalid." : "Source role mismatch detected."}
           </div>
           <button @click=${() => this._openConfigPage()}>
             Fix Configuration
           </button>
         </div>
       `;
     }
     return nothing;
   }
   ```

4. **Export Handler**:
   ```javascript
   async _handleExportDiagnostics() {
     try {
       await this.hass.callService("zero_net_export", "export_diagnostics");
       // Poll for file download (or show a message)
       alert("Diagnostics exported. Check your Home Assistant config folder.");
     } catch (error) {
       alert("Failed to export diagnostics: " + error.message);
     }
   }
   ```

5. **Polling for Diagnostics**:
   ```javascript
   connectedCallback() {
     super.connectedCallback();
     this._pollInterval = setInterval(() => this._refreshDiagnostics(), 30000);
   }

   disconnectedCallback() {
     super.disconnectedCallback();
     clearInterval(this._pollInterval);
   }

   async _refreshDiagnostics() {
     try {
       const diagnostics = await this.hass.callWS({
         type: "zero_net_export/get_diagnostics",
         config_entry_id: this._configEntryId,
       });
       this._diagnostics = diagnostics;
     } catch (error) {
       console.error("Failed to refresh diagnostics:", error);
     }
   }
   ```

---

## 4. Tests

### 4.1 Unit Tests

1. **`test_coordinator_diagnostics.py`**:
   - Test `async_get_diagnostics()` returns correct structure.
   - Test `async_export_diagnostics()` generates valid JSON.
   - Test log buffer captures entries and respects max size.
   - Test sensitive data filtering.

### 4.2 Integration Tests

1. **Service Call Test**:
   - Call `zero_net_export.export_diagnostics` service.
   - Verify file is created in `/config`.
   - Verify file contains expected data.

---

## 5. Validation Plan

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

## 6. Release Impact

- **User-Facing**: New Diagnostics tab, error banners, download button.
- **CHANGELOG**: Add "Added Diagnostics & Support Polish" section.
- **Breaking Changes**: None.

---

**Next Step**: Begin implementation (backend first, then frontend).
