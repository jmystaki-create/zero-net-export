"""Buttons for Zero Net Export."""
from __future__ import annotations

from homeassistant.components import persistent_notification
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .candidate_utils import (
    assess_candidate,
    build_candidate_overview_summary,
    build_candidate_preview,
    discover_candidate_devices,
)
from .const import DOMAIN
from .entity import ZeroNetExportEntity
from .native_support import (
    DETAILED_MANAGEMENT_PATH,
    DEVICES_CONFIGURE_PATH,
    DEVICES_SECTION_LABEL,
    POLICY_CONFIGURE_PATH,
    PRIMARY_CONFIGURE_PATH,
    SOURCES_CONFIGURE_PATH,
    SUPPORT_CONFIGURE_PATH,
    build_native_command_center_guide_text,
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
        ZeroNetExportShowManagedDeviceReviewButton(coordinator),
        ZeroNetExportShowNativeSupportCenterButton(coordinator),
        ZeroNetExportShowNativeDiagnosticsButton(coordinator),
        ZeroNetExportShowSetupChecklistButton(coordinator),
    ]
    state = coordinator.data
    if state is not None:
        entities.extend(
            ZeroNetExportShowManagedDeviceDetailButton(coordinator, device_key, details["name"])
            for device_key, details in state.device_details.items()
        )
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


