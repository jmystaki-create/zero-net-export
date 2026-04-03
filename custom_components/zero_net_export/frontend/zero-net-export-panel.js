const PANEL_GET_STATE = 'zero_net_export/panel/get_state';
const PANEL_SAVE_CONTROLLER = 'zero_net_export/panel/save_controller_settings';
const PANEL_RESET_CONTROLLER = 'zero_net_export/panel/reset_controller_overrides';
const PANEL_SAVE_SOURCES = 'zero_net_export/panel/save_sources';
const PANEL_ADD_DEVICE = 'zero_net_export/panel/add_device';
const PANEL_UPDATE_DEVICE = 'zero_net_export/panel/update_device';
const PANEL_DELETE_DEVICE = 'zero_net_export/panel/delete_device';
const PANEL_RESET_DEVICE = 'zero_net_export/panel/reset_device_overrides';
const TABS = ['overview', 'setup', 'devices', 'diagnostics', 'settings'];
const DEVICE_KINDS = [
  { value: 'fixed', label: 'Fixed Load' },
  { value: 'variable', label: 'Variable Load' },
];
const DEVICE_TEMPLATES = [
  {
    key: 'hot_water',
    label: 'Hot Water Diverter',
    description: 'Fixed resistive load such as a hot water service or relay-controlled heater.',
    values: {
      name: 'Hot Water',
      kind: 'fixed',
      adapter: 'fixed_toggle',
      nominal_power_w: 3600,
      min_power_w: 3600,
      max_power_w: 3600,
      step_w: 3600,
      priority: 100,
      enabled: true,
      min_on_seconds: 900,
      min_off_seconds: 900,
      cooldown_seconds: 60,
      max_active_seconds: null,
    },
  },
  {
    key: 'pool_pump',
    label: 'Pool Pump',
    description: 'Fixed load with longer run windows and anti-flap protection.',
    values: {
      name: 'Pool Pump',
      kind: 'fixed',
      adapter: 'fixed_toggle',
      nominal_power_w: 1100,
      min_power_w: 1100,
      max_power_w: 1100,
      step_w: 1100,
      priority: 140,
      enabled: true,
      min_on_seconds: 1800,
      min_off_seconds: 900,
      cooldown_seconds: 60,
      max_active_seconds: 28800,
    },
  },
  {
    key: 'ev_charger',
    label: 'EV Charger',
    description: 'Variable charger current/power target exposed through a number entity.',
    values: {
      name: 'EV Charger',
      kind: 'variable',
      adapter: 'variable_number',
      nominal_power_w: 7000,
      min_power_w: 1400,
      max_power_w: 7000,
      step_w: 230,
      priority: 80,
      enabled: true,
      min_on_seconds: 300,
      min_off_seconds: 300,
      cooldown_seconds: 30,
      max_active_seconds: null,
    },
  },
  {
    key: 'battery_charge_sink',
    label: 'Battery Charge Sink',
    description: 'Variable battery/inverter charge target used to absorb surplus while respecting reserve rules.',
    values: {
      name: 'Battery Charge Sink',
      kind: 'variable',
      adapter: 'variable_number',
      nominal_power_w: 5000,
      min_power_w: 500,
      max_power_w: 5000,
      step_w: 100,
      priority: 60,
      enabled: true,
      min_on_seconds: 120,
      min_off_seconds: 120,
      cooldown_seconds: 15,
      max_active_seconds: null,
    },
  },
  {
    key: 'smart_plug_load',
    label: 'Smart Plug Load',
    description: 'Small fixed discretionary load such as a dryer, dehumidifier, or heater on a smart plug.',
    values: {
      name: 'Smart Plug Load',
      kind: 'fixed',
      adapter: 'fixed_toggle',
      nominal_power_w: 800,
      min_power_w: 800,
      max_power_w: 800,
      step_w: 800,
      priority: 180,
      enabled: true,
      min_on_seconds: 600,
      min_off_seconds: 600,
      cooldown_seconds: 60,
      max_active_seconds: 14400,
    },
  },
];
const MODES = [
  { value: 'zero_export', label: 'Zero Export' },
  { value: 'soft_zero_export', label: 'Soft Zero Export' },
  { value: 'self_consumption_max', label: 'Self-Consumption Max' },
  { value: 'import_min', label: 'Import Min' },
  { value: 'manual_hold', label: 'Manual / Hold' },
];

