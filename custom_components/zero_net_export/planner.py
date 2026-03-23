"""Explanation-first control planning for Zero Net Export."""
from __future__ import annotations

from dataclasses import dataclass
import math

from .const import MODE_IMPORT_MIN, MODE_MANUAL_HOLD, MODE_SELF_CONSUMPTION_MAX, MODE_SOFT_ZERO_EXPORT
from .device_model import DEVICE_KIND_FIXED, DEVICE_KIND_VARIABLE, DeviceRuntime


@dataclass(slots=True)
class PlannedDeviceAction:
    """Advisory action for a single controllable device."""

    device_key: str
    name: str
    kind: str
    action: str
    requested_power_w: float | None
    delta_power_w: float
    priority: int
    reason: str


@dataclass(slots=True)
class ControlPlan:
    """Control-loop decision for the current coordinator cycle."""

    status: str
    summary: str
    reason: str
    export_error_w: float | None
    action_count: int
    planned_power_delta_w: float
    variable_power_delta_w: float
    fixed_power_delta_w: float
    actions: list[PlannedDeviceAction]


@dataclass(slots=True)
class PlannerContext:
    enabled: bool
    mode: str
    safe_mode: bool
    target_export_w: float
    deadband_w: float
    grid_import_power_w: float | None
    grid_export_power_w: float | None
    battery_soc: float | None
    battery_reserve_soc: float


@dataclass(slots=True)
class ModePolicy:
    effective_target_export_w: float
    allow_fixed_absorb: bool
    allow_surplus_absorb: bool
    label: str
    reason: str


def build_control_plan(context: PlannerContext, devices: list[DeviceRuntime]) -> ControlPlan:
    """Build the advisory plan for the current coordinator cycle.

    The planner remains pure decision logic: it converts export/import error plus
    usable device inventory into an explainable action plan. The coordinator may
    later pass guard-approved actions from that plan to the executor.
    """

    if not context.enabled:
        return ControlPlan(
            status="disabled",
            summary="Control disabled by operator",
            reason="The controller switch is off, so no device actions are planned.",
            export_error_w=None,
            action_count=0,
            planned_power_delta_w=0.0,
            variable_power_delta_w=0.0,
            fixed_power_delta_w=0.0,
            actions=[],
        )

    if context.mode == MODE_MANUAL_HOLD:
        return ControlPlan(
            status="manual_hold",
            summary="Manual hold mode is active",
            reason="Zero Net Export is monitoring sources but intentionally holding device targets steady.",
            export_error_w=None,
            action_count=0,
            planned_power_delta_w=0.0,
            variable_power_delta_w=0.0,
            fixed_power_delta_w=0.0,
            actions=[],
        )

    if context.safe_mode:
        return ControlPlan(
            status="blocked",
            summary="Safe mode is blocking control actions",
            reason="Source validation is degraded or blocked, so the planner will not recommend device actions.",
            export_error_w=None,
            action_count=0,
            planned_power_delta_w=0.0,
            variable_power_delta_w=0.0,
            fixed_power_delta_w=0.0,
            actions=[],
        )

    if context.grid_export_power_w is None or context.grid_import_power_w is None:
        return ControlPlan(
            status="blocked",
            summary="Grid power readings are incomplete",
            reason="Both grid import and grid export power are required before the planner can compute export error.",
            export_error_w=None,
            action_count=0,
            planned_power_delta_w=0.0,
            variable_power_delta_w=0.0,
            fixed_power_delta_w=0.0,
            actions=[],
        )

    usable_devices = [device for device in devices if device.usable]
    mode_policy = _mode_policy(context)
    export_error_w = _export_error_w(context, mode_policy)

    if not usable_devices:
        return ControlPlan(
            status="waiting_for_devices",
            summary="No usable devices are currently available",
            reason=(
                "Source validation is healthy, but no enabled controllable devices are ready for planning. "
                f"{mode_policy.reason}"
            ),
            export_error_w=export_error_w,
            action_count=0,
            planned_power_delta_w=0.0,
            variable_power_delta_w=0.0,
            fixed_power_delta_w=0.0,
            actions=[],
        )

    if abs(export_error_w) <= context.deadband_w:
        return ControlPlan(
            status="holding",
            summary=(
                f"Within deadband for {mode_policy.label}; holding steady at export error {round(export_error_w)} W"
            ),
            reason=(
                f"Current net export is already close enough to the {mode_policy.label} target of "
                f"about {round(mode_policy.effective_target_export_w)} W. {mode_policy.reason}"
            ),
            export_error_w=export_error_w,
            action_count=0,
            planned_power_delta_w=0.0,
            variable_power_delta_w=0.0,
            fixed_power_delta_w=0.0,
            actions=[],
        )

    if export_error_w > 0:
        if not mode_policy.allow_surplus_absorb:
            return ControlPlan(
                status="battery_reserve_hold",
                summary=(
                    f"Surplus export detected ({round(export_error_w)} W), but battery reserve protection is holding discretionary loads"
                ),
                reason=(
                    f"Battery state of charge is below the configured reserve of about {round(context.battery_reserve_soc)}%. "
                    f"{mode_policy.reason} Surplus-absorption actions are being held so the battery can recover first."
                ),
                export_error_w=export_error_w,
                action_count=0,
                planned_power_delta_w=0.0,
                variable_power_delta_w=0.0,
                fixed_power_delta_w=0.0,
                actions=[],
            )
        return _plan_absorb_surplus(export_error_w, usable_devices, mode_policy)
    return _plan_reduce_load(abs(export_error_w), usable_devices, mode_policy)


