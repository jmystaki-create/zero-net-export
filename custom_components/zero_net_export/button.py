"""Buttons for Zero Net Export."""
from __future__ import annotations

from homeassistant.components import persistent_notification
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .candidate_utils import discover_candidate_devices
from .const import DOMAIN
from .entity import ZeroNetExportEntity
from .native_support import (
    DEVICES_CONFIGURE_PATH,
    DEVICES_SECTION_LABEL,
    POLICY_CONFIGURE_PATH,
    POLICY_SECTION_LABEL,
    PRIMARY_CONFIGURE_PATH,
    SOURCES_CONFIGURE_PATH,
    SOURCES_SECTION_LABEL,
    SUPPORT_CONFIGURE_PATH,
    SUPPORT_SECTION_LABEL,
    build_native_command_center_summary,
    build_native_operator_readiness,
    build_native_support_center,
    build_native_support_snapshot,
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ZeroNetExportResetControllerOverridesButton(coordinator),
        ZeroNetExportShowNativeCommandCenterButton(coordinator),
        ZeroNetExportShowFleetConsoleButton(coordinator),
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


def _fleet_console_notification_id(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_fleet_console"


def _command_center_notification_id(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_command_center"


class ZeroNetExportResetControllerOverridesButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "reset_controller_overrides", "Reset controller overrides")

    @property
    def extra_state_attributes(self):
        return self._validation_details

    async def async_press(self) -> None:
        await self.coordinator.async_reset_controller_overrides()


class ZeroNetExportShowNativeCommandCenterButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "show_native_command_center", "Show command center guide")
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:map-marker-path"

    @property
    def extra_state_attributes(self):
        command_center = build_native_command_center_summary(self.coordinator)
        return {
            "configure_path": PRIMARY_CONFIGURE_PATH,
            "recommended_section": command_center.get("recommended_section"),
            "recommended_path": command_center.get("recommended_path"),
            "next_step": command_center.get("next_action_summary"),
            "install_status": command_center.get("install_status"),
            "install_consistency": command_center.get("install_consistency"),
            "source_status": command_center.get("source_status"),
            "source_attention_roles": command_center.get("source_attention_roles"),
            "source_mapping_summary": command_center.get("source_mapping_summary"),
            "device_status": command_center.get("device_status"),
            "device_next_step": command_center.get("device_next_step"),
            "policy_status": command_center.get("policy_status"),
            "policy_readiness": command_center.get("policy_readiness"),
            "support_status": command_center.get("support_status"),
        }

    async def async_press(self) -> None:
        command_center = build_native_command_center_summary(self.coordinator)
        message = "\n".join(
            [
                "Zero Net Export native command center guide",
                "",
                f"Primary path: {PRIMARY_CONFIGURE_PATH}",
                f"Recommended section right now: {command_center.get('recommended_section')}",
                f"Recommended path right now: {command_center.get('recommended_path')}",
                f"What to do next: {command_center.get('next_action_summary')}",
                f"Installed package: {command_center.get('install_status')}",
                f"Install consistency: {command_center.get('install_consistency')}",
                "",
                "Current status",
                f"- {SOURCES_SECTION_LABEL}: {command_center.get('source_status')}",
                f"- Current mapped roles: {command_center.get('source_mapping_summary')}",
                f"- Affected mapped roles: {command_center.get('source_attention_roles')}",
                f"- {DEVICES_SECTION_LABEL}: {command_center.get('device_status')}",
                f"- Managed-device next step: {command_center.get('device_next_step')}",
                f"- {POLICY_SECTION_LABEL}: {command_center.get('policy_status')}",
                f"- {POLICY_SECTION_LABEL} readiness: {command_center.get('policy_readiness')}",
                f"- {SUPPORT_SECTION_LABEL}: {command_center.get('support_status')}",
                "",
                "Where each native path lives",
                f"- {SOURCES_SECTION_LABEL}: {command_center.get('sources_path')}",
                f"- {DEVICES_SECTION_LABEL}: {command_center.get('devices_path')}",
                f"- {POLICY_SECTION_LABEL}: {command_center.get('policy_path')}",
                f"- {SUPPORT_SECTION_LABEL}: {command_center.get('support_path')}",
            ]
        )
        persistent_notification.async_create(
            self.hass,
            message,
            title=f"{self.coordinator.entry.title}: command center guide",
            notification_id=_command_center_notification_id(self.coordinator.entry.entry_id),
        )


class ZeroNetExportShowFleetConsoleButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "show_fleet_console", "Show fleet console")
        self._attr_icon = "mdi:format-list-group"

    @property
    def extra_state_attributes(self):
        state = self._state
        managed = list((state.device_details or {}).values()) if state is not None else []
        managed_ids = {str(detail.get('entity_id')) for detail in managed if detail.get('entity_id')}
        candidates = discover_candidate_devices(self.hass.states.async_all(), managed_ids)
        return {
            'configure_path': DEVICES_CONFIGURE_PATH,
            'managed_count': len(managed),
            'candidate_count': len(candidates),
            'candidate_devices': candidates[:12],
            'top_candidate': candidates[0] if candidates else None,
            'promotion_handoff': f'Open {DEVICES_CONFIGURE_PATH}, choose Add fixed/variable, then pick this candidate in the candidate-pick step.' if candidates else None,
        }

    async def async_press(self) -> None:
        state = self._state
        managed = list((state.device_details or {}).values()) if state is not None else []
        managed_ids = {str(detail.get('entity_id')) for detail in managed if detail.get('entity_id')}
        candidates = [
            (item['name'], item['entity_id'], item['domain'], item['state'])
            for item in discover_candidate_devices(self.hass.states.async_all(), managed_ids)
        ]
        lines = [
            'Zero Net Export native fleet console',
            '',
            f'Primary path: {DEVICES_CONFIGURE_PATH}',
            '',
            f'{DEVICES_SECTION_LABEL}: {len(managed)}',
        ]
        if managed:
            lines.extend(
                f"- {detail.get('name')}: {detail.get('status')} | enabled={detail.get('effective_enabled')} | entity={detail.get('entity_id')}"
                for detail in managed[:12]
            )
        else:
            lines.append('- No managed devices configured yet')
        lines.extend(['', f'Unmanaged candidate devices: {len(candidates)}'])
        if candidates:
            lines.extend(f'- {name} ({entity_id}, {domain}, state {value})' for name, entity_id, domain, value in candidates[:12])
            top_name, top_entity_id, top_domain, top_value = candidates[0]
            top_add_label = 'fixed load device' if top_domain in {'switch', 'input_boolean', 'light'} else 'variable load device'
            lines.extend([
                '',
                f'Top candidate: {top_name} ({top_entity_id}, {top_domain}, state {top_value})',
                'Next step:',
                f'- Open {DEVICES_CONFIGURE_PATH}.',
                f'- Choose Add {top_add_label}.',
                f'- In Pick unmanaged candidate, select {top_entity_id}.',
            ])
        else:
            lines.extend([
                '- No unmanaged candidate devices discovered right now',
                '',
                'Next step:',
                f'- Open {POLICY_CONFIGURE_PATH} to tune controller behaviour, or {SOURCES_CONFIGURE_PATH} if runtime health still needs work.',
            ])
        persistent_notification.async_create(
            self.hass,
            '\n'.join(lines),
            title=f"{self.coordinator.entry.title}: fleet console",
            notification_id=_fleet_console_notification_id(self.coordinator.entry.entry_id),
        )


class ZeroNetExportShowNativeSupportCenterButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "show_native_support_center", "Show support center")
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:lifebuoy"

    @property
    def extra_state_attributes(self):
        readiness = build_native_operator_readiness(self.coordinator)
        command_center = build_native_command_center_summary(self.coordinator)
        return {
            "configure_path": SUPPORT_CONFIGURE_PATH,
            "phase": readiness.get("phase"),
            "next_step": command_center.get("next_action_summary") or readiness.get("next_step"),
            "recommended_section": command_center.get("recommended_section"),
            "recommended_path": command_center.get("recommended_path"),
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
        command_center = build_native_command_center_summary(self.coordinator)
        return {
            "configure_path": SUPPORT_CONFIGURE_PATH,
            "recommended_section": command_center.get("recommended_section"),
            "recommended_path": command_center.get("recommended_path"),
            "next_step": command_center.get("next_action_summary"),
            "diagnostic_summary": self._state.diagnostic_summary if self._state else None,
            "health_summary": self._state.health_summary if self._state else None,
        }

    async def async_press(self) -> None:
        snapshot = build_native_support_snapshot(self.coordinator)
        message = (
            "Native Zero Net Export diagnostics snapshot\n\n"
            "This is intended for the Home Assistant device page, Scripts, and button.press automations so diagnostics stay reachable from native Home Assistant surfaces.\n\n"
            f"Primary setup path: {PRIMARY_CONFIGURE_PATH}\n"
            f"Diagnostics path: {SUPPORT_CONFIGURE_PATH}\n\n"
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
        command_center = build_native_command_center_summary(self.coordinator)
        return {
            "configure_path": SUPPORT_CONFIGURE_PATH,
            "recommended_section": command_center.get("recommended_section"),
            "recommended_path": command_center.get("recommended_path"),
            "next_step": command_center.get("next_action_summary") or readiness.get("next_step"),
            "diagnostic_summary": self._state.diagnostic_summary if self._state else None,
            "source_mismatch": self._state.source_mismatch if self._state else None,
            "stale_data": self._state.stale_data if self._state else None,
            "checklist": readiness.get("checklist"),
        }

    async def async_press(self) -> None:
        readiness = build_native_operator_readiness(self.coordinator)
        command_center = build_native_command_center_summary(self.coordinator)
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
                f"Diagnostics path: {SUPPORT_CONFIGURE_PATH}",
                f"Recommended command-center section: {command_center.get('recommended_section')}",
                f"Recommended command-center path: {command_center.get('recommended_path')}",
                f"Readiness phase: {readiness.get('phase') or 'unknown'}",
                f"Summary: {readiness.get('summary') or (self._state.health_summary if self._state else None)}",
                f"Next step: {command_center.get('next_action_summary') or readiness.get('next_step') or (self._state.recommendation if self._state else None)}",
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