def _managed_device_review_notification_id(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_managed_device_review"


def _managed_device_detail_notification_id(entry_id: str, device_key: str) -> str:
    return f"{DOMAIN}_{entry_id}_managed_device_{device_key}_review"


def _has_active_plan(detail: dict) -> bool:
    return str(detail.get("planned_action") or "") not in {"", "hold"}


def _candidate_usefulness_summary(candidate: dict) -> str:
    fit = assess_candidate(candidate)
    confidence = str(fit.get("confidence") or "medium")
    warnings = [str(item).strip() for item in (fit.get("warnings") or []) if str(item).strip()]
    usefulness = "review first" if confidence == "medium" and warnings else {
        "high": "likely useful",
        "medium": "possible fit",
        "low": "review carefully",
    }.get(confidence, confidence)
    summary = str(fit.get("summary") or "Looks like a plausible controllable candidate, but review before promotion.")
    return f"{usefulness}: {summary}"


def _device_runtime_sort_key(detail: dict) -> tuple[int, int, int, str]:
    effective_enabled = bool(detail.get("effective_enabled", detail.get("enabled", True)))
    usable = detail.get("usable") is True
    blocked = detail.get("usable") is False
    planned = _has_active_plan(detail)
    return (
        0 if blocked else 1,
        0 if planned else 1,
        0 if effective_enabled and usable else 1,
        str(detail.get("name") or detail.get("entity_id") or ""),
    )


def _format_device_review_line(detail: dict) -> str:
    runtime_bits = [
        str(detail.get("kind") or "unknown"),
        str(detail.get("status") or "status unknown"),
        "usable" if detail.get("usable") else "not usable",
        "enabled" if detail.get("effective_enabled", detail.get("enabled", True)) else "disabled",
    ]
    priority = detail.get("priority")
    if priority is not None:
        runtime_bits.append(f"priority {int(priority)}")
    operator_priority_override = detail.get("operator_priority_override")
    if operator_priority_override is not None:
        runtime_bits.append(f"priority override {int(operator_priority_override)}")
    operator_enabled_override = detail.get("operator_enabled_override")
    if operator_enabled_override is not None:
        runtime_bits.append(f"enabled override {'on' if operator_enabled_override else 'off'}")
    runtime_bits.append(f"power {_format_power(detail.get('current_power_w'))}")
    if detail.get("kind") == "variable" and detail.get("current_target_power_w") is not None:
        runtime_bits.append(f"target {_format_power(detail.get('current_target_power_w'))}")
    runtime_bits.append(f"guard {detail.get('guard_status') or 'unknown'}")
    runtime_bits.append(f"action {detail.get('planned_action') or 'hold'}")
    last_action_status = str(detail.get("last_action_status") or "").strip()
    if last_action_status and last_action_status not in {"ok", "applied", "success"}:
        runtime_bits.append(f"last {last_action_status}")
    device_label = str(detail.get("name") or detail.get("entity_id") or "managed device")
    return f"- {device_label}: {' | '.join(runtime_bits)}"


def _first_matching_device_name(device_details: list[dict], *, predicate) -> str:
    for detail in device_details:
        if predicate(detail):
            return str(detail.get("name") or detail.get("entity_id") or "").strip()
    return ""


def _managed_snapshot_summary(device_details: list[dict], *, include_planned_count: bool = False) -> str:
    managed_count = len(device_details)
    enabled_count = sum(
        1 for detail in device_details if detail.get("effective_enabled", detail.get("enabled", True))
    )
    usable_count = sum(1 for detail in device_details if detail.get("usable") is True)
    planned_count = sum(1 for detail in device_details if _has_active_plan(detail))
    first_blocked_name = _first_matching_device_name(
        device_details,
        predicate=lambda detail: detail.get("usable") is False,
    )
    first_planned_name = _first_matching_device_name(
        device_details,
        predicate=_has_active_plan,
    )
    parts = [f"{managed_count} managed", f"{enabled_count} enabled", f"{usable_count} usable"]
    if first_blocked_name:
        parts.append(f"blocked {first_blocked_name}")
    if include_planned_count:
        parts.append(f"{planned_count} planned action(s)")
    if first_planned_name:
        parts.append(f"plan {first_planned_name}")
    return " | ".join(parts)


def _unmanaged_snapshot_summary(candidates: list[dict]) -> str:
    overview = build_candidate_overview_summary(candidates, include_top_review_hint=False)
    if not candidates:
        return overview

    top_preview = build_candidate_preview(candidates[0], include_entity_id=False, include_state=False)
    _, separator, preview_tail = top_preview.partition(" | ")
    if separator and preview_tail:
        return f"{overview} | {preview_tail}"
    return overview


def _format_power(value: object) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{int(round(float(value)))} W"
    except (TypeError, ValueError):
        return str(value)


def _format_enabled_override(value: object) -> str:
    if value is None:
        return "none"
    return "forcing on" if bool(value) else "forcing off"


def _format_priority_override(value: object) -> str:
    if value is None:
        return "none"
    try:
        return f"forcing {int(value)}"
    except (TypeError, ValueError):
        return f"forcing {value}"


def _managed_devices_blocker_first_lines(command_center: dict) -> list[str]:
    recommended_section = str(command_center.get("recommended_section") or "").strip()
    recommended_path = str(command_center.get("recommended_path") or "").strip()
    recommended_reason = str(command_center.get("recommended_reason") or "").strip()
    next_step = str(command_center.get("device_next_step") or command_center.get("next_action_summary") or "").strip()

    if not recommended_section or recommended_section == DEVICES_SECTION_LABEL:
        return []

    lines = ["Before fleet work:"]
    if recommended_path:
        lines.append(f"- Open {recommended_path} first.")
    if recommended_reason:
        lines.append(f"- Why: {recommended_reason}")
    if next_step:
        lines.append(f"- After repair: {next_step}")
    return lines


def _managed_devices_workspace_handoff(command_center: dict, top_candidate: dict | None) -> list[str]:
    recommended_section = str(command_center.get("recommended_section") or "").strip()
    recommended_path = str(command_center.get("recommended_path") or "").strip()
    recommended_reason = str(command_center.get("recommended_reason") or "").strip()
    next_step = str(command_center.get("device_next_step") or command_center.get("next_action_summary") or "").strip()

    if recommended_section and recommended_section != DEVICES_SECTION_LABEL:
        lines = ["Return after blocker repair:"]
        if recommended_path:
            lines.append(f"- Open {recommended_path} first.")
        if recommended_reason:
            lines.append(f"- Why: {recommended_reason}")
        if next_step:
            lines.append(f"- Next fleet step after repair: {next_step}")
        lines.append(f"- Then reopen {DEVICES_CONFIGURE_PATH} for Managed Devices.")
        lines.append(f"- Use {DETAILED_MANAGEMENT_PATH} only for deeper per-device review after the main fleet step is clear.")
        return lines

    lines = ["Promotion handoff:"]
    if top_candidate:
        top_add_label = "fixed load device" if top_candidate["kind"] == "fixed" else "variable load device"
        lines.extend(
            [
                f"- Open {DEVICES_CONFIGURE_PATH} as the primary Managed Devices workspace.",
                f"- Choose Add {top_add_label}.",
                f"- In Pick unmanaged candidate, select {build_candidate_preview(top_candidate, include_entity_id=False, include_state=False)}.",
                "- Review fit and warnings, then save it into Managed Devices.",
                f"- Use {DETAILED_MANAGEMENT_PATH} afterward only if you need deeper per-device review.",
            ]
        )
    else:
        lines.extend(
            [
                f"- Open {POLICY_CONFIGURE_PATH} to tune controller behaviour, or {SOURCES_CONFIGURE_PATH} if runtime health still needs work.",
            ]
        )
    return lines


def _build_managed_device_detail_lines(
    detail: dict,
    *,
    command_center: dict,
    managed_snapshot: str,
    unmanaged_snapshot: str,
    top_candidate: dict | None,
) -> list[str]:
    entity_id = str(detail.get("entity_id") or "unknown entity")
    device_label = str(detail.get("name") or entity_id)
    blocker_first_lines = _managed_devices_blocker_first_lines(command_center)
    kind = str(detail.get("kind") or "unknown")
    requested_target_power = detail.get("planned_requested_power_w")
    if requested_target_power is None:
        requested_target_power = detail.get("current_target_power_w")

    control_profile_lines = [
        f"- Enabled: {'yes' if detail.get('effective_enabled', detail.get('enabled', True)) else 'no'}",
        f"- Usable: {'yes' if detail.get('usable') else 'no'}",
        f"- Priority: {detail.get('priority') if detail.get('priority') is not None else 'n/a'}",
        f"- Current power: {_format_power(detail.get('current_power_w'))}",
    ]
    if detail.get("planned_power_delta_w") is not None:
        control_profile_lines.append(f"- Planned power delta: {_format_power(detail.get('planned_power_delta_w'))}")
    if requested_target_power is not None:
        control_profile_lines.append(f"- Requested target power: {_format_power(requested_target_power)}")
    if detail.get("nominal_power_w") is not None:
        control_profile_lines.append(f"- Nominal power: {_format_power(detail.get('nominal_power_w'))}")
    if kind == "variable":
        min_power = detail.get("min_power_w")
        max_power = detail.get("max_power_w")
        if min_power is not None or max_power is not None:
            control_profile_lines.append(f"- Variable range: {_format_power(min_power)} to {_format_power(max_power)}")
        if detail.get("step_w") is not None:
            control_profile_lines.append(f"- Step size: {_format_power(detail.get('step_w'))}")
    control_profile_lines.extend(
        [
            f"- Cooldown: {int(detail.get('cooldown_seconds') or 0)} s",
            f"- Min on time: {int(detail.get('min_on_seconds') or 0)} s",
            f"- Min off time: {int(detail.get('min_off_seconds') or 0)} s",
            f"- Max active time: {int(detail.get('max_active_seconds') or 0)} s",
        ]
    )

    lines = [
        "Zero Net Export managed-device detail review",
        "",
        f"Managed Devices path: {DEVICES_CONFIGURE_PATH}",
        f"Detailed device-view path: {DETAILED_MANAGEMENT_PATH}",
        f"Recommended next step: {command_center.get('device_next_step') or command_center.get('next_action_summary') or 'Review the current fleet state.'}",
        *(["", *blocker_first_lines] if blocker_first_lines else []),
        "",
        "Managed devices workspace context:",
        f"- Managed snapshot: {managed_snapshot}",
        f"- Unmanaged snapshot: {unmanaged_snapshot}",
        (
            f"- Top unmanaged candidate right now: {build_candidate_preview(top_candidate, include_entity_id=False)}"
            if top_candidate
            else "- Top unmanaged candidate right now: none"
        ),
        "",
        f"Device: {device_label}",
        f"Kind: {kind}",
        f"Runtime status: {detail.get('status') or 'status unknown'}",
        f"Guard state: {detail.get('guard_status') or 'unknown'}",
        f"Planned action: {detail.get('planned_action') or 'hold'}",
        f"Planned action reason: {detail.get('planned_action_reason') or 'No planned action reason recorded.'}",
        f"Reason: {detail.get('reason') or 'No runtime reason recorded.'}",
        "",
        "Control profile:",
        *control_profile_lines,
        "",
        "Operator overrides:",
        f"- Enabled override: {_format_enabled_override(detail.get('operator_enabled_override'))}",
        f"- Priority override: {_format_priority_override(detail.get('operator_priority_override'))}",
        "",
        "Latest execution:",
        f"- Last action status: {detail.get('last_action_status') or 'No recent action'}",
        f"- Last action result: {detail.get('last_action_result_message') or 'No recent action result recorded.'}",
        f"- Last requested power: {_format_power(detail.get('last_requested_power_w'))}",
        f"- Last applied power: {_format_power(detail.get('last_applied_power_w'))}",
        f"- Success count: {int(detail.get('successful_action_count') or 0)}",
        f"- Failure count: {int(detail.get('failed_action_count') or 0)}",
        "",
        "Next native actions:",
        f"- Return to {DEVICES_CONFIGURE_PATH} as the primary Managed Devices workspace for edits, enablement, promotion, or removal.",
        "- Use this device's sensors on the Zero Net Export device page to watch current power, plan, guard, and last-action detail.",
        f"- Use the reset overrides button for this device if operator overrides should be cleared.",
    ]
    return lines


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
        self._attr_icon = "mdi:map-marker-path"

    @property
    def extra_state_attributes(self):
        command_center = build_native_command_center_summary(self.coordinator)
        return {
            "configure_path": PRIMARY_CONFIGURE_PATH,
            "recommended_section": command_center.get("recommended_section"),
            "recommended_path": command_center.get("recommended_path"),
            "recommended_reason": command_center.get("recommended_reason"),
            "next_step": command_center.get("next_action_summary"),
            "install_status": command_center.get("install_status"),
            "install_consistency": command_center.get("install_consistency"),
            "source_status": command_center.get("source_status"),
            "source_attention_roles": command_center.get("source_attention_roles"),
            "source_mapping_summary": command_center.get("source_mapping_summary"),
            "unavailable_sources": command_center.get("unavailable_sources"),
            "stale_sources": command_center.get("stale_sources"),
            "device_status": command_center.get("device_status"),
            "device_next_step": command_center.get("device_next_step"),
            "policy_status": command_center.get("policy_status"),
            "policy_readiness": command_center.get("policy_readiness"),
            "support_status": command_center.get("support_status"),
            "detailed_management_summary": command_center.get("detailed_management_summary"),
        }

    async def async_press(self) -> None:
        command_center = build_native_command_center_summary(self.coordinator)
        persistent_notification.async_create(
            self.hass,
            build_native_command_center_guide_text(command_center),
            title=f"{self.coordinator.entry.title}: command center guide",
            notification_id=_command_center_notification_id(self.coordinator.entry.entry_id),
        )


class ZeroNetExportShowFleetConsoleButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "show_fleet_console", "Review managed devices workspace")
        self._attr_icon = "mdi:format-list-group"

    @property
    def extra_state_attributes(self):
        state = self._state
        managed = list((state.device_details or {}).values()) if state is not None else []
        ordered = sorted(managed, key=_device_runtime_sort_key)
        managed_ids = {str(detail.get('entity_id')) for detail in managed if detail.get('entity_id')}
        candidates = discover_candidate_devices(self.hass.states.async_all(), managed_ids)
        top_candidate = candidates[0] if candidates else None
        top_candidate_fit = assess_candidate(top_candidate) if top_candidate else None
        command_center = build_native_command_center_summary(self.coordinator)
        return {
            'configure_path': DEVICES_CONFIGURE_PATH,
            'detailed_management_path': DETAILED_MANAGEMENT_PATH,
            'recommended_section': command_center.get('recommended_section'),
            'recommended_path': command_center.get('recommended_path'),
            'recommended_reason': command_center.get('recommended_reason'),
            'blocker_first': "\n".join(_managed_devices_blocker_first_lines(command_center)),
            'managed_count': len(managed),
            'enabled_count': sum(
                1 for detail in managed if detail.get('effective_enabled', detail.get('enabled', True))
            ),
            'usable_count': sum(1 for detail in managed if detail.get('usable') is True),
            'first_blocked_device': _first_matching_device_name(
                ordered,
                predicate=lambda detail: detail.get('usable') is False,
            ),
            'first_planned_device': _first_matching_device_name(
                ordered,
                predicate=_has_active_plan,
            ),
            'managed_snapshot': _managed_snapshot_summary(ordered),
            'unmanaged_snapshot': _unmanaged_snapshot_summary(candidates),
            'candidate_count': len(candidates),
            'candidate_devices': candidates[:12],
            'top_candidate': top_candidate,
            'top_candidate_fit': top_candidate_fit,
            'next_step': command_center.get('device_next_step') or command_center.get('next_action_summary'),
            'devices': ordered[:12],
            'promotion_handoff': "\n".join(_managed_devices_workspace_handoff(command_center, top_candidate)),
        }

    async def async_press(self) -> None:
        state = self._state
        managed = list((state.device_details or {}).values()) if state is not None else []
        ordered = sorted(managed, key=_device_runtime_sort_key)
        managed_ids = {str(detail.get('entity_id')) for detail in managed if detail.get('entity_id')}
        candidates = discover_candidate_devices(self.hass.states.async_all(), managed_ids)
        top_candidate = candidates[0] if candidates else None
        top_candidate_fit = assess_candidate(top_candidate) if top_candidate else None
        command_center = build_native_command_center_summary(self.coordinator)
        blocker_first_lines = _managed_devices_blocker_first_lines(command_center)
        lines = [
            'Zero Net Export managed devices workspace',
            '',
            f'Workspace path: {DEVICES_CONFIGURE_PATH}',
            f'Detailed review path: {DETAILED_MANAGEMENT_PATH}',
            f"Recommended next step: {command_center.get('device_next_step') or command_center.get('next_action_summary') or 'Review the current fleet state.'}",
            *(['', *blocker_first_lines] if blocker_first_lines else []),
            '',
            'Managed devices (top section):',
            f"- Snapshot: {_managed_snapshot_summary(ordered)}",
            *([_format_device_review_line(detail) for detail in ordered[:12]] or ['- No managed devices configured yet.']),
            '',
            'Unmanaged candidates (bottom section):',
            f"- Snapshot: {_unmanaged_snapshot_summary(candidates)}",
            (
                f"- Top candidate usefulness: {_candidate_usefulness_summary(top_candidate)}"
                if top_candidate_fit
                else '- Top candidate usefulness: No unmanaged candidate guidance available right now.'
            ),
            (
                '- Top candidate warnings: '
                + (
                    '; '.join(top_candidate_fit.get('warnings') or [])
                    if top_candidate_fit and top_candidate_fit.get('warnings')
                    else 'No immediate warnings.'
                )
            ),
            *(
                [
                    f"- {build_candidate_preview(item, include_entity_id=False, include_state=True)}"
                    for item in candidates[:6]
                ]
                or ['- No unmanaged candidate devices discovered right now.']
            ),
            '',
            *_managed_devices_workspace_handoff(command_center, top_candidate),
        ]
        persistent_notification.async_create(
            self.hass,
            '\n'.join(lines),
            title=f"{self.coordinator.entry.title}: managed devices workspace",
            notification_id=_fleet_console_notification_id(self.coordinator.entry.entry_id),
        )


