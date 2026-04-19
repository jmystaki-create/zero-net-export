"""Sensors for Zero Net Export."""
from __future__ import annotations

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
    candidate_needs_review,
    candidate_review_kind_counts,
    discover_candidate_devices,
    first_review_candidate,
)
from .const import DOMAIN, INTEGRATION_VERSION
from .entity import ZeroNetExportEntity
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
    "recommendation": "Recommendation",
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
    "device_count": "Managed devices",
    "enabled_device_count": "Enabled devices",
    "usable_device_count": "Usable devices",
    "fixed_device_count": "Fixed devices",
    "variable_device_count": "Variable devices",
    "controllable_nominal_power_w": "Managed controllable power",
    "usable_nominal_power_w": "Usable controllable power",
    "device_status_summary": "Device status summary",
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
    "managed_fleet_overview": "Managed devices overview",
    "managed_fleet_attention": "Managed devices attention",
    "managed_fleet_ready": "Managed devices ready next",
    "unmanaged_candidate_count": "Unmanaged candidate devices",
    "unmanaged_candidate_overview": "Unmanaged candidate overview",
    "top_unmanaged_candidate": "Currently surfaced unmanaged candidate",
    "top_candidate_fit": "Currently surfaced candidate usefulness",
    "top_candidate_warnings": "Currently surfaced candidate warnings",
    "candidate_shortlist": "Candidate shortlist",
    "candidate_shortlist_fit": "Candidate shortlist usefulness",
    "fleet_console_next_step": "Managed devices next step",
    "mapped_source_blocker_summary": "Mapped-source blocker summary",
    "mapped_source_blocker_next_step": "Mapped-source blocker next step",
    "command_center_status": "Command center status",
    "command_center_recommended_path": "Command center recommended path",
    "command_center_next_step": "Command center next step",
}

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
    if state is not None:
        for device_key, details in state.device_details.items():
            entities.extend(
                [
                    ZeroNetExportDeviceManagedSummarySensor(coordinator, device_key, details["name"]),
                    ZeroNetExportDeviceStatusSensor(coordinator, device_key, details["name"]),
                    ZeroNetExportDevicePowerSensor(coordinator, device_key, details["name"], "current_power_w", "Current power"),
                    ZeroNetExportDevicePlanSensor(coordinator, device_key, details["name"]),
                    ZeroNetExportDeviceGuardSensor(coordinator, device_key, details["name"]),
                    ZeroNetExportDevicePowerSensor(
                        coordinator,
                        device_key,
                        details["name"],
                        "planned_power_delta_w",
                        "Planned power delta",
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                    ZeroNetExportDevicePowerSensor(
                        coordinator,
                        device_key,
                        details["name"],
                        "last_requested_power_w",
                        "Last requested power",
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                    ZeroNetExportDevicePowerSensor(
                        coordinator,
                        device_key,
                        details["name"],
                        "last_applied_power_w",
                        "Last applied power",
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                    ZeroNetExportDeviceDurationSensor(coordinator, device_key, details["name"], "current_active_seconds", "Current active runtime"),
                    ZeroNetExportDeviceDurationSensor(coordinator, device_key, details["name"], "active_runtime_today_seconds", "Active runtime today"),
                    ZeroNetExportDeviceTimestampSensor(coordinator, device_key, details["name"], "last_action_at", "Last action at"),
                    ZeroNetExportDeviceTimestampSensor(coordinator, device_key, details["name"], "last_applied_at", "Last applied at"),
                    ZeroNetExportDeviceDetailSensor(coordinator, device_key, details["name"], "last_action_status", "Last action status"),
                    ZeroNetExportDeviceDetailSensor(coordinator, device_key, details["name"], "last_action_result_message", "Last action result"),
                ]
            )
            if details["kind"] == "variable":
                entities.append(
                    ZeroNetExportDevicePowerSensor(
                        coordinator,
                        device_key,
                        details["name"],
                        "current_target_power_w",
                        "Target power",
                    )
                )

    async_add_entities(entities)


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


def _managed_entity_ids(state) -> set[str]:
    return {
        str(detail.get("entity_id"))
        for detail in (getattr(state, "device_details", {}) or {}).values()
        if detail.get("entity_id")
    }


def _candidate_devices_for_hass(hass, managed_entity_ids: set[str]) -> list[dict[str, str]]:
    return discover_candidate_devices(hass.states.async_all(), managed_entity_ids)


def _candidate_devices_for_state(coordinator, hass, state) -> list[dict[str, str]]:
    managed_entity_ids = _managed_entity_ids(state)
    cache_key = (id(state), tuple(sorted(managed_entity_ids)))
    cached = getattr(coordinator, "_zne_candidate_sensor_cache", None)
    if cached and cached.get("key") == cache_key:
        return cached["candidates"]
    candidates = _candidate_devices_for_hass(hass, managed_entity_ids)
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
    devices = list((device_details or {}).values())
    return {
        "managed_count": len(devices),
        "enabled_count": sum(1 for detail in devices if detail.get("effective_enabled", detail.get("enabled", True))),
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
    ordered = sorted((device_details or {}).values(), key=_device_sort_key)
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
    summary = " | ".join(parts)
    if len(summary) <= max_chars:
        return summary
    compact_parts = [
        part
        for part in parts
        if " fixed review" not in part and " variable review" not in part
    ]
    compact_summary = " | ".join(compact_parts)
    if len(compact_summary) <= max_chars:
        return compact_summary

    optional_markers = (" enabled", " usable")
    trimmed_parts = list(compact_parts)
    for marker in optional_markers:
        if len(" | ".join(trimmed_parts)) <= max_chars:
            break
        for index, part in enumerate(list(trimmed_parts)):
            if part.endswith(marker):
                del trimmed_parts[index]
                break
    trimmed_summary = " | ".join(trimmed_parts)
    if len(trimmed_summary) <= max_chars:
        return trimmed_summary

    compact_parts = [
        _truncate_sensor_state(part, max_chars=56)
        if part.startswith(("review ", "ready ", "top "))
        else part
        for part in trimmed_parts
    ]
    compact_summary = " | ".join(compact_parts)
    return _truncate_sensor_state(compact_summary, max_chars=max_chars)


def _unmanaged_candidate_overview_state(candidates: list[dict[str, object]]) -> str:
    if not candidates:
        return build_candidate_overview_summary(candidates)

    fixed_candidate_count = sum(1 for item in candidates if str(item.get("kind") or "") == "fixed")
    variable_candidate_count = sum(1 for item in candidates if str(item.get("kind") or "") == "variable")
    review_needed_count = sum(1 for item in candidates if candidate_needs_review(assess_candidate(item)))
    ready_candidate_count = max(len(candidates) - review_needed_count, 0)
    fixed_review_count, variable_review_count = candidate_review_kind_counts(candidates)
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
        parts.append(f"top {top_candidate_preview or top_candidate_name}")

    return _fleet_overview_state(parts)


def _merged_entry_config(entry) -> dict[str, object]:
    merged = dict(getattr(entry, "data", {}) or {})
    merged.update(dict(getattr(entry, "options", {}) or {}))
    return merged


class ZeroNetExportSensor(ZeroNetExportEntity, SensorEntity):
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
        if self._key in {"managed_fleet_overview", "managed_fleet_attention", "managed_fleet_ready"}:
            counts = _managed_fleet_counts(state.device_details)
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
            review_candidate_name = str((review_candidate or {}).get("name") or (review_candidate or {}).get("entity_id") or "").strip()
            review_candidate_preview = build_candidate_compact_preview(review_candidate) if review_candidate else ""
            ready_candidate_name = str((ready_candidate or {}).get("name") or (ready_candidate or {}).get("entity_id") or "").strip()
            ready_candidate_preview = build_candidate_compact_preview(ready_candidate) if ready_candidate else ""
            first_blocked_name = _first_matching_device_name(
                state.device_details,
                predicate=_device_has_blocked_activity,
            )
            first_planned_name = _first_matching_device_name(
                state.device_details,
                predicate=_device_has_active_plan,
            )
            first_attention_name = _first_matching_device_name(
                state.device_details,
                predicate=_device_needs_attention,
            )
            merged = _merged_entry_config(self.coordinator.entry)
            blocking_source_summary = build_source_attention_summary(state, merged, limit=2, blocking_only=True)
            blocking_validation_details = summarize_validation_issue_messages(state, severities={"error"}, limit=1)
            source_blocked = blocking_source_summary != "None" or blocking_validation_details != "None"

            if self._key == "managed_fleet_attention":
                if counts["managed_count"] == 0:
                    if source_blocked:
                        return "Repair sources first before managed-device review"
                    if review_candidate_name:
                        return f"No managed devices yet | review {review_candidate_preview or review_candidate_name} first"
                    return "No managed devices yet"
                attention_parts = []
                if counts["attention_count"]:
                    attention_parts.append(
                        "1 managed device needs attention"
                        if counts["attention_count"] == 1
                        else f"{counts['attention_count']} managed devices need attention"
                    )
                else:
                    attention_parts.append("No managed-device attention right now")
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
                if counts["active_power_w"] > 0:
                    attention_parts.append(f"active load {counts['active_power_w']:g} W")
                return _fleet_overview_state(attention_parts)

            if self._key == "managed_fleet_ready":
                ready_parts = []
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
                if source_blocked:
                    ready_parts.append("repair sources first")
                return _fleet_overview_state(ready_parts)

            summary_parts = [f"{counts['managed_count']} managed"]
            summary_parts.append(
                f"{candidate_count} unmanaged" if candidate_count else "no unmanaged candidates"
            )
            if counts["managed_count"] == 0:
                if source_blocked:
                    summary_parts.append("repair sources first")
                if fixed_candidate_count:
                    summary_parts.append(_count_label(fixed_candidate_count, "fixed candidate"))
                if variable_candidate_count:
                    summary_parts.append(_count_label(variable_candidate_count, "variable candidate"))
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
                    summary_parts.append(f"top {top_candidate_preview or top_candidate_name}")
                return _fleet_overview_state(summary_parts)
            if source_blocked:
                summary_parts.append("repair sources first")
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
                    f"plan {first_planned_name}" if first_planned_name else f"{counts['planned_count']} active plan"
                )
            if counts["active_power_w"] > 0:
                summary_parts.append(f"active load {counts['active_power_w']:g} W")
                summary_parts.append(
                    "1 active managed device"
                    if counts["active_count"] == 1
                    else f"{counts['active_count']} active managed devices"
                )
            if candidate_count:
                if fixed_candidate_count:
                    summary_parts.append(_count_label(fixed_candidate_count, "fixed candidate"))
                if variable_candidate_count:
                    summary_parts.append(_count_label(variable_candidate_count, "variable candidate"))
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
                    summary_parts.append(f"top {top_candidate_preview or top_candidate_name}")
            summary_parts.extend(
                [
                    f"{counts['enabled_count']} enabled",
                    f"{counts['usable_count']} usable",
                ]
            )
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
            counts = _managed_fleet_counts(state.device_details)
            blocked_activity_count = counts["blocked_count"] or int(getattr(state, "blocked_planned_action_count", 0) or 0)
            merged = _merged_entry_config(self.coordinator.entry)
            blocking_source_summary = build_source_attention_summary(state, merged, limit=3, blocking_only=True)
            blocking_validation_details = summarize_validation_issue_messages(state, severities={"error"}, limit=2)
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
                state.device_details,
                predicate=_device_has_blocked_activity,
            )
            first_planned_name = _first_matching_device_name(
                state.device_details,
                predicate=_device_has_active_plan,
            )
            first_attention_name = _first_matching_device_name(
                state.device_details,
                predicate=_device_needs_attention,
            )
            if blocking_source_summary != "None" or blocking_validation_details != "None":
                return _truncate_sensor_state(
                    f"Open {SOURCES_CONFIGURE_PATH}, repair blocking source roles first, then return to {DEVICES_CONFIGURE_PATH}"
                )
            if counts["managed_count"] == 0 and candidates:
                if review_candidate_name:
                    next_step = (
                        f"Open {DEVICES_CONFIGURE_PATH} and review {review_candidate_name} first from the unmanaged list"
                    )
                    if ready_candidate_name and ready_candidate_name != review_candidate_name:
                        next_step += f", then promote {ready_candidate_name} next"
                    return _truncate_sensor_state(next_step)
                return _truncate_sensor_state(
                    f"Open {DEVICES_CONFIGURE_PATH} and promote {ready_candidate_name or top_candidate_name or 'the next unmanaged candidate'} next"
                )
            if blocked_activity_count:
                target = f" starting with {first_blocked_name}" if first_blocked_name else ""
                return _truncate_sensor_state(
                    f"Open {DEVICES_CONFIGURE_PATH}, review blocked managed devices{target}, then fix the next guard or readiness issue"
                )
            if counts["planned_count"]:
                target = f" for {first_planned_name}" if first_planned_name else ""
                return _truncate_sensor_state(
                    f"Open {DEVICES_CONFIGURE_PATH} and confirm the active managed-device plan{target} before changing the fleet"
                )
            if first_attention_name:
                return _truncate_sensor_state(
                    f"Open {DEVICES_CONFIGURE_PATH} and review managed-device attention starting with {first_attention_name} before changing the fleet"
                )
            if candidates:
                if review_candidate_name:
                    next_step = (
                        f"Review unmanaged candidates, starting with {review_candidate_name}, from {DEVICES_CONFIGURE_PATH}"
                    )
                    if ready_candidate_name and ready_candidate_name != review_candidate_name:
                        next_step += f", then promote {ready_candidate_name} next"
                    return _truncate_sensor_state(next_step)
                return _truncate_sensor_state(
                    f"Review unmanaged candidates, then promote {ready_candidate_name or top_candidate_name or 'the next unmanaged candidate'} from {DEVICES_CONFIGURE_PATH}"
                )
            return _truncate_sensor_state(
                f"Open {POLICY_CONFIGURE_PATH} to tune behaviour, or {SOURCES_CONFIGURE_PATH} if runtime health still needs work"
            )
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
                return f"Open {SOURCES_CONFIGURE_PATH}, repair mapped-source blockers, then save and reload the integration"
            return f"Mapped sources currently look healthy; continue in {DEVICES_CONFIGURE_PATH} or {POLICY_CONFIGURE_PATH}"
        if self._key in {"command_center_status", "command_center_recommended_path", "command_center_next_step"}:
            command_center = build_native_command_center_summary(self.coordinator)
            mapping = {
                "command_center_status": command_center.get("status_summary"),
                "command_center_recommended_path": command_center.get("recommended_path"),
                "command_center_next_step": command_center.get("next_action_summary"),
            }
            return mapping.get(self._key)
        return getattr(state, self._key)

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
        if self._key in {"managed_fleet_overview", "managed_fleet_attention", "managed_fleet_ready", "unmanaged_candidate_count", "unmanaged_candidate_overview", "top_unmanaged_candidate", "top_candidate_fit", "top_candidate_warnings", "candidate_shortlist", "candidate_shortlist_fit", "fleet_console_next_step"}:
            state = self._state
            if state is None:
                return None
            candidates = _candidate_devices_for_state(self.coordinator, self.hass, state)
            counts = _managed_fleet_counts(state.device_details)
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
                "managed_devices": list((state.device_details or {}).values()),
                **counts,
                "candidate_devices": candidates[:12],
                "candidate_count": len(candidates),
                "review_needed_count": review_needed_count,
                "ready_candidate_count": max(len(candidates) - review_needed_count, 0),
                "blocked_activity_count": blocked_activity_count,
                "blocked_planned_action_count": int(getattr(state, "blocked_planned_action_count", 0) or 0),
                "fixed_candidate_count": sum(1 for item in candidates if str(item.get('kind') or '') == 'fixed'),
                "variable_candidate_count": sum(1 for item in candidates if str(item.get('kind') or '') == 'variable'),
                "top_candidate": top_candidate,
                "top_candidate_name": str(top_candidate.get('name') or top_candidate.get('entity_id') or '').strip() if top_candidate else None,
                "review_candidate": review_candidate,
                "ready_candidate": ready_candidate,
                "first_blocked_device": _first_matching_device_name(
                    state.device_details,
                    predicate=_device_has_blocked_activity,
                ) or None,
                "first_active_plan_device": _first_matching_device_name(
                    state.device_details,
                    predicate=_device_has_active_plan,
                ) or None,
                "first_attention_device": _first_matching_device_name(
                    state.device_details,
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
                "recommended_next_step": readiness.get("next_step"),
            }
        if self._key in {"command_center_status", "command_center_recommended_path", "command_center_next_step"}:
            command_center = build_native_command_center_summary(self.coordinator)
            return {
                "source_status": command_center.get("source_status"),
                "source_attention_roles": command_center.get("source_attention_roles"),
                "device_status": command_center.get("device_status"),
                "device_next_step": command_center.get("device_next_step"),
                "policy_status": command_center.get("policy_status"),
                "policy_readiness": command_center.get("policy_readiness"),
                "support_status": command_center.get("support_status"),
                "status_summary": command_center.get("status_summary"),
                "recommended_section": command_center.get("recommended_section"),
                "recommended_path": command_center.get("recommended_path"),
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


def _device_kind_summary(kind: object) -> str:
    if kind == "fixed":
        return "fixed load"
    if kind == "variable":
        return "variable load"
    return str(kind or "unknown kind")


class ZeroNetExportDeviceManagedSummarySensor(ZeroNetExportEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_managed_summary", f"{device_name} managed summary")
        self._device_key = device_key

    @staticmethod
    def _active_planned_action(detail: dict[str, Any]) -> str:
        planned_action = str(detail.get("planned_action") or "").strip()
        return planned_action if planned_action not in {"", "hold"} else ""

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        detail = state.device_details.get(self._device_key, {})
        runtime_bits = [
            _device_kind_summary(detail.get("kind")),
            str(detail.get("status") or "status unknown"),
            "usable" if detail.get("usable") else "not usable",
            "enabled" if detail.get("effective_enabled", detail.get("enabled", True)) else "disabled",
        ]
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
        return state.device_details.get(self._device_key, {})


class ZeroNetExportDeviceStatusSensor(ZeroNetExportEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_status", f"{device_name} status")
        self._device_key = device_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get("status")

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})


class ZeroNetExportDevicePlanSensor(ZeroNetExportEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_planned_action", f"{device_name} planned action")
        self._device_key = device_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get("planned_action")

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})


class ZeroNetExportDeviceGuardSensor(ZeroNetExportEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str):
        super().__init__(coordinator, f"device_{device_key}_guard_status", f"{device_name} guard status")
        self._device_key = device_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get("guard_status")

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})


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
        super().__init__(coordinator, f"device_{device_key}_{value_key}", f"{device_name} {suffix}")
        self._device_key = device_key
        self._value_key = value_key
        self._attr_entity_category = entity_category

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get(self._value_key)

    @property
    def native_unit_of_measurement(self):
        return UnitOfPower.WATT

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})


class ZeroNetExportDeviceDurationSensor(ZeroNetExportEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", f"{device_name} {suffix}")
        self._device_key = device_key
        self._value_key = value_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get(self._value_key)

    @property
    def native_unit_of_measurement(self):
        return UnitOfTime.SECONDS

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})


class ZeroNetExportDeviceTimestampSensor(ZeroNetExportEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", f"{device_name} {suffix}")
        self._device_key = device_key
        self._value_key = value_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get(self._value_key)

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})


class ZeroNetExportDeviceDetailSensor(ZeroNetExportEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_key: str, device_name: str, value_key: str, suffix: str):
        super().__init__(coordinator, f"device_{device_key}_{value_key}", f"{device_name} {suffix}")
        self._device_key = device_key
        self._value_key = value_key

    @property
    def native_value(self):
        state = self._state
        if state is None:
            return None
        return state.device_details.get(self._device_key, {}).get(self._value_key)

    @property
    def extra_state_attributes(self):
        state = self._state
        if state is None:
            return {}
        return state.device_details.get(self._device_key, {})
