"""Sensors for Zero Net Export."""
from __future__ import annotations

from collections.abc import Mapping

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower, UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from .candidate_utils import (
    assess_candidate,
    build_candidate_compact_preview,
    build_candidate_fit_summary,
    build_candidate_name_summary,
    build_candidate_overview_summary,
    build_candidate_preview,
    build_candidate_review_hint,
    candidate_needs_review,
    candidate_review_kind_counts,
    discover_candidate_devices,
    first_review_candidate,
)
from .const import DEVICE_CANDIDATE_DOMAINS, DOMAIN, INTEGRATION_VERSION
from .entity import (
    ZeroNetExportEntity,
    attach_managed_load_device,
    integration_page_managed_load_details,
    managed_load_detail,
    managed_load_detail_mapping,
    managed_load_details_mapping,
    managed_load_device_info,
    managed_load_settings_action_name,
    remove_integration_page_child_device_registry,
    remove_unmanaged_candidate_child_devices_for_entry,
    sync_integration_page_child_device_registry,
    legacy_unmanaged_candidate_device_info,
    unmanaged_candidate_cleanup_device_info,
)
from .native_support import (
    DEVICES_CONFIGURE_PATH,
    POLICY_CONFIGURE_PATH,
    SOURCES_CONFIGURE_PATH,
    build_native_command_center_summary,
    build_native_operator_readiness,
    build_source_attention_details,
    build_source_attention_brief,
    build_source_attention_role_summary,
    build_source_attention_summary,
    format_fleet_activity_for_operator,
    summarize_validation_issue_messages,
)
from .release_info import build_release_info


SENSOR_DEFS = {
    "installed_version": "Installed version",
    "previous_installed_version": "Previous installed version",
    "release_summary": "Release summary",
    "changes_preview": "Changes preview",
    "update_summary": "Update summary",
    "status": "Status",
    "reason": "Reason",
    "recommendation": "Current native next action",
    "diagnostic_summary": "Diagnostic summary",
    "confidence": "Confidence",
    "stale_source_count": "Stale source count",
    "stale_source_summary": "Stale source summary",
    "health_status": "Health status",
    "health_summary": "Health summary",
    "actions_today": "Actions today",
    "successful_actions_today": "Successful actions today",
    "failed_actions_today": "Failed actions today",
    "energy_redirected_today_kwh": "Energy redirected today",
    "active_controlled_power_w": "Active controlled power",
    "battery_reserve_soc": "Battery reserve SOC",
    "solar_power_w": "Solar power",
    "grid_import_power_w": "Grid import power",
    "grid_export_power_w": "Grid export power",
    "home_load_power_w": "Home load power",
    "battery_soc": "Battery state of charge",
    "surplus_w": "Surplus",
    "last_reconciliation_error_w": "Last reconciliation error",
    "device_count": "Managed Devices count",
    "enabled_device_count": "Managed Devices enabled count",
    "usable_device_count": "Managed Devices usable count",
    "fixed_device_count": "Managed Devices fixed-load count",
    "variable_device_count": "Managed Devices variable-load count",
    "controllable_nominal_power_w": "Managed Devices controllable power",
    "usable_nominal_power_w": "Managed Devices usable power",
    "device_status_summary": "Managed Devices status summary",
    "control_status": "Control status",
    "control_summary": "Control summary",
    "control_reason": "Control reason",
    "control_guard_summary": "Control guard summary",
    "last_action_status": "Last action status",
    "last_action_summary": "Last action summary",
    "last_action_at": "Last action at",
    "last_successful_action_at": "Last successful action at",
    "last_failed_action_at": "Last failed action at",
    "last_action_device": "Last action device",
    "last_failed_action_device": "Last failed action device",
    "last_failed_action_message": "Last failed action message",
    "recent_action_summary": "Recent action summary",
    "recent_failure_summary": "Recent failure summary",
    "last_successful_action_summary": "Last successful action summary",
    "action_history_count": "Action history count",
    "successful_action_count": "Successful action count",
    "failed_action_count": "Failed action count",
    "total_successful_action_count": "Total successful action count",
    "total_failed_action_count": "Total failed action count",
    "export_error_w": "Export error",
    "planned_action_count": "Planned action count",
    "executable_action_count": "Executable action count",
    "blocked_planned_action_count": "Blocked planned action count",
    "planned_power_delta_w": "Planned power delta",
    "variable_planned_power_delta_w": "Variable planned power delta",
    "fixed_planned_power_delta_w": "Fixed planned power delta",
    "managed_devices_surface": "Managed Devices surface",
    "managed_fleet_overview": "Managed Devices overview",
    "managed_fleet_attention": "Managed Devices attention",
    "managed_fleet_ready": "Managed Devices ready next",
    "unmanaged_candidate_count": "Managed Devices unmanaged backlog count",
    "unmanaged_candidate_overview": "Managed Devices unmanaged backlog",
    "top_unmanaged_candidate": "Managed Devices surfaced unmanaged candidate",
    "top_candidate_fit": "Managed Devices surfaced candidate usefulness",
    "top_candidate_warnings": "Managed Devices surfaced candidate warnings",
    "candidate_shortlist": "Managed Devices candidate shortlist",
    "candidate_shortlist_fit": "Managed Devices candidate shortlist usefulness",
    "fleet_console_next_step": "Managed Devices next step",
    "mapped_source_blocker_summary": "Source blocker summary",
    "mapped_source_blocker_next_step": "Source blocker next step",
    "command_center_status": "Command center status",
    "command_center_recommended_path": "Command center focus path",
    "command_center_next_step": "Command center next step",
}

SOURCE_BLOCKER_ACTIVE_LABEL = "source blockers active"

SOURCE_LABELS = {
    "solar_power": "Solar power",
    "solar_energy": "Solar energy",
    "grid_import_power": "Grid import power",
    "grid_export_power": "Grid export power",
    "grid_import_energy": "Grid import energy",
    "grid_export_energy": "Grid export energy",
    "home_load_power": "Home load power",
    "battery_soc": "Battery state of charge",
    "battery_charge_power": "Battery charge power",
    "battery_discharge_power": "Battery discharge power",
}

TIMESTAMP_SENSOR_KEYS = {"last_action_at", "last_successful_action_at", "last_failed_action_at"}


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


FLEET_WORKSPACE_SENSOR_KEYS = {
    "managed_devices_surface",
    "managed_fleet_overview",
    "managed_fleet_attention",
    "managed_fleet_ready",
    "unmanaged_candidate_count",
    "unmanaged_candidate_overview",
    "top_unmanaged_candidate",
    "top_candidate_fit",
    "top_candidate_warnings",
    "candidate_shortlist",
    "candidate_shortlist_fit",
    "fleet_console_next_step",
}


def _count_label(count: int, singular: str, plural: str | None = None) -> str:
    noun = singular if count == 1 else (plural or f"{singular}s")
    return f"{count} {noun}"


def _unmanaged_count_label(count: int) -> str:
    return "no unmanaged candidates" if count <= 0 else f"{count} unmanaged backlog"


def _candidate_kind_backlog_mix_parts(
    *,
    fixed_candidate_count: int,
    variable_candidate_count: int,
    fixed_review_count: int,
    variable_review_count: int,
    fixed_ready_count: int,
    variable_ready_count: int,
) -> list[str]:
    parts: list[str] = []

    def _append(kind_label: str, candidate_count: int, review_count: int, ready_count: int) -> None:
        if candidate_count <= 0 or (review_count <= 0 and ready_count <= 0):
            return
        if review_count > 0 and ready_count > 0:
            parts.append(f"{kind_label} backlog {review_count} review/{ready_count} ready")
        elif review_count > 0:
            parts.append(f"{kind_label} backlog {review_count} review")
        elif ready_count > 0:
            parts.append(f"{kind_label} backlog {ready_count} ready")

    include_fixed = bool(fixed_candidate_count and (variable_candidate_count or (fixed_review_count and fixed_ready_count)))
    include_variable = bool(variable_candidate_count and (fixed_candidate_count or (variable_review_count and variable_ready_count)))
    if include_fixed:
        _append("fixed", fixed_candidate_count, fixed_review_count, fixed_ready_count)
    if include_variable:
        _append("variable", variable_candidate_count, variable_review_count, variable_ready_count)
    return parts


def _single_kind_candidate_backlog_parts(
    *,
    fixed_candidate_count: int,
    variable_candidate_count: int,
    fixed_review_count: int,
    variable_review_count: int,
    fixed_ready_count: int,
    variable_ready_count: int,
) -> list[str]:
    if fixed_candidate_count > 0 and variable_candidate_count <= 0:
        if fixed_review_count > 0 and fixed_ready_count > 0:
            return [f"fixed backlog {fixed_review_count} review/{fixed_ready_count} ready"]
        if fixed_review_count > 0:
            return [f"fixed backlog {fixed_review_count} review"]
        if fixed_ready_count > 0:
            return [f"fixed backlog {fixed_ready_count} ready"]
    if variable_candidate_count > 0 and fixed_candidate_count <= 0:
        if variable_review_count > 0 and variable_ready_count > 0:
            return [f"variable backlog {variable_review_count} review/{variable_ready_count} ready"]
        if variable_review_count > 0:
            return [f"variable backlog {variable_review_count} review"]
        if variable_ready_count > 0:
            return [f"variable backlog {variable_ready_count} ready"]
    return []


