# Zero Net Export — Application Development Constraints

Zero Net Export is now a **Home Assistant application backed by a custom integration**.

The project direction changed on 2026-06-26 after repeated validation showed that
Home Assistant's native device/config-entry surfaces cannot carry the full Zero
Net Export product scope. The integration backend remains valuable, but the
primary operator experience must move into a Zero Net Export-owned application
surface inside Home Assistant.

This document is the highest-priority project rulebook for OpenClaw and all
automated agents working on this repository. If another document conflicts with
this document, this document wins.

---

## 1. Product direction

Build Zero Net Export as an application for Home Assistant.

The application must capture the full scope of Zero Net Export:

- system overview and readiness
- source/sensor role mapping and health
- managed-device onboarding, editing, staging, prioritisation, and removal
- control policy, target export, deadband, battery reserve, refresh cadence, and mode
- runtime planning/execution visibility
- diagnostics, repairs, install validation, and release/support evidence
- multi-plan/service separation
- safe operator actions and explicit confirmation for destructive operations

The Home Assistant integration remains the backend engine:

- config entry lifecycle
- coordinator/runtime state
- planner/executor/control logic
- source validation
- managed-device model
- entities for automation/status
- services/actions
- repairs, persistent notifications, diagnostics
- HACS/install/release validation

Native Home Assistant surfaces are now **supporting surfaces**, not the primary
product UI.

---

## 2. Target application surface

The approved primary surface is a Home Assistant-hosted application/panel.

Feasibility basis:

- Home Assistant developer docs define panels as full-screen pages linked from
  the sidebar, with real-time access to the `hass` object from JavaScript.
- Home Assistant allows users to register custom panels through `panel_custom`.
- The developer docs also note that components can register panels.

Approved implementation direction:

- Add a Zero Net Export application route/panel inside Home Assistant.
- Ship frontend assets as part of the integration when technically feasible.
- Use Home Assistant backend services, websocket commands, config entries,
  diagnostics, and entity state as the app's data/control layer.
- Keep the app inside Home Assistant's auth/session/frontend shell.

The old rule forbidding custom panel/sidebar/frontend work is retired.

---

## 3. Source of truth order

When documents disagree, use this authority order:

1. `CONSTRAINTS.md`
2. `PROJECT_STATUS.md`
3. `docs/ZNE_APPLICATION_DIRECTION.md`
4. `docs/ACTIVE_USER_REQUESTS.md`
5. `docs/BUGS.md`
6. `docs/SUPERVISOR.md`
7. Current implementation under `custom_components/zero_net_export`
8. `README.md`
9. Historical docs only if explicitly referenced by the user

Deprecated native-only docs must not create work.

Historical design docs, old implementation maps, previous UX plans, or
superseded notes must not override the current application direction.

---

## 4. Allowed implementation surfaces

The project may use these surfaces:

- Home Assistant custom application/panel as the primary operator UI
- Integration backend modules under `custom_components/zero_net_export`
- Static/frontend assets shipped by the integration
- Home Assistant config entries and options/reconfigure flows when they remain useful
- Native Home Assistant entities
- Native device/entity registry behavior
- Native services/actions
- Native Repairs issues
- Persistent notifications
- Diagnostics snapshots/downloads
- Translations under `strings.json`
- Optional Lovelace examples for supplementary visibility
- Tests, validation scripts, and documentation

The application should own normal operator workflows. Native HA Configure/device
pages should remain as fallback, secondary visibility, automation, and recovery
surfaces.

---

## 5. Forbidden work unless explicitly approved

Do not implement or propose the following unless Riley explicitly approves it:

- external web UI outside Home Assistant
- Home Assistant core patch
- Home Assistant frontend patch
- browser-extension UI
- cloud service requirement for local control
- YAML/raw JSON as the primary user workflow
- undocumented Home Assistant frontend monkey-patching
- destructive live Home Assistant changes outside the release-management process
- direct mutation of original/source Home Assistant devices/entities when removing
  a Zero Net Export managed-device record

The application may use documented/custom Home Assistant frontend extension
points, but must not depend on hidden internal DOM structure for correctness.

---

## 6. Required proof before implementation

Before application architecture, frontend implementation, or backend API work,
OpenClaw must state:

1. The requested behavior.
2. The intended Home Assistant application/backend surface.
3. The feasibility classification.
4. The authoritative evidence or live proof used.
5. The exact files expected to change.
6. The validation plan.

Feasibility classification must be one of:

- Application panel supported
- Integration backend supported
- Native HA support surface
- Lovelace-only supplement
- External/custom unsupported
- Not implementable

If a request requires external UI, Home Assistant core/frontend patching, or
undocumented frontend internals, stop and report the boundary.

---

## 7. Application architecture guardrails

The app must be product-grade, not a thin collection of debug panels.

Required guardrails:

- One clear primary entry point in Home Assistant.
- Mobile and desktop layouts must be designed and validated.
- Every destructive action needs explicit confirmation and clear scope.
- Multi-plan/service state must remain entry-scoped.
- Original Home Assistant devices/entities must remain owned by their source integrations.
- Backend operations must validate inputs and fail closed.
- Runtime control must remain safe-mode-first when sources or managed devices are invalid.
- App state must be derived from authoritative backend/runtime data, not duplicated silently in frontend-only state.
- The native entity/device surface must not be allowed to re-expand into the primary UI.

---

## 8. Release and validation gates

No application release is ready until:

- repo tests pass
- frontend build/static asset validation passes, once frontend assets exist
- Home Assistant installs/loads the integration
- the application route/panel appears in Home Assistant
- browser validation proves the app is nonblank and usable on desktop and mobile
- core workflows are validated: setup/readiness, source mapping, managed devices,
  controls, diagnostics, and multi-plan isolation
- logs are checked for Zero Net Export errors/warnings/tracebacks
- changelog and release notes describe the application direction

Live Home Assistant deploy/restart/release actions still require explicit approval.

---

## 9. Current decision questions

Before application implementation starts, ask Riley for decisions when they are
not already clear. Keep questions focused. Current open questions are tracked in
`docs/ZNE_APPLICATION_DIRECTION.md`.
