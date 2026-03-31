const PANEL_GET_STATE = 'zero_net_export/panel/get_state';
const TABS = ['overview', 'setup', 'devices', 'diagnostics', 'settings'];

class ZeroNetExportPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = undefined;
    this._state = undefined;
    this._error = undefined;
    this._loading = true;
    this._activeTab = 'overview';
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

  _setTab(tab) {
    this._activeTab = tab;
    this._render();
  }

  _entry() {
    return this._state?.entries?.[0];
  }

  _metric(label, value, suffix = '') {
    const safeValue = value === null || value === undefined || value === '' ? '—' : `${value}${suffix}`;
    return `<div class="metric"><div class="label">${label}</div><div class="value">${safeValue}</div></div>`;
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
        <p><strong>Target export:</strong> ${overview.target_export_w ?? '—'} W</p>
        <p><strong>Deadband:</strong> ${overview.deadband_w ?? '—'} W</p>
        <p><strong>Battery reserve:</strong> ${overview.battery_reserve_soc ?? '—'} %</p>
        <p><strong>Reason:</strong> ${overview.reason || '—'}</p>
        <p><strong>Recommendation:</strong> ${overview.recommendation || '—'}</p>
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
          <td>${item.priority ?? '—'}</td>
          <td>${item.reason || '—'}</td>
        </tr>`)
      .join('');

    return `
      <section class="panel-section">
        <h3>Managed Devices</h3>
        <p><strong>Summary:</strong> ${devices.summary || '—'}</p>
        <p><strong>Devices:</strong> ${devices.device_count ?? 0} total / ${devices.usable_device_count ?? 0} usable</p>
        <p><strong>Nominal power:</strong> ${devices.controllable_nominal_power_w ?? '—'} W</p>
      </section>
      <section class="panel-section">
        <table>
          <thead><tr><th>Name</th><th>Type</th><th>Status</th><th>Power (W)</th><th>Priority</th><th>Reason</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="6">No managed devices configured yet.</td></tr>'}</tbody>
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
    return `
      <section class="panel-section">
        <h3>Settings</h3>
        <p>This first panel shell is intentionally read-only.</p>
        <p>Next milestones: source save flows, controller setting mutations, and guided device add/edit/remove.</p>
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
        .refresh {
          background: var(--primary-color);
          color: var(--text-primary-color);
          border: none;
          border-radius: 10px;
          padding: 10px 14px;
          cursor: pointer;
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
          <p>${this._state?.top_health_summary || 'Panel-first operator shell'}</p>
        </div>
        <button class="refresh">Refresh</button>
      </div>
      <div class="tabs">${tabs}</div>
      ${this._renderBody()}
    `;

    this.shadowRoot.querySelector('.refresh')?.addEventListener('click', () => this._loadState());
    this.shadowRoot.querySelectorAll('.tab').forEach((button) => {
      button.addEventListener('click', () => this._setTab(button.dataset.tab));
    });
  }
}

customElements.define('zero-net-export-panel', ZeroNetExportPanel);
