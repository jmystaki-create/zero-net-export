# WB-ZNE-MDUIUX-009 Optional Backend Aggregate Sensors

Status: done
Priority: normal
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md` / Managed Devices Tab UI/UX Review

## Outcome

Optional Backend Aggregate Sensors is implemented or explicitly resolved for the Managed Devices load-aware fleet console.

## Acceptance Criteria

- [x] Add backend aggregate sensors only if frontend derivation is insufficient.
- [x] Define aggregate semantics before implementation.
- [x] Protect recorder attribute budget.
- [x] Keep entity/device page visibility intentional.

## Validation

- [x] Source/test evidence covers this card.
- [ ] Browser/live validation is captured when the card changes rendered UI or live HA state visibility.
- [x] No unrelated control behavior changes are introduced.

## Resolution

Resolved as frontend-derived for this release. Existing `sensor.managed_devices_overview` attributes and per-device managed fleet payloads provide enough information for the dashboard without adding new recorder-visible backend sensors. Backend aggregate sensors should only be reconsidered if multiple HA surfaces need the same metrics outside the sidebar app.
