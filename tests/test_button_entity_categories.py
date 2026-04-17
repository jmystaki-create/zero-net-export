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
ENTITY_PATH = PACKAGE_ROOT / "entity.py"
BUTTON_PATH = PACKAGE_ROOT / "button.py"


def _load_button_module(notification_calls: list[dict] | None = None):
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    homeassistant_pkg = sys.modules.setdefault("homeassistant", types.ModuleType("homeassistant"))
    homeassistant_pkg.__path__ = []

    components_pkg = sys.modules.setdefault("homeassistant.components", types.ModuleType("homeassistant.components"))
    components_pkg.__path__ = []
    homeassistant_pkg.components = components_pkg

    helpers_pkg = sys.modules.setdefault("homeassistant.helpers", types.ModuleType("homeassistant.helpers"))
    helpers_pkg.__path__ = []
    homeassistant_pkg.helpers = helpers_pkg

    persistent_notification_module = types.ModuleType("homeassistant.components.persistent_notification")
    if notification_calls is None:
        persistent_notification_module.async_create = lambda *args, **kwargs: None
    else:
        def _record_notification(*args, **kwargs):
            notification_calls.append({"args": args, "kwargs": kwargs})
        persistent_notification_module.async_create = _record_notification
    sys.modules[persistent_notification_module.__name__] = persistent_notification_module
    components_pkg.persistent_notification = persistent_notification_module

    button_component_module = types.ModuleType("homeassistant.components.button")
    button_component_module.ButtonEntity = type("ButtonEntity", (), {})
    sys.modules[button_component_module.__name__] = button_component_module
    components_pkg.button = button_component_module

    entity_helper_module = types.ModuleType("homeassistant.helpers.entity")
    entity_helper_module.EntityCategory = types.SimpleNamespace(DIAGNOSTIC="diagnostic")
    sys.modules[entity_helper_module.__name__] = entity_helper_module
    helpers_pkg.entity = entity_helper_module

    update_coordinator_module = types.ModuleType("homeassistant.helpers.update_coordinator")

    class CoordinatorEntity:
        def __init__(self, coordinator) -> None:
            self.coordinator = coordinator

    update_coordinator_module.CoordinatorEntity = CoordinatorEntity
    sys.modules[update_coordinator_module.__name__] = update_coordinator_module
    helpers_pkg.update_coordinator = update_coordinator_module

    const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", CONST_PATH)
    assert const_spec and const_spec.loader
    integration_const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = integration_const_module
    const_spec.loader.exec_module(integration_const_module)

    entity_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.entity", ENTITY_PATH)
    assert entity_spec and entity_spec.loader
    integration_entity_module = importlib.util.module_from_spec(entity_spec)
    sys.modules[entity_spec.name] = integration_entity_module
    entity_spec.loader.exec_module(integration_entity_module)

    native_support_module = types.ModuleType("custom_components.zero_net_export.native_support")
    native_support_module.DETAILED_MANAGEMENT_PATH = "detailed device path"
    native_support_module.DEVICES_CONFIGURE_PATH = "devices path"
    native_support_module.DEVICES_SECTION_LABEL = "Managed Devices"
    native_support_module.POLICY_CONFIGURE_PATH = "policy path"
    native_support_module.POLICY_SECTION_LABEL = "Controls"
    native_support_module.PRIMARY_CONFIGURE_PATH = "primary path"
    native_support_module.SOURCES_CONFIGURE_PATH = "sources path"
    native_support_module.SOURCES_SECTION_LABEL = "Sensors"
    native_support_module.SUPPORT_CONFIGURE_PATH = "support path"
    native_support_module.SUPPORT_SECTION_LABEL = "Diagnostics"
    native_support_module.build_native_command_center_summary = lambda coordinator: {
        "recommended_section": "Sensors",
        "recommended_path": "sources path",
        "recommended_reason": "Mapped source blockers remain.",
        "next_action_summary": "Review the next managed device.",
        "install_status": "install summary",
        "install_consistency": "install consistency",
        "source_status": "Sensors need review.",
        "source_mapping_summary": "Solar power -> sensor.pv_power",
        "unavailable_sources": "Solar power",
        "stale_sources": "None",
        "source_attention_roles": "Solar power -> sensor.pv_power (unavailable)",
        "device_status": "Managed fleet looks healthy.",
        "device_next_step": "Review the next managed device.",
        "policy_status": "Controls ready.",
        "policy_readiness": "Ready after source repair.",
        "support_status": "Diagnostics available.",
        "detailed_management_summary": "Use the device page for deeper per-device review.",
        "sources_path": "sources path",
        "devices_path": "devices path",
        "policy_path": "policy path",
        "support_path": "support path",
        "mode_path": "mode path",
    }
    native_support_module.build_native_command_center_guide_text = lambda command_center: (
        "Zero Net Export native command center guide\n\n"
        f"Recommended section right now: {command_center.get('recommended_section')}\n"
        f"Why this section is recommended: {command_center.get('recommended_reason')}\n"
        f"Managed-device deep review: {command_center.get('detailed_management_summary')}"
    )
    native_support_module.build_native_operator_readiness = lambda coordinator: {}
    native_support_module.build_native_support_center = lambda coordinator: "support center"
    native_support_module.build_native_support_snapshot = lambda coordinator: "support snapshot"
    sys.modules[native_support_module.__name__] = native_support_module

    candidate_utils_module = types.ModuleType("custom_components.zero_net_export.candidate_utils")

    def _discover_candidate_devices(states, managed_entity_ids):
        candidates = []
        for state in states:
            entity_id = getattr(state, "entity_id", "")
            if entity_id in managed_entity_ids:
                continue
            domain, _, _object_id = entity_id.partition(".")
            if domain not in {"switch", "number", "input_boolean"}:
                continue
            attributes = getattr(state, "attributes", {}) or {}
            candidates.append(
                {
                    "entity_id": entity_id,
                    "name": str(attributes.get("friendly_name") or entity_id),
                    "domain": domain,
                    "kind": "fixed" if domain in {"switch", "input_boolean"} else "variable",
                    "state": str(getattr(state, "state", "")),
                    "unit": str(attributes.get("unit_of_measurement") or ""),
                    "device_class": str(attributes.get("device_class") or ""),
                }
            )
        return sorted(candidates, key=lambda item: (0 if item["domain"] == "switch" else 1, item["name"]))

    def _assess_candidate(candidate):
        if candidate.get("domain") == "switch":
            return {
                "confidence": "high",
                "summary": "Switch entities are usually likely fixed-load candidates when they control a real appliance or relay.",
                "warnings": [],
            }
        return {
            "confidence": "medium",
            "summary": "Looks like a plausible controllable candidate, but review before promotion.",
            "warnings": ["Variable power controls need a meaningful unit, sane range, and clear relation to real device power."],
        }

    def _build_candidate_overview_summary(candidates, **kwargs):
        items = list(candidates)
        if not items:
            return "No unmanaged candidate devices discovered"
        parts = [f"{len(items)} {'candidate' if len(items) == 1 else 'candidates'}"]
        fixed_count = sum(1 for item in items if item["kind"] == "fixed")
        variable_count = sum(1 for item in items if item["kind"] == "variable")
        if fixed_count:
            parts.append(f"{fixed_count} fixed candidate" if fixed_count == 1 else f"{fixed_count} fixed candidates")
        if variable_count:
            parts.append(f"{variable_count} variable candidate" if variable_count == 1 else f"{variable_count} variable candidates")
        if items[0].get("name"):
            parts.append(f"top {items[0]['name']}")
        return " | ".join(parts)

    candidate_utils_module.discover_candidate_devices = _discover_candidate_devices
    candidate_utils_module.assess_candidate = _assess_candidate
    candidate_utils_module.build_candidate_overview_summary = _build_candidate_overview_summary
    candidate_utils_module.build_candidate_review_hint = lambda candidate, **kwargs: "likely useful"
    candidate_utils_module.build_candidate_preview = lambda candidate, include_entity_id=True, include_kind=True, include_state=False, **kwargs: (
        f"{candidate['name']} ("
        + ", ".join(
            bit
            for bit in [
                candidate["entity_id"] if include_entity_id else "",
                candidate["kind"] if include_kind else "",
                f"state {candidate['state']}" if include_state else "",
            ]
            if bit
        )
        + ") | "
        + ("likely useful" if candidate["domain"] == "switch" else "review first")
        + " | key warning: "
        + (
            "No immediate warnings"
            if candidate["domain"] == "switch"
            else "Variable power controls need a meaningful unit, sane range, and clear relation to real device power."
        )
    )
    sys.modules[candidate_utils_module.__name__] = candidate_utils_module

    button_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.button", BUTTON_PATH)
    assert button_spec and button_spec.loader
    button_module = importlib.util.module_from_spec(button_spec)
    sys.modules[button_spec.name] = button_module
    button_spec.loader.exec_module(button_module)
    return button_module


