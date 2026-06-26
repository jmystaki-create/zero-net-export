# ZNE-APP-001 Milestone 1 feasibility

Date: 2026-06-26
Status: feasibility complete for milestone planning and first implementation slice; implementation not started

## Requested behavior

Create the first Zero Net Export Home Assistant application milestone: a
sidebar-default `Zero Net Export` app for Home Assistant `2026.6.4+` with an
editable app shell, multi-plan context, and first slices of Sources, Managed
Devices, Controls, and Diagnostics.

## Target environment

- Home Assistant `2026.6.4+`
- Home Assistant frontend panel/custom panel surface
- Zero Net Export custom integration installed through HACS
- Existing Zero Net Export backend modules and config entries

## Authoritative evidence checked

Home Assistant developer docs checked on 2026-06-26:

- `https://developers.home-assistant.io/docs/frontend/custom-ui/creating-custom-panels/`
  - Panels are pages within Home Assistant.
  - Panels can allow control.
  - Panels are linked from the sidebar and rendered full screen.
  - Panels receive real-time access to the Home Assistant object via JavaScript.
  - Panels are custom elements and can use any framework if wrapped as a custom
    element.
  - The frontend passes `hass`, `narrow`, `route`, and `panel` properties to
    the panel custom element.
  - Components can register panels, and users can register panels through
    `panel_custom`.
- `https://www.home-assistant.io/integrations/panel_custom/`
  - Custom panels are JavaScript panels added to Home Assistant.
  - Sidebar title, sidebar icon, URL path, module URL, config, and admin
    requirement are supported configuration concepts.
- `https://developers.home-assistant.io/docs/api/websocket/`
  - Home Assistant exposes `/api/websocket`.
  - Clients authenticate and then send command messages with typed JSON payloads.
  - This is a supported route for streaming/command-style data when needed.

Live proof checked:

- The validation Home Assistant instance reports version `2026.6.4` from
  `/api/config`.
- The validation Home Assistant host reports Home Assistant Core `2026.6.4`,
  Home Assistant OS `18.0`, aarch64, and Home Assistant Yellow hardware via
  read-only `ha core info` / `ha host info`.

Home Assistant Core source checked for tag/branch `2026.6.4` on 2026-06-26:

- `homeassistant/components/panel_custom/__init__.py`
  - Exposes `async_register_panel(...)`.
  - Requires either `js_url` or `module_url`.
  - Accepts `frontend_url_path`, `webcomponent_name`, `sidebar_title`,
    `sidebar_icon`, `config`, `require_admin`, and `config_panel_domain`.
  - Delegates registration to `frontend.async_register_built_in_panel(...)`
    with `component_name="custom"`.
- `homeassistant/components/frontend/__init__.py`
  - Defines `async_register_built_in_panel(...)`.
  - Stores registered panels in `hass.data[DATA_PANELS]` by
    `frontend_url_path`.
  - Supports sidebar title, icon, default visibility, route path, panel config,
    admin requirement, and config panel domain.
  - Fires `EVENT_PANELS_UPDATED` after registration/removal.
- `homeassistant/components/http/__init__.py`
  - Defines `StaticPathConfig`.
  - Exposes `hass.http.async_register_static_paths(...)` for serving a folder or
    file as a static path.

Repo evidence checked:

- Earlier old-panel code was removed by ZNE-589, but the removal was a product
  direction decision, not proof that panels are technically impossible.
- Existing tests intentionally assert panel absence and must be revised in the
  app implementation.
- Existing backend has coordinator/runtime state, entities, services/actions,
  config entries, repairs, diagnostics, and install validation helpers.

## Supported findings

- A Zero Net Export app/panel is supported as the primary app surface.
- The app can be sidebar-visible by default.
- A custom element/Lit-style frontend is aligned with Home Assistant panel docs.
- Home Assistant `2026.6.4` supports programmatic custom panel registration
  through `panel_custom.async_register_panel(...)`; this is the first
  implementation path to use unless a focused coding proof rejects it.
- Home Assistant `2026.6.4` supports serving HACS-delivered frontend files from
  the integration via `hass.http.async_register_static_paths(...)` and
  `StaticPathConfig`.
- The panel can read `hass.states` and other frontend `hass` data for initial
  rendering.
- If the app needs a cleaner backend data model than entities provide, a
  documented websocket/API path is plausible and should be designed explicitly.
- Home Assistant `2026.6.4+` is a valid first target because it is the live
  validation target and matches the current documented panel behavior.

## Unsupported / excluded findings

- Do not patch Home Assistant frontend/core.
- Do not inject controls into native device-page cards, native row menus, or
  frontend DOM internals.
- Do not use an external web UI outside Home Assistant.
- Do not use raw JSON/YAML as the primary workflow.
- Do not treat the old removed `ZNE Managed Devices` panel implementation as
  shippable without revalidating it against the new product scope.

## Open questions before coding

- Exact backend app snapshot shape.
- Whether entity state plus existing services are sufficient for the first
  editable slices, or whether a dedicated app API is needed immediately.
- Exact frontend build approach for the first custom element. Default remains a
  small static JavaScript module until the implementation proves a build step is
  required.

## Feasibility decision

Milestone 1 is feasible as a Home Assistant `2026.6.4+` application/panel backed
by the existing integration. The approved first implementation route is:

1. Register a static frontend asset path with `StaticPathConfig`.
2. Register the sidebar app with `panel_custom.async_register_panel(...)`.
3. Use a JavaScript module URL from the static path.
4. Render a custom element named for Zero Net Export.

Implementation must start with the smallest nonblank sidebar app shell and a
real backend readiness value, then add thin editable slices for Sources, Managed
Devices, Controls, and Diagnostics.

## Validation required before completion

- Repo tests for panel registration/app snapshot/entry scoping.
- Full test discovery.
- `git diff --check`.
- Live Home Assistant browser proof on desktop and mobile/narrow after explicit
  deploy/restart approval.
- Zero Net Export log scan.
- Proof no native device-page/card injection was used.
