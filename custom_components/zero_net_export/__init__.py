"""Zero Net Export integration."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import logging
from pathlib import Path
import re
from typing import Any

import voluptuous as vol

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_BATTERY_RESERVE_SOC,
    CONF_DEADBAND_W,
    CONF_DEVICE_INVENTORY_JSON,
    CONF_GRID_EXPORT_ENERGY_ENTITY,
    CONF_GRID_EXPORT_POWER_ENTITY,
    CONF_GRID_IMPORT_ENERGY_ENTITY,
    CONF_GRID_IMPORT_POWER_ENTITY,
    CONF_HOME_LOAD_POWER_ENTITY,
    CONF_REFRESH_SECONDS,
    CONF_SOLAR_ENERGY_ENTITY,
    CONF_SOLAR_POWER_ENTITY,
    CONF_TARGET_EXPORT_W,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_DEADBAND_W,
    DEFAULT_DEVICE_INVENTORY_JSON,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_TARGET_EXPORT_W,
    DOMAIN,
    APP_MODULE_URL,
    APP_PANEL_COMPONENT_NAME,
    APP_PANEL_ICON,
    APP_PANEL_TITLE,
    APP_PANEL_URL_PATH,
    APP_STATIC_URL_PATH,
    INTEGRATION_VERSION,
    PLATFORMS,
    REQUIRED_SOURCE_KEYS,
    SOURCE_ROLE_LABELS,
)
from .app_api import build_app_panel_config
from .coordinator import ZeroNetExportCoordinator
from .device_model import parse_device_configs
from .entity import sync_fleet_workspace_entity_registry, sync_primary_controller_device_registry
from .native_support import (
    DEVICES_CONFIGURE_PATH,
    DIAGNOSTICS_DEVICE_ACTIONS_PATH,
    POLICY_CONFIGURE_PATH,
    PRIMARY_CONFIGURE_PATH,
    SOURCES_CONFIGURE_PATH,
    SUPPORT_CONFIGURE_PATH,
    build_native_operator_readiness,
    build_source_attention_role_summary,
    build_source_selector_fallback_hint,
)
from .release_info import async_prime_install_provenance
from .repairs import async_clear_repairs_issues, async_sync_repairs_issues


STALE_GUIDED_FLOW_BUTTON_SUFFIXES = {
    "open_sensors_guided_flow",
    "open_controls_guided_flow",
    "open_managed_devices_guided_flow",
    "open_diagnostics_guided_flow",
}
STALE_MANAGED_LOAD_BUTTON_SUFFIXES = (
    "_edit_configuration",
    "_remove_from_zne",
)
DATA_APP_PANEL_REGISTERED = "app_panel_registered"
DATA_APP_STATIC_REGISTERED = "app_static_registered"
PROMOTION_FIXED_CANDIDATE_DOMAINS = ("switch", "climate", "input_boolean", "light")
PROMOTION_DEVICE_KIND_FIXED = "fixed"
PROMOTION_DEVICE_KIND_VARIABLE = "variable"
PROMOTION_ADAPTER_FIXED_TOGGLE = "fixed_toggle"
PROMOTION_ADAPTER_VARIABLE_NUMBER = "variable_number"

_LOGGER = logging.getLogger(__name__)


def _setup_notification_id(entry: ConfigEntry) -> str:
    return f"{DOMAIN}_{entry.entry_id}_native_setup"


def _async_remove_stale_guided_flow_button_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove registry rows for retired device-page launcher buttons."""
    entity_registry = er.async_get(hass)
    unique_id_prefix = f"{entry.entry_id}_"
    for entity_id, entity_entry in list(entity_registry.entities.items()):
        if getattr(entity_entry, "platform", None) != DOMAIN:
            continue
        unique_id = str(getattr(entity_entry, "unique_id", "") or "")
        if not unique_id.startswith(unique_id_prefix):
            continue
        suffix = unique_id.removeprefix(unique_id_prefix)
        if suffix in STALE_GUIDED_FLOW_BUTTON_SUFFIXES or (
            suffix.startswith("device_") and suffix.endswith(STALE_MANAGED_LOAD_BUTTON_SUFFIXES)
        ):
            entity_registry.async_remove(entity_id)


def _missing_required_source_mappings(entry: ConfigEntry) -> list[str]:
    merged = dict(entry.data)
    merged.update(entry.options)
    return [key for key in REQUIRED_SOURCE_KEYS if not merged.get(key)]


