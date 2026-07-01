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

  _sourceRoles() {
    return [
      { key: "solar_power_entity", label: "Solar power", required: true },
      { key: "solar_energy_entity", label: "Solar energy", required: true },
      { key: "grid_import_power_entity", label: "Grid import power", required: true },
      { key: "grid_export_power_entity", label: "Grid export power", required: true },
      { key: "grid_import_energy_entity", label: "Grid import energy", required: true },
      { key: "grid_export_energy_entity", label: "Grid export energy", required: true },
      { key: "home_load_power_entity", label: "Home load power", required: false },
      { key: "battery_soc_entity", label: "Battery state of charge", required: false },
      { key: "battery_charge_power_entity", label: "Battery charge power", required: false },
      { key: "battery_discharge_power_entity", label: "Battery discharge power", required: false },
    ];
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

  _sourceState(role, suffix, suffixName) {
    if (!this._hass || !this._hass.states) {
      return undefined;
    }
    const exactCandidates = [
      `sensor.zero_net_export_source_${role.key}_${suffix}`,
      `sensor.zero_net_export_${role.key.replace(/_entity$/, "")}_${suffix}`,
    ];
    for (const entityId of exactCandidates) {
      if (this._hass.states[entityId]) {
        return this._hass.states[entityId];
      }
    }
    const roleNeedle = role.key.replace(/_entity$/, "");
    const labelNeedle = `${role.label} ${suffixName}`.toLowerCase();
    return Object.entries(this._hass.states)
      .filter(([entityId]) => entityId.startsWith("sensor."))
      .map(([, state]) => state)
      .find((state) => {
        const friendlyName = String((state.attributes && state.attributes.friendly_name) || "").toLowerCase();
        const entityId = String(state.entity_id || "").toLowerCase();
        return friendlyName === labelNeedle || (entityId.includes(roleNeedle) && entityId.includes(suffix));
      });
  }

  _sourceValue(role, suffix, suffixName, fallback = "") {
    const state = this._sourceState(role, suffix, suffixName);
    if (!state || state.state === undefined || state.state === null) {
      return fallback;
    }
    return String(state.state);
  }

  _sourceAttr(role, suffix, suffixName, attr, fallback = "") {
    const state = this._sourceState(role, suffix, suffixName);
    if (!state || !state.attributes || state.attributes[attr] === undefined || state.attributes[attr] === null) {
      return fallback;
    }
    return state.attributes[attr];
  }

  async _onClick(event) {
    const target = event.target.closest("button");
    const select = event.target.closest("select");
    const checkbox = event.target.closest("input[type=checkbox]");

    // Handle filter/sort changes
    if (select && (select.dataset.filterPlan || select.dataset.filterStatus || select.dataset.filterPriority || select.dataset.filterReadiness || select.dataset.sortBy || select.dataset.sortDir)) {
      this._render();
      return;
    }

    // Handle bulk checkbox changes
    if (checkbox && (checkbox.classList.contains("zne-bulk-checkbox") || checkbox.classList.contains("zne-bulk-confirm"))) {
      this._updateBulkSelection();
      return;
    }

    // Handle bulk action buttons
    if (target && (target.id === "bulk-enable" || target.id === "bulk-disable" || target.id === "bulk-select-all" || target.id === "bulk-clear")) {
      await this._handleBulkAction(target.id);
      return;
    }

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

    // Handle fleet row click for drill-down
    const fleetRow = event.target.closest(".zne-fleet-row");
    if (fleetRow && !event.target.closest("button") && !event.target.closest("input[type=checkbox]")) {
      const deviceKey = fleetRow.dataset.deviceKey;
      const selectedInput = this.querySelector("[data-selected-device]");
      if (selectedInput) {
        selectedInput.value = deviceKey || "";
        this._render();
      }
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

    const managedDeviceKeyInput = this.querySelector("[data-zne-managed-key]");
    const managedDeviceKey = managedDeviceKeyInput ? managedDeviceKeyInput.value.trim() : "";
    const managedConfirmInput = this.querySelector("[data-zne-managed-confirm]");
    const managedConfirm = managedConfirmInput ? managedConfirmInput.value.trim() : "";
    const sourceRoleValues = {};
    this.querySelectorAll("[data-zne-source-role]").forEach((input) => {
      const value = input.value.trim();
      const original = (input.dataset.zneSourceOriginal || "").trim();
      if (value || original || value !== original) {
        sourceRoleValues[input.dataset.zneSourceRole] = value;
      }
    });

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
        if (!managedDeviceKey) {
          throw new Error("Enter a managed-device key first.");
        }
        await this._hass.callService("zero_net_export", "update_managed_device", {
          entry_id: this._selectedEntryId(),
          device_key: managedDeviceKey,
          enabled: action === "managed-enable",
        });
        this._message = action === "managed-enable" ? "Managed record enable requested." : "Managed record disable requested.";
      }

      if (action === "managed-remove") {
        if (!managedDeviceKey) {
          throw new Error("Enter a managed-device key first.");
        }
        if (managedConfirm !== "REMOVE FROM ZNE") {
          throw new Error("Type REMOVE FROM ZNE to confirm.");
        }
        await this._hass.callService("zero_net_export", "remove_managed_device", {
          entry_id: this._selectedEntryId(),
          device_key: managedDeviceKey,
          confirm: true,
        });
        this._message = "Managed record removal requested. The original Home Assistant entity is left untouched.";
      }

      if (action === "fleet-toggle") {
        const deviceKey = target.dataset.deviceKey;
        if (!deviceKey) {
          throw new Error("No device key provided.");
        }
        // Find the device in the fleet to get its current state
        const overview = this._state("sensor.managed_devices_overview");
        const fleet = overview && overview.attributes && Array.isArray(overview.attributes.managed_devices)
          ? overview.attributes.managed_devices
          : [];
        const device = fleet.find(d => d.key === deviceKey);
        if (!device) {
          throw new Error("Device not found in fleet.");
        }
        await this._hass.callService("zero_net_export", "update_managed_device", {
          entry_id: device.entry_id || this._selectedEntryId(),
          device_key: deviceKey,
          enabled: !device.enabled,
        });
        this._message = `Managed record ${device.enabled ? "disabled" : "enabled"} for ${deviceKey}.`;
      }

      if (action === "fleet-remove") {
        const deviceKey = target.dataset.deviceKey;
        if (!deviceKey) {
          throw new Error("No device key provided.");
        }
        const overview = this._state("sensor.managed_devices_overview");
        const fleet = overview && overview.attributes && Array.isArray(overview.attributes.managed_devices)
          ? overview.attributes.managed_devices
          : [];
        const device = fleet.find(d => d.key === deviceKey);
        if (!device) {
          throw new Error("Device not found in fleet.");
        }
        const managedConfirmInput = this.querySelector("[data-zne-managed-confirm]");
        const managedConfirm = managedConfirmInput ? managedConfirmInput.value.trim() : "";
        if (managedConfirm !== "REMOVE FROM ZNE") {
          throw new Error("Type REMOVE FROM ZNE to confirm.");
        }
        await this._hass.callService("zero_net_export", "remove_managed_device", {
          entry_id: device.entry_id || this._selectedEntryId(),
          device_key: deviceKey,
          confirm: true,
        });
        // Clear the selected device
        const selectedInput = this.querySelector("[data-selected-device]");
        if (selectedInput) {
          selectedInput.value = "";
        }
        this._message = `Managed record removal requested for ${deviceKey}. The original Home Assistant entity is left untouched.`;
      }

      if (action === "update-source-roles") {
        await this._hass.callService("zero_net_export", "update_source_roles", {
          entry_id: this._selectedEntryId(),
          ...sourceRoleValues,
        });
        this._message = "Source-role save requested. Home Assistant will reload this Zero Net Export plan.";
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

  _updateBulkSelection() {
    const checkboxes = this.querySelectorAll(".zne-bulk-checkbox");
    const selectedCount = Array.from(checkboxes).filter(cb => cb.checked).length;

    // Update hidden input to store selected count
    let selectedInput = this.querySelector("[data-bulk-selected]");
    if (!selectedInput) {
      selectedInput = document.createElement("input");
      selectedInput.type = "hidden";
      selectedInput.dataset.bulkSelected = "";
      this.insertBefore(selectedInput, this.firstChild);
    }
    selectedInput.value = String(selectedCount);

    // Update bulk action buttons
    const bulkEnableBtn = this.querySelector("#bulk-enable");
    const bulkDisableBtn = this.querySelector("#bulk-disable");
    const bulkSelectAllBtn = this.querySelector("#bulk-select-all");
    const bulkClearBtn = this.querySelector("#bulk-clear");
    const bulkConfirm = this.querySelector(".zne-bulk-confirm");
    const confirmed = Boolean(bulkConfirm && bulkConfirm.checked);

    if (bulkEnableBtn) {
      bulkEnableBtn.disabled = selectedCount === 0 || !confirmed;
      bulkEnableBtn.textContent = `Enable Selected (${selectedCount})`;
    }
    if (bulkDisableBtn) {
      bulkDisableBtn.disabled = selectedCount === 0 || !confirmed;
      bulkDisableBtn.textContent = `Disable Selected (${selectedCount})`;
    }
    if (bulkSelectAllBtn) {
      const filteredCount = this._state("sensor.managed_devices_overview")?.attributes?.filtered_count || checkboxes.length;
      bulkSelectAllBtn.textContent = `Select All (${filteredCount})`;
    }
    if (bulkClearBtn) {
      bulkClearBtn.disabled = selectedCount === 0;
    }
  }

  async _handleBulkAction(action) {
    if (action === "bulk-select-all") {
      const checkboxes = this.querySelectorAll(".zne-bulk-checkbox");
      checkboxes.forEach(cb => cb.checked = true);
      this._updateBulkSelection();
      this._message = `All ${checkboxes.length} visible device(s) selected.`;
      return;
    }

    if (action === "bulk-clear") {
      const checkboxes = this.querySelectorAll(".zne-bulk-checkbox");
      const bulkConfirm = this.querySelector(".zne-bulk-confirm");
      checkboxes.forEach(cb => cb.checked = false);
      if (bulkConfirm) {
        bulkConfirm.checked = false;
      }
      this._updateBulkSelection();
      this._message = "Selection cleared.";
      return;
    }

    const checkboxes = this.querySelectorAll(".zne-bulk-checkbox:checked");
    const selectedDevices = Array.from(checkboxes).map(cb => cb.dataset.deviceKey);

    if (selectedDevices.length === 0) {
      this._message = "No devices selected.";
      return;
    }

    const bulkConfirm = this.querySelector(".zne-bulk-confirm");
    if (!bulkConfirm || !bulkConfirm.checked) {
      this._message = "Confirm the selected-device bulk change first.";
      this._updateBulkSelection();
      return;
    }

    this._busy = true;
    this._message = "";
    this._render();

    try {
      if (action === "bulk-enable") {
        let changed = 0;
        for (const deviceKey of selectedDevices) {
          const overview = this._state("sensor.managed_devices_overview");
          const fleet = overview && overview.attributes && Array.isArray(overview.attributes.managed_devices)
            ? overview.attributes.managed_devices
            : [];
          const device = fleet.find(d => d.key === deviceKey);
          if (device && !device.enabled) {
            await this._hass.callService("zero_net_export", "update_managed_device", {
              entry_id: device.entry_id || this._selectedEntryId(),
              device_key: deviceKey,
              enabled: true,
            });
            changed += 1;
          }
        }
        this._message = `Enable requested for ${changed} selected device(s).`;
      } else if (action === "bulk-disable") {
        let changed = 0;
        for (const deviceKey of selectedDevices) {
          const overview = this._state("sensor.managed_devices_overview");
          const fleet = overview && overview.attributes && Array.isArray(overview.attributes.managed_devices)
            ? overview.attributes.managed_devices
            : [];
          const device = fleet.find(d => d.key === deviceKey);
          if (device && device.enabled) {
            await this._hass.callService("zero_net_export", "update_managed_device", {
              entry_id: device.entry_id || this._selectedEntryId(),
              device_key: deviceKey,
              enabled: false,
            });
            changed += 1;
          }
        }
        this._message = `Disable requested for ${changed} selected device(s).`;
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
    const entries = this._entries();
    const roles = this._sourceRoles();
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
        <div class="zne-card">
          <h3>Plan</h3>
          <label>Zero Net Export plan
            <select data-zne-entry-id>
              <option value="">Auto</option>
              ${entries.map((entry) => `<option value="${this._escape(entry.entry_id)}">${this._escape(entry.title || entry.entry_id)}</option>`).join("")}
            </select>
          </label>
          <p class="zne-muted">Source saves are scoped to the selected Zero Net Export plan.</p>
        </div>
        <div class="zne-list">
          ${roles.map((role) => {
            const status = this._sourceValue(role, "status", "status", "missing");
            const reading = this._sourceValue(role, "reading", "reading", "unknown");
            const age = this._sourceValue(role, "age_seconds", "age", "unknown");
            const issueCount = this._sourceValue(role, "issue_count", "issue count", "0");
            const binding = this._sourceAttr(role, "status", "status", "binding", "");
            const bindingLabel = this._sourceAttr(role, "status", "status", "binding_label", binding || "Not configured");
            return `
            <div class="zne-source zne-source-editor">
              <div>
                <strong>${this._escape(role.label)}</strong>
                <span>${role.required ? "Required" : "Optional"}</span>
              </div>
              <div class="zne-source-detail">
                ${this._pill("status", status)}
                <span class="zne-meta">Binding: ${this._escape(bindingLabel)}</span>
                <span class="zne-meta">Reading: ${this._escape(reading)} | Age: ${this._escape(age)} s | Issues: ${this._escape(issueCount)}</span>
                <input data-zne-source-role="${this._escape(role.key)}" data-zne-source-original="${this._escape(binding)}" type="text" autocomplete="off" placeholder="sensor.example" value="${this._escape(binding)}">
              </div>
            </div>
          `;
          }).join("")}
        </div>
        <div class="zne-actions">
          <button type="button" data-zne-action="update-source-roles">Save source roles</button>
        </div>
        <p class="zne-muted">Saving uses the Zero Net Export backend service and reloads the selected plan. It does not edit Home Assistant source entities.</p>
      </section>
    `;
  }

  _managedDevicesSection() {
    const entries = this._entries();
    const overview = this._state("sensor.managed_devices_overview");
    const fleet = overview && overview.attributes && Array.isArray(overview.attributes.managed_devices)
      ? overview.attributes.managed_devices
      : [];

    // Compute summary counts
    const total = fleet.length;
    const enabled = fleet.filter(d => d.enabled === true).length;
    const disabled = fleet.filter(d => d.enabled === false).length;
    const blocked = fleet.filter(d => d.blocked === true || d.blocked === "true" || d.status === "blocked").length;
    const stale = fleet.filter(d => d.stale === true || d.stale === "true" || d.last_seen_age > 3600).length;

    // Filter state (stored in data attributes on the section)
    const filterPlan = this.querySelector("[data-filter-plan]")?.value || "all";
    const filterStatus = this.querySelector("[data-filter-status]")?.value || "all";
    const filterPriority = this.querySelector("[data-filter-priority]")?.value || "all";
    const filterReadiness = this.querySelector("[data-filter-readiness]")?.value || "all";

    // Sort state
    const sortBy = this.querySelector("[data-sort-by]")?.value || "priority";
    const sortDir = this.querySelector("[data-sort-dir]")?.value || "desc";

    // Apply filters
    let filtered = fleet;
    if (filterPlan !== "all" && filterPlan !== "") {
      filtered = filtered.filter(d => d.entry_id === filterPlan);
    }
    if (filterStatus !== "all") {
      const statusMatch = filterStatus === "enabled" ? true : false;
      filtered = filtered.filter(d => d.enabled === statusMatch);
    }
    if (filterPriority !== "all") {
      filtered = filtered.filter(d => String(d.priority || "").toLowerCase() === filterPriority.toLowerCase());
    }
    if (filterReadiness !== "all") {
      filtered = filtered.filter(d => String(d.readiness || d.status || "").toLowerCase() === filterReadiness.toLowerCase());
    }

    // Apply sorting
    const sortField = sortBy;
    const reverse = sortDir === "asc" ? -1 : 1;
    filtered = [...filtered].sort((a, b) => {
      let valA, valB;
      if (sortField === "priority") {
        const priorityOrder = {"high": 3, "medium": 2, "low": 1, "": 0};
        valA = priorityOrder[(a.priority || "").toLowerCase()] || 0;
        valB = priorityOrder[(b.priority || "").toLowerCase()] || 0;
      } else if (sortField === "status") {
        valA = a.enabled ? 1 : 0;
        valB = b.enabled ? 1 : 0;
      } else if (sortField === "last_seen") {
        valA = a.last_seen_age || 0;
        valB = b.last_seen_age || 0;
      } else {
        valA = a[sortField] || "";
        valB = b[sortField] || "";
      }
      if (valA < valB) return -1 * reverse;
      if (valA > valB) return 1 * reverse;
      return 0;
    });

    // Get unique values for filter dropdowns
    const plans = [...new Set(fleet.map(d => d.entry_id))];
    const priorities = [...new Set(fleet.map(d => d.priority).filter(p => p))];
    const readinessStates = [...new Set(fleet.map(d => d.readiness || d.status).filter(r => r))];

    // Selected device for drill-down (stored in data attribute)
    const selectedDeviceKey = this.querySelector("[data-selected-device]")?.value || "";
    const selectedDevice = selectedDeviceKey
      ? fleet.find(d => d.key === selectedDeviceKey)
      : null;

    // Format last-seen age helper
    const formatAge = (ageSeconds) => {
      if (!ageSeconds || ageSeconds === 0) return "Just now";
      const mins = Math.round(ageSeconds / 60);
      if (mins < 60) return `${mins} min ago`;
      const hours = Math.round(mins / 60);
      if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
      const days = Math.round(hours / 24);
      return `${days} day${days > 1 ? "s" : ""} ago`;
    };

    return `
      <section class="zne-panel">
        <div class="zne-panel-title">
          <h2>Managed Devices</h2>
          <button type="button" data-route="/config/integrations/integration/zero_net_export">Open HA managed devices setup</button>
        </div>

        <!-- Fleet Summary -->
        <div class="zne-grid">
          <div class="zne-card">
            <h3>Fleet Summary</h3>
            <div class="zne-fleet-stats">
              <span class="zne-stat"><strong>${total}</strong> Total</span>
              <span class="zne-stat good"><strong>${enabled}</strong> Enabled</span>
              <span class="zne-stat neutral"><strong>${disabled}</strong> Disabled</span>
              <span class="zne-stat bad"><strong>${blocked}</strong> Blocked</span>
              <span class="zne-stat bad"><strong>${stale}</strong> Stale</span>
            </div>
          </div>

          <!-- Filters -->
          <div class="zne-card">
            <h3>Filters</h3>
            <label>Plan
              <select data-filter-plan>
                <option value="all">All Plans</option>
                ${plans.map(p => `<option value="${this._escape(p)}" ${p === filterPlan ? "selected" : ""}>${this._escape(p)}</option>`).join("")}
              </select>
            </label>
            <label>Status
              <select data-filter-status>
                <option value="all">All Status</option>
                <option value="enabled" ${filterStatus === "enabled" ? "selected" : ""}>Enabled</option>
                <option value="disabled" ${filterStatus === "disabled" ? "selected" : ""}>Disabled</option>
              </select>
            </label>
            <label>Priority
              <select data-filter-priority>
                <option value="all">All Priorities</option>
                ${priorities.map(p => `<option value="${this._escape(p)}" ${p === filterPriority ? "selected" : ""}>${this._escape(p)}</option>`).join("")}
              </select>
            </label>
            <label>Readiness
              <select data-filter-readiness>
                <option value="all">All Readiness</option>
                ${readinessStates.map(r => `<option value="${this._escape(r)}" ${r === filterReadiness ? "selected" : ""}>${this._escape(r)}</option>`).join("")}
              </select>
            </label>
          </div>

          <!-- Sort Controls -->
          <div class="zne-card">
            <h3>Sort</h3>
            <label>By
              <select data-sort-by>
                <option value="priority" ${sortBy === "priority" ? "selected" : ""}>Priority</option>
                <option value="status" ${sortBy === "status" ? "selected" : ""}>Status</option>
                <option value="last_seen" ${sortBy === "last_seen" ? "selected" : ""}>Last Seen</option>
              </select>
            </label>
            <label>Direction
              <select data-sort-dir>
                <option value="desc" ${sortDir === "desc" ? "selected" : ""}>Descending</option>
                <option value="asc" ${sortDir === "asc" ? "selected" : ""}>Ascending</option>
              </select>
            </label>
          </div>
        </div>

        <!-- Fleet Table -->
        <div class="zne-card">
          <h3>Fleet List (${filtered.length} devices)</h3>

          <!-- Bulk Actions -->
          <div class="zne-actions" style="margin-bottom: 12px;">
            <button type="button" id="bulk-enable" class="zne-btn zne-btn-good" disabled>
              Enable Selected (${this.querySelector("[data-bulk-selected]")?.value || 0})
            </button>
            <button type="button" id="bulk-disable" class="zne-btn zne-btn-bad" disabled>
              Disable Selected (${this.querySelector("[data-bulk-selected]")?.value || 0})
            </button>
            <button type="button" id="bulk-select-all" class="zne-btn zne-btn-tertiary">
              Select All (${filtered.length})
            </button>
            <button type="button" id="bulk-clear" class="zne-btn zne-btn-tertiary">
              Clear Selection
            </button>
          </div>
          <label class="zne-bulk-confirm-row">
            <input type="checkbox" class="zne-bulk-confirm">
            Confirm bulk changes for the selected visible devices.
          </label>

          ${filtered.length === 0
            ? '<p class="zne-muted">No managed devices found.</p>'
            : `
            <div class="zne-fleet-table">
              <div class="zne-fleet-header">
                <span style="width: 30px;">&#160;</span>
                <span>Device Key</span>
                <span>Plan</span>
                <span>Status</span>
                <span>Priority</span>
                <span>Readiness</span>
                <span>Last Seen</span>
                <span>Blockers</span>
                <span>Actions</span>
              </div>
              ${filtered.map(d => {
                const blockers = d.blockers && Array.isArray(d.blockers) ? d.blockers.length : (d.blocked ? 1 : 0);
                return `
                <div class="zne-fleet-row ${d.enabled ? "enabled" : "disabled"}" data-device-key="${this._escape(d.key)}">
                  <span style="width: 30px; text-align: center;">
                    <input type="checkbox" class="zne-bulk-checkbox" data-device-key="${this._escape(d.key)}" />
                  </span>
                  <span><strong>${this._escape(d.key)}</strong></span>
                  <span>${this._escape(d.entry_id || "-")}</span>
                  <span>${this._pill(d.enabled ? "Enabled" : "Disabled", d.enabled ? "good" : "neutral")}</span>
                  <span>${this._escape(d.priority || "-")}</span>
                  <span>${this._escape(d.readiness || d.status || "-")}</span>
                  <span>${this._escape(formatAge(d.last_seen_age))}</span>
                  <span>${blockers > 0 ? this._pill(`${blockers} blocker${blockers > 1 ? "s" : ""}`, "bad") : "-"}</span>
                  <span>
                    <button type="button" data-zne-action="fleet-toggle" data-device-key="${this._escape(d.key)}">
                      ${d.enabled ? "Disable" : "Enable"}
                    </button>
                  </span>
                </div>
              `;}).join("")}
            </div>
            `}
        </div>

        <!-- Device Detail (Drill-down) -->
        ${selectedDevice ? `
        <div class="zne-card">
          <h3>Device Detail: ${this._escape(selectedDevice.key)}</h3>
          <div class="zne-device-detail">
            <div class="zne-row"><span>Key:</span><strong>${this._escape(selectedDevice.key)}</strong></div>
            <div class="zne-row"><span>Plan:</span><strong>${this._escape(selectedDevice.entry_id || "-")}</strong></div>
            <div class="zne-row"><span>Status:</span><strong>${this._escape(selectedDevice.enabled ? "Enabled" : "Disabled")}</strong></div>
            <div class="zne-row"><span>Priority:</span><strong>${this._escape(selectedDevice.priority || "-")}</strong></div>
            <div class="zne-row"><span>Readiness:</span><strong>${this._escape(selectedDevice.readiness || selectedDevice.status || "-")}</strong></div>
            ${selectedDevice.blocked ? `<div class="zne-row"><span>Blocked:</span><strong>Yes</strong></div>` : ""}
            ${selectedDevice.last_seen_age ? `<div class="zne-row"><span>Last Seen:</span><strong>${Math.round(selectedDevice.last_seen_age / 60)} min ago</strong></div>` : ""}
            ${selectedDevice.settings ? `<div class="zne-row"><span>Settings:</span><pre>${this._escape(JSON.stringify(selectedDevice.settings, null, 2))}</pre></div>` : ""}
          </div>
          <div class="zne-actions">
            <button type="button" data-zne-action="fleet-toggle" data-device-key="${this._escape(selectedDevice.key)}">
              ${selectedDevice.enabled ? "Disable" : "Enable"}
            </button>
            <button type="button" data-zne-action="fleet-remove" data-device-key="${this._escape(selectedDevice.key)}">Remove</button>
          </div>
        </div>
        ` : ""}

        <!-- Legacy Single-Device Actions (preserved) -->
        <div class="zne-card">
          <h3>Scoped Service Action (Legacy)</h3>
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
          grid-template-columns: minmax(88px, 0.35fr) minmax(0, 1fr);
          align-items: start;
          gap: 10px;
          padding: 8px 0;
          border-top: 1px solid var(--divider-color);
          line-height: 1.35;
        }

        .zne-row > span,
        .zne-source > span {
          display: block;
          min-width: 0;
          color: var(--secondary-text-color);
          line-height: 1.35;
        }

        .zne-row > strong,
        .zne-source > .zne-pill {
          display: block;
          min-width: 0;
          justify-self: end;
          max-width: 100%;
          overflow-wrap: anywhere;
          word-break: normal;
          text-align: right;
          line-height: 1.35;
        }

        .zne-source-editor {
          grid-template-columns: minmax(150px, 0.35fr) minmax(0, 1fr);
        }

        .zne-source-editor strong,
        .zne-source-editor span,
        .zne-source-detail {
          min-width: 0;
        }

        .zne-source-editor > div:first-child {
          display: grid;
          gap: 3px;
        }

        .zne-source-detail {
          display: grid;
          gap: 5px;
          justify-items: end;
        }

        .zne-source-detail input {
          max-width: 420px;
        }

        .zne-control-row {
          grid-template-columns: minmax(0, 1fr) auto auto;
          align-items: center;
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
          white-space: normal;
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

        /* Fleet table styles */
        .zne-fleet-stats {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
        }

        .zne-stat {
          display: inline-flex;
          align-items: center;
          padding: 4px 8px;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
          font-size: 13px;
        }

        .zne-stat.good {
          color: var(--success-color, #2e7d32);
          border-color: var(--success-color, #2e7d32);
        }

        .zne-stat.bad {
          color: var(--error-color, #c62828);
          border-color: var(--error-color, #c62828);
        }

        .zne-stat.neutral {
          color: var(--secondary-text-color);
        }

        .zne-fleet-table {
          display: flex;
          flex-direction: column;
        }

        .zne-fleet-header {
          display: grid;
          grid-template-columns: 0.3fr 1fr 1fr 0.8fr 0.8fr 1fr 0.8fr 0.8fr 0.8fr;
          gap: 8px;
          padding: 8px 0;
          border-bottom: 2px solid var(--divider-color);
          font-weight: 500;
          font-size: 13px;
          color: var(--secondary-text-color);
        }

        .zne-fleet-row {
          display: grid;
          grid-template-columns: 0.3fr 1fr 1fr 0.8fr 0.8fr 1fr 0.8fr 0.8fr 0.8fr;
          gap: 8px;
          padding: 10px 0;
          border-bottom: 1px solid var(--divider-color);
          align-items: center;
          cursor: pointer;
        }

        .zne-fleet-row:hover {
          background: var(--secondary-background-color);
        }

        .zne-fleet-row.enabled {
          border-left: 3px solid var(--success-color, #2e7d32);
        }

        .zne-fleet-row.disabled {
          border-left: 3px solid var(--secondary-text-color);
        }

        .zne-fleet-row span {
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .zne-device-detail {
          display: grid;
          gap: 6px;
          padding: 10px 0;
        }

        .zne-device-detail .zne-row {
          display: flex;
          gap: 8px;
          padding: 4px 0;
          border-top: none;
        }

        .zne-device-detail pre {
          background: var(--primary-background-color);
          padding: 8px;
          border-radius: 4px;
          font-size: 12px;
          overflow-x: auto;
          margin: 4px 0;
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

          .zne-row, .zne-source {
            grid-template-columns: minmax(0, 1fr);
            gap: 4px;
          }

          .zne-row > strong,
          .zne-source > .zne-pill {
            justify-self: start;
            text-align: left;
          }

          .zne-source-editor {
            grid-template-columns: minmax(0, 1fr);
          }

          .zne-source-detail {
            justify-items: stretch;
          }

          .zne-source-detail input {
            max-width: none;
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

if (!customElements.get("zero-net-export-app")) {
  customElements.define("zero-net-export-app", ZeroNetExportApp);
}
