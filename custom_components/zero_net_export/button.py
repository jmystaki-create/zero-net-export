"""Buttons for Zero Net Export."""
from __future__ import annotations

from homeassistant.components import persistent_notification
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .candidate_utils import (
    assess_candidate,
    build_candidate_overview_summary,
    build_candidate_preview,
    build_candidate_review_hint,
    candidate_needs_review,
    discover_candidate_devices,
    first_review_candidate,
)
from .const import DOMAIN
from .device_model import DEVICE_KIND_FIXED, DEVICE_KIND_VARIABLE
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


def _compact_reason_fragment(detail: dict) -> str:
    if _has_active_plan(detail):
        reason = str(detail.get("planned_action_reason") or "").strip()
    elif detail.get("usable") is False:
        reason = str(detail.get("reason") or "").strip()
    else:
        reason = ""
    if not reason or reason.lower().startswith("no "):
        return ""
    normalized = " ".join(reason.split()).strip().rstrip(". ")
    if len(normalized) > 72:
        normalized = normalized[:69].rstrip() + "..."
    return normalized


def _compact_last_result_fragment(detail: dict) -> str:
    last_action_status = str(detail.get("last_action_status") or "").strip().lower()
    if not last_action_status or last_action_status in {"ok", "applied", "success"}:
        return ""
    message = str(detail.get("last_action_result_message") or "").strip()
    if not message or message.lower().startswith("no recent"):
        return ""
    normalized = " ".join(message.split()).strip().rstrip(". ")
    if len(normalized) > 72:
        normalized = normalized[:69].rstrip() + "..."
    return normalized


def _compact_guard_reason_fragment(detail: dict) -> str:
    guard_reason = str(detail.get("guard_reason") or "").strip()
    if not guard_reason or guard_reason.lower().startswith("no action is currently planned"):
        return ""
    normalized = " ".join(guard_reason.split()).strip().rstrip(". ")
    if len(normalized) > 72:
        normalized = normalized[:69].rstrip() + "..."
    return normalized


def _device_has_blocked_activity(detail: dict) -> bool:
    planned_action = str(detail.get("planned_action") or "").strip().lower()
    if detail.get("usable") is False:
        return True
    return planned_action not in {"", "hold"} and detail.get("action_executable") is False


def _format_device_review_line(detail: dict, *, audit: bool = False) -> str:
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
    nominal_power = detail.get("nominal_power_w")
    if audit and nominal_power is not None:
        runtime_bits.append(f"nominal {_format_power(nominal_power)}")
    current_runtime = detail.get("current_active_seconds")
    if current_runtime not in (None, 0, 0.0):
        runtime_bits.append(f"runtime {_format_duration(current_runtime)}")
    runtime_today = detail.get("active_runtime_today_seconds")
    if runtime_today not in (None, 0, 0.0):
        runtime_bits.append(f"today {_format_duration(runtime_today)}")
    runtime_bits.append(f"guard {detail.get('guard_status') or 'unknown'}")
    runtime_bits.append(f"action {detail.get('planned_action') or 'hold'}")
    reason_fragment = _compact_reason_fragment(detail)
    if reason_fragment:
        runtime_bits.append(f"why {reason_fragment}")
    guard_reason_fragment = _compact_guard_reason_fragment(detail)
    if guard_reason_fragment and _device_has_blocked_activity(detail):
        runtime_bits.append(f"guard why {guard_reason_fragment}")
    last_action_status = str(detail.get("last_action_status") or "").strip()
    if last_action_status and last_action_status not in {"ok", "applied", "success"}:
        runtime_bits.append(f"last {last_action_status}")
    if audit:
        last_requested_power = detail.get("last_requested_power_w")
        if last_requested_power is not None:
            runtime_bits.append(f"last req {_format_power(last_requested_power)}")
        last_applied_power = detail.get("last_applied_power_w")
        if last_applied_power is not None:
            runtime_bits.append(f"last applied {_format_power(last_applied_power)}")
        result_fragment = _compact_last_result_fragment(detail)
        if result_fragment:
            runtime_bits.append(f"result {result_fragment}")
        success_count = int(detail.get("successful_action_count") or 0)
        failure_count = int(detail.get("failed_action_count") or 0)
        if success_count or failure_count:
            runtime_bits.append(f"runs {success_count} ok/{failure_count} fail")
        last_action_age = detail.get("last_action_seconds_ago")
        if last_action_age not in (None, 0, 0.0):
            runtime_bits.append(f"last act {_format_duration(last_action_age)} ago")
        last_applied_at = detail.get("last_applied_at")
        if last_applied_at is not None:
            runtime_bits.append(f"last applied at {_format_timestamp(last_applied_at)}")
    device_label = str(detail.get("name") or detail.get("entity_id") or "managed device")
    return f"- {device_label}: {' | '.join(runtime_bits)}"


def _device_needs_review_attention(detail: dict) -> bool:
    if _device_has_blocked_activity(detail) or _has_active_plan(detail):
        return True
    last_action_status = str(detail.get("last_action_status") or "").strip().lower()
    return bool(last_action_status and last_action_status not in {"ok", "applied", "success"})


