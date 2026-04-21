"""Native Home Assistant operator support helpers for Zero Net Export."""
from __future__ import annotations

from datetime import datetime
import json
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
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def _count_label(count: int, singular: str, plural: str | None = None) -> str:
    noun = singular if count == 1 else (plural or f"{singular}s")
    return f"{count} {noun}"


def _planned_action_count_label(count: int) -> str:
    return _count_label(count, "planned action")


def _managed_count_label(count: int) -> str:
    return "no managed yet" if count <= 0 else f"{count} managed"


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
    parts = [part.strip() for part in normalized.split(" | ") if part.strip()]
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


def _truncate_state_summary(text: str, *, fallback: str) -> str:
    normalized = " ".join(str(text).split())
    if len(normalized) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return normalized
    return fallback


def _compact_top_alert_summary(*variants: list[str], fallback: str) -> str:
    for variant in variants:
        summary = " | ".join(str(part).strip() for part in variant if str(part).strip())
        if summary and len(summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return summary
    return fallback


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
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, starting with attention on {attention_target}."
            )
        if review_candidate_name:
            compact_review = review_candidate_name
            compact_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, start in the unmanaged section: {compact_review}"
            )
            if ready_candidate_name and ready_candidate_name != review_candidate_name:
                compact_ready = ready_candidate_name
                compact_step += f", then promote next from the unmanaged section: {compact_ready}"
            return compact_step + "."
        if ready_candidate_name or top_candidate_name or top_candidate_preview:
            compact_ready = ready_candidate_preview or ready_candidate_name or top_candidate_preview or top_candidate_name or "the next unmanaged candidate"
            return (
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, then promote next from the unmanaged section: {compact_ready}."
            )
        if has_managed_devices:
            return (
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, edit device settings, or stage enablement changes."
            )
        return (
            f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available."
        )

    if recommended_section == POLICY_SECTION_LABEL:
        return (
            f"Open {POLICY_CONFIGURE_PATH} to continue in Controls and tune target export, deadband, reserve, or live mode."
        )
    if recommended_section == SOURCES_SECTION_LABEL:
        return f"Open {SOURCES_CONFIGURE_PATH} to continue in Sensors and confirm the live source mapping and health."
    return f"Open {SUPPORT_CONFIGURE_PATH} to continue the next native validation step."


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
            f"these mapped-source blockers first: {affected_roles_text}"
            if affected_roles_text and affected_roles_text != "None"
            else f"these mapped-source blockers ({'; '.join(attention_parts)})"
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
            f"repair these highlighted mapped roles first: {affected_roles_text}, then clear the blocking source validation errors ({blocking_details})"
            if affected_roles_text and affected_roles_text != "None"
            else f"repair the blocking source validation errors ({blocking_details})"
        )
        confirm_roles = affected_roles_text if affected_roles_text and affected_roles_text != "None" else blocking_details
        return (
            f"Open {SOURCES_CONFIGURE_PATH}, {blocker_text}. Confirm each mapped entity selection still points at the intended Home Assistant entity, then save and reload the integration, "
            f"{_confirm_recovery_suffix(confirm_roles)}"
        )

    return (
        f"Open {SOURCES_CONFIGURE_PATH}, review the mapped sources, then save and reload the integration, "
        "then reopen Sensors to confirm live source health."
    )


def build_live_source_health_summary(state: Any) -> str:
    """Return source-specific runtime health without leaking device/runtime summaries."""
    if state is None:
        return "Live source health will appear here after the integration loads."

    source_attention = build_source_attention_details(state)
    merged_attention = build_source_attention_summary(state, limit=4)
    if merged_attention != "None":
        return f"Mapped source roles need attention: {merged_attention}"

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
        return diagnostic_summary

    source_diagnostics = source_attention.get("source_diagnostics", {})
    if source_diagnostics:
        ok_count = sum(1 for details in source_diagnostics.values() if details.get("status") == "ok")
        return f"Mapped sources currently look healthy across {ok_count} mapped role(s)."

    return "Mapped sources currently look healthy."


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
    if _runtime_device_has_blocked_activity(detail):
        parts.append("not usable" if detail.get("usable") is False else "blocked")
    elif _runtime_device_has_active_plan(detail):
        planned_action = str(detail.get("planned_action") or "").strip()
        if planned_action:
            parts.append(f"action {planned_action}")
    elif _runtime_device_has_recent_attention(detail) and detail.get("last_action_status"):
        parts.append(f"last {detail.get('last_action_status')}")
    if detail.get("observed_active") is True and detail.get("current_power_w") not in (None, ""):
        active_power = f"active {float(detail.get('current_power_w') or 0):g} W"
        if active_power not in parts:
            parts.append(active_power)
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

    if detail.get("observed_active") is True and detail.get("current_power_w") not in (None, ""):
        active_power = f"active {float(detail.get('current_power_w') or 0):g} W"
        if active_power not in parts:
            parts.append(active_power)

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
    return active_count, round(active_power_w, 1)