VALIDATION_ATTRIBUTE_SENSOR_KEYS = {
    "release_summary",
    "changes_preview",
    "confidence",
    "recommendation",
    "diagnostic_summary",
    "stale_source_count",
    "stale_source_summary",
    "health_status",
    "health_summary",
    "actions_today",
    "successful_actions_today",
    "failed_actions_today",
    "energy_redirected_today_kwh",
    "active_controlled_power_w",
    "battery_reserve_soc",
    "device_status_summary",
    "control_status",
    "control_summary",
    "control_reason",
    "control_guard_summary",
    "last_action_status",
    "last_action_summary",
    "last_action_at",
    "last_successful_action_at",
    "last_failed_action_at",
    "last_action_device",
    "last_failed_action_device",
    "last_failed_action_message",
    "recent_action_summary",
    "recent_failure_summary",
    "last_successful_action_summary",
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [ZeroNetExportSensor(coordinator, key, name) for key, name in SENSOR_DEFS.items()]
    entities.extend(_build_source_entities(coordinator))

    state = coordinator.data
    managed_details = _integration_page_managed_details(entry, state)
    coordinator._zne_integration_page_managed_details = managed_details
    managed_device_entities = {}
    for device_key, detail in managed_details.items():
        device_entities = _build_managed_device_row_entities(coordinator, device_key, detail)
        managed_device_entities[device_key] = device_entities
        entities.extend(device_entities)

    candidates = _candidate_devices_for_state(coordinator, hass, state, managed_details)
    _cleanup_legacy_unmanaged_candidate_device_rows(coordinator, hass, candidates)

    async_add_entities(entities)
    _register_managed_device_row_sync(
        coordinator,
        hass,
        entry,
        async_add_entities,
        managed_device_entities,
    )
    _register_unmanaged_candidate_cleanup(
        coordinator,
        hass,
        entry,
    )


def _build_managed_device_row_entities(coordinator, device_key: str, detail: dict[str, object]) -> list[ZeroNetExportEntity]:
    """Build the native integration-page child-device entities for one managed load."""
    device_name = str(detail.get("name") or device_key or "Managed device")
    entities: list[ZeroNetExportEntity] = [
        ZeroNetExportDeviceManagedSummarySensor(coordinator, device_key, device_name),
        ZeroNetExportDeviceStatusSensor(coordinator, device_key, device_name),
        ZeroNetExportDevicePowerSensor(coordinator, device_key, device_name, "current_power_w", "Current power"),
        ZeroNetExportDevicePlanSensor(coordinator, device_key, device_name),
        ZeroNetExportDeviceGuardSensor(coordinator, device_key, device_name),
        ZeroNetExportDevicePowerSensor(
            coordinator,
            device_key,
            device_name,
            "planned_power_delta_w",
            "Planned power delta",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        ZeroNetExportDevicePowerSensor(
            coordinator,
            device_key,
            device_name,
            "last_requested_power_w",
            "Last requested power",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        ZeroNetExportDevicePowerSensor(
            coordinator,
            device_key,
            device_name,
            "last_applied_power_w",
            "Last applied power",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        ZeroNetExportDeviceDurationSensor(coordinator, device_key, device_name, "current_active_seconds", "Current active runtime"),
        ZeroNetExportDeviceDurationSensor(coordinator, device_key, device_name, "active_runtime_today_seconds", "Active runtime today"),
        ZeroNetExportDeviceTimestampSensor(coordinator, device_key, device_name, "last_action_at", "Last action at"),
        ZeroNetExportDeviceTimestampSensor(coordinator, device_key, device_name, "last_applied_at", "Last applied at"),
        ZeroNetExportDeviceDetailSensor(coordinator, device_key, device_name, "last_action_status", "Last action status"),
        ZeroNetExportDeviceDetailSensor(coordinator, device_key, device_name, "last_action_result_message", "Last action result"),
    ]
    if detail.get("kind") == "variable":
        entities.append(
            ZeroNetExportDevicePowerSensor(
                coordinator,
                device_key,
                device_name,
                "current_target_power_w",
                "Target power",
            )
        )
    return entities


def _refresh_managed_device_row_entities(
    hass,
    coordinator,
    device_key: str,
    detail: dict[str, object],
    entities,
    async_add_entities,
) -> None:
    """Refresh existing managed child-device row metadata after managed-load detail changes."""
    target_power_key = f"device_{device_key}_current_target_power_w"
    target_power_entities = [entity for entity in entities if getattr(entity, "_key", None) == target_power_key]
    if detail.get("kind") == "variable" and not target_power_entities:
        device_name = str(detail.get("name") or device_key or "Managed device")
        target_power_entity = ZeroNetExportDevicePowerSensor(
            coordinator,
            device_key,
            device_name,
            "current_target_power_w",
            "Target power",
        )
        entities.append(target_power_entity)
        async_add_entities([target_power_entity])
    elif detail.get("kind") != "variable" and target_power_entities:
        for target_power_entity in target_power_entities:
            entities.remove(target_power_entity)
            _schedule_integration_page_entity_removal(hass, target_power_entity)

    device_name = str(detail.get("name") or device_key or "Managed device")
    device_info = managed_load_device_info(coordinator, device_key, detail)
    for entity in entities:
        suffix = getattr(entity, "_zero_net_export_managed_name_suffix", None)
        if suffix:
            entity._attr_name = managed_load_settings_action_name(device_name, suffix)
        entity._attr_device_info = device_info
        sync_integration_page_child_device_registry(
            hass,
            device_info,
            getattr(entity, "_zero_net_export_legacy_device_info", None),
        )
        write_state = getattr(entity, "async_write_ha_state", None)
        if write_state is not None:
            write_state()


def _register_managed_device_row_sync(
    coordinator,
    hass,
    entry,
    async_add_entities,
    known_managed_entities: dict[str, list[ZeroNetExportEntity]],
) -> None:
    """Keep managed device rows aligned without requiring platform reload."""

    def _sync_managed_device_rows() -> None:
        state = getattr(coordinator, "data", None)
        managed_details = _integration_page_managed_details(entry, state)
        coordinator._zne_integration_page_managed_details = managed_details
        current_device_keys = set(managed_details)
        for stale_key in sorted(set(known_managed_entities) - current_device_keys):
            stale_entities = known_managed_entities.pop(stale_key)
            for stale_entity in stale_entities:
                _schedule_integration_page_entity_removal(hass, stale_entity, remove_child_device=True)

        new_entities = []
        for device_key, detail in managed_details.items():
            existing_entities = known_managed_entities.get(device_key)
            if existing_entities is not None:
                _refresh_managed_device_row_entities(
                    hass,
                    coordinator,
                    device_key,
                    detail,
                    existing_entities,
                    async_add_entities,
                )
                continue
            device_entities = _build_managed_device_row_entities(coordinator, device_key, detail)
            known_managed_entities[device_key] = device_entities
            new_entities.extend(device_entities)
        if new_entities:
            async_add_entities(new_entities)

    add_listener = getattr(coordinator, "async_add_listener", None)
    if add_listener is None:
        return
    async_on_unload = getattr(entry, "async_on_unload", None)
    unsubscribe = add_listener(_sync_managed_device_rows)
    if unsubscribe is not None and async_on_unload is not None:
        async_on_unload(unsubscribe)


def _register_unmanaged_candidate_cleanup(
    coordinator,
    hass,
    entry,
) -> None:
    """Remove/suppress legacy unmanaged device-list rows while keeping backlog discovery available."""

    def _cleanup_legacy_unmanaged_candidate_device_rows_from_state() -> None:
        state = getattr(coordinator, "data", None)
        if state is None:
            return
        candidates = _candidate_devices_for_state(coordinator, hass, state)
        _cleanup_legacy_unmanaged_candidate_device_rows(coordinator, hass, candidates)

    add_listener = getattr(coordinator, "async_add_listener", None)
    if add_listener is None:
        return
    async_on_unload = getattr(entry, "async_on_unload", None)
    unsubscribe = add_listener(_cleanup_legacy_unmanaged_candidate_device_rows_from_state)
    if unsubscribe is not None and async_on_unload is not None:
        async_on_unload(unsubscribe)

    bus = getattr(hass, "bus", None)
    async_listen = getattr(bus, "async_listen", None)
    if async_listen is None:
        return

    def _cleanup_after_candidate_state_change(event) -> None:
        data = getattr(event, "data", {}) or {}
        entity_id = str(data.get("entity_id") or "")
        domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
        if domain not in DEVICE_CANDIDATE_DOMAINS:
            return
        _cleanup_legacy_unmanaged_candidate_device_rows_from_state()

    unsubscribe_state = async_listen("state_changed", _cleanup_after_candidate_state_change)
    if unsubscribe_state is not None and async_on_unload is not None:
        async_on_unload(unsubscribe_state)


def _cleanup_legacy_unmanaged_candidate_device_rows(coordinator, hass, candidates: list[dict[str, object]]) -> None:
    """Remove discovered unmanaged candidates from the native device-list surface.

    Candidate discovery still feeds Managed Devices backlog/review surfaces; this cleanup only
    suppresses the old integration-page `Un Managed — ...` child-device representation.
    """
    remove_unmanaged_candidate_child_devices_for_entry(hass, coordinator.entry.entry_id)
    for candidate in candidates:
        remove_integration_page_child_device_registry(hass, unmanaged_candidate_cleanup_device_info(coordinator, candidate))
        legacy_info = legacy_unmanaged_candidate_device_info(coordinator, candidate)
        if legacy_info is not None:
            remove_integration_page_child_device_registry(hass, legacy_info)


def _schedule_integration_page_entity_removal(hass, entity, *, remove_child_device: bool = False) -> None:
    """Remove a stale integration-page child-row entity after its backing row disappears."""
    if remove_child_device:
        remove_integration_page_child_device_registry(hass, getattr(entity, "_attr_device_info", None))
    remove = getattr(entity, "async_remove", None)
    if remove is None:
        return
    try:
        result = remove(force_remove=True)
    except TypeError:
        result = remove()
    if result is None:
        return
    create_task = getattr(hass, "async_create_task", None)
    if create_task is not None:
        create_task(result)
        return
    close = getattr(result, "close", None)
    if close is not None:
        close()


def _integration_page_managed_details(entry, state) -> dict[str, dict[str, object]]:
    """Return managed rows for the integration page, merging config inventory with runtime details."""
    return integration_page_managed_load_details(entry, state)


def _build_source_entities(coordinator):
    entities = []
    for source_key, label in SOURCE_LABELS.items():
        entities.extend(
            [
                ZeroNetExportSourceStatusSensor(coordinator, source_key, label),
                ZeroNetExportSourceReadingSensor(coordinator, source_key, label),
                ZeroNetExportSourceAgeSensor(coordinator, source_key, label),
                ZeroNetExportSourceIssueCountSensor(coordinator, source_key, label),
            ]
        )
    return entities


def _candidate_fit_details(candidate: dict[str, str]) -> dict[str, str | list[str]]:
    return assess_candidate(candidate)


def _managed_device_details(state) -> dict[str, dict[str, object]]:
    return managed_load_details_mapping(getattr(state, "device_details", {}) if state is not None else {})


def _managed_device_detail(state, device_key: str) -> dict[str, object]:
    return _managed_device_details(state).get(device_key, {})


def _managed_device_detail_for_coordinator(coordinator, state, device_key: str) -> dict[str, object]:
    """Return runtime detail overlaid with integration-page config fallback detail."""
    if state is None:
        return {}
    return managed_load_detail(coordinator, device_key)


def _managed_entity_ids(state) -> set[str]:
    return {
        str(detail.get("entity_id"))
        for detail in _managed_device_details(state).values()
        if detail.get("entity_id")
    }


def _candidate_state_signature(states: list[object]) -> tuple[tuple[str, str, str, str, str], ...]:
    """Return the candidate-relevant HA state signature used for cache invalidation."""
    signature: list[tuple[str, str, str, str, str]] = []
    for state in states:
        entity_id = str(getattr(state, "entity_id", "") or "")
        domain, _, object_id = entity_id.partition(".")
        if domain not in DEVICE_CANDIDATE_DOMAINS or object_id.startswith(f"{DOMAIN}_"):
            continue
        state_value = str(getattr(state, "state", "") or "")
        attributes = getattr(state, "attributes", {}) or {}
        if not isinstance(attributes, Mapping):
            attributes = {}
        signature.append(
            (
                entity_id,
                state_value,
                str(attributes.get("friendly_name") or ""),
                str(attributes.get("unit_of_measurement") or ""),
                str(attributes.get("device_class") or ""),
            )
        )
    return tuple(sorted(signature))


class _CandidateStateSnapshot:
    """Small HA-state facade so candidate discovery and cache keys share one snapshot."""

    def __init__(self, states: list[object]) -> None:
        self.states = self
        self._states = states

    def async_all(self) -> list[object]:
        return self._states


def _candidate_devices_for_hass(hass, managed_entity_ids: set[str]) -> list[dict[str, str]]:
    return discover_candidate_devices(hass.states.async_all(), managed_entity_ids)


def _candidate_devices_for_state(
    coordinator,
    hass,
    state,
    configured_managed_details: dict[str, dict[str, object]] | None = None,
) -> list[dict[str, str]]:
    managed_entity_ids = _managed_entity_ids(state)
    managed_detail_sources = [configured_managed_details]
    if configured_managed_details is None:
        managed_detail_sources.append(getattr(coordinator, "_zne_integration_page_managed_details", None))
    for managed_details in managed_detail_sources:
        if managed_details:
            managed_entity_ids.update(
                str(detail.get("entity_id"))
                for detail in managed_details.values()
                if detail.get("entity_id")
            )
    hass_states = list(hass.states.async_all())
    cache_key = (id(state), tuple(sorted(managed_entity_ids)), _candidate_state_signature(hass_states))
    cached = getattr(coordinator, "_zne_candidate_sensor_cache", None)
    if cached and cached.get("key") == cache_key:
        return cached["candidates"]
    candidates = _candidate_devices_for_hass(_CandidateStateSnapshot(hass_states), managed_entity_ids)
    setattr(
        coordinator,
        "_zne_candidate_sensor_cache",
        {
            "key": cache_key,
            "candidates": candidates,
        },
    )
    return candidates


def _managed_fleet_counts(device_details: dict[str, dict[str, object]] | None) -> dict[str, int]:
    devices = list(managed_load_details_mapping(device_details or {}).values())
    return {
        "managed_count": len(devices),
        "enabled_count": sum(1 for detail in devices if detail.get("effective_enabled", detail.get("enabled", True))),
        "disabled_count": max(
            len(devices)
            - sum(1 for detail in devices if detail.get("effective_enabled", detail.get("enabled", True))),
            0,
        ),
        "usable_count": sum(1 for detail in devices if detail.get("usable") is True),
        "blocked_count": sum(1 for detail in devices if detail.get("usable") is False),
        "planned_count": sum(1 for detail in devices if _device_has_active_plan(detail)),
        "attention_count": sum(1 for detail in devices if _device_needs_attention(detail)),
        "recent_attention_count": sum(1 for detail in devices if _device_has_recent_attention(detail)),
        "active_count": sum(1 for detail in devices if detail.get("observed_active") is True),
        "fixed_count": sum(1 for detail in devices if detail.get("kind") == "fixed"),
        "variable_count": sum(1 for detail in devices if detail.get("kind") == "variable"),
        "nominal_power_w": int(sum(float(detail.get("nominal_power_w", 0) or 0) for detail in devices)),
        "active_power_w": round(sum(float(detail.get("current_power_w", 0) or 0) for detail in devices if detail.get("observed_active") is True), 1),
    }


def _device_sort_key(detail: dict[str, object]) -> tuple[int, int, int, int, int, str]:
    effective_enabled = bool(detail.get("effective_enabled", detail.get("enabled", True)))
    usable = detail.get("usable")
    blocked_rank = 0 if _device_has_blocked_activity(detail) else 1
    planned_rank = 0 if _device_has_active_plan(detail) else 1
    recent_attention_rank = 0 if _device_has_recent_attention(detail) else 1
    enabled_usable_rank = 0 if effective_enabled and usable is True else 1
    return (
        blocked_rank,
        planned_rank,
        recent_attention_rank,
        enabled_usable_rank,
        int(detail.get("priority", 0) or 0),
        str(detail.get("name") or detail.get("entity_id") or "").lower(),
    )


def _first_matching_device_name(
    device_details: dict[str, dict[str, object]] | None,
    *,
    predicate,
) -> str:
    ordered = sorted(managed_load_details_mapping(device_details or {}).values(), key=_device_sort_key)
    for detail in ordered:
        if predicate(detail):
            return str(detail.get("name") or detail.get("entity_id") or "").strip()
    return ""


def _device_has_blocked_activity(detail: dict[str, object]) -> bool:
    planned_action = str(detail.get("planned_action") or "").strip().lower()
    if detail.get("usable") is False:
        return True
    return planned_action not in {"", "hold"} and detail.get("action_executable") is False


def _device_has_active_plan(detail: dict[str, object]) -> bool:
    return str(detail.get("planned_action") or "").strip().lower() not in {"", "hold"}


def _device_has_recent_attention(detail: dict[str, object]) -> bool:
    last_action_status = str(detail.get("last_action_status") or "").strip().lower()
    return bool(last_action_status and last_action_status not in {"ok", "applied", "success"})


def _device_needs_attention(detail: dict[str, object]) -> bool:
    return bool(
        _device_has_blocked_activity(detail)
        or _device_has_active_plan(detail)
        or _device_has_recent_attention(detail)
    )


def _truncate_sensor_state(text: str, *, max_chars: int = 255) -> str:
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 3].rstrip()}..."


def _fleet_overview_state(parts: list[str], *, max_chars: int = 255) -> str:
    def _compress_part(part: str, *, part_max_chars: int = 64) -> str:
        if len(part) <= part_max_chars:
            return part
        if " | " not in part:
            return _truncate_sensor_state(part, max_chars=part_max_chars)

        segments = part.split(" | ")
        if part.startswith(("review ", "ready ", "surfaced ")):
            if part.startswith("review "):
                compact_segments = [_truncate_sensor_state(segments[0], max_chars=32)]
                if len(segments) > 1:
                    compact_segments.append(_truncate_sensor_state(segments[1], max_chars=16))
                compact_segments.extend(
                    "warn"
                    if segment.startswith("warn")
                    else _truncate_sensor_state(segment, max_chars=5)
                    for segment in segments[2:]
                )
                return _truncate_sensor_state(" | ".join(compact_segments), max_chars=part_max_chars)
            compact_segments = [_truncate_sensor_state(segments[0], max_chars=30)]
            compact_segments.extend(_truncate_sensor_state(segment, max_chars=20) for segment in segments[1:])
            return _truncate_sensor_state(" | ".join(compact_segments), max_chars=part_max_chars)
        return _truncate_sensor_state(part, max_chars=part_max_chars)

    summary = " | ".join(parts)
    if len(summary) <= max_chars:
        return summary

    compact_parts = [
        part
        for part in parts
        if " fixed review" not in part
        and " variable review" not in part
    ]
    compact_summary = " | ".join(compact_parts)
    if len(compact_summary) <= max_chars:
        return compact_summary

    trimmed_parts = list(compact_parts)
    for marker in (" enabled", " usable"):
        if len(" | ".join(trimmed_parts)) <= max_chars:
            break
        for index, part in enumerate(list(trimmed_parts)):
            if part.endswith(marker):
                del trimmed_parts[index]
                break

    trimmed_summary = " | ".join(trimmed_parts)
    if len(trimmed_summary) <= max_chars:
        return trimmed_summary

    compact_trimmed_parts = [
        _compress_part(part, part_max_chars=64)
        if part.startswith(("review ", "ready ", "surfaced ", "attention ", "blocked ", "plan "))
        else part
        for part in trimmed_parts
    ]
    compact_trimmed_summary = " | ".join(compact_trimmed_parts)
    if len(compact_trimmed_summary) <= max_chars:
        return compact_trimmed_summary

    optional_parts = list(compact_trimmed_parts)
    for marker in (" W nominal", " fixed managed", " variable managed", "surfaced "):
        if len(" | ".join(optional_parts)) <= max_chars:
            break
        for index, part in enumerate(list(optional_parts)):
            if part.endswith(marker) or part.startswith(marker):
                del optional_parts[index]
                break

    optional_summary = " | ".join(optional_parts)
    if optional_summary and len(optional_summary) <= max_chars:
        return optional_summary

    minimal_parts: list[str] = []
    if parts:
        minimal_parts.append(parts[0])
    if len(parts) > 1:
        minimal_parts.append(parts[1])
    if parts and parts[0] == SOURCE_BLOCKER_ACTIVE_LABEL and len(parts) > 2:
        minimal_parts.append(parts[2])

    preserve_candidate_kind_counts = not any(
        part == SOURCE_BLOCKER_ACTIVE_LABEL
        or part.endswith("needs attention")
        or part.endswith("need attention")
        or part.startswith("active load ")
        for part in optional_parts
    )

    for part in optional_parts[2:]:
        if part == SOURCE_BLOCKER_ACTIVE_LABEL or part.endswith("needs attention") or part.endswith("need attention"):
            minimal_parts.append(part)
            continue
        if part.startswith(("blocked ", "attention ", "plan ", "active load ")):
            minimal_parts.append(_truncate_sensor_state(part, max_chars=56))
            continue
        if part.endswith("active managed device") or part.endswith("active managed devices"):
            minimal_parts.append(part)
            continue
        if preserve_candidate_kind_counts and (part.endswith("fixed candidate") or part.endswith("fixed candidates")):
            minimal_parts.append(part)
            continue
        if preserve_candidate_kind_counts and (part.endswith("variable candidate") or part.endswith("variable candidates")):
            minimal_parts.append(part)
            continue
        if preserve_candidate_kind_counts and part.startswith(("fixed backlog ", "variable backlog ")):
            minimal_parts.append(part)
            continue
        if part.endswith("needs review") or part.endswith("need review"):
            minimal_parts.append(part)
            continue
        if part.startswith("review "):
            minimal_parts.append(_compress_part(part, part_max_chars=64))
            continue
        if part.endswith("ready to promote"):
            minimal_parts.append(part)
            continue
        if part.startswith("ready "):
            if preserve_candidate_kind_counts:
                minimal_parts.append(_compress_part(part, part_max_chars=64))
            continue

    minimal_summary = " | ".join(dict.fromkeys(minimal_parts))
    if minimal_summary and len(minimal_summary) <= max_chars:
        return minimal_summary

    compact_minimal_parts = [
        _truncate_sensor_state(part, max_chars=32)
        if part.startswith(("blocked ", "attention ", "plan ", "review ", "ready "))
        else part
        for part in dict.fromkeys(minimal_parts)
    ]
    compact_minimal_summary = " | ".join(compact_minimal_parts)
    if compact_minimal_summary and len(compact_minimal_summary) <= max_chars:
        return compact_minimal_summary

    return _truncate_sensor_state(compact_minimal_summary or optional_summary or trimmed_summary, max_chars=max_chars)


def _unmanaged_candidate_overview_state(candidates: list[dict[str, object]]) -> str:
    if not candidates:
        return build_candidate_overview_summary(candidates)

    fixed_candidate_count = sum(1 for item in candidates if str(item.get("kind") or "") == "fixed")
    variable_candidate_count = sum(1 for item in candidates if str(item.get("kind") or "") == "variable")
    review_needed_count = sum(1 for item in candidates if candidate_needs_review(assess_candidate(item)))
    ready_candidate_count = max(len(candidates) - review_needed_count, 0)
    fixed_review_count, variable_review_count = candidate_review_kind_counts(candidates)
    fixed_ready_count = max(fixed_candidate_count - fixed_review_count, 0)
    variable_ready_count = max(variable_candidate_count - variable_review_count, 0)
    top_candidate = candidates[0]
    top_candidate_name = str(top_candidate.get("name") or top_candidate.get("entity_id") or "").strip()
    top_candidate_preview = build_candidate_compact_preview(top_candidate)
    review_candidate = first_review_candidate(candidates)
    review_candidate_name = str((review_candidate or {}).get("name") or (review_candidate or {}).get("entity_id") or "").strip()
    review_candidate_preview = build_candidate_compact_preview(review_candidate) if review_candidate else ""
    ready_candidate = next(
        (item for item in candidates if not candidate_needs_review(assess_candidate(item))),
        None,
    )
    ready_candidate_name = str((ready_candidate or {}).get("name") or (ready_candidate or {}).get("entity_id") or "").strip()
    ready_candidate_preview = build_candidate_compact_preview(ready_candidate) if ready_candidate else ""

    parts = [
        _count_label(len(candidates), "candidate"),
    ]
    if fixed_candidate_count:
        parts.append(_count_label(fixed_candidate_count, "fixed candidate"))
    if variable_candidate_count:
        parts.append(_count_label(variable_candidate_count, "variable candidate"))
    backlog_parts = _candidate_kind_backlog_mix_parts(
        fixed_candidate_count=fixed_candidate_count,
        variable_candidate_count=variable_candidate_count,
        fixed_review_count=fixed_review_count,
        variable_review_count=variable_review_count,
        fixed_ready_count=fixed_ready_count,
        variable_ready_count=variable_ready_count,
    )
    if backlog_parts:
        parts.extend(backlog_parts)
    else:
        parts.extend(
            _single_kind_candidate_backlog_parts(
                fixed_candidate_count=fixed_candidate_count,
                variable_candidate_count=variable_candidate_count,
                fixed_review_count=fixed_review_count,
                variable_review_count=variable_review_count,
                fixed_ready_count=fixed_ready_count,
                variable_ready_count=variable_ready_count,
            )
        )
    if review_needed_count:
        parts.append("1 needs review" if review_needed_count == 1 else f"{review_needed_count} need review")
        if fixed_review_count:
            parts.append(_count_label(fixed_review_count, "fixed review"))
        if variable_review_count:
            parts.append(_count_label(variable_review_count, "variable review"))
        if review_candidate_name:
            parts.append(f"review {review_candidate_preview or review_candidate_name}")
    if ready_candidate_count:
        parts.append(
            "1 ready to promote"
            if ready_candidate_count == 1
            else f"{ready_candidate_count} ready to promote"
        )
    if ready_candidate_name:
        parts.append(f"ready {ready_candidate_preview or ready_candidate_name}")
    if top_candidate_name and top_candidate_name not in {review_candidate_name, ready_candidate_name}:
        parts.append(f"surfaced {top_candidate_preview or top_candidate_name}")

    return _fleet_overview_state(parts)


def _merged_entry_config(entry) -> dict[str, object]:
    merged = dict(getattr(entry, "data", {}) or {})
    merged.update(dict(getattr(entry, "options", {}) or {}))
    return merged


def _same_managed_detail(left: dict[str, Any] | None, right: dict[str, Any] | None) -> bool:
    if not left or not right:
        return False
    left_id = str(left.get("entity_id") or left.get("name") or "").strip()
    right_id = str(right.get("entity_id") or right.get("name") or "").strip()
    return bool(left_id and right_id and left_id == right_id)


def _healthy_sources_next_step(coordinator, hass, state) -> str:
    candidates = _candidate_devices_for_state(coordinator, hass, state)
    counts = _managed_fleet_counts(getattr(state, "device_details", {}) or {})
    blocked_activity_count = counts["blocked_count"] or int(getattr(state, "blocked_planned_action_count", 0) or 0)
    top_candidate = candidates[0] if candidates else None
    top_candidate_name = str((top_candidate or {}).get("name") or (top_candidate or {}).get("entity_id") or "").strip()
    review_candidate = first_review_candidate(candidates or [])
    review_candidate_name = str((review_candidate or {}).get("name") or (review_candidate or {}).get("entity_id") or "").strip()
    ready_candidate = next(
        (item for item in (candidates or []) if not candidate_needs_review(assess_candidate(item))),
        None,
    )
    ready_candidate_name = str((ready_candidate or {}).get("name") or (ready_candidate or {}).get("entity_id") or "").strip()
    first_blocked_name = _first_matching_device_name(
        getattr(state, "device_details", {}) or {},
        predicate=_device_has_blocked_activity,
    )
    first_planned_name = _first_matching_device_name(
        getattr(state, "device_details", {}) or {},
        predicate=_device_has_active_plan,
    )
    first_attention_name = _first_matching_device_name(
        getattr(state, "device_details", {}) or {},
        predicate=_device_needs_attention,
    )

    if counts["managed_count"] == 0 and candidates:
        if review_candidate_name:
            next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, review unmanaged candidate: {review_candidate_name}"
            )
            if ready_candidate_name and ready_candidate_name != review_candidate_name:
                next_step += (
                    f", then promote ready unmanaged candidate: {ready_candidate_name}"
                )
            return _truncate_sensor_state(next_step)
        return _truncate_sensor_state(
            f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then promote ready unmanaged candidate: {ready_candidate_name or top_candidate_name or 'the next unmanaged candidate'}"
        )
    if blocked_activity_count:
        target = f" starting with {first_blocked_name}" if first_blocked_name else ""
        return _truncate_sensor_state(
            f"Open {DEVICES_CONFIGURE_PATH} to review blocked devices in the Managed Devices workspace{target}, then fix the next guard or readiness issue"
        )
    if counts["planned_count"]:
        target = f" for {first_planned_name}" if first_planned_name else ""
        return _truncate_sensor_state(
            f"Open {DEVICES_CONFIGURE_PATH} to confirm the active fleet plan in the Managed Devices workspace{target}"
        )
    if first_attention_name:
        return _truncate_sensor_state(
            f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, starting with attention on {first_attention_name}"
        )
    if candidates:
        if review_candidate_name:
            next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, review unmanaged candidate: {review_candidate_name}"
            )
            if ready_candidate_name and ready_candidate_name != review_candidate_name:
                next_step += (
                    f", then promote ready unmanaged candidate: {ready_candidate_name}"
                )
            return _truncate_sensor_state(next_step)
        return _truncate_sensor_state(
            f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then promote ready unmanaged candidate: {ready_candidate_name or top_candidate_name or 'the next unmanaged candidate'}"
        )
    if counts["managed_count"] == 0:
        return _truncate_sensor_state(
            f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available"
        )
    return _truncate_sensor_state(
        f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then edit device settings or stage enablement changes"
    )


class ZeroNetExportSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, key: str, name: str) -> None:
        super().__init__(coordinator, key, name)
        if key in FLEET_WORKSPACE_SENSOR_KEYS:
            # Managed/unmanaged workspace summaries should not pollute the primary
            # Zero Net Export device-info page Controls/Activity surface.
            self._attr_device_info = None

    @property
    def native_value(self):
        if self._key == "installed_version":
            return INTEGRATION_VERSION
        if self._key in {"release_summary", "changes_preview"}:
            info = build_release_info(INTEGRATION_VERSION, include_changelog=False)
            return info.get(self._key)
        if self._key in {"previous_installed_version", "update_summary"}:
            update = self._validation_details.get("release_update", {})
            mapping = {
                "previous_installed_version": update.get("previous_installed_version"),
                "update_summary": update.get("summary"),
            }
            return mapping.get(self._key)
        state = self._state
        if state is None:
            return None
        candidates = None
        if self._key in FLEET_WORKSPACE_SENSOR_KEYS:
            candidates = _candidate_devices_for_state(self.coordinator, self.hass, state)
        if self._key in {"managed_devices_surface", "managed_fleet_overview", "managed_fleet_attention", "managed_fleet_ready"}:
            device_details = _managed_device_details(state)
            counts = _managed_fleet_counts(device_details)
            blocked_activity_count = counts["blocked_count"] or int(getattr(state, "blocked_planned_action_count", 0) or 0)
            candidate_count = len(candidates)
            fixed_candidate_count = sum(1 for item in candidates if str(item.get("kind") or "") == "fixed")
            variable_candidate_count = sum(1 for item in candidates if str(item.get("kind") or "") == "variable")
            review_needed_count = sum(1 for item in candidates if candidate_needs_review(assess_candidate(item)))
            ready_candidate_count = max(candidate_count - review_needed_count, 0)
            top_candidate_name = str(candidates[0].get("name") or candidates[0].get("entity_id") or "").strip() if candidates else ""
            top_candidate_preview = build_candidate_compact_preview(candidates[0]) if candidates else ""
            review_candidate = next(
                (item for item in candidates if candidate_needs_review(assess_candidate(item))),
                None,
            )
            ready_candidate = next(
                (item for item in candidates if not candidate_needs_review(assess_candidate(item))),
                None,
            )
            fixed_review_count, variable_review_count = candidate_review_kind_counts(candidates)
            fixed_ready_count = max(fixed_candidate_count - fixed_review_count, 0)
            variable_ready_count = max(variable_candidate_count - variable_review_count, 0)
            review_candidate_name = str((review_candidate or {}).get("name") or (review_candidate or {}).get("entity_id") or "").strip()
            review_candidate_preview = build_candidate_compact_preview(review_candidate) if review_candidate else ""
            ready_candidate_name = str((ready_candidate or {}).get("name") or (ready_candidate or {}).get("entity_id") or "").strip()
            ready_candidate_preview = build_candidate_compact_preview(ready_candidate) if ready_candidate else ""
            ordered_details = sorted(device_details.values(), key=_device_sort_key)
            first_blocked_detail = next(
                (detail for detail in ordered_details if _device_has_blocked_activity(detail)),
                None,
            )
            first_planned_detail = next(
                (detail for detail in ordered_details if _device_has_active_plan(detail)),
                None,
            )
            first_attention_detail = next(
                (detail for detail in ordered_details if _device_needs_attention(detail)),
                None,
            )
            first_blocked_name = str((first_blocked_detail or {}).get("name") or (first_blocked_detail or {}).get("entity_id") or "").strip()
            first_planned_name = str((first_planned_detail or {}).get("name") or (first_planned_detail or {}).get("entity_id") or "").strip()
            first_attention_name = str((first_attention_detail or {}).get("name") or (first_attention_detail or {}).get("entity_id") or "").strip()
            first_active_detail = next(
                (
                    detail
                    for detail in ordered_details
                    if detail.get("observed_active") is True
                ),
                None,
            )
            suppress_planned_focus = bool(
                first_planned_detail
                and first_attention_detail
                and first_active_detail
                and _same_managed_detail(first_planned_detail, first_attention_detail)
                and not _same_managed_detail(first_planned_detail, first_active_detail)
            )
            merged = _merged_entry_config(self.coordinator.entry)
            blocking_source_summary = build_source_attention_summary(state, merged, limit=2, blocking_only=True)
            blocking_validation_details = summarize_validation_issue_messages(state, severities={"error"}, limit=1)
            source_blocked = blocking_source_summary != "None" or blocking_validation_details != "None"

            if self._key == "managed_devices_surface":
                surface_parts = ["Managed Devices surface"]
                surface_parts.append(
                    "no managed yet" if counts["managed_count"] == 0 else f"{counts['managed_count']} managed"
                )
                if counts["attention_count"]:
                    surface_parts.append(
                        "1 needs attention"
                        if counts["attention_count"] == 1
                        else f"{counts['attention_count']} need attention"
                    )
                elif counts["managed_count"]:
                    surface_parts.append("managed clear")
                if blocked_activity_count:
                    surface_parts.append(
                        f"blocked {first_blocked_name}" if first_blocked_name else f"blocked {blocked_activity_count}"
                    )
                elif counts["planned_count"]:
                    surface_parts.append(
                        f"plan {first_planned_name}" if first_planned_name else f"{counts['planned_count']} active plan"
                    )
                if counts["active_count"]:
                    surface_parts.append(
                        "1 active" if counts["active_count"] == 1 else f"{counts['active_count']} active"
                    )
                surface_parts.append(_unmanaged_count_label(candidate_count))
                if source_blocked:
                    surface_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
                elif review_candidate_name:
                    surface_parts.append(f"review {review_candidate_preview or review_candidate_name}")
                elif ready_candidate_name:
                    surface_parts.append(f"ready {ready_candidate_preview or ready_candidate_name}")
                elif candidate_count:
                    surface_parts.append("candidate review available")
                surface_parts.append("open Managed Devices workspace")
                return _fleet_overview_state(surface_parts)

            if self._key == "managed_fleet_attention":
                if counts["managed_count"] == 0:
                    if source_blocked:
                        return _truncate_sensor_state(f"No managed devices yet | {SOURCE_BLOCKER_ACTIVE_LABEL}")
                    if review_candidate_name:
                        return _truncate_sensor_state(
                            "No managed devices yet | Managed Devices workspace: "
                            f"review unmanaged candidate: {review_candidate_preview or review_candidate_name}"
                        )
                    return "No managed devices yet"
                attention_parts = []
                if counts["attention_count"]:
                    attention_parts.append(
                        "1 managed device needs attention"
                        if counts["attention_count"] == 1
                        else f"{counts['attention_count']} managed devices need attention"
                    )
                else:
                    attention_parts.append("Managed Devices: clear right now")
                if first_attention_name:
                    attention_parts.append(f"attention {first_attention_name}")
                if blocked_activity_count:
                    attention_parts.append(
                        f"blocked {first_blocked_name}" if first_blocked_name else f"blocked {blocked_activity_count}"
                    )
                if counts["planned_count"]:
                    attention_parts.append(
                        f"plan {first_planned_name}" if first_planned_name else f"{counts['planned_count']} active plan"
                    )
                if counts["active_count"]:
                    if counts["active_power_w"] > 0:
                        attention_parts.append(f"active load {counts['active_power_w']:g} W")
                    attention_parts.append(
                        "1 active managed device"
                        if counts["active_count"] == 1
                        else f"{counts['active_count']} active managed devices"
                    )
                return _fleet_overview_state(attention_parts)

            if self._key == "managed_fleet_ready":
                ready_parts = []
                if source_blocked:
                    ready_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
                if candidate_count:
                    if fixed_candidate_count:
                        ready_parts.append(_count_label(fixed_candidate_count, "fixed candidate"))
                    if variable_candidate_count:
                        ready_parts.append(_count_label(variable_candidate_count, "variable candidate"))
                    backlog_parts = _candidate_kind_backlog_mix_parts(
                        fixed_candidate_count=fixed_candidate_count,
                        variable_candidate_count=variable_candidate_count,
                        fixed_review_count=fixed_review_count,
                        variable_review_count=variable_review_count,
                        fixed_ready_count=fixed_ready_count,
                        variable_ready_count=variable_ready_count,
                    )
                    if backlog_parts:
                        ready_parts.extend(backlog_parts)
                    else:
                        ready_parts.extend(
                            _single_kind_candidate_backlog_parts(
                                fixed_candidate_count=fixed_candidate_count,
                                variable_candidate_count=variable_candidate_count,
                                fixed_review_count=fixed_review_count,
                                variable_review_count=variable_review_count,
                                fixed_ready_count=fixed_ready_count,
                                variable_ready_count=variable_ready_count,
                            )
                        )
                if ready_candidate_count:
                    ready_parts.append(
                        "1 ready to promote" if ready_candidate_count == 1 else f"{ready_candidate_count} ready to promote"
                    )
                    if ready_candidate_name:
                        ready_parts.append(f"ready {ready_candidate_preview or ready_candidate_name}")
                elif candidate_count:
                    ready_parts.append("No ready-to-promote unmanaged devices yet")
                else:
                    ready_parts.append("No unmanaged candidates right now")
                if review_needed_count:
                    ready_parts.append(
                        "1 still needs review" if review_needed_count == 1 else f"{review_needed_count} still need review"
                    )
                    if review_candidate_name:
                        ready_parts.append(f"review {review_candidate_preview or review_candidate_name}")
                return _fleet_overview_state(ready_parts)

            summary_parts = []
            if source_blocked:
                summary_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
            summary_parts.append("no managed yet" if counts["managed_count"] == 0 else f"{counts['managed_count']} managed")
            summary_parts.append(_unmanaged_count_label(candidate_count))
            if counts["managed_count"] == 0:
                if fixed_candidate_count:
                    summary_parts.append(_count_label(fixed_candidate_count, "fixed candidate"))
                if variable_candidate_count:
                    summary_parts.append(_count_label(variable_candidate_count, "variable candidate"))
                backlog_parts = _candidate_kind_backlog_mix_parts(
                    fixed_candidate_count=fixed_candidate_count,
                    variable_candidate_count=variable_candidate_count,
                    fixed_review_count=fixed_review_count,
                    variable_review_count=variable_review_count,
                    fixed_ready_count=fixed_ready_count,
                    variable_ready_count=variable_ready_count,
                )
                if backlog_parts:
                    summary_parts.extend(backlog_parts)
                else:
                    summary_parts.extend(
                        _single_kind_candidate_backlog_parts(
                            fixed_candidate_count=fixed_candidate_count,
                            variable_candidate_count=variable_candidate_count,
                            fixed_review_count=fixed_review_count,
                            variable_review_count=variable_review_count,
                            fixed_ready_count=fixed_ready_count,
                            variable_ready_count=variable_ready_count,
                        )
                    )
                if review_needed_count:
                    summary_parts.append("1 needs review" if review_needed_count == 1 else f"{review_needed_count} need review")
                    if fixed_review_count:
                        summary_parts.append(_count_label(fixed_review_count, "fixed review"))
                    if variable_review_count:
                        summary_parts.append(_count_label(variable_review_count, "variable review"))
                if ready_candidate_count:
                    summary_parts.append(
                        "1 ready to promote"
                        if ready_candidate_count == 1
                        else f"{ready_candidate_count} ready to promote"
                    )
                if review_candidate_name:
                    summary_parts.append(f"review {review_candidate_preview or review_candidate_name}")
                if ready_candidate_name:
                    summary_parts.append(f"ready {ready_candidate_preview or ready_candidate_name}")
                if top_candidate_name and top_candidate_name not in {review_candidate_name, ready_candidate_name}:
                    summary_parts.append(f"surfaced {top_candidate_preview or top_candidate_name}")
                return _fleet_overview_state(summary_parts)
            if counts["attention_count"]:
                summary_parts.append(
                    "1 managed device needs attention"
                    if counts["attention_count"] == 1
                    else f"{counts['attention_count']} managed devices need attention"
                )
            if first_attention_name and first_attention_name not in {first_blocked_name, first_planned_name}:
                summary_parts.append(f"attention {first_attention_name}")
            if blocked_activity_count:
                summary_parts.append(
                    f"blocked {first_blocked_name}" if first_blocked_name else f"blocked {blocked_activity_count}"
                )
            if counts["planned_count"]:
                summary_parts.append(
                    f"plan {first_planned_name}"
                    if first_planned_name and not suppress_planned_focus
                    else f"{counts['planned_count']} active plan"
                )
            if counts["active_count"]:
                if counts["active_power_w"] > 0:
                    summary_parts.append(f"active load {counts['active_power_w']:g} W")
                summary_parts.append(
                    "1 active managed device"
                    if counts["active_count"] == 1
                    else f"{counts['active_count']} active managed devices"
                )
                if first_active_detail and (not counts["attention_count"] or not _same_managed_detail(first_active_detail, first_attention_detail)) and (not blocked_activity_count or (first_blocked_detail and not _same_managed_detail(first_active_detail, first_blocked_detail))) and (not counts["planned_count"] or (first_planned_detail and not _same_managed_detail(first_active_detail, first_planned_detail))):
                    summary_parts.append(f"active device {_managed_snapshot_focus_label(first_active_detail)}")
            if candidate_count:
                if fixed_candidate_count:
                    summary_parts.append(_count_label(fixed_candidate_count, "fixed candidate"))
                if variable_candidate_count:
                    summary_parts.append(_count_label(variable_candidate_count, "variable candidate"))
                backlog_parts = _candidate_kind_backlog_mix_parts(
                    fixed_candidate_count=fixed_candidate_count,
                    variable_candidate_count=variable_candidate_count,
                    fixed_review_count=fixed_review_count,
                    variable_review_count=variable_review_count,
                    fixed_ready_count=fixed_ready_count,
                    variable_ready_count=variable_ready_count,
                )
                if backlog_parts:
                    summary_parts.extend(backlog_parts)
                else:
                    summary_parts.extend(
                        _single_kind_candidate_backlog_parts(
                            fixed_candidate_count=fixed_candidate_count,
                            variable_candidate_count=variable_candidate_count,
                            fixed_review_count=fixed_review_count,
                            variable_review_count=variable_review_count,
                            fixed_ready_count=fixed_ready_count,
                            variable_ready_count=variable_ready_count,
                        )
                    )
                if review_needed_count:
                    summary_parts.append("1 needs review" if review_needed_count == 1 else f"{review_needed_count} need review")
                    if fixed_review_count:
                        summary_parts.append(_count_label(fixed_review_count, "fixed review"))
                    if variable_review_count:
                        summary_parts.append(_count_label(variable_review_count, "variable review"))
                if ready_candidate_count:
                    summary_parts.append(
                        "1 ready to promote"
                        if ready_candidate_count == 1
                        else f"{ready_candidate_count} ready to promote"
                    )
                if review_candidate_name:
                    summary_parts.append(f"review {review_candidate_preview or review_candidate_name}")
                if ready_candidate_name:
                    summary_parts.append(f"ready {ready_candidate_preview or ready_candidate_name}")
                if top_candidate_name and top_candidate_name not in {review_candidate_name, ready_candidate_name}:
                    summary_parts.append(f"surfaced {top_candidate_preview or top_candidate_name}")
            summary_parts.append(f"{counts['enabled_count']} enabled")
            if counts.get("disabled_count"):
                summary_parts.append(f"{counts['disabled_count']} disabled")
            summary_parts.append(f"{counts['usable_count']} usable")
            summary_parts.append(f"{counts['fixed_count']} fixed managed")
            if counts["variable_count"]:
                summary_parts.append(f"{counts['variable_count']} variable managed")
            if counts["nominal_power_w"]:
                summary_parts.append(f"{counts['nominal_power_w']} W nominal")
            return _fleet_overview_state(summary_parts)
        if self._key == "unmanaged_candidate_count":
            return len(candidates or [])
        if self._key == "unmanaged_candidate_overview":
            return _unmanaged_candidate_overview_state(candidates or [])
        if self._key == "top_unmanaged_candidate":
            if not candidates:
                return "None"
            top = candidates[0]
            return build_candidate_preview(top, include_entity_id=False)
        if self._key == "top_candidate_fit":
            if not candidates:
                return "No candidate usefulness guidance available"
            return _candidate_usefulness_summary(candidates[0])
        if self._key == "top_candidate_warnings":
            if not candidates:
                return "No warnings"
            fit = _candidate_fit_details(candidates[0])
            warnings = fit.get('warnings') or []
            return "; ".join(warnings) if warnings else "No immediate warnings"
        if self._key == "candidate_shortlist":
            if not candidates:
                return "No additional candidates"
            return build_candidate_name_summary(candidates)
        if self._key == "candidate_shortlist_fit":
            return build_candidate_fit_summary(candidates or [])
        if self._key == "fleet_console_next_step":
            merged = _merged_entry_config(self.coordinator.entry)
            blocking_source_summary = build_source_attention_summary(state, merged, limit=3, blocking_only=True)
            blocking_validation_details = summarize_validation_issue_messages(state, severities={"error"}, limit=2)
            if blocking_source_summary != "None" or blocking_validation_details != "None":
                return _truncate_sensor_state(
                    f"Open {SOURCES_CONFIGURE_PATH}, repair blocking source roles first, then return to {DEVICES_CONFIGURE_PATH}"
                )
            return _healthy_sources_next_step(self.coordinator, self.hass, state)
        if self._key in {"mapped_source_blocker_summary", "mapped_source_blocker_next_step"}:
            merged = _merged_entry_config(self.coordinator.entry)
            summary = build_source_attention_summary(state, merged, limit=4)
            brief = build_source_attention_brief(state, merged, limit=3)
            if self._key == "mapped_source_blocker_summary":
                blocking_details = summarize_validation_issue_messages(state, severities={"error"}, limit=3)
                if summary != "None":
                    return brief
                if blocking_details != "None":
                    return blocking_details
                return "None"
            if summary != "None" or summarize_validation_issue_messages(state, severities={"error"}, limit=3) != "None":
                return f"Open {SOURCES_CONFIGURE_PATH}, repair source blockers, then save and reload the integration"
            recommended_next_step = str(build_native_operator_readiness(self.coordinator).get("next_step") or "").strip()
            if recommended_next_step:
                return recommended_next_step
            return _healthy_sources_next_step(self.coordinator, self.hass, state)
        if self._key in {"command_center_status", "command_center_recommended_path", "command_center_next_step"}:
            command_center = build_native_command_center_summary(self.coordinator)
            mapping = {
                "command_center_status": command_center.get("status_summary"),
                "command_center_recommended_path": command_center.get("recommended_path"),
                "command_center_next_step": command_center.get("next_action_summary"),
            }
            return mapping.get(self._key)
        return getattr(state, self._key, None)

    @property
    def entity_category(self):
        if self._key in FLEET_WORKSPACE_SENSOR_KEYS:
            return None
        if self._key in {
            "installed_version",
            "previous_installed_version",
            "release_summary",
            "changes_preview",
            "update_summary",
            "diagnostic_summary",
            "health_status",
            "health_summary",
            "recommendation",
            "control_status",
            "control_summary",
            "control_reason",
            "control_guard_summary",
            "last_action_status",
            "last_action_summary",
            "last_action_at",
            "last_successful_action_at",
            "last_failed_action_at",
            "last_action_device",
            "last_failed_action_device",
            "last_failed_action_message",
            "recent_action_summary",
            "recent_failure_summary",
            "last_successful_action_summary",
            "stale_source_count",
            "stale_source_summary",
            "action_history_count",
            "successful_action_count",
            "failed_action_count",
            "total_successful_action_count",
            "total_failed_action_count",
            "planned_action_count",
            "executable_action_count",
            "blocked_planned_action_count",
            "mapped_source_blocker_summary",
            "mapped_source_blocker_next_step",
            "command_center_status",
            "command_center_recommended_path",
            "command_center_next_step",
        }:
            return EntityCategory.DIAGNOSTIC
        return None

    @property
    def native_unit_of_measurement(self):
        if self._key.endswith("_power_w") or self._key in {
            "surplus_w",
            "last_reconciliation_error_w",
            "controllable_nominal_power_w",
            "usable_nominal_power_w",
            "export_error_w",
            "planned_power_delta_w",
            "variable_planned_power_delta_w",
            "fixed_planned_power_delta_w",
        }:
            return UnitOfPower.WATT
        if self._key == "energy_redirected_today_kwh":
            return UnitOfEnergy.KILO_WATT_HOUR
        if self._key in {"battery_soc", "battery_reserve_soc"}:
            return PERCENTAGE
        return None

    @property
    def extra_state_attributes(self):
        if self._key == "installed_version":
            return build_release_info(INTEGRATION_VERSION, include_changelog=False)
        if self._key in {"previous_installed_version", "release_summary", "changes_preview", "update_summary"}:
            return {
                **build_release_info(INTEGRATION_VERSION, include_changelog=False),
                **(self._validation_details.get("release_update", {}) or {}),
                "config_entry_version": self.coordinator.entry.version,
            }
        if self._key in {"managed_devices_surface", "managed_fleet_overview", "managed_fleet_attention", "managed_fleet_ready", "unmanaged_candidate_count", "unmanaged_candidate_overview", "top_unmanaged_candidate", "top_candidate_fit", "top_candidate_warnings", "candidate_shortlist", "candidate_shortlist_fit", "fleet_console_next_step"}:
            state = self._state
            if state is None:
                return None
            candidates = _candidate_devices_for_state(self.coordinator, self.hass, state)
            device_details = _managed_device_details(state)
            counts = _managed_fleet_counts(device_details)
            blocked_activity_count = counts["blocked_count"] or int(getattr(state, "blocked_planned_action_count", 0) or 0)
            review_needed_count = sum(1 for item in candidates if candidate_needs_review(assess_candidate(item)))
            top_candidate = candidates[0] if candidates else None
            review_candidate = first_review_candidate(candidates)
            ready_candidate = next(
                (item for item in candidates if not candidate_needs_review(assess_candidate(item))),
                None,
            )
            merged = _merged_entry_config(self.coordinator.entry)
            blocking_source_summary = build_source_attention_summary(state, merged, limit=3, blocking_only=True)
            blocking_validation_details = summarize_validation_issue_messages(state, severities={"error"}, limit=2)
            return {
                "configure_path": DEVICES_CONFIGURE_PATH,
                "managed_devices": list(device_details.values()),
                **counts,
                "candidate_devices": candidates[:12],
                "candidate_count": len(candidates),
                "review_needed_count": review_needed_count,
                "ready_candidate_count": max(len(candidates) - review_needed_count, 0),
                "fixed_review_count": sum(
                    1
                    for item in candidates
                    if str(item.get('kind') or '') == 'fixed' and candidate_needs_review(assess_candidate(item))
                ),
                "variable_review_count": sum(
                    1
                    for item in candidates
                    if str(item.get('kind') or '') == 'variable' and candidate_needs_review(assess_candidate(item))
                ),
                "fixed_ready_count": sum(
                    1
                    for item in candidates
                    if str(item.get('kind') or '') == 'fixed' and not candidate_needs_review(assess_candidate(item))
                ),
                "variable_ready_count": sum(
                    1
                    for item in candidates
                    if str(item.get('kind') or '') == 'variable' and not candidate_needs_review(assess_candidate(item))
                ),
                "blocked_activity_count": blocked_activity_count,
                "blocked_planned_action_count": int(getattr(state, "blocked_planned_action_count", 0) or 0),
                "fixed_candidate_count": sum(1 for item in candidates if str(item.get('kind') or '') == 'fixed'),
                "variable_candidate_count": sum(1 for item in candidates if str(item.get('kind') or '') == 'variable'),
                "top_candidate": top_candidate,
                "top_candidate_name": str(top_candidate.get('name') or top_candidate.get('entity_id') or '').strip() if top_candidate else None,
                "review_candidate": review_candidate,
                "ready_candidate": ready_candidate,
                "first_blocked_device": _first_matching_device_name(
                    device_details,
                    predicate=_device_has_blocked_activity,
                ) or None,
                "first_active_plan_device": _first_matching_device_name(
                    device_details,
                    predicate=_device_has_active_plan,
                ) or None,
                "first_attention_device": _first_matching_device_name(
                    device_details,
                    predicate=_device_needs_attention,
                ) or None,
                "source_blocked": blocking_source_summary != "None" or blocking_validation_details != "None",
                "source_blocker_summary": blocking_source_summary,
                "blocking_validation_details": blocking_validation_details,
                "source_repair_path": SOURCES_CONFIGURE_PATH,
                "top_candidate_fit": _candidate_fit_details(top_candidate) if top_candidate else None,
            }
        if self._key in {"mapped_source_blocker_summary", "mapped_source_blocker_next_step"}:
            state = self._state
            if state is None:
                return None
            merged = _merged_entry_config(self.coordinator.entry)
            readiness = build_native_operator_readiness(self.coordinator)
            attention = build_source_attention_details(state)
            return {
                "configure_path": SOURCES_CONFIGURE_PATH,
                "support_path": build_native_command_center_summary(self.coordinator).get("support_path"),
                "source_attention_summary": build_source_attention_summary(state, merged, limit=4),
                "affected_mapped_sources": build_source_attention_role_summary(state, merged, limit=6),
                "blocking_validation_details": summarize_validation_issue_messages(state, severities={"error"}, limit=3),
                "unavailable_source_keys": attention.get("unavailable_source_keys"),
                "stale_source_keys": attention.get("stale_source_keys"),
                "current_native_next_step": readiness.get("next_step"),
            }
        if self._key in {"command_center_status", "command_center_recommended_path", "command_center_next_step"}:
            command_center = build_native_command_center_summary(self.coordinator)
            return {
                "source_status": command_center.get("source_status"),
                "source_attention_roles": command_center.get("source_attention_roles"),
                "fleet_activity_summary": format_fleet_activity_for_operator(command_center.get("fleet_activity_summary")),
                "device_status": command_center.get("device_status"),
                "device_next_step": command_center.get("device_next_step"),
                "policy_status": command_center.get("policy_status"),
                "policy_readiness": command_center.get("policy_readiness"),
                "support_status": command_center.get("support_status"),
                "status_summary": command_center.get("status_summary"),
                "current_focus_section": command_center.get("recommended_section"),
                "current_focus_path": command_center.get("recommended_path"),
                "sources_path": command_center.get("sources_path"),
                "devices_path": command_center.get("devices_path"),
                "policy_path": command_center.get("policy_path"),
                "support_path": command_center.get("support_path"),
            }
        if self._key in VALIDATION_ATTRIBUTE_SENSOR_KEYS:
            return self._validation_details
        return None

    @property
    def device_class(self):
        if self._key in TIMESTAMP_SENSOR_KEYS:
            return SensorDeviceClass.TIMESTAMP
        return None


