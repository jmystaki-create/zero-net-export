# WB-ZNE-015 Promotion Confirmation Regression

Status: Doing
Priority: High
Labels: bug, managed-devices, app-frontend, validation, release

## Purpose

Track `ZNE-599`, the live Managed Devices regression where an unmanaged
candidate can be opened for review, but the confirmation checkbox does not stay
pressed and the candidate is not added to the managed Fleet List.

## Linked Bug

- `ZNE-599` - Promote confirmation does not add unmanaged candidate to managed
  fleet.

## User Outcome

Operators can review an unmanaged candidate, explicitly confirm promotion, and
see the load appear in the managed Fleet List without changing or removing the
original Home Assistant entity/device.

## Observed Behavior

On installed `v0.4.12`, Riley reported that clicking the confirmation checkbox
in the `Review & promote` workflow does not keep the tick pressed, and clicking
`Promote to fleet` does not add the candidate to the managed list. Screenshot
evidence shows `Lounge Room - Heated Floor` / `switch.ac_outlet_1` selected as
`Reviewing` in the unmanaged queue, with the review form open above the table.

## Current Implementation State

A local frontend fix now persists promotion draft values and the required
confirmation checkbox state on the custom element, so Home Assistant app
re-renders should not clear the tick before `Promote to fleet` submits. The
submit path remains the app-owned backend service
`zero_net_export.promote_managed_device` with `confirm: true`; the original Home
Assistant entity/device is not mutated by the app.

Focused validation passed:

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- `python3 -m unittest tests.test_managed_devices_panel -v` (`23` tests)
- `git diff --check`

## Acceptance Criteria

- The confirmation checkbox toggles reliably and remains checked until the form
  is cancelled, submitted, or another candidate is selected.
- `Promote to fleet` is blocked until confirmation is checked and required form
  values are valid.
- A confirmed submit creates the managed load through the supported app/backend
  path.
- The promoted candidate appears in the managed Fleet List.
- The promoted candidate no longer appears as a ready unmanaged candidate.
- The original Home Assistant entity/device remains present and unmodified.
- Regression tests cover the confirmation gate and successful promotion flow.

## Validation Plan

1. Run broader repo validation.
2. Release through GitHub/HACS after explicit approval.
3. Restart Home Assistant and validate a safe
   unmanaged candidate promotion with browser/API proof and targeted log review.

## Next Actions

1. Complete broader validation and release preparation for the local fix.
2. Use a safe candidate such as `switch.ac_outlet_1` or another disposable load
   for live validation.
