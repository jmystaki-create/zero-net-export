"""Native Home Assistant operator support helpers for Zero Net Export."""
from __future__ import annotations

from datetime import datetime
import json
from typing import Any

from homeassistant.util import dt as dt_util

from .const import (
    CONF_BATTERY_CHARGE_POWER_ENTITY,
    CONF_BATTERY_DISCHARGE_POWER_ENTITY,
    CONF_BATTERY_SOC_ENTITY,
    CONF_DEVICE_INVENTORY_JSON,
    CONF_GRID_EXPORT_ENERGY_ENTITY,
    CONF_GRID_EXPORT_POWER_ENTITY,
    CONF_GRID_IMPORT_ENERGY_ENTITY,
    CONF_GRID_IMPORT_POWER_ENTITY,
    CONF_HOME_LOAD_POWER_ENTITY,
    CONF_SOLAR_ENERGY_ENTITY,
    CONF_SOLAR_POWER_ENTITY,
    INTEGRATION_VERSION,
    REQUIRED_SOURCE_KEYS,
    SOURCE_ROLE_LABELS,
)
from .device_model import parse_device_configs
from .release_info import build_release_info
from .validation import SourceSpec, format_source_binding_label

PRIMARY_CONFIGURE_PATH = "Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure"


def _validation_details(state: Any) -> dict[str, Any]:
    if state is None:
        return {}
    return state.validation_details or {}


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
    validation_details = _validation_details(state)
    validation_issues = validation_details.get("issues", [])
    blocking_validation_issues = [
        issue for issue in validation_issues if str(issue.get("severity", "")).lower() == "error"
    ]
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

    if missing_required_sources:
        phase = "source_setup"
        next_step = "Finish required source mapping in Configure, then save and reload the integration."
        summary = "Native setup is blocked on missing required source mappings."
    elif blocking_validation_issues or state_stale_data:
        phase = "source_remediation"
        if state_stale_data and stale_summary:
            next_step = f"Open Configure or the diagnostics snapshot and fix the stale mapped sources. {stale_summary}."
        else:
            next_step = "Use native diagnostics and calibration hints to fix source validation or stale-data issues."
        summary = "Native setup is waiting on healthy validated source data."
    elif device_parse_issues:
        phase = "device_remediation"
        next_step = "Fix the managed-device configuration in Configure so the configured fleet parses cleanly."
        summary = "Native setup is blocked on managed-device configuration issues."
    elif not configured_devices:
        phase = "device_onboarding"
        next_step = "Add the first controllable device from Configure."
        summary = "Sources are ready; the next milestone is adding controllable devices."
    elif not state_usable_device_count:
        phase = "runtime_readiness"
        next_step = "Review per-device diagnostics to unblock at least one usable device."
        summary = "Configured devices exist, but none are currently eligible for control."
    elif state_safe_mode:
        phase = "runtime_readiness"
        next_step = "Clear the current safe-mode condition before treating the integration as production-ready."
        summary = "The native operator flow is mostly built, but runtime is still held in safe mode."
    else:
        phase = "operator_ready"
        next_step = "Validate the native Configure workflow in a real Home Assistant install and refine any remaining friction there."
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


def build_native_support_snapshot(coordinator: Any) -> str:
    """Return the operator support snapshot for native HA surfaces."""
    state, configured_devices, device_parse_issues, operator_readiness = _build_support_sections(coordinator)
    release_info = build_release_info(INTEGRATION_VERSION, include_changelog=False)
    validation_details = _validation_details(state)
    release_update = validation_details.get("release_update", {})
    source_diagnostics = validation_details.get("source_diagnostics", {})
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
        f"Update visibility: {release_update.get('summary', 'n/a')}",
        "",
        "Primary setup path",
        f"- {PRIMARY_CONFIGURE_PATH}",
        "",
        "Readiness",
        f"- phase: {operator_readiness.get('phase')}",
        f"- summary: {operator_readiness.get('summary')}",
        f"- next_step: {operator_readiness.get('next_step')}",
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
        "",
        "Configured devices",
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


def build_native_support_center(coordinator: Any) -> str:
    """Return a single operator-facing support bundle for native HA surfaces."""
    _, _, _, operator_readiness = _build_support_sections(coordinator)
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
            f"Readiness phase: {operator_readiness.get('phase')}",
            f"Summary: {operator_readiness.get('summary')}",
            f"Next step: {operator_readiness.get('next_step')}",
            "",
            "Checklist",
            *(checklist_lines or ["- No checklist available yet."]),
            "",
            "Support snapshot",
            snapshot,
        ]
    )