def _device_has_recent_attention(detail: dict) -> bool:
    last_action_status = str(detail.get("last_action_status") or "").strip().lower()
    return bool(last_action_status and last_action_status not in {"ok", "applied", "success"})


def _device_review_sort_key(detail: dict) -> tuple[int, int, int, int, int, str]:
    effective_enabled = bool(detail.get("effective_enabled", detail.get("enabled", True)))
    usable = detail.get("usable")
    blocked_rank = 0 if _device_has_blocked_activity(detail) else 1
    planned_rank = 0 if _has_active_plan(detail) else 1
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


def _sorted_review_devices(device_details: list[dict]) -> list[dict]:
    return sorted(device_details, key=_device_review_sort_key)


def _partition_review_devices(device_details: list[dict]) -> tuple[list[dict], list[dict]]:
    ordered = _sorted_review_devices(device_details)
    attention = [detail for detail in ordered if _device_needs_review_attention(detail)]
    remaining = [detail for detail in ordered if not _device_needs_review_attention(detail)]
    return attention, remaining


def _first_review_attention_device_name(device_details: list[dict]) -> str:
    return _first_matching_device_name(device_details, predicate=_device_needs_review_attention)


def _first_matching_device_name(device_details: list[dict], *, predicate) -> str:
    for detail in _sorted_review_devices(device_details):
        if predicate(detail):
            return str(detail.get("name") or detail.get("entity_id") or "").strip()
    return ""


def _device_matches(detail: dict, target: dict) -> bool:
    detail_entity_id = str(detail.get("entity_id") or "").strip()
    target_entity_id = str(target.get("entity_id") or "").strip()
    if detail_entity_id and target_entity_id and detail_entity_id == target_entity_id:
        return True
    detail_name = str(detail.get("name") or "").strip()
    target_name = str(target.get("name") or "").strip()
    return bool(detail_name and target_name and detail_name == target_name)


def _device_bucket_position(device_details: list[dict], target: dict) -> int | None:
    for index, detail in enumerate(_sorted_review_devices(device_details), start=1):
        if _device_matches(detail, target):
            return index
    return None


def _next_bucket_device_name(device_details: list[dict], target: dict) -> str:
    found_target = False
    for detail in _sorted_review_devices(device_details):
        if found_target:
            return str(detail.get("name") or detail.get("entity_id") or "managed device").strip()
        if _device_matches(detail, target):
            found_target = True
    return ""


def _managed_entity_ids(state) -> set[str]:
    return {
        str(detail.get("entity_id"))
        for detail in (getattr(state, "device_details", None) or {}).values()
        if detail.get("entity_id")
    }


def _candidate_devices_for_state(coordinator, hass, state) -> list[dict[str, str]]:
    if hass is None:
        return []
    managed_entity_ids = _managed_entity_ids(state)
    cache_key = (id(state), tuple(sorted(managed_entity_ids)))
    cached = getattr(coordinator, "_zne_candidate_button_cache", None)
    if cached and cached.get("key") == cache_key:
        return cached["candidates"]
    candidates = discover_candidate_devices(hass.states.async_all(), managed_entity_ids)
    setattr(
        coordinator,
        "_zne_candidate_button_cache",
        {
            "key": cache_key,
            "candidates": candidates,
        },
    )
    return candidates


