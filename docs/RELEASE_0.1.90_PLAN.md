# Zero Net Export 0.1.90 Release Plan

## Purpose

`0.1.90` is the corrective release for the live `0.1.89` device-page Managed Devices visibility failure.

`0.1.89` was successfully published, deployed, restarted, and fingerprint-verified, but James's live Home Assistant screenshot showed the Zero Net Export device page still looked effectively unchanged for the requested Managed Devices outcome: firmware `0.1.89` was visible, a Controls card exposed vague review buttons, and Activity showed candidate events, but there was no obvious Managed Devices window/panel/surface on the device info page.

This release must not be treated as another wording-polish loop. It exists to close the concrete product gap: **the native Home Assistant device page must visibly communicate Managed Devices status and interaction, within HA's auto-generated device-page constraints.**

## Current evidence from 0.1.89

Verified before this plan:

- GitHub release `v0.1.89` is published.
- Home Assistant installed package reported `sensor.zero_net_export_installed_version = 0.1.89`.
- Live install fingerprint comparison reported `overall_match: true` for the deployed `0.1.89` build.
- James's screenshot showed the native Zero Net Export device page with:
  - Device info firmware `0.1.89`
  - Controls rows including `Review managed devices`, `Review managed devices ...`, and `Show command center g...`
  - Activity rows for candidate shortlist/usefulness/warnings
  - no visually obvious Managed Devices window, panel, or grouped fleet surface on that page

Conclusion: the install/release path worked, but the visible UI outcome failed.

## Product requirement clarified for 0.1.90

The device page is a required operator surface, not merely a secondary afterthought.

`Configure -> Managed Devices` remains the primary add/promote/edit workflow, but the Zero Net Export device info page must still provide a clear native Managed Devices surface that lets an operator see, at a glance:

1. managed fleet count/state
2. unmanaged candidate count/state
3. the first review-first or ready-next candidate
4. the current blocker or next fleet action
5. which button/action opens the detailed Managed Devices view

The user should not need to infer this from generic Activity entries or ambiguous button labels.

## Home Assistant constraint

Home Assistant device pages are auto-generated from entities, controls, diagnostics, activity, and device metadata. A custom integration cannot simply inject an arbitrary bespoke React-style panel into the native device info page.

Therefore `0.1.90` must solve this with native HA-compatible surface design:

- clearer entity names
- stronger entity ordering/category choices where HA permits it
- a dedicated visible Managed Devices summary entity or entity cluster
- clearer button labels and persistent-notification titles
- device-page attributes that expose concise fleet state
- optional guidance to use Configure for deep edits, without hiding the at-a-glance status there

A label-only rename is not sufficient unless live screenshot evidence proves the device page now reads as a Managed Devices surface.

## Gap analysis

### Gap 1 — Device page exposes actions, not an obvious surface

Current `0.1.89` behavior:
- The device page shows button rows inside Controls.
- The user sees `Review managed devices`, but that reads as a generic action, not as a Managed Devices window.
- Activity contains candidate events, but Activity is history, not the current fleet surface.

Required `0.1.90` behavior:
- The device page must show a named Managed Devices surface/cluster in the ordinary entity layout.
- The surface must carry current state, not only a button that opens another notification.

Implementation direction:
- Promote the existing fleet summary sensors/buttons into a coherent device-page cluster with unambiguous names such as `Managed Devices overview`, `Managed Devices next step`, and `Managed Devices window`.
- Ensure the first visible Managed Devices rows summarize current fleet/candidate state, not just emit an action.

### Gap 2 — Configure workflow exists, but device-page expectation was not met

Current `0.1.89` behavior:
- Much of the actual workflow lives in `Configure -> Managed Devices` and config-flow screens.
- The device page points toward that workflow, but does not itself make the managed/unmanaged distinction visually obvious.

Required `0.1.90` behavior:
- The device page must be honest about the boundary: it is not the full editor, but it must still be a usable Managed Devices status/review surface.
- The page must make `Configure -> Managed Devices` the deep-edit path while showing enough state to justify the handoff.

Implementation direction:
- Put the primary current state on the device page.
- Put edit/promote/save forms in Configure.
- Use the button/notification as the drill-down, not as the only evidence that the feature exists.

