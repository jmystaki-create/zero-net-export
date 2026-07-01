# ZNE-APP-003 Managed Devices Fleet Control

Date: 2026-07-01
Status: draft; awaiting feasibility gate and acceptance

## Task

Define and implement the next Zero Net Export application milestone focused on
**Managed Devices Fleet Control**.

Task type: feature / application milestone.

## User outcome

An operator can use the Zero Net Export app to:
- See the complete fleet of managed devices across all plans/services.
- Filter by plan, status, priority, or readiness.
- Review device health, last-seen age, and runtime blockers.
- Perform bulk actions (enable/disable, priority adjustment) with strong confirmation.
- Drill into individual device details, edit captured settings, and remove from ZNE.
- Understand why specific devices are not participating in runtime control.

## Why this is next

Sources workflow (ZNE-APP-002) is released and live-validated. The next highest-value
slice is making the managed-device fleet actionable in the app. Runtime control depends
on device readiness; operators need a single app surface to inspect, repair, and
control the fleet without relying on native Home Assistant device pages.

## Acceptance criteria

- The Managed Devices tab in the app shows a complete fleet list across all plans.
- Each row displays: device name, plan/service context, status (enabled/disabled),
  priority, last-seen age, and readiness state.
- Filter controls exist for plan, status, priority, and readiness.
- Bulk action controls exist for enable/disable and priority adjustment.
- Bulk actions require strong confirmation (e.g., typing "CONFIRM" or selecting
  a confirmation checkbox plus explicit action button).
- Drill-down detail view shows captured settings, runtime state, and blockers.
- Edit captured settings uses a supported HA reconfigure/options flow scoped to
  the owning config entry.
- Remove from ZNE uses the supported backend service path and preserves the
  original HA device/entity.
- Fleet summary shows counts: total, enabled, disabled, blocked, stale.
- Desktop and narrow browser proof are captured before release.
- Repo validation passes JavaScript syntax check, changed Python compile check,
  focused fleet-control tests, full test discovery, and `git diff --check`.
- Live validation passes HACS install/update, Home Assistant restart, install
  fingerprint match, app/static route checks, targeted log review, browser proof,
  and a reversible managed-device add/remove or edit proof if a safe disposable
  device is available.
- No native Home Assistant device-page/card/row injection is introduced.
- No direct Home Assistant file-backend deployment is used for release or live
  validation.

## Validation plan

Repo validation:
- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- changed Python `py_compile`
- focused fleet-control workflow tests
- full unittest discovery
- `git diff --check`

Live validation through GitHub/HACS only:
- publish/install candidate through the established GitHub/HACS path
- restart Home Assistant and wait for API recovery
- confirm installed version and install fingerprint
- confirm `/zero-net-export` and static app asset return HTTP 200
- capture desktop and narrow Managed Devices fleet screenshots
- verify fleet list, filters, summary counts, and status rendering
- perform bulk action on a disposable test device with confirmation
- confirm fleet summary updates and runtime state reflects the change
- check targeted Zero Net Export logs for traceback/error/warning

## Scope exclusions
- Do not implement native Home Assistant device-page/card/row injection.
- Do not patch Home Assistant frontend/core.
- Do not edit Home Assistant storage or custom component files directly on the
  live instance for validation.
- Do not broaden this milestone into runtime planning/execution redesign except
  where fleet status depends on runtime state display.

## Release impact
This milestone is expected to become the next app feature release after
implementation and validation. Version number is not assigned here.

## Implementation status
Pending: target-environment feasibility check and acceptance.