def _mode_policy(context: PlannerContext) -> ModePolicy:
    configured_target = float(context.target_export_w)
    deadband = max(float(context.deadband_w), 0.0)
    battery_reserve_active = _battery_reserve_active(context)
    reserve_reason = ""
    if battery_reserve_active:
        reserve_reason = (
            f" Battery reserve protection is active because battery SOC is about {round(context.battery_soc or 0)}% "
            f"and the configured reserve is {round(context.battery_reserve_soc)}%."
        )

    if context.mode == MODE_SOFT_ZERO_EXPORT:
        effective_target = max(configured_target, deadband)
        return ModePolicy(
            effective_target_export_w=effective_target,
            allow_fixed_absorb=True,
            allow_surplus_absorb=not battery_reserve_active,
            label="Soft Zero Export",
            reason="Soft Zero Export tolerates a small export margin before it starts soaking surplus aggressively." + reserve_reason,
        )

    if context.mode == MODE_SELF_CONSUMPTION_MAX:
        effective_target = min(configured_target, -deadband)
        return ModePolicy(
            effective_target_export_w=effective_target,
            allow_fixed_absorb=True,
            allow_surplus_absorb=not battery_reserve_active,
            label="Self-Consumption Max",
            reason="Self-Consumption Max biases the target slightly below zero so controllable loads can soak more surplus." + reserve_reason,
        )

    if context.mode == MODE_IMPORT_MIN:
        effective_target = max(configured_target, deadband)
        return ModePolicy(
            effective_target_export_w=effective_target,
            allow_fixed_absorb=False,
            allow_surplus_absorb=not battery_reserve_active,
            label="Import Min",
            reason="Import Min avoids turning on coarse fixed loads just to chase small exports, but it still sheds discretionary load on import pressure." + reserve_reason,
        )

    return ModePolicy(
        effective_target_export_w=configured_target,
        allow_fixed_absorb=True,
        allow_surplus_absorb=not battery_reserve_active,
        label="Zero Export",
        reason="Zero Export uses the configured export target directly and balances variable then fixed loads around it." + reserve_reason,
    )


def _battery_reserve_active(context: PlannerContext) -> bool:
    if context.battery_soc is None:
        return False
    return float(context.battery_soc) < float(context.battery_reserve_soc)


def _export_error_w(context: PlannerContext, mode_policy: ModePolicy) -> float:
    net_export_w = (context.grid_export_power_w or 0.0) - (context.grid_import_power_w or 0.0)
    return net_export_w - mode_policy.effective_target_export_w


