from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"
CONST_PATH = PACKAGE_ROOT / "const.py"
MODULE_PATH = PACKAGE_ROOT / "config_flow.py"


def _load_config_flow_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    homeassistant_module = sys.modules.setdefault("homeassistant", types.ModuleType("homeassistant"))
    homeassistant_module.__path__ = []

    voluptuous_module = types.ModuleType("voluptuous")
    voluptuous_module.Schema = lambda value: value
    voluptuous_module.Required = lambda key, default=None: key
    voluptuous_module.Optional = lambda key, default=None: key
    sys.modules[voluptuous_module.__name__] = voluptuous_module

    components_module = sys.modules.setdefault("homeassistant.components", types.ModuleType("homeassistant.components"))
    components_module.__path__ = []

    persistent_notification_module = types.ModuleType("homeassistant.components.persistent_notification")
    persistent_notification_module.async_create = lambda *args, **kwargs: None
    sys.modules[persistent_notification_module.__name__] = persistent_notification_module

    config_entries_module = types.ModuleType("homeassistant.config_entries")

    class ConfigFlow:
        def __init_subclass__(cls, **kwargs):
            return None

    class OptionsFlow:
        def __init__(self, *args, **kwargs) -> None:
            pass

    config_entries_module.ConfigFlow = ConfigFlow
    config_entries_module.OptionsFlow = OptionsFlow
    sys.modules[config_entries_module.__name__] = config_entries_module

    core_module = types.ModuleType("homeassistant.core")
    core_module.callback = lambda func: func
    sys.modules[core_module.__name__] = core_module

    helpers_module = sys.modules.setdefault("homeassistant.helpers", types.ModuleType("homeassistant.helpers"))
    helpers_module.__path__ = []

    selector_module = types.ModuleType("homeassistant.helpers.selector")
    selector_module.SelectOptionDict = lambda **kwargs: kwargs
    selector_module.SelectSelector = lambda config: config
    selector_module.SelectSelectorConfig = lambda **kwargs: kwargs
    selector_module.SelectSelectorMode = types.SimpleNamespace(LIST="list", DROPDOWN="dropdown")
    selector_module.TextSelector = lambda config: config
    selector_module.TextSelectorConfig = lambda **kwargs: kwargs
    selector_module.TextSelectorType = types.SimpleNamespace(TEXT="text")
    selector_module.NumberSelector = lambda config: config
    selector_module.NumberSelectorConfig = lambda **kwargs: kwargs
    selector_module.NumberSelectorMode = types.SimpleNamespace(BOX="box")
    selector_module.BooleanSelector = lambda *args, **kwargs: {"boolean": True}
    selector_module.EntitySelector = lambda config: config
    selector_module.EntitySelectorConfig = lambda **kwargs: kwargs
    sys.modules[selector_module.__name__] = selector_module

    candidate_utils_module = types.ModuleType("custom_components.zero_net_export.candidate_utils")
    candidate_utils_module.assess_candidate = lambda candidate: {
        "confidence": "medium",
        "summary": "Looks like a plausible controllable candidate, but review before promotion.",
        "warnings": [],
    }
    candidate_utils_module.build_candidate_preview = lambda candidate, include_entity_id=True, include_kind=True, include_state=False, **kwargs: (
        f"{candidate.get('name') or candidate.get('entity_id')}"
        + (
            ""
            if not (include_entity_id or include_kind or include_state)
            else " ("
            + ", ".join(
                bit
                for bit in [
                    candidate.get("entity_id") if include_entity_id else "",
                    candidate.get("kind") if include_kind else "",
                    f"state {candidate.get('state')}" if include_state and candidate.get("state") else "",
                ]
                if bit
            )
            + ")"
        )
        + " | likely useful | key warning: No immediate warnings"
    )
    candidate_utils_module.build_candidate_review_line = lambda label, level, summary: f"{label}: {level} - {summary}"
    candidate_utils_module.build_candidate_review_hint = lambda candidate, **kwargs: "likely useful"
    candidate_utils_module.candidate_needs_review = lambda fit: str((fit or {}).get("confidence") or "medium") != "high"
    candidate_utils_module.first_review_candidate = lambda candidates: next(
        (
            candidate
            for candidate in candidates
            if candidate_utils_module.candidate_needs_review(candidate_utils_module.assess_candidate(candidate))
        ),
        None,
    )
    candidate_utils_module.discover_candidate_devices = lambda states, managed_entity_ids: []
    sys.modules[candidate_utils_module.__name__] = candidate_utils_module

    const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", CONST_PATH)
    assert const_spec and const_spec.loader
    const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = const_module
    const_spec.loader.exec_module(const_module)

    device_model_module = types.ModuleType("custom_components.zero_net_export.device_model")
    device_model_module.ADAPTER_FIXED_TOGGLE = "fixed_toggle"
    device_model_module.ADAPTER_VARIABLE_NUMBER = "variable_number"
    device_model_module.DEVICE_KIND_FIXED = "fixed"
    device_model_module.DEVICE_KIND_VARIABLE = "variable"
    device_model_module.default_device_blueprint = lambda: "[]"
    device_model_module.get_device_template = lambda kind, key: None
    device_model_module.get_device_templates = lambda kind: []
    device_model_module.parse_device_configs = lambda raw: ([], [])
    sys.modules[device_model_module.__name__] = device_model_module

    native_support_module = types.ModuleType("custom_components.zero_net_export.native_support")
    native_support_module.ADVANCED_DEVICES_CONFIGURE_PATH = "advanced path"
    native_support_module.DETAILED_MANAGEMENT_PATH = "detailed device path"
    native_support_module.DIAGNOSTICS_DEVICE_ACTIONS_PATH = "device path -> Review diagnostics / Show setup checklist / Review diagnostics snapshot"
    native_support_module.DEVICES_CONFIGURE_PATH = "devices path"
    native_support_module.DEVICES_SECTION_LABEL = "Managed Devices"
    native_support_module.INTEGRATION_DEVICE_PATH = "device path"
    native_support_module.MODE_CONTROL_PATH = "mode path"
    native_support_module.POLICY_CONFIGURE_PATH = "policy path"
    native_support_module.POLICY_SECTION_LABEL = "Controls"
    native_support_module.PRIMARY_CONFIGURE_PATH = "primary path"
    native_support_module.SOURCES_CONFIGURE_PATH = "sources path"
    native_support_module.SOURCES_SECTION_LABEL = "Sensors"
    native_support_module.SUPPORT_CONFIGURE_PATH = "support path"
    native_support_module.SUPPORT_SECTION_LABEL = "Diagnostics"
    native_support_module._source_specs_from_config = lambda config, grid_mode=None: []
    native_support_module.build_live_source_health_summary = lambda *args, **kwargs: "healthy"
    native_support_module.build_native_command_center_summary = lambda *args, **kwargs: {}
    native_support_module.build_native_operator_readiness = lambda *args, **kwargs: {}
    native_support_module.build_source_attention_details = lambda *args, **kwargs: {}
    native_support_module.build_source_attention_role_summary = lambda *args, **kwargs: "None"
    native_support_module.build_source_attention_summary = lambda *args, **kwargs: "None"
    native_support_module.build_source_mapping_summary = lambda *args, **kwargs: "None"
    native_support_module.build_source_repair_step = lambda *args, **kwargs: "Repair step"
    native_support_module.build_source_selector_fallback_hint = lambda *args, **kwargs: "Fallback hint"
    native_support_module.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
    sys.modules[native_support_module.__name__] = native_support_module

    release_info_module = types.ModuleType("custom_components.zero_net_export.release_info")
    release_info_module.build_install_consistency_summary = lambda *args, **kwargs: "consistent"
    release_info_module.build_install_fingerprint_summary = lambda *args, **kwargs: "fingerprint"
    release_info_module.build_install_provenance = lambda *args, **kwargs: {}
    release_info_module.build_install_repair_step = lambda *args, **kwargs: "repair step"
    sys.modules[release_info_module.__name__] = release_info_module

    validation_module = types.ModuleType("custom_components.zero_net_export.validation")
    validation_module.DERIVED_SOURCE_MODE_DIRECT = "direct"
    validation_module.DERIVED_SOURCE_MODE_NEGATIVE_ABS = "negative_abs"
    validation_module.DERIVED_SOURCE_MODE_POSITIVE = "positive"
    validation_module.DERIVED_SOURCE_PREFIX = "derived_"
    validation_module.ENERGY_UNITS = {"kWh"}
    validation_module.PERCENT_UNITS = {"%"}
    validation_module.POWER_UNITS = {"W"}
    validation_module.TOTAL_STATE_CLASSES = {"total", "total_increasing"}
    validation_module.parse_source_binding = lambda value: value
    validation_module.validate_configured_entities = lambda *args, **kwargs: SimpleNamespace(
        is_valid=True,
        errors=[],
        warnings=[],
        source_diagnostics={},
        source_freshness={},
        diagnostic_summary="",
        blocking_details="",
        status="validated",
    )
    sys.modules[validation_module.__name__] = validation_module

    module_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.config_flow", MODULE_PATH)
    assert module_spec and module_spec.loader
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


