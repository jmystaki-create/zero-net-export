"""Controllable device model for Zero Net Export."""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
import re
from typing import Any


DEVICE_KIND_FIXED = "fixed"
DEVICE_KIND_VARIABLE = "variable"
DEVICE_KINDS = [DEVICE_KIND_FIXED, DEVICE_KIND_VARIABLE]

ADAPTER_FIXED_TOGGLE = "fixed_toggle"
ADAPTER_VARIABLE_NUMBER = "variable_number"
KNOWN_ADAPTERS = [ADAPTER_FIXED_TOGGLE, ADAPTER_VARIABLE_NUMBER]

ACTIVE_STATE_STRINGS = {"on", "home", "heat", "cool", "auto", "open", "opening", "closing"}
INACTIVE_STATE_STRINGS = {"off", "closed", "idle", "standby"}


@dataclass(slots=True)
class DeviceAdapterSpec:
    """Static metadata for a supported device adapter."""

    key: str
    label: str
    kind: str
    entity_domains: tuple[str, ...]
    actions: tuple[str, ...]
    description: str


ADAPTER_SPECS: dict[str, DeviceAdapterSpec] = {
    ADAPTER_FIXED_TOGGLE: DeviceAdapterSpec(
        key=ADAPTER_FIXED_TOGGLE,
        label="Fixed toggle entity",
        kind=DEVICE_KIND_FIXED,
        entity_domains=("switch", "input_boolean"),
        actions=("turn_on", "turn_off"),
        description="Uses the entity domain's turn_on/turn_off services for fixed loads.",
    ),
    ADAPTER_VARIABLE_NUMBER: DeviceAdapterSpec(
        key=ADAPTER_VARIABLE_NUMBER,
        label="Variable number entity",
        kind=DEVICE_KIND_VARIABLE,
        entity_domains=("number", "input_number"),
        actions=("increase", "decrease"),
        description="Uses number/input_number.set_value for variable power targets.",
    ),
}


@dataclass(slots=True)
class DeviceConfig:
    """Operator-configured controllable device."""

    key: str
    name: str
    kind: str
    entity_id: str
    adapter: str | None
    nominal_power_w: float
    min_power_w: float
    max_power_w: float
    step_w: float
    priority: int
    enabled: bool
    min_on_seconds: int
    min_off_seconds: int
    cooldown_seconds: int


@dataclass(slots=True)
class DeviceRuntime:
    """Runtime usability and explainability for a controllable device."""

    config: DeviceConfig
    usable: bool
    status: str
    reason: str
    adapter: DeviceAdapterSpec | None
    adapter_status: str
    adapter_reason: str
    current_power_w: float | None
    current_target_power_w: float | None
    observed_active: bool
    configured_enabled: bool
    configured_priority: int
    effective_enabled: bool
    effective_priority: int
    operator_enabled_override: bool | None
    operator_priority_override: int | None


@dataclass(slots=True)
class DeviceModelSummary:
    """Aggregated runtime view of the configured device fleet."""

    devices: list[DeviceRuntime]
    total_devices: int
    enabled_devices: int
    usable_devices: int
    fixed_devices: int
    variable_devices: int
    total_nominal_power_w: float
    usable_nominal_power_w: float


def default_device_blueprint() -> str:
    return json.dumps(
        [
            {
                "name": "Hot Water",
                "kind": "fixed",
                "entity_id": "switch.hot_water",
                "adapter": "fixed_toggle",
                "nominal_power_w": 2400,
                "priority": 100,
                "enabled": True,
                "min_on_seconds": 900,
                "min_off_seconds": 900,
                "cooldown_seconds": 60,
            },
            {
                "name": "EV Charger",
                "kind": "variable",
                "entity_id": "number.ev_charger_current_limit",
                "adapter": "variable_number",
                "min_power_w": 1400,
                "max_power_w": 7200,
                "step_w": 100,
                "priority": 50,
                "enabled": True,
                "min_on_seconds": 300,
                "min_off_seconds": 60,
                "cooldown_seconds": 30,
            },
        ],
        indent=2,
    )


