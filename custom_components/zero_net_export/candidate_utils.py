"""Managed-device candidate discovery helpers for native HA surfaces."""
from __future__ import annotations

from typing import Any, Iterable

from .const import DEVICE_CANDIDATE_DOMAINS, DEVICE_CANDIDATE_FIXED_DOMAINS, DOMAIN


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

_REVIEW_LEVEL_LABELS = {
    "high": "strong",
    "medium": "review",
    "low": "caution",
}

_POSITIVE_LOAD_KEYWORDS = (
    "charger",
    "ev",
    "heater",
    "hot water",
    "water heater",
    "boiler",
    "geyser",
    "pool",
    "pump",
    "outlet",
    "plug",
    "aircon",
    "air conditioner",
    "hvac",
    "ac ",
)

_NEGATIVE_NON_LOAD_KEYWORDS = (
    "adguard",
    "crossfade",
    "loudness",
    "surround",
    "music",
    "sound",
    "sonos",
    "alarm",
    "api",
    "stream",
    "streamer",
    "audio",
    "speaker",
    "filter",
    "parental",
    "protection",
    "query",
    "browsing",
    "search",
    "media",
    "subwoofer",
    "speech enhancement",
    "speech_enhancement",
    "bass",
    "treble",
    "balance",
    "audio delay",
)

_NEGATIVE_ENTITY_ID_FRAGMENTS = (
    "_none",
    "_speech_enhancement",
    "_subwoofer",
)

_EXCLUDED_DEVICE_CLASSES = {
    "energy_storage",
    "temperature",
}

_EXCLUDED_VARIABLE_KEYWORDS = (
    "audio delay",
    "auto-relock",
    "auto relock",
    "battery capacity",
    "buy price",
    "dyn. price",
    "music surround level",
    "price fee",
    "price vat",
    "sell price",
    "sub gain",
    "surround level",
    "tax percent",
    "temperature limit",
)

_EXCLUDED_VARIABLE_ENTITY_ID_FRAGMENTS = (
    "_auto_relock",
    "_battery_capacity",
    "_buy_price",
    "_dyn_price_",
    "_sell_price",
    "_sub_gain",
    "_surround_level",
    "_tax_percent",
    "_temperature_limit",
)


def _candidate_text(candidate: dict[str, Any]) -> str:
    return " ".join(
        str(candidate.get(key) or "")
        for key in ("name", "entity_id", "device_class")
    ).lower()


def _negative_non_load_penalty(candidate: dict[str, Any]) -> int:
    text = _candidate_text(candidate)
    entity_id = str(candidate.get("entity_id") or "").lower()
    penalty = 0
    if any(keyword in text for keyword in _NEGATIVE_NON_LOAD_KEYWORDS):
        penalty += 3
    if any(fragment in entity_id for fragment in _NEGATIVE_ENTITY_ID_FRAGMENTS):
        penalty += 2
    return penalty


def _has_negative_non_load_signal(candidate: dict[str, Any]) -> bool:
    return _negative_non_load_penalty(candidate) > 0


def _candidate_desirability_rank(candidate: dict[str, Any]) -> int:
    """Return a secondary rank that prefers likely real loads over obvious service toggles."""
    text = _candidate_text(candidate)
    score = 0
    if any(keyword in text for keyword in _POSITIVE_LOAD_KEYWORDS):
        score -= 2
    score += _negative_non_load_penalty(candidate)
    if str(candidate.get("device_class") or "").lower() == "outlet":
        score -= 1
    return score


def _should_exclude_candidate(candidate: dict[str, Any]) -> bool:
    """Return True when an entity is clearly not a real managed-load promotion target."""
    domain = str(candidate.get("domain") or "")
    kind = str(candidate.get("kind") or "")
    text = _candidate_text(candidate)
    entity_id = str(candidate.get("entity_id") or "").lower()
    device_class = str(candidate.get("device_class") or "").lower()

    if domain == "light" and not any(keyword in text for keyword in _POSITIVE_LOAD_KEYWORDS):
        return True

    if kind != "variable" or domain not in {"number", "input_number"}:
        return False

    if device_class in _EXCLUDED_DEVICE_CLASSES:
        return True
    if any(keyword in text for keyword in _EXCLUDED_VARIABLE_KEYWORDS):
        return True
    if any(fragment in entity_id for fragment in _EXCLUDED_VARIABLE_ENTITY_ID_FRAGMENTS):
        return True
    return False


