class ZeroNetExportApp extends HTMLElement {
  constructor() {
    super();
    this._activeSection = "overview";
    this._busy = false;
    this._message = "";
    this._onClick = this._onClick.bind(this);
  }

  set hass(value) {
    this._hass = value;
    this._render();
  }

  set panel(value) {
    this._panel = value;
    this._render();
  }

  connectedCallback() {
    this.addEventListener("click", this._onClick);
    this._render();
  }

  disconnectedCallback() {
    this.removeEventListener("click", this._onClick);
  }

  _state(entityId) {
    return this._hass && this._hass.states ? this._hass.states[entityId] : undefined;
  }

  _stateText(entityId, fallback = "unknown") {
    const state = this._state(entityId);
    if (!state || state.state === undefined || state.state === null) {
      return fallback;
    }
    return String(state.state);
  }

  _attr(entityId, attr, fallback = "") {
    const state = this._state(entityId);
    if (!state || !state.attributes || state.attributes[attr] === undefined || state.attributes[attr] === null) {
      return fallback;
    }
    return state.attributes[attr];
  }

  _entries() {
    const config = (this._panel && this._panel.config) || {};
    return Array.isArray(config.entries) ? config.entries : [];
  }

  _zneStates() {
    if (!this._hass || !this._hass.states) {
      return [];
    }
    return Object.entries(this._hass.states)
      .filter(([entityId]) => entityId.includes("zero_net_export") || entityId.includes("managed_devices_"))
      .sort(([left], [right]) => left.localeCompare(right));
  }

