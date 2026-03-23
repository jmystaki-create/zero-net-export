"""Binary sensors for Zero Net Export."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN
from .entity import ZeroNetExportEntity


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


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ZeroNetExportBinarySensor(coordinator, "active", "Active"),
        ZeroNetExportBinarySensor(coordinator, "source_mismatch", "Source mismatch"),
        ZeroNetExportBinarySensor(coordinator, "safe_mode", "Safe mode"),
        ZeroNetExportBinarySensor(coordinator, "stale_data", "Stale data"),
        ZeroNetExportBinarySensor(coordinator, "command_failure", "Command failure"),
        ZeroNetExportBinarySensor(coordinator, "battery_below_reserve", "Battery below reserve"),
    ]

    entities.extend(
        ZeroNetExportDeviceUsableBinarySensor(coordinator, device_key, details["name"])
        for device_key, details in coordinator.data.device_details.items()
    )
    entities.extend(
        ZeroNetExportSourceStaleBinarySensor(coordinator, source_key, label)
        for source_key, label in SOURCE_LABELS.items()
    )
    async_add_entities(entities)


class ZeroNetExportBinarySensor(ZeroNetExportEntity, BinarySensorEntity):
    @property
    def is_on(self):
        return getattr(self.coordinator.data, self._key)


class ZeroNetExportSourceStaleBinarySensor(ZeroNetExportEntity, BinarySensorEntity):
    def __init__(self, coordinator, source_key: str, source_label: str):
        super().__init__(coordinator, f"source_{source_key}_stale", f"{source_label} stale")
        self._source_key = source_key

    @property
    def is_on(self):
        freshness = self.coordinator.data.validation_details.get("source_freshness", {}).get(self._source_key, {})
        return bool(freshness.get("stale"))

    @property
    def extra_state_attributes(self):
        diagnostic = self.coordinator.data.validation_details.get("source_diagnostics", {}).get(self._source_key, {})
        freshness = self.coordinator.data.validation_details.get("source_freshness", {}).get(self._source_key, {})
        return {
            **diagnostic,
            "freshness": freshness,
        }


class ZeroNetExportDeviceUsableBinarySensor(ZeroNetExportEntity, BinarySensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_usable", f"{device_name} usable")
        self._device_key = device_key

    @property
    def is_on(self):
        return bool(self.coordinator.data.device_details[self._device_key]["usable"])

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.device_details[self._device_key]
