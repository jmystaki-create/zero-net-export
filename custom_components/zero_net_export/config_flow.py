"""Config flow for Zero Net Export."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import persistent_notification
from homeassistant.core import callback
from homeassistant.helpers import selector

from .candidate_utils import (
    assess_candidate,
    build_candidate_preview,
    build_candidate_review_hint,
    build_candidate_review_line,
    candidate_needs_review,
    discover_candidate_devices,
)
from .const import (
    CONF_BATTERY_CHARGE_POWER_ENTITY,
    CONF_BATTERY_DISCHARGE_POWER_ENTITY,
    CONF_BATTERY_RESERVE_SOC,
    CONF_BATTERY_SOC_ENTITY,
    CONF_DEADBAND_W,
    CONF_DEVICE_INVENTORY_JSON,
    DEVICE_CANDIDATE_FIXED_DOMAINS,
    DEVICE_CANDIDATE_VARIABLE_DOMAINS,
    CONF_GRID_EXPORT_ENERGY_ENTITY,
    CONF_GRID_EXPORT_POWER_ENTITY,
    CONF_GRID_IMPORT_ENERGY_ENTITY,
    CONF_GRID_IMPORT_POWER_ENTITY,
    CONF_GRID_SENSOR_MODE,
    CONF_HOME_LOAD_POWER_ENTITY,
    CONF_NAME,
    CONF_REFRESH_SECONDS,
    CONF_SOLAR_ENERGY_ENTITY,
    CONF_SOLAR_POWER_ENTITY,
    CONF_TARGET_EXPORT_W,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_DEADBAND_W,
    DEFAULT_DEVICE_INVENTORY_JSON,
    DEFAULT_GRID_SENSOR_MODE,
    DEFAULT_NAME,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_TARGET_EXPORT_W,
    DOMAIN,
    GRID_SENSOR_MODE_COMBINED,
    GRID_SENSOR_MODE_SEPARATE,
    MODE_DESCRIPTIONS,
    MODE_LABELS,
    MODE_ZERO_EXPORT,
    REQUIRED_SOURCE_KEYS,
    SOURCE_ROLE_LABELS,
)
from .device_model import (
    ADAPTER_FIXED_TOGGLE,
    ADAPTER_VARIABLE_NUMBER,
    DEVICE_KIND_FIXED,
    DEVICE_KIND_VARIABLE,
    default_device_blueprint,
    get_device_template,
    get_device_templates,
    parse_device_configs,
)
from .native_support import (
    ADVANCED_DEVICES_CONFIGURE_PATH,
    DETAILED_MANAGEMENT_PATH,
    DIAGNOSTICS_DEVICE_ACTIONS_PATH,
    DEVICES_CONFIGURE_PATH,
    DEVICES_SECTION_LABEL,
    INTEGRATION_DEVICE_PATH,
    MODE_CONTROL_PATH,
    POLICY_CONFIGURE_PATH,
    POLICY_SECTION_LABEL,
    PRIMARY_CONFIGURE_PATH,
    SOURCES_CONFIGURE_PATH,
    SOURCES_SECTION_LABEL,
    SUPPORT_CONFIGURE_PATH,
    SUPPORT_SECTION_LABEL,
    _source_specs_from_config,
    build_live_source_health_summary,
    build_native_command_center_summary,
    build_native_operator_readiness,
    build_source_attention_details,
    build_source_attention_role_summary,
    build_source_attention_summary,
    build_source_mapping_summary,
    build_source_repair_step,
    build_source_selector_fallback_hint,
    summarize_validation_issue_messages,
)
from .release_info import (
    build_install_consistency_summary,
    build_install_fingerprint_summary,
    build_install_provenance,
    build_install_repair_step,
)
from .validation import (
    DERIVED_SOURCE_MODE_DIRECT,
    DERIVED_SOURCE_MODE_NEGATIVE_ABS,
    DERIVED_SOURCE_MODE_POSITIVE,
    DERIVED_SOURCE_PREFIX,
    ENERGY_UNITS,
    PERCENT_UNITS,
    POWER_UNITS,
    TOTAL_STATE_CLASSES,
    parse_source_binding,
    validate_configured_entities,
)

_LOGGER = logging.getLogger(__name__)


def _candidate_usefulness_label(fit: dict[str, Any]) -> str:
    confidence = str(fit.get("confidence") or "medium")
    warnings = [str(item).strip() for item in (fit.get("warnings") or []) if str(item).strip()]
    if confidence == "medium" and warnings:
        return "review first"
    return {
        "high": "likely useful",
        "medium": "possible fit",
        "low": "review carefully",
    }.get(confidence, confidence)


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


def _coerce_text(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value
    return str(value)


def _entry_default_number(config_entry, key: str, fallback: int | float) -> int | float:
    return _coerce_number(config_entry.options.get(key, config_entry.data.get(key, fallback)), fallback)


def _entry_default_text(config_entry, key: str, fallback: str) -> str:
    return _coerce_text(config_entry.options.get(key, config_entry.data.get(key, fallback)), fallback)


def _live_mode_details(coordinator: Any) -> tuple[str, str]:
    state = getattr(coordinator, "data", None) if coordinator is not None else None
    raw_mode = str(getattr(state, "mode", "") or MODE_ZERO_EXPORT)
    mode_label = MODE_LABELS.get(raw_mode, raw_mode)
    mode_description = MODE_DESCRIPTIONS.get(raw_mode, f"Use {MODE_CONTROL_PATH} to adjust live controller behaviour.")
    return mode_label, mode_description


def _overlay_runtime_device_details(
    devices: list[dict[str, Any]], coordinator: Any | None
) -> list[dict[str, Any]]:
    """Merge runtime-only device visibility into parsed config-flow devices."""
    state = getattr(coordinator, "data", None) if coordinator is not None else None
    runtime_details = getattr(state, "device_details", {}) or {}
    if not runtime_details:
        return [dict(device) for device in devices]

    runtime_by_key = {
        str(device_key): details
        for device_key, details in runtime_details.items()
        if isinstance(details, dict)
    }
    runtime_by_entity_id = {
        str(details.get("entity_id")): details
        for details in runtime_details.values()
        if isinstance(details, dict) and details.get("entity_id")
    }

    enriched: list[dict[str, Any]] = []
    for device in devices:
        merged = dict(device)
        runtime = runtime_by_key.get(str(device.get("key")))
        if runtime is None and device.get("entity_id"):
            runtime = runtime_by_entity_id.get(str(device.get("entity_id")))
        if runtime:
            merged.update(
                {
                    "status": runtime.get("status"),
                    "usable": runtime.get("usable"),
                    "effective_enabled": runtime.get("effective_enabled", device.get("enabled", True)),
                    "guard_status": runtime.get("guard_status"),
                    "planned_action": runtime.get("planned_action"),
                    "last_action_status": runtime.get("last_action_status"),
                    "current_power_w": runtime.get("current_power_w"),
                    "current_target_power_w": runtime.get("current_target_power_w"),
                    "current_active_seconds": runtime.get("current_active_seconds"),
                    "active_runtime_today_seconds": runtime.get("active_runtime_today_seconds"),
                    "observed_active": runtime.get("observed_active"),
                }
            )
        enriched.append(merged)
    return enriched


def _format_runtime_power_label(value: Any) -> str:
    if value in (None, "", "unknown", "unavailable"):
        return "n/a"
    try:
        watts = float(value)
    except (TypeError, ValueError):
        return str(value)
    if watts.is_integer():
        return f"{int(watts)} W"
    return f"{watts:.1f} W"


def _format_runtime_duration_label(value: Any) -> str:
    if value in (None, "", "unknown", "unavailable"):
        return "n/a"
    try:
        total_seconds = max(int(round(float(value))), 0)
    except (TypeError, ValueError):
        return str(value)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def _build_bootstrap_schema(defaults: dict | None = None) -> vol.Schema:
    defaults = defaults or {}

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
        }
    )


def _build_bootstrap_entry_data(user_input: dict[str, str]) -> dict[str, str | int | float | None]:
    return {
        CONF_NAME: user_input[CONF_NAME],
        CONF_SOLAR_POWER_ENTITY: None,
        CONF_SOLAR_ENERGY_ENTITY: None,
        CONF_GRID_IMPORT_POWER_ENTITY: None,
        CONF_GRID_EXPORT_POWER_ENTITY: None,
        CONF_GRID_IMPORT_ENERGY_ENTITY: None,
        CONF_GRID_EXPORT_ENERGY_ENTITY: None,
        CONF_HOME_LOAD_POWER_ENTITY: None,
        CONF_BATTERY_SOC_ENTITY: None,
        CONF_BATTERY_CHARGE_POWER_ENTITY: None,
        CONF_BATTERY_DISCHARGE_POWER_ENTITY: None,
        CONF_TARGET_EXPORT_W: DEFAULT_TARGET_EXPORT_W,
        CONF_DEADBAND_W: DEFAULT_DEADBAND_W,
        CONF_BATTERY_RESERVE_SOC: DEFAULT_BATTERY_RESERVE_SOC,
        CONF_REFRESH_SECONDS: DEFAULT_REFRESH_SECONDS,
        CONF_DEVICE_INVENTORY_JSON: DEFAULT_DEVICE_INVENTORY_JSON,
    }


def _device_options_json(devices: list[dict[str, Any]]) -> str:
    import json

    return json.dumps(devices, indent=2)


COMBINED_GRID_ENERGY_FALLBACK_KEY = "grid_energy_entity_manual"
BATTERY_SOC_FALLBACK_KEY = "battery_soc_entity_manual"
MANUAL_CANDIDATE_SELECTION = "__manual__"
MANUAL_CANDIDATE_SHORTLIST_LABEL = "Open manual Managed Devices form (entity not surfaced here)"


def _build_derived_binding(mode: str, entity_id: str | None) -> str | None:
    if not entity_id:
        return None
    return f"{DERIVED_SOURCE_PREFIX}:{mode}:{entity_id}"


def _normalize_selector_entity_value(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("entity_id", "value", "id"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate:
                return candidate
    return str(value)


def _normalize_entity_selector_input(user_input: dict[str, Any] | None, key: str) -> str | None:
    if not user_input:
        return None
    value = _normalize_selector_entity_value(user_input.get(key))
    if value:
        return value
    alt_key = f"{key}.entity_id"
    alt_value = _normalize_selector_entity_value(user_input.get(alt_key))
    if alt_value:
        return alt_value
    selector_value = user_input.get(key)
    if isinstance(selector_value, dict):
        for nested_key in ("entity_id", "value", "id"):
            nested_value = _normalize_selector_entity_value(selector_value.get(nested_key))
            if nested_value:
                return nested_value
    return None


def _selector_entity_default(raw: str | None, *, allow_derived: bool = False) -> str:
    binding = parse_source_binding(raw)
    if not binding.valid or not binding.entity_id:
        return ""
    if binding.mode == DERIVED_SOURCE_MODE_DIRECT:
        return binding.entity_id
    return binding.entity_id if allow_derived else ""


def _infer_grid_sensor_mode(config: dict[str, Any]) -> str:
    import_power = parse_source_binding(config.get(CONF_GRID_IMPORT_POWER_ENTITY))
    export_power = parse_source_binding(config.get(CONF_GRID_EXPORT_POWER_ENTITY))
    import_energy = parse_source_binding(config.get(CONF_GRID_IMPORT_ENERGY_ENTITY))
    export_energy = parse_source_binding(config.get(CONF_GRID_EXPORT_ENERGY_ENTITY))

    power_combined = (
        import_power.valid
        and export_power.valid
        and import_power.entity_id
        and import_power.entity_id == export_power.entity_id
        and import_power.mode == DERIVED_SOURCE_MODE_POSITIVE
        and export_power.mode == DERIVED_SOURCE_MODE_NEGATIVE_ABS
    )
    energy_combined = (
        import_energy.valid
        and export_energy.valid
        and import_energy.entity_id
        and import_energy.entity_id == export_energy.entity_id
        and import_energy.mode == DERIVED_SOURCE_MODE_POSITIVE
        and export_energy.mode == DERIVED_SOURCE_MODE_NEGATIVE_ABS
    )
    if power_combined and energy_combined:
        return GRID_SENSOR_MODE_COMBINED
    if not any(
        config.get(key)
        for key in (
            CONF_GRID_IMPORT_POWER_ENTITY,
            CONF_GRID_EXPORT_POWER_ENTITY,
            CONF_GRID_IMPORT_ENERGY_ENTITY,
            CONF_GRID_EXPORT_ENERGY_ENTITY,
        )
    ):
        return DEFAULT_GRID_SENSOR_MODE
    return GRID_SENSOR_MODE_SEPARATE


def _grid_mode_default(config_entry) -> str:
    configured = config_entry.options.get(CONF_GRID_SENSOR_MODE, config_entry.data.get(CONF_GRID_SENSOR_MODE))
    if configured in {GRID_SENSOR_MODE_COMBINED, GRID_SENSOR_MODE_SEPARATE}:
        return str(configured)
    snapshot = dict(config_entry.data)
    snapshot.update(config_entry.options)
    return _infer_grid_sensor_mode(snapshot)


def _format_candidate_label(entity_id: str, state: Any) -> str:
    friendly = state.attributes.get("friendly_name") if state is not None else None
    state_value = state.state if state is not None else "unknown"
    domain = entity_id.split(".", 1)[0] if "." in entity_id else "unknown"
    label = str(friendly or entity_id)
    return f"{label} ({entity_id}, {domain}, state {state_value})"


def _format_source_option_label(entity_id: str, state: Any) -> str:
    friendly = state.attributes.get("friendly_name") if state is not None else None
    unit = state.attributes.get("unit_of_measurement") if state is not None else None
    state_value = state.state if state is not None else "unknown"
    label = str(friendly or entity_id)
    if unit:
        return f"{label} ({entity_id}, state {state_value} {unit})"
    return f"{label} ({entity_id}, state {state_value})"


def _source_candidate_reason_bits(state: Any, role_key: str, quantity: str) -> list[str]:
    if state is None:
        return []

    blob = _state_search_blob(state)
    device_class = str(state.attributes.get("device_class") or "")
    unit = str(state.attributes.get("unit_of_measurement") or "")
    state_class = str(state.attributes.get("state_class") or "")
    reasons: list[str] = []

    if quantity == "power" and (device_class == "power" or unit in POWER_UNITS):
        reasons.append("power-sensor metadata")
    elif quantity == "energy" and ((device_class == "energy" or unit in ENERGY_UNITS) and state_class in TOTAL_STATE_CLASSES):
        reasons.append("energy-dashboard-friendly metadata")
    elif quantity == "energy" and (device_class == "energy" or unit in ENERGY_UNITS):
        reasons.append("energy-sensor metadata")
    elif quantity == "percent" and (device_class == "battery" or unit in PERCENT_UNITS):
        reasons.append("battery/SOC metadata")

    role_match_tokens: dict[str, tuple[str, ...]] = {
        CONF_SOLAR_POWER_ENTITY: ("solar power", "pv", "generation"),
        CONF_SOLAR_ENERGY_ENTITY: ("yield total", "energy production", "generated"),
        CONF_GRID_IMPORT_POWER_ENTITY: ("grid import", "from grid", "import"),
        CONF_GRID_EXPORT_POWER_ENTITY: ("grid export", "to grid", "feed in", "returned"),
        CONF_GRID_IMPORT_ENERGY_ENTITY: ("total active energy", "grid import", "import"),
        CONF_GRID_EXPORT_ENERGY_ENTITY: ("returned energy", "grid export", "export"),
        CONF_HOME_LOAD_POWER_ENTITY: ("home demand", "house load", "consumption"),
        CONF_BATTERY_SOC_ENTITY: ("state of charge", "battery soc", "soc"),
        CONF_BATTERY_CHARGE_POWER_ENTITY: ("charge power", "charging"),
        CONF_BATTERY_DISCHARGE_POWER_ENTITY: ("discharge power", "discharging"),
    }
    matched_token = next((token for token in role_match_tokens.get(role_key, ()) if token in blob), None)
    if matched_token is not None:
        reasons.append(f"name matches '{matched_token}'")

    raw_state = str(getattr(state, "state", "") or "").lower()
    if raw_state not in {"unknown", "unavailable", ""}:
        reasons.append("currently reporting")

    deduped: list[str] = []
    for reason in reasons:
        if reason not in deduped:
            deduped.append(reason)
    return deduped[:3]


def _format_source_candidate_label(entity_id: str, state: Any, role_key: str, quantity: str) -> str:
    label = _format_source_option_label(entity_id, state)
    reasons = _source_candidate_reason_bits(state, role_key, quantity)
    if not reasons:
        return label
    return f"{label} [{'; '.join(reasons)}]"


def _state_search_blob(state: Any) -> str:
    entity_id = str(getattr(state, "entity_id", "") or "")
    friendly = str(state.attributes.get("friendly_name") or "") if state is not None else ""
    device_class = str(state.attributes.get("device_class") or "") if state is not None else ""
    parts = [part for part in (entity_id, friendly, device_class) if part]
    normalized = [part.replace("_", " ").replace("-", " ") for part in parts]
    return " ".join(parts + normalized).lower()


def _source_role_keywords(role_key: str) -> tuple[set[str], set[str]]:
    positive: dict[str, set[str]] = {
        CONF_SOLAR_POWER_ENTITY: {"solar", "pv", "inverter", "generation", "produced", "production"},
        CONF_SOLAR_ENERGY_ENTITY: {"solar", "pv", "inverter", "generation", "produced", "production", "yield"},
        CONF_GRID_IMPORT_POWER_ENTITY: {"grid", "import", "consumption", "from_grid", "mains", "purchase", "delivery", "bought"},
        CONF_GRID_EXPORT_POWER_ENTITY: {"grid", "export", "feed", "feedin", "to_grid", "mains", "return", "returned", "injection", "delivered"},
        CONF_GRID_IMPORT_ENERGY_ENTITY: {"grid", "import", "consumption", "from_grid", "mains", "purchase", "delivery", "bought"},
        CONF_GRID_EXPORT_ENERGY_ENTITY: {"grid", "export", "feed", "feedin", "to_grid", "mains", "return", "returned", "injection", "delivered"},
        CONF_HOME_LOAD_POWER_ENTITY: {"home", "house", "load", "consumption", "demand", "usage", "to_home", "site"},
        CONF_BATTERY_SOC_ENTITY: {"battery", "soc", "state_of_charge", "charge", "capacity"},
        CONF_BATTERY_CHARGE_POWER_ENTITY: {"battery", "charge", "charging", "charger"},
        CONF_BATTERY_DISCHARGE_POWER_ENTITY: {"battery", "discharge", "discharging", "inverter"},
    }
    negative: dict[str, set[str]] = {
        CONF_SOLAR_POWER_ENTITY: {"grid", "battery", "load", "house", "home", "soc", "import", "export"},
        CONF_SOLAR_ENERGY_ENTITY: {"grid", "battery", "load", "house", "home", "soc", "import", "export"},
        CONF_GRID_IMPORT_POWER_ENTITY: {"export", "feed", "feedin", "to_grid", "return", "returned", "injection", "solar", "pv", "battery", "soc"},
        CONF_GRID_EXPORT_POWER_ENTITY: {"import", "consumption", "from_grid", "purchase", "delivery", "bought", "solar", "pv", "battery", "soc"},
        CONF_GRID_IMPORT_ENERGY_ENTITY: {"export", "feed", "feedin", "to_grid", "return", "returned", "injection", "solar", "pv", "battery", "soc"},
        CONF_GRID_EXPORT_ENERGY_ENTITY: {"import", "consumption", "from_grid", "purchase", "delivery", "bought", "solar", "pv", "battery", "soc"},
        CONF_HOME_LOAD_POWER_ENTITY: {"grid", "solar", "pv", "battery", "soc", "export", "import"},
        CONF_BATTERY_SOC_ENTITY: {"grid", "solar", "pv", "load", "house", "home"},
        CONF_BATTERY_CHARGE_POWER_ENTITY: {"grid", "solar", "pv", "load", "house", "home", "soc"},
        CONF_BATTERY_DISCHARGE_POWER_ENTITY: {"grid", "solar", "pv", "load", "house", "home", "soc"},
    }
    return positive.get(role_key, set()), negative.get(role_key, set())


def _score_source_candidate(state: Any, role_key: str, quantity: str) -> int:
    blob = _state_search_blob(state)
    positive, negative = _source_role_keywords(role_key)
    score = 0
    for keyword in positive:
        if keyword in blob:
            score += 3
    for keyword in negative:
        if keyword in blob:
            score -= 2

    device_class = str(state.attributes.get("device_class") or "") if state is not None else ""
    unit = str(state.attributes.get("unit_of_measurement") or "") if state is not None else ""
    entity_id = str(getattr(state, "entity_id", "") or "")
    friendly_name = str(state.attributes.get("friendly_name") or "") if state is not None else ""
    state_class = str(state.attributes.get("state_class") or "") if state is not None else ""

    if quantity == "power":
        if device_class == "power" or unit in POWER_UNITS:
            score += 2
    elif quantity == "energy":
        if device_class == "energy" or unit in ENERGY_UNITS:
            score += 2
    elif quantity == "percent":
        if device_class == "battery" or unit in PERCENT_UNITS:
            score += 2

    if entity_id.startswith("sensor."):
        score += 1
    if role_key in {CONF_GRID_IMPORT_ENERGY_ENTITY, CONF_GRID_EXPORT_ENERGY_ENTITY, CONF_SOLAR_ENERGY_ENTITY} and state_class in TOTAL_STATE_CLASSES:
        score += 2
    if role_key in {CONF_GRID_IMPORT_POWER_ENTITY, CONF_GRID_EXPORT_POWER_ENTITY, CONF_HOME_LOAD_POWER_ENTITY, CONF_SOLAR_POWER_ENTITY} and any(token in blob for token in {"power", "watt", "watts"}):
        score += 1

    # Prefer whole-system live sensors over historical, diagnostic, or per-device telemetry.
    if "zero_net_export" in entity_id:
        score -= 20
    if entity_id.startswith("sensor.inverter_"):
        score -= 3
    if any(token in blob for token in {"max reported", "today", "yesterday", "this week", "this month", "lifetime", "estimated"}):
        score -= 4
    if any(token in blob for token in {"cost", "compensation"}):
        score -= 10
    if any(token in blob for token in {"home demand", "solar power", "state of charge", "grid import", "grid export", "returned energy", "total active energy", "yield total"}):
        score += 4
    if any(token in blob for token in {"bedroom", "lounge", "compressor", "estimated consumption"}):
        score -= 4
    if role_key == CONF_SOLAR_POWER_ENTITY and "solar power" in blob:
        score += 6
    if role_key == CONF_HOME_LOAD_POWER_ENTITY and "home demand" in blob:
        score += 6
    if role_key == CONF_BATTERY_SOC_ENTITY and "state of charge" in blob:
        score += 6
    if role_key == CONF_BATTERY_CHARGE_POWER_ENTITY and "charge power" in blob:
        score += 5
    if role_key == CONF_BATTERY_DISCHARGE_POWER_ENTITY and "discharge power" in blob:
        score += 5
    if role_key == CONF_GRID_IMPORT_POWER_ENTITY and "grid import" in blob:
        score += 6
    if role_key == CONF_GRID_IMPORT_POWER_ENTITY and "grid export" in blob:
        score -= 8
    if role_key == CONF_GRID_EXPORT_POWER_ENTITY and "grid export" in blob:
        score += 6
    if role_key == CONF_GRID_EXPORT_POWER_ENTITY and "grid import" in blob:
        score -= 8
    if role_key == CONF_GRID_IMPORT_ENERGY_ENTITY and "total active energy" in blob:
        score += 6
    if role_key == CONF_GRID_IMPORT_ENERGY_ENTITY and "returned energy" in blob:
        score -= 8
    if role_key == CONF_GRID_EXPORT_ENERGY_ENTITY and "returned energy" in blob:
        score += 8
    if role_key == CONF_SOLAR_ENERGY_ENTITY and any(token in blob for token in {"yield total", "energy production", "generated"}):
        score += 4
    if quantity == "energy" and any(token in blob for token in {"phase a", "phase b", "phase c"}):
        score -= 2
    if quantity == "energy" and any(token in friendly_name.lower() for token in {"today", "yesterday", "this week", "this month"}):
        score -= 3

    raw_state = str(getattr(state, "state", "") or "").lower()
    if raw_state in {"unknown", "unavailable"}:
        score -= 3
    return score


def _state_matches_source_quantity(state: Any, quantity: str) -> bool:
    if state is None:
        return False

    device_class = str(state.attributes.get("device_class") or "")
    unit = str(state.attributes.get("unit_of_measurement") or "")
    state_class = str(state.attributes.get("state_class") or "")

    if quantity == "power":
        return device_class == "power" or unit in POWER_UNITS
    if quantity == "energy":
        return (
            device_class == "energy"
            or unit in ENERGY_UNITS
            or state_class in TOTAL_STATE_CLASSES
        )
    if quantity == "percent":
        return device_class in {"battery", "power_factor"} or unit in PERCENT_UNITS
    return False


def _rank_source_candidates(
    states: list[Any],
    role_key: str,
    quantity: str,
    *,
    minimum_score: int | None = None,
) -> list[tuple[int, str, Any]]:
    ranked: list[tuple[int, str, Any]] = []
    for state in states:
        entity_id = str(getattr(state, "entity_id", "") or "")
        if entity_id.split(".", 1)[0] != "sensor":
            continue
        if not _state_matches_source_quantity(state, quantity):
            continue
        score = _score_source_candidate(state, role_key, quantity)
        if minimum_score is not None and score < minimum_score:
            continue
        ranked.append((score, entity_id, state))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked


def _best_source_candidate_entity(
    states: list[Any],
    role_key: str,
    quantity: str,
    *,
    minimum_score: int = 10,
    minimum_margin: int = 3,
) -> str | None:
    ranked = _rank_source_candidates(states, role_key, quantity, minimum_score=minimum_score)
    if not ranked:
        return None

    best_score, best_entity_id, _ = ranked[0]
    if len(ranked) == 1:
        return best_entity_id

    second_score = ranked[1][0]
    if best_score - second_score >= minimum_margin:
        return best_entity_id

    best_blob = _state_search_blob(ranked[0][2])
    explicit_tokens: dict[str, tuple[str, ...]] = {
        CONF_SOLAR_POWER_ENTITY: ("solar power", "pv power"),
        CONF_SOLAR_ENERGY_ENTITY: ("yield total", "energy production", "generated"),
        CONF_GRID_IMPORT_POWER_ENTITY: ("grid import", "from grid"),
        CONF_GRID_EXPORT_POWER_ENTITY: ("grid export", "to grid", "returned"),
        CONF_GRID_IMPORT_ENERGY_ENTITY: ("total active energy", "imported energy", "from grid"),
        CONF_GRID_EXPORT_ENERGY_ENTITY: ("returned energy", "exported energy", "to grid"),
        CONF_HOME_LOAD_POWER_ENTITY: ("home demand", "house load"),
        CONF_BATTERY_SOC_ENTITY: ("state of charge", "battery soc"),
    }
    if any(token in best_blob for token in explicit_tokens.get(role_key, ())):
        return best_entity_id
    return None


def _grid_mode_missing_sources(config: dict[str, Any], grid_mode: str) -> list[str]:
    required_keys = [
        CONF_SOLAR_POWER_ENTITY,
        CONF_SOLAR_ENERGY_ENTITY,
    ]
    if grid_mode == GRID_SENSOR_MODE_COMBINED:
        required_keys.extend(
            [
                CONF_GRID_IMPORT_POWER_ENTITY,
                CONF_GRID_IMPORT_ENERGY_ENTITY,
            ]
        )
    else:
        required_keys.extend(
            [
                CONF_GRID_IMPORT_POWER_ENTITY,
                CONF_GRID_EXPORT_POWER_ENTITY,
                CONF_GRID_IMPORT_ENERGY_ENTITY,
                CONF_GRID_EXPORT_ENERGY_ENTITY,
            ]
        )
    return [key for key in required_keys if not config.get(key)]


def _summarize_issue_messages(
    issues: list[Any],
    *,
    severities: set[str] | None = None,
    limit: int = 3,
) -> str:
    allowed = {severity.lower() for severity in severities} if severities else None
    messages: list[str] = []
    for issue in issues:
        severity = str(getattr(issue, "severity", "") or "").lower()
        if allowed is not None and severity not in allowed:
            continue
        message = str(getattr(issue, "message", "") or "").strip()
        if message and message not in messages:
            messages.append(message)
        if len(messages) >= limit:
            break
    return "; ".join(messages) if messages else "None"


def _issue_role_keys(issues: list[Any], *, severities: set[str] | None = None) -> list[str]:
    allowed = {severity.lower() for severity in severities} if severities else None
    keys: list[str] = []
    for issue in issues:
        severity = str(getattr(issue, "severity", "") or "").lower()
        if allowed is not None and severity not in allowed:
            continue
        code = str(getattr(issue, "code", "") or "")
        if "_" not in code:
            continue
        key = code.rsplit("_", 1)[0]
        if key in SOURCE_ROLE_LABELS and key not in keys:
            keys.append(key)
    return keys


def _command_center_menu_options(recommended_section: str) -> list[str]:
    recommended_map = {
        SOURCES_SECTION_LABEL: "native_setup",
        DEVICES_SECTION_LABEL: "devices",
        POLICY_SECTION_LABEL: "policy",
        SUPPORT_SECTION_LABEL: "support",
    }
    base_options = ["native_setup", "policy", "devices", "support"]
    recommended_option = recommended_map.get(recommended_section)
    ordered = [option for option in base_options if option == recommended_option]
    ordered.extend(option for option in base_options if option != recommended_option)
    return ordered


class ZeroNetExportConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            entry_data = _build_bootstrap_entry_data(user_input)
            return self.async_create_entry(title=user_input[CONF_NAME], data=entry_data)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_bootstrap_schema(user_input),
            errors={},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ZeroNetExportOptionsFlow(config_entry)


class ZeroNetExportOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        super().__init__()
        self._config_entry = config_entry
        self._pending_grid_sensor_mode: str | None = None
        self._pending_device_kind: str | None = None
        self._pending_device_key: str | None = None
        self._pending_device_template_key: str | None = None
        self._pending_candidate_entity_id: str | None = None
        self._pending_candidate_summary: dict[str, Any] | None = None

    @staticmethod
    def _active_planned_action(device: dict[str, Any]) -> str:
        planned_action = str(device.get("planned_action") or "").strip()
        return planned_action if planned_action not in {"", "hold"} else ""

    @classmethod
    def _device_has_blocked_activity(cls, device: dict[str, Any]) -> bool:
        if device.get("usable") is False:
            return True
        return bool(cls._active_planned_action(device)) and device.get("action_executable") is False

    @staticmethod
    def _device_has_recent_attention(device: dict[str, Any]) -> bool:
        last_action_status = str(device.get("last_action_status") or "").strip().lower()
        return bool(last_action_status and last_action_status not in {"ok", "applied", "success"})

    @classmethod
    def _device_needs_attention(cls, device: dict[str, Any]) -> bool:
        return bool(
            cls._device_has_blocked_activity(device)
            or cls._active_planned_action(device)
            or cls._device_has_recent_attention(device)
        )

    @classmethod
    def _device_sort_key(cls, device: dict[str, Any]) -> tuple[int, int, int, int, int, str]:
        effective_enabled = bool(device.get("effective_enabled", device.get("enabled", True)))
        usable = device.get("usable")
        blocked_rank = 0 if cls._device_has_blocked_activity(device) else 1
        planned_rank = 0 if cls._active_planned_action(device) else 1
        recent_attention_rank = 0 if cls._device_has_recent_attention(device) else 1
        enabled_usable_rank = 0 if effective_enabled and usable is True else 1
        return (
            blocked_rank,
            planned_rank,
            recent_attention_rank,
            enabled_usable_rank,
            int(device.get("priority", 0) or 0),
            str(device.get("name", "")).lower(),
        )

    @staticmethod
    def _device_status_label(device: dict[str, Any]) -> str:
        state = "enabled" if device.get("effective_enabled", device.get("enabled", True)) else "disabled"
        priority = int(device.get("priority", 0) or 0)
        nominal_power = int(float(device.get("nominal_power_w", 0) or 0))
        operator_priority_override = device.get("operator_priority_override")
        operator_enabled_override = device.get("operator_enabled_override")
        runtime_bits: list[str] = []
        planned_action = ZeroNetExportOptionsFlow._active_planned_action(device)
        if ZeroNetExportOptionsFlow._device_has_blocked_activity(device):
            runtime_bits.append("blocked")
        elif planned_action:
            runtime_bits.append("planned")
        elif ZeroNetExportOptionsFlow._device_has_recent_attention(device):
            runtime_bits.append("attention")
        elif device.get("observed_active") is True:
            runtime_bits.append("active")
        if device.get("usable") is not None:
            runtime_bits.append("usable" if device.get("usable") else "not usable")
        if device.get("status"):
            runtime_bits.append(str(device.get("status")))
        runtime_bits.append(f"power {_format_runtime_power_label(device.get('current_power_w'))}")
        if device.get("kind") == DEVICE_KIND_VARIABLE and device.get("current_target_power_w") is not None:
            runtime_bits.append(f"target {_format_runtime_power_label(device.get('current_target_power_w'))}")
        current_runtime = device.get("current_active_seconds")
        if current_runtime not in (None, 0, 0.0):
            runtime_bits.append(f"runtime {_format_runtime_duration_label(current_runtime)}")
        runtime_today = device.get("active_runtime_today_seconds")
        if runtime_today not in (None, 0, 0.0):
            runtime_bits.append(f"today {_format_runtime_duration_label(runtime_today)}")
        if device.get("guard_status"):
            runtime_bits.append(f"guard {device.get('guard_status')}")
        if planned_action:
            runtime_bits.append(f"action {planned_action}")
        if device.get("last_action_status"):
            runtime_bits.append(f"last {device.get('last_action_status')}")
        if operator_priority_override is not None:
            runtime_bits.append(f"priority override {int(operator_priority_override)}")
        if operator_enabled_override is not None:
            runtime_bits.append(f"enabled override {'on' if operator_enabled_override else 'off'}")
        runtime_summary = f" [{' | '.join(runtime_bits)}]" if runtime_bits else ""
        return (
            f"{device.get('name', 'Unnamed device')}{runtime_summary} "
            f"({device.get('kind', 'unknown')}, {state}, priority {priority}, nominal {nominal_power} W)"
        )

    @staticmethod
    def _managed_runtime_activity(devices: list[dict[str, Any]]) -> tuple[int, float]:
        active_devices = [device for device in devices if device.get("observed_active") is True]
        active_power_w = round(sum(float(device.get("current_power_w", 0) or 0) for device in active_devices), 1)
        return len(active_devices), active_power_w

    @classmethod
    def _managed_snapshot_focus_label(cls, device: dict[str, Any] | None) -> str:
        if not device:
            return ""
        name = str(device.get("name") or device.get("entity_id") or "Unnamed device").strip()
        parts: list[str] = []
        kind = str(device.get("kind") or "").strip()
        if kind:
            parts.append(kind)
        if cls._device_has_blocked_activity(device):
            parts.append("not usable" if device.get("usable") is False else "blocked")
        elif cls._active_planned_action(device):
            parts.append(f"action {cls._active_planned_action(device)}")
        elif cls._device_has_recent_attention(device) and device.get("last_action_status"):
            parts.append(f"last {device.get('last_action_status')}")
        elif device.get("observed_active") is True and device.get("current_power_w") not in (None, ""):
            parts.append(f"active {_format_runtime_power_label(device.get('current_power_w'))}")
        return f"{name} ({' | '.join(parts)})" if parts else name

    def _fleet_summary_lines(self, devices: list[dict[str, Any]]) -> list[str]:
        if not devices:
            return ["- None"]
        ordered = sorted(devices, key=self._device_sort_key)
        attention_devices = [
            device for device in ordered if self._device_needs_attention(device)
        ]
        other_devices = [
            device for device in ordered if not self._device_needs_attention(device)
        ]
        enabled_count = sum(1 for device in devices if device.get("effective_enabled", device.get("enabled", True)))
        usable_count = sum(1 for device in devices if device.get("usable") is True)
        blocked_count = sum(1 for device in devices if self._device_has_blocked_activity(device))
        planned_count = sum(1 for device in devices if self._active_planned_action(device))
        attention_count = sum(1 for device in devices if self._device_needs_attention(device))
        active_count, active_power_w = self._managed_runtime_activity(devices)
        fixed_count = sum(1 for device in devices if device.get("kind") == DEVICE_KIND_FIXED)
        variable_count = sum(1 for device in devices if device.get("kind") == DEVICE_KIND_VARIABLE)
        total_power = int(sum(float(device.get("nominal_power_w", 0) or 0) for device in devices))
        attention_device = next((device for device in ordered if self._device_needs_attention(device)), None)
        active_device = next((device for device in ordered if device.get("observed_active") is True), None)
        blocked_device = next((device for device in ordered if self._device_has_blocked_activity(device)), None)
        planned_device = next((device for device in ordered if self._active_planned_action(device)), None)
        fleet_summary_parts = [f"{len(devices)} managed device(s)"]
        if attention_count:
            fleet_summary_parts.append(
                "1 managed device needs attention"
                if attention_count == 1
                else f"{attention_count} managed devices need attention"
            )
            if attention_device:
                fleet_summary_parts.append(
                    f"attention first {self._managed_snapshot_focus_label(attention_device)}"
                )
        if blocked_device:
            fleet_summary_parts.append(f"blocked {self._managed_snapshot_focus_label(blocked_device)}")
        elif blocked_count:
            fleet_summary_parts.append(f"{blocked_count} blocked")
        if planned_count:
            fleet_summary_parts.append(
                "1 planned action(s)" if planned_count == 1 else f"{planned_count} planned action(s)"
            )
            if planned_device:
                fleet_summary_parts.append(f"plan {self._managed_snapshot_focus_label(planned_device)}")
        if active_count:
            fleet_summary_parts.append(f"active load {active_power_w:g} W")
            fleet_summary_parts.append(
                "1 active managed device" if active_count == 1 else f"{active_count} active managed devices"
            )
            if active_device and not attention_device and not blocked_device and not planned_device:
                fleet_summary_parts.append(
                    f"active device {self._managed_snapshot_focus_label(active_device)}"
                )
        fleet_summary_parts.extend(
            [
                f"{enabled_count} enabled",
                f"{usable_count} usable",
                f"{blocked_count} blocked",
                f"{fixed_count} fixed",
                f"{variable_count} variable",
                f"{total_power} W nominal controllable power",
            ]
        )
        lines = [
            "- Fleet summary: " + ", ".join(fleet_summary_parts),
            "- Managed devices needing attention first:",
        ]
        if attention_devices:
            lines.extend(f"- {self._device_status_label(device)}" for device in attention_devices)
        else:
            lines.append("- None")
        lines.append("- Other managed devices:")
        if other_devices:
            lines.extend(f"- {self._device_status_label(device)}" for device in other_devices)
        else:
            lines.append("- None")
        return lines

    def _device_blocker_summary(self) -> str:
        coordinator = self._coordinator()
        if coordinator is None:
            return "No higher-priority Sensors, Controls, or Diagnostics blocker is currently ahead of fleet work."

        command_center = build_native_command_center_summary(coordinator)
        recommended_section = str(command_center.get("recommended_section") or "").strip()
        recommended_reason = str(command_center.get("recommended_reason") or "").strip()
        recommended_path = str(command_center.get("recommended_path") or "").strip()
        next_action = str(
            command_center.get("next_action_summary")
            or command_center.get("device_next_step")
            or ""
        ).strip()
        device_blocker_step = str(command_center.get("device_next_step") or "").strip()

        blocker_step = ""
        if recommended_section and recommended_section != DEVICES_SECTION_LABEL and next_action:
            blocker_step = next_action
        elif any(
            path in device_blocker_step
            for path in (SOURCES_CONFIGURE_PATH, POLICY_CONFIGURE_PATH, SUPPORT_CONFIGURE_PATH)
        ):
            blocker_step = device_blocker_step

        if blocker_step:
            detail_parts = [f"Before fleet work: {blocker_step}"]
            if recommended_reason:
                detail_parts.append(f"Why: {recommended_reason}")
            if recommended_path and recommended_path not in blocker_step:
                detail_parts.append(f"Path: {recommended_path}")
            return "\n".join(detail_parts)

        return "No higher-priority Sensors, Controls, or Diagnostics blocker is currently ahead of fleet work."

    def _device_candidates(self) -> list[dict[str, Any]]:
        devices, _ = self._load_devices()
        managed_ids = {str(device.get("entity_id")) for device in devices if device.get("entity_id")}
        candidates: list[dict[str, Any]] = []
        for candidate in discover_candidate_devices(self.hass.states.async_all(), managed_ids):
            entity_id = candidate["entity_id"]
            state = self.hass.states.get(entity_id)
            candidates.append(
                {
                    **candidate,
                    "label": build_candidate_preview(
                        candidate,
                        include_entity_id=False,
                        include_state=False,
                    ),
                    "fallback_label": _format_candidate_label(entity_id, state),
                }
            )
        return candidates

    def _managed_snapshot_text(self, devices: list[dict[str, Any]]) -> str:
        if not devices:
            return "0 managed | 0 enabled | 0 usable"

        ordered = sorted(devices, key=self._device_sort_key)
        enabled_count = sum(1 for device in devices if device.get("effective_enabled", device.get("enabled", True)))
        usable_count = sum(1 for device in devices if device.get("usable") is True)
        attention_count = sum(1 for device in devices if self._device_needs_attention(device))
        active_count, active_power_w = self._managed_runtime_activity(devices)
        fixed_count = sum(1 for device in devices if device.get("kind") == DEVICE_KIND_FIXED)
        variable_count = sum(1 for device in devices if device.get("kind") == DEVICE_KIND_VARIABLE)
        nominal_power = int(sum(float(device.get("nominal_power_w", 0) or 0) for device in devices))
        planned_count = sum(1 for device in devices if self._active_planned_action(device))
        kind_known = any(device.get("kind") in {DEVICE_KIND_FIXED, DEVICE_KIND_VARIABLE} for device in devices)
        attention_device = next((device for device in ordered if self._device_needs_attention(device)), None)
        active_device = next((device for device in ordered if device.get("observed_active") is True), None)
        blocked_device = next((device for device in ordered if self._device_has_blocked_activity(device)), None)
        planned_device = next((device for device in ordered if self._active_planned_action(device)), None)
        summary_parts = [
            f"{len(devices)} managed",
            f"{enabled_count} enabled",
            f"{usable_count} usable",
        ]
        if active_count:
            summary_parts.append(f"active load {active_power_w:g} W")
            summary_parts.append(
                "1 active managed device" if active_count == 1 else f"{active_count} active managed devices"
            )
            if active_device and not attention_device and not blocked_device and not planned_device:
                summary_parts.append(f"active device {self._managed_snapshot_focus_label(active_device)}")
        if attention_count:
            summary_parts.append(
                "1 managed device needs attention"
                if attention_count == 1
                else f"{attention_count} managed devices need attention"
            )
            if attention_device:
                summary_parts.append(f"attention first {self._managed_snapshot_focus_label(attention_device)}")
        if kind_known:
            summary_parts.append(f"{fixed_count} fixed managed")
            if variable_count:
                summary_parts.append(f"{variable_count} variable managed")
            summary_parts.append(f"{nominal_power} W nominal")
        if blocked_device:
            summary_parts.append(f"blocked {self._managed_snapshot_focus_label(blocked_device)}")
        if planned_count:
            summary_parts.append(f"{planned_count} planned action(s)")
        if planned_device:
            summary_parts.append(f"plan {self._managed_snapshot_focus_label(planned_device)}")
        return " | ".join(summary_parts)

    @staticmethod
    def _candidate_mix_counts(candidates: list[dict[str, Any]]) -> tuple[int, int]:
        fixed_count = sum(1 for item in candidates if item.get("kind") == DEVICE_KIND_FIXED)
        variable_count = sum(1 for item in candidates if item.get("kind") == DEVICE_KIND_VARIABLE)
        return fixed_count, variable_count

    @staticmethod
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
        any_ready = fixed_ready_count > 0 or variable_ready_count > 0

        def _append(kind_label: str, candidate_count: int, review_count: int, ready_count: int) -> None:
            if candidate_count <= 0 or not any_ready or (review_count <= 0 and ready_count <= 0):
                return
            if review_count > 0 and ready_count > 0:
                parts.append(f"{kind_label} backlog {review_count} review/{ready_count} ready")
            elif review_count > 0:
                parts.append(f"{kind_label} backlog {review_count} review")
            elif ready_count > 0:
                parts.append(f"{kind_label} backlog {ready_count} ready")

        include_fixed = bool(
            fixed_candidate_count and (variable_candidate_count or (fixed_review_count and fixed_ready_count))
        )
        include_variable = bool(
            variable_candidate_count and (fixed_candidate_count or (variable_review_count and variable_ready_count))
        )
        if include_fixed:
            _append("fixed", fixed_candidate_count, fixed_review_count, fixed_ready_count)
        if include_variable:
            _append("variable", variable_candidate_count, variable_review_count, variable_ready_count)
        return parts

    @classmethod
    def _unmanaged_snapshot_text(cls, candidates: list[dict[str, Any]]) -> str:
        if not candidates:
            return "0 candidates"

        fixed_count, variable_count = cls._candidate_mix_counts(candidates)
        review_candidates = [item for item in candidates if candidate_needs_review(assess_candidate(item))]
        ready_candidate_count = max(len(candidates) - len(review_candidates), 0)
        fixed_review_count = sum(1 for item in review_candidates if item.get("kind") == DEVICE_KIND_FIXED)
        variable_review_count = sum(1 for item in review_candidates if item.get("kind") == DEVICE_KIND_VARIABLE)
        fixed_ready_count = max(fixed_count - fixed_review_count, 0)
        variable_ready_count = max(variable_count - variable_review_count, 0)
        top_candidate = candidates[0]
        top_name = str(top_candidate.get("name") or top_candidate.get("entity_id") or "").strip()
        review_candidate = review_candidates[0] if review_candidates else None
        ready_candidate = next(
            (item for item in candidates if not candidate_needs_review(assess_candidate(item))),
            None,
        )
        ready_name = str((ready_candidate or {}).get("name") or (ready_candidate or {}).get("entity_id") or "").strip()
        parts = [f"{len(candidates)} candidates"]
        if fixed_count:
            parts.append(f"{fixed_count} fixed candidate" if fixed_count == 1 else f"{fixed_count} fixed candidates")
        if variable_count:
            parts.append(f"{variable_count} variable candidate" if variable_count == 1 else f"{variable_count} variable candidates")
        parts.extend(
            cls._candidate_kind_backlog_mix_parts(
                fixed_candidate_count=fixed_count,
                variable_candidate_count=variable_count,
                fixed_review_count=fixed_review_count,
                variable_review_count=variable_review_count,
                fixed_ready_count=fixed_ready_count,
                variable_ready_count=variable_ready_count,
            )
        )
        if review_candidates:
            parts.append("1 needs review" if len(review_candidates) == 1 else f"{len(review_candidates)} need review")
            if fixed_review_count:
                parts.append(f"{fixed_review_count} fixed review")
            if variable_review_count:
                parts.append(f"{variable_review_count} variable review")
            review_name = str((review_candidate or {}).get("name") or (review_candidate or {}).get("entity_id") or "").strip()
            if review_name:
                parts.append(f"review {review_name}")
                parts.append(
                    build_candidate_review_hint(
                        review_candidate,
                        include_warning=review_candidate is not top_candidate,
                        max_warning_chars=32,
                    )
                )
        top_hint = build_candidate_review_hint(top_candidate, max_warning_chars=32)
        if top_candidate is review_candidate:
            if " | warn " in top_hint:
                _, _, warning = top_hint.partition(" | warn ")
                parts.append(f"key warning: {warning}")
            else:
                parts.append("key warning: No immediate warnings")
        if ready_candidate_count:
            parts.append(
                "1 ready to promote"
                if ready_candidate_count == 1
                else f"{ready_candidate_count} ready to promote"
            )
        if ready_name:
            parts.append(f"ready {ready_name}")
            parts.append(build_candidate_review_hint(ready_candidate, include_warning=False, max_warning_chars=32))
        elif top_name and top_candidate is not review_candidate:
            parts.append(f"surfaced {top_name}")
        if top_candidate is ready_candidate:
            if " | warn " in top_hint:
                _, _, warning = top_hint.partition(" | warn ")
                parts.append(f"key warning: {warning}")
            else:
                parts.append("key warning: No immediate warnings")
        elif top_candidate is not review_candidate:
            top_preview = build_candidate_preview(top_candidate, include_entity_id=False, include_state=False)
            _, separator, preview_tail = top_preview.partition(" | ")
            if separator and preview_tail:
                parts.append(preview_tail)
            elif top_preview:
                parts.append(top_preview)
            if "key warning:" not in (preview_tail if separator else top_preview):
                if " | warn " in top_hint:
                    _, _, warning = top_hint.partition(" | warn ")
                    parts.append(f"key warning: {warning}")
                else:
                    parts.append("key warning: No immediate warnings")
        return " | ".join(parts)

    @staticmethod
    def _trim_focus_sentence(text: str) -> str:
        return text.rstrip().rstrip(".!? ")

    @classmethod
    def _top_candidate_focus_text(cls, candidate: dict[str, Any] | None) -> str:
        if not candidate:
            return "none discovered right now"
        return cls._trim_focus_sentence(build_candidate_preview(candidate, include_entity_id=False))

    @staticmethod
    def _review_candidate_focus_text(candidates: list[dict[str, Any]]) -> str:
        review_candidate = next(
            (item for item in candidates if candidate_needs_review(assess_candidate(item))),
            None,
        )
        if not review_candidate:
            return "None flagged for review right now"
        return build_candidate_preview(review_candidate, include_entity_id=False)

    @staticmethod
    def _ready_candidate_focus_text(candidates: list[dict[str, Any]]) -> str:
        ready_candidate = next(
            (item for item in candidates if not candidate_needs_review(assess_candidate(item))),
            None,
        )
        if not ready_candidate:
            return "None ready to promote right now"
        return build_candidate_preview(ready_candidate, include_entity_id=False)

    @classmethod
    def _post_save_candidate_follow_through(cls, candidates: list[dict[str, Any]]) -> str:
        top_candidate = candidates[0] if candidates else None
        review_candidate = next(
            (item for item in candidates if candidate_needs_review(assess_candidate(item))),
            None,
        )
        ready_candidate = next(
            (item for item in candidates if not candidate_needs_review(assess_candidate(item))),
            None,
        )
        if review_candidate is not None:
            follow_through = (
                "start in the unmanaged section: "
                + cls._top_candidate_focus_text(review_candidate)
            )
            if ready_candidate is not None and ready_candidate is not review_candidate:
                follow_through += (
                    ", then promote next from the unmanaged section: "
                    + cls._top_candidate_focus_text(ready_candidate)
                )
            return follow_through
        if top_candidate is not None:
            return (
                "promote next from the unmanaged section: "
                + cls._top_candidate_focus_text(top_candidate)
            )
        return "use the deeper device review path only if you need more per-device runtime detail"

    @staticmethod
    def _candidate_snapshot_text(candidates: list[dict[str, Any]], *, limit: int = 12) -> str:
        if not candidates:
            return "- No unmanaged candidate devices discovered right now"

        surfaced = candidates[:limit]
        review_first = [item for item in surfaced if candidate_needs_review(assess_candidate(item))]
        ready_now = [item for item in surfaced if item not in review_first]

        lines: list[str] = []
        if review_first:
            lines.append("- Review-first unmanaged candidates:")
            lines.extend(
                f"- {build_candidate_preview(item, include_entity_id=False)}" for item in review_first
            )
        if ready_now:
            lines.append("- Ready to promote next:")
            lines.extend(
                f"- {build_candidate_preview(item, include_entity_id=False)}" for item in ready_now
            )

        remaining_count = max(len(candidates) - len(surfaced), 0)
        if remaining_count:
            lines.append(
                "- Additional surfaced candidates remain below: "
                + ("1 more" if remaining_count == 1 else f"{remaining_count} more")
            )

        return "\n".join(lines)

    @staticmethod
    def _candidate_kind_summary(candidates: list[dict[str, Any]], kind: str, *, limit: int = 6) -> str:
        matching = [item for item in candidates if item.get("kind") == kind]
        surfaced = matching[:limit]
        if not surfaced:
            if kind == DEVICE_KIND_FIXED:
                return "- No fixed-load candidates discovered right now"
            return "- No variable-load candidates discovered right now"

        kind_label = "fixed-load" if kind == DEVICE_KIND_FIXED else "variable-load"
        review_first = [item for item in surfaced if candidate_needs_review(assess_candidate(item))]
        ready_now = [item for item in surfaced if item not in review_first]

        lines: list[str] = []
        if review_first:
            lines.append(f"- Review-first {kind_label} candidates:")
            lines.extend(
                f"- {build_candidate_preview(item, include_entity_id=False)}" for item in review_first
            )
        if ready_now:
            lines.append(f"- Ready-next {kind_label} candidates:")
            lines.extend(
                f"- {build_candidate_preview(item, include_entity_id=False)}" for item in ready_now
            )

        remaining_count = max(len(matching) - len(surfaced), 0)
        if remaining_count:
            lines.append(
                f"- Additional {kind_label} candidates remain below: "
                + ("1 more" if remaining_count == 1 else f"{remaining_count} more")
            )
        return "\n".join(lines)

    def _managed_devices_workspace_placeholders(
        self,
        display_devices: list[dict[str, Any]],
        candidates: list[dict[str, Any]],
    ) -> dict[str, str]:
        fixed_candidate_count, variable_candidate_count = self._candidate_mix_counts(candidates)
        top_candidate = candidates[0] if candidates else None
        return {
            "configure_path": DEVICES_CONFIGURE_PATH,
            "devices_path": DEVICES_CONFIGURE_PATH,
            "sources_path": SOURCES_CONFIGURE_PATH,
            "policy_path": POLICY_CONFIGURE_PATH,
            "mode_path": MODE_CONTROL_PATH,
            "support_path": SUPPORT_CONFIGURE_PATH,
            "device_count": str(len(display_devices)),
            "managed_snapshot": self._managed_snapshot_text(display_devices),
            "device_summary": "\n".join(self._fleet_summary_lines(display_devices)),
            "candidate_count": str(len(candidates)),
            "unmanaged_snapshot": self._unmanaged_snapshot_text(candidates),
            "candidate_summary": self._candidate_snapshot_text(candidates),
            "fixed_candidate_count": str(fixed_candidate_count),
            "fixed_candidate_summary": self._candidate_kind_summary(candidates, DEVICE_KIND_FIXED),
            "variable_candidate_count": str(variable_candidate_count),
            "variable_candidate_summary": self._candidate_kind_summary(candidates, DEVICE_KIND_VARIABLE),
            "top_candidate": self._top_candidate_focus_text(top_candidate),
            "review_candidate": self._review_candidate_focus_text(candidates),
            "ready_candidate": self._ready_candidate_focus_text(candidates),
        }

    @staticmethod
    def _count_label(count: int, singular: str, plural: str | None = None) -> str:
        if count == 1:
            return f"1 {singular}"
        return f"{count} {plural or singular + 's'}"

    @classmethod
    def _device_action_label(
        cls,
        action: str,
        *,
        managed_count: int,
        attention_count: int,
        fixed_candidate_count: int,
        variable_candidate_count: int,
        fixed_review_candidate_count: int,
        variable_review_candidate_count: int,
        fixed_ready_candidate_count: int,
        variable_ready_candidate_count: int,
    ) -> str:
        def _review_count_label(count: int) -> str:
            return "1 candidate needs review" if count == 1 else f"{count} candidates need review"

        def _ready_count_label(count: int) -> str:
            return "1 candidate ready to promote" if count == 1 else f"{count} candidates ready to promote"

        def _attention_count_label(count: int) -> str:
            return "1 managed device needs attention" if count == 1 else f"{count} managed devices need attention"

        if action == "add_fixed":
            if fixed_candidate_count:
                label = (
                    "Promote fixed-load candidate"
                    f" / {cls._count_label(fixed_candidate_count, 'fixed candidate')} surfaced"
                )
                if fixed_review_candidate_count:
                    label += f" / {_review_count_label(fixed_review_candidate_count)}"
                if fixed_ready_candidate_count:
                    label += f" / {_ready_count_label(fixed_ready_candidate_count)}"
                return label
            return "Add fixed load device manually"
        if action == "add_variable":
            if variable_candidate_count:
                label = (
                    "Promote variable-load candidate"
                    f" / {cls._count_label(variable_candidate_count, 'variable candidate')} surfaced"
                )
                if variable_review_candidate_count:
                    label += f" / {_review_count_label(variable_review_candidate_count)}"
                if variable_ready_candidate_count:
                    label += f" / {_ready_count_label(variable_ready_candidate_count)}"
                return label
            return "Add variable load device manually"
        if action == "bulk_enable":
            label = (
                "Review managed devices workspace / enable or disable devices"
                f" / {cls._count_label(managed_count, 'managed device')}"
            )
            if attention_count:
                label += f" / {_attention_count_label(attention_count)}"
            return label
        if action == "edit":
            label = f"Edit managed device / {cls._count_label(managed_count, 'managed device')}"
            if attention_count:
                label += f" / {_attention_count_label(attention_count)}"
            return label
        if action == "remove":
            label = f"Remove managed device / {cls._count_label(managed_count, 'managed device')}"
            if attention_count:
                label += f" / {_attention_count_label(attention_count)}"
            return label
        if action == "json":
            return "Advanced JSON editor / recovery"
        return action

    @staticmethod
    def _candidate_picker_role_prefix(
        candidate: dict[str, Any],
        *,
        top_candidate: dict[str, Any] | None,
        review_candidate: dict[str, Any] | None,
        ready_candidate: dict[str, Any] | None,
    ) -> str:
        candidate_id = str(candidate.get("entity_id") or "")
        is_top = bool(candidate_id) and candidate_id == str((top_candidate or {}).get("entity_id") or "")
        is_review = bool(candidate_id) and candidate_id == str((review_candidate or {}).get("entity_id") or "")
        is_ready = bool(candidate_id) and candidate_id == str((ready_candidate or {}).get("entity_id") or "")
        if is_top and is_review:
            return "Currently surfaced, review first"
        if is_top and is_ready:
            return "Currently surfaced, ready next"
        if is_top:
            return "Currently surfaced"
        if is_review:
            return "Review first"
        if is_ready:
            return "Ready next"
        return ""

    @classmethod
    def _candidate_picker_label(
        cls,
        candidate: dict[str, Any],
        *,
        top_candidate: dict[str, Any] | None,
        review_candidate: dict[str, Any] | None,
        ready_candidate: dict[str, Any] | None,
    ) -> str:
        label = str(candidate.get("label") or candidate.get("fallback_label") or candidate.get("entity_id") or "candidate")
        prefix = cls._candidate_picker_role_prefix(
            candidate,
            top_candidate=top_candidate,
            review_candidate=review_candidate,
            ready_candidate=ready_candidate,
        )
        if prefix in {"Review first", "Currently surfaced, review first"}:
            label = label.replace(" | review first |", " |", 1)
            if label.endswith(" | review first"):
                label = label[: -len(" | review first")]
        return f"{prefix}: {label}" if prefix else label

    def _candidate_options(self, *, kind: str | None = None) -> list[selector.SelectOptionDict]:
        candidates = self._device_candidates()
        if kind:
            candidates = [item for item in candidates if item["kind"] == kind]
        top_candidate = candidates[0] if candidates else None
        review_candidate = next(
            (item for item in candidates if candidate_needs_review(assess_candidate(item))),
            None,
        )
        ready_candidate = next(
            (item for item in candidates if not candidate_needs_review(assess_candidate(item))),
            None,
        )
        return [
            selector.SelectOptionDict(
                value=item["entity_id"],
                label=self._candidate_picker_label(
                    item,
                    top_candidate=top_candidate,
                    review_candidate=review_candidate,
                    ready_candidate=ready_candidate,
                ),
            )
            for item in candidates[:100]
        ]

    def _top_candidates_for_kind(self, kind: str, *, limit: int = 3) -> list[dict[str, Any]]:
        return [item for item in self._device_candidates() if item["kind"] == kind][:limit]

    def _candidate_quick_picks(self, kind: str) -> list[dict[str, Any]]:
        ranked = sorted(
            self._top_candidates_for_kind(kind, limit=12),
            key=lambda item: (
                0 if str((self._candidate_summary(item["entity_id"]) or {}).get("fit_confidence")) == "high" else 1,
                0 if str(item.get("domain") or "") == "switch" else 1,
                str(item.get("name") or item.get("entity_id") or ""),
            ),
        )
        quick_picks = ranked[:3]
        top_candidate = ranked[0] if ranked else None
        review_candidate = next(
            (item for item in ranked if candidate_needs_review(assess_candidate(item))),
            None,
        )
        ready_candidate = next(
            (item for item in ranked if not candidate_needs_review(assess_candidate(item))),
            None,
        )

        def _ensure_visible(candidate: dict[str, Any] | None) -> None:
            if not candidate:
                return
            candidate_id = str(candidate.get("entity_id") or "")
            if not candidate_id or any(str(item.get("entity_id") or "") == candidate_id for item in quick_picks):
                return
            protected_ids = {
                str((top_candidate or {}).get("entity_id") or ""),
                str((review_candidate or {}).get("entity_id") or ""),
                str((ready_candidate or {}).get("entity_id") or ""),
            }
            for index in range(len(quick_picks) - 1, -1, -1):
                quick_pick_id = str(quick_picks[index].get("entity_id") or "")
                if quick_pick_id not in protected_ids:
                    quick_picks[index] = candidate
                    return
            if len(quick_picks) < 3:
                quick_picks.append(candidate)

        _ensure_visible(review_candidate)
        _ensure_visible(ready_candidate)
        return quick_picks

    def _source_entity_options(
        self,
        *,
        quantity: str,
        current_entity_id: str | None = None,
        optional: bool = False,
        none_label: str = "Not configured",
        role_key: str | None = None,
    ) -> list[selector.SelectOptionDict]:
        options: list[selector.SelectOptionDict] = []
        seen: set[str] = set()
        all_states = list(self.hass.states.async_all())

        if optional:
            options.append(selector.SelectOptionDict(value="", label=none_label))
            seen.add("")

        if current_entity_id:
            state = self.hass.states.get(current_entity_id)
            current_label = (
                _format_source_candidate_label(current_entity_id, state, role_key, quantity)
                if role_key
                else _format_source_option_label(current_entity_id, state)
            )
            options.append(selector.SelectOptionDict(value=current_entity_id, label=f"Current mapping: {current_label}"))
            seen.add(current_entity_id)

        ranked_states = (
            _rank_source_candidates(all_states, role_key or "", quantity)
            if role_key
            else [(0, str(state.entity_id), state) for state in all_states if str(state.entity_id).split(".", 1)[0] == "sensor" and _state_matches_source_quantity(state, quantity)]
        )

        for _, entity_id, state in ranked_states:
            if entity_id in seen:
                continue
            option_label = (
                _format_source_candidate_label(entity_id, state, role_key, quantity)
                if role_key
                else _format_source_option_label(entity_id, state)
            )
            options.append(selector.SelectOptionDict(value=entity_id, label=option_label))
            seen.add(entity_id)
            if len(options) >= 150:
                break
        return options

    def _source_role_candidates(self, role_key: str, quantity: str, *, limit: int = 3) -> list[str]:
        ranked = _rank_source_candidates(list(self.hass.states.async_all()), role_key, quantity, minimum_score=2)
        return [
            _format_source_candidate_label(entity_id, state, role_key, quantity)
            for _, entity_id, state in ranked[:limit]
        ]

    def _source_candidate_role_specs(self, grid_mode: str) -> list[tuple[str, str]]:
        role_specs: list[tuple[str, str]] = [
            (CONF_SOLAR_POWER_ENTITY, "power"),
            (CONF_SOLAR_ENERGY_ENTITY, "energy"),
        ]
        if grid_mode == GRID_SENSOR_MODE_COMBINED:
            role_specs.extend(
                [
                    (CONF_GRID_IMPORT_POWER_ENTITY, "power"),
                    (CONF_GRID_IMPORT_ENERGY_ENTITY, "energy"),
                ]
            )
        else:
            role_specs.extend(
                [
                    (CONF_GRID_IMPORT_POWER_ENTITY, "power"),
                    (CONF_GRID_EXPORT_POWER_ENTITY, "power"),
                    (CONF_GRID_IMPORT_ENERGY_ENTITY, "energy"),
                    (CONF_GRID_EXPORT_ENERGY_ENTITY, "energy"),
                ]
            )
        role_specs.extend(
            [
                (CONF_HOME_LOAD_POWER_ENTITY, "power"),
                (CONF_BATTERY_SOC_ENTITY, "percent"),
                (CONF_BATTERY_CHARGE_POWER_ENTITY, "power"),
                (CONF_BATTERY_DISCHARGE_POWER_ENTITY, "power"),
            ]
        )
        return role_specs

    @staticmethod
    def _source_role_display_label(role_key: str, grid_mode: str) -> str:
        role_labels = {
            CONF_GRID_IMPORT_POWER_ENTITY: "Combined / net grid power" if grid_mode == GRID_SENSOR_MODE_COMBINED else SOURCE_ROLE_LABELS.get(CONF_GRID_IMPORT_POWER_ENTITY, CONF_GRID_IMPORT_POWER_ENTITY),
            CONF_GRID_IMPORT_ENERGY_ENTITY: "Combined / net grid energy" if grid_mode == GRID_SENSOR_MODE_COMBINED else SOURCE_ROLE_LABELS.get(CONF_GRID_IMPORT_ENERGY_ENTITY, CONF_GRID_IMPORT_ENERGY_ENTITY),
            CONF_HOME_LOAD_POWER_ENTITY: "Home load power (optional)",
            CONF_BATTERY_SOC_ENTITY: "Battery state of charge (optional)",
            CONF_BATTERY_CHARGE_POWER_ENTITY: "Battery charge power (optional)",
            CONF_BATTERY_DISCHARGE_POWER_ENTITY: "Battery discharge power (optional)",
        }
        return role_labels.get(role_key, SOURCE_ROLE_LABELS.get(role_key, role_key))

    def _source_candidate_hint_summary(self, grid_mode: str, *, role_keys: list[str] | None = None) -> str:
        role_specs = self._source_candidate_role_specs(grid_mode)
        if role_keys:
            prioritized = [item for item in role_specs if item[0] in role_keys]
            remaining = [item for item in role_specs if item[0] not in role_keys]
            role_specs = prioritized + remaining

        lines: list[str] = []
        for role_key, quantity in role_specs:
            candidates = self._source_role_candidates(role_key, quantity)
            if not candidates:
                continue
            label = self._source_role_display_label(role_key, grid_mode)
            joined = "; ".join(candidates)
            lines.append(f"- {label}: {joined}")
        return "\n".join(lines) if lines else "- No strong live source candidates were detected from current sensor names, units, and device classes yet."

    def _priority_source_candidate_hint_summary(self, grid_mode: str, role_keys: list[str] | None) -> str:
        if not role_keys:
            return "- No specific blocked source roles are highlighted right now."

        role_specs = [item for item in self._source_candidate_role_specs(grid_mode) if item[0] in role_keys]
        lines: list[str] = []
        for role_key, quantity in role_specs:
            candidates = self._source_role_candidates(role_key, quantity)
            label = self._source_role_display_label(role_key, grid_mode)
            if candidates:
                lines.append(f"- {label}: {'; '.join(candidates)}")
            else:
                lines.append(f"- {label}: no strong live candidates detected yet")
        return "\n".join(lines)

    def _source_role_guide_summary(self, grid_mode: str) -> str:
        guide_lines = [
            "- Solar power: usually a live whole-system PV power sensor, often labelled Solar Power, PV Power, or similar.",
            "- Solar energy: usually the accumulating PV production total, often labelled Yield Total, Energy Production, or Generated Energy.",
        ]
        if grid_mode == GRID_SENSOR_MODE_COMBINED:
            guide_lines.extend(
                [
                    "- Combined / net grid power: use one signed net grid power sensor. Positive values should mean import and negative values should mean export.",
                    "- Combined / net grid energy: use one signed or net grid energy total when available. If your install instead exposes separate import/export energy totals, switch grid mode to Separate.",
                ]
            )
        else:
            guide_lines.extend(
                [
                    "- Grid import power: usually the live import-only sensor, often labelled Grid Import, From Grid, or Purchased Power.",
                    "- Grid export power: usually the live export-only sensor, often labelled Grid Export, To Grid, Feed In, or Returned Power.",
                    "- Grid import energy: often labelled Total Active Energy, Imported Energy, or From Grid.",
                    "- Grid export energy: often labelled Returned Energy, Exported Energy, or To Grid.",
                ]
            )
        guide_lines.extend(
            [
                "- Home load power: usually the whole-home demand sensor, often labelled Home Demand, House Load, or Consumption.",
                "- Battery state of charge: usually the battery percentage sensor, often labelled State of Charge or Battery SOC.",
            ]
        )
        return "\n".join(guide_lines)

    def _candidate_summary(self, entity_id: str | None) -> dict[str, Any] | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        domain = entity_id.split('.', 1)[0] if '.' in entity_id else ''
        kind = DEVICE_KIND_FIXED if domain in DEVICE_CANDIDATE_FIXED_DOMAINS else DEVICE_KIND_VARIABLE
        templates = get_device_templates(kind)
        suggested_template = templates[0] if templates else None
        candidate_fit = assess_candidate(
            {
                "entity_id": entity_id,
                "name": str(state.attributes.get('friendly_name') or entity_id),
                "domain": domain,
                "kind": kind,
                "state": str(state.state),
                "unit": str(state.attributes.get('unit_of_measurement') or ''),
                "device_class": str(state.attributes.get('device_class') or ''),
            }
        )
        confidence = str(candidate_fit.get("confidence") or "medium")
        fit_usefulness = _candidate_usefulness_label(candidate_fit)
        fit_summary = str(candidate_fit.get("summary") or "Looks like a plausible controllable candidate, but review before promotion.")
        warnings: list[str] = list(candidate_fit.get("warnings") or [])

        if domain == 'switch' and kind == DEVICE_KIND_FIXED:
            suggested_template = next((item for item in templates if item.key in {'hot_water', 'smart_plug', 'pool_pump'}), suggested_template)
        if domain in {'number', 'input_number'} and kind == DEVICE_KIND_VARIABLE:
            suggested_template = next((item for item in templates if item.key in {'ev_charger', 'battery_charge_sink'}), suggested_template)
        unit = str(state.attributes.get('unit_of_measurement') or '')
        device_class = str(state.attributes.get('device_class') or '')

        return {
            'entity_id': entity_id,
            'name': str(state.attributes.get('friendly_name') or entity_id),
            'domain': domain,
            'kind': kind,
            'state': str(state.state),
            'unit': unit,
            'device_class': device_class,
            'suggested_template_key': suggested_template.key if suggested_template else None,
            'suggested_template_label': suggested_template.label if suggested_template else 'Custom',
            'suggested_template_description': suggested_template.description if suggested_template else 'Use a custom configuration for this entity.',
            'fit_confidence': confidence,
            'fit_usefulness': fit_usefulness,
            'fit_summary': fit_summary,
            'warnings': warnings,
        }

    def _load_devices(self) -> tuple[list[dict[str, Any]], list[str]]:
        raw_inventory = _entry_default_text(
            self._config_entry,
            CONF_DEVICE_INVENTORY_JSON,
            DEFAULT_DEVICE_INVENTORY_JSON,
        )
        devices, issues = parse_device_configs(raw_inventory)
        return [
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
            for device in devices
        ], issues

    def _managed_workspace_post_save_step(self) -> str:
        if getattr(self, "hass", None) is None:
            return ""
        coordinator = self._coordinator()
        if coordinator is None:
            return ""
        command_center = build_native_command_center_summary(coordinator)
        device_next_step = str(command_center.get("device_next_step") or "").strip()
        if not device_next_step or DEVICES_CONFIGURE_PATH not in device_next_step:
            return ""
        if any(path in device_next_step for path in (SOURCES_CONFIGURE_PATH, POLICY_CONFIGURE_PATH, SUPPORT_CONFIGURE_PATH)):
            return ""
        if any(
            phrase in device_next_step
            for phrase in (
                "review blocked managed devices in the Managed Devices workspace",
                "confirm the active managed-device plan in the Managed Devices workspace",
                "review attention in the Managed Devices workspace",
                "review the Managed Devices workspace, edit device settings, or stage enablement changes",
            )
        ):
            return device_next_step
        return ""

    def _build_device_action_feedback(
        self,
        *,
        action: str,
        devices: list[dict[str, Any]],
        device: dict[str, Any] | None = None,
        previous_device: dict[str, Any] | None = None,
    ) -> dict[str, str] | None:
        managed_count = len(devices)
        enabled_count = sum(1 for item in devices if item.get("enabled", True))
        disabled_count = managed_count - enabled_count
        kind_label = "fixed load" if str((device or previous_device or {}).get("kind")) == DEVICE_KIND_FIXED else "variable load"
        current_name = str((device or {}).get("name") or (previous_device or {}).get("name") or "Managed device")
        blocker_summary = self._device_blocker_summary()
        blocker_lines = [line.strip() for line in blocker_summary.splitlines() if line.strip()]
        blocker_active = any(line.startswith("Before fleet work:") for line in blocker_lines)

        managed_ids = {str(item.get("entity_id")) for item in devices if item.get("entity_id")}
        candidates = (
            discover_candidate_devices(self.hass.states.async_all(), managed_ids)
            if getattr(getattr(self, "hass", None), "states", None) is not None
            else []
        )
        managed_snapshot = self._managed_snapshot_text(devices)
        unmanaged_snapshot = self._unmanaged_snapshot_text(candidates)
        review_candidate = self._review_candidate_focus_text(candidates)
        ready_candidate = self._ready_candidate_focus_text(candidates)

        managed_workspace_follow_through = self._managed_workspace_post_save_step()
        candidate_follow_through = self._post_save_candidate_follow_through(candidates)

        if action == "promote" and device is not None:
            title = "managed-device promotion saved"
            changed = f"Promoted {current_name} into Managed Devices as a {kind_label}."
            next_step = (
                f"Next step: reopen {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, then {candidate_follow_through}."
            )
        elif action == "edit" and device is not None:
            title = "managed-device update saved"
            changed = f"Updated {current_name} in Managed Devices."
            next_step = (
                f"Next step: reopen {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, then {candidate_follow_through}."
            )
        elif action == "remove" and previous_device is not None:
            title = "managed-device removal saved"
            changed = f"Removed {current_name} from Managed Devices."
            next_step = (
                f"Next step: reopen {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace and remaining fleet, then {candidate_follow_through}."
            )
        elif action == "bulk_enable":
            title = "managed-device enablement saved"
            changed = "Saved the Managed Devices enablement review."
            next_step = (
                f"Next step: reopen {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, then {candidate_follow_through}."
            )
        else:
            return None

        if blocker_active:
            next_step = f"Next step: {blocker_lines[0].removeprefix('Before fleet work: ').strip()}"
        elif managed_workspace_follow_through:
            next_step = f"Next step: {managed_workspace_follow_through}"

        fleet_snapshot = f"Fleet now: {managed_count} managed | {enabled_count} enabled | {disabled_count} disabled"
        message_lines = [
            "Zero Net Export managed-device update",
            "",
            changed,
            fleet_snapshot,
            managed_snapshot,
            unmanaged_snapshot,
            f"Review-first unmanaged candidate: {review_candidate}",
            f"Ready-next unmanaged candidate: {ready_candidate}",
        ]
        if blocker_active:
            message_lines.extend([
                "",
                "Blocker-first handoff:",
                *[f"- {line}" for line in blocker_lines],
            ])
        message_lines.extend(
            [
                "",
                f"Primary Managed Devices workspace in Configure: {DEVICES_CONFIGURE_PATH}",
                f"Secondary device-page review path, only after the main fleet step is clear: {DETAILED_MANAGEMENT_PATH}",
                next_step,
            ]
        )
        return {"title": title, "message": "\n".join(message_lines)}

    def _show_device_action_feedback(self, feedback: dict[str, str] | None) -> None:
        if not feedback:
            return
        persistent_notification.async_create(
            self.hass,
            feedback["message"],
            title=f"{self._config_entry.title}: {feedback['title']}",
            notification_id=f"{DOMAIN}_{self._config_entry.entry_id}_managed_device_update",
        )

    async def _save_devices(self, devices: list[dict[str, Any]], *, feedback: dict[str, str] | None = None):
        merged_options = dict(self._config_entry.options)
        merged_options[CONF_DEVICE_INVENTORY_JSON] = _device_options_json(devices)
        self.hass.config_entries.async_update_entry(self._config_entry, options=merged_options)
        await self.hass.config_entries.async_reload(self._config_entry.entry_id)
        self._show_device_action_feedback(feedback)
        return self.async_create_entry(title="", data=merged_options)

    @staticmethod
    def _build_device_payload(user_input: dict[str, Any], kind: str, *, key: str | None = None) -> dict[str, Any]:
        name = str(user_input["name"]).strip()
        payload: dict[str, Any] = {
            "name": name,
            "kind": kind,
            "entity_id": user_input["entity_id"],
            "adapter": ADAPTER_FIXED_TOGGLE if kind == DEVICE_KIND_FIXED else ADAPTER_VARIABLE_NUMBER,
            "nominal_power_w": float(user_input["nominal_power_w"]),
            "priority": int(user_input["priority"]),
            "enabled": bool(user_input.get("enabled", True)),
            "min_on_seconds": int(user_input["min_on_seconds"]),
            "min_off_seconds": int(user_input["min_off_seconds"]),
            "cooldown_seconds": int(user_input["cooldown_seconds"]),
            "max_active_seconds": int(user_input["max_active_seconds"]) or None,
        }
        if key:
            payload["key"] = key
        if kind == DEVICE_KIND_FIXED:
            payload["min_power_w"] = payload["nominal_power_w"]
            payload["max_power_w"] = payload["nominal_power_w"]
            payload["step_w"] = payload["nominal_power_w"]
        else:
            payload["min_power_w"] = float(user_input["min_power_w"])
            payload["max_power_w"] = float(user_input["max_power_w"])
            payload["step_w"] = float(user_input["step_w"])
        return payload

    @staticmethod
    def _device_form_defaults(
        device: dict[str, Any] | None,
        kind: str,
        template_defaults: dict[str, Any] | None = None,
        candidate_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        defaults = {
            "name": "",
            "entity_id": "",
            "nominal_power_w": 2400 if kind == DEVICE_KIND_FIXED else 3600,
            "priority": 100,
            "enabled": True,
            "min_on_seconds": 900 if kind == DEVICE_KIND_FIXED else 300,
            "min_off_seconds": 900 if kind == DEVICE_KIND_FIXED else 60,
            "cooldown_seconds": 60 if kind == DEVICE_KIND_FIXED else 30,
            "max_active_seconds": 14400 if kind == DEVICE_KIND_FIXED else 28800,
            "min_power_w": 1400,
            "max_power_w": 7200,
            "step_w": 100,
        }
        if template_defaults:
            defaults.update(template_defaults)
        if device is None:
            if candidate_summary:
                candidate_name = str(candidate_summary.get("name") or "").strip()
                if candidate_name:
                    defaults["name"] = candidate_name
                confidence = str(candidate_summary.get("fit_confidence") or "")
                domain = str(candidate_summary.get("domain") or "")
                if kind == DEVICE_KIND_FIXED:
                    if confidence == "high":
                        defaults["priority"] = 120 if domain == "switch" else defaults["priority"]
                        defaults["min_on_seconds"] = max(int(defaults["min_on_seconds"]), 900)
                        defaults["min_off_seconds"] = max(int(defaults["min_off_seconds"]), 900)
                    elif confidence == "low":
                        defaults["priority"] = min(int(defaults["priority"]), 60)
                else:
                    if confidence == "high":
                        defaults["priority"] = 50
                        defaults["step_w"] = 100
                        defaults["min_on_seconds"] = max(int(defaults["min_on_seconds"]), 300)
                    elif confidence == "low":
                        defaults["priority"] = 70
                if domain == "light":
                    defaults["priority"] = min(int(defaults["priority"]), 80)
                if domain in {"input_boolean", "input_number"}:
                    defaults["enabled"] = False
            return defaults
        defaults.update(
            {
                "name": device.get("name", defaults["name"]),
                "entity_id": device.get("entity_id", defaults["entity_id"]),
                "nominal_power_w": device.get("nominal_power_w", defaults["nominal_power_w"]),
                "priority": device.get("priority", defaults["priority"]),
                "enabled": device.get("enabled", defaults["enabled"]),
                "min_on_seconds": device.get("min_on_seconds", defaults["min_on_seconds"]),
                "min_off_seconds": device.get("min_off_seconds", defaults["min_off_seconds"]),
                "cooldown_seconds": device.get("cooldown_seconds", defaults["cooldown_seconds"]),
                "max_active_seconds": device.get("max_active_seconds") or 0,
                "min_power_w": device.get("min_power_w", defaults["min_power_w"]),
                "max_power_w": device.get("max_power_w", defaults["max_power_w"]),
                "step_w": device.get("step_w", defaults["step_w"]),
            }
        )
        return defaults

    @staticmethod
    def _default_guidance_text(kind: str, defaults: dict[str, Any]) -> str:
        if kind == DEVICE_KIND_FIXED:
            return (
                f"Starting defaults: {int(defaults.get('nominal_power_w', 0) or 0)} W nominal, priority {int(defaults.get('priority', 0) or 0)}, "
                f"min on {int(defaults.get('min_on_seconds', 0) or 0)} s, min off {int(defaults.get('min_off_seconds', 0) or 0)} s."
            )
        return (
            f"Starting defaults: {int(defaults.get('min_power_w', 0) or 0)} to {int(defaults.get('max_power_w', 0) or 0)} W, "
            f"step {int(defaults.get('step_w', 0) or 0)} W, priority {int(defaults.get('priority', 0) or 0)}."
        )

    def _coordinator(self):
        return self.hass.data.get(DOMAIN, {}).get(self._config_entry.entry_id)

    @staticmethod
    def _format_source_role_names(source_keys: list[str]) -> str:
        named_roles = [SOURCE_ROLE_LABELS.get(key, key) for key in source_keys if key]
        return ", ".join(named_roles[:6]) if named_roles else "None"

    def _source_attention_state(
        self,
        *,
        effective_config: dict[str, Any] | None = None,
        grid_mode: str | None = None,
    ) -> dict[str, Any]:
        effective = effective_config or {**self._config_entry.data, **self._config_entry.options}
        resolved_grid_mode = grid_mode or _grid_mode_default(self._config_entry)
        missing_source_keys = _grid_mode_missing_sources(effective, resolved_grid_mode)
        coordinator = self._coordinator()
        state = getattr(coordinator, "data", None) if coordinator is not None else None
        readiness = build_native_operator_readiness(coordinator) if coordinator is not None else {}
        source_attention = build_source_attention_details(state)
        unavailable_source_keys = source_attention["unavailable_source_keys"]
        stale_source_keys = source_attention["stale_source_keys"]
        blocking_validation_details = summarize_validation_issue_messages(
            state,
            severities={"error"},
            limit=3,
        )
        has_blocking_validation_errors = blocking_validation_details != "None"
        return {
            "coordinator": coordinator,
            "state": state,
            "readiness": readiness,
            "effective_config": effective,
            "validation_details": source_attention["validation_details"],
            "source_diagnostics": source_attention["source_diagnostics"],
            "missing_source_keys": missing_source_keys,
            "unavailable_source_keys": unavailable_source_keys,
            "stale_source_keys": stale_source_keys,
            "blocking_validation_details": blocking_validation_details,
            "has_blocking_validation_errors": has_blocking_validation_errors,
            "has_runtime_source_attention": bool(
                unavailable_source_keys or stale_source_keys or has_blocking_validation_errors
            ),
        }

    def _source_placeholders(
        self,
        *,
        effective_config: dict[str, Any] | None = None,
        grid_mode: str | None = None,
    ) -> dict[str, str]:
        attention = self._source_attention_state(effective_config=effective_config, grid_mode=grid_mode)
        state = attention["state"]
        readiness = attention["readiness"]
        effective = attention["effective_config"]
        missing_source_keys = attention["missing_source_keys"]
        unavailable_source_keys = attention["unavailable_source_keys"]
        stale_source_keys = attention["stale_source_keys"]
        blocking_validation_details = attention["blocking_validation_details"]
        source_attention_roles = build_source_attention_role_summary(state, effective, limit=4)
        validation_issues = list(attention["validation_details"].get("issues", []) or [])
        blocking_validation_issues = [
            issue for issue in validation_issues if str(issue.get("severity", "")).lower() == "error"
        ]
        blocking_fallback_hint = build_source_selector_fallback_hint(validation_issues=blocking_validation_issues)
        missing_fallback_hint = build_source_selector_fallback_hint(role_keys=missing_source_keys)
        runtime_attention_fallback_hint = build_source_selector_fallback_hint(
            role_keys=[*unavailable_source_keys, *stale_source_keys]
        )

        missing_sources = self._format_source_role_names(missing_source_keys)
        unavailable_sources = self._format_source_role_names(unavailable_source_keys)
        stale_sources = self._format_source_role_names(stale_source_keys)
        required_source_keys = _grid_mode_missing_sources({}, grid_mode or _grid_mode_default(self._config_entry))
        required_source_count = len(required_source_keys)
        mapped_required_source_count = max(required_source_count - len(missing_source_keys), 0)
        source_mapping_progress = (
            f"{mapped_required_source_count} of {required_source_count} required roles mapped"
        )
        if missing_source_keys:
            source_mapping_progress += (
                f"; {len(missing_source_keys)} missing required role"
                if len(missing_source_keys) == 1
                else f"; {len(missing_source_keys)} missing required roles"
            )

        source_blocker_parts: list[str] = []
        if missing_source_keys:
            source_blocker_parts.append(
                "1 missing required role"
                if len(missing_source_keys) == 1
                else f"{len(missing_source_keys)} missing required roles"
            )
        if unavailable_source_keys:
            source_blocker_parts.append(
                "1 unavailable mapped role"
                if len(unavailable_source_keys) == 1
                else f"{len(unavailable_source_keys)} unavailable mapped roles"
            )
        if stale_source_keys:
            source_blocker_parts.append(
                "1 stale mapped role"
                if len(stale_source_keys) == 1
                else f"{len(stale_source_keys)} stale mapped roles"
            )
        if blocking_validation_details != "None":
            source_blocker_parts.append("blocking validation errors present")
        source_blocker_summary = "; ".join(source_blocker_parts) or "No blocking source issues right now."

        priority_role_keys = missing_source_keys or unavailable_source_keys or stale_source_keys or _issue_role_keys(
            blocking_validation_issues,
            severities={"error"},
        )

        if missing_source_keys:
            source_health = f"Missing required sources: {missing_sources}"
            source_next_step = build_source_repair_step(missing_source_keys=missing_source_keys)
            if missing_fallback_hint:
                source_next_step += f" {missing_fallback_hint}"
        elif unavailable_source_keys or stale_source_keys:
            issue_parts = []
            if unavailable_source_keys:
                issue_parts.append(f"unavailable: {unavailable_sources}")
            if stale_source_keys:
                issue_parts.append(f"stale: {stale_sources}")
            source_health = "Mapped source roles need attention, " + "; ".join(issue_parts)
            source_next_step = str(
                readiness.get("next_step")
                or build_source_repair_step(
                    unavailable_source_keys=unavailable_source_keys,
                    stale_source_keys=stale_source_keys,
                )
            )
            if runtime_attention_fallback_hint and runtime_attention_fallback_hint not in source_next_step:
                source_next_step += f" {runtime_attention_fallback_hint}"
        elif blocking_validation_details != "None":
            source_health = "Mapped source validation still has blocking errors: " + blocking_validation_details
            source_next_step = str(
                readiness.get("next_step")
                or build_source_repair_step(blocking_validation_details=blocking_validation_details)
            )
            if blocking_fallback_hint and blocking_fallback_hint not in source_next_step:
                source_next_step += f" {blocking_fallback_hint}"
        elif state is None:
            source_health = "Live source health will appear here after the integration loads."
            source_next_step = (
                f"Save source mapping, reload the integration, then reopen {SOURCES_CONFIGURE_PATH} to confirm live source health."
            )
        else:
            source_health = build_live_source_health_summary(state)
            devices, issues = self._load_devices()
            candidates = self._device_candidates()
            review_candidate = next(
                (candidate for candidate in candidates if candidate_needs_review(assess_candidate(candidate))),
                None,
            )
            ready_candidate = next(
                (candidate for candidate in candidates if not candidate_needs_review(assess_candidate(candidate))),
                None,
            )
            primary_candidate = review_candidate or (candidates[0] if candidates else None)
            source_next_step = str(readiness.get("next_step") or "").strip()
            if not source_next_step:
                if issues:
                    source_next_step = (
                        f"Open {DEVICES_CONFIGURE_PATH} to repair the managed-device issues first, then return to Controls once the fleet is ready."
                    )
                elif not devices and primary_candidate:
                    source_next_step = (
                        f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, start in the unmanaged section: {self._top_candidate_focus_text(primary_candidate)}"
                    )
                    if ready_candidate and ready_candidate != primary_candidate:
                        source_next_step += (
                            f", then promote next from the unmanaged section: {self._top_candidate_focus_text(ready_candidate)}"
                        )
                    source_next_step += "."
                elif not devices:
                    source_next_step = "Use the Managed Devices workspace to add the first fixed or variable load manually."
                elif primary_candidate:
                    candidate_focus = self._top_candidate_focus_text(primary_candidate)
                    if review_candidate:
                        source_next_step = (
                            f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, start in the unmanaged section: {candidate_focus}"
                        )
                        if ready_candidate and ready_candidate != primary_candidate:
                            source_next_step += (
                                f", then promote next from the unmanaged section: {self._top_candidate_focus_text(ready_candidate)}"
                            )
                        source_next_step += "."
                    else:
                        source_next_step = (
                            f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, then promote next from the unmanaged section: {candidate_focus}."
                        )
                else:
                    source_next_step = (
                        f"Open {POLICY_CONFIGURE_PATH} to tune target export, reserve, deadband, or live mode."
                    )

        contextual_fallback_hint = (
            blocking_fallback_hint or missing_fallback_hint or runtime_attention_fallback_hint
        )

        return {
            "missing_sources": missing_sources,
            "source_health": source_health,
            "source_mapping_progress": source_mapping_progress,
            "source_blocker_summary": source_blocker_summary,
            "source_next_step": source_next_step,
            "source_repair_step": build_source_repair_step(
                missing_source_keys=missing_source_keys,
                unavailable_source_keys=unavailable_source_keys,
                stale_source_keys=stale_source_keys,
                blocking_validation_details=blocking_validation_details,
            ),
            "source_mapping_summary": build_source_mapping_summary(effective),
            "unavailable_sources": unavailable_sources,
            "stale_sources": stale_sources,
            "source_attention_roles": source_attention_roles,
            "blocking_validation_details": blocking_validation_details,
            "source_fallback_hint": contextual_fallback_hint,
            "priority_source_candidate_hints": self._priority_source_candidate_hint_summary(
                grid_mode or _grid_mode_default(self._config_entry),
                priority_role_keys,
            ),
        }

    def _support_placeholders(self) -> dict[str, str]:
        coordinator = self._coordinator()
        state = getattr(coordinator, "data", None) if coordinator is not None else None
        readiness = build_native_operator_readiness(coordinator) if coordinator is not None else {}
        command_center = build_native_command_center_summary(coordinator) if coordinator is not None else {}
        install_provenance = build_install_provenance()
        source_attention = build_source_attention_details(state)
        unavailable_sources = self._format_source_role_names(source_attention["unavailable_source_keys"])
        stale_sources = self._format_source_role_names(source_attention["stale_source_keys"])
        merged = dict(self._config_entry.data)
        merged.update(self._config_entry.options)
        health_summary = "Integration state not loaded yet"
        if state is not None:
            health_summary = state.health_summary or state.diagnostic_summary or health_summary
        blocking_validation_issues = [
            issue
            for issue in (source_attention["validation_details"].get("issues", []) or [])
            if str(issue.get("severity", "")).lower() == "error"
        ]
        missing_source_keys = [key for key in REQUIRED_SOURCE_KEYS if not merged.get(key)]
        support_fallback_hint = build_source_selector_fallback_hint(
            role_keys=[
                *missing_source_keys,
                *source_attention["unavailable_source_keys"],
                *source_attention["stale_source_keys"],
            ],
            validation_issues=blocking_validation_issues,
        )
        support_grid_mode = merged.get(CONF_GRID_SENSOR_MODE)
        if support_grid_mode not in {GRID_SENSOR_MODE_COMBINED, GRID_SENSOR_MODE_SEPARATE}:
            support_grid_mode = _infer_grid_sensor_mode(merged)
        support_blocking_role_keys = [
            *missing_source_keys,
            *source_attention["unavailable_source_keys"],
            *source_attention["stale_source_keys"],
            *_issue_role_keys(blocking_validation_issues, severities={"error"}),
        ]
        support_candidate_hints = self._source_candidate_hint_summary(
            support_grid_mode,
            role_keys=support_blocking_role_keys,
        )
        support_priority_candidate_hints = self._priority_source_candidate_hint_summary(
            support_grid_mode,
            support_blocking_role_keys,
        )
        support_next_step = str(readiness.get("next_step") or "").strip()
        if not support_next_step and not install_provenance.get("live_validation_safe"):
            support_next_step = build_install_repair_step(install_provenance)
        if not support_next_step and (
            missing_source_keys
            or source_attention["unavailable_source_keys"]
            or source_attention["stale_source_keys"]
            or blocking_validation_issues
        ):
            support_next_step = build_source_repair_step(
                missing_source_keys=missing_source_keys,
                unavailable_source_keys=source_attention["unavailable_source_keys"],
                stale_source_keys=source_attention["stale_source_keys"],
                blocking_validation_details=summarize_validation_issue_messages(state, severities={"error"}, limit=3),
            )
        if not support_next_step:
            support_next_step = (
                f"Open {SUPPORT_CONFIGURE_PATH} to confirm the current blocker, then use "
                f"{DIAGNOSTICS_DEVICE_ACTIONS_PATH} or Settings -> Repairs if deeper triage is still needed."
            )
        support_install_consistency = build_install_consistency_summary(install_provenance)
        support_install_fingerprint_summary = build_install_fingerprint_summary(install_provenance)
        support_install_next_step = (
            "Exact-build trust currently looks good. Use the device-page diagnostics snapshot only if you need the full install evidence."
            if install_provenance.get("live_validation_safe")
            else build_install_repair_step(install_provenance)
        )
        return {
            "support_status": readiness.get("summary") or health_summary,
            "support_next_step": support_next_step,
            "support_path": SUPPORT_CONFIGURE_PATH,
            "sources_path": SOURCES_CONFIGURE_PATH,
            "devices_path": DEVICES_CONFIGURE_PATH,
            "policy_path": POLICY_CONFIGURE_PATH,
            "mode_path": MODE_CONTROL_PATH,
            "readiness_phase": str(readiness.get("phase") or "unknown"),
            "health_status": health_summary,
            "support_source_mapping_summary": build_source_mapping_summary(merged),
            "support_unavailable_sources": unavailable_sources or "None",
            "support_stale_sources": stale_sources or "None",
            "support_source_attention_roles": build_source_attention_role_summary(state, merged, limit=4),
            "support_attention_summary": build_source_attention_summary(state, merged, limit=4),
            "support_blocking_details": summarize_validation_issue_messages(state, severities={"error"}, limit=3),
            "support_source_repair_step": build_source_repair_step(
                missing_source_keys=missing_source_keys,
                unavailable_source_keys=source_attention["unavailable_source_keys"],
                stale_source_keys=source_attention["stale_source_keys"],
                blocking_validation_details=summarize_validation_issue_messages(state, severities={"error"}, limit=3),
            ),
            "support_fallback_hint": support_fallback_hint or "Not needed right now.",
            "support_install_status": str(install_provenance.get("summary") or "Installed package provenance unavailable"),
            "support_install_consistency": support_install_consistency,
            "support_install_next_step": support_install_next_step,
            "support_install_snapshot_path": f"{INTEGRATION_DEVICE_PATH} -> Review diagnostics snapshot",
            "support_install_fingerprint_summary": support_install_fingerprint_summary,
            "support_candidate_hints": support_candidate_hints,
            "support_priority_candidate_hints": support_priority_candidate_hints,
            "recommended_section": str(command_center.get("recommended_section") or SUPPORT_SECTION_LABEL),
            "recommended_path": str(command_center.get("recommended_path") or SUPPORT_CONFIGURE_PATH),
            "next_action_summary": str(
                command_center.get("next_action_summary")
                or readiness.get("next_step")
                or f"Review the current blocker, then follow the recommended native path under {PRIMARY_CONFIGURE_PATH}."
            ),
        }

    async def async_step_init(self, user_input=None):
        command_center = build_native_command_center_summary(self._coordinator())

        mode_label, mode_description = _live_mode_details(self._coordinator())
        placeholders = {
            "configure_path": PRIMARY_CONFIGURE_PATH,
            "headline_decision": command_center["headline_decision"],
            "alert_summary": command_center["alert_summary"],
            "energy_state_summary": command_center["energy_state_summary"],
            "control_decision_summary": command_center["control_decision_summary"],
            "control_outcome_summary": command_center["control_outcome_summary"],
            "fleet_activity_summary": command_center["fleet_activity_summary"],
            "source_status": command_center["source_status"],
            "source_attention_summary": command_center["source_attention_summary"],
            "source_attention_roles": command_center["source_attention_roles"],
            "unavailable_sources": command_center["unavailable_sources"],
            "stale_sources": command_center["stale_sources"],
            "source_mapping_summary": command_center["source_mapping_summary"],
            "install_status": command_center["install_status"],
            "install_consistency": command_center["install_consistency"],
            "install_fingerprint_summary": command_center["install_fingerprint_summary"],
            "device_status": command_center["device_status"],
            "device_next_step": command_center["device_next_step"],
            "policy_status": command_center["policy_status"],
            "policy_readiness": command_center["policy_readiness"],
            "recommended_section": command_center["recommended_section"],
            "recommended_path": command_center["recommended_path"],
            "sources_path": SOURCES_CONFIGURE_PATH,
            "devices_path": DEVICES_CONFIGURE_PATH,
            "policy_path": POLICY_CONFIGURE_PATH,
            "mode_path": MODE_CONTROL_PATH,
            "current_mode": mode_label,
            "mode_summary": mode_description,
            "next_action_summary": command_center["next_action_summary"],
            "source_repair_step": command_center.get("source_repair_step") or build_source_repair_step(),
            "recommended_menu_hint": (
                f"The first menu item below now matches the recommended next section: {command_center['recommended_section']}."
            ),
        }
        placeholders.update(self._support_placeholders())

        return self.async_show_menu(
            step_id="init",
            menu_options=_command_center_menu_options(command_center["recommended_section"]),
            description_placeholders=placeholders,
        )

    async def async_step_native_setup(self, user_input=None):
        current_mode = self._pending_grid_sensor_mode or _grid_mode_default(self._config_entry)
        if user_input is not None:
            self._pending_grid_sensor_mode = user_input[CONF_GRID_SENSOR_MODE]
            return await self.async_step_native_setup_sources()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_GRID_SENSOR_MODE,
                    default=current_mode,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=GRID_SENSOR_MODE_COMBINED, label="Combined / net sensors"),
                            selector.SelectOptionDict(value=GRID_SENSOR_MODE_SEPARATE, label="Separate import and export sensors"),
                        ],
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )

        effective_config = dict(self._config_entry.data)
        effective_config.update(self._config_entry.options)
        source_placeholders = self._source_placeholders(effective_config=effective_config, grid_mode=current_mode)
        return self.async_show_form(
            step_id="native_setup",
            data_schema=schema,
            errors={},
            description_placeholders={
                "configure_path": SOURCES_CONFIGURE_PATH,
                "sources_path": SOURCES_CONFIGURE_PATH,
                "policy_path": POLICY_CONFIGURE_PATH,
                "mode_path": MODE_CONTROL_PATH,
                "devices_path": DEVICES_CONFIGURE_PATH,
                "support_path": SUPPORT_CONFIGURE_PATH,
                **source_placeholders,
            },
        )

    async def async_step_native_setup_sources(self, user_input=None):
        errors: dict[str, str] = {}
        grid_mode = self._pending_grid_sensor_mode or _grid_mode_default(self._config_entry)
        source_placeholders: dict[str, str] | None = None

        if user_input is not None:
            merged_data = dict(self._config_entry.data)
            merged_options = dict(self._config_entry.options)

            merged_data[CONF_SOLAR_POWER_ENTITY] = _normalize_entity_selector_input(user_input, CONF_SOLAR_POWER_ENTITY)
            merged_data[CONF_SOLAR_ENERGY_ENTITY] = _normalize_entity_selector_input(user_input, CONF_SOLAR_ENERGY_ENTITY)
            merged_data[CONF_HOME_LOAD_POWER_ENTITY] = _normalize_entity_selector_input(user_input, CONF_HOME_LOAD_POWER_ENTITY)
            merged_data[CONF_BATTERY_SOC_ENTITY] = (
                _normalize_entity_selector_input(user_input, BATTERY_SOC_FALLBACK_KEY)
                or _normalize_entity_selector_input(user_input, CONF_BATTERY_SOC_ENTITY)
            )
            merged_data[CONF_BATTERY_CHARGE_POWER_ENTITY] = _normalize_entity_selector_input(user_input, CONF_BATTERY_CHARGE_POWER_ENTITY)
            merged_data[CONF_BATTERY_DISCHARGE_POWER_ENTITY] = _normalize_entity_selector_input(user_input, CONF_BATTERY_DISCHARGE_POWER_ENTITY)

            if grid_mode == GRID_SENSOR_MODE_COMBINED:
                combined_power = _normalize_entity_selector_input(user_input, "grid_power_entity")
                combined_energy = (
                    _normalize_entity_selector_input(user_input, COMBINED_GRID_ENERGY_FALLBACK_KEY)
                    or _normalize_entity_selector_input(user_input, "grid_energy_entity")
                )
                merged_data[CONF_GRID_IMPORT_POWER_ENTITY] = _build_derived_binding(DERIVED_SOURCE_MODE_POSITIVE, combined_power)
                merged_data[CONF_GRID_EXPORT_POWER_ENTITY] = _build_derived_binding(DERIVED_SOURCE_MODE_NEGATIVE_ABS, combined_power)
                merged_data[CONF_GRID_IMPORT_ENERGY_ENTITY] = _build_derived_binding(DERIVED_SOURCE_MODE_POSITIVE, combined_energy)
                merged_data[CONF_GRID_EXPORT_ENERGY_ENTITY] = _build_derived_binding(DERIVED_SOURCE_MODE_NEGATIVE_ABS, combined_energy)
            else:
                merged_data[CONF_GRID_IMPORT_POWER_ENTITY] = _normalize_entity_selector_input(user_input, CONF_GRID_IMPORT_POWER_ENTITY)
                merged_data[CONF_GRID_EXPORT_POWER_ENTITY] = _normalize_entity_selector_input(user_input, CONF_GRID_EXPORT_POWER_ENTITY)
                merged_data[CONF_GRID_IMPORT_ENERGY_ENTITY] = _normalize_entity_selector_input(user_input, CONF_GRID_IMPORT_ENERGY_ENTITY)
                merged_data[CONF_GRID_EXPORT_ENERGY_ENTITY] = _normalize_entity_selector_input(user_input, CONF_GRID_EXPORT_ENERGY_ENTITY)

            merged_options[CONF_GRID_SENSOR_MODE] = grid_mode

            issues = validate_configured_entities(
                self.hass,
                merged_data,
                _source_specs_from_config(merged_data),
            )
            blocking_issues = [issue for issue in issues if issue.severity == "error"]
            if blocking_issues:
                errors["base"] = "source_entities_invalid"
                issue_role_keys = _issue_role_keys(blocking_issues, severities={"error"})
                missing_source_keys = _grid_mode_missing_sources(merged_data, grid_mode)
                source_fallback_hint = build_source_selector_fallback_hint(role_keys=issue_role_keys)
                source_placeholders = {
                    "missing_sources": self._format_source_role_names(missing_source_keys),
                    "source_health": (
                        "Source mapping still has blocking validation errors: "
                        + _summarize_issue_messages(blocking_issues, severities={"error"}, limit=3)
                    ),
                    "source_next_step": (
                        f"Open {SOURCES_CONFIGURE_PATH}, then repair these highlighted source roles: {self._format_source_role_names(issue_role_keys)}. "
                        f"{source_fallback_hint}"
                        if issue_role_keys
                        else f"Open {SOURCES_CONFIGURE_PATH}, repair the highlighted source roles, then save and reload the integration."
                    ),
                    "source_mapping_summary": build_source_mapping_summary(merged_data),
                    "unavailable_sources": "None",
                    "stale_sources": "None",
                    "source_attention_roles": self._format_source_role_names(issue_role_keys),
                    "blocking_validation_details": _summarize_issue_messages(blocking_issues, severities={"error"}, limit=4),
                    "source_fallback_hint": source_fallback_hint,
                    "priority_source_candidate_hints": self._priority_source_candidate_hint_summary(
                        grid_mode,
                        issue_role_keys,
                    ),
                }
            else:
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data=merged_data,
                    options=merged_options,
                )
                await self.hass.config_entries.async_reload(self._config_entry.entry_id)
                self._pending_grid_sensor_mode = None
                return self.async_create_entry(title="", data=merged_options)

        grid_import_power_raw = _entry_default_text(self._config_entry, CONF_GRID_IMPORT_POWER_ENTITY, "")
        grid_import_energy_raw = _entry_default_text(self._config_entry, CONF_GRID_IMPORT_ENERGY_ENTITY, "")
        source_defaults = {
            CONF_SOLAR_POWER_ENTITY: _entry_default_text(self._config_entry, CONF_SOLAR_POWER_ENTITY, ""),
            CONF_SOLAR_ENERGY_ENTITY: _entry_default_text(self._config_entry, CONF_SOLAR_ENERGY_ENTITY, ""),
            "grid_power_entity": _selector_entity_default(grid_import_power_raw, allow_derived=True),
            "grid_energy_entity": _selector_entity_default(grid_import_energy_raw, allow_derived=True),
            COMBINED_GRID_ENERGY_FALLBACK_KEY: "",
            CONF_GRID_IMPORT_POWER_ENTITY: _selector_entity_default(
                _entry_default_text(self._config_entry, CONF_GRID_IMPORT_POWER_ENTITY, "")
            ),
            CONF_GRID_EXPORT_POWER_ENTITY: _selector_entity_default(
                _entry_default_text(self._config_entry, CONF_GRID_EXPORT_POWER_ENTITY, "")
            ),
            CONF_GRID_IMPORT_ENERGY_ENTITY: _selector_entity_default(
                _entry_default_text(self._config_entry, CONF_GRID_IMPORT_ENERGY_ENTITY, "")
            ),
            CONF_GRID_EXPORT_ENERGY_ENTITY: _selector_entity_default(
                _entry_default_text(self._config_entry, CONF_GRID_EXPORT_ENERGY_ENTITY, "")
            ),
            CONF_HOME_LOAD_POWER_ENTITY: _entry_default_text(self._config_entry, CONF_HOME_LOAD_POWER_ENTITY, ""),
            CONF_BATTERY_SOC_ENTITY: _entry_default_text(self._config_entry, CONF_BATTERY_SOC_ENTITY, ""),
            BATTERY_SOC_FALLBACK_KEY: "",
            CONF_BATTERY_CHARGE_POWER_ENTITY: _entry_default_text(self._config_entry, CONF_BATTERY_CHARGE_POWER_ENTITY, ""),
            CONF_BATTERY_DISCHARGE_POWER_ENTITY: _entry_default_text(self._config_entry, CONF_BATTERY_DISCHARGE_POWER_ENTITY, ""),
        }
        if user_input is None and grid_mode != GRID_SENSOR_MODE_COMBINED:
            all_states = list(self.hass.states.async_all())
            suggested_defaults = {
                CONF_SOLAR_POWER_ENTITY: _best_source_candidate_entity(all_states, CONF_SOLAR_POWER_ENTITY, "power"),
                CONF_SOLAR_ENERGY_ENTITY: _best_source_candidate_entity(all_states, CONF_SOLAR_ENERGY_ENTITY, "energy"),
                CONF_GRID_IMPORT_POWER_ENTITY: _best_source_candidate_entity(all_states, CONF_GRID_IMPORT_POWER_ENTITY, "power"),
                CONF_GRID_EXPORT_POWER_ENTITY: _best_source_candidate_entity(all_states, CONF_GRID_EXPORT_POWER_ENTITY, "power"),
                CONF_GRID_IMPORT_ENERGY_ENTITY: _best_source_candidate_entity(all_states, CONF_GRID_IMPORT_ENERGY_ENTITY, "energy"),
                CONF_GRID_EXPORT_ENERGY_ENTITY: _best_source_candidate_entity(all_states, CONF_GRID_EXPORT_ENERGY_ENTITY, "energy"),
            }
            for key, suggestion in suggested_defaults.items():
                if not source_defaults.get(key) and suggestion:
                    source_defaults[key] = suggestion
        if user_input is not None:
            for key in (
                CONF_SOLAR_POWER_ENTITY,
                CONF_SOLAR_ENERGY_ENTITY,
                "grid_power_entity",
                "grid_energy_entity",
                COMBINED_GRID_ENERGY_FALLBACK_KEY,
                CONF_GRID_IMPORT_POWER_ENTITY,
                CONF_GRID_EXPORT_POWER_ENTITY,
                CONF_GRID_IMPORT_ENERGY_ENTITY,
                CONF_GRID_EXPORT_ENERGY_ENTITY,
                CONF_HOME_LOAD_POWER_ENTITY,
                CONF_BATTERY_SOC_ENTITY,
                BATTERY_SOC_FALLBACK_KEY,
                CONF_BATTERY_CHARGE_POWER_ENTITY,
                CONF_BATTERY_DISCHARGE_POWER_ENTITY,
            ):
                if key in user_input:
                    source_defaults[key] = _normalize_entity_selector_input(user_input, key) or ""

        power_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor"], device_class=["power"])
        )
        energy_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor"], device_class=["energy"])
        )
        combined_energy_options = self._source_entity_options(
            quantity="energy",
            current_entity_id=source_defaults["grid_energy_entity"] or None,
            optional=True,
            none_label="Select combined / net grid energy entity",
            role_key=CONF_GRID_IMPORT_ENERGY_ENTITY,
        )
        battery_soc_options = self._source_entity_options(
            quantity="percent",
            current_entity_id=source_defaults[CONF_BATTERY_SOC_ENTITY] or None,
            optional=True,
            none_label="Battery SOC not configured",
            role_key=CONF_BATTERY_SOC_ENTITY,
        )

        fields: dict[Any, Any] = {
            vol.Required(
                CONF_SOLAR_POWER_ENTITY,
                default=source_defaults[CONF_SOLAR_POWER_ENTITY],
            ): power_selector,
            vol.Required(
                CONF_SOLAR_ENERGY_ENTITY,
                default=source_defaults[CONF_SOLAR_ENERGY_ENTITY],
            ): energy_selector,
        }
        if grid_mode == GRID_SENSOR_MODE_COMBINED:
            fields[
                vol.Required(
                    "grid_power_entity",
                    default=source_defaults["grid_power_entity"],
                )
            ] = power_selector
            fields[
                vol.Optional(
                    "grid_energy_entity",
                    default=source_defaults["grid_energy_entity"],
                )
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=combined_energy_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
            fields[
                vol.Optional(
                    COMBINED_GRID_ENERGY_FALLBACK_KEY,
                    default=source_defaults[COMBINED_GRID_ENERGY_FALLBACK_KEY],
                )
            ] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            )
        else:
            fields[
                vol.Required(
                    CONF_GRID_IMPORT_POWER_ENTITY,
                    default=source_defaults[CONF_GRID_IMPORT_POWER_ENTITY],
                )
            ] = power_selector
            fields[
                vol.Required(
                    CONF_GRID_EXPORT_POWER_ENTITY,
                    default=source_defaults[CONF_GRID_EXPORT_POWER_ENTITY],
                )
            ] = power_selector
            fields[
                vol.Required(
                    CONF_GRID_IMPORT_ENERGY_ENTITY,
                    default=source_defaults[CONF_GRID_IMPORT_ENERGY_ENTITY],
                )
            ] = energy_selector
            fields[
                vol.Required(
                    CONF_GRID_EXPORT_ENERGY_ENTITY,
                    default=source_defaults[CONF_GRID_EXPORT_ENERGY_ENTITY],
                )
            ] = energy_selector
        fields[
            vol.Optional(
                CONF_HOME_LOAD_POWER_ENTITY,
                default=source_defaults[CONF_HOME_LOAD_POWER_ENTITY],
            )
        ] = power_selector
        fields[
            vol.Optional(
                CONF_BATTERY_SOC_ENTITY,
                default=source_defaults[CONF_BATTERY_SOC_ENTITY],
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=battery_soc_options,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
        fields[
            vol.Optional(
                BATTERY_SOC_FALLBACK_KEY,
                default=source_defaults[BATTERY_SOC_FALLBACK_KEY],
            )
        ] = selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        )
        fields[
            vol.Optional(
                CONF_BATTERY_CHARGE_POWER_ENTITY,
                default=source_defaults[CONF_BATTERY_CHARGE_POWER_ENTITY],
            )
        ] = power_selector
        fields[
            vol.Optional(
                CONF_BATTERY_DISCHARGE_POWER_ENTITY,
                default=source_defaults[CONF_BATTERY_DISCHARGE_POWER_ENTITY],
            )
        ] = power_selector
        schema = vol.Schema(fields)

        if source_placeholders is None:
            effective_config = dict(self._config_entry.data)
            effective_config.update(self._config_entry.options)
            source_placeholders = self._source_placeholders(effective_config=effective_config, grid_mode=grid_mode)
        source_candidate_hints = self._source_candidate_hint_summary(grid_mode)
        grid_mapping_note = (
            "Combined / net mode reuses one signed grid power sensor and one signed or net grid energy sensor to derive both grid import and grid export roles."
            if grid_mode == GRID_SENSOR_MODE_COMBINED
            else "Separate mode expects distinct import and export power and energy sensors from Home Assistant."
        )
        fallback_guidance = source_placeholders.get("source_fallback_hint") or (
            "Combined / net grid energy and battery SOC now use native dropdowns to reduce Home Assistant selector validation failures on some installs. If Home Assistant still rejects a valid selection, clear that selector, paste the same entity ID into the matching fallback field below, then save again."
        )
        return self.async_show_form(
            step_id="native_setup_sources",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "grid_mode": "Combined / net sensors" if grid_mode == GRID_SENSOR_MODE_COMBINED else "Separate import and export sensors",
                "configure_path": SOURCES_CONFIGURE_PATH,
                "sources_path": SOURCES_CONFIGURE_PATH,
                "policy_path": POLICY_CONFIGURE_PATH,
                "mode_path": MODE_CONTROL_PATH,
                "devices_path": DEVICES_CONFIGURE_PATH,
                "support_path": SUPPORT_CONFIGURE_PATH,
                "grid_mapping_note": grid_mapping_note,
                "fallback_guidance": fallback_guidance,
                "source_candidate_hints": source_candidate_hints,
                "source_role_guide": self._source_role_guide_summary(grid_mode),
                **source_placeholders,
            },
        )

    def _device_next_step(self, devices: list[dict[str, Any]], issues: list[str], candidates: list[dict[str, Any]]) -> str:
        coordinator = self._coordinator()
        if coordinator is not None:
            command_center = build_native_command_center_summary(coordinator)
            recommended_section = str(command_center.get("recommended_section") or "").strip()
            if recommended_section and recommended_section != DEVICES_SECTION_LABEL:
                blocker_next_step = str(
                    command_center.get("next_action_summary")
                    or command_center.get("device_next_step")
                    or ""
                ).strip()
                if blocker_next_step:
                    return blocker_next_step

            device_blocker_step = str(command_center.get("device_next_step") or "").strip()
            if any(
                path in device_blocker_step
                for path in (SOURCES_CONFIGURE_PATH, POLICY_CONFIGURE_PATH, SUPPORT_CONFIGURE_PATH)
            ):
                return device_blocker_step
            if any(
                phrase in device_blocker_step
                for phrase in (
                    "review blocked managed devices in the Managed Devices workspace",
                    "confirm the active managed-device plan in the Managed Devices workspace",
                    "review attention in the Managed Devices workspace",
                )
            ):
                return device_blocker_step

        top_candidate = candidates[0] if candidates else None
        review_candidate = next(
            (candidate for candidate in (candidates or []) if candidate_needs_review(assess_candidate(candidate))),
            None,
        )
        ready_candidate = next(
            (candidate for candidate in (candidates or []) if not candidate_needs_review(assess_candidate(candidate))),
            None,
        )
        primary_candidate = review_candidate or top_candidate
        if issues:
            return "Repair the managed-device issues first, then return here to review enablement or add another load."
        if not devices and primary_candidate:
            next_step = (
                f"Start by reviewing {self._top_candidate_focus_text(primary_candidate)} through the matching promotion action below, then save it into Managed Devices"
            )
            if ready_candidate and ready_candidate != primary_candidate:
                next_step += (
                    f", then promote next from the unmanaged section: {self._top_candidate_focus_text(ready_candidate)}"
                )
            return next_step + "."
        if not devices:
            return "Use the Managed Devices workspace to add the first fixed or variable load manually."
        if primary_candidate:
            candidate_focus = self._top_candidate_focus_text(primary_candidate)
            if review_candidate:
                next_step = (
                    f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, start in the unmanaged section: {candidate_focus}"
                )
                if ready_candidate and ready_candidate != primary_candidate:
                    next_step += (
                        f", then promote next from the unmanaged section: {self._top_candidate_focus_text(ready_candidate)}"
                    )
                return next_step + "."
            return (
                f"Open {DEVICES_CONFIGURE_PATH} to review the Managed Devices workspace, then promote next from the unmanaged section: {candidate_focus}."
            )
        return "Use the Managed Devices workspace to stage enablement, or edit an existing device if the current fleet still needs tuning."

    def _detailed_management_summary(self) -> str:
        command_center = build_native_command_center_summary(self._coordinator())
        return str(
            command_center.get("detailed_management_summary")
            or f"Use {DETAILED_MANAGEMENT_PATH} as the secondary device-page review path for deeper managed-device review."
        )

    async def async_step_devices(self, user_input=None):
        devices, issues = self._load_devices()
        display_devices = _overlay_runtime_device_details(devices, self._coordinator())
        candidates = self._device_candidates()
        if user_input is not None:
            choice = user_input.get("device_action")
            if choice == "add_fixed":
                self._pending_device_kind = DEVICE_KIND_FIXED
                self._pending_device_key = None
                self._pending_device_template_key = None
                self._pending_candidate_entity_id = None
                self._pending_candidate_summary = None
                return await self.async_step_device_pick_candidate()
            if choice == "add_variable":
                self._pending_device_kind = DEVICE_KIND_VARIABLE
                self._pending_device_key = None
                self._pending_device_template_key = None
                self._pending_candidate_entity_id = None
                self._pending_candidate_summary = None
                return await self.async_step_device_pick_candidate()
            if choice == "bulk_enable" and devices:
                return await self.async_step_device_bulk_enable()
            if choice == "edit" and devices:
                return await self.async_step_device_edit_pick()
            if choice == "remove" and devices:
                return await self.async_step_device_remove()
            if choice == "json":
                return await self.async_step_devices_json()

        fixed_candidates = [item for item in candidates if item['kind'] == DEVICE_KIND_FIXED]
        variable_candidates = [item for item in candidates if item['kind'] == DEVICE_KIND_VARIABLE]
        fixed_review_candidate_count = sum(
            1 for item in fixed_candidates if candidate_needs_review(assess_candidate(item))
        )
        variable_review_candidate_count = sum(
            1 for item in variable_candidates if candidate_needs_review(assess_candidate(item))
        )
        fixed_ready_candidate_count = max(len(fixed_candidates) - fixed_review_candidate_count, 0)
        variable_ready_candidate_count = max(len(variable_candidates) - variable_review_candidate_count, 0)
        attention_count = sum(1 for device in display_devices if self._device_needs_attention(device))
        choices = [
            selector.SelectOptionDict(
                value="add_fixed",
                label=self._device_action_label(
                    "add_fixed",
                    managed_count=len(devices),
                    attention_count=attention_count,
                    fixed_candidate_count=len(fixed_candidates),
                    variable_candidate_count=len(variable_candidates),
                    fixed_review_candidate_count=fixed_review_candidate_count,
                    variable_review_candidate_count=variable_review_candidate_count,
                    fixed_ready_candidate_count=fixed_ready_candidate_count,
                    variable_ready_candidate_count=variable_ready_candidate_count,
                ),
            ),
            selector.SelectOptionDict(
                value="add_variable",
                label=self._device_action_label(
                    "add_variable",
                    managed_count=len(devices),
                    attention_count=attention_count,
                    fixed_candidate_count=len(fixed_candidates),
                    variable_candidate_count=len(variable_candidates),
                    fixed_review_candidate_count=fixed_review_candidate_count,
                    variable_review_candidate_count=variable_review_candidate_count,
                    fixed_ready_candidate_count=fixed_ready_candidate_count,
                    variable_ready_candidate_count=variable_ready_candidate_count,
                ),
            ),
        ]
        if devices:
            choices.append(
                selector.SelectOptionDict(
                    value="bulk_enable",
                    label=self._device_action_label(
                        "bulk_enable",
                        managed_count=len(devices),
                        attention_count=attention_count,
                        fixed_candidate_count=len(fixed_candidates),
                        variable_candidate_count=len(variable_candidates),
                        fixed_review_candidate_count=fixed_review_candidate_count,
                        variable_review_candidate_count=variable_review_candidate_count,
                        fixed_ready_candidate_count=fixed_ready_candidate_count,
                        variable_ready_candidate_count=variable_ready_candidate_count,
                    ),
                )
            )
            choices.append(
                selector.SelectOptionDict(
                    value="edit",
                    label=self._device_action_label(
                        "edit",
                        managed_count=len(devices),
                        attention_count=attention_count,
                        fixed_candidate_count=len(fixed_candidates),
                        variable_candidate_count=len(variable_candidates),
                        fixed_review_candidate_count=fixed_review_candidate_count,
                        variable_review_candidate_count=variable_review_candidate_count,
                        fixed_ready_candidate_count=fixed_ready_candidate_count,
                        variable_ready_candidate_count=variable_ready_candidate_count,
                    ),
                )
            )
            choices.append(
                selector.SelectOptionDict(
                    value="remove",
                    label=self._device_action_label(
                        "remove",
                        managed_count=len(devices),
                        attention_count=attention_count,
                        fixed_candidate_count=len(fixed_candidates),
                        variable_candidate_count=len(variable_candidates),
                        fixed_review_candidate_count=fixed_review_candidate_count,
                        variable_review_candidate_count=variable_review_candidate_count,
                        fixed_ready_candidate_count=fixed_ready_candidate_count,
                        variable_ready_candidate_count=variable_ready_candidate_count,
                    ),
                )
            )
        choices.append(
            selector.SelectOptionDict(
                value="json",
                label=self._device_action_label(
                    "json",
                    managed_count=len(devices),
                    attention_count=attention_count,
                    fixed_candidate_count=len(fixed_candidates),
                    variable_candidate_count=len(variable_candidates),
                    fixed_review_candidate_count=fixed_review_candidate_count,
                    variable_review_candidate_count=variable_review_candidate_count,
                    fixed_ready_candidate_count=fixed_ready_candidate_count,
                    variable_ready_candidate_count=variable_ready_candidate_count,
                ),
            )
        )
        summary = "\n".join(self._fleet_summary_lines(display_devices))
        workspace_placeholders = self._managed_devices_workspace_placeholders(display_devices, candidates)
        managed_snapshot = workspace_placeholders["managed_snapshot"]
        unmanaged_snapshot = workspace_placeholders["unmanaged_snapshot"]
        candidate_summary = workspace_placeholders["candidate_summary"]
        fixed_candidate_summary = workspace_placeholders["fixed_candidate_summary"]
        variable_candidate_summary = workspace_placeholders["variable_candidate_summary"]
        top_candidate = candidates[0] if candidates else None
        device_next_step = self._device_next_step(display_devices, issues, candidates)
        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(
                {
                    vol.Required("device_action"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=choices, mode=selector.SelectSelectorMode.LIST)
                    )
                }
            ),
            errors={"base": "device_inventory_invalid"} if issues else {},
            description_placeholders={
                "configure_path": DEVICES_CONFIGURE_PATH,
                "device_count": str(len(devices)),
                "device_summary": summary,
                "managed_snapshot": managed_snapshot,
                "candidate_count": str(len(candidates)),
                "unmanaged_snapshot": unmanaged_snapshot,
                "candidate_summary": candidate_summary,
                "fixed_candidate_count": str(len(fixed_candidates)),
                "fixed_candidate_summary": fixed_candidate_summary,
                "variable_candidate_count": str(len(variable_candidates)),
                "variable_candidate_summary": variable_candidate_summary,
                "top_candidate": self._top_candidate_focus_text(top_candidate),
                "review_candidate": self._review_candidate_focus_text(candidates),
                "ready_candidate": self._ready_candidate_focus_text(candidates),
                "device_next_step": device_next_step,
                "device_blocker_summary": self._device_blocker_summary(),
                "detailed_management_summary": self._detailed_management_summary(),
                "device_issues": "\n".join(f"- {issue}" for issue in issues[:6]) if issues else "None",
            },
        )

    async def async_step_device_pick_candidate(self, user_input=None):
        kind = self._pending_device_kind or DEVICE_KIND_FIXED
        quick_picks = self._candidate_quick_picks(kind)
        options = self._candidate_options(kind=kind)
        if user_input is not None:
            quick_pick = str(user_input.get("quick_pick") or "")
            if quick_pick == MANUAL_CANDIDATE_SELECTION:
                self._pending_candidate_entity_id = None
                self._pending_candidate_summary = None
                self._pending_device_template_key = None
                return await self.async_step_device_template()
            if quick_pick == "more":
                return await self.async_step_device_pick_candidate_full()
            if quick_pick:
                self._pending_candidate_entity_id = quick_pick
                self._pending_candidate_summary = self._candidate_summary(self._pending_candidate_entity_id)
                return await self.async_step_device_vetting()

        if not options:
            self._pending_candidate_entity_id = None
            self._pending_candidate_summary = None
            return await self.async_step_device_template()

        devices, _ = self._load_devices()
        display_devices = _overlay_runtime_device_details(devices, self._coordinator())
        all_candidates = self._device_candidates()
        workspace_placeholders = self._managed_devices_workspace_placeholders(display_devices, all_candidates)
        fixed_candidate_count, variable_candidate_count = self._candidate_mix_counts(all_candidates)
        top_candidate = all_candidates[0] if all_candidates else None
        review_candidate = next(
            (item for item in all_candidates if candidate_needs_review(assess_candidate(item))),
            None,
        )
        ready_candidate = next(
            (item for item in all_candidates if not candidate_needs_review(assess_candidate(item))),
            None,
        )
        quick_pick_options = [
            *(
                selector.SelectOptionDict(
                    value=item["entity_id"],
                    label=self._candidate_picker_label(
                        item,
                        top_candidate=top_candidate,
                        review_candidate=review_candidate,
                        ready_candidate=ready_candidate,
                    ),
                )
                for item in quick_picks
            ),
            selector.SelectOptionDict(value="more", label="Show full candidate list"),
            selector.SelectOptionDict(value=MANUAL_CANDIDATE_SELECTION, label=MANUAL_CANDIDATE_SHORTLIST_LABEL),
        ]
        top_candidate_summary = "\n".join(
            "- "
            + self._candidate_picker_label(
                {
                    **item,
                    "label": build_candidate_preview(item, include_entity_id=False, include_kind=True, include_state=False),
                },
                top_candidate=top_candidate,
                review_candidate=review_candidate,
                ready_candidate=ready_candidate,
            )
            for item in quick_picks
        ) if quick_picks else "- No suggested candidates right now"
        candidate_path_summary = (
            "1. Pick a candidate from the shortlist.\n"
            "2. Review fit and warnings.\n"
            "3. Choose a preset.\n"
            "4. Save it into Managed Devices."
        )
        return self.async_show_form(
            step_id="device_pick_candidate",
            data_schema=vol.Schema(
                {
                    vol.Required("quick_pick", default=quick_pick_options[0]["value"]): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=quick_pick_options, mode=selector.SelectSelectorMode.LIST)
                    )
                }
            ),
            errors={},
            description_placeholders={
                "device_kind": "fixed load" if kind == DEVICE_KIND_FIXED else "variable load",
                "top_candidates": top_candidate_summary,
                "candidate_path_summary": candidate_path_summary,
                "device_blocker_summary": self._device_blocker_summary(),
                "device_next_step": self._device_next_step(display_devices, [], all_candidates),
                **workspace_placeholders,
                "configure_path": DEVICES_CONFIGURE_PATH,
                "detailed_management_summary": self._detailed_management_summary(),
            },
        )

    async def async_step_device_pick_candidate_full(self, user_input=None):
        kind = self._pending_device_kind or DEVICE_KIND_FIXED
        options = self._candidate_options(kind=kind)
        if user_input is not None:
            selected = str(user_input.get("candidate_entity_id") or "")
            if selected == MANUAL_CANDIDATE_SELECTION:
                self._pending_candidate_entity_id = None
                self._pending_candidate_summary = None
                self._pending_device_template_key = None
                return await self.async_step_device_template()
            self._pending_candidate_entity_id = selected or None
            self._pending_candidate_summary = self._candidate_summary(self._pending_candidate_entity_id)
            return await self.async_step_device_vetting()

        picker_options = [
            selector.SelectOptionDict(value=MANUAL_CANDIDATE_SELECTION, label=MANUAL_CANDIDATE_SHORTLIST_LABEL),
            *options,
        ]
        default_candidate = self._pending_candidate_entity_id or MANUAL_CANDIDATE_SELECTION
        devices, _ = self._load_devices()
        display_devices = _overlay_runtime_device_details(devices, self._coordinator())
        all_candidates = self._device_candidates()
        workspace_placeholders = self._managed_devices_workspace_placeholders(display_devices, all_candidates)
        fixed_candidate_count, variable_candidate_count = self._candidate_mix_counts(all_candidates)
        top_candidate = all_candidates[0] if all_candidates else None
        candidate_path_summary = (
            "1. Pick a candidate from the shortlist or full list.\n"
            "2. Review fit and warnings.\n"
            "3. Choose a preset.\n"
            "4. Save it into Managed Devices."
        )
        return self.async_show_form(
            step_id="device_pick_candidate_full",
            data_schema=vol.Schema(
                {
                    vol.Required("candidate_entity_id", default=default_candidate): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=picker_options, mode=selector.SelectSelectorMode.DROPDOWN)
                    )
                }
            ),
            errors={},
            description_placeholders={
                "device_kind": "fixed load" if kind == DEVICE_KIND_FIXED else "variable load",
                "candidate_path_summary": candidate_path_summary,
                "device_blocker_summary": self._device_blocker_summary(),
                "device_next_step": self._device_next_step(display_devices, [], all_candidates),
                **workspace_placeholders,
                "configure_path": DEVICES_CONFIGURE_PATH,
                "detailed_management_summary": self._detailed_management_summary(),
            },
        )

    async def async_step_device_vetting(self, user_input=None):
        summary = self._pending_candidate_summary or self._candidate_summary(self._pending_candidate_entity_id)
        if summary is None:
            return await self.async_step_device_template()
        if user_input is not None:
            self._pending_candidate_summary = summary
            if not self._pending_device_template_key and summary.get('suggested_template_key'):
                self._pending_device_template_key = str(summary['suggested_template_key'])
            return await self.async_step_device_template()

        next_step = (
            "Continue to choose the suggested preset and then confirm the final device settings before saving into the managed fleet."
            if summary.get("fit_confidence") != "low"
            else "Continue only if this entity really drives a controllable device. If not, go back and choose manual selection or a different candidate."
        )
        promotion_path_summary = (
            "Promotion path: shortlist or full list -> review candidate -> choose preset -> save into Managed Devices."
        )
        devices, _ = self._load_devices()
        display_devices = _overlay_runtime_device_details(devices, self._coordinator())
        candidates = self._device_candidates()
        workspace_placeholders = self._managed_devices_workspace_placeholders(display_devices, candidates)
        return self.async_show_form(
            step_id="device_vetting",
            data_schema=vol.Schema({}),
            errors={},
            description_placeholders={
                "device_blocker_summary": self._device_blocker_summary(),
                "device_next_step": self._device_next_step(display_devices, [], candidates),
                **workspace_placeholders,
                "configure_path": DEVICES_CONFIGURE_PATH,
                "candidate_preview": build_candidate_preview(
                    summary,
                    include_entity_id=False,
                    include_state=False,
                ),
                "candidate_domain": str(summary.get('domain') or 'unknown'),
                "candidate_kind": "fixed load" if summary.get('kind') == DEVICE_KIND_FIXED else "variable load",
                "candidate_state": str(summary.get('state') or 'unknown'),
                "candidate_unit": str(summary.get('unit') or 'none'),
                "candidate_device_class": str(summary.get('device_class') or 'none'),
                "candidate_fit_usefulness": str(summary.get('fit_usefulness') or 'review first'),
                "candidate_fit_summary": str(summary.get('fit_summary') or 'No fit guidance available.'),
                "candidate_suitability": build_candidate_review_line(
                    "Control suitability",
                    str(summary.get('suitability_level') or 'review'),
                    str(summary.get('suitability_summary') or 'Review whether this entity is a clean control fit.'),
                ),
                "candidate_safety": build_candidate_review_line(
                    "Safety / confidence",
                    str(summary.get('safety_level') or 'review'),
                    str(summary.get('safety_summary') or 'Confirm the entity is safe to automate before promotion.'),
                ),
                "candidate_operational_value": build_candidate_review_line(
                    "Operational value",
                    str(summary.get('operational_value_level') or 'review'),
                    str(summary.get('operational_value_summary') or 'Confirm this candidate will materially help absorb export.'),
                ),
                "candidate_warnings": "\n".join(f"- {item}" for item in (summary.get('warnings') or [])) or "- No immediate warnings detected.",
                "suggested_template": str(summary.get('suggested_template_label') or 'Custom'),
                "suggested_template_description": str(summary.get('suggested_template_description') or 'Use a custom configuration for this entity.'),
                "candidate_next_step": next_step,
                "promotion_path_summary": promotion_path_summary,
                "detailed_management_summary": self._detailed_management_summary(),
            },
        )

    async def async_step_device_template(self, user_input=None):
        kind = self._pending_device_kind or DEVICE_KIND_FIXED
        templates = get_device_templates(kind)
        if user_input is not None:
            self._pending_device_template_key = user_input.get("device_template")
            return await self.async_step_device_add()

        summary = self._pending_candidate_summary or self._candidate_summary(self._pending_candidate_entity_id)
        if summary is not None:
            self._pending_candidate_summary = summary

        if not self._pending_device_template_key and self._pending_candidate_summary and self._pending_candidate_summary.get("suggested_template_key"):
            self._pending_device_template_key = str(self._pending_candidate_summary["suggested_template_key"])

        next_step = (
            "Choose the closest preset, then confirm the final device settings before saving into Managed Devices."
            if (summary or {}).get("fit_confidence") != "low"
            else "Choose a preset only if this entity really drives a controllable device. Otherwise go back and pick a different candidate or use manual selection."
        )
        promotion_path_summary = (
            "Promotion path: shortlist or full list -> review candidate -> choose preset -> save into Managed Devices."
        )

        options = [
            selector.SelectOptionDict(value=template.key, label=template.label)
            for template in templates
        ]
        devices, _ = self._load_devices()
        display_devices = _overlay_runtime_device_details(devices, self._coordinator())
        candidates = self._device_candidates()
        workspace_placeholders = self._managed_devices_workspace_placeholders(display_devices, candidates)
        return self.async_show_form(
            step_id="device_template",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "device_template",
                        default=self._pending_device_template_key or (templates[0].key if templates else ""),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.LIST)
                    )
                }
            ),
            errors={},
            description_placeholders={
                "device_kind": "fixed load" if kind == DEVICE_KIND_FIXED else "variable load",
                "device_blocker_summary": self._device_blocker_summary(),
                "device_next_step": self._device_next_step(display_devices, [], candidates),
                **workspace_placeholders,
                "configure_path": DEVICES_CONFIGURE_PATH,
                "detailed_management_summary": self._detailed_management_summary(),
                "candidate_preview": build_candidate_preview(
                    summary or {},
                    include_entity_id=False,
                    include_state=False,
                ) if summary else "No candidate selected yet.",
                "candidate_fit_usefulness": str((summary or {}).get('fit_usefulness') or 'review first'),
                "candidate_fit_summary": str((summary or {}).get('fit_summary') or 'No fit guidance available.'),
                "candidate_warnings": "\n".join(f"- {item}" for item in ((summary or {}).get('warnings') or [])) or "- No immediate warnings detected.",
                "suggested_template": str((summary or {}).get('suggested_template_label') or 'Custom'),
                "suggested_template_description": str((summary or {}).get('suggested_template_description') or 'Use a custom configuration for this entity.'),
                "candidate_next_step": next_step,
                "promotion_path_summary": promotion_path_summary,
                "template_summary": "\n".join(
                    f"- {template.label}: {template.description}" for template in templates
                ),
            },
        )

    async def async_step_device_add(self, user_input=None):
        errors: dict[str, str] = {}
        kind = self._pending_device_kind or DEVICE_KIND_FIXED
        editing_key = self._pending_device_key
        devices, _ = self._load_devices()
        candidates = self._device_candidates()
        existing_device = next((device for device in devices if device.get("key") == editing_key), None)

        if editing_key and existing_device is None:
            return await self.async_step_devices()

        if user_input is not None:
            new_device = self._build_device_payload(user_input, kind, key=editing_key)
            candidate_devices = [
                new_device if editing_key and device.get("key") == editing_key else device for device in devices
            ]
            if not editing_key:
                candidate_devices.append(new_device)
            raw_inventory = _device_options_json(candidate_devices)
            _, device_issues = parse_device_configs(raw_inventory)
            if device_issues:
                errors["base"] = "device_inventory_invalid"
            else:
                feedback = self._build_device_action_feedback(
                    action="edit" if editing_key else "promote",
                    devices=candidate_devices,
                    device=new_device,
                    previous_device=existing_device,
                )
                self._pending_device_key = None
                self._pending_device_template_key = None
                self._pending_candidate_entity_id = None
                self._pending_candidate_summary = None
                return await self._save_devices(candidate_devices, feedback=feedback)

        selected_template = get_device_template(kind, self._pending_device_template_key)
        defaults = self._device_form_defaults(
            existing_device,
            kind,
            template_defaults=selected_template.defaults if selected_template and not editing_key else None,
            candidate_summary=self._pending_candidate_summary if not editing_key else None,
        )
        display_devices = _overlay_runtime_device_details(devices, self._coordinator())
        promotion_path_summary = (
            "Promotion path: shortlist or full list -> review candidate -> choose preset -> save into Managed Devices."
        )
        workspace_placeholders = self._managed_devices_workspace_placeholders(display_devices, candidates)
        if not editing_key and self._pending_candidate_entity_id:
            selected_candidate = next((item for item in candidates if item["entity_id"] == self._pending_candidate_entity_id), None)
            if selected_candidate is not None:
                defaults["entity_id"] = selected_candidate["entity_id"]
                defaults["name"] = selected_candidate["name"]
        entity_domain = list(DEVICE_CANDIDATE_FIXED_DOMAINS) if kind == DEVICE_KIND_FIXED else list(DEVICE_CANDIDATE_VARIABLE_DOMAINS)
        schema_dict: dict[Any, Any] = {
            vol.Required("name", default=defaults["name"]): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            ),
            vol.Required("entity_id", default=defaults["entity_id"]): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=entity_domain)
            ),
            vol.Required("nominal_power_w", default=defaults["nominal_power_w"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=50000, step=10, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("priority", default=defaults["priority"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=1000, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("enabled", default=defaults["enabled"]): selector.BooleanSelector(),
            vol.Required("min_on_seconds", default=defaults["min_on_seconds"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=86400, step=30, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("min_off_seconds", default=defaults["min_off_seconds"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=86400, step=30, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("cooldown_seconds", default=defaults["cooldown_seconds"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=3600, step=5, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("max_active_seconds", default=defaults["max_active_seconds"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=172800, step=60, mode=selector.NumberSelectorMode.BOX)
            ),
        }
        if kind == DEVICE_KIND_VARIABLE:
            schema_dict.update(
                {
                    vol.Required("min_power_w", default=defaults["min_power_w"]): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=50000, step=10, mode=selector.NumberSelectorMode.BOX)
                    ),
                    vol.Required("max_power_w", default=defaults["max_power_w"]): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=50000, step=10, mode=selector.NumberSelectorMode.BOX)
                    ),
                    vol.Required("step_w", default=defaults["step_w"]): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=5000, step=10, mode=selector.NumberSelectorMode.BOX)
                    ),
                }
            )

        return self.async_show_form(
            step_id="device_add",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
            description_placeholders={
                "device_blocker_summary": self._device_blocker_summary(),
                "device_next_step": self._device_next_step(display_devices, [], candidates),
                "device_kind": "fixed load" if kind == DEVICE_KIND_FIXED else "variable load",
                **workspace_placeholders,
                "configure_path": DEVICES_CONFIGURE_PATH,
                "device_mode": "Edit" if editing_key else "Add",
                "device_template": selected_template.label if selected_template else "Custom",
                "template_description": selected_template.description if selected_template else "Use manual values for this device.",
                "candidate_preview": build_candidate_preview(
                    self._pending_candidate_summary or {},
                    include_entity_id=False,
                    include_state=False,
                ) if self._pending_candidate_summary else "Manual path, review the entity and settings before saving.",
                "default_guidance": self._default_guidance_text(kind, defaults),
                "selected_candidate_fit": str((self._pending_candidate_summary or {}).get("fit_usefulness") or "manual review"),
                "selected_candidate_summary": str((self._pending_candidate_summary or {}).get("fit_summary") or "Manual path, review the entity and settings before saving."),
                "selected_candidate_warnings": "\n".join(
                    f"- {item}" for item in ((self._pending_candidate_summary or {}).get("warnings") or [])
                ) or "- No extra warnings captured for this candidate.",
                "promotion_path_summary": promotion_path_summary,
                "detailed_management_summary": self._detailed_management_summary(),
            },
        )

    async def async_step_device_bulk_enable(self, user_input=None):
        devices, _ = self._load_devices()
        if not devices:
            return await self.async_step_devices()

        display_devices = _overlay_runtime_device_details(devices, self._coordinator())
        candidates = self._device_candidates()
        workspace_placeholders = self._managed_devices_workspace_placeholders(display_devices, candidates)
        enabled_keys = [device["key"] for device in devices if device.get("enabled", True)]
        if user_input is not None:
            selected_keys = {str(key) for key in user_input.get("enabled_devices", [])}
            updated_devices = [
                {**device, "enabled": device.get("key") in selected_keys}
                for device in devices
            ]
            feedback = self._build_device_action_feedback(action="bulk_enable", devices=updated_devices)
            return await self._save_devices(updated_devices, feedback=feedback)

        options = [
            selector.SelectOptionDict(value=device["key"], label=self._device_status_label(device))
            for device in sorted(display_devices, key=self._device_sort_key)
        ]
        return self.async_show_form(
            step_id="device_bulk_enable",
            data_schema=vol.Schema(
                {
                    vol.Required("enabled_devices", default=enabled_keys): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors={},
            description_placeholders={
                "enabled_count": str(len(enabled_keys)),
                "device_next_step": self._device_next_step(display_devices, [], candidates),
                **workspace_placeholders,
                "device_blocker_summary": self._device_blocker_summary(),
                "detailed_management_summary": self._detailed_management_summary(),
            },
        )

    async def async_step_device_edit_pick(self, user_input=None):
        devices, issues = self._load_devices()
        display_devices = _overlay_runtime_device_details(devices, self._coordinator())
        candidates = self._device_candidates()
        workspace_placeholders = self._managed_devices_workspace_placeholders(display_devices, candidates)
        if user_input is not None:
            selected_key = user_input["device_key"]
            selected_device = next((device for device in devices if device.get("key") == selected_key), None)
            if selected_device is None:
                return await self.async_step_devices()
            self._pending_device_key = selected_key
            self._pending_device_kind = str(selected_device.get("kind", DEVICE_KIND_FIXED))
            self._pending_device_template_key = None
            self._pending_candidate_entity_id = None
            self._pending_candidate_summary = None
            return await self.async_step_device_add()

        options = [
            selector.SelectOptionDict(value=device["key"], label=self._device_status_label(device))
            for device in sorted(display_devices, key=self._device_sort_key)
        ]
        return self.async_show_form(
            step_id="device_edit_pick",
            data_schema=vol.Schema(
                {
                    vol.Required("device_key"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
                    )
                }
            ),
            errors={},
            description_placeholders={
                "configure_path": DEVICES_CONFIGURE_PATH,
                **workspace_placeholders,
                "device_next_step": self._device_next_step(display_devices, issues, candidates),
                "device_blocker_summary": self._device_blocker_summary(),
                "detailed_management_summary": self._detailed_management_summary(),
            },
        )

    async def async_step_device_remove(self, user_input=None):
        devices, issues = self._load_devices()
        display_devices = _overlay_runtime_device_details(devices, self._coordinator())
        candidates = self._device_candidates()
        workspace_placeholders = self._managed_devices_workspace_placeholders(display_devices, candidates)
        if user_input is not None:
            remove_name = user_input["device_key"]
            removed_device = next((device for device in devices if device.get("key") == remove_name), None)
            remaining = [device for device in devices if device.get("key") != remove_name]
            feedback = self._build_device_action_feedback(action="remove", devices=remaining, previous_device=removed_device)
            return await self._save_devices(remaining, feedback=feedback)

        options = [
            selector.SelectOptionDict(value=device["key"], label=self._device_status_label(device))
            for device in sorted(display_devices, key=self._device_sort_key)
        ]
        return self.async_show_form(
            step_id="device_remove",
            data_schema=vol.Schema(
                {
                    vol.Required("device_key"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
                    )
                }
            ),
            errors={},
            description_placeholders={
                "configure_path": DEVICES_CONFIGURE_PATH,
                **workspace_placeholders,
                "device_next_step": self._device_next_step(display_devices, issues, candidates),
                "device_blocker_summary": self._device_blocker_summary(),
                "detailed_management_summary": self._detailed_management_summary(),
            },
        )

    async def async_step_devices_json(self, user_input=None):
        errors = {}
        description_placeholders = {
            "device_blueprint": default_device_blueprint(),
            "configure_path": ADVANCED_DEVICES_CONFIGURE_PATH,
            "devices_path": DEVICES_CONFIGURE_PATH,
            "sources_path": SOURCES_CONFIGURE_PATH,
            "policy_path": POLICY_CONFIGURE_PATH,
            "mode_path": MODE_CONTROL_PATH,
            "support_path": SUPPORT_CONFIGURE_PATH,
            "detailed_management_summary": self._detailed_management_summary(),
            "device_issues": "",
        }

        if user_input is not None:
            raw_inventory = user_input.get(CONF_DEVICE_INVENTORY_JSON)
            _, device_issues = parse_device_configs(raw_inventory)
            if device_issues:
                errors["base"] = "device_inventory_invalid"
                description_placeholders["device_issues"] = "\n".join(
                    f"- {issue}" for issue in device_issues[:6]
                )
            else:
                merged_options = dict(self._config_entry.options)
                merged_options[CONF_DEVICE_INVENTORY_JSON] = _coerce_text(
                    raw_inventory,
                    DEFAULT_DEVICE_INVENTORY_JSON,
                )
                self.hass.config_entries.async_update_entry(self._config_entry, options=merged_options)
                await self.hass.config_entries.async_reload(self._config_entry.entry_id)
                return self.async_create_entry(title="", data=merged_options)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE_INVENTORY_JSON,
                    default=_entry_default_text(
                        self._config_entry,
                        CONF_DEVICE_INVENTORY_JSON,
                        DEFAULT_DEVICE_INVENTORY_JSON,
                    ),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        multiline=True,
                        type=selector.TextSelectorType.TEXT,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="devices_json",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    async def async_step_policy(self, user_input=None):
        errors = {}

        if user_input is not None:
            merged_options = dict(self._config_entry.options)
            merged_options.update(user_input)
            self.hass.config_entries.async_update_entry(self._config_entry, options=merged_options)
            await self.hass.config_entries.async_reload(self._config_entry.entry_id)
            return self.async_create_entry(title="", data=merged_options)

        effective_config = dict(self._config_entry.data)
        effective_config.update(self._config_entry.options)
        devices, device_issues = self._load_devices()
        grid_mode = _grid_mode_default(self._config_entry)
        source_placeholders = self._source_placeholders(effective_config=effective_config, grid_mode=grid_mode)
        source_attention = self._source_attention_state(effective_config=effective_config, grid_mode=grid_mode)
        missing_sources = source_attention["missing_source_keys"]
        runtime_source_attention = source_attention["has_runtime_source_attention"]
        if missing_sources:
            policy_readiness = "Finish source mapping first: " + self._format_source_role_names(missing_sources)
            policy_next_step = f"Open {SOURCES_CONFIGURE_PATH} before changing controller behaviour."
        elif runtime_source_attention:
            policy_readiness = source_placeholders["source_health"] + ". " + source_placeholders["source_next_step"]
            policy_next_step = source_placeholders["source_next_step"]
        elif device_issues:
            policy_readiness = f"Managed-device issues still need repair before policy tuning can be trusted ({len(device_issues)} issue(s))."
            policy_next_step = f"Open {DEVICES_CONFIGURE_PATH} and repair the fleet before trusting policy changes."
        elif not devices:
            policy_readiness = "No managed devices are configured yet. You can tune policy now, but control will not act until devices are added."
            policy_next_step = (
                f"After tuning defaults here, open {DEVICES_CONFIGURE_PATH} to use the Managed Devices workspace "
                "and add the first fixed or variable load manually."
            )
        else:
            policy_readiness = f"Sources are mapped and {len(devices)} managed device(s) are configured, so policy changes are actionable now."
            policy_next_step = (
                f"Tune behaviour here, then use {MODE_CONTROL_PATH} or {INTEGRATION_DEVICE_PATH} to verify the current controller outcome."
            )

        command_center = build_native_command_center_summary(self._coordinator())
        recommended_section = str(command_center.get("recommended_section") or "").strip().lower()
        if recommended_section == str(DEVICES_SECTION_LABEL).strip().lower():
            managed_devices_follow_through = str(command_center.get("next_action_summary") or "").strip()
            if managed_devices_follow_through:
                policy_next_step = managed_devices_follow_through
        mode_label, mode_description = _live_mode_details(self._coordinator())
        policy_summary = (
            f"Live mode {mode_label}; target {int(_entry_default_number(self._config_entry, CONF_TARGET_EXPORT_W, DEFAULT_TARGET_EXPORT_W))} W, "
            f"deadband {int(_entry_default_number(self._config_entry, CONF_DEADBAND_W, DEFAULT_DEADBAND_W))} W, "
            f"battery reserve {int(_entry_default_number(self._config_entry, CONF_BATTERY_RESERVE_SOC, DEFAULT_BATTERY_RESERVE_SOC))}%, "
            f"refresh {int(_entry_default_number(self._config_entry, CONF_REFRESH_SECONDS, DEFAULT_REFRESH_SECONDS))} s"
        )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_TARGET_EXPORT_W,
                    default=_entry_default_number(
                        self._config_entry,
                        CONF_TARGET_EXPORT_W,
                        DEFAULT_TARGET_EXPORT_W,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=-5000, max=10000, step=10, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_DEADBAND_W,
                    default=_entry_default_number(
                        self._config_entry,
                        CONF_DEADBAND_W,
                        DEFAULT_DEADBAND_W,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=2000, step=10, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_BATTERY_RESERVE_SOC,
                    default=_entry_default_number(
                        self._config_entry,
                        CONF_BATTERY_RESERVE_SOC,
                        DEFAULT_BATTERY_RESERVE_SOC,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_REFRESH_SECONDS,
                    default=_entry_default_number(
                        self._config_entry,
                        CONF_REFRESH_SECONDS,
                        DEFAULT_REFRESH_SECONDS,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=300, step=5, mode=selector.NumberSelectorMode.BOX)
                ),
            }
        )
        return self.async_show_form(
            step_id="policy",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "configure_path": POLICY_CONFIGURE_PATH,
                "sources_path": SOURCES_CONFIGURE_PATH,
                "devices_path": DEVICES_CONFIGURE_PATH,
                "policy_path": POLICY_CONFIGURE_PATH,
                "mode_path": MODE_CONTROL_PATH,
                "current_mode": mode_label,
                "mode_summary": mode_description,
                "support_path": SUPPORT_CONFIGURE_PATH,
                "policy_readiness": policy_readiness,
                "policy_summary": policy_summary,
                "policy_next_step": policy_next_step,
                "control_decision_summary": str(command_center.get("control_decision_summary") or "No live control decision is available yet."),
                "control_outcome_summary": str(command_center.get("control_outcome_summary") or "Live control outcome will appear here after the integration loads."),
            },
        )

    async def async_step_support(self, user_input=None):
        if user_input is not None:
            return await self.async_step_init()

        return self.async_show_form(
            step_id="support",
            data_schema=vol.Schema({}),
            errors={},
            description_placeholders={
                "configure_path": SUPPORT_CONFIGURE_PATH,
                **self._support_placeholders(),
            },
        )

    async def async_step_advanced(self, user_input=None):
        return await self.async_step_devices_json(user_input)