const SOURCE_FIELDS = [
  { key: 'solar_power_entity', label: 'Solar Power', required: true },
  { key: 'solar_energy_entity', label: 'Solar Energy', required: true },
  { key: 'grid_import_power_entity', label: 'Grid Import Power', required: true },
  { key: 'grid_export_power_entity', label: 'Grid Export Power', required: true },
  { key: 'grid_import_energy_entity', label: 'Grid Import Energy', required: true },
  { key: 'grid_export_energy_entity', label: 'Grid Export Energy', required: true },
  { key: 'home_load_power_entity', label: 'Home Load Power', required: true },
  { key: 'battery_soc_entity', label: 'Battery SOC', required: false },
  { key: 'battery_charge_power_entity', label: 'Battery Charge Power', required: false },
  { key: 'battery_discharge_power_entity', label: 'Battery Discharge Power', required: false },
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
    this._editingDeviceKey = 'new';
    this._deviceDraft = {};
    this._selectedTemplateKey = 'custom';
    this._selectedEntryId = undefined;
    this._refreshTimer = undefined;
    this._copyStatus = undefined;
    this._boundVisibilityRefresh = () => {
      if (!document.hidden) {
        this._loadState({ force: true });
      }
    };
    this._boundWindowFocusRefresh = () => this._loadState({ force: true });
  }

  set hass(hass) {
    const firstHassAssignment = !this._hass && !!hass;
    this._hass = hass;
    if (firstHassAssignment && !this._state) {
      this._loadState();
      return;
    }
    this._render();
  }

  connectedCallback() {
    document.addEventListener('visibilitychange', this._boundVisibilityRefresh);
    window.addEventListener('focus', this._boundWindowFocusRefresh);
    this._startAutoRefresh();
    if (this._hass && !this._state) {
      this._loadState();
      return;
    }
    this._render();
  }

  disconnectedCallback() {
    document.removeEventListener('visibilitychange', this._boundVisibilityRefresh);
    window.removeEventListener('focus', this._boundWindowFocusRefresh);
    this._stopAutoRefresh();
  }

  _startAutoRefresh() {
    this._stopAutoRefresh();
    this._refreshTimer = window.setInterval(() => {
      if (!document.hidden) {
        this._loadState();
      }
    }, 15000);
  }

  _stopAutoRefresh() {
    if (this._refreshTimer) {
      window.clearInterval(this._refreshTimer);
      this._refreshTimer = undefined;
    }
  }

  async _loadState({ force = false } = {}) {
    if (!this._hass) {
      this._loading = false;
      this._render();
      return;
    }
    if (!force && (this._busy || document.hidden)) {
      return;
    }
    const showLoadingState = !this._state;
    if (showLoadingState) {
      this._loading = true;
      this._render();
    }
    try {
      this._state = await this._hass.callWS({ type: PANEL_GET_STATE });
      this._reconcileSelectedEntry();
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
      this._reconcileSelectedEntry();
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._busy = false;
      this._render();
    }
  }

  async _copySupportSnapshot() {
    const snapshot = this._entry()?.settings?.support_snapshot;
    if (!snapshot) {
      this._copyStatus = 'No support snapshot is available yet.';
      this._render();
      return;
    }
    try {
      await navigator.clipboard.writeText(snapshot);
      this._copyStatus = 'Support snapshot copied to clipboard.';
    } catch (err) {
      this._copyStatus = `Failed to copy support snapshot: ${err?.message || String(err)}`;
    }
    this._render();
  }

  _setTab(tab) {
    this._activeTab = tab;
    this._render();
  }

  _reconcileSelectedEntry() {
    const entries = this._state?.entries || [];
    if (!entries.length) {
      this._selectedEntryId = undefined;
      return;
    }
    if (entries.some((item) => item.entry_id === this._selectedEntryId)) {
      return;
    }
    this._selectedEntryId = this._state?.active_entry_id || entries[0]?.entry_id;
  }

  _setEntry(entryId) {
    this._selectedEntryId = entryId;
    this._editingDeviceKey = 'new';
    this._deviceDraft = {};
    this._selectedTemplateKey = 'custom';
    this._render();
  }

  _entry() {
    const entries = this._state?.entries || [];
    return entries.find((item) => item.entry_id === this._selectedEntryId)
      || entries.find((item) => item.entry_id === this._state?.active_entry_id)
      || entries[0];
  }

  _entryId() {
    return this._entry()?.entry_id;
  }

  _metric(label, value, suffix = '') {
    const safeValue = value === null || value === undefined || value === '' ? '—' : `${value}${suffix}`;
    return `<div class="metric"><div class="label">${label}</div><div class="value">${safeValue}</div></div>`;
  }

  _formatDateTime(value) {
    if (!value) {
      return '—';
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString();
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

  _deviceConfigItems(entry) {
    return entry?.devices?.configured_items || [];
  }

  _activeDeviceConfig(entry) {
    const items = this._deviceConfigItems(entry);
    if (!items.length || this._editingDeviceKey === 'new') {
      return null;
    }
    return items.find((item) => item.key === this._editingDeviceKey) || null;
  }

  _deviceFormValue(entry, field, fallback = '') {
    const active = this._activeDeviceConfig(entry);
    const draftValue = this._deviceDraft[field];
    const value = draftValue !== undefined ? draftValue : active?.[field];
    return value === null || value === undefined ? fallback : value;
  }

  _deviceKindValue(entry) {
    return this._deviceFormValue(entry, 'kind', 'fixed');
  }

  _deviceAdapterOptions(entry, kind) {
    return (entry?.devices?.adapter_options || []).filter((item) => item.kind === kind);
  }

  _deviceTemplate() {
    return DEVICE_TEMPLATES.find((item) => item.key === this._selectedTemplateKey) || null;
  }

  _activeDeviceRuntime(entry) {
    const key = this._editingDeviceKey;
    if (!key || key === 'new') {
      return null;
    }
    return (entry?.devices?.items || []).find((item) => item.key === key) || null;
  }

  _setDeviceDraft(values = {}, { preserveEntity = true } = {}) {
    const nextDraft = { ...this._deviceDraft, ...values };
    if (!preserveEntity && !('entity_id' in values)) {
      nextDraft.entity_id = '';
    }
    this._deviceDraft = nextDraft;
  }

  _resetDeviceDraft(entry, editingKey = this._editingDeviceKey) {
    this._deviceDraft = {};
    this._selectedTemplateKey = 'custom';
    if (!entry || editingKey === 'new') {
      return;
    }
    const active = (entry?.devices?.configured_items || []).find((item) => item.key === editingKey);
    if (!active) {
      return;
    }
    const template = DEVICE_TEMPLATES.find((item) => item.values.kind === active.kind && item.values.adapter === active.adapter);
    if (template) {
      this._selectedTemplateKey = template.key;
    }
  }

  _applyTemplate(entry, templateKey) {
    this._selectedTemplateKey = templateKey;
    if (templateKey === 'custom') {
      if (this._editingDeviceKey === 'new') {
        this._deviceDraft = {};
      } else {
        this._resetDeviceDraft(entry);
      }
      this._render();
      return;
    }

    const template = DEVICE_TEMPLATES.find((item) => item.key === templateKey);
    if (!template) {
      return;
    }

    const currentEntityId = this.shadowRoot.querySelector('#device-entity-id')?.value?.trim()
      || this._deviceFormValue(entry, 'entity_id', '');

    this._deviceDraft = {
      ...template.values,
      entity_id: currentEntityId,
    };
    this._render();
  }

  _captureDeviceDraft(entry) {
    const kind = this.shadowRoot.querySelector('#device-kind')?.value || this._deviceKindValue(entry);
    this._deviceDraft = {
      ...this._deviceDraft,
      name: this.shadowRoot.querySelector('#device-name')?.value ?? this._deviceFormValue(entry, 'name', ''),
      kind,
      entity_id: this.shadowRoot.querySelector('#device-entity-id')?.value ?? this._deviceFormValue(entry, 'entity_id', ''),
      adapter: this.shadowRoot.querySelector('#device-adapter')?.value ?? this._deviceFormValue(entry, 'adapter', ''),
      nominal_power_w: this.shadowRoot.querySelector('#device-nominal')?.value ?? this._deviceFormValue(entry, 'nominal_power_w', 0),
      min_power_w: this.shadowRoot.querySelector('#device-min-power')?.value ?? this._deviceFormValue(entry, 'min_power_w', 0),
      max_power_w: this.shadowRoot.querySelector('#device-max-power')?.value ?? this._deviceFormValue(entry, 'max_power_w', 0),
      step_w: this.shadowRoot.querySelector('#device-step')?.value ?? this._deviceFormValue(entry, 'step_w', 0),
      priority: this.shadowRoot.querySelector('#device-priority')?.value ?? this._deviceFormValue(entry, 'priority', 100),
      enabled: (this.shadowRoot.querySelector('#device-configured-enabled')?.value ?? `${this._deviceFormValue(entry, 'enabled', true)}`) === 'true',
      min_on_seconds: this.shadowRoot.querySelector('#device-min-on')?.value ?? this._deviceFormValue(entry, 'min_on_seconds', 300),
      min_off_seconds: this.shadowRoot.querySelector('#device-min-off')?.value ?? this._deviceFormValue(entry, 'min_off_seconds', 300),
      cooldown_seconds: this.shadowRoot.querySelector('#device-cooldown')?.value ?? this._deviceFormValue(entry, 'cooldown_seconds', 30),
      max_active_seconds: this.shadowRoot.querySelector('#device-max-active')?.value ?? this._deviceFormValue(entry, 'max_active_seconds', ''),
    };
  }

  _deviceEntityOptions(entry, kind) {
    const domains = kind === 'variable' ? ['number', 'input_number'] : ['switch', 'input_boolean'];
    return (entry?.devices?.available_entities || []).filter((item) => domains.includes(item.domain));
  }

  _readNumber(selector, fallback = 0) {
    const raw = this.shadowRoot.querySelector(selector)?.value;
    if (raw === '' || raw === null || raw === undefined) {
      return fallback;
    }
    return Number(raw);
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
    const readiness = setup.operator_readiness || {};
    const validation = setup.validation || {};
    const sourceMapping = setup.source_mapping || {};
    const sourceDiagnostics = setup.source_diagnostics || validation.source_diagnostics || {};
    const sourceSuggestions = setup.entity_suggestions || {};
    const calibrationHints = setup.calibration_hints || validation.calibration_hints || [];
    const entityOptions = (setup.available_entities || [])
      .map((item) => `<option value="${item.entity_id}">${item.label}</option>`)
      .join('');
    const sourceInputs = SOURCE_FIELDS.map((field) => `
      <label>
        <span>${field.label}${field.required ? ' *' : ''}</span>
        <input
          list="source-entity-options"
          id="source-${field.key}"
          value="${sourceMapping[field.key] || ''}"
          placeholder="sensor.example_${field.key}"
          ${this._busy ? 'disabled' : ''}
        />
        ${((sourceSuggestions[field.key]?.items || []).length)
          ? `<div class="suggestion-block">
              <div class="suggestion-label">Suggested matches · ${sourceSuggestions[field.key]?.description || ''}</div>
              <div class="chip-row">
                ${(sourceSuggestions[field.key].items || []).map((item) => `<button type="button" class="suggestion-chip" data-source-field="${field.key}" data-source-entity="${item.entity_id}" ${this._busy ? 'disabled' : ''}>${item.label}</button>`).join('')}
              </div>
            </div>`
          : `<div class="suggestion-block muted">No obvious ${field.label.toLowerCase()} candidates detected yet.</div>`}
      </label>
    `).join('');
    const sourceFreshness = validation.source_freshness || {};
    const freshnessRows = Object.entries(sourceFreshness)
      .map(([key, item]) => `<tr><td>${key}</td><td>${item.entity_id || '—'}</td><td>${item.stale ? 'Stale' : 'OK'}</td><td>${item.age_seconds ?? '—'}</td></tr>`)
      .join('');
    const diagnosticRows = Object.entries(sourceDiagnostics)
      .map(([key, item]) => {
        const issueSummary = Array.isArray(item.issues) && item.issues.length
          ? item.issues.map((issue) => `${issue.severity}: ${issue.message}`).join(' · ')
          : 'No issues reported';
        return `<tr>
          <td>${key}</td>
          <td>${item.entity_id || '—'}</td>
          <td>${item.status || '—'}</td>
          <td>${item.value ?? item.raw_state ?? '—'}</td>
          <td>${item.unit || '—'}</td>
          <td>${item.device_class || '—'}</td>
          <td>${item.state_class || '—'}</td>
          <td>${issueSummary}</td>
        </tr>`;
      })
      .join('');
    const hintItems = calibrationHints
      .map((item) => `<li>${item}</li>`)
      .join('');
    const readinessItems = (readiness.checklist || [])
      .map((item) => `<li><strong>${item.complete ? '✅' : '⬜'} ${item.label}</strong><br /><span class="muted">${item.detail || ''}</span></li>`)
      .join('');

    return `
      <section class="panel-section">
        <h3>Setup & Validation</h3>
        <p><strong>Diagnostic summary:</strong> ${setup.diagnostic_summary || '—'}</p>
        <p><strong>Stale data:</strong> ${setup.stale_data ? 'Yes' : 'No'}</p>
        <p><strong>Source mismatch:</strong> ${setup.source_mismatch ? 'Yes' : 'No'}</p>
        <p><strong>Stale source summary:</strong> ${setup.stale_source_summary || '—'}</p>
        <p class="muted">Save source mappings here to reload the integration with validated panel-first setup data.</p>
      </section>
      <section class="panel-section">
        <h3>Operator Readiness</h3>
        <p><strong>Current phase:</strong> ${readiness.phase || '—'}</p>
        <p><strong>Status:</strong> ${readiness.summary || 'No readiness summary published yet.'}</p>
        <p><strong>Next step:</strong> ${readiness.next_step || 'No next-step guidance available yet.'}</p>
        ${readinessItems ? `<div class="hint-list"><ul>${readinessItems}</ul></div>` : '<p class="muted">No readiness checklist available yet.</p>'}
      </section>
      ${hintItems ? `
      <section class="panel-section">
        <h3>Calibration Hints</h3>
        <div class="hint-list"><ul>${hintItems}</ul></div>
      </section>` : ''}
      <section class="panel-section">
        <h3>Source Mapping</h3>
        <div class="form-grid">${sourceInputs}
          <label>
            <span>Refresh Seconds</span>
            <input id="source-refresh-seconds" type="number" min="5" max="300" step="5" value="${sourceMapping.refresh_seconds ?? 30}" ${this._busy ? 'disabled' : ''} />
          </label>
        </div>
        <datalist id="source-entity-options">${entityOptions}</datalist>
        <div class="button-row">
          <button class="action-button" data-action="save-sources" ${this._busy ? 'disabled' : ''}>Save Source Mapping</button>
        </div>
      </section>
      <section class="panel-section">
        <h3>Mapped Source Freshness</h3>
        <table>
          <thead><tr><th>Role</th><th>Entity</th><th>Status</th><th>Age (s)</th></tr></thead>
          <tbody>${freshnessRows || '<tr><td colspan="4">No source diagnostics available yet.</td></tr>'}</tbody>
        </table>
      </section>
      <section class="panel-section">
        <h3>Mapped Source Diagnostics</h3>
        <p class="muted">Use this to confirm units, device classes, state classes, and validation issues before assuming a source is safe to drive control decisions.</p>
        <table>
          <thead><tr><th>Role</th><th>Entity</th><th>Status</th><th>Reading</th><th>Unit</th><th>Device Class</th><th>State Class</th><th>Issues</th></tr></thead>
          <tbody>${diagnosticRows || '<tr><td colspan="8">No source diagnostics available yet.</td></tr>'}</tbody>
        </table>
      </section>
    `;
  }

  _renderDevices(entry) {
    const devices = entry?.devices || {};
    const configured = devices.configured_items || [];
    const activeRuntime = this._activeDeviceRuntime(entry);
    const template = this._deviceTemplate();
    const selectedKind = this._deviceKindValue(entry);
    const adapterOptions = this._deviceAdapterOptions(entry, selectedKind)
      .map((item) => `<option value="${item.key}" ${this._deviceFormValue(entry, 'adapter', '') === item.key ? 'selected' : ''}>${item.label}</option>`)
      .join('');
    const entityOptions = this._deviceEntityOptions(entry, selectedKind)
      .map((item) => `<option value="${item.entity_id}">${item.label}</option>`)
      .join('');
    const deviceChooser = configured
      .map((item) => `<option value="${item.key}" ${this._editingDeviceKey === item.key ? 'selected' : ''}>${item.name}</option>`)
      .join('');
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
            <button class="small-button" data-edit-device="${item.key}" ${this._busy ? 'disabled' : ''}>Edit</button>
            <button class="small-button secondary" data-reset-device="${item.key}" ${this._busy ? 'disabled' : ''}>Reset</button>
          </td>
        </tr>`)
      .join('');

    const templateOptions = DEVICE_TEMPLATES
      .map((item) => `<option value="${item.key}" ${this._selectedTemplateKey === item.key ? 'selected' : ''}>${item.label}</option>`)
      .join('');

    const editorModeLabel = this._editingDeviceKey === 'new' ? 'Add new device' : `Editing ${this._deviceFormValue(entry, 'name', this._editingDeviceKey)}`;

    return `
      <section class="panel-section">
        <h3>Managed Devices</h3>
        <p><strong>Summary:</strong> ${devices.summary || '—'}</p>
        <p><strong>Devices:</strong> ${devices.device_count ?? 0} total / ${devices.usable_device_count ?? 0} usable</p>
        <p><strong>Nominal power:</strong> ${devices.controllable_nominal_power_w ?? '—'} W</p>
        <p class="muted">Add, edit, and remove devices here so normal setup no longer depends on raw JSON in the options flow.</p>
        ${(devices.parse_issues || []).length ? `<p class="error"><strong>Inventory issues:</strong> ${(devices.parse_issues || []).join(' · ')}</p>` : ''}
      </section>
      <section class="panel-section">
        <h3>Device Editor</h3>
        <p><strong>Editor mode:</strong> ${editorModeLabel}</p>
        <div class="form-grid">
          <label>
            <span>Template</span>
            <select id="device-template" ${this._busy ? 'disabled' : ''}>
              <option value="custom" ${this._selectedTemplateKey === 'custom' ? 'selected' : ''}>Custom device</option>
              ${templateOptions}
            </select>
          </label>
        </div>
        ${template ? `<div class="hint-list"><strong>${template.label}</strong><p class="muted">${template.description}</p></div>` : '<p class="muted">Pick a template to prefill a common device profile, then point it at the correct Home Assistant entity.</p>'}
        <div class="form-grid">
          <label>
            <span>Edit Device</span>
            <select id="device-edit-key" ${this._busy ? 'disabled' : ''}>
              <option value="new" ${this._editingDeviceKey === 'new' ? 'selected' : ''}>Add new device</option>
              ${deviceChooser}
            </select>
          </label>
          <label>
            <span>Name</span>
            <input id="device-name" value="${this._deviceFormValue(entry, 'name', '')}" ${this._busy ? 'disabled' : ''} />
          </label>
          <label>
            <span>Kind</span>
            <select id="device-kind" ${this._busy ? 'disabled' : ''}>
              ${DEVICE_KINDS.map((item) => `<option value="${item.value}" ${selectedKind === item.value ? 'selected' : ''}>${item.label}</option>`).join('')}
            </select>
          </label>
          <label>
            <span>Entity</span>
            <input list="device-entity-options" id="device-entity-id" value="${this._deviceFormValue(entry, 'entity_id', '')}" placeholder="switch.hot_water" ${this._busy ? 'disabled' : ''} />
          </label>
          <label>
            <span>Adapter</span>
            <select id="device-adapter" ${this._busy ? 'disabled' : ''}>${adapterOptions}</select>
          </label>
          <label>
            <span>Nominal Power (W)</span>
            <input id="device-nominal" type="number" min="1" value="${this._deviceFormValue(entry, 'nominal_power_w', 0)}" ${this._busy ? 'disabled' : ''} />
          </label>
          <label>
            <span>Min Power (W)</span>
            <input id="device-min-power" type="number" min="1" value="${this._deviceFormValue(entry, 'min_power_w', 0)}" ${this._busy ? 'disabled' : ''} />
          </label>
          <label>
            <span>Max Power (W)</span>
            <input id="device-max-power" type="number" min="1" value="${this._deviceFormValue(entry, 'max_power_w', 0)}" ${this._busy ? 'disabled' : ''} />
          </label>
          <label>
            <span>Step (W)</span>
            <input id="device-step" type="number" min="1" value="${this._deviceFormValue(entry, 'step_w', 0)}" ${this._busy ? 'disabled' : ''} />
          </label>
          <label>
            <span>Priority</span>
            <input id="device-priority" type="number" value="${this._deviceFormValue(entry, 'priority', 100)}" ${this._busy ? 'disabled' : ''} />
          </label>
          <label>
            <span>Configured Enabled</span>
            <select id="device-configured-enabled" ${this._busy ? 'disabled' : ''}>
              <option value="true" ${this._deviceFormValue(entry, 'enabled', true) ? 'selected' : ''}>Enabled</option>
              <option value="false" ${!this._deviceFormValue(entry, 'enabled', true) ? 'selected' : ''}>Disabled</option>
            </select>
          </label>
          <label>
            <span>Min On (s)</span>
            <input id="device-min-on" type="number" min="0" value="${this._deviceFormValue(entry, 'min_on_seconds', 300)}" ${this._busy ? 'disabled' : ''} />
          </label>
          <label>
            <span>Min Off (s)</span>
            <input id="device-min-off" type="number" min="0" value="${this._deviceFormValue(entry, 'min_off_seconds', 300)}" ${this._busy ? 'disabled' : ''} />
          </label>
          <label>
            <span>Cooldown (s)</span>
            <input id="device-cooldown" type="number" min="0" value="${this._deviceFormValue(entry, 'cooldown_seconds', 30)}" ${this._busy ? 'disabled' : ''} />
          </label>
          <label>
            <span>Max Active Runtime (s)</span>
            <input id="device-max-active" type="number" min="0" value="${this._deviceFormValue(entry, 'max_active_seconds', '')}" placeholder="blank for none" ${this._busy ? 'disabled' : ''} />
          </label>
        </div>
        <datalist id="device-entity-options">${entityOptions}</datalist>
        <div class="button-row">
          <button class="action-button" data-action="save-device" ${this._busy ? 'disabled' : ''}>${this._editingDeviceKey === 'new' ? 'Add Device' : 'Save Device'}</button>
          ${this._editingDeviceKey !== 'new' ? `<button class="action-button secondary" data-action="delete-device" ${this._busy ? 'disabled' : ''}>Delete Device</button>` : ''}
          <button class="action-button secondary" data-action="reset-device-form" ${this._busy ? 'disabled' : ''}>Reset Form</button>
          <button class="action-button secondary" data-action="new-device" ${this._busy ? 'disabled' : ''}>New Blank Device</button>
        </div>
        <p class="muted">${selectedKind === 'variable' ? 'Variable devices should point at a number/input_number entity that represents a live power or current target.' : 'Fixed loads should point at a switch/input_boolean entity that can be safely toggled by Zero Net Export.'}</p>
      </section>
      ${activeRuntime ? `
      <section class="panel-section">
        <h3>Selected Device Runtime</h3>
        <p><strong>Status:</strong> ${activeRuntime.status || '—'}</p>
        <p><strong>Usable:</strong> ${activeRuntime.usable ? 'Yes' : 'No'}</p>
        <p><strong>Reason:</strong> ${activeRuntime.reason || '—'}</p>
        <p><strong>Current power:</strong> ${activeRuntime.current_power_w ?? '—'} W</p>
        <p><strong>Current target:</strong> ${activeRuntime.current_target_power_w ?? '—'} W</p>
        <p><strong>Planned action:</strong> ${activeRuntime.planned_action || 'hold'} (${activeRuntime.planned_requested_power_w ?? '—'} W)</p>
        <p><strong>Guard:</strong> ${activeRuntime.guard_status || '—'}</p>
        <p><strong>Last result:</strong> ${activeRuntime.last_action_status || '—'} · ${activeRuntime.last_action_result_message || 'No recorded action yet.'}</p>
        <p><strong>Successful actions:</strong> ${activeRuntime.successful_action_count ?? 0} · <strong>Failed actions:</strong> ${activeRuntime.failed_action_count ?? 0}</p>
      </section>` : ''}
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
    const actionRows = (diagnostics.action_history || [])
      .map((item) => `
        <tr>
          <td>${this._formatDateTime(item.at)}</td>
          <td>${item.name || item.device_key || '—'}</td>
          <td>${item.action || '—'}</td>
          <td>${item.success ? 'Success' : 'Failed'}</td>
          <td>${item.requested_power_w ?? '—'}</td>
          <td>${item.message || '—'}</td>
        </tr>`)
      .join('');
    const sourceRows = Object.entries(diagnostics.source_diagnostics || {})
      .map(([key, item]) => {
        const freshness = diagnostics.source_freshness?.[key] || {};
        const issues = Array.isArray(item.issues) ? item.issues.join(' · ') : '—';
        return `
          <tr>
            <td>${key}</td>
            <td>${item.entity_id || '—'}</td>
            <td>${item.status || '—'}</td>
            <td>${freshness.stale ? 'Stale' : 'OK'}</td>
            <td>${freshness.age_seconds ?? '—'}</td>
            <td>${issues || '—'}</td>
          </tr>`;
      })
      .join('');
    const deviceRows = (diagnostics.device_items || [])
      .map((item) => `
        <tr>
          <td>${item.name || item.key || '—'}</td>
          <td>${item.planned_action || 'hold'}</td>
          <td>${item.guard_status || '—'}</td>
          <td>${item.planned_requested_power_w ?? item.current_target_power_w ?? '—'}</td>
          <td>${item.last_action_status || '—'}</td>
          <td>${item.last_action_result_message || item.reason || '—'}</td>
        </tr>`)
      .join('');
    const calibrationHints = (diagnostics.calibration_hints || [])
      .map((item) => `<li>${item}</li>`)
      .join('');
    return `
      <section class="panel-section">
        <h3>Diagnostics & Explanation</h3>
        <p><strong>Health:</strong> ${diagnostics.health_status || '—'}</p>
        <p><strong>Health summary:</strong> ${diagnostics.health_summary || '—'}</p>
        <p><strong>Control status:</strong> ${diagnostics.control_status || '—'}</p>
        <p><strong>Control summary:</strong> ${diagnostics.control_summary || '—'}</p>
        <p><strong>Control reason:</strong> ${diagnostics.control_reason || '—'}</p>
        <p><strong>Guard summary:</strong> ${diagnostics.control_guard_summary || '—'}</p>
        <p><strong>Plan counts:</strong> ${diagnostics.planned_action_count ?? 0} planned / ${diagnostics.executable_action_count ?? 0} executable / ${diagnostics.blocked_planned_action_count ?? 0} blocked</p>
        <p><strong>Planned power delta:</strong> ${diagnostics.planned_power_delta_w ?? '—'} W</p>
        <p><strong>Last action:</strong> ${diagnostics.last_action_summary || '—'}</p>
        <p><strong>Last action device:</strong> ${diagnostics.last_action_device || '—'}</p>
        <p><strong>Last action at:</strong> ${this._formatDateTime(diagnostics.last_action_at)}</p>
        <p><strong>Recent actions:</strong> ${diagnostics.recent_action_summary || '—'}</p>
        <p><strong>Last successful action:</strong> ${diagnostics.last_successful_action_summary || '—'}</p>
        <p><strong>Last successful at:</strong> ${this._formatDateTime(diagnostics.last_successful_action_at)}</p>
        <p><strong>Recent failures:</strong> ${diagnostics.recent_failure_summary || '—'}</p>
        <p><strong>Last failed device:</strong> ${diagnostics.last_failed_action_device || '—'}</p>
        <p><strong>Last failed message:</strong> ${diagnostics.last_failed_action_message || '—'}</p>
        <p><strong>Last failed at:</strong> ${this._formatDateTime(diagnostics.last_failed_action_at)}</p>
        <p><strong>Stale data:</strong> ${diagnostics.stale_data ? 'Yes' : 'No'}</p>
        <p><strong>Source mismatch:</strong> ${diagnostics.source_mismatch ? 'Yes' : 'No'}</p>
        <p><strong>Battery below reserve:</strong> ${diagnostics.battery_below_reserve ? 'Yes' : 'No'}</p>
        <p><strong>Stale source summary:</strong> ${diagnostics.stale_source_summary || '—'}</p>
      </section>
      <section class="panel-section">
        <h3>Recent Action Timeline</h3>
        <p><strong>Recorded actions:</strong> ${diagnostics.action_history_count ?? 0}</p>
        <table>
          <thead><tr><th>When</th><th>Device</th><th>Action</th><th>Result</th><th>Requested W</th><th>Message</th></tr></thead>
          <tbody>${actionRows || '<tr><td colspan="6">No action history recorded yet.</td></tr>'}</tbody>
        </table>
      </section>
      <section class="panel-section">
        <h3>Source Diagnostics</h3>
        <table>
          <thead><tr><th>Source</th><th>Entity</th><th>Status</th><th>Freshness</th><th>Age (s)</th><th>Issues</th></tr></thead>
          <tbody>${sourceRows || '<tr><td colspan="6">No source diagnostics available yet.</td></tr>'}</tbody>
        </table>
        ${calibrationHints ? `<div class="hint-list"><strong>Calibration hints</strong><ul>${calibrationHints}</ul></div>` : ''}
      </section>
      <section class="panel-section">
        <h3>Per-Device Explanation</h3>
        <table>
          <thead><tr><th>Device</th><th>Planned Action</th><th>Guard</th><th>Requested/Target W</th><th>Last Result</th><th>Explanation</th></tr></thead>
          <tbody>${deviceRows || '<tr><td colspan="6">No managed devices available yet.</td></tr>'}</tbody>
        </table>
      </section>
    `;
  }

  _renderSettings(entry) {
    const overview = entry?.overview || {};
    const settings = entry?.settings || {};
    const defaults = this._controllerDefaults(entry);
    const configuredDefaults = settings.controller_defaults || {};
    const operatorSummary = settings.operator_summary || {};
    const workflow = settings.workflow || {};
    const readiness = workflow.readiness || {};
    const links = settings.links || {};
    const modeOptions = MODES.map((mode) => `<option value="${mode.value}" ${overview.mode === mode.value ? 'selected' : ''}>${mode.label}</option>`).join('');
    const workflowItems = (workflow.normal_operator_path || [])
      .map((item) => `<li>${item}</li>`)
      .join('');
    const linkItems = Object.entries(links)
      .map(([key, value]) => `<li><a href="${value}" target="_blank" rel="noreferrer">${key.replaceAll('_', ' ')}</a></li>`)
      .join('');
    const supportSnapshot = settings.support_snapshot || '';
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
        <h3>Operator Defaults & Health</h3>
        <p><strong>Configured refresh interval:</strong> ${configuredDefaults.refresh_seconds ?? '—'} s</p>
        <p><strong>Configured target export:</strong> ${configuredDefaults.target_export_w ?? '—'} W</p>
        <p><strong>Configured deadband:</strong> ${configuredDefaults.deadband_w ?? '—'} W</p>
        <p><strong>Configured battery reserve:</strong> ${configuredDefaults.battery_reserve_soc ?? '—'} %</p>
        <p><strong>Device fleet:</strong> ${operatorSummary.device_count ?? 0} total / ${operatorSummary.enabled_device_count ?? 0} enabled / ${operatorSummary.usable_device_count ?? 0} usable</p>
        <p><strong>Health:</strong> ${operatorSummary.health_status || '—'}</p>
        <p><strong>Health summary:</strong> ${operatorSummary.health_summary || '—'}</p>
        <p><strong>Safe mode:</strong> ${operatorSummary.safe_mode ? 'Yes' : 'No'}</p>
        <p><strong>Stale data:</strong> ${operatorSummary.stale_data ? 'Yes' : 'No'}</p>
        <p><strong>Source mismatch:</strong> ${operatorSummary.source_mismatch ? 'Yes' : 'No'}</p>
      </section>
      <section class="panel-section">
        <h3>Panel-First Workflow</h3>
        <p><strong>Primary operator surface:</strong> ${workflow.panel_primary ? 'Panel app' : 'Not declared'}</p>
        <p><strong>YAML dashboard:</strong> ${workflow.dashboard_fallback_only ? 'Fallback/debug only' : 'Primary surface'}</p>
        <p><strong>JSON options flow:</strong> ${workflow.json_options_fallback_only ? 'Advanced fallback only' : 'Normal path'}</p>
        <p><strong>Readiness phase:</strong> ${readiness.phase || '—'}</p>
        <p><strong>Readiness summary:</strong> ${readiness.summary || '—'}</p>
        <p><strong>Recommended next step:</strong> ${readiness.next_step || '—'}</p>
        ${workflowItems ? `<ul>${workflowItems}</ul>` : '<p>No workflow guidance published yet.</p>'}
      </section>
      <section class="panel-section">
        <h3>Release & Support</h3>
        <p><strong>Entry:</strong> ${operatorSummary.entry_title || entry?.title || 'Not configured'}</p>
        <p><strong>Integration version:</strong> ${entry?.integration_version || operatorSummary.integration_version || this._state?.integration_version || '—'}</p>
        <p><strong>Config entry version:</strong> ${entry?.config_entry_version ?? operatorSummary.config_entry_version ?? '—'}</p>
        <p><strong>Panel schema version:</strong> ${this._state?.panel_schema_version ?? '—'}</p>
        <div class="button-row">
          <button class="action-button secondary" data-action="copy-support-snapshot" ${this._busy ? 'disabled' : ''}>Copy Support Snapshot</button>
        </div>
        ${this._copyStatus ? `<p><strong>Copy status:</strong> ${this._copyStatus}</p>` : ''}
        <label>
          <span>Support snapshot preview</span>
          <textarea readonly rows="16">${supportSnapshot}</textarea>
        </label>
        ${linkItems ? `<ul>${linkItems}</ul>` : '<p>No support links available.</p>'}
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

  async _saveSourcesFromForm() {
    const payload = {
      type: PANEL_SAVE_SOURCES,
      entry_id: this._entryId(),
      refresh_seconds: Number(this.shadowRoot.querySelector('#source-refresh-seconds')?.value ?? 30),
    };

    SOURCE_FIELDS.forEach((field) => {
      const value = this.shadowRoot.querySelector(`#source-${field.key}`)?.value?.trim() || '';
      payload[field.key] = value;
    });

    await this._callWS(payload);
  }

  async _saveDeviceFromForm() {
    const kind = this.shadowRoot.querySelector('#device-kind')?.value || 'fixed';
    const payload = {
      entry_id: this._entryId(),
      name: this.shadowRoot.querySelector('#device-name')?.value?.trim() || '',
      kind,
      entity_id: this.shadowRoot.querySelector('#device-entity-id')?.value?.trim() || '',
      adapter: this.shadowRoot.querySelector('#device-adapter')?.value || undefined,
      nominal_power_w: this._readNumber('#device-nominal', 0),
      priority: this._readNumber('#device-priority', 100),
      configured_enabled: this.shadowRoot.querySelector('#device-configured-enabled')?.value === 'true',
      min_on_seconds: this._readNumber('#device-min-on', 300),
      min_off_seconds: this._readNumber('#device-min-off', 300),
      cooldown_seconds: this._readNumber('#device-cooldown', 30),
    };

    const maxActiveRaw = this.shadowRoot.querySelector('#device-max-active')?.value;
    payload.max_active_seconds = maxActiveRaw === '' ? null : Number(maxActiveRaw);

    if (kind === 'variable') {
      payload.min_power_w = this._readNumber('#device-min-power', 0);
      payload.max_power_w = this._readNumber('#device-max-power', 0);
      payload.step_w = this._readNumber('#device-step', 0);
    }

    if (this._editingDeviceKey === 'new') {
      payload.type = PANEL_ADD_DEVICE;
      payload.enabled = payload.configured_enabled;
      delete payload.configured_enabled;
    } else {
      payload.type = PANEL_UPDATE_DEVICE;
      payload.device_key = this._editingDeviceKey;
      payload.save_config = true;
    }

    await this._callWS(payload);
    this._deviceDraft = {};
    this._selectedTemplateKey = 'custom';
  }

  _attachEventHandlers() {
    this.shadowRoot.querySelector('.refresh')?.addEventListener('click', () => this._loadState());
    this.shadowRoot.querySelector('#entry-picker')?.addEventListener('change', (event) => {
      this._setEntry(event.target.value);
    });
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

    this.shadowRoot.querySelector('[data-action="copy-support-snapshot"]')?.addEventListener('click', async () => {
      await this._copySupportSnapshot();
    });

    this.shadowRoot.querySelector('[data-action="save-sources"]')?.addEventListener('click', async () => {
      await this._saveSourcesFromForm();
    });

    this.shadowRoot.querySelectorAll('[data-source-field]').forEach((button) => {
      button.addEventListener('click', () => {
        const input = this.shadowRoot.querySelector(`#source-${button.dataset.sourceField}`);
        if (input) {
          input.value = button.dataset.sourceEntity || '';
        }
      });
    });

    const entry = this._entry();

    this.shadowRoot.querySelector('#device-edit-key')?.addEventListener('change', (event) => {
      this._editingDeviceKey = event.target.value;
      this._resetDeviceDraft(entry, this._editingDeviceKey);
      this._render();
    });

    this.shadowRoot.querySelector('#device-template')?.addEventListener('change', (event) => {
      this._captureDeviceDraft(entry);
      this._applyTemplate(entry, event.target.value);
    });

    this.shadowRoot.querySelector('#device-kind')?.addEventListener('change', () => {
      this._captureDeviceDraft(entry);
      this._render();
    });

    this.shadowRoot.querySelector('[data-action="save-device"]')?.addEventListener('click', async () => {
      await this._saveDeviceFromForm();
    });

    this.shadowRoot.querySelector('[data-action="new-device"]')?.addEventListener('click', () => {
      this._editingDeviceKey = 'new';
      this._deviceDraft = {};
      this._selectedTemplateKey = 'custom';
      this._render();
    });

    this.shadowRoot.querySelector('[data-action="reset-device-form"]')?.addEventListener('click', () => {
      this._resetDeviceDraft(entry);
      this._render();
    });

    this.shadowRoot.querySelector('[data-action="delete-device"]')?.addEventListener('click', async () => {
      if (this._editingDeviceKey === 'new') {
        return;
      }
      await this._callWS({ type: PANEL_DELETE_DEVICE, entry_id: this._entryId(), device_key: this._editingDeviceKey });
      this._editingDeviceKey = 'new';
      this._deviceDraft = {};
      this._selectedTemplateKey = 'custom';
    });

    this.shadowRoot.querySelectorAll('[data-edit-device]').forEach((button) => {
      button.addEventListener('click', () => {
        this._editingDeviceKey = button.dataset.editDevice;
        this._resetDeviceDraft(entry, this._editingDeviceKey);
        this._render();
      });
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
    const entryOptions = (this._state?.entries || [])
      .map((entry) => `<option value="${entry.entry_id}" ${this._entryId() === entry.entry_id ? 'selected' : ''}>${entry.title || entry.entry_id}</option>`)
      .join('');
    const multipleEntries = (this._state?.entry_count || 0) > 1;

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
          flex-wrap: wrap;
        }
        .header-actions {
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
        }
        .entry-picker {
          min-width: 260px;
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
        .hint-list {
          margin-top: 12px;
        }
        .suggestion-block {
          margin-top: 8px;
        }
        .suggestion-label {
          font-size: 12px;
          color: var(--secondary-text-color);
          margin-bottom: 6px;
        }
        .chip-row {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        .suggestion-chip {
          background: var(--secondary-background-color, var(--card-background-color));
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color);
          border-radius: 999px;
          padding: 6px 10px;
          cursor: pointer;
          text-align: left;
        }
        .live-chip {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border-radius: 999px;
          background: var(--card-background-color);
          border: 1px solid var(--divider-color);
          color: var(--secondary-text-color);
          font-size: 13px;
        }
        .live-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #2e7d32;
          box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.18);
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
        <div class="header-actions">
          <div class="live-chip" title="This panel refreshes automatically while visible and refreshes again when Home Assistant regains focus.">
            <span class="live-dot"></span>
            <span>Auto-refresh every 15s</span>
          </div>
          ${multipleEntries ? `
            <label class="entry-picker">
              <span>Active system</span>
              <select id="entry-picker" ${this._busy ? 'disabled' : ''}>${entryOptions}</select>
            </label>
          ` : ''}
          <button class="refresh" ${this._busy ? 'disabled' : ''}>Refresh</button>
        </div>
      </div>
      ${multipleEntries ? `<div class="panel-section"><p><strong>Configured systems:</strong> ${this._state?.entry_count || 0}. This panel can now switch between configured Zero Net Export entries instead of silently operating on the first one only.</p></div>` : ''}
      <div class="tabs">${tabs}</div>
      ${this._renderBody()}
    `;

    this._attachEventHandlers();
  }
}

if (!customElements.get('zero-net-export-panel')) {
  customElements.define('zero-net-export-panel', ZeroNetExportPanel);
}
