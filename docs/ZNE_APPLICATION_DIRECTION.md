# Zero Net Export Application Direction

Date: 2026-06-26
Status: current product direction; initial product decisions recorded

## Decision

Zero Net Export is moving from a native-device-page-led custom integration to a
Home Assistant application backed by the existing integration backend.

The reason is practical: the current repo and validation history show that the
native Home Assistant device page, config-entry rows, button entities, and
options flows cannot deliver the full operator experience. They remain useful
supporting surfaces, but they are no longer the product shell.

## Goal

Develop an application for Home Assistant that captures the full Zero Net Export
scope:

- overview and readiness
- source/sensor mapping
- managed-device onboarding and fleet management
- controls and policy
- runtime planning/execution visibility
- diagnostics, repairs, support, and install validation
- multi-plan/service separation

## Target architecture

Use a Home Assistant-hosted application/panel as the primary operator UI.

Keep the existing integration backend for:

- config entries
- coordinator/runtime state
- source validation
- planner/executor logic
- managed-device inventory
- services/actions
- entities for automations and secondary visibility
- repairs, notifications, diagnostics, and release/install checks

The application should communicate with the backend through documented Home
Assistant mechanisms such as entity state, services/actions, config entries,
diagnostics, and, if needed, explicit websocket/API endpoints added by the
integration.

## Feasibility summary

Supported:

- Home Assistant panels are app-like full-screen pages linked from the sidebar.
- Panels receive the Home Assistant `hass` object in JavaScript.
- Home Assistant supports custom panel registration via `panel_custom`.
- Home Assistant developer docs state components can register panels.
- The existing backend already exposes much of the data/control surface needed
  by an app: entities, services, diagnostics, config flows, runtime state, and
  install validation helpers.

Unsupported as a primary strategy:

- forcing rich product workflow into native device-page cards
- relying on button entity rows to navigate into selected edit/remove flows
- arbitrary injection into native HA device-page cards or row overflow menus
- restoring raw JSON/YAML as the normal operator workflow
- patching Home Assistant frontend/core

Implementation decisions:

- The app should appear in the Home Assistant sidebar by default.
- The app name is `Zero Net Export`.
- The first implementation target should include editable setup/workflow
  capability, not only a read-only overview.
- Multi-plan/service support is required from day one.
- Frontend stack default: use the simplest maintainable Home Assistant-friendly
  web-component approach first. Treat vanilla/Lit-style implementation as the
  recommended default until a milestone feasibility check proves another stack
  is better.
- First must-work scope: include the core workflows needed for a complete app
  path: source mapping, managed devices, controls, and diagnostics. Build them
  incrementally, but do not define the application milestone as a single-workflow
  demo.
- Destructive actions should use strong confirmation. For high-impact actions,
  require typing an explicit confirmation word or phrase.
- Keep optional Lovelace dashboard examples as supplementary visibility.
- HACS-only delivery is acceptable for app frontend assets.
- Minimum supported Home Assistant version is `2026.6.4+`, matching the live
  validation target checked on 2026-06-26. Lower-version compatibility can be
  considered later only after a deliberate compatibility pass.

Unknown until implementation planning:

- exact frontend packaging/build approach
- whether automatic panel registration or `panel_custom` YAML registration is
  the first delivery mechanism
- which backend API shape should be added beyond current entities/services
- whether future lower-version compatibility is worth testing after the first
  application milestone

## Application information architecture

Initial target sections:

1. Overview
   - readiness, active blockers, current export/import state, active plan, safe mode
2. Sources
   - source role mapping, live health, stale/unavailable diagnostics, validation
3. Managed Devices
   - candidate review, add/edit/remove, priority, enablement, runtime status
4. Controls
   - controller enable/mode, target export, deadband, reserve, refresh cadence
5. Runtime
   - current plan, planned actions, applied actions, holds, safe-mode reasons
6. Diagnostics
   - repairs, install fingerprint, logs/support bundle, release/runtime summary
7. Settings
   - app preferences, advanced recovery, JSON import/export when needed

## Migration stance

Do not throw away the backend. Port the product workflow first.

Recommended phases:

1. Update docs and tests so application/panel work is allowed and expected.
2. Add a minimal nonblank Home Assistant app/panel route.
3. Build an editable first app milestone with a working overview plus the first
   slice of source mapping, managed devices, controls, and diagnostics.
4. Add backend read/write model/API where entity state and services are
   insufficient.
5. Expand each core workflow until the app can replace the native Configure
   path for normal operation.
6. De-emphasise native Configure/device-page workflow in docs after app validation.

## Riley decisions recorded

1. Sidebar by default.
2. App name: `Zero Net Export`.
3. First release should include editable workflows.
4. Multi-plan/service support from day one.
5. Frontend stack undecided by Riley; use a conservative vanilla/Lit-style
   default unless feasibility proves otherwise.
6. First acceptance path should cover the core app workflows rather than a
   single isolated feature.
7. Destructive actions need strong confirmation.
8. Keep optional Lovelace examples.
9. HACS-only delivery is acceptable.
10. Minimum Home Assistant version: `2026.6.4+`, based on the live validation
    target.

## Acceptance criteria for the first implementation milestone

- Home Assistant loads the integration.
- The Zero Net Export application route/panel appears as intended.
- The app renders a nonblank editable application shell on desktop and mobile.
- Overview shows current readiness and at least one real backend/runtime value.
- First editable slices exist for source mapping, managed devices, controls, and diagnostics.
- Multi-plan/service context is visible and entry-scoped.
- Destructive actions in the milestone use strong confirmation.
- Minimum supported Home Assistant version is documented as `2026.6.4+`.
- No native device-page/card injection is used.
- Existing backend tests still pass.
- Browser proof and logs are captured before any release claim.