def parse_device_configs(raw: str | None) -> tuple[list[DeviceConfig], list[str]]:
    if not raw or not raw.strip():
        return [], []

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as err:
        return [], [f"Device inventory JSON is invalid: {err.msg} (line {err.lineno} column {err.colno})"]

    if not isinstance(payload, list):
        return [], ["Device inventory must be a JSON array"]

    devices: list[DeviceConfig] = []
    issues: list[str] = []
    seen_keys: set[str] = set()

    for index, item in enumerate(payload, start=1):
        prefix = f"device #{index}"
        if not isinstance(item, dict):
            issues.append(f"{prefix} must be an object")
            continue

        name = str(item.get("name", "")).strip()
        if not name:
            issues.append(f"{prefix} is missing a non-empty name")
            continue

        key = _slugify(str(item.get("key") or name))
        if not key:
            issues.append(f"{prefix} produced an empty key; provide a key or a better name")
            continue
        if key in seen_keys:
            issues.append(f"{prefix} duplicates key '{key}'")
            continue
        seen_keys.add(key)

        kind = str(item.get("kind", "")).strip().lower()
        if kind not in DEVICE_KINDS:
            issues.append(f"{prefix} kind must be one of {DEVICE_KINDS}")
            continue

        entity_id = str(item.get("entity_id", "")).strip()
        if not entity_id:
            issues.append(f"{prefix} is missing entity_id")
            continue

        adapter = str(item.get("adapter", "")).strip().lower() or None
        if adapter is not None and adapter not in KNOWN_ADAPTERS:
            issues.append(f"{prefix} adapter must be one of {KNOWN_ADAPTERS}")
            continue

        nominal_power_w = _as_float(item.get("nominal_power_w"), default=None)
        min_power_w = _as_float(item.get("min_power_w"), default=nominal_power_w)
        max_power_w = _as_float(item.get("max_power_w"), default=nominal_power_w)
        step_w = _as_float(item.get("step_w"), default=100.0 if kind == DEVICE_KIND_VARIABLE else nominal_power_w)
        priority = int(_as_float(item.get("priority"), default=100.0) or 100)
        enabled = bool(item.get("enabled", True))
        min_on_seconds = _as_int(item.get("min_on_seconds"), default=300)
        min_off_seconds = _as_int(item.get("min_off_seconds"), default=300)
        cooldown_seconds = _as_int(item.get("cooldown_seconds"), default=30)

        if nominal_power_w is None or nominal_power_w <= 0:
            issues.append(f"{prefix} nominal_power_w must be a positive number")
            continue
        if min_power_w is None or min_power_w <= 0:
            issues.append(f"{prefix} min_power_w must be a positive number")
            continue
        if max_power_w is None or max_power_w <= 0:
            issues.append(f"{prefix} max_power_w must be a positive number")
            continue
        if step_w is None or step_w <= 0:
            issues.append(f"{prefix} step_w must be a positive number")
            continue
        if min_power_w > max_power_w:
            issues.append(f"{prefix} min_power_w cannot exceed max_power_w")
            continue
        if kind == DEVICE_KIND_FIXED and min_power_w != max_power_w:
            issues.append(f"{prefix} fixed devices must use the same min_power_w and max_power_w")
            continue
        if kind == DEVICE_KIND_VARIABLE and nominal_power_w < min_power_w:
            issues.append(f"{prefix} nominal_power_w cannot be below min_power_w for variable devices")
            continue
        if min_on_seconds is None or min_on_seconds < 0:
            issues.append(f"{prefix} min_on_seconds must be zero or a positive integer")
            continue
        if min_off_seconds is None or min_off_seconds < 0:
            issues.append(f"{prefix} min_off_seconds must be zero or a positive integer")
            continue
        if cooldown_seconds is None or cooldown_seconds < 0:
            issues.append(f"{prefix} cooldown_seconds must be zero or a positive integer")
            continue

        devices.append(
            DeviceConfig(
                key=key,
                name=name,
                kind=kind,
                entity_id=entity_id,
                adapter=adapter,
                nominal_power_w=nominal_power_w,
                min_power_w=min_power_w,
                max_power_w=max_power_w,
                step_w=step_w,
                priority=priority,
                enabled=enabled,
                min_on_seconds=min_on_seconds,
                min_off_seconds=min_off_seconds,
                cooldown_seconds=cooldown_seconds,
            )
        )

    devices.sort(key=lambda item: (item.priority, item.name.lower()))
    return devices, issues


def build_device_summary(
    hass,
    devices: list[DeviceConfig],
    safe_mode: bool,
    overrides: dict[str, dict[str, Any]] | None = None,
) -> DeviceModelSummary:
    runtimes: list[DeviceRuntime] = []
    overrides = overrides or {}

    for device in devices:
        override = overrides.get(device.key, {})
        operator_enabled_override = _coerce_bool_or_none(override.get("operator_enabled_override"))
        operator_priority_override = _coerce_int_or_none(override.get("operator_priority_override"))
        effective_enabled = device.enabled if operator_enabled_override is None else operator_enabled_override
        effective_priority = device.priority if operator_priority_override is None else operator_priority_override
        effective_config = replace(device, enabled=effective_enabled, priority=effective_priority)

        state = hass.states.get(device.entity_id)
        current_power_w = None
        if state is not None:
            try:
                current_power_w = float(state.state)
            except (TypeError, ValueError):
                current_power_w = None

        adapter, adapter_status, adapter_reason = resolve_device_adapter(effective_config)
        observed_active = infer_device_active(effective_config, state, current_power_w)
        usable, status, reason = _evaluate_device(effective_config, state, safe_mode, adapter)
        current_target_power_w = effective_config.nominal_power_w if effective_config.kind == DEVICE_KIND_FIXED and observed_active else None
        if effective_config.kind == DEVICE_KIND_VARIABLE and current_power_w is not None:
            current_target_power_w = current_power_w
        runtimes.append(
            DeviceRuntime(
                config=effective_config,
                usable=usable,
                status=status,
                reason=reason,
                adapter=adapter,
                adapter_status=adapter_status,
                adapter_reason=adapter_reason,
                current_power_w=current_power_w,
                current_target_power_w=current_target_power_w,
                observed_active=observed_active,
                configured_enabled=device.enabled,
                configured_priority=device.priority,
                effective_enabled=effective_enabled,
                effective_priority=effective_priority,
                operator_enabled_override=operator_enabled_override,
                operator_priority_override=operator_priority_override,
            )
        )

    return DeviceModelSummary(
        devices=runtimes,
        total_devices=len(runtimes),
        enabled_devices=sum(1 for runtime in runtimes if runtime.config.enabled),
        usable_devices=sum(1 for runtime in runtimes if runtime.usable),
        fixed_devices=sum(1 for runtime in runtimes if runtime.config.kind == DEVICE_KIND_FIXED),
        variable_devices=sum(1 for runtime in runtimes if runtime.config.kind == DEVICE_KIND_VARIABLE),
        total_nominal_power_w=sum(runtime.config.nominal_power_w for runtime in runtimes),
        usable_nominal_power_w=sum(runtime.config.nominal_power_w for runtime in runtimes if runtime.usable),
    )


