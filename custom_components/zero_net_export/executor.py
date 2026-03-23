"""Guarded Home Assistant action executor for Zero Net Export."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .device_model import ADAPTER_FIXED_TOGGLE, ADAPTER_VARIABLE_NUMBER, DEVICE_KIND_VARIABLE, DeviceRuntime
from .planner import PlannedDeviceAction


@dataclass(slots=True)
class ActionResult:
    device_key: str
    name: str
    entity_id: str
    action: str
    requested_power_w: float | None
    success: bool
    status: str
    message: str
    service: str | None
    service_data: dict[str, Any] | None


async def execute_action(
    hass: HomeAssistant,
    runtime: DeviceRuntime,
    planned: PlannedDeviceAction,
) -> ActionResult:
    """Execute one already guard-approved planned action.

    This is intentionally narrow for the first live-control milestone:
    - fixed devices use entity-domain turn_on / turn_off services
    - variable devices use number/input_number.set_value
    - unknown domains remain unsupported and are reported clearly
    """

    entity_id = runtime.config.entity_id

    try:
        service, data = _build_service_call(runtime, planned)
    except ValueError as err:
        return ActionResult(
            device_key=runtime.config.key,
            name=runtime.config.name,
            entity_id=entity_id,
            action=planned.action,
            requested_power_w=planned.requested_power_w,
            success=False,
            status="unsupported",
            message=str(err),
            service=None,
            service_data=None,
        )

    try:
        await hass.services.async_call(
            domain=service[0],
            service=service[1],
            service_data=data,
            blocking=True,
        )
    except HomeAssistantError as err:
        return ActionResult(
            device_key=runtime.config.key,
            name=runtime.config.name,
            entity_id=entity_id,
            action=planned.action,
            requested_power_w=planned.requested_power_w,
            success=False,
            status="failed",
            message=f"Service call failed: {err}",
            service=f"{service[0]}.{service[1]}",
            service_data=data,
        )

    return ActionResult(
        device_key=runtime.config.key,
        name=runtime.config.name,
        entity_id=entity_id,
        action=planned.action,
        requested_power_w=planned.requested_power_w,
        success=True,
        status="applied",
        message=_success_message(runtime, planned),
        service=f"{service[0]}.{service[1]}",
        service_data=data,
    )


def _build_service_call(
    runtime: DeviceRuntime,
    planned: PlannedDeviceAction,
) -> tuple[tuple[str, str], dict[str, Any]]:
    domain = runtime.config.entity_id.split(".", 1)[0] if "." in runtime.config.entity_id else ""
    adapter_key = runtime.adapter.key if runtime.adapter else None

    if adapter_key == ADAPTER_FIXED_TOGGLE and planned.action in {"turn_on", "turn_off"}:
        if not domain:
            raise ValueError(f"{runtime.config.name} has an invalid entity_id {runtime.config.entity_id!r}")
        return (domain, planned.action), {"entity_id": runtime.config.entity_id}

    if adapter_key == ADAPTER_VARIABLE_NUMBER and planned.action in {"increase", "decrease"} and runtime.config.kind == DEVICE_KIND_VARIABLE:
        if planned.requested_power_w is None:
            raise ValueError(f"{runtime.config.name} variable action is missing requested_power_w")
        return (domain, "set_value"), {
            "entity_id": runtime.config.entity_id,
            "value": planned.requested_power_w,
        }

    raise ValueError(
        f"{runtime.config.name} action {planned.action!r} is not supported by adapter {adapter_key or 'none'}"
    )


def _success_message(runtime: DeviceRuntime, planned: PlannedDeviceAction) -> str:
    if planned.action in {"turn_on", "turn_off"}:
        return f"Applied {planned.action} to {runtime.config.entity_id}"
    return (
        f"Set {runtime.config.entity_id} to about {round(planned.requested_power_w or 0)} W "
        f"via {planned.action} action"
    )