def _managed_snapshot_summary(device_details: list[dict], *, include_planned_count: bool = False) -> str:
    managed_count = len(device_details)
    enabled_count = sum(
        1 for detail in device_details if detail.get("effective_enabled", detail.get("enabled", True))
    )
    usable_count = sum(1 for detail in device_details if detail.get("usable") is True)
    planned_count = sum(1 for detail in device_details if _has_active_plan(detail))
    attention_count = sum(1 for detail in device_details if _device_needs_review_attention(detail))
    active_devices = [detail for detail in device_details if detail.get("observed_active") is True]
    active_count = len(active_devices)
    active_power = round(sum(float(detail.get("current_power_w", 0) or 0) for detail in active_devices), 1)
    fixed_count = sum(1 for detail in device_details if detail.get("kind") == DEVICE_KIND_FIXED)
    variable_count = sum(1 for detail in device_details if detail.get("kind") == DEVICE_KIND_VARIABLE)
    nominal_power = int(sum(float(detail.get("nominal_power_w", 0) or 0) for detail in device_details))
    kind_known = any(detail.get("kind") in {DEVICE_KIND_FIXED, DEVICE_KIND_VARIABLE} for detail in device_details)
    first_attention_name = _first_matching_device_name(
        device_details,
        predicate=_device_needs_review_attention,
    )
    first_blocked_name = _first_matching_device_name(
        device_details,
        predicate=_device_has_blocked_activity,
    )
    first_planned_name = _first_matching_device_name(
        device_details,
        predicate=_has_active_plan,
    )
    parts = [f"{managed_count} managed", f"{enabled_count} enabled", f"{usable_count} usable"]
    if active_count:
        parts.append(f"active load {active_power:g} W")
        parts.append("1 active managed device" if active_count == 1 else f"{active_count} active managed devices")
    if attention_count:
        parts.append(
            "1 managed device needs attention"
            if attention_count == 1
            else f"{attention_count} managed devices need attention"
        )
        if first_attention_name:
            parts.append(f"attention first {first_attention_name}")
    if kind_known:
        parts.append(f"{fixed_count} fixed managed")
        if variable_count:
            parts.append(f"{variable_count} variable managed")
        parts.append(f"{nominal_power} W nominal")
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

    review_candidate = first_review_candidate(candidates)
    review_name = str((review_candidate or {}).get("name") or (review_candidate or {}).get("entity_id") or "").strip()
    parts = overview.split(" | ")

    top_preview = build_candidate_preview(candidates[0], include_entity_id=False, include_state=False)
    _, separator, preview_tail = top_preview.partition(" | ")
    if review_name and preview_tail.startswith(("review first", "review carefully")):
        if not any(part.endswith("needs review") or part.endswith("need review") for part in parts):
            top_index = next((index for index, part in enumerate(parts) if part.startswith(("surfaced ", "top ", "review "))), len(parts))
            parts.insert(top_index, "1 needs review")
            review_kind = str((review_candidate or {}).get("kind") or "").strip()
            if review_kind in {"fixed", "variable"}:
                parts.insert(top_index + 1, f"1 {review_kind} review")
        candidate_labels = [f"surfaced {review_name}", f"top {review_name}"]
        existing_label = next((label for label in candidate_labels if label in parts), None)
        if existing_label:
            if f"review {review_name}" in parts:
                parts.remove(existing_label)
            else:
                parts[parts.index(existing_label)] = f"review {review_name}"
        elif f"review {review_name}" not in parts:
            top_index = next((index for index, part in enumerate(parts) if part.startswith(("surfaced ", "top "))), len(parts))
            parts.insert(top_index, f"review {review_name}")
    if separator and preview_tail and preview_tail not in " | ".join(parts):
        preview_summary = " | ".join([*parts, preview_tail])
        if len(preview_summary) > 220:
            top_hint = build_candidate_review_hint(candidates[0], max_warning_chars=32)
            if " | warn " in top_hint:
                preview_tail = top_hint.replace(" | warn ", " | key warning: ")
        parts.append(preview_tail)

    ready_candidate = next(
        (item for item in candidates if not candidate_needs_review(assess_candidate(item))),
        None,
    )
    ready_name = str((ready_candidate or {}).get("name") or (ready_candidate or {}).get("entity_id") or "").strip()
    if (
        review_candidate
        and ready_candidate
        and ready_candidate is not candidates[0]
        and ready_name
        and f"ready {ready_name}" not in parts
    ):
        ready_parts = [f"ready {ready_name}"]
        ready_hint = build_candidate_review_hint(ready_candidate, include_warning=False)
        if ready_hint:
            ready_parts.append(ready_hint)
        while ready_parts:
            candidate_summary = " | ".join([*parts, *ready_parts])
            if len(candidate_summary) <= 240:
                return candidate_summary
            ready_parts.pop()
        trimmed_parts = list(parts)
        removable_prefixes = (
            "1 fixed review",
            "1 variable review",
            "2 fixed review",
            "2 variable review",
            "3 fixed review",
            "3 variable review",
        )
        while trimmed_parts:
            candidate_summary = " | ".join([*trimmed_parts, f"ready {ready_name}"])
            if len(candidate_summary) <= 240:
                return candidate_summary
            removable_index = next(
                (index for index, part in enumerate(trimmed_parts) if part.startswith(removable_prefixes)),
                -1,
            )
            if removable_index == -1:
                break
            trimmed_parts.pop(removable_index)

    summary = " | ".join(parts)
    if len(summary) <= 240:
        return summary
    return summary[:239].rstrip() + "…"


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


def _format_duration(seconds: object) -> str:
    if seconds is None:
        return "n/a"
    try:
        total_seconds = int(round(float(seconds)))
    except (TypeError, ValueError):
        return str(seconds)
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


def _format_timestamp(value: object) -> str:
    if value is None:
        return "n/a"
    try:
        iso_value = value.isoformat()
    except AttributeError:
        iso_value = str(value)
    return iso_value.replace("+00:00", "Z")


def _managed_devices_post_blocker_step(
    command_center: dict,
    candidates: list[dict] | None,
    *,
    has_managed_devices: bool,
) -> str:
    next_step = str(command_center.get("device_next_step") or command_center.get("next_action_summary") or "").strip()
    recommended_path = str(command_center.get("recommended_path") or "").strip()
    blocker_owned_paths = (SOURCES_CONFIGURE_PATH, POLICY_CONFIGURE_PATH, SUPPORT_CONFIGURE_PATH)

    if next_step and not (
        (recommended_path and recommended_path in next_step)
        or any(path in next_step for path in blocker_owned_paths)
    ):
        return next_step

    top_candidate, _, review_candidate, _ = _managed_devices_review_focus(candidates)
    primary_candidate = review_candidate or top_candidate
    if primary_candidate:
        return (
            f"Open {DEVICES_CONFIGURE_PATH} and review "
            f"{build_candidate_preview(primary_candidate, include_entity_id=False, include_state=False)} first."
        )
    if has_managed_devices:
        return f"Open {DEVICES_CONFIGURE_PATH} and review the current managed fleet."
    return f"Open {DEVICES_CONFIGURE_PATH} and check for the next unmanaged promotion candidate."