def _plan_absorb_surplus(export_error_w: float, devices: list[DeviceRuntime], mode_policy: ModePolicy) -> ControlPlan:
    remaining_w = export_error_w
    actions: list[PlannedDeviceAction] = []
    variable_delta_w = 0.0
    fixed_delta_w = 0.0

    variable_devices = sorted(
        [device for device in devices if device.config.kind == DEVICE_KIND_VARIABLE],
        key=lambda device: (device.config.priority, device.config.name.lower()),
    )
    fixed_devices = sorted(
        [device for device in devices if device.config.kind == DEVICE_KIND_FIXED],
        key=lambda device: (device.config.priority, device.config.name.lower()),
    )

    for device in variable_devices:
        if remaining_w <= 0:
            break
        current_target_w = _variable_current_target_w(device)
        available_headroom_w = max(device.config.max_power_w - current_target_w, 0.0)
        if available_headroom_w <= 0:
            continue

        delta_w = min(available_headroom_w, remaining_w)
        delta_w = _quantize_down(delta_w, device.config.step_w)
        if delta_w <= 0:
            continue

        requested_power_w = current_target_w + delta_w
        requested_power_w = min(requested_power_w, device.config.max_power_w)
        requested_power_w = _quantize_down(requested_power_w, device.config.step_w)

        if current_target_w <= 0 and requested_power_w < device.config.min_power_w:
            requested_power_w = _quantize_up(device.config.min_power_w, device.config.step_w)
            if requested_power_w > device.config.max_power_w:
                continue

        actual_delta_w = max(requested_power_w - current_target_w, 0.0)
        if actual_delta_w <= 0:
            continue

        remaining_w -= actual_delta_w
        variable_delta_w += actual_delta_w
        actions.append(
            PlannedDeviceAction(
                device_key=device.config.key,
                name=device.config.name,
                kind=device.config.kind,
                action="increase",
                requested_power_w=requested_power_w,
                delta_power_w=actual_delta_w,
                priority=device.config.priority,
                reason=(
                    f"Increase variable target from about {round(current_target_w)} W to about {round(requested_power_w)} W "
                    f"to absorb roughly {round(actual_delta_w)} W of surplus export."
                ),
            )
        )

    if mode_policy.allow_fixed_absorb:
        for device in fixed_devices:
            if remaining_w <= 0:
                break
            fixed_delta_w += device.config.nominal_power_w
            remaining_w -= device.config.nominal_power_w
            actions.append(
                PlannedDeviceAction(
                    device_key=device.config.key,
                    name=device.config.name,
                    kind=device.config.kind,
                    action="turn_on",
                    requested_power_w=device.config.nominal_power_w,
                    delta_power_w=device.config.nominal_power_w,
                    priority=device.config.priority,
                    reason=f"Enable fixed load to absorb coarse surplus in {round(device.config.nominal_power_w)} W steps.",
                )
            )

    planned_power_delta_w = variable_delta_w + fixed_delta_w
    uncovered_w = max(remaining_w, 0.0)
    summary = (
        f"Planned {len(actions)} action(s) to absorb about {round(planned_power_delta_w)} W "
        f"against {round(export_error_w)} W of excess export in {mode_policy.label} mode"
    )
    reason = (
        f"{mode_policy.reason} Prioritised variable devices for fine control"
        + (", then fixed loads for coarse absorption." if mode_policy.allow_fixed_absorb else "; fixed-load absorption is intentionally disabled in this mode.")
    )
    if not actions:
        summary = (
            f"Excess export detected ({round(export_error_w)} W), but no usable devices had absorbable headroom "
            f"for {mode_policy.label} mode"
        )
        reason = (
            "Configured devices are usable, but none could accept a safe positive power allocation in this advisory planner. "
            f"{mode_policy.reason}"
        )
    elif uncovered_w > 0:
        reason = (
            f"{mode_policy.reason} Planned all currently modelled headroom, but about {round(uncovered_w)} W of surplus would still remain."
        )

    return ControlPlan(
        status="plan_ready" if actions else "blocked",
        summary=summary,
        reason=reason,
        export_error_w=export_error_w,
        action_count=len(actions),
        planned_power_delta_w=planned_power_delta_w,
        variable_power_delta_w=variable_delta_w,
        fixed_power_delta_w=fixed_delta_w,
        actions=actions,
    )


