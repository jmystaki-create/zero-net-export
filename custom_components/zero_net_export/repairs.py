"""Repairs / issue-registry support for Zero Net Export."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

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
    PRIMARY_CONFIGURE_PATH,
    SOURCES_CONFIGURE_PATH,
    SUPPORT_CONFIGURE_PATH,
    build_native_operator_readiness,
    build_source_attention_details,
)

ISSUE_SETUP_INCOMPLETE = "setup_incomplete"
ISSUE_DEVICE_INVENTORY_INVALID = "device_inventory_invalid"
ISSUE_RUNTIME_ATTENTION = "runtime_attention"
ISSUE_KEYS = (ISSUE_SETUP_INCOMPLETE, ISSUE_DEVICE_INVENTORY_INVALID, ISSUE_RUNTIME_ATTENTION)


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
        or f"Open {PRIMARY_CONFIGURE_PATH} and continue the guided native setup flow."
    )
    summary = str(readiness.get("summary") or "Zero Net Export still needs attention before it is fully operator-ready.")

    setup_issue_id = _entry_issue_id(entry, ISSUE_SETUP_INCOMPLETE)
    inventory_issue_id = _entry_issue_id(entry, ISSUE_DEVICE_INVENTORY_INVALID)
    runtime_issue_id = _entry_issue_id(entry, ISSUE_RUNTIME_ATTENTION)

    if missing_sources or not devices:
        _create_issue(
            hass,
            setup_issue_id,
            issue_key=ISSUE_SETUP_INCOMPLETE,
            severity=ir.IssueSeverity.WARNING,
            translation_placeholders={
                "configure_path": PRIMARY_CONFIGURE_PATH,
                "missing_sources": ", ".join(missing_sources) if missing_sources else "None",
                "device_count": str(len(devices)),
                "next_step": next_step,
                "summary": summary,
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
    source_attention = build_source_attention_details(data)
    unavailable_source_keys = source_attention["unavailable_source_keys"]
    unavailable_sources = _format_named_source_roles(unavailable_source_keys)
    stale_source_keys = source_attention["stale_source_keys"]
    stale_sources = _format_named_source_roles(stale_source_keys)

    if data.stale_data:
        if stale_sources:
            runtime_reasons.append(f"Stale required mapped sources: {stale_sources}.")
        runtime_reasons.append(data.stale_source_summary or "One or more required source entities are stale.")
    if data.safe_mode:
        if unavailable_sources:
            runtime_reasons.append(f"Unavailable mapped sources are holding safe mode: {unavailable_sources}.")
        runtime_reasons.append(data.reason or "Source validation has put the controller into safe mode.")
    if data.command_failure:
        runtime_reasons.append(data.last_failed_action_message or data.recent_failure_summary or "A recent device command failed.")
    if data.device_count > 0 and data.usable_device_count == 0 and not device_issues and not data.stale_data:
        runtime_reasons.append(data.device_status_summary or "Configured devices exist, but none are currently usable.")

    runtime_next_step = str(readiness.get("next_step") or data.recommendation or next_step)
    if missing_source_keys:
        runtime_next_step = f"Open {SOURCES_CONFIGURE_PATH}, finish the missing required source roles, then save and reload the integration."
    elif unavailable_sources:
        runtime_next_step = (
            f"Open {SOURCES_CONFIGURE_PATH}, then repair these unavailable mapped source roles: {unavailable_sources}."
        )
    elif stale_sources:
        runtime_next_step = (
            f"Open {SOURCES_CONFIGURE_PATH} or {SUPPORT_CONFIGURE_PATH}, then fix these stale mapped source roles: {stale_sources}."
        )
    elif data.stale_data:
        runtime_next_step = (
            f"Open {SOURCES_CONFIGURE_PATH} or {SUPPORT_CONFIGURE_PATH}, then fix the stale mapped sources before retrying control."
        )

    if runtime_reasons:
        _create_issue(
            hass,
            runtime_issue_id,
            issue_key=ISSUE_RUNTIME_ATTENTION,
            severity=ir.IssueSeverity.WARNING,
            translation_placeholders={
                "configure_path": PRIMARY_CONFIGURE_PATH,
                "support_path": SOURCES_CONFIGURE_PATH if (missing_source_keys or unavailable_sources or stale_sources or data.stale_data) else SUPPORT_CONFIGURE_PATH,
                "health_summary": str(data.health_summary or summary),
                "reason_summary": " ".join(runtime_reasons[:3]),
                "unavailable_sources": unavailable_sources or "None",
                "stale_sources": stale_sources or "None",
                "next_step": runtime_next_step,
            },
        )
    else:
        _delete_issue(hass, runtime_issue_id)
