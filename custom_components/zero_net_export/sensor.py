"""Sensors for Zero Net Export."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower, UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from .const import DEVICE_CANDIDATE_DOMAINS, DEVICE_CANDIDATE_FIXED_DOMAINS, DOMAIN, INTEGRATION_VERSION
from .entity import ZeroNetExportEntity
from .native_support import build_native_command_center_summary
from .release_info import build_release_info


SENSOR_DEFS = {
    "installed_version": "Installed version",
    "previous_installed_version": "Previous installed version",
    "release_summary": "Release summary",
    "changes_preview": "Changes preview",
    "update_summary": "Update summary",
    "status": "Status",
    "reason": "Reason",
    "recommendation": "Recommendation",
    "diagnostic_summary": "Diagnostic summary",
    "confidence": "Confidence",
    "stale_source_count": "Stale source count",
    "stale_source_summary": "Stale source summary",
    "health_status": "Health status",
    "health_summary": "Health summary",
    "actions_today": "Actions today",
    "successful_actions_today": "Successful actions today",
    "failed_actions_today": "Failed actions today",
    "energy_redirected_today_kwh": "Energy redirected today",
    "active_controlled_power_w": "Active controlled power",
    "battery_reserve_soc": "Battery reserve SOC",
    "solar_power_w": "Solar power",
    "grid_import_power_w": "Grid import power",
    "grid_export_power_w": "Grid export power",
    "home_load_power_w": "Home load power",
    "battery_soc": "Battery state of charge",
    "surplus_w": "Surplus",
    "last_reconciliation_error_w": "Last reconciliation error",
    "device_count": "Configured devices",
    "enabled_device_count": "Enabled devices",
    "usable_device_count": "Usable devices",
    "fixed_device_count": "Fixed devices",
    "variable_device_count": "Variable devices",
    "controllable_nominal_power_w": "Configured controllable power",
    "usable_nominal_power_w": "Usable controllable power",
    "device_status_summary": "Device status summary",
    "control_status": "Control status",
    "control_summary": "Control summary",
    "control_reason": "Control reason",
    "control_guard_summary": "Control guard summary",
    "last_action_status": "Last action status",
    "last_action_summary": "Last action summary",
    "last_action_at": "Last action at",
    "last_successful_action_at": "Last successful action at",
    "last_failed_action_at": "Last failed action at",
    "last_action_device": "Last action device",
    "last_failed_action_device": "Last failed action device",
    "last_failed_action_message": "Last failed action message",
    "recent_action_summary": "Recent action summary",
    "recent_failure_summary": "Recent failure summary",
    "last_successful_action_summary": "Last successful action summary",
    "action_history_count": "Action history count",
    "successful_action_count": "Successful action count",
    "failed_action_count": "Failed action count",
    "total_successful_action_count": "Total successful action count",
    "total_failed_action_count": "Total failed action count",
    "export_error_w": "Export error",
    "planned_action_count": "Planned action count",
    "executable_action_count": "Executable action count",
    "blocked_planned_action_count": "Blocked planned action count",
    "planned_power_delta_w": "Planned power delta",
    "variable_planned_power_delta_w": "Variable planned power delta",
    "fixed_planned_power_delta_w": "Fixed planned power delta",
    "managed_fleet_overview": "Managed fleet overview",
    "unmanaged_candidate_count": "Unmanaged candidate devices",
    "unmanaged_candidate_overview": "Unmanaged candidate overview",
    "top_unmanaged_candidate": "Top unmanaged candidate",
    "top_candidate_fit": "Top candidate fit",
    "top_candidate_warnings": "Top candidate warnings",
    "candidate_shortlist": "Candidate shortlist",
    "candidate_shortlist_fit": "Candidate shortlist fit",
    "fleet_console_next_step": "Fleet console next step",
    "command_center_status": "Command center status",
    "command_center_recommended_path": "Command center recommended path",
    "command_center_next_step": "Command center next step",
}

SOURCE_LABELS = {
    "solar_power": "Solar power",
    "solar_energy": "Solar energy",
    "grid_import_power": "Grid import power",
    "grid_export_power": "Grid export power",
    "grid_import_energy": "Grid import energy",
    "grid_export_energy": "Grid export energy",
    "home_load_power": "Home load power",
    "battery_soc": "Battery state of charge",
    "battery_charge_power": "Battery charge power",
    "battery_discharge_power": "Battery discharge power",
}

TIMESTAMP_SENSOR_KEYS = {"last_action_at", "last_successful_action_at", "last_failed_action_at"}
VALIDATION_ATTRIBUTE_SENSOR_KEYS = {
    "release_summary",
    "changes_preview",
    "confidence",
    "recommendation",
    "diagnostic_summary",
    "stale_source_count",
    "stale_source_summary",
    "health_status",
    "health_summary",
    "actions_today",
    "successful_actions_today",
    "failed_actions_today",
    "energy_redirected_today_kwh",
    "active_controlled_power_w",
    "battery_reserve_soc",
    "device_status_summary",
    "control_status",
    "control_summary",
    "control_reason",
    "control_guard_summary",
    "last_action_status",
    "last_action_summary",
    "last_action_at",
    "last_successful_action_at",
    "last_failed_action_at",
    "last_action_device",
    "last_failed_action_device",
    "last_failed_action_message",
    "recent_action_summary",
    "recent_failure_summary",
    "last_successful_action_summary",
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [ZeroNetExportSensor(coordinator, key, name) for key, name in SENSOR_DEFS.items()]
    entities.extend(_build_source_entities(coordinator))

    state = coordinator.data
    if state is not None:
        for device_key, details in state.device_details.items():
            entities.extend(
                [
                    ZeroNetExportDeviceStatusSensor(coordinator, device_key, details["name"]),
                    ZeroNetExportDevicePowerSensor(coordinator, device_key, details["name"], "current_power_w", "Current power"),
                    ZeroNetExportDevicePlanSensor(coordinator, device_key, details["name"]),
                    ZeroNetExportDeviceGuardSensor(coordinator, device_key, details["name"]),
                    ZeroNetExportDevicePowerSensor(coordinator, device_key, details["name"], "planned_power_delta_w", "Planned power delta"),
                    ZeroNetExportDevicePowerSensor(coordinator, device_key, details["name"], "last_requested_power_w", "Last requested power"),
                    ZeroNetExportDevicePowerSensor(coordinator, device_key, details["name"], "last_applied_power_w", "Last applied power"),
                    ZeroNetExportDeviceDurationSensor(coordinator, device_key, details["name"], "current_active_seconds", "Current active runtime"),
                    ZeroNetExportDeviceDurationSensor(coordinator, device_key, details["name"], "active_runtime_today_seconds", "Active runtime today"),
                    ZeroNetExportDeviceTimestampSensor(coordinator, device_key, details["name"], "last_action_at", "Last action at"),
                    ZeroNetExportDeviceTimestampSensor(coordinator, device_key, details["name"], "last_applied_at", "Last applied at"),
                    ZeroNetExportDeviceDetailSensor(coordinator, device_key, details["name"], "last_action_status", "Last action status"),
                    ZeroNetExportDeviceDetailSensor(coordinator, device_key, details["name"], "last_action_result_message", "Last action result"),
                ]
            )
            if details["kind"] == "variable":
                entities.append(
                    ZeroNetExportDevicePowerSensor(
                        coordinator,
                        device_key,
                        details["name"],
                        "current_target_power_w",
                        "Target power",
                    )
                )

    async_add_entities(entities)


def _build_source_entities(coordinator):
    entities = []
    for source_key, label in SOURCE_LABELS.items():
        entities.extend(
            [
                ZeroNetExportSourceStatusSensor(coordinator, source_key, label),
                ZeroNetExportSourceReadingSensor(coordinator, source_key, label),
                ZeroNetExportSourceAgeSensor(coordinator, source_key, label),
                ZeroNetExportSourceIssueCountSensor(coordinator, source_key, label),
            ]
        )
    return entities


def _candidate_fit_details(candidate: dict[str, str]) -> dict[str, str | list[str]]:
    domain = candidate.get("domain") or ""
    confidence = "medium"
    summary = "Looks like a plausible candidate, but review before promotion."
    warnings: list[str] = []
    if domain == "switch":
        confidence = "high"
        summary = "Strong fixed-load candidate when this switch controls a real discretionary appliance or relay."
    elif domain == "light":
        confidence = "medium"
        summary = "Potentially controllable, but many lights are comfort loads rather than discretionary sinks."
        warnings.append("Confirm this light is appropriate for automated energy control.")
    elif domain == "input_boolean":
        confidence = "low"
        summary = "Likely a helper or intent flag rather than a physical load."
        warnings.append("Verify this helper actually drives a safe controllable device.")
    elif domain == "number":
        confidence = "high"
        summary = "Strong variable-load candidate if this entity is a writable power/current target."
    elif domain == "input_number":
        confidence = "medium"
        summary = "Possible variable-load candidate, but often just a helper value."
        warnings.append("Check that changing this helper really affects a physical device.")
    return {"confidence": confidence, "summary": summary, "warnings": warnings}


def _candidate_devices_for_hass(hass, managed_entity_ids: set[str]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for state in sorted(hass.states.async_all(), key=lambda item: item.entity_id):
        entity_id = state.entity_id
        domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
        if domain not in DEVICE_CANDIDATE_DOMAINS:
            continue
        if entity_id in managed_entity_ids:
            continue
        state_value = str(state.state).lower()
        if state_value in {"unknown", "unavailable"}:
            continue
        candidates.append(
            {
                "entity_id": entity_id,
                "name": str(state.attributes.get("friendly_name") or entity_id),
                "domain": domain,
                "kind": "fixed" if domain in DEVICE_CANDIDATE_FIXED_DOMAINS else "variable",
                "state": str(state.state),
            }
        )
    return candidates


class ZeroNetExportSensor(ZeroNetExportEntity, SensorEntity):
    @property
    def native_value(self):
        if self._key == "installed_version":
            return INTEGRATION_VERSION
        if self._key in {"release_summary", "changes_preview"}:
            info = build_release_info(INTEGRATION_VERSION, include_changelog=False)
            return info.get(self._key)
        if self._key in {"previous_installed_version", "update_summary"}:
            update = self._validation_details.get("release_update", {})
            mapping = {
                "previous_installed_version": update.get("previous_installed_version"),
                "update_summary": update.get("summary"),
            }
            return mapping.get(self._key)
        state = self._state
        if state is None:
            return None
        if self._key == "managed_fleet_overview":
            device_details = list((state.device_details or {}).values())
            if not device_details:
                return "No managed devices yet"
            enabled = sum(1 for detail in device_details if detail.get("effective_enabled"))
            usable = sum(1 for detail in device_details if detail.get("usable"))
            return f"{len(device_details)} managed, {enabled} enabled, {usable} usable"
        if self._key == "unmanaged_candidate_count":
            managed_ids = {str(detail.get('entity_id')) for detail in (state.device_details or {}).values() if detail.get('entity_id')}
            return len(_candidate_devices_for_hass(self.hass, managed_ids))
        if self._key == "unmanaged_candidate_overview":
            managed_ids = {str(detail.get('entity_id')) for detail in (state.device_details or {}).values() if detail.get('entity_id')}
            candidates = _candidate_devices_for_hass(self.hass, managed_ids)
            if not candidates:
                return "No unmanaged candidate devices discovered"
            preview = ", ".join(item['name'] for item in candidates[:4])
            if len(candidates) > 4:
                preview += f", +{len(candidates) - 4} more"
            return preview
        if self._key == "top_unmanaged_candidate":
            managed_ids = {str(detail.get('entity_id')) for detail in (state.device_details or {}).values() if detail.get('entity_id')}
            candidates = _candidate_devices_for_hass(self.hass, managed_ids)
            if not candidates:
                return "None"
            top = candidates[0]
            return f"{top['name']} ({top['entity_id']})"
        if self._key == "top_candidate_fit":
            managed_ids = {str(detail.get('entity_id')) for detail in (state.device_details or {}).values() if detail.get('entity_id')}
            candidates = _candidate_devices_for_hass(self.hass, managed_ids)
            if not candidates:
                return "No candidate fit guidance available"
            fit = _candidate_fit_details(candidates[0])
            return f"{fit['confidence']}: {fit['summary']}"
        if self._key == "top_candidate_warnings":
            managed_ids = {str(detail.get('entity_id')) for detail in (state.device_details or {}).values() if detail.get('entity_id')}
            candidates = _candidate_devices_for_hass(self.hass, managed_ids)
            if not candidates:
                return "No warnings"
            fit = _candidate_fit_details(candidates[0])
            warnings = fit.get('warnings') or []
            return "; ".join(warnings) if warnings else "No immediate warnings"
        if self._key == "candidate_shortlist":
            managed_ids = {str(detail.get('entity_id')) for detail in (state.device_details or {}).values() if detail.get('entity_id')}
            candidates = _candidate_devices_for_hass(self.hass, managed_ids)
            if not candidates:
                return "No additional candidates"
            shortlist = candidates[:3]
            return "; ".join(f"{item['name']} ({item['entity_id']})" for item in shortlist)
        if self._key == "candidate_shortlist_fit":
            managed_ids = {str(detail.get('entity_id')) for detail in (state.device_details or {}).values() if detail.get('entity_id')}
            candidates = _candidate_devices_for_hass(self.hass, managed_ids)
            if not candidates:
                return "No shortlist fit guidance"
            shortlist = candidates[:3]
            parts = []
            for item in shortlist:
                fit = _candidate_fit_details(item)
                parts.append(f"{item['name']}: {fit['confidence']}")
            return "; ".join(parts)
        if self._key == "fleet_console_next_step":
            managed_ids = {str(detail.get('entity_id')) for detail in (state.device_details or {}).values() if detail.get('entity_id')}
            candidates = _candidate_devices_for_hass(self.hass, managed_ids)
            if not state.device_details and candidates:
                return "Open Configure -> Managed devices and tag the first candidate into the fleet"
            if candidates:
                return "Review unmanaged candidates, then promote the next controllable device in Configure"
            return "Open Configure -> Policy and controller settings to tune behaviour, or Configure -> Sources and source mapping if runtime health still needs work"
        if self._key in {"command_center_status", "command_center_recommended_path", "command_center_next_step"}:
            command_center = build_native_command_center_summary(self.coordinator)
            mapping = {
                "command_center_status": command_center.get("recommended_section"),
                "command_center_recommended_path": command_center.get("recommended_path"),
                "command_center_next_step": command_center.get("next_action_summary"),
            }
            return mapping.get(self._key)
        return getattr(state, self._key)

    @property
    def entity_category(self):
        if self._key in {
            "installed_version",
            "previous_installed_version",
            "release_summary",
            "changes_preview",
            "update_summary",
            "diagnostic_summary",
            "health_status",
            "health_summary",
            "recommendation",
            "control_status",
            "control_summary",
            "control_reason",
            "control_guard_summary",
            "last_action_status",
            "last_action_summary",
            "last_action_at",
            "last_successful_action_at",
            "last_failed_action_at",
            "last_action_device",
            "last_failed_action_device",
            "last_failed_action_message",
            "recent_action_summary",
            "recent_failure_summary",
            "last_successful_action_summary",
            "stale_source_count",
            "stale_source_summary",
            "action_history_count",
            "successful_action_count",
            "failed_action_count",
            "total_successful_action_count",
            "total_failed_action_count",
            "planned_action_count",
            "executable_action_count",
            "blocked_planned_action_count",
            "command_center_status",
            "command_center_recommended_path",
            "command_center_next_step",
        }:
            return EntityCategory.DIAGNOSTIC
        return None

    @property
    def native_unit_of_measurement(self):
        if self._key.endswith("_power_w") or self._key in {
            "surplus_w",
            "last_reconciliation_error_w",
            "controllable_nominal_power_w",
            "usable_nominal_power_w",
            "export_error_w",
            "planned_power_delta_w",
            "variable_planned_power_delta_w",
            "fixed_planned_power_delta_w",
        }:
            return UnitOfPower.WATT
        if self._key == "energy_redirected_today_kwh":
            return UnitOfEnergy.KILO_WATT_HOUR
        if self._key in {"battery_soc", "battery_reserve_soc"}:
            return PERCENTAGE
        return None

    @property
    def extra_state_attributes(self):
        if self._key == "installed_version":
            return build_release_info(INTEGRATION_VERSION, include_changelog=False)
        if self._key in {"previous_installed_version", "release_summary", "changes_preview", "update_summary"}:
            return {
                **build_release_info(INTEGRATION_VERSION, include_changelog=False),
                **(self._validation_details.get("release_update", {}) or {}),
                "config_entry_version": self.coordinator.entry.version,
            }
        if self._key in {"managed_fleet_overview", "unmanaged_candidate_count", "unmanaged_candidate_overview", "top_unmanaged_candidate", "top_candidate_fit", "top_candidate_warnings", "candidate_shortlist", "candidate_shortlist_fit", "fleet_console_next_step"}:
            state = self._state
            if state is None:
                return None
            managed_ids = {str(detail.get('entity_id')) for detail in (state.device_details or {}).values() if detail.get('entity_id')}
            candidates = _candidate_devices_for_hass(self.hass, managed_ids)
            top_candidate = candidates[0] if candidates else None
            return {
                "configure_path": "Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed devices",
                "managed_devices": list((state.device_details or {}).values()),
                "candidate_devices": candidates[:12],
                "candidate_count": len(candidates),
                "top_candidate": top_candidate,
                "top_candidate_fit": _candidate_fit_details(top_candidate) if top_candidate else None,
            }
        if self._key in {"command_center_status", "command_center_recommended_path", "command_center_next_step"}:
            command_center = build_native_command_center_summary(self.coordinator)
            return {
                "source_status": command_center.get("source_status"),
                "device_status": command_center.get("device_status"),
                "policy_status": command_center.get("policy_status"),
                "support_status": command_center.get("support_status"),
                "recommended_section": command_center.get("recommended_section"),
                "recommended_path": command_center.get("recommended_path"),
                "sources_path": command_center.get("sources_path"),
                "devices_path": command_center.get("devices_path"),
                "policy_path": command_center.get("policy_path"),
                "support_path": command_center.get("support_path"),
            }
        if self._key in VALIDATION_ATTRIBUTE_SENSOR_KEYS:
            return self._validation_details
        return None

    @property
    def device_class(self):
        if self._key in TIMESTAMP_SENSOR_KEYS:
            return SensorDeviceClass.TIMESTAMP
        return None


class ZeroNetExportSourceBaseSensor(ZeroNetExportEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, source_key: str, source_label: str, suffix_key: str, suffix_name: str):
        super().__init__(coordinator, f"source_{source_key}_{suffix_key}", f"{source_label} {suffix_name}")
        self._source_key = source_key

    @property
    def _source_diagnostic(self):
        return self._validation_details.get("source_diagnostics", {}).get(self._source_key, {})

    @property
    def _source_freshness(self):
        return self._validation_details.get("source_freshness", {}).get(self._source_key, {})

    @property
    def extra_state_attributes(self):
        return {
            **self._source_diagnostic,
            "freshness": self._source_freshness,
        }


class ZeroNetExportSourceStatusSensor(ZeroNetExportSourceBaseSensor):
    def __init__(self, coordinator, source_key: str, source_label: str):
        super().__init__(coordinator, source_key, source_label, "status", "status")

    @property
    def native_value(self):
        return self._source_diagnostic.get("status")


class ZeroNetExportSourceReadingSensor(ZeroNetExportSourceBaseSensor):
    def __init__(self, coordinator, source_key: str, source_label: str):
        super().__init__(coordinator, source_key, source_label, "reading", "reading")

    @property
    def native_value(self):
        return self._source_diagnostic.get("value")

    @property
    def native_unit_of_measurement(self):
        return self._source_diagnostic.get("unit")


class ZeroNetExportSourceAgeSensor(ZeroNetExportSourceBaseSensor):
    def __init__(self, coordinator, source_key: str, source_label: str):
        super().__init__(coordinator, source_key, source_label, "age_seconds", "age")

    @property
    def native_value(self):
        return self._source_freshness.get("age_seconds")

    @property
    def native_unit_of_measurement(self):
        return "s"


class ZeroNetExportSourceIssueCountSensor(ZeroNetExportSourceBaseSensor):
    def __init__(self, coordinator, source_key: str, source_label: str):
        super().__init__(coordinator, source_key, source_label, "issue_count", "issue count")

    @property
    def native_value(self):
        issue_counts = self._source_diagnostic.get("issue_counts") or {}
        return sum(int(issue_counts.get(level) or 0) for level in ("error", "warning", "info"))


class ZeroNetExportDeviceStatusSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_status", f"{device_name} status")
        self._device_key = device_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get("status")

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})


class ZeroNetExportDevicePlanSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_planned_action", f"{device_name} planned action")
        self._device_key = device_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get("planned_action")

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})


class ZeroNetExportDeviceGuardSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_guard_status", f"{device_name} guard status")
        self._device_key = device_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get("guard_status")

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})


class ZeroNetExportDevicePowerSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", f"{device_name} {suffix}")
        self._device_key = device_key
        self._value_key = value_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get(self._value_key)

    @property
    def native_unit_of_measurement(self):
        return UnitOfPower.WATT

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})


class ZeroNetExportDeviceDurationSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", f"{device_name} {suffix}")
        self._device_key = device_key
        self._value_key = value_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get(self._value_key)

    @property
    def native_unit_of_measurement(self):
        return UnitOfTime.SECONDS

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})


class ZeroNetExportDeviceTimestampSensor(ZeroNetExportEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", f"{device_name} {suffix}")
        self._device_key = device_key
        self._value_key = value_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get(self._value_key)

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})


class ZeroNetExportDeviceDetailSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", f"{device_name} {suffix}")
        self._device_key = device_key
        self._value_key = value_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get(self._value_key)

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})