class ButtonEntityCategoryTests(unittest.TestCase):
    def test_workspace_handoff_returns_promotion_steps_when_managed_devices_is_the_active_section(self) -> None:
        button_module = _load_button_module()

        handoff = button_module._managed_devices_workspace_handoff(
            {
                "recommended_section": button_module.DEVICES_SECTION_LABEL,
                "recommended_path": "devices path",
                "recommended_reason": "Managed fleet work is the current priority.",
                "device_next_step": "Promote the next candidate.",
            },
            {"name": "Hot water", "entity_id": "switch.hot_water", "kind": "fixed", "domain": "switch"},
        )

        self.assertEqual(handoff[0], "Promotion handoff:")
        self.assertIn("- Open devices path as the primary Managed Devices workspace.", handoff)
        self.assertIn("- Choose Add fixed load device.", handoff)
        self.assertIn("- In Pick unmanaged candidate, select Hot water (fixed) | likely useful | key warning: No immediate warnings.", handoff)
        self.assertIn("- Use detailed device path afterward only if you need deeper per-device review.", handoff)

    def test_primary_operator_buttons_stay_out_of_diagnostics(self) -> None:
        button_module = _load_button_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=None,
        )

        command_center = button_module.ZeroNetExportShowNativeCommandCenterButton(coordinator)
        fleet_console = button_module.ZeroNetExportShowFleetConsoleButton(coordinator)
        managed_review = button_module.ZeroNetExportShowManagedDeviceReviewButton(coordinator)
        diagnostics = button_module.ZeroNetExportShowNativeDiagnosticsButton(coordinator)

        self.assertIsNone(getattr(command_center, "_attr_entity_category", None))
        self.assertIsNone(getattr(fleet_console, "_attr_entity_category", None))
        self.assertIsNone(getattr(managed_review, "_attr_entity_category", None))
        self.assertEqual(diagnostics._attr_entity_category, button_module.EntityCategory.DIAGNOSTIC)

    def test_diagnostics_buttons_use_diagnostics_first_labels(self) -> None:
        button_module = _load_button_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=None,
        )

        support = button_module.ZeroNetExportShowNativeSupportCenterButton(coordinator)
        diagnostics = button_module.ZeroNetExportShowNativeDiagnosticsButton(coordinator)

        self.assertEqual(getattr(support, "_attr_name", None), "Review diagnostics")
        self.assertEqual(getattr(diagnostics, "_attr_name", None), "Review diagnostics snapshot")

    def test_fleet_console_button_renders_managed_vs_unmanaged_workspace(self) -> None:
        notification_calls: list[dict] = []
        button_module = _load_button_module(notification_calls)
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "entity_id": "switch.pool_pump",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "status": "Ready for control",
                        "guard_status": "ready",
                        "planned_action": "turn_on",
                    },
                    "ev": {
                        "name": "EV charger",
                        "entity_id": "number.ev_limit",
                        "usable": False,
                        "enabled": True,
                        "effective_enabled": False,
                        "status": "Held by guard",
                        "guard_status": "blocked",
                        "planned_action": "hold",
                    },
                }
            ),
        )
        button = button_module.ZeroNetExportShowFleetConsoleButton(coordinator)
        self.assertEqual(button._attr_name, "Review managed devices workspace")
        button.hass = SimpleNamespace(
            states=SimpleNamespace(
                async_all=lambda: [
                    SimpleNamespace(
                        entity_id="switch.pool_pump",
                        state="off",
                        attributes={"friendly_name": "Pool pump"},
                    ),
                    SimpleNamespace(
                        entity_id="switch.hot_water",
                        state="off",
                        attributes={"friendly_name": "Hot water"},
                    ),
                    SimpleNamespace(
                        entity_id="input_boolean.helper_candidate",
                        state="on",
                        attributes={"friendly_name": "Helper candidate"},
                    ),
                ]
            )
        )

        import asyncio
        asyncio.run(button.async_press())

        self.assertEqual(len(notification_calls), 1)
        self.assertEqual(notification_calls[0]["kwargs"]["title"], "Test Entry: managed devices workspace")
        message = notification_calls[0]["args"][1]
        self.assertIn("Zero Net Export managed devices workspace", message)
        self.assertIn("Workspace path: devices path", message)
        self.assertIn("Detailed review path: detailed device path", message)
        self.assertIn("Before fleet work:", message)
        self.assertLess(message.index("Before fleet work:"), message.index("Managed devices (top section):"))
        self.assertIn("Managed devices (top section):", message)
        self.assertIn("- Snapshot: 2 managed | 1 enabled | 1 usable | blocked EV charger | plan Pool pump", message)
        self.assertIn("Unmanaged candidates (bottom section):", message)
        self.assertIn("- Snapshot: 2 candidates | 2 fixed candidates | top Hot water | likely useful | key warning: No immediate warnings", message)
        self.assertIn("Top candidate usefulness: likely useful: Switch entities are usually likely fixed-load candidates when they control a real appliance or relay.", message)
        blocked_line = "- EV charger: unknown | Held by guard | not usable | disabled | power n/a | guard blocked | action hold"
        planned_line = "- Pool pump: unknown | Ready for control | usable | enabled | power n/a | guard ready | action turn_on"
        self.assertIn(blocked_line, message)
        self.assertIn(planned_line, message)
        self.assertLess(message.index(blocked_line), message.index(planned_line))
        self.assertNotIn("entity=number.ev_limit", message)
        self.assertNotIn("entity=switch.pool_pump", message)
        self.assertIn("- Hot water (fixed, state off) | likely useful | key warning: No immediate warnings", message)
        self.assertIn("Return after blocker repair:", message)
        self.assertIn("- Open sources path first.", message)
        self.assertIn("- Why: Mapped source blockers remain.", message)
        self.assertIn("- Next fleet step after repair: Review the next managed device.", message)
        self.assertIn("- Then reopen devices path for Managed Devices.", message)
        self.assertIn("- Use detailed device path only for deeper per-device review after the main fleet step is clear.", message)

    def test_managed_device_review_button_renders_runtime_fleet_summary(self) -> None:
        notification_calls: list[dict] = []
        button_module = _load_button_module(notification_calls)
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "entity_id": "switch.pool_pump",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "status": "Ready for control",
                        "guard_status": "ready",
                        "planned_action": "turn_on",
                    },
                    "ev": {
                        "name": "EV charger",
                        "entity_id": "number.ev_limit",
                        "usable": False,
                        "enabled": True,
                        "effective_enabled": False,
                        "status": "Held by guard",
                        "guard_status": "blocked",
                        "planned_action": "hold",
                    },
                }
            ),
        )
        button = button_module.ZeroNetExportShowManagedDeviceReviewButton(coordinator)
        self.assertEqual(button._attr_name, "Review managed devices")
        button.hass = SimpleNamespace(
            states=SimpleNamespace(
                async_all=lambda: [
                    SimpleNamespace(
                        entity_id="switch.pool_pump",
                        state="off",
                        attributes={"friendly_name": "Pool pump"},
                    ),
                    SimpleNamespace(
                        entity_id="switch.hot_water",
                        state="off",
                        attributes={"friendly_name": "Hot water"},
                    ),
                    SimpleNamespace(
                        entity_id="input_boolean.helper_candidate",
                        state="on",
                        attributes={"friendly_name": "Helper candidate"},
                    ),
                ]
            )
        )

        import asyncio
        asyncio.run(button.async_press())

        self.assertEqual(len(notification_calls), 1)
        message = notification_calls[0]["args"][1]
        self.assertIn("Zero Net Export managed devices review", message)
        self.assertIn("Managed devices (top section):", message)
        self.assertIn("- Snapshot: 2 managed | 1 enabled | 1 usable | blocked EV charger | 1 planned action(s) | plan Pool pump", message)
        self.assertIn("Unmanaged candidates (bottom section): 2 candidates | 2 fixed candidates | top Hot water | likely useful | key warning: No immediate warnings", message)
        self.assertIn("Top candidate usefulness: likely useful: Switch entities are usually likely fixed-load candidates when they control a real appliance or relay.", message)
        self.assertIn("Top candidate warnings: No immediate warnings.", message)
        blocked_line = "- EV charger: unknown | Held by guard | not usable | disabled | power n/a | guard blocked | action hold"
        planned_line = "- Pool pump: unknown | Ready for control | usable | enabled | power n/a | guard ready | action turn_on"
        self.assertIn(blocked_line, message)
        self.assertIn(planned_line, message)
        self.assertLess(message.index(blocked_line), message.index(planned_line))
        self.assertNotIn("entity=number.ev_limit", message)
        self.assertNotIn("entity=switch.pool_pump", message)
        self.assertIn("Top unmanaged candidates:", message)
        self.assertIn("- Hot water (fixed, state off)", message)
        self.assertIn("Detailed device-view path: detailed device path", message)
        self.assertIn("Before fleet work:", message)
        self.assertLess(message.index("Before fleet work:"), message.index("Managed devices (top section):"))
        self.assertIn("Return after blocker repair:", message)
        self.assertIn("- Open sources path first.", message)
        self.assertIn("- Why: Mapped source blockers remain.", message)
        self.assertIn("- Then reopen devices path for Managed Devices.", message)
        self.assertIn("- Use detailed device path only for deeper per-device review after the main fleet step is clear.", message)

    def test_managed_device_review_button_exposes_unmanaged_candidate_attributes(self) -> None:
        button_module = _load_button_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "entity_id": "switch.pool_pump",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "status": "Ready for control",
                        "guard_status": "ready",
                        "planned_action": "turn_on",
                    }
                }
            ),
        )
        button = button_module.ZeroNetExportShowManagedDeviceReviewButton(coordinator)
        button.hass = SimpleNamespace(
            states=SimpleNamespace(
                async_all=lambda: [
                    SimpleNamespace(
                        entity_id="switch.pool_pump",
                        state="off",
                        attributes={"friendly_name": "Pool pump"},
                    ),
                    SimpleNamespace(
                        entity_id="number.ev_limit",
                        state="16",
                        attributes={"friendly_name": "EV limit"},
                    ),
                ]
            )
        )

        attrs = button.extra_state_attributes

        self.assertEqual(attrs["managed_count"], 1)
        self.assertEqual(attrs["managed_snapshot"], "1 managed | 1 enabled | 1 usable | 1 planned action(s) | plan Pool pump")
        self.assertEqual(attrs["unmanaged_snapshot"], "1 candidate | 1 variable candidate | top EV limit | review first | key warning: Variable power controls need a meaningful unit, sane range, and clear relation to real device power.")
        self.assertEqual(attrs["first_blocked_device"], "")
        self.assertEqual(attrs["first_planned_device"], "Pool pump")
        self.assertEqual(attrs["recommended_section"], "Sensors")
        self.assertEqual(attrs["recommended_path"], "sources path")
        self.assertEqual(attrs["recommended_reason"], "Mapped source blockers remain.")
        self.assertIn("Before fleet work:", attrs["blocker_first"])
        self.assertEqual(attrs["unmanaged_candidate_count"], 1)
        self.assertEqual(attrs["top_unmanaged_candidate"]["entity_id"], "number.ev_limit")
        self.assertEqual(attrs["top_candidate_fit"]["confidence"], "medium")
        self.assertTrue(any("meaningful unit" in warning for warning in attrs["top_candidate_fit"]["warnings"]))
        self.assertEqual(attrs["candidate_devices"][0]["name"], "EV limit")
        self.assertIn("Return after blocker repair:", attrs["promotion_handoff"])
        self.assertIn("- Open sources path first.", attrs["promotion_handoff"])

    def test_fleet_console_attributes_gate_promotion_handoff_behind_blocker_repair(self) -> None:
        button_module = _load_button_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "entity_id": "switch.pool_pump",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "status": "Ready for control",
                        "guard_status": "ready",
                        "planned_action": "turn_on",
                    }
                }
            ),
        )
        button = button_module.ZeroNetExportShowFleetConsoleButton(coordinator)
        button.hass = SimpleNamespace(
            states=SimpleNamespace(
                async_all=lambda: [
                    SimpleNamespace(
                        entity_id="switch.pool_pump",
                        state="off",
                        attributes={"friendly_name": "Pool pump"},
                    ),
                    SimpleNamespace(
                        entity_id="switch.hot_water",
                        state="off",
                        attributes={"friendly_name": "Hot water"},
                    ),
                ]
            )
        )

        attrs = button.extra_state_attributes

        self.assertEqual(attrs["recommended_section"], "Sensors")
        self.assertEqual(attrs["managed_snapshot"], "1 managed | 1 enabled | 1 usable | plan Pool pump")
        self.assertEqual(attrs["unmanaged_snapshot"], "1 candidate | 1 fixed candidate | top Hot water | likely useful | key warning: No immediate warnings")
        self.assertEqual(attrs["first_blocked_device"], "")
        self.assertEqual(attrs["first_planned_device"], "Pool pump")
        self.assertIn("Before fleet work:", attrs["blocker_first"])
        self.assertIn("Return after blocker repair:", attrs["promotion_handoff"])
        self.assertIn("- Open sources path first.", attrs["promotion_handoff"])
        self.assertIn("- Why: Mapped source blockers remain.", attrs["promotion_handoff"])

    def test_empty_planned_action_does_not_create_a_fake_active_plan_snapshot(self) -> None:
        button_module = _load_button_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "entity_id": "switch.pool_pump",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "status": "Ready for control",
                        "guard_status": "ready",
                        "planned_action": "",
                    }
                }
            ),
        )

        fleet_button = button_module.ZeroNetExportShowFleetConsoleButton(coordinator)
        review_button = button_module.ZeroNetExportShowManagedDeviceReviewButton(coordinator)
        fleet_button.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))
        review_button.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        fleet_attrs = fleet_button.extra_state_attributes
        review_attrs = review_button.extra_state_attributes

        self.assertEqual(fleet_attrs["managed_snapshot"], "1 managed | 1 enabled | 1 usable")
        self.assertEqual(fleet_attrs["first_planned_device"], "")
        self.assertEqual(review_attrs["managed_snapshot"], "1 managed | 1 enabled | 1 usable | 0 planned action(s)")
        self.assertEqual(review_attrs["planned_action_count"], 0)
        self.assertEqual(review_attrs["first_planned_device"], "")

    def test_managed_device_review_line_carries_kind_priority_and_power_context(self) -> None:
        button_module = _load_button_module()

        line = button_module._format_device_review_line(
            {
                "name": "EV charger",
                "entity_id": "number.ev_limit",
                "kind": "variable",
                "status": "Tracking export",
                "usable": True,
                "enabled": True,
                "effective_enabled": True,
                "priority": 40,
                "operator_priority_override": 55,
                "operator_enabled_override": False,
                "current_power_w": 1800,
                "current_target_power_w": 2200,
                "guard_status": "ready",
                "planned_action": "set_power",
                "last_action_status": "throttled",
            }
        )

        self.assertEqual(
            line,
            "- EV charger: variable | Tracking export | usable | enabled | priority 40 | priority override 55 | enabled override off | power 1800 W | target 2200 W | guard ready | action set_power | last throttled",
        )

    def test_managed_device_detail_button_renders_per_device_review(self) -> None:
        notification_calls: list[dict] = []
        button_module = _load_button_module(notification_calls)
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "entity_id": "switch.pool_pump",
                        "kind": "fixed",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "status": "Ready for control",
                        "reason": "Export is above target and this load can absorb it.",
                        "guard_status": "ready",
                        "planned_action": "turn_on",
                        "planned_action_reason": "Use the pump to absorb export.",
                        "planned_power_delta_w": 1200,
                        "nominal_power_w": 1200,
                        "min_power_w": 1200,
                        "max_power_w": 1200,
                        "step_w": 1200,
                        "current_power_w": 0,
                        "current_target_power_w": None,
                        "priority": 90,
                        "cooldown_seconds": 300,
                        "min_on_seconds": 900,
                        "min_off_seconds": 600,
                        "max_active_seconds": 7200,
                        "operator_enabled_override": None,
                        "operator_priority_override": 75,
                        "last_action_status": "applied",
                        "last_action_result_message": "Turned on successfully.",
                        "last_requested_power_w": 1200,
                        "last_applied_power_w": 1200,
                        "successful_action_count": 4,
                        "failed_action_count": 1,
                    }
                }
            ),
        )
        button = button_module.ZeroNetExportShowManagedDeviceDetailButton(coordinator, "pool", "Pool pump")
        button.hass = SimpleNamespace(
            states=SimpleNamespace(
                async_all=lambda: [
                    SimpleNamespace(
                        entity_id="switch.hot_water",
                        state="off",
                        attributes={"friendly_name": "Hot water"},
                    )
                ]
            )
        )

        import asyncio
        asyncio.run(button.async_press())

        self.assertEqual(button._attr_name, "Review Pool pump")
        self.assertEqual(len(notification_calls), 1)
        message = notification_calls[0]["args"][1]
        self.assertIn("Zero Net Export managed-device detail review", message)
        self.assertIn("Managed Devices path: devices path", message)
        self.assertIn("Recommended next step: Review the next managed device.", message)
        self.assertIn("Before fleet work:", message)
        self.assertIn("Managed devices workspace context:", message)
        self.assertIn("- Managed snapshot: 1 managed | 1 enabled | 1 usable | 1 fixed managed | 1200 W nominal | 1 planned action(s) | plan Pool pump", message)
        self.assertIn("- Unmanaged snapshot: 1 candidate | 1 fixed candidate | top Hot water | likely useful | key warning: No immediate warnings", message)
        self.assertIn("- Top unmanaged candidate right now: Hot water (fixed) | likely useful | key warning: No immediate warnings", message)
        self.assertIn("Device: Pool pump", message)
        self.assertNotIn("Entity: switch.pool_pump", message)
        self.assertNotIn("Use switch.pool_pump sensors", message)
        self.assertNotIn("entity=switch.pool_pump", message)
        self.assertIn("Use this device's sensors on the Zero Net Export device page", message)
        self.assertIn("Guard state: ready", message)
        self.assertIn("Planned action: turn_on", message)
        self.assertIn("- Priority: 90", message)
        self.assertIn("- Planned power delta: 1200 W", message)
        self.assertNotIn("- Variable range:", message)
        self.assertNotIn("- Step size:", message)
        self.assertNotIn("- Requested target power:", message)
        self.assertIn("- Priority override: forcing 75", message)
        self.assertIn("- Enabled override: none", message)
        self.assertIn("- Last action result: Turned on successfully.", message)
        self.assertIn("Return to devices path as the primary Managed Devices workspace for edits, enablement, promotion, or removal.", message)

    def test_managed_device_detail_button_exposes_workspace_context_attributes(self) -> None:
        button_module = _load_button_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "entity_id": "switch.pool_pump",
                        "kind": "fixed",
                        "usable": False,
                        "enabled": True,
                        "effective_enabled": True,
                        "status": "Blocked",
                        "guard_status": "source blocked",
                        "planned_action": "hold",
                    }
                }
            ),
        )
        button = button_module.ZeroNetExportShowManagedDeviceDetailButton(coordinator, "pool", "Pool pump")
        button.hass = SimpleNamespace(
            states=SimpleNamespace(
                async_all=lambda: [
                    SimpleNamespace(
                        entity_id="switch.hot_water",
                        state="off",
                        attributes={"friendly_name": "Hot water"},
                    )
                ]
            )
        )

        attrs = button.extra_state_attributes

        self.assertEqual(attrs["recommended_section"], "Sensors")
        self.assertEqual(attrs["recommended_path"], "sources path")
        self.assertEqual(attrs["recommended_reason"], "Mapped source blockers remain.")
        self.assertIn("Before fleet work:", attrs["blocker_first"])
        self.assertEqual(attrs["managed_snapshot"], "1 managed | 1 enabled | 0 usable | 1 fixed managed | 0 W nominal | blocked Pool pump | 0 planned action(s)")
        self.assertEqual(attrs["unmanaged_snapshot"], "1 candidate | 1 fixed candidate | top Hot water | likely useful | key warning: No immediate warnings")
        self.assertEqual(attrs["top_unmanaged_candidate"]["entity_id"], "switch.hot_water")

    def test_command_center_guide_button_uses_shared_full_guide_text(self) -> None:
        notification_calls: list[dict] = []
        button_module = _load_button_module(notification_calls)
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=None,
        )
        button = button_module.ZeroNetExportShowNativeCommandCenterButton(coordinator)
        button.hass = SimpleNamespace()

        import asyncio
        asyncio.run(button.async_press())

        self.assertEqual(len(notification_calls), 1)
        message = notification_calls[0]["args"][1]
        self.assertIn("Zero Net Export native command center guide", message)
        self.assertIn("Recommended section right now: Sensors", message)
        self.assertIn("Why this section is recommended: Mapped source blockers remain.", message)
        self.assertIn("Managed-device deep review: Use the device page for deeper per-device review.", message)


if __name__ == "__main__":
    unittest.main()
