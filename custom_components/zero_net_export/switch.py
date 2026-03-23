"""Switches for Zero Net Export."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN
from .entity import ZeroNetExportEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [ZeroNetExportEnabledSwitch(coordinator, "enabled", "Enabled")]
    entities.extend(
        ZeroNetExportDeviceEnabledSwitch(coordinator, device_key, details["name"])
        for device_key, details in coordinator.data.device_details.items()
    )
    async_add_entities(entities)


class ZeroNetExportEnabledSwitch(ZeroNetExportEntity, SwitchEntity):
    @property
    def is_on(self):
        return self.coordinator.data.enabled

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.validation_details

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_enabled(False)


class ZeroNetExportDeviceEnabledSwitch(ZeroNetExportEntity, SwitchEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_enabled", f"{device_name} enabled")
        self._device_key = device_key

    @property
    def is_on(self):
        return bool(self.coordinator.data.device_details[self._device_key]["effective_enabled"])

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.device_details[self._device_key]

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_device_enabled_override(self._device_key, True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_device_enabled_override(self._device_key, False)