class ZeroNetExportSourceBaseSensor(ZeroNetExportEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, source_key: str, source_label: str, suffix_key: str, suffix_name: str):
        super().__init__(coordinator, f"source_{source_key}_{suffix_key}", f"{source_label} {suffix_name}")
        self._source_key = source_key

    @property
    def _source_diagnostic(self):
        return self._validation_details.get("source_diagnostics", {}).get(self._source_key, {})

    @property
    def _source_freshness(self):
        return self._validation_details.get("source_freshness", {}).get(self._source_key, {})

    @property
    def extra_state_attributes(self):
        return {
            **self._source_diagnostic,
            "freshness": self._source_freshness,
        }


class ZeroNetExportSourceStatusSensor(ZeroNetExportSourceBaseSensor):
    def __init__(self, coordinator, source_key: str, source_label: str):
        super().__init__(coordinator, source_key, source_label, "status", "status")

    @property
    def native_value(self):
        return self._source_diagnostic.get("status")


class ZeroNetExportSourceReadingSensor(ZeroNetExportSourceBaseSensor):
    def __init__(self, coordinator, source_key: str, source_label: str):
        super().__init__(coordinator, source_key, source_label, "reading", "reading")

    @property
    def native_value(self):
        return self._source_diagnostic.get("value")

    @property
    def native_unit_of_measurement(self):
        return self._source_diagnostic.get("unit")


