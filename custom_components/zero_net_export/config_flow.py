"""Config flow for Zero Net Export."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BATTERY_CHARGE_POWER_ENTITY,
    CONF_BATTERY_DISCHARGE_POWER_ENTITY,
    CONF_BATTERY_RESERVE_SOC,
    CONF_BATTERY_SOC_ENTITY,
    CONF_DEADBAND_W,
    CONF_DEVICE_INVENTORY_JSON,
    DEVICE_CANDIDATE_DOMAINS,
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
    DEVICES_CONFIGURE_PATH,
    INTEGRATION_DEVICE_PATH,
    MODE_CONTROL_PATH,
    POLICY_CONFIGURE_PATH,
    PRIMARY_CONFIGURE_PATH,
    SOURCES_CONFIGURE_PATH,
    SUPPORT_CONFIGURE_PATH,
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
        "Sources and source mapping": "native_setup",
        "Managed devices": "devices",
        "Policy and controller settings": "policy",
        "Health, support, and troubleshooting": "support",
    }
    base_options = ["native_setup", "policy", "devices", "support"]
    recommended_option = recommended_map.get(recommended_section)
    ordered = [option for option in base_options if option == recommended_option]
    ordered.extend(option for option in base_options if option != recommended_option)
    ordered.append("advanced")
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
    def _device_status_label(device: dict[str, Any]) -> str:
        state = "enabled" if device.get("enabled", True) else "disabled"
        priority = int(device.get("priority", 0) or 0)
        power = int(float(device.get("nominal_power_w", 0) or 0))
        return (
            f"{device.get('name', 'Unnamed device')} "
            f"({device.get('kind', 'unknown')}, {state}, priority {priority}, {power} W, {device.get('entity_id', 'unknown entity')})"
        )

    def _fleet_summary_lines(self, devices: list[dict[str, Any]]) -> list[str]:
        if not devices:
            return ["- None"]
        ordered = sorted(
            devices,
            key=lambda item: (
                0 if item.get("enabled", True) else 1,
                int(item.get("priority", 0) or 0),
                str(item.get("name", "")).lower(),
            ),
        )
        enabled_count = sum(1 for device in devices if device.get("enabled", True))
        fixed_count = sum(1 for device in devices if device.get("kind") == DEVICE_KIND_FIXED)
        variable_count = sum(1 for device in devices if device.get("kind") == DEVICE_KIND_VARIABLE)
        total_power = int(sum(float(device.get("nominal_power_w", 0) or 0) for device in devices))
        lines = [
            f"- Fleet summary: {len(devices)} device(s), {enabled_count} enabled, {fixed_count} fixed, {variable_count} variable, {total_power} W nominal controllable power",
        ]
        lines.extend(f"- {self._device_status_label(device)}" for device in ordered)
        return lines

    def _device_candidates(self) -> list[dict[str, Any]]:
        devices, _ = self._load_devices()
        managed_ids = {str(device.get("entity_id")) for device in devices if device.get("entity_id")}
        candidates: list[dict[str, Any]] = []
        for state in sorted(self.hass.states.async_all(), key=lambda item: item.entity_id):
            entity_id = state.entity_id
            domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
            if domain not in DEVICE_CANDIDATE_DOMAINS:
                continue
            if entity_id in managed_ids:
                continue
            if str(state.state).lower() in {"unavailable", "unknown"}:
                continue
            kind = DEVICE_KIND_FIXED if domain in DEVICE_CANDIDATE_FIXED_DOMAINS else DEVICE_KIND_VARIABLE
            candidates.append(
                {
                    "entity_id": entity_id,
                    "label": _format_candidate_label(entity_id, state),
                    "name": str(state.attributes.get("friendly_name") or entity_id),
                    "kind": kind,
                    "domain": domain,
                    "state": str(state.state),
                }
            )
        return candidates

    def _candidate_options(self, *, kind: str | None = None) -> list[selector.SelectOptionDict]:
        candidates = self._device_candidates()
        if kind:
            candidates = [item for item in candidates if item["kind"] == kind]
        return [
            selector.SelectOptionDict(value=item["entity_id"], label=item["label"])
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
        return ranked[:3]

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

        ranked_states: list[tuple[int, str, Any]] = []
        for state in self.hass.states.async_all():
            if state.entity_id.split(".", 1)[0] != "sensor":
                continue
            if not _state_matches_source_quantity(state, quantity):
                continue
            score = _score_source_candidate(state, role_key or "", quantity) if role_key else 0
            ranked_states.append((-score, state.entity_id, state))

        for _, _, state in sorted(ranked_states):
            entity_id = state.entity_id
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
        ranked: list[tuple[int, str, str]] = []
        for state in self.hass.states.async_all():
            if state.entity_id.split(".", 1)[0] != "sensor":
                continue
            if not _state_matches_source_quantity(state, quantity):
                continue
            score = _score_source_candidate(state, role_key, quantity)
            if score < 2:
                continue
            ranked.append((score, state.entity_id, _format_source_candidate_label(state.entity_id, state, role_key, quantity)))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [label for _, _, label in ranked[:limit]]

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
        confidence = "medium"
        fit_summary = "Looks like a plausible controllable candidate, but review before promotion."
        warnings: list[str] = []

        if domain == 'switch' and kind == DEVICE_KIND_FIXED:
            suggested_template = next((item for item in templates if item.key in {'hot_water', 'smart_plug', 'pool_pump'}), suggested_template)
            confidence = 'high'
            fit_summary = 'Switch entities are usually strong fixed-load candidates when they control a real appliance or relay.'
        elif domain == 'light' and kind == DEVICE_KIND_FIXED:
            confidence = 'medium'
            fit_summary = 'Light entities can be controllable, but many are comfort or presence loads rather than discretionary energy sinks.'
            warnings.append('Confirm this light is a real discretionary load, not a normal lighting circuit people expect to stay manual.')
        elif domain == 'input_boolean' and kind == DEVICE_KIND_FIXED:
            confidence = 'low'
            fit_summary = 'Helpers can represent automation intent, not a physical load.'
            warnings.append('This is an input_boolean helper. Verify it really drives a safe controllable load before promoting it.')
        if domain in {'number', 'input_number'} and kind == DEVICE_KIND_VARIABLE:
            suggested_template = next((item for item in templates if item.key in {'ev_charger', 'battery_charge_sink'}), suggested_template)
            confidence = 'high' if domain == 'number' else 'medium'
            fit_summary = 'Number-style entities are strong variable-load candidates when they represent a real power or current target.'
            if domain == 'input_number':
                warnings.append('This is an input_number helper. Check that changing it actually drives a real device, not just a dashboard helper.')

        raw_state = str(state.state).strip().lower()
        if raw_state in {'unknown', 'unavailable'}:
            warnings.append(f'Entity state is currently {raw_state}. Promotion is risky until it reports cleanly.')
            confidence = 'low'
        unit = str(state.attributes.get('unit_of_measurement') or '')
        device_class = str(state.attributes.get('device_class') or '')
        if kind == DEVICE_KIND_VARIABLE and not unit:
            warnings.append('Variable candidates are safer when the entity exposes a meaningful unit such as A, W, or %.')
        if kind == DEVICE_KIND_VARIABLE and device_class == 'battery':
            warnings.append('Battery-class entities are often telemetry, not safe control targets. Confirm this is a writable control entity.')
            confidence = 'low'

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

    async def _save_devices(self, devices: list[dict[str, Any]]):
        merged_options = dict(self._config_entry.options)
        merged_options[CONF_DEVICE_INVENTORY_JSON] = _device_options_json(devices)
        self.hass.config_entries.async_update_entry(self._config_entry, options=merged_options)
        await self.hass.config_entries.async_reload(self._config_entry.entry_id)
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
            source_next_step = str(
                readiness.get("next_step") or "Source mapping looks healthy; continue to managed devices or policy."
            )

        contextual_fallback_hint = (
            blocking_fallback_hint or missing_fallback_hint or runtime_attention_fallback_hint
        )

        return {
            "missing_sources": missing_sources,
            "source_health": source_health,
            "source_next_step": source_next_step,
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
                f"{INTEGRATION_DEVICE_PATH} support actions or Settings -> Repairs if deeper triage is still needed."
            )
        support_install_consistency = build_install_consistency_summary(install_provenance)
        support_install_fingerprint_summary = build_install_fingerprint_summary(install_provenance)
        mode_label, mode_description = _live_mode_details(coordinator)
        return {
            "support_status": readiness.get("summary") or health_summary,
            "support_next_step": support_next_step,
            "support_path": SUPPORT_CONFIGURE_PATH,
            "mode_path": MODE_CONTROL_PATH,
            "current_mode": mode_label,
            "mode_summary": mode_description,
            "readiness_phase": str(readiness.get("phase") or "unknown"),
            "health_status": health_summary,
            "support_source_mapping_summary": build_source_mapping_summary(merged),
            "support_unavailable_sources": unavailable_sources or "None",
            "support_stale_sources": stale_sources or "None",
            "support_source_attention_roles": build_source_attention_role_summary(state, merged, limit=4),
            "support_attention_summary": build_source_attention_summary(state, merged, limit=4),
            "support_blocking_details": summarize_validation_issue_messages(state, severities={"error"}, limit=3),
            "support_fallback_hint": support_fallback_hint or "Not needed right now.",
            "support_install_status": str(install_provenance.get("summary") or "Installed package provenance unavailable"),
            "support_install_consistency": support_install_consistency,
            "support_install_fingerprint_summary": support_install_fingerprint_summary,
            "support_candidate_hints": support_candidate_hints,
            "support_priority_candidate_hints": support_priority_candidate_hints,
            "recommended_section": str(command_center.get("recommended_section") or "Health, support, and troubleshooting"),
            "recommended_path": str(command_center.get("recommended_path") or SUPPORT_CONFIGURE_PATH),
            "next_action_summary": str(command_center.get("next_action_summary") or readiness.get("next_step") or "Review the current blocker, then follow the recommended native Configure path."),
        }

    async def async_step_init(self, user_input=None):
        command_center = build_native_command_center_summary(self._coordinator())

        mode_label, mode_description = _live_mode_details(self._coordinator())
        placeholders = {
            "configure_path": PRIMARY_CONFIGURE_PATH,
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
            merged_options[CONF_REFRESH_SECONDS] = int(
                _coerce_number(user_input.get(CONF_REFRESH_SECONDS), DEFAULT_REFRESH_SECONDS)
            )

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
            CONF_REFRESH_SECONDS: _entry_default_number(
                self._config_entry,
                CONF_REFRESH_SECONDS,
                DEFAULT_REFRESH_SECONDS,
            ),
        }
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
            source_defaults[CONF_REFRESH_SECONDS] = _coerce_number(
                user_input.get(CONF_REFRESH_SECONDS),
                DEFAULT_REFRESH_SECONDS,
            )

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
        fields[
            vol.Required(
                CONF_REFRESH_SECONDS,
                default=source_defaults[CONF_REFRESH_SECONDS],
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=5, max=300, step=5, mode=selector.NumberSelectorMode.BOX)
        )

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
                "grid_mapping_note": grid_mapping_note,
                "fallback_guidance": fallback_guidance,
                "source_candidate_hints": source_candidate_hints,
                "source_role_guide": self._source_role_guide_summary(grid_mode),
                **source_placeholders,
            },
        )

    def _device_next_step(self, devices: list[dict[str, Any]], issues: list[str], candidates: list[dict[str, Any]]) -> str:
        top_candidate = candidates[0] if candidates else None
        if issues:
            return "Repair the managed-device issues first, then return here to review enablement or add another load."
        if not devices and top_candidate:
            return (
                f"Start with {top_candidate['name']} ({top_candidate['entity_id']}) by choosing the matching add action below, then review the candidate and save it into the fleet."
            )
        if not devices:
            return "Choose Add fixed load device or Add variable load device to tag the first controllable load into the fleet."
        if top_candidate:
            return (
                f"Review the current fleet, then consider promoting the next unmanaged candidate: {top_candidate['name']} ({top_candidate['entity_id']})."
            )
        return "Use Review fleet to stage enablement, or edit an existing device if the current fleet still needs tuning."

    async def async_step_devices(self, user_input=None):
        devices, issues = self._load_devices()
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

        choices = [
            selector.SelectOptionDict(value="add_fixed", label="Add fixed load device"),
            selector.SelectOptionDict(value="add_variable", label="Add variable load device"),
        ]
        if devices:
            choices.append(selector.SelectOptionDict(value="bulk_enable", label="Review fleet / enable or disable devices"))
            choices.append(selector.SelectOptionDict(value="edit", label="Edit managed device"))
            choices.append(selector.SelectOptionDict(value="remove", label="Remove managed device"))
        choices.append(selector.SelectOptionDict(value="json", label="Advanced JSON editor / recovery"))
        summary = "\n".join(self._fleet_summary_lines(devices))
        fixed_candidates = [item for item in candidates if item['kind'] == DEVICE_KIND_FIXED]
        variable_candidates = [item for item in candidates if item['kind'] == DEVICE_KIND_VARIABLE]
        candidate_summary = "\n".join(
            f"- {item['name']} ({item['entity_id']}, {item['kind']})" for item in candidates[:12]
        ) if candidates else "- No unmanaged candidate devices discovered right now"
        fixed_candidate_summary = "\n".join(
            f"- {item['name']} ({item['entity_id']})" for item in fixed_candidates[:6]
        ) if fixed_candidates else "- No fixed-load candidates discovered right now"
        variable_candidate_summary = "\n".join(
            f"- {item['name']} ({item['entity_id']})" for item in variable_candidates[:6]
        ) if variable_candidates else "- No variable-load candidates discovered right now"
        top_candidate = candidates[0] if candidates else None
        device_next_step = self._device_next_step(devices, issues, candidates)
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
                "candidate_count": str(len(candidates)),
                "candidate_summary": candidate_summary,
                "fixed_candidate_count": str(len(fixed_candidates)),
                "fixed_candidate_summary": fixed_candidate_summary,
                "variable_candidate_count": str(len(variable_candidates)),
                "variable_candidate_summary": variable_candidate_summary,
                "top_candidate": (
                    f"{top_candidate['name']} ({top_candidate['entity_id']}, {top_candidate['kind']})"
                    if top_candidate
                    else "None discovered right now"
                ),
                "device_next_step": device_next_step,
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

        quick_pick_options = [
            *(selector.SelectOptionDict(value=item["entity_id"], label=item["label"]) for item in quick_picks),
            selector.SelectOptionDict(value="more", label="Show full candidate list"),
            selector.SelectOptionDict(value=MANUAL_CANDIDATE_SELECTION, label="Manual entity selection / entity not listed"),
        ]
        top_candidate_summary = "\n".join(
            (
                f"- {item['name']} ({item['entity_id']}, state {item['state']})"
                + f" | fit {(self._candidate_summary(item['entity_id']) or {}).get('fit_confidence', 'unknown')}"
            )
            for item in quick_picks
        ) if quick_picks else "- No suggested candidates right now"
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
                "candidate_count": str(len(options)),
                "top_candidates": top_candidate_summary,
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
            selector.SelectOptionDict(value=MANUAL_CANDIDATE_SELECTION, label="Manual entity selection / entity not listed"),
            *options,
        ]
        default_candidate = self._pending_candidate_entity_id or MANUAL_CANDIDATE_SELECTION
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
                "candidate_count": str(len(options)),
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
        return self.async_show_form(
            step_id="device_vetting",
            data_schema=vol.Schema({}),
            errors={},
            description_placeholders={
                "candidate_name": str(summary.get('name') or summary.get('entity_id') or 'candidate'),
                "candidate_entity_id": str(summary.get('entity_id') or ''),
                "candidate_domain": str(summary.get('domain') or 'unknown'),
                "candidate_kind": "fixed load" if summary.get('kind') == DEVICE_KIND_FIXED else "variable load",
                "candidate_state": str(summary.get('state') or 'unknown'),
                "candidate_unit": str(summary.get('unit') or 'none'),
                "candidate_device_class": str(summary.get('device_class') or 'none'),
                "candidate_fit_confidence": str(summary.get('fit_confidence') or 'unknown'),
                "candidate_fit_summary": str(summary.get('fit_summary') or 'No fit guidance available.'),
                "candidate_warnings": "\n".join(f"- {item}" for item in (summary.get('warnings') or [])) or "- No immediate warnings detected.",
                "suggested_template": str(summary.get('suggested_template_label') or 'Custom'),
                "suggested_template_description": str(summary.get('suggested_template_description') or 'Use a custom configuration for this entity.'),
                "candidate_next_step": next_step,
            },
        )

    async def async_step_device_template(self, user_input=None):
        kind = self._pending_device_kind or DEVICE_KIND_FIXED
        templates = get_device_templates(kind)
        if user_input is not None:
            self._pending_device_template_key = user_input.get("device_template")
            return await self.async_step_device_add()

        if not self._pending_device_template_key and self._pending_candidate_summary and self._pending_candidate_summary.get("suggested_template_key"):
            self._pending_device_template_key = str(self._pending_candidate_summary["suggested_template_key"])

        options = [
            selector.SelectOptionDict(value=template.key, label=template.label)
            for template in templates
        ]
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
                self._pending_device_key = None
                self._pending_device_template_key = None
                self._pending_candidate_entity_id = None
                self._pending_candidate_summary = None
                return await self._save_devices(candidate_devices)

        selected_template = get_device_template(kind, self._pending_device_template_key)
        defaults = self._device_form_defaults(
            existing_device,
            kind,
            template_defaults=selected_template.defaults if selected_template and not editing_key else None,
            candidate_summary=self._pending_candidate_summary if not editing_key else None,
        )
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
                "device_kind": "fixed load" if kind == DEVICE_KIND_FIXED else "variable load",
                "configure_path": DEVICES_CONFIGURE_PATH,
                "device_mode": "Edit" if editing_key else "Add",
                "device_template": selected_template.label if selected_template else "Custom",
                "template_description": selected_template.description if selected_template else "Use manual values for this device.",
                "candidate_hint": next((item["label"] for item in candidates if item["entity_id"] == defaults.get("entity_id")), "Pick an unmanaged candidate entity from the selector or choose a manual entity."),
                "default_guidance": self._default_guidance_text(kind, defaults),
                "selected_candidate_fit": str((self._pending_candidate_summary or {}).get("fit_confidence") or "manual"),
                "selected_candidate_summary": str((self._pending_candidate_summary or {}).get("fit_summary") or "Manual path, review the entity and settings before saving."),
                "selected_candidate_warnings": "\n".join(
                    f"- {item}" for item in ((self._pending_candidate_summary or {}).get("warnings") or [])
                ) or "- No extra warnings captured for this candidate.",
            },
        )

    async def async_step_device_bulk_enable(self, user_input=None):
        devices, _ = self._load_devices()
        if not devices:
            return await self.async_step_devices()

        enabled_keys = [device["key"] for device in devices if device.get("enabled", True)]
        if user_input is not None:
            selected_keys = {str(key) for key in user_input.get("enabled_devices", [])}
            updated_devices = [
                {**device, "enabled": device.get("key") in selected_keys}
                for device in devices
            ]
            return await self._save_devices(updated_devices)

        options = [
            selector.SelectOptionDict(value=device["key"], label=self._device_status_label(device))
            for device in sorted(devices, key=lambda item: str(item.get("name", "")).lower())
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
                "device_summary": "\n".join(self._fleet_summary_lines(devices)),
                "enabled_count": str(len(enabled_keys)),
                "device_count": str(len(devices)),
            },
        )

    async def async_step_device_edit_pick(self, user_input=None):
        devices, issues = self._load_devices()
        candidates = self._device_candidates()
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
            for device in sorted(devices, key=lambda item: str(item.get("name", "")).lower())
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
                "device_count": str(len(devices)),
                "device_summary": "\n".join(self._fleet_summary_lines(devices)),
                "device_next_step": self._device_next_step(devices, issues, candidates),
            },
        )

    async def async_step_device_remove(self, user_input=None):
        devices, issues = self._load_devices()
        candidates = self._device_candidates()
        if user_input is not None:
            remove_name = user_input["device_key"]
            remaining = [device for device in devices if device.get("key") != remove_name]
            return await self._save_devices(remaining)

        options = [
            selector.SelectOptionDict(value=device["key"], label=self._device_status_label(device))
            for device in sorted(devices, key=lambda item: str(item.get("name", "")).lower())
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
                "device_count": str(len(devices)),
                "device_summary": "\n".join(self._fleet_summary_lines(devices)),
                "device_next_step": self._device_next_step(devices, issues, candidates),
            },
        )

    async def async_step_devices_json(self, user_input=None):
        errors = {}
        description_placeholders = {
            "device_blueprint": default_device_blueprint(),
            "configure_path": ADVANCED_DEVICES_CONFIGURE_PATH,
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
            policy_next_step = f"After tuning defaults here, open {DEVICES_CONFIGURE_PATH} and add the first controllable load."
        else:
            policy_readiness = f"Sources are mapped and {len(devices)} managed device(s) are configured, so policy changes are actionable now."
            policy_next_step = (
                f"Adjust behaviour here, then use {INTEGRATION_DEVICE_PATH}, its entities, and support actions to verify runtime health."
            )

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
