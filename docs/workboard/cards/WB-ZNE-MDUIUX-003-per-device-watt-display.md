# WB-ZNE-MDUIUX-003 Per-Device Watt Display

Status: done
Priority: high
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md` / Managed Devices Tab UI/UX Review

## Outcome

Per-Device Watt Display is implemented or explicitly resolved for the Managed Devices load-aware fleet console.

## Acceptance Criteria

- [x] Every managed-device row displays watt impact.
- [x] Use `current_power_w` when available.
- [x] Fallback to estimated active nominal watts when observed active and measured watts are missing.
- [x] Show nominal watts as secondary context.

## Validation

- [x] Source/test evidence covers this card.
- [ ] Browser/live proof remains tracked by `WB-ZNE-MDUIUX-010` before release closeout.
- [x] No unrelated control behavior changes are introduced.

## Implementation Note

Completed in the first frontend implementation slice. Release/live browser proof remains tracked by `WB-ZNE-MDUIUX-010`.
