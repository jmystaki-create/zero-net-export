"""Managed-device candidate discovery helpers for native HA surfaces."""
from __future__ import annotations

import re
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
    "high": "likely useful",
    "medium": "possible fit",
    "low": "review carefully",
}


def candidate_usefulness_label(fit: dict[str, Any]) -> str:
    """Return the operator-facing usefulness label for a candidate fit."""
    confidence = str(fit.get("confidence") or "medium")
    warnings = [str(item).strip() for item in (fit.get("warnings") or []) if str(item).strip()]
    if confidence == "medium" and warnings:
        return "review first"
    return _FIT_USEFULNESS_LABELS.get(confidence, confidence)


def candidate_needs_review(fit: dict[str, Any]) -> bool:
    """Return True when the candidate still needs explicit operator review."""
    return candidate_usefulness_label(fit) != "likely useful"


def first_review_candidate(candidates: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the first surfaced candidate that still needs explicit review."""
    for candidate in candidates:
        if candidate_needs_review(assess_candidate(candidate)):
            return candidate
    return None


def candidate_review_kind_counts(candidates: Iterable[dict[str, Any]]) -> tuple[int, int]:
    """Return fixed and variable review-first counts for the surfaced candidates."""
    fixed_review_count = 0
    variable_review_count = 0
    for candidate in candidates:
        if not candidate_needs_review(assess_candidate(candidate)):
            continue
        if str(candidate.get("kind") or "") == "variable":
            variable_review_count += 1
        else:
            fixed_review_count += 1
    return fixed_review_count, variable_review_count


def format_count_label(count: int, singular: str, plural: str | None = None) -> str:
    """Return a compact count label with correct singular/plural wording."""
    if plural is None:
        plural = f"{singular}s"
    noun = singular if count == 1 else plural
    return f"{count} {noun}"


def _truncate_summary(text: str, *, max_chars: int) -> str:
    normalized = " ".join(str(text or "").split()).strip()
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 1].rstrip() + "…"

_REVIEW_LEVEL_LABELS = {
    "high": "strong",
    "medium": "review",
    "low": "caution",
}

_POSITIVE_LOAD_KEYWORDS = (
    "charger",
    "ev",
    "heater",
    "heated floor",
    "floor heat",
    "hot water",
    "water heater",
    "boiler",
    "geyser",
    "pool",
    "pump",
    "outlet",
    "plug",
    "purifier",
    "towel rail",
    "coffee",
    "dishwasher",
    "aircon",
    "air conditioner",
    "ac unit",
    "hvac",
)

_APPLIANCE_STYLE_KEYWORDS = tuple(
    keyword for keyword in _POSITIVE_LOAD_KEYWORDS if keyword not in {"outlet", "plug"}
)

_FALSE_POSITIVE_LOAD_PHRASES = (
    "ac outlet",
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
    "child lock",
    "childlock",
    "eco dry",
    "exhaust fan",
    "range hood",
    "hood power",
    "shellyproem",
)

_NEGATIVE_ENTITY_ID_FRAGMENTS = (
    "_none",
    "_speech_enhancement",
    "_subwoofer",
    "_exhaust_fan",
    "_hood_power",
)

_GENERIC_POWER_KEYWORDS = (
    " power",
    "power ",
)

_LIGHTING_KEYWORDS = (
    " light",
    " lights",
    "lamp",
    "downlight",
    "spotlight",
    "led",
)

_EXCLUDED_DEVICE_CLASSES = {
    "energy_storage",
    "temperature",
}

_EXCLUDED_VARIABLE_KEYWORDS = (
    "audio delay",
    "auto-relock",
    "auto relock",
    "balance",
    "bass",
    "battery capacity",
    "buy price",
    "dyn. price",
    "music surround level",
    "price fee",
    "price vat",
    "sell price",
    "start in relative",
    "sub gain",
    "surround level",
    "tax percent",
    "temperature limit",
    "treble",
)

_EXCLUDED_VARIABLE_ENTITY_ID_FRAGMENTS = (
    "_auto_relock",
    "_battery_capacity",
    "_buy_price",
    "_dyn_price_",
    "_sell_price",
    "_start_in_relative",
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


def _normalized_candidate_name(candidate: dict[str, Any]) -> str:
    """Return a normalized candidate label for cross-surface duplicate detection."""
    name = str(candidate.get("name") or candidate.get("entity_id") or "").lower().replace("-", " ")
    return re.sub(r"[^a-z0-9]+", " ", name).strip()


def _has_positive_load_signal(candidate: dict[str, Any]) -> bool:
    text = _candidate_text(candidate)
    if any(phrase in text for phrase in _FALSE_POSITIVE_LOAD_PHRASES):
        text = " ".join(part for part in text.split() if part not in {"ac", "outlet"})
    return any(keyword in text for keyword in _POSITIVE_LOAD_KEYWORDS)


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


def _generic_power_penalty(candidate: dict[str, Any]) -> int:
    """Return a mild penalty for vague room/circuit power labels.

    These are still plausible candidates, but they should rank behind more explicit
    appliance-style names like chargers, heated floors, towel rails, and purifiers.
    """
    text = _candidate_text(candidate)
    name_text = str(candidate.get("name") or "").lower()
    if not any(keyword in text for keyword in _GENERIC_POWER_KEYWORDS):
        return 0
    if _has_positive_load_signal(candidate):
        return 0
    if str(candidate.get("device_class") or "").lower() == "outlet":
        return 0
    return 1


def _anonymous_outlet_penalty(candidate: dict[str, Any]) -> int:
    """Return a mild penalty for numbered outlet/plug labels with no appliance context.

    Generic outlet hardware names are still plausible fixed-load candidates, but they
    should rank behind entities whose friendly names already identify a real appliance.
    """
    name_text = str(candidate.get("name") or "").lower().strip()
    entity_id = str(candidate.get("entity_id") or "").lower()
    combined_text = f"{name_text} {entity_id}".strip()
    looks_like_outlet = (
        str(candidate.get("device_class") or "").lower() == "outlet"
        or "outlet" in combined_text
        or "plug" in combined_text
    )
    if not looks_like_outlet:
        return 0
    if any(keyword in combined_text for keyword in _APPLIANCE_STYLE_KEYWORDS):
        return 0
    if any(char.isdigit() for char in combined_text):
        return 2
    return 1


def _candidate_desirability_rank(candidate: dict[str, Any]) -> int:
    """Return a secondary rank that prefers likely real loads over obvious service toggles."""
    text = _candidate_text(candidate)
    score = 0
    if _has_positive_load_signal(candidate):
        score -= 2
    score += _negative_non_load_penalty(candidate)
    score += _generic_power_penalty(candidate)
    score += _anonymous_outlet_penalty(candidate)
    if str(candidate.get("device_class") or "").lower() == "outlet":
        score -= 1
    return score


def _looks_like_lighting_candidate(candidate: dict[str, Any]) -> bool:
    text = _candidate_text(candidate)
    entity_id = str(candidate.get("entity_id") or "").lower().replace("_", " ")
    return any(keyword in text or keyword in entity_id for keyword in _LIGHTING_KEYWORDS)



def _should_exclude_candidate(candidate: dict[str, Any]) -> bool:
    """Return True when an entity is clearly not a real managed-load promotion target."""
    domain = str(candidate.get("domain") or "")
    kind = str(candidate.get("kind") or "")
    text = _candidate_text(candidate)
    entity_id = str(candidate.get("entity_id") or "").lower()
    device_class = str(candidate.get("device_class") or "").lower()
    positive_name_signal = _has_positive_load_signal(candidate)

    if domain == "light" and not positive_name_signal:
        return True

    if domain in DEVICE_CANDIDATE_FIXED_DOMAINS and _looks_like_lighting_candidate(candidate) and not positive_name_signal:
        return True

    if domain in DEVICE_CANDIDATE_FIXED_DOMAINS and _negative_non_load_penalty(candidate) >= 3:
        return True

    if domain in DEVICE_CANDIDATE_FIXED_DOMAINS and any(fragment in entity_id for fragment in _NEGATIVE_ENTITY_ID_FRAGMENTS):
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


def _deduplicate_shadowed_helper_candidates(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop helper duplicates when a stronger native candidate already names the same load.

    Helper-backed entities can be useful fallbacks, but when the same load already has a
    native switch/light/number candidate with the same friendly label they mostly add noise
    to Managed Devices promotion lists and make the managed-versus-unmanaged split less clear.
    """
    candidate_list = list(candidates)
    non_helper_names = {
        _normalized_candidate_name(candidate)
        for candidate in candidate_list
        if str(candidate.get("domain") or "") not in {"input_boolean", "input_number"}
    }
    return [
        candidate
        for candidate in candidate_list
        if not (
            str(candidate.get("domain") or "") in {"input_boolean", "input_number"}
            and _normalized_candidate_name(candidate) in non_helper_names
        )
    ]


def _degrade_confidence(current: str) -> str:
    if current == "high":
        return "medium"
    if current == "medium":
        return "low"
    return current



def assess_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Return shared fit guidance for a discovered unmanaged candidate."""
    domain = str(candidate.get("domain") or "")
    kind = str(candidate.get("kind") or ("fixed" if domain in DEVICE_CANDIDATE_FIXED_DOMAINS else "variable"))
    raw_state = str(candidate.get("state") or "").strip().lower()
    unit = str(candidate.get("unit") or "")
    device_class = str(candidate.get("device_class") or "")

    confidence = "medium"
    summary = "Looks like a potentially useful controllable candidate, but review before promotion."
    warnings: list[str] = []
    suitability_summary = "The entity shape looks workable for Zero Net Export, but it still needs operator review before promotion."
    safety_summary = "No obvious safety blocker is visible yet, but confirm the entity really controls the intended device."
    operational_value_summary = "This candidate could help absorb export, but confirm it represents a meaningful discretionary load."

    candidate_text = _candidate_text(candidate)
    positive_name_signal = _has_positive_load_signal(candidate)
    negative_name_signal = _has_negative_non_load_signal(candidate)
    generic_power_signal = _generic_power_penalty(candidate) > 0
    anonymous_outlet_signal = _anonymous_outlet_penalty(candidate) > 0

    if domain == "switch" and kind == "fixed":
        confidence = "high"
        summary = "Switch entities are usually likely fixed-load candidates when they control a real appliance or relay."
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
        summary = "Number-style entities are usually likely variable-load candidates when they represent a real power or current target."
        suitability_summary = "Writable number entities are usually a good native fit for variable control when they directly represent power, current, or another real throttling target."
        operational_value_summary = "Variable loads often provide good operational value because they can track export more smoothly than simple on/off loads."
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
        confidence = _degrade_confidence(confidence)
        suitability_summary = "The native control shape may still work, but the entity name suggests this could be a feature toggle or service control instead of a real appliance."
        safety_summary = "Confidence is lower because the entity name does not clearly look like a physical discretionary load yet."
        operational_value_summary = "Operational value is doubtful until you confirm this entity maps to a real export-absorbing device rather than software behaviour."

    if generic_power_signal:
        warnings.append(
            "The label is still generic power/circuit wording. Confirm this is a real discretionary appliance or circuit you actually want Zero Net Export to control."
        )
        confidence = _degrade_confidence(confidence)
        suitability_summary = "The control shape may still work, but the name is generic enough that it could be a broad room circuit rather than a clearly intentional managed load."
        safety_summary = "Confidence is lower until the operator confirms this generic power label really maps to the intended controllable appliance or circuit."
        operational_value_summary = "Operational value is still plausible, but generic circuit labels usually need extra review because they do not clearly say which load will absorb export."

    if anonymous_outlet_signal:
        warnings.append(
            "The label still looks like generic outlet hardware rather than a named appliance. Confirm what is plugged into it before promotion."
        )
        confidence = _degrade_confidence(confidence)
        suitability_summary = "Outlet control is technically workable, but anonymous outlet labels need extra review because they do not identify the real appliance behind the relay."
        safety_summary = "Confidence is lower until the operator confirms which appliance this outlet actually controls and whether it is safe to cycle automatically."
        operational_value_summary = "Operational value depends on the real appliance behind the outlet, so generic numbered plugs should be reviewed before treating them as first-choice promotion targets."

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

    helper_confidence_cap = {
        "input_boolean": "low",
        "input_number": "medium",
    }.get(domain)
    if helper_confidence_cap == "medium" and confidence == "high":
        confidence = "medium"
        safety_summary = "Helper-backed variable control still needs extra review because the entity may be a dashboard or automation helper rather than the device's native control surface."
        operational_value_summary = "Operational value can still be good, but helper-backed variable controls should stay review-first until the operator confirms they directly drive the real load."
    elif helper_confidence_cap == "low" and confidence != "low":
        confidence = "low"
        safety_summary = "Helper-backed control stays low-confidence until the operator confirms it directly drives a safe physical load."
        operational_value_summary = "Operational value stays uncertain until the helper is confirmed to control a meaningful real-world load."

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


def build_candidate_usefulness_summary(candidate: dict[str, Any]) -> str:
    """Return an operator-facing usefulness plus explanation line."""
    fit = assess_candidate(candidate)
    usefulness = candidate_usefulness_label(fit)
    summary = str(fit.get("summary") or "Looks like a potentially useful controllable candidate, but review before promotion.")
    return f"{usefulness}: {summary}"


def build_candidate_review_hint(
    candidate: dict[str, Any],
    *,
    include_warning: bool = True,
    max_warning_chars: int = 56,
) -> str:
    """Return a compact usefulness-plus-warning hint for dense unmanaged snapshots."""
    fit = assess_candidate(candidate)
    usefulness = candidate_usefulness_label(fit)
    if not include_warning:
        return usefulness

    warnings = [str(item).strip() for item in (fit.get("warnings") or []) if str(item).strip()]
    if not warnings:
        return usefulness

    warning = _truncate_summary(warnings[0], max_chars=max_warning_chars)
    return f"{usefulness} | warn {warning}"


def build_candidate_compact_preview(
    candidate: dict[str, Any],
    *,
    include_warning: bool = True,
    max_warning_chars: int = 36,
) -> str:
    """Return a short operator-facing candidate label for dense fleet summaries."""
    name = str(candidate.get("name") or candidate.get("entity_id") or "candidate").strip()
    kind = str(candidate.get("kind") or "unknown").strip()
    heading = name if not kind else f"{name} ({kind})"
    detail_bits = [build_candidate_review_hint(candidate, include_warning=False)]
    if include_warning:
        warning = _compact_candidate_warning(candidate, max_chars=max_warning_chars)
        if warning:
            detail_bits.append(f"warn {warning}")
    detail = " | ".join(bit for bit in detail_bits if bit)
    return f"{heading} | {detail}" if detail else heading


def build_candidate_preview(
    candidate: dict[str, Any],
    *,
    include_entity_id: bool = True,
    include_kind: bool = True,
    include_state: bool = False,
) -> str:
    """Return a concise operator-facing preview for unmanaged candidate rows."""
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
    review_hint = build_candidate_review_hint(candidate, include_warning=True, max_warning_chars=96)
    key_warning = "No immediate warnings"
    if " | warn " in review_hint:
        _, _, warning = review_hint.partition(" | warn ")
        key_warning = warning
    usefulness = build_candidate_review_hint(candidate, include_warning=False)

    return f"{heading} | {usefulness} | key warning: {key_warning}"


def _compact_candidate_warning(candidate: dict[str, Any], *, max_chars: int = 28) -> str:
    """Return a shortlist-friendly warning label for dense unmanaged rows."""
    warnings = [str(item).strip() for item in (assess_candidate(candidate).get("warnings") or []) if str(item).strip()]
    if not warnings:
        return ""

    warning = warnings[0].lower()
    if "input_number helper" in warning or "input_boolean helper" in warning:
        return "helper-backed"
    if "generic outlet hardware" in warning:
        return "generic outlet label"
    if "generic power/circuit wording" in warning:
        return "generic circuit label"
    if "service, media feature, or software toggle" in warning:
        return "service-style label"
    if "meaningful unit" in warning:
        return "missing clear unit"
    if "light is a real discretionary load" in warning:
        return "lighting load"
    return _truncate_summary(warnings[0], max_chars=max_chars)



def build_candidate_name_summary(
    candidates: Iterable[dict[str, Any]],
    *,
    limit: int = 3,
    max_chars: int = 240,
) -> str:
    """Return a compact shortlist summary with kind, usefulness, and key warning hints."""
    candidate_list = list(candidates)
    if not candidate_list:
        return "None"

    summary_parts = []
    for item in candidate_list[:limit]:
        name = str(item.get('name') or item.get('entity_id') or '').strip()
        if not name:
            continue
        detail = f"{str(item.get('kind') or 'candidate')} | {build_candidate_review_hint(item, include_warning=False)}"
        warning = _compact_candidate_warning(item)
        if warning:
            detail += f" | {warning}"
        summary_parts.append(f"{name} ({detail})")
    remainder = len(candidate_list) - min(len(candidate_list), limit)
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


def build_candidate_fit_summary(
    candidates: Iterable[dict[str, Any]],
    *,
    limit: int = 3,
    max_chars: int = 240,
) -> str:
    """Return shortlist fit guidance with compact warning hints when needed."""
    candidate_list = list(candidates)
    if not candidate_list:
        return "No shortlist fit guidance"

    summary_parts = [
        (
            f"{str(item.get('name') or item.get('entity_id') or 'candidate').strip()}: "
            f"{build_candidate_review_hint(item, include_warning=True, max_warning_chars=40)}"
        ).strip()
        for item in candidate_list[:limit]
        if str(item.get('name') or item.get('entity_id') or '').strip()
    ]
    remainder = len(candidate_list) - min(len(candidate_list), limit)
    if remainder > 0:
        summary_parts.append(f"+{remainder} more")

    summary = "; ".join(summary_parts) or "No shortlist fit guidance"
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
    include_top_review_hint: bool = True,
) -> str:
    """Return a compact managed-vs-unmanaged snapshot distinct from the shortlist."""
    candidate_list = list(candidates)
    if not candidate_list:
        return "No unmanaged candidate devices discovered"

    fixed_count = sum(1 for item in candidate_list if str(item.get("kind") or "") == "fixed")
    variable_count = sum(1 for item in candidate_list if str(item.get("kind") or "") == "variable")
    review_needed_count = sum(1 for item in candidate_list if candidate_needs_review(assess_candidate(item)))
    ready_candidate_count = max(len(candidate_list) - review_needed_count, 0)
    fixed_review_count, variable_review_count = candidate_review_kind_counts(candidate_list)
    review_candidate = first_review_candidate(candidate_list)
    review_candidate_name = str((review_candidate or {}).get("name") or (review_candidate or {}).get("entity_id") or "").strip()
    top_name = str(candidate_list[0].get("name") or candidate_list[0].get("entity_id") or "").strip()
    summary_parts = [format_count_label(len(candidate_list), "candidate")]
    if fixed_count:
        summary_parts.append(format_count_label(fixed_count, "fixed candidate"))
    if variable_count:
        summary_parts.append(format_count_label(variable_count, "variable candidate"))
    if review_needed_count:
        summary_parts.append("1 needs review" if review_needed_count == 1 else f"{review_needed_count} need review")
        if fixed_review_count:
            summary_parts.append(format_count_label(fixed_review_count, "fixed review"))
        if variable_review_count:
            summary_parts.append(format_count_label(variable_review_count, "variable review"))
        if review_candidate_name and review_candidate_name != top_name:
            summary_parts.append(f"review {review_candidate_name}")
            summary_parts.append(build_candidate_review_hint(review_candidate))
    if ready_candidate_count:
        summary_parts.append(
            "1 ready to promote"
            if ready_candidate_count == 1
            else f"{ready_candidate_count} ready to promote"
        )
    if top_name:
        summary_parts.append(f"top {top_name}")
    if include_top_review_hint and candidate_list:
        summary_parts.append(build_candidate_review_hint(candidate_list[0]))

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
    return rank_candidates(_deduplicate_shadowed_helper_candidates(candidates))