def candidate_sort_key(candidate: dict[str, Any]) -> tuple[int, int, int, str, str]:
    """Return a stable sort key that prefers stronger promotion targets first."""
    domain = str(candidate.get("domain") or "")
    name = str(candidate.get("name") or candidate.get("entity_id") or "").lower()
    entity_id = str(candidate.get("entity_id") or "")
    desirability_rank = _candidate_desirability_rank(candidate)
    confidence_rank = _CANDIDATE_CONFIDENCE_ORDER.get(domain, 99) + desirability_rank
    return (
        confidence_rank,
        desirability_rank,
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
    suitability_summary = "The entity shape looks workable for Zero Net Export, but it still needs operator review before promotion."
    safety_summary = "No obvious safety blocker is visible yet, but confirm the entity really controls the intended device."
    operational_value_summary = "This candidate could help absorb export, but confirm it represents a meaningful discretionary load."

    candidate_text = _candidate_text(candidate)
    positive_name_signal = any(keyword in candidate_text for keyword in _POSITIVE_LOAD_KEYWORDS)
    negative_name_signal = _has_negative_non_load_signal(candidate)

    if domain == "switch" and kind == "fixed":
        confidence = "high"
        summary = "Switch entities are usually strong fixed-load candidates when they control a real appliance or relay."
        suitability_summary = "Switch control is usually a clean native fit for fixed loads because Zero Net Export can turn the load on or off directly."
        operational_value_summary = "Fixed relay-style loads are usually useful when they represent a real appliance that can absorb surplus export in simple blocks."
    elif domain == "light" and kind == "fixed":
        summary = "Light entities can be controllable, but many are comfort or presence loads rather than discretionary energy sinks."
        suitability_summary = "Light control can work technically, but it needs review because many lights are comfort loads rather than intentional energy sinks."
        operational_value_summary = "Operational value is uncertain unless this light really represents a discretionary load the operator is happy to cycle."
        warnings.append(
            "Confirm this light is a real discretionary load, not a normal lighting circuit people expect to stay manual."
        )
    elif domain == "input_boolean" and kind == "fixed":
        confidence = "low"
        summary = "Helpers can represent automation intent, not a physical load."
        suitability_summary = "Helper booleans are a weak control fit because they often represent intent or automation state instead of a directly controllable appliance."
        safety_summary = "Confidence is low until you verify this helper really drives a safe physical load instead of only toggling logic."
        operational_value_summary = "Operational value is low unless this helper clearly maps to a meaningful real-world load behind the scenes."
        warnings.append(
            "This is an input_boolean helper. Verify it really drives a safe controllable load before promoting it."
        )
    elif domain in {"number", "input_number"} and kind == "variable":
        confidence = "high" if domain == "number" else "medium"
        summary = "Number-style entities are strong variable-load candidates when they represent a real power or current target."
        suitability_summary = "Writable number entities are a strong fit for variable control when they directly represent power, current, or another real throttling target."
        operational_value_summary = "Variable loads often provide strong operational value because they can track export more smoothly than simple on/off loads."
        if domain == "input_number":
            safety_summary = "Confidence is only moderate for helpers until you confirm this input_number actually drives a real device and is not just a dashboard helper."
            warnings.append(
                "This is an input_number helper. Check that changing it actually drives a real device, not just a dashboard helper."
            )

    if positive_name_signal:
        if confidence == "medium":
            confidence = "high"
        operational_value_summary = "The entity name suggests a real discretionary load, so it looks more likely to matter operationally once promoted."

    if negative_name_signal:
        warnings.append(
            "The entity name looks more like a service, media feature, or software toggle than a discretionary power load. Confirm it really controls a real appliance before promotion."
        )
        if confidence == "high":
            confidence = "medium"
        elif confidence == "medium":
            confidence = "low"
        suitability_summary = "The native control shape may still work, but the entity name suggests this could be a feature toggle or service control instead of a real appliance."
        safety_summary = "Confidence is lower because the entity name does not clearly look like a physical discretionary load yet."
        operational_value_summary = "Operational value is doubtful until you confirm this entity maps to a real export-absorbing device rather than software behaviour."

    if raw_state in {"unknown", "unavailable"}:
        warnings.append(f"Entity state is currently {raw_state}. Promotion is risky until it reports cleanly.")
        confidence = "low"
        safety_summary = f"Confidence is low because the entity is currently {raw_state}; wait for a clean live state before trusting it as a managed device."

    if kind == "variable" and not unit:
        warnings.append("Variable candidates are safer when the entity exposes a meaningful unit such as A, W, or %.")
        if confidence == "high":
            confidence = "medium"
        suitability_summary = "Variable control still looks plausible, but it needs extra review because the entity does not expose a clear unit such as A, W, or %."

    if kind == "variable" and device_class == "battery":
        warnings.append("Battery-class entities are often telemetry, not safe control targets. Confirm this is a writable control entity.")
        confidence = "low"
        safety_summary = "Confidence is low because battery-class entities are often telemetry sensors rather than safe writable controls."
        operational_value_summary = "Operational value is unclear until you confirm this entity is a real control target instead of battery telemetry."

    if not warnings and confidence == "high":
        safety_summary = "No immediate warning stands out in the current metadata, so this candidate looks safe enough to review and promote if the operator recognizes the load."

    return {
        "confidence": confidence,
        "summary": summary,
        "warnings": warnings,
        "suitability_level": "high" if confidence == "high" else "medium" if domain not in {"input_boolean"} else "low",
        "suitability_summary": suitability_summary,
        "safety_level": confidence,
        "safety_summary": safety_summary,
        "operational_value_level": (
            "high"
            if (domain == "switch" and kind == "fixed") or (domain == "number" and kind == "variable")
            else "medium"
            if domain in {"light", "input_number"}
            else "low"
        ),
        "operational_value_summary": operational_value_summary,
    }


def build_candidate_review_line(label: str, level: str, summary: str) -> str:
    """Return a concise structured review line for candidate vetting."""
    level_label = _REVIEW_LEVEL_LABELS.get(str(level or "").lower(), str(level or "review"))
    return f"{label}: {level_label} - {summary}"


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


def build_candidate_overview_summary(
    candidates: Iterable[dict[str, Any]],
    *,
    max_chars: int = 240,
) -> str:
    """Return a compact managed-vs-unmanaged snapshot distinct from the shortlist."""
    candidate_list = list(candidates)
    if not candidate_list:
        return "No unmanaged candidate devices discovered"

    fixed_count = sum(1 for item in candidate_list if str(item.get("kind") or "") == "fixed")
    variable_count = sum(1 for item in candidate_list if str(item.get("kind") or "") == "variable")
    top_name = str(candidate_list[0].get("name") or candidate_list[0].get("entity_id") or "").strip()
    summary_parts = [f"{len(candidate_list)} candidates", f"{fixed_count} fixed"]
    if variable_count:
        summary_parts.append(f"{variable_count} variable")
    if top_name:
        summary_parts.append(f"top {top_name}")

    summary = " | ".join(summary_parts)
    while len(summary_parts) > 2 and len(summary) > max_chars:
        summary_parts.pop()
        summary = " | ".join(summary_parts)

    if len(summary) <= max_chars:
        return summary
    return summary[: max_chars - 1].rstrip() + "…"


def discover_candidate_devices(states: Iterable[Any], managed_entity_ids: set[str]) -> list[dict[str, str]]:
    """Return unmanaged controllable-device candidates in promotion order."""
    candidates: list[dict[str, str]] = []
    for state in states:
        entity_id = getattr(state, "entity_id", "")
        domain, _, object_id = entity_id.partition(".")
        if domain not in DEVICE_CANDIDATE_DOMAINS:
            continue
        if entity_id in managed_entity_ids:
            continue
        if object_id.startswith(f"{DOMAIN}_"):
            continue
        state_value = str(getattr(state, "state", "")).lower()
        if state_value in {"unknown", "unavailable"}:
            continue
        attributes = getattr(state, "attributes", {}) or {}
        candidate = {
            "entity_id": entity_id,
            "name": str(attributes.get("friendly_name") or entity_id),
            "domain": domain,
            "kind": "fixed" if domain in DEVICE_CANDIDATE_FIXED_DOMAINS else "variable",
            "state": str(getattr(state, "state", "")),
            "unit": str(attributes.get("unit_of_measurement") or ""),
            "device_class": str(attributes.get("device_class") or ""),
        }
        if _should_exclude_candidate(candidate):
            continue
        candidates.append(candidate)
    return rank_candidates(candidates)