class ZeroNetExportShowManagedDeviceReviewButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "show_managed_device_review", "Review managed devices")
        self._attr_icon = "mdi:clipboard-list-outline"

    def _unmanaged_candidates(self) -> list[dict[str, str]]:
        if self.hass is None:
            return []
        state = self._state
        managed_ids = {
            str(detail.get("entity_id"))
            for detail in (getattr(state, "device_details", None) or {}).values()
            if detail.get("entity_id")
        }
        return discover_candidate_devices(self.hass.states.async_all(), managed_ids)

    @property
    def extra_state_attributes(self):
        state = self._state
        device_details = list((state.device_details or {}).values()) if state is not None else []
        ordered = sorted(device_details, key=_device_runtime_sort_key)
        candidates = self._unmanaged_candidates()
        top_candidate = candidates[0] if candidates else None
        command_center = build_native_command_center_summary(self.coordinator)
        return {
            "configure_path": DEVICES_CONFIGURE_PATH,
            "detailed_management_path": DETAILED_MANAGEMENT_PATH,
            "recommended_section": command_center.get("recommended_section"),
            "recommended_path": command_center.get("recommended_path"),
            "recommended_reason": command_center.get("recommended_reason"),
            "blocker_first": "\n".join(_managed_devices_blocker_first_lines(command_center)),
            "managed_count": len(device_details),
            "enabled_count": sum(
                1 for detail in device_details if detail.get("effective_enabled", detail.get("enabled", True))
            ),
            "usable_count": sum(1 for detail in device_details if detail.get("usable") is True),
            "planned_action_count": sum(1 for detail in device_details if _has_active_plan(detail)),
            "blocked_count": sum(1 for detail in device_details if detail.get("usable") is False),
            "first_blocked_device": _first_matching_device_name(
                ordered,
                predicate=lambda detail: detail.get("usable") is False,
            ),
            "first_planned_device": _first_matching_device_name(
                ordered,
                predicate=_has_active_plan,
            ),
            "managed_snapshot": _managed_snapshot_summary(ordered, include_planned_count=True),
            "unmanaged_snapshot": _unmanaged_snapshot_summary(candidates),
            "unmanaged_candidate_count": len(candidates),
            "top_unmanaged_candidate": top_candidate,
            "top_candidate_fit": assess_candidate(top_candidate) if top_candidate else None,
            "candidate_devices": candidates[:12],
            "next_step": command_center.get("device_next_step") or command_center.get("next_action_summary"),
            "devices": ordered[:12],
            "promotion_handoff": "\n".join(_managed_devices_workspace_handoff(command_center, top_candidate)),
        }

    async def async_press(self) -> None:
        state = self._state
        device_details = list((state.device_details or {}).values()) if state is not None else []
        ordered = sorted(device_details, key=_device_runtime_sort_key)
        candidates = self._unmanaged_candidates()
        top_candidate = candidates[0] if candidates else None
        top_candidate_fit = assess_candidate(top_candidate) if top_candidate else None
        command_center = build_native_command_center_summary(self.coordinator)
        blocker_first_lines = _managed_devices_blocker_first_lines(command_center)
        lines = [
            "Zero Net Export managed devices review",
            "",
            f"Managed Devices path: {DEVICES_CONFIGURE_PATH}",
            f"Detailed device-view path: {DETAILED_MANAGEMENT_PATH}",
            f"Recommended next step: {command_center.get('device_next_step') or command_center.get('next_action_summary') or 'Review the current fleet state.'}",
            *(["", *blocker_first_lines] if blocker_first_lines else []),
            "",
            "Managed devices (top section):",
            f"- Snapshot: {_managed_snapshot_summary(ordered, include_planned_count=True)}",
            f"Unmanaged candidates (bottom section): {_unmanaged_snapshot_summary(candidates)}",
            (
                f"Top candidate usefulness: {_candidate_usefulness_summary(top_candidate)}"
                if top_candidate_fit
                else "Top candidate usefulness: No unmanaged candidate guidance available right now."
            ),
            (
                "Top candidate warnings: "
                + (
                    "; ".join(top_candidate_fit.get("warnings") or [])
                    if top_candidate_fit and top_candidate_fit.get("warnings")
                    else "No immediate warnings."
                )
            ),
            "",
            "Managed devices right now:",
            *([_format_device_review_line(detail) for detail in ordered[:20]] or ["- No managed devices configured yet."]),
            "",
            "Top unmanaged candidates:",
            *(
                [
                    f"- {build_candidate_preview(item, include_entity_id=False, include_state=True)}"
                    for item in candidates[:6]
                ]
                or ["- No unmanaged candidate devices discovered right now."]
            ),
            "",
            *_managed_devices_workspace_handoff(command_center, top_candidate),
            "",
            "Use each managed-device review button on the Zero Net Export device page for a deeper per-device snapshot, plus the paired status sensors and reset-override buttons.",
        ]
        persistent_notification.async_create(
            self.hass,
            "\n".join(lines),
            title=f"{self.coordinator.entry.title}: managed-device review",
            notification_id=_managed_device_review_notification_id(self.coordinator.entry.entry_id),
        )