class ConfigFlowDeviceRuntimeOverlayTests(unittest.TestCase):
    def test_config_flow_copy_uses_explicit_diagnostics_path_wording(self) -> None:
        source = MODULE_PATH.read_text()

        self.assertIn("DIAGNOSTICS_DEVICE_ACTIONS_PATH", source)
        self.assertNotIn("support actions", source)
        self.assertNotIn("device support actions", source)

    def test_best_source_candidate_prefers_explicit_grid_export_energy_sensor(self) -> None:
        module = _load_config_flow_module()
        states = [
            SimpleNamespace(
                entity_id="sensor.shelly_total_active_returned_energy",
                state="103.35",
                attributes={
                    "friendly_name": "Energy returned",
                    "device_class": "energy",
                    "unit_of_measurement": "kWh",
                    "state_class": "total_increasing",
                },
            ),
            SimpleNamespace(
                entity_id="sensor.shelly_total_active_energy",
                state="4021.11",
                attributes={
                    "friendly_name": "Total active energy",
                    "device_class": "energy",
                    "unit_of_measurement": "kWh",
                    "state_class": "total_increasing",
                },
            ),
        ]

        best = module._best_source_candidate_entity(states, module.CONF_GRID_EXPORT_ENERGY_ENTITY, "energy")

        self.assertEqual(best, "sensor.shelly_total_active_returned_energy")

    def test_best_source_candidate_rejects_ambiguous_generic_power_pair(self) -> None:
        module = _load_config_flow_module()
        states = [
            SimpleNamespace(
                entity_id="sensor.inverter_power_a",
                state="850",
                attributes={
                    "friendly_name": "Inverter power A",
                    "device_class": "power",
                    "unit_of_measurement": "W",
                    "state_class": "measurement",
                },
            ),
            SimpleNamespace(
                entity_id="sensor.inverter_power_b",
                state="830",
                attributes={
                    "friendly_name": "Inverter power B",
                    "device_class": "power",
                    "unit_of_measurement": "W",
                    "state_class": "measurement",
                },
            ),
        ]

        best = module._best_source_candidate_entity(states, module.CONF_SOLAR_POWER_ENTITY, "power")

        self.assertIsNone(best)

    def test_best_source_candidate_accepts_clear_solar_power_sensor(self) -> None:
        module = _load_config_flow_module()
        states = [
            SimpleNamespace(
                entity_id="sensor.x1_p6k_us_s_solar_power",
                state="1030",
                attributes={
                    "friendly_name": "Solar power",
                    "device_class": "power",
                    "unit_of_measurement": "W",
                    "state_class": "measurement",
                },
            ),
            SimpleNamespace(
                entity_id="sensor.x1_p6k_us_s_home_demand",
                state="400",
                attributes={
                    "friendly_name": "Home demand",
                    "device_class": "power",
                    "unit_of_measurement": "W",
                    "state_class": "measurement",
                },
            ),
        ]

        best = module._best_source_candidate_entity(states, module.CONF_SOLAR_POWER_ENTITY, "power")

        self.assertEqual(best, "sensor.x1_p6k_us_s_solar_power")

    def test_runtime_overlay_adds_usable_and_status_by_key(self) -> None:
        module = _load_config_flow_module()
        devices = [
            {
                "key": "pool_pump",
                "name": "Pool pump",
                "kind": "fixed",
                "entity_id": "switch.pool_pump",
                "enabled": True,
                "priority": 10,
                "nominal_power_w": 1200,
            }
        ]
        coordinator = SimpleNamespace(
            data=SimpleNamespace(
                device_details={
                    "pool_pump": {
                        "entity_id": "switch.pool_pump",
                        "usable": True,
                        "effective_enabled": True,
                        "status": "Ready for control",
                    }
                }
            )
        )

        enriched = module._overlay_runtime_device_details(devices, coordinator)

        self.assertTrue(enriched[0]["usable"])
        self.assertTrue(enriched[0]["effective_enabled"])
        self.assertEqual(enriched[0]["status"], "Ready for control")

    def test_runtime_overlay_falls_back_to_entity_id_match(self) -> None:
        module = _load_config_flow_module()
        devices = [{"key": "legacy_key", "entity_id": "switch.hot_water", "enabled": False}]
        coordinator = SimpleNamespace(
            data=SimpleNamespace(
                device_details={
                    "runtime_key": {
                        "entity_id": "switch.hot_water",
                        "usable": False,
                        "effective_enabled": False,
                        "status": "Blocked by guard",
                    }
                }
            )
        )

        enriched = module._overlay_runtime_device_details(devices, coordinator)

        self.assertFalse(enriched[0]["usable"])
        self.assertFalse(enriched[0]["effective_enabled"])
        self.assertEqual(enriched[0]["status"], "Blocked by guard")

    def test_device_status_label_and_summary_show_runtime_state(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace())
        devices = [
            {
                "key": "pool_pump",
                "name": "Pool pump",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.pool_pump",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "status": "Ready for control",
                "guard_status": "ready",
                "planned_action": "turn_on",
                "last_action_status": "queued",
                "priority": 10,
                "nominal_power_w": 1200,
                "current_power_w": 1185,
            },
            {
                "key": "ev",
                "name": "EV charger",
                "kind": module.DEVICE_KIND_VARIABLE,
                "entity_id": "number.ev_limit",
                "enabled": True,
                "effective_enabled": False,
                "operator_enabled_override": False,
                "usable": False,
                "status": "Held by guard",
                "guard_status": "cooldown",
                "planned_action": "hold",
                "last_action_status": "throttled",
                "priority": 20,
                "operator_priority_override": 20,
                "nominal_power_w": 7000,
                "current_power_w": 1800,
                "current_target_power_w": 2200,
            },
        ]

        label = flow._device_status_label(devices[0])
        variable_label = flow._device_status_label(devices[1])
        summary_lines = flow._fleet_summary_lines(devices)

        self.assertIn("usable", label)
        self.assertIn("Ready for control", label)
        self.assertIn("power 1185 W", label)
        self.assertIn("guard ready", label)
        self.assertIn("action turn_on", label)
        self.assertIn("last queued", label)
        self.assertIn("priority 10", label)
        self.assertIn("nominal 1200 W", label)
        self.assertIn("power 1800 W", variable_label)
        self.assertIn("target 2200 W", variable_label)
        self.assertIn("last throttled", variable_label)
        self.assertIn("priority override 20", variable_label)
        self.assertIn("enabled override off", variable_label)
        self.assertIn("1 enabled", summary_lines[0])
        self.assertIn("1 usable", summary_lines[0])
        self.assertIn("1 blocked", summary_lines[0])
        self.assertIn("1 planned action(s)", summary_lines[0])
        self.assertEqual(summary_lines[1], "- Managed devices needing attention first:")
        self.assertIn("EV charger", summary_lines[2])
        self.assertIn("power 1800 W", summary_lines[2])
        self.assertIn("target 2200 W", summary_lines[2])
        self.assertIn("guard cooldown", summary_lines[2])
        self.assertIn("priority override 20", summary_lines[2])
        self.assertIn("enabled override off", summary_lines[2])
        self.assertNotIn("action hold", variable_label)
        self.assertNotIn("action hold", summary_lines[2])
        self.assertIn("Pool pump", summary_lines[3])
        self.assertIn("power 1185 W", summary_lines[3])
        self.assertIn("action turn_on", summary_lines[3])

    def test_overlay_runtime_device_details_carries_power_target_last_action_and_active_runtime(self) -> None:
        module = _load_config_flow_module()
        devices = [
            {
                "key": "ev",
                "name": "EV charger",
                "kind": module.DEVICE_KIND_VARIABLE,
                "entity_id": "number.ev_limit",
                "enabled": True,
                "priority": 20,
                "nominal_power_w": 7000,
            }
        ]
        coordinator = SimpleNamespace(
            data=SimpleNamespace(
                device_details={
                    "ev": {
                        "entity_id": "number.ev_limit",
                        "usable": True,
                        "effective_enabled": True,
                        "status": "Tracking export",
                        "guard_status": "ready",
                        "planned_action": "set_power",
                        "last_action_status": "throttled",
                        "current_power_w": 1800,
                        "current_target_power_w": 2200,
                        "observed_active": True,
                    }
                }
            )
        )

        enriched = module._overlay_runtime_device_details(devices, coordinator)

        self.assertEqual(enriched[0]["current_power_w"], 1800)
        self.assertEqual(enriched[0]["current_target_power_w"], 2200)
        self.assertEqual(enriched[0]["last_action_status"], "throttled")
        self.assertTrue(enriched[0]["observed_active"])

    def test_device_sort_key_surfaces_blocked_devices_before_healthy_plans(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace())
        devices = [
            {
                "key": "pool_pump",
                "name": "Pool pump",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.pool_pump",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "status": "Ready for control",
                "guard_status": "ready",
                "planned_action": "turn_on",
                "priority": 10,
                "nominal_power_w": 1200,
            },
            {
                "key": "ev",
                "name": "EV charger",
                "kind": module.DEVICE_KIND_VARIABLE,
                "entity_id": "number.ev_limit",
                "enabled": True,
                "effective_enabled": False,
                "usable": False,
                "status": "Held by guard",
                "guard_status": "cooldown",
                "planned_action": "hold",
                "priority": 20,
                "nominal_power_w": 7000,
            },
        ]

        ordered = sorted(devices, key=flow._device_sort_key)

        self.assertEqual(ordered[0]["name"], "EV charger")
        self.assertEqual(ordered[1]["name"], "Pool pump")

    def test_device_sort_key_and_fleet_summary_surface_recent_failures_as_attention(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace())
        devices = [
            {
                "key": "pool_pump",
                "name": "Pool pump",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.pool_pump",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "status": "Ready for control",
                "guard_status": "ready",
                "planned_action": "hold",
                "last_action_status": "failed",
                "priority": 10,
                "nominal_power_w": 1200,
                "current_power_w": 0,
            },
            {
                "key": "water_heater",
                "name": "Water heater",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.water_heater",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "status": "Ready for control",
                "guard_status": "ready",
                "planned_action": "hold",
                "priority": 20,
                "nominal_power_w": 900,
                "current_power_w": 0,
            },
        ]

        ordered = sorted(devices, key=flow._device_sort_key)
        summary_lines = flow._fleet_summary_lines(devices)

        self.assertEqual(ordered[0]["name"], "Pool pump")
        self.assertEqual(summary_lines[1], "- Managed devices needing attention first:")
        self.assertIn("Pool pump", summary_lines[2])
        self.assertIn("last failed", summary_lines[2])
        self.assertEqual(summary_lines[3], "- Other managed devices:")
        self.assertIn("Water heater", summary_lines[4])

    def test_managed_snapshot_surfaces_failed_only_attention(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace())
        devices = [
            {
                "key": "pool_pump",
                "name": "Pool pump",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.pool_pump",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "status": "Ready for control",
                "guard_status": "ready",
                "planned_action": "hold",
                "last_action_status": "failed",
                "priority": 10,
                "nominal_power_w": 1200,
                "current_power_w": 0,
            },
            {
                "key": "water_heater",
                "name": "Water heater",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.water_heater",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "status": "Ready for control",
                "guard_status": "ready",
                "planned_action": "hold",
                "priority": 20,
                "nominal_power_w": 900,
                "current_power_w": 0,
            },
        ]

        self.assertEqual(
            flow._managed_snapshot_text(devices),
            "Managed now: 2 | enabled: 2 | usable: 2 | 1 managed device needs attention | fixed managed: 2 | nominal: 2100 W | blocked first: none | next plan: none",
        )

    def test_device_next_step_prefers_global_blocker_guidance_before_local_promotion(self) -> None:
        module = _load_config_flow_module()
        module.build_native_command_center_summary = lambda coordinator: {
            "recommended_section": module.SOURCES_SECTION_LABEL,
            "next_action_summary": "Open sources path and finish source repair before promoting more devices.",
        }
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow.hass = SimpleNamespace(
            data={
                module.DOMAIN: {
                    "entry-1": SimpleNamespace(data=SimpleNamespace(), entry=SimpleNamespace(data={}, options={}))
                }
            }
        )

        next_step = flow._device_next_step(
            devices=[],
            issues=[],
            candidates=[{"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": module.DEVICE_KIND_FIXED}],
        )

        self.assertEqual(
            next_step,
            "Open sources path and finish source repair before promoting more devices.",
        )

    def test_device_blocker_summary_surfaces_global_blocker_reason_and_path(self) -> None:
        module = _load_config_flow_module()
        module.build_native_command_center_summary = lambda coordinator: {
            "recommended_section": module.SOURCES_SECTION_LABEL,
            "recommended_reason": "Mapped source blockers remain.",
            "recommended_path": module.SOURCES_CONFIGURE_PATH,
            "next_action_summary": "Open sources path and finish source repair before promoting more devices.",
        }
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow.hass = SimpleNamespace(
            data={
                module.DOMAIN: {
                    "entry-1": SimpleNamespace(data=SimpleNamespace(), entry=SimpleNamespace(data={}, options={}))
                }
            }
        )

        blocker_summary = flow._device_blocker_summary()

        self.assertIn("Before fleet work: Open sources path and finish source repair before promoting more devices.", blocker_summary)
        self.assertIn("Why: Mapped source blockers remain.", blocker_summary)

    def test_device_blocker_summary_confirms_when_fleet_work_can_proceed(self) -> None:
        module = _load_config_flow_module()
        module.build_native_command_center_summary = lambda coordinator: {
            "recommended_section": module.DEVICES_SECTION_LABEL,
            "next_action_summary": "Review the managed fleet next.",
        }
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow.hass = SimpleNamespace(
            data={
                module.DOMAIN: {
                    "entry-1": SimpleNamespace(data=SimpleNamespace(), entry=SimpleNamespace(data={}, options={}))
                }
            }
        )

        blocker_summary = flow._device_blocker_summary()

        self.assertEqual(
            blocker_summary,
            "No higher-priority Sensors, Controls, or Diagnostics blocker is currently ahead of fleet work.",
        )

    def test_device_pick_candidate_forms_surface_blocker_and_workspace_snapshots(self) -> None:
        module = _load_config_flow_module()
        module.build_native_command_center_summary = lambda coordinator: {
            "recommended_section": module.SOURCES_SECTION_LABEL,
            "recommended_reason": "Mapped source blockers remain.",
            "recommended_path": module.SOURCES_CONFIGURE_PATH,
            "next_action_summary": "Open sources path and finish source repair before promoting more devices.",
        }
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow.hass = SimpleNamespace(
            data={
                module.DOMAIN: {
                    "entry-1": SimpleNamespace(data=SimpleNamespace(), entry=SimpleNamespace(data={}, options={}))
                }
            },
            states=SimpleNamespace(
                async_all=lambda: [],
                get=lambda entity_id: None,
            ),
        )
        flow.async_show_form = lambda **kwargs: kwargs
        flow._pending_device_kind = module.DEVICE_KIND_FIXED
        flow._load_devices = lambda: ([
            {
                "key": "ev",
                "name": "EV charger",
                "kind": module.DEVICE_KIND_VARIABLE,
                "entity_id": "number.ev_limit",
                "enabled": True,
                "effective_enabled": False,
                "usable": False,
                "planned_action": "hold",
            },
            {
                "key": "pool",
                "name": "Pool pump",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.pool_pump",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "planned_action": "turn_on",
            },
        ], [])
        flow._device_candidates = lambda: [
            {"entity_id": "switch.ac_outlet_2", "name": "AC Outlet 2", "kind": module.DEVICE_KIND_FIXED, "label": "AC Outlet 2"},
            {"entity_id": "switch.towel_rail", "name": "Towel Rail", "kind": module.DEVICE_KIND_FIXED, "label": "Towel Rail"},
            {"entity_id": "number.ev_spare", "name": "Spare EV limit", "kind": module.DEVICE_KIND_VARIABLE, "label": "Spare EV limit"},
        ]
        flow._candidate_quick_picks = lambda kind: [
            {"entity_id": "switch.ac_outlet_2", "name": "AC Outlet 2", "kind": module.DEVICE_KIND_FIXED, "label": "AC Outlet 2"},
            {"entity_id": "switch.towel_rail", "name": "Towel Rail", "kind": module.DEVICE_KIND_FIXED, "label": "Towel Rail"},
        ]
        flow._candidate_options = lambda kind=None: [
            {"value": "switch.ac_outlet_2", "label": "AC Outlet 2"},
            {"value": "switch.towel_rail", "label": "Towel Rail"},
        ] if kind == module.DEVICE_KIND_FIXED else []

        shortlist = asyncio.run(flow.async_step_device_pick_candidate())
        full_list = asyncio.run(flow.async_step_device_pick_candidate_full())

        expected_blocker = (
            "Before fleet work: Open sources path and finish source repair before promoting more devices.\n"
            "Why: Mapped source blockers remain."
        )
        self.assertEqual(shortlist["description_placeholders"]["device_blocker_summary"], expected_blocker)
        self.assertEqual(full_list["description_placeholders"]["device_blocker_summary"], expected_blocker)
        self.assertEqual(
            shortlist["description_placeholders"]["device_next_step"],
            "Open sources path and finish source repair before promoting more devices.",
        )
        self.assertEqual(
            full_list["description_placeholders"]["device_next_step"],
            "Open sources path and finish source repair before promoting more devices.",
        )
        self.assertEqual(
            shortlist["description_placeholders"]["managed_snapshot"],
            "Managed now: 2 | enabled: 1 | usable: 1 | 2 managed devices need attention | fixed managed: 1 | variable managed: 1 | nominal: 0 W | blocked first: EV charger | next plan: Pool pump",
        )
        self.assertEqual(
            shortlist["description_placeholders"]["device_summary"],
            "- Fleet summary: 2 device(s), 1 enabled, 1 usable, 1 blocked, 1 planned action(s), 2 managed devices need attention, 1 fixed, 1 variable, 0 W nominal controllable power\n"
            "- Managed devices needing attention first:\n"
            "- EV charger [not usable | power n/a] (variable, disabled, priority 0, nominal 0 W)\n"
            "- Pool pump [usable | power n/a | action turn_on] (fixed, enabled, priority 0, nominal 0 W)\n"
            "- Other managed devices:\n"
            "- None",
        )
        self.assertEqual(
            full_list["description_placeholders"]["unmanaged_snapshot"],
            "Unmanaged now: 3 | fixed candidates: 2 | variable candidates: 1 | top candidate: AC Outlet 2 | 3 need review | fixed review: 2 | variable review: 1 | top usefulness: likely useful",
        )
        self.assertEqual(shortlist["description_placeholders"]["fixed_candidate_count"], "2")
        self.assertEqual(shortlist["description_placeholders"]["variable_candidate_count"], "1")
        self.assertEqual(
            shortlist["description_placeholders"]["top_candidate"],
            "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings",
        )
        self.assertEqual(
            shortlist["description_placeholders"]["review_candidate"],
            "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings",
        )
        self.assertIn(
            "Pick a candidate from the shortlist or full list.",
            full_list["description_placeholders"]["candidate_path_summary"],
        )
        self.assertEqual(shortlist["description_placeholders"]["configure_path"], module.DEVICES_CONFIGURE_PATH)
        self.assertEqual(full_list["description_placeholders"]["detailed_management_summary"], flow._detailed_management_summary())

    def test_detailed_management_summary_falls_back_to_secondary_review_path_wording(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow._coordinator = lambda: SimpleNamespace(data=SimpleNamespace())
        module.build_native_command_center_summary = lambda coordinator: {}

        self.assertEqual(
            flow._detailed_management_summary(),
            f"Use {module.DETAILED_MANAGEMENT_PATH} for deeper managed-device review.",
        )

    def test_managed_snapshot_treats_non_executable_plans_as_blocked_before_usable_flips_false(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))

        devices = [
            {
                "key": "pool",
                "name": "Pool pump",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.pool_pump",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "planned_action": "turn_on",
                "action_executable": False,
            },
            {
                "key": "ev",
                "name": "EV charger",
                "kind": module.DEVICE_KIND_VARIABLE,
                "entity_id": "number.ev_limit",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "planned_action": "set_power",
                "action_executable": True,
            },
        ]

        self.assertEqual(
            flow._managed_snapshot_text(devices),
            "Managed now: 2 | enabled: 2 | usable: 2 | 2 managed devices need attention | fixed managed: 1 | variable managed: 1 | nominal: 0 W | blocked first: Pool pump | next plan: Pool pump",
        )
        self.assertEqual(
            flow._fleet_summary_lines(devices),
            [
                "- Fleet summary: 2 device(s), 2 enabled, 2 usable, 1 blocked, 2 planned action(s), 2 managed devices need attention, 1 fixed, 1 variable, 0 W nominal controllable power",
                "- Managed devices needing attention first:",
                "- Pool pump [usable | power n/a | action turn_on] (fixed, enabled, priority 0, nominal 0 W)",
                "- EV charger [usable | power n/a | action set_power] (variable, enabled, priority 0, nominal 0 W)",
                "- Other managed devices:",
                "- None",
            ],
        )

    def test_managed_snapshot_and_fleet_summary_surface_active_managed_runtime(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))

        devices = [
            {
                "key": "pool",
                "name": "Pool pump",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.pool_pump",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "planned_action": "turn_on",
                "observed_active": True,
                "current_power_w": 1185,
                "nominal_power_w": 1200,
            },
            {
                "key": "ev",
                "name": "EV charger",
                "kind": module.DEVICE_KIND_VARIABLE,
                "entity_id": "number.ev_limit",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "planned_action": "set_power",
                "observed_active": True,
                "current_power_w": 2200,
                "nominal_power_w": 7000,
            },
        ]

        self.assertEqual(
            flow._managed_snapshot_text(devices),
            "Managed now: 2 | enabled: 2 | usable: 2 | active load: 3385 W | active managed: 2 devices | 2 managed devices need attention | fixed managed: 1 | variable managed: 1 | nominal: 8200 W | blocked first: none | next plan: EV charger",
        )
        self.assertEqual(
            flow._fleet_summary_lines(devices)[0],
            "- Fleet summary: 2 device(s), 2 enabled, 2 usable, 0 blocked, 2 planned action(s), 2 managed devices need attention, active load 3385 W, 2 active managed devices, 1 fixed, 1 variable, 8200 W nominal controllable power",
        )

    def test_fleet_summary_lines_split_attention_first_from_other_managed_devices(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))

        devices = [
            {
                "key": "water_heater",
                "name": "Water heater",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.water_heater",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "planned_action": "hold",
            },
            {
                "key": "pool",
                "name": "Pool pump",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.pool_pump",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "planned_action": "turn_on",
            },
        ]

        self.assertEqual(
            flow._fleet_summary_lines(devices),
            [
                "- Fleet summary: 2 device(s), 2 enabled, 2 usable, 0 blocked, 1 planned action(s), 1 managed device needs attention, 2 fixed, 0 variable, 0 W nominal controllable power",
                "- Managed devices needing attention first:",
                "- Pool pump [usable | power n/a | action turn_on] (fixed, enabled, priority 0, nominal 0 W)",
                "- Other managed devices:",
                "- Water heater [usable | power n/a] (fixed, enabled, priority 0, nominal 0 W)",
            ],
        )

    def test_support_form_exposes_exact_bucket_paths(self) -> None:
        module = _load_config_flow_module()
        module.build_native_command_center_summary = lambda coordinator: {
            "recommended_section": module.SUPPORT_SECTION_LABEL,
            "recommended_reason": "Review diagnostics details.",
            "recommended_path": module.SUPPORT_CONFIGURE_PATH,
            "next_action_summary": "Open support path and review the current blocker.",
        }
        module.build_native_operator_readiness = lambda coordinator: {
            "phase": "support_needed",
            "summary": "Diagnostics needed.",
            "next_step": "Open support path and review the current blocker.",
        }
        module.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
            "validation_details": {"issues": []},
        }
        module.build_source_attention_summary = lambda *args, **kwargs: "None"
        module.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        module.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        module.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar"
        module.build_install_provenance = lambda *args, **kwargs: {
            "live_validation_safe": True,
            "summary": "Installed package ok",
        }
        module.build_install_consistency_summary = lambda provenance: "Installed package version metadata matches the running code version."
        module.build_install_fingerprint_summary = lambda provenance: "- component_root: /config/custom_components/zero_net_export"
        module._infer_grid_sensor_mode = lambda merged: module.GRID_SENSOR_MODE_SEPARATE
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow.hass = SimpleNamespace(
            data={
                module.DOMAIN: {
                    "entry-1": SimpleNamespace(data=SimpleNamespace(health_summary="Healthy"), entry=SimpleNamespace(data={}, options={}))
                }
            },
            states=SimpleNamespace(async_all=lambda: [], get=lambda entity_id: None),
        )
        flow.async_show_form = lambda **kwargs: kwargs

        result = asyncio.run(flow.async_step_support())
        placeholders = result["description_placeholders"]

        self.assertEqual(placeholders["sources_path"], module.SOURCES_CONFIGURE_PATH)
        self.assertEqual(placeholders["policy_path"], module.POLICY_CONFIGURE_PATH)
        self.assertEqual(placeholders["devices_path"], module.DEVICES_CONFIGURE_PATH)
        self.assertEqual(placeholders["mode_path"], module.MODE_CONTROL_PATH)
        self.assertEqual(placeholders["support_path"], module.SUPPORT_CONFIGURE_PATH)
        self.assertEqual(
            placeholders["support_install_next_step"],
            "Exact-build trust currently looks good. Use the device-page diagnostics snapshot only if you need the full install evidence.",
        )
        self.assertEqual(
            placeholders["support_install_snapshot_path"],
            f"{module.INTEGRATION_DEVICE_PATH} -> Review diagnostics snapshot",
        )

    def test_existing_fleet_forms_keep_managed_and_unmanaged_snapshots_visible(self) -> None:
        module = _load_config_flow_module()
        module.build_native_command_center_summary = lambda coordinator: {
            "recommended_section": module.SOURCES_SECTION_LABEL,
            "recommended_reason": "Mapped source blockers remain.",
            "recommended_path": module.SOURCES_CONFIGURE_PATH,
            "next_action_summary": "Open sources path and finish source repair before fleet edits.",
        }
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow.hass = SimpleNamespace(
            data={
                module.DOMAIN: {
                    "entry-1": SimpleNamespace(data=SimpleNamespace(), entry=SimpleNamespace(data={}, options={}))
                }
            },
            states=SimpleNamespace(async_all=lambda: []),
        )
        flow.async_show_form = lambda **kwargs: kwargs
        flow._load_devices = lambda: ([
            {
                "key": "pool",
                "name": "Pool pump",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.pool_pump",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "planned_action": "turn_on",
            },
            {
                "key": "ev",
                "name": "EV charger",
                "kind": module.DEVICE_KIND_VARIABLE,
                "entity_id": "number.ev_limit",
                "enabled": True,
                "effective_enabled": False,
                "usable": False,
                "planned_action": "hold",
            },
        ], [])
        flow._device_candidates = lambda: [
            {"entity_id": "switch.ac_outlet_2", "name": "AC Outlet 2", "kind": module.DEVICE_KIND_FIXED, "label": "AC Outlet 2"},
            {"entity_id": "switch.towel_rail", "name": "Towel Rail", "kind": module.DEVICE_KIND_FIXED, "label": "Towel Rail"},
        ]

        bulk_enable = asyncio.run(flow.async_step_device_bulk_enable())
        edit_pick = asyncio.run(flow.async_step_device_edit_pick())
        remove = asyncio.run(flow.async_step_device_remove())

        for result in (bulk_enable, edit_pick, remove):
            self.assertEqual(
                result["description_placeholders"]["device_next_step"],
                "Open sources path and finish source repair before fleet edits.",
            )
            self.assertEqual(
                result["description_placeholders"]["managed_snapshot"],
                "Managed now: 2 | enabled: 1 | usable: 1 | 2 managed devices need attention | fixed managed: 1 | variable managed: 1 | nominal: 0 W | blocked first: EV charger | next plan: Pool pump",
            )
            self.assertEqual(
                result["description_placeholders"]["unmanaged_snapshot"],
                "Unmanaged now: 2 | fixed candidates: 2 | variable candidates: 0 | top candidate: AC Outlet 2 | 2 need review | fixed review: 2 | top usefulness: likely useful",
            )
            self.assertEqual(result["description_placeholders"]["fixed_candidate_count"], "2")
            self.assertEqual(result["description_placeholders"]["variable_candidate_count"], "0")
            self.assertEqual(
                result["description_placeholders"]["top_candidate"],
                "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings",
            )
            self.assertEqual(
                result["description_placeholders"]["review_candidate"],
                "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings",
            )
            self.assertEqual(
                result["description_placeholders"]["candidate_summary"],
                "- Review-first unmanaged candidates:\n"
                "- AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings\n"
                "- Towel Rail (fixed) | likely useful | key warning: No immediate warnings",
            )

    def test_device_vetting_form_surfaces_blocker_summary_placeholder(self) -> None:
        module = _load_config_flow_module()
        module.build_native_command_center_summary = lambda coordinator: {
            "recommended_section": module.SOURCES_SECTION_LABEL,
            "recommended_reason": "Mapped source blockers remain.",
            "recommended_path": module.SOURCES_CONFIGURE_PATH,
            "next_action_summary": "Open sources path and finish source repair before promoting more devices.",
        }
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow.hass = SimpleNamespace(
            data={
                module.DOMAIN: {
                    "entry-1": SimpleNamespace(data=SimpleNamespace(), entry=SimpleNamespace(data={}, options={}))
                }
            },
            states=SimpleNamespace(async_all=lambda: []),
        )
        flow.async_show_form = lambda **kwargs: kwargs
        flow._pending_candidate_entity_id = "switch.ac_outlet_2"
        flow._pending_candidate_summary = {
            "name": "AC Outlet 2",
            "entity_id": "switch.ac_outlet_2",
            "kind": module.DEVICE_KIND_FIXED,
            "fit_confidence": "high",
            "fit_summary": "Strong match.",
            "warnings": [],
            "suggested_template_label": "Fixed plug",
            "suggested_template_description": "Use the fixed plug preset.",
        }

        result = asyncio.run(flow.async_step_device_vetting())

        self.assertEqual(result["description_placeholders"]["device_blocker_summary"], (
            "Before fleet work: Open sources path and finish source repair before promoting more devices.\n"
            "Why: Mapped source blockers remain."
        ))
        self.assertEqual(
            result["description_placeholders"]["device_next_step"],
            "Open sources path and finish source repair before promoting more devices.",
        )
        self.assertEqual(
            result["description_placeholders"]["candidate_preview"],
            "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings",
        )
        self.assertEqual(
            result["description_placeholders"]["candidate_summary"],
            "- No unmanaged candidate devices discovered right now",
        )
        self.assertNotIn("candidate_entity_id", result["description_placeholders"])

    def test_device_add_form_surfaces_blocker_summary_placeholder(self) -> None:
        module = _load_config_flow_module()
        module.build_native_command_center_summary = lambda coordinator: {
            "recommended_section": module.SOURCES_SECTION_LABEL,
            "recommended_reason": "Mapped source blockers remain.",
            "recommended_path": module.SOURCES_CONFIGURE_PATH,
            "next_action_summary": "Open sources path and finish source repair before promoting more devices.",
        }
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow.hass = SimpleNamespace(
            data={
                module.DOMAIN: {
                    "entry-1": SimpleNamespace(data=SimpleNamespace(), entry=SimpleNamespace(data={}, options={}))
                }
            },
            states=SimpleNamespace(async_all=lambda: []),
        )
        flow.async_show_form = lambda **kwargs: kwargs
        flow._pending_device_kind = module.DEVICE_KIND_FIXED

        result = asyncio.run(flow.async_step_device_add())

        self.assertEqual(result["description_placeholders"]["device_blocker_summary"], (
            "Before fleet work: Open sources path and finish source repair before promoting more devices.\n"
            "Why: Mapped source blockers remain."
        ))
        self.assertEqual(
            result["description_placeholders"]["device_next_step"],
            "Open sources path and finish source repair before promoting more devices.",
        )
        self.assertEqual(
            result["description_placeholders"]["candidate_summary"],
            "- No unmanaged candidate devices discovered right now",
        )

    def test_promotion_forms_keep_managed_and_unmanaged_context_visible(self) -> None:
        module = _load_config_flow_module()
        module.build_native_command_center_summary = lambda coordinator: {
            "recommended_section": module.SOURCES_SECTION_LABEL,
            "recommended_reason": "Mapped source blockers remain.",
            "recommended_path": module.SOURCES_CONFIGURE_PATH,
            "next_action_summary": "Open sources path and finish source repair before promoting more devices.",
        }
        module.get_device_templates = lambda kind: [
            SimpleNamespace(key="fixed_plug", label="Fixed plug", description="Use the fixed plug preset."),
        ]
        module.get_device_template = lambda kind, key: SimpleNamespace(
            key="fixed_plug",
            label="Fixed plug",
            description="Use the fixed plug preset.",
            defaults={},
        )
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow.hass = SimpleNamespace(
            data={
                module.DOMAIN: {
                    "entry-1": SimpleNamespace(data=SimpleNamespace(), entry=SimpleNamespace(data={}, options={}))
                }
            },
            states=SimpleNamespace(async_all=lambda: []),
        )
        flow.async_show_form = lambda **kwargs: kwargs
        flow._load_devices = lambda: ([
            {
                "key": "pool",
                "name": "Pool pump",
                "entity_id": "switch.pool_pump",
                "kind": module.DEVICE_KIND_FIXED,
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "planned_action": "on",
            },
            {
                "key": "ev",
                "name": "EV charger",
                "entity_id": "number.ev_charger_current",
                "kind": module.DEVICE_KIND_VARIABLE,
                "enabled": True,
                "effective_enabled": True,
                "usable": False,
                "guard_reason": "Source stale",
            },
        ], [])
        flow._device_candidates = lambda: [
            {
                "entity_id": "switch.ac_outlet_2",
                "name": "AC Outlet 2",
                "kind": module.DEVICE_KIND_FIXED,
                "label": "AC Outlet 2",
            },
            {
                "entity_id": "switch.towel_rail",
                "name": "Towel Rail",
                "kind": module.DEVICE_KIND_FIXED,
                "label": "Towel Rail",
            },
        ]
        flow._pending_device_kind = module.DEVICE_KIND_FIXED
        flow._pending_candidate_entity_id = "switch.ac_outlet_2"
        flow._pending_candidate_summary = {
            "name": "AC Outlet 2",
            "entity_id": "switch.ac_outlet_2",
            "kind": module.DEVICE_KIND_FIXED,
            "fit_confidence": "high",
            "fit_usefulness": "likely useful",
            "fit_summary": "Strong match.",
            "warnings": [],
            "suggested_template_key": "fixed_plug",
            "suggested_template_label": "Fixed plug",
            "suggested_template_description": "Use the fixed plug preset.",
        }
        flow._pending_device_template_key = "fixed_plug"

        vetting = asyncio.run(flow.async_step_device_vetting())
        template = asyncio.run(flow.async_step_device_template())
        add = asyncio.run(flow.async_step_device_add())

        for result in (vetting, template, add):
            self.assertEqual(
                result["description_placeholders"]["device_next_step"],
                "Open sources path and finish source repair before promoting more devices.",
            )
            self.assertEqual(
                result["description_placeholders"]["managed_snapshot"],
                "Managed now: 2 | enabled: 2 | usable: 1 | 2 managed devices need attention | fixed managed: 1 | variable managed: 1 | nominal: 0 W | blocked first: EV charger | next plan: Pool pump",
            )
            self.assertEqual(
                result["description_placeholders"]["device_summary"],
                "- Fleet summary: 2 device(s), 2 enabled, 1 usable, 1 blocked, 1 planned action(s), 2 managed devices need attention, 1 fixed, 1 variable, 0 W nominal controllable power\n"
                "- Managed devices needing attention first:\n"
                "- EV charger [not usable | power n/a] (variable, enabled, priority 0, nominal 0 W)\n"
                "- Pool pump [usable | power n/a | action on] (fixed, enabled, priority 0, nominal 0 W)\n"
                "- Other managed devices:\n"
                "- None",
            )
            self.assertEqual(
                result["description_placeholders"]["unmanaged_snapshot"],
                "Unmanaged now: 2 | fixed candidates: 2 | variable candidates: 0 | top candidate: AC Outlet 2 | 2 need review | fixed review: 2 | top usefulness: likely useful",
            )
            self.assertEqual(result["description_placeholders"]["fixed_candidate_count"], "2")
            self.assertEqual(result["description_placeholders"]["variable_candidate_count"], "0")
            self.assertEqual(
                result["description_placeholders"]["top_candidate"],
                "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings",
            )
            self.assertEqual(
                result["description_placeholders"]["review_candidate"],
                "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings",
            )
            self.assertEqual(
                result["description_placeholders"]["candidate_summary"],
                "- Review-first unmanaged candidates:\n"
                "- AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings\n"
                "- Towel Rail (fixed) | likely useful | key warning: No immediate warnings",
            )
            self.assertEqual(result["description_placeholders"]["configure_path"], module.DEVICES_CONFIGURE_PATH)
        self.assertEqual(
            vetting["description_placeholders"]["candidate_preview"],
            "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings",
        )
        self.assertEqual(
            template["description_placeholders"]["candidate_preview"],
            "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings",
        )
        self.assertEqual(
            template["description_placeholders"]["promotion_path_summary"],
            "Promotion path: shortlist or full list -> review candidate -> choose preset -> save into Managed Devices.",
        )
        self.assertEqual(
            add["description_placeholders"]["promotion_path_summary"],
            "Promotion path: shortlist or full list -> review candidate -> choose preset -> save into Managed Devices.",
        )
        self.assertEqual(template["description_placeholders"]["candidate_fit_usefulness"], "likely useful")
        self.assertEqual(template["description_placeholders"]["candidate_fit_summary"], "Strong match.")
        self.assertEqual(template["description_placeholders"]["candidate_warnings"], "- No immediate warnings detected.")
        self.assertEqual(template["description_placeholders"]["suggested_template"], "Fixed plug")
        self.assertEqual(
            template["description_placeholders"]["candidate_next_step"],
            "Choose the closest preset, then confirm the final device settings before saving into Managed Devices.",
        )
        self.assertEqual(
            add["description_placeholders"]["candidate_preview"],
            "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings",
        )
        self.assertEqual(add["description_placeholders"]["selected_candidate_fit"], "likely useful")
        self.assertNotIn("candidate_hint", add["description_placeholders"])
        self.assertNotIn("candidate_entity_id", vetting["description_placeholders"])

    def test_managed_devices_summaries_and_shortlist_hide_raw_candidate_entity_ids(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow.hass = SimpleNamespace(
            data={
                module.DOMAIN: {
                    "entry-1": SimpleNamespace(data=SimpleNamespace(), entry=SimpleNamespace(data={}, options={}))
                }
            },
            states=SimpleNamespace(async_all=lambda: [], get=lambda entity_id: None),
        )
        flow.async_show_form = lambda **kwargs: kwargs
        flow._load_devices = lambda: (
            [
                {
                    "key": "pool",
                    "entity_id": "switch.pool_pump",
                    "name": "Pool pump",
                    "kind": module.DEVICE_KIND_FIXED,
                    "enabled": True,
                    "priority": 40,
                    "nominal_power_w": 900,
                }
            ],
            [],
        )
        flow._device_candidates = lambda: [
            {
                "entity_id": "switch.ac_outlet_2",
                "name": "AC Outlet 2",
                "kind": module.DEVICE_KIND_FIXED,
                "label": "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings",
            },
            {
                "entity_id": "number.ev_spare",
                "name": "Spare EV limit",
                "kind": module.DEVICE_KIND_VARIABLE,
                "label": "Spare EV limit (variable) | useful fallback | key warning: Variable power range should be checked before promotion",
            },
        ]
        flow._candidate_quick_picks = lambda kind: [
            {
                "entity_id": "switch.ac_outlet_2",
                "name": "AC Outlet 2",
                "kind": module.DEVICE_KIND_FIXED,
                "label": "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings",
                "state": "off",
            }
        ]
        flow._candidate_options = lambda kind=None: [
            {"value": "switch.ac_outlet_2", "label": "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings"},
        ]
        flow._pending_device_kind = module.DEVICE_KIND_FIXED

        devices_screen = asyncio.run(flow.async_step_devices())
        shortlist = asyncio.run(flow.async_step_device_pick_candidate())

        self.assertIn("Pool pump", devices_screen["description_placeholders"]["device_summary"])
        self.assertNotIn("switch.pool_pump", devices_screen["description_placeholders"]["device_summary"])
        self.assertIn("priority 40", devices_screen["description_placeholders"]["device_summary"])
        self.assertIn("AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings", devices_screen["description_placeholders"]["candidate_summary"])
        self.assertNotIn("switch.ac_outlet_2", devices_screen["description_placeholders"]["candidate_summary"])
        self.assertNotIn("number.ev_spare", devices_screen["description_placeholders"]["candidate_summary"])
        self.assertIn("AC Outlet 2 (state off) | likely useful | key warning: No immediate warnings", shortlist["description_placeholders"]["top_candidates"])
        self.assertNotIn("switch.ac_outlet_2", shortlist["description_placeholders"]["top_candidates"])

    def test_candidate_quick_picks_keep_first_review_first_candidate_visible(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow._top_candidates_for_kind = lambda kind, limit=12: [
            {"entity_id": "switch.air_purifier", "name": "Air Purifier", "kind": module.DEVICE_KIND_FIXED, "domain": "switch"},
            {"entity_id": "switch.coffee_machine", "name": "Coffee machine", "kind": module.DEVICE_KIND_FIXED, "domain": "switch"},
            {"entity_id": "switch.dishwasher_power", "name": "Dishwasher Power", "kind": module.DEVICE_KIND_FIXED, "domain": "switch"},
            {"entity_id": "switch.ac_outlet_2", "name": "AC Outlet 2", "kind": module.DEVICE_KIND_FIXED, "domain": "switch"},
        ]
        flow._candidate_summary = lambda entity_id: {
            "switch.air_purifier": {"fit_confidence": "high"},
            "switch.coffee_machine": {"fit_confidence": "high"},
            "switch.dishwasher_power": {"fit_confidence": "high"},
            "switch.ac_outlet_2": {"fit_confidence": "medium"},
        }.get(entity_id, {"fit_confidence": "high"})
        module.assess_candidate = lambda candidate: {
            "confidence": "medium" if candidate.get("entity_id") == "switch.ac_outlet_2" else "high",
            "summary": "Needs review." if candidate.get("entity_id") == "switch.ac_outlet_2" else "Strong match.",
            "warnings": ["Generic outlet label."] if candidate.get("entity_id") == "switch.ac_outlet_2" else [],
        }

        quick_picks = flow._candidate_quick_picks(module.DEVICE_KIND_FIXED)

        self.assertEqual(
            [item["entity_id"] for item in quick_picks],
            ["switch.air_purifier", "switch.coffee_machine", "switch.ac_outlet_2"],
        )

    def test_candidate_options_label_top_and_review_first_roles(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow._device_candidates = lambda: [
            {
                "entity_id": "switch.air_purifier",
                "name": "Air Purifier",
                "kind": module.DEVICE_KIND_FIXED,
                "label": "Air Purifier (fixed) | likely useful | key warning: No immediate warnings",
            },
            {
                "entity_id": "switch.ac_outlet_2",
                "name": "AC Outlet 2",
                "kind": module.DEVICE_KIND_FIXED,
                "label": "AC Outlet 2 (fixed) | review first | key warning: Generic outlet label",
            },
        ]
        module.assess_candidate = lambda candidate: {
            "confidence": "medium" if candidate.get("entity_id") == "switch.ac_outlet_2" else "high",
            "summary": "Needs review." if candidate.get("entity_id") == "switch.ac_outlet_2" else "Strong match.",
            "warnings": ["Generic outlet label"] if candidate.get("entity_id") == "switch.ac_outlet_2" else [],
        }

        options = flow._candidate_options(kind=module.DEVICE_KIND_FIXED)

        self.assertEqual(
            options[0]["label"],
            "Suggested now: Air Purifier (fixed) | likely useful | key warning: No immediate warnings",
        )
        self.assertEqual(
            options[1]["label"],
            "Review first: AC Outlet 2 (fixed) | review first | key warning: Generic outlet label",
        )

    def test_candidate_shortlist_summary_marks_review_first_top_candidate(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1", options={}, data={}))
        flow.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: [], get=lambda entity_id: None), data={})
        flow.async_show_form = lambda **kwargs: kwargs
        flow._load_devices = lambda: ([], [])
        flow._coordinator = lambda: SimpleNamespace(data=SimpleNamespace())
        flow._device_blocker_summary = lambda: "No higher-priority Sensors, Controls, or Diagnostics blocker is currently ahead of fleet work."
        flow._device_next_step = lambda devices, issues, candidates: "Review the shortlist and promote the next candidate."
        flow._managed_snapshot_text = lambda devices: "Managed now: 0 | enabled: 0 | usable: 0 | blocked first: none | next plan: none"
        flow._unmanaged_snapshot_text = lambda candidates: "Unmanaged now: 1 | fixed candidates: 1 | variable candidates: 0 | top candidate: AC Outlet 2 | 1 needs review | top usefulness: review first"
        flow._candidate_snapshot_text = lambda candidates: "- AC Outlet 2 (fixed) | review first | key warning: Generic outlet label"
        flow._detailed_management_summary = lambda: "device path"
        flow._top_candidate_focus_text = lambda candidate: "AC Outlet 2 (fixed) | review first | key warning: Generic outlet label"
        flow._review_candidate_focus_text = lambda candidates: "AC Outlet 2 (fixed) | review first | key warning: Generic outlet label"
        flow._candidate_quick_picks = lambda kind: [
            {
                "entity_id": "switch.ac_outlet_2",
                "name": "AC Outlet 2",
                "kind": module.DEVICE_KIND_FIXED,
                "label": "AC Outlet 2 (fixed) | review first | key warning: Generic outlet label",
                "state": "off",
            }
        ]
        flow._candidate_options = lambda kind=None: [
            {"value": "switch.ac_outlet_2", "label": "Suggested now, review first: AC Outlet 2 (fixed) | review first | key warning: Generic outlet label"},
        ]
        flow._device_candidates = lambda: [
            {
                "entity_id": "switch.ac_outlet_2",
                "name": "AC Outlet 2",
                "kind": module.DEVICE_KIND_FIXED,
                "label": "AC Outlet 2 (fixed) | review first | key warning: Generic outlet label",
                "state": "off",
            }
        ]
        module.assess_candidate = lambda candidate: {
            "confidence": "medium",
            "summary": "Needs review.",
            "warnings": ["Generic outlet label"],
        }
        module.build_candidate_preview = lambda candidate, include_entity_id=False, include_kind=False, include_state=True, **kwargs: (
            "AC Outlet 2 (state off) | review first | key warning: Generic outlet label"
        )

        shortlist = asyncio.run(flow.async_step_device_pick_candidate())

        self.assertIn(
            "Suggested now, review first: AC Outlet 2 (state off) | review first | key warning: Generic outlet label",
            shortlist["description_placeholders"]["top_candidates"],
        )

    def test_build_device_action_feedback_for_promotion_uses_native_paths(self) -> None:
        module = _load_config_flow_module()
        module.discover_candidate_devices = lambda states, managed_ids: [
            {"entity_id": "switch.ac_outlet_2", "name": "AC Outlet 2", "kind": module.DEVICE_KIND_FIXED},
            {"entity_id": "number.ev_charger", "name": "EV Charger", "kind": module.DEVICE_KIND_VARIABLE},
        ]
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(title="Zero Net Export", entry_id="entry-1", options={}))
        flow.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []), data={})

        feedback = flow._build_device_action_feedback(
            action="promote",
            devices=[{"key": "pool", "name": "Pool pump", "entity_id": "switch.pool_pump", "kind": module.DEVICE_KIND_FIXED, "enabled": True}],
            device={"key": "pool", "name": "Pool pump", "entity_id": "switch.pool_pump", "kind": module.DEVICE_KIND_FIXED, "enabled": True},
        )

        self.assertIsNotNone(feedback)
        assert feedback is not None
        self.assertEqual(feedback["title"], "managed-device promotion saved")
        self.assertIn("Promoted Pool pump into Managed Devices as a fixed load.", feedback["message"])
        self.assertNotIn("switch.pool_pump", feedback["message"])
        self.assertIn("Managed now: 1 | enabled: 1 | usable: 0 | fixed managed: 1 | nominal: 0 W | blocked first: none | next plan: none", feedback["message"])
        self.assertIn("Unmanaged now: 2 | fixed candidates: 1 | variable candidates: 1 | top candidate: AC Outlet 2 | 2 need review | fixed review: 1 | variable review: 1 | top usefulness: likely useful", feedback["message"])
        self.assertIn("Review-first unmanaged candidate: AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings", feedback["message"])
        self.assertIn("Managed Devices path: devices path", feedback["message"])
        self.assertIn(
            "Detailed review path, only after the main fleet step is clear: detailed device path",
            feedback["message"],
        )
        self.assertIn(
            "Next step: reopen devices path to confirm the fleet snapshot, then review AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings first in the unmanaged section.",
            feedback["message"],
        )

    def test_unmanaged_snapshot_surfaces_review_first_backlog_and_top_warning(self) -> None:
        module = _load_config_flow_module()
        module.assess_candidate = lambda candidate: {
            "confidence": "medium" if candidate.get("entity_id") == "input_boolean.virtual_load" else "high",
            "summary": "Review before promotion.",
            "warnings": ["This is an input_boolean helper."] if candidate.get("entity_id") == "input_boolean.virtual_load" else [],
        }
        module.build_candidate_review_hint = lambda candidate, include_warning=True, max_warning_chars=56, **kwargs: (
            "review carefully | warn This is an input_boolean helper."
            if candidate.get("entity_id") == "input_boolean.virtual_load" and include_warning
            else "review carefully"
            if candidate.get("entity_id") == "input_boolean.virtual_load"
            else "likely useful"
        )
        summary = module.ZeroNetExportOptionsFlow._unmanaged_snapshot_text(
            [
                {
                    "entity_id": "input_boolean.virtual_load",
                    "name": "Virtual load",
                    "kind": module.DEVICE_KIND_FIXED,
                },
                {
                    "entity_id": "switch.hot_water",
                    "name": "Hot water relay",
                    "kind": module.DEVICE_KIND_FIXED,
                },
            ]
        )

        self.assertEqual(
            summary,
            "Unmanaged now: 2 | fixed candidates: 2 | variable candidates: 0 | top candidate: Virtual load | 1 needs review | fixed review: 1 | top usefulness: review carefully | top warning: This is an input_boolean helper.",
        )

    def test_unmanaged_snapshot_counts_low_confidence_candidates_as_needing_review(self) -> None:
        module = _load_config_flow_module()
        module.assess_candidate = lambda candidate: {
            "confidence": "high" if candidate.get("entity_id") == "switch.hot_water" else "low",
            "summary": "Review before promotion.",
            "warnings": [],
        }
        module.build_candidate_review_hint = lambda candidate, include_warning=True, max_warning_chars=56, **kwargs: (
            "likely useful"
            if candidate.get("entity_id") == "switch.hot_water"
            else (
                "review carefully | warn Helper-backed load needs review."
                if include_warning
                else "review carefully"
            )
        )
        summary = module.ZeroNetExportOptionsFlow._unmanaged_snapshot_text(
            [
                {
                    "entity_id": "switch.hot_water",
                    "name": "Hot water relay",
                    "kind": module.DEVICE_KIND_FIXED,
                },
                {
                    "entity_id": "input_boolean.virtual_load",
                    "name": "Virtual load",
                    "kind": module.DEVICE_KIND_FIXED,
                },
            ]
        )

        self.assertEqual(
            summary,
            "Unmanaged now: 2 | fixed candidates: 2 | variable candidates: 0 | top candidate: Hot water relay | 1 needs review | fixed review: 1 | review first: Virtual load | review usefulness: review carefully | review warning: Helper-backed load needs review. | top usefulness: likely useful",
        )

    def test_candidate_snapshot_groups_review_first_before_ready_candidates(self) -> None:
        module = _load_config_flow_module()
        module.assess_candidate = lambda candidate: {
            "confidence": "low" if candidate.get("entity_id") == "input_boolean.virtual_load" else "high",
            "summary": "Review before promotion.",
            "warnings": ["Helper-backed load needs review."] if candidate.get("entity_id") == "input_boolean.virtual_load" else [],
        }
        module.build_candidate_review_hint = lambda candidate, include_warning=True, max_warning_chars=56, **kwargs: (
            "review carefully | warn Helper-backed load needs review."
            if candidate.get("entity_id") == "input_boolean.virtual_load" and include_warning
            else "review carefully"
            if candidate.get("entity_id") == "input_boolean.virtual_load"
            else "likely useful"
        )

        summary = module.ZeroNetExportOptionsFlow._candidate_snapshot_text(
            [
                {
                    "entity_id": "switch.hot_water",
                    "name": "Hot water relay",
                    "kind": module.DEVICE_KIND_FIXED,
                },
                {
                    "entity_id": "input_boolean.virtual_load",
                    "name": "Virtual load",
                    "kind": module.DEVICE_KIND_FIXED,
                },
            ]
        )

        self.assertIn("- Review-first unmanaged candidates:", summary)
        self.assertIn("- Ready to promote next:", summary)
        self.assertIn("Virtual load (fixed)", summary)
        self.assertIn("Hot water relay (fixed)", summary)
        self.assertLess(summary.index("Virtual load (fixed)"), summary.index("- Ready to promote next:"))
        self.assertLess(summary.index("- Ready to promote next:"), summary.index("Hot water relay (fixed)"))

    def test_candidate_summary_passes_name_and_entity_id_into_fit_assessment(self) -> None:
        module = _load_config_flow_module()
        captured: dict[str, object] = {}

        def _assess_candidate(candidate):
            captured.update(candidate)
            return {
                "confidence": "medium",
                "summary": "Review before promotion.",
                "warnings": [],
            }

        module.assess_candidate = _assess_candidate
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(title="Zero Net Export", entry_id="entry-1", options={}))
        flow.hass = SimpleNamespace(
            states=SimpleNamespace(
                get=lambda entity_id: SimpleNamespace(
                    state="off",
                    attributes={
                        "friendly_name": "AC Outlet 2",
                        "device_class": "outlet",
                        "unit_of_measurement": "",
                    },
                )
            )
        )

        summary = flow._candidate_summary("switch.ac_outlet_2")

        self.assertIsNotNone(summary)
        self.assertEqual(captured["entity_id"], "switch.ac_outlet_2")
        self.assertEqual(captured["name"], "AC Outlet 2")
        self.assertEqual(captured["domain"], "switch")
        self.assertEqual(captured["device_class"], "outlet")

    def test_build_device_action_feedback_for_bulk_enable_summarizes_fleet(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(title="Zero Net Export", entry_id="entry-1", options={}))
        flow.hass = SimpleNamespace(data={})

        feedback = flow._build_device_action_feedback(
            action="bulk_enable",
            devices=[
                {"key": "pool", "enabled": True},
                {"key": "ev", "enabled": False},
            ],
        )

        self.assertIsNotNone(feedback)
        assert feedback is not None
        self.assertEqual(feedback["title"], "managed-device enablement saved")
        self.assertIn("Fleet now: 2 managed | 1 enabled | 1 disabled", feedback["message"])
        self.assertIn("Managed now: 2 | enabled: 1 | usable: 0 | blocked first: none | next plan: none", feedback["message"])
        self.assertIn("Unmanaged now: 0 | fixed candidates: 0 | variable candidates: 0 | top candidate: none", feedback["message"])
        self.assertIn(
            "Next step: reopen devices path to confirm the updated enablement snapshot, then use the deeper device review path only if you need more per-device runtime detail.",
            feedback["message"],
        )

    def test_build_device_action_feedback_prioritizes_blocker_first_handoff(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(title="Zero Net Export", entry_id="entry-1", options={}))
        flow._device_blocker_summary = lambda: "Before fleet work: Open sources path and finish the required source mapping.\nWhy: Missing required source roles.\nPath: sources path"

        feedback = flow._build_device_action_feedback(
            action="promote",
            devices=[{"key": "pool", "name": "Pool pump", "entity_id": "switch.pool_pump", "kind": module.DEVICE_KIND_FIXED, "enabled": True}],
            device={"key": "pool", "name": "Pool pump", "entity_id": "switch.pool_pump", "kind": module.DEVICE_KIND_FIXED, "enabled": True},
        )

        self.assertIsNotNone(feedback)
        assert feedback is not None
        self.assertIn("Blocker-first handoff:", feedback["message"])
        self.assertIn("- Before fleet work: Open sources path and finish the required source mapping.", feedback["message"])
        self.assertIn("- Why: Missing required source roles.", feedback["message"])
        self.assertIn("Next step: Open sources path and finish the required source mapping.", feedback["message"])

    def test_build_device_action_feedback_remove_prefers_review_first_candidate(self) -> None:
        module = _load_config_flow_module()
        module.assess_candidate = lambda candidate: {
            "confidence": "medium" if candidate.get("entity_id") == "switch.virtual_load" else "high",
            "summary": "Review before promotion.",
            "warnings": ["Helper-backed load needs review."] if candidate.get("entity_id") == "switch.virtual_load" else [],
        }
        module.discover_candidate_devices = lambda states, managed_ids: [
            {"entity_id": "switch.hot_water", "name": "Hot water", "kind": module.DEVICE_KIND_FIXED},
            {"entity_id": "switch.virtual_load", "name": "Virtual load", "kind": module.DEVICE_KIND_FIXED},
        ]
        module.build_candidate_preview = lambda candidate, include_entity_id=True, include_kind=True, include_state=False, **kwargs: (
            "Virtual load (fixed) | review first | key warning: Helper-backed load needs review."
            if candidate.get("entity_id") == "switch.virtual_load"
            else "Hot water (fixed) | likely useful | key warning: No immediate warnings"
        )
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(title="Zero Net Export", entry_id="entry-1", options={}))
        flow.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []), data={})

        feedback = flow._build_device_action_feedback(
            action="remove",
            devices=[],
            previous_device={"key": "pool", "name": "Pool pump", "entity_id": "switch.pool_pump", "kind": module.DEVICE_KIND_FIXED, "enabled": True},
        )

        self.assertIsNotNone(feedback)
        assert feedback is not None
        self.assertIn(
            "Next step: reopen devices path to review the remaining fleet, then review Virtual load (fixed) | review first | key warning: Helper-backed load needs review. first in the unmanaged section.",
            feedback["message"],
        )

    def test_device_next_step_uses_candidate_preview_without_raw_entity_id(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1"))
        flow.hass = SimpleNamespace(data={module.DOMAIN: {"entry-1": None}})
        flow._top_candidate_focus_text = lambda candidate: "AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings"

        next_step = flow._device_next_step(
            devices=[],
            issues=[],
            candidates=[{"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": module.DEVICE_KIND_FIXED}],
        )

        self.assertIn("Start with AC Outlet 2 (fixed) | likely useful | key warning: No immediate warnings", next_step)
        self.assertNotIn("switch.ac_outlet_2", next_step)

    def test_device_next_step_prefers_first_review_candidate_when_it_differs_from_top_rank(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1"))
        flow.hass = SimpleNamespace(data={module.DOMAIN: {"entry-1": None}})
        module.assess_candidate = lambda candidate: {
            "confidence": "medium" if candidate.get("entity_id") == "input_boolean.virtual_load" else "high",
            "warnings": ["Helper entities may not reflect a controllable appliance load."]
            if candidate.get("entity_id") == "input_boolean.virtual_load"
            else [],
        }
        flow._top_candidate_focus_text = lambda candidate: (
            "Virtual load (fixed) | review first | key warning: Helper entities may not reflect a controllable appliance load."
            if candidate["name"] == "Virtual load"
            else "Dishwasher Power (fixed) | likely useful | key warning: No immediate warnings"
        )

        next_step = flow._device_next_step(
            devices=[],
            issues=[],
            candidates=[
                {"name": "Dishwasher Power", "entity_id": "switch.dishwasher_power", "kind": module.DEVICE_KIND_FIXED},
                {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": module.DEVICE_KIND_FIXED},
            ],
        )

        self.assertIn(
            "Start with Virtual load (fixed) | review first | key warning: Helper entities may not reflect a controllable appliance load.",
            next_step,
        )
        self.assertNotIn("Dishwasher Power", next_step)

    def test_device_next_step_uses_promotion_wording_when_no_candidates_exist_yet(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace(entry_id="entry-1"))
        flow.hass = SimpleNamespace(data={module.DOMAIN: {"entry-1": None}})

        next_step = flow._device_next_step(devices=[], issues=[], candidates=[])

        self.assertEqual(
            next_step,
            "Choose Add fixed load device or Add variable load device to start the first managed-device promotion flow.",
        )

    def test_device_sort_key_prefers_actionable_devices_first(self) -> None:
        module = _load_config_flow_module()
        flow = module.ZeroNetExportOptionsFlow(SimpleNamespace())
        devices = [
            {
                "key": "disabled_ready",
                "name": "Disabled but ready",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.disabled_ready",
                "enabled": False,
                "effective_enabled": False,
                "usable": True,
                "priority": 1,
                "nominal_power_w": 800,
            },
            {
                "key": "enabled_blocked",
                "name": "Enabled but blocked",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.enabled_blocked",
                "enabled": True,
                "effective_enabled": True,
                "usable": False,
                "priority": 1,
                "nominal_power_w": 900,
            },
            {
                "key": "enabled_ready",
                "name": "Enabled and ready",
                "kind": module.DEVICE_KIND_FIXED,
                "entity_id": "switch.enabled_ready",
                "enabled": True,
                "effective_enabled": True,
                "usable": True,
                "priority": 50,
                "nominal_power_w": 1000,
            },
        ]

        summary_lines = flow._fleet_summary_lines(devices)

        self.assertEqual(summary_lines[1], "- Managed devices needing attention first:")
        self.assertIn("Enabled but blocked", summary_lines[2])
        self.assertEqual(summary_lines[3], "- Other managed devices:")
        self.assertIn("Enabled and ready", summary_lines[4])
        self.assertIn("Disabled but ready", summary_lines[5])


if __name__ == "__main__":
    unittest.main()
