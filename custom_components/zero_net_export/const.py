"""Constants for Zero Net Export."""
from __future__ import annotations

import json
from pathlib import Path

DOMAIN = "zero_net_export"
PLATFORMS = ["sensor", "switch", "select", "number", "binary_sensor", "button"]


def _read_integration_version() -> str:
    """Return the packaged integration version from manifest.json."""
    manifest_path = Path(__file__).with_name("manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "unknown"
    version = manifest.get("version")
    return str(version) if version is not None else "unknown"


INTEGRATION_VERSION = _read_integration_version()

CONF_NAME = "name"
CONF_SOLAR_POWER_ENTITY = "solar_power_entity"
CONF_SOLAR_ENERGY_ENTITY = "solar_energy_entity"
CONF_GRID_IMPORT_POWER_ENTITY = "grid_import_power_entity"
CONF_GRID_EXPORT_POWER_ENTITY = "grid_export_power_entity"
CONF_GRID_IMPORT_ENERGY_ENTITY = "grid_import_energy_entity"
CONF_GRID_EXPORT_ENERGY_ENTITY = "grid_export_energy_entity"
CONF_HOME_LOAD_POWER_ENTITY = "home_load_power_entity"
CONF_BATTERY_SOC_ENTITY = "battery_soc_entity"
CONF_BATTERY_CHARGE_POWER_ENTITY = "battery_charge_power_entity"
CONF_BATTERY_DISCHARGE_POWER_ENTITY = "battery_discharge_power_entity"

SOURCE_ROLE_LABELS = {
    CONF_SOLAR_POWER_ENTITY: "Solar power",
    CONF_SOLAR_ENERGY_ENTITY: "Solar energy",
    CONF_GRID_IMPORT_POWER_ENTITY: "Grid import power",
    CONF_GRID_EXPORT_POWER_ENTITY: "Grid export power",
    CONF_GRID_IMPORT_ENERGY_ENTITY: "Grid import energy",
    CONF_GRID_EXPORT_ENERGY_ENTITY: "Grid export energy",
    CONF_HOME_LOAD_POWER_ENTITY: "Home load power",
    CONF_BATTERY_SOC_ENTITY: "Battery state of charge",
    CONF_BATTERY_CHARGE_POWER_ENTITY: "Battery charge power",
    CONF_BATTERY_DISCHARGE_POWER_ENTITY: "Battery discharge power",
}

REQUIRED_SOURCE_KEYS = (
    CONF_SOLAR_POWER_ENTITY,
    CONF_SOLAR_ENERGY_ENTITY,
    CONF_GRID_IMPORT_POWER_ENTITY,
    CONF_GRID_EXPORT_POWER_ENTITY,
    CONF_GRID_IMPORT_ENERGY_ENTITY,
    CONF_GRID_EXPORT_ENERGY_ENTITY,
    CONF_HOME_LOAD_POWER_ENTITY,
)
CONF_TARGET_EXPORT_W = "target_export_w"
CONF_DEADBAND_W = "deadband_w"
CONF_BATTERY_RESERVE_SOC = "battery_reserve_soc"
CONF_REFRESH_SECONDS = "refresh_seconds"
CONF_DEVICE_INVENTORY_JSON = "device_inventory_json"

DEFAULT_NAME = "Zero Net Export"
DEFAULT_TARGET_EXPORT_W = 0
DEFAULT_DEADBAND_W = 100
DEFAULT_BATTERY_RESERVE_SOC = 20
DEFAULT_REFRESH_SECONDS = 30
DEFAULT_DEVICE_INVENTORY_JSON = "[]"

MODE_ZERO_EXPORT = "zero_export"
MODE_SOFT_ZERO_EXPORT = "soft_zero_export"
MODE_SELF_CONSUMPTION_MAX = "self_consumption_max"
MODE_IMPORT_MIN = "import_min"
MODE_MANUAL_HOLD = "manual_hold"

MODES = [
    MODE_ZERO_EXPORT,
    MODE_SOFT_ZERO_EXPORT,
    MODE_SELF_CONSUMPTION_MAX,
    MODE_IMPORT_MIN,
    MODE_MANUAL_HOLD,
]
