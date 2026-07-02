# Milestone 6: Diagnostics & Support Polish - Feasibility Check

**Date**: 2026-07-02  
**Status**: **ACCEPTED**  
**Author**: dev agent

---

## 1. Target Environment

- **Runtime**: Home Assistant 2026.6+ (validation instance: 2026.6.x)
- **Integration**: Zero Net Export custom integration (HACS path)
- **Frontend**: Custom panel via `homeassistant-panel` (Lit-based web component)
- **Backend**: Python 3.11+, Home Assistant core services

---

## 2. Feasibility Findings

### 2.1 Backend: Log Retrieval

**Claim**: We can retrieve recent log entries for display in the Diagnostics tab.

**Finding**: **Supported** (with constraint).

**Evidence**:
- Home Assistant does **not** expose a public API to read the core log buffer directly from integrations.
- **Workaround**: We can implement an **internal log buffer** in the integration that captures our own log messages (via a custom logger handler or by wrapping `_LOGGER`).
- **Alternative**: Use the `hassio/core/logs` API (if running as Home Assistant OS) — but this is **not available** for custom integrations in the standard sandbox.

**Decision**: Implement an **internal log buffer** in the coordinator that stores the last 50 log entries with timestamp, level, and message.

**Constraint**: Only `zero_net_export` logs will be captured (not full HA logs).

---

### 2.2 Backend: Sensor States & Config Entry

**Claim**: We can retrieve current sensor states and config entry state.

**Finding**: **Supported**.

**Evidence**:
- `hass.states.get(entity_id)` is available to integrations.
- `hass.config_entries.async_get_entry(entry_id)` is available.
- Both are standard HA APIs used in many integrations.

**Decision**: Implement `async_get_diagnostics()` in coordinator to gather:
- All `zero_net_export_*` sensor states.
- Config entry state (disabled, disabled_by, etc.).
- Reconciliation history (from existing in-memory buffer).

---

### 2.3 Backend: Diagnostics Export

**Claim**: We can generate and export a JSON diagnostics file.

**Finding**: **Supported**.

**Evidence**:
- Python `json` module can serialize data.
- HA provides `hass.config.path()` to write files to the config directory.
- We can expose a service `zero_net_export.export_diagnostics` that writes the file and returns the path.
- Frontend can then fetch the file via a static URL (or we can use the `file_download` service).

**Constraint**: Must filter sensitive data (tokens, passwords) before export.

**Decision**: Implement `async_export_diagnostics()` that:
- Gathers all diagnostic data.
- Filters sensitive fields.
- Writes to `/config/zne-diagnostics-YYYYMMDD-HHMMSS.json`.
- Returns the file path to the caller.

---

### 2.4 Frontend: Diagnostics Tab

**Claim**: We can add a new "Diagnostics" tab with log list, health summary, and trend.

**Finding**: **Supported**.

**Evidence**:
- The app already uses Lit for reactive components.
- Tab navigation is already implemented (Overview, Sources, Managed Devices).
- We can add a new tab with a list component for logs, a summary card for health, and a simple chart or list for reconciliation trend.
- Auto-refresh via `setInterval` polling the backend service.

**Constraint**: Log data must be fetched via a service call (cannot directly access HA logs).

**Decision**: Implement:
- `_diagnosticsSection()` method rendering the tab content.
- `_handleExportDiagnostics()` calling the backend service.
- Polling every 30 seconds to refresh log entries and health summary.

---

### 2.5 Frontend: Error Banners & Repair Guidance

**Claim**: We can show error banners with repair links when sources are missing or mismatched.

**Finding**: **Supported**.

**Evidence**:
- The app already subscribes to `sensor.zero_net_export_status` and `binary_sensor.zero_net_export_source_mismatch`.
- We can render conditional UI based on these states.
- HA provides `hass.openConfigFlow()` or direct links to entity config pages.

**Decision**: Implement:
- Error banner component that checks status sensor and mismatch sensor.
- Repair links that open the correct HA config page (e.g., `config/flow` for integration, `config/entities` for specific entities).

---

### 2.6 Security & Privacy

**Claim**: We can avoid exposing sensitive data in diagnostics export.

**Finding**: **Supported**.

**Evidence**:
- We control the data gathered in `async_get_diagnostics()`.
- We can filter out fields like `token`, `password`, `api_key`, `secret`.
- Log entries can be filtered for sensitive patterns (regex).

**Decision**: Implement filtering in `async_export_diagnostics()`:
- Remove known sensitive field names.
- Redact log messages matching patterns like `token=\S+`, `password=\S+`.

---

## 3. Feasibility Summary

| Component | Feasibility | Constraint / Mitigation |
|-----------|-------------|-------------------------|
| Log Retrieval | **Supported** | Internal buffer only (not full HA logs) |
| Sensor States | **Supported** | None |
| Config Entry | **Supported** | None |
| Diagnostics Export | **Supported** | Must filter sensitive data |
| Diagnostics Tab UI | **Supported** | Polling every 30s max |
| Error Banners | **Supported** | None |
| Security/Privacy | **Supported** | Filter sensitive fields/logs |

---

## 4. Acceptance

**Feasibility Check**: **ACCEPTED**

All components are feasible within the Home Assistant integration sandbox and the existing app architecture.

**Next Step**: Proceed to **Implementation Plan** (backend + frontend).

---

**Sign-off**:  
- Feasibility written: 2026-07-02  
- Accepted by: dev agent (self-approval per Milestone 6 definition)  
- No blocking constraints identified.
