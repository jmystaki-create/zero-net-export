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


def assess_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Return shared fit guidance for a discovered unmanaged candidate."""
    domain = str(candidate.get("domain") or "")
    kind = str(candidate.get("kind") or ("fixed" if domain in DEVICE_CANDIDATE_FIXED_DOMAINS else "variable"))
    raw_state = str(candidate.get("state") or "").strip().lower()
    unit = str(candidate.get("unit") or "")
    device_class = str(candidate.get("device_class") or "")

    confidence = "medium"
    summary = "Looks like a plausible controllable candidate, but review before promotion."
    warnings: list[str] = []

    if domain == "switch" and kind == "fixed":
        confidence = "high"
        summary = "Switch entities are usually strong fixed-load candidates when they control a real appliance or relay."
    elif domain == "light" and kind == "fixed":
        summary = "Light entities can be controllable, but many are comfort or presence loads rather than discretionary energy sinks."
        warnings.append(
            "Confirm this light is a real discretionary load, not a normal lighting circuit people expect to stay manual."
        )
    elif domain == "input_boolean" and kind == "fixed":
        confidence = "low"
        summary = "Helpers can represent automation intent, not a physical load."
        warnings.append(
            "This is an input_boolean helper. Verify it really drives a safe controllable load before promoting it."
        )
    elif domain in {"number", "input_number"} and kind == "variable":
        confidence = "high" if domain == "number" else "medium"
        summary = "Number-style entities are strong variable-load candidates when they represent a real power or current target."
        if domain == "input_number":
            warnings.append(
                "This is an input_number helper. Check that changing it actually drives a real device, not just a dashboard helper."
            )

    if raw_state in {"unknown", "unavailable"}:
        warnings.append(f"Entity state is currently {raw_state}. Promotion is risky until it reports cleanly.")
        confidence = "low"

    if kind == "variable" and not unit:
        warnings.append("Variable candidates are safer when the entity exposes a meaningful unit such as A, W, or %.")
        if confidence == "high":
            confidence = "medium"

    if kind == "variable" and device_class == "battery":
        warnings.append("Battery-class entities are often telemetry, not safe control targets. Confirm this is a writable control entity.")
        confidence = "low"

    return {
        "confidence": confidence,
        "summary": summary,
        "warnings": warnings,
    }


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
                "unit": str(attributes.get("unit_of_measurement") or ""),
                "device_class": str(attributes.get("device_class") or ""),
            }
        )
    return rank_candidates(candidates)