class ZeroNetExportSourceAgeSensor(ZeroNetExportSourceBaseSensor):
    def __init__(self, coordinator, source_key: str, source_label: str):
        super().__init__(coordinator, source_key, source_label, "age_seconds", "age")

    @property
    def native_value(self):
        return self._source_freshness.get("age_seconds")

    @property
    def native_unit_of_measurement(self):
        return "s"


class ZeroNetExportSourceIssueCountSensor(ZeroNetExportSourceBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, source_key: str, source_label: str):
        super().__init__(coordinator, source_key, source_label, "issue_count", "issue count")

    @property
    def native_value(self):
        issue_counts = self._source_diagnostic.get("issue_counts") or {}
        return sum(int(issue_counts.get(level) or 0) for level in ("error", "warning", "info"))


def _format_device_power_summary(value) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{int(round(float(value)))} W"
    except (TypeError, ValueError):
        return str(value)


def _format_device_duration_summary(value) -> str:
    if value is None:
        return "n/a"
    try:
        total_seconds = int(round(float(value)))
    except (TypeError, ValueError):
        return str(value)
    if total_seconds < 60:
        return f"{total_seconds}s"
    minutes, remainder = divmod(total_seconds, 60)
    if minutes < 60:
        return f"{minutes}m {remainder}s" if remainder else f"{minutes}m"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        parts = [f"{hours}h"]
        if minutes:
            parts.append(f"{minutes}m")
        return " ".join(parts)
    days, hours = divmod(hours, 24)
    parts = [f"{days}d"]
    if hours:
        parts.append(f"{hours}h")
    return " ".join(parts)