class ZeroNetExportShowManagedDeviceDetailButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_review", f"Review {device_name}")
        self._device_key = device_key
        self._attr_icon = "mdi:text-box-search-outline"

    def _detail(self) -> dict:
        state = self._state
        if state is None:
            return {}
        return dict((state.device_details or {}).get(self._device_key, {}) or {})

    @property
    def extra_state_attributes(self):
        detail = self._detail()
        state = self._state
        managed = list((state.device_details or {}).values()) if state is not None else []
        ordered = sorted(managed, key=_device_runtime_sort_key)
        managed_ids = {str(item.get("entity_id")) for item in managed if item.get("entity_id")}
        candidates = discover_candidate_devices(self.hass.states.async_all(), managed_ids) if self.hass else []
        top_candidate = candidates[0] if candidates else None
        command_center = build_native_command_center_summary(self.coordinator)
        return {
            "configure_path": DEVICES_CONFIGURE_PATH,
            "detailed_management_path": DETAILED_MANAGEMENT_PATH,
            "recommended_section": command_center.get("recommended_section"),
            "recommended_path": command_center.get("recommended_path"),
            "recommended_reason": command_center.get("recommended_reason"),
            "blocker_first": "\n".join(_managed_devices_blocker_first_lines(command_center)),
            "managed_snapshot": _managed_snapshot_summary(ordered, include_planned_count=True),
            "unmanaged_snapshot": _unmanaged_snapshot_summary(candidates),
            "top_unmanaged_candidate": top_candidate,
            **detail,
        }

    async def async_press(self) -> None:
        detail = self._detail()
        state = self._state
        managed = list((state.device_details or {}).values()) if state is not None else []
        ordered = sorted(managed, key=_device_runtime_sort_key)
        managed_ids = {str(item.get("entity_id")) for item in managed if item.get("entity_id")}
        candidates = discover_candidate_devices(self.hass.states.async_all(), managed_ids) if self.hass else []
        top_candidate = candidates[0] if candidates else None
        command_center = build_native_command_center_summary(self.coordinator)
        persistent_notification.async_create(
            self.hass,
            "\n".join(
                _build_managed_device_detail_lines(
                    detail,
                    command_center=command_center,
                    managed_snapshot=_managed_snapshot_summary(ordered, include_planned_count=True),
                    unmanaged_snapshot=_unmanaged_snapshot_summary(candidates),
                    top_candidate=top_candidate,
                )
            ),
            title=f"{self.coordinator.entry.title}: review {detail.get('name') or self._device_key}",
            notification_id=_managed_device_detail_notification_id(self.coordinator.entry.entry_id, self._device_key),
        )


class ZeroNetExportShowNativeSupportCenterButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "show_native_support_center", "Review diagnostics")
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
            title=f"{self.coordinator.entry.title}: diagnostics guide",
            notification_id=_support_notification_id(self.coordinator.entry.entry_id),
        )


class ZeroNetExportShowNativeDiagnosticsButton(ZeroNetExportEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "show_native_diagnostics", "Review diagnostics snapshot")
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
            title=f"{self.coordinator.entry.title}: diagnostics snapshot",
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
