"""Buttons for Zero Net Export."""
from __future__ import annotations

from homeassistant.components import persistent_notification
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import ZeroNetExportEntity
from .native_support import (
    PRIMARY_CONFIGURE_PATH,
    build_native_operator_readiness,
    build_native_support_center,
    build_native_support_snapshot,
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ZeroNetExportResetControllerOverridesButton(coordinator),
        ZeroNetExportShowNativeSupportCenterButton(coordinator),
        ZeroNetExportShowNativeDiagnosticsButton(coordinator),
        ZeroNetExportShowSetupChecklistButton(coordinator),
    ]
    state = coordinator.data
    if state is not None:
        entities.extend(
            ZeroNetExportResetDeviceOverridesButton(coordinator, device_key, details["name"])
            for device_key, details in state.device_details.items()
        )
    async_add_entities(entities)


def _support_notification_id(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_native_support"


def _diagnostics_notification_id(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_native_diagnostics"


def _setup_notification_id(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_native_setup"


class ZeroNetExportResetControllerOverridesButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "reset_controller_overrides", "Reset controller overrides")

    @property
    def extra_state_attributes(self):
        return self._validation_details

    async def async_press(self) -> None:
        await self.coordinator.async_reset_controller_overrides()


class ZeroNetExportShowNativeSupportCenterButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "show_native_support_center", "Show support center")
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:lifebuoy"

    @property
    def extra_state_attributes(self):
        readiness = build_native_operator_readiness(self.coordinator)
        return {
            "configure_path": PRIMARY_CONFIGURE_PATH,
            "phase": readiness.get("phase"),
            "next_step": readiness.get("next_step"),
            "diagnostic_summary": self._state.diagnostic_summary if self._state else None,
            "health_summary": self._state.health_summary if self._state else None,
        }

    async def async_press(self) -> None:
        support_center = build_native_support_center(self.coordinator)
        persistent_notification.async_create(
            self.hass,
            f"```\n{support_center}\n```",
            title=f"{self.coordinator.entry.title}: support center",
            notification_id=_support_notification_id(self.coordinator.entry.entry_id),
        )


class ZeroNetExportShowNativeDiagnosticsButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "show_native_diagnostics", "Show native diagnostics snapshot")
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:clipboard-pulse-outline"

    @property
    def extra_state_attributes(self):
        return {
            "configure_path": PRIMARY_CONFIGURE_PATH,
            "diagnostic_summary": self._state.diagnostic_summary if self._state else None,
            "health_summary": self._state.health_summary if self._state else None,
        }

    async def async_press(self) -> None:
        snapshot = build_native_support_snapshot(self.coordinator)
        message = (
            "Native Zero Net Export diagnostics snapshot\n\n"
            "This is intended for the Home Assistant device page, Scripts, and button.press automations so diagnostics stay reachable from native Home Assistant surfaces.\n\n"
            f"Primary setup path: {PRIMARY_CONFIGURE_PATH}\n\n"
            f"```\n{snapshot}\n```"
        )
        persistent_notification.async_create(
            self.hass,
            message,
            title=f"{self.coordinator.entry.title}: native diagnostics snapshot",
            notification_id=_diagnostics_notification_id(self.coordinator.entry.entry_id),
        )


class ZeroNetExportShowSetupChecklistButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "show_setup_checklist", "Show setup checklist")
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:format-list-checks"

    @property
    def extra_state_attributes(self):
        readiness = build_native_operator_readiness(self.coordinator)
        return {
            "configure_path": PRIMARY_CONFIGURE_PATH,
            "diagnostic_summary": self._state.diagnostic_summary if self._state else None,
            "source_mismatch": self._state.source_mismatch if self._state else None,
            "stale_data": self._state.stale_data if self._state else None,
            "checklist": readiness.get("checklist"),
        }

    async def async_press(self) -> None:
        readiness = build_native_operator_readiness(self.coordinator)
        checklist = readiness.get("checklist") or []
        checklist_lines = [
            f"- [{'x' if item.get('complete') else ' '}] {item.get('label')}: {item.get('detail')}"
            for item in checklist
        ]
        message = "\n".join(
            [
                "Zero Net Export native setup checklist",
                "",
                f"Entry: {self.coordinator.entry.title}",
                f"Primary setup path: {PRIMARY_CONFIGURE_PATH}",
                f"Readiness phase: {readiness.get('phase') or 'unknown'}",
                f"Summary: {readiness.get('summary') or (self._state.health_summary if self._state else None)}",
                f"Next step: {readiness.get('next_step') or (self._state.recommendation if self._state else None)}",
                "",
                "Checklist",
                *(checklist_lines or ["- No checklist available yet."]),
            ]
        )
        persistent_notification.async_create(
            self.hass,
            message,
            title=f"{self.coordinator.entry.title}: setup checklist",
            notification_id=_setup_notification_id(self.coordinator.entry.entry_id),
        )


class ZeroNetExportResetDeviceOverridesButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_reset_overrides", f"{device_name} reset overrides")
        self._device_key = device_key

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})

    async def async_press(self) -> None:
        await self.coordinator.async_reset_device_overrides(self._device_key)
