"""Numbers for Zero Net Export."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfPower

from .const import DOMAIN
from .entity import ZeroNetExportEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ZeroNetExportNumber(coordinator, "target_export_w", "Target export", 0, 10000, 10),
        ZeroNetExportNumber(coordinator, "deadband_w", "Deadband", 0, 2000, 10),
        ZeroNetExportNumber(coordinator, "battery_reserve_soc", "Battery reserve SOC", 0, 100, 1),
    ]
    entities.extend(
        [
            ZeroNetExportDevicePriorityNumber(coordinator, device_key, details["name"])
            for device_key, details in coordinator.data.device_details.items()
        ]
    )
    async_add_entities(entities)


class ZeroNetExportNumber(ZeroNetExportEntity, NumberEntity):
    def __init__(self, coordinator, key, name, min_value, max_value, step):
        super().__init__(coordinator, key, name)
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step

    @property
    def native_value(self):
        return getattr(self.coordinator.data, self._key)

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.validation_details

    async def async_set_native_value(self, value: float):
        if self._key == "target_export_w":
            await self.coordinator.async_set_target_export_w_override(value)
        elif self._key == "deadband_w":
            await self.coordinator.async_set_deadband_w_override(value)
        elif self._key == "battery_reserve_soc":
            await self.coordinator.async_set_battery_reserve_soc_override(value)

    @property
    def native_unit_of_measurement(self):
        if self._key == "target_export_w":
            return UnitOfPower.WATT
        if self._key == "battery_reserve_soc":
            return "%"
        return None


class ZeroNetExportDevicePriorityNumber(ZeroNetExportEntity, NumberEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_priority", f"{device_name} priority")
        self._device_key = device_key
        self._attr_native_min_value = 0
        self._attr_native_max_value = 1000
        self._attr_native_step = 1
        self._attr_mode = "box"

    @property
    def native_value(self):
        return self.coordinator.data.device_details[self._device_key]["effective_priority"]

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.device_details[self._device_key]

    async def async_set_native_value(self, value: float):
        await self.coordinator.async_set_device_priority_override(self._device_key, int(value))
