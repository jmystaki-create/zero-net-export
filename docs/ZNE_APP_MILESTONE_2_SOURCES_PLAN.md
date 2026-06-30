# ZNE-APP-002 Sources workflow milestone

Date: 2026-06-30
Status: accepted; repo implementation validated; live validation pending

## Task

Build the next Zero Net Export Home Assistant application milestone around the
app-native Sources workflow.

Task type: feature / application milestone.

## User outcome

An operator can use the Zero Net Export app to understand and repair required
source-role setup without falling back to a vague native Home Assistant
configuration page. The app should show why runtime control is blocked, which
source roles need attention, and how a saved source change affects readiness.

## Why this is next

Release `0.2.2` proved the app can be installed through GitHub/HACS, render in
Home Assistant, survive restart, call supported services, and perform guarded
managed-device writes. The live validation instance still reports runtime
control blocked until required source roles are configured. Closing that gap is
the highest-value next app milestone because runtime control cannot be useful
until source readiness is app-visible and repairable.

## Acceptance criteria

- The Sources tab lists every source role used by the integration, including:
  solar power, solar energy, grid import/export power, grid import/export
  energy, home load power, battery state of charge, battery charge power, and
  battery discharge power.
- Required roles are visually distinct from optional roles.
- Each role shows the saved Home Assistant entity binding when available.
- Each role shows current live status, reading, unit, age, and issue count when
  those are exposed by the backend.
- Missing, unavailable, stale, non-numeric, and validation-error states are
  visible without relying on long prose.
- The app shows the source blocker summary and next repair step in the Sources
  workflow.
- The operator can select a configured Zero Net Export plan/service context
  before reviewing or editing source roles.
- The first write path is conservative: save source-role changes through a
  supported Home Assistant/integration backend mechanism, scoped to the selected
  config entry.
- If the existing backend does not expose a suitable app write API, this
  milestone must add an explicit backend service or websocket/API endpoint
  rather than relying on native page injection or raw storage edits.
- After saving, the app reloads or refreshes state enough to show whether source
  blockers changed.
- Runtime/Overview readiness reflects the updated source blocker state.
- The implementation uses the Home Assistant app panel and `hass` object already
  proven in milestone 1.
- No native Home Assistant device-page/card/row injection is introduced.
- No direct Home Assistant file-backend deployment is used for release or live
  validation; changes flow through GitHub and HACS.
- Desktop and narrow browser proof are captured before release.
- Repo validation passes JavaScript syntax check, changed Python compile check,
  focused tests for the Sources workflow, full test discovery, and
  `git diff --check`.
- Live validation passes HACS install/update, Home Assistant restart, install
  fingerprint match, app/static route checks, targeted log review, browser proof,
  and a reversible source-role write path if a disposable/safe source mapping is
  available.

## Validation plan

Repo validation:

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- changed Python `py_compile`
- focused app/source workflow tests
- full unittest discovery
- `git diff --check`

Live validation through GitHub/HACS only:

- publish/install candidate through the established GitHub/HACS path
- restart Home Assistant and wait for API recovery
- confirm installed version and install fingerprint
- confirm `/zero-net-export` and static app asset return HTTP 200
- capture desktop and narrow Sources screenshots
- verify source roles, blocker summary, role status, and plan context render
- perform only a reversible source-role write if a safe source entity is
  identified and approved
- confirm source blocker/runtime readiness state updates or record why no live
  write was safe
- check targeted Zero Net Export logs for traceback/error/warning

## Scope exclusions

- Do not implement native Home Assistant device-page/card/row injection.
- Do not patch Home Assistant frontend/core.
- Do not edit Home Assistant storage or custom component files directly on the
  live instance for validation.
- Do not make runtime control claims until source-role readiness is validated.
- Do not broaden this milestone into managed-device onboarding or control-policy
  redesign except where those screens need to display the source blocker state.

## Release impact

This milestone is expected to become the next app feature release after
implementation and validation. Version number is not assigned here.

## Implementation status

Repo implementation is complete and validated in
`validation/zne-app-milestone-2-sources-implementation.md`.

Live validation remains pending through the approved GitHub/HACS release path.
