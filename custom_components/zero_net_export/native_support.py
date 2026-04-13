"""Native Home Assistant operator support helpers for Zero Net Export."""
from __future__ import annotations

from datetime import datetime
import json
from typing import Any

from homeassistant.util import dt as dt_util

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
    build_release_info,
)
from .validation import SourceSpec, format_source_binding_label

PRIMARY_CONFIGURE_PATH = "Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure"
INTEGRATION_DEVICE_PATH = (
    "Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device"
)
SOURCES_CONFIGURE_PATH = f"{PRIMARY_CONFIGURE_PATH} -> Sensors"
DEVICES_CONFIGURE_PATH = f"{PRIMARY_CONFIGURE_PATH} -> Managed devices"
ADVANCED_DEVICES_CONFIGURE_PATH = f"{DEVICES_CONFIGURE_PATH} -> Advanced JSON editor and recovery"
DETAILED_MANAGEMENT_PATH = (
    f"{INTEGRATION_DEVICE_PATH} -> managed-device entities, per-device status sensors, reset-override buttons, and native support actions"
)
POLICY_CONFIGURE_PATH = f"{PRIMARY_CONFIGURE_PATH} -> Controls"
MODE_CONTROL_PATH = f"{INTEGRATION_DEVICE_PATH} -> Mode"
SUPPORT_CONFIGURE_PATH = (
    f"{PRIMARY_CONFIGURE_PATH} -> Diagnostics; deeper health review: "
    f"{INTEGRATION_DEVICE_PATH} -> Show support center / Show setup checklist / Show native diagnostics snapshot; "
    "Settings -> Repairs"
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

    for key, details in source_diagnostics.items():
        freshness = source_freshness.get(key, {}) or {}
        merged = dict(details)
        if "stale" not in merged:
            merged["stale"] = bool(freshness.get("stale", False))
        if merged.get("age_seconds") is None:
            merged["age_seconds"] = freshness.get("age_seconds")
        if merged.get("last_updated") is None:
            merged["last_updated"] = freshness.get("last_updated")
        if merged.get("stale_threshold_seconds") is None:
            merged["stale_threshold_seconds"] = freshness.get("stale_threshold_seconds")
        enriched_source_diagnostics[key] = merged
        if merged.get("status") == "unavailable":
            unavailable_source_keys.append(key)
        if merged.get("stale") or (merged.get("age_seconds") or 0) > 120:
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


def build_source_attention_role_summary(
    state: Any,
    config: dict[str, Any] | None = None,
    *,
    limit: int = 6,
) -> str:
    """Return concise role -> entity guidance for unavailable or stale mapped sources."""
    source_attention = build_source_attention_details(state)
    source_diagnostics = source_attention["source_diagnostics"]
    configured = config or {}

    details_lines: list[str] = []
    for key in _ordered_source_attention_keys(source_attention)[:limit]:
        details = source_diagnostics.get(key, {})
        configured_label = format_source_binding_label(configured.get(key)) if configured.get(key) else None
        entity_label = str(details.get("entity_id") or configured_label or "not resolved")

        markers: list[str] = []
        if details.get("status") == "unavailable":
            markers.append("unavailable")
        if details.get("stale"):
            age_seconds = details.get("age_seconds")
            if age_seconds is not None:
                markers.append(f"stale {int(age_seconds)} s")
            else:
                markers.append("stale")
        issue_messages = [str(issue).strip() for issue in (details.get("issues") or []) if str(issue).strip()]
        if issue_messages:
            markers.append(issue_messages[0])
        if not issue_messages:
            validation_issues = list(source_attention.get("validation_details", {}).get("issues", []) or [])
            validation_role_keys = _issue_role_keys(validation_issues)
            if key in validation_role_keys:
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
                        markers.append(message)
                        break

        marker_text = "; ".join(markers) if markers else "needs attention"
        details_lines.append(f"{SOURCE_ROLE_LABELS.get(key, key)} -> {entity_label} ({marker_text})")

    return "; ".join(details_lines) if details_lines else "None"


def build_source_attention_summary(
    state: Any,
    config: dict[str, Any] | None = None,
    *,
    limit: int = 4,
) -> str:
    """Return a concise operator-facing summary of current mapped-source blockers."""
    source_attention = build_source_attention_details(state)
    source_diagnostics = source_attention["source_diagnostics"]
    configured = config or {}

    if not _ordered_source_attention_keys(source_attention):
        return "None"

    parts: list[str] = []
    for key in _ordered_source_attention_keys(source_attention)[:limit]:
        details = source_diagnostics.get(key, {})
        configured_label = format_source_binding_label(configured.get(key)) if configured.get(key) else None
        entity_label = str(details.get("entity_id") or configured_label or "not resolved")
        status_bits: list[str] = []
        if details.get("status") == "unavailable":
            status_bits.append("unavailable")
        if details.get("stale"):
            age_seconds = details.get("age_seconds")
            status_bits.append(f"stale {int(age_seconds)} s" if age_seconds is not None else "stale")
        if not status_bits:
            status_bits.append("needs attention")
        parts.append(f"{SOURCE_ROLE_LABELS.get(key, key)} ({entity_label}, {', '.join(status_bits)})")

    remaining = len(_ordered_source_attention_keys(source_attention)) - len(parts)
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
    for issue in validation_issues or []:
        code = str(issue.get("code") or "")
        if "_" not in code:
            continue
        key = code.rsplit("_", 1)[0]
        if key in SOURCE_ROLE_LABELS:
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

    if missing_roles != "None":
        return (
            f"Open {SOURCES_CONFIGURE_PATH}, finish these required source roles: {missing_roles}, then save and reload the integration."
        )

    attention_parts: list[str] = []
    if unavailable_roles != "None":
        attention_parts.append(f"unavailable roles: {unavailable_roles}")
    if stale_roles != "None":
        attention_parts.append(f"stale roles: {stale_roles}")
    if attention_parts:
        blocker_text = (
            f"these mapped-source blockers first: {affected_roles_text}"
            if affected_roles_text and affected_roles_text != "None"
            else f"these mapped-source blockers ({'; '.join(attention_parts)})"
        )
        return (
            f"Open {SOURCES_CONFIGURE_PATH}, repair {blocker_text}, then save and reload the integration."
        )

    if blocking_details and blocking_details != "None":
        blocker_text = (
            f"repair these highlighted mapped roles first: {affected_roles_text}, then clear the blocking source validation errors ({blocking_details})"
            if affected_roles_text and affected_roles_text != "None"
            else f"repair the blocking source validation errors ({blocking_details})"
        )
        return f"Open {SOURCES_CONFIGURE_PATH}, {blocker_text}, then save and reload the integration."

    return f"Open {SOURCES_CONFIGURE_PATH}, review the mapped sources, then save and reload the integration."


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
                f"Open {SOURCES_CONFIGURE_PATH} or {INTEGRATION_DEVICE_PATH} -> Show native diagnostics snapshot, "
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
            f"Use {INTEGRATION_DEVICE_PATH} -> Show native diagnostics snapshot, then return to {DEVICES_CONFIGURE_PATH} "
            "to unblock at least one usable device."
        )
        summary = "Managed devices exist, but none are currently eligible for control."
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
            f"Validate {PRIMARY_CONFIGURE_PATH} plus {INTEGRATION_DEVICE_PATH} support actions in a real "
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
            f"Add the first managed device in {DEVICES_CONFIGURE_PATH}, then use {DETAILED_MANAGEMENT_PATH} "
            "for per-device review once the fleet exists."
        )

    usable_count = int(getattr(state, "usable_device_count", 0) or 0) if state is not None else 0
    if usable_count <= 0:
        return (
            f"Use {DETAILED_MANAGEMENT_PATH} to inspect each managed device's status, guards, plans, and reset actions, "
            "then return to Managed devices to adjust the fleet if needed."
        )

    return (
        f"Use {DETAILED_MANAGEMENT_PATH} for per-device status, planned actions, guard state, and reset actions when the fleet needs deeper review."
    )


