# ZNE-APP-002 Sources workflow feasibility

Date: 2026-06-30
Status: written; pending Riley acceptance before implementation

## Task

- Task ID: ZNE-APP-002
- Task type: feature / application milestone
- User outcome: Operators can review and repair source-role setup inside the
  Zero Net Export Home Assistant app so runtime control blockers are visible and
  actionable.
- Proposed design/code area: Home Assistant app panel frontend,
  application-facing backend read/write API, source-role validation/status
  surfaces, tests, and release validation.

## Target environment

- Platform/runtime/UI/framework/API: Home Assistant custom integration and
  custom panel app, using the `hass` JavaScript object, entity state, services,
  and integration backend APIs.
- Version(s) or deployed target: Home Assistant `2026.6.4+`, with live
  validation through GitHub/HACS only.
- Exact behaviour being relied on:
  - The app panel receives `hass.states` and can render integration entities.
  - The app panel can call Home Assistant services through `hass.callService`.
  - The integration can expose source-role status through entities and source
    validation helpers.
  - The integration can add an explicit supported backend write surface if
    existing native configuration flows are insufficient for an app-native save.

## Authoritative sources consulted

- Source 1:
  - URL/path: `validation/zne-app-milestone-1-feasibility.md`
  - What it proves: Milestone 1 already source/live-proved the Home Assistant
    `2026.6.4` app panel/static asset path used by the sidebar app.
- Source 2:
  - URL/path: `custom_components/zero_net_export/frontend/zero-net-export-app.js`
  - What it proves: The installed app already reads `hass.states`, renders a
    Sources tab, navigates to native HA fallback routes, and calls supported
    Home Assistant services for managed-device/control writes.
- Source 3:
  - URL/path: `custom_components/zero_net_export/const.py`
  - What it proves: The integration defines source-role constants and required
    source keys, with labels for solar, grid, home load, and battery roles.
- Source 4:
  - URL/path: `custom_components/zero_net_export/validation.py`
  - What it proves: Existing source validation detects missing, unavailable,
    non-numeric, negative, overlapping, out-of-range, and reconciliation states;
    it returns status, safe mode, mismatch, diagnostic summary, hints, and
    per-source diagnostics.
- Source 5:
  - URL/path: `custom_components/zero_net_export/sensor.py`
  - What it proves: Existing source entities expose per-role status, reading,
    age, and issue-count sensors that the app can read via `hass.states`.
- Source 6:
  - URL/path: `custom_components/zero_net_export/app_api.py`
  - What it proves: Current app bootstrap only exposes static panel metadata and
    config-entry title/id/state, so richer app-native source editing will likely
    need either frontend entity-state composition plus a supported write service,
    or an expanded explicit app API.

## Findings

### Supported

- Mechanism: App-native source status display from Home Assistant entity state.
  - Evidence: `zero-net-export-app.js` already uses `hass.states`; `sensor.py`
    builds per-source status/reading/age/issue-count entities.
  - Design implication: The first Sources screen can be built without native
    Home Assistant page injection.

- Mechanism: App-visible blocker/readiness display from existing runtime sensors.
  - Evidence: Current app already displays
    `sensor.zero_net_export_source_blocker_summary`; source validation builds
    blocker-safe-mode outcomes.
  - Design implication: The Sources milestone can connect role rows to the
    existing blocker summary and Overview readiness.

- Mechanism: Conservative app write path through supported backend services or
  explicit app API.
  - Evidence: The `0.2.2` app successfully called integration services for
    managed-device writes through `hass.callService`; Home Assistant app panels
    can call services through the proven `hass` object.
  - Design implication: Source-role writes should use a scoped backend service
    or explicit API, not direct storage edits or frontend injection.

- Mechanism: Entry-scoped plan/service context.
  - Evidence: `app_api.py` exposes config-entry id/title/state to the app;
    previous validation confirms multi-plan config entries are distinct.
  - Design implication: The Sources workflow can require plan selection before
    saving source-role changes.

### Unsupported

- Mechanism: Native Home Assistant device-page/card/row injection for Sources.
  - Evidence: Project direction and milestone 1 feasibility already mark native
    page injection unsupported as a primary strategy.
  - Design implication: Do not attempt to solve source setup by placing custom
    cards or row actions into native HA pages.

- Mechanism: Direct live Home Assistant file-backend deployment for validation.
  - Evidence: User explicitly requires changes to flow through GitHub and be
    downloaded/installed by HACS.
  - Design implication: Live validation must use GitHub/HACS, restart, and
    fingerprint checks.

### Unknown / requires implementation proof

- Mechanism: Reusing existing native config-flow source-save logic directly from
  the app.
  - Why docs/source are insufficient: The current app has no generic config-flow
    submit bridge; `app_api.py` exposes only panel metadata and config-entry
    state.
  - Proposed validation: Inspect current config-flow source update path during
    implementation planning and either wrap it in a service/API or deliberately
    hand off to native Configure as a fallback for the first iteration.
  - Decision needed before implementation: Accept whether `ZNE-APP-002` must
    include app-native saving in the first release slice, or whether a read-rich
    Sources screen with explicit native Configure handoff is acceptable as a
    smaller interim step.

- Mechanism: Safe live write validation using the current Home Assistant source
  entities.
  - Why docs/source are insufficient: A reversible source-role mapping requires
    identifying a harmless existing entity and restoring the original mapping.
  - Proposed validation: Before live write proof, capture current source-role
    mappings, choose a safe disposable or equivalent mapping, save through the
    installed app, verify readiness changes, then restore.
  - Decision needed before proceeding to live write validation: Approval for the
    exact source mapping to modify.

## Constraints accepted for this task

- Use Home Assistant `2026.6.4+` as the supported app target.
- Keep the Home Assistant app/panel as the primary operator surface.
- Keep existing backend validation, coordinator/runtime, repairs, and entity
  surfaces as the foundation.
- Scope writes to the selected Zero Net Export config entry.
- Use GitHub/HACS-only deployment for live validation.
- Do not proceed to implementation until this feasibility record and the
  milestone plan are accepted.

## Exclusions

- Excluded path: Native HA device-page/card/row injection.
  - Reason: Previously found unsupported for the product workflow.
  - What would be required to reconsider: New Home Assistant official source/API
    support or an explicit upstream frontend contribution plan.

- Excluded path: Direct edits to live HA storage or direct custom component file
  deployment.
  - Reason: Violates the approved GitHub/HACS validation path.
  - What would be required to reconsider: Explicit user override for a one-off
    emergency diagnostic, not release validation.

- Excluded path: Claiming runtime control readiness from a UI-only source screen.
  - Reason: Runtime control depends on source-role health and backend validation.
  - What would be required to reconsider: Live evidence that required roles are
    mapped and validation no longer blocks control.

## Acceptance

- Feasibility check written by: OpenClaw dev
- Validation performed by: OpenClaw read-only source inspection
- Accepted by: pending Riley acceptance
- Date/time: 2026-06-30
- Link to task/status update: `PROJECT_STATUS.md`

## Result

Decision: ready for Riley acceptance; implementation remains blocked until
accepted.

Next safe step: have Riley accept the `ZNE-APP-002` milestone plan and this
feasibility check, then implement the smallest Sources workflow slice.
