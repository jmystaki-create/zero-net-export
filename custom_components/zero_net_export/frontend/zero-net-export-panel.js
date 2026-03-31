const PANEL_GET_STATE = 'zero_net_export/panel/get_state';
const PANEL_SAVE_CONTROLLER = 'zero_net_export/panel/save_controller_settings';
const PANEL_RESET_CONTROLLER = 'zero_net_export/panel/reset_controller_overrides';
const PANEL_UPDATE_DEVICE = 'zero_net_export/panel/update_device';
const PANEL_RESET_DEVICE = 'zero_net_export/panel/reset_device_overrides';
const TABS = ['overview', 'setup', 'devices', 'diagnostics', 'settings'];
const MODES = [
  { value: 'zero_export', label: 'Zero Export' },
  { value: 'soft_zero_export', label: 'Soft Zero Export' },
  { value: 'self_consumption_max', label: 'Self-Consumption Max' },
  { value: 'import_min', label: 'Import Min' },
  { value: 'manual_hold', label: 'Manual / Hold' },
];

class ZeroNetExportPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = undefined;
    this._state = undefined;
    this._error = undefined;
    this._loading = true;
    this._activeTab = 'overview';
    this._busy = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._state && !this._loading) {
      this._loadState();
      return;
    }
    this._render();
  }

  connectedCallback() {
    this._loadState();
  }

  async _loadState() {
    if (!this._hass) {
      return;
    }
    this._loading = true;
    this._render();
    try {
      this._state = await this._hass.callWS({ type: PANEL_GET_STATE });
      this._error = undefined;
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _callWS(payload) {
    if (!this._hass || this._busy) {
      return;
    }
    this._busy = true;
    this._error = undefined;
    this._render();
    try {
      this._state = await this._hass.callWS(payload);
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._busy = false;
      this._render();
    }
  }

  _setTab(tab) {
    this._activeTab = tab;
    this._render();
  }

  _entry() {
    return this._state?.entries?.[0];
  }

  _entryId() {
    return this._entry()?.entry_id;
  }

  _metric(label, value, suffix = '') {
    const safeValue = value === null || value === undefined || value === '' ? '—' : `${value}${suffix}`;
    return `<div class="metric"><div class="label">${label}</div><div class="value">${safeValue}</div></div>`;
  }

  _controllerDefaults(entry) {
    const settings = entry?.overview?.controller_settings || {};
    return {
      configured_target_export_w: settings.configured_target_export_w,
      configured_deadband_w: settings.configured_deadband_w,
      configured_battery_reserve_soc: settings.configured_battery_reserve_soc,
      target_export_override_active: settings.target_export_override_active,
      deadband_override_active: settings.deadband_override_active,
      battery_reserve_override_active: settings.battery_reserve_override_active,
    };
  }

  _renderOverview(entry) {
    const overview = entry?.overview || {};
    return `
      <section class="card-grid">
        ${this._metric('Solar', overview.solar_power_w, ' W')}
        ${this._metric('Home Load', overview.home_load_power_w, ' W')}
        ${this._metric('Grid Import', overview.grid_import_power_w, ' W')}
        ${this._metric('Grid Export', overview.grid_export_power_w, ' W')}
        ${this._metric('Battery SOC', overview.battery_soc, ' %')}
        ${this._metric('Surplus', overview.surplus_w, ' W')}
      </section>
      <section class="panel-section">
        <h3>Controller</h3>
        <p><strong>Mode:</strong> ${overview.mode || '—'}</p>
        <p><strong>Status:</strong> ${overview.status || '—'}</p>
        <p><strong>Health:</strong> ${overview.health_status || '—'}</p>
        <p><strong>Enabled:</strong> ${overview.enabled ? 'Yes' : 'No'}</p>
        <p><strong>Target export:</strong> ${overview.target_export_w ?? '—'} W</p>
        <p><strong>Deadband:</strong> ${overview.deadband_w ?? '—'} W</p>
        <p><strong>Battery reserve:</strong> ${overview.battery_reserve_soc ?? '—'} %</p>
        <p><strong>Reason:</strong> ${overview.reason || '—'}</p>
        <p><strong>Recommendation:</strong> ${overview.recommendation || '—'}</p>
      </section>
      <section class="panel-section">
        <h3>Quick Actions</h3>
        <div class="button-row">
          <button class="action-button" data-action="controller-enabled" data-value="true" ${this._busy ? 'disabled' : ''}>Enable Control</button>
          <button class="action-button secondary" data-action="controller-enabled" data-value="false" ${this._busy ? 'disabled' : ''}>Disable Control</button>
          <button class="action-button secondary" data-action="reset-controller" ${this._busy ? 'disabled' : ''}>Reset Overrides</button>
        </div>
      </section>
    `;
  }

  _renderSetup(entry) {
    const setup = entry?.setup || {};
    const validation = setup.validation || {};
    const sourceFreshness = validation.source_freshness || {};
    const freshnessRows = Object.entries(sourceFreshness)
      .map(([key, item]) => `<tr><td>${key}</td><td>${item.entity_id || '—'}</td><td>${item.stale ? 'Stale' : 'OK'}</td><td>${item.age_seconds ?? '—'}</td></tr>`)
      .join('');

    return `
      <section class="panel-section">
        <h3>Setup & Validation</h3>
        <p><strong>Diagnostic summary:</strong> ${setup.diagnostic_summary || '—'}</p>
        <p><strong>Stale data:</strong> ${setup.stale_data ? 'Yes' : 'No'}</p>
        <p><strong>Source mismatch:</strong> ${setup.source_mismatch ? 'Yes' : 'No'}</p>
        <p><strong>Stale source summary:</strong> ${setup.stale_source_summary || '—'}</p>
        <p class="muted">Source mapping save flows are the next panel-first setup milestone; current setup state is read through the normalized backend payload.</p>
      </section>
      <section class="panel-section">
        <h3>Mapped Source Freshness</h3>
        <table>
          <thead><tr><th>Role</th><th>Entity</th><th>Status</th><th>Age (s)</th></tr></thead>
          <tbody>${freshnessRows || '<tr><td colspan="4">No source diagnostics available yet.</td></tr>'}</tbody>
        </table>
      </section>
    `;
  }

  _renderDevices(entry) {
    const devices = entry?.devices || {};
    const rows = (devices.items || [])
      .map((item) => `
        <tr>
          <td>${item.name || item.key || '—'}</td>
          <td>${item.kind || '—'}</td>
          <td>${item.usable ? 'Usable' : 'Blocked'}</td>
          <td>${item.current_power_w ?? '—'}</td>
          <td>
            <input
              class="priority-input"
              type="number"
              value="${item.effective_priority ?? item.priority ?? 100}"
              data-device-priority="${item.key}"
              ${this._busy ? 'disabled' : ''}
            />
          </td>
          <td>
            <label class="toggle-row">
              <input type="checkbox" data-device-enabled="${item.key}" ${item.effective_enabled ? 'checked' : ''} ${this._busy ? 'disabled' : ''} />
              <span>${item.effective_enabled ? 'Enabled' : 'Disabled'}</span>
            </label>
          </td>
          <td>${item.reason || '—'}</td>
          <td>
            <button class="small-button secondary" data-reset-device="${item.key}" ${this._busy ? 'disabled' : ''}>Reset</button>
          </td>
        </tr>`)
      .join('');

    return `
      <section class="panel-section">
        <h3>Managed Devices</h3>
        <p><strong>Summary:</strong> ${devices.summary || '—'}</p>
        <p><strong>Devices:</strong> ${devices.device_count ?? 0} total / ${devices.usable_device_count ?? 0} usable</p>
        <p><strong>Nominal power:</strong> ${devices.controllable_nominal_power_w ?? '—'} W</p>
        <p class="muted">This panel now supports runtime enable/disable and priority overrides. Full add/edit/remove onboarding is the next device milestone.</p>
      </section>
      <section class="panel-section">
        <table>
          <thead><tr><th>Name</th><th>Type</th><th>Status</th><th>Power (W)</th><th>Priority</th><th>Enabled</th><th>Reason</th><th>Overrides</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="8">No managed devices configured yet.</td></tr>'}</tbody>
        </table>
      </section>
    `;
  }

  _renderDiagnostics(entry) {
    const diagnostics = entry?.diagnostics || {};
    return `
      <section class="panel-section">
        <h3>Diagnostics</h3>
        <p><strong>Control status:</strong> ${diagnostics.control_status || '—'}</p>
        <p><strong>Control summary:</strong> ${diagnostics.control_summary || '—'}</p>
        <p><strong>Guard summary:</strong> ${diagnostics.control_guard_summary || '—'}</p>
        <p><strong>Last action:</strong> ${diagnostics.last_action_summary || '—'}</p>
        <p><strong>Recent actions:</strong> ${diagnostics.recent_action_summary || '—'}</p>
        <p><strong>Recent failures:</strong> ${diagnostics.recent_failure_summary || '—'}</p>
      </section>
    `;
  }

  _renderSettings(entry) {
    const overview = entry?.overview || {};
    const defaults = this._controllerDefaults(entry);
    const modeOptions = MODES.map((mode) => `<option value="${mode.value}" ${overview.mode === mode.value ? 'selected' : ''}>${mode.label}</option>`).join('');
    return `
      <section class="panel-section">
        <h3>Controller Settings</h3>
        <div class="form-grid">
          <label>
            <span>Enabled</span>
            <select id="controller-enabled" ${this._busy ? 'disabled' : ''}>
              <option value="true" ${overview.enabled ? 'selected' : ''}>Enabled</option>
              <option value="false" ${!overview.enabled ? 'selected' : ''}>Disabled</option>
            </select>
          </label>
          <label>
            <span>Mode</span>
            <select id="controller-mode" ${this._busy ? 'disabled' : ''}>${modeOptions}</select>
          </label>
          <label>
            <span>Target Export (W)</span>
            <input id="controller-target" type="number" value="${overview.target_export_w ?? 0}" ${this._busy ? 'disabled' : ''} />
          </label>
          <label>
            <span>Deadband (W)</span>
            <input id="controller-deadband" type="number" min="0" value="${overview.deadband_w ?? 0}" ${this._busy ? 'disabled' : ''} />
          </label>
          <label>
            <span>Battery Reserve (%)</span>
            <input id="controller-reserve" type="number" min="0" max="100" value="${overview.battery_reserve_soc ?? 0}" ${this._busy ? 'disabled' : ''} />
          </label>
        </div>
        <div class="button-row">
          <button class="action-button" data-action="save-controller" ${this._busy ? 'disabled' : ''}>Save Runtime Settings</button>
          <button class="action-button secondary" data-action="reset-controller" ${this._busy ? 'disabled' : ''}>Reset to Config Defaults</button>
        </div>
        <p><strong>Configured defaults:</strong> target ${defaults.configured_target_export_w ?? '—'} W, deadband ${defaults.configured_deadband_w ?? '—'} W, reserve ${defaults.configured_battery_reserve_soc ?? '—'} %</p>
        <p><strong>Override state:</strong> target ${defaults.target_export_override_active ? 'active' : 'default'}, deadband ${defaults.deadband_override_active ? 'active' : 'default'}, reserve ${defaults.battery_reserve_override_active ? 'active' : 'default'}</p>
      </section>
      <section class="panel-section">
        <h3>Panel Status</h3>
        <p><strong>Entry:</strong> ${entry?.title || 'Not configured'}</p>
        <p><strong>Schema version:</strong> ${this._state?.panel_schema_version ?? '—'}</p>
      </section>
    `;
  }

  _renderBody() {
    if (this._loading) {
      return `<div class="empty">Loading Zero Net Export panel…</div>`;
    }
    if (this._error) {
      return `<div class="empty error">Failed to load panel state: ${this._error}</div>`;
    }
    const entry = this._entry();
    if (!entry) {
      return `<div class="empty">Zero Net Export is not configured yet. Add the integration first, then reopen this panel.</div>`;
    }
    switch (this._activeTab) {
      case 'setup':
        return this._renderSetup(entry);
      case 'devices':
        return this._renderDevices(entry);
      case 'diagnostics':
        return this._renderDiagnostics(entry);
      case 'settings':
        return this._renderSettings(entry);
      default:
        return this._renderOverview(entry);
    }
  }

  async _saveControllerFromForm() {
    const enabledValue = this.shadowRoot.querySelector('#controller-enabled')?.value;
    const modeValue = this.shadowRoot.querySelector('#controller-mode')?.value;
    const targetValue = Number(this.shadowRoot.querySelector('#controller-target')?.value ?? 0);
    const deadbandValue = Number(this.shadowRoot.querySelector('#controller-deadband')?.value ?? 0);
    const reserveValue = Number(this.shadowRoot.querySelector('#controller-reserve')?.value ?? 0);

    await this._callWS({
      type: PANEL_SAVE_CONTROLLER,
      entry_id: this._entryId(),
      enabled: enabledValue === 'true',
      mode: modeValue,
      target_export_w: targetValue,
      deadband_w: deadbandValue,
      battery_reserve_soc: reserveValue,
    });
  }

  _attachEventHandlers() {
    this.shadowRoot.querySelector('.refresh')?.addEventListener('click', () => this._loadState());
    this.shadowRoot.querySelectorAll('.tab').forEach((button) => {
      button.addEventListener('click', () => this._setTab(button.dataset.tab));
    });

    this.shadowRoot.querySelectorAll('[data-action="controller-enabled"]').forEach((button) => {
      button.addEventListener('click', async () => {
        await this._callWS({
          type: PANEL_SAVE_CONTROLLER,
          entry_id: this._entryId(),
          enabled: button.dataset.value === 'true',
        });
      });
    });

    this.shadowRoot.querySelectorAll('[data-action="reset-controller"]').forEach((button) => {
      button.addEventListener('click', async () => {
        await this._callWS({
          type: PANEL_RESET_CONTROLLER,
          entry_id: this._entryId(),
        });
      });
    });

    this.shadowRoot.querySelector('[data-action="save-controller"]')?.addEventListener('click', async () => {
      await this._saveControllerFromForm();
    });

    this.shadowRoot.querySelectorAll('[data-device-enabled]').forEach((input) => {
      input.addEventListener('change', async () => {
        await this._callWS({
          type: PANEL_UPDATE_DEVICE,
          entry_id: this._entryId(),
          device_key: input.dataset.deviceEnabled,
          enabled: input.checked,
        });
      });
    });

    this.shadowRoot.querySelectorAll('[data-device-priority]').forEach((input) => {
      input.addEventListener('change', async () => {
        await this._callWS({
          type: PANEL_UPDATE_DEVICE,
          entry_id: this._entryId(),
          device_key: input.dataset.devicePriority,
          priority: Number(input.value),
        });
      });
    });

    this.shadowRoot.querySelectorAll('[data-reset-device]').forEach((button) => {
      button.addEventListener('click', async () => {
        await this._callWS({
          type: PANEL_RESET_DEVICE,
          entry_id: this._entryId(),
          device_key: button.dataset.resetDevice,
        });
      });
    });
  }

  _render() {
    const tabs = TABS.map((tab) => `
      <button class="tab ${this._activeTab === tab ? 'active' : ''}" data-tab="${tab}">${tab}</button>
    `).join('');

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          padding: 16px;
          color: var(--primary-text-color);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
        }
        .title h1 {
          margin: 0;
          font-size: 28px;
        }
        .title p {
          margin: 4px 0 0;
          color: var(--secondary-text-color);
        }
        .refresh,
        .action-button,
        .small-button {
          background: var(--primary-color);
          color: var(--text-primary-color);
          border: none;
          border-radius: 10px;
          padding: 10px 14px;
          cursor: pointer;
        }
        .small-button {
          padding: 6px 10px;
          border-radius: 8px;
        }
        .secondary {
          background: var(--card-background-color);
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color);
        }
        button:disabled,
        input:disabled,
        select:disabled {
          opacity: 0.6;
          cursor: default;
        }
        .tabs {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-bottom: 16px;
        }
        .tab {
          border: 1px solid var(--divider-color);
          background: var(--card-background-color);
          color: inherit;
          border-radius: 999px;
          padding: 8px 14px;
          text-transform: capitalize;
          cursor: pointer;
        }
        .tab.active {
          border-color: var(--primary-color);
          color: var(--primary-color);
        }
        .card-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 12px;
          margin-bottom: 16px;
        }
        .metric,
        .panel-section {
          background: var(--card-background-color);
          border-radius: 16px;
          padding: 16px;
          box-shadow: var(--ha-card-box-shadow, none);
        }
        .metric .label {
          color: var(--secondary-text-color);
          font-size: 12px;
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 0.04em;
        }
        .metric .value {
          font-size: 24px;
          font-weight: 600;
        }
        .panel-section {
          margin-bottom: 16px;
        }
        .button-row {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 12px;
        }
        .form-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 12px;
        }
        label {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .toggle-row {
          flex-direction: row;
          align-items: center;
        }
        input,
        select {
          background: var(--card-background-color);
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color);
          border-radius: 10px;
          padding: 10px 12px;
        }
        .priority-input {
          width: 90px;
        }
        .muted {
          color: var(--secondary-text-color);
        }
        table {
          width: 100%;
          border-collapse: collapse;
        }
        th, td {
          text-align: left;
          padding: 10px 8px;
          border-bottom: 1px solid var(--divider-color);
          vertical-align: top;
        }
        .empty {
          background: var(--card-background-color);
          border-radius: 16px;
          padding: 24px;
        }
        .error {
          color: var(--error-color);
        }
      </style>
      <div class="header">
        <div class="title">
          <h1>Zero Net Export</h1>
          <p>${this._state?.top_health_summary || 'Panel-first operator shell'}${this._busy ? ' · Saving…' : ''}</p>
        </div>
        <button class="refresh" ${this._busy ? 'disabled' : ''}>Refresh</button>
      </div>
      <div class="tabs">${tabs}</div>
      ${this._renderBody()}
    `;

    this._attachEventHandlers();
  }
}

customElements.define('zero-net-export-panel', ZeroNetExportPanel);
