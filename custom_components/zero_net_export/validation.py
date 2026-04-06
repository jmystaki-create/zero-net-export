"""Source validation helpers for Zero Net Export."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_UNIT_OF_MEASUREMENT

ATTR_STATE_CLASS = "state_class"
from homeassistant.core import HomeAssistant, State

from .const import SOURCE_ROLE_LABELS

POWER_UNITS = {"W", "kW"}
ENERGY_UNITS = {"Wh", "kWh"}
PERCENT_UNITS = {"%"}
TOTAL_STATE_CLASSES = {"total", "total_increasing"}
MEASUREMENT_STATE_CLASS = "measurement"


DERIVED_SOURCE_PREFIX = "znesrc"
DERIVED_SOURCE_MODE_DIRECT = "direct"
DERIVED_SOURCE_MODE_POSITIVE = "positive"
DERIVED_SOURCE_MODE_NEGATIVE_ABS = "negative_abs"


@dataclass(slots=True)
class SourceBinding:
    raw: str | None
    entity_id: str | None
    mode: str
    valid: bool
    error: str | None = None


@dataclass(slots=True)
class SourceReading:
    entity_id: str | None
    value: float | None
    unit: str | None
    raw_state: str | None
    available: bool
    binding: str | None = None
    binding_label: str | None = None
    raw_value: float | None = None


@dataclass(slots=True)
class ValidationIssue:
    code: str
    severity: str
    message: str
    entity_id: str | None = None


@dataclass(slots=True)
class ValidationResult:
    confidence: str
    status: str
    reason: str
    safe_mode: bool
    source_mismatch: bool
    last_reconciliation_error_w: float | None
    surplus_w: float | None
    recommendation: str
    diagnostic_summary: str
    calibration_hints: list[str]
    source_diagnostics: dict[str, dict[str, Any]]
    issues: list[ValidationIssue]


@dataclass(slots=True)
class SourceSpec:
    key: str
    entity_id: str | None
    quantity: str
    required: bool = True
    allow_negative: bool = False


def _role_label(key: str) -> str:
    return SOURCE_ROLE_LABELS.get(key, key)


def parse_source_binding(raw: str | None) -> SourceBinding:
    if not raw:
        return SourceBinding(raw=raw, entity_id=None, mode=DERIVED_SOURCE_MODE_DIRECT, valid=True)
    if not isinstance(raw, str):
        return SourceBinding(raw=str(raw), entity_id=None, mode=DERIVED_SOURCE_MODE_DIRECT, valid=False, error="Binding must be a string")
    if not raw.startswith(f"{DERIVED_SOURCE_PREFIX}:"):
        return SourceBinding(raw=raw, entity_id=raw, mode=DERIVED_SOURCE_MODE_DIRECT, valid=True)

    parts = raw.split(":", 2)
    if len(parts) != 3:
        return SourceBinding(raw=raw, entity_id=None, mode=DERIVED_SOURCE_MODE_DIRECT, valid=False, error="Derived binding format must be znesrc:<mode>:<entity_id>")

    _, mode, entity_id = parts
    if mode not in {DERIVED_SOURCE_MODE_POSITIVE, DERIVED_SOURCE_MODE_NEGATIVE_ABS}:
        return SourceBinding(raw=raw, entity_id=entity_id or None, mode=mode, valid=False, error=f"Unsupported derived binding mode: {mode}")
    if not entity_id:
        return SourceBinding(raw=raw, entity_id=None, mode=mode, valid=False, error="Derived binding is missing an entity id")
    return SourceBinding(raw=raw, entity_id=entity_id, mode=mode, valid=True)


def format_source_binding_label(raw: str | None) -> str:
    binding = parse_source_binding(raw)
    if not binding.raw:
        return "Not configured"
    if not binding.valid:
        return binding.raw
    if binding.mode == DERIVED_SOURCE_MODE_DIRECT:
        return binding.entity_id or binding.raw or "Not configured"
    if binding.mode == DERIVED_SOURCE_MODE_POSITIVE:
        return f"{binding.entity_id} (signed split → positive only)"
    if binding.mode == DERIVED_SOURCE_MODE_NEGATIVE_ABS:
        return f"{binding.entity_id} (signed split → negative becomes positive)"
    return binding.raw or (binding.entity_id or "Not configured")


def _apply_binding_mode(value: float | None, mode: str) -> float | None:
    if value is None:
        return None
    if mode == DERIVED_SOURCE_MODE_DIRECT:
        return value
    if mode == DERIVED_SOURCE_MODE_POSITIVE:
        return max(value, 0.0)
    if mode == DERIVED_SOURCE_MODE_NEGATIVE_ABS:
        return max(-value, 0.0)
    return None


def get_source_reading(hass: HomeAssistant, entity_id: str | None) -> tuple[SourceReading, State | None]:
    binding = parse_source_binding(entity_id)
    if not binding.raw:
        return SourceReading(entity_id=None, value=None, unit=None, raw_state=None, available=False, binding=entity_id, binding_label=format_source_binding_label(entity_id)), None
    if not binding.valid or not binding.entity_id:
        return SourceReading(entity_id=binding.entity_id, value=None, unit=None, raw_state=None, available=False, binding=entity_id, binding_label=format_source_binding_label(entity_id)), None

    state = hass.states.get(binding.entity_id)
    if state is None:
        return SourceReading(entity_id=binding.entity_id, value=None, unit=None, raw_state=None, available=False, binding=entity_id, binding_label=format_source_binding_label(entity_id)), None

    try:
        raw_value = float(state.state)
    except (TypeError, ValueError):
        raw_value = None

    return (
        SourceReading(
            entity_id=binding.entity_id,
            value=_apply_binding_mode(raw_value, binding.mode),
            unit=state.attributes.get(ATTR_UNIT_OF_MEASUREMENT),
            raw_state=state.state,
            available=state.state not in {"unknown", "unavailable"},
            binding=entity_id,
            binding_label=format_source_binding_label(entity_id),
            raw_value=raw_value,
        ),
        state,
    )


def _expected_units(quantity: str) -> set[str]:
    if quantity == "power":
        return POWER_UNITS
    if quantity == "energy":
        return ENERGY_UNITS
    if quantity == "percent":
        return PERCENT_UNITS
    return set()


def _expected_state_class(quantity: str) -> str | set[str] | None:
    if quantity in {"power", "percent"}:
        return MEASUREMENT_STATE_CLASS
    if quantity == "energy":
        return TOTAL_STATE_CLASSES
    return None


def _check_metadata(state: State | None, spec: SourceSpec, issues: list[ValidationIssue]) -> None:
    if state is None:
        return

    unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
    expected_units = _expected_units(spec.quantity)
    if expected_units and unit not in expected_units:
        issues.append(
            ValidationIssue(
                code=f"{spec.key}_unexpected_unit",
                severity="warning",
                message=f"{_role_label(spec.key)} uses unit {unit!r}; expected one of {sorted(expected_units)}",
                entity_id=spec.entity_id,
            )
        )

    state_class = state.attributes.get(ATTR_STATE_CLASS)
    expected_state_class = _expected_state_class(spec.quantity)
    if isinstance(expected_state_class, set):
        if state_class not in expected_state_class:
            issues.append(
                ValidationIssue(
                    code=f"{spec.key}_unexpected_state_class",
                    severity="warning",
                    message=f"{_role_label(spec.key)} state_class is {state_class!r}; expected one of {sorted(expected_state_class)}",
                    entity_id=spec.entity_id,
                )
            )
    elif expected_state_class and state_class != expected_state_class:
        issues.append(
            ValidationIssue(
                code=f"{spec.key}_unexpected_state_class",
                severity="warning",
                message=f"{_role_label(spec.key)} state_class is {state_class!r}; expected {expected_state_class!r}",
                entity_id=spec.entity_id,
            )
        )

    device_class = state.attributes.get(ATTR_DEVICE_CLASS)
    if spec.quantity == "power" and device_class not in {None, "power"}:
        issues.append(
            ValidationIssue(
                code=f"{spec.key}_unexpected_device_class",
                severity="warning",
                message=f"{_role_label(spec.key)} device_class is {device_class!r}; expected 'power'",
                entity_id=spec.entity_id,
            )
        )
    if spec.quantity == "energy" and device_class not in {None, "energy"}:
        issues.append(
            ValidationIssue(
                code=f"{spec.key}_unexpected_device_class",
                severity="warning",
                message=f"{_role_label(spec.key)} device_class is {device_class!r}; expected 'energy'",
                entity_id=spec.entity_id,
            )
        )
    if spec.quantity == "percent" and device_class not in {None, "battery", "power_factor"}:
        issues.append(
            ValidationIssue(
                code=f"{spec.key}_unexpected_device_class",
                severity="info",
                message=f"{_role_label(spec.key)} device_class is {device_class!r}; battery-like percent sensor expected",
                entity_id=spec.entity_id,
            )
        )


def validate_configured_entities(
    hass: HomeAssistant,
    configs: dict[str, str | int | float | None],
    specs: list[SourceSpec],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen_entities: dict[str, str] = {}

    for spec in specs:
        entity_id = configs.get(spec.key)
        if not entity_id:
            if spec.required:
                issues.append(
                    ValidationIssue(
                        code=f"{spec.key}_not_configured",
                        severity="error",
                        message=f"{_role_label(spec.key)} is required but not configured",
                    )
                )
            continue

        if not isinstance(entity_id, str):
            issues.append(
                ValidationIssue(
                    code=f"{spec.key}_invalid_entity_id",
                    severity="error",
                    message=f"{_role_label(spec.key)} must be an entity id string",
                )
            )
            continue

        binding = parse_source_binding(entity_id)
        if not binding.valid or not binding.entity_id:
            issues.append(
                ValidationIssue(
                    code=f"{spec.key}_invalid_entity_id",
                    severity="error",
                    message=f"{_role_label(spec.key)} binding is invalid: {binding.error or 'unknown binding error'}",
                    entity_id=entity_id,
                )
            )
            continue

        previous_key = seen_entities.get(entity_id)
        if previous_key is not None:
            issues.append(
                ValidationIssue(
                    code=f"{spec.key}_duplicate_entity",
                    severity="error",
                    message=f"{_role_label(spec.key)} reuses {format_source_binding_label(entity_id)}, already assigned to {_role_label(previous_key)}",
                    entity_id=binding.entity_id,
                )
            )
            continue
        seen_entities[entity_id] = spec.key

        reading, state = get_source_reading(hass, entity_id)
        if state is None:
            issues.append(
                ValidationIssue(
                    code=f"{spec.key}_missing_entity",
                    severity="error" if spec.required else "warning",
                    message=f"{_role_label(spec.key)} entity {binding.entity_id} was not found in Home Assistant",
                    entity_id=binding.entity_id,
                )
            )
            continue

        if not reading.available:
            issues.append(
                ValidationIssue(
                    code=f"{spec.key}_unavailable",
                    severity="error" if spec.required else "warning",
                    message=f"{_role_label(spec.key)} entity {entity_id} is unavailable",
                    entity_id=entity_id,
                )
            )
            continue

        if reading.value is None:
            issues.append(
                ValidationIssue(
                    code=f"{spec.key}_non_numeric",
                    severity="error" if spec.required else "warning",
                    message=f"{_role_label(spec.key)} entity {entity_id} does not currently expose a numeric state",
                    entity_id=entity_id,
                )
            )
            continue

        _check_metadata(state, spec, issues)

    return issues


def build_recommendation(issues: list[ValidationIssue]) -> str:
    issue_codes = {issue.code for issue in issues}

    if not issues:
        return "Validation healthy; safe to start device modelling on top of these sources"

    if any(issue.severity == "error" for issue in issues):
        if any(code.endswith("_missing_entity") or code.endswith("_not_configured") for code in issue_codes):
            return "Complete the required source mapping before enabling any control actions"
        if any(code.endswith("_duplicate_entity") for code in issue_codes):
            return "Assign distinct Home Assistant entities to each logical role; import and export cannot safely share one source"
        if any(code.endswith("_non_numeric") or code.endswith("_unavailable") for code in issue_codes):
            return "Choose stable numeric sensors for required roles or fix entity availability before enabling control"
        return "Resolve blocking source errors before allowing live control"

    if "power_reconciliation_large_error" in issue_codes:
        return "Check sign conventions and source role mapping; one or more power sensors likely uses the opposite import/export direction"
    if "grid_import_export_overlap" in issue_codes:
        return "Prefer a net-grid sensor split or correct import/export mapping; both grid directions should not stay materially positive together"
    if "battery_charge_discharge_overlap" in issue_codes:
        return "Check battery charge/discharge sign handling or map only one native direction per sensor"
    if any(code.endswith("_unexpected_unit") for code in issue_codes):
        return "Pick sensors with native W, kW, Wh, or kWh units so control calculations stay explainable"
    if any(code.endswith("_unexpected_state_class") or code.endswith("_unexpected_device_class") for code in issue_codes):
        return "Prefer Home Assistant energy-dashboard-friendly sensors with matching device_class and state_class metadata"
    if "battery_soc_out_of_range" in issue_codes:
        return "Verify battery state-of-charge scaling; the controller expects a percent value between 0 and 100"

    return "Warnings remain; keep the integration in monitor mode until the source model reconciles cleanly"


def build_diagnostic_summary(
    issues: list[ValidationIssue],
    reconciliation_error: float | None,
    source_diagnostics: dict[str, dict[str, Any]],
) -> str:
    if not issues:
        return "Source model looks internally consistent; no calibration issues detected right now"

    issue_codes = {issue.code for issue in issues}
    unavailable = [key for key, diagnostic in source_diagnostics.items() if diagnostic["status"] == "unavailable"]
    non_numeric = [key for key, diagnostic in source_diagnostics.items() if diagnostic["status"] == "non_numeric"]
    metadata_warning_sources = [
        key for key, diagnostic in source_diagnostics.items() if diagnostic["issue_counts"]["warning"] > 0 and diagnostic["status"] == "ok"
    ]

    if any(issue.severity == "error" for issue in issues):
        if unavailable:
            return f"Blocking source outage: {', '.join(_role_label(key) for key in unavailable)} is unavailable or missing"
        if non_numeric:
            return f"Blocking source type issue: {', '.join(_role_label(key) for key in non_numeric)} is not exposing a numeric reading"
        return "Blocking source validation errors remain; safe mode is preventing control"

    if "grid_import_export_overlap" in issue_codes:
        return "Grid import and export are positive together; the grid split likely needs sign or role correction"
    if "battery_charge_discharge_overlap" in issue_codes:
        return "Battery charge and discharge are positive together; battery direction mapping likely needs correction"
    if "power_reconciliation_large_error" in issue_codes and reconciliation_error is not None:
        direction = "higher" if reconciliation_error > 0 else "lower"
        return (
            "Power sources do not reconcile cleanly; "
            f"home load reads about {abs(reconciliation_error):.0f} W {direction} than the other flows imply"
        )
    if metadata_warning_sources:
        return (
            "Source values are numeric but some metadata is off; review units/device_class/state_class for "
            + ", ".join(metadata_warning_sources)
        )
    return "Source validation warnings remain; review them, but only blocking errors or stale required data should hold the controller in safe mode"


def build_calibration_hints(
    issues: list[ValidationIssue],
    reconciliation_error: float | None,
    source_diagnostics: dict[str, dict[str, Any]],
) -> list[str]:
    hints: list[str] = []
    issue_codes = {issue.code for issue in issues}

    if not issues:
        return ["No validation issues detected; source calibration currently looks healthy"]

    if any(issue.severity == "error" for issue in issues):
        missing_or_unavailable = [
            key
            for key, diagnostic in source_diagnostics.items()
            if diagnostic["status"] in {"missing", "unavailable", "non_numeric"}
        ]
        if missing_or_unavailable:
            hints.append(
                "Restore stable numeric readings for: " + ", ".join(missing_or_unavailable)
            )

    if "power_reconciliation_large_error" in issue_codes:
        if reconciliation_error is not None and reconciliation_error > 0:
            hints.append(
                "The configured home-load path may be overstated, or one supply path may have the opposite sign to the others"
            )
        elif reconciliation_error is not None and reconciliation_error < 0:
            hints.append(
                "The configured home-load path may be understated, or export/charge flow may be sign-inverted"
            )
        hints.append(
            "Compare all power sensors during an obvious export period and verify that import/charge stay near zero while export/discharge rise"
        )

    if "grid_import_export_overlap" in issue_codes:
        hints.append(
            "Check whether one grid sensor is actually net flow with signed values; if so, split it explicitly instead of mapping the same sign into both directions"
        )

    if "battery_charge_discharge_overlap" in issue_codes:
        hints.append(
            "Map battery charge and discharge as separate positive-only directions, or leave the absent direction unmapped if the integration exposes signed net battery power"
        )

    if any(code.endswith("_unexpected_unit") for code in issue_codes):
        hints.append("Prefer sensors with native W/kW or Wh/kWh units so scaling stays explicit and explainable")

    if any(code.endswith("_unexpected_state_class") or code.endswith("_unexpected_device_class") for code in issue_codes):
        hints.append(
            "Prefer energy-dashboard-friendly sensors with matching device_class/state_class metadata so validation can trust their semantics"
        )

    if "battery_soc_out_of_range" in issue_codes:
        hints.append("Battery SOC should be a real 0-100 percent sensor, not a 0-1 fraction or vendor-specific scale")

    if not hints:
        hints.append("Warnings remain; inspect the validation issue list for the exact source roles involved")

    deduped: list[str] = []
    for hint in hints:
        if hint not in deduped:
            deduped.append(hint)
    return deduped


def build_source_diagnostics(
    readings: dict[str, SourceReading],
    states: dict[str, State | None],
    specs: list[SourceSpec],
    issues: list[ValidationIssue],
) -> dict[str, dict[str, Any]]:
    diagnostics: dict[str, dict[str, Any]] = {}

    for spec in specs:
        reading = readings[spec.key]
        state = states[spec.key]
        related_issues = [issue for issue in issues if issue.code.startswith(f"{spec.key}_")]
        severity_counts = {
            "error": sum(1 for issue in related_issues if issue.severity == "error"),
            "warning": sum(1 for issue in related_issues if issue.severity == "warning"),
            "info": sum(1 for issue in related_issues if issue.severity == "info"),
        }

        status = "ok"
        if not spec.entity_id:
            status = "missing"
        elif state is None or not reading.available:
            status = "unavailable"
        elif reading.value is None:
            status = "non_numeric"
        elif severity_counts["error"] > 0:
            status = "error"
        elif severity_counts["warning"] > 0:
            status = "warning"
        elif severity_counts["info"] > 0:
            status = "info"

        diagnostics[spec.key] = {
            "entity_id": reading.entity_id,
            "binding": reading.binding,
            "binding_label": reading.binding_label,
            "required": spec.required,
            "quantity": spec.quantity,
            "status": status,
            "available": reading.available,
            "value": reading.value,
            "raw_value": reading.raw_value,
            "raw_state": reading.raw_state,
            "unit": reading.unit,
            "state_class": state.attributes.get(ATTR_STATE_CLASS) if state else None,
            "device_class": state.attributes.get(ATTR_DEVICE_CLASS) if state else None,
            "issues": [
                {
                    "code": issue.code,
                    "severity": issue.severity,
                    "message": issue.message,
                }
                for issue in related_issues
            ],
            "issue_counts": severity_counts,
        }

    return diagnostics


def validate_sources(
    readings: dict[str, SourceReading],
    states: dict[str, State | None],
    specs: list[SourceSpec],
) -> ValidationResult:
    issues: list[ValidationIssue] = []

    for spec in specs:
        reading = readings[spec.key]
        if spec.required and not spec.entity_id:
            issues.append(
                ValidationIssue(
                    code=f"{spec.key}_not_configured",
                    severity="error",
                    message=f"{_role_label(spec.key)} is required but not configured",
                )
            )
            continue

        if spec.entity_id and not reading.available:
            issues.append(
                ValidationIssue(
                    code=f"{spec.key}_unavailable",
                    severity="error" if spec.required else "warning",
                    message=f"{_role_label(spec.key)} is unavailable",
                    entity_id=spec.entity_id,
                )
            )
            continue

        if spec.entity_id and reading.value is None:
            issues.append(
                ValidationIssue(
                    code=f"{spec.key}_non_numeric",
                    severity="error" if spec.required else "warning",
                    message=f"{_role_label(spec.key)} does not expose a numeric state",
                    entity_id=spec.entity_id,
                )
            )
            continue

        if reading.value is not None and not spec.allow_negative and reading.value < 0:
            issues.append(
                ValidationIssue(
                    code=f"{spec.key}_negative_value",
                    severity="warning",
                    message=f"{_role_label(spec.key)} reported a negative value {reading.value}",
                    entity_id=spec.entity_id,
                )
            )

        _check_metadata(states[spec.key], spec, issues)

    solar = readings["solar_power"].value
    home = readings["home_load_power"].value
    grid_import = readings["grid_import_power"].value or 0.0
    grid_export = readings["grid_export_power"].value or 0.0
    battery_charge = readings["battery_charge_power"].value or 0.0
    battery_discharge = readings["battery_discharge_power"].value or 0.0
    battery_soc = readings["battery_soc"].value

    reconciliation_error = None
    if solar is not None and home is not None:
        inferred_home = solar + grid_import + battery_discharge - grid_export - battery_charge
        reconciliation_error = home - inferred_home
        if abs(reconciliation_error) > 250:
            issues.append(
                ValidationIssue(
                    code="power_reconciliation_large_error",
                    severity="warning",
                    message=(
                        "Power sources do not reconcile closely; "
                        f"error is {reconciliation_error:.0f} W"
                    ),
                )
            )

    if readings["grid_import_power"].value and readings["grid_export_power"].value:
        if readings["grid_import_power"].value > 50 and readings["grid_export_power"].value > 50:
            issues.append(
                ValidationIssue(
                    code="grid_import_export_overlap",
                    severity="warning",
                    message="Grid import and export are both materially positive at the same time",
                )
            )

    if battery_charge > 50 and battery_discharge > 50:
        issues.append(
            ValidationIssue(
                code="battery_charge_discharge_overlap",
                severity="warning",
                message="Battery charge and discharge are both materially positive at the same time",
            )
        )

    if battery_soc is not None and not 0 <= battery_soc <= 100:
        issues.append(
            ValidationIssue(
                code="battery_soc_out_of_range",
                severity="warning",
                message=f"battery_soc is outside 0-100%: {battery_soc}",
                entity_id=readings["battery_soc"].entity_id,
            )
        )

    source_diagnostics = build_source_diagnostics(readings, states, specs, issues)

    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")

    confidence = "high"
    status = "validated"
    safe_mode = False

    if error_count:
        confidence = "low"
        status = "blocked"
        safe_mode = True
    elif warning_count:
        confidence = "medium"
        status = "degraded"
        safe_mode = False

    surplus_w = None
    if solar is not None and home is not None:
        surplus_w = solar + grid_import + battery_discharge - home - battery_charge - grid_export

    if error_count:
        top_issue = next(issue for issue in issues if issue.severity == "error")
        reason = f"Validation blocked: {top_issue.message}"
    elif warning_count:
        top_issue = next(issue for issue in issues if issue.severity == "warning")
        reason = f"Validation degraded: {top_issue.message}"
    else:
        reason = "Source validation passed; inputs reconcile within tolerance"

    return ValidationResult(
        confidence=confidence,
        status=status,
        reason=reason,
        safe_mode=safe_mode,
        source_mismatch=error_count > 0 or warning_count > 0,
        last_reconciliation_error_w=reconciliation_error,
        surplus_w=surplus_w,
        recommendation=build_recommendation(issues),
        diagnostic_summary=build_diagnostic_summary(issues, reconciliation_error, source_diagnostics),
        calibration_hints=build_calibration_hints(issues, reconciliation_error, source_diagnostics),
        source_diagnostics=source_diagnostics,
        issues=issues,
    )


def issues_as_attributes(issues: list[ValidationIssue]) -> dict[str, Any]:
    return {
        "issue_count": len(issues),
        "issues": [
            {
                "code": issue.code,
                "severity": issue.severity,
                "message": issue.message,
                "entity_id": issue.entity_id,
            }
            for issue in issues
        ],
    }