def _normalize_source_mapping_case_drift(text: str) -> str:
    """Catch title-case source-mapping fallback text before persistent notices render."""
    text = re.sub(
        r"\bOpen Configure and finish (?:required )?(?:source[- ]mappings?|source[- ]roles?)\b",
        f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bOpen Configure to finish (?:required )?(?:source[- ]mappings?|source[- ]roles?)\b",
        f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bOpen(?: the)? Source[- ]Mappings? Step\b",
        f"Open {SOURCES_CONFIGURE_PATH}",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bMissing Required Source Mappings\b",
        lambda match: "Missing required source roles" if match.group(0)[0].isupper() else "missing required source roles",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bRequired Source Mapping\b",
        lambda match: "Required source roles" if match.group(0)[0].isupper() else "required source roles",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bFinish Source Mapping\b",
        lambda match: "Finish source roles" if match.group(0)[0].isupper() else "finish source roles",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bSource[- ]Mappings? Step\b",
        "Sensors source roles",
        text,
        flags=re.IGNORECASE,
    )
    return re.sub(
        r"\bSource[- ]Mappings?\b",
        lambda match: "Source roles" if match.group(0)[0].isupper() else "source roles",
        text,
        flags=re.IGNORECASE,
    )


def _normalize_native_setup_notice_text(value: Any) -> str:
    """Keep setup notifications on the operator-facing source-role wording."""
    text = str(value or "")
    replacements = {
        "Open Configure and finish required source roles": f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        "Open Configure and finish source mapping": f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        "Open Configure and finish source roles": f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        "Open Configure and finish source role": f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        "Open Configure to finish required source roles": f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        "Open Configure to finish source mapping": f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        "Open Configure to finish source roles": f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        "Open Configure to finish source role": f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        "Open the Source-mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the source-mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open Source-mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open source-mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the Source-mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the source-mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open Source-mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open source-mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the Source mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the source mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open Source mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open source mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the Source mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the source mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open Source mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open source mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Missing required source mappings": "Missing required source roles",
        "missing required source mappings": "missing required source roles",
        "Missing source mappings": "Missing source roles",
        "missing source mappings": "missing source roles",
        "Finish source mapping": "Finish source roles",
        "finish source mapping": "finish source roles",
        "Required source mapping": "Required source roles",
        "required source mapping": "required source roles",
        "Open Sensors and": f"Open {SOURCES_CONFIGURE_PATH} and",
        "Open Sensors to": f"Open {SOURCES_CONFIGURE_PATH} to",
        "Open Sources and": f"Open {SOURCES_CONFIGURE_PATH} and",
        "Open Sources to": f"Open {SOURCES_CONFIGURE_PATH} to",
        "Open Controls and": f"Open {POLICY_CONFIGURE_PATH} and",
        "Open Controls to": f"Open {POLICY_CONFIGURE_PATH} to",
        "Open Managed Devices and": f"Open {DEVICES_CONFIGURE_PATH} and",
        "Open Managed Devices to": f"Open {DEVICES_CONFIGURE_PATH} to",
        "Open Diagnostics and": f"Open {SUPPORT_CONFIGURE_PATH} and",
        "Open Diagnostics to": f"Open {SUPPORT_CONFIGURE_PATH} to",
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
        "Mapped role blockers": "Source blockers",
        "Mapped role blocker": "Source blocker",
        "mapped-role blockers": "source blockers",
        "mapped-role blocker": "source blocker",
        "mapped role blockers": "source blockers",
        "mapped role blocker": "source blocker",
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
        "Source-mapping step": "Sensors source roles",
        "source-mapping step": "Sensors source roles",
        "Source-mappings step": "Sensors source roles",
        "source-mappings step": "Sensors source roles",
        "Source-mappings": "Source roles",
        "source-mappings": "source roles",
        "Source-mapping": "Source roles",
        "source-mapping": "source roles",
        "Source mapping step": "Sensors source roles",
        "source mapping step": "Sensors source roles",
        "Source mappings": "Source roles",
        "source mappings": "source roles",
        "Source mapping": "Source roles",
        "source mapping": "source roles",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = _normalize_source_mapping_case_drift(text)
    arrow_paths = {
        "Sensors": SOURCES_CONFIGURE_PATH,
        "Controls": POLICY_CONFIGURE_PATH,
        "Managed Devices": DEVICES_CONFIGURE_PATH,
        "Diagnostics": SUPPORT_CONFIGURE_PATH,
    }
    for section_label, section_path in arrow_paths.items():
        escaped_section = re.escape(section_label)
        text = re.sub(
            rf"{re.escape(PRIMARY_CONFIGURE_PATH)}\s*(?:->|→|>)\s*{escaped_section}(?!; device-page diagnostics)",
            section_path,
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            rf"(?<!Integrations -> )Zero Net Export\s*->\s*Configure\s*(?:->|→|>)\s*{escaped_section}(?!; device-page diagnostics)",
            section_path,
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            rf"(?<!Zero Net Export -> )Configure\s*(?:->|→|>)\s*{escaped_section}(?!; device-page diagnostics)",
            section_path,
            text,
            flags=re.IGNORECASE,
        )
    section_paths = {
        "Sensors": SOURCES_CONFIGURE_PATH,
        "Sources": SOURCES_CONFIGURE_PATH,
        "Controls": POLICY_CONFIGURE_PATH,
        "Managed Devices": DEVICES_CONFIGURE_PATH,
        "Diagnostics": SUPPORT_CONFIGURE_PATH,
    }
    for section_label, section_path in section_paths.items():
        text = re.sub(
            rf"\bOpen {re.escape(section_label)}(?!(?:\s+path)\b)(?=(?:\s|[.,;:]|$))",
            f"Open {section_path}",
            text,
            flags=re.IGNORECASE,
        )
    return text


async def _async_update_native_setup_notice(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: ZeroNetExportCoordinator | None = None,
) -> None:
    missing_sources = _missing_required_source_mappings(entry)
    raw_inventory = entry.options.get(
        CONF_DEVICE_INVENTORY_JSON,
        entry.data.get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
    )
    devices, device_issues = parse_device_configs(raw_inventory)
    state = coordinator.data if coordinator is not None else None
    merged = dict(entry.data)
    merged.update(entry.options)
    readiness = build_native_operator_readiness(coordinator) if coordinator is not None else {}
    source_attention_roles = build_source_attention_role_summary(state, merged, limit=4)

    if not missing_sources and devices and not device_issues and source_attention_roles == "None":
        persistent_notification.async_dismiss(hass, _setup_notification_id(entry))
        return

    readable_roles = [SOURCE_ROLE_LABELS.get(key, key) for key in missing_sources]
    fallback_hint = build_source_selector_fallback_hint(role_keys=missing_sources) or "Not needed right now."
    readiness_summary = _normalize_native_setup_notice_text(
        readiness.get("summary") or "Setup incomplete."
    )
    missing_lines = [
        f"• Source roles: {', '.join(readable_roles) if readable_roles else 'None'}",
        f"• Managed devices: {len(devices)}",
    ]
    if device_issues:
        missing_lines.append(f"• Device issues: {'; '.join(device_issues[:3])}")
    elif not devices:
        missing_lines.append("• Device issues: No controllable devices added yet.")
    if source_attention_roles != "None":
        missing_lines.append(f"• Blockers: {source_attention_roles}")

    next_step = _normalize_native_setup_notice_text(
        readiness.get("next_step") or f"Open {PRIMARY_CONFIGURE_PATH} and continue setup."
    )
    if fallback_hint != "Not needed right now.":
        next_step = next_step.replace(f" {fallback_hint}", "").replace(fallback_hint, "").strip()

    message = (
        "Setup incomplete — control is paused until setup is finished.\n\n"
        "Do this first\n"
        + f"• {next_step}"
        + "\n\nMissing\n"
        + "\n".join(missing_lines)
        + "\n\nOpen\n"
        + f"• Sensors: {SOURCES_CONFIGURE_PATH}\n"
        + f"• Managed Devices: {DEVICES_CONFIGURE_PATH}\n"
        + f"• Controls: {POLICY_CONFIGURE_PATH}\n"
        + f"• Diagnostics: {SUPPORT_CONFIGURE_PATH}"
        + "\n\nFallback only if Home Assistant rejects a valid selector choice\n"
        + f"• {fallback_hint}"
    )
    persistent_notification.async_create(
        hass,
        message,
        title=f"{entry.title}: setup incomplete",
        notification_id=_setup_notification_id(entry),
    )


def _managed_device_identifier_part(value: object) -> str:
    """Return the same safe managed-device identifier fragment used by entity.py."""
    original = str(value or "unknown").strip() or "unknown"
    safe = re.sub(r"[^a-zA-Z0-9_]+", "_", original).strip("_").lower() or "unknown"
    if original == safe:
        return safe
    digest = hashlib.sha1(original.encode("utf-8")).hexdigest()[:8]
    return f"{safe}_{digest}"


def _coerce_number(value: Any, fallback: int | float) -> int | float:
    if value in (None, ""):
        return fallback
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    if isinstance(fallback, int) and not isinstance(fallback, bool):
        return int(parsed)
    return parsed


UPDATE_MANAGED_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): str,
        vol.Required("device_key"): str,
        vol.Optional("name"): str,
        vol.Optional("entity_id"): str,
        vol.Optional("enabled"): bool,
        vol.Optional("priority"): int,
        vol.Optional("nominal_power_w"): float,
        vol.Optional("min_power_w"): float,
        vol.Optional("max_power_w"): float,
        vol.Optional("step_w"): float,
        vol.Optional("min_on_seconds"): int,
        vol.Optional("min_off_seconds"): int,
        vol.Optional("cooldown_seconds"): int,
        vol.Optional("max_active_seconds"): int,
    }
)


