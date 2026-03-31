"""Coordinator for Zero Net Export."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.util import dt as dt_util

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_BATTERY_CHARGE_POWER_ENTITY,
    CONF_BATTERY_DISCHARGE_POWER_ENTITY,
    CONF_BATTERY_RESERVE_SOC,
    CONF_BATTERY_SOC_ENTITY,
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
    MODE_ZERO_EXPORT,
)
from .device_model import DeviceRuntime, build_device_summary, parse_device_configs, runtime_as_attributes
from .executor import ActionResult, execute_action
from .planner import PlannerContext, PlannedDeviceAction, build_control_plan
from .validation import SourceSpec, ValidationIssue, get_source_reading, issues_as_attributes, validate_sources

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}_runtime"
MAX_ACTION_HISTORY = 20
MAX_DAILY_METRIC_DAYS = 7
STALE_SOURCE_MIN_SECONDS = 120
STALE_SOURCE_REFRESH_MULTIPLIER = 3
COMMAND_FAILURE_ACTIVE_SECONDS = 900


@dataclass
class DeviceGuardRuntime:
    observed_active: bool
    last_state_change_at: datetime | None
    last_turned_on_at: datetime | None
    last_turned_off_at: datetime | None
    last_action_at: datetime | None
    last_action: str | None
    last_action_status: str | None


@dataclass
class ZeroNetExportState:
    mode: str
    enabled: bool
    active: bool
    safe_mode: bool
    actions_today: int
    successful_actions_today: int
    failed_actions_today: int
    energy_redirected_today_kwh: float
    active_controlled_power_w: float
    target_export_w: float
    deadband_w: float
    battery_reserve_soc: float
    battery_below_reserve: bool
    solar_power_w: float | None
    solar_energy_kwh: float | None
    grid_import_power_w: float | None
    grid_export_power_w: float | None
    grid_import_energy_kwh: float | None
    grid_export_energy_kwh: float | None
    home_load_power_w: float | None
    battery_soc: float | None
    battery_charge_power_w: float | None
    battery_discharge_power_w: float | None
    surplus_w: float | None
    last_reconciliation_error_w: float | None
    confidence: str
    status: str
    reason: str
    recommendation: str
    diagnostic_summary: str
    source_mismatch: bool
    stale_data: bool
    command_failure: bool
    stale_source_count: int
    stale_source_summary: str
    health_status: str
    health_summary: str
    validation_details: dict
    device_count: int
    enabled_device_count: int
    usable_device_count: int
    fixed_device_count: int
    variable_device_count: int
    controllable_nominal_power_w: float
    usable_nominal_power_w: float
    device_status_summary: str
    control_status: str
    control_summary: str
    control_reason: str
    control_guard_summary: str
    last_action_status: str
    last_action_summary: str
    last_action_at: datetime | None
    last_successful_action_at: datetime | None
    last_failed_action_at: datetime | None
    last_action_device: str | None
    last_failed_action_device: str | None
    last_failed_action_message: str | None
    recent_action_summary: str
    recent_failure_summary: str
    last_successful_action_summary: str
    action_history_count: int
    successful_action_count: int
    failed_action_count: int
    total_successful_action_count: int
    total_failed_action_count: int
    export_error_w: float | None
    planned_action_count: int
    executable_action_count: int
    blocked_planned_action_count: int
    planned_power_delta_w: float
    variable_planned_power_delta_w: float
    fixed_planned_power_delta_w: float
    device_details: dict[str, dict]


class ZeroNetExportCoordinator(DataUpdateCoordinator[ZeroNetExportState]):
    def __init__(self, hass, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._mode = MODE_ZERO_EXPORT
        self._enabled = True
        self._target_export_w_override: float | None = None
        self._deadband_w_override: float | None = None
        self._battery_reserve_soc_override: float | None = None
        self._device_guard_state: dict[str, DeviceGuardRuntime] = {}
        self._action_history: list[dict] = []
        self._persistent_device_state: dict[str, dict[str, Any]] = {}
        self._daily_metrics: dict[str, dict[str, Any]] = {}
        self._last_daily_metrics_update_at: datetime | None = None
        self._total_successful_action_count = 0
        self._total_failed_action_count = 0
        self._last_safe_mode: bool | None = None
        self._last_source_mismatch: bool | None = None
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}_{entry.entry_id}",
        )
        super().__init__(
            hass,
            logger=None,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(
                    CONF_REFRESH_SECONDS,
                    entry.data.get(CONF_REFRESH_SECONDS, DEFAULT_REFRESH_SECONDS),
                )
            ),
        )

    async def async_initialize(self) -> None:
        """Load persisted runtime metadata before the first refresh."""
        stored = await self._store.async_load() or {}
        controller = dict(stored.get("controller") or {})
        self._action_history = list(stored.get("action_history") or [])[:MAX_ACTION_HISTORY]
        self._persistent_device_state = dict(stored.get("devices") or {})
        self._daily_metrics = dict(stored.get("daily_metrics") or {})
        self._prune_daily_metrics()
        self._last_daily_metrics_update_at = self._parse_iso_datetime(stored.get("last_daily_metrics_update_at"))
        self._total_successful_action_count = int(stored.get("total_successful_action_count") or 0)
        self._total_failed_action_count = int(stored.get("total_failed_action_count") or 0)
        self._mode = str(controller.get("mode") or MODE_ZERO_EXPORT)
        self._enabled = bool(controller.get("enabled", True))
        self._target_export_w_override = self._parse_float(controller.get("target_export_w"))
        self._deadband_w_override = self._parse_float(controller.get("deadband_w"))
        self._battery_reserve_soc_override = self._parse_float(controller.get("battery_reserve_soc"))

    def _parse_float(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _configured_target_export_w(self) -> float:
        return float(
            self.entry.options.get(
                CONF_TARGET_EXPORT_W,
                self.entry.data.get(CONF_TARGET_EXPORT_W, DEFAULT_TARGET_EXPORT_W),
            )
        )

    def _configured_deadband_w(self) -> float:
        return float(
            self.entry.options.get(
                CONF_DEADBAND_W,
                self.entry.data.get(CONF_DEADBAND_W, DEFAULT_DEADBAND_W),
            )
        )

    def _effective_target_export_w(self) -> float:
        if self._target_export_w_override is not None:
            return self._target_export_w_override
        return self._configured_target_export_w()

    def _effective_deadband_w(self) -> float:
        if self._deadband_w_override is not None:
            return self._deadband_w_override
        return self._configured_deadband_w()

    def _configured_battery_reserve_soc(self) -> float:
        return float(
            self.entry.options.get(
                CONF_BATTERY_RESERVE_SOC,
                self.entry.data.get(CONF_BATTERY_RESERVE_SOC, DEFAULT_BATTERY_RESERVE_SOC),
            )
        )

    def _effective_battery_reserve_soc(self) -> float:
        if self._battery_reserve_soc_override is not None:
            return self._battery_reserve_soc_override
        return self._configured_battery_reserve_soc()

    def _controller_settings_attributes(self) -> dict[str, Any]:
        return {
            "mode": self._mode,
            "enabled": self._enabled,
            "configured_target_export_w": self._configured_target_export_w(),
            "effective_target_export_w": self._effective_target_export_w(),
            "target_export_override_active": self._target_export_w_override is not None,
            "configured_deadband_w": self._configured_deadband_w(),
            "effective_deadband_w": self._effective_deadband_w(),
            "deadband_override_active": self._deadband_w_override is not None,
            "configured_battery_reserve_soc": self._configured_battery_reserve_soc(),
            "effective_battery_reserve_soc": self._effective_battery_reserve_soc(),
            "battery_reserve_override_active": self._battery_reserve_soc_override is not None,
        }

    def _source_specs(self) -> list[SourceSpec]:
        return [
            SourceSpec("solar_power", self.entry.data.get(CONF_SOLAR_POWER_ENTITY), "power"),
            SourceSpec("solar_energy", self.entry.data.get(CONF_SOLAR_ENERGY_ENTITY), "energy"),
            SourceSpec("grid_import_power", self.entry.data.get(CONF_GRID_IMPORT_POWER_ENTITY), "power"),
            SourceSpec("grid_export_power", self.entry.data.get(CONF_GRID_EXPORT_POWER_ENTITY), "power"),
            SourceSpec("grid_import_energy", self.entry.data.get(CONF_GRID_IMPORT_ENERGY_ENTITY), "energy"),
            SourceSpec("grid_export_energy", self.entry.data.get(CONF_GRID_EXPORT_ENERGY_ENTITY), "energy"),
            SourceSpec("home_load_power", self.entry.data.get(CONF_HOME_LOAD_POWER_ENTITY), "power"),
            SourceSpec("battery_soc", self.entry.data.get(CONF_BATTERY_SOC_ENTITY), "percent", required=False),
            SourceSpec("battery_charge_power", self.entry.data.get(CONF_BATTERY_CHARGE_POWER_ENTITY), "power", required=False),
            SourceSpec("battery_discharge_power", self.entry.data.get(CONF_BATTERY_DISCHARGE_POWER_ENTITY), "power", required=False),
        ]

    def _normalize_value(self, key: str, value: float | None, unit: str | None) -> float | None:
        if value is None:
            return None
        if key.endswith("_power") and unit == "kW":
            return value * 1000.0
        return value

    def _device_inventory_raw(self) -> str:
        return self.entry.options.get(
            CONF_DEVICE_INVENTORY_JSON,
            self.entry.data.get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
        )

    def _device_issues_as_validation(self, issues: list[str]) -> list[ValidationIssue]:
        return [
            ValidationIssue(
                code="device_inventory_invalid",
                severity="warning",
                message=issue,
            )
            for issue in issues
        ]

    def _device_status_summary(self, runtimes: list[DeviceRuntime], safe_mode: bool, parse_issues: list[str]) -> str:
        if parse_issues:
            return "Device inventory needs correction before control actions can start"
        if not runtimes:
            return "No controllable devices configured yet"
        usable = sum(1 for runtime in runtimes if runtime.usable)
        enabled = sum(1 for runtime in runtimes if runtime.config.enabled)
        unsupported = sum(1 for runtime in runtimes if runtime.adapter is None and runtime.config.enabled)
        if safe_mode:
            return f"{enabled} enabled device(s) configured, but source validation is holding control in safe mode"
        if unsupported and usable == 0:
            return f"{unsupported} enabled device(s) still need a supported adapter before control can start"
        if unsupported:
            return f"{usable} of {enabled} enabled device(s) are usable; {unsupported} still need a supported adapter"
        if usable == 0:
            return "Devices are configured, but none are currently usable"
        return f"{usable} of {enabled} enabled device(s) are currently usable"

    def _sync_device_guard_state(self, runtimes: list[DeviceRuntime], now: datetime) -> dict[str, DeviceGuardRuntime]:
        active_keys = {runtime.config.key for runtime in runtimes}
        self._device_guard_state = {
            key: value for key, value in self._device_guard_state.items() if key in active_keys
        }
        self._persistent_device_state = {
            key: value for key, value in self._persistent_device_state.items() if key in active_keys
        }

        for runtime in runtimes:
            state = self._device_guard_state.get(runtime.config.key)
            if state is None:
                state = DeviceGuardRuntime(
                    observed_active=runtime.observed_active,
                    last_state_change_at=now,
                    last_turned_on_at=now if runtime.observed_active else None,
                    last_turned_off_at=now if not runtime.observed_active else None,
                    last_action_at=None,
                    last_action=None,
                    last_action_status=None,
                )
                self._device_guard_state[runtime.config.key] = state
                continue

            if state.observed_active != runtime.observed_active:
                state.observed_active = runtime.observed_active
                state.last_state_change_at = now
                if runtime.observed_active:
                    state.last_turned_on_at = now
                else:
                    state.last_turned_off_at = now

        return self._device_guard_state

    def _seconds_since(self, when: datetime | None, now: datetime) -> float | None:
        if when is None:
            return None
        return max((now - when).total_seconds(), 0.0)

    def _active_runtime_seconds(self, runtime: DeviceRuntime, now: datetime) -> float | None:
        if not runtime.observed_active:
            return None
        memory = self._device_guard_state.get(runtime.config.key)
        if memory is None:
            return runtime.current_active_seconds
        inferred = self._seconds_since(memory.last_turned_on_at, now)
        if inferred is not None:
            return inferred
        return runtime.current_active_seconds

    def _guard_action(self, runtime: DeviceRuntime, planned: PlannedDeviceAction | None, now: datetime) -> dict:
        memory = self._device_guard_state.get(runtime.config.key)
        observed_active = runtime.observed_active
        since_on = self._seconds_since(memory.last_turned_on_at if memory else None, now)
        since_off = self._seconds_since(memory.last_turned_off_at if memory else None, now)
        since_action = self._seconds_since(memory.last_action_at if memory else None, now)

        hold_response = {
            "guard_status": "idle",
            "guard_reason": "No action is currently planned for this device.",
            "action_executable": False,
            "blocked_by": None,
            "last_action": memory.last_action if memory else None,
            "last_action_status": memory.last_action_status if memory else None,
            "last_action_seconds_ago": since_action,
        }
        if planned is None:
            return hold_response

        if planned.action == "hold":
            return hold_response

        if planned.action == "turn_on" and observed_active:
            return {
                "guard_status": "already_satisfied",
                "guard_reason": "Device already appears active, so an additional turn-on action is unnecessary.",
                "action_executable": False,
                "blocked_by": "already_active",
                "last_action": memory.last_action if memory else None,
                "last_action_status": memory.last_action_status if memory else None,
                "last_action_seconds_ago": since_action,
            }

        if planned.action == "turn_off" and not observed_active:
            return {
                "guard_status": "already_satisfied",
                "guard_reason": "Device already appears inactive, so an additional turn-off action is unnecessary.",
                "action_executable": False,
                "blocked_by": "already_inactive",
                "last_action": memory.last_action if memory else None,
                "last_action_status": memory.last_action_status if memory else None,
                "last_action_seconds_ago": since_action,
            }

        if planned.action in {"increase", "decrease"} and runtime.config.kind == "variable":
            if planned.policy != "runtime_cap" and since_action is not None and since_action < runtime.config.cooldown_seconds:
                wait_s = round(runtime.config.cooldown_seconds - since_action)
                return {
                    "guard_status": "blocked",
                    "guard_reason": f"Variable device cooldown is still active for about {wait_s} more second(s).",
                    "action_executable": False,
                    "blocked_by": "cooldown",
                    "last_action": memory.last_action if memory else None,
                    "last_action_status": memory.last_action_status if memory else None,
                    "last_action_seconds_ago": since_action,
                }
            if planned.policy == "runtime_cap":
                return {
                    "guard_status": "ready",
                    "guard_reason": "Runtime-cap safety action bypasses the normal cooldown so the device can be wound back promptly.",
                    "action_executable": True,
                    "blocked_by": None,
                    "last_action": memory.last_action if memory else None,
                    "last_action_status": memory.last_action_status if memory else None,
                    "last_action_seconds_ago": since_action,
                }
            return {
                "guard_status": "ready",
                "guard_reason": "Variable device action passes the current cooldown guard and is ready for live execution.",
                "action_executable": True,
                "blocked_by": None,
                "last_action": memory.last_action if memory else None,
                "last_action_status": memory.last_action_status if memory else None,
                "last_action_seconds_ago": since_action,
            }

        if planned.action == "turn_on":
            if planned.policy != "runtime_cap" and since_off is not None and since_off < runtime.config.min_off_seconds:
                wait_s = round(runtime.config.min_off_seconds - since_off)
                return {
                    "guard_status": "blocked",
                    "guard_reason": f"Min-off protection is still active for about {wait_s} more second(s).",
                    "action_executable": False,
                    "blocked_by": "min_off",
                    "last_action": memory.last_action if memory else None,
                    "last_action_status": memory.last_action_status if memory else None,
                    "last_action_seconds_ago": since_action,
                }
            if planned.policy != "runtime_cap" and since_action is not None and since_action < runtime.config.cooldown_seconds:
                wait_s = round(runtime.config.cooldown_seconds - since_action)
                return {
                    "guard_status": "blocked",
                    "guard_reason": f"Action cooldown is still active for about {wait_s} more second(s).",
                    "action_executable": False,
                    "blocked_by": "cooldown",
                    "last_action": memory.last_action if memory else None,
                    "last_action_status": memory.last_action_status if memory else None,
                    "last_action_seconds_ago": since_action,
                }
            return {
                "guard_status": "ready",
                "guard_reason": "Turn-on action passes min-off and cooldown guards.",
                "action_executable": True,
                "blocked_by": None,
                "last_action": memory.last_action if memory else None,
                "last_action_status": memory.last_action_status if memory else None,
                "last_action_seconds_ago": since_action,
            }

        if planned.action == "turn_off":
            if planned.policy != "runtime_cap" and since_on is not None and since_on < runtime.config.min_on_seconds:
                wait_s = round(runtime.config.min_on_seconds - since_on)
                return {
                    "guard_status": "blocked",
                    "guard_reason": f"Min-on protection is still active for about {wait_s} more second(s).",
                    "action_executable": False,
                    "blocked_by": "min_on",
                    "last_action": memory.last_action if memory else None,
                    "last_action_status": memory.last_action_status if memory else None,
                    "last_action_seconds_ago": since_action,
                }
            if planned.policy != "runtime_cap" and since_action is not None and since_action < runtime.config.cooldown_seconds:
                wait_s = round(runtime.config.cooldown_seconds - since_action)
                return {
                    "guard_status": "blocked",
                    "guard_reason": f"Action cooldown is still active for about {wait_s} more second(s).",
                    "action_executable": False,
                    "blocked_by": "cooldown",
                    "last_action": memory.last_action if memory else None,
                    "last_action_status": memory.last_action_status if memory else None,
                    "last_action_seconds_ago": since_action,
                }
            if planned.policy == "runtime_cap":
                return {
                    "guard_status": "ready",
                    "guard_reason": "Runtime-cap safety action bypasses min-on and cooldown protection so the device can be shed promptly.",
                    "action_executable": True,
                    "blocked_by": None,
                    "last_action": memory.last_action if memory else None,
                    "last_action_status": memory.last_action_status if memory else None,
                    "last_action_seconds_ago": since_action,
                }
            return {
                "guard_status": "ready",
                "guard_reason": "Turn-off action passes min-on and cooldown guards.",
                "action_executable": True,
                "blocked_by": None,
                "last_action": memory.last_action if memory else None,
                "last_action_status": memory.last_action_status if memory else None,
                "last_action_seconds_ago": since_action,
            }

        return {
            "guard_status": "blocked",
            "guard_reason": "Planner action type is not recognised by the current control guard layer.",
            "action_executable": False,
            "blocked_by": "unknown_action",
            "last_action": memory.last_action if memory else None,
            "last_action_status": memory.last_action_status if memory else None,
            "last_action_seconds_ago": since_action,
        }

    def _action_history_attributes(self) -> dict:
        return {
            "action_history_count": len(self._action_history),
            "action_history": list(self._action_history),
            "total_successful_action_count": self._total_successful_action_count,
            "total_failed_action_count": self._total_failed_action_count,
        }

    def _local_day_key(self, when: datetime) -> str:
        return dt_util.as_local(when).date().isoformat()

    def _prune_daily_metrics(self) -> None:
        keys = sorted(self._daily_metrics.keys())
        if len(keys) <= MAX_DAILY_METRIC_DAYS:
            return
        for key in keys[:-MAX_DAILY_METRIC_DAYS]:
            self._daily_metrics.pop(key, None)

    def _daily_metrics_bucket(self, when: datetime) -> dict[str, Any]:
        day_key = self._local_day_key(when)
        bucket = self._daily_metrics.setdefault(
            day_key,
            {
                "successful_actions": 0,
                "failed_actions": 0,
                "energy_redirected_kwh": 0.0,
                "per_device_active_seconds": {},
            },
        )
        bucket.setdefault("per_device_active_seconds", {})
        self._prune_daily_metrics()
        return bucket

    def _active_controlled_power_w(self, runtimes: list[DeviceRuntime]) -> float:
        total = 0.0
        for runtime in runtimes:
            if not runtime.config.enabled or not runtime.observed_active:
                continue
            if runtime.config.kind == "variable":
                contribution = runtime.current_target_power_w
                if contribution is None:
                    contribution = runtime.current_power_w
            else:
                contribution = runtime.current_power_w
                if contribution is None or contribution <= 0:
                    contribution = runtime.config.nominal_power_w
            if contribution is None or contribution <= 0:
                continue
            total += float(contribution)
        return total

    async def _update_daily_energy_metrics(self, now: datetime, runtimes: list[DeviceRuntime]) -> None:
        active_power_w = self._active_controlled_power_w(runtimes)
        if self._last_daily_metrics_update_at is not None:
            elapsed_seconds = max((now - self._last_daily_metrics_update_at).total_seconds(), 0.0)
            elapsed_hours = elapsed_seconds / 3600.0
            bucket = self._daily_metrics_bucket(now)
            changed = False
            if elapsed_hours > 0 and active_power_w > 0:
                bucket["energy_redirected_kwh"] = round(
                    float(bucket.get("energy_redirected_kwh") or 0.0) + ((active_power_w * elapsed_hours) / 1000.0),
                    4,
                )
                changed = True
            if elapsed_seconds > 0:
                per_device_active_seconds = dict(bucket.get("per_device_active_seconds") or {})
                for runtime in runtimes:
                    if not runtime.config.enabled or not runtime.observed_active:
                        continue
                    per_device_active_seconds[runtime.config.key] = round(
                        float(per_device_active_seconds.get(runtime.config.key) or 0.0) + elapsed_seconds,
                        1,
                    )
                    changed = True
                bucket["per_device_active_seconds"] = per_device_active_seconds
            if changed:
                await self._save_runtime_store()
        else:
            self._prune_daily_metrics()
        self._last_daily_metrics_update_at = now

    def _today_metrics_snapshot(self, now: datetime) -> dict[str, Any]:
        bucket = self._daily_metrics.get(
            self._local_day_key(now),
            {
                "successful_actions": 0,
                "failed_actions": 0,
                "energy_redirected_kwh": 0.0,
                "per_device_active_seconds": {},
            },
        )
        successful = int(bucket.get("successful_actions") or 0)
        failed = int(bucket.get("failed_actions") or 0)
        return {
            "actions_today": successful + failed,
            "successful_actions_today": successful,
            "failed_actions_today": failed,
            "energy_redirected_today_kwh": round(float(bucket.get("energy_redirected_kwh") or 0.0), 3),
        }

    def _source_stale_threshold_seconds(self) -> int:
        refresh_seconds = int(
            self.entry.options.get(
                CONF_REFRESH_SECONDS,
                self.entry.data.get(CONF_REFRESH_SECONDS, DEFAULT_REFRESH_SECONDS),
            )
        )
        return max(STALE_SOURCE_MIN_SECONDS, refresh_seconds * STALE_SOURCE_REFRESH_MULTIPLIER)

    def _source_freshness(self, specs: list[SourceSpec], states: dict[str, Any], now: datetime) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        threshold_seconds = self._source_stale_threshold_seconds()
        stale_sources: list[dict[str, Any]] = []
        freshness: dict[str, dict[str, Any]] = {}

        for spec in specs:
            state = states.get(spec.key)
            if state is None or not spec.entity_id:
                freshness[spec.key] = {
                    "entity_id": spec.entity_id,
                    "required": spec.required,
                    "stale": False,
                    "last_updated": None,
                    "age_seconds": None,
                    "stale_threshold_seconds": threshold_seconds,
                }
                continue

            last_updated = getattr(state, "last_updated", None)
            if last_updated is not None and last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            age_seconds = max((now - last_updated).total_seconds(), 0.0) if last_updated else None
            stale = bool(age_seconds is not None and age_seconds > threshold_seconds)
            detail = {
                "key": spec.key,
                "entity_id": spec.entity_id,
                "required": spec.required,
                "stale": stale,
                "last_updated": last_updated.isoformat() if last_updated else None,
                "age_seconds": round(age_seconds, 1) if age_seconds is not None else None,
                "stale_threshold_seconds": threshold_seconds,
            }
            freshness[spec.key] = detail
            if stale and spec.required:
                stale_sources.append(detail)

        return stale_sources, freshness

    def _stale_source_summary(self, stale_sources: list[dict[str, Any]]) -> str:
        if not stale_sources:
            return "No required mapped sources currently look stale"
        parts = []
        for item in stale_sources[:3]:
            age = item.get("age_seconds")
            if age is None:
                parts.append(str(item.get("key")))
            else:
                parts.append(f"{item.get('key')} ({round(float(age))} s old)")
        summary = ", ".join(parts)
        if len(stale_sources) > 3:
            summary += f", +{len(stale_sources) - 3} more"
        return f"Stale required sources detected: {summary}"

    def _command_failure_active(self, latest_action_snapshot: dict[str, Any], now: datetime) -> bool:
        last_failed_at = latest_action_snapshot.get("last_failed_action_at")
        if last_failed_at is None:
            return False
        age_seconds = max((now - last_failed_at).total_seconds(), 0.0)
        last_successful_at = latest_action_snapshot.get("last_successful_action_at")
        if last_successful_at and last_successful_at >= last_failed_at:
            return False
        return age_seconds <= COMMAND_FAILURE_ACTIVE_SECONDS

    def _health_status_summary(self, *, safe_mode: bool, stale_sources: list[dict[str, Any]], command_failure: bool, validation_reason: str, latest_action_snapshot: dict[str, Any]) -> tuple[str, str]:
        if stale_sources:
            return "stale_data", self._stale_source_summary(stale_sources)
        if safe_mode:
            return "safe_mode", validation_reason
        if command_failure:
            device = latest_action_snapshot.get("last_failed_action_device") or "device"
            message = latest_action_snapshot.get("last_failed_action_message") or "Recent guarded command failed"
            return "command_failure", f"Recent command failure on {device}: {message}"
        return "healthy", "No active stale-data or command-failure health condition"

    def _persistent_state_for_device(self, device_key: str) -> dict[str, Any]:
        return self._persistent_device_state.get(device_key, {})

    def _device_active_runtime_today_seconds(self, device_key: str, now: datetime) -> float:
        bucket = self._daily_metrics.get(self._local_day_key(now), {})
        per_device = bucket.get("per_device_active_seconds") or {}
        return round(float(per_device.get(device_key) or 0.0), 1)

    def _summarize_history_entry(self, item: dict[str, Any]) -> str:
        name = item.get("name") or item.get("device_key") or "device"
        action = item.get("action") or "action"
        status = item.get("status") or ("applied" if item.get("success") else "failed")
        requested = item.get("requested_power_w")
        if requested is not None and action in {"increase", "decrease"}:
            return f"{name} {action} → {round(float(requested))} W ({status})"
        return f"{name} {action} ({status})"

    def _history_summary(self, *, success: bool | None = None, limit: int = 3) -> str:
        items = self._action_history
        if success is not None:
            items = [item for item in items if bool(item.get("success")) is success]
        if not items:
            if success is True:
                return "No successful control actions recorded yet"
            if success is False:
                return "No recent failed control actions"
            return "No recent control actions recorded"
        return " | ".join(self._summarize_history_entry(item) for item in items[:limit])

    def _latest_action_snapshot(self) -> dict[str, Any]:
        latest = self._action_history[0] if self._action_history else None
        latest_success = next((item for item in self._action_history if item.get("success")), None)
        latest_failure = next((item for item in self._action_history if not item.get("success")), None)
        return {
            "last_action_at": self._parse_iso_datetime(latest.get("at")) if latest else None,
            "last_successful_action_at": self._parse_iso_datetime(latest_success.get("at")) if latest_success else None,
            "last_failed_action_at": self._parse_iso_datetime(latest_failure.get("at")) if latest_failure else None,
            "last_action_device": latest.get("name") if latest else None,
            "last_failed_action_device": latest_failure.get("name") if latest_failure else None,
            "last_failed_action_message": latest_failure.get("message") if latest_failure else None,
            "recent_action_summary": self._history_summary(),
            "recent_failure_summary": self._history_summary(success=False),
            "last_successful_action_summary": self._summarize_history_entry(latest_success) if latest_success else "No successful control actions recorded yet",
        }

    def _parse_iso_datetime(self, value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            parsed = datetime.fromisoformat(str(value))
        except (TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    async def _emit_runtime_events(self, *, safe_mode: bool, source_mismatch: bool, reason: str) -> None:
        if self._last_safe_mode is None:
            self._last_safe_mode = safe_mode
        elif self._last_safe_mode != safe_mode:
            event_type = f"{DOMAIN}.safe_mode_entered" if safe_mode else f"{DOMAIN}.safe_mode_exited"
            self.hass.bus.async_fire(
                event_type,
                {
                    "entry_id": self.entry.entry_id,
                    "name": self.entry.title,
                    "safe_mode": safe_mode,
                    "reason": reason,
                },
            )
            self._last_safe_mode = safe_mode

        if self._last_source_mismatch is None:
            self._last_source_mismatch = source_mismatch
        elif self._last_source_mismatch != source_mismatch:
            event_type = f"{DOMAIN}.source_mismatch" if source_mismatch else f"{DOMAIN}.source_mismatch_cleared"
            self.hass.bus.async_fire(
                event_type,
                {
                    "entry_id": self.entry.entry_id,
                    "name": self.entry.title,
                    "source_mismatch": source_mismatch,
                    "reason": reason,
                },
            )
            self._last_source_mismatch = source_mismatch

    async def async_set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        await self._save_runtime_store()
        await self.async_request_refresh()

    async def async_set_mode(self, mode: str) -> None:
        self._mode = mode
        await self._save_runtime_store()
        await self.async_request_refresh()

    async def async_set_target_export_w_override(self, value: float) -> None:
        self._target_export_w_override = float(value)
        await self._save_runtime_store()
        await self.async_request_refresh()

    async def async_set_deadband_w_override(self, value: float) -> None:
        self._deadband_w_override = float(value)
        await self._save_runtime_store()
        await self.async_request_refresh()

    async def async_set_battery_reserve_soc_override(self, value: float) -> None:
        self._battery_reserve_soc_override = max(0.0, min(float(value), 100.0))
        await self._save_runtime_store()
        await self.async_request_refresh()

    async def async_reset_controller_overrides(self) -> None:
        self._target_export_w_override = None
        self._deadband_w_override = None
        self._battery_reserve_soc_override = None
        await self._save_runtime_store()
        await self.async_request_refresh()

    async def async_set_device_enabled_override(self, device_key: str, enabled: bool) -> None:
        persistent = self._persistent_device_state.setdefault(device_key, {})
        persistent["operator_enabled_override"] = bool(enabled)
        await self._save_runtime_store()
        await self.async_request_refresh()

    async def async_set_device_priority_override(self, device_key: str, priority: int) -> None:
        persistent = self._persistent_device_state.setdefault(device_key, {})
        persistent["operator_priority_override"] = int(priority)
        await self._save_runtime_store()
        await self.async_request_refresh()

    async def async_reset_device_overrides(self, device_key: str) -> None:
        persistent = self._persistent_device_state.setdefault(device_key, {})
        persistent.pop("operator_enabled_override", None)
        persistent.pop("operator_priority_override", None)
        await self._save_runtime_store()
        await self.async_request_refresh()

    async def _save_runtime_store(self) -> None:
        await self._store.async_save(
            {
                "controller": {
                    "mode": self._mode,
                    "enabled": self._enabled,
                    "target_export_w": self._target_export_w_override,
                    "deadband_w": self._deadband_w_override,
                    "battery_reserve_soc": self._battery_reserve_soc_override,
                },
                "devices": self._persistent_device_state,
                "action_history": self._action_history[:MAX_ACTION_HISTORY],
                "daily_metrics": self._daily_metrics,
                "last_daily_metrics_update_at": self._last_daily_metrics_update_at.isoformat()
                if self._last_daily_metrics_update_at
                else None,
                "total_successful_action_count": self._total_successful_action_count,
                "total_failed_action_count": self._total_failed_action_count,
            }
        )

    async def _record_action_result(self, runtime: DeviceRuntime, result: ActionResult, now: datetime) -> None:
        memory = self._device_guard_state.get(result.device_key)
        if memory is not None and result.success:
            memory.last_action_at = now
            memory.last_action = result.action
            memory.last_action_status = result.status

        persistent = self._persistent_device_state.setdefault(result.device_key, {})
        persistent.update(
            {
                "last_action_at": now.isoformat(),
                "last_action": result.action,
                "last_action_status": result.status,
                "last_result_message": result.message,
                "last_service": result.service,
                "last_service_data": result.service_data,
                "last_requested_power_w": result.requested_power_w,
            }
        )
        daily_bucket = self._daily_metrics_bucket(now)
        if result.success:
            self._total_successful_action_count += 1
            daily_bucket["successful_actions"] = int(daily_bucket.get("successful_actions") or 0) + 1
            persistent["success_count"] = int(persistent.get("success_count") or 0) + 1
            persistent["last_applied_at"] = now.isoformat()
            if result.requested_power_w is not None:
                persistent["last_applied_power_w"] = result.requested_power_w
            elif result.action == "turn_on":
                persistent["last_applied_power_w"] = runtime.config.nominal_power_w
            elif result.action == "turn_off":
                persistent["last_applied_power_w"] = 0.0
        else:
            self._total_failed_action_count += 1
            daily_bucket["failed_actions"] = int(daily_bucket.get("failed_actions") or 0) + 1
            persistent["failure_count"] = int(persistent.get("failure_count") or 0) + 1

        event_payload = {
            "at": now.isoformat(),
            "device_key": result.device_key,
            "name": result.name,
            "entity_id": result.entity_id,
            "action": result.action,
            "requested_power_w": result.requested_power_w,
            "success": result.success,
            "status": result.status,
            "message": result.message,
            "service": result.service,
            "service_data": result.service_data,
        }
        self._action_history.insert(0, event_payload)
        self._action_history = self._action_history[:MAX_ACTION_HISTORY]
        await self._save_runtime_store()
        self.hass.bus.async_fire(f"{DOMAIN}.action_applied", event_payload)

    async def _execute_guarded_actions(
        self,
        runtimes: list[DeviceRuntime],
        planned_by_key: dict[str, PlannedDeviceAction],
        device_details: dict[str, dict],
        now: datetime,
    ) -> list[ActionResult]:
        results: list[ActionResult] = []
        for runtime in runtimes:
            details = device_details[runtime.config.key]
            if not details["action_executable"]:
                continue
            planned = planned_by_key.get(runtime.config.key)
            if planned is None:
                continue

            result = await execute_action(self.hass, runtime, planned)
            results.append(result)
            await self._record_action_result(runtime, result, now)
            details["last_action"] = result.action
            details["last_action_status"] = result.status
            details["last_action_at"] = now
            details["last_action_seconds_ago"] = 0.0 if result.success else details.get("last_action_seconds_ago")
            details["last_action_result_message"] = result.message
            details["last_action_service"] = result.service
            details["last_action_service_data"] = result.service_data
            details["last_requested_power_w"] = result.requested_power_w
            if result.success and result.requested_power_w is not None:
                details["last_applied_power_w"] = result.requested_power_w
                details["last_applied_at"] = now
            elif result.success and result.action == "turn_off":
                details["last_applied_power_w"] = 0.0
                details["last_applied_at"] = now
            elif result.success and result.action == "turn_on":
                details["last_applied_power_w"] = runtime.config.nominal_power_w
                details["last_applied_at"] = now
            elif result.success:
                details["last_applied_at"] = now
            if result.success:
                details["guard_status"] = "applied"
                details["guard_reason"] = result.message
            else:
                details["guard_status"] = result.status
                details["guard_reason"] = result.message
                details["action_executable"] = False
                details["blocked_by"] = result.status
        return results

    def _execution_summary(self, results: list[ActionResult]) -> tuple[str, str, int, int]:
        if not results:
            return (
                "idle",
                "No Home Assistant action was executed in this cycle.",
                0,
                0,
            )
        success_count = sum(1 for result in results if result.success)
        failed_count = len(results) - success_count
        if failed_count == 0:
            summary = f"Applied {success_count} guarded Home Assistant action(s) this cycle."
            return "applied", summary, success_count, failed_count
        if success_count == 0:
            summary = f"All {failed_count} attempted Home Assistant action(s) failed or were unsupported."
            return "failed", summary, success_count, failed_count
        summary = f"Applied {success_count} action(s); {failed_count} action(s) failed or were unsupported."
        return "partial", summary, success_count, failed_count

    def _control_guard_summary(
        self,
        planned_count: int,
        executable_count: int,
        blocked_count: int,
        results: list[ActionResult],
    ) -> str:
        if planned_count == 0:
            return "No guard evaluation was needed because no device action was planned in this cycle"
        if results:
            success_count = sum(1 for result in results if result.success)
            failed_count = len(results) - success_count
            if failed_count == 0:
                return f"Executed {success_count} guard-approved action(s); {blocked_count} planned action(s) remained blocked"
            return (
                f"Attempted {len(results)} guard-approved action(s): {success_count} applied, "
                f"{failed_count} failed/unsupported, {blocked_count} still blocked"
            )
        if executable_count == planned_count:
            return f"All {planned_count} planned action(s) passed the current anti-flap guards"
        if executable_count == 0:
            return f"All {blocked_count} planned action(s) were blocked by anti-flap or state guards"
        return f"{executable_count} planned action(s) passed guards and {blocked_count} were held back"

    async def _async_update_data(self) -> ZeroNetExportState:
        try:
            now = datetime.now(timezone.utc)
            specs = self._source_specs()
            readings = {}
            states = {}
            for spec in specs:
                reading, state = get_source_reading(self.hass, spec.entity_id)
                reading.value = self._normalize_value(spec.key, reading.value, reading.unit)
                readings[spec.key] = reading
                states[spec.key] = state

            validation = validate_sources(readings, states, specs)
            stale_sources, source_freshness = self._source_freshness(specs, states, now)
            stale_data = len(stale_sources) > 0
            effective_safe_mode = validation.safe_mode or stale_data

            configured_devices, device_parse_issues = parse_device_configs(self._device_inventory_raw())
            device_summary = build_device_summary(
                self.hass,
                configured_devices,
                effective_safe_mode,
                overrides=self._persistent_device_state,
            )
            self._sync_device_guard_state(device_summary.devices, now)
            for runtime in device_summary.devices:
                runtime.current_active_seconds = self._active_runtime_seconds(runtime, now)
            combined_issues = validation.issues + self._device_issues_as_validation(device_parse_issues)
            device_status_summary = self._device_status_summary(
                device_summary.devices,
                effective_safe_mode,
                device_parse_issues,
            )

            control_plan = build_control_plan(
                PlannerContext(
                    enabled=self._enabled,
                    mode=self._mode,
                    safe_mode=effective_safe_mode,
                    target_export_w=self._effective_target_export_w(),
                    deadband_w=self._effective_deadband_w(),
                    grid_import_power_w=readings["grid_import_power"].value,
                    grid_export_power_w=readings["grid_export_power"].value,
                    battery_soc=readings["battery_soc"].value,
                    battery_reserve_soc=self._effective_battery_reserve_soc(),
                ),
                device_summary.devices,
            )

            active = self._enabled and not effective_safe_mode and device_summary.usable_devices > 0
            if not self._enabled:
                status = "disabled"
                reason = "Controller disabled by operator"
            elif stale_data:
                status = "stale_data"
                reason = self._stale_source_summary(stale_sources)
            elif validation.status == "validated":
                if device_summary.total_devices == 0:
                    status = "validated"
                    reason = "Sources validated; configure controllable devices to start control"
                elif device_summary.usable_devices == 0:
                    status = "waiting_for_devices"
                    reason = "Sources validated; device inventory exists but no devices are currently usable"
                else:
                    status = "ready"
                    reason = f"Sources validated; {device_summary.usable_devices} controllable device(s) are ready"
            else:
                status = validation.status
                reason = validation.reason

            recommendation = validation.recommendation
            if stale_data:
                recommendation = (
                    "Refresh or replace the stale required source sensors before allowing more control actions; "
                    "the controller is holding safe mode until live data resumes"
                )
            elif not configured_devices and not device_parse_issues and validation.status == "validated":
                recommendation = "Add fixed and variable controllable devices next; source validation is already healthy"
            elif device_parse_issues:
                recommendation = "Fix the device inventory JSON so Zero Net Export can reason about controllable loads"

            battery_below_reserve = bool(
                readings["battery_soc"].value is not None
                and readings["battery_soc"].value < self._effective_battery_reserve_soc()
            )

            planned_by_key = {item.device_key: item for item in control_plan.actions}
            device_details = {}
            executable_action_count = 0
            blocked_planned_action_count = 0
            for runtime in device_summary.devices:
                planned = planned_by_key.get(runtime.config.key)
                guard = self._guard_action(runtime, planned, now)
                persisted = self._persistent_state_for_device(runtime.config.key)
                if planned is not None:
                    if guard["action_executable"]:
                        executable_action_count += 1
                    else:
                        blocked_planned_action_count += 1
                device_details[runtime.config.key] = {
                    **runtime_as_attributes(runtime),
                    "key": runtime.config.key,
                    "name": runtime.config.name,
                    "usable": runtime.usable,
                    "status": runtime.status,
                    "reason": runtime.reason,
                    "current_power_w": runtime.current_power_w,
                    "current_target_power_w": runtime.current_target_power_w,
                    "active_runtime_today_seconds": self._device_active_runtime_today_seconds(runtime.config.key, now),
                    "planned_action": "hold",
                    "planned_power_delta_w": 0.0,
                    "planned_requested_power_w": None,
                    "planned_action_reason": "No current advisory action for this device in the latest control cycle.",
                    "planned_action_policy": None,
                    "last_action_at": self._parse_iso_datetime(persisted.get("last_action_at")),
                    "last_action_result_message": persisted.get("last_result_message"),
                    "last_action_service": persisted.get("last_service"),
                    "last_action_service_data": persisted.get("last_service_data"),
                    "last_requested_power_w": persisted.get("last_requested_power_w"),
                    "last_applied_power_w": persisted.get("last_applied_power_w"),
                    "last_applied_at": self._parse_iso_datetime(persisted.get("last_applied_at")),
                    "successful_action_count": int(persisted.get("success_count") or 0),
                    "failed_action_count": int(persisted.get("failure_count") or 0),
                    **(
                        {
                            "planned_action": planned.action,
                            "planned_power_delta_w": planned.delta_power_w,
                            "planned_requested_power_w": planned.requested_power_w,
                            "planned_action_reason": planned.reason,
                            "planned_action_policy": planned.policy,
                        }
                        if planned
                        else {}
                    ),
                    **guard,
                }

            await self._update_daily_energy_metrics(now, device_summary.devices)
            today_metrics = self._today_metrics_snapshot(now)
            for runtime in device_summary.devices:
                device_details[runtime.config.key]["active_runtime_today_seconds"] = self._device_active_runtime_today_seconds(
                    runtime.config.key,
                    now,
                )

            action_results: list[ActionResult] = []
            if control_plan.status == "plan_ready" and executable_action_count > 0:
                action_results = await self._execute_guarded_actions(
                    device_summary.devices,
                    planned_by_key,
                    device_details,
                    now,
                )
                today_metrics = self._today_metrics_snapshot(now)

            last_action_status, last_action_summary, successful_action_count, failed_action_count = self._execution_summary(
                action_results
            )
            control_guard_summary = self._control_guard_summary(
                control_plan.action_count,
                executable_action_count,
                blocked_planned_action_count,
                action_results,
            )
            latest_action_snapshot = self._latest_action_snapshot()
            command_failure = self._command_failure_active(latest_action_snapshot, now)
            health_status, health_summary = self._health_status_summary(
                safe_mode=effective_safe_mode,
                stale_sources=stale_sources,
                command_failure=command_failure,
                validation_reason=reason,
                latest_action_snapshot=latest_action_snapshot,
            )
            await self._emit_runtime_events(
                safe_mode=effective_safe_mode,
                source_mismatch=validation.source_mismatch,
                reason=reason,
            )

            validation_details = {
                **issues_as_attributes(combined_issues),
                **self._action_history_attributes(),
                **self._controller_settings_attributes(),
                **today_metrics,
                "active_controlled_power_w": round(self._active_controlled_power_w(device_summary.devices), 1),
                "battery_below_reserve": battery_below_reserve,
                "daily_metrics": self._daily_metrics,
                "daily_metrics_basis": "Energy redirected today is an estimate derived from observed active managed-device power integrated over coordinator refresh time, not a revenue-grade meter total.",
                "diagnostic_summary": validation.diagnostic_summary,
                "calibration_hints": list(validation.calibration_hints),
                "source_diagnostics": validation.source_diagnostics,
                "source_freshness": source_freshness,
                "stale_source_count": len(stale_sources),
                "stale_source_summary": self._stale_source_summary(stale_sources),
                "health_status": health_status,
                "health_summary": health_summary,
                "command_failure_active_window_seconds": COMMAND_FAILURE_ACTIVE_SECONDS,
            }

            return ZeroNetExportState(
                mode=self._mode,
                enabled=self._enabled,
                active=active,
                safe_mode=effective_safe_mode,
                actions_today=today_metrics["actions_today"],
                successful_actions_today=today_metrics["successful_actions_today"],
                failed_actions_today=today_metrics["failed_actions_today"],
                energy_redirected_today_kwh=today_metrics["energy_redirected_today_kwh"],
                active_controlled_power_w=round(self._active_controlled_power_w(device_summary.devices), 1),
                target_export_w=self._effective_target_export_w(),
                deadband_w=self._effective_deadband_w(),
                battery_reserve_soc=self._effective_battery_reserve_soc(),
                battery_below_reserve=battery_below_reserve,
                solar_power_w=readings["solar_power"].value,
                solar_energy_kwh=readings["solar_energy"].value,
                grid_import_power_w=readings["grid_import_power"].value,
                grid_export_power_w=readings["grid_export_power"].value,
                grid_import_energy_kwh=readings["grid_import_energy"].value,
                grid_export_energy_kwh=readings["grid_export_energy"].value,
                home_load_power_w=readings["home_load_power"].value,
                battery_soc=readings["battery_soc"].value,
                battery_charge_power_w=readings["battery_charge_power"].value,
                battery_discharge_power_w=readings["battery_discharge_power"].value,
                surplus_w=validation.surplus_w,
                last_reconciliation_error_w=validation.last_reconciliation_error_w,
                confidence=validation.confidence,
                status=status,
                reason=reason,
                recommendation=recommendation,
                diagnostic_summary=validation.diagnostic_summary,
                source_mismatch=validation.source_mismatch,
                stale_data=stale_data,
                command_failure=command_failure,
                stale_source_count=len(stale_sources),
                stale_source_summary=self._stale_source_summary(stale_sources),
                health_status=health_status,
                health_summary=health_summary,
                validation_details=validation_details,
                device_count=device_summary.total_devices,
                enabled_device_count=device_summary.enabled_devices,
                usable_device_count=device_summary.usable_devices,
                fixed_device_count=device_summary.fixed_devices,
                variable_device_count=device_summary.variable_devices,
                controllable_nominal_power_w=device_summary.total_nominal_power_w,
                usable_nominal_power_w=device_summary.usable_nominal_power_w,
                device_status_summary=device_status_summary,
                control_status=control_plan.status,
                control_summary=control_plan.summary,
                control_reason=control_plan.reason,
                control_guard_summary=control_guard_summary,
                last_action_status=last_action_status,
                last_action_summary=last_action_summary,
                last_action_at=latest_action_snapshot["last_action_at"],
                last_successful_action_at=latest_action_snapshot["last_successful_action_at"],
                last_failed_action_at=latest_action_snapshot["last_failed_action_at"],
                last_action_device=latest_action_snapshot["last_action_device"],
                last_failed_action_device=latest_action_snapshot["last_failed_action_device"],
                last_failed_action_message=latest_action_snapshot["last_failed_action_message"],
                recent_action_summary=latest_action_snapshot["recent_action_summary"],
                recent_failure_summary=latest_action_snapshot["recent_failure_summary"],
                last_successful_action_summary=latest_action_snapshot["last_successful_action_summary"],
                action_history_count=len(self._action_history),
                successful_action_count=successful_action_count,
                failed_action_count=failed_action_count,
                total_successful_action_count=self._total_successful_action_count,
                total_failed_action_count=self._total_failed_action_count,
                export_error_w=control_plan.export_error_w,
                planned_action_count=control_plan.action_count,
                executable_action_count=executable_action_count,
                blocked_planned_action_count=blocked_planned_action_count,
                planned_power_delta_w=control_plan.planned_power_delta_w,
                variable_planned_power_delta_w=control_plan.variable_power_delta_w,
                fixed_planned_power_delta_w=control_plan.fixed_power_delta_w,
                device_details=device_details,
            )
        except Exception as err:
            raise UpdateFailed(str(err)) from err