  _escape(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  _entityRow(label, entityId, fallback = "unknown") {
    const state = this._stateText(entityId, fallback);
    return `
      <div class="zne-row">
        <span>${this._escape(label)}</span>
        <strong>${this._escape(state)}</strong>
      </div>
    `;
  }

  _statusClass(value) {
    const normalized = String(value || "").toLowerCase();
    if (["on", "blocked", "missing", "error", "safe_mode"].includes(normalized)) {
      return "bad";
    }
    if (["off", "ok", "ready", "loaded", "available"].includes(normalized)) {
      return "good";
    }
    return "neutral";
  }

  _pill(label, value) {
    return `<span class="zne-pill ${this._statusClass(value)}">${this._escape(label)}: ${this._escape(value)}</span>`;
  }

  _navButton(id, label) {
    const active = this._activeSection === id ? "active" : "";
    return `<button class="zne-nav ${active}" type="button" data-section="${this._escape(id)}">${this._escape(label)}</button>`;
  }

  _selectedEntryId() {
    const entryInput = this.querySelector("[data-zne-entry-id]");
    if (entryInput && entryInput.value) {
      return entryInput.value;
    }
    const entries = this._entries();
    return entries.length === 1 ? entries[0].entry_id : "";
  }

  async _onClick(event) {
    const target = event.target.closest("button");
    if (!target) {
      return;
    }

    if (target.dataset.section) {
      this._activeSection = target.dataset.section;
      this._render();
      return;
    }

    if (target.dataset.route) {
      this._navigate(target.dataset.route);
      return;
    }

    if (target.dataset.zneAction) {
      await this._handleAction(target.dataset.zneAction, target);
    }
  }

  _navigate(path) {
    window.history.pushState(null, "", path);
    window.dispatchEvent(new Event("location-changed"));
  }

  async _handleAction(action, target) {
    if (!this._hass || !this._hass.callService) {
      this._message = "Home Assistant service API is not ready yet.";
      this._render();
      return;
    }

    this._busy = true;
    this._message = "";
    this._render();

    try {
      if (action === "toggle-enabled") {
        const current = this._stateText("switch.zero_net_export_enabled", "off");
        await this._hass.callService("switch", current === "on" ? "turn_off" : "turn_on", {
          entity_id: "switch.zero_net_export_enabled",
        });
        this._message = current === "on" ? "Control disabled." : "Control enabled.";
      }

      if (action === "set-mode") {
        const modeInput = this.querySelector("[data-zne-mode]");
        await this._hass.callService("select", "select_option", {
          entity_id: "select.zero_net_export_mode",
          option: modeInput.value,
        });
        this._message = `Mode update requested: ${modeInput.value}`;
      }

      if (action === "set-number") {
        const entityId = target.dataset.entityId;
        const valueInput = this.querySelector(`[data-zne-number="${entityId}"]`);
        await this._hass.callService("number", "set_value", {
          entity_id: entityId,
          value: Number(valueInput.value),
        });
        this._message = "Control value update requested.";
      }

      if (action === "managed-enable" || action === "managed-disable") {
        const deviceKey = this.querySelector("[data-zne-managed-key]").value.trim();
        if (!deviceKey) {
          throw new Error("Enter a managed-device key first.");
        }
        await this._hass.callService("zero_net_export", "update_managed_device", {
          entry_id: this._selectedEntryId(),
          device_key: deviceKey,
          enabled: action === "managed-enable",
        });
        this._message = action === "managed-enable" ? "Managed record enable requested." : "Managed record disable requested.";
      }

      if (action === "managed-remove") {
        const deviceKey = this.querySelector("[data-zne-managed-key]").value.trim();
        const confirm = this.querySelector("[data-zne-managed-confirm]").value.trim();
        if (!deviceKey) {
          throw new Error("Enter a managed-device key first.");
        }
        if (confirm !== "REMOVE FROM ZNE") {
          throw new Error("Type REMOVE FROM ZNE to confirm.");
        }
        await this._hass.callService("zero_net_export", "remove_managed_device", {
          entry_id: this._selectedEntryId(),
          device_key: deviceKey,
          confirm: true,
        });
        this._message = "Managed record removal requested. The original Home Assistant entity is left untouched.";
      }

      if (action === "copy-diagnostics") {
        const text = this._diagnosticText();
        await navigator.clipboard.writeText(text);
        this._message = "Diagnostics summary copied.";
      }
    } catch (error) {
      this._message = error && error.message ? error.message : String(error);
    } finally {
      this._busy = false;
      this._render();
    }
  }

  _diagnosticText() {
    return [
      `Zero Net Export ${this._stateText("sensor.zero_net_export_installed_version", "unknown")}`,
      `Status: ${this._stateText("sensor.zero_net_export_status", "unknown")}`,
      `Safe mode: ${this._stateText("binary_sensor.zero_net_export_safe_mode", "unknown")}`,
      `Sources: ${this._stateText("sensor.zero_net_export_source_blocker_summary", "unknown")}`,
      `Update: ${this._stateText("sensor.zero_net_export_update_summary", "unknown")}`,
    ].join("\n");
  }

  _overviewSection() {
    const entries = this._entries();
    const status = this._stateText("sensor.zero_net_export_status", "unknown");
    const safeMode = this._stateText("binary_sensor.zero_net_export_safe_mode", "unknown");
    const sourceMismatch = this._stateText("binary_sensor.zero_net_export_source_mismatch", "unknown");
    return `
      <section class="zne-panel">
        <div class="zne-panel-title">
          <h2>Overview</h2>
          <div>${this._pill("Status", status)} ${this._pill("Safe mode", safeMode)} ${this._pill("Source mismatch", sourceMismatch)}</div>
        </div>
        <div class="zne-grid">
          <div class="zne-card">
            <h3>Readiness</h3>
            ${this._entityRow("Controller", "sensor.zero_net_export_status")}
            ${this._entityRow("Command center", "sensor.zero_net_export_command_center_status")}
            ${this._entityRow("Next step", "sensor.zero_net_export_command_center_next_step")}
          </div>
          <div class="zne-card">
            <h3>Plans</h3>
            ${entries.length ? entries.map((entry) => `
              <div class="zne-plan">
                <strong>${this._escape(entry.title || "Zero Net Export")}</strong>
                <span>${this._escape(entry.entry_id || "")}</span>
                <span>${this._escape(entry.state || "unknown")}</span>
              </div>
            `).join("") : `<p class="zne-muted">No config entries are exposed to the app yet.</p>`}
          </div>
        </div>
      </section>
    `;
  }

  _sourcesSection() {
    const sources = [
      ["Solar power", "sensor.zero_net_export_solar_power_status"],
      ["Solar energy", "sensor.zero_net_export_solar_energy_status"],
      ["Grid import power", "sensor.zero_net_export_grid_import_power_status"],
      ["Grid export power", "sensor.zero_net_export_grid_export_power_status"],
      ["Grid import energy", "sensor.zero_net_export_grid_import_energy_status"],
      ["Grid export energy", "sensor.zero_net_export_grid_export_energy_status"],
      ["Home load power", "sensor.zero_net_export_home_load_power_status"],
      ["Battery SOC", "sensor.zero_net_export_battery_state_of_charge_status"],
    ];
    return `
      <section class="zne-panel">
        <div class="zne-panel-title">
          <h2>Sources</h2>
          <button type="button" data-route="/config/integrations/integration/zero_net_export">Open HA source setup</button>
        </div>
        <div class="zne-card">
          <h3>Current blockers</h3>
          <p>${this._escape(this._stateText("sensor.zero_net_export_source_blocker_summary", "No source blockers reported"))}</p>
        </div>
        <div class="zne-list">
          ${sources.map(([label, entityId]) => `
            <div class="zne-source">
              <span>${this._escape(label)}</span>
              ${this._pill("state", this._stateText(entityId, "missing"))}
            </div>
          `).join("")}
        </div>
      </section>
    `;
  }

  _managedDevicesSection() {
    const entries = this._entries();
    return `
      <section class="zne-panel">
        <div class="zne-panel-title">
          <h2>Managed Devices</h2>
          <button type="button" data-route="/config/integrations/integration/zero_net_export">Open HA managed devices setup</button>
        </div>
        <div class="zne-grid">
          <div class="zne-card">
            <h3>Fleet summary</h3>
            ${this._entityRow("Overview", "sensor.managed_devices_overview", "No managed-device overview yet")}
            ${this._entityRow("Attention", "sensor.managed_devices_attention", "No attention item")}
            ${this._entityRow("Ready next", "sensor.managed_devices_ready_next", "No ready item")}
            ${this._entityRow("Unmanaged backlog", "sensor.managed_devices_unmanaged_backlog_count", "0")}
          </div>
          <div class="zne-card">
            <h3>Scoped service action</h3>
            <label>Plan
              <select data-zne-entry-id>
                <option value="">Auto</option>
                ${entries.map((entry) => `<option value="${this._escape(entry.entry_id)}">${this._escape(entry.title || entry.entry_id)}</option>`).join("")}
              </select>
            </label>
            <label>Managed-device key
              <input data-zne-managed-key type="text" autocomplete="off" placeholder="pool_pump">
            </label>
            <div class="zne-actions">
              <button type="button" data-zne-action="managed-enable">Enable record</button>
              <button type="button" data-zne-action="managed-disable">Disable record</button>
            </div>
            <label>Removal confirmation
              <input data-zne-managed-confirm type="text" autocomplete="off" placeholder="REMOVE FROM ZNE">
            </label>
            <button class="danger" type="button" data-zne-action="managed-remove">Remove from ZNE only</button>
            <p class="zne-muted">Removal deletes the Zero Net Export managed record only. It does not remove the original Home Assistant entity.</p>
          </div>
        </div>
      </section>
    `;
  }

  _controlsSection() {
    const modeState = this._state("select.zero_net_export_mode");
    const options = modeState && Array.isArray(modeState.attributes.options) ? modeState.attributes.options : [this._stateText("select.zero_net_export_mode", "Zero export")];
    const numbers = [
      ["Target export", "number.zero_net_export_target_export", "W"],
      ["Deadband", "number.zero_net_export_deadband", "W"],
      ["Battery reserve", "number.zero_net_export_battery_reserve_soc", "%"],
    ];
    const enabled = this._stateText("switch.zero_net_export_enabled", "unknown");
    return `
      <section class="zne-panel">
        <div class="zne-panel-title">
          <h2>Controls</h2>
          ${this._pill("Enabled", enabled)}
        </div>
        <div class="zne-grid">
          <div class="zne-card">
            <h3>Live mode</h3>
            <label>Mode
              <select data-zne-mode>
                ${options.map((option) => `<option ${option === this._stateText("select.zero_net_export_mode") ? "selected" : ""}>${this._escape(option)}</option>`).join("")}
              </select>
            </label>
            <div class="zne-actions">
              <button type="button" data-zne-action="set-mode">Apply mode</button>
              <button type="button" data-zne-action="toggle-enabled">${enabled === "on" ? "Disable control" : "Enable control"}</button>
            </div>
          </div>
          <div class="zne-card">
            <h3>Policy values</h3>
            ${numbers.map(([label, entityId, unit]) => `
              <div class="zne-control-row">
                <label>${this._escape(label)}
                  <input data-zne-number="${this._escape(entityId)}" type="number" value="${this._escape(this._stateText(entityId, "0"))}">
                </label>
                <span>${this._escape(unit)}</span>
                <button type="button" data-zne-action="set-number" data-entity-id="${this._escape(entityId)}">Apply</button>
              </div>
            `).join("")}
          </div>
        </div>
      </section>
    `;
  }

  _runtimeSection() {
    return `
      <section class="zne-panel">
        <div class="zne-panel-title">
          <h2>Runtime</h2>
          ${this._pill("Active", this._stateText("binary_sensor.zero_net_export_active", "unknown"))}
        </div>
        <div class="zne-grid">
          <div class="zne-card">
            <h3>Power</h3>
            ${this._entityRow("Surplus", "sensor.zero_net_export_surplus")}
            ${this._entityRow("Active controlled power", "sensor.zero_net_export_active_controlled_power")}
            ${this._entityRow("Planned power delta", "sensor.zero_net_export_planned_power_delta")}
          </div>
          <div class="zne-card">
            <h3>Actions</h3>
            ${this._entityRow("Actions today", "sensor.zero_net_export_actions_today")}
            ${this._entityRow("Successful today", "sensor.zero_net_export_successful_actions_today")}
            ${this._entityRow("Total failed", "sensor.zero_net_export_total_failed_action_count")}
          </div>
        </div>
      </section>
    `;
  }

  _diagnosticsSection() {
    return `
      <section class="zne-panel">
        <div class="zne-panel-title">
          <h2>Diagnostics</h2>
          <button type="button" data-zne-action="copy-diagnostics">Copy summary</button>
        </div>
        <div class="zne-grid">
          <div class="zne-card">
            <h3>Release</h3>
            ${this._entityRow("Installed", "sensor.zero_net_export_installed_version")}
            ${this._entityRow("Update summary", "sensor.zero_net_export_update_summary")}
            ${this._entityRow("Changes", "sensor.zero_net_export_changes_preview")}
          </div>
          <div class="zne-card">
            <h3>Support</h3>
            ${this._entityRow("Safe mode", "binary_sensor.zero_net_export_safe_mode")}
            ${this._entityRow("Stale data", "binary_sensor.zero_net_export_stale_data")}
            ${this._entityRow("Command failure", "binary_sensor.zero_net_export_command_failure")}
          </div>
        </div>
      </section>
    `;
  }

  _settingsSection() {
    return `
      <section class="zne-panel">
        <div class="zne-panel-title">
          <h2>Settings</h2>
        </div>
        <div class="zne-card">
          <h3>Application boundary</h3>
          <p>The sidebar app is now the primary workflow surface. Native Home Assistant configure/device pages remain available as backend support paths while the app-native editors are filled in.</p>
        </div>
      </section>
    `;
  }

  _activeContent() {
    if (this._activeSection === "sources") {
      return this._sourcesSection();
    }
    if (this._activeSection === "managed") {
      return this._managedDevicesSection();
    }
    if (this._activeSection === "controls") {
      return this._controlsSection();
    }
    if (this._activeSection === "runtime") {
      return this._runtimeSection();
    }
    if (this._activeSection === "diagnostics") {
      return this._diagnosticsSection();
    }
    if (this._activeSection === "settings") {
      return this._settingsSection();
    }
    return this._overviewSection();
  }

  _render() {
    const config = (this._panel && this._panel.config) || {};
    const states = this._zneStates();
    const title = this._escape(config.title || "Zero Net Export");
    const version = this._escape(config.version || "unknown");
    const planCount = this._entries().length;
    const readyLabel = this._escape(this._hass ? "Connected to Home Assistant" : "Waiting for Home Assistant");

    this.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100vh;
          box-sizing: border-box;
          color: var(--primary-text-color);
          background: var(--primary-background-color);
          font-family: var(--paper-font-body1_-_font-family, Roboto, Arial, sans-serif);
        }

        * {
          box-sizing: border-box;
        }

        .zne-app {
          max-width: 1180px;
          margin: 0 auto;
          padding: 20px;
        }

        .zne-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 16px;
          border-bottom: 1px solid var(--divider-color);
          padding-bottom: 14px;
        }