def _build_operator_checklist(state: Any, entry: Any, configured_devices: list[dict[str, Any]], device_parse_issues: list[str]) -> dict[str, Any]:
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
            "label": "Required source mapping complete",
            "complete": not missing_required_sources,
            "detail": (
                "All required solar and grid sources are configured."
                if not missing_required_sources
                else "Missing required sources: "
                + ", ".join(SOURCE_ROLE_LABELS.get(key, key) for key in missing_required_sources)
            ),
        },
        {
            "key": "sources_validated",
            "label": "Source validation healthy",
            "complete": not blocking_validation_issues and not state_stale_data,
            "detail": (
                "Mapped sources currently validate cleanly enough for runtime control."
                if not blocking_validation_issues and not state_stale_data
                else (
                    f"Blocking validation issues: {len(blocking_validation_issues)}"
                    if blocking_validation_issues
                    else (stale_summary or "One or more mapped sources are stale.")
                )
            ),
        },
        {
            "key": "devices_configured",
            "label": "Controllable devices onboarded",
            "complete": bool(configured_devices) and not device_parse_issues,
            "detail": (
                f"{len(configured_devices)} device(s) configured."
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
                f"{state_usable_device_count} usable device(s) available right now."
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

    if missing_required_sources:
        phase = "source_setup"
        next_step = (
            f"Open {SOURCES_CONFIGURE_PATH}, finish the missing required source roles, then save and reload the integration."
        )
        summary = "Native setup is blocked on missing required source mappings."
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
                f"then fix the stale mapped sources. {stale_summary}."
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
        next_step = f"Open {DEVICES_CONFIGURE_PATH} and add the first controllable device."
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
            f"Validate {PRIMARY_CONFIGURE_PATH} plus {DIAGNOSTICS_DEVICE_ACTIONS_PATH} in a real "
            "Home Assistant install and refine any remaining friction there."
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
    )
    return state, configured_devices, device_parse_issues, operator_readiness


def build_detailed_management_handoff(
    configured_devices: list[dict[str, Any]] | None,
    *,
    state: Any | None = None,
) -> str:
    """Return the deeper native device-view handoff for per-device review and actions."""
    devices = configured_devices or []
    if not devices:
        return (
            f"Use {DEVICES_CONFIGURE_PATH} to review a currently surfaced unmanaged candidate in the Managed Devices workspace when one fits, or add the first fixed or variable load manually there, then use {DETAILED_MANAGEMENT_PATH} "
            "as the secondary device-page review path once the fleet exists."
        )

    usable_count = int(getattr(state, "usable_device_count", 0) or 0) if state is not None else 0
    if usable_count <= 0:
        return (
            f"Use {DETAILED_MANAGEMENT_PATH} as the secondary device-page review path to inspect each managed device's status, guards, plans, and reset actions, "
            "then return to Managed Devices to adjust the fleet if needed."
        )

    return (
        f"Use {DETAILED_MANAGEMENT_PATH} as the secondary device-page review path for per-device status, planned actions, guard state, and reset actions when the fleet needs deeper review."
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
        "Mapped sources",
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


def build_native_command_center_guide_text(command_center: dict[str, Any]) -> str:
    """Return the basic setup focused command-center guide text."""
    recommended_section = normalize_command_center_section(command_center.get("recommended_section"))
    alert_summary = _normalize_native_path_text(command_center.get("alert_summary"))
    next_action_summary = _normalize_native_path_text(command_center.get("next_action_summary"))
    recommended_path = _normalize_native_path_text(command_center.get("recommended_path"))
    return "\n".join(
        [
            "Zero Net Export command center",
            "",
            "Use this command center for live setup, the current operating picture, and the next native action.",
            "Finish source mapping and core control checks here.",
            "When the next step moves into fleet work, continue in the Managed Devices workspace.",
            "",
            "Now",
            f"- Headline decision: {command_center.get('headline_decision')}",
            f"- Alerts: {alert_summary}",
            f"- Recommended next step: {next_action_summary}",
            f"- Recommended section: {recommended_section}",
            f"- Recommended path: {recommended_path}",
            "",
            "Structured control board",
            f"- Energy state: {command_center.get('energy_state_summary')}",
            f"- Control decision: {command_center.get('control_decision_summary')}",
            f"- Control outcome: {command_center.get('control_outcome_summary')}",
            f"- Fleet activity: {command_center.get('fleet_activity_summary')}",
            "",
            "Setup check",
            f"- Sensors: {command_center.get('source_status')}",
            f"- Source map: {command_center.get('source_mapping_summary')}",
            f"- Controls: {command_center.get('policy_status')}",
            f"- Diagnostics: {command_center.get('support_status')}",
            f"- Source blockers: {command_center.get('source_attention_summary')}",
            f"- Repair path: {command_center.get('source_repair_step')}",
            "",
            "Native paths",
            f"- Sensors: {command_center.get('sources_path')}",
            f"- Controls: {command_center.get('policy_path')}",
            f"- Live mode shortcut (Controls device action): {command_center.get('mode_path')}",
            f"- Managed Devices: {command_center.get('devices_path')}",
            f"- Diagnostics: {command_center.get('support_path')}",
            "",
            "Bucket ownership",
            "- Sensors owns source mapping and source health.",
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
        return "Mapped sources need attention before control can continue."
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
) -> str:
    def _clip_part(text: str, *, max_chars: int) -> str:
        normalized = " ".join(str(text).split())
        if len(normalized) <= max_chars:
            return normalized
        if max_chars <= 3:
            return normalized[:max_chars]
        return normalized[: max_chars - 3].rstrip() + "..."

    summary = base_status
    if candidate_count <= 0:
        return summary
    summary += f"; {candidate_count} unmanaged"
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
        summary += f"; {_count_label(ready_candidate_count, 'ready to promote')}"
    if review_candidate_preview and review_candidate_name:
        summary += f"; review {review_candidate_preview}"
    if ready_candidate_preview and ready_candidate_name:
        summary += f"; ready {ready_candidate_preview}"
    if top_candidate_preview and top_candidate_name not in {review_candidate_name, ready_candidate_name}:
        summary += f"; surfaced {top_candidate_preview}"
    if len(summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return summary

    compact_parts: list[str] = [
        _clip_part(base_status, max_chars=72),
        f"{candidate_count} unmanaged",
    ]
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
        compact_parts.append(_count_label(ready_candidate_count, "ready to promote"))
        if ready_candidate_preview:
            compact_parts.append(f"ready {ready_candidate_preview}")
        elif ready_candidate_name:
            compact_parts.append(f"ready {ready_candidate_name}")
    compact_summary = "; ".join(compact_parts)
    if single_kind_overflow_backlog_parts:
        single_kind_compact_parts: list[str] = [
            _clip_part(base_status, max_chars=72),
            f"{candidate_count} unmanaged",
            *single_kind_overflow_backlog_parts,
        ]
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
            _clip_part(base_status, max_chars=72),
            f"{candidate_count} unmanaged",
            *single_kind_overflow_backlog_parts,
        ]
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
            _clip_part(base_status, max_chars=56),
            f"{candidate_count} unmanaged",
            *single_kind_overflow_backlog_parts,
        ]
        if review_candidate_name:
            single_kind_named_parts.append(f"review {review_candidate_name}")
        elif review_candidate_preview:
            single_kind_named_parts.append(f"review {review_candidate_preview}")
        if ready_candidate_name:
            single_kind_named_parts.append(f"ready {ready_candidate_name}")
        elif ready_candidate_preview:
            single_kind_named_parts.append(f"ready {ready_candidate_preview}")
        single_kind_named_summary = "; ".join(single_kind_named_parts)
        if len(single_kind_named_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return single_kind_named_summary

    clipped_compact_parts = [
        _clip_part(part, max_chars=72) if part.startswith(("review ", "ready ", "surfaced ")) else part
        for part in compact_parts
    ]
    clipped_compact_summary = "; ".join(clipped_compact_parts)
    if len(clipped_compact_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return clipped_compact_summary

    essential_parts: list[str] = [
        _clip_part(base_status, max_chars=48),
        f"{candidate_count} unmanaged",
    ]
    if backlog_parts:
        essential_parts.extend(backlog_parts)
    elif single_kind_backlog_parts:
        essential_parts.extend(single_kind_backlog_parts)
    if review_needed_count:
        essential_parts.append(_count_label(review_needed_count, "needs review", "need review"))
    if ready_candidate_count:
        essential_parts.append(_count_label(ready_candidate_count, "ready to promote"))
    if review_candidate_preview:
        essential_parts.append(_clip_part(f"review {review_candidate_preview}", max_chars=48))
    elif review_candidate_name:
        essential_parts.append(_clip_part(f"review {review_candidate_name}", max_chars=48))
    if ready_candidate_preview:
        essential_parts.append(_clip_part(f"ready {ready_candidate_preview}", max_chars=48))
    elif ready_candidate_name:
        essential_parts.append(_clip_part(f"ready {ready_candidate_name}", max_chars=48))

    essential_summary = "; ".join(essential_parts)
    if len(essential_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return essential_summary

    if single_kind_overflow_backlog_parts:
        single_kind_parts: list[str] = [
            _clip_part(base_status, max_chars=40),
            f"{candidate_count} unmanaged",
            *single_kind_overflow_backlog_parts,
        ]
        if review_needed_count:
            single_kind_parts.append(_count_label(review_needed_count, "needs review", "need review"))
            if review_candidate_preview:
                single_kind_parts.append(f"review {review_candidate_preview}")
            elif review_candidate_name:
                single_kind_parts.append(f"review {review_candidate_name}")
        if ready_candidate_count:
            single_kind_parts.append(_count_label(ready_candidate_count, "ready to promote"))
            if ready_candidate_preview:
                single_kind_parts.append(f"ready {ready_candidate_preview}")
            elif ready_candidate_name:
                single_kind_parts.append(f"ready {ready_candidate_name}")
        single_kind_summary = "; ".join(single_kind_parts)
        if len(single_kind_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return single_kind_summary

        concise_single_kind_parts: list[str] = [
            _clip_part(base_status, max_chars=40),
            f"{candidate_count} unmanaged",
            *single_kind_overflow_backlog_parts,
        ]
        if review_candidate_name:
            concise_single_kind_parts.append(f"review {review_candidate_name}")
        elif review_candidate_preview:
            concise_single_kind_parts.append(f"review {review_candidate_preview}")
        if ready_candidate_name:
            concise_single_kind_parts.append(f"ready {ready_candidate_name}")
        elif ready_candidate_preview:
            concise_single_kind_parts.append(f"ready {ready_candidate_preview}")
        concise_single_kind_summary = "; ".join(concise_single_kind_parts)
        if len(concise_single_kind_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return concise_single_kind_summary

        clipped_single_kind_parts = [
            _clip_part(part, max_chars=48) if part.startswith(("review ", "ready ")) else part
            for part in concise_single_kind_parts
        ]
        clipped_single_kind_summary = "; ".join(clipped_single_kind_parts)
        if len(clipped_single_kind_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return clipped_single_kind_summary

    minimal_parts: list[str] = [
        _clip_part(base_status, max_chars=40),
        f"{candidate_count} unmanaged",
    ]
    if review_needed_count:
        minimal_parts.append(_count_label(review_needed_count, "needs review", "need review"))
        minimal_parts.append(
            _clip_part(f"review {(review_candidate_preview or review_candidate_name)}", max_chars=36)
        )
    if ready_candidate_count:
        minimal_parts.append(_count_label(ready_candidate_count, "ready to promote"))
        minimal_parts.append(
            _clip_part(f"ready {(ready_candidate_preview or ready_candidate_name)}", max_chars=36)
        )
    minimal_summary = "; ".join(part for part in minimal_parts if part)
    if len(minimal_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return minimal_summary

    return _clip_part(minimal_summary or compact_summary or summary, max_chars=MAX_NATIVE_SENSOR_STATE_CHARS)


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
) -> str:
    managed_count = int(getattr(state, "device_count", 0) or 0) if state is not None else 0
    enabled_count = int(getattr(state, "enabled_device_count", 0) or 0) if state is not None else 0
    usable_count = int(getattr(state, "usable_device_count", 0) or 0) if state is not None else 0
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
    blocked_device_count = (
        sum(1 for detail in (getattr(state, "device_details", {}) or {}).values() if detail.get("usable") is False)
        if state is not None
        else 0
    )
    blocked_activity_count = blocked_device_count or (
        int(getattr(state, "blocked_planned_action_count", 0) or 0) if state is not None else 0
    )
    first_planned_device = _first_runtime_device_detail(
        state,
        predicate=_runtime_device_has_active_plan,
    )
    attention_kind = str((first_attention_device or {}).get("kind") or "").strip()
    if first_attention_device and (
        _same_runtime_device(first_attention_device, first_blocked_device)
        or _same_runtime_device(first_attention_device, first_planned_device)
    ):
        attention_name = str(
            (first_attention_device or {}).get("name")
            or (first_attention_device or {}).get("entity_id")
            or "managed device"
        ).strip()
        attention_parts = [attention_kind] if attention_kind else []
        if (
            first_attention_device.get("observed_active") is True
            and first_attention_device.get("current_power_w") not in (None, "")
        ):
            attention_parts.append(f"active {float(first_attention_device.get('current_power_w') or 0):g} W")
        attention_focus_label = (
            f"{attention_name} ({' | '.join(attention_parts)})" if attention_parts else attention_name
        )
    else:
        attention_focus_label = _command_center_managed_snapshot_focus_label(first_attention_device)
    first_active_device = _first_runtime_device_detail(
        state,
        predicate=lambda detail: detail.get("observed_active") is True,
    )
    planned_activity_count = (
        sum(1 for detail in (getattr(state, "device_details", {}) or {}).values() if _runtime_device_has_active_plan(detail))
        if state is not None
        else 0
    )

    summary_parts: list[str] = [_managed_count_label(managed_count)]

    ready_candidate_count = max(candidate_count - review_needed_count, 0)
    fixed_ready_count = max(fixed_candidate_count - fixed_review_count, 0)
    variable_ready_count = max(variable_candidate_count - variable_review_count, 0)

    if managed_count == 0 and source_blocked:
        summary_parts.append("repair sources first")
    elif source_blocked and managed_count > 0:
        summary_parts.append("repair sources first")

    if managed_count > 0:
        if attention_device_count:
            summary_parts.append(
                "1 managed device needs attention"
                if attention_device_count == 1
                else f"{attention_device_count} managed devices need attention"
            )
        if first_attention_device:
            summary_parts.append(
                f"attention first {attention_focus_label or _command_center_fleet_focus_label(first_attention_device)}"
            )
        if blocked_activity_count:
            summary_parts.append(
                f"blocked {_command_center_fleet_focus_label(first_blocked_device)}"
                if first_blocked_device
                else f"blocked {blocked_activity_count}"
            )
        if planned_activity_count:
            summary_parts.append(
                _planned_action_count_label(planned_activity_count)
            )
        if first_planned_device:
            summary_parts.append(
                f"plan {_command_center_fleet_focus_label(first_planned_device, include_plan_context=True)}"
            )
        if active_managed_power_w > 0:
            summary_parts.append(f"active load {active_managed_power_w:g} W")
            summary_parts.append(
                "1 active managed device"
                if active_managed_count == 1
                else f"{active_managed_count} active managed devices"
            )
            if first_active_device and (not attention_device_count or not _same_runtime_device(first_active_device, first_attention_device)) and (not blocked_activity_count or (first_blocked_device and not _same_runtime_device(first_active_device, first_blocked_device))) and (not planned_activity_count or (first_planned_device and not _same_runtime_device(first_active_device, first_planned_device))):
                summary_parts.append(
                    f"active device {_command_center_managed_snapshot_focus_label(first_active_device)}"
                )

    if candidate_count:
        summary_parts.append(f"{candidate_count} unmanaged")
    else:
        summary_parts.append("no unmanaged candidates")

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

    if managed_count > 0:
        summary_parts.extend([f"enabled {enabled_count}", f"usable {usable_count}"])
        if kind_known:
            summary_parts.append(f"{fixed_managed_count} fixed managed")
            if variable_managed_count:
                summary_parts.append(f"{variable_managed_count} variable managed")
            summary_parts.append(f"{nominal_power_w} W nominal")

    summary = " | ".join(summary_parts)
    if len(summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return summary

    compact_summary_parts = list(summary_parts)
    optional_part_matchers = [
        lambda part: part.startswith("usable "),
        lambda part: part.startswith("enabled "),
        lambda part: _matches_count_label(part, "fixed review"),
        lambda part: _matches_count_label(part, "variable review"),
        lambda part: part.startswith("fixed backlog "),
        lambda part: part.startswith("variable backlog "),
        lambda part: _matches_count_label(part, "fixed managed"),
        lambda part: _matches_count_label(part, "variable managed"),
        lambda part: part.endswith(" W nominal"),
        lambda part: _matches_count_label(part, "planned action"),
        lambda part: part.startswith("plan "),
    ]
    for matcher in optional_part_matchers:
        if len(" | ".join(compact_summary_parts)) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            break
        for index, part in enumerate(list(compact_summary_parts)):
            if matcher(part):
                del compact_summary_parts[index]
                break

    compact_summary = " | ".join(compact_summary_parts)
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
    if compact_summary and len(compact_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return compact_summary

    def _clip_part(text: str, *, max_chars: int) -> str:
        normalized = " ".join(str(text).split())
        if len(normalized) <= max_chars:
            return normalized
        if max_chars <= 3:
            return normalized[:max_chars]
        return normalized[: max_chars - 3].rstrip() + "..."

    minimal_parts: list[str] = [_managed_count_label(managed_count)]

    if source_blocked:
        minimal_parts.append("repair sources first")

    if managed_count > 0 and kind_known and variable_managed_count:
        minimal_parts.append(f"{fixed_managed_count} fixed managed")
        minimal_parts.append(f"{variable_managed_count} variable managed")

    if attention_device_count:
        minimal_parts.append(
            "1 managed device needs attention"
            if attention_device_count == 1
            else f"{attention_device_count} managed devices need attention"
        )

    if first_attention_device:
        minimal_parts.append(
            _clip_part(
                f"attention first {attention_focus_label or _command_center_fleet_focus_label(first_attention_device)}",
                max_chars=72,
            )
        )
    if first_blocked_device:
        minimal_parts.append(
            _clip_part(
                f"blocked {_command_center_fleet_focus_label(first_blocked_device)}",
                max_chars=72,
            )
        )
    elif blocked_activity_count:
        minimal_parts.append(f"blocked {blocked_activity_count}")

    if planned_activity_count:
        minimal_parts.append(_planned_action_count_label(planned_activity_count))
        if first_planned_device:
            minimal_parts.append(
                _clip_part(
                    f"plan {_command_center_fleet_focus_label(first_planned_device, include_plan_context=True)}",
                    max_chars=72,
                )
            )

    if active_managed_power_w > 0:
        minimal_parts.append(f"active load {active_managed_power_w:g} W")
        minimal_parts.append(
            "1 active managed device"
            if active_managed_count == 1
            else f"{active_managed_count} active managed devices"
        )
        if first_active_device and (not attention_device_count or not _same_runtime_device(first_active_device, first_attention_device)) and (not blocked_activity_count or (first_blocked_device and not _same_runtime_device(first_active_device, first_blocked_device))) and (not planned_activity_count or (first_planned_device and not _same_runtime_device(first_active_device, first_planned_device))):
            minimal_parts.append(
                _clip_part(
                    f"active device {_command_center_managed_snapshot_focus_label(first_active_device)}",
                    max_chars=72,
                )
            )

    ready_candidate_count = max(candidate_count - review_needed_count, 0)
    if candidate_count:
        minimal_parts.append(f"{candidate_count} unmanaged")
    else:
        minimal_parts.append("no unmanaged candidates")

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

    if review_needed_count:
        minimal_parts.append(
            "1 needs review" if review_needed_count == 1 else f"{review_needed_count} need review"
        )
        if review_candidate_preview:
            minimal_parts.append(_clip_part(f"review {review_candidate_preview}", max_chars=72))
        elif review_candidate_name:
            minimal_parts.append(_clip_part(f"review {review_candidate_name}", max_chars=72))

    if ready_candidate_count:
        minimal_parts.append(
            "1 ready to promote"
            if ready_candidate_count == 1
            else f"{ready_candidate_count} ready to promote"
        )
        if ready_candidate_preview and ready_candidate_name:
            minimal_parts.append(_clip_part(f"ready {ready_candidate_preview}", max_chars=72))
        elif ready_candidate_name:
            minimal_parts.append(_clip_part(f"ready {ready_candidate_name}", max_chars=72))

    if top_candidate_preview and top_candidate_name not in {review_candidate_name, ready_candidate_name}:
        minimal_parts.append(_clip_part(f"surfaced {top_candidate_preview}", max_chars=72))
    elif top_candidate_name and top_candidate_name not in {review_candidate_name, ready_candidate_name}:
        minimal_parts.append(_clip_part(f"surfaced {top_candidate_name}", max_chars=72))

    if managed_count > 0:
        minimal_parts.append(f"enabled {enabled_count}")
        minimal_parts.append(f"usable {usable_count}")

    if kind_known and nominal_power_w > 0:
        minimal_parts.append(f"{nominal_power_w} W nominal")

    minimal_summary = " | ".join(minimal_parts)
    if len(minimal_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return minimal_summary

    if managed_count <= 0 and fixed_candidate_count and variable_candidate_count:
        empty_fleet_kind_parts: list[str] = [_managed_count_label(managed_count)]
        if source_blocked:
            empty_fleet_kind_parts.append("repair sources first")
        empty_fleet_kind_parts.extend(
            [
                f"{candidate_count} unmanaged",
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
                    _clip_part(f"review {review_candidate_preview}", max_chars=40)
                )
            elif review_candidate_name:
                empty_fleet_kind_parts.append(
                    _clip_part(f"review {review_candidate_name}", max_chars=40)
                )
        if ready_candidate_count:
            empty_fleet_kind_parts.append(
                "1 ready to promote"
                if ready_candidate_count == 1
                else f"{ready_candidate_count} ready to promote"
            )
            if ready_candidate_preview and ready_candidate_name:
                empty_fleet_kind_parts.append(
                    _clip_part(f"ready {ready_candidate_preview}", max_chars=40)
                )
            elif ready_candidate_name:
                empty_fleet_kind_parts.append(
                    _clip_part(f"ready {ready_candidate_name}", max_chars=40)
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
        lambda part: _matches_count_label(part, "fixed managed"),
        lambda part: _matches_count_label(part, "variable managed"),
        lambda part: part.endswith(" W nominal"),
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
                if part.endswith(" unmanaged") or part == "no unmanaged candidates"
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
                _matches_count_label(part, "needs review", "need review")
                or _matches_count_label(part, "ready to promote")
            )
        ]
        compact_single_kind_review_focus_parts = [
            _clip_part(part, max_chars=28)
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
        and first_active_device
        and (not first_attention_device or not _same_runtime_device(first_active_device, first_attention_device))
        and (not first_blocked_device or not _same_runtime_device(first_active_device, first_blocked_device))
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
            if not backlog_inserted and (part.endswith(" unmanaged") or part == "no unmanaged candidates"):
                managed_unmanaged_split_parts.extend(backlog_parts)
                backlog_inserted = True
        if not backlog_inserted:
            managed_unmanaged_split_parts.extend(backlog_parts)
        managed_unmanaged_split_summary = " | ".join(managed_unmanaged_split_parts)
        if managed_unmanaged_split_summary and len(managed_unmanaged_split_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
            return managed_unmanaged_split_summary

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
        _clip_part(part, max_chars=48)
        if part.startswith(("blocked ", "attention first ", "review ", "ready ", "surfaced "))
        else part
        for part in minimal_parts
    ]
    compact_minimal_summary = " | ".join(compact_minimal_parts)
    if compact_minimal_summary and len(compact_minimal_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return compact_minimal_summary

    essential_parts: list[str] = [_managed_count_label(managed_count)]
    if source_blocked:
        essential_parts.append("repair sources first")
    if first_attention_device:
        essential_parts.append(
            _clip_part(
                f"attention first {attention_focus_label or _command_center_fleet_focus_label(first_attention_device)}",
                max_chars=32,
            )
        )
    if blocked_activity_count:
        essential_parts.append(
            _clip_part(
                f"blocked {_command_center_fleet_focus_label(first_blocked_device)}"
                if first_blocked_device
                else f"blocked {blocked_activity_count}",
                max_chars=32,
            )
        )
    if planned_activity_count:
        essential_parts.append(_planned_action_count_label(planned_activity_count))
    if active_managed_power_w > 0:
        essential_parts.append(f"active load {active_managed_power_w:g} W")
        essential_parts.append(
            "1 active managed device"
            if active_managed_count == 1
            else f"{active_managed_count} active managed devices"
        )
        if first_active_device and (not attention_device_count or not _same_runtime_device(first_active_device, first_attention_device)) and (not blocked_activity_count or (first_blocked_device and not _same_runtime_device(first_active_device, first_blocked_device))) and (not planned_activity_count or (first_planned_device and not _same_runtime_device(first_active_device, first_planned_device))):
            essential_parts.append(
                _clip_part(
                    f"active device {_command_center_managed_snapshot_focus_label(first_active_device)}",
                    max_chars=32,
                )
            )
    essential_parts.append(f"{candidate_count} unmanaged" if candidate_count else "no unmanaged candidates")
    if fixed_candidate_count and variable_candidate_count:
        essential_parts.append(_count_label(fixed_candidate_count, "fixed candidate"))
        essential_parts.append(_count_label(variable_candidate_count, "variable candidate"))
    if review_needed_count:
        essential_parts.append(
            "1 needs review" if review_needed_count == 1 else f"{review_needed_count} need review"
        )
        if review_candidate_preview:
            essential_parts.append(_clip_part(f"review {review_candidate_preview}", max_chars=32))
        elif review_candidate_name:
            essential_parts.append(_clip_part(f"review {review_candidate_name}", max_chars=32))
    if ready_candidate_count:
        essential_parts.append(
            "1 ready to promote"
            if ready_candidate_count == 1
            else f"{ready_candidate_count} ready to promote"
        )
        if ready_candidate_preview and ready_candidate_name:
            essential_parts.append(_clip_part(f"ready {ready_candidate_preview}", max_chars=32))
        elif ready_candidate_name:
            essential_parts.append(_clip_part(f"ready {ready_candidate_name}", max_chars=32))

    essential_summary = " | ".join(essential_parts)
    if essential_summary and len(essential_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return essential_summary

    managed_backlog_essential_parts: list[str] = []
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
                _clip_part(f"review {review_backlog_label}", max_chars=32)
            )
        elif part.startswith("ready ") and ready_backlog_label:
            managed_backlog_essential_parts.append(
                _clip_part(f"ready {ready_backlog_label}", max_chars=32)
            )
        else:
            managed_backlog_essential_parts.append(part)
    if single_kind_overflow_backlog_parts and candidate_count > 1:
        insertion_index = next(
            (
                index + 1
                for index, part in enumerate(managed_backlog_essential_parts)
                if part.endswith(" unmanaged") or part == "no unmanaged candidates"
            ),
            len(managed_backlog_essential_parts),
        )
        for backlog_part in reversed(single_kind_overflow_backlog_parts):
            if backlog_part not in managed_backlog_essential_parts:
                managed_backlog_essential_parts.insert(insertion_index, backlog_part)
    managed_backlog_essential_summary = " | ".join(managed_backlog_essential_parts)
    if managed_backlog_essential_summary and len(managed_backlog_essential_summary) <= MAX_NATIVE_SENSOR_STATE_CHARS:
        return managed_backlog_essential_summary

    if single_kind_overflow_backlog_parts and candidate_count > 1:
        compact_single_kind_backlog_parts = [
            part
            for part in managed_backlog_essential_parts
            if not (
                _matches_count_label(part, "needs review", "need review")
                or _matches_count_label(part, "ready to promote")
                or part.startswith("active device ")
            )
        ]
        compact_single_kind_backlog_parts = [
            _clip_part(part, max_chars=28)
            if part.startswith(("attention first ", "blocked ", "review ", "ready "))
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
        _clip_part(part, max_chars=36)
        if part.startswith(("review ", "ready ", "surfaced "))
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
    blocked_activity_count = (
        sum(1 for detail in (getattr(state, "device_details", {}) or {}).values() if _runtime_device_has_blocked_activity(detail))
        if state is not None
        else 0
    )
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
        attention_prefix = "Mapped source blockers: " + source_attention_summary if source_attention_summary != "None" else "Mapped sources need attention."
        validation_suffix = (
            f" Blocking validation details: {blocking_validation_details}"
            if blocking_validation_details != "None"
            else ""
        )
        source_status = attention_prefix + validation_suffix
    elif state is None:
        source_status = "Source health will appear here after the integration loads."
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
            f"{len(configured_devices)} configured, with {len(device_parse_issues)} issue(s) to repair",
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
        )
        device_next_step = f"Open {DEVICES_CONFIGURE_PATH} to repair the managed-device configuration before relying on control."
    elif has_managed_devices:
        runtime_device_status = str(getattr(state, "device_status_summary", "") or "").strip() if state is not None else ""
        device_status = _command_center_device_status_with_unmanaged_context(
            runtime_device_status or f"{runtime_device_count} configured",
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
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, starting with attention on {attention_target}."
            )
        elif candidate_count:
            if review_candidate_name:
                device_next_step = (
                    f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, start in the unmanaged section: "
                    f"{review_candidate_preview or review_candidate_name}"
                )
                if ready_candidate_name and ready_candidate_name != review_candidate_name:
                    device_next_step += (
                        f", then promote next from the unmanaged section: "
                        f"{ready_candidate_preview or ready_candidate_name}"
                    )
            else:
                device_next_step = (
                    f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, then promote next from the unmanaged section: "
                    f"{ready_candidate_preview or top_candidate_preview or top_candidate_name or 'the next unmanaged candidate'}"
                )
        else:
            device_next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, edit device settings, or stage enablement changes."
            )
    else:
        device_status = _command_center_device_status_with_unmanaged_context(
            "Managed Devices: no managed devices configured yet",
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
        )
        if review_candidate_name:
            device_next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, start in the unmanaged section: "
                f"{review_candidate_preview or review_candidate_name}"
            )
            if ready_candidate_name and ready_candidate_name != review_candidate_name:
                device_next_step += (
                    f", then promote next from the unmanaged section: "
                    f"{ready_candidate_preview or ready_candidate_name}"
                )
        elif ready_candidate_name or top_candidate_preview or top_candidate_name:
            device_next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, then promote next from the unmanaged section: "
                f"{ready_candidate_preview or ready_candidate_name or top_candidate_preview or top_candidate_name or 'the next unmanaged candidate'}"
            )
        else:
            device_next_step = (
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available."
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
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, start in the unmanaged section: "
                f"{review_candidate_preview or review_candidate_name}"
            )
            if ready_candidate_name and ready_candidate_name != review_candidate_name:
                next_action_summary += (
                    f", then promote next from the unmanaged section: "
                    f"{ready_candidate_preview or ready_candidate_name}"
                )
        elif ready_candidate_name or ready_candidate_preview or top_candidate_preview or top_candidate_name:
            next_action_summary = (
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, then promote next from the unmanaged section: "
                f"{ready_candidate_preview or ready_candidate_name or top_candidate_preview or top_candidate_name or primary_candidate_focus}"
            )
        else:
            next_action_summary = (
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available."
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
                f"Open {SOURCES_CONFIGURE_PATH} next to confirm the live source mapping and source health."
            )
        elif recommended_section == POLICY_SECTION_LABEL:
            next_action_summary = (
                f"Sources and devices are in place, so open {POLICY_CONFIGURE_PATH} next to tune target export, deadband, reserve, or live mode."
            )
        else:
            next_action_summary = str(
                readiness.get("next_step")
                or f"Open {SUPPORT_CONFIGURE_PATH} to continue the next native validation step."
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
        policy_readiness = "Finish source mapping first. Policy tuning is not actionable until the required mapped roles are complete."
    elif runtime_source_attention:
        policy_readiness = f"Repair mapped-source blockers in {SOURCES_CONFIGURE_PATH} before treating policy changes as actionable runtime changes."
    elif device_parse_issues:
        policy_readiness = "Repair the managed-device configuration first so policy changes apply to a trustworthy fleet."
    elif not has_managed_devices:
        policy_readiness = "You can tune policy now, but no controllable device can act until at least one managed device is added."
    else:
        policy_readiness = "Sources are mapped and managed devices exist, so policy changes are actionable now."

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
        else "No mapped-source blockers currently highlighted"
    )
    install_alert = None
    if install_provenance_pending:
        install_alert = f"Install provenance refresh still pending: {install_consistency}"
    elif install_provenance.get("manifest_matches_code_version") is False:
        install_alert = f"Installed package needs exact-build revalidation: {install_consistency}"

    source_alert = None
    if missing_required_sources:
        source_alert = "Missing required source roles: " + ", ".join(
            SOURCE_ROLE_LABELS.get(key, key) for key in missing_required_sources
        )
    elif runtime_source_attention:
        source_alert = f"Mapped-source blockers: {source_attention_summary_display}"

    device_alert = None
    review_alert = None
    review_alert_compact = None
    ready_alert = None
    ready_alert_compact = None
    ready_candidate_count = max(candidate_count - review_needed_count, 0)
    if device_parse_issues:
        device_alert = f"Managed-device configuration needs repair for {len(device_parse_issues)} item(s)."
    else:
        if blocked_activity_count:
            blocked_target = (
                _command_center_runtime_device_preview(first_blocked_device)
                if first_blocked_device
                else f"{blocked_activity_count} blocked managed device(s)"
            )
            device_alert = f"Managed Devices: blocked {blocked_target}"
        elif managed_attention_count:
            attention_target = (
                _command_center_runtime_device_preview(first_attention_device)
                if first_attention_device
                else (
                    "1 managed device needs attention"
                    if managed_attention_count == 1
                    else f"{managed_attention_count} managed devices need attention"
                )
            )
            device_alert = f"Managed Devices: {attention_target}"
        elif not has_managed_devices:
            device_alert = "Managed Devices: no managed devices configured yet."

        if review_needed_count:
            review_target = review_candidate_preview or review_candidate_name or "the first unmanaged candidate"
            review_alert = f"Unmanaged review first: {review_target}"
            review_alert_compact = f"Unmanaged review first: {review_candidate_name or 'the first unmanaged candidate'}"
            if ready_candidate_name and ready_candidate_name != review_candidate_name:
                ready_target = ready_candidate_preview or ready_candidate_name
                review_alert += f"; ready next {ready_target}"
                review_alert_compact += f"; ready next {ready_candidate_name}"
        elif ready_candidate_count:
            ready_target = ready_candidate_preview or ready_candidate_name or "the next unmanaged candidate"
            ready_alert = f"Unmanaged ready next: {ready_target}"
            ready_alert_compact = f"Unmanaged ready next: {ready_candidate_name or 'the next unmanaged candidate'}"

    readiness_alert = str(readiness.get("summary") or support_status) if readiness_phase == "runtime_readiness" else None

    recommended_reason = status_summary_map.get(recommended_section, support_status)
    top_alerts = [install_alert, source_alert, device_alert, review_alert or ready_alert, readiness_alert]
    if not any(top_alerts) and recommended_reason:
        top_alerts = [str(recommended_reason)]

    review_or_ready_compact = review_alert_compact or ready_alert_compact
    review_or_ready = review_alert or ready_alert
    top_alert_fallback = next(
        (
            alert
            for alert in [source_alert, device_alert, review_or_ready_compact, review_or_ready, readiness_alert, install_alert]
            if alert
        ),
        "No top-level alerts right now.",
    )
    alert_summary = _compact_top_alert_summary(
        top_alerts,
        [source_alert, device_alert, review_or_ready, readiness_alert, install_alert],
        [source_alert, device_alert, review_or_ready_compact, readiness_alert],
        [source_alert, device_alert, review_or_ready_compact],
        [source_alert, device_alert, review_or_ready],
        [source_alert, device_alert],
        [device_alert, review_or_ready_compact],
        [device_alert],
        [review_or_ready_compact],
        [readiness_alert],
        [install_alert],
        fallback=top_alert_fallback,
    )

    recommended_path = path_summary_map.get(recommended_section, PRIMARY_CONFIGURE_PATH)

    status_summary = _truncate_state_summary(
        str(recommended_reason),
        fallback=(
            f"Open {recommended_path} to continue in the recommended command-center section."
            if recommended_section != DEVICES_SECTION_LABEL
            else f"Open {DEVICES_CONFIGURE_PATH} to continue fleet work."
        ),
    )
    next_action_summary = _truncate_state_summary(
        str(next_action_summary),
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
        " | ".join(
            part
            for part in [
                f"solar {getattr(state, 'solar_power_w', None)} W" if state is not None and getattr(state, 'solar_power_w', None) is not None else None,
                f"grid import {getattr(state, 'grid_import_power_w', None)} W" if state is not None and getattr(state, 'grid_import_power_w', None) is not None else None,
                f"grid export {getattr(state, 'grid_export_power_w', None)} W" if state is not None and getattr(state, 'grid_export_power_w', None) is not None else None,
                f"home load {getattr(state, 'home_load_power_w', None)} W" if state is not None and getattr(state, 'home_load_power_w', None) is not None else None,
                f"battery {getattr(state, 'battery_soc', None)}%" if state is not None and getattr(state, 'battery_soc', None) is not None else None,
                f"battery charge {getattr(state, 'battery_charge_power_w', None)} W" if state is not None and getattr(state, 'battery_charge_power_w', None) is not None else None,
                f"battery discharge {getattr(state, 'battery_discharge_power_w', None)} W" if state is not None and getattr(state, 'battery_discharge_power_w', None) is not None else None,
            ]
            if part is not None
        ) or "Energy state will appear here after runtime loads.",
        fallback="Energy state will appear here after runtime loads.",
    )
    control_decision_summary = _truncate_state_summary(
        " | ".join(
            part
            for part in [
                f"mode {current_mode}",
                f"target {int(merged.get(CONF_TARGET_EXPORT_W, DEFAULT_TARGET_EXPORT_W) or DEFAULT_TARGET_EXPORT_W)} W",
                f"error {getattr(state, 'export_error_w', None)} W" if state is not None and getattr(state, 'export_error_w', None) is not None else None,
                str(getattr(state, 'control_reason', '') or '').strip() or None,
            ]
            if part is not None
        ) or f"mode {current_mode}",
        fallback=f"mode {current_mode}",
    )
    control_outcome_summary = _truncate_state_summary(
        " | ".join(
            part
            for part in [
                str(getattr(state, 'control_summary', '') or '').strip() or None,
                f"planned actions {getattr(state, 'planned_action_count', None)}" if state is not None and getattr(state, 'planned_action_count', None) is not None else None,
                f"executable {getattr(state, 'executable_action_count', None)}" if state is not None and getattr(state, 'executable_action_count', None) is not None else None,
                f"active load {getattr(state, 'active_controlled_power_w', None)} W" if state is not None and getattr(state, 'active_controlled_power_w', None) is not None else None,
            ]
            if part is not None
        ) or "Control outcome will appear here after runtime loads.",
        fallback="Control outcome will appear here after runtime loads.",
    )
    fleet_activity_summary = _truncate_state_summary(
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
            )
        ),
        fallback=device_status,
    )

    return {
        "headline_decision": _truncate_state_summary(headline_decision, fallback="Runtime summary unavailable."),
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
            f"{DIAGNOSTICS_DEVICE_ACTIONS_PATH} or Settings -> Repairs if deeper triage is still needed."
        )
    install_next_step = (
        "Exact-build trust currently looks good. Use the device-page diagnostics snapshot only if you need the full install evidence."
        if install_provenance.get("live_validation_safe")
        else build_install_repair_step(install_provenance)
    )
    if blocking_keys or blocking_validation_issues:
        priority_candidate_hints = (
            f"Open {SOURCES_CONFIGURE_PATH} to review the ranked live source candidates for the blocked roles."
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
            "Use Diagnostics when setup is blocked, runtime health needs explanation, or install trust needs proof.",
            f"Primary setup path: {PRIMARY_CONFIGURE_PATH}",
            "",
            "Diagnostics now",
            f"- Readiness phase: {operator_readiness.get('phase')}",
            f"- Health summary: {operator_readiness.get('summary')}",
            f"- Top alerts: {command_center.get('alert_summary')}",
            "",
            "Blocker triage",
            f"- Blocking mapped roles: {_format_source_role_list(blocking_keys) if blocking_keys else 'None'}",
            f"- Blocking validation details: {command_center.get('blocking_validation_details') or 'None'}",
            f"- If Sensors owns the repair, use: {command_center.get('source_repair_step')}",
            f"- For deeper source-map detail, open Sensors: {command_center.get('sources_path')}",
            f"- Best live candidate cues for blocked roles: {priority_candidate_hints}",
            f"- Selector workaround, only if Home Assistant rejects a valid choice: {fallback_hint}",
            "",
            "Install validation",
            f"- Installed package: {command_center.get('install_status')}",
            f"- Install consistency: {command_center.get('install_consistency')}",
            f"- Exact-build next step: {install_next_step}",
            f"- Full install evidence: {snapshot_path}",
            *checklist_lines,
            "",
            "Bucket ownership and paths",
            f"- {SOURCES_SECTION_LABEL}: {command_center.get('sources_path')}",
            f"- {POLICY_SECTION_LABEL}: {command_center.get('policy_path')}",
            f"- Live mode shortcut ({POLICY_SECTION_LABEL} device action): {command_center.get('mode_path')}",
            f"- {DEVICES_SECTION_LABEL}: {command_center.get('devices_path')}",
            f"- {SUPPORT_SECTION_LABEL}: {command_center.get('support_path')}",
            f"- Managed-device deep review: {command_center.get('detailed_management_summary')}",
            f"- Review diagnostics snapshot: {snapshot_path}",
            f"- Show setup checklist: {checklist_path}",
        ]
    )
