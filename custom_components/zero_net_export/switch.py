"""Switches for Zero Net Export."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN
from .entity import ZeroNetExportEntity, attach_managed_load_device


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [ZeroNetExportEnabledSwitch(coordinator, "enabled", "Enabled")]
    state = coordinator.data
    if state is not None:
        entities.extend(
            ZeroNetExportDeviceEnabledSwitch(coordinator, device_key, details["name"])
            for device_key, details in state.device_details.items()
        )
    async_add_entities(entities)


class ZeroNetExportEnabledSwitch(ZeroNetExportEntity, SwitchEntity):
    @property
    def is_on(self):
        state = self._state
        if state is None:
            return None
        return state.enabled

    @property
    def extra_state_attributes(self):
        return self._validation_details

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_enabled(False)


class ZeroNetExportDeviceEnabledSwitch(ZeroNetExportEntity, SwitchEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_enabled", f"{device_name} enabled")
        self._device_key = device_key
        attach_managed_load_device(self, coordinator, device_key, device_name)

    @property
    def is_on(self):
        state = self._state
        if state is None:
            return None
        return bool(state.device_details.get(self._device_key, {}).get("effective_enabled"))

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_device_enabled_override(self._device_key, True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_device_enabled_override(self._device_key, False)