### Gap 3 — Acceptance criteria were too forgiving

Current `0.1.89` docs said the device page should be a useful secondary review/audit path, but did not require screenshot-grade evidence that James could actually see the expected Managed Devices surface on the device page.

Required `0.1.90` behavior:
- The release cannot be called ready until a live screenshot, or equivalent live HA capture, shows the Managed Devices device-page surface visibly present.

Implementation direction:
- Add explicit screenshot-grade acceptance gates.
- Treat generic button rows and Activity-only evidence as insufficient.

### Gap 4 — Wording churn can masquerade as progress

Current failure mode:
- Renaming a button to `Managed Devices window` could improve discoverability, but by itself it does not prove the requested UI exists.

Required `0.1.90` behavior:
- Every change must be tied to one visible acceptance target: current fleet state, candidate state, next action, deep-edit path, or live screenshot evidence.

Implementation direction:
- Track implementation against the acceptance checklist below.
- Do not ship `0.1.90` based only on renamed labels or docs.

## Required implementation outcomes

`0.1.90` must deliver all of these:

1. **Device-page Managed Devices identity**
   - The page visibly names `Managed Devices` as a surface, not only as a button action.

2. **At-a-glance managed/unmanaged state**
   - The page shows current managed count/status and unmanaged candidate count/status in visible entities or equivalent native rows.

3. **Next fleet action visible**
   - The page shows the current blocker or next fleet action without requiring the user to press a button first.

4. **Clear drill-down action**
   - The page has an obvious action to open the detailed Managed Devices review/window, with a title that matches what appears after pressing it.

5. **Configure boundary remains clear**
   - Deep edits/promotions remain in `Configure -> Managed Devices`, but the device page explains this from current state, not from generic helper text.

6. **Screenshot-grade validation**
   - A live HA screenshot or browser capture proves the device page now visibly contains the Managed Devices surface.

## Non-goals

Do not use `0.1.90` for:

- broad copy cleanup unrelated to the screenshot failure
- optional dashboard redesign
- retagging or rewriting `v0.1.89`
- claiming HA supports arbitrary custom device-page panels unless verified
- hiding the issue behind Configure-only instructions

## Candidate implementation checklist

Before coding:

- [ ] Capture current live device-page baseline from James's screenshot and/or browser.
- [ ] Inspect current device-page entities and ordering via HA API/entity registry.
- [ ] Identify which existing sensors/buttons appear on the Zero Net Export device page and what card/section HA places them in.

Repo implementation:

- [ ] Add or adjust a dedicated device-page Managed Devices summary row/entity if needed.
- [ ] Rename/reorder Managed Devices actions only as part of a larger visible surface, not as the whole fix.
- [ ] Ensure entity categories do not hide the key Managed Devices rows under Diagnostics if they must be visible on the device page.
- [ ] Keep deep edit/promote flow in `Configure -> Managed Devices`.
- [ ] Update tests to assert device-page Managed Devices names, categories, and attributes.

Release:

- [ ] Bump manifest and version-coupled tests to `0.1.90` only after the repo implementation is complete.
- [ ] Add `0.1.90` changelog section describing the device-page Managed Devices visibility fix.
- [ ] Run full tests.
- [ ] Capture expected install fingerprint.
- [ ] Commit, tag `v0.1.90`, push, and publish GitHub release only after approval/release readiness.

Deploy/validate:

- [ ] Deploy exact `0.1.90` build to Home Assistant or verify HACS installs it.
- [ ] Restart Home Assistant Core.
- [ ] Validate install fingerprint `overall_match: true`.
- [ ] Verify `sensor.zero_net_export_installed_version = 0.1.90`.
- [ ] Capture screenshot-grade proof of the device page showing the Managed Devices surface.
- [ ] Verify pressing the Managed Devices action opens the expected notification/review/window with current state.

## Acceptance test

`0.1.90` is successful only if James can open the Zero Net Export device info page and immediately answer:

- How many managed devices are there?
- Is there an unmanaged backlog?
- What is the next fleet action or blocker?
- Where do I open the detailed Managed Devices workflow?

If the answer still requires reading Activity history, hunting through generic Controls rows, or being told to go elsewhere first, the fix has failed.
