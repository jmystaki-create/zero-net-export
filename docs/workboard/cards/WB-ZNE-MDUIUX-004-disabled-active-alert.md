# WB-ZNE-MDUIUX-004 Disabled Active Load Alert

Status: done
Priority: high
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md` / Managed Devices Tab UI/UX Review

## Outcome

Disabled Active Load Alert is implemented or explicitly resolved for the Managed Devices load-aware fleet console.

## Acceptance Criteria

- [x] Detect managed devices that are observed active while disabled.
- [x] Show aggregate disabled-active watts near the top.
- [x] Name the first affected device.
- [x] Do not imply ZNE caused the state or bypass enable/disable guards.

## Validation

- [x] Source/test evidence covers this card.
- [ ] Browser/live proof remains tracked by `WB-ZNE-MDUIUX-010` before release closeout.
- [x] No unrelated control behavior changes are introduced.

## Implementation Note

Completed in the first frontend implementation slice. Release/live browser proof remains tracked by `WB-ZNE-MDUIUX-010`.