def _device_kind_summary(kind: object) -> str:
    if kind == "fixed":
        return "fixed load"
    if kind == "variable":
        return "variable load"
    return str(kind or "unknown kind")


def _managed_snapshot_focus_label(detail: dict[str, Any] | None) -> str:
    if not detail:
        return ""
    name = str(detail.get("name") or detail.get("entity_id") or "Unnamed device").strip()
    parts: list[str] = []
    kind = str(detail.get("kind") or "").strip()
    if kind:
        parts.append(kind)
    if _device_has_blocked_activity(detail):
        parts.append("not usable" if detail.get("usable") is False else "blocked")
    elif _device_has_active_plan(detail):
        planned_action = str(detail.get("planned_action") or "").strip()
        if planned_action:
            parts.append(f"action {planned_action}")
    elif _device_has_recent_attention(detail) and detail.get("last_action_status"):
        parts.append(f"last {detail.get('last_action_status')}")
    if detail.get("observed_active") is True:
        if detail.get("current_power_w") not in (None, ""):
            active_power = f"active {_format_device_power_summary(detail.get('current_power_w'))}"
            if active_power not in parts:
                parts.append(active_power)
        elif "active" not in parts:
            parts.append("active")
    return f"{name} ({' | '.join(parts)})" if parts else name


