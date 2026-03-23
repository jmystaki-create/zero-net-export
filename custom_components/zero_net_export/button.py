"""Buttons for Zero Net Export."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from .const import DOMAIN
from .entity import ZeroNetExportEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [ZeroNetExportResetControllerOverridesButton(coordinator)]
    entities.extend(
        ZeroNetExportResetDeviceOverridesButton(coordinator, device_key, details["name"])
        for device_key, details in coordinator.data.device_details.items()
    )
    async_add_entities(entities)


class ZeroNetExportResetControllerOverridesButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "reset_controller_overrides", "Reset controller overrides")

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.validation_details

    async def async_press(self) -> None:
        await self.coordinator.async_reset_controller_overrides()


class ZeroNetExportResetDeviceOverridesButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_reset_overrides", f"{device_name} reset overrides")
        self._device_key = device_key

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.device_details[self._device_key]

    async def async_press(self) -> None:
        await self.coordinator.async_reset_device_overrides(self._device_key)