def runtime_as_attributes(runtime: DeviceRuntime) -> dict[str, Any]:
    return {
        "entity_id": runtime.config.entity_id,
        "kind": runtime.config.kind,
        "configured_adapter": runtime.config.adapter,
        "resolved_adapter": runtime.adapter.key if runtime.adapter else None,
        "adapter_label": runtime.adapter.label if runtime.adapter else None,
        "adapter_status": runtime.adapter_status,
        "adapter_reason": runtime.adapter_reason,
        "supported_actions": list(runtime.adapter.actions) if runtime.adapter else [],
        "priority": runtime.effective_priority,
        "configured_priority": runtime.configured_priority,
        "effective_priority": runtime.effective_priority,
        "operator_priority_override": runtime.operator_priority_override,
        "enabled": runtime.effective_enabled,
        "configured_enabled": runtime.configured_enabled,
        "effective_enabled": runtime.effective_enabled,
        "operator_enabled_override": runtime.operator_enabled_override,
        "nominal_power_w": runtime.config.nominal_power_w,
        "min_power_w": runtime.config.min_power_w,
        "max_power_w": runtime.config.max_power_w,
        "step_w": runtime.config.step_w,
        "min_on_seconds": runtime.config.min_on_seconds,
        "min_off_seconds": runtime.config.min_off_seconds,
        "cooldown_seconds": runtime.config.cooldown_seconds,
        "observed_active": runtime.observed_active,
    }


def infer_device_active(device: DeviceConfig, state, current_power_w: float | None) -> bool:
    if state is None:
        return False
    raw_state = str(state.state).strip().lower()
    if raw_state in {"unknown", "unavailable"}:
        return False
    if raw_state in ACTIVE_STATE_STRINGS:
        return True
    if raw_state in INACTIVE_STATE_STRINGS:
        return False
    if current_power_w is not None:
        return current_power_w > 0
    return False


def resolve_device_adapter(device: DeviceConfig) -> tuple[DeviceAdapterSpec | None, str, str]:
    domain = device.entity_id.split(".", 1)[0] if "." in device.entity_id else ""

    if device.adapter:
        adapter = ADAPTER_SPECS.get(device.adapter)
        if adapter is None:
            return None, "invalid", f"Configured adapter {device.adapter!r} is not recognised"
        if adapter.kind != device.kind:
            return None, "invalid", f"Adapter {adapter.key} only supports {adapter.kind} devices"
        if domain and domain not in adapter.entity_domains:
            supported = ", ".join(adapter.entity_domains)
            return None, "mismatch", f"Adapter {adapter.key} expects {supported} entities, not {device.entity_id}"
        return adapter, "explicit", f"Using explicitly configured adapter {adapter.key}"

    for adapter in ADAPTER_SPECS.values():
        if adapter.kind == device.kind and domain in adapter.entity_domains:
            return adapter, "inferred", f"Inferred adapter {adapter.key} from {device.entity_id}"

    supported = ", ".join(
        sorted({domain_name for adapter in ADAPTER_SPECS.values() if adapter.kind == device.kind for domain_name in adapter.entity_domains})
    )
    return None, "unsupported", f"No safe {device.kind} adapter is available for {device.entity_id}; supported domains: {supported}"


def _evaluate_device(device: DeviceConfig, state, safe_mode: bool, adapter: DeviceAdapterSpec | None) -> tuple[bool, str, str]:
    if not device.enabled:
        return False, "disabled", "Disabled by operator"
    if adapter is None:
        return False, "unsupported", "No supported device adapter is configured or inferable for this entity"
    if safe_mode:
        return False, "blocked", "Source validation is degraded or blocked; control actions remain disabled"
    if state is None:
        return False, "unavailable", f"Configured entity {device.entity_id} was not found"
    if state.state in {"unknown", "unavailable"}:
        return False, "unavailable", f"Configured entity {device.entity_id} is {state.state}"
    return True, "ready", "Eligible for guarded control with the resolved device adapter"


def _as_float(value: Any, default: float | None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int | None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool_or_none(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    return None


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return normalized.strip("_")
