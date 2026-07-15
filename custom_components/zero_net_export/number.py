"""Numbers for Zero Net Export."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfPower
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import (
    ZeroNetExportEntity,
    attach_managed_load_device,
    integration_page_managed_load_details,
    managed_load_detail,
    managed_load_display_name,
    managed_load_settings_action_name,
    recorder_safe_managed_detail,
    recorder_safe_validation_details,
    register_managed_load_platform_sync,
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ZeroNetExportNumber(coordinator, "target_export_w", "Target export", 0, 10000, 10),
        ZeroNetExportNumber(coordinator, "deadband_w", "Deadband", 0, 2000, 10),
        ZeroNetExportNumber(coordinator, "battery_reserve_soc", "Battery reserve SOC", 0, 100, 1),
    ]
    state = coordinator.data
    managed_details = integration_page_managed_load_details(entry, state)
    coordinator._zne_integration_page_managed_details = managed_details
    managed_entities = {
        device_key: [ZeroNetExportDevicePriorityNumber(coordinator, device_key, managed_load_display_name(device_key, details))]
        for device_key, details in managed_details.items()
    }
    for device_entities in managed_entities.values():
        entities.extend(device_entities)
    async_add_entities(entities)
    register_managed_load_platform_sync(
        hass,
        entry,
        coordinator,
        async_add_entities,
        managed_entities,
        lambda device_key, details: [
            ZeroNetExportDevicePriorityNumber(coordinator, device_key, managed_load_display_name(device_key, details))
        ],
    )


class ZeroNetExportNumber(ZeroNetExportEntity, NumberEntity):
    def __init__(self, coordinator, key, name, min_value, max_value, step):
        super().__init__(coordinator, key, name)
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return getattr(state, self._key, None)

    @property
    def extra_state_attributes(self):
        return recorder_safe_validation_details(self._validation_details)

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
        super().__init__(coordinator, f"device_{device_key}_priority", managed_load_settings_action_name(device_name, "priority"))
        self._device_key = device_key
        self._zero_net_export_managed_name_suffix = "priority"
        self._attr_entity_category = EntityCategory.CONFIG
        attach_managed_load_device(self, coordinator, device_key, device_name)
        self._attr_native_min_value = 0
        self._attr_native_max_value = 1000
        self._attr_native_step = 1
        self._attr_mode = "box"

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return managed_load_detail(self.coordinator, self._device_key).get("effective_priority")

    @property
    def extra_state_attributes(self):
        return recorder_safe_managed_detail(managed_load_detail(self.coordinator, self._device_key))

    async def async_set_native_value(self, value: float):
        await self.coordinator.async_set_device_priority_override(self._device_key, int(value))
