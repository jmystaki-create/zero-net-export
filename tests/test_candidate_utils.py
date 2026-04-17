from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"
CONST_PATH = PACKAGE_ROOT / "const.py"
MODULE_PATH = PACKAGE_ROOT / "candidate_utils.py"


def _load_candidate_utils_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", CONST_PATH)
    assert const_spec and const_spec.loader
    integration_const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = integration_const_module
    const_spec.loader.exec_module(integration_const_module)

    module_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.candidate_utils", MODULE_PATH)
    assert module_spec and module_spec.loader
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


class CandidateUtilsTests(unittest.TestCase):
    def test_discover_candidate_devices_prefers_real_load_signals_before_helpers(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="input_boolean.virtual_load", state="on", attributes={"friendly_name": "Virtual load"}),
            SimpleNamespace(entity_id="light.patio", state="on", attributes={"friendly_name": "Patio lights"}),
            SimpleNamespace(entity_id="number.ev_charger_limit", state="16", attributes={"friendly_name": "EV charger limit"}),
            SimpleNamespace(entity_id="switch.hot_water", state="off", attributes={"friendly_name": "Hot water relay"}),
            SimpleNamespace(entity_id="input_number.helper_limit", state="12", attributes={"friendly_name": "Helper limit"}),
            SimpleNamespace(entity_id="switch.adguard_home_filtering", state="on", attributes={"friendly_name": "AdGuard Home Filtering"}),
            SimpleNamespace(entity_id="switch.ac_outlet_2", state="off", attributes={"friendly_name": "AC Outlet 2", "device_class": "outlet"}),
            SimpleNamespace(entity_id="switch.bedroom_crossfade", state="off", attributes={"friendly_name": "3rd Bedroom Crossfade"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual(
            [candidate["entity_id"] for candidate in candidates],
            [
                "switch.hot_water",
                "number.ev_charger_limit",
                "switch.ac_outlet_2",
                "input_number.helper_limit",
                "input_boolean.virtual_load",
            ],
        )

    def test_discover_candidate_devices_filters_managed_internal_unknown_and_unavailable_entities(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="switch.managed_device", state="on", attributes={"friendly_name": "Managed"}),
            SimpleNamespace(entity_id="switch.zero_net_export_enabled", state="on", attributes={"friendly_name": "Zero Net Export Enabled"}),
            SimpleNamespace(entity_id="switch.unknown_device", state="unknown", attributes={"friendly_name": "Unknown"}),
            SimpleNamespace(entity_id="number.unavailable_device", state="unavailable", attributes={"friendly_name": "Unavailable"}),
            SimpleNamespace(entity_id="sensor.not_a_device", state="42", attributes={"friendly_name": "Not a device"}),
            SimpleNamespace(entity_id="switch.pool_pump", state="off", attributes={"friendly_name": "Pool pump"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids={"switch.managed_device"})

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["entity_id"], "switch.pool_pump")
        self.assertEqual(candidates[0]["kind"], "fixed")

    def test_assess_candidate_flags_helper_and_missing_unit_risk(self) -> None:
        module = _load_candidate_utils_module()

        helper_fit = module.assess_candidate(
            {
                "domain": "input_boolean",
                "kind": "fixed",
                "state": "on",
                "unit": "",
                "device_class": "",
            }
        )
        variable_fit = module.assess_candidate(
            {
                "domain": "input_number",
                "kind": "variable",
                "state": "12",
                "unit": "",
                "device_class": "",
            }
        )

        self.assertEqual(helper_fit["confidence"], "low")
        self.assertIn("automation intent", helper_fit["summary"])
        self.assertTrue(any("input_boolean helper" in warning for warning in helper_fit["warnings"]))
        self.assertEqual(helper_fit["suitability_level"], "low")
        self.assertEqual(helper_fit["safety_level"], "low")
        self.assertEqual(helper_fit["operational_value_level"], "low")
        self.assertEqual(variable_fit["confidence"], "medium")
        self.assertTrue(any("meaningful unit" in warning for warning in variable_fit["warnings"]))
        self.assertEqual(variable_fit["suitability_level"], "medium")
        self.assertEqual(variable_fit["safety_level"], "medium")
        self.assertIn("Variable control", variable_fit["suitability_summary"])

    def test_assess_candidate_caps_helper_backed_variable_controls_at_review_first_confidence(self) -> None:
        module = _load_candidate_utils_module()

        fit = module.assess_candidate(
            {
                "entity_id": "input_number.lounge_room_heated_floor",
                "name": "Lounge Room Heated Floor",
                "domain": "input_number",
                "kind": "variable",
                "state": "65",
                "unit": "%",
                "device_class": "",
            }
        )

        self.assertEqual(fit["confidence"], "medium")
        self.assertIn("Helper-backed variable control", fit["safety_summary"])
        self.assertIn("review-first", fit["operational_value_summary"])

    def test_assess_candidate_adds_balanced_review_dimensions_for_strong_switch(self) -> None:
        module = _load_candidate_utils_module()

        fit = module.assess_candidate(
            {
                "entity_id": "switch.hot_water",
                "name": "Hot water relay",
                "domain": "switch",
                "kind": "fixed",
                "state": "off",
                "unit": "",
                "device_class": "",
            }
        )

        self.assertEqual(fit["confidence"], "high")
        self.assertEqual(fit["suitability_level"], "high")
        self.assertEqual(fit["safety_level"], "high")
        self.assertEqual(fit["operational_value_level"], "high")
        self.assertIn("clean native fit", fit["suitability_summary"])
        self.assertIn("safe enough", fit["safety_summary"])
        self.assertIn("more likely to matter operationally", fit["operational_value_summary"])

    def test_build_candidate_usefulness_summary_uses_operator_facing_labels(self) -> None:
        module = _load_candidate_utils_module()

        summary = module.build_candidate_usefulness_summary(
            {
                "entity_id": "switch.hot_water",
                "name": "Hot water relay",
                "domain": "switch",
                "kind": "fixed",
                "state": "off",
                "unit": "",
                "device_class": "",
            }
        )

        self.assertEqual(
            summary,
            "likely useful: Switch entities are usually likely fixed-load candidates when they control a real appliance or relay.",
        )

    def test_assess_candidate_penalizes_obvious_service_toggle_names(self) -> None:
        module = _load_candidate_utils_module()

        fit = module.assess_candidate(
            {
                "entity_id": "switch.adguard_home_filtering",
                "name": "AdGuard Home Filtering",
                "domain": "switch",
                "kind": "fixed",
                "state": "on",
                "unit": "",
                "device_class": "",
            }
        )

        self.assertEqual(fit["confidence"], "medium")
        self.assertTrue(any("service, media feature, or software toggle" in warning for warning in fit["warnings"]))
        self.assertIn("feature toggle or service control", fit["suitability_summary"])
        self.assertIn("does not clearly look like a physical discretionary load", fit["safety_summary"])

    def test_assess_candidate_penalizes_generic_power_labels(self) -> None:
        module = _load_candidate_utils_module()

        fit = module.assess_candidate(
            {
                "entity_id": "switch.garage_power",
                "name": "Garage Power",
                "domain": "switch",
                "kind": "fixed",
                "state": "off",
                "unit": "",
                "device_class": "",
            }
        )

        self.assertEqual(fit["confidence"], "medium")
        self.assertTrue(any("generic power/circuit wording" in warning for warning in fit["warnings"]))
        self.assertIn("generic enough", fit["suitability_summary"])
        self.assertIn("generic circuit labels", fit["operational_value_summary"])

    def test_assess_candidate_penalizes_anonymous_outlets(self) -> None:
        module = _load_candidate_utils_module()

        fit = module.assess_candidate(
            {
                "entity_id": "switch.ac_outlet_2",
                "name": "AC Outlet 2",
                "domain": "switch",
                "kind": "fixed",
                "state": "off",
                "unit": "",
                "device_class": "outlet",
            }
        )

        self.assertEqual(fit["confidence"], "medium")
        self.assertTrue(any("generic outlet hardware" in warning for warning in fit["warnings"]))
        self.assertIn("anonymous outlet labels", fit["suitability_summary"])
        self.assertIn("what is plugged into it", fit["warnings"][0] if fit["warnings"] else "")

    def test_discover_candidate_devices_excludes_media_feature_toggles_and_none_wrappers_but_keeps_real_loads(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="switch.master_bedroom_speech_enhancement", state="off", attributes={"friendly_name": "Living Room Speech enhancement"}),
            SimpleNamespace(entity_id="switch.living_room_subwoofer_enabled_2", state="on", attributes={"friendly_name": "Living Room Subwoofer enabled"}),
            SimpleNamespace(entity_id="switch.lounge_room_none", state="off", attributes={"friendly_name": "Lounge Room Power"}),
            SimpleNamespace(entity_id="switch.ac_outlet_2", state="off", attributes={"friendly_name": "AC Outlet 2", "device_class": "outlet"}),
            SimpleNamespace(entity_id="switch.ebike_charger", state="off", attributes={"friendly_name": "Ebike Charger"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual(
            [candidate["entity_id"] for candidate in candidates],
            [
                "switch.ebike_charger",
                "switch.ac_outlet_2",
            ],
        )

    def test_discover_candidate_devices_excludes_generic_lights_but_keeps_positive_load_names(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="light.patio", state="on", attributes={"friendly_name": "Patio lights"}),
            SimpleNamespace(entity_id="light.pool_pump", state="on", attributes={"friendly_name": "Pool pump light"}),
            SimpleNamespace(entity_id="switch.hot_water", state="off", attributes={"friendly_name": "Hot water relay"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual(
            [candidate["entity_id"] for candidate in candidates],
            ["switch.hot_water", "light.pool_pump"],
        )

    def test_discover_candidate_devices_excludes_switch_exposed_lighting_circuits(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="switch.batten_roof_lights", state="off", attributes={"friendly_name": "Batten Roof Lights"}),
            SimpleNamespace(entity_id="switch.workshop_lamp", state="off", attributes={"friendly_name": "Workshop Lamp"}),
            SimpleNamespace(entity_id="switch.ebike_charger", state="off", attributes={"friendly_name": "Ebike Charger"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual(
            [candidate["entity_id"] for candidate in candidates],
            ["switch.ebike_charger"],
        )

    def test_discover_candidate_devices_excludes_variable_settings_and_telemetry_numbers(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="number.ev_charger_limit", state="16", attributes={"friendly_name": "EV charger limit", "unit_of_measurement": "A"}),
            SimpleNamespace(entity_id="number.bathroom_room_temperature_limit", state="30", attributes={"friendly_name": "Bathroom Room temperature limit", "device_class": "temperature"}),
            SimpleNamespace(entity_id="number.switchbot_lock_pro_auto_relock_time", state="0", attributes={"friendly_name": "SwitchBot Lock Pro Auto-relock time", "unit_of_measurement": "s"}),
            SimpleNamespace(entity_id="number.system_rome_dyn_price_fee", state="0", attributes={"friendly_name": "System Rome Dyn. price fee"}),
            SimpleNamespace(entity_id="number.energy_buy_price", state="0.27", attributes={"friendly_name": "Energy buy price", "unit_of_measurement": "$/kWh"}),
            SimpleNamespace(entity_id="input_number.sell_tax_percent", state="10", attributes={"friendly_name": "Sell tax percent", "unit_of_measurement": "%"}),
            SimpleNamespace(entity_id="number.lounge_room_surround_level", state="3", attributes={"friendly_name": "Lounge Room Surround level"}),
            SimpleNamespace(entity_id="number.living_room_balance", state="0", attributes={"friendly_name": "Living Room Balance"}),
            SimpleNamespace(entity_id="number.living_room_bass", state="0", attributes={"friendly_name": "Living Room Bass"}),
            SimpleNamespace(entity_id="number.living_room_treble", state="0", attributes={"friendly_name": "Living Room Treble"}),
            SimpleNamespace(entity_id="number.x1_p6k_us_s_battery_capacity", state="20000", attributes={"friendly_name": "X1 Battery capacity", "device_class": "energy_storage", "unit_of_measurement": "Wh"}),
            SimpleNamespace(entity_id="number.living_room_sub_gain_2", state="0", attributes={"friendly_name": "Living Room Sub gain"}),
            SimpleNamespace(entity_id="number.dishwasher_start_in_relative", state="0", attributes={"friendly_name": "Dishwasher Start in relative", "unit_of_measurement": "h"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual([candidate["entity_id"] for candidate in candidates], ["number.ev_charger_limit"])

    def test_discover_candidate_devices_excludes_obvious_service_media_and_none_switches(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="switch.ac_outlet_2", state="off", attributes={"friendly_name": "AC Outlet 2", "device_class": "outlet"}),
            SimpleNamespace(entity_id="switch.bedroom_crossfade", state="off", attributes={"friendly_name": "3rd Bedroom Crossfade"}),
            SimpleNamespace(entity_id="switch.adguard_home_filtering", state="on", attributes={"friendly_name": "AdGuard Home Filtering"}),
            SimpleNamespace(entity_id="switch.sonos_alarm_28", state="off", attributes={"friendly_name": "Garage On_36 alarm 10:45"}),
            SimpleNamespace(entity_id="switch.lounge_room_streamer", state="off", attributes={"friendly_name": "Lounge Room Streamer"}),
            SimpleNamespace(entity_id="switch.shellyproem50_a0dd6ca0970c_switch_0", state="off", attributes={"friendly_name": "shellyproem50-a0dd6ca0970c"}),
            SimpleNamespace(entity_id="switch.living_room_none", state="off", attributes={"friendly_name": "Living Room Power"}),
            SimpleNamespace(entity_id="switch.dishwasher_childlock", state="off", attributes={"friendly_name": "Dishwasher Child lock"}),
            SimpleNamespace(entity_id="switch.dishwasher_eco_dry", state="off", attributes={"friendly_name": "Dishwasher Eco dry"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual(
            [candidate["entity_id"] for candidate in candidates],
            ["switch.ac_outlet_2"],
        )

    def test_discover_candidate_devices_prefers_explicit_appliances_before_generic_power_labels(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="switch.garage_power", state="off", attributes={"friendly_name": "Garage Power"}),
            SimpleNamespace(entity_id="switch.third_bedroom_power", state="off", attributes={"friendly_name": "3rd Bedroom Power"}),
            SimpleNamespace(entity_id="switch.ebike_charger", state="off", attributes={"friendly_name": "Ebike Charger"}),
            SimpleNamespace(entity_id="switch.coffee_machine", state="off", attributes={"friendly_name": "Coffee machine"}),
            SimpleNamespace(entity_id="switch.ac_outlet_2", state="off", attributes={"friendly_name": "AC Outlet 2", "device_class": "outlet"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual(
            [candidate["entity_id"] for candidate in candidates],
            [
                "switch.coffee_machine",
                "switch.ebike_charger",
                "switch.ac_outlet_2",
                "switch.third_bedroom_power",
                "switch.garage_power",
            ],
        )

    def test_discover_candidate_devices_does_not_let_generic_power_labels_hide_behind_plug_entity_ids(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="switch.smart_plug_6", state="off", attributes={"friendly_name": "Garage Power"}),
            SimpleNamespace(entity_id="switch.coffee_machine", state="off", attributes={"friendly_name": "Coffee machine"}),
            SimpleNamespace(entity_id="switch.plug_8", state="off", attributes={"friendly_name": "Air Purifier"}),
            SimpleNamespace(entity_id="switch.towel_rail", state="off", attributes={"friendly_name": "Towel Rail"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual(
            [candidate["entity_id"] for candidate in candidates],
            [
                "switch.plug_8",
                "switch.coffee_machine",
                "switch.towel_rail",
                "switch.smart_plug_6",
            ],
        )

    def test_build_candidate_review_line_formats_label_level_and_summary(self) -> None:
        module = _load_candidate_utils_module()

        line = module.build_candidate_review_line(
            "Control suitability",
            "high",
            "Switch control is usually a clean native fit for fixed loads.",
        )

        self.assertEqual(
            line,
            "Control suitability: strong - Switch control is usually a clean native fit for fixed loads.",
        )

    def test_build_candidate_preview_includes_usefulness_and_key_warning(self) -> None:
        module = _load_candidate_utils_module()

        preview = module.build_candidate_preview(
            {
                "entity_id": "input_boolean.virtual_load",
                "name": "Virtual load",
                "kind": "fixed",
                "domain": "input_boolean",
                "state": "on",
                "unit": "",
                "device_class": "",
            }
        )

        self.assertIn("Virtual load (input_boolean.virtual_load, fixed)", preview)
        self.assertIn("review carefully", preview)
        self.assertIn("input_boolean helper", preview)

    def test_build_candidate_preview_uses_no_warning_fallback_for_strong_match(self) -> None:
        module = _load_candidate_utils_module()

        preview = module.build_candidate_preview(
            {
                "entity_id": "switch.hot_water",
                "name": "Hot water relay",
                "kind": "fixed",
                "domain": "switch",
                "state": "off",
                "unit": "",
                "device_class": "",
            },
            include_state=True,
        )

        self.assertIn("likely useful", preview)
        self.assertIn("state off", preview)
        self.assertIn("No immediate warnings", preview)

    def test_build_candidate_preview_keeps_helper_backed_variable_controls_review_first(self) -> None:
        module = _load_candidate_utils_module()

        preview = module.build_candidate_preview(
            {
                "entity_id": "input_number.lounge_room_heated_floor",
                "name": "Lounge Room Heated Floor",
                "kind": "variable",
                "domain": "input_number",
                "state": "65",
                "unit": "%",
                "device_class": "",
            }
        )

        self.assertIn("review first", preview)
        self.assertIn("input_number.lounge_room_heated_floor", preview)
        self.assertIn("input_number helper", preview)

    def test_build_candidate_preview_demotes_generic_power_labels_to_plausible_match(self) -> None:
        module = _load_candidate_utils_module()

        preview = module.build_candidate_preview(
            {
                "entity_id": "switch.garage_power",
                "name": "Garage Power",
                "kind": "fixed",
                "domain": "switch",
                "state": "off",
                "unit": "",
                "device_class": "",
            }
        )

        self.assertIn("review first", preview)
        self.assertIn("generic power/circuit wording", preview)

    def test_build_candidate_name_summary_stays_compact_for_sensor_states(self) -> None:
        module = _load_candidate_utils_module()

        candidates = [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed", "domain": "switch", "state": "off"},
            {"name": "AdGuard Home Filtering", "entity_id": "switch.adguard_home_filtering", "kind": "fixed", "domain": "switch", "state": "off"},
            {"name": "AdGuard Home Parental control", "entity_id": "switch.adguard_home_parental_control", "kind": "fixed", "domain": "switch", "state": "off"},
            {"name": "3rd Bedroom Crossfade", "entity_id": "switch.bedroom_crossfade", "kind": "fixed", "domain": "switch", "state": "off"},
            {"name": "3rd Bedroom Loudness", "entity_id": "switch.bedroom_loudness", "kind": "fixed", "domain": "switch", "state": "off"},
        ]

        summary = module.build_candidate_name_summary(candidates)

        self.assertIn("AC Outlet 2 (fixed | review first | generic outlet label)", summary)
        self.assertIn("AdGuard Home Filtering (fixed | review first | service-style label)", summary)
        self.assertIn("+2 more", summary)
        self.assertLessEqual(len(summary), 240)

    def test_build_candidate_name_summary_marks_helper_backed_variable_controls(self) -> None:
        module = _load_candidate_utils_module()

        summary = module.build_candidate_name_summary(
            [
                {
                    "name": "Lounge Room Heated Floor",
                    "entity_id": "input_number.lounge_room_heated_floor",
                    "kind": "variable",
                    "domain": "input_number",
                    "state": "65",
                    "unit": "%",
                    "device_class": "",
                }
            ]
        )

        self.assertEqual(
            summary,
            "Lounge Room Heated Floor (variable | review first | helper-backed)",
        )

    def test_build_candidate_fit_summary_carries_warning_hints(self) -> None:
        module = _load_candidate_utils_module()

        summary = module.build_candidate_fit_summary(
            [
                {
                    "name": "Virtual load",
                    "entity_id": "input_boolean.virtual_load",
                    "kind": "fixed",
                    "domain": "input_boolean",
                    "state": "on",
                    "unit": "",
                    "device_class": "",
                },
                {
                    "name": "Hot water relay",
                    "entity_id": "switch.hot_water",
                    "kind": "fixed",
                    "domain": "switch",
                    "state": "off",
                    "unit": "",
                    "device_class": "",
                },
            ]
        )

        self.assertIn("Virtual load: review carefully | warn This is an input_boolean helper.", summary)
        self.assertIn("Hot water relay: likely useful", summary)
        self.assertLessEqual(len(summary), 240)

    def test_build_candidate_overview_summary_distinguishes_overview_from_shortlist(self) -> None:
        module = _load_candidate_utils_module()

        candidates = [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
            {"name": "Hot water relay", "entity_id": "switch.hot_water", "kind": "fixed"},
            {"name": "EV charger limit", "entity_id": "number.ev_charger_limit", "kind": "variable"},
            {"name": "Pool pump", "entity_id": "switch.pool_pump", "kind": "fixed"},
        ]

        summary = module.build_candidate_overview_summary(candidates)

        self.assertIn("4 candidates | 3 fixed candidates | 1 variable candidate | top AC Outlet 2 | review first", summary)
        self.assertIn("generic outlet hardware", summary)
        self.assertLessEqual(len(summary), 240)

    def test_build_candidate_overview_summary_carries_top_warning_hint(self) -> None:
        module = _load_candidate_utils_module()

        summary = module.build_candidate_overview_summary(
            [
                {
                    "name": "Virtual load",
                    "entity_id": "input_boolean.virtual_load",
                    "kind": "fixed",
                    "domain": "input_boolean",
                    "state": "on",
                    "unit": "",
                    "device_class": "",
                },
                {"name": "Hot water relay", "entity_id": "switch.hot_water", "kind": "fixed"},
            ]
        )

        self.assertIn("2 candidates | 2 fixed candidates | top Virtual load | review carefully", summary)
        self.assertIn("warn This is an input_boolean helper.", summary)
        self.assertLessEqual(len(summary), 240)

    def test_discover_candidate_devices_demotes_anonymous_numbered_outlets_below_named_appliances(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="switch.ac_outlet_2", state="off", attributes={"friendly_name": "AC Outlet 2", "device_class": "outlet"}),
            SimpleNamespace(entity_id="switch.smart_plug_6", state="off", attributes={"friendly_name": "Smart Plug 6"}),
            SimpleNamespace(entity_id="switch.coffee_machine", state="off", attributes={"friendly_name": "Coffee machine"}),
            SimpleNamespace(entity_id="switch.air_purifier", state="off", attributes={"friendly_name": "Air Purifier"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual(
            [candidate["entity_id"] for candidate in candidates],
            [
                "switch.air_purifier",
                "switch.coffee_machine",
                "switch.ac_outlet_2",
                "switch.smart_plug_6",
            ],
        )

    def test_discover_candidate_devices_excludes_ventilation_style_loads_from_promotion(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="switch.exhaust_fan", state="off", attributes={"friendly_name": "Exhaust Fan"}),
            SimpleNamespace(entity_id="switch.hood_power", state="off", attributes={"friendly_name": "Hood Power"}),
            SimpleNamespace(entity_id="switch.dishwasher_power", state="off", attributes={"friendly_name": "Dishwasher Power"}),
            SimpleNamespace(entity_id="switch.air_purifier", state="off", attributes={"friendly_name": "Air Purifier"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual(
            [candidate["entity_id"] for candidate in candidates],
            [
                "switch.air_purifier",
                "switch.dishwasher_power",
            ],
        )

    def test_discover_candidate_devices_does_not_treat_ac_outlets_as_aircon_loads(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="switch.ac_outlet_2", state="off", attributes={"friendly_name": "AC Outlet 2", "device_class": "outlet"}),
            SimpleNamespace(entity_id="switch.dishwasher_power", state="off", attributes={"friendly_name": "Dishwasher Power"}),
            SimpleNamespace(entity_id="switch.garage_power", state="off", attributes={"friendly_name": "Garage Power"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual(
            [candidate["entity_id"] for candidate in candidates],
            [
                "switch.dishwasher_power",
                "switch.ac_outlet_2",
                "switch.garage_power",
            ],
        )

    def test_discover_candidate_devices_drops_helper_duplicates_when_native_load_label_matches(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(
                entity_id="switch.ac_outlet_1",
                state="off",
                attributes={"friendly_name": "Lounge Room - Heated Floor"},
            ),
            SimpleNamespace(
                entity_id="input_number.lounge_room_heated_floor",
                state="18",
                attributes={"friendly_name": "Lounge Room Heated Floor"},
            ),
            SimpleNamespace(
                entity_id="input_number.powder_room_heated_floor",
                state="18",
                attributes={"friendly_name": "Powder Room Heated Floor"},
            ),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual(
            [candidate["entity_id"] for candidate in candidates],
            [
                "switch.ac_outlet_1",
                "input_number.powder_room_heated_floor",
            ],
        )


if __name__ == "__main__":
    unittest.main()