def _plan_reduce_load(import_error_w: float, devices: list[DeviceRuntime], mode_policy: ModePolicy) -> ControlPlan:
    remaining_w = import_error_w
    actions: list[PlannedDeviceAction] = []
    variable_delta_w = 0.0
    fixed_delta_w = 0.0

    variable_devices = sorted(
        [device for device in devices if device.config.kind == DEVICE_KIND_VARIABLE],
        key=lambda device: (device.config.priority, device.config.name.lower()),
        reverse=True,
    )
    fixed_devices = sorted(
        [device for device in devices if device.config.kind == DEVICE_KIND_FIXED],
        key=lambda device: (device.config.priority, device.config.name.lower()),
        reverse=True,
    )

    for device in variable_devices:
        if remaining_w <= 0:
            break
        current_target_w = _variable_current_target_w(device)
        if current_target_w <= 0:
            continue

        minimum_target_w = device.config.min_power_w if current_target_w > 0 else 0.0
        shedable_w = max(current_target_w - minimum_target_w, 0.0)
        if shedable_w <= 0:
            continue

        delta_w = min(shedable_w, remaining_w)
        delta_w = _quantize_down(delta_w, device.config.step_w)
        if delta_w <= 0:
            continue

        requested_power_w = max(current_target_w - delta_w, minimum_target_w)
        requested_power_w = _quantize_down(requested_power_w, device.config.step_w)
        requested_power_w = max(requested_power_w, minimum_target_w)

        actual_delta_w = max(current_target_w - requested_power_w, 0.0)
        if actual_delta_w <= 0:
            continue

        remaining_w -= actual_delta_w
        variable_delta_w -= actual_delta_w
        actions.append(
            PlannedDeviceAction(
                device_key=device.config.key,
                name=device.config.name,
                kind=device.config.kind,
                action="decrease",
                requested_power_w=requested_power_w,
                delta_power_w=-actual_delta_w,
                priority=device.config.priority,
                reason=(
                    f"Reduce variable target from about {round(current_target_w)} W to about {round(requested_power_w)} W "
                    f"to shed roughly {round(actual_delta_w)} W of discretionary load."
                ),
            )
        )

    for device in fixed_devices:
        if remaining_w <= 0:
            break
        remaining_w -= device.config.nominal_power_w
        fixed_delta_w -= device.config.nominal_power_w
        actions.append(
            PlannedDeviceAction(
                device_key=device.config.key,
                name=device.config.name,
                kind=device.config.kind,
                action="turn_off",
                requested_power_w=0.0,
                delta_power_w=-device.config.nominal_power_w,
                priority=device.config.priority,
                reason=f"Advisory fixed-load shed step worth about {round(device.config.nominal_power_w)} W.",
            )
        )

    planned_power_delta_w = variable_delta_w + fixed_delta_w
    uncovered_w = max(remaining_w, 0.0)
    summary = (
        f"Planned {len(actions)} action(s) to reduce load by about {round(abs(planned_power_delta_w))} W "
        f"against {round(import_error_w)} W of import pressure in {mode_policy.label} mode"
    )
    reason = (
        f"{mode_policy.reason} Import-side shedding stays conservative in v1: "
        "variable devices are trimmed toward their configured minimums before fixed loads are turned off."
    )
    if not actions:
        summary = (
            f"Import pressure detected ({round(import_error_w)} W), but no usable devices were available for advisory load shedding "
            f"in {mode_policy.label} mode"
        )
        reason = (
            "The planner could not identify any currently usable controllable devices that expose shed-able power in the current model. "
            f"{mode_policy.reason}"
        )
    elif uncovered_w > 0:
        reason = (
            f"{mode_policy.reason} Planned all currently modelled shedding, but about {round(uncovered_w)} W of import pressure would still remain."
        )

    return ControlPlan(
        status="plan_ready" if actions else "blocked",
        summary=summary,
        reason=reason,
        export_error_w=-import_error_w,
        action_count=len(actions),
        planned_power_delta_w=planned_power_delta_w,
        variable_power_delta_w=variable_delta_w,
        fixed_power_delta_w=fixed_delta_w,
        actions=actions,
    )


def _variable_current_target_w(device: DeviceRuntime) -> float:
    current_target_w = device.current_target_power_w
    if current_target_w is None:
        current_target_w = device.current_power_w
    if current_target_w is None:
        return 0.0
    return max(float(current_target_w), 0.0)


def _quantize_down(value_w: float, step_w: float) -> float:
    if step_w <= 0:
        return max(value_w, 0.0)
    whole_steps = int(max(value_w, 0.0) // step_w)
    return whole_steps * step_w


def _quantize_up(value_w: float, step_w: float) -> float:
    if step_w <= 0:
        return max(value_w, 0.0)
    whole_steps = math.ceil(max(value_w, 0.0) / step_w)
    return whole_steps * step_w