def _attach_managed_load_device(entity, coordinator, device_key: str, device_name: str) -> None:
    attach_managed_load_device(entity, coordinator, device_key, device_name)


class ZeroNetExportDeviceManagedSummarySensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(
            coordinator,
            f"device_{device_key}_managed_summary",
            managed_load_settings_action_name(device_name, "managed summary"),
        )
        self._device_key = device_key
        self._zero_net_export_managed_name_suffix = "managed summary"
        _attach_managed_load_device(self, coordinator, device_key, device_name)

    @staticmethod
    def _active_planned_action(detail: dict[str, Any]) -> str:
        planned_action = str(detail.get("planned_action") or "").strip()
        return planned_action if planned_action not in {"", "hold"} else ""

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        detail = _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key)
        runtime_bits: list[str] = []
        if _device_has_blocked_activity(detail):
            runtime_bits.append("blocked")
        elif self._active_planned_action(detail):
            runtime_bits.append("planned")
        elif _device_has_recent_attention(detail):
            runtime_bits.append("attention")
        if detail.get("observed_active") is True and "active" not in runtime_bits:
            runtime_bits.append("active")

        runtime_bits.extend(
            [
                _device_kind_summary(detail.get("kind")),
                str(detail.get("status") or "status unknown"),
                "usable" if detail.get("usable") else "not usable",
                "enabled" if detail.get("effective_enabled", detail.get("enabled", True)) else "disabled",
            ]
        )
        priority = detail.get("priority")
        if priority is not None:
            runtime_bits.append(f"priority {priority}")
        operator_priority_override = detail.get("operator_priority_override")
        if operator_priority_override is not None:
            runtime_bits.append(f"priority override {operator_priority_override}")
        operator_enabled_override = detail.get("operator_enabled_override")
        if operator_enabled_override is not None:
            runtime_bits.append(f"enabled override {'on' if operator_enabled_override else 'off'}")
        runtime_bits.append(f"power {_format_device_power_summary(detail.get('current_power_w'))}")
        nominal_power = detail.get("nominal_power_w")
        if nominal_power not in (None, ""):
            try:
                nominal_value = float(nominal_power)
            except (TypeError, ValueError):
                nominal_value = 0
            if nominal_value > 0:
                runtime_bits.append(f"nominal {nominal_value:g} W")
        if detail.get("kind") == "variable" and detail.get("current_target_power_w") is not None:
            runtime_bits.append(f"target {_format_device_power_summary(detail.get('current_target_power_w'))}")
        current_runtime = detail.get("current_active_seconds")
        if current_runtime not in (None, 0, 0.0):
            runtime_bits.append(f"runtime {_format_device_duration_summary(current_runtime)}")
        runtime_today = detail.get("active_runtime_today_seconds")
        if runtime_today not in (None, 0, 0.0):
            runtime_bits.append(f"today {_format_device_duration_summary(runtime_today)}")
        guard_status = str(detail.get("guard_status") or "").strip()
        if guard_status and guard_status not in {"ready", "idle"}:
            runtime_bits.append(f"guard {guard_status}")
        planned_action = self._active_planned_action(detail)
        if planned_action:
            runtime_bits.append(f"action {planned_action}")
        last_action_status = str(detail.get("last_action_status") or "").strip()
        if last_action_status and last_action_status not in {"ok", "applied", "success"}:
            runtime_bits.append(f"last {last_action_status}")
        return " | ".join(runtime_bits)

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return {
            **_managed_device_detail_for_coordinator(self.coordinator, state, self._device_key),
            "bucket": "Managed Devices",
            "integration_page_group": "Managed Devices",
        }


