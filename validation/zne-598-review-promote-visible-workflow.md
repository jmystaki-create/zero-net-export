# ZNE-598 Review Promote Visible Workflow

Date: 2026-07-13
Status: fixed in repo, pending release/live validation

## Request

Riley reported that clicking `Review & promote` on the Managed Devices
Unmanaged Candidate Queue did not perform any clear action, and asked for
validation with Slave.

## Classification

- Type: bug
- Area: Managed Devices application UI
- Installed version observed: `v0.4.10`
- Target environment: Home Assistant sidebar app served through the Zero Net
  Export integration frontend module

## Acceptance Criteria

- Clicking `Review & promote` immediately exposes the selected candidate's
  review/promotion workflow.
- The selected candidate row has visible state feedback.
- Keyboard/scroll focus moves to the review workflow so it is not hidden below a
  long unmanaged candidate list.
- Existing promotion confirmation and `zero_net_export.promote_managed_device`
  service behavior remain unchanged.

## Live Slave Validation

- Browser node: Slave Debian Browser Node.
- Page:
  `http://192.168.86.200:8123/zero-net-export?validation=zne-fr-017-v0410-promotion`
- Header showed `Version 0.4.10`.
- Managed Devices showed `Unmanaged Candidate Queue` with `Review & promote`
  buttons.
- First candidate: `Lounge Room - Heated Floor`, `switch.ac_outlet_1`.
- Result: after the click attempt, the visible page still showed the unmanaged
  queue and no clear review workflow above the fold.
- Browser console check on the installed app returned no error messages.

Verdict: live installed `v0.4.10` reproduces the user-visible problem.

## Cause

The selected candidate review panel was rendered after the entire unmanaged
candidate table. On a long queue, selecting the first row could update state
without exposing the review panel in the visible viewport, making the button
look like a no-op.

## Fix

- Render the candidate promotion panel above the unmanaged candidate table.
- Add `data-zne-promotion-panel` and `tabindex="-1"` so the app can focus the
  workflow.
- After selecting a candidate, focus and scroll the panel into view.
- Mark the selected candidate row and change its action button label to
  `Reviewing`.

## Repo Validation

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
  - Result: PASS
- `python3 -m unittest -v tests.test_managed_devices_panel`
  - Result: PASS, 23 tests
- `git diff --check`
  - Result: PASS
- `python3 -m unittest discover -v`
  - Result: PASS, 637 tests

## Release / Live Validation Pending

This is fixed in repo only. Live validation requires a GitHub/HACS release,
Home Assistant restart, install fingerprint check, and Slave browser proof that
clicking `Review & promote` visibly opens and focuses the review workflow.