def _managed_devices_blocker_first_lines(
    command_center: dict,
    candidates: list[dict] | None,
    *,
    has_managed_devices: bool,
) -> list[str]:
    recommended_section = str(command_center.get("recommended_section") or "").strip()
    recommended_path = str(command_center.get("recommended_path") or "").strip()
    recommended_reason = str(command_center.get("recommended_reason") or "").strip()
    next_step = _managed_devices_post_blocker_step(
        command_center,
        candidates,
        has_managed_devices=has_managed_devices,
    )

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


def _managed_devices_review_focus(candidates: list[dict] | None) -> tuple[dict | None, dict | None, dict | None, dict | None]:
    candidate_list = candidates or []
    top_candidate = candidate_list[0] if candidate_list else None
    review_candidate = first_review_candidate(candidate_list)
    return (
        top_candidate,
        assess_candidate(top_candidate) if top_candidate else None,
        review_candidate,
        assess_candidate(review_candidate) if review_candidate else None,
    )


def _first_ready_candidate(candidates: list[dict] | None) -> dict | None:
    return next(
        (
            item
            for item in (candidates or [])
            if not candidate_needs_review(assess_candidate(item))
        ),
        None,
    )


def _managed_devices_workspace_handoff(
    command_center: dict,
    candidates: list[dict] | None,
    *,
    has_managed_devices: bool,
) -> list[str]:
    recommended_section = str(command_center.get("recommended_section") or "").strip()
    recommended_path = str(command_center.get("recommended_path") or "").strip()
    recommended_reason = str(command_center.get("recommended_reason") or "").strip()
    next_step = _managed_devices_post_blocker_step(
        command_center,
        candidates,
        has_managed_devices=has_managed_devices,
    )

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

    top_candidate, _, review_candidate, _ = _managed_devices_review_focus(candidates)
    primary_candidate = review_candidate or top_candidate

    lines = ["Promotion handoff:"]
    if primary_candidate:
        top_add_label = "fixed load device" if primary_candidate["kind"] == "fixed" else "variable load device"
        lines.extend(
            [
                f"- Open {DEVICES_CONFIGURE_PATH} in Configure as the primary Managed Devices workspace.",
                f"- Choose Add {top_add_label}.",
                f"- In Pick unmanaged candidate, select {build_candidate_preview(primary_candidate, include_entity_id=False, include_state=False)}.",
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
    ordered_devices: list[dict],
    candidates: list[dict] | None,
    top_candidate: dict | None,
    review_candidate: dict | None,
    review_candidate_fit: dict | None,
    ready_candidate_fit: dict | None,
) -> list[str]:
    entity_id = str(detail.get("entity_id") or "unknown entity")
    device_label = str(detail.get("name") or entity_id)
    blocker_first_lines = _managed_devices_blocker_first_lines(
        command_center,
        candidates,
        has_managed_devices=bool(managed_snapshot and not managed_snapshot.startswith("0 managed")),
    )
    attention_devices, remaining_devices = _partition_review_devices(ordered_devices)
    device_is_attention = any(
        candidate.get("entity_id") == entity_id or candidate.get("name") == device_label
        for candidate in attention_devices
    )
    ready_candidate = _first_ready_candidate(candidates)
    peer_attention_details = [
        candidate
        for candidate in attention_devices
        if (candidate.get("entity_id") or candidate.get("name")) not in {entity_id, device_label}
    ]
    peer_steady_details = [
        candidate
        for candidate in remaining_devices
        if (candidate.get("entity_id") or candidate.get("name")) not in {entity_id, device_label}
    ]
    peer_attention_devices = [
        str(candidate.get("name") or candidate.get("entity_id") or "managed device")
        for candidate in peer_attention_details
    ]
    peer_steady_devices = [
        str(candidate.get("name") or candidate.get("entity_id") or "managed device")
        for candidate in peer_steady_details
    ]
    current_bucket = attention_devices if device_is_attention else remaining_devices
    current_bucket_label = "attention-first" if device_is_attention else "steady"
    current_bucket_position = _device_bucket_position(current_bucket, detail)
    next_bucket_device = _next_bucket_device_name(current_bucket, detail)
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
    if detail.get("current_active_seconds") is not None:
        control_profile_lines.append(
            f"- Active runtime now: {_format_duration(detail.get('current_active_seconds'))}"
        )
    if detail.get("active_runtime_today_seconds") is not None:
        control_profile_lines.append(
            f"- Active runtime today: {_format_duration(detail.get('active_runtime_today_seconds'))}"
        )

    lines = [
        "Zero Net Export managed-device detail review",
        "",
        f"Primary Managed Devices workspace in Configure: {DEVICES_CONFIGURE_PATH}",
        f"Secondary device-page audit path: {DETAILED_MANAGEMENT_PATH}",
        f"Recommended next step: {command_center.get('device_next_step') or command_center.get('next_action_summary') or 'Review the current fleet state.'}",
        *(["", *blocker_first_lines] if blocker_first_lines else []),
        "",
        "Managed devices workspace context:",
        f"- Managed snapshot: {managed_snapshot}",
        f"- Unmanaged snapshot: {unmanaged_snapshot}",
        (
            f"- Currently surfaced unmanaged candidate: {build_candidate_preview(top_candidate, include_entity_id=False)}"
            if top_candidate
            else "- Currently surfaced unmanaged candidate: none"
        ),
        *(
            [
                f"- First review-first unmanaged candidate: {build_candidate_preview(review_candidate, include_entity_id=False, include_state=False)}",
                "- First review-first unmanaged usefulness: " + _candidate_usefulness_summary(review_candidate),
                "- First review-first unmanaged warnings: "
                + (
                    "; ".join(review_candidate_fit.get("warnings") or [])
                    if review_candidate_fit and review_candidate_fit.get("warnings")
                    else "No immediate warnings."
                ),
            ]
            if review_candidate and review_candidate != top_candidate
            else []
        ),
        *(
            [
                f"- Ready-next unmanaged candidate: {build_candidate_preview(ready_candidate, include_entity_id=False, include_state=False)}",
                "- Ready-next unmanaged usefulness: " + _candidate_usefulness_summary(ready_candidate),
                "- Ready-next unmanaged warnings: "
                + (
                    "; ".join(ready_candidate_fit.get("warnings") or [])
                    if ready_candidate_fit and ready_candidate_fit.get("warnings")
                    else "No immediate warnings."
                ),
            ]
            if review_candidate and ready_candidate and ready_candidate is not review_candidate
            else []
        ),
        "",
        "Fleet attention context:",
        (
            "- This device is currently in the attention-first review bucket."
            if device_is_attention
            else "- This device is currently in the steady managed-device bucket."
        ),
        (
            f"- First managed device needing attention: {_first_review_attention_device_name(ordered_devices)}"
            if attention_devices
            else "- First managed device needing attention: none"
        ),
        (
            "- Other managed devices needing attention: " + ", ".join(peer_attention_devices[:5])
            if peer_attention_devices
            else "- Other managed devices needing attention: none"
        ),
        (
            "- Other steady managed devices: " + ", ".join(peer_steady_devices[:5])
            if peer_steady_devices
            else "- Other steady managed devices: none"
        ),
        *(
            [
                "",
                "Other attention-device audit preview:",
                *[_format_device_review_line(candidate, audit=True) for candidate in peer_attention_details[:3]],
            ]
            if peer_attention_details
            else []
        ),
        *(
            [
                "",
                "Other steady-device audit preview:",
                *[_format_device_review_line(candidate, audit=True) for candidate in peer_steady_details[:3]],
            ]
            if peer_steady_details
            else []
        ),
        "",
        "Current device audit snapshot:",
        _format_device_review_line(detail, audit=True),
        "",
        "Review-order context:",
        (
            f"- This device is #{current_bucket_position} in the {current_bucket_label} review bucket."
            if current_bucket_position is not None
            else f"- This device is currently grouped into the {current_bucket_label} review bucket."
        ),
        f"- {current_bucket_label.capitalize()} bucket size: {len(current_bucket)}",
        (
            f"- Next device in this review bucket: {next_bucket_device}"
            if next_bucket_device
            else "- Next device in this review bucket: none"
        ),
        "",
        f"Device: {device_label}",
        f"Kind: {kind}",
        f"Runtime status: {detail.get('status') or 'status unknown'}",
        f"Guard state: {detail.get('guard_status') or 'unknown'}",
        f"Guard reason: {detail.get('guard_reason') or 'No current guard constraint recorded.'}",
        f"Blocked by: {detail.get('blocked_by') or 'none'}",
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
        f"- Last action at: {_format_timestamp(detail.get('last_action_at'))}",
        f"- Last action age: {_format_duration(detail.get('last_action_seconds_ago'))}",
        f"- Last action result: {detail.get('last_action_result_message') or 'No recent action result recorded.'}",
        f"- Last requested power: {_format_power(detail.get('last_requested_power_w'))}",
        f"- Last applied power: {_format_power(detail.get('last_applied_power_w'))}",
        f"- Last applied at: {_format_timestamp(detail.get('last_applied_at'))}",
        f"- Success count: {int(detail.get('successful_action_count') or 0)}",
        f"- Failure count: {int(detail.get('failed_action_count') or 0)}",
        "",
        "Next native actions:",
        f"- Return to {DEVICES_CONFIGURE_PATH} in Configure as the primary Managed Devices workspace for edits, enablement, promotion, or removal.",
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
        candidates = _candidate_devices_for_state(self.coordinator, self.hass, state)
        top_candidate, top_candidate_fit, review_candidate, review_candidate_fit = _managed_devices_review_focus(candidates)
        ready_candidate = _first_ready_candidate(candidates)
        ready_candidate_fit = assess_candidate(ready_candidate) if ready_candidate else None
        command_center = build_native_command_center_summary(self.coordinator)
        attention_devices, remaining_devices = _partition_review_devices(ordered)
        return {
            'configure_path': DEVICES_CONFIGURE_PATH,
            'detailed_management_path': DETAILED_MANAGEMENT_PATH,
            'recommended_section': command_center.get('recommended_section'),
            'recommended_path': command_center.get('recommended_path'),
            'recommended_reason': command_center.get('recommended_reason'),
            'blocker_first': "\n".join(
                _managed_devices_blocker_first_lines(
                    command_center,
                    candidates,
                    has_managed_devices=bool(managed),
                )
            ),
            'managed_count': len(managed),
            'enabled_count': sum(
                1 for detail in managed if detail.get('effective_enabled', detail.get('enabled', True))
            ),
            'usable_count': sum(1 for detail in managed if detail.get('usable') is True),
            'attention_count': len(attention_devices),
            'first_attention_device': _first_review_attention_device_name(ordered),
            'first_blocked_device': _first_matching_device_name(
                ordered,
                predicate=_device_has_blocked_activity,
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
            'first_review_candidate': review_candidate,
            'first_review_candidate_fit': review_candidate_fit,
            'ready_next_candidate': ready_candidate,
            'ready_next_candidate_fit': ready_candidate_fit,
            'next_step': command_center.get('device_next_step') or command_center.get('next_action_summary'),
            'attention_devices': attention_devices[:12],
            'steady_devices': remaining_devices[:12],
            'devices': ordered[:12],
            'promotion_handoff': "\n".join(
                _managed_devices_workspace_handoff(
                    command_center,
                    candidates,
                    has_managed_devices=bool(managed),
                )
            ),
        }

    async def async_press(self) -> None:
        state = self._state
        managed = list((state.device_details or {}).values()) if state is not None else []
        ordered = sorted(managed, key=_device_runtime_sort_key)
        candidates = _candidate_devices_for_state(self.coordinator, self.hass, state)
        top_candidate, top_candidate_fit, review_candidate, review_candidate_fit = _managed_devices_review_focus(candidates)
        ready_candidate = _first_ready_candidate(candidates)
        ready_candidate_fit = assess_candidate(ready_candidate) if ready_candidate else None
        command_center = build_native_command_center_summary(self.coordinator)
        attention_devices, remaining_devices = _partition_review_devices(ordered)
        blocker_first_lines = _managed_devices_blocker_first_lines(
            command_center,
            candidates,
            has_managed_devices=bool(ordered),
        )
        lines = [
            'Zero Net Export managed devices workspace',
            '',
            f'Primary Managed Devices workspace in Configure: {DEVICES_CONFIGURE_PATH}',
            f'Secondary device-page review path: {DETAILED_MANAGEMENT_PATH}',
            f"Recommended next step: {command_center.get('device_next_step') or command_center.get('next_action_summary') or 'Review the current fleet state.'}",
            *(['', *blocker_first_lines] if blocker_first_lines else []),
            '',
            'Managed devices (top section):',
            f"- Snapshot: {_managed_snapshot_summary(ordered)}",
            'Managed devices needing attention first:',
            *(
                [_format_device_review_line(detail) for detail in attention_devices[:12]]
                or ['- No blocked, active-plan, or recent-failure managed devices right now.']
            ),
            '',
            'Other managed devices:',
            *(
                [_format_device_review_line(detail) for detail in remaining_devices[:12]]
                or ['- No additional steady managed devices right now.']
            ),
            '',
            'Unmanaged candidates (bottom section):',
            f"- Snapshot: {_unmanaged_snapshot_summary(candidates)}",
            (
                f"- Currently surfaced candidate usefulness: {_candidate_usefulness_summary(top_candidate)}"
                if top_candidate_fit
                else '- Currently surfaced candidate usefulness: No unmanaged candidate guidance available right now.'
            ),
            (
                '- Currently surfaced candidate warnings: '
                + (
                    '; '.join(top_candidate_fit.get('warnings') or [])
                    if top_candidate_fit and top_candidate_fit.get('warnings')
                    else 'No immediate warnings.'
                )
            ),
            *(
                [
                    f"- First review-first candidate: {build_candidate_preview(review_candidate, include_entity_id=False, include_state=False)}",
                    f"- First review-first candidate usefulness: {_candidate_usefulness_summary(review_candidate)}",
                    '- First review-first candidate warnings: '
                    + (
                        '; '.join(review_candidate_fit.get('warnings') or [])
                        if review_candidate_fit and review_candidate_fit.get('warnings')
                        else 'No immediate warnings.'
                    ),
                ]
                if review_candidate and review_candidate != top_candidate
                else []
            ),
            *(
                [
                    f"- Ready-next candidate: {build_candidate_preview(ready_candidate, include_entity_id=False, include_state=False)}",
                    f"- Ready-next candidate usefulness: {_candidate_usefulness_summary(ready_candidate)}",
                    '- Ready-next candidate warnings: '
                    + (
                        '; '.join(ready_candidate_fit.get('warnings') or [])
                        if ready_candidate_fit and ready_candidate_fit.get('warnings')
                        else 'No immediate warnings.'
                    ),
                ]
                if review_candidate and ready_candidate and ready_candidate is not review_candidate
                else []
            ),
            'Currently surfaced unmanaged candidates:',
            *(
                [
                    f"- {build_candidate_preview(item, include_entity_id=False, include_state=False)}"
                    for item in candidates[:6]
                ]
                or ['- No unmanaged candidate devices discovered right now.']
            ),
            '',
            *_managed_devices_workspace_handoff(
                command_center,
                candidates,
                has_managed_devices=bool(ordered),
            ),
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
        return _candidate_devices_for_state(self.coordinator, self.hass, self._state)

    @property
    def extra_state_attributes(self):
        state = self._state
        device_details = list((state.device_details or {}).values()) if state is not None else []
        ordered = sorted(device_details, key=_device_runtime_sort_key)
        candidates = self._unmanaged_candidates()
        top_candidate, top_candidate_fit, review_candidate, review_candidate_fit = _managed_devices_review_focus(candidates)
        ready_candidate = _first_ready_candidate(candidates)
        ready_candidate_fit = assess_candidate(ready_candidate) if ready_candidate else None
        command_center = build_native_command_center_summary(self.coordinator)
        attention_devices, remaining_devices = _partition_review_devices(ordered)
        return {
            "configure_path": DEVICES_CONFIGURE_PATH,
            "detailed_management_path": DETAILED_MANAGEMENT_PATH,
            "recommended_section": command_center.get("recommended_section"),
            "recommended_path": command_center.get("recommended_path"),
            "recommended_reason": command_center.get("recommended_reason"),
            "blocker_first": "\n".join(
                _managed_devices_blocker_first_lines(
                    command_center,
                    candidates,
                    has_managed_devices=bool(device_details),
                )
            ),
            "managed_count": len(device_details),
            "enabled_count": sum(
                1 for detail in device_details if detail.get("effective_enabled", detail.get("enabled", True))
            ),
            "usable_count": sum(1 for detail in device_details if detail.get("usable") is True),
            "planned_action_count": sum(1 for detail in device_details if _has_active_plan(detail)),
            "blocked_count": sum(1 for detail in device_details if _device_has_blocked_activity(detail)),
            "attention_count": len(attention_devices),
            "first_attention_device": _first_review_attention_device_name(ordered),
            "first_blocked_device": _first_matching_device_name(
                ordered,
                predicate=_device_has_blocked_activity,
            ),
            "first_planned_device": _first_matching_device_name(
                ordered,
                predicate=_has_active_plan,
            ),
            "managed_snapshot": _managed_snapshot_summary(ordered, include_planned_count=True),
            "unmanaged_snapshot": _unmanaged_snapshot_summary(candidates),
            "unmanaged_candidate_count": len(candidates),
            "top_unmanaged_candidate": top_candidate,
            "top_candidate_fit": top_candidate_fit,
            "first_review_candidate": review_candidate,
            "first_review_candidate_fit": review_candidate_fit,
            "ready_next_candidate": ready_candidate,
            "ready_next_candidate_fit": ready_candidate_fit,
            "candidate_devices": candidates[:12],
            "next_step": command_center.get("device_next_step") or command_center.get("next_action_summary"),
            "attention_devices": attention_devices[:12],
            "steady_devices": remaining_devices[:12],
            "devices": ordered[:12],
            "promotion_handoff": "\n".join(
                _managed_devices_workspace_handoff(
                    command_center,
                    candidates,
                    has_managed_devices=bool(device_details),
                )
            ),
        }

    async def async_press(self) -> None:
        state = self._state
        device_details = list((state.device_details or {}).values()) if state is not None else []
        ordered = sorted(device_details, key=_device_runtime_sort_key)
        candidates = self._unmanaged_candidates()
        top_candidate, top_candidate_fit, review_candidate, review_candidate_fit = _managed_devices_review_focus(candidates)
        ready_candidate = _first_ready_candidate(candidates)
        ready_candidate_fit = assess_candidate(ready_candidate) if ready_candidate else None
        command_center = build_native_command_center_summary(self.coordinator)
        blocker_first_lines = _managed_devices_blocker_first_lines(
            command_center,
            candidates,
            has_managed_devices=bool(ordered),
        )
        attention_devices, remaining_devices = _partition_review_devices(ordered)
        lines = [
            "Zero Net Export managed devices review",
            "",
            f"Primary Managed Devices workspace in Configure: {DEVICES_CONFIGURE_PATH}",
            f"Secondary device-page audit path: {DETAILED_MANAGEMENT_PATH}",
            f"Recommended next step: {command_center.get('device_next_step') or command_center.get('next_action_summary') or 'Review the current fleet state.'}",
            *(["", *blocker_first_lines] if blocker_first_lines else []),
            "",
            "Managed devices (top section):",
            f"- Snapshot: {_managed_snapshot_summary(ordered, include_planned_count=True)}",
            f"Unmanaged candidates (bottom section): {_unmanaged_snapshot_summary(candidates)}",
            (
                f"Currently surfaced candidate usefulness: {_candidate_usefulness_summary(top_candidate)}"
                if top_candidate_fit
                else "Currently surfaced candidate usefulness: No unmanaged candidate guidance available right now."
            ),
            (
                "Currently surfaced candidate warnings: "
                + (
                    "; ".join(top_candidate_fit.get("warnings") or [])
                    if top_candidate_fit and top_candidate_fit.get("warnings")
                    else "No immediate warnings."
                )
            ),
            *(
                [
                    f"First review-first candidate: {build_candidate_preview(review_candidate, include_entity_id=False, include_state=False)}",
                    "First review-first candidate usefulness: " + _candidate_usefulness_summary(review_candidate),
                    "First review-first candidate warnings: "
                    + (
                        "; ".join(review_candidate_fit.get("warnings") or [])
                        if review_candidate_fit and review_candidate_fit.get("warnings")
                        else "No immediate warnings."
                    ),
                ]
                if review_candidate and review_candidate != top_candidate
                else []
            ),
            *(
                [
                    f"Ready-next candidate: {build_candidate_preview(ready_candidate, include_entity_id=False, include_state=False)}",
                    "Ready-next candidate usefulness: " + _candidate_usefulness_summary(ready_candidate),
                    "Ready-next candidate warnings: "
                    + (
                        "; ".join(ready_candidate_fit.get("warnings") or [])
                        if ready_candidate_fit and ready_candidate_fit.get("warnings")
                        else "No immediate warnings."
                    ),
                ]
                if review_candidate and ready_candidate and ready_candidate is not review_candidate
                else []
            ),
            "",
            "Managed devices needing attention first:",
            *(
                [_format_device_review_line(detail, audit=True) for detail in attention_devices[:12]]
                or ["- No blocked, active-plan, or recent-failure managed devices right now."]
            ),
            "",
            "Other managed devices:",
            *(
                [_format_device_review_line(detail, audit=True) for detail in remaining_devices[:12]]
                or ["- No additional steady managed devices right now."]
            ),
            "",
            "Currently surfaced unmanaged candidates:",
            *(
                [
                    f"- {build_candidate_preview(item, include_entity_id=False, include_state=False)}"
                    for item in candidates[:6]
                ]
                or ["- No unmanaged candidate devices discovered right now."]
            ),
            "",
            *_managed_devices_workspace_handoff(
                command_center,
                candidates,
                has_managed_devices=bool(ordered),
            ),
            "",
            "Use the per-device Review buttons on the Zero Net Export device page when you need a deeper audit trail for one managed device.",
        ]
        persistent_notification.async_create(
            self.hass,
            "\n".join(lines),
            title=f"{self.coordinator.entry.title}: managed devices review",
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
        candidates = _candidate_devices_for_state(self.coordinator, self.hass, state)
        top_candidate, top_candidate_fit, review_candidate, review_candidate_fit = _managed_devices_review_focus(candidates)
        ready_candidate = _first_ready_candidate(candidates)
        ready_candidate_fit = assess_candidate(ready_candidate) if ready_candidate else None
        command_center = build_native_command_center_summary(self.coordinator)
        return {
            "configure_path": DEVICES_CONFIGURE_PATH,
            "detailed_management_path": DETAILED_MANAGEMENT_PATH,
            "recommended_section": command_center.get("recommended_section"),
            "recommended_path": command_center.get("recommended_path"),
            "recommended_reason": command_center.get("recommended_reason"),
            "blocker_first": "\n".join(
                _managed_devices_blocker_first_lines(
                    command_center,
                    candidates,
                    has_managed_devices=bool(ordered),
                )
            ),
            "managed_snapshot": _managed_snapshot_summary(ordered, include_planned_count=True),
            "unmanaged_snapshot": _unmanaged_snapshot_summary(candidates),
            "top_unmanaged_candidate": top_candidate,
            "top_candidate_fit": top_candidate_fit,
            "first_review_candidate": review_candidate,
            "first_review_candidate_fit": review_candidate_fit,
            "ready_next_candidate": ready_candidate,
            "ready_next_candidate_fit": ready_candidate_fit,
            **detail,
        }

    async def async_press(self) -> None:
        detail = self._detail()
        state = self._state
        managed = list((state.device_details or {}).values()) if state is not None else []
        ordered = sorted(managed, key=_device_runtime_sort_key)
        candidates = _candidate_devices_for_state(self.coordinator, self.hass, state)
        top_candidate, _top_candidate_fit, review_candidate, review_candidate_fit = _managed_devices_review_focus(candidates)
        ready_candidate = _first_ready_candidate(candidates)
        ready_candidate_fit = assess_candidate(ready_candidate) if ready_candidate else None
        command_center = build_native_command_center_summary(self.coordinator)
        persistent_notification.async_create(
            self.hass,
            "\n".join(
                _build_managed_device_detail_lines(
                    detail,
                    command_center=command_center,
                    managed_snapshot=_managed_snapshot_summary(ordered, include_planned_count=True),
                    unmanaged_snapshot=_unmanaged_snapshot_summary(candidates),
                    ordered_devices=ordered,
                    candidates=candidates,
                    top_candidate=top_candidate,
                    review_candidate=review_candidate,
                    review_candidate_fit=review_candidate_fit,
                    ready_candidate_fit=ready_candidate_fit,
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
