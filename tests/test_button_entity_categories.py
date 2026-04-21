from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from datetime import datetime, timezone
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

    device_model_path = PACKAGE_ROOT / "device_model.py"
    device_model_spec = importlib.util.spec_from_file_location(
        "custom_components.zero_net_export.device_model",
        device_model_path,
    )
    assert device_model_spec and device_model_spec.loader
    device_model_module = importlib.util.module_from_spec(device_model_spec)
    sys.modules[device_model_spec.name] = device_model_module
    device_model_spec.loader.exec_module(device_model_module)

    native_support_module = types.ModuleType("custom_components.zero_net_export.native_support")
    native_support_module.DETAILED_MANAGEMENT_PATH = "detailed device path"
    native_support_module.DIAGNOSTICS_DEVICE_ACTIONS_PATH = "device path -> Review diagnostics / Show setup checklist / Review diagnostics snapshot"
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
            parts.append(f"surfaced {items[0]['name']}")
        return " | ".join(parts)

    candidate_utils_module.discover_candidate_devices = _discover_candidate_devices
    candidate_utils_module.assess_candidate = _assess_candidate
    candidate_utils_module.candidate_needs_review = lambda fit: str((fit or {}).get("confidence") or "medium") != "high"
    candidate_utils_module.first_review_candidate = lambda candidates: next(
        (
            candidate
            for candidate in candidates
            if str((_assess_candidate(candidate) or {}).get("confidence") or "medium") != "high"
        ),
        next(iter(candidates), None),
    )
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
            [{"name": "Hot water", "entity_id": "switch.hot_water", "kind": "fixed", "domain": "switch"}],
            has_managed_devices=False,
        )

        self.assertEqual(handoff[0], "Promotion handoff:")
        self.assertIn("- Open devices path in Configure for the primary Managed Devices workspace.", handoff)
        self.assertIn("- Open Promotion shortlist for fixed-load candidates.", handoff)
        self.assertIn("- In Promotion shortlist, select Hot water (fixed) | likely useful | key warning: No immediate warnings.", handoff)
        self.assertIn("- Use detailed device path afterward only if you need deeper per-device review.", handoff)
        self.assertNotIn("Choose Promote fixed-load candidate", "\n".join(handoff))

    def test_workspace_handoff_prefers_first_review_candidate_over_top_rank(self) -> None:
        button_module = _load_button_module()

        handoff = button_module._managed_devices_workspace_handoff(
            {
                "recommended_section": button_module.DEVICES_SECTION_LABEL,
                "recommended_path": "devices path",
                "recommended_reason": "Managed fleet work is the current priority.",
                "device_next_step": "Promote the next candidate.",
            },
            [
                {"name": "Dishwasher Power", "entity_id": "switch.dishwasher_power", "kind": "fixed", "domain": "switch"},
                {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed", "domain": "input_boolean"},
            ],
            has_managed_devices=False,
        )

        self.assertIn("- Open Promotion shortlist for fixed-load candidates.", handoff)
        self.assertIn(
            "- In Promotion shortlist, select Virtual load (fixed) | review first | key warning: Variable power controls need a meaningful unit, sane range, and clear relation to real device power..",
            handoff,
        )
        self.assertNotIn("Choose Promote fixed-load candidate", "\n".join(handoff))
        self.assertIn(
            "- Then promote next from the unmanaged section: Dishwasher Power (fixed) | likely useful | key warning: No immediate warnings.",
            handoff,
        )
        self.assertFalse(any("Dishwasher Power" in line for line in handoff if "In Promotion shortlist" in line))

    def test_workspace_handoff_uses_variable_shortlist_wording_for_variable_candidates(self) -> None:
        button_module = _load_button_module()

        handoff = button_module._managed_devices_workspace_handoff(
            {
                "recommended_section": button_module.DEVICES_SECTION_LABEL,
                "recommended_path": "devices path",
                "recommended_reason": "Managed fleet work is the current priority.",
                "device_next_step": "Promote the next candidate.",
            },
            [{"name": "EV Charger", "entity_id": "number.ev_charger", "kind": "variable", "domain": "number"}],
            has_managed_devices=False,
        )

        self.assertIn("- Open Promotion shortlist for variable-load candidates.", handoff)
        self.assertNotIn("Choose Promote variable-load candidate", "\n".join(handoff))

    def test_workspace_handoff_keeps_empty_fleet_on_managed_devices_when_no_candidate_is_surfaced(self) -> None:
        button_module = _load_button_module()

        handoff = button_module._managed_devices_workspace_handoff(
            {
                "recommended_section": button_module.DEVICES_SECTION_LABEL,
                "recommended_path": "devices path",
                "recommended_reason": "Managed fleet work is the current priority.",
                "device_next_step": "Open devices path and check for the next unmanaged promotion candidate.",
            },
            [],
            has_managed_devices=False,
        )

        self.assertEqual(handoff[0], "Promotion handoff:")
        self.assertIn("- Open devices path in Configure for the primary Managed Devices workspace.", handoff)
        self.assertIn(
            "- Review the Managed Devices workspace first, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available.",
            handoff,
        )
        self.assertNotIn("ready yet", "\n".join(handoff))
        self.assertNotIn("tune controller behaviour", "\n".join(handoff))

    def test_workspace_handoff_keeps_existing_fleet_review_in_managed_devices_when_no_candidate_is_surfaced(self) -> None:
        button_module = _load_button_module()

        handoff = button_module._managed_devices_workspace_handoff(
            {
                "recommended_section": button_module.DEVICES_SECTION_LABEL,
                "recommended_path": "devices path",
                "recommended_reason": "Managed fleet work is the current priority.",
                "device_next_step": "Open devices path and review the current managed fleet.",
            },
            [],
            has_managed_devices=True,
        )

        self.assertEqual(handoff[0], "Promotion handoff:")
        self.assertIn("- Reopen devices path in Configure for the primary Managed Devices workspace.", handoff)
        self.assertIn(
            "- Use the Managed Devices workspace to edit device settings or stage enablement changes before changing controls or deeper diagnostics.",
            handoff,
        )
        self.assertNotIn("tune controller behaviour", "\n".join(handoff))

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
        self.assertIn("Primary Managed Devices workspace in Configure: devices path", message)
        self.assertIn("Secondary device-page review path: detailed device path", message)
        self.assertIn(
            "Device-page boundary: Make promotion, enablement, removal, and other fleet edits in devices path; use the device page only for secondary review and handoff.",
            message,
        )
        self.assertIn("Before fleet work:", message)
        self.assertLess(message.index("Before fleet work:"), message.index("Managed devices (top section):"))
        self.assertIn("Managed devices (top section):", message)
        self.assertIn("- Snapshot: 2 managed | 1 enabled | 1 usable | 2 managed devices need attention | attention first EV charger | blocked EV charger | plan Pool pump", message)
        self.assertIn("Managed devices needing attention first:", message)
        self.assertIn("Other managed devices:", message)
        self.assertIn("Unmanaged candidates (bottom section):", message)
        self.assertIn("- Snapshot: 2 candidates | 2 fixed candidates | surfaced Hot water | likely useful | key warning: No immediate warnings", message)
        self.assertIn("Currently surfaced candidate usefulness: likely useful: Switch entities are usually likely fixed-load candidates when they control a real appliance or relay.", message)
        self.assertIn(
            "- First review-first candidate: Helper candidate (fixed) | review first | key warning: Variable power controls need a meaningful unit, sane range, and clear relation to real device power.",
            message,
        )
        self.assertIn(
            "- First review-first candidate usefulness: review first: Looks like a plausible controllable candidate, but review before promotion.",
            message,
        )
        self.assertIn(
            "- Another ready unmanaged candidate: Hot water (fixed) | likely useful | key warning: No immediate warnings",
            message,
        )
        self.assertIn(
            "- Another ready unmanaged usefulness: likely useful: Switch entities are usually likely fixed-load candidates when they control a real appliance or relay.",
            message,
        )
        self.assertIn("- Another ready unmanaged warnings: No immediate warnings.", message)
        blocked_line = "- EV charger: unknown | Held by guard | not usable | disabled | power n/a | guard blocked | action hold"
        planned_line = "- Pool pump: unknown | Ready for control | usable | enabled | power n/a | guard ready | action turn_on"
        self.assertIn(blocked_line, message)
        self.assertIn(planned_line, message)
        self.assertIn("- No additional steady managed devices right now.", message)
        self.assertLess(message.index("Managed devices needing attention first:"), message.index(blocked_line))
        self.assertLess(message.index(blocked_line), message.index(planned_line))
        self.assertLess(message.index(planned_line), message.index("Other managed devices:"))
        self.assertNotIn("entity=number.ev_limit", message)
        self.assertNotIn("entity=switch.pool_pump", message)
        self.assertIn("Currently surfaced unmanaged candidates:", message)
        self.assertIn("- Hot water (fixed) | likely useful | key warning: No immediate warnings", message)
        self.assertIn("Return after blocker repair:", message)
        self.assertIn("- Open sources path first.", message)
        self.assertIn("- Why: Mapped source blockers remain.", message)
        self.assertIn("- Next fleet step after repair: Review the next managed device.", message)
        self.assertIn("- Then reopen devices path for Managed Devices.", message)
        self.assertIn("- Use detailed device path only for deeper per-device review after the main fleet step is clear.", message)
        self.assertIn(
            "- Make promotion, enablement, removal, and other fleet edits in devices path; use the device page only for secondary review and handoff.",
            message,
        )

    def test_candidate_discovery_cache_is_shared_across_button_surfaces_for_same_state(self) -> None:
        button_module = _load_button_module()
        discover_calls: list[tuple[str, ...]] = []
        original_discover = button_module.discover_candidate_devices

        def _counting_discover(states, managed_entity_ids):
            discover_calls.append(tuple(sorted(managed_entity_ids)))
            return original_discover(states, managed_entity_ids)

        button_module.discover_candidate_devices = _counting_discover
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
        hass = SimpleNamespace(
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

        fleet_button = button_module.ZeroNetExportShowFleetConsoleButton(coordinator)
        fleet_button.hass = hass
        review_button = button_module.ZeroNetExportShowManagedDeviceReviewButton(coordinator)
        review_button.hass = hass
        detail_button = button_module.ZeroNetExportShowManagedDeviceDetailButton(coordinator, "pool", "Pool pump")
        detail_button.hass = hass

        self.assertEqual(fleet_button.extra_state_attributes["candidate_count"], 2)
        self.assertEqual(review_button.extra_state_attributes["unmanaged_candidate_count"], 2)
        self.assertEqual(detail_button.extra_state_attributes["top_unmanaged_candidate"]["name"], "Hot water")
        self.assertEqual(discover_calls, [("number.ev_limit", "switch.pool_pump")])

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
                        "nominal_power_w": 1200,
                        "observed_active": True,
                        "current_power_w": 1180,
                        "current_active_seconds": 930,
                        "active_runtime_today_seconds": 4520,
                        "last_requested_power_w": 1200,
                        "last_applied_power_w": 1200,
                        "successful_action_count": 4,
                        "failed_action_count": 1,
                        "last_action_seconds_ago": 125,
                        "last_applied_at": datetime(2026, 4, 18, 8, 31, tzinfo=timezone.utc),
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
                        "last_action_status": "guard_blocked",
                        "last_action_result_message": "Battery reserve blocked the last run.",
                        "last_action_seconds_ago": 180,
                        "last_applied_at": datetime(2026, 4, 18, 8, 29, tzinfo=timezone.utc),
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
        self.assertEqual(notification_calls[0]["kwargs"]["title"], "Test Entry: managed devices review")
        message = notification_calls[0]["args"][1]
        self.assertIn("Zero Net Export managed devices review", message)
        self.assertIn("Managed devices (top section):", message)
        self.assertIn("- Snapshot: 2 managed | 1 enabled | 1 usable | active load 1180 W | 1 active managed device | active device Pool pump (action turn_on) | 2 managed devices need attention | attention first EV charger | blocked EV charger | 1 planned action(s) | plan Pool pump", message)
        self.assertIn("Unmanaged candidates (bottom section): 2 candidates | 2 fixed candidates | surfaced Hot water | likely useful | key warning: No immediate warnings", message)
        self.assertIn("Currently surfaced candidate usefulness: likely useful: Switch entities are usually likely fixed-load candidates when they control a real appliance or relay.", message)
        self.assertIn("Currently surfaced candidate warnings: No immediate warnings.", message)
        self.assertIn(
            "First review-first candidate: Helper candidate (fixed) | review first | key warning: Variable power controls need a meaningful unit, sane range, and clear relation to real device power.",
            message,
        )
        self.assertIn(
            "First review-first candidate usefulness: review first: Looks like a plausible controllable candidate, but review before promotion.",
            message,
        )
        self.assertIn(
            "Another ready unmanaged candidate: Hot water (fixed) | likely useful | key warning: No immediate warnings",
            message,
        )
        self.assertIn(
            "Another ready unmanaged usefulness: likely useful: Switch entities are usually likely fixed-load candidates when they control a real appliance or relay.",
            message,
        )
        self.assertIn("Another ready unmanaged warnings: No immediate warnings.", message)
        self.assertIn("Managed devices needing attention first:", message)
        self.assertIn("Other managed devices:", message)
        blocked_line = "- EV charger: unknown | Held by guard | not usable | disabled | power n/a | guard blocked | action hold | last guard_blocked | result Battery reserve blocked the last run | last act 3m ago | last applied at 2026-04-18T08:29:00Z"
        planned_line = "- Pool pump: unknown | Ready for control | usable | enabled | power 1180 W | nominal 1200 W | runtime 15m 30s | today 1h 15m | guard ready | action turn_on | last req 1200 W | last applied 1200 W | runs 4 ok/1 fail | last act 2m 5s ago | last applied at 2026-04-18T08:31:00Z"
        self.assertIn(blocked_line, message)
        self.assertIn(planned_line, message)
        self.assertLess(message.index("Managed devices needing attention first:"), message.index(blocked_line))
        self.assertLess(message.index(blocked_line), message.index(planned_line))
        self.assertNotIn("entity=number.ev_limit", message)
        self.assertNotIn("entity=switch.pool_pump", message)
        self.assertIn("Currently surfaced unmanaged candidates:", message)
        self.assertIn("- Hot water (fixed) | likely useful | key warning: No immediate warnings", message)
        self.assertIn("Secondary device-page audit path: detailed device path", message)
        self.assertIn(
            "Device-page boundary: Make promotion, enablement, removal, and other fleet edits in devices path; use the device page only for secondary review and handoff.",
            message,
        )
        self.assertIn("Use the per-device Review buttons on the Zero Net Export device page when you need a deeper audit trail for one managed device.", message)
        self.assertIn("Before fleet work:", message)
        self.assertLess(message.index("Before fleet work:"), message.index("Managed devices (top section):"))
        self.assertIn("Return after blocker repair:", message)
        self.assertIn("- Open sources path first.", message)
        self.assertIn("- Why: Mapped source blockers remain.", message)
        self.assertIn("- Then reopen devices path for Managed Devices.", message)
        self.assertIn("- Use detailed device path only for deeper per-device review after the main fleet step is clear.", message)
        self.assertIn(
            "- Make promotion, enablement, removal, and other fleet edits in devices path; use the device page only for secondary review and handoff.",
            message,
        )

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
                        "observed_active": True,
                        "current_power_w": 1180,
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
        self.assertEqual(attrs["managed_snapshot"], "1 managed | 1 enabled | 1 usable | active load 1180 W | 1 active managed device | active device Pool pump (action turn_on) | 1 managed device needs attention | attention first Pool pump | 1 planned action(s) | plan Pool pump")
        self.assertEqual(attrs["unmanaged_snapshot"], "1 candidate | 1 variable candidate | 1 needs review | 1 variable review | review EV limit | review first | key warning: Variable power controls need a meaningful unit, sane range, and clear relation to real device power.")
        self.assertEqual(attrs["attention_count"], 1)
        self.assertEqual(attrs["first_attention_device"], "Pool pump")
        self.assertEqual(attrs["first_blocked_device"], "")
        self.assertEqual(attrs["first_planned_device"], "Pool pump")
        self.assertEqual(attrs["recommended_section"], "Sensors")
        self.assertEqual(attrs["recommended_path"], "sources path")
        self.assertEqual(attrs["recommended_reason"], "Mapped source blockers remain.")
        self.assertIn("Before fleet work:", attrs["blocker_first"])
        self.assertEqual(
            attrs["workspace_boundary"],
            "Make promotion, enablement, removal, and other fleet edits in devices path; use the device page only for secondary review and handoff.",
        )
        self.assertEqual(attrs["unmanaged_candidate_count"], 1)
        self.assertEqual(attrs["top_unmanaged_candidate"]["entity_id"], "number.ev_limit")
        self.assertEqual(attrs["top_candidate_fit"]["confidence"], "medium")
        self.assertEqual(attrs["first_review_candidate"]["entity_id"], "number.ev_limit")
        self.assertEqual(attrs["first_review_candidate_fit"]["confidence"], "medium")
        self.assertIsNone(attrs["ready_next_candidate"])
        self.assertIsNone(attrs["ready_next_candidate_fit"])
        self.assertTrue(any("meaningful unit" in warning for warning in attrs["top_candidate_fit"]["warnings"]))
        self.assertEqual(attrs["candidate_devices"][0]["name"], "EV limit")
        self.assertIn("Return after blocker repair:", attrs["promotion_handoff"])
        self.assertIn("- Open sources path first.", attrs["promotion_handoff"])
        self.assertIn(
            "- Make promotion, enablement, removal, and other fleet edits in devices path; use the device page only for secondary review and handoff.",
            attrs["promotion_handoff"],
        )

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
                        "observed_active": True,
                        "current_power_w": 1180,
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
        self.assertEqual(attrs["managed_snapshot"], "1 managed | 1 enabled | 1 usable | active load 1180 W | 1 active managed device | active device Pool pump (action turn_on) | 1 managed device needs attention | attention first Pool pump | plan Pool pump")
        self.assertEqual(attrs["unmanaged_snapshot"], "1 candidate | 1 fixed candidate | surfaced Hot water | likely useful | key warning: No immediate warnings")
        self.assertEqual(attrs["attention_count"], 1)
        self.assertEqual(attrs["first_attention_device"], "Pool pump")
        self.assertEqual(attrs["first_blocked_device"], "")
        self.assertEqual(attrs["first_planned_device"], "Pool pump")
        self.assertEqual(attrs["first_review_candidate"]["entity_id"], "switch.hot_water")
        self.assertEqual(attrs["first_review_candidate_fit"]["confidence"], "high")
        self.assertEqual(attrs["ready_next_candidate"]["entity_id"], "switch.hot_water")
        self.assertEqual(attrs["ready_next_candidate_fit"]["confidence"], "high")
        self.assertIn("Before fleet work:", attrs["blocker_first"])
        self.assertIn("Return after blocker repair:", attrs["promotion_handoff"])
        self.assertIn("- Open sources path first.", attrs["promotion_handoff"])
        self.assertIn("- Why: Mapped source blockers remain.", attrs["promotion_handoff"])

    def test_device_page_unmanaged_snapshot_names_ready_next_when_top_candidate_needs_review(self) -> None:
        button_module = _load_button_module()

        summary = button_module._unmanaged_snapshot_summary(
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

        self.assertIn("review Virtual load", summary)
        self.assertIn("ready Hot water relay", summary)
        self.assertIn("review Virtual load | review first | key warning:", summary)

    def test_blocker_handoff_after_repair_uses_real_fleet_step_not_blocker_step(self) -> None:
        button_module = _load_button_module()
        button_module.build_native_command_center_summary = lambda coordinator: {
            "recommended_section": "Sensors",
            "recommended_path": "sources path",
            "recommended_reason": "Mapped source blockers remain.",
            "next_action_summary": "Open sources path and finish source repair before promoting more devices.",
            "device_next_step": "Open sources path and finish source repair before promoting more devices.",
        }
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(device_details={}),
        )
        button = button_module.ZeroNetExportShowFleetConsoleButton(coordinator)
        button.hass = SimpleNamespace(
            states=SimpleNamespace(
                async_all=lambda: [
                    SimpleNamespace(
                        entity_id="switch.hot_water",
                        state="off",
                        attributes={"friendly_name": "Hot water"},
                    ),
                ]
            )
        )

        attrs = button.extra_state_attributes

        self.assertIn(
            "- Next fleet step after repair: Open devices path to review the Managed Devices workspace, start in the unmanaged section: Hot water (fixed) | likely useful | key warning: No immediate warnings.",
            attrs["promotion_handoff"],
        )
        self.assertIn(
            "- After repair: Open devices path to review the Managed Devices workspace, start in the unmanaged section: Hot water (fixed) | likely useful | key warning: No immediate warnings.",
            attrs["blocker_first"],
        )
        self.assertNotIn(
            "Open devices path and review Hot water (fixed) | likely useful | key warning: No immediate warnings first.",
            attrs["blocker_first"],
        )
        self.assertNotIn(
            "- Next fleet step after repair: Open sources path and finish source repair before promoting more devices.",
            attrs["promotion_handoff"],
        )

    def test_blocker_handoff_after_repair_keeps_ready_next_candidate_visible(self) -> None:
        button_module = _load_button_module()

        next_step = button_module._managed_devices_post_blocker_step(
            {
                "recommended_section": "Sensors",
                "recommended_path": "sources path",
                "recommended_reason": "Mapped source blockers remain.",
                "next_action_summary": "Open sources path and finish source repair first.",
                "device_next_step": "Open sources path and finish source repair first.",
            },
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
            ],
            has_managed_devices=False,
        )

        self.assertIn(
            "start in the unmanaged section: Virtual load (fixed) | review first",
            next_step,
        )
        self.assertIn(
            "then promote next from the unmanaged section: Hot water relay (fixed) | likely useful",
            next_step,
        )

    def test_blocker_handoff_after_repair_keeps_existing_fleet_on_managed_devices_workspace_when_no_candidates_exist(self) -> None:
        button_module = _load_button_module()

        lines = button_module._managed_devices_blocker_first_lines(
            {
                "recommended_section": "Sensors",
                "recommended_path": "sources path",
                "recommended_reason": "Mapped source blockers remain.",
                "next_action_summary": "Open sources path and finish source repair first.",
                "device_next_step": "Open sources path and finish source repair first.",
            },
            [],
            has_managed_devices=True,
        )

        self.assertIn(
            "- After repair: Open devices path and use the Managed Devices workspace to edit device settings or stage enablement changes before changing controls or deeper diagnostics.",
            lines,
        )

    def test_blocker_handoff_after_repair_keeps_empty_fleet_manual_in_managed_devices_workspace_when_no_candidates_exist(self) -> None:
        button_module = _load_button_module()

        lines = button_module._managed_devices_blocker_first_lines(
            {
                "recommended_section": "Sensors",
                "recommended_path": "sources path",
                "recommended_reason": "Mapped source blockers remain.",
                "next_action_summary": "Open sources path and finish source repair first.",
                "device_next_step": "Open sources path and finish source repair first.",
            },
            [],
            has_managed_devices=False,
        )

        self.assertIn(
            "- After repair: Open devices path to review the Managed Devices workspace, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available.",
            lines,
        )
        self.assertNotIn(
            "check for the next unmanaged promotion candidate",
            "\n".join(lines),
        )

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

    def test_empty_managed_snapshot_uses_operator_wording(self) -> None:
        button_module = _load_button_module()

        self.assertEqual(
            button_module._managed_snapshot_summary([], include_planned_count=True),
            "no managed yet | 0 enabled | 0 usable | 0 planned action(s)",
        )

    def test_managed_snapshot_names_first_attention_device_without_blocked_or_planned_rows(self) -> None:
        button_module = _load_button_module()

        summary = button_module._managed_snapshot_summary(
            [
                {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "enabled": True,
                    "effective_enabled": True,
                    "status": "Last action failed",
                    "last_action_status": "failed",
                    "guard_status": "ready",
                    "planned_action": "",
                    "nominal_power_w": 1200,
                }
            ],
            include_planned_count=True,
        )

        self.assertEqual(
            summary,
            "1 managed | 1 enabled | 1 usable | 1 managed device needs attention | attention first Pool pump | 1 fixed managed | 1200 W nominal | 0 planned action(s)",
        )

    def test_managed_snapshot_prefers_attention_first_order_over_config_insertion_order(self) -> None:
        button_module = _load_button_module()

        summary = button_module._managed_snapshot_summary(
            [
                {
                    "name": "EV charger",
                    "entity_id": "number.ev_limit",
                    "kind": "variable",
                    "usable": True,
                    "enabled": True,
                    "effective_enabled": True,
                    "priority": 50,
                    "planned_action": "set_power",
                },
                {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "enabled": True,
                    "effective_enabled": True,
                    "priority": 10,
                    "planned_action": "turn_on",
                },
            ],
            include_planned_count=True,
        )

        self.assertEqual(
            summary,
            "2 managed | 2 enabled | 1 usable | 2 managed devices need attention | attention first Pool pump | 1 fixed managed | 1 variable managed | 0 W nominal | blocked Pool pump | 2 planned action(s) | plan Pool pump",
        )

    def test_managed_device_review_line_carries_kind_priority_power_and_plan_reason_context(self) -> None:
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
                "current_active_seconds": 930,
                "active_runtime_today_seconds": 4520,
                "guard_status": "ready",
                "planned_action": "set_power",
                "planned_action_reason": "Lift target to absorb the current export spike before grid feed-in rises further.",
                "last_action_status": "throttled",
            }
        )

        self.assertEqual(
            line,
            "- EV charger: variable | Tracking export | usable | enabled | priority 40 | priority override 55 | enabled override off | power 1800 W | target 2200 W | runtime 15m 30s | today 1h 15m | guard ready | action set_power | why Lift target to absorb the current export spike before grid feed-in ri... | last throttled",
        )

    def test_managed_device_review_line_uses_block_reason_for_unusable_device(self) -> None:
        button_module = _load_button_module()

        line = button_module._format_device_review_line(
            {
                "name": "Pool pump",
                "entity_id": "switch.pool_pump",
                "kind": "fixed",
                "status": "Waiting for source repair",
                "usable": False,
                "enabled": True,
                "effective_enabled": True,
                "current_power_w": 0,
                "guard_status": "blocked",
                "planned_action": "hold",
                "reason": "Solar power source is unavailable, so this device cannot be evaluated safely right now.",
            }
        )

        self.assertEqual(
            line,
            "- Pool pump: fixed | Waiting for source repair | not usable | enabled | power 0 W | guard blocked | action hold | why Solar power source is unavailable, so this device cannot be evaluated...",
        )

    def test_managed_device_review_line_surfaces_guard_reason_for_blocked_planned_action(self) -> None:
        button_module = _load_button_module()

        line = button_module._format_device_review_line(
            {
                "name": "Pool pump",
                "entity_id": "switch.pool_pump",
                "kind": "fixed",
                "status": "Ready for control",
                "usable": True,
                "enabled": True,
                "effective_enabled": True,
                "current_power_w": 0,
                "guard_status": "blocked",
                "guard_reason": "Action cooldown is still active for about 120 more second(s).",
                "action_executable": False,
                "planned_action": "turn_on",
                "planned_action_reason": "Use the pump to absorb export.",
            }
        )

        self.assertEqual(
            line,
            "- Pool pump: fixed | Ready for control | usable | enabled | power 0 W | guard blocked | action turn_on | why Use the pump to absorb export | guard why Action cooldown is still active for about 120 more second(s)",
        )

    def test_managed_device_review_line_audit_mode_adds_nominal_and_last_action_timing(self) -> None:
        button_module = _load_button_module()

        line = button_module._format_device_review_line(
            {
                "name": "Pool pump",
                "entity_id": "switch.pool_pump",
                "kind": "fixed",
                "status": "Tracking export",
                "usable": True,
                "enabled": True,
                "effective_enabled": True,
                "priority": 90,
                "current_power_w": 1180,
                "nominal_power_w": 1200,
                "guard_status": "ready",
                "planned_action": "turn_on",
                "last_requested_power_w": 1200,
                "last_applied_power_w": 1200,
                "successful_action_count": 4,
                "failed_action_count": 1,
                "last_action_seconds_ago": 125,
                "last_applied_at": datetime(2026, 4, 18, 8, 31, tzinfo=timezone.utc),
            },
            audit=True,
        )

        self.assertEqual(
            line,
            "- Pool pump: fixed | Tracking export | usable | enabled | priority 90 | power 1180 W | nominal 1200 W | guard ready | action turn_on | last req 1200 W | last applied 1200 W | runs 4 ok/1 fail | last act 2m 5s ago | last applied at 2026-04-18T08:31:00Z",
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
                        "observed_active": True,
                        "current_power_w": 1180,
                        "current_target_power_w": None,
                        "priority": 90,
                        "cooldown_seconds": 300,
                        "min_on_seconds": 900,
                        "min_off_seconds": 600,
                        "max_active_seconds": 7200,
                        "operator_enabled_override": None,
                        "operator_priority_override": 75,
                        "last_action_status": "applied",
                        "last_action_at": datetime(2026, 4, 18, 8, 32, tzinfo=timezone.utc),
                        "last_action_seconds_ago": 125,
                        "last_action_result_message": "Turned on successfully.",
                        "last_requested_power_w": 1200,
                        "last_applied_power_w": 1200,
                        "last_applied_at": datetime(2026, 4, 18, 8, 31, tzinfo=timezone.utc),
                        "current_active_seconds": 930,
                        "active_runtime_today_seconds": 4520,
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
        self.assertIn("Primary Managed Devices workspace in Configure: devices path", message)
        self.assertIn("Recommended next step: Review the next managed device.", message)
        self.assertIn("Before fleet work:", message)
        self.assertIn("Managed devices workspace context:", message)
        self.assertIn("- Managed snapshot: 1 managed | 1 enabled | 1 usable | active load 1180 W | 1 active managed device | active device Pool pump (fixed | action turn_on) | 1 managed device needs attention | attention first Pool pump | 1 fixed managed | 1200 W nominal | 1 planned action(s) | plan Pool pump", message)
        self.assertIn("- Unmanaged snapshot: 1 candidate | 1 fixed candidate | surfaced Hot water | likely useful | key warning: No immediate warnings", message)
        self.assertIn("- Currently surfaced unmanaged candidate: Hot water (fixed) | likely useful | key warning: No immediate warnings", message)
        self.assertIn("Fleet attention context:", message)
        self.assertIn("- This device is currently in the attention-first review bucket.", message)
        self.assertIn("- First managed device needing attention: Pool pump", message)
        self.assertIn("- Other managed devices needing attention: none", message)
        self.assertIn("- Other steady managed devices: none", message)
        self.assertIn("Device: Pool pump", message)
        self.assertNotIn("Entity: switch.pool_pump", message)
        self.assertNotIn("Use switch.pool_pump sensors", message)
        self.assertNotIn("entity=switch.pool_pump", message)
        self.assertIn("Use this device's sensors on the Zero Net Export device page", message)
        self.assertIn("Guard state: ready", message)
        self.assertIn("Planned action: turn_on", message)
        self.assertIn("- Priority: 90", message)
        self.assertIn("- Planned power delta: 1200 W", message)
        self.assertIn("- Active runtime now: 15m 30s", message)
        self.assertIn("- Active runtime today: 1h 15m", message)
        self.assertNotIn("- Variable range:", message)
        self.assertNotIn("- Step size:", message)
        self.assertNotIn("- Requested target power:", message)
        self.assertIn("- Priority override: forcing 75", message)
        self.assertIn("- Enabled override: none", message)
        self.assertIn("- Last action at: 2026-04-18T08:32:00Z", message)
        self.assertIn("- Last action age: 2m 5s", message)
        self.assertIn("- Last action result: Turned on successfully.", message)
        self.assertIn("- Last applied at: 2026-04-18T08:31:00Z", message)
        self.assertIn("Return to devices path in Configure for primary Managed Devices workspace edits, enablement, promotion, or removal.", message)

    def test_managed_device_detail_button_surfaces_review_first_candidate_context(self) -> None:
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
                        "guard_status": "ready",
                        "planned_action": "turn_on",
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
                    ),
                    SimpleNamespace(
                        entity_id="number.ev_limit",
                        state="2200",
                        attributes={"friendly_name": "EV limit"},
                    ),
                ]
            )
        )

        import asyncio
        asyncio.run(button.async_press())

        message = notification_calls[0]["args"][1]
        self.assertIn("- Currently surfaced unmanaged candidate: Hot water (fixed) | likely useful | key warning: No immediate warnings", message)
        self.assertIn("- First review-first unmanaged candidate: EV limit (variable) | review first | key warning: Variable power controls need a meaningful unit, sane range, and clear relation to real device power.", message)
        self.assertIn("- First review-first unmanaged usefulness: review first: Looks like a plausible controllable candidate, but review before promotion.", message)
        self.assertIn("- First review-first unmanaged warnings: Variable power controls need a meaningful unit, sane range, and clear relation to real device power.", message)
        self.assertIn("- Another ready unmanaged candidate: Hot water (fixed) | likely useful | key warning: No immediate warnings", message)
        self.assertIn("- Another ready unmanaged usefulness: likely useful: Switch entities are usually likely fixed-load candidates when they control a real appliance or relay.", message)
        self.assertIn("- Another ready unmanaged warnings: No immediate warnings.", message)

    def test_managed_device_detail_button_surfaces_peer_attention_context(self) -> None:
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
                        "guard_status": "ready",
                        "planned_action": "turn_on",
                    },
                    "heater": {
                        "name": "Water heater",
                        "entity_id": "switch.water_heater",
                        "kind": "fixed",
                        "usable": False,
                        "enabled": True,
                        "effective_enabled": True,
                        "status": "Blocked",
                        "guard_status": "source blocked",
                        "planned_action": "turn_on",
                        "action_executable": False,
                    },
                    "fan": {
                        "name": "Garage fan",
                        "entity_id": "switch.garage_fan",
                        "kind": "fixed",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "status": "Idle",
                        "guard_status": "ready",
                        "planned_action": "hold",
                    },
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

        message = notification_calls[0]["args"][1]
        self.assertIn("Fleet attention context:", message)
        self.assertIn("- This device is currently in the attention-first review bucket.", message)
        self.assertIn("- First managed device needing attention: Water heater", message)
        self.assertIn("- Other managed devices needing attention: Water heater", message)
        self.assertIn("- Other steady managed devices: Garage fan", message)
        self.assertIn("Other attention-device audit preview:", message)
        self.assertIn(
            "- Water heater: fixed | Blocked | not usable | enabled | power n/a | guard source blocked | action turn_on",
            message,
        )
        self.assertIn("Other steady-device audit preview:", message)
        self.assertIn(
            "- Garage fan: fixed | Idle | usable | enabled | power n/a | guard ready | action hold",
            message,
        )
        self.assertIn("Current device audit snapshot:", message)
        self.assertIn(
            "- Pool pump: fixed | Ready for control | usable | enabled | power n/a | guard ready | action turn_on",
            message,
        )
        self.assertIn("Review-order context:", message)
        self.assertIn("- This device is #2 in the attention-first review bucket.", message)
        self.assertIn("- Attention-first bucket size: 2", message)
        self.assertIn("- Next device in this review bucket: none", message)

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
                    ),
                    SimpleNamespace(
                        entity_id="number.ev_limit",
                        state="2200",
                        attributes={"friendly_name": "EV limit"},
                    ),
                ]
            )
        )

        attrs = button.extra_state_attributes

        self.assertEqual(attrs["recommended_section"], "Sensors")
        self.assertEqual(attrs["recommended_path"], "sources path")
        self.assertEqual(attrs["recommended_reason"], "Mapped source blockers remain.")
        self.assertIn("Before fleet work:", attrs["blocker_first"])
        self.assertEqual(attrs["managed_snapshot"], "1 managed | 1 enabled | 0 usable | 1 managed device needs attention | attention first Pool pump | 1 fixed managed | 0 W nominal | blocked Pool pump | 0 planned action(s)")
        self.assertEqual(attrs["unmanaged_snapshot"], "2 candidates | 1 fixed candidate | 1 variable candidate | surfaced Hot water | likely useful | key warning: No immediate warnings")
        self.assertEqual(attrs["top_unmanaged_candidate"]["entity_id"], "switch.hot_water")
        self.assertEqual(attrs["first_review_candidate"]["entity_id"], "number.ev_limit")
        self.assertEqual(attrs["first_review_candidate_fit"]["confidence"], "medium")
        self.assertEqual(attrs["ready_next_candidate"]["entity_id"], "switch.hot_water")
        self.assertEqual(attrs["ready_next_candidate_fit"]["confidence"], "high")

    def test_managed_device_review_attributes_treat_blocked_plans_as_blocked_activity(self) -> None:
        button_module = _load_button_module()
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
                        "guard_status": "blocked",
                        "guard_reason": "Action cooldown is still active for about 120 more second(s).",
                        "action_executable": False,
                        "planned_action": "turn_on",
                    }
                }
            ),
        )
        button = button_module.ZeroNetExportShowManagedDeviceReviewButton(coordinator)
        button.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        attrs = button.extra_state_attributes

        self.assertEqual(attrs["first_blocked_device"], "Pool pump")
        self.assertEqual(attrs["managed_snapshot"], "1 managed | 1 enabled | 1 usable | 1 managed device needs attention | attention first Pool pump | 1 fixed managed | 0 W nominal | blocked Pool pump | 1 planned action(s) | plan Pool pump")

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
