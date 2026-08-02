# WB-ZNE-MDUIUX-006 Candidate Queue Load Awareness

Status: done
Priority: normal
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md` / Managed Devices Tab UI/UX Review

## Outcome

Candidate Queue Load Awareness is implemented or explicitly resolved for the Managed Devices load-aware fleet console.

## Acceptance Criteria

- [x] Preserve candidate review and promotion.
- [x] Assess whether reliable candidate watt estimates are available.
- [x] If reliable, show estimated/configured watts in candidate rows.
- [x] If not reliable, document backend requirement instead of guessing.

## Validation

- [x] Source/test evidence covers this card.
- [ ] Browser/live validation is captured when the card changes rendered UI or live HA state visibility.
- [x] No unrelated control behavior changes are introduced.

## Resolution

Implemented a conservative candidate `Load` column. It shows measured/supplied watts when the candidate payload exposes reliable watt metadata, converts W/kW entity states when the candidate entity itself reports power, and otherwise shows `Set in review` with copy that watts must be confirmed before promotion.
