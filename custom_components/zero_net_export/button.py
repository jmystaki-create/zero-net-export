"""Buttons for Zero Net Export."""
from __future__ import annotations

from homeassistant.components import persistent_notification
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import ZeroNetExportEntity
from .panel import build_native_operator_readiness, build_native_support_snapshot
from .panel_paths import panel_setup_path


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ZeroNetExportResetControllerOverridesButton(coordinator),
        ZeroNetExportShowNativeDiagnosticsButton(coordinator),
        ZeroNetExportShowSetupChecklistButton(coordinator),
    ]
    entities.extend(
        ZeroNetExportResetDeviceOverridesButton(coordinator, device_key, details["name"])
        for device_key, details in coordinator.data.device_details.items()
    )
    async_add_entities(entities)


def _diagnostics_notification_id(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_native_diagnostics"


def _setup_notification_id(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_native_setup"


class ZeroNetExportResetControllerOverridesButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "reset_controller_overrides", "Reset controller overrides")

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.validation_details

    async def async_press(self) -> None:
        await self.coordinator.async_reset_controller_overrides()


class ZeroNetExportShowNativeDiagnosticsButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "show_native_diagnostics", "Show native diagnostics snapshot")
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:clipboard-pulse-outline"

    @property
    def extra_state_attributes(self):
        return {
            "panel_path": panel_setup_path(self.coordinator.entry),
            "diagnostic_summary": self.coordinator.data.diagnostic_summary,
            "health_summary": self.coordinator.data.health_summary,
        }

    async def async_press(self) -> None:
        snapshot = build_native_support_snapshot(self.coordinator)
        message = (
            "Native Zero Net Export diagnostics snapshot\n\n"
            "This is intended for the Home Assistant device page, Scripts, and button.press automations when the custom panel route is unavailable.\n\n"
            f"Sidebar setup path: {panel_setup_path(self.coordinator.entry)}\n\n"
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
            "panel_path": panel_setup_path(self.coordinator.entry),
            "diagnostic_summary": self.coordinator.data.diagnostic_summary,
            "source_mismatch": self.coordinator.data.source_mismatch,
            "stale_data": self.coordinator.data.stale_data,
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
                f"Panel path: {panel_setup_path(self.coordinator.entry)}",
                f"Readiness phase: {readiness.get('phase') or 'unknown'}",
                f"Summary: {readiness.get('summary') or self.coordinator.data.health_summary}",
                f"Next step: {readiness.get('next_step') or self.coordinator.data.recommendation}",
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
        return self.coordinator.data.device_details[self._device_key]

    async def async_press(self) -> None:
        await self.coordinator.async_reset_device_overrides(self._device_key)
