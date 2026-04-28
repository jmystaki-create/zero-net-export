"""Switches for Zero Net Export."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import (
    ZeroNetExportEntity,
    attach_managed_load_device,
    integration_page_managed_load_details,
    managed_load_detail,
    managed_load_display_name,
    managed_load_settings_action_name,
    register_managed_load_platform_sync,
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [ZeroNetExportEnabledSwitch(coordinator, "enabled", "Enabled")]
    state = coordinator.data
    managed_details = integration_page_managed_load_details(entry, state)
    coordinator._zne_integration_page_managed_details = managed_details
    managed_entities = {
        device_key: [ZeroNetExportDeviceEnabledSwitch(coordinator, device_key, managed_load_display_name(device_key, details))]
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
            ZeroNetExportDeviceEnabledSwitch(coordinator, device_key, managed_load_display_name(device_key, details))
        ],
    )


class ZeroNetExportEnabledSwitch(ZeroNetExportEntity, SwitchEntity):
    @property
    def is_on(self):
        state = self._state
        if state is None:
            return None
        return getattr(state, "enabled", None)

    @property
    def extra_state_attributes(self):
        return self._validation_details

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_enabled(False)


class ZeroNetExportDeviceEnabledSwitch(ZeroNetExportEntity, SwitchEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_enabled", managed_load_settings_action_name(device_name, "enabled"))
        self._device_key = device_key
        self._zero_net_export_managed_name_suffix = "enabled"
        self._attr_entity_category = EntityCategory.CONFIG
        attach_managed_load_device(self, coordinator, device_key, device_name)

    @property
    def is_on(self):
        state = self._state
        if state is None:
            return None
        return managed_load_detail(self.coordinator, self._device_key).get("effective_enabled")

    @property
    def extra_state_attributes(self):
        return managed_load_detail(self.coordinator, self._device_key)

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_device_enabled_override(self._device_key, True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_device_enabled_override(self._device_key, False)
