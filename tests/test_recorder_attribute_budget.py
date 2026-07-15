"""Recorder attribute budget regressions."""

from __future__ import annotations

import json
from types import SimpleNamespace
import unittest

from tests.test_button_entity_categories import _load_button_module
from tests.test_device_page_managed_settings import _load_simple_platform_module
from tests.test_sensor_entity_categories import _load_sensor_module


def _attr_size(attributes: dict) -> int:
    return len(json.dumps(attributes, default=str, sort_keys=True))


def _coordinator(validation_details: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        entry=SimpleNamespace(entry_id="entry-1", title="Winter Plan", data={}, options={}, version=1),
        data=SimpleNamespace(
            validation_details=validation_details or {},
            device_details={
                "the_7th": {
                    "name": "The 7th",
                    "entity_id": "light.7th",
                    "kind": "fixed",
                    "enabled": True,
                    "effective_enabled": True,
                    "usable": True,
                    "nominal_power_w": 5,
                    "planned_action": "hold",
                    "guard_status": "ready",
                    "last_action_result_message": "applied",
                    "debug_blob": "x" * 5000,
                }
            },
        ),
    )


def _large_validation_details() -> dict:
    return {
        "health_status": "healthy",
        "health_summary": "No active stale-data or command-failure health condition",
        "action_history_count": 20,
        "action_history": [{"device": f"Load {index}", "result": "applied", "detail": "x" * 500} for index in range(20)],
        "daily_metrics": {f"2026-07-{index:02d}": {"per_device_active_seconds": {"load": index}} for index in range(1, 8)},
        "source_diagnostics": {
            f"source_{index}": {"status": "ok", "entity_id": f"sensor.source_{index}", "detail": "x" * 500}
            for index in range(10)
        },
        "source_freshness": {
            f"source_{index}": {"stale": False, "entity_id": f"sensor.source_{index}", "detail": "x" * 300}
            for index in range(10)
        },
        "calibration_hints": ["x" * 500 for _ in range(10)],
    }


class RecorderAttributeBudgetTest(unittest.TestCase):
    def test_validation_detail_entities_expose_recorder_safe_attributes(self) -> None:
        sensor_module = _load_sensor_module()
        button_module = _load_button_module()
        switch_module = _load_simple_platform_module("switch", "switch", "SwitchEntity")
        select_module = _load_simple_platform_module("select", "select", "SelectEntity")
        number_module = _load_simple_platform_module("number", "number", "NumberEntity")
        from custom_components.zero_net_export.entity import RECORDER_ATTRIBUTE_TARGET_BYTES

        coordinator = _coordinator(_large_validation_details())

        entities = [
            switch_module.ZeroNetExportEnabledSwitch(coordinator, "enabled", "Enabled"),
            select_module.ZeroNetExportModeSelect(coordinator, "mode", "Mode"),
            number_module.ZeroNetExportNumber(coordinator, "target_export_w", "Target export", 0, 10000, 10),
            button_module.ZeroNetExportResetControllerOverridesButton(coordinator),
            sensor_module.ZeroNetExportSensor(coordinator, "health_status", "Health status"),
        ]

        for entity in entities:
            attrs = entity.extra_state_attributes
            self.assertLess(_attr_size(attrs), RECORDER_ATTRIBUTE_TARGET_BYTES)
            self.assertNotIn("action_history", attrs)
            self.assertNotIn("daily_metrics", attrs)
            self.assertNotIn("source_diagnostics", attrs)
            self.assertEqual(attrs["action_history_count"], 20)
            self.assertEqual(attrs["source_role_count"], 10)

    def test_managed_devices_attributes_keep_counts_and_compact_candidates(self) -> None:
        sensor_module = _load_sensor_module()
        button_module = _load_button_module()
        from custom_components.zero_net_export.entity import RECORDER_ATTRIBUTE_TARGET_BYTES

        coordinator = _coordinator()
        candidates = [
            {
                "entity_id": f"switch.pool_pump_{index}",
                "name": f"Pool pump {index}",
                "domain": "switch",
                "state": "off",
                "kind": "fixed",
                "debug_blob": "x" * 500,
            }
            for index in range(30)
        ]
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: candidates
        button_module.discover_candidate_devices = lambda states, managed_ids: candidates
        hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed Devices overview")
        overview.hass = hass
        attrs = overview.extra_state_attributes

        self.assertEqual(attrs["candidate_count"], 30)
        self.assertEqual(len(attrs["candidate_devices"]), 30)
        self.assertNotIn("debug_blob", attrs["candidate_devices"][0])
        self.assertLess(_attr_size(attrs), RECORDER_ATTRIBUTE_TARGET_BYTES)

        button = button_module.ZeroNetExportShowManagedDeviceReviewButton(coordinator)
        button.hass = hass
        button_attrs = button.extra_state_attributes

        self.assertEqual(button_attrs["unmanaged_candidate_count"], 30)
        self.assertNotIn("debug_blob", button_attrs["candidate_devices"][0])
        self.assertLess(_attr_size(button_attrs), RECORDER_ATTRIBUTE_TARGET_BYTES)


if __name__ == "__main__":
    unittest.main()
