"""Native Home Assistant operator support helpers for Zero Net Export."""
from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any

from homeassistant.util import dt as dt_util

from .candidate_utils import (
    assess_candidate,
    build_candidate_compact_preview,
    build_candidate_review_hint,
    candidate_needs_review,
    discover_candidate_devices,
)
from .const import (
    CONF_BATTERY_RESERVE_SOC,
    CONF_BATTERY_CHARGE_POWER_ENTITY,
    CONF_BATTERY_DISCHARGE_POWER_ENTITY,
    CONF_BATTERY_SOC_ENTITY,
    CONF_DEADBAND_W,
    CONF_DEVICE_INVENTORY_JSON,
    CONF_GRID_EXPORT_ENERGY_ENTITY,
    CONF_GRID_EXPORT_POWER_ENTITY,
    CONF_GRID_IMPORT_ENERGY_ENTITY,
    CONF_GRID_IMPORT_POWER_ENTITY,
    CONF_HOME_LOAD_POWER_ENTITY,
    CONF_SOLAR_ENERGY_ENTITY,
    CONF_SOLAR_POWER_ENTITY,
    CONF_TARGET_EXPORT_W,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_DEADBAND_W,
    DEFAULT_TARGET_EXPORT_W,
    INTEGRATION_VERSION,
    MODE_LABELS,
    REQUIRED_SOURCE_KEYS,
    SOURCE_ROLE_LABELS,
)
from .device_model import parse_device_configs
from .release_info import (
    build_install_consistency_summary,
    build_install_fingerprint_summary,
    build_install_provenance,
    build_install_repair_step,
    build_release_info,
)
from .validation import SourceSpec, format_source_binding_label

PRIMARY_CONFIGURE_PATH = "Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure"
INTEGRATION_DEVICE_PATH = (
    "Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device"
)
SOURCES_SECTION_LABEL = "Sensors"
SOURCES_SECTION_ALIASES = {
    "Sensors and source mapping": SOURCES_SECTION_LABEL,
    "Sources and source mapping": SOURCES_SECTION_LABEL,
    "Sources": SOURCES_SECTION_LABEL,
}
DEVICES_SECTION_LABEL = "Managed Devices"
DEVICES_SECTION_ALIASES = {"Managed devices": DEVICES_SECTION_LABEL}
POLICY_SECTION_LABEL = "Controls"
SUPPORT_SECTION_LABEL = "Diagnostics"
SOURCES_CONFIGURE_PATH = f"{PRIMARY_CONFIGURE_PATH} -> {SOURCES_SECTION_LABEL}"
DEVICES_CONFIGURE_PATH = f"{PRIMARY_CONFIGURE_PATH} -> {DEVICES_SECTION_LABEL}"
ADVANCED_DEVICES_CONFIGURE_PATH = f"{DEVICES_CONFIGURE_PATH} -> Advanced JSON editor and recovery"
DETAILED_MANAGEMENT_PATH = (
    f"{INTEGRATION_DEVICE_PATH} -> Review managed devices workspace / Review managed devices / per-device Review buttons"
)
DIAGNOSTICS_DEVICE_ACTIONS_PATH = (
    f"{INTEGRATION_DEVICE_PATH} -> Review diagnostics / Show setup checklist / Review diagnostics snapshot"
)


