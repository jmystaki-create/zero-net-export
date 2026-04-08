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
from .native_support import PRIMARY_CONFIGURE_PATH, build_native_operator_readiness

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


def async_sync_repairs_issues(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: Any | None = None,
    state: Any | None = None,
) -> None:
    """Publish actionable setup/runtime issues into Home Assistant Repairs."""
    merged = dict(entry.data)
    merged.update(entry.options)
    missing_sources = [SOURCE_ROLE_LABELS.get(key, key) for key in REQUIRED_SOURCE_KEYS if not merged.get(key)]

    raw_inventory = entry.options.get(
        CONF_DEVICE_INVENTORY_JSON,
        entry.data.get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
    )
    devices, device_issues = parse_device_configs(raw_inventory)

    readiness = build_native_operator_readiness(coordinator) if coordinator is not None else {}
    next_step = str(readiness.get("next_step") or "Open Configure and continue the guided native setup flow.")
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
                "configure_path": PRIMARY_CONFIGURE_PATH,
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
    if data.stale_data:
        runtime_reasons.append(data.stale_source_summary or "One or more required source entities are stale.")
    if data.safe_mode:
        runtime_reasons.append(data.reason or "Source validation has put the controller into safe mode.")
    if data.command_failure:
        runtime_reasons.append(data.last_failed_action_message or data.recent_failure_summary or "A recent device command failed.")
    if data.device_count > 0 and data.usable_device_count == 0 and not device_issues and not data.stale_data:
        runtime_reasons.append(data.device_status_summary or "Configured devices exist, but none are currently usable.")

    if runtime_reasons:
        _create_issue(
            hass,
            runtime_issue_id,
            issue_key=ISSUE_RUNTIME_ATTENTION,
            severity=ir.IssueSeverity.WARNING,
            translation_placeholders={
                "configure_path": PRIMARY_CONFIGURE_PATH,
                "health_summary": str(data.health_summary or summary),
                "reason_summary": " ".join(runtime_reasons[:3]),
                "next_step": str(readiness.get("next_step") or data.recommendation or next_step),
            },
        )
    else:
        _delete_issue(hass, runtime_issue_id)
