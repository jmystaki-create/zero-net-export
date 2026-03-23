"""Selects for Zero Net Export."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity

from .const import DOMAIN, MODES
from .entity import ZeroNetExportEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZeroNetExportModeSelect(coordinator, 'mode', 'Mode')])


class ZeroNetExportModeSelect(ZeroNetExportEntity, SelectEntity):
    @property
    def options(self):
        return MODES

    @property
    def current_option(self):
        return self.coordinator.data.mode

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.validation_details

    async def async_select_option(self, option: str):
        await self.coordinator.async_set_mode(option)