class ZeroNetExportDeviceStatusSensor(ZeroNetExportEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_status", managed_load_settings_action_name(device_name, "status"))
        self._device_key = device_key
        self._zero_net_export_managed_name_suffix = "status"
        _attach_managed_load_device(self, coordinator, device_key, device_name)

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key).get("status")

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key)


class ZeroNetExportDevicePlanSensor(ZeroNetExportEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_planned_action", managed_load_settings_action_name(device_name, "planned action"))
        self._device_key = device_key
        self._zero_net_export_managed_name_suffix = "planned action"
        _attach_managed_load_device(self, coordinator, device_key, device_name)

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key).get("planned_action")

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key)


class ZeroNetExportDeviceGuardSensor(ZeroNetExportEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_guard_status", managed_load_settings_action_name(device_name, "guard status"))
        self._device_key = device_key
        self._zero_net_export_managed_name_suffix = "guard status"
        _attach_managed_load_device(self, coordinator, device_key, device_name)

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key).get("guard_status")

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key)


class ZeroNetExportDevicePowerSensor(ZeroNetExportEntity, SensorEntity):
    def __init__(
        self,
        coordinator,
        device_key: str,
        device_name: str,
        value_key: str,
        suffix: str,
        *,
        entity_category=None,
    ):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", managed_load_settings_action_name(device_name, suffix))
        self._device_key = device_key
        self._value_key = value_key
        self._zero_net_export_managed_name_suffix = suffix
        self._attr_entity_category = entity_category
        _attach_managed_load_device(self, coordinator, device_key, device_name)

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key).get(self._value_key)

    @property
    def native_unit_of_measurement(self):
        return UnitOfPower.WATT

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key)


class ZeroNetExportDeviceDurationSensor(ZeroNetExportEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", managed_load_settings_action_name(device_name, suffix))
        self._device_key = device_key
        self._value_key = value_key
        self._zero_net_export_managed_name_suffix = suffix
        _attach_managed_load_device(self, coordinator, device_key, device_name)

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key).get(self._value_key)

    @property
    def native_unit_of_measurement(self):
        return UnitOfTime.SECONDS

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key)


class ZeroNetExportDeviceTimestampSensor(ZeroNetExportEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", managed_load_settings_action_name(device_name, suffix))
        self._device_key = device_key
        self._value_key = value_key
        self._zero_net_export_managed_name_suffix = suffix
        _attach_managed_load_device(self, coordinator, device_key, device_name)

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key).get(self._value_key)

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key)


class ZeroNetExportDeviceDetailSensor(ZeroNetExportEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", managed_load_settings_action_name(device_name, suffix))
        self._device_key = device_key
        self._value_key = value_key
        self._zero_net_export_managed_name_suffix = suffix
        _attach_managed_load_device(self, coordinator, device_key, device_name)

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key).get(self._value_key)

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return _managed_device_detail_for_coordinator(self.coordinator, state, self._device_key)
