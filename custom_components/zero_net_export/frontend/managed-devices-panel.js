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
        .wrap { max-width:980px; margin:0 auto; }
        .header { margin-bottom:18px; }
        h1 { font-size:28px; margin:0 0 6px; font-weight:500; }
        .sub { color:var(--secondary-text-color); font-size:14px; }
        .card { background:var(--card-background-color); border-radius:12px; box-shadow:var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,.18)); overflow:hidden; border:1px solid var(--divider-color); }
        .row { display:grid; grid-template-columns:1fr auto; gap:16px; align-items:center; min-height:72px; padding:14px 16px; border-top:1px solid var(--divider-color); }
        .row:first-child { border-top:0; }
        .name { font-size:16px; font-weight:500; }
        .meta { margin-top:4px; color:var(--secondary-text-color); font-size:13px; line-height:1.35; }
        .gear { width:44px; height:44px; border-radius:999px; border:0; cursor:pointer; display:inline-flex; align-items:center; justify-content:center; color:var(--primary-color); background:var(--secondary-background-color); }
        .gear:hover, .gear:focus { background:var(--primary-color); color:var(--text-primary-color, white); outline:0; }
        .gear svg { width:24px; height:24px; fill:currentColor; }
        .editor { grid-column:1 / -1; padding:16px; border:1px solid var(--divider-color); border-radius:10px; background:var(--secondary-background-color); }
        .grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; }
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
      </style>`;
  }

  gearIcon() {
    return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19.43 12.98c.04-.32.07-.65.07-.98s-.02-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.37-.31-.6-.22l-2.49 1a7.28 7.28 0 0 0-1.69-.98L14.5 2.42A.49.49 0 0 0 14 2h-4c-.25 0-.46.18-.5.42L9.12 5.07c-.61.24-1.18.56-1.69.98l-2.49-1a.49.49 0 0 0-.6.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.08.65-.08.98s.03.66.08.98l-2.11 1.65a.5.5 0 0 0-.12.64l2 3.46c.12.22.37.31.6.22l2.49-1c.51.4 1.08.74 1.69.98l.38 2.65c.04.24.25.42.5.42h4c.25 0 .46-.18.5-.42l.38-2.65c.61-.24 1.18-.58 1.69-.98l2.49 1c.23.08.48 0 .6-.22l2-3.46a.5.5 0 0 0-.12-.64l-2.11-1.65ZM12 15.5A3.5 3.5 0 1 1 12 8a3.5 3.5 0 0 1 0 7.5Z"/></svg>`;
  }

  getSurface() {
    const states = this._hass?.states || {};
    return Object.values(states).find((state) => state.entity_id === 'sensor.zero_net_export_managed_devices_surface') ||
      Object.values(states).find((state) => state.entity_id?.startsWith('sensor.zero_net_export') && state.attributes?.managed_devices);
  }

  devices() {
    const surface = this.getSurface();
    const devices = surface?.attributes?.managed_devices || [];
    return Array.isArray(devices) ? devices : [];
  }

  openEditor(key) {
    this._editing = key;
    this.render();
  }

  closeEditor() {
    this._editing = null;
    this.render();
  }

  async saveDevice(key) {
    const root = this.querySelector(`[data-editor="${CSS.escape(key)}"]`);
    if (!root || !this._hass) return;
    const value = (name) => root.querySelector(`[name="${name}"]`)?.value;
    const checked = (name) => !!root.querySelector(`[name="${name}"]`)?.checked;
    const payload = {
      device_key: key,
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

  editor(device) {
    const key = device.key || device.device_key || device.name;
    const val = (field, fallback = '') => device[field] ?? fallback;
    return `
      <div class="editor" data-editor="${this.escapeAttr(key)}">
        <div class="grid">
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
        <div class="actions"><button class="cancel" data-cancel="${this.escapeAttr(key)}">Cancel</button><button class="save" data-save="${this.escapeAttr(key)}">Save settings</button></div>
      </div>`;
  }

  row(device) {
    const key = String(device.key || device.device_key || device.name || 'managed-device');
    const kind = device.kind || 'managed';
    const status = device.status || (device.usable ? 'ready' : 'configured');
    const power = device.current_power_w ?? device.nominal_power_w ?? '—';
    return `
      <div class="row">
        <div>
          <div class="name">${this.escape(device.name || key)}</div>
          <div class="meta">${this.escape(kind)} • ${this.escape(status)} • ${this.escape(power)} W • ${this.escape(device.entity_id || '')}</div>
        </div>
        <button class="gear" title="Edit ${this.escapeAttr(device.name || key)} settings" aria-label="Edit ${this.escapeAttr(device.name || key)} settings" data-gear="${this.escapeAttr(key)}">${this.gearIcon()}</button>
        ${this._editing === key ? this.editor({...device, key}) : ''}
      </div>`;
  }

  bind() {
    this.querySelectorAll('[data-gear]').forEach((button) => button.addEventListener('click', () => this.openEditor(button.dataset.gear)));
    this.querySelectorAll('[data-cancel]').forEach((button) => button.addEventListener('click', () => this.closeEditor()));
    this.querySelectorAll('[data-save]').forEach((button) => button.addEventListener('click', () => this.saveDevice(button.dataset.save)));
  }

  render() {
    if (!this.isConnected || !this._hass) return;
    const devices = this.devices();
    this.innerHTML = `${this.css()}<div class="wrap"><div class="header"><h1>Managed Devices</h1><div class="sub">Right-side gears edit the settings used when each load was first provisioned.</div></div>${this._error ? `<div class="error">${this.escape(this._error)}</div>` : ''}<div class="card">${devices.length ? devices.map((device) => this.row(device)).join('') : '<div class="empty">No managed devices configured yet.</div>'}</div></div>`;
    this.bind();
  }

  escape(value) { return String(value ?? '').replace(/[&<>"']/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch])); }
  escapeAttr(value) { return this.escape(value); }
}

customElements.define('zero-net-export-managed-devices-panel', ZeroNetExportManagedDevicesPanel);
