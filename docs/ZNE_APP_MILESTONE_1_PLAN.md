# ZNE-APP-001 Milestone 1 Plan

Date: 2026-06-26
Status: planned; panel registration proof complete; implementation not started

## Objective

Deliver the first Home Assistant application milestone for Zero Net Export.

The milestone creates a sidebar-default `Zero Net Export` app for Home Assistant
`2026.6.4+`, backed by the existing custom integration. It must render a real,
editable application shell with multi-plan context and first workflow slices for
Overview, Sources, Managed Devices, Controls, and Diagnostics.

## Classification

Type: feature / architecture / frontend application milestone.

Target environment:

- Home Assistant `2026.6.4+`
- Home Assistant custom panel/application surface
- Zero Net Export custom integration backend
- HACS delivery

Feasibility record:

- General application direction: `validation/zne-application-feasibility.md`
- Milestone-specific feasibility: `validation/zne-app-milestone-1-feasibility.md`
- Panel registration proof: Home Assistant Core `2026.6.4` source supports
  `panel_custom.async_register_panel(...)`, `frontend.async_register_built_in_panel(...)`,
  and `hass.http.async_register_static_paths(...)` with `StaticPathConfig`.

## Product decisions

- Sidebar entry: yes, by default.
- App name: `Zero Net Export`.
- First release: editable workflows, not read-only only.
- Multi-plan/service support: required from day one.
- Frontend stack: simplest Home Assistant-friendly web component approach first;
  vanilla/Lit-style unless implementation proof shows otherwise.
- Destructive actions: strong confirmation. High-impact actions require typing
  an explicit confirmation phrase.
- Delivery: HACS-only for app frontend assets.
- Optional Lovelace examples: keep as supplementary visibility.
- Minimum Home Assistant version: `2026.6.4+`.

## Milestone scope

### In scope

1. App shell
   - Home Assistant sidebar panel named `Zero Net Export`.
   - Route/path owned by Zero Net Export.
   - Desktop and mobile/narrow layout.
   - Navigation sections: Overview, Sources, Managed Devices, Controls, Runtime,
     Diagnostics, Settings.

2. Backend read model
   - Provide one app-facing snapshot of entries/plans, readiness, source status,
     managed-device summary, control settings, runtime summary, diagnostics
     summary, and install/version status.
   - Prefer existing coordinator/entities/services where adequate.
   - Add explicit websocket/API surface only where current entities/services are
     too noisy or incomplete for app UX.

3. Editable first slices
   - Sources: show mapped roles and provide an initial edit path or handoff
     designed for replacement by app-native editing.
   - Managed Devices: list managed devices per plan, show candidate/summary
     state, and provide first edit/remove/add affordances with safe scoping.
   - Controls: show enabled/mode/target/deadband/reserve/refresh and provide
     first editable controls where backend paths already exist safely.
   - Diagnostics: show setup blockers, repair/install/version evidence, and a
     copyable support summary.

4. Multi-plan guardrail
   - Every displayed plan/service must be clearly identified.
   - Every write operation must carry the owning config entry id.
   - The app must not cross-edit Summer/Winter or other plan state.

5. Safety guardrail
   - Destructive actions require strong confirmation.
   - Removing a managed device must remove only the Zero Net Export managed
     record and must not remove the original Home Assistant device/entity.

### Out of scope

- Home Assistant core/frontend patching.
- External web UI outside Home Assistant.
- Native device-page/card/row injection.
- Lower-version compatibility below Home Assistant `2026.6.4`.
- Publishing a release, deploying to live HA, or restarting HA without approval.
- Releasing the old `0.1.110` native-device-page work unless separately requested.

## Candidate implementation approach

1. Register a static frontend path from the integration using
   `StaticPathConfig` and `hass.http.async_register_static_paths(...)`.
2. Add a frontend asset directory under `custom_components/zero_net_export/`.
3. Add a minimal JavaScript module/custom element for the app shell.
4. Register the panel with `panel_custom.async_register_panel(...)` so the app
   appears as `Zero Net Export` in the sidebar by default.
5. Add a small backend app snapshot helper module.
6. Add websocket/API endpoint or service-backed read path if needed for a clean
   app snapshot.
7. Add tests that replace the old "panel must not exist" assertions with
   "approved app panel exists and uses supported paths" assertions.
8. Add browser validation scripts/artifacts for desktop and mobile/narrow
   render proof.

## Files expected to change in implementation

Likely:

- `custom_components/zero_net_export/manifest.json`
- `custom_components/zero_net_export/__init__.py`
- `custom_components/zero_net_export/frontend/...`
- `custom_components/zero_net_export/app_api.py` or equivalent
- `custom_components/zero_net_export/strings.json`
- `custom_components/zero_net_export/translations/en.json`
- `tests/test_managed_devices_panel.py`
- new app/panel tests under `tests/`
- `README.md`
- `CHANGELOG.md`
- `PROJECT_STATUS.md`
- validation records under `validation/`

Exact implementation files must be confirmed in the coding task before edits.

## Acceptance criteria

- Home Assistant `2026.6.4+` loads the integration.
- `Zero Net Export` appears in the sidebar by default.
- The app route renders a nonblank app shell on desktop and mobile/narrow.
- The Overview shows at least one real backend/runtime value from the live
  integration.
- The app shows all configured ZNE plans/services and preserves entry scoping.
- First editable slices exist for Sources, Managed Devices, Controls, and
  Diagnostics.
- Managed-device destructive actions require strong confirmation.
- Removing/unmanaging a device preserves the original Home Assistant
  device/entity.
- The implementation does not inject controls into native HA device pages/cards.
- Existing backend tests still pass.
- New app/panel tests cover registration, app snapshot shape, entry scoping, and
  stale old-panel assumptions.
- Browser proof is captured before any release claim.

## Validation plan

Repo validation:

- focused app/panel tests
- changed-file `py_compile`
- `python3 -m unittest discover -s tests`
- `git diff --check`

Live validation after explicit approval:

- HACS/release-managed install only
- Home Assistant restart/API recovery
- install fingerprint comparison
- log scan for Zero Net Export errors/warnings/tracebacks
- desktop browser screenshot of app shell
- mobile/narrow browser screenshot of app shell
- browser check that sidebar entry exists
- browser/API proof that Overview uses real backend data
- write-path proof for one safe editable control
- strong-confirmation proof for one destructive managed-device action using a
  disposable managed load
- proof original/source Home Assistant device/entity remains present after
  unmanage/remove

## Risks

- Panel registration is source-proven for Home Assistant `2026.6.4`, but the
  first coding slice still needs repo tests and live browser proof before any
  release claim.
- The existing backend exposes many details through entity state and long
  diagnostic text; the app may need a cleaner backend snapshot API to avoid
  recreating the old "command wall" problem.
- Tests currently include historical "panel is absent" assertions. Those must be
  updated deliberately as part of the implementation.
- Editable workflow breadth is larger than a read-only shell. Keep the first
  slices thin, entry-scoped, and safe rather than trying to finish the full app
  in one release.

## Next implementation task

Implement the smallest nonblank sidebar app shell using the proven supported
panel/static-asset path, with one real backend readiness value.
