# WB-ZNE-UIUX-005 Diagnostics And Raw Detail Preservation

Status: done
Priority: high
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md`

## Outcome

Overview copy becomes operator-friendly while Diagnostics keeps raw troubleshooting detail.

## Review Coverage

- Product Constraints To Preserve
- Key UX Finding 5
- Recommended Direction 5
- Functionality Risk Review: losing troubleshooting detail
- Validation Plan: Diagnostics proof

## Acceptance Criteria

- [x] Move raw enum strings, long entity IDs, source-role internals, and low-level labels out of the primary Overview reading path.
- [x] Keep raw values accessible through Diagnostics, details drawers, or secondary metadata.
- [x] Do not remove troubleshooting data from the app.
- [x] Support/debug workflows remain at least as capable as before.

## Validation

- [x] Browser proof that Overview no longer leads with raw internals.
- [x] Browser proof that Diagnostics still exposes raw values needed for troubleshooting.
- [x] Targeted logs if Diagnostics rendering errors are suspected.

## Functional Safety

- Preserve existing tabs, data sources, service wiring, plan context, Diagnostics access, and confirmation gates unless a separate accepted design changes them.

## Implementation Note

Repo implementation is complete for this card as part of the 2026-08-02 Overview UI/UX refactor. Live HACS/browser proof remains tracked by `WB-ZNE-UIUX-010`.