def build_native_support_snapshot(coordinator: Any) -> str:
    """Return the operator support snapshot for native HA surfaces."""
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
    source_health_lines = [
        (
            f"- {SOURCE_ROLE_LABELS.get(key, key)}: status={details.get('status') or 'unknown'}, "
            f"age_s={details.get('age_seconds') if details.get('age_seconds') is not None else 'n/a'}, "
            f"issues={len(details.get('issues') or [])}, "
            f"entity={details.get('entity_id') or 'n/a'}"
        )
        for key, details in source_diagnostics.items()
    ]
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
        device_lines.append(
            (
                f"- {item.get('key')}: enabled={item.get('enabled')}, "
                f"usable={runtime.get('usable', 'n/a')}, "
                f"status={runtime.get('status', 'n/a')}, "
                f"planned={runtime.get('planned_action', 'n/a')}, "
                f"guard={runtime.get('guard_status', 'n/a')}, "
                f"kind={item.get('kind')}, adapter={item.get('adapter')}, "
                f"priority={item.get('priority')}, entity={item.get('entity_id')}"
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
        "Zero Net Export support snapshot",
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
        "Primary setup path",
        f"- {PRIMARY_CONFIGURE_PATH}",
        f"- Health and support: {SUPPORT_CONFIGURE_PATH}",
        f"- Recommended command-center section: {command_center.get('recommended_section')}",
        f"- Recommended command-center path: {command_center.get('recommended_path')}",
        f"- Command-center next action: {command_center.get('next_action_summary')}",
        f"- Managed-device deep review: {command_center.get('detailed_management_summary')}",
        "",
        "Readiness",
        f"- phase: {operator_readiness.get('phase')}",
        f"- summary: {operator_readiness.get('summary')}",
        f"- next_step: {command_center.get('next_action_summary') or operator_readiness.get('next_step')}",
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
        "Managed devices",
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
    readiness_phase = str(readiness.get("phase") or "")

    missing_required_sources = [key for key in REQUIRED_SOURCE_KEYS if not merged.get(key)]
    source_attention = build_source_attention_details(state)
    unavailable_source_roles = [SOURCE_ROLE_LABELS.get(key, key) for key in source_attention["unavailable_source_keys"]]
    stale_source_roles = [SOURCE_ROLE_LABELS.get(key, key) for key in source_attention["stale_source_keys"]]
    source_attention_summary = build_source_attention_summary(state, merged, limit=4)
    source_attention_roles = build_source_attention_role_summary(state, merged, limit=4)
    blocking_validation_details = summarize_validation_issue_messages(state, severities={"error"}, limit=3)
    runtime_source_attention = bool(unavailable_source_roles or stale_source_roles or blocking_validation_details != "None")

    if missing_required_sources:
        source_status = "Missing required source roles: " + ", ".join(
            SOURCE_ROLE_LABELS.get(key, key) for key in missing_required_sources
        )
        recommended_section = "Sensors"
    elif runtime_source_attention:
        attention_prefix = "Mapped source blockers: " + source_attention_summary if source_attention_summary != "None" else "Mapped sources need attention."
        validation_suffix = (
            f" Blocking validation details: {blocking_validation_details}"
            if blocking_validation_details != "None"
            else ""
        )
        source_status = attention_prefix + validation_suffix
        recommended_section = "Sensors"
    elif state is None:
        source_status = "Source health will appear here after the integration loads."
        recommended_section = "Sensors"
    else:
        source_status = build_live_source_health_summary(state)
        recommended_section = "Managed devices" if not configured_devices else "Controls"

    if device_parse_issues:
        device_status = f"{len(configured_devices)} configured, with {len(device_parse_issues)} issue(s) to repair"
        device_next_step = f"Open {DEVICES_CONFIGURE_PATH} to repair the managed-device configuration before relying on control."
        recommended_section = "Managed devices"
    elif configured_devices:
        runtime_device_status = str(getattr(state, "device_status_summary", "") or "").strip() if state is not None else ""
        device_status = runtime_device_status or f"{len(configured_devices)} configured"
        device_next_step = (
            f"Open {DEVICES_CONFIGURE_PATH} to review the fleet, edit device settings, or stage enablement changes."
        )
    else:
        device_status = "No managed devices configured yet"
        device_next_step = f"Open {DEVICES_CONFIGURE_PATH} and add at least one controllable load from the managed-device flow."
        if not missing_required_sources and not runtime_source_attention:
            recommended_section = "Managed devices"

    if missing_required_sources:
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
    elif not configured_devices:
        next_action_summary = "Add at least one managed device next so Zero Net Export has a controllable load."
    elif readiness_phase == "runtime_readiness":
        next_action_summary = str(
            readiness.get("next_step")
            or f"Open {SUPPORT_CONFIGURE_PATH} and the native diagnostics surfaces to clear the current runtime blocker."
        )
        recommended_section = "Diagnostics"
    elif readiness_phase == "operator_ready":
        next_action_summary = str(
            readiness.get("next_step")
            or "Validate the native Configure path and device support actions in a real Home Assistant install."
        )
    else:
        next_action_summary = "Sources and devices are in place, so policy tuning or support review are the next useful steps."

    current_mode = MODE_LABELS.get(str(getattr(state, "mode", "") or ""), str(getattr(state, "mode", "") or "Unknown mode"))
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
    elif not configured_devices:
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
        "Sensors": source_status,
        "Managed devices": device_status,
        "Controls": policy_status,
        "Diagnostics": support_status,
    }

    path_summary_map = {
        "Sensors": SOURCES_CONFIGURE_PATH,
        "Managed devices": DEVICES_CONFIGURE_PATH,
        "Controls": POLICY_CONFIGURE_PATH,
        "Diagnostics": SUPPORT_CONFIGURE_PATH,
    }

    install_status = str(install_provenance.get("summary") or "Installed package provenance unavailable")
    install_consistency = build_install_consistency_summary(install_provenance)
    install_fingerprint_summary = build_install_fingerprint_summary(install_provenance)

    return {
        "source_status": source_status,
        "source_attention_summary": source_attention_summary,
        "source_attention_roles": source_attention_roles,
        "unavailable_sources": ", ".join(unavailable_source_roles) if unavailable_source_roles else "None",
        "stale_sources": ", ".join(stale_source_roles) if stale_source_roles else "None",
        "source_mapping_summary": build_source_mapping_summary(merged),
        "device_status": device_status,
        "device_next_step": device_next_step,
        "policy_status": policy_status,
        "policy_readiness": policy_readiness,
        "support_status": support_status,
        "install_status": install_status,
        "install_consistency": install_consistency,
        "install_fingerprint_summary": install_fingerprint_summary,
        "status_summary": status_summary_map.get(recommended_section, support_status),
        "recommended_section": recommended_section,
        "recommended_path": path_summary_map.get(recommended_section, PRIMARY_CONFIGURE_PATH),
        "next_action_summary": next_action_summary,
        "detailed_management_path": DETAILED_MANAGEMENT_PATH,
        "detailed_management_summary": detailed_management_summary,
        "sources_path": SOURCES_CONFIGURE_PATH,
        "devices_path": DEVICES_CONFIGURE_PATH,
        "policy_path": POLICY_CONFIGURE_PATH,
        "mode_path": MODE_CONTROL_PATH,
        "support_path": SUPPORT_CONFIGURE_PATH,
    }


def build_native_support_center(coordinator: Any) -> str:
    """Return a single operator-facing support bundle for native HA surfaces."""
    _, _, _, operator_readiness = _build_support_sections(coordinator)
    command_center = build_native_command_center_summary(coordinator)
    snapshot = build_native_support_snapshot(coordinator)
    checklist_lines = [
        f"- [{'x' if item.get('complete') else ' '}] {item.get('label')}: {item.get('detail')}"
        for item in operator_readiness.get('checklist', [])
    ]
    return "\n".join(
        [
            "Zero Net Export native support center",
            "",
            f"Primary setup path: {PRIMARY_CONFIGURE_PATH}",
            f"Health and support path: {SUPPORT_CONFIGURE_PATH}",
            f"Recommended command-center section: {command_center.get('recommended_section')}",
            f"Recommended command-center path: {command_center.get('recommended_path')}",
            f"Managed-device deep review: {command_center.get('detailed_management_summary')}",
            f"Readiness phase: {operator_readiness.get('phase')}",
            f"Summary: {operator_readiness.get('summary')}",
            f"Next step: {command_center.get('next_action_summary') or operator_readiness.get('next_step')}",
            "",
            "Checklist",
            *(checklist_lines or ["- No checklist available yet."]),
            "",
            "Support snapshot",
            snapshot,
        ]
    )
