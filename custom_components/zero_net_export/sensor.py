"""Sensors for Zero Net Export."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower, UnitOfTime

from .const import DOMAIN
from .entity import ZeroNetExportEntity


SENSOR_DEFS = {
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

    for device_key, details in coordinator.data.device_details.items():
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


class ZeroNetExportSensor(ZeroNetExportEntity, SensorEntity):
    @property
    def native_value(self):
        return getattr(self.coordinator.data, self._key)

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
        if self._key in VALIDATION_ATTRIBUTE_SENSOR_KEYS:
            return self.coordinator.data.validation_details
        return None

    @property
    def device_class(self):
        if self._key in TIMESTAMP_SENSOR_KEYS:
            return SensorDeviceClass.TIMESTAMP
        return None


class ZeroNetExportSourceBaseSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, source_key: str, source_label: str, suffix_key: str, suffix_name: str):
        super().__init__(coordinator, f"source_{source_key}_{suffix_key}", f"{source_label} {suffix_name}")
        self._source_key = source_key

    @property
    def _source_diagnostic(self):
        return self.coordinator.data.validation_details.get("source_diagnostics", {}).get(self._source_key, {})

    @property
    def _source_freshness(self):
        return self.coordinator.data.validation_details.get("source_freshness", {}).get(self._source_key, {})

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
        return self.coordinator.data.device_details[self._device_key]["status"]

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.device_details[self._device_key]


class ZeroNetExportDevicePlanSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_planned_action", f"{device_name} planned action")
        self._device_key = device_key

    @property
    def native_value(self):
        return self.coordinator.data.device_details[self._device_key]["planned_action"]

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.device_details[self._device_key]


class ZeroNetExportDeviceGuardSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_guard_status", f"{device_name} guard status")
        self._device_key = device_key

    @property
    def native_value(self):
        return self.coordinator.data.device_details[self._device_key]["guard_status"]

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.device_details[self._device_key]


class ZeroNetExportDevicePowerSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", f"{device_name} {suffix}")
        self._device_key = device_key
        self._value_key = value_key

    @property
    def native_value(self):
        return self.coordinator.data.device_details[self._device_key][self._value_key]

    @property
    def native_unit_of_measurement(self):
        return UnitOfPower.WATT

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.device_details[self._device_key]


class ZeroNetExportDeviceDurationSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", f"{device_name} {suffix}")
        self._device_key = device_key
        self._value_key = value_key

    @property
    def native_value(self):
        return self.coordinator.data.device_details[self._device_key][self._value_key]

    @property
    def native_unit_of_measurement(self):
        return UnitOfTime.SECONDS

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.device_details[self._device_key]


class ZeroNetExportDeviceTimestampSensor(ZeroNetExportEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", f"{device_name} {suffix}")
        self._device_key = device_key
        self._value_key = value_key

    @property
    def native_value(self):
        return self.coordinator.data.device_details[self._device_key][self._value_key]

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.device_details[self._device_key]


class ZeroNetExportDeviceDetailSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", f"{device_name} {suffix}")
        self._device_key = device_key
        self._value_key = value_key

    @property
    def native_value(self):
        return self.coordinator.data.device_details[self._device_key][self._value_key]

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.device_details[self._device_key]
