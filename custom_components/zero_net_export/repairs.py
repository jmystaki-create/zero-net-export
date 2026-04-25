"""Repairs / issue-registry support for Zero Net Export."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.components.repairs import RepairsFlow

from .const import (
    CONF_DEVICE_INVENTORY_JSON,
    DEFAULT_DEVICE_INVENTORY_JSON,
    DOMAIN,
    REQUIRED_SOURCE_KEYS,
    SOURCE_ROLE_LABELS,
)
from .device_model import parse_device_configs
from .native_support import (
    ADVANCED_DEVICES_CONFIGURE_PATH,
    DEVICES_CONFIGURE_PATH,
    POLICY_CONFIGURE_PATH,
    PRIMARY_CONFIGURE_PATH,
    SOURCES_CONFIGURE_PATH,
    SUPPORT_CONFIGURE_PATH,
    build_native_operator_readiness,
    build_source_attention_details,
    build_source_attention_role_summary,
    build_source_repair_step,
    build_source_selector_fallback_hint,
    summarize_validation_issue_messages,
)
from .release_info import (
    build_install_consistency_summary,
    build_install_provenance,
    build_install_repair_step,
)

ISSUE_SETUP_INCOMPLETE = "setup_incomplete"
ISSUE_DEVICE_INVENTORY_INVALID = "device_inventory_invalid"
ISSUE_RUNTIME_ATTENTION = "runtime_attention"
ISSUE_KEYS = (ISSUE_SETUP_INCOMPLETE, ISSUE_DEVICE_INVENTORY_INVALID, ISSUE_RUNTIME_ATTENTION)


class ZeroNetExportRepairsFlow(RepairsFlow):
    """Minimal Repairs flow so Home Assistant accepts this integration's repairs platform."""

    def __init__(self, issue_id: str, data: dict[str, str] | None = None) -> None:
        self.issue_id = issue_id
        self._data = data or {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        placeholders = {
            "issue_id": self.issue_id,
            "next_step": self._data.get(
                "next_step",
                f"Review {PRIMARY_CONFIGURE_PATH} first, then use {SUPPORT_CONFIGURE_PATH} for diagnostics and troubleshooting.",
            ),
            "configure_path": self._data.get("configure_path", PRIMARY_CONFIGURE_PATH),
            "support_path": self._data.get("support_path", SUPPORT_CONFIGURE_PATH),
        }
        return self.async_show_form(
            step_id="confirm",
            data_schema=None,
            description_placeholders=placeholders,
        )

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None):
        return self.async_create_entry(title="Zero Net Export", data={"issue_id": self.issue_id})


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str] | None = None,
) -> RepairsFlow | None:
    """Return a Repairs flow instance so the integration exposes a valid repairs platform."""
    return ZeroNetExportRepairsFlow(issue_id, data)


def _entry_issue_id(entry: ConfigEntry, issue_key: str) -> str:
    return f"{entry.entry_id}_{issue_key}"


def _delete_issue(hass: HomeAssistant, issue_id: str) -> None:
    ir.async_delete_issue(hass, DOMAIN, issue_id)


def _create_issue(
    hass: HomeAssistant,
    issue_id: str,
    *,
    issue_key: str,
    severity: ir.IssueSeverity,
    translation_placeholders: dict[str, str],
) -> None:
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=False,
        severity=severity,
        translation_key=issue_key,
        translation_placeholders=translation_placeholders,
    )