REMOVE_MANAGED_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): str,
        vol.Required("device_key"): str,
        vol.Required("confirm"): bool,
    }
)

PROMOTE_MANAGED_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): str,
        vol.Required("candidate_entity_id"): str,
        vol.Optional("device_key"): str,
        vol.Optional("name"): str,
        vol.Optional("kind"): str,
        vol.Optional("template_key"): str,
        vol.Optional("enabled"): bool,
        vol.Optional("priority"): int,
        vol.Optional("nominal_power_w"): float,
        vol.Optional("min_power_w"): float,
        vol.Optional("max_power_w"): float,
        vol.Optional("step_w"): float,
        vol.Optional("min_on_seconds"): int,
        vol.Optional("min_off_seconds"): int,
        vol.Optional("cooldown_seconds"): int,
        vol.Optional("max_active_seconds"): int,
        vol.Required("confirm"): bool,
    }
)

SOURCE_ROLE_KEYS = tuple(SOURCE_ROLE_LABELS.keys())

UPDATE_SOURCE_ROLES_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): str,
        **{vol.Optional(key): str for key in SOURCE_ROLE_KEYS},
    }
)

ENTRY_SCOPED_SERVICE_SCHEMA = vol.Schema({vol.Optional("entry_id"): str})


def _device_config_to_payload(device) -> dict[str, Any]:
    payload = asdict(device)
    if payload.get("max_active_seconds") is None:
        payload["max_active_seconds"] = 0
    return payload


