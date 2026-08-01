# WB-ZNE-UIUX-003 Live Power Snapshot

Status: todo
Priority: high
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md`

## Outcome

The Overview presents reconciliation values as a fast scannable power snapshot while preserving existing source data.

## Review Coverage

- Live Page Observations: reconciliation values
- Learnings Summary item 4
- Key UX Finding 3
- Recommended Direction 3
- What I Would Not Change Yet

## Acceptance Criteria

- [ ] Show Home Load, Source/Solar, Battery, Grid/Surplus, Reconciliation Error, and Confidence as compact snapshot metrics.
- [ ] Preserve existing units and source values; this is presentation-only unless a data gap is proven.
- [ ] Battery charging/discharging direction is translated into operator language.
- [ ] Raw entity/source detail remains available through Diagnostics or details.

## Validation

- [ ] Browser proof that live values are visible and scannable on desktop.
- [ ] Browser proof that values remain visible on narrow/mobile width.
- [ ] Focused check that displayed values remain numerically consistent with source states.

## Functional Safety

- Preserve existing tabs, data sources, service wiring, plan context, Diagnostics access, and confirmation gates unless a separate accepted design changes them.

## Implementation Note

Repo implementation is complete for this card as part of the 2026-08-02 Overview UI/UX refactor. Live HACS/browser proof remains tracked by `WB-ZNE-UIUX-010`.