def async_clear_repairs_issues(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove all Repairs issues for a specific Zero Net Export entry."""
    for issue_key in ISSUE_KEYS:
        _delete_issue(hass, _entry_issue_id(entry, issue_key))


def _format_named_source_roles(source_keys: list[str]) -> str:
    named_roles = [SOURCE_ROLE_LABELS.get(key, key) for key in source_keys if key]
    if not named_roles:
        return ""
    return ", ".join(named_roles[:6])


def async_sync_repairs_issues(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: Any | None = None,
    state: Any | None = None,
) -> None:
    """Publish actionable setup/runtime issues into Home Assistant Repairs."""
    merged = dict(entry.data)
    merged.update(entry.options)
    missing_source_keys = [key for key in REQUIRED_SOURCE_KEYS if not merged.get(key)]
    missing_sources = [SOURCE_ROLE_LABELS.get(key, key) for key in missing_source_keys]

    raw_inventory = entry.options.get(
        CONF_DEVICE_INVENTORY_JSON,
        entry.data.get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
    )
    devices, device_issues = parse_device_configs(raw_inventory)

    readiness = build_native_operator_readiness(coordinator) if coordinator is not None else {}
    next_step = str(
        readiness.get("next_step")
        or build_source_repair_step(missing_source_keys=missing_source_keys)
    )
    summary = str(readiness.get("summary") or "Zero Net Export still needs attention before it is fully operator-ready.")

    setup_issue_id = _entry_issue_id(entry, ISSUE_SETUP_INCOMPLETE)
    inventory_issue_id = _entry_issue_id(entry, ISSUE_DEVICE_INVENTORY_INVALID)
    runtime_issue_id = _entry_issue_id(entry, ISSUE_RUNTIME_ATTENTION)

    setup_fallback_hint = build_source_selector_fallback_hint(role_keys=missing_source_keys)
    setup_fallback_text = setup_fallback_hint or "Not needed right now."
    if setup_fallback_hint and setup_fallback_hint not in next_step:
        next_step = f"{next_step} {setup_fallback_hint}"

    if missing_sources or not devices:
        _create_issue(
            hass,
            setup_issue_id,
            issue_key=ISSUE_SETUP_INCOMPLETE,
            severity=ir.IssueSeverity.WARNING,
            translation_placeholders={
                "configure_path": PRIMARY_CONFIGURE_PATH,
                "sources_path": SOURCES_CONFIGURE_PATH,
                "policy_path": POLICY_CONFIGURE_PATH,
                "devices_path": DEVICES_CONFIGURE_PATH,
                "support_path": SUPPORT_CONFIGURE_PATH,
                "missing_sources": ", ".join(missing_sources) if missing_sources else "None",
                "device_count": str(len(devices)),
                "next_step": next_step,
                "summary": summary,
                "fallback_hint": setup_fallback_text,
            },
        )
    else:
        _delete_issue(hass, setup_issue_id)

    if device_issues:
        _create_issue(
            hass,
            inventory_issue_id,
            issue_key=ISSUE_DEVICE_INVENTORY_INVALID,
            severity=ir.IssueSeverity.ERROR,
            translation_placeholders={
                "configure_path": DEVICES_CONFIGURE_PATH,
                "advanced_recovery_path": ADVANCED_DEVICES_CONFIGURE_PATH,
                "issue_count": str(len(device_issues)),
                "issue_examples": "; ".join(device_issues[:3]),
            },
        )
    else:
        _delete_issue(hass, inventory_issue_id)

    runtime_state = state or (coordinator.data if coordinator is not None else None)
    if runtime_state is None:
        _delete_issue(hass, runtime_issue_id)
        return

    data = runtime_state
    runtime_reasons: list[str] = []
    install_provenance = build_install_provenance()
    merged_config = dict(entry.data)
    merged_config.update(entry.options)
    install_validation_blocked = not bool(install_provenance.get("live_validation_safe"))
    source_attention = build_source_attention_details(data)
    unavailable_source_keys = source_attention["unavailable_source_keys"]
    unavailable_sources = _format_named_source_roles(unavailable_source_keys)
    stale_source_keys = source_attention["stale_source_keys"]
    stale_sources = _format_named_source_roles(stale_source_keys)
    blocking_validation_details = summarize_validation_issue_messages(data, severities={"error"}, limit=3)

    if install_validation_blocked:
        runtime_reasons.append(build_install_consistency_summary(install_provenance))
    if data.stale_data:
        if stale_sources:
            runtime_reasons.append(f"Stale required mapped sources: {stale_sources}.")
        runtime_reasons.append(data.stale_source_summary or "One or more required source entities are stale.")
    if data.safe_mode:
        if unavailable_sources:
            runtime_reasons.append(f"Unavailable mapped sources are holding safe mode: {unavailable_sources}.")
        if blocking_validation_details != "None":
            runtime_reasons.append(f"Blocking source validation details: {blocking_validation_details}.")
        runtime_reasons.append(data.reason or "Source validation has put the controller into safe mode.")
    if data.command_failure:
        runtime_reasons.append(data.last_failed_action_message or data.recent_failure_summary or "A recent device command failed.")
    if data.device_count > 0 and data.usable_device_count == 0 and not device_issues and not data.stale_data:
        runtime_reasons.append(data.device_status_summary or "Managed devices exist, but none are currently usable.")

    runtime_next_step = str(readiness.get("next_step") or data.recommendation or next_step)
    if install_validation_blocked:
        runtime_next_step = build_install_repair_step(install_provenance)
    elif missing_source_keys or unavailable_source_keys or stale_source_keys or data.stale_data or blocking_validation_details != "None":
        runtime_next_step = build_source_repair_step(
            missing_source_keys=missing_source_keys,
            unavailable_source_keys=unavailable_source_keys,
            stale_source_keys=stale_source_keys,
            blocking_validation_details=blocking_validation_details,
        )

    runtime_fallback_hint = build_source_selector_fallback_hint(
        role_keys=[*missing_source_keys, *unavailable_source_keys, *stale_source_keys]
    )
    runtime_fallback_text = runtime_fallback_hint or "Not needed right now."
    if runtime_fallback_hint and runtime_fallback_hint not in runtime_next_step:
        runtime_next_step = f"{runtime_next_step} {runtime_fallback_hint}"

    if runtime_reasons:
        _create_issue(
            hass,
            runtime_issue_id,
            issue_key=ISSUE_RUNTIME_ATTENTION,
            severity=ir.IssueSeverity.WARNING,
            translation_placeholders={
                "configure_path": PRIMARY_CONFIGURE_PATH,
                "sources_path": SOURCES_CONFIGURE_PATH,
                "devices_path": DEVICES_CONFIGURE_PATH,
                "support_path": SUPPORT_CONFIGURE_PATH if install_validation_blocked else (SOURCES_CONFIGURE_PATH if (missing_source_keys or unavailable_sources or stale_sources or data.stale_data) else SUPPORT_CONFIGURE_PATH),
                "health_summary": str(data.health_summary or summary),
                "reason_summary": " ".join(runtime_reasons[:3]),
                "unavailable_sources": unavailable_sources or "None",
                "stale_sources": stale_sources or "None",
                "source_attention_roles": build_source_attention_role_summary(data, merged_config, limit=4),
                "source_repair_step": build_source_repair_step(
                    missing_source_keys=missing_source_keys,
                    unavailable_source_keys=unavailable_source_keys,
                    stale_source_keys=stale_source_keys,
                    blocking_validation_details=blocking_validation_details,
                ),
                "install_status": str(install_provenance.get("summary") or "Installed package provenance unavailable"),
                "install_consistency": build_install_consistency_summary(install_provenance),
                "next_step": runtime_next_step,
                "fallback_hint": runtime_fallback_text,
                "blocking_validation_details": blocking_validation_details,
            },
        )
    else:
        _delete_issue(hass, runtime_issue_id)