        h1, h2, h3, p {
          margin-top: 0;
        }

        h1 {
          margin-bottom: 4px;
          font-size: 28px;
          line-height: 1.2;
          font-weight: 500;
        }

        h2 {
          margin-bottom: 0;
          font-size: 20px;
          line-height: 1.3;
          font-weight: 500;
        }

        h3 {
          margin-bottom: 10px;
          font-size: 15px;
          line-height: 1.3;
          font-weight: 500;
        }

        button, input, select {
          font: inherit;
        }

        button {
          min-height: 36px;
          border: 1px solid var(--divider-color);
          border-radius: 6px;
          padding: 7px 10px;
          color: var(--primary-text-color);
          background: var(--card-background-color);
          cursor: pointer;
        }

        button:hover {
          background: var(--secondary-background-color);
        }

        button.danger {
          color: var(--error-color, #c62828);
          border-color: var(--error-color, #c62828);
        }

        input, select {
          width: 100%;
          min-height: 36px;
          border: 1px solid var(--divider-color);
          border-radius: 6px;
          padding: 6px 8px;
          color: var(--primary-text-color);
          background: var(--card-background-color);
        }

        label {
          display: grid;
          gap: 5px;
          margin: 0 0 10px;
          color: var(--secondary-text-color);
          font-size: 13px;
        }

        label input, label select {
          color: var(--primary-text-color);
          font-size: 14px;
        }

        .zne-meta, .zne-muted {
          color: var(--secondary-text-color);
          font-size: 13px;
          line-height: 1.4;
        }

        .zne-status {
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          padding: 10px 12px;
          min-width: 220px;
          text-align: right;
          background: var(--card-background-color);
        }

        .zne-tabs {
          display: flex;
          gap: 6px;
          overflow-x: auto;
          padding: 12px 0;
          border-bottom: 1px solid var(--divider-color);
        }

        .zne-nav.active {
          border-color: var(--primary-color);
          color: var(--primary-color);
        }

        .zne-panel {
          padding-top: 16px;
        }

        .zne-panel-title {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 12px;
        }

        .zne-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
          gap: 12px;
        }

        .zne-card {
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          padding: 14px;
          background: var(--card-background-color);
          min-width: 0;
        }

        .zne-row, .zne-source, .zne-control-row {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          align-items: center;
          gap: 10px;
          padding: 8px 0;
          border-top: 1px solid var(--divider-color);
        }

        .zne-control-row {
          grid-template-columns: minmax(0, 1fr) auto auto;
        }

        .zne-row:first-of-type, .zne-source:first-child {
          border-top: 0;
        }

        .zne-list {
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          padding: 6px 14px;
          background: var(--card-background-color);
        }

        .zne-pill {
          display: inline-flex;
          align-items: center;
          min-height: 26px;
          border: 1px solid var(--divider-color);
          border-radius: 999px;
          padding: 3px 9px;
          margin: 2px;
          font-size: 12px;
          white-space: nowrap;
        }

        .zne-pill.good {
          color: var(--success-color, #2e7d32);
          border-color: var(--success-color, #2e7d32);
        }

        .zne-pill.bad {
          color: var(--error-color, #c62828);
          border-color: var(--error-color, #c62828);
        }

        .zne-plan {
          display: grid;
          gap: 3px;
          padding: 8px 0;
          border-top: 1px solid var(--divider-color);
        }

        .zne-plan:first-of-type {
          border-top: 0;
        }

        .zne-plan span {
          color: var(--secondary-text-color);
          font-size: 12px;
          overflow-wrap: anywhere;
        }

        .zne-actions {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin: 8px 0;
        }

        .zne-message {
          margin-top: 12px;
          min-height: 20px;
          color: var(--secondary-text-color);
        }

        .zne-busy {
          opacity: .6;
          pointer-events: none;
        }

        @media (max-width: 720px) {
          .zne-app {
            padding: 14px;
          }

          .zne-header, .zne-panel-title {
            display: block;
          }

          .zne-status {
            margin-top: 12px;
            text-align: left;
          }

          .zne-control-row {
            grid-template-columns: 1fr;
            align-items: stretch;
          }
        }
      </style>
      <main class="zne-app ${this._busy ? "zne-busy" : ""}">
        <header class="zne-header">
          <div>
            <h1>${title}</h1>
            <div class="zne-meta">Version ${version} · ${planCount} plan${planCount === 1 ? "" : "s"}</div>
          </div>
          <div class="zne-status">
            <strong>${readyLabel}</strong>
            <div class="zne-meta">${states.length} Zero Net Export app-visible entities</div>
          </div>
        </header>
        <nav class="zne-tabs" aria-label="Zero Net Export application sections">
          ${this._navButton("overview", "Overview")}
          ${this._navButton("sources", "Sources")}
          ${this._navButton("managed", "Managed Devices")}
          ${this._navButton("controls", "Controls")}
          ${this._navButton("runtime", "Runtime")}
          ${this._navButton("diagnostics", "Diagnostics")}
          ${this._navButton("settings", "Settings")}
        </nav>
        ${this._activeContent()}
        <div class="zne-message" role="status">${this._escape(this._message)}</div>
      </main>
    `;
  }
}

customElements.define("zero-net-export-app", ZeroNetExportApp);
