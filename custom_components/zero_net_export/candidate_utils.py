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

_FIT_USEFULNESS_LABELS = {
    "high": "strong match",
    "medium": "plausible match",
    "low": "needs extra review",
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


def build_candidate_preview(
    candidate: dict[str, Any],
    *,
    include_entity_id: bool = True,
    include_kind: bool = True,
    include_state: bool = False,
) -> str:
    """Return a concise operator-facing preview for unmanaged candidate rows."""
    fit = assess_candidate(candidate)
    name = str(candidate.get("name") or candidate.get("entity_id") or "candidate")
    entity_id = str(candidate.get("entity_id") or "")
    kind = str(candidate.get("kind") or "unknown")
    state = str(candidate.get("state") or "")

    detail_bits: list[str] = []
    if include_entity_id and entity_id:
        detail_bits.append(entity_id)
    if include_kind and kind:
        detail_bits.append(kind)
    if include_state and state:
        detail_bits.append(f"state {state}")

    heading = name if not detail_bits else f"{name} ({', '.join(detail_bits)})"
    confidence = str(fit.get("confidence") or "medium")
    usefulness = _FIT_USEFULNESS_LABELS.get(confidence, confidence)
    warnings = [str(item).strip() for item in (fit.get("warnings") or []) if str(item).strip()]
    key_warning = warnings[0] if warnings else "No immediate warnings"

    return f"{heading} | {usefulness} | key warning: {key_warning}"


def build_candidate_name_summary(
    candidates: Iterable[dict[str, Any]],
    *,
    limit: int = 3,
    max_chars: int = 240,
) -> str:
    """Return a compact candidate name list safe for sensor state strings."""
    candidate_list = list(candidates)
    if not candidate_list:
        return "None"

    names = [str(item.get("name") or item.get("entity_id") or "candidate").strip() for item in candidate_list[:limit]]
    names = [name for name in names if name]
    remainder = len(candidate_list) - min(len(candidate_list), limit)
    summary_parts = names[:]
    if remainder > 0:
        summary_parts.append(f"+{remainder} more")

    summary = "; ".join(summary_parts) or "None"
    if len(summary) <= max_chars:
        return summary

    while len(summary_parts) > 1 and len(summary) > max_chars:
        if summary_parts[-1].startswith("+"):
            summary_parts.pop(-2)
        else:
            summary_parts.pop()
        summary = "; ".join(summary_parts)

    if len(summary) <= max_chars:
        return summary
    return summary[: max_chars - 1].rstrip() + "…"


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
