"""Binary sensors for Zero Net Export."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import ZeroNetExportEntity, attach_managed_load_device, managed_load_detail, managed_load_display_name


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
        ZeroNetExportBinarySensor(
            coordinator,
            "source_mismatch",
            "Source mismatch",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        ZeroNetExportBinarySensor(coordinator, "safe_mode", "Safe mode", entity_category=EntityCategory.DIAGNOSTIC),
        ZeroNetExportBinarySensor(coordinator, "stale_data", "Stale data", entity_category=EntityCategory.DIAGNOSTIC),
        ZeroNetExportBinarySensor(
            coordinator,
            "command_failure",
            "Command failure",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        ZeroNetExportBinarySensor(
            coordinator,
            "battery_below_reserve",
            "Battery below reserve",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    ]

    state = coordinator.data
    if state is not None:
        entities.extend(
            ZeroNetExportDeviceUsableBinarySensor(coordinator, device_key, managed_load_display_name(device_key, details))
            for device_key, details in (getattr(state, "device_details", {}) or {}).items()
        )
    entities.extend(
        ZeroNetExportSourceStaleBinarySensor(coordinator, source_key, label)
        for source_key, label in SOURCE_LABELS.items()
    )
    async_add_entities(entities)


class ZeroNetExportBinarySensor(ZeroNetExportEntity, BinarySensorEntity):
    def __init__(self, coordinator, key, name, *, entity_category=None):
        super().__init__(coordinator, key, name)
        self._attr_entity_category = entity_category

    @property
    def is_on(self):
        state = self._state
        if state is None:
            return None
        return getattr(state, self._key, None)


class ZeroNetExportSourceStaleBinarySensor(ZeroNetExportEntity, BinarySensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, source_key: str, source_label: str):
        super().__init__(coordinator, f"source_{source_key}_stale", f"{source_label} stale")
        self._source_key = source_key

    @property
    def is_on(self):
        freshness = self._validation_details.get("source_freshness", {}).get(self._source_key, {})
        return bool(freshness.get("stale"))

    @property
    def extra_state_attributes(self):
        diagnostic = self._validation_details.get("source_diagnostics", {}).get(self._source_key, {})
        freshness = self._validation_details.get("source_freshness", {}).get(self._source_key, {})
        return {
            **diagnostic,
            "freshness": freshness,
        }


class ZeroNetExportDeviceUsableBinarySensor(ZeroNetExportEntity, BinarySensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_usable", f"{device_name} usable")
        self._device_key = device_key
        attach_managed_load_device(self, coordinator, device_key, device_name)

    @property
    def is_on(self):
        state = self._state
        if state is None:
            return None
        return managed_load_detail(self.coordinator, self._device_key).get("usable")

    @property
    def extra_state_attributes(self):
        return managed_load_detail(self.coordinator, self._device_key)
