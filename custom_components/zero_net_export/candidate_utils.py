"""Managed-device candidate discovery helpers for native HA surfaces."""
from __future__ import annotations

from typing import Any, Iterable

from .const import DEVICE_CANDIDATE_DOMAINS, DEVICE_CANDIDATE_FIXED_DOMAINS


_CANDIDATE_CONFIDENCE_ORDER = {
    "switch": 0,
    "number": 0,
    "light": 1,
    "input_number": 1,
    "input_boolean": 2,
}

_CANDIDATE_DOMAIN_ORDER = {
    "switch": 0,
    "number": 1,
    "light": 2,
    "input_number": 3,
    "input_boolean": 4,
}


def candidate_sort_key(candidate: dict[str, Any]) -> tuple[int, int, str, str]:
    """Return a stable sort key that prefers stronger promotion targets first."""
    domain = str(candidate.get("domain") or "")
    name = str(candidate.get("name") or candidate.get("entity_id") or "").lower()
    entity_id = str(candidate.get("entity_id") or "")
    return (
        _CANDIDATE_CONFIDENCE_ORDER.get(domain, 99),
        _CANDIDATE_DOMAIN_ORDER.get(domain, 99),
        name,
        entity_id,
    )


def rank_candidates(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return candidates in the native promotion order used across UI surfaces."""
    return sorted(candidates, key=candidate_sort_key)


def discover_candidate_devices(states: Iterable[Any], managed_entity_ids: set[str]) -> list[dict[str, str]]:
    """Return unmanaged controllable-device candidates in promotion order."""
    candidates: list[dict[str, str]] = []
    for state in states:
        entity_id = getattr(state, "entity_id", "")
        domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
        if domain not in DEVICE_CANDIDATE_DOMAINS:
            continue
        if entity_id in managed_entity_ids:
            continue
        state_value = str(getattr(state, "state", "")).lower()
        if state_value in {"unknown", "unavailable"}:
            continue
        attributes = getattr(state, "attributes", {}) or {}
        candidates.append(
            {
                "entity_id": entity_id,
                "name": str(attributes.get("friendly_name") or entity_id),
                "domain": domain,
                "kind": "fixed" if domain in DEVICE_CANDIDATE_FIXED_DOMAINS else "variable",
                "state": str(getattr(state, "state", "")),
            }
        )
    return rank_candidates(candidates)