def _normalize_native_path_text(text: Any) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    replacements = {
        "Open Configure > Sensors": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open Configure > Controls": f"Open {POLICY_CONFIGURE_PATH}",
        "Open Configure > Managed Devices": f"Open {DEVICES_CONFIGURE_PATH}",
        "Open Configure > Diagnostics": f"Open {SUPPORT_CONFIGURE_PATH}",
        "Configure > Sensors": SOURCES_CONFIGURE_PATH,
        "Configure > Controls": POLICY_CONFIGURE_PATH,
        "Configure > Managed Devices": DEVICES_CONFIGURE_PATH,
        "Configure > Diagnostics": SUPPORT_CONFIGURE_PATH,
        "Start in the unmanaged section": f"Review the Managed Devices workspace at {DEVICES_CONFIGURE_PATH}, starting with unmanaged candidates",
        "start in the unmanaged section": f"review the Managed Devices workspace at {DEVICES_CONFIGURE_PATH}, starting with unmanaged candidates",
        "Review the unmanaged section": f"Review the Managed Devices workspace at {DEVICES_CONFIGURE_PATH}, starting with unmanaged candidates",
        "review the unmanaged section": f"review the Managed Devices workspace at {DEVICES_CONFIGURE_PATH}, starting with unmanaged candidates",
        "Review first in the unmanaged section": f"Review the Managed Devices workspace at {DEVICES_CONFIGURE_PATH}, starting with the review-first unmanaged candidate",
        "review first in the unmanaged section": f"review the Managed Devices workspace at {DEVICES_CONFIGURE_PATH}, starting with the review-first unmanaged candidate",
        "Promote next from the unmanaged section": f"Promote the ready unmanaged candidate in the Managed Devices workspace at {DEVICES_CONFIGURE_PATH}",
        "promote next from the unmanaged section": f"promote the ready unmanaged candidate in the Managed Devices workspace at {DEVICES_CONFIGURE_PATH}",
        "Mapped-source blockers": "Source blockers",
        "Mapped-source blocker": "Source blocker",
        "mapped-source blockers": "source blockers",
        "mapped-source blocker": "source blocker",
        "Mapped source blockers": "Source blockers",
        "Mapped source blocker": "Source blocker",
        "mapped source blockers": "source blockers",
        "mapped source blocker": "source blocker",
        "Mapped-source roles": "Source roles",
        "Mapped-source role": "Source role",
        "mapped-source roles": "source roles",
        "mapped-source role": "source role",
        "Mapped source roles": "Source roles",
        "Mapped source role": "Source role",
        "mapped source roles": "source roles",
        "mapped source role": "source role",
        "Mapped-role blockers": "Source blockers",
        "Mapped-role blocker": "Source blocker",
        "mapped-role blockers": "source blockers",
        "mapped-role blocker": "source blocker",
        "Mapped-roles": "Source roles",
        "Mapped-role": "Source role",
        "mapped-roles": "source roles",
        "mapped-role": "source role",
        "Mapped roles": "Source roles",
        "Mapped role": "Source role",
        "mapped roles": "source roles",
        "mapped role": "source role",
        "Mapped sources": "Source roles",
        "Mapped source": "Source role",
        "mapped sources": "source roles",
        "mapped source": "source role",
        "Sensors and source mapping": SOURCES_SECTION_LABEL,
        "Sources and source mapping": SOURCES_SECTION_LABEL,
        "Required source mapping": "Required source roles",
        "required source mapping": "required source roles",
        "Finish source mapping": "Finish source roles",
        "finish source mapping": "finish source roles",
        "Source mappings": "Source roles",
        "Source mapping": "Source roles",
        "source mappings": "source roles",
        "source mapping": "source roles",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def _count_label(count: int, singular: str, plural: str | None = None) -> str:
    noun = singular if count == 1 else (plural or f"{singular}s")
    return f"{count} {noun}"


def _planned_action_count_label(count: int) -> str:
    return _count_label(count, "planned action")


def _blocked_activity_count_label(count: int) -> str:
    return _count_label(count, "blocked managed action")


def _managed_attention_count_label(count: int) -> str:
    return _count_label(count, "managed device needs attention", "managed devices need attention")


def _managed_count_label(count: int) -> str:
    return "no managed yet" if count <= 0 else f"{count} managed"


def _configured_device_count_label(count: int) -> str:
    return _count_label(count, "device")


def _usable_device_count_label(count: int) -> str:
    return _count_label(count, "usable device")


def _repair_issue_count_label(count: int) -> str:
    return _count_label(count, "issue")


def _repair_item_count_label(count: int) -> str:
    return _count_label(count, "item")


SOURCE_BLOCKER_ACTIVE_LABEL = "source blockers active"


def _unmanaged_count_label(count: int) -> str:
    return "no unmanaged candidates" if count <= 0 else f"{count} unmanaged backlog"


def _compact_unmanaged_count_label(count: int) -> str:
    return "no unmanaged candidates" if count <= 0 else f"{count} unmanaged backlog"


def _is_unmanaged_count_part(text: str) -> bool:
    normalized = " ".join(str(text or "").split())
    return normalized == "no unmanaged candidates" or normalized.endswith(" unmanaged") or normalized.endswith(" unmanaged backlog")


def _is_managed_count_part(text: str) -> bool:
    normalized = " ".join(str(text or "").split())
    return normalized == "no managed yet" or normalized.endswith(" managed")


def _matches_count_label(text: str, singular: str, plural: str | None = None) -> bool:
    normalized = " ".join(str(text or "").split())
    if not normalized:
        return False
    singular_label = singular
    plural_label = plural or f"{singular}s"
    return normalized.endswith(f" {singular_label}") or normalized.endswith(f" {plural_label}")


def _count_label_value(text: str, singular: str, plural: str | None = None) -> int | None:
    normalized = " ".join(str(text or "").split())
    if not _matches_count_label(normalized, singular, plural):
        return None
    count_text, _, _ = normalized.partition(" ")
    try:
        return int(count_text)
    except ValueError:
        return None


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


def _prefer_review_ready_over_large_kind_mix(summary: str) -> str:
    normalized = " ".join(str(summary or "").split())
    if len(normalized) > MAX_NATIVE_SENSOR_STATE_CHARS:
        return normalized
    parts = _split_fleet_activity_parts(normalized)
    if not any(part.startswith("review ") for part in parts):
        return normalized
    if not any(part.startswith("ready ") for part in parts):
        return normalized
    if not any(
        (_count_label_value(part, "fixed candidate") or 0) > 5
        or (_count_label_value(part, "variable candidate") or 0) > 5
        for part in parts
    ):
        return normalized
    trimmed_parts = [
        part
        for part in parts
        if not (
            _matches_count_label(part, "fixed candidate")
            or _matches_count_label(part, "variable candidate")
            or part.startswith("fixed backlog ")
            or part.startswith("variable backlog ")
            or _matches_count_label(part, "planned action")
        )
    ]
    trimmed_summary = " | ".join(trimmed_parts)
    if trimmed_summary and len(trimmed_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return trimmed_summary
    return normalized


POLICY_CONFIGURE_PATH = f"{PRIMARY_CONFIGURE_PATH} -> {POLICY_SECTION_LABEL}"
MODE_CONTROL_PATH = f"{INTEGRATION_DEVICE_PATH} -> Mode"
SUPPORT_CONFIGURE_PATH = (
    f"{PRIMARY_CONFIGURE_PATH} -> {SUPPORT_SECTION_LABEL}; device-page diagnostics: "
    f"{DIAGNOSTICS_DEVICE_ACTIONS_PATH}; Settings -> Repairs"
)
MAX_NATIVE_SENSOR_STATE_CHARS = 255

_FLEET_ACTIVITY_COMMA_DELIMITER_RE = re.compile(
    r", (?=(?:"
    r"source blockers active|"
    r"no managed yet|"
    r"no unmanaged candidates|"
    r"\d+ managed\b|"
    r"\d+ unmanaged(?: backlog)?\b|"
    r"enabled \d+|disabled \d+|usable \d+|"
    r"\d+ fixed managed|\d+ variable managed|\d+ W nominal|"
    r"\d+ managed device(?:s)? need(?:s)? attention|"
    r"\d+ blocked managed action(?:s)?|"
    r"\d+ planned action(?:s)?|"
    r"\d+ active managed device(?:s)?|"
    r"\d+ need(?:s)? review|"
    r"\d+ ready to promote|"
    r"attention first |blocked |plan |active load |active device |"
    r"review |ready |surfaced |fixed backlog |variable backlog "
    r"))"
)


def _normalize_fleet_activity_delimiters(summary: str) -> str:
    """Normalize fallback fleet-list separators without splitting preview detail text."""

    normalized = " ".join(str(summary or "").split()).replace("; ", " | ")
    return _FLEET_ACTIVITY_COMMA_DELIMITER_RE.sub(" | ", normalized)


def _truncate_state_summary(text: str, *, fallback: str) -> str:
    normalized = " ".join(str(text).split())
    if len(normalized) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return normalized
    return fallback


def _dedupe_fleet_activity_summary(
    summary: str,
    *,
    suppress_blocked: bool = True,
    suppress_planned: bool = True,
) -> str:
    return " | ".join(
        _dedupe_attention_overlap_parts(
            _split_fleet_activity_parts(summary),
            suppress_blocked=suppress_blocked,
            suppress_planned=suppress_planned,
        )
    )


def _fleet_activity_fallback_from_device_status(device_status: str) -> str:
    normalized = " ".join(str(device_status or "").split())
    if not normalized:
        return "runtime pending | fleet activity waiting"
    if normalized.startswith(f"{DEVICES_SECTION_LABEL}:"):
        normalized = normalized.partition(":")[2].strip()
    normalized = _normalize_fleet_activity_delimiters(normalized.rstrip("."))
    normalized = _dedupe_fleet_activity_summary(normalized)
    compacted = _compact_fleet_activity_overflow_summary(normalized)
    if compacted and len(compacted) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return compacted
    clipped = _clip_state_part(normalized, max_chars=MAX_NATIVE_SENSOR_STATE_CHARS)
    return clipped or "runtime pending | fleet activity waiting"


def format_fleet_activity_for_operator(summary: str) -> str:
    """Make compact fleet state read as managed versus unmanaged in prose surfaces."""

    normalized = _normalize_fleet_activity_delimiters(summary)
    normalized = _dedupe_fleet_activity_summary(normalized)
    if not normalized:
        return "runtime pending | fleet activity waiting"

    parts = []
    for part in _split_fleet_activity_parts(normalized):
        tokens = part.split()
        if len(tokens) == 2 and tokens[0].isdigit() and tokens[1] == "managed" and tokens[0] == "0":
            part = "no managed yet"
        elif len(tokens) == 2 and tokens[0].isdigit() and tokens[1] == "unmanaged":
            part = f"{tokens[0]} unmanaged backlog"
        parts.append(part)
    def _is_managed_inventory_part(part: str) -> bool:
        return bool(
            part.startswith(("enabled ", "disabled ", "usable "))
            or _matches_count_label(part, "fixed managed")
            or _matches_count_label(part, "variable managed")
            or part.endswith(" W nominal")
        )

    def _is_managed_activity_part(part: str) -> bool:
        return bool(
            _is_managed_count_part(part)
            or _is_managed_inventory_part(part)
            or part.startswith(("attention first ", "blocked ", "plan ", "active load ", "active device "))
            or _matches_count_label(part, "managed device needs attention", "managed devices need attention")
            or _matches_count_label(part, "blocked managed action")
            or _matches_count_label(part, "planned action")
            or _matches_count_label(part, "active managed device", "active managed devices")
        )

    unmanaged_index = next(
        (index for index, part in enumerate(parts) if _is_unmanaged_count_part(part)),
        None,
    )
    if unmanaged_index is None:
        return normalized

    managed_index = next(
        (index for index, part in enumerate(parts) if _is_managed_count_part(part)),
        None,
    )
    if managed_index is None:
        return normalized

    if managed_index > unmanaged_index:
        global_problem_parts = [part for part in parts if part == SOURCE_BLOCKER_ACTIVE_LABEL]
        grouping_start = min(managed_index, unmanaged_index)
        prefix_parts = [
            part
            for part in parts[:grouping_start]
            if part and part not in global_problem_parts
        ]
        candidate_parts = [
            part
            for part in parts[grouping_start:]
            if part and part not in global_problem_parts
        ]
        managed_parts = [part for part in candidate_parts if _is_managed_activity_part(part)]
        unmanaged_parts = [part for part in candidate_parts if not _is_managed_activity_part(part)]
        prefix_parts = [*global_problem_parts, *prefix_parts]
        if not managed_parts or not unmanaged_parts:
            return normalized

        unmanaged_label = (
            "Unmanaged candidates" if unmanaged_parts == ["no unmanaged candidates"] else "Unmanaged backlog"
        )
        grouped_summary = f"Managed devices: {' | '.join(managed_parts)}; {unmanaged_label}: {' | '.join(unmanaged_parts)}"
        if prefix_parts:
            return f"{' | '.join(prefix_parts)}; {grouped_summary}"
        return grouped_summary

    global_problem_parts = [part for part in parts if part == SOURCE_BLOCKER_ACTIVE_LABEL]
    prefix_parts = [part for part in parts[:managed_index] if part and part not in global_problem_parts]
    managed_parts = [
        part for part in parts[managed_index:unmanaged_index] if part and part not in global_problem_parts
    ]
    trailing_managed_parts = [
        part for part in parts[unmanaged_index:] if part and part not in global_problem_parts and _is_managed_activity_part(part)
    ]
    unmanaged_parts = [
        part
        for part in parts[unmanaged_index:]
        if part and part not in global_problem_parts and not _is_managed_activity_part(part)
    ]
    managed_parts.extend(part for part in trailing_managed_parts if part not in managed_parts)
    prefix_parts = [*global_problem_parts, *prefix_parts]
    if not managed_parts or not unmanaged_parts:
        return normalized

    unmanaged_label = (
        "Unmanaged candidates" if unmanaged_parts == ["no unmanaged candidates"] else "Unmanaged backlog"
    )
    grouped_summary = f"Managed devices: {' | '.join(managed_parts)}; {unmanaged_label}: {' | '.join(unmanaged_parts)}"
    if prefix_parts:
        return f"{' | '.join(prefix_parts)}; {grouped_summary}"
    return grouped_summary


def _is_fleet_activity_top_level_part(text: str) -> bool:
    normalized = " ".join(str(text or "").split())
    if not normalized:
        return False
    if normalized in {"review first", "review carefully"}:
        return False
    return bool(
        normalized == SOURCE_BLOCKER_ACTIVE_LABEL
        or _is_managed_count_part(normalized)
        or _is_unmanaged_count_part(normalized)
        or normalized.startswith(
            (
                "attention first ",
                "blocked ",
                "plan ",
                "active load ",
                "active device ",
                "review ",
                "ready ",
                "surfaced ",
                "enabled ",
                "disabled ",
                "usable ",
                "fixed backlog ",
                "variable backlog ",
            )
        )
        or _matches_count_label(normalized, "managed device needs attention", "managed devices need attention")
        or _matches_count_label(normalized, "blocked managed action")
        or _matches_count_label(normalized, "needs review", "need review")
        or _matches_count_label(normalized, "ready to promote")
        or _matches_count_label(normalized, "fixed candidate")
        or _matches_count_label(normalized, "variable candidate")
        or _matches_count_label(normalized, "fixed managed")
        or _matches_count_label(normalized, "variable managed")
        or _matches_count_label(normalized, "planned action")
        or _matches_count_label(normalized, "active managed device", "active managed devices")
        or normalized.endswith(" W nominal")
    )


def _split_fleet_activity_parts(summary: str) -> list[str]:
    raw_parts = [part.strip() for part in str(summary or "").split(" | ") if part.strip()]
    if not raw_parts:
        return []

    parts: list[str] = []
    for raw_part in raw_parts:
        if parts and not _is_fleet_activity_top_level_part(raw_part):
            parts[-1] = f"{parts[-1]} | {raw_part}"
        else:
            parts.append(raw_part)
    return parts


def _focus_state_subject(part: str) -> str:
    normalized = " ".join(str(part or "").split())
    prefix = next(
        (
            candidate
            for candidate in ("attention first ", "blocked ", "plan ", "active device ")
            if normalized.startswith(candidate)
        ),
        "",
    )
    if not prefix:
        return ""
    payload = normalized[len(prefix) :].strip()
    if " (" in payload:
        payload = payload.rsplit(" (", 1)[0].strip()
    return payload.casefold()


def _fleet_activity_global_signals_first(parts: list[str]) -> list[str]:
    """Keep fleet-wide blockers outside the managed/unmanaged buckets."""

    global_parts = [part for part in parts if part == SOURCE_BLOCKER_ACTIVE_LABEL]
    if not global_parts:
        return parts
    return [*global_parts, *(part for part in parts if part != SOURCE_BLOCKER_ACTIVE_LABEL)]


def _dedupe_attention_overlap_parts(
    parts: list[str],
    *,
    suppress_blocked: bool = True,
    suppress_planned: bool = True,
) -> list[str]:
    attention_subjects = {
        subject for part in parts if part.startswith("attention first ") if (subject := _focus_state_subject(part))
    }
    if not attention_subjects:
        return parts

    compact_parts: list[str] = []
    suppressed_blocked = False
    suppressed_planned = False
    for part in parts:
        subject = _focus_state_subject(part)
        if suppress_blocked and part.startswith("blocked ") and subject in attention_subjects:
            suppressed_blocked = True
            continue
        if suppress_planned and part.startswith("plan ") and subject in attention_subjects:
            suppressed_planned = True
            continue
        compact_parts.append(part)

    if suppressed_blocked:
        compact_parts = [
            part
            for part in compact_parts
            if _count_label_value(part, "blocked managed action") not in {1}
        ]
    if suppressed_planned:
        compact_parts = [part for part in compact_parts if _count_label_value(part, "planned action") not in {1}]
    return compact_parts


def _compact_fleet_activity_overflow_summary(summary: str) -> str:
    normalized = " ".join(str(summary or "").split())
    if len(normalized) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return normalized

    parts = _fleet_activity_global_signals_first(_split_fleet_activity_parts(normalized))

    managed_part = next((part for part in parts if _is_managed_count_part(part)), "")
    if (
        managed_part
        and managed_part != "no managed yet"
        and any(part.startswith("review ") for part in parts)
        and any(part.startswith("ready ") for part in parts)
        and any(part.startswith(("fixed backlog ", "variable backlog ")) for part in parts)
        and any(
            _matches_count_label(part, "fixed candidate") or _matches_count_label(part, "variable candidate")
            for part in parts
        )
        and SOURCE_BLOCKER_ACTIVE_LABEL not in parts
        and not any(
            part.startswith(("attention first ", "blocked ", "plan ", "active load ", "active device "))
            for part in parts
        )
    ):
        review_story_parts = [
            part
            for part in parts
            if not (
                _matches_count_label(part, "fixed candidate")
                or _matches_count_label(part, "variable candidate")
            )
        ]
        review_story_variants = [review_story_parts]
        for max_chars in (40, 32, 28):
            review_story_variants.append(
                [
                    _clip_review_ready_state_part(part, max_chars=max_chars)
                    if part.startswith(("review ", "ready "))
                    else part
                    for part in review_story_parts
                ]
            )
        for review_story_parts_variant in review_story_variants:
            review_story_summary = " | ".join(review_story_parts_variant)
            if review_story_summary and len(review_story_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
                return review_story_summary

    signal_first_parts = list(parts)
    signal_first_removable_matchers = (
        lambda part: part.endswith(" managed device needs attention") or part.endswith(" managed devices need attention"),
        lambda part: _matches_count_label(part, "blocked managed action"),
        lambda part: _matches_count_label(part, "needs review", "need review"),
        lambda part: _matches_count_label(part, "ready to promote"),
        lambda part: _matches_count_label(part, "fixed candidate") or _matches_count_label(part, "variable candidate"),
        lambda part: part.startswith("fixed backlog ") or part.startswith("variable backlog "),
        lambda part: _matches_count_label(part, "planned action"),
        lambda part: part.startswith(("enabled ", "disabled ", "usable ")) or part.endswith(" W nominal"),
    )
    for matcher in signal_first_removable_matchers:
        if len(" | ".join(signal_first_parts)) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            break
        for index, part in enumerate(list(signal_first_parts)):
            if matcher(part):
                del signal_first_parts[index]
                break

    signal_first_summary = " | ".join(signal_first_parts)
    if signal_first_summary and len(signal_first_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        has_review_ready_story = any(part.startswith(("review ", "ready ")) for part in signal_first_parts)
        has_backlog_mix = any(part.startswith(("fixed backlog ", "variable backlog ")) for part in signal_first_parts)
        has_candidate_inventory = any(
            _matches_count_label(part, "fixed candidate") or _matches_count_label(part, "variable candidate")
            for part in signal_first_parts
        )
        if has_review_ready_story and has_backlog_mix and has_candidate_inventory:
            story_first_parts = [
                part
                for part in signal_first_parts
                if not (
                    _matches_count_label(part, "fixed candidate")
                    or _matches_count_label(part, "variable candidate")
                )
            ]
            story_first_summary = " | ".join(story_first_parts)
            if story_first_summary and len(story_first_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
                return story_first_summary

            story_backlog_parts = [
                part
                for part in story_first_parts
                if not (
                    part.endswith(" managed device needs attention")
                    or part.endswith(" managed devices need attention")
                    or _matches_count_label(part, "blocked managed action")
                    or _matches_count_label(part, "needs review", "need review")
                    or _matches_count_label(part, "ready to promote")
                    or _matches_count_label(part, "active managed device", "active managed devices")
                )
            ]
            story_backlog_tighter_parts = []
            for part in story_backlog_parts:
                if part.startswith(("attention first ", "blocked ", "plan ", "active device ")):
                    story_backlog_tighter_parts.append(_clip_state_part(part, max_chars=26))
                elif part.startswith(("review ", "ready ")):
                    story_backlog_tighter_parts.append(_clip_review_ready_state_part(part, max_chars=24))
                else:
                    story_backlog_tighter_parts.append(part)
            story_backlog_tighter_summary = " | ".join(story_backlog_tighter_parts)
            if story_backlog_tighter_summary and len(story_backlog_tighter_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
                return story_backlog_tighter_summary
        return signal_first_summary

    signal_first_tighter_parts = []
    for part in signal_first_parts:
        if part.startswith(("attention first ", "blocked ", "plan ", "active device ")):
            signal_first_tighter_parts.append(_clip_state_part(part, max_chars=28))
        elif part.startswith(("review ", "ready ")):
            signal_first_tighter_parts.append(_clip_review_ready_state_part(part, max_chars=32))
        else:
            signal_first_tighter_parts.append(part)
    signal_first_tighter_summary = " | ".join(signal_first_tighter_parts)
    if signal_first_tighter_summary and len(signal_first_tighter_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        has_review_ready_story = any(part.startswith(("review ", "ready ")) for part in signal_first_tighter_parts)
        has_backlog_mix = any(part.startswith(("fixed backlog ", "variable backlog ")) for part in signal_first_tighter_parts)
        if has_review_ready_story and has_backlog_mix:
            story_backlog_tighter_parts = [
                part
                for part in signal_first_tighter_parts
                if not (
                    part.endswith(" managed device needs attention")
                    or part.endswith(" managed devices need attention")
                    or _matches_count_label(part, "blocked managed action")
                    or _matches_count_label(part, "needs review", "need review")
                    or _matches_count_label(part, "ready to promote")
                    or _matches_count_label(part, "active managed device", "active managed devices")
                )
            ]
            story_backlog_tighter_summary = " | ".join(story_backlog_tighter_parts)
            if story_backlog_tighter_summary and len(story_backlog_tighter_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
                return story_backlog_tighter_summary
        return signal_first_tighter_summary

    compact_parts = list(parts)
    removable_matchers = (
        lambda part: part.endswith(" managed device needs attention") or part.endswith(" managed devices need attention"),
        lambda part: _matches_count_label(part, "blocked managed action"),
        lambda part: _matches_count_label(part, "needs review", "need review"),
        lambda part: _matches_count_label(part, "ready to promote"),
        lambda part: _matches_count_label(part, "fixed candidate") or _matches_count_label(part, "variable candidate"),
        lambda part: part.startswith("fixed backlog ") or part.startswith("variable backlog "),
        lambda part: _matches_count_label(part, "planned action"),
        lambda part: part.startswith(("enabled ", "disabled ", "usable ")) or part.endswith(" W nominal"),
        lambda part: _matches_count_label(part, "active managed device", "active managed devices"),
    )
    for matcher in removable_matchers:
        if len(" | ".join(compact_parts)) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            break
        for index, part in enumerate(list(compact_parts)):
            if matcher(part):
                del compact_parts[index]
                break

    compact_summary = " | ".join(compact_parts)
    if compact_summary and len(compact_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return compact_summary

    priority_parts: list[str] = []
    managed_part = next((part for part in parts if _is_managed_count_part(part)), "")
    unmanaged_part = next((part for part in parts if _is_unmanaged_count_part(part)), "")
    source_blocker_part = next((part for part in parts if part == SOURCE_BLOCKER_ACTIVE_LABEL), "")
    review_part = next((part for part in parts if part.startswith("review ")), "")
    ready_part = next((part for part in parts if part.startswith("ready ")), "")
    active_count_part = next(
        (
            part
            for part in parts
            if _matches_count_label(part, "active managed device", "active managed devices")
        ),
        "",
    )
    focus_parts = [
        part
        for part in parts
        if part.startswith(("attention first ", "blocked ", "plan ", "active load ", "active device "))
    ]
    prioritized_focus_parts: list[str] = []
    for prefix in ("attention first ", "active device ", "active load ", "blocked ", "plan "):
        focus_part = next((part for part in parts if part.startswith(prefix)), "")
        if focus_part and focus_part not in prioritized_focus_parts:
            prioritized_focus_parts.append(focus_part)
    if not prioritized_focus_parts:
        prioritized_focus_parts = focus_parts[:2]

    if source_blocker_part:
        priority_parts.append(source_blocker_part)
    priority_parts.extend(prioritized_focus_parts[:3])
    if active_count_part and active_count_part not in priority_parts:
        insertion_index = next(
            (
                index + 1
                for index, part in enumerate(priority_parts)
                if part.startswith(("active load ", "active device "))
            ),
            len(priority_parts),
        )
        priority_parts.insert(insertion_index, active_count_part)
    if managed_part:
        priority_parts.append(managed_part)
    if unmanaged_part:
        priority_parts.append(unmanaged_part)
    if review_part:
        priority_parts.append(_clip_review_ready_state_part(review_part, max_chars=36))
    if ready_part:
        priority_parts.append(_clip_review_ready_state_part(ready_part, max_chars=36))

    priority_summary = " | ".join(priority_parts)
    if priority_summary and len(priority_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return priority_summary

    tighter_priority_parts = []
    for part in priority_parts:
        if part.startswith(("attention first ", "blocked ", "plan ", "active device ")):
            tighter_priority_parts.append(_clip_state_part(part, max_chars=30))
        elif part.startswith("active load "):
            tighter_priority_parts.append(part)
        elif part.startswith(("review ", "ready ")):
            tighter_priority_parts.append(_clip_review_ready_state_part(part, max_chars=28))
        else:
            tighter_priority_parts.append(part)
    tighter_priority_summary = " | ".join(tighter_priority_parts)
    if tighter_priority_summary and len(tighter_priority_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return tighter_priority_summary

    return normalized


def _clip_focus_state_part(text: str, *, max_chars: int) -> str | None:
    normalized = " ".join(str(text).split())
    prefixes = ("attention first ", "blocked ", "plan ", "active device ")
    prefix = next((item for item in prefixes if normalized.startswith(item)), "")
    if not prefix:
        return None

    payload = normalized[len(prefix):].strip()
    if not payload:
        return None

    primary_label = payload
    detail_parts: list[str] = []
    if payload.endswith(")") and " (" in payload:
        possible_label, possible_details = payload.rsplit(" (", 1)
        possible_details = possible_details[:-1]
        parsed_detail_parts = [part.strip() for part in possible_details.split("|") if part.strip()]
        if possible_label.strip() and parsed_detail_parts:
            primary_label = possible_label.strip()
            detail_parts = parsed_detail_parts

    kind_detail = next((part for part in detail_parts if part in {"fixed", "variable"}), "")
    state_details = [part for part in detail_parts if part not in {"fixed", "variable"}]
    status_detail = state_details[0] if state_details else ""
    if status_detail == "not usable":
        status_detail = "blocked"

    active_detail = next((part for part in state_details if part.startswith("active")), "")
    compact_status_detail = status_detail
    if status_detail == "blocked":
        compact_status_detail = "block"
    elif status_detail.startswith("active "):
        compact_status_detail = "active"
    elif status_detail.startswith("action "):
        compact_status_detail = status_detail.removeprefix("action ").strip() or status_detail

    compact_active_detail = "active" if active_detail.startswith("active ") else active_detail

    suffix_options: list[str] = []
    if status_detail and active_detail and active_detail != status_detail:
        suffix_options.append(f" ({status_detail} | {active_detail})")
        if compact_active_detail and compact_active_detail != active_detail:
            suffix_options.append(f" ({status_detail} | {compact_active_detail})")
        if compact_status_detail and compact_status_detail != status_detail:
            suffix_options.append(f" ({compact_status_detail} | {compact_active_detail or active_detail})")
        if compact_active_detail:
            suffix_options.append(f" ({compact_active_detail})")
        if kind_detail:
            suffix_options.append(f" ({kind_detail} | {compact_status_detail or status_detail} | {compact_active_detail or active_detail})")
            suffix_options.append(f" ({kind_detail} | {status_detail} | {compact_active_detail or active_detail})")
    if status_detail:
        suffix_options.append(f" ({status_detail})")
        if compact_status_detail and compact_status_detail != status_detail:
            suffix_options.append(f" ({compact_status_detail})")
    if kind_detail and status_detail:
        suffix_options.append(f" ({kind_detail} | {status_detail})")
    if kind_detail:
        suffix_options.append(f" ({kind_detail})")

    seen_suffixes: set[str] = set()
    unique_suffix_options = []
    for suffix in suffix_options:
        if suffix not in seen_suffixes:
            unique_suffix_options.append(suffix)
            seen_suffixes.add(suffix)

    for suffix in unique_suffix_options:
        available_label_chars = max_chars - len(prefix) - len(suffix)
        if available_label_chars <= 1:
            continue
        clipped_label = _clip_state_part(primary_label, max_chars=available_label_chars)
        clipped = f"{prefix}{clipped_label}{suffix}".strip()
        if len(clipped) <= max_chars:
            return clipped

    return None


def _clip_state_part(text: str, *, max_chars: int) -> str:
    normalized = " ".join(str(text).split())
    if len(normalized) <= max_chars:
        return normalized
    focus_clipped = _clip_focus_state_part(normalized, max_chars=max_chars)
    if focus_clipped:
        return focus_clipped
    if max_chars <= 3:
        return normalized[:max_chars]
    return normalized[: max_chars - 3].rstrip() + "..."


def _clip_review_ready_state_part(text: str, *, max_chars: int) -> str:
    normalized = " ".join(str(text).split())
    if len(normalized) <= max_chars:
        return normalized

    prefix, separator, payload = normalized.partition(" ")
    if prefix not in {"review", "ready"} or not separator or not payload:
        return _clip_state_part(normalized, max_chars=max_chars)

    payload_parts = [part.strip() for part in payload.split(" | ") if part.strip()]
    primary_label = payload_parts[0] if payload_parts else ""
    if not primary_label:
        return _clip_state_part(normalized, max_chars=max_chars)

    base_label = primary_label
    kind_suffix = ""
    if primary_label.endswith(")") and " (" in primary_label:
        possible_base, possible_suffix = primary_label.rsplit(" (", 1)
        possible_suffix = f" ({possible_suffix}"
        if possible_base and len(possible_suffix) < max_chars - len(prefix) - 1:
            base_label = possible_base.strip()
            kind_suffix = possible_suffix

    detail_parts = payload_parts[1:]
    detail_reserve = 0
    if detail_parts and max_chars >= 80:
        preferred_detail_chars = min(len(detail_parts[0]), 18)
        reserved_candidate = max_chars - len(prefix) - 1 - len(kind_suffix) - len(" | ") - preferred_detail_chars
        if reserved_candidate >= 12:
            detail_reserve = len(" | ") + preferred_detail_chars

    available_label_chars = max_chars - len(prefix) - 1 - len(kind_suffix) - detail_reserve
    if available_label_chars <= 0:
        return _clip_state_part(f"{prefix} {primary_label}", max_chars=max_chars)

    clipped_label = _clip_state_part(base_label, max_chars=available_label_chars)
    clipped = f"{prefix} {clipped_label}{kind_suffix}".strip()
    if len(clipped) > max_chars:
        return _clip_state_part(f"{prefix} {primary_label}", max_chars=max_chars)

    if not detail_parts:
        return clipped

    detail_candidates: list[str] = []
    for detail in detail_parts:
        if detail not in detail_candidates:
            detail_candidates.append(detail)

    warning_details = [
        detail
        for detail in detail_candidates
        if detail.startswith("warn ") or detail.startswith("key warning:")
    ]
    non_warning_details = [detail for detail in detail_candidates if detail not in warning_details]
    meaningful_warning_details = [
        detail for detail in warning_details if "no immediate warnings" not in detail.lower()
    ]

    if prefix == "review":
        detail_candidates = warning_details + non_warning_details
    elif prefix == "ready" and meaningful_warning_details:
        trailing_details = [
            detail
            for detail in detail_candidates
            if detail not in meaningful_warning_details and detail not in warning_details
        ]
        detail_candidates = meaningful_warning_details + trailing_details

    detailed = clipped
    for detail in detail_candidates:
        remaining_chars = max_chars - len(detailed) - len(" | ")
        if remaining_chars <= 0:
            break
        clipped_detail = _clip_state_part(detail, max_chars=remaining_chars)
        candidate = f"{detailed} | {clipped_detail}".strip()
        if len(candidate) <= max_chars:
            detailed = candidate

    return detailed


def _compact_metric_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError, OverflowError):
        return str(value)


def _value_is_zeroish(value: Any) -> bool:
    try:
        return float(value) == 0.0
    except (TypeError, ValueError, OverflowError):
        return False


def _compact_energy_state_summary(state: Any) -> str:
    def _part(label: str, value: Any, suffix: str, *, compact: bool = False) -> str | None:
        if value is None:
            return None
        display = _compact_metric_value(value) if compact else str(value)
        return f"{label} {display}{suffix}"

    solar_power_w = getattr(state, "solar_power_w", None) if state is not None else None
    grid_import_power_w = getattr(state, "grid_import_power_w", None) if state is not None else None
    grid_export_power_w = getattr(state, "grid_export_power_w", None) if state is not None else None
    home_load_power_w = getattr(state, "home_load_power_w", None) if state is not None else None
    battery_soc = getattr(state, "battery_soc", None) if state is not None else None
    battery_charge_power_w = getattr(state, "battery_charge_power_w", None) if state is not None else None
    battery_discharge_power_w = getattr(state, "battery_discharge_power_w", None) if state is not None else None

    raw_parts = [
        _part("solar", solar_power_w, " W"),
        _part("grid import", grid_import_power_w, " W"),
        _part("grid export", grid_export_power_w, " W"),
        _part("home load", home_load_power_w, " W"),
        _part("battery", battery_soc, "%"),
        _part("battery charge", battery_charge_power_w, " W"),
        _part("battery discharge", battery_discharge_power_w, " W"),
    ]
    raw_summary = " | ".join(part for part in raw_parts if part is not None)
    if raw_summary and len(raw_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return raw_summary

    compact_parts = [
        _part("solar", solar_power_w, " W", compact=True),
        _part("grid import", grid_import_power_w, " W", compact=True),
        _part("grid export", grid_export_power_w, " W", compact=True),
        _part("home load", home_load_power_w, " W", compact=True),
        _part("battery", battery_soc, "%", compact=True),
        _part("battery charge", battery_charge_power_w, " W", compact=True),
        _part("battery discharge", battery_discharge_power_w, " W", compact=True),
    ]
    compact_summary = " | ".join(part for part in compact_parts if part is not None)
    if compact_summary and len(compact_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return compact_summary

    non_zero_flow_parts = [
        _part("solar", solar_power_w, " W", compact=True),
        _part("grid import", grid_import_power_w, " W", compact=True),
        _part("grid export", grid_export_power_w, " W", compact=True),
        _part("home load", home_load_power_w, " W", compact=True),
        _part("battery", battery_soc, "%", compact=True),
        None
        if _value_is_zeroish(battery_charge_power_w)
        else _part("battery charge", battery_charge_power_w, " W", compact=True),
        None
        if _value_is_zeroish(battery_discharge_power_w)
        else _part("battery discharge", battery_discharge_power_w, " W", compact=True),
    ]
    non_zero_flow_summary = " | ".join(part for part in non_zero_flow_parts if part is not None)
    if non_zero_flow_summary and len(non_zero_flow_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return non_zero_flow_summary

    core_parts = [
        _part("solar", solar_power_w, " W", compact=True),
        _part("grid import", grid_import_power_w, " W", compact=True),
        _part("grid export", grid_export_power_w, " W", compact=True),
        _part("home load", home_load_power_w, " W", compact=True),
        _part("battery", battery_soc, "%", compact=True),
    ]
    if not _value_is_zeroish(battery_charge_power_w):
        core_parts.append(_part("battery charge", battery_charge_power_w, " W", compact=True))
    if not _value_is_zeroish(battery_discharge_power_w):
        core_parts.append(_part("battery discharge", battery_discharge_power_w, " W", compact=True))
    core_summary = " | ".join(part for part in core_parts if part is not None)
    if core_summary and len(core_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return core_summary

    clipped_core_summary = " | ".join(
        _clip_state_part(part, max_chars=36)
        for part in core_parts
        if part is not None
    )
    if clipped_core_summary and len(clipped_core_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return clipped_core_summary

    return raw_summary


def _compact_control_decision_summary(
    *,
    current_mode: str,
    target_export_w: int,
    export_error_w: Any,
    control_reason: str,
) -> str:
    base_parts = [
        f"mode {current_mode}",
        f"target {target_export_w} W",
        f"error {export_error_w} W" if export_error_w is not None else None,
    ]
    detail = str(control_reason or "").strip() or None
    full_summary = " | ".join(part for part in [*base_parts, detail] if part is not None)
    if full_summary and len(full_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return full_summary
    metrics_summary = " | ".join(part for part in base_parts if part is not None)
    if detail:
        clipped_detail = _clip_state_part(detail, max_chars=96)
        clipped_summary = " | ".join(part for part in [*base_parts, clipped_detail] if part is not None)
        if clipped_summary and len(clipped_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return clipped_summary
        if metrics_summary and len(metrics_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return metrics_summary
        if clipped_detail and len(clipped_detail) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return clipped_detail
    if metrics_summary and len(metrics_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return metrics_summary
    return f"mode {current_mode}"



def _compact_control_outcome_summary(
    *,
    control_summary: str,
    planned_action_count: Any,
    executable_action_count: Any,
    active_controlled_power_w: Any,
    active_managed_count: int = 0,
) -> str:
    detail = str(control_summary or "").strip() or None
    active_power_known = active_controlled_power_w is not None and not _value_is_zeroish(active_controlled_power_w)
    active_count_part = None
    if active_managed_count > 0 and not active_power_known:
        active_count_part = (
            "1 active managed device"
            if active_managed_count == 1
            else f"{active_managed_count} active managed devices"
        )
    metric_parts = [
        f"planned actions {planned_action_count}" if planned_action_count is not None else None,
        f"ready actions {executable_action_count}" if executable_action_count is not None else None,
        f"active load {active_controlled_power_w} W" if active_power_known else active_count_part,
    ]
    metrics_summary = " | ".join(part for part in metric_parts if part is not None)
    full_summary = " | ".join(part for part in [metrics_summary, detail] if part)
    if full_summary and len(full_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return full_summary
    if detail:
        clipped_detail = _clip_state_part(detail, max_chars=96)
        if metrics_summary:
            clipped_summary = " | ".join(part for part in [metrics_summary, clipped_detail] if part)
            if len(clipped_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
                return clipped_summary
        if metrics_summary and len(metrics_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return metrics_summary
        if len(clipped_detail) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return clipped_detail
    if metrics_summary and len(metrics_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return metrics_summary
    return "runtime pending | control outcome waiting"


def _normalized_alert_part(part: Any) -> str:
    normalized = " ".join(str(part or "").split())
    return "" if normalized.lower() == "none" else normalized



def _compact_top_alert_summary(*variants: list[str], fallback: str) -> str:
    for variant in variants:
        summary = " | ".join(
            normalized
            for part in variant
            if (normalized := _normalized_alert_part(part))
        )
        if summary and len(summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return summary
    return fallback


def _compact_command_center_device_alert_target(
    prefix: str,
    detail: dict[str, Any] | None,
    *,
    max_chars: int = 46,
) -> str:
    detail = detail or {}
    name = str(detail.get("name") or detail.get("entity_id") or "managed device").strip()
    signal_parts: list[str] = []
    deferred_parts: list[str] = []
    kind = str(detail.get("kind") or "").strip()

    planned_action = str(detail.get("planned_action") or "").strip()
    last_action_status = str(detail.get("last_action_status") or "").strip()
    if _runtime_device_has_blocked_activity(detail):
        signal_parts.append("not usable" if detail.get("usable") is False else "blocked")
        if planned_action and planned_action.lower() != "hold":
            signal_parts.append(f"action {planned_action}")
        if last_action_status and last_action_status.lower() not in {"ok", "applied", "success"}:
            signal_parts.append(f"last {last_action_status}")
    elif _runtime_device_has_active_plan(detail):
        if planned_action:
            signal_parts.append(f"action {planned_action}")
    elif _runtime_device_has_recent_attention(detail) and last_action_status:
        signal_parts.append(f"last {last_action_status}")

    if detail.get("observed_active") is True:
        current_power = detail.get("current_power_w")
        if current_power not in (None, ""):
            signal_parts.append(f"active {float(current_power or 0):g} W")
        elif "active" not in signal_parts:
            signal_parts.append("active")

    if kind:
        deferred_parts.append(kind)
    signal_parts.extend(deferred_parts)

    for keep_count in range(len(signal_parts), 0, -1):
        signal_text = " | ".join(signal_parts[:keep_count])
        reserved_chars = len(prefix) + len(signal_text) + 3
        name_budget = max_chars - reserved_chars
        if name_budget < 8:
            continue
        compact_name = _clip_state_part(name, max_chars=name_budget)
        if not compact_name:
            continue
        compact_label = f"{prefix}{compact_name} ({signal_text})"
        if len(compact_label) <= max_chars:
            return compact_label

    signal_first_preview = _command_center_managed_snapshot_focus_label(detail)
    if signal_first_preview:
        compact = _clip_state_part(f"{prefix}{signal_first_preview}", max_chars=max_chars)
        if compact:
            return compact

    preview = _command_center_runtime_device_preview(detail)
    if preview:
        compact = _clip_state_part(f"{prefix}{preview}", max_chars=max_chars)
        if compact:
            return compact

    compact_name = _clip_state_part(f"{prefix}{name}", max_chars=max_chars)
    return compact_name or f"{prefix}{name}".strip()


def _compact_next_action_fallback(
    *,
    missing_required_sources: list[str],
    runtime_source_attention: bool,
    recommended_section: str,
    device_parse_issues: list[str],
    has_managed_devices: bool,
    candidate_count: int,
    managed_attention_count: int,
    blocked_activity_count: int,
    first_blocked_device: dict[str, Any] | None,
    first_planned_device: dict[str, Any] | None,
    first_attention_device: dict[str, Any] | None,
    review_candidate_name: str,
    review_candidate_preview: str,
    ready_candidate_name: str,
    ready_candidate_preview: str,
    top_candidate_name: str,
    top_candidate_preview: str,
) -> str:
    if missing_required_sources or runtime_source_attention:
        return f"Open {SOURCES_CONFIGURE_PATH} and use the highlighted native guidance to continue."

    if (
        recommended_section == DEVICES_SECTION_LABEL
        or device_parse_issues
        or not has_managed_devices
        or candidate_count
        or managed_attention_count
        or blocked_activity_count
    ):
        if blocked_activity_count:
            blocked_target = _command_center_runtime_device_preview(first_blocked_device) or "the first blocked device"
            return (
                f"Open {DEVICES_CONFIGURE_PATH} to review blocked devices in the Managed Devices workspace, starting with {blocked_target}."
            )
        if first_planned_device:
            planned_target = _command_center_runtime_device_preview(first_planned_device) or "the active fleet plan"
            return (
                f"Open {DEVICES_CONFIGURE_PATH} to confirm the active fleet plan in the Managed Devices workspace for {planned_target}."
            )
        if first_attention_device:
            attention_target = _command_center_runtime_device_preview(first_attention_device) or "the first managed device needing attention"
            return (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, starting with attention on {attention_target}."
            )
        if review_candidate_name:
            compact_review = review_candidate_name
            compact_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, review unmanaged candidate: {compact_review}"
            )
            if ready_candidate_name and ready_candidate_name != review_candidate_name:
                compact_ready = ready_candidate_name
                compact_step += f", then promote ready unmanaged candidate: {compact_ready}"
            return compact_step + "."
        if ready_candidate_name or top_candidate_name or top_candidate_preview:
            compact_ready = ready_candidate_preview or ready_candidate_name or top_candidate_preview or top_candidate_name or "the next unmanaged candidate"
            return (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then promote ready unmanaged candidate: {compact_ready}."
            )
        if has_managed_devices:
            return (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then edit device settings or stage enablement changes."
            )
        return (
            f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available."
        )

    if recommended_section == POLICY_SECTION_LABEL:
        return (
            f"Open {POLICY_CONFIGURE_PATH} to continue in Controls and tune target export, deadband, reserve, or live mode."
        )
    if recommended_section == SOURCES_SECTION_LABEL:
        return f"Open {SOURCES_CONFIGURE_PATH} to continue in Sensors and confirm the live source roles and health."
    return (
        f"Open {SUPPORT_CONFIGURE_PATH} to continue in Diagnostics with blocker triage, repairs, or install validation."
    )


def _validation_details(state: Any) -> dict[str, Any]:
    if state is None:
        return {}
    return state.validation_details or {}


def build_source_attention_details(state: Any) -> dict[str, Any]:
    """Return merged source diagnostics plus freshness metadata for operator surfaces."""
    validation_details = _validation_details(state)
    source_diagnostics = dict(validation_details.get("source_diagnostics", {}) or {})
    source_freshness = validation_details.get("source_freshness", {}) or {}

    unavailable_source_keys: list[str] = []
    stale_source_keys: list[str] = []
    enriched_source_diagnostics: dict[str, dict[str, Any]] = {}

    ordered_keys = list(dict.fromkeys([*source_diagnostics.keys(), *source_freshness.keys()]))
    for key in ordered_keys:
        details = source_diagnostics.get(key, {}) or {}
        freshness = source_freshness.get(key, {}) or {}
        merged = dict(freshness)
        merged.update(details)
        if "stale" not in merged:
            merged["stale"] = bool(freshness.get("stale", False))
        if merged.get("age_seconds") is None:
            merged["age_seconds"] = freshness.get("age_seconds")
        if merged.get("last_updated") is None:
            merged["last_updated"] = freshness.get("last_updated")
        if merged.get("stale_threshold_seconds") is None:
            merged["stale_threshold_seconds"] = freshness.get("stale_threshold_seconds")
        if merged.get("entity_id") is None:
            merged["entity_id"] = freshness.get("entity_id")
        enriched_source_diagnostics[key] = merged
        is_unavailable = merged.get("status") == "unavailable"
        stale_threshold_seconds = merged.get("stale_threshold_seconds")
        if stale_threshold_seconds is None:
            stale_threshold_seconds = 120
        is_stale = bool(merged.get("stale")) or (
            merged.get("age_seconds") is not None and float(merged.get("age_seconds") or 0) > float(stale_threshold_seconds)
        )
        if is_unavailable:
            unavailable_source_keys.append(key)
        if is_stale and not is_unavailable:
            stale_source_keys.append(key)

    return {
        "validation_details": validation_details,
        "source_diagnostics": enriched_source_diagnostics,
        "source_freshness": source_freshness,
        "unavailable_source_keys": unavailable_source_keys,
        "stale_source_keys": stale_source_keys,
    }


def _issue_role_keys(issues: list[dict[str, Any]] | None, *, severities: set[str] | None = None) -> list[str]:
    allowed = {severity.lower() for severity in severities} if severities else None
    known_suffixes = ("_missing_entity", "_unavailable", "_non_numeric")
    keys: list[str] = []
    for issue in issues or []:
        severity = str(issue.get("severity", "") or "").lower()
        if allowed is not None and severity not in allowed:
            continue
        code = str(issue.get("code", "") or "")
        key = next((code[: -len(suffix)] for suffix in known_suffixes if code.endswith(suffix)), "")
        if key in SOURCE_ROLE_LABELS and key not in keys:
            keys.append(key)
    return keys


def _ordered_source_attention_keys(source_attention: dict[str, Any]) -> list[str]:
    ordered_keys: list[str] = []
    for key in source_attention["unavailable_source_keys"] + source_attention["stale_source_keys"]:
        if key not in ordered_keys:
            ordered_keys.append(key)
    validation_role_keys = _issue_role_keys(
        source_attention.get("validation_details", {}).get("issues", []),
        severities={"error"},
    )
    for key in validation_role_keys:
        if key not in ordered_keys:
            ordered_keys.append(key)
    return ordered_keys


def _blocking_source_attention_keys(source_attention: dict[str, Any]) -> list[str]:
    blocking_keys: list[str] = []
    validation_role_keys = set(
        _issue_role_keys(
            source_attention.get("validation_details", {}).get("issues", []),
            severities={"error"},
        )
    )
    for key in _ordered_source_attention_keys(source_attention):
        details = source_attention["source_diagnostics"].get(key, {}) or {}
        is_required = details.get("required") is True or key in REQUIRED_SOURCE_KEYS
        is_unavailable = details.get("status") == "unavailable"
        is_stale = bool(details.get("stale")) and not is_unavailable
        stale_blocks_runtime = details.get("stale_blocks_runtime")
        if stale_blocks_runtime is None:
            stale_blocks_runtime = is_required
        if key in validation_role_keys:
            blocking_keys.append(key)
        elif is_unavailable and is_required:
            blocking_keys.append(key)
        elif is_stale and stale_blocks_runtime:
            blocking_keys.append(key)
    return blocking_keys


def _validation_issue_message_for_role(source_attention: dict[str, Any], key: str) -> str:
    validation_issues = list(source_attention.get("validation_details", {}).get("issues", []) or [])
    validation_role_keys = _issue_role_keys(validation_issues)
    if key not in validation_role_keys:
        return ""

    for issue in validation_issues:
        code = str(issue.get("code", "") or "")
        issue_key = next(
            (
                code[: -len(suffix)]
                for suffix in ("_missing_entity", "_unavailable", "_non_numeric")
                if code.endswith(suffix)
            ),
            "",
        )
        if issue_key != key:
            continue
        message = str(issue.get("message") or "").strip()
        if message:
            return message
    return ""


def _looks_like_entity_id(value: str) -> bool:
    domain, separator, object_id = value.partition(".")
    return bool(separator and domain and object_id and " " not in value)



def _humanize_entity_id(value: str) -> str:
    _, _, object_id = value.partition(".")
    text = (object_id or value).replace("_", " ").strip()
    return text.title() if text else value



def _source_attention_target_label(key: str, details: dict[str, Any], configured_label: str | None) -> str:
    role_label = str(SOURCE_ROLE_LABELS.get(key, key) or "").strip().lower()
    for raw_label in (
        details.get("friendly_name"),
        configured_label,
        details.get("entity_id"),
    ):
        label = str(raw_label or "").strip()
        if not label:
            continue
        if _looks_like_entity_id(label):
            label = _humanize_entity_id(label)
        if label.strip().lower() == role_label:
            continue
        return label
    return ""



def build_source_attention_role_summary(
    state: Any,
    config: dict[str, Any] | None = None,
    *,
    limit: int = 6,
    blocking_only: bool = False,
) -> str:
    """Return concise operator-facing guidance for unavailable or stale mapped sources."""
    source_attention = build_source_attention_details(state)
    source_diagnostics = source_attention["source_diagnostics"]
    configured = config or {}
    attention_keys = (
        _blocking_source_attention_keys(source_attention)
        if blocking_only
        else _ordered_source_attention_keys(source_attention)
    )

    details_lines: list[str] = []
    for key in attention_keys[:limit]:
        details = source_diagnostics.get(key, {})
        configured_label = format_source_binding_label(configured.get(key)) if configured.get(key) else None
        target_label = _source_attention_target_label(key, details, configured_label)

        markers: list[str] = []
        is_unavailable = details.get("status") == "unavailable"
        if is_unavailable:
            markers.append("unavailable")
        if details.get("stale") and not is_unavailable:
            age_seconds = details.get("age_seconds")
            if age_seconds is not None:
                markers.append(f"stale {int(age_seconds)} s")
            else:
                markers.append("stale")
        issue_messages = [str(issue).strip() for issue in (details.get("issues") or []) if str(issue).strip()]
        if issue_messages:
            markers.append(issue_messages[0])
        if not issue_messages:
            validation_message = _validation_issue_message_for_role(source_attention, key)
            if validation_message:
                markers.append(validation_message)

        marker_text = "; ".join(markers) if markers else "needs attention"
        role_label = SOURCE_ROLE_LABELS.get(key, key)
        details_lines.append(
            f"{role_label} -> {target_label} ({marker_text})"
            if target_label
            else f"{role_label} ({marker_text})"
        )

    return "; ".join(details_lines) if details_lines else "None"


def build_source_attention_summary(
    state: Any,
    config: dict[str, Any] | None = None,
    *,
    limit: int = 4,
    blocking_only: bool = False,
) -> str:
    """Return a concise operator-facing summary of current mapped-source blockers."""
    source_attention = build_source_attention_details(state)
    source_diagnostics = source_attention["source_diagnostics"]
    configured = config or {}
    attention_keys = (
        _blocking_source_attention_keys(source_attention)
        if blocking_only
        else _ordered_source_attention_keys(source_attention)
    )

    if not attention_keys:
        return "None"

    parts: list[str] = []
    for key in attention_keys[:limit]:
        details = source_diagnostics.get(key, {})
        configured_label = format_source_binding_label(configured.get(key)) if configured.get(key) else None
        target_label = _source_attention_target_label(key, details, configured_label)
        status_bits: list[str] = []
        is_unavailable = details.get("status") == "unavailable"
        if is_unavailable:
            status_bits.append("unavailable")
        if details.get("stale") and not is_unavailable:
            age_seconds = details.get("age_seconds")
            status_bits.append(f"stale {int(age_seconds)} s" if age_seconds is not None else "stale")
        validation_message = _validation_issue_message_for_role(source_attention, key)
        if validation_message and validation_message not in status_bits:
            status_bits.append(validation_message)
        if not status_bits:
            status_bits.append("needs attention")
        role_label = SOURCE_ROLE_LABELS.get(key, key)
        status_text = ", ".join(status_bits)
        parts.append(
            f"{role_label} ({target_label}, {status_text})"
            if target_label
            else f"{role_label} ({status_text})"
        )

    remaining = len(attention_keys) - len(parts)
    if remaining > 0:
        parts.append(f"+{remaining} more")
    return "; ".join(parts)


def build_source_attention_brief(
    state: Any,
    config: dict[str, Any] | None = None,
    *,
    limit: int = 3,
    blocking_only: bool = False,
) -> str:
    """Return a shorter mapped-source attention summary for compact sensors/cards."""
    source_attention = build_source_attention_details(state)
    source_diagnostics = source_attention["source_diagnostics"]
    configured = config or {}
    attention_keys = (
        _blocking_source_attention_keys(source_attention)
        if blocking_only
        else _ordered_source_attention_keys(source_attention)
    )

    if not attention_keys:
        return "None"

    parts: list[str] = []
    for key in attention_keys[:limit]:
        details = source_diagnostics.get(key, {})
        configured_label = format_source_binding_label(configured.get(key)) if configured.get(key) else None
        target_label = _source_attention_target_label(key, details, configured_label)
        status_bits: list[str] = []
        is_unavailable = details.get("status") == "unavailable"
        if is_unavailable:
            status_bits.append("unavailable")
        elif details.get("stale"):
            status_bits.append("stale")
        validation_message = _validation_issue_message_for_role(source_attention, key)
        if validation_message:
            status_bits.append(validation_message)
        marker = ", ".join(status_bits) if status_bits else "needs attention"
        role_label = SOURCE_ROLE_LABELS.get(key, key)
        parts.append(
            f"{role_label} ({target_label}, {marker})"
            if target_label
            else f"{role_label} ({marker})"
        )

    remaining = len(attention_keys) - len(parts)
    if remaining > 0:
        parts.append(f"+{remaining} more")
    return "; ".join(parts)


def summarize_validation_issue_messages(
    state: Any,
    *,
    severities: set[str] | None = None,
    limit: int = 3,
) -> str:
    """Return a concise deduplicated summary of validation issue messages."""
    validation_details = _validation_details(state)
    raw_issues = list(validation_details.get("issues", []) or [])
    allowed = {severity.lower() for severity in severities} if severities else None

    messages: list[str] = []
    for issue in raw_issues:
        severity = str(issue.get("severity", "")).lower()
        if allowed is not None and severity not in allowed:
            continue
        message = str(issue.get("message") or "").strip()
        if message and message not in messages:
            messages.append(message)
        if len(messages) >= limit:
            break

    return "; ".join(messages) if messages else "None"


def build_source_selector_fallback_hint(
    *,
    role_keys: list[str] | None = None,
    validation_issues: list[dict[str, Any]] | None = None,
) -> str:
    """Return operator guidance for known HA entity-selector fallback paths."""
    roles = set(role_keys or [])
    for key in _issue_role_keys(validation_issues):
        roles.add(key)

    hints: list[str] = []
    if roles.intersection({CONF_GRID_IMPORT_ENERGY_ENTITY, CONF_GRID_EXPORT_ENERGY_ENTITY}):
        hints.append(
            "If Home Assistant rejects a valid Combined / net grid energy choice, first capture the exact validation error or screenshot, then clear that selector, paste the same entity ID into the Combined / net grid energy entity ID fallback field, and save again."
        )
    if CONF_BATTERY_SOC_ENTITY in roles:
        hints.append(
            "If Home Assistant rejects a valid Battery state of charge choice, first capture the exact validation error or screenshot, then clear that selector, paste the same entity ID into the Battery state of charge entity ID fallback field, and save again."
        )
    return " ".join(hints) if hints else ""


def _format_source_role_list(source_keys: list[str] | None) -> str:
    named_roles = [SOURCE_ROLE_LABELS.get(key, key) for key in (source_keys or []) if key]
    return ", ".join(named_roles[:6]) if named_roles else "None"


def build_source_repair_step(
    *,
    missing_source_keys: list[str] | None = None,
    unavailable_source_keys: list[str] | None = None,
    stale_source_keys: list[str] | None = None,
    blocking_validation_details: str | None = None,
    affected_roles: str | None = None,
) -> str:
    """Return a concise operator-facing next step for source repair work."""
    missing_roles = _format_source_role_list(missing_source_keys)
    unavailable_roles = _format_source_role_list(unavailable_source_keys)
    stale_roles = _format_source_role_list(stale_source_keys)
    blocking_details = str(blocking_validation_details or "").strip()
    affected_roles_text = str(affected_roles or "").strip()

    def _confirm_recovery_suffix(target_roles: str) -> str:
        role_text = target_roles.strip()
        if not role_text or role_text == "None":
            return "then reopen Sensors to confirm live source health."
        return f"then reopen Sensors to confirm these roles recover: {role_text}."

    if missing_roles != "None":
        return (
            f"Open {SOURCES_CONFIGURE_PATH}, finish these required source roles: {missing_roles}, then save and reload the integration, "
            f"{_confirm_recovery_suffix(missing_roles)}"
        )

    attention_parts: list[str] = []
    repair_actions: list[str] = []
    if unavailable_roles != "None":
        attention_parts.append(f"unavailable roles: {unavailable_roles}")
        repair_actions.append(f"restore live availability for {unavailable_roles}")
    if stale_roles != "None":
        attention_parts.append(f"stale roles: {stale_roles}")
        repair_actions.append(f"refresh or replace stale readings for {stale_roles}")
    if attention_parts:
        blocker_text = (
            f"these source blockers first: {affected_roles_text}"
            if affected_roles_text and affected_roles_text != "None"
            else f"these source blockers ({'; '.join(attention_parts)})"
        )
        repair_action_text = "; ".join(repair_actions)
        confirm_role_parts = [role for role in (unavailable_roles, stale_roles) if role != "None"]
        confirm_roles = (
            affected_roles_text
            if affected_roles_text and affected_roles_text != "None"
            else ", ".join(confirm_role_parts)
        )
        return (
            f"Open {SOURCES_CONFIGURE_PATH}, repair {blocker_text}. In Home Assistant, make sure the mapped entities still exist and are reporting fresh numeric values, "
            f"then {repair_action_text}, save and reload the integration, {_confirm_recovery_suffix(confirm_roles)}"
        )

    if blocking_details and blocking_details != "None":
        blocker_text = (
            f"repair these highlighted source roles first: {affected_roles_text}, then clear the blocking source validation errors ({blocking_details})"
            if affected_roles_text and affected_roles_text != "None"
            else f"repair the blocking source validation errors ({blocking_details})"
        )
        confirm_roles = affected_roles_text if affected_roles_text and affected_roles_text != "None" else blocking_details
        return (
            f"Open {SOURCES_CONFIGURE_PATH}, {blocker_text}. Confirm each mapped entity selection still points at the intended Home Assistant entity, then save and reload the integration, "
            f"{_confirm_recovery_suffix(confirm_roles)}"
        )

    return (
        f"Open {SOURCES_CONFIGURE_PATH}, review the source map, then save and reload the integration, "
        "then reopen Sensors to confirm live source health."
    )


def build_live_source_health_summary(state: Any) -> str:
    """Return source-specific runtime health without leaking device/runtime summaries."""
    if state is None:
        return "runtime pending | source health waiting"

    source_attention = build_source_attention_details(state)
    merged_attention = build_source_attention_summary(state, limit=4)
    if merged_attention != "None":
        return f"Source roles need attention: {merged_attention}"

    blocking_validation = summarize_validation_issue_messages(state, severities={"error"}, limit=3)
    if blocking_validation != "None":
        diagnostic_summary = str(getattr(state, "diagnostic_summary", "") or "").strip()
        return diagnostic_summary or blocking_validation

    if bool(getattr(state, "stale_data", False)):
        stale_summary = str(getattr(state, "stale_source_summary", "") or "").strip()
        if stale_summary:
            return stale_summary

    diagnostic_summary = str(getattr(state, "diagnostic_summary", "") or "").strip()
    if diagnostic_summary and diagnostic_summary != "Source model looks internally consistent; no calibration issues detected right now":
        return diagnostic_summary.replace("Source mapping currently looks healthy", "Source roles currently look healthy")

    source_diagnostics = source_attention.get("source_diagnostics", {})
    if source_diagnostics:
        ok_count = sum(1 for details in source_diagnostics.values() if details.get("status") == "ok")
        return f"Source roles currently look healthy across {_count_label(ok_count, 'source role')}."

    return "Source roles currently look healthy."


def build_source_mapping_summary(
    config: dict[str, Any] | None,
    *,
    include_optional: bool = True,
) -> str:
    """Return a readable role -> entity summary for the configured source mapping."""
    merged = config or {}
    lines: list[str] = []
    for spec in _source_specs_from_config(merged):
        if not include_optional and not spec.required:
            continue
        raw_value = merged.get(spec.key)
        if raw_value:
            mapping = format_source_binding_label(raw_value)
        elif spec.required:
            mapping = "Not mapped yet"
        else:
            continue
        lines.append(f"- {SOURCE_ROLE_LABELS.get(spec.key, spec.key)}: {mapping}")
    return "\n".join(lines) if lines else "- None"


def _source_specs_from_config(config: dict[str, Any]) -> list[SourceSpec]:
    return [
        SourceSpec(CONF_SOLAR_POWER_ENTITY, config.get(CONF_SOLAR_POWER_ENTITY), "power"),
        SourceSpec(CONF_SOLAR_ENERGY_ENTITY, config.get(CONF_SOLAR_ENERGY_ENTITY), "energy"),
        SourceSpec(CONF_GRID_IMPORT_POWER_ENTITY, config.get(CONF_GRID_IMPORT_POWER_ENTITY), "power"),
        SourceSpec(CONF_GRID_EXPORT_POWER_ENTITY, config.get(CONF_GRID_EXPORT_POWER_ENTITY), "power"),
        SourceSpec(CONF_GRID_IMPORT_ENERGY_ENTITY, config.get(CONF_GRID_IMPORT_ENERGY_ENTITY), "energy"),
        SourceSpec(CONF_GRID_EXPORT_ENERGY_ENTITY, config.get(CONF_GRID_EXPORT_ENERGY_ENTITY), "energy"),
        SourceSpec(CONF_HOME_LOAD_POWER_ENTITY, config.get(CONF_HOME_LOAD_POWER_ENTITY), "power", required=False),
        SourceSpec(CONF_BATTERY_SOC_ENTITY, config.get(CONF_BATTERY_SOC_ENTITY), "percent", required=False),
        SourceSpec(CONF_BATTERY_CHARGE_POWER_ENTITY, config.get(CONF_BATTERY_CHARGE_POWER_ENTITY), "power", required=False),
        SourceSpec(CONF_BATTERY_DISCHARGE_POWER_ENTITY, config.get(CONF_BATTERY_DISCHARGE_POWER_ENTITY), "power", required=False),
    ]


def _configured_device_payloads(entry: Any) -> tuple[list[dict[str, Any]], list[str]]:
    raw = entry.options.get(CONF_DEVICE_INVENTORY_JSON, entry.data.get(CONF_DEVICE_INVENTORY_JSON))
    devices, issues = parse_device_configs(raw)
    payloads: list[dict[str, Any]] = []
    for device in devices:
        payloads.append(
            {
                "key": device.key,
                "name": device.name,
                "kind": device.kind,
                "entity_id": device.entity_id,
                "adapter": device.adapter,
                "nominal_power_w": device.nominal_power_w,
                "min_power_w": device.min_power_w,
                "max_power_w": device.max_power_w,
                "step_w": device.step_w,
                "priority": device.priority,
                "enabled": device.enabled,
                "min_on_seconds": device.min_on_seconds,
                "min_off_seconds": device.min_off_seconds,
                "cooldown_seconds": device.cooldown_seconds,
                "max_active_seconds": device.max_active_seconds,
            }
        )
    return payloads, issues


def _ordered_runtime_device_details(state: Any) -> list[dict[str, Any]]:
    if state is None:
        return []
    details = list((getattr(state, "device_details", {}) or {}).values())
    return sorted(details, key=_runtime_device_sort_key)


def _first_runtime_device_name(state: Any, *, predicate) -> str:
    for detail in _ordered_runtime_device_details(state):
        if predicate(detail):
            return str(detail.get("name") or detail.get("entity_id") or "").strip()
    return ""


def _first_runtime_device_detail(state: Any, *, predicate) -> dict[str, Any] | None:
    for detail in _ordered_runtime_device_details(state):
        if predicate(detail):
            return detail
    return None


def _first_distinct_runtime_device_detail(
    state: Any,
    *,
    predicate,
    excluded: tuple[dict[str, Any] | None, ...],
) -> dict[str, Any] | None:
    for detail in _ordered_runtime_device_details(state):
        if not predicate(detail):
            continue
        if any(_same_runtime_device(detail, other) for other in excluded if other):
            continue
        return detail
    return None


def _runtime_device_has_blocked_activity(detail: dict[str, Any]) -> bool:
    planned_action = str(detail.get("planned_action") or "").strip().lower()
    if detail.get("usable") is False:
        return True
    return planned_action not in {"", "hold"} and detail.get("action_executable") is False


def _runtime_device_has_active_plan(detail: dict[str, Any]) -> bool:
    planned_action = str(detail.get("planned_action") or "").strip().lower()
    return planned_action not in {"", "hold"}


def _runtime_device_has_recent_attention(detail: dict[str, Any]) -> bool:
    last_action_status = str(detail.get("last_action_status") or "").strip().lower()
    return bool(last_action_status and last_action_status not in {"ok", "applied", "success"})


def _runtime_device_needs_attention(detail: dict[str, Any]) -> bool:
    return bool(
        _runtime_device_has_blocked_activity(detail)
        or _runtime_device_has_active_plan(detail)
        or _runtime_device_has_recent_attention(detail)
    )


def _runtime_device_sort_key(detail: dict[str, Any]) -> tuple[int, int, int, int, int, str]:
    effective_enabled = bool(detail.get("effective_enabled", detail.get("enabled", True)))
    usable = detail.get("usable")
    blocked_rank = 0 if _runtime_device_has_blocked_activity(detail) else 1
    planned_rank = 0 if _runtime_device_has_active_plan(detail) else 1
    recent_attention_rank = 0 if _runtime_device_has_recent_attention(detail) else 1
    enabled_usable_rank = 0 if effective_enabled and usable is True else 1
    return (
        blocked_rank,
        planned_rank,
        recent_attention_rank,
        enabled_usable_rank,
        int(detail.get("priority", 0) or 0),
        str(detail.get("name") or detail.get("entity_id") or "").lower(),
    )


def _command_center_runtime_device_preview(detail: dict[str, Any] | None) -> str:
    if not detail:
        return ""
    name = str(detail.get("name") or detail.get("entity_id") or "managed device").strip()
    bits: list[str] = []
    kind = str(detail.get("kind") or "").strip()
    if kind:
        bits.append(kind)
    if detail.get("usable") is False:
        bits.append("not usable")
    current_power = detail.get("current_power_w")
    if current_power is not None:
        bits.append(f"power {current_power} W")
    if kind == "variable" and detail.get("current_target_power_w") is not None:
        bits.append(f"target {detail.get('current_target_power_w')} W")
    planned_action = str(detail.get("planned_action") or "").strip()
    if planned_action and planned_action.lower() != "hold":
        bits.append(f"action {planned_action}")
    last_action_status = str(detail.get("last_action_status") or "").strip().lower()
    if last_action_status and last_action_status not in {"ok", "applied", "success"}:
        bits.append(f"last {detail.get('last_action_status')}")
    if not bits:
        return name
    return f"{name} ({' | '.join(bits[:4])})"


def _command_center_managed_snapshot_focus_label(detail: dict[str, Any] | None) -> str:
    if not detail:
        return ""
    name = str(detail.get("name") or detail.get("entity_id") or "Unnamed device").strip()
    parts: list[str] = []
    kind = str(detail.get("kind") or "").strip()
    if kind:
        parts.append(kind)
    planned_action = str(detail.get("planned_action") or "").strip()
    last_action_status = str(detail.get("last_action_status") or "").strip()
    if _runtime_device_has_blocked_activity(detail):
        parts.append("not usable" if detail.get("usable") is False else "blocked")
        if planned_action and planned_action.lower() != "hold":
            parts.append(f"action {planned_action}")
        if last_action_status and last_action_status.lower() not in {"ok", "applied", "success"}:
            parts.append(f"last {last_action_status}")
    elif _runtime_device_has_active_plan(detail):
        if planned_action:
            parts.append(f"action {planned_action}")
    elif _runtime_device_has_recent_attention(detail) and last_action_status:
        parts.append(f"last {last_action_status}")
    if detail.get("observed_active") is True:
        if detail.get("current_power_w") not in (None, ""):
            active_power = f"active {float(detail.get('current_power_w') or 0):g} W"
            if active_power not in parts:
                parts.append(active_power)
        elif "active" not in parts:
            parts.append("active")
    return f"{name} ({' | '.join(parts)})" if parts else name


def _command_center_fleet_focus_label(
    detail: dict[str, Any] | None,
    *,
    include_plan_context: bool = False,
) -> str:
    if not detail:
        return ""
    name = str(detail.get("name") or detail.get("entity_id") or "Unnamed device").strip()
    parts: list[str] = []
    kind = str(detail.get("kind") or "").strip()
    if kind:
        parts.append(kind)

    blocked = _runtime_device_has_blocked_activity(detail)
    planned_action = str(detail.get("planned_action") or "").strip()
    last_action_status = str(detail.get("last_action_status") or "").strip()
    if blocked:
        parts.append("not usable" if detail.get("usable") is False else "blocked")
        if planned_action and planned_action.lower() != "hold":
            parts.append(f"action {planned_action}")
        if last_action_status and last_action_status.lower() not in {"ok", "applied", "success"}:
            parts.append(f"last {last_action_status}")
    elif include_plan_context:
        current_target_power_w = detail.get("current_target_power_w")
        current_power_w = detail.get("current_power_w")
        if kind == "variable" and current_target_power_w not in (None, ""):
            parts.append(f"target {float(current_target_power_w or 0):g} W")
        elif detail.get("observed_active") is True and current_power_w not in (None, ""):
            parts.append(f"active {float(current_power_w or 0):g} W")
        if planned_action and planned_action.lower() != "hold":
            parts.append(f"action {planned_action}")
    else:
        if _runtime_device_has_recent_attention(detail) and last_action_status:
            parts.append(f"last {last_action_status}")

    if detail.get("observed_active") is True:
        if detail.get("current_power_w") not in (None, ""):
            active_power = f"active {float(detail.get('current_power_w') or 0):g} W"
            if active_power not in parts:
                parts.append(active_power)
        elif "active" not in parts:
            parts.append("active")

    return f"{name} ({' | '.join(parts)})" if parts else name


def _same_runtime_device(left: dict[str, Any] | None, right: dict[str, Any] | None) -> bool:
    if not left or not right:
        return False
    left_id = str(left.get("entity_id") or left.get("name") or "").strip()
    right_id = str(right.get("entity_id") or right.get("name") or "").strip()
    return bool(left_id and right_id and left_id == right_id)


def _managed_runtime_mix(state: Any) -> tuple[bool, int, int, int]:
    if state is None:
        return False, 0, 0, 0
    device_details = list((getattr(state, "device_details", {}) or {}).values())
    fixed_count = int(getattr(state, "fixed_device_count", 0) or 0)
    variable_count = int(getattr(state, "variable_device_count", 0) or 0)
    nominal_power = int(float(getattr(state, "controllable_nominal_power_w", 0) or 0))

    if not fixed_count:
        fixed_count = sum(1 for detail in device_details if str(detail.get("kind") or "") == "fixed")
    if not variable_count:
        variable_count = sum(1 for detail in device_details if str(detail.get("kind") or "") == "variable")
    if not nominal_power:
        nominal_power = int(sum(float(detail.get("nominal_power_w", 0) or 0) for detail in device_details))

    kind_known = bool(fixed_count or variable_count) or any(
        str(detail.get("kind") or "") in {"fixed", "variable"} for detail in device_details
    )
    return kind_known, fixed_count, variable_count, nominal_power


def _managed_runtime_activity(state: Any) -> tuple[int, float]:
    if state is None:
        return 0, 0.0
    device_details = list((getattr(state, "device_details", {}) or {}).values())
    active_count = sum(1 for detail in device_details if detail.get("observed_active") is True)
    active_power_w = float(getattr(state, "active_controlled_power_w", 0) or 0)
    if active_power_w <= 0 and active_count:
        active_power_w = sum(
            float(detail.get("current_power_w", 0) or 0)
            for detail in device_details
            if detail.get("observed_active") is True
        )
    if active_count <= 0 and active_power_w > 0:
        managed_count = int(getattr(state, "device_count", 0) or 0)
        if managed_count > 0:
            active_count = 1
    return active_count, round(active_power_w, 1)


def _build_operator_checklist(
    state: Any,
    entry: Any,
    configured_devices: list[dict[str, Any]],
    device_parse_issues: list[str],
    *,
    coordinator: Any | None = None,
) -> dict[str, Any]:
    state_stale_data = bool(getattr(state, "stale_data", False)) if state is not None else False
    state_usable_device_count = int(getattr(state, "usable_device_count", 0) or 0) if state is not None else 0
    state_safe_mode = bool(getattr(state, "safe_mode", False)) if state is not None else False

    source_mapping = {
        CONF_SOLAR_POWER_ENTITY: entry.data.get(CONF_SOLAR_POWER_ENTITY),
        CONF_SOLAR_ENERGY_ENTITY: entry.data.get(CONF_SOLAR_ENERGY_ENTITY),
        CONF_GRID_IMPORT_POWER_ENTITY: entry.data.get(CONF_GRID_IMPORT_POWER_ENTITY),
        CONF_GRID_EXPORT_POWER_ENTITY: entry.data.get(CONF_GRID_EXPORT_POWER_ENTITY),
        CONF_GRID_IMPORT_ENERGY_ENTITY: entry.data.get(CONF_GRID_IMPORT_ENERGY_ENTITY),
        CONF_GRID_EXPORT_ENERGY_ENTITY: entry.data.get(CONF_GRID_EXPORT_ENERGY_ENTITY),
        CONF_HOME_LOAD_POWER_ENTITY: entry.data.get(CONF_HOME_LOAD_POWER_ENTITY),
        CONF_BATTERY_SOC_ENTITY: entry.data.get(CONF_BATTERY_SOC_ENTITY),
        CONF_BATTERY_CHARGE_POWER_ENTITY: entry.data.get(CONF_BATTERY_CHARGE_POWER_ENTITY),
        CONF_BATTERY_DISCHARGE_POWER_ENTITY: entry.data.get(CONF_BATTERY_DISCHARGE_POWER_ENTITY),
    }
    missing_required_sources = [key for key in REQUIRED_SOURCE_KEYS if not source_mapping.get(key)]
    source_attention = build_source_attention_details(state)
    validation_details = source_attention["validation_details"]
    validation_issues = validation_details.get("issues", [])
    source_diagnostics = source_attention["source_diagnostics"]
    blocking_validation_issues = [
        issue for issue in validation_issues if str(issue.get("severity", "")).lower() == "error"
    ]
    blocking_fallback_roles = [
        key
        for key in source_attention["unavailable_source_keys"] + source_attention["stale_source_keys"]
        if key in {CONF_GRID_IMPORT_ENERGY_ENTITY, CONF_GRID_EXPORT_ENERGY_ENTITY, CONF_BATTERY_SOC_ENTITY}
    ]
    blocking_fallback_hint = build_source_selector_fallback_hint(
        role_keys=blocking_fallback_roles,
        validation_issues=blocking_validation_issues,
    )
    stale_summary = str(validation_details.get("stale_source_summary") or "").strip()

    checklist = [
        {
            "key": "sources_mapped",
            "label": "Required source roles complete",
            "complete": not missing_required_sources,
            "detail": (
                "All required solar and grid source roles are configured."
                if not missing_required_sources
                else "Missing required source roles: "
                + ", ".join(SOURCE_ROLE_LABELS.get(key, key) for key in missing_required_sources)
            ),
        },
        {
            "key": "sources_validated",
            "label": "Source validation healthy",
            "complete": not blocking_validation_issues and not state_stale_data,
            "detail": (
                "Source roles currently validate cleanly enough for runtime control."
                if not blocking_validation_issues and not state_stale_data
                else (
                    f"Blocking validation issues: {len(blocking_validation_issues)}"
                    if blocking_validation_issues
                    else (stale_summary or "One or more source roles are stale.")
                )
            ),
        },
        {
            "key": "devices_configured",
            "label": "Controllable devices onboarded",
            "complete": bool(configured_devices) and not device_parse_issues,
            "detail": (
                f"{_configured_device_count_label(len(configured_devices))} configured."
                if configured_devices and not device_parse_issues
                else (
                    f"Managed-device configuration issues: {'; '.join(device_parse_issues[:3])}"
                    if device_parse_issues
                    else "No controllable devices configured yet."
                )
            ),
        },
        {
            "key": "devices_usable",
            "label": "At least one device currently usable",
            "complete": bool(state_usable_device_count),
            "detail": (
                f"{_usable_device_count_label(state_usable_device_count)} available right now."
                if state_usable_device_count
                else "No managed devices are currently usable for control."
            ),
        },
    ]

    unavailable_source_roles = [
        SOURCE_ROLE_LABELS.get(key, key)
        for key in source_attention["unavailable_source_keys"]
    ]
    stale_source_roles = [
        SOURCE_ROLE_LABELS.get(key, key)
        for key in source_attention["stale_source_keys"]
    ]
    source_attention_roles = build_source_attention_role_summary(state, source_mapping, limit=4)
    candidates, top_candidate_name = _command_center_candidate_snapshot(coordinator, state)
    top_candidate_preview = (
        build_candidate_compact_preview(candidates[0], include_warning=True)
        if candidates
        else ""
    )
    review_candidate = next(
        (item for item in candidates if candidate_needs_review(assess_candidate(item))),
        None,
    )
    review_candidate_name = str((review_candidate or {}).get("name") or (review_candidate or {}).get("entity_id") or "").strip()
    review_candidate_preview = (
        build_candidate_compact_preview(review_candidate, include_warning=True)
        if review_candidate
        else ""
    )
    ready_candidate = next(
        (item for item in candidates if not candidate_needs_review(assess_candidate(item))),
        None,
    )
    ready_candidate_name = str((ready_candidate or {}).get("name") or (ready_candidate or {}).get("entity_id") or "").strip()
    ready_candidate_preview = (
        build_candidate_compact_preview(ready_candidate, include_warning=True)
        if ready_candidate
        else ""
    )

    if missing_required_sources:
        phase = "source_setup"
        next_step = (
            f"Open {SOURCES_CONFIGURE_PATH}, finish the missing required source roles, then save and reload the integration."
        )
        summary = "Native setup is blocked on missing required source roles."
    elif blocking_validation_issues or state_stale_data:
        phase = "source_remediation"
        if unavailable_source_roles:
            listed = source_attention_roles if source_attention_roles != "None" else ", ".join(unavailable_source_roles[:6])
            next_step = build_source_repair_step(
                unavailable_source_keys=source_attention["unavailable_source_keys"],
                affected_roles=listed,
            )
        elif state_stale_data and stale_source_roles:
            listed = source_attention_roles if source_attention_roles != "None" else ", ".join(stale_source_roles[:6])
            next_step = build_source_repair_step(
                stale_source_keys=source_attention["stale_source_keys"],
                affected_roles=listed,
            )
        elif state_stale_data and stale_summary:
            next_step = (
                f"Open {SOURCES_CONFIGURE_PATH} or {INTEGRATION_DEVICE_PATH} -> Review diagnostics snapshot, "
                f"then fix the stale source roles. {stale_summary}."
            )
        else:
            next_step = build_source_repair_step(
                blocking_validation_details=summarize_validation_issue_messages(state, severities={"error"}, limit=3),
                affected_roles=source_attention_roles,
            )
        if blocking_fallback_hint:
            next_step += f" {blocking_fallback_hint}"
        summary = "Native setup is waiting on healthy validated source data."
    elif device_parse_issues:
        phase = "device_remediation"
        next_step = (
            f"Open {DEVICES_CONFIGURE_PATH} to repair the managed-device configuration, "
            f"or use {ADVANCED_DEVICES_CONFIGURE_PATH} only if the native forms cannot fix it."
        )
        summary = "Native setup is blocked on managed-device configuration issues."
    elif not configured_devices:
        phase = "device_onboarding"
        if review_candidate_name:
            next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, review unmanaged candidate: "
                f"{review_candidate_preview or review_candidate_name}"
            )
            if ready_candidate_name and ready_candidate_name != review_candidate_name:
                next_step += (
                    f", then promote ready unmanaged candidate: "
                    f"{ready_candidate_preview or ready_candidate_name}"
                )
            next_step += "."
            summary = "Sources are ready; the next milestone is reviewing the current unmanaged backlog in the Managed Devices workspace."
        elif ready_candidate_name or top_candidate_preview or top_candidate_name:
            next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then promote ready unmanaged candidate: "
                f"{ready_candidate_preview or ready_candidate_name or top_candidate_preview or top_candidate_name or 'the next unmanaged candidate'}."
            )
            summary = "Sources are ready; the next milestone is promoting the current unmanaged backlog in the Managed Devices workspace."
        else:
            next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available."
            )
            summary = "Sources are ready; the next milestone is adding controllable devices."
    elif not state_usable_device_count:
        phase = "runtime_readiness"
        next_step = (
            f"Use {INTEGRATION_DEVICE_PATH} -> Review diagnostics snapshot, then return to {DEVICES_CONFIGURE_PATH} "
            "to unblock at least one usable device."
        )
        summary = "Managed Devices exist, but none are currently eligible for control."
    elif state_safe_mode:
        phase = "runtime_readiness"
        next_step = (
            f"Open {SOURCES_CONFIGURE_PATH} and {SUPPORT_CONFIGURE_PATH}, then clear the current safe-mode condition "
            "before treating the integration as production-ready."
        )
        summary = "The native operator flow is mostly built, but runtime is still held in safe mode."
    else:
        phase = "operator_ready"
        next_step = (
            f"Review {PRIMARY_CONFIGURE_PATH} plus {DIAGNOSTICS_DEVICE_ACTIONS_PATH} in the exact "
            "Home Assistant install; keep any follow-up in those native paths."
        )
        summary = "Setup and troubleshooting are available through native Home Assistant surfaces."

    return {
        "phase": phase,
        "summary": summary,
        "next_step": next_step,
        "checklist": checklist,
    }


def _build_support_sections(coordinator: Any) -> tuple[Any, list[dict[str, Any]], list[str], dict[str, Any]]:
    state = coordinator.data
    configured_devices, device_parse_issues = _configured_device_payloads(coordinator.entry)
    operator_readiness = _build_operator_checklist(
        state,
        coordinator.entry,
        configured_devices,
        device_parse_issues,
        coordinator=coordinator,
    )
    return state, configured_devices, device_parse_issues, operator_readiness


def build_detailed_management_handoff(
    configured_devices: list[dict[str, Any]] | None,
    *,
    state: Any | None = None,
) -> str:
    """Return the secondary native device-view handoff for per-device review/audit actions."""
    devices = configured_devices or []
    if not devices:
        return (
            f"Keep {DEVICES_CONFIGURE_PATH} as the Managed Devices workspace: review the unmanaged candidate when one is surfaced, or add the first fixed or variable load manually when no surfaced unmanaged candidate is available; use {DETAILED_MANAGEMENT_PATH} "
            "as the secondary device-page review/audit path once the fleet exists."
        )

    usable_count = int(getattr(state, "usable_device_count", 0) or 0) if state is not None else 0
    if usable_count <= 0:
        return (
            f"Use {DETAILED_MANAGEMENT_PATH} as the secondary device-page review/audit path to inspect each managed device's status, guards, plans, and reset actions, "
            "then return to the Managed Devices workspace to adjust the fleet if needed."
        )

    return (
        f"Use {DETAILED_MANAGEMENT_PATH} as the secondary device-page review/audit path for per-device status, planned actions, guard state, and reset actions when the fleet needs audit detail."
    )


def build_native_support_snapshot(coordinator: Any) -> str:
    """Return the operator diagnostics snapshot for native HA surfaces."""
    state, configured_devices, device_parse_issues, operator_readiness = _build_support_sections(coordinator)
    command_center = build_native_command_center_summary(coordinator)
    release_info = build_release_info(INTEGRATION_VERSION, include_changelog=False)
    install_provenance = build_install_provenance()
    source_attention = build_source_attention_details(state)
    validation_details = source_attention["validation_details"]
    release_update = validation_details.get("release_update", {})
    source_diagnostics = source_attention["source_diagnostics"]
    mapped_sources = [
        f"- {SOURCE_ROLE_LABELS.get(key, key)}: {format_source_binding_label(coordinator.entry.data.get(key))}"
        for key in (
            CONF_SOLAR_POWER_ENTITY,
            CONF_SOLAR_ENERGY_ENTITY,
            CONF_GRID_IMPORT_POWER_ENTITY,
            CONF_GRID_EXPORT_POWER_ENTITY,
            CONF_GRID_IMPORT_ENERGY_ENTITY,
            CONF_GRID_EXPORT_ENERGY_ENTITY,
            CONF_HOME_LOAD_POWER_ENTITY,
            CONF_BATTERY_SOC_ENTITY,
            CONF_BATTERY_CHARGE_POWER_ENTITY,
            CONF_BATTERY_DISCHARGE_POWER_ENTITY,
        )
    ]
    source_health_lines = []
    for key, details in source_diagnostics.items():
        configured_label = format_source_binding_label(coordinator.entry.data.get(key))
        target_label = _source_attention_target_label(key, details, configured_label)
        line = (
            f"- {SOURCE_ROLE_LABELS.get(key, key)}: status={details.get('status') or 'unknown'}, "
            f"age_s={details.get('age_seconds') if details.get('age_seconds') is not None else 'n/a'}, "
            f"issues={len(details.get('issues') or [])}"
        )
        if target_label:
            line += f", mapped={target_label}"
        source_health_lines.append(line)
    unavailable_source_roles = [
        SOURCE_ROLE_LABELS.get(key, key)
        for key in source_attention["unavailable_source_keys"]
    ]
    stale_source_roles = [
        SOURCE_ROLE_LABELS.get(key, key)
        for key in source_attention["stale_source_keys"]
    ]
    runtime_device_details = getattr(state, "device_details", None) or {}
    device_lines = []
    for item in configured_devices:
        runtime = runtime_device_details.get(item.get("key"), {})
        device_label = str(
            runtime.get("name")
            or item.get("name")
            or _humanize_entity_id(str(item.get("entity_id") or "managed_device"))
        ).strip()
        device_lines.append(
            (
                f"- {device_label}: enabled={item.get('enabled')}, "
                f"usable={runtime.get('usable', 'n/a')}, "
                f"status={runtime.get('status', 'n/a')}, "
                f"planned={runtime.get('planned_action', 'n/a')}, "
                f"guard={runtime.get('guard_status', 'n/a')}, "
                f"kind={item.get('kind')}, adapter={item.get('adapter')}, "
                f"priority={item.get('priority')}"
            )
        )
    recent_issues = list(validation_details.get("issues", []))[:5]
    issue_lines = [
        f"- {issue.get('severity', 'info')}: {issue.get('message', issue)}"
        for issue in recent_issues
    ]
    install_fingerprint_lines = [
        (
            f"- {name}: sha256_12={details.get('sha256_12') or 'n/a'}, "
            f"size_bytes={details.get('size_bytes') if details.get('size_bytes') is not None else 'n/a'}, "
            f"exists={details.get('exists')}"
        )
        for name, details in (install_provenance.get("tracked_files") or {}).items()
    ]
    checklist_lines = [
        f"- [{'x' if item.get('complete') else ' '}] {item.get('label')}: {item.get('detail')}"
        for item in operator_readiness.get("checklist", [])
    ]

    sections = [
        "Zero Net Export diagnostics snapshot",
        f"Generated: {dt_util.now().isoformat()}",
        f"Entry title: {coordinator.entry.title}",
        f"Entry id: {coordinator.entry.entry_id}",
        f"Integration version: {INTEGRATION_VERSION}",
        f"Config entry version: {coordinator.entry.version}",
        f"Release summary: {release_info.get('summary', 'n/a')}",
        f"Install provenance: {install_provenance.get('summary', 'n/a')}",
        f"Install consistency: {build_install_consistency_summary(install_provenance)}",
        f"Update visibility: {release_update.get('summary', 'n/a')}",
        "",
        "Installed package fingerprint",
        f"- component_root: {install_provenance.get('component_root', 'n/a')}",
        f"- code_version: {install_provenance.get('code_version', 'n/a')}",
        f"- manifest_version: {install_provenance.get('manifest_version', 'n/a')}",
        f"- manifest_matches_code_version: {install_provenance.get('manifest_matches_code_version', 'n/a')}",
        *install_fingerprint_lines,
        "",
        "Native paths",
        f"- {PRIMARY_CONFIGURE_PATH}",
        f"- {SOURCES_SECTION_LABEL}: {command_center.get('sources_path')}",
        f"- {DEVICES_SECTION_LABEL}: {command_center.get('devices_path')}",
        f"- {POLICY_SECTION_LABEL}: {command_center.get('policy_path')}",
        f"- Live mode shortcut ({POLICY_SECTION_LABEL} device action): {command_center.get('mode_path')}",
        f"- {SUPPORT_SECTION_LABEL}: {command_center.get('support_path')}",
        "",
        "Readiness",
        f"- phase: {operator_readiness.get('phase')}",
        f"- summary: {operator_readiness.get('summary')}",
        f"- next_step: {_normalize_native_path_text(command_center.get('next_action_summary') or operator_readiness.get('next_step'))}",
        *checklist_lines,
        "",
        "Runtime summary",
        f"- control_status: {getattr(state, 'control_status', None)}",
        f"- control_summary: {getattr(state, 'control_summary', None)}",
        f"- health_status: {getattr(state, 'health_status', None)}",
        f"- health_summary: {getattr(state, 'health_summary', None)}",
        f"- safe_mode: {getattr(state, 'safe_mode', None)}",
        f"- stale_data: {getattr(state, 'stale_data', None)}",
        f"- source_mismatch: {getattr(state, 'source_mismatch', None)}",
        f"- battery_below_reserve: {getattr(state, 'battery_below_reserve', None)}",
        f"- confidence: {getattr(state, 'confidence', None)}",
        f"- recommendation: {getattr(state, 'recommendation', None)}",
        f"- last_action_status: {getattr(state, 'last_action_status', None)}",
        f"- last_action_summary: {getattr(state, 'last_action_summary', None)}",
        f"- recent_failure_summary: {getattr(state, 'recent_failure_summary', None)}",
        "",
        "Source roles",
        *mapped_sources,
        "",
        "Source health",
        *(source_health_lines or ["- none"]),
        f"- unavailable roles: {', '.join(unavailable_source_roles) if unavailable_source_roles else 'none'}",
        f"- stale roles: {', '.join(stale_source_roles) if stale_source_roles else 'none'}",
        "",
        DEVICES_SECTION_LABEL,
        f"- total: {getattr(state, 'device_count', 0)}",
        f"- enabled: {getattr(state, 'enabled_device_count', 0)}",
        f"- usable: {getattr(state, 'usable_device_count', 0)}",
        *(device_lines or ["- none configured"]),
        "",
        "Device parse issues",
        *([f"- {issue}" for issue in device_parse_issues] or ["- none"]),
        "",
        "Recent validation issues",
        *(issue_lines or ["- none"]),
    ]
    return "\n".join(sections)


def build_native_operator_readiness(coordinator: Any) -> dict[str, Any]:
    """Return the operator readiness block for native HA surfaces."""
    _, _, _, operator_readiness = _build_support_sections(coordinator)
    return operator_readiness


def normalize_command_center_section(section: str | None) -> str:
    """Return the canonical command-center section label for UI-facing text."""
    text = str(section or "").strip()
    if text in SOURCES_SECTION_ALIASES:
        return SOURCES_SECTION_ALIASES[text]
    if text in DEVICES_SECTION_ALIASES:
        return DEVICES_SECTION_ALIASES[text]
    return text


def build_native_setup_recommendation(
    *,
    missing_source_keys: list[str] | None = None,
    source_attention_roles: str | None = None,
    device_issues: list[str] | None = None,
    has_devices: bool = False,
    readiness_phase: str | None = None,
    candidate_count: int = 0,
    review_needed_count: int = 0,
    managed_attention_count: int = 0,
    blocked_activity_count: int = 0,
) -> dict[str, str]:
    """Return the best current native section for setup follow-through."""
    if missing_source_keys or (source_attention_roles and source_attention_roles != "None"):
        return {
            "recommended_section": SOURCES_SECTION_LABEL,
            "recommended_path": SOURCES_CONFIGURE_PATH,
        }
    if device_issues or not has_devices:
        return {
            "recommended_section": DEVICES_SECTION_LABEL,
            "recommended_path": DEVICES_CONFIGURE_PATH,
        }
    if candidate_count or review_needed_count or managed_attention_count or blocked_activity_count:
        return {
            "recommended_section": DEVICES_SECTION_LABEL,
            "recommended_path": DEVICES_CONFIGURE_PATH,
        }
    if str(readiness_phase or "").strip() == "runtime_readiness":
        return {
            "recommended_section": SUPPORT_SECTION_LABEL,
            "recommended_path": SUPPORT_CONFIGURE_PATH,
        }
    return {
        "recommended_section": POLICY_SECTION_LABEL,
        "recommended_path": POLICY_CONFIGURE_PATH,
    }


def _command_center_guide_fleet_activity_summary(command_center: dict[str, Any]) -> str:
    """Return command-center guide fleet activity with managed/unmanaged grouping."""
    return format_fleet_activity_for_operator(str(command_center.get("fleet_activity_summary") or ""))


def build_native_command_center_guide_text(command_center: dict[str, Any]) -> str:
    """Return the basic setup focused command-center guide text."""
    alert_summary = _normalize_native_path_text(command_center.get("alert_summary"))
    next_action_summary = _normalize_native_path_text(command_center.get("next_action_summary"))
    source_status = _normalize_native_path_text(command_center.get("source_status"))
    source_attention_summary = _normalize_native_path_text(
        command_center.get("source_attention_summary")
    )
    if source_attention_summary.lower().startswith("source blockers:"):
        source_attention_summary = source_attention_summary.split(":", 1)[1].strip()
    source_repair_step = _normalize_native_path_text(command_center.get("source_repair_step"))
    fleet_activity_summary = _command_center_guide_fleet_activity_summary(command_center)
    now_lines = [
        "Now",
        f"- Headline decision: {command_center.get('headline_decision')}",
        f"- Alerts: {alert_summary}",
        f"- Next action: {next_action_summary}",
    ]
    return "\n".join(
        [
            "Zero Net Export command center",
            "",
            *now_lines,
            "",
            "Structured control board",
            f"- Energy state: {command_center.get('energy_state_summary')}",
            f"- Control decision: {command_center.get('control_decision_summary')}",
            f"- Control outcome: {command_center.get('control_outcome_summary')}",
            f"- Fleet activity: {fleet_activity_summary}",
            "",
            "Setup check",
            f"- Sensors: {source_status}",
            f"- Source roles: {command_center.get('source_mapping_summary')}",
            f"- Controls: {command_center.get('policy_status')}",
            f"- Diagnostics: {command_center.get('support_status')}",
            f"- Source blockers: {source_attention_summary}",
            f"- Repair path: {source_repair_step}",
            f"- Recommended section: {command_center.get('recommended_section')}",
            "",
            "Command-center use",
            "- Live setup and current operating picture.",
            "- Finish source roles and core control checks in the command center; when fleet work is next, continue in the Managed Devices workspace.",
            "",
            "Native paths",
            f"- Sensors: {command_center.get('sources_path')}",
            f"- Controls: {command_center.get('policy_path')}",
            f"- Live mode shortcut (Controls device action): {command_center.get('mode_path')}",
            f"- Managed Devices: {command_center.get('devices_path')}",
            f"- Diagnostics: {command_center.get('support_path')}",
            "",
            "Bucket ownership",
            "- Sensors owns source roles and source health.",
            "- Controls owns target export, reserve, deadband, and live mode.",
            f"- Managed Devices owns fleet onboarding, promotion, edits, enablement, and removal: {command_center.get('devices_path')}",
            f"- Diagnostics owns troubleshooting, repairs, and install validation: {command_center.get('support_path')}.",
        ]
    )


def _decision_mode_text(state: Any) -> str:
    current_mode = str(getattr(state, "mode", "") or "")
    return MODE_LABELS.get(current_mode, current_mode or "Unknown mode")


def _build_headline_decision(
    state: Any,
    *,
    missing_required_sources: list[str],
    runtime_source_attention: bool,
    source_attention_summary: str,
    blocking_validation_details: str,
    configured_devices: list[dict[str, Any]],
) -> str:
    if missing_required_sources:
        return "Setup incomplete, waiting for required sensors."
    if runtime_source_attention:
        if source_attention_summary != "None":
            return "Source data needs attention, control is constrained."
        if blocking_validation_details != "None":
            return "Source validation failed, control is constrained."
        return "Source data needs attention before control can continue."
    if state is None:
        return "Waiting for runtime state to load."

    if getattr(state, "battery_below_reserve", False):
        return "Battery reserve protected, not engaging load."

    planned_action_count = int(getattr(state, "planned_action_count", 0) or 0)
    executable_action_count = int(getattr(state, "executable_action_count", 0) or 0)
    active_controlled_power_w = float(getattr(state, "active_controlled_power_w", 0) or 0)
    blocked_planned_action_count = int(getattr(state, "blocked_planned_action_count", 0) or 0)
    usable_device_count = int(getattr(state, "usable_device_count", 0) or 0)
    target_export_w = float(getattr(state, "target_export_w", 0) or 0)
    deadband_w = float(getattr(state, "deadband_w", 0) or 0)
    grid_export_power_w = getattr(state, "grid_export_power_w", None)
    grid_import_power_w = getattr(state, "grid_import_power_w", None)
    export_error_w = getattr(state, "export_error_w", None)

    if executable_action_count > 0:
        if grid_export_power_w is not None and float(grid_export_power_w) > target_export_w + deadband_w:
            return "Export too high, engaging load."
        if grid_import_power_w is not None and float(grid_import_power_w) > deadband_w:
            return "Import detected, shedding load."
        return "Control adjustment ready, applying managed-device action."

    if planned_action_count > 0 or blocked_planned_action_count > 0:
        if usable_device_count <= 0 and configured_devices:
            return "Export outside target, no eligible device available."
        control_reason = str(getattr(state, "control_reason", "") or "").lower()
        if blocked_planned_action_count > 0 or "guard" in control_reason or "wait" in control_reason:
            return "Action queued, waiting for device guard."
        return "Control change planned, waiting to execute."

    if export_error_w is not None and abs(float(export_error_w)) <= deadband_w:
        if active_controlled_power_w > 0:
            return "Near target, holding current managed load."
        return "Near target, holding."

    if grid_export_power_w is not None and float(grid_export_power_w) > target_export_w + deadband_w:
        if usable_device_count <= 0:
            return "Export too high, no eligible device available."
        return "Export above target, waiting for an eligible managed device."

    if grid_import_power_w is not None and float(grid_import_power_w) > deadband_w:
        if active_controlled_power_w > 0:
            return "Import detected, holding managed load until the next control window."
        return "Import detected, not engaging load."

    if active_controlled_power_w > 0:
        return "Managed load active, holding current fleet posture."

    return str(
        getattr(state, "reason", "")
        or getattr(state, "control_reason", "")
        or getattr(state, "status", "")
        or f"{_decision_mode_text(state)} state available."
    )


def _command_center_candidate_snapshot(coordinator: Any, state: Any) -> tuple[list[dict[str, str]], str]:
    hass = getattr(coordinator, "hass", None) if coordinator is not None else None
    states = getattr(getattr(hass, "states", None), "async_all", None)
    if not callable(states):
        return [], ""
    managed_ids = {
        str(detail.get("entity_id"))
        for detail in ((getattr(state, "device_details", None) or {}) or {}).values()
        if detail.get("entity_id")
    }
    candidates = discover_candidate_devices(states(), managed_ids)
    top_candidate_name = str(candidates[0].get("name") or candidates[0].get("entity_id") or "").strip() if candidates else ""
    return candidates, top_candidate_name


def _command_center_candidate_focus_text(candidate: dict[str, Any] | None) -> str:
    if not candidate:
        return "the surfaced candidate"
    name = str(candidate.get("name") or candidate.get("entity_id") or "the surfaced candidate").strip()
    kind = str(candidate.get("kind") or "candidate").strip()
    review_hint = build_candidate_review_hint(candidate, include_warning=False)
    focus = f"{name} ({kind})"
    return f"{focus} | {review_hint}" if review_hint else focus


def _primary_candidate_focus(candidates: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    review_candidate = next(
        (item for item in candidates if candidate_needs_review(assess_candidate(item))),
        None,
    )
    primary_candidate = review_candidate or (candidates[0] if candidates else None)
    return primary_candidate, _command_center_candidate_focus_text(primary_candidate)


def _command_center_device_status_with_unmanaged_context(
    base_status: str,
    *,
    managed_count: int,
    candidate_count: int,
    fixed_candidate_count: int,
    variable_candidate_count: int,
    review_needed_count: int,
    fixed_review_count: int,
    variable_review_count: int,
    top_candidate_name: str,
    top_candidate_preview: str,
    review_candidate_name: str,
    review_candidate_preview: str,
    ready_candidate_name: str,
    ready_candidate_preview: str,
    managed_attention_count: int = 0,
    blocked_activity_count: int = 0,
    active_managed_count: int = 0,
    active_managed_power_w: float = 0.0,
    attention_device_preview: str = "",
    blocked_device_preview: str = "",
    planned_device_preview: str = "",
    active_device_preview: str = "",
    source_blocked: bool = False,
) -> str:
    def _clip_part(text: str, *, max_chars: int) -> str:
        normalized = " ".join(str(text).split())
        if len(normalized) <= max_chars:
            return normalized
        if max_chars <= 3:
            return normalized[:max_chars]
        return normalized[: max_chars - 3].rstrip() + "..."

    normalized_base_status = " ".join(str(base_status or "").split())
    generic_managed_status = normalized_base_status.rstrip(".") in {
        "1 configured device available",
        f"{managed_count} configured device available",
        f"{managed_count} configured devices available",
    } or (
        managed_count > 1 and normalized_base_status.rstrip(".") == f"{managed_count} configured devices available"
    )
    summary = _managed_count_label(managed_count) if generic_managed_status else base_status
    managed_parts: list[str] = []
    compact_active_device_preview = active_device_preview and "." not in active_device_preview.partition(" ")[0]
    base_has_unmanaged_label = managed_count > 0 and candidate_count > 0 and _unmanaged_count_label(candidate_count) in normalized_base_status
    base_has_source_blockers = SOURCE_BLOCKER_ACTIVE_LABEL in normalized_base_status

    def _compact_focus_part(prefix: str, preview: str, *, max_chars: int) -> str:
        focus_part = f"{prefix}{preview}".strip()
        return _clip_state_part(focus_part, max_chars=max_chars) or _clip_part(focus_part, max_chars=max_chars)

    def _compact_managed_base_parts(*, max_chars: int) -> list[str]:
        if not (generic_managed_status and managed_count > 0):
            return [_clip_part(base_status, max_chars=max_chars)]

        compact_parts: list[str] = [_managed_count_label(managed_count)]
        if managed_attention_count:
            compact_parts.append(
                "1 managed device needs attention"
                if managed_attention_count == 1
                else f"{managed_attention_count} managed devices need attention"
            )
            if attention_device_preview:
                compact_parts.append(
                    _compact_focus_part("attention first ", attention_device_preview, max_chars=min(max_chars, 52))
                )
        if blocked_activity_count:
            compact_parts.append(_blocked_activity_count_label(blocked_activity_count))
            if blocked_device_preview:
                compact_parts.append(
                    _compact_focus_part("blocked ", blocked_device_preview, max_chars=min(max_chars, 52))
                )
        if planned_device_preview:
            compact_parts.append(
                _compact_focus_part("plan ", planned_device_preview, max_chars=min(max_chars, 52))
            )
        if active_managed_count:
            if active_managed_power_w > 0 and not (candidate_count > 0 and active_device_preview):
                compact_parts.append(f"active load {active_managed_power_w:g} W")
            compact_parts.append(
                "1 active managed device"
                if active_managed_count == 1
                else f"{active_managed_count} active managed devices"
            )
            if compact_active_device_preview and candidate_count > 1 and 0 < review_needed_count < candidate_count:
                compact_parts.append(
                    _compact_focus_part(
                        "active device ",
                        active_device_preview,
                        max_chars=min(max_chars, 48),
                    )
                )
        return compact_parts

    if generic_managed_status and managed_count > 0:
        if managed_attention_count:
            managed_parts.append(
                "1 managed device needs attention"
                if managed_attention_count == 1
                else f"{managed_attention_count} managed devices need attention"
            )
            if attention_device_preview:
                managed_parts.append(f"attention first {attention_device_preview}")
        if blocked_activity_count:
            managed_parts.append(_blocked_activity_count_label(blocked_activity_count))
            if blocked_device_preview:
                managed_parts.append(f"blocked {blocked_device_preview}")
        if planned_device_preview:
            managed_parts.append(f"plan {planned_device_preview}")
        if active_managed_count:
            if active_managed_power_w > 0:
                managed_parts.append(f"active load {active_managed_power_w:g} W")
            managed_parts.append(
                "1 active managed device"
                if active_managed_count == 1
                else f"{active_managed_count} active managed devices"
            )
            if active_device_preview:
                managed_parts.append(f"active device {active_device_preview}")
    if managed_parts:
        summary = "; ".join([summary, *managed_parts])
    if candidate_count <= 0:
        if generic_managed_status and managed_count > 0:
            summary += "; no unmanaged candidates"
            if source_blocked:
                summary += f"; {SOURCE_BLOCKER_ACTIVE_LABEL}"
            if len(summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
                return summary

            compact_parts = [*_compact_managed_base_parts(max_chars=40), "no unmanaged candidates"]
            if source_blocked:
                compact_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
            compact_summary = "; ".join(compact_parts)
            if len(compact_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
                return compact_summary

            fallback_parts = [_managed_count_label(managed_count)]
            if managed_attention_count:
                fallback_parts.append(
                    "1 managed device needs attention"
                    if managed_attention_count == 1
                    else f"{managed_attention_count} managed devices need attention"
                )
                if attention_device_preview:
                    fallback_parts.append(
                        _compact_focus_part("attention first ", attention_device_preview, max_chars=48)
                    )
            if blocked_activity_count:
                fallback_parts.append(_blocked_activity_count_label(blocked_activity_count))
                if blocked_device_preview:
                    fallback_parts.append(_compact_focus_part("blocked ", blocked_device_preview, max_chars=48))
            if planned_device_preview:
                fallback_parts.append(_compact_focus_part("plan ", planned_device_preview, max_chars=48))
            if active_managed_count:
                fallback_parts.append(
                    "1 active managed device"
                    if active_managed_count == 1
                    else f"{active_managed_count} active managed devices"
                )
            fallback_parts.append("no unmanaged candidates")
            if source_blocked:
                fallback_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
            fallback_summary = "; ".join(fallback_parts)
            if len(fallback_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
                return fallback_summary

            tighter_fallback_parts = [*_compact_managed_base_parts(max_chars=32), "no unmanaged candidates"]
            if source_blocked:
                tighter_fallback_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
            tighter_fallback_summary = "; ".join(tighter_fallback_parts)
            if len(tighter_fallback_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
                return tighter_fallback_summary
            return "; ".join(
                [
                    _managed_count_label(managed_count),
                    *(
                        [
                            "1 managed device needs attention"
                            if managed_attention_count == 1
                            else f"{managed_attention_count} managed devices need attention"
                        ]
                        if managed_attention_count
                        else []
                    ),
                    *(
                        [_blocked_activity_count_label(blocked_activity_count)]
                        if blocked_activity_count
                        else []
                    ),
                    *(
                        [
                            "1 active managed device"
                            if active_managed_count == 1
                            else f"{active_managed_count} active managed devices"
                        ]
                        if active_managed_count
                        else []
                    ),
                    "no unmanaged candidates",
                    *([SOURCE_BLOCKER_ACTIVE_LABEL] if source_blocked else []),
                ]
            )
        return f"{summary}; {SOURCE_BLOCKER_ACTIVE_LABEL}" if source_blocked else summary
    unmanaged_label = _unmanaged_count_label(candidate_count)
    if not base_has_unmanaged_label:
        summary += f"; {unmanaged_label}"
    if source_blocked and not (generic_managed_status and base_has_source_blockers):
        summary += f"; {SOURCE_BLOCKER_ACTIVE_LABEL}"
    ready_candidate_count = max(candidate_count - review_needed_count, 0)
    fixed_ready_count = max(fixed_candidate_count - fixed_review_count, 0)
    variable_ready_count = max(variable_candidate_count - variable_review_count, 0)
    backlog_parts = _candidate_kind_backlog_mix_parts(
        fixed_candidate_count=fixed_candidate_count,
        variable_candidate_count=variable_candidate_count,
        fixed_review_count=fixed_review_count,
        variable_review_count=variable_review_count,
        fixed_ready_count=fixed_ready_count,
        variable_ready_count=variable_ready_count,
    )
    single_kind_backlog_parts = _single_kind_candidate_backlog_parts(
        fixed_candidate_count=fixed_candidate_count,
        variable_candidate_count=variable_candidate_count,
        fixed_review_count=fixed_review_count,
        variable_review_count=variable_review_count,
        fixed_ready_count=fixed_ready_count,
        variable_ready_count=variable_ready_count,
    )
    single_kind_overflow_backlog_parts = (
        backlog_parts
        if backlog_parts and bool(fixed_candidate_count) != bool(variable_candidate_count)
        else single_kind_backlog_parts if single_kind_backlog_parts and not backlog_parts else []
    )
    if backlog_parts:
        for backlog_part in backlog_parts:
            summary += f"; {backlog_part}"
    else:
        for backlog_part in single_kind_backlog_parts:
            summary += f"; {backlog_part}"
    if review_needed_count:
        summary += f"; {_count_label(review_needed_count, 'needs review', 'need review')}"
    if ready_candidate_count:
        summary += f"; {_count_label(ready_candidate_count, 'ready to promote', 'ready to promote')}"
    if review_candidate_preview and review_candidate_name:
        summary += f"; review {review_candidate_preview}"
    if ready_candidate_preview and ready_candidate_name:
        summary += f"; ready {ready_candidate_preview}"
    if top_candidate_preview and top_candidate_name not in {review_candidate_name, ready_candidate_name}:
        summary += f"; surfaced {top_candidate_preview}"
    if len(summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return summary

    compact_parts: list[str] = [
        *_compact_managed_base_parts(max_chars=72),
        *([] if (generic_managed_status and base_has_unmanaged_label) else [_compact_unmanaged_count_label(candidate_count)]),
    ]
    if source_blocked and not (generic_managed_status and base_has_source_blockers):
        compact_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
    if backlog_parts:
        compact_parts.extend(backlog_parts)
    elif single_kind_backlog_parts:
        compact_parts.extend(single_kind_backlog_parts)
    if review_needed_count:
        compact_parts.append(_count_label(review_needed_count, "needs review", "need review"))
        if review_candidate_preview:
            compact_parts.append(f"review {review_candidate_preview}")
        elif review_candidate_name:
            compact_parts.append(f"review {review_candidate_name}")
    if ready_candidate_count:
        compact_parts.append(_count_label(ready_candidate_count, "ready to promote", "ready to promote"))
        if ready_candidate_preview:
            compact_parts.append(f"ready {ready_candidate_preview}")
        elif ready_candidate_name:
            compact_parts.append(f"ready {ready_candidate_name}")
    compact_summary = "; ".join(compact_parts)
    if single_kind_overflow_backlog_parts:
        single_kind_compact_parts: list[str] = [
            *_compact_managed_base_parts(max_chars=72),
            *([] if (generic_managed_status and base_has_unmanaged_label) else [_compact_unmanaged_count_label(candidate_count)]),
        ]
        if source_blocked and not (generic_managed_status and base_has_source_blockers):
            single_kind_compact_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
        single_kind_compact_parts.extend(single_kind_overflow_backlog_parts)
        if review_needed_count:
            single_kind_compact_parts.append(_count_label(review_needed_count, "needs review", "need review"))
        if ready_candidate_count:
            single_kind_compact_parts.append(_count_label(ready_candidate_count, "ready to promote", "ready to promote"))
        if review_candidate_preview:
            single_kind_compact_parts.append(f"review {review_candidate_preview}")
        elif review_candidate_name:
            single_kind_compact_parts.append(f"review {review_candidate_name}")
        if ready_candidate_preview:
            single_kind_compact_parts.append(f"ready {ready_candidate_preview}")
        elif ready_candidate_name:
            single_kind_compact_parts.append(f"ready {ready_candidate_name}")
        single_kind_compact_summary = "; ".join(single_kind_compact_parts)
        if len(single_kind_compact_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return single_kind_compact_summary
    if len(compact_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS and not single_kind_overflow_backlog_parts:
        return compact_summary

    if single_kind_overflow_backlog_parts:
        single_kind_compact_parts: list[str] = [
            *_compact_managed_base_parts(max_chars=72),
            _compact_unmanaged_count_label(candidate_count),
        ]
        if source_blocked:
            single_kind_compact_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
        single_kind_compact_parts.extend(single_kind_overflow_backlog_parts)
        if review_needed_count:
            single_kind_compact_parts.append(_count_label(review_needed_count, "needs review", "need review"))
        if ready_candidate_count:
            single_kind_compact_parts.append(_count_label(ready_candidate_count, "ready to promote", "ready to promote"))
        if review_candidate_preview:
            single_kind_compact_parts.append(f"review {review_candidate_preview}")
        elif review_candidate_name:
            single_kind_compact_parts.append(f"review {review_candidate_name}")
        if ready_candidate_preview:
            single_kind_compact_parts.append(f"ready {ready_candidate_preview}")
        elif ready_candidate_name:
            single_kind_compact_parts.append(f"ready {ready_candidate_name}")
        single_kind_compact_summary = "; ".join(single_kind_compact_parts)
        if len(single_kind_compact_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return single_kind_compact_summary

        single_kind_named_parts: list[str] = [
            *_compact_managed_base_parts(max_chars=56),
            *([] if (generic_managed_status and base_has_unmanaged_label) else [_compact_unmanaged_count_label(candidate_count)]),
        ]
        if source_blocked and not (generic_managed_status and base_has_source_blockers):
            single_kind_named_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
        single_kind_named_parts.extend(single_kind_overflow_backlog_parts)
        if review_needed_count:
            single_kind_named_parts.append(_count_label(review_needed_count, "needs review", "need review"))
        if ready_candidate_count:
            single_kind_named_parts.append(_count_label(ready_candidate_count, "ready to promote", "ready to promote"))
        if review_candidate_preview:
            single_kind_named_parts.append(f"review {review_candidate_preview}")
        elif review_candidate_name:
            single_kind_named_parts.append(f"review {review_candidate_name}")
        if ready_candidate_preview:
            single_kind_named_parts.append(f"ready {ready_candidate_preview}")
        elif ready_candidate_name:
            single_kind_named_parts.append(f"ready {ready_candidate_name}")
        single_kind_named_summary = "; ".join(single_kind_named_parts)
        if len(single_kind_named_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return single_kind_named_summary

    clipped_compact_parts = [
        _clip_review_ready_state_part(part, max_chars=72)
        if part.startswith(("review ", "ready "))
        else _clip_part(part, max_chars=72)
        if part.startswith(("surfaced ",))
        else part
        for part in compact_parts
    ]
    clipped_compact_summary = "; ".join(clipped_compact_parts)
    if len(clipped_compact_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return clipped_compact_summary

    essential_parts: list[str] = [
        *_compact_managed_base_parts(max_chars=48),
        *([] if (generic_managed_status and base_has_unmanaged_label) else [_compact_unmanaged_count_label(candidate_count)]),
    ]
    if source_blocked and not (generic_managed_status and base_has_source_blockers):
        essential_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
    if backlog_parts:
        essential_parts.extend(backlog_parts)
    elif single_kind_backlog_parts:
        essential_parts.extend(single_kind_backlog_parts)
    if review_needed_count:
        essential_parts.append(_count_label(review_needed_count, "needs review", "need review"))
    if ready_candidate_count:
        essential_parts.append(_count_label(ready_candidate_count, "ready to promote", "ready to promote"))
    if review_candidate_preview:
        essential_parts.append(_clip_review_ready_state_part(f"review {review_candidate_preview}", max_chars=48))
    elif review_candidate_name:
        essential_parts.append(_clip_review_ready_state_part(f"review {review_candidate_name}", max_chars=48))
    if ready_candidate_preview:
        essential_parts.append(_clip_review_ready_state_part(f"ready {ready_candidate_preview}", max_chars=48))
    elif ready_candidate_name:
        essential_parts.append(_clip_review_ready_state_part(f"ready {ready_candidate_name}", max_chars=48))

    essential_summary = "; ".join(essential_parts)
    if len(essential_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return essential_summary

    if single_kind_overflow_backlog_parts:
        single_kind_parts: list[str] = [
            *_compact_managed_base_parts(max_chars=40),
            *([] if (generic_managed_status and base_has_unmanaged_label) else [_compact_unmanaged_count_label(candidate_count)]),
        ]
        if source_blocked and not (generic_managed_status and base_has_source_blockers):
            single_kind_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
        single_kind_parts.extend(single_kind_overflow_backlog_parts)
        if review_needed_count:
            single_kind_parts.append(_count_label(review_needed_count, "needs review", "need review"))
            if review_candidate_preview:
                single_kind_parts.append(f"review {review_candidate_preview}")
            elif review_candidate_name:
                single_kind_parts.append(f"review {review_candidate_name}")
        if ready_candidate_count:
            single_kind_parts.append(_count_label(ready_candidate_count, "ready to promote", "ready to promote"))
            if ready_candidate_preview:
                single_kind_parts.append(f"ready {ready_candidate_preview}")
            elif ready_candidate_name:
                single_kind_parts.append(f"ready {ready_candidate_name}")
        single_kind_summary = "; ".join(single_kind_parts)
        if len(single_kind_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return single_kind_summary

        concise_single_kind_parts: list[str] = [
            *_compact_managed_base_parts(max_chars=40),
            *([] if (generic_managed_status and base_has_unmanaged_label) else [_compact_unmanaged_count_label(candidate_count)]),
        ]
        if source_blocked and not (generic_managed_status and base_has_source_blockers):
            concise_single_kind_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
        concise_single_kind_parts.extend(single_kind_overflow_backlog_parts)
        if review_needed_count:
            concise_single_kind_parts.append(_count_label(review_needed_count, "needs review", "need review"))
        if ready_candidate_count:
            concise_single_kind_parts.append(_count_label(ready_candidate_count, "ready to promote", "ready to promote"))
        if review_candidate_preview:
            concise_single_kind_parts.append(f"review {review_candidate_preview}")
        elif review_candidate_name:
            concise_single_kind_parts.append(f"review {review_candidate_name}")
        if ready_candidate_preview:
            concise_single_kind_parts.append(f"ready {ready_candidate_preview}")
        elif ready_candidate_name:
            concise_single_kind_parts.append(f"ready {ready_candidate_name}")
        concise_single_kind_summary = "; ".join(concise_single_kind_parts)
        if len(concise_single_kind_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return concise_single_kind_summary

        clipped_single_kind_parts = [
            _clip_review_ready_state_part(part, max_chars=48)
            if part.startswith(("review ", "ready "))
            else part
            for part in concise_single_kind_parts
        ]
        clipped_single_kind_summary = "; ".join(clipped_single_kind_parts)
        if len(clipped_single_kind_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return clipped_single_kind_summary

    minimal_parts: list[str] = [
        *_compact_managed_base_parts(max_chars=40),
        *([] if (generic_managed_status and base_has_unmanaged_label) else [_compact_unmanaged_count_label(candidate_count)]),
    ]
    if source_blocked and not (generic_managed_status and base_has_source_blockers):
        minimal_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
    if review_needed_count:
        minimal_parts.append(_count_label(review_needed_count, "needs review", "need review"))
        minimal_parts.append(
            _clip_review_ready_state_part(
                f"review {(review_candidate_preview or review_candidate_name)}",
                max_chars=36,
            )
        )
    if ready_candidate_count:
        minimal_parts.append(_count_label(ready_candidate_count, "ready to promote", "ready to promote"))
        minimal_parts.append(
            _clip_review_ready_state_part(
                f"ready {(ready_candidate_preview or ready_candidate_name)}",
                max_chars=36,
            )
        )
    minimal_summary = "; ".join(part for part in minimal_parts if part)
    if len(minimal_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return minimal_summary

    tighter_minimal_parts: list[str] = [_managed_count_label(managed_count)]
    if managed_attention_count:
        tighter_minimal_parts.append(
            "1 managed device needs attention"
            if managed_attention_count == 1
            else f"{managed_attention_count} managed devices need attention"
        )
        if attention_device_preview:
            tighter_minimal_parts.append(
                _compact_focus_part("attention first ", attention_device_preview, max_chars=20)
            )
    if blocked_activity_count and not blocked_device_preview:
        tighter_minimal_parts.append(_blocked_activity_count_label(blocked_activity_count))
    if blocked_device_preview:
        tighter_minimal_parts.append(_compact_focus_part("blocked ", blocked_device_preview, max_chars=20))
    if planned_device_preview:
        tighter_minimal_parts.append(_compact_focus_part("plan ", planned_device_preview, max_chars=20))
    if active_managed_count:
        tighter_minimal_parts.append(
            "1 active managed device"
            if active_managed_count == 1
            else f"{active_managed_count} active managed devices"
        )
        if active_device_preview:
            tighter_minimal_parts.append(_compact_focus_part("active device ", active_device_preview, max_chars=20))
    if not (generic_managed_status and base_has_unmanaged_label):
        tighter_minimal_parts.append(_compact_unmanaged_count_label(candidate_count))
    if source_blocked and not (generic_managed_status and base_has_source_blockers):
        tighter_minimal_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
    if review_needed_count:
        tighter_minimal_parts.append(_count_label(review_needed_count, "needs review", "need review"))
        tighter_minimal_parts.append(
            _clip_review_ready_state_part(
                f"review {(review_candidate_preview or review_candidate_name)}",
                max_chars=20,
            )
        )
    if ready_candidate_count:
        tighter_minimal_parts.append(_count_label(ready_candidate_count, "ready to promote", "ready to promote"))
        tighter_minimal_parts.append(
            _clip_review_ready_state_part(
                f"ready {(ready_candidate_preview or ready_candidate_name)}",
                max_chars=20,
            )
        )
    tighter_minimal_summary = "; ".join(part for part in tighter_minimal_parts if part)
    if len(tighter_minimal_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return tighter_minimal_summary

    return _clip_part(tighter_minimal_summary or minimal_summary or compact_summary or summary, max_chars=MAX_NATIVE_SENSOR_STATE_CHARS)


def _restore_active_device_under_overflow(
    summary: str,
    *,
    active_managed_count: int,
    active_device_preview: str,
    active_device_distinct: bool = False,
    source_blocked: bool = False,
) -> str:
    if (
        not summary
        or active_managed_count <= 0
        or not active_device_preview
        or "active device " in summary
        or ("review " not in summary and "ready " not in summary)
    ):
        return summary

    if (
        active_managed_count <= 1
        and (not active_device_distinct or not source_blocked)
        and "blocked " in summary
        and (
            "fixed backlog " in summary
            or "variable backlog " in summary
            or "needs review" in summary
            or "need review" in summary
            or "ready to promote" in summary
        )
    ):
        return summary

    active_device_part = _clip_state_part(
        f"active device {active_device_preview}",
        max_chars=48,
    ) or f"active device {active_device_preview}"
    parts = [part.strip() for part in summary.split("|") if part.strip()]
    if active_device_part in parts:
        return summary

    insertion_index = next(
        (
            index + 1
            for index, part in enumerate(parts)
            if part.startswith(("active load ",))
            or _matches_count_label(part, "active managed device", "active managed devices")
        ),
        next(
            (
                index + 1
                for index, part in enumerate(parts)
                if part.startswith(("attention first ", "blocked ", "plan "))
            ),
            len(parts),
        ),
    )

    candidate_parts = list(parts)
    candidate_parts.insert(insertion_index, active_device_part)
    candidate_summary = " | ".join(candidate_parts)
    if len(candidate_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return candidate_summary

    removable_matchers = (
        lambda part: part.startswith("active load "),
        lambda part: _matches_count_label(part, "fixed candidate"),
        lambda part: _matches_count_label(part, "variable candidate"),
        lambda part: _matches_count_label(part, "fixed review"),
        lambda part: _matches_count_label(part, "variable review"),
        lambda part: part.startswith("fixed backlog "),
        lambda part: part.startswith("variable backlog "),
        lambda part: part.startswith(("enabled ", "disabled ", "usable ")),
        lambda part: part.endswith(" W nominal"),
        lambda part: _matches_count_label(part, "fixed managed"),
        lambda part: _matches_count_label(part, "variable managed"),
        lambda part: _matches_count_label(part, "planned action"),
        lambda part: part.startswith("plan "),
    )
    for matcher in removable_matchers:
        if len(candidate_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            break
        for index, part in enumerate(list(candidate_parts)):
            if part == active_device_part:
                continue
            if matcher(part):
                del candidate_parts[index]
                candidate_summary = " | ".join(candidate_parts)
                break

    return candidate_summary if len(candidate_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS else summary


def _restore_ready_promotion_count_under_overflow(
    summary: str,
    *,
    review_needed_count: int,
    ready_candidate_count: int,
) -> str:
    if (
        not summary
        or review_needed_count
        or ready_candidate_count <= 0
        or "ready to promote" in summary
        or "ready " not in summary
    ):
        return summary

    ready_count_part = (
        "1 ready to promote"
        if ready_candidate_count == 1
        else f"{ready_candidate_count} ready to promote"
    )
    parts = [part.strip() for part in summary.split("|") if part.strip()]
    if ready_count_part in parts:
        return summary

    ready_preview_index = next(
        (index for index, part in enumerate(parts) if part.startswith("ready ")),
        None,
    )
    if ready_preview_index is None:
        return summary

    candidate_parts = list(parts)
    candidate_parts.insert(ready_preview_index, ready_count_part)
    candidate_summary = " | ".join(candidate_parts)
    if len(candidate_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return candidate_summary

    without_active_load = [part for part in candidate_parts if not part.startswith("active load ")]
    without_active_load_summary = " | ".join(without_active_load)
    if len(without_active_load_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return without_active_load_summary

    return summary


def _build_command_center_fleet_activity_summary(
    state: Any,
    *,
    candidate_count: int,
    fixed_candidate_count: int,
    variable_candidate_count: int,
    review_needed_count: int,
    fixed_review_count: int,
    variable_review_count: int,
    review_candidate_name: str,
    review_candidate_preview: str,
    ready_candidate_name: str,
    ready_candidate_preview: str,
    top_candidate_name: str,
    top_candidate_preview: str,
    source_blocked: bool,
    configured_managed_count: int = 0,
) -> str:
    device_details = list((getattr(state, "device_details", {}) or {}).values()) if state is not None else []
    runtime_device_count_known = state is not None and hasattr(state, "device_count")
    managed_count = int(getattr(state, "device_count", 0) or 0) if state is not None else 0
    if not runtime_device_count_known and configured_managed_count > managed_count:
        managed_count = configured_managed_count
    enabled_count = int(getattr(state, "enabled_device_count", 0) or 0) if state is not None else 0
    usable_count = int(getattr(state, "usable_device_count", 0) or 0) if state is not None else 0
    if device_details:
        managed_count = max(managed_count, len(device_details))
        enabled_count = max(
            enabled_count,
            sum(1 for detail in device_details if detail.get("effective_enabled", detail.get("enabled", True))),
        )
        usable_count = max(usable_count, sum(1 for detail in device_details if detail.get("usable") is True))
    disabled_count = max(managed_count - enabled_count, 0)
    kind_known, fixed_managed_count, variable_managed_count, nominal_power_w = _managed_runtime_mix(state)
    active_managed_count, active_managed_power_w = _managed_runtime_activity(state)
    first_attention_device = _first_runtime_device_detail(
        state,
        predicate=_runtime_device_needs_attention,
    )
    attention_device_count = (
        sum(1 for detail in (getattr(state, "device_details", {}) or {}).values() if _runtime_device_needs_attention(detail))
        if state is not None
        else 0
    )
    first_blocked_device = _first_runtime_device_detail(
        state,
        predicate=_runtime_device_has_blocked_activity,
    )
    blocked_focus_device = _first_distinct_runtime_device_detail(
        state,
        predicate=_runtime_device_has_blocked_activity,
        excluded=(first_attention_device,),
    ) or first_blocked_device
    blocked_activity_count = (
        sum(1 for detail in (getattr(state, "device_details", {}) or {}).values() if _runtime_device_has_blocked_activity(detail))
        if state is not None
        else 0
    )
    if state is not None:
        blocked_activity_count = max(
            blocked_activity_count,
            int(getattr(state, "blocked_planned_action_count", 0) or 0),
        )
    managed_attention_count = attention_device_count
    first_planned_device = _first_runtime_device_detail(
        state,
        predicate=_runtime_device_has_active_plan,
    )
    planned_focus_device = _first_distinct_runtime_device_detail(
        state,
        predicate=_runtime_device_has_active_plan,
        excluded=(first_attention_device,),
    ) or first_planned_device
    attention_focus_label = _command_center_managed_snapshot_focus_label(first_attention_device)
    attention_covers_blocked_focus = bool(
        first_attention_device
        and blocked_focus_device
        and _same_runtime_device(first_attention_device, blocked_focus_device)
    )
    attention_covers_planned_focus = bool(
        first_attention_device
        and planned_focus_device
        and _same_runtime_device(first_attention_device, planned_focus_device)
    )
    first_active_device = _first_runtime_device_detail(
        state,
        predicate=lambda detail: detail.get("observed_active") is True,
    )
    active_focus_device = _first_distinct_runtime_device_detail(
        state,
        predicate=lambda detail: detail.get("observed_active") is True,
        excluded=(first_attention_device, blocked_focus_device, planned_focus_device),
    ) or first_active_device
    suppress_planned_focus = bool(
        planned_focus_device
        and first_attention_device
        and first_active_device
        and _same_runtime_device(planned_focus_device, first_attention_device)
        and not _same_runtime_device(planned_focus_device, first_active_device)
    )
    planned_activity_count = (
        sum(1 for detail in (getattr(state, "device_details", {}) or {}).values() if _runtime_device_has_active_plan(detail))
        if state is not None
        else 0
    )
    managed_attention_count = max(managed_attention_count, blocked_activity_count, planned_activity_count)

    summary_parts: list[str] = []

    ready_candidate_count = max(candidate_count - review_needed_count, 0)
    fixed_ready_count = max(fixed_candidate_count - fixed_review_count, 0)
    variable_ready_count = max(variable_candidate_count - variable_review_count, 0)
    runtime_inventory_known = state is not None
    show_inventory_context = runtime_inventory_known and managed_count > 0 and candidate_count <= 0
    show_quiet_managed_inventory_context = bool(
        runtime_inventory_known
        and managed_count > 0
        and candidate_count > 0
        and not managed_attention_count
        and not blocked_activity_count
        and not planned_activity_count
        and active_managed_count <= 0
    )

    def _prioritize_operational_parts(parts: list[str]) -> list[str]:
        ordered_parts = list(parts)

        if managed_count > 0:
            managed_label = _managed_count_label(managed_count)
            if managed_label in ordered_parts:
                managed_index = ordered_parts.index(managed_label)
                del ordered_parts[managed_index]

                def _is_managed_operational_part(part: str) -> bool:
                    return bool(
                        part.endswith(" managed device needs attention")
                        or part.endswith(" managed devices need attention")
                        or part == SOURCE_BLOCKER_ACTIVE_LABEL
                        or part.startswith(("attention first ", "blocked ", "plan ", "active load ", "active device "))
                        or _matches_count_label(part, "planned action")
                        or _matches_count_label(part, "active managed device", "active managed devices")
                        or _matches_count_label(part, "blocked managed action", "blocked managed actions")
                        or (
                            (candidate_count <= 0 or show_quiet_managed_inventory_context)
                            and (
                                part.startswith(("enabled ", "disabled ", "usable "))
                                or _matches_count_label(part, "fixed managed")
                                or _matches_count_label(part, "variable managed")
                                or part.endswith(" W nominal")
                            )
                        )
                    )

                insertion_index = next(
                    (index for index, part in enumerate(ordered_parts) if not _is_managed_operational_part(part)),
                    len(ordered_parts),
                )
                ordered_parts.insert(insertion_index, managed_label)

        if managed_count > 0 and candidate_count > 0:
            unmanaged_label = _unmanaged_count_label(candidate_count)
            if unmanaged_label in ordered_parts:
                unmanaged_index = ordered_parts.index(unmanaged_label)
                del ordered_parts[unmanaged_index]

                source_blocker_part = SOURCE_BLOCKER_ACTIVE_LABEL if SOURCE_BLOCKER_ACTIVE_LABEL in ordered_parts else ""
                if source_blocker_part:
                    ordered_parts.remove(source_blocker_part)

                backlog_parts = [
                    part for part in ordered_parts if part.startswith(("fixed backlog ", "variable backlog "))
                ]
                review_ready_parts = [
                    part
                    for part in ordered_parts
                    if _matches_count_label(part, "needs review", "need review")
                    or _matches_count_label(part, "ready to promote")
                    or _matches_count_label(part, "fixed review")
                    or _matches_count_label(part, "variable review")
                    or part.startswith(("review ", "ready "))
                ]
                candidate_inventory_parts = [
                    part
                    for part in ordered_parts
                    if _matches_count_label(part, "fixed candidate")
                    or _matches_count_label(part, "variable candidate")
                ]
                surfaced_parts = [part for part in ordered_parts if part.startswith("surfaced ")]

                reordered_unmanaged_parts: list[str] = [unmanaged_label]
                reordered_unmanaged_parts.extend(backlog_parts)
                reordered_unmanaged_parts.extend(review_ready_parts)
                reordered_unmanaged_parts.extend(candidate_inventory_parts)
                reordered_unmanaged_parts.extend(surfaced_parts)

                consumed_parts = {
                    unmanaged_label,
                    source_blocker_part,
                    *backlog_parts,
                    *review_ready_parts,
                    *candidate_inventory_parts,
                    *surfaced_parts,
                }
                remaining_parts = [part for part in ordered_parts if part not in consumed_parts]

                insertion_index = max(
                    (
                        index + 1
                        for index, part in enumerate(remaining_parts)
                        if part == _managed_count_label(managed_count)
                        or part.startswith(("attention first ", "blocked ", "plan ", "active load ", "active device "))
                        or part.endswith(" managed device needs attention")
                        or part.endswith(" managed devices need attention")
                        or _matches_count_label(part, "planned action")
                        or _matches_count_label(part, "active managed device", "active managed devices")
                        or _matches_count_label(part, "blocked managed action", "blocked managed actions")
                        or (
                            show_quiet_managed_inventory_context
                            and (
                                part.startswith(("enabled ", "disabled ", "usable "))
                                or _matches_count_label(part, "fixed managed")
                                or _matches_count_label(part, "variable managed")
                                or part.endswith(" W nominal")
                            )
                        )
                    ),
                    default=0,
                )
                ordered_parts = remaining_parts[:insertion_index] + reordered_unmanaged_parts + remaining_parts[insertion_index:]
                if source_blocker_part:
                    ordered_parts.insert(0, source_blocker_part)

        return _fleet_activity_global_signals_first(ordered_parts)

    if managed_count <= 0:
        summary_parts.append(_managed_count_label(managed_count))
        summary_parts.append(_unmanaged_count_label(candidate_count))
        if source_blocked:
            summary_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)

    if managed_count > 0:
        if managed_attention_count:
            summary_parts.append(
                "1 managed device needs attention"
                if managed_attention_count == 1
                else f"{managed_attention_count} managed devices need attention"
            )
        if first_attention_device:
            summary_parts.append(
                f"attention first {attention_focus_label or _command_center_fleet_focus_label(first_attention_device)}"
            )
        if blocked_activity_count:
            if blocked_activity_count > 1 or not blocked_focus_device:
                summary_parts.append(_blocked_activity_count_label(blocked_activity_count))
            if blocked_focus_device:
                summary_parts.append(
                    f"blocked {_command_center_fleet_focus_label(blocked_focus_device)}"
                )
        if planned_activity_count:
            summary_parts.append(
                _planned_action_count_label(planned_activity_count)
            )
        if planned_focus_device and not suppress_planned_focus:
            summary_parts.append(
                f"plan {_command_center_fleet_focus_label(planned_focus_device, include_plan_context=True)}"
            )
        if active_managed_count > 0:
            if active_managed_power_w > 0:
                summary_parts.append(f"active load {active_managed_power_w:g} W")
            summary_parts.append(
                "1 active managed device"
                if active_managed_count == 1
                else f"{active_managed_count} active managed devices"
            )
            if active_focus_device and (
                active_focus_device is not first_active_device
                or (
                    (not attention_device_count or not _same_runtime_device(active_focus_device, first_attention_device))
                    and (not blocked_activity_count or (blocked_focus_device and not _same_runtime_device(active_focus_device, blocked_focus_device)))
                    and (not planned_activity_count or (planned_focus_device and not _same_runtime_device(active_focus_device, planned_focus_device)))
                )
            ):
                summary_parts.append(
                    f"active device {_command_center_managed_snapshot_focus_label(active_focus_device)}"
                )
        summary_parts.append(_managed_count_label(managed_count))
        summary_parts.append(_unmanaged_count_label(candidate_count))
        if source_blocked:
            summary_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)

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
            if review_candidate_name:
                summary_parts.append(f"review {review_candidate_preview or review_candidate_name}")
        if ready_candidate_count:
            summary_parts.append(
                "1 ready to promote"
                if ready_candidate_count == 1
                else f"{ready_candidate_count} ready to promote"
            )
        if ready_candidate_name:
            summary_parts.append(f"ready {ready_candidate_preview or ready_candidate_name}")
        if top_candidate_name and top_candidate_name not in {review_candidate_name, ready_candidate_name}:
            summary_parts.append(f"surfaced {top_candidate_preview or top_candidate_name}")

    if show_inventory_context:
        summary_parts.append(f"enabled {enabled_count}")
        if disabled_count:
            summary_parts.append(f"disabled {disabled_count}")
        summary_parts.append(f"usable {usable_count}")
        if kind_known:
            summary_parts.append(f"{fixed_managed_count} fixed managed")
            if variable_managed_count:
                summary_parts.append(f"{variable_managed_count} variable managed")
            summary_parts.append(f"{nominal_power_w} W nominal")
    elif show_quiet_managed_inventory_context:
        summary_parts.append(f"enabled {enabled_count}")
        if disabled_count:
            summary_parts.append(f"disabled {disabled_count}")
        summary_parts.append(f"usable {usable_count}")
        if kind_known:
            summary_parts.append(f"{fixed_managed_count} fixed managed")
            if variable_managed_count:
                summary_parts.append(f"{variable_managed_count} variable managed")

    summary_parts = _prioritize_operational_parts(summary_parts)
    summary = " | ".join(summary_parts)
    if len(summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return summary

    compact_summary_parts = list(summary_parts)
    optional_part_matchers = [
        lambda part: _matches_count_label(part, "fixed review"),
        lambda part: _matches_count_label(part, "variable review"),
    ]
    if show_quiet_managed_inventory_context:
        optional_part_matchers.extend(
            [
                lambda part: _matches_count_label(part, "fixed candidate"),
                lambda part: _matches_count_label(part, "variable candidate"),
            ]
        )
    optional_part_matchers.extend(
        [
            lambda part: part.startswith("usable "),
            lambda part: part.startswith("disabled "),
            lambda part: part.startswith("enabled "),
            lambda part: part.startswith("fixed backlog "),
            lambda part: part.startswith("variable backlog "),
            lambda part: part.endswith(" W nominal"),
            lambda part: _matches_count_label(part, "fixed managed"),
            lambda part: _matches_count_label(part, "variable managed"),
            lambda part: _matches_count_label(part, "planned action"),
            lambda part: part.startswith("plan "),
        ]
    )
    for matcher in optional_part_matchers:
        if len(" | ".join(compact_summary_parts)) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            break
        for index, part in enumerate(list(compact_summary_parts)):
            if matcher(part):
                del compact_summary_parts[index]
                break

    compact_summary = " | ".join(compact_summary_parts)
    active_count_label = (
        "1 active managed device"
        if active_managed_count == 1
        else f"{active_managed_count} active managed devices"
        if active_managed_count > 1
        else ""
    )
    if (
        compact_summary
        and len(compact_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS
        and active_count_label
        and active_count_label not in compact_summary_parts
    ):
        active_signal_parts = [
            part
            for part in compact_summary_parts
            if not (
                part.endswith(" managed device needs attention")
                or part.endswith(" managed devices need attention")
            )
        ]
        insertion_index = next(
            (
                index + 1
                for index, part in enumerate(active_signal_parts)
                if part.startswith(("active load ", "plan ", "blocked ", "attention first "))
            ),
            len(active_signal_parts),
        )
        active_signal_parts.insert(insertion_index, active_count_label)
        active_signal_summary = " | ".join(active_signal_parts)
        if ready_candidate_count and not review_needed_count:
            ready_count_part = (
                "1 ready to promote"
                if ready_candidate_count == 1
                else f"{ready_candidate_count} ready to promote"
            )
            if ready_count_part not in active_signal_parts:
                ready_count_active_parts = [
                    part for part in active_signal_parts if not part.startswith("active load ")
                ]
                ready_insertion_index = next(
                    (
                        index
                        for index, part in enumerate(ready_count_active_parts)
                        if part.startswith("ready ")
                    ),
                    len(ready_count_active_parts),
                )
                ready_count_active_parts.insert(ready_insertion_index, ready_count_part)
                ready_count_active_summary = " | ".join(ready_count_active_parts)
                if len(ready_count_active_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
                    return ready_count_active_summary
        if len(active_signal_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return active_signal_summary

    compact_review_focus_parts = [
        part
        for part in compact_summary_parts
        if not (
            _matches_count_label(part, "fixed candidate")
            or _matches_count_label(part, "variable candidate")
            or part.startswith("fixed backlog ")
            or part.startswith("variable backlog ")
            or _matches_count_label(part, "planned action")
        )
    ]
    compact_review_focus_summary = " | ".join(compact_review_focus_parts)
    if (
        compact_review_focus_summary
        and len(compact_review_focus_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS
        and (fixed_candidate_count > 5 or variable_candidate_count > 5)
    ):
        return compact_review_focus_summary
    if ready_candidate_count and not review_needed_count:
        ready_count_part = (
            "1 ready to promote"
            if ready_candidate_count == 1
            else f"{ready_candidate_count} ready to promote"
        )
        if ready_count_part not in compact_summary_parts:
            ready_count_compact_parts = [
                part for part in compact_summary_parts if not part.startswith("active load ")
            ]
            insertion_index = next(
                (
                    index
                    for index, part in enumerate(ready_count_compact_parts)
                    if part.startswith("ready ")
                ),
                len(ready_count_compact_parts),
            )
            ready_count_compact_parts.insert(insertion_index, ready_count_part)
            ready_count_compact_summary = " | ".join(ready_count_compact_parts)
            if (
                ready_count_compact_summary
                and len(ready_count_compact_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS
            ):
                return ready_count_compact_summary
    if compact_summary and len(compact_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return compact_summary

    def _clip_part(text: str, *, max_chars: int) -> str:
        normalized = " ".join(str(text).split())
        if len(normalized) <= max_chars:
            return normalized
        if max_chars >= 40 and normalized.startswith(("attention first ", "active device ")):
            focus_clipped = _clip_state_part(normalized, max_chars=max_chars)
            if focus_clipped:
                return focus_clipped
        if max_chars <= 3:
            return normalized[:max_chars]
        return normalized[: max_chars - 3].rstrip() + "..."

    minimal_parts: list[str] = []

    if managed_count <= 0:
        minimal_parts.append(_managed_count_label(managed_count))
        minimal_parts.append(_compact_unmanaged_count_label(candidate_count))
        if source_blocked:
            minimal_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)

    if show_inventory_context and kind_known:
        if fixed_managed_count:
            minimal_parts.append(f"{fixed_managed_count} fixed managed")
        if variable_managed_count:
            minimal_parts.append(f"{variable_managed_count} variable managed")

    if managed_attention_count:
        minimal_parts.append(
            "1 managed device needs attention"
            if managed_attention_count == 1
            else f"{managed_attention_count} managed devices need attention"
        )

    if first_attention_device:
        attention_part = (
            f"attention first {attention_focus_label or _command_center_fleet_focus_label(first_attention_device)}"
        )
        minimal_parts.append(
            _clip_state_part(attention_part, max_chars=72) or _clip_part(attention_part, max_chars=72)
        )
    if blocked_activity_count:
        if blocked_activity_count > 1 or not blocked_focus_device:
            minimal_parts.append(_blocked_activity_count_label(blocked_activity_count))
        if blocked_focus_device:
            blocked_part = f"blocked {_command_center_fleet_focus_label(blocked_focus_device)}"
            minimal_parts.append(
                _clip_state_part(blocked_part, max_chars=72) or _clip_part(blocked_part, max_chars=72)
            )

    if planned_activity_count:
        minimal_parts.append(_planned_action_count_label(planned_activity_count))
        if planned_focus_device and not suppress_planned_focus:
            planned_part = (
                f"plan {_command_center_fleet_focus_label(planned_focus_device, include_plan_context=True)}"
            )
            minimal_parts.append(
                _clip_state_part(planned_part, max_chars=72) or _clip_part(planned_part, max_chars=72)
            )

    if active_managed_count > 0:
        if active_managed_power_w > 0:
            minimal_parts.append(f"active load {active_managed_power_w:g} W")
        minimal_parts.append(
            "1 active managed device"
            if active_managed_count == 1
            else f"{active_managed_count} active managed devices"
        )
        if active_focus_device and (
            active_focus_device is not first_active_device
            or (
                (not attention_device_count or not _same_runtime_device(active_focus_device, first_attention_device))
                and (not blocked_activity_count or (blocked_focus_device and not _same_runtime_device(active_focus_device, blocked_focus_device)))
                and (not planned_activity_count or (planned_focus_device and not _same_runtime_device(active_focus_device, planned_focus_device)))
            )
        ):
            active_device_part = (
                f"active device {_command_center_managed_snapshot_focus_label(active_focus_device)}"
            )
            minimal_parts.append(
                _clip_state_part(active_device_part, max_chars=72)
                or _clip_part(active_device_part, max_chars=72)
            )

    ready_candidate_count = max(candidate_count - review_needed_count, 0)
    if managed_count > 0:
        minimal_parts.append(_managed_count_label(managed_count))
        minimal_parts.append(_compact_unmanaged_count_label(candidate_count))
        if source_blocked:
            minimal_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)

    if fixed_candidate_count and variable_candidate_count:
        minimal_parts.append(_count_label(fixed_candidate_count, "fixed candidate"))
        minimal_parts.append(_count_label(variable_candidate_count, "variable candidate"))
    backlog_parts = _candidate_kind_backlog_mix_parts(
        fixed_candidate_count=fixed_candidate_count,
        variable_candidate_count=variable_candidate_count,
        fixed_review_count=fixed_review_count,
        variable_review_count=variable_review_count,
        fixed_ready_count=fixed_ready_count,
        variable_ready_count=variable_ready_count,
    )
    single_kind_backlog_parts = _single_kind_candidate_backlog_parts(
        fixed_candidate_count=fixed_candidate_count,
        variable_candidate_count=variable_candidate_count,
        fixed_review_count=fixed_review_count,
        variable_review_count=variable_review_count,
        fixed_ready_count=fixed_ready_count,
        variable_ready_count=variable_ready_count,
    )
    single_kind_overflow_backlog_parts = (
        backlog_parts
        if backlog_parts and bool(fixed_candidate_count) != bool(variable_candidate_count)
        else single_kind_backlog_parts if single_kind_backlog_parts and not backlog_parts else []
    )
    preserve_compact_kind_backlog = bool(
        backlog_parts and fixed_candidate_count <= 5 and variable_candidate_count <= 5
    )
    if preserve_compact_kind_backlog:
        minimal_parts.extend(backlog_parts)

    if review_needed_count:
        minimal_parts.append(
            "1 needs review" if review_needed_count == 1 else f"{review_needed_count} need review"
        )
        if review_candidate_preview:
            minimal_parts.append(
                _clip_review_ready_state_part(f"review {review_candidate_preview}", max_chars=72)
            )
        elif review_candidate_name:
            minimal_parts.append(
                _clip_review_ready_state_part(f"review {review_candidate_name}", max_chars=72)
            )

    if ready_candidate_count:
        minimal_parts.append(
            "1 ready to promote"
            if ready_candidate_count == 1
            else f"{ready_candidate_count} ready to promote"
        )
        if ready_candidate_preview and ready_candidate_name:
            minimal_parts.append(
                _clip_review_ready_state_part(f"ready {ready_candidate_preview}", max_chars=72)
            )
        elif ready_candidate_name:
            minimal_parts.append(
                _clip_review_ready_state_part(f"ready {ready_candidate_name}", max_chars=72)
            )

    if top_candidate_preview and top_candidate_name not in {review_candidate_name, ready_candidate_name}:
        minimal_parts.append(_clip_part(f"surfaced {top_candidate_preview}", max_chars=72))
    elif top_candidate_name and top_candidate_name not in {review_candidate_name, ready_candidate_name}:
        minimal_parts.append(_clip_part(f"surfaced {top_candidate_name}", max_chars=72))

    if show_inventory_context:
        minimal_parts.append(f"enabled {enabled_count}")
        if disabled_count:
            minimal_parts.append(f"disabled {disabled_count}")
        minimal_parts.append(f"usable {usable_count}")

    if show_inventory_context and kind_known and nominal_power_w > 0:
        minimal_parts.append(f"{nominal_power_w} W nominal")

    minimal_parts = _prioritize_operational_parts(minimal_parts)
    minimal_summary = " | ".join(minimal_parts)
    if len(minimal_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return minimal_summary

    if managed_count > 0 and candidate_count <= 0 and not (source_blocked and kind_known):
        compact_focus_context_parts: list[str] = []
        if managed_attention_count:
            compact_focus_context_parts.append(
                "1 managed device needs attention"
                if managed_attention_count == 1
                else f"{managed_attention_count} managed devices need attention"
            )
        if first_attention_device:
            attention_part = (
                f"attention first {attention_focus_label or _command_center_fleet_focus_label(first_attention_device)}"
            )
            compact_focus_context_parts.append(
                _clip_state_part(attention_part, max_chars=48) or _clip_part(attention_part, max_chars=48)
            )
        if active_managed_count > 0:
            if active_managed_power_w > 0:
                compact_focus_context_parts.append(f"active load {active_managed_power_w:g} W")
            compact_focus_context_parts.append(
                "1 active managed device"
                if active_managed_count == 1
                else f"{active_managed_count} active managed devices"
            )
            if active_focus_device and (
                active_focus_device is not first_active_device
                or (
                    (not attention_device_count or not _same_runtime_device(active_focus_device, first_attention_device))
                    and (not blocked_activity_count or (blocked_focus_device and not _same_runtime_device(active_focus_device, blocked_focus_device)))
                    and (not planned_activity_count or (planned_focus_device and not _same_runtime_device(active_focus_device, planned_focus_device)))
                )
            ):
                active_device_part = (
                    f"active device {_command_center_managed_snapshot_focus_label(active_focus_device)}"
                )
                compact_focus_context_parts.append(
                    _clip_state_part(active_device_part, max_chars=48)
                    or _clip_part(active_device_part, max_chars=48)
                )
        compact_focus_context_parts.append(_managed_count_label(managed_count))
        compact_focus_context_parts.append(_compact_unmanaged_count_label(candidate_count))
        if source_blocked:
            compact_focus_context_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
        compact_focus_context_parts = _prioritize_operational_parts(compact_focus_context_parts)
        compact_focus_context_summary = " | ".join(compact_focus_context_parts)
        if len(compact_focus_context_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return compact_focus_context_summary

    if managed_count > 0 and candidate_count <= 0 and source_blocked and kind_known:
        source_blocked_inventory_parts: list[str] = []
        if managed_attention_count:
            source_blocked_inventory_parts.append(
                "1 managed device needs attention"
                if managed_attention_count == 1
                else f"{managed_attention_count} managed devices need attention"
            )
        if first_attention_device:
            attention_part = (
                f"attention first {attention_focus_label or _command_center_fleet_focus_label(first_attention_device)}"
            )
            source_blocked_inventory_parts.append(
                _clip_state_part(attention_part, max_chars=56)
                or _clip_part(attention_part, max_chars=56)
            )
        if active_managed_count > 0:
            if active_managed_power_w > 0:
                source_blocked_inventory_parts.append(f"active load {active_managed_power_w:g} W")
            source_blocked_inventory_parts.append(
                "1 active managed device"
                if active_managed_count == 1
                else f"{active_managed_count} active managed devices"
            )
        source_blocked_inventory_parts.extend(
            [
                _managed_count_label(managed_count),
                _compact_unmanaged_count_label(candidate_count),
                SOURCE_BLOCKER_ACTIVE_LABEL,
                f"{fixed_managed_count} fixed managed",
            ]
        )
        if variable_managed_count:
            source_blocked_inventory_parts.append(f"{variable_managed_count} variable managed")
        if nominal_power_w > 0:
            source_blocked_inventory_parts.append(f"{nominal_power_w} W nominal")
        source_blocked_inventory_parts = _prioritize_operational_parts(source_blocked_inventory_parts)
        source_blocked_inventory_summary = " | ".join(source_blocked_inventory_parts)
        if len(source_blocked_inventory_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return source_blocked_inventory_summary

    if managed_count <= 0 and fixed_candidate_count and variable_candidate_count:
        empty_fleet_kind_parts: list[str] = [
            _managed_count_label(managed_count),
            _compact_unmanaged_count_label(candidate_count),
        ]
        if source_blocked:
            empty_fleet_kind_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
        empty_fleet_kind_parts.extend(
            [
                _count_label(fixed_candidate_count, "fixed candidate"),
                _count_label(variable_candidate_count, "variable candidate"),
            ]
        )
        if review_needed_count:
            empty_fleet_kind_parts.append(
                "1 needs review" if review_needed_count == 1 else f"{review_needed_count} need review"
            )
            if review_candidate_preview:
                empty_fleet_kind_parts.append(
                    _clip_review_ready_state_part(f"review {review_candidate_preview}", max_chars=40)
                )
            elif review_candidate_name:
                empty_fleet_kind_parts.append(
                    _clip_review_ready_state_part(f"review {review_candidate_name}", max_chars=40)
                )
        if ready_candidate_count:
            empty_fleet_kind_parts.append(
                "1 ready to promote"
                if ready_candidate_count == 1
                else f"{ready_candidate_count} ready to promote"
            )
            if ready_candidate_preview and ready_candidate_name:
                empty_fleet_kind_parts.append(
                    _clip_review_ready_state_part(f"ready {ready_candidate_preview}", max_chars=40)
                )
            elif ready_candidate_name:
                empty_fleet_kind_parts.append(
                    _clip_review_ready_state_part(f"ready {ready_candidate_name}", max_chars=40)
                )
        empty_fleet_kind_summary = " | ".join(empty_fleet_kind_parts)
        if len(empty_fleet_kind_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return empty_fleet_kind_summary

    removable_part_matchers = (
        lambda part: part.startswith("surfaced "),
        lambda part: part.startswith("enabled "),
        lambda part: part.startswith("usable "),
        lambda part: _matches_count_label(part, "fixed candidate"),
        lambda part: _matches_count_label(part, "variable candidate"),
        lambda part: part.startswith("fixed backlog "),
        lambda part: part.startswith("variable backlog "),
        lambda part: part.endswith(" W nominal"),
        lambda part: _matches_count_label(part, "fixed managed"),
        lambda part: _matches_count_label(part, "variable managed"),
        lambda part: _matches_count_label(part, "planned action"),
        lambda part: part.startswith("plan "),
    )
    for matcher in removable_part_matchers:
        if len(minimal_parts) <= 2:
            break
        if len(" | ".join(minimal_parts)) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            break
        for index, part in enumerate(list(minimal_parts)):
            if matcher(part):
                del minimal_parts[index]
                break

    minimized_summary = " | ".join(minimal_parts)

    review_focus_parts = [
        part
        for part in minimal_parts
        if not (
            _matches_count_label(part, "fixed candidate")
            or _matches_count_label(part, "variable candidate")
            or part.startswith("fixed backlog ")
            or part.startswith("variable backlog ")
            or _matches_count_label(part, "planned action")
        )
    ]
    review_focus_summary = " | ".join(review_focus_parts)
    if (
        review_focus_summary
        and len(review_focus_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS
        and (fixed_candidate_count > 5 or variable_candidate_count > 5)
    ):
        return review_focus_summary
    if single_kind_backlog_parts and not backlog_parts and candidate_count > 1:
        single_kind_review_focus_parts = list(review_focus_parts)
        insertion_index = next(
            (
                index + 1
                for index, part in enumerate(single_kind_review_focus_parts)
                if _is_unmanaged_count_part(part)
            ),
            len(single_kind_review_focus_parts),
        )
        for backlog_part in reversed(single_kind_backlog_parts):
            if backlog_part not in single_kind_review_focus_parts:
                single_kind_review_focus_parts.insert(insertion_index, backlog_part)
        single_kind_review_focus_summary = " | ".join(single_kind_review_focus_parts)
        if (
            single_kind_review_focus_summary
            and len(single_kind_review_focus_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS
        ):
            return single_kind_review_focus_summary
        compact_single_kind_review_focus_parts = [
            part
            for part in single_kind_review_focus_parts
            if not (
                part.endswith(" managed device needs attention")
                or part.endswith(" managed devices need attention")
                or _matches_count_label(part, "needs review", "need review")
                or _matches_count_label(part, "ready to promote")
            )
        ]
        compact_single_kind_review_focus_parts = [
            _clip_part(part, max_chars=27)
            if part.startswith(("attention first ", "blocked ", "review ", "ready ", "active device "))
            else part
            for part in compact_single_kind_review_focus_parts
        ]
        compact_single_kind_review_focus_summary = " | ".join(compact_single_kind_review_focus_parts)
        if (
            compact_single_kind_review_focus_summary
            and len(compact_single_kind_review_focus_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS
        ):
            return compact_single_kind_review_focus_summary
    if minimized_summary and len(minimized_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return minimized_summary
    if review_focus_summary and len(review_focus_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return review_focus_summary

    review_backlog_label = (review_candidate_preview or review_candidate_name).split(" | ", 1)[0].strip()
    ready_backlog_label = (ready_candidate_preview or ready_candidate_name).split(" | ", 1)[0].strip()

    attention_priority_parts = [
        _clip_part(part, max_chars=32)
        if part.startswith(("attention first ", "blocked ", "plan ", "active device "))
        else part
        for part in review_focus_parts
        if not (
            _matches_count_label(part, "fixed candidate")
            or _matches_count_label(part, "variable candidate")
            or _matches_count_label(part, "planned action")
        )
    ]
    if (
        backlog_parts
        and fixed_candidate_count
        and variable_candidate_count
        and candidate_count <= 2
        and managed_count > 1
        and active_managed_count > 0
        and active_focus_device
        and (active_focus_device is not first_active_device or (
            (not first_attention_device or not _same_runtime_device(active_focus_device, first_attention_device))
            and (not blocked_focus_device or not _same_runtime_device(active_focus_device, blocked_focus_device))
        ))
    ):
        managed_unmanaged_split_parts: list[str] = []
        backlog_inserted = False
        for part in attention_priority_parts:
            if (
                part.startswith("active load ")
                or part.startswith("active device ")
                or _matches_count_label(part, "active managed device", "active managed devices")
                or _matches_count_label(part, "needs review", "need review")
                or _matches_count_label(part, "ready to promote")
            ):
                continue
            if part.startswith(("review ", "ready ")):
                managed_unmanaged_split_parts.append(_clip_part(part, max_chars=28))
            else:
                managed_unmanaged_split_parts.append(part)
            if not backlog_inserted and _is_unmanaged_count_part(part):
                managed_unmanaged_split_parts.extend(backlog_parts)
                backlog_inserted = True
        if not backlog_inserted:
            managed_unmanaged_split_parts.extend(backlog_parts)
        managed_unmanaged_split_summary = " | ".join(managed_unmanaged_split_parts)
        if managed_unmanaged_split_summary and len(managed_unmanaged_split_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return managed_unmanaged_split_summary

    if show_inventory_context and kind_known and bool(fixed_managed_count) != bool(variable_managed_count):
        single_kind_managed_part = (
            f"{fixed_managed_count} fixed managed" if fixed_managed_count else f"{variable_managed_count} variable managed"
        )
        if single_kind_managed_part not in attention_priority_parts:
            managed_mix_attention_parts = list(attention_priority_parts)
            insertion_index = next(
                (
                    index + 1
                    for index, part in enumerate(managed_mix_attention_parts)
                    if part == _managed_count_label(managed_count)
                ),
                1 if managed_mix_attention_parts else 0,
            )
            managed_mix_attention_parts.insert(insertion_index, single_kind_managed_part)
            managed_mix_attention_summary = " | ".join(managed_mix_attention_parts)
            if (
                managed_mix_attention_summary
                and len(managed_mix_attention_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS
            ):
                return managed_mix_attention_summary

    if ready_candidate_count and not review_needed_count:
        ready_count_part = (
            "1 ready to promote"
            if ready_candidate_count == 1
            else f"{ready_candidate_count} ready to promote"
        )
        if ready_count_part not in attention_priority_parts:
            ready_count_attention_parts = [
                part for part in attention_priority_parts if not part.startswith("active load ")
            ]
            insertion_index = next(
                (
                    index
                    for index, part in enumerate(ready_count_attention_parts)
                    if part.startswith("ready ")
                ),
                len(ready_count_attention_parts),
            )
            ready_count_attention_parts.insert(insertion_index, ready_count_part)
            ready_count_attention_summary = " | ".join(ready_count_attention_parts)
            if (
                ready_count_attention_summary
                and len(ready_count_attention_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS
            ):
                return ready_count_attention_summary

    attention_priority_parts = _prioritize_operational_parts(attention_priority_parts)
    attention_priority_summary = " | ".join(attention_priority_parts)
    if attention_priority_summary and len(attention_priority_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return attention_priority_summary

    attention_backlog_parts: list[str] = []
    for part in attention_priority_parts:
        if part.startswith("review ") and review_backlog_label:
            attention_backlog_parts.append(f"review {review_backlog_label}")
        elif part.startswith("ready ") and ready_backlog_label:
            attention_backlog_parts.append(f"ready {ready_backlog_label}")
        else:
            attention_backlog_parts.append(part)
    attention_backlog_summary = " | ".join(attention_backlog_parts)
    if attention_backlog_summary and len(attention_backlog_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return attention_backlog_summary

    review_priority_parts = [
        _clip_part(part, max_chars=32) if part.startswith(("blocked ", "plan ")) else part
        for part in review_focus_parts
        if not part.startswith(("attention first ",))
    ]
    review_priority_summary = " | ".join(review_priority_parts)
    if review_priority_summary and len(review_priority_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return review_priority_summary

    review_priority_parts = [
        part
        for part in review_priority_parts
        if not (
            _matches_count_label(part, "fixed candidate")
            or _matches_count_label(part, "variable candidate")
            or _matches_count_label(part, "planned action")
        )
    ]
    review_priority_summary = " | ".join(review_priority_parts)
    if review_priority_summary and len(review_priority_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return review_priority_summary

    backlog_priority_parts: list[str] = []
    for part in review_priority_parts:
        if part.startswith("review ") and review_backlog_label:
            backlog_priority_parts.append(f"review {review_backlog_label}")
        elif part.startswith("ready ") and ready_backlog_label:
            backlog_priority_parts.append(f"ready {ready_backlog_label}")
        else:
            backlog_priority_parts.append(part)
    backlog_priority_summary = " | ".join(backlog_priority_parts)
    if backlog_priority_summary and len(backlog_priority_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return backlog_priority_summary

    compact_minimal_parts = [
        _clip_state_part(part, max_chars=48) or _clip_part(part, max_chars=48)
        if part.startswith(("attention first ", "active device "))
        else _clip_review_ready_state_part(part, max_chars=48)
        if part.startswith(("review ", "ready "))
        else _clip_part(part, max_chars=48)
        if part.startswith(("blocked ", "surfaced "))
        else part
        for part in minimal_parts
    ]
    compact_minimal_summary = " | ".join(compact_minimal_parts)
    if compact_minimal_summary and len(compact_minimal_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return compact_minimal_summary

    essential_parts: list[str] = [_managed_count_label(managed_count)]
    if managed_count <= 0:
        essential_parts.append(_compact_unmanaged_count_label(candidate_count))
        if source_blocked:
            essential_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
    if first_attention_device:
        essential_parts.append(
            _clip_part(
                f"attention first {attention_focus_label or _command_center_fleet_focus_label(first_attention_device)}",
                max_chars=32,
            )
        )
    if blocked_activity_count:
        if blocked_activity_count > 1 or not blocked_focus_device:
            essential_parts.append(_blocked_activity_count_label(blocked_activity_count))
        if blocked_focus_device:
            essential_parts.append(
                _clip_part(
                    f"blocked {_command_center_fleet_focus_label(blocked_focus_device)}",
                    max_chars=32,
                )
            )
    if planned_activity_count:
        essential_parts.append(_planned_action_count_label(planned_activity_count))
    if active_managed_count > 0:
        if active_managed_power_w > 0:
            essential_parts.append(f"active load {active_managed_power_w:g} W")
        essential_parts.append(
            "1 active managed device"
            if active_managed_count == 1
            else f"{active_managed_count} active managed devices"
        )
        if active_focus_device and (
            active_focus_device is not first_active_device
            or (
                (not attention_device_count or not _same_runtime_device(active_focus_device, first_attention_device))
                and (not blocked_activity_count or (blocked_focus_device and not _same_runtime_device(active_focus_device, blocked_focus_device)))
                and (not planned_activity_count or (first_planned_device and not _same_runtime_device(active_focus_device, first_planned_device)))
            )
        ):
            essential_parts.append(
                _clip_part(
                    f"active device {_command_center_managed_snapshot_focus_label(active_focus_device)}",
                    max_chars=32,
                )
            )
    if managed_count > 0:
        essential_parts.append(_compact_unmanaged_count_label(candidate_count))
        if source_blocked:
            essential_parts.append(SOURCE_BLOCKER_ACTIVE_LABEL)
    if fixed_candidate_count and variable_candidate_count:
        essential_parts.append(_count_label(fixed_candidate_count, "fixed candidate"))
        essential_parts.append(_count_label(variable_candidate_count, "variable candidate"))
    preserve_compact_kind_backlog = bool(
        backlog_parts and fixed_candidate_count <= 5 and variable_candidate_count <= 5
    )
    if preserve_compact_kind_backlog:
        essential_parts.extend(backlog_parts)
    if review_needed_count:
        essential_parts.append(
            "1 needs review" if review_needed_count == 1 else f"{review_needed_count} need review"
        )
        if review_candidate_preview:
            essential_parts.append(
                _clip_review_ready_state_part(f"review {review_candidate_preview}", max_chars=32)
            )
        elif review_candidate_name:
            essential_parts.append(
                _clip_review_ready_state_part(f"review {review_candidate_name}", max_chars=32)
            )
    if ready_candidate_count:
        essential_parts.append(
            "1 ready to promote"
            if ready_candidate_count == 1
            else f"{ready_candidate_count} ready to promote"
        )
        if ready_candidate_preview and ready_candidate_name:
            essential_parts.append(
                _clip_review_ready_state_part(f"ready {ready_candidate_preview}", max_chars=32)
            )
        elif ready_candidate_name:
            essential_parts.append(
                _clip_review_ready_state_part(f"ready {ready_candidate_name}", max_chars=32)
            )

    essential_parts = _prioritize_operational_parts(essential_parts)
    essential_summary = " | ".join(essential_parts)
    if essential_summary and len(essential_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return essential_summary

    managed_backlog_essential_parts: list[str] = []
    duplicate_attention_blocked = bool(
        first_attention_device
        and blocked_focus_device
        and _same_runtime_device(first_attention_device, blocked_focus_device)
    )
    duplicate_attention_planned = bool(
        first_attention_device
        and first_planned_device
        and _same_runtime_device(first_attention_device, first_planned_device)
    )
    active_device_part = (
        _clip_part(
            f"active device {_command_center_managed_snapshot_focus_label(active_focus_device)}",
            max_chars=24,
        )
        if active_focus_device
        and (
            active_focus_device is not first_active_device
            or (
                (not attention_device_count or not _same_runtime_device(active_focus_device, first_attention_device))
                and (not blocked_activity_count or (blocked_focus_device and not _same_runtime_device(active_focus_device, blocked_focus_device)))
                and (not planned_activity_count or (first_planned_device and not _same_runtime_device(active_focus_device, first_planned_device)))
            )
        )
        else ""
    )
    for part in essential_parts:
        if (
            _matches_count_label(part, "fixed candidate")
            or _matches_count_label(part, "variable candidate")
            or _matches_count_label(part, "planned action")
            or part.startswith("active device ")
        ):
            continue
        if part.startswith("review ") and review_backlog_label:
            managed_backlog_essential_parts.append(
                _clip_review_ready_state_part(f"review {review_backlog_label}", max_chars=32)
            )
        elif part.startswith("ready ") and ready_backlog_label:
            managed_backlog_essential_parts.append(
                _clip_review_ready_state_part(f"ready {ready_backlog_label}", max_chars=32)
            )
        else:
            managed_backlog_essential_parts.append(part)
    if single_kind_overflow_backlog_parts and candidate_count > 1:
        insertion_index = next(
            (
                index + 1
                for index, part in enumerate(managed_backlog_essential_parts)
                if _is_unmanaged_count_part(part)
            ),
            len(managed_backlog_essential_parts),
        )
        for backlog_part in reversed(single_kind_overflow_backlog_parts):
            if backlog_part not in managed_backlog_essential_parts:
                managed_backlog_essential_parts.insert(insertion_index, backlog_part)
    managed_backlog_essential_parts = _prioritize_operational_parts(managed_backlog_essential_parts)
    managed_backlog_essential_summary = " | ".join(managed_backlog_essential_parts)
    if managed_backlog_essential_summary and len(managed_backlog_essential_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return managed_backlog_essential_summary

    if active_device_part:
        active_story_parts = list(managed_backlog_essential_parts)
        for duplicate_prefix, duplicate_active in (
            ("blocked ", duplicate_attention_blocked),
            ("plan ", duplicate_attention_planned),
        ):
            if duplicate_active:
                for index, part in enumerate(list(active_story_parts)):
                    if part.startswith(duplicate_prefix):
                        del active_story_parts[index]
                        break
        insertion_index = next(
            (
                index + 1
                for index, part in enumerate(active_story_parts)
                if part.startswith("active load ")
            ),
            next(
                (
                    index + 1
                    for index, part in enumerate(active_story_parts)
                    if part.startswith(("attention first ", "blocked ", "plan "))
                ),
                len(active_story_parts),
            ),
        )
        if active_device_part not in active_story_parts:
            active_story_parts.insert(insertion_index, active_device_part)
        active_story_summary = " | ".join(active_story_parts)
        if active_story_summary and len(active_story_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return active_story_summary
        if SOURCE_BLOCKER_ACTIVE_LABEL in active_story_parts:
            source_blocker_priority_active_parts = [
                part
                for part in active_story_parts
                if not (
                    _matches_count_label(part, "needs review", "need review")
                    or _matches_count_label(part, "ready to promote")
                    or _matches_count_label(part, "active managed device", "active managed devices")
                    or part.endswith(" managed device needs attention")
                    or part.endswith(" managed devices need attention")
                )
            ]
            source_blocker_priority_active_summary = " | ".join(source_blocker_priority_active_parts)
            if (
                source_blocker_priority_active_summary
                and len(source_blocker_priority_active_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS
            ):
                return source_blocker_priority_active_summary
            active_story_without_source_blockers = [
                part for part in active_story_parts if part != SOURCE_BLOCKER_ACTIVE_LABEL
            ]
            active_story_summary = " | ".join(active_story_without_source_blockers)
            if active_story_summary and len(active_story_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
                return active_story_summary
        focused_active_story_parts = [
            part
            for part in active_story_parts
            if not (
                _matches_count_label(part, "active managed device", "active managed devices")
                or part.endswith(" managed device needs attention")
                or part.endswith(" managed devices need attention")
            )
        ]
        story_backlog_parts = backlog_parts or single_kind_overflow_backlog_parts or single_kind_backlog_parts
        if story_backlog_parts:
            insertion_index = next(
                (
                    index + 1
                    for index, part in enumerate(focused_active_story_parts)
                    if _is_unmanaged_count_part(part)
                ),
                len(focused_active_story_parts),
            )
            for backlog_part in reversed(story_backlog_parts):
                if backlog_part not in focused_active_story_parts:
                    focused_active_story_parts.insert(insertion_index, backlog_part)
        focused_active_story_parts = [
            _clip_part(part, max_chars=28)
            if part.startswith(("attention first ", "blocked ", "plan ", "active device "))
            else _clip_review_ready_state_part(part, max_chars=25)
            if part.startswith("review ")
            else _clip_review_ready_state_part(part, max_chars=22)
            if part.startswith("ready ")
            else part
            for part in focused_active_story_parts
        ]
        focused_active_story_summary = " | ".join(focused_active_story_parts)
        if focused_active_story_summary and len(focused_active_story_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return focused_active_story_summary
        if SOURCE_BLOCKER_ACTIVE_LABEL in focused_active_story_parts:
            source_blocker_priority_parts = [
                part
                for part in focused_active_story_parts
                if not (
                    _matches_count_label(part, "needs review", "need review")
                    or _matches_count_label(part, "ready to promote")
                    or _matches_count_label(part, "active managed device", "active managed devices")
                )
            ]
            source_blocker_priority_summary = " | ".join(source_blocker_priority_parts)
            if (
                source_blocker_priority_summary
                and len(source_blocker_priority_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS
            ):
                return source_blocker_priority_summary

    operator_story_parts: list[str] = []
    for part in managed_backlog_essential_parts:
        if (
            _matches_count_label(part, "fixed candidate")
            or _matches_count_label(part, "variable candidate")
            or _matches_count_label(part, "active managed device", "active managed devices")
            or part.endswith(" managed device needs attention")
            or part.endswith(" managed devices need attention")
            or part.startswith(("surfaced ", "enabled ", "disabled ", "usable "))
            or part.endswith(" W nominal")
        ):
            continue
        if part.startswith(("attention first ", "blocked ", "plan ", "active device ")):
            operator_story_parts.append(_clip_part(part, max_chars=28))
        elif part.startswith(("review ", "ready ")):
            operator_story_parts.append(_clip_review_ready_state_part(part, max_chars=28))
        else:
            operator_story_parts.append(part)
    story_backlog_parts = backlog_parts or single_kind_overflow_backlog_parts or single_kind_backlog_parts
    if story_backlog_parts:
        insertion_index = next(
            (
                index + 1
                for index, part in enumerate(operator_story_parts)
                if _is_unmanaged_count_part(part)
            ),
            len(operator_story_parts),
        )
        for backlog_part in reversed(story_backlog_parts):
            if backlog_part not in operator_story_parts:
                operator_story_parts.insert(insertion_index, backlog_part)
    operator_story_parts = _prioritize_operational_parts(operator_story_parts)
    operator_story_summary = " | ".join(operator_story_parts)
    if operator_story_summary and len(operator_story_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return operator_story_summary

    compact_operator_story_source_parts = list(operator_story_parts)
    for duplicate_prefix, duplicate_active in (
        ("blocked ", duplicate_attention_blocked),
        ("plan ", duplicate_attention_planned),
    ):
        if duplicate_active:
            for index, part in enumerate(list(compact_operator_story_source_parts)):
                if part.startswith(duplicate_prefix):
                    del compact_operator_story_source_parts[index]
                    break
    compact_operator_story_parts = [
        _clip_part(part, max_chars=30)
        if part.startswith(("attention first ", "blocked ", "plan ", "active device "))
        else _clip_review_ready_state_part(part, max_chars=25)
        if part.startswith("review ")
        else _clip_review_ready_state_part(part, max_chars=22)
        if part.startswith("ready ")
        else part
        for part in compact_operator_story_source_parts
    ]
    compact_operator_story_summary = " | ".join(compact_operator_story_parts)
    if compact_operator_story_summary and len(compact_operator_story_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return compact_operator_story_summary
    if SOURCE_BLOCKER_ACTIVE_LABEL in compact_operator_story_parts:
        source_blocker_priority_operator_parts = [
            part
            for part in compact_operator_story_parts
            if not (
                _matches_count_label(part, "needs review", "need review")
                or _matches_count_label(part, "ready to promote")
                or _matches_count_label(part, "active managed device", "active managed devices")
            )
        ]
        source_blocker_priority_operator_summary = " | ".join(
            source_blocker_priority_operator_parts
        )
        if (
            source_blocker_priority_operator_summary
            and len(source_blocker_priority_operator_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS
        ):
            return source_blocker_priority_operator_summary
        compact_operator_story_without_source_blockers = [
            part for part in compact_operator_story_parts if part != SOURCE_BLOCKER_ACTIVE_LABEL
        ]
        compact_operator_story_without_source_blockers_summary = " | ".join(
            compact_operator_story_without_source_blockers
        )
        if (
            compact_operator_story_without_source_blockers_summary
            and len(compact_operator_story_without_source_blockers_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS
        ):
            return compact_operator_story_without_source_blockers_summary

    if single_kind_overflow_backlog_parts and candidate_count > 1:
        compact_single_kind_backlog_parts = [
            part
            for part in managed_backlog_essential_parts
            if not (
                _matches_count_label(part, "needs review", "need review")
                or _matches_count_label(part, "ready to promote")
                or _matches_count_label(part, "active managed device", "active managed devices")
                or part.startswith("active device ")
            )
        ]
        compact_single_kind_backlog_parts = [
            _clip_part(part, max_chars=28)
            if part.startswith(("attention first ", "blocked "))
            else _clip_review_ready_state_part(part, max_chars=28)
            if part.startswith(("review ", "ready "))
            else part
            for part in compact_single_kind_backlog_parts
        ]
        single_kind_backlog_summary = " | ".join(compact_single_kind_backlog_parts)
        if single_kind_backlog_summary and len(single_kind_backlog_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return single_kind_backlog_summary

    ultra_parts = list(essential_parts)
    for removable_prefix in (
        "attention first ",
        "blocked ",
        "planned action",
    ):
        if len(" | ".join(ultra_parts)) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            break
        for index, part in enumerate(list(ultra_parts)):
            if part.startswith(removable_prefix) or part.endswith(removable_prefix):
                del ultra_parts[index]
                break

    ultra_summary = " | ".join(ultra_parts)
    if ultra_summary and len(ultra_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return ultra_summary

    clipped_ultra_parts = [
        _clip_review_ready_state_part(part, max_chars=36)
        if part.startswith(("review ", "ready "))
        else _clip_part(part, max_chars=36)
        if part.startswith(("surfaced ",))
        else part
        for part in ultra_parts
    ]
    clipped_ultra_summary = " | ".join(clipped_ultra_parts)
    if clipped_ultra_summary and len(clipped_ultra_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return clipped_ultra_summary

    return compact_minimal_summary if compact_minimal_summary else summary


def build_native_command_center_summary(coordinator: Any) -> dict[str, str]:
    """Return the command-center summary shown in Configure and device surfaces."""
    state = getattr(coordinator, "data", None) if coordinator is not None else None
    readiness = build_native_operator_readiness(coordinator) if coordinator is not None else {}
    install_provenance = build_install_provenance()

    entry = getattr(coordinator, "entry", None)
    merged: dict[str, Any] = {}
    if entry is not None:
        merged.update(entry.data)
        merged.update(entry.options)

    configured_devices, device_parse_issues = _configured_device_payloads(entry) if entry is not None else ([], [])
    candidates, top_candidate_name = _command_center_candidate_snapshot(coordinator, state)
    top_candidate_preview = (
        build_candidate_compact_preview(candidates[0], include_warning=True)
        if candidates
        else ""
    )
    top_candidate_focus = _command_center_candidate_focus_text(candidates[0] if candidates else None)
    review_candidate = next(
        (item for item in candidates if candidate_needs_review(assess_candidate(item))),
        None,
    )
    review_candidate_name = str((review_candidate or {}).get("name") or (review_candidate or {}).get("entity_id") or "").strip()
    review_candidate_preview = (
        build_candidate_compact_preview(review_candidate, include_warning=True)
        if review_candidate
        else ""
    )
    ready_candidate = next(
        (item for item in candidates if not candidate_needs_review(assess_candidate(item))),
        None,
    )
    ready_candidate_name = str((ready_candidate or {}).get("name") or (ready_candidate or {}).get("entity_id") or "").strip()
    ready_candidate_preview = (
        build_candidate_compact_preview(ready_candidate, include_warning=True)
        if ready_candidate
        else ""
    )
    _, primary_candidate_focus = _primary_candidate_focus(candidates)
    candidate_count = len(candidates)
    fixed_candidate_count = sum(1 for item in candidates if str(item.get("kind") or "") == "fixed")
    variable_candidate_count = sum(1 for item in candidates if str(item.get("kind") or "") == "variable")
    review_needed_count = sum(1 for item in candidates if candidate_needs_review(assess_candidate(item)))
    managed_attention_count = (
        sum(1 for detail in (getattr(state, "device_details", {}) or {}).values() if _runtime_device_needs_attention(detail))
        if state is not None
        else 0
    )
    active_managed_count, active_managed_power_w = _managed_runtime_activity(state)
    first_active_device = _first_runtime_device_detail(
        state,
        predicate=lambda detail: detail.get("observed_active") is True,
    )
    blocked_activity_count = (
        sum(1 for detail in (getattr(state, "device_details", {}) or {}).values() if _runtime_device_has_blocked_activity(detail))
        if state is not None
        else 0
    )
    if state is not None:
        blocked_activity_count = max(
            blocked_activity_count,
            int(getattr(state, "blocked_planned_action_count", 0) or 0),
        )
    managed_attention_count = max(managed_attention_count, blocked_activity_count)
    fixed_review_count = sum(
        1
        for item in candidates
        if str(item.get("kind") or "") == "fixed" and candidate_needs_review(assess_candidate(item))
    )
    variable_review_count = sum(
        1
        for item in candidates
        if str(item.get("kind") or "") == "variable" and candidate_needs_review(assess_candidate(item))
    )
    readiness_phase = str(readiness.get("phase") or "")
    runtime_device_count = (
        int(getattr(state, "device_count", len(configured_devices)) or 0)
        if state is not None
        else len(configured_devices)
    )
    has_managed_devices = runtime_device_count > 0
    first_blocked_device = _first_runtime_device_detail(state, predicate=_runtime_device_has_blocked_activity)
    first_planned_device = _first_runtime_device_detail(state, predicate=_runtime_device_has_active_plan)
    first_attention_device = _first_runtime_device_detail(state, predicate=_runtime_device_needs_attention)
    active_restore_device = _first_distinct_runtime_device_detail(
        state,
        predicate=lambda detail: detail.get("observed_active") is True,
        excluded=(first_attention_device, first_blocked_device, first_planned_device),
    ) or first_active_device
    active_device_preview = _command_center_managed_snapshot_focus_label(active_restore_device)
    active_device_distinct = bool(
        active_restore_device
        and (
            active_restore_device is not first_active_device
            or (
                (not first_attention_device or not _same_runtime_device(active_restore_device, first_attention_device))
                and (not first_blocked_device or not _same_runtime_device(active_restore_device, first_blocked_device))
                and (not first_planned_device or not _same_runtime_device(active_restore_device, first_planned_device))
            )
        )
    )
    install_consistency = build_install_consistency_summary(install_provenance)
    install_provenance_pending = bool(install_provenance.get("pending_async_refresh"))
    install_provenance_blocked = install_provenance_pending or install_provenance.get("manifest_matches_code_version") is False

    missing_required_sources = [key for key in REQUIRED_SOURCE_KEYS if not merged.get(key)]
    source_attention = build_source_attention_details(state)
    unavailable_source_roles = [SOURCE_ROLE_LABELS.get(key, key) for key in source_attention["unavailable_source_keys"]]
    stale_source_roles = [SOURCE_ROLE_LABELS.get(key, key) for key in source_attention["stale_source_keys"]]
    source_attention_summary = build_source_attention_summary(state, merged, limit=4, blocking_only=True)
    source_attention_roles = build_source_attention_role_summary(state, merged, limit=4, blocking_only=True)
    blocking_validation_details = summarize_validation_issue_messages(state, severities={"error"}, limit=3)
    runtime_source_attention = bool(unavailable_source_roles or stale_source_roles or blocking_validation_details != "None")

    if missing_required_sources:
        source_status = "Missing required source roles: " + ", ".join(
            SOURCE_ROLE_LABELS.get(key, key) for key in missing_required_sources
        )
    elif runtime_source_attention:
        attention_prefix = "Source blockers: " + source_attention_summary if source_attention_summary != "None" else "Source data needs attention."
        validation_suffix = (
            f" Blocking validation details: {blocking_validation_details}"
            if blocking_validation_details != "None"
            else ""
        )
        source_status = attention_prefix + validation_suffix
    elif state is None:
        source_status = "runtime pending | source health waiting"
    else:
        source_status = build_live_source_health_summary(state)

    headline_decision = _build_headline_decision(
        state,
        missing_required_sources=missing_required_sources,
        runtime_source_attention=runtime_source_attention,
        source_attention_summary=source_attention_summary,
        blocking_validation_details=blocking_validation_details,
        configured_devices=configured_devices,
    )

    if device_parse_issues:
        device_status = _command_center_device_status_with_unmanaged_context(
            f"{len(configured_devices)} configured, with {_repair_issue_count_label(len(device_parse_issues))} to repair",
            managed_count=len(configured_devices),
            candidate_count=candidate_count,
            fixed_candidate_count=fixed_candidate_count,
            variable_candidate_count=variable_candidate_count,
            review_needed_count=review_needed_count,
            fixed_review_count=fixed_review_count,
            variable_review_count=variable_review_count,
            top_candidate_name=top_candidate_name,
            top_candidate_preview=top_candidate_preview,
            review_candidate_name=review_candidate_name,
            review_candidate_preview=review_candidate_preview,
            ready_candidate_name=ready_candidate_name,
            ready_candidate_preview=ready_candidate_preview,
            active_managed_count=active_managed_count,
            active_managed_power_w=active_managed_power_w,
            attention_device_preview=_command_center_managed_snapshot_focus_label(first_attention_device),
            blocked_device_preview=_command_center_fleet_focus_label(first_blocked_device),
            planned_device_preview=_command_center_fleet_focus_label(first_planned_device, include_plan_context=True),
            active_device_preview=active_device_preview,
            source_blocked=bool(missing_required_sources or runtime_source_attention),
        )
        device_next_step = f"Open {DEVICES_CONFIGURE_PATH} to repair the managed-device configuration before relying on control."
    elif has_managed_devices:
        runtime_device_status = str(getattr(state, "device_status_summary", "") or "").strip() if state is not None else ""
        device_status = _command_center_device_status_with_unmanaged_context(
            runtime_device_status or f"{runtime_device_count} configured",
            managed_count=runtime_device_count,
            candidate_count=candidate_count,
            fixed_candidate_count=fixed_candidate_count,
            variable_candidate_count=variable_candidate_count,
            review_needed_count=review_needed_count,
            fixed_review_count=fixed_review_count,
            variable_review_count=variable_review_count,
            top_candidate_name=top_candidate_name,
            top_candidate_preview=top_candidate_preview,
            review_candidate_name=review_candidate_name,
            review_candidate_preview=review_candidate_preview,
            ready_candidate_name=ready_candidate_name,
            ready_candidate_preview=ready_candidate_preview,
            managed_attention_count=managed_attention_count,
            blocked_activity_count=blocked_activity_count,
            active_managed_count=active_managed_count,
            active_managed_power_w=active_managed_power_w,
            attention_device_preview=_command_center_managed_snapshot_focus_label(first_attention_device),
            blocked_device_preview=_command_center_fleet_focus_label(first_blocked_device),
            planned_device_preview=_command_center_fleet_focus_label(first_planned_device, include_plan_context=True),
            active_device_preview=active_device_preview,
            source_blocked=bool(missing_required_sources or runtime_source_attention),
        )
        if blocked_activity_count:
            blocked_target = _command_center_runtime_device_preview(first_blocked_device) or "the first blocked device"
            device_next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to review blocked devices in the Managed Devices workspace, starting with {blocked_target}."
            )
        elif first_planned_device:
            planned_target = _command_center_runtime_device_preview(first_planned_device) or "the active fleet plan"
            device_next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to confirm the active fleet plan in the Managed Devices workspace for {planned_target}."
            )
        elif first_attention_device:
            attention_target = _command_center_runtime_device_preview(first_attention_device) or "the first managed device needing attention"
            device_next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, starting with attention on {attention_target}."
            )
        elif candidate_count:
            if review_candidate_name:
                device_next_step = (
                    f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, review unmanaged candidate: "
                    f"{review_candidate_preview or review_candidate_name}"
                )
                if ready_candidate_name and ready_candidate_name != review_candidate_name:
                    device_next_step += (
                        f", then promote ready unmanaged candidate: "
                        f"{ready_candidate_preview or ready_candidate_name}"
                    )
            else:
                device_next_step = (
                    f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then promote ready unmanaged candidate: "
                    f"{ready_candidate_preview or top_candidate_preview or top_candidate_name or 'the next unmanaged candidate'}"
                )
        else:
            device_next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then edit device settings or stage enablement changes."
            )
    else:
        device_status = _command_center_device_status_with_unmanaged_context(
            "Managed Devices: no managed yet",
            managed_count=0,
            candidate_count=candidate_count,
            fixed_candidate_count=fixed_candidate_count,
            variable_candidate_count=variable_candidate_count,
            review_needed_count=review_needed_count,
            fixed_review_count=fixed_review_count,
            variable_review_count=variable_review_count,
            top_candidate_name=top_candidate_name,
            top_candidate_preview=top_candidate_preview,
            review_candidate_name=review_candidate_name,
            review_candidate_preview=review_candidate_preview,
            ready_candidate_name=ready_candidate_name,
            ready_candidate_preview=ready_candidate_preview,
            active_managed_count=active_managed_count,
            active_managed_power_w=active_managed_power_w,
            attention_device_preview=_command_center_managed_snapshot_focus_label(first_attention_device),
            blocked_device_preview=_command_center_fleet_focus_label(first_blocked_device),
            planned_device_preview=_command_center_fleet_focus_label(first_planned_device, include_plan_context=True),
            active_device_preview=active_device_preview,
            source_blocked=bool(missing_required_sources or runtime_source_attention),
        )
        if review_candidate_name:
            device_next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, review unmanaged candidate: "
                f"{review_candidate_preview or review_candidate_name}"
            )
            if ready_candidate_name and ready_candidate_name != review_candidate_name:
                device_next_step += (
                    f", then promote ready unmanaged candidate: "
                    f"{ready_candidate_preview or ready_candidate_name}"
                )
        elif ready_candidate_name or top_candidate_preview or top_candidate_name:
            device_next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then promote ready unmanaged candidate: "
                f"{ready_candidate_preview or ready_candidate_name or top_candidate_preview or top_candidate_name or 'the next unmanaged candidate'}"
            )
        else:
            device_next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available."
            )

    recommendation = build_native_setup_recommendation(
        missing_source_keys=missing_required_sources,
        source_attention_roles=source_attention_roles,
        device_issues=device_parse_issues,
        has_devices=has_managed_devices,
        readiness_phase=readiness_phase,
        candidate_count=candidate_count,
        review_needed_count=review_needed_count,
        managed_attention_count=managed_attention_count,
        blocked_activity_count=blocked_activity_count,
    )
    recommended_section = normalize_command_center_section(recommendation["recommended_section"])

    source_repair_step = build_source_repair_step(
        missing_source_keys=missing_required_sources,
        unavailable_source_keys=source_attention["unavailable_source_keys"],
        stale_source_keys=source_attention["stale_source_keys"],
        blocking_validation_details=blocking_validation_details,
        affected_roles=source_attention_roles,
    )

    if install_provenance_blocked:
        device_next_step = build_install_repair_step(install_provenance)
    elif missing_required_sources or runtime_source_attention:
        device_next_step = source_repair_step

    if install_provenance_blocked:
        next_action_summary = build_install_repair_step(install_provenance)
        recommended_section = SUPPORT_SECTION_LABEL
    elif missing_required_sources:
        next_action_summary = build_source_repair_step(missing_source_keys=missing_required_sources)
    elif runtime_source_attention:
        next_action_summary = str(
            readiness.get("next_step")
            or build_source_repair_step(
                unavailable_source_keys=source_attention["unavailable_source_keys"],
                stale_source_keys=source_attention["stale_source_keys"],
                blocking_validation_details=blocking_validation_details,
                affected_roles=source_attention_roles,
            )
        )
    elif device_parse_issues:
        next_action_summary = "Repair the managed-device configuration next so control actions can be trusted."
    elif not has_managed_devices:
        if review_candidate_name:
            next_action_summary = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, review unmanaged candidate: "
                f"{review_candidate_preview or review_candidate_name}"
            )
            if ready_candidate_name and ready_candidate_name != review_candidate_name:
                next_action_summary += (
                    f", then promote ready unmanaged candidate: "
                    f"{ready_candidate_preview or ready_candidate_name}"
                )
        elif ready_candidate_name or ready_candidate_preview or top_candidate_preview or top_candidate_name:
            next_action_summary = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then promote ready unmanaged candidate: "
                f"{ready_candidate_preview or ready_candidate_name or top_candidate_preview or top_candidate_name or primary_candidate_focus}"
            )
        else:
            next_action_summary = (
                f"Open {DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available."
            )
    elif readiness_phase == "runtime_readiness":
        next_action_summary = str(
            readiness.get("next_step")
            or f"Open {SUPPORT_CONFIGURE_PATH} and {DIAGNOSTICS_DEVICE_ACTIONS_PATH} to clear the current runtime blocker."
        )
        recommended_section = SUPPORT_SECTION_LABEL
    elif recommended_section == DEVICES_SECTION_LABEL and (candidate_count or managed_attention_count or blocked_activity_count):
        next_action_summary = device_next_step
    elif readiness_phase == "operator_ready":
        if recommended_section == DEVICES_SECTION_LABEL:
            next_action_summary = device_next_step
        elif recommended_section == SOURCES_SECTION_LABEL:
            next_action_summary = (
                f"Open {SOURCES_CONFIGURE_PATH} next to confirm the live source roles and source health."
            )
        elif recommended_section == POLICY_SECTION_LABEL:
            next_action_summary = (
                f"Sources and devices are in place, so open {POLICY_CONFIGURE_PATH} next to tune target export, deadband, reserve, or live mode."
            )
        else:
            next_action_summary = str(
                readiness.get("next_step")
                or f"Open {SUPPORT_CONFIGURE_PATH} to continue in Diagnostics with blocker triage, repairs, or install validation."
            )
    else:
        next_action_summary = (
            f"Sources and devices are in place, so open {POLICY_CONFIGURE_PATH} next to tune target export, deadband, reserve, or live mode."
        )

    current_mode = _decision_mode_text(state)
    policy_status = (
        f"Mode {current_mode}; target {int(merged.get(CONF_TARGET_EXPORT_W, DEFAULT_TARGET_EXPORT_W) or DEFAULT_TARGET_EXPORT_W)} W, "
        f"deadband {int(merged.get(CONF_DEADBAND_W, DEFAULT_DEADBAND_W) or DEFAULT_DEADBAND_W)} W, "
        f"battery reserve {int(merged.get(CONF_BATTERY_RESERVE_SOC, DEFAULT_BATTERY_RESERVE_SOC) or DEFAULT_BATTERY_RESERVE_SOC)}%"
    )
    if missing_required_sources:
        policy_readiness = "Finish required source roles first. Controls changes are not actionable until the required source roles are complete."
    elif runtime_source_attention:
        policy_readiness = f"Repair source blockers in {SOURCES_CONFIGURE_PATH} before treating Controls changes as actionable runtime changes."
    elif device_parse_issues:
        policy_readiness = "Repair the managed-device configuration first so Controls changes apply to a trustworthy fleet."
    elif not has_managed_devices:
        policy_readiness = "You can set Controls defaults now, but no controllable device can act until at least one managed device is added."
    else:
        policy_readiness = "Source roles are complete and managed devices exist, so Controls changes are actionable now."

    support_status = str(
        readiness.get("summary")
        or getattr(state, "health_summary", None)
        or getattr(state, "diagnostic_summary", None)
        or "Integration state not loaded yet"
    )
    detailed_management_summary = build_detailed_management_handoff(configured_devices, state=state)
    status_summary_map = {
        SOURCES_SECTION_LABEL: source_status,
        DEVICES_SECTION_LABEL: device_status,
        POLICY_SECTION_LABEL: policy_status,
        SUPPORT_SECTION_LABEL: support_status,
    }

    path_summary_map = {
        SOURCES_SECTION_LABEL: SOURCES_CONFIGURE_PATH,
        DEVICES_SECTION_LABEL: DEVICES_CONFIGURE_PATH,
        POLICY_SECTION_LABEL: POLICY_CONFIGURE_PATH,
        SUPPORT_SECTION_LABEL: SUPPORT_CONFIGURE_PATH,
    }

    install_status = str(install_provenance.get("summary") or "Installed package provenance unavailable")
    install_fingerprint_summary = build_install_fingerprint_summary(install_provenance)
    source_attention_summary_display = (
        source_attention_summary
        if source_attention_summary != "None"
        else "No source blockers currently highlighted"
    )
    install_alert = None
    if install_provenance_pending:
        install_alert = f"Install provenance refresh still pending: {install_consistency}"
    elif install_provenance.get("manifest_matches_code_version") is False:
        install_alert = f"Installed package needs exact-build revalidation: {install_consistency}"

    source_alert = None
    source_alert_compact = None
    if missing_required_sources:
        source_alert = "Missing required source roles: " + ", ".join(
            SOURCE_ROLE_LABELS.get(key, key) for key in missing_required_sources
        )
        source_alert_compact = source_alert
    elif runtime_source_attention:
        source_alert = f"Source blockers: {source_attention_summary_display}"
        compact_source_detail = (
            source_attention_roles
            if source_attention_roles != "None"
            else source_attention_summary_display
        )
        source_alert_compact = f"Source blockers: {compact_source_detail}"

    device_alert = None
    device_alert_compact = None
    review_alert = None
    review_alert_compact = None
    ready_alert = None
    ready_alert_compact = None
    ready_candidate_count = max(candidate_count - review_needed_count, 0)

    def _compact_alert_review_ready_target(prefix: str, preview: str, name: str) -> str:
        compact = _clip_review_ready_state_part(
            f"{prefix} {preview or name}".strip(),
            max_chars=72,
        )
        if compact.startswith(f"{prefix} "):
            return compact[len(prefix) + 1 :].strip()
        return preview or name
    if device_parse_issues:
        device_alert = f"Managed-device configuration needs repair for {_repair_item_count_label(len(device_parse_issues))}."
        device_alert_compact = device_alert
    else:
        if blocked_activity_count:
            if first_blocked_device:
                blocked_target = _command_center_runtime_device_preview(first_blocked_device)
                compact_blocked_target = _compact_command_center_device_alert_target(
                    "blocked ",
                    first_blocked_device,
                )
                if blocked_activity_count > 1:
                    device_alert = (
                        f"Managed Devices: {_blocked_activity_count_label(blocked_activity_count)}, "
                        f"starting with {blocked_target}"
                    )
                    device_alert_compact = (
                        f"Managed Devices: {_blocked_activity_count_label(blocked_activity_count)}, "
                        f"{compact_blocked_target or 'blocked managed device'}"
                    )
                else:
                    device_alert = f"Managed Devices: blocked {blocked_target}"
                    device_alert_compact = (
                        f"Managed Devices: {compact_blocked_target or 'blocked managed device'}"
                    )
            else:
                device_alert = f"Managed Devices: {_blocked_activity_count_label(blocked_activity_count)}"
                device_alert_compact = device_alert
        elif managed_attention_count:
            if first_attention_device:
                attention_target = _command_center_runtime_device_preview(first_attention_device)
                compact_attention_target = _compact_command_center_device_alert_target(
                    "attention first ",
                    first_attention_device,
                )
                if managed_attention_count > 1:
                    device_alert = (
                        f"Managed Devices: {_managed_attention_count_label(managed_attention_count)}, "
                        f"attention first {attention_target}"
                    )
                    device_alert_compact = (
                        f"Managed Devices: {_managed_attention_count_label(managed_attention_count)}, "
                        f"{compact_attention_target or 'attention first managed device'}"
                    )
                else:
                    device_alert = f"Managed Devices: attention first {attention_target}"
                    device_alert_compact = (
                        f"Managed Devices: {compact_attention_target or 'attention first managed device'}"
                    )
            else:
                device_alert = f"Managed Devices: {_managed_attention_count_label(managed_attention_count)}"
                device_alert_compact = device_alert
        elif not has_managed_devices:
            device_alert = "Managed Devices: no managed yet."
            device_alert_compact = device_alert
            if candidate_count:
                device_alert = (
                    f"Managed Devices: no managed yet; {_unmanaged_count_label(candidate_count)}."
                )
                device_alert_compact = device_alert

        if review_needed_count:
            review_target = review_candidate_preview or review_candidate_name or "the first unmanaged candidate"
            compact_review_target = _compact_alert_review_ready_target(
                "review",
                review_candidate_preview,
                review_candidate_name or "the first unmanaged candidate",
            )
            review_alert = f"Managed Devices: review first {review_target}"
            review_alert_compact = f"Managed Devices: review first {compact_review_target}"
            if ready_candidate_name and ready_candidate_name != review_candidate_name:
                ready_target = ready_candidate_preview or ready_candidate_name
                compact_ready_target = _compact_alert_review_ready_target(
                    "ready",
                    ready_candidate_preview,
                    ready_candidate_name,
                )
                review_alert += f"; ready next {ready_target}"
                review_alert_compact += f"; ready next {compact_ready_target}"
        elif ready_candidate_count:
            ready_target = ready_candidate_preview or ready_candidate_name or "the next unmanaged candidate"
            compact_ready_target = _compact_alert_review_ready_target(
                "ready",
                ready_candidate_preview,
                ready_candidate_name or "the next unmanaged candidate",
            )
            ready_alert = f"Managed Devices: ready next {ready_target}"
            ready_alert_compact = f"Managed Devices: ready next {compact_ready_target}"

    readiness_alert = str(readiness.get("summary") or support_status) if readiness_phase == "runtime_readiness" else None

    recommended_reason = _normalize_native_path_text(status_summary_map.get(recommended_section, support_status))
    top_alerts = [install_alert, source_alert, device_alert, review_alert or ready_alert, readiness_alert]
    if not any(top_alerts) and recommended_reason:
        top_alerts = [str(recommended_reason)]

    review_or_ready_compact = review_alert_compact or ready_alert_compact
    review_or_ready = review_alert or ready_alert
    top_alert_fallback = next(
        (
            alert
            for alert in [
                source_alert_compact,
                source_alert,
                device_alert_compact,
                device_alert,
                review_or_ready_compact,
                review_or_ready,
                readiness_alert,
                install_alert,
            ]
            if alert
        ),
        "No top-level alerts right now.",
    )
    compact_source_alert = source_alert_compact or source_alert
    compact_device_alert = device_alert_compact or device_alert
    tight_source_alert = (
        SOURCE_BLOCKER_ACTIVE_LABEL
        if (missing_required_sources or runtime_source_attention)
        else compact_source_alert
    )
    alert_summary = _compact_top_alert_summary(
        top_alerts,
        [source_alert, device_alert, review_or_ready, readiness_alert, install_alert],
        [source_alert, device_alert, review_or_ready_compact, readiness_alert],
        [tight_source_alert, compact_device_alert, review_or_ready_compact],
        [compact_source_alert, compact_device_alert, review_or_ready_compact],
        [compact_source_alert, device_alert, review_or_ready_compact],
        [tight_source_alert, compact_device_alert],
        [compact_source_alert, compact_device_alert],
        [compact_source_alert, device_alert, review_or_ready],
        [tight_source_alert, review_or_ready_compact],
        [compact_device_alert, review_or_ready_compact],
        [device_alert, review_or_ready_compact],
        [compact_source_alert, review_or_ready_compact],
        [compact_source_alert],
        [compact_device_alert],
        [device_alert],
        [review_or_ready_compact],
        [readiness_alert],
        [install_alert],
        fallback=top_alert_fallback,
    )

    recommended_path = path_summary_map.get(recommended_section, PRIMARY_CONFIGURE_PATH)

    status_summary_fallback = {
        SOURCES_SECTION_LABEL: (
            f"Open {SOURCES_CONFIGURE_PATH} to continue in Sensors and confirm the live source roles and health."
        ),
        DEVICES_SECTION_LABEL: device_next_step,
        POLICY_SECTION_LABEL: (
            f"Open {POLICY_CONFIGURE_PATH} to continue in Controls and tune target export, deadband, reserve, or live mode."
        ),
        SUPPORT_SECTION_LABEL: (
            f"Open {SUPPORT_CONFIGURE_PATH} to continue in Diagnostics with blocker triage, repairs, or install validation."
        ),
    }
    status_summary = _truncate_state_summary(
        str(recommended_reason),
        fallback=status_summary_fallback.get(
            recommended_section,
            f"Open {recommended_path} to continue in Configure.",
        ),
    )
    next_action_summary = _truncate_state_summary(
        _normalize_native_path_text(next_action_summary),
        fallback=_compact_next_action_fallback(
            missing_required_sources=missing_required_sources,
            runtime_source_attention=runtime_source_attention,
            recommended_section=recommended_section,
            device_parse_issues=device_parse_issues,
            has_managed_devices=has_managed_devices,
            candidate_count=candidate_count,
            managed_attention_count=managed_attention_count,
            blocked_activity_count=blocked_activity_count,
            first_blocked_device=first_blocked_device,
            first_planned_device=first_planned_device,
            first_attention_device=first_attention_device,
            review_candidate_name=review_candidate_name,
            review_candidate_preview=review_candidate_preview,
            ready_candidate_name=ready_candidate_name,
            ready_candidate_preview=ready_candidate_preview,
            top_candidate_name=top_candidate_name,
            top_candidate_preview=top_candidate_preview,
        ),
    )

    energy_state_summary = _truncate_state_summary(
        _compact_energy_state_summary(state) or "runtime pending | energy state waiting",
        fallback="runtime pending | energy state waiting",
    )
    control_decision_summary = _compact_control_decision_summary(
        current_mode=current_mode,
        target_export_w=int(merged.get(CONF_TARGET_EXPORT_W, DEFAULT_TARGET_EXPORT_W) or DEFAULT_TARGET_EXPORT_W),
        export_error_w=getattr(state, 'export_error_w', None) if state is not None else None,
        control_reason=str(getattr(state, 'control_reason', '') or '').strip(),
    )
    control_outcome_summary = _compact_control_outcome_summary(
        control_summary=str(getattr(state, 'control_summary', '') or '').strip(),
        planned_action_count=getattr(state, 'planned_action_count', None) if state is not None else None,
        executable_action_count=getattr(state, 'executable_action_count', None) if state is not None else None,
        active_controlled_power_w=getattr(state, 'active_controlled_power_w', None) if state is not None else None,
        active_managed_count=active_managed_count,
    )
    fleet_activity_summary_raw = _restore_active_device_under_overflow(
        _restore_ready_promotion_count_under_overflow(
            _compact_fleet_activity_overflow_summary(
                _prefer_review_ready_over_large_kind_mix(
                    _build_command_center_fleet_activity_summary(
                        state,
                        candidate_count=candidate_count,
                        fixed_candidate_count=fixed_candidate_count,
                        variable_candidate_count=variable_candidate_count,
                        review_needed_count=review_needed_count,
                        fixed_review_count=fixed_review_count,
                        variable_review_count=variable_review_count,
                        review_candidate_name=review_candidate_name,
                        review_candidate_preview=review_candidate_preview,
                        ready_candidate_name=ready_candidate_name,
                        ready_candidate_preview=ready_candidate_preview,
                        top_candidate_name=top_candidate_name,
                        top_candidate_preview=top_candidate_preview,
                        source_blocked=bool(missing_required_sources or runtime_source_attention),
                        configured_managed_count=len(configured_devices),
                    )
                )
            ),
            review_needed_count=review_needed_count,
            ready_candidate_count=ready_candidate_count,
        ),
        active_managed_count=active_managed_count,
        active_device_preview=active_device_preview,
        active_device_distinct=active_device_distinct,
        source_blocked=bool(missing_required_sources or runtime_source_attention),
    )
    if candidate_count:
        fleet_activity_summary_raw = _dedupe_fleet_activity_summary(
            fleet_activity_summary_raw,
            suppress_blocked=candidate_count > 1,
            suppress_planned=True,
        )
    fleet_activity_summary = _truncate_state_summary(
        fleet_activity_summary_raw,
        fallback=_fleet_activity_fallback_from_device_status(device_status),
    )

    return {
        "headline_decision": _clip_state_part(headline_decision, max_chars=MAX_NATIVE_SENSOR_STATE_CHARS)
        or "Runtime summary unavailable.",
        "alert_summary": alert_summary,
        "energy_state_summary": energy_state_summary,
        "control_decision_summary": control_decision_summary,
        "control_outcome_summary": control_outcome_summary,
        "fleet_activity_summary": fleet_activity_summary,
        "source_status": source_status,
        "source_attention_summary": source_attention_summary_display,
        "source_attention_roles": source_attention_roles,
        "blocking_validation_details": blocking_validation_details,
        "unavailable_sources": ", ".join(unavailable_source_roles) if unavailable_source_roles else "None",
        "stale_sources": ", ".join(stale_source_roles) if stale_source_roles else "None",
        "source_mapping_summary": build_source_mapping_summary(merged),
        "source_repair_step": source_repair_step,
        "device_status": device_status,
        "device_next_step": device_next_step,
        "policy_status": policy_status,
        "policy_readiness": policy_readiness,
        "support_status": support_status,
        "install_status": install_status,
        "install_consistency": install_consistency,
        "install_fingerprint_summary": install_fingerprint_summary,
        "status_summary": status_summary,
        "recommended_reason": recommended_reason,
        "recommended_section": recommended_section,
        "recommended_path": recommended_path,
        "next_action_summary": next_action_summary,
        "detailed_management_summary": detailed_management_summary,
        "sources_path": SOURCES_CONFIGURE_PATH,
        "devices_path": DEVICES_CONFIGURE_PATH,
        "policy_path": POLICY_CONFIGURE_PATH,
        "mode_path": MODE_CONTROL_PATH,
        "support_path": SUPPORT_CONFIGURE_PATH,
    }


def _compact_setup_checklist_lines(checklist: list[dict[str, Any]] | None) -> list[str]:
    items = list(checklist or [])
    if not items:
        return ["- Setup checklist status: no checklist available yet."]

    complete_count = sum(1 for item in items if item.get("complete"))
    pending_labels = [str(item.get("label") or "Unnamed check").strip() for item in items if not item.get("complete")]
    lines = [f"- Setup checklist status: {complete_count}/{len(items)} complete"]
    if pending_labels:
        preview = ", ".join(label for label in pending_labels[:3] if label)
        remaining = len(pending_labels) - min(len(pending_labels), 3)
        suffix = f", +{remaining} more" if remaining > 0 else ""
        lines.append(f"- Next incomplete checks: {preview}{suffix}")
    else:
        lines.append("- Next incomplete checks: all current setup checks are complete")
    return lines


def build_native_support_center(coordinator: Any) -> str:
    """Return a compact operator-facing diagnostics guide for native HA surfaces."""
    state, _, _, operator_readiness = _build_support_sections(coordinator)
    command_center = build_native_command_center_summary(coordinator)
    install_provenance = build_install_provenance()
    source_attention = build_source_attention_details(state)
    blocking_keys = _blocking_source_attention_keys(source_attention)
    blocking_validation_issues = [
        issue
        for issue in (source_attention.get("validation_details", {}).get("issues", []) or [])
        if str(issue.get("severity", "")).lower() == "error"
    ]
    fallback_hint = build_source_selector_fallback_hint(
        role_keys=blocking_keys,
        validation_issues=blocking_validation_issues,
    ) or "Not needed right now."
    support_next_step = str(operator_readiness.get("next_step") or "").strip()
    if not support_next_step and not install_provenance.get("live_validation_safe"):
        support_next_step = build_install_repair_step(install_provenance)
    if not support_next_step and (blocking_keys or blocking_validation_issues):
        support_next_step = str(command_center.get("source_repair_step") or "").strip()
    if not support_next_step:
        support_next_step = (
            f"Open {SUPPORT_CONFIGURE_PATH} to confirm the current blocker, then use "
            f"{DIAGNOSTICS_DEVICE_ACTIONS_PATH} or Settings -> Repairs if more troubleshooting is still needed."
        )
    install_next_step = (
        "Exact-build trust currently looks good. Use the device-page diagnostics snapshot only if you need the full install evidence."
        if install_provenance.get("live_validation_safe")
        else build_install_repair_step(install_provenance)
    )
    if blocking_keys or blocking_validation_issues:
        priority_candidate_hints = (
            f"Open {SOURCES_CONFIGURE_PATH} to review live source candidates for the blocked roles."
        )
    else:
        priority_candidate_hints = "Not needed right now."
    checklist_lines = _compact_setup_checklist_lines(operator_readiness.get("checklist"))
    snapshot_path = f"{INTEGRATION_DEVICE_PATH} -> Review diagnostics snapshot"
    checklist_path = f"{INTEGRATION_DEVICE_PATH} -> Show setup checklist"
    return "\n".join(
        [
            "Zero Net Export diagnostics guide",
            "",
            "Diagnostics is for blockers, runtime health, and install evidence.",
            "Troubleshooting, Repairs, and install validation belong in Diagnostics; Sensors, Controls, and Managed Devices keep normal operator work.",
            f"Command center path: {PRIMARY_CONFIGURE_PATH}",
            "",
            "Diagnostics now",
            f"- Readiness phase: {operator_readiness.get('phase')}",
            f"- Health summary: {operator_readiness.get('summary')}",
            f"- Top alerts: {command_center.get('alert_summary')}",
            "",
            "Blocker triage",
            f"- Blocking source roles: {_format_source_role_list(blocking_keys) if blocking_keys else 'None'}",
            f"- Blocking validation details: {command_center.get('blocking_validation_details') or 'None'}",
            f"- If Sensors owns the repair, use: {command_center.get('source_repair_step')}",
            f"- Source-role evidence: {command_center.get('sources_path')}",
            f"- Blocked-role candidate cues: {priority_candidate_hints}",
            f"- Selector fallback, only if Home Assistant rejects a valid choice: {fallback_hint}",
            "",
            "Install validation",
            f"- Installed package: {command_center.get('install_status')}",
            f"- Install consistency: {command_center.get('install_consistency')}",
            f"- Exact-build step: {install_next_step}",
            f"- Install evidence: {snapshot_path}",
            *checklist_lines,
            "",
            "Bucket ownership and paths",
            f"- {SOURCES_SECTION_LABEL}: {command_center.get('sources_path')}",
            f"- {POLICY_SECTION_LABEL}: {command_center.get('policy_path')}",
            f"- Live mode shortcut ({POLICY_SECTION_LABEL} device action): {command_center.get('mode_path')}",
            f"- {DEVICES_SECTION_LABEL}: {command_center.get('devices_path')}",
            f"- {SUPPORT_SECTION_LABEL}: {command_center.get('support_path')}",
            f"- Managed-device audit path: {command_center.get('detailed_management_summary')}",
            f"- Review diagnostics snapshot: {snapshot_path}",
            f"- Show setup checklist: {checklist_path}",
        ]
    )