def _entry_from_service_call(hass: HomeAssistant, call: Any) -> ConfigEntry:
    """Resolve a service call to exactly one Zero Net Export config entry."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise ValueError("Zero Net Export has no configured entries")
    requested_entry_id = str(call.data.get("entry_id") or "")
    if not requested_entry_id and len(entries) > 1:
        raise ValueError("Set entry_id when more than one Zero Net Export plan is configured")
    entry = next((candidate for candidate in entries if candidate.entry_id == requested_entry_id), None) if requested_entry_id else entries[0]
    if entry is None:
        raise ValueError(f"Zero Net Export entry '{requested_entry_id}' was not found")
    return entry


def _coordinator_from_service_call(hass: HomeAssistant, call: Any) -> ZeroNetExportCoordinator:
    """Resolve a service call to the selected entry coordinator."""
    entry = _entry_from_service_call(hass, call)
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is None:
        raise ValueError(f"Zero Net Export entry '{entry.entry_id}' is not loaded")
    return coordinator


def _managed_device_entry_and_payloads(hass: HomeAssistant, call: Any) -> tuple[ConfigEntry, str, list[dict[str, Any]]]:
    """Return the selected ZNE entry, requested managed-device key, and inventory payloads."""
    entry = _entry_from_service_call(hass, call)
    device_key = str(call.data["device_key"])
    raw_inventory = entry.options.get(
        CONF_DEVICE_INVENTORY_JSON,
        entry.data.get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
    )
    devices, issues = parse_device_configs(raw_inventory)
    if issues:
        raise ValueError("Managed-device inventory is invalid: " + "; ".join(issues[:3]))
    return entry, device_key, [_device_config_to_payload(device) for device in devices]


def _candidate_kind_from_entity_id(entity_id: str) -> str:
    domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
    return PROMOTION_DEVICE_KIND_FIXED if domain in PROMOTION_FIXED_CANDIDATE_DOMAINS else PROMOTION_DEVICE_KIND_VARIABLE


def _candidate_template_defaults(kind: str, template_key: str | None) -> dict[str, Any]:
    from .device_model import get_device_template, get_device_templates

    template = get_device_template(kind, template_key)
    if template is None:
        templates = get_device_templates(kind)
        template = templates[0] if templates else None
    return dict(template.defaults) if template is not None else {}


def _promoted_candidate_defaults(candidate: dict[str, Any], fit: dict[str, Any], template_defaults: dict[str, Any]) -> dict[str, Any]:
    entity_id = str(candidate.get("entity_id") or "").strip()
    kind = str(candidate.get("kind") or _candidate_kind_from_entity_id(entity_id))
    domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
    defaults: dict[str, Any] = {
        "name": str(candidate.get("name") or entity_id).strip(),
        "entity_id": entity_id,
        "kind": kind,
        "adapter": PROMOTION_ADAPTER_FIXED_TOGGLE if kind == PROMOTION_DEVICE_KIND_FIXED else PROMOTION_ADAPTER_VARIABLE_NUMBER,
        "nominal_power_w": 2400 if kind == PROMOTION_DEVICE_KIND_FIXED else 3600,
        "priority": 100,
        "enabled": True,
        "min_on_seconds": 900 if kind == PROMOTION_DEVICE_KIND_FIXED else 300,
        "min_off_seconds": 900 if kind == PROMOTION_DEVICE_KIND_FIXED else 60,
        "cooldown_seconds": 60 if kind == PROMOTION_DEVICE_KIND_FIXED else 30,
        "max_active_seconds": 14400 if kind == PROMOTION_DEVICE_KIND_FIXED else 28800,
        "min_power_w": 1400,
        "max_power_w": 7200,
        "step_w": 100,
    }
    defaults.update(template_defaults)
    confidence = str(fit.get("confidence") or "medium")
    if kind == PROMOTION_DEVICE_KIND_FIXED:
        if confidence == "high" and domain == "switch":
            defaults["priority"] = max(int(defaults["priority"]), 120)
            defaults["min_on_seconds"] = max(int(defaults["min_on_seconds"]), 900)
            defaults["min_off_seconds"] = max(int(defaults["min_off_seconds"]), 900)
        elif confidence == "low":
            defaults["priority"] = min(int(defaults["priority"]), 60)
        if domain == "light":
            defaults["priority"] = min(int(defaults["priority"]), 80)
        if domain == "input_boolean":
            defaults["enabled"] = False
    else:
        if confidence == "high":
            defaults["priority"] = 50
            defaults["step_w"] = 100
            defaults["min_on_seconds"] = max(int(defaults["min_on_seconds"]), 300)
        elif confidence == "low":
            defaults["priority"] = 70
        if domain == "input_number":
            defaults["enabled"] = False
    return defaults


def _promoted_candidate_payload(candidate: dict[str, Any], fit: dict[str, Any], call_data: dict[str, Any]) -> dict[str, Any]:
    entity_id = str(candidate.get("entity_id") or "").strip()
    kind = str(call_data.get("kind") or candidate.get("kind") or _candidate_kind_from_entity_id(entity_id))
    if kind not in {PROMOTION_DEVICE_KIND_FIXED, PROMOTION_DEVICE_KIND_VARIABLE}:
        raise ValueError("Promoted managed-device kind must be fixed or variable")
    defaults = _promoted_candidate_defaults(
        {**candidate, "kind": kind},
        fit,
        _candidate_template_defaults(kind, call_data.get("template_key")),
    )
    name = str(call_data.get("name") or defaults["name"]).strip()
    payload: dict[str, Any] = {
        "name": name,
        "kind": kind,
        "entity_id": entity_id,
        "adapter": PROMOTION_ADAPTER_FIXED_TOGGLE if kind == PROMOTION_DEVICE_KIND_FIXED else PROMOTION_ADAPTER_VARIABLE_NUMBER,
        "nominal_power_w": float(_coerce_number(call_data.get("nominal_power_w"), defaults["nominal_power_w"])),
        "priority": int(_coerce_number(call_data.get("priority"), defaults["priority"])),
        "enabled": bool(call_data.get("enabled", defaults["enabled"])),
        "min_on_seconds": int(_coerce_number(call_data.get("min_on_seconds"), defaults["min_on_seconds"])),
        "min_off_seconds": int(_coerce_number(call_data.get("min_off_seconds"), defaults["min_off_seconds"])),
        "cooldown_seconds": int(_coerce_number(call_data.get("cooldown_seconds"), defaults["cooldown_seconds"])),
        "max_active_seconds": int(_coerce_number(call_data.get("max_active_seconds"), defaults["max_active_seconds"])) or None,
    }
    device_key = str(call_data.get("device_key") or "").strip()
    if device_key:
        payload["key"] = device_key
    if kind == PROMOTION_DEVICE_KIND_FIXED:
        payload["min_power_w"] = payload["nominal_power_w"]
        payload["max_power_w"] = payload["nominal_power_w"]
        payload["step_w"] = payload["nominal_power_w"]
    else:
        payload["min_power_w"] = float(_coerce_number(call_data.get("min_power_w"), defaults["min_power_w"]))
        payload["max_power_w"] = float(_coerce_number(call_data.get("max_power_w"), defaults["max_power_w"]))
        payload["step_w"] = float(_coerce_number(call_data.get("step_w"), defaults["step_w"]))
    return payload


async def _async_promote_managed_device_from_candidate(hass: HomeAssistant, call: Any) -> None:
    """Promote a surfaced unmanaged candidate into one ZNE managed-device record."""
    from .candidate_utils import assess_candidate, discover_candidate_devices

    if call.data.get("confirm") is not True:
        raise ValueError("Set confirm=true to promote an unmanaged candidate")
    entry = _entry_from_service_call(hass, call)
    raw_inventory = entry.options.get(
        CONF_DEVICE_INVENTORY_JSON,
        entry.data.get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
    )
    devices, issues = parse_device_configs(raw_inventory)
    if issues:
        raise ValueError("Managed-device inventory is invalid: " + "; ".join(issues[:3]))
    payloads = [_device_config_to_payload(device) for device in devices]
    managed_entity_ids = {str(payload.get("entity_id")) for payload in payloads if payload.get("entity_id")}
    candidate_entity_id = str(call.data["candidate_entity_id"]).strip()
    if candidate_entity_id in managed_entity_ids:
        raise ValueError(f"Candidate '{candidate_entity_id}' is already managed")
    candidates = discover_candidate_devices(hass.states.async_all(), managed_entity_ids)
    candidate = next((item for item in candidates if item.get("entity_id") == candidate_entity_id), None)
    if candidate is None:
        raise ValueError(f"Candidate '{candidate_entity_id}' is not currently available for promotion")
    fit = assess_candidate(candidate)
    payload = _promoted_candidate_payload(candidate, fit, dict(call.data))
    candidate_payloads = [*payloads, payload]
    _validated_devices, validation_issues = parse_device_configs(json.dumps(candidate_payloads))
    if validation_issues:
        raise ValueError("Promoted managed-device settings are invalid: " + "; ".join(validation_issues[:3]))
    promoted_key = _device_config_to_payload(_validated_devices[-1]).get("key")
    duplicate_keys = [item.get("key") for item in candidate_payloads]
    if len([key for key in duplicate_keys if key == promoted_key]) > 1:
        raise ValueError(f"Managed device key '{promoted_key}' is already managed")

    merged_options = dict(entry.options)
    merged_options[CONF_DEVICE_INVENTORY_JSON] = json.dumps(candidate_payloads, indent=2, sort_keys=True)
    hass.config_entries.async_update_entry(entry, options=merged_options)
    await hass.config_entries.async_reload(entry.entry_id)
    persistent_notification.async_create(
        hass,
        (
            f"Promoted {payload.get('name') or candidate_entity_id} into the Zero Net Export managed fleet. "
            "This created a ZNE managed-load record and child device; the original Home Assistant device and entity were not modified."
        ),
        title=f"{entry.title}: unmanaged candidate promoted",
        notification_id=f"{DOMAIN}_{entry.entry_id}_managed_device_promoted",
    )


async def _async_update_managed_device_from_panel(hass: HomeAssistant, call: Any) -> None:
    """Update a managed device from a native Home Assistant action/service."""
    entry, device_key, payloads = _managed_device_entry_and_payloads(hass, call)
    target = next((payload for payload in payloads if payload.get("key") == device_key), None)
    if target is None:
        raise ValueError(f"Managed device '{device_key}' was not found")

    editable_fields = {
        "name",
        "entity_id",
        "enabled",
        "priority",
        "nominal_power_w",
        "min_power_w",
        "max_power_w",
        "step_w",
        "min_on_seconds",
        "min_off_seconds",
        "cooldown_seconds",
        "max_active_seconds",
    }
    for field in editable_fields:
        if field in call.data:
            target[field] = call.data[field]
    if target.get("max_active_seconds") == 0:
        target["max_active_seconds"] = None

    _validated_devices, validation_issues = parse_device_configs(json.dumps(payloads))
    if validation_issues:
        raise ValueError("Managed-device settings are invalid: " + "; ".join(validation_issues[:3]))

    merged_options = dict(entry.options)
    merged_options[CONF_DEVICE_INVENTORY_JSON] = json.dumps(payloads, indent=2, sort_keys=True)
    hass.config_entries.async_update_entry(entry, options=merged_options)
    await hass.config_entries.async_reload(entry.entry_id)
    persistent_notification.async_create(
        hass,
        f"Updated managed-device settings for {target.get('name') or device_key}. Original Home Assistant devices and entities were not modified.",
        title=f"{entry.title}: managed device settings saved",
        notification_id=f"{DOMAIN}_{entry.entry_id}_managed_device_panel_update",
    )


async def _async_remove_managed_device_payload(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device_key: str,
    payloads: list[dict[str, Any]],
) -> bool:
    """Remove one managed device from one ZNE entry only."""
    removed = next((payload for payload in payloads if payload.get("key") == device_key), None)
    if removed is None:
        return False
    remaining = [payload for payload in payloads if payload.get("key") != device_key]
    _validated_devices, validation_issues = parse_device_configs(json.dumps(remaining))
    if validation_issues:
        raise ValueError("Managed-device settings are invalid after removal: " + "; ".join(validation_issues[:3]))

    merged_options = dict(entry.options)
    merged_options[CONF_DEVICE_INVENTORY_JSON] = json.dumps(remaining, indent=2, sort_keys=True)
    hass.config_entries.async_update_entry(entry, options=merged_options)
    await hass.config_entries.async_reload(entry.entry_id)
    persistent_notification.async_create(
        hass,
        (
            f"Removed {removed.get('name') or device_key} from Zero Net Export management. "
            "This only removed the ZNE managed-load record and its ZNE child-device rows; the original Home Assistant device/entity was left untouched."
        ),
        title=f"{entry.title}: managed device removed",
        notification_id=f"{DOMAIN}_{entry.entry_id}_managed_device_removed",
    )
    return True


async def _async_remove_managed_device(hass: HomeAssistant, call: Any) -> None:
    """Remove one managed device from ZNE configuration only."""
    if call.data.get("confirm") is not True:
        raise ValueError("Set confirm=true to remove a managed device from Zero Net Export")
    entry, device_key, payloads = _managed_device_entry_and_payloads(hass, call)
    if not await _async_remove_managed_device_payload(hass, entry, device_key, payloads):
        raise ValueError(f"Managed device '{device_key}' was not found")


async def _async_update_source_roles_from_app(hass: HomeAssistant, call: Any) -> None:
    """Update source-role bindings for one ZNE config entry from the app."""
    from .native_support import _source_specs_from_config
    from .validation import validate_configured_entities

    entry = _entry_from_service_call(hass, call)
    merged_data = dict(entry.data)
    merged_options = dict(entry.options)

    changed_roles: list[str] = []
    for key in SOURCE_ROLE_KEYS:
        if key not in call.data:
            continue
        value = str(call.data.get(key) or "").strip()
        merged_data[key] = value
        changed_roles.append(SOURCE_ROLE_LABELS.get(key, key))

    if not changed_roles:
        raise ValueError("No source roles were supplied")

    issues = validate_configured_entities(
        hass,
        merged_data,
        _source_specs_from_config(merged_data),
    )
    blocking_issues = [issue for issue in issues if issue.severity == "error"]
    if blocking_issues:
        summary = "; ".join(issue.message for issue in blocking_issues[:3])
        raise ValueError("Source-role settings are invalid: " + summary)

    hass.config_entries.async_update_entry(entry, data=merged_data, options=merged_options)
    await hass.config_entries.async_reload(entry.entry_id)
    persistent_notification.async_create(
        hass,
        "Saved Zero Net Export source roles: " + ", ".join(changed_roles) + ".",
        title=f"{entry.title}: source roles saved",
        notification_id=f"{DOMAIN}_{entry.entry_id}_source_roles_saved",
    )


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    device_entry: Any,
) -> bool:
    """Support Home Assistant's native integration-row Delete device action.

    HA exposes `supports_remove_device` from this backend hook and calls it
    only after its own native confirmation.  Remove the selected ZNE
    managed-load record from this config entry and leave the original/source
    Home Assistant device and entity untouched.
    """
    identifiers = getattr(device_entry, "identifiers", set()) or set()
    managed_identifier_prefix = f"{config_entry.entry_id}:managed-device:"
    raw_inventory = config_entry.options.get(
        CONF_DEVICE_INVENTORY_JSON,
        config_entry.data.get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
    )
    devices, issues = parse_device_configs(raw_inventory)
    if issues:
        raise ValueError("Managed-device inventory is invalid: " + "; ".join(issues[:3]))
    payloads = [_device_config_to_payload(device) for device in devices]
    device_key_by_identifier = {
        f"{config_entry.entry_id}:managed-device:{_managed_device_identifier_part(payload.get('key'))}": str(payload.get("key"))
        for payload in payloads
        if payload.get("key")
    }

    for domain, identifier in identifiers:
        if domain != DOMAIN:
            continue
        identifier = str(identifier)
        if not identifier.startswith(managed_identifier_prefix):
            continue
        device_key = device_key_by_identifier.get(identifier)
        if device_key is None:
            return False
        return await _async_remove_managed_device_payload(hass, config_entry, device_key, payloads)
    return False


def _register_services(hass: HomeAssistant) -> None:
    async def _handle_update_managed_device(call: Any) -> None:
        await _async_update_managed_device_from_panel(hass, call)

    async def _handle_remove_managed_device(call: Any) -> None:
        await _async_remove_managed_device(hass, call)

    async def _handle_promote_managed_device(call: Any) -> None:
        await _async_promote_managed_device_from_candidate(hass, call)

    async def _handle_update_source_roles(call: Any) -> None:
        await _async_update_source_roles_from_app(hass, call)

    async def _handle_pause_executor(call: Any) -> None:
        await _coordinator_from_service_call(hass, call).async_pause_executor()

    async def _handle_resume_executor(call: Any) -> None:
        await _coordinator_from_service_call(hass, call).async_resume_executor()

    async def _handle_export_diagnostics(call: Any) -> None:
        coordinator = _coordinator_from_service_call(hass, call)
        filename = await coordinator.async_export_diagnostics(hass)
        _LOGGER.info("Diagnostics exported to %s", filename)

    async def _handle_repair_issue(call: Any) -> None:
        entry = _entry_from_service_call(hass, call)
        async_clear_repairs_issues(hass, entry)
        _LOGGER.info("Repairs issues cleared for Zero Net Export entry %s", entry.entry_id)

    registrations = (
        ("update_managed_device", _handle_update_managed_device, UPDATE_MANAGED_DEVICE_SCHEMA),
        ("remove_managed_device", _handle_remove_managed_device, REMOVE_MANAGED_DEVICE_SCHEMA),
        ("promote_managed_device", _handle_promote_managed_device, PROMOTE_MANAGED_DEVICE_SCHEMA),
        ("update_source_roles", _handle_update_source_roles, UPDATE_SOURCE_ROLES_SCHEMA),
        ("pause_executor", _handle_pause_executor, ENTRY_SCOPED_SERVICE_SCHEMA),
        ("resume_executor", _handle_resume_executor, ENTRY_SCOPED_SERVICE_SCHEMA),
        ("export_diagnostics", _handle_export_diagnostics, ENTRY_SCOPED_SERVICE_SCHEMA),
        ("repair_issue", _handle_repair_issue, ENTRY_SCOPED_SERVICE_SCHEMA),
    )
    for service_name, handler, schema in registrations:
        if hass.services.has_service(DOMAIN, service_name):
            continue
        hass.services.async_register(DOMAIN, service_name, handler, schema=schema)


async def _async_register_app_panel(hass: HomeAssistant) -> None:
    """Register the Zero Net Export Home Assistant application panel."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if not domain_data.get(DATA_APP_STATIC_REGISTERED):
        from homeassistant.components.http import StaticPathConfig

        frontend_dir = Path(__file__).with_name("frontend")
        await hass.http.async_register_static_paths(
            [StaticPathConfig(APP_STATIC_URL_PATH, str(frontend_dir), True)]
        )
        domain_data[DATA_APP_STATIC_REGISTERED] = True

    if domain_data.get(DATA_APP_PANEL_REGISTERED):
        return

    from homeassistant.components import panel_custom

    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=APP_PANEL_URL_PATH,
        webcomponent_name=APP_PANEL_COMPONENT_NAME,
        sidebar_title=APP_PANEL_TITLE,
        sidebar_icon=APP_PANEL_ICON,
        module_url=APP_MODULE_URL,
        config=build_app_panel_config(hass),
        require_admin=False,
        config_panel_domain=DOMAIN,
    )
    domain_data[DATA_APP_PANEL_REGISTERED] = True


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration domain."""
    hass.data.setdefault(DOMAIN, {})
    _register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await _async_register_app_panel(hass)
    sync_primary_controller_device_registry(hass, entry)
    _async_remove_stale_guided_flow_button_entities(hass, entry)
    await _async_update_native_setup_notice(hass, entry)
    await async_prime_install_provenance(hass, force_refresh=True)

    coordinator = ZeroNetExportCoordinator(hass, entry)
    await coordinator.async_initialize()
    await coordinator.async_note_current_integration_version(INTEGRATION_VERSION)
    await coordinator.async_config_entry_first_refresh()

    await _async_update_native_setup_notice(hass, entry, coordinator)
    async_sync_repairs_issues(hass, entry, coordinator)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    sync_primary_controller_device_registry(hass, entry)
    sync_fleet_workspace_entity_registry(hass, entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        persistent_notification.async_dismiss(hass, _setup_notification_id(entry))
        async_clear_repairs_issues(hass, entry)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Normalize legacy entry data so upgraded installs do not crash newer flows."""
    data = dict(entry.data)
    changed = False

    normalized_defaults: dict[str, Any] = {
        CONF_TARGET_EXPORT_W: _coerce_number(data.get(CONF_TARGET_EXPORT_W), DEFAULT_TARGET_EXPORT_W),
        CONF_DEADBAND_W: _coerce_number(data.get(CONF_DEADBAND_W), DEFAULT_DEADBAND_W),
        CONF_BATTERY_RESERVE_SOC: _coerce_number(data.get(CONF_BATTERY_RESERVE_SOC), DEFAULT_BATTERY_RESERVE_SOC),
        CONF_REFRESH_SECONDS: _coerce_number(data.get(CONF_REFRESH_SECONDS), DEFAULT_REFRESH_SECONDS),
        CONF_DEVICE_INVENTORY_JSON: data.get(CONF_DEVICE_INVENTORY_JSON),
    }
    if normalized_defaults[CONF_DEVICE_INVENTORY_JSON] in (None, ""):
        normalized_defaults[CONF_DEVICE_INVENTORY_JSON] = DEFAULT_DEVICE_INVENTORY_JSON
    elif not isinstance(normalized_defaults[CONF_DEVICE_INVENTORY_JSON], str):
        normalized_defaults[CONF_DEVICE_INVENTORY_JSON] = str(normalized_defaults[CONF_DEVICE_INVENTORY_JSON])

    for key, normalized in normalized_defaults.items():
        if data.get(key) != normalized:
            data[key] = normalized
            changed = True

    if changed:
        hass.config_entries.async_update_entry(entry, data=data)

    _async_remove_stale_guided_flow_button_entities(hass, entry)
    await _async_update_native_setup_notice(hass, entry)
    await async_prime_install_provenance(hass, force_refresh=True)
    async_sync_repairs_issues(hass, entry)

    return True
