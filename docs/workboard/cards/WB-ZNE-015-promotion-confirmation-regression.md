# WB-ZNE-015 Promotion Confirmation Regression

Status: Done
Priority: High
Labels: bug, managed-devices, app-frontend, validation, release, released-live-validated

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

## Result

Released/live validated in `v0.4.15`.

The final fix spans the full app/backend promotion path:

- promotion draft values and confirmation state persist on the custom element
  across Home Assistant app re-renders;
- confirmed submit stays on `zero_net_export.promote_managed_device` with
  `confirm: true`;
- backend service schemas coerce UI numeric payloads before validation;
- the Fleet List sorts/filters numeric managed-device priority values without a
  frontend render error.

Live proof promoted `switch.ac_outlet_1` to managed key
`lounge_room_heated_floor` with `enabled: false`, preserved the original Home
Assistant entity, removed the switch from the unmanaged queue, and rendered the
managed Fleet List in a fresh `v0.4.15` browser tab with no console errors.

Evidence: `validation/0.4.15-release-validation.md`.

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

## Validation Completed

- `python3 -m unittest discover -s tests -v` passed (`641` tests).
- Focused release tests passed (`87` tests).
- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js` passed.
- `python3 -m compileall -q custom_components/zero_net_export tests scripts` passed.
- `git diff --check` passed.
- GitHub/HACS release `v0.4.15` installed, Home Assistant restarted, and install
  fingerprints matched before and after restart.
- Live browser/API validation confirmed the promotion result and clean fresh
  console.

## Next Actions

No further `ZNE-599` action. Continue with the focused read-only installed
`ZNE-597` Battery Power/source-reading unit proof, then choose the next app
workflow slice.
