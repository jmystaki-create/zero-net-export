"""Selects for Zero Net Export."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity

from .const import DOMAIN, MODE_LABELS, MODES
from .entity import ZeroNetExportEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZeroNetExportModeSelect(coordinator, 'mode', 'Mode')])


class ZeroNetExportModeSelect(ZeroNetExportEntity, SelectEntity):
    @property
    def options(self):
        return [MODE_LABELS.get(mode, mode) for mode in MODES]

    @property
    def current_option(self):
        state = self._state
        if state is None:
            return None
        mode = getattr(state, "mode", None)
        if mode is None:
            return None
        return MODE_LABELS.get(mode, mode)

    @property
    def extra_state_attributes(self):
        return self._validation_details

    async def async_select_option(self, option: str):
        selected_mode = next((mode for mode, label in MODE_LABELS.items() if label == option), option)
        await self.coordinator.async_set_mode(selected_mode)
