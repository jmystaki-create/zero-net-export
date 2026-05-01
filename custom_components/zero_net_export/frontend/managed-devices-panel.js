class ZeroNetExportManagedDevicesPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  set panel(panel) {
    this._panel = panel;
    this.render();
  }

  connectedCallback() {
    this.render();
  }

  css() {
    return `
      <style>
        :host { display:block; padding:24px; box-sizing:border-box; color:var(--primary-text-color); }
        .wrap { max-width:1040px; margin:0 auto; }
        .header { margin-bottom:18px; }
        h1 { font-size:28px; margin:0 0 6px; font-weight:500; }
        h2 { font-size:20px; margin:0 0 10px; font-weight:500; }
        .sub { color:var(--secondary-text-color); font-size:14px; line-height:1.45; }
        .tabs { display:flex; flex-wrap:wrap; gap:8px; margin:16px 0; }
        .tab { border:1px solid var(--divider-color); border-radius:999px; padding:8px 12px; background:var(--card-background-color); color:var(--primary-text-color); cursor:pointer; }
        .tab.active { background:var(--primary-color); color:var(--text-primary-color, white); border-color:var(--primary-color); }
        .grid2 { display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:14px; }
        .card { background:var(--card-background-color); border-radius:12px; box-shadow:var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,.18)); overflow:hidden; border:1px solid var(--divider-color); }
        .pad { padding:16px; }
        .row { display:grid; grid-template-columns:1fr auto; gap:16px; align-items:center; min-height:72px; padding:14px 16px; border-top:1px solid var(--divider-color); }
        .row:first-child { border-top:0; }
        .name { font-size:16px; font-weight:500; }
        .meta { margin-top:4px; color:var(--secondary-text-color); font-size:13px; line-height:1.35; }
        .pill { display:inline-block; margin:4px 6px 0 0; padding:4px 8px; border-radius:999px; background:var(--secondary-background-color); color:var(--secondary-text-color); font-size:12px; }
        .gear { width:44px; height:44px; border-radius:999px; border:0; cursor:pointer; display:inline-flex; align-items:center; justify-content:center; color:var(--primary-color); background:var(--secondary-background-color); }
        .gear:hover, .gear:focus { background:var(--primary-color); color:var(--text-primary-color, white); outline:0; }
        .gear svg { width:24px; height:24px; fill:currentColor; }
        .editor { grid-column:1 / -1; padding:16px; border:1px solid var(--divider-color); border-radius:10px; background:var(--secondary-background-color); }
        .formgrid { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; }
        label { display:flex; flex-direction:column; gap:5px; font-size:12px; color:var(--secondary-text-color); }
        input { box-sizing:border-box; width:100%; border:1px solid var(--divider-color); border-radius:8px; padding:10px; background:var(--card-background-color); color:var(--primary-text-color); font:inherit; }
        .checkbox { flex-direction:row; align-items:center; margin-top:12px; }
        .checkbox input { width:auto; }
        .actions { display:flex; gap:10px; justify-content:flex-end; margin-top:14px; }
        .save, .cancel { border:0; border-radius:8px; padding:10px 14px; cursor:pointer; font-weight:500; }
        .save { background:var(--primary-color); color:var(--text-primary-color, white); }
        .cancel { background:transparent; color:var(--primary-text-color); }
        .empty { padding:24px; color:var(--secondary-text-color); }
        .error { padding:12px 14px; border-radius:8px; background:var(--error-color); color:white; margin-bottom:14px; }
        ul { margin:10px 0 0 20px; padding:0; }
        li { margin:6px 0; }
      </style>`;
  }

  sections() {
    return [
      ['overview', 'Overview'],
      ['sensors', 'Sensors'],
      ['controls', 'Controls'],
      ['managed-devices', 'Managed Devices'],
      ['diagnostics', 'Diagnostics'],
    ];
  }

  currentSection() {
    const requested = new URLSearchParams(window.location.search).get('section') || '';
    const path = String(window.location.pathname || '');
    if (!requested && path.includes('managed-devices')) return 'managed-devices';
    return this.sections().some(([key]) => key === requested) ? requested : 'overview';
  }

  setSection(section) {
    const params = new URLSearchParams(window.location.search);
    params.set('section', section);
    const base = window.location.pathname || '/zero-net-export';
    history.replaceState(null, '', `${base}?${params.toString()}`);
    this.render();
  }

  gearIcon() {
    return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19.43 12.98c.04-.32.07-.65.07-.98s-.02-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.37-.31-.6-.22l-2.49 1a7.28 7.28 0 0 0-1.69-.98L14.5 2.42A.49.49 0 0 0 14 2h-4c-.25 0-.46.18-.5.42L9.12 5.07c-.61.24-1.18.56-1.69.98l-2.49-1a.49.49 0 0 0-.6.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.08.65-.08.98s.03.66.08.98l-2.11 1.65a.5.5 0 0 0-.12.64l2 3.46c.12.22.37.31.6.22l2.49-1c.51.4 1.08.74 1.69.98l.38 2.65c.04.24.25.42.5.42h4c.25 0 .46-.18.5-.42l.38-2.65c.61-.24 1.18-.58 1.69-.98l2.49 1c.23.08.48 0 .6-.22l2-3.46a.5.5 0 0 0-.12-.64l-2.11-1.65ZM12 15.5A3.5 3.5 0 1 1 12 8a3.5 3.5 0 0 1 0 7.5Z"/></svg>`;
  }

  statesByDomain(domain) {
    return Object.values(this._hass?.states || {}).filter((state) => state.entity_id?.startsWith(`${domain}.zero_net_export`));
  }

  zeroNetStates() {
    return Object.values(this._hass?.states || {}).filter((state) => state.entity_id?.includes('zero_net_export'));
  }

  managedSurfaces() {
    const states = this._hass?.states || {};
    return Object.values(states).filter((state) =>
      state.entity_id?.startsWith('sensor.zero_net_export') && Array.isArray(state.attributes?.managed_devices)
    );
  }

  devices() {
    const byKey = new Map();
    for (const surface of this.managedSurfaces()) {
      const entryId = surface.attributes?.config_entry_id || surface.attributes?.entry_id || '';
      for (const device of surface.attributes.managed_devices) {
        const deviceKey = String(device.key || device.device_key || device.name || 'managed-device');
        const stableKey = `${device.entry_id || entryId}:${deviceKey}`;
        if (!byKey.has(stableKey)) {
          byKey.set(stableKey, {...device, entry_id: device.entry_id || entryId});
        }
      }
    }
    return [...byKey.values()];
  }

  applyDeepLink(devices) {
    if (this._deepLinkApplied) return;
    this._deepLinkApplied = true;
    const requested = new URLSearchParams(window.location.search).get('managed_device');
    if (!requested) return;
    const match = devices.find((device) => {
      const key = String(device.key || device.device_key || device.name || 'managed-device');
      const entryId = String(device.entry_id || 'default-entry');
      return `${entryId}:${key}` === requested;
    });
    if (match) {
      const key = String(match.key || match.device_key || match.name || 'managed-device');
      const entryId = String(match.entry_id || 'default-entry');
      this._editing = `${entryId}:${key}`;
    }
  }

  openEditor(editKey) {
    this._editing = editKey;
    this.render();
  }

  closeEditor() {
    this._editing = null;
    this.render();
  }

  async saveDevice(editKey) {
    const root = this.querySelector(`[data-editor="${CSS.escape(editKey)}"]`);
    if (!root || !this._hass) return;
    const value = (name) => root.querySelector(`[name="${name}"]`)?.value;
    const checked = (name) => !!root.querySelector(`[name="${name}"]`)?.checked;
    const payload = {
      entry_id: root.dataset.entryId || '',
      device_key: root.dataset.deviceKey || '',
      name: value('name'),
      entity_id: value('entity_id'),
      enabled: checked('enabled'),
      priority: Number(value('priority')),
      nominal_power_w: Number(value('nominal_power_w')),
      min_power_w: Number(value('min_power_w')),
      max_power_w: Number(value('max_power_w')),
      step_w: Number(value('step_w')),
      min_on_seconds: Number(value('min_on_seconds')),
      min_off_seconds: Number(value('min_off_seconds')),
      cooldown_seconds: Number(value('cooldown_seconds')),
      max_active_seconds: Number(value('max_active_seconds') || 0),
    };
    try {
      await this._hass.callService('zero_net_export', 'update_managed_device', payload);
      this._editing = null;
      this._error = '';
    } catch (err) {
      this._error = err?.message || String(err);
    }
    this.render();
  }

  editor(device, editKey) {
    const key = device.key || device.device_key || device.name;
    const val = (field, fallback = '') => device[field] ?? fallback;
    return `
      <div class="editor" data-editor="${this.escapeAttr(editKey)}" data-entry-id="${this.escapeAttr(device.entry_id || '')}" data-device-key="${this.escapeAttr(key)}">
        <div class="formgrid">
          <label>Name<input name="name" value="${this.escapeAttr(val('name'))}"></label>
          <label>Entity<input name="entity_id" value="${this.escapeAttr(val('entity_id'))}"></label>
          <label>Priority<input name="priority" type="number" value="${this.escapeAttr(val('priority', 100))}"></label>
          <label>Nominal W<input name="nominal_power_w" type="number" value="${this.escapeAttr(val('nominal_power_w', 2400))}"></label>
          <label>Min W<input name="min_power_w" type="number" value="${this.escapeAttr(val('min_power_w', val('nominal_power_w', 2400)))}"></label>
          <label>Max W<input name="max_power_w" type="number" value="${this.escapeAttr(val('max_power_w', val('nominal_power_w', 2400)))}"></label>
          <label>Step W<input name="step_w" type="number" value="${this.escapeAttr(val('step_w', val('nominal_power_w', 2400)))}"></label>
          <label>Min on seconds<input name="min_on_seconds" type="number" value="${this.escapeAttr(val('min_on_seconds', 900))}"></label>
          <label>Min off seconds<input name="min_off_seconds" type="number" value="${this.escapeAttr(val('min_off_seconds', 900))}"></label>
          <label>Cooldown seconds<input name="cooldown_seconds" type="number" value="${this.escapeAttr(val('cooldown_seconds', 60))}"></label>
          <label>Max active seconds<input name="max_active_seconds" type="number" value="${this.escapeAttr(val('max_active_seconds', 14400) || 0)}"></label>
        </div>
        <label class="checkbox"><input name="enabled" type="checkbox" ${val('enabled', val('effective_enabled', true)) ? 'checked' : ''}> Enabled</label>
        <div class="actions"><button class="cancel" data-cancel="${this.escapeAttr(editKey)}">Cancel</button><button class="save" data-save="${this.escapeAttr(editKey)}">Save settings</button></div>
      </div>`;
  }

  row(device) {
    const key = String(device.key || device.device_key || device.name || 'managed-device');
    const entryId = String(device.entry_id || 'default-entry');
    const editKey = `${entryId}:${key}`;
    const kind = device.kind || 'managed';
    const status = device.status || (device.usable ? 'ready' : 'configured');
    const power = device.current_power_w ?? device.nominal_power_w ?? '—';
    return `
      <div class="row">
        <div>
          <div class="name">${this.escape(device.name || key)}</div>
          <div class="meta">${this.escape(kind)} • ${this.escape(status)} • ${this.escape(power)} W • ${this.escape(device.entity_id || '')}</div>
        </div>
        <button class="gear" title="Edit ${this.escapeAttr(device.name || key)} settings" aria-label="Edit ${this.escapeAttr(device.name || key)} settings" data-gear="${this.escapeAttr(editKey)}">${this.gearIcon()}</button>
        ${this._editing === editKey ? this.editor({...device, key}, editKey) : ''}
      </div>`;
  }

  bind() {
    this.querySelectorAll('[data-tab]').forEach((button) => button.addEventListener('click', () => this.setSection(button.dataset.tab)));
    this.querySelectorAll('[data-gear]').forEach((button) => button.addEventListener('click', () => this.openEditor(button.dataset.gear)));
    this.querySelectorAll('[data-cancel]').forEach((button) => button.addEventListener('click', () => this.closeEditor()));
    this.querySelectorAll('[data-save]').forEach((button) => button.addEventListener('click', () => this.saveDevice(button.dataset.save)));
  }

  tabs(active) {
    return `<div class="tabs">${this.sections().map(([key, label]) => `<button class="tab ${active === key ? 'active' : ''}" data-tab="${this.escapeAttr(key)}">${this.escape(label)}</button>`).join('')}</div>`;
  }

  summaryCard(title, rows) {
    return `<div class="card pad"><h2>${this.escape(title)}</h2><ul>${rows.map((row) => `<li>${this.escape(row)}</li>`).join('')}</ul></div>`;
  }

  overview() {
    const states = this.zeroNetStates();
    const sensors = this.statesByDomain('sensor').length;
    const diagnostics = states.filter((state) => state.attributes?.entity_category === 'diagnostic' || state.entity_id?.includes('diagnostic')).length;
    const buttons = this.statesByDomain('button').length;
    return `<div class="grid2">
      ${this.summaryCard('Tier 2 is here', ['Use the tabs above for Sensors, Controls, Managed Devices, and Diagnostics.', 'Tier 1 Home Assistant device-page buttons can show this page link, but native HA button rows cannot browser-navigate by themselves.', 'The primary controller device configuration link points to this Tier 2 surface.'])}
      ${this.summaryCard('Current install snapshot', [`${sensors} Zero Net Export sensors visible to the frontend`, `${buttons} Zero Net Export buttons/actions`, `${diagnostics} diagnostic/support states available behind the compact Diagnostics tab`])}
    </div>`;
  }

  sensorsSection() {
    const sensors = this.statesByDomain('sensor').slice(0, 8);
    return `<div class="card pad"><h2>Sensors setup</h2><div class="sub">Map source roles and confirm the key Tier 1 readings without scrolling through every diagnostic entity.</div>${sensors.map((state) => `<span class="pill">${this.escape(state.attributes?.friendly_name || state.entity_id)}: ${this.escape(state.state)}</span>`).join('')}</div>`;
  }

  controlsSection() {
    const controls = [...this.statesByDomain('switch'), ...this.statesByDomain('number'), ...this.statesByDomain('select')].slice(0, 10);
    return `<div class="card pad"><h2>Controls setup</h2><div class="sub">Review operator-facing control settings: enablement, mode, target export, reserve, and tuning controls.</div>${controls.length ? controls.map((state) => `<span class="pill">${this.escape(state.attributes?.friendly_name || state.entity_id)}: ${this.escape(state.state)}</span>`).join('') : '<div class="empty">No control entities are currently visible to this frontend state.</div>'}</div>`;
  }

  managedDevicesSection(devices) {
    return `<div class="header"><h1>Managed Devices</h1><div class="sub">Right-side gears edit the settings used when each load was first provisioned.</div></div>${this._error ? `<div class="error">${this.escape(this._error)}</div>` : ''}<div class="card">${devices.length ? devices.map((device) => this.row(device)).join('') : '<div class="empty">No managed devices configured yet.</div>'}</div>`;
  }

  diagnosticsSection() {
    const diagnostic = this.zeroNetStates().filter((state) => state.attributes?.entity_category === 'diagnostic' || state.entity_id?.includes('diagnostic'));
    const primary = diagnostic.slice(0, 12);
    return `<div class="card pad"><h2>Diagnostics</h2><div class="sub">Compact Tier 2 diagnostics view. Showing the first ${primary.length} support items here instead of filling the native device page for pages.</div>${primary.map((state) => `<span class="pill">${this.escape(state.attributes?.friendly_name || state.entity_id)}: ${this.escape(state.state)}</span>`).join('') || '<div class="empty">No diagnostic states found.</div>'}</div>`;
  }

  content(active, devices) {
    if (active === 'sensors') return this.sensorsSection();
    if (active === 'controls') return this.controlsSection();
    if (active === 'managed-devices') return this.managedDevicesSection(devices);
    if (active === 'diagnostics') return this.diagnosticsSection();
    return this.overview();
  }

  render() {
    if (!this.isConnected || !this._hass) return;
    const devices = this.devices();
    this.applyDeepLink(devices);
    const active = this.currentSection();
    const title = active === 'managed-devices' ? 'Managed Devices' : 'Zero Net Export Tier 2';
    const sub = active === 'managed-devices' ? 'Edit managed-load settings or switch tabs for the rest of Tier 2.' : 'Accessible Tier 2 setup surface for Sensors, Controls, Managed Devices, and Diagnostics.';
    this.innerHTML = `${this.css()}<div class="wrap"><div class="header"><h1>${this.escape(title)}</h1><div class="sub">${this.escape(sub)}</div></div>${this.tabs(active)}${this.content(active, devices)}</div>`;
    this.bind();
  }

  escape(value) { return String(value ?? '').replace(/[&<>"']/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch])); }
  escapeAttr(value) { return this.escape(value); }
}

customElements.define('zero-net-export-managed-devices-panel', ZeroNetExportManagedDevicesPanel);
