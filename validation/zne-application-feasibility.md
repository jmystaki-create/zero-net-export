# Zero Net Export Home Assistant application feasibility

Date: 2026-06-26
Status: feasibility complete for documentation/direction change; implementation not started

## Task

Assess and record whether Zero Net Export can move from a native-device-page-led
integration workflow to a Home Assistant application that captures the full Zero
Net Export product scope.

## Target environment

- Home Assistant frontend custom panel/application surface
- Zero Net Export custom integration backend
- HACS/manual custom integration delivery
- Existing Home Assistant native entities, services/actions, diagnostics,
  repairs, config entries, and notifications as support surfaces

## Authoritative evidence

Home Assistant developer documentation checked on 2026-06-26:

- `https://developers.home-assistant.io/docs/frontend/custom-ui/creating-custom-panels/`
  - Panels are pages inside Home Assistant.
  - Panels can allow control.
  - Panels are linked from the sidebar and rendered full screen.
  - Panels have real-time access to the Home Assistant object via JavaScript.
  - Components can register panels.
- `https://www.home-assistant.io/integrations/panel_custom/`
  - Home Assistant supports custom panels written in JavaScript.
  - A panel can have a sidebar title, icon, URL path, module URL, and config.
- `https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup/`
  - Integrations can add service actions, and actions should validate inputs in
    the service action implementation.

Repo evidence checked:

- `PROJECT_STATUS.md` records repeated native-device-page limitations and
  corrective releases.
- `validation/zne-592-native-clickthrough-feasibility.md` records that normal
  button rows cannot launch selected managed-load edit/remove workflows.
- `validation/zne-fr-009-010-ha-design-guideline-feasibility.md` records that
  arbitrary editable cards cannot be inserted into the native device page through
  supported custom-integration APIs.
- `docs/ZNE-589_HOME_ASSISTANT_MENU_PANEL_FEASIBILITY.md` records that the old
  panel was removed because the project direction then forbade custom panels,
  not because Home Assistant panels were technically impossible.

## Supported findings

- Home Assistant has an application-like panel concept suitable for a Zero Net
  Export command-center UI.
- A panel can be full-screen, reachable through the sidebar, and backed by
  Home Assistant's JavaScript `hass` object.
- The existing integration backend can remain the control/data layer.
- Native entities, services/actions, diagnostics, repairs, and notifications can
  continue to support automations, fallback visibility, and recovery.
- This direction resolves the core product mismatch: Zero Net Export needs a
  coherent app workspace, while Home Assistant device pages are metadata/entity
  summaries.

## Unsupported findings

- The full Zero Net Export workflow should not continue to depend on exact
  placement inside native Home Assistant device-page cards, row actions, or
  overflow menus.
- A custom integration should not rely on undocumented Home Assistant frontend
  DOM structure to inject controls into native screens.
- External web UI, Home Assistant core/frontend patching, or browser-extension
  UI is not approved by this feasibility result.

## Unknowns

- Exact frontend packaging pattern to use for the first app version.
- Whether automatic panel registration or user-configured `panel_custom` should
  be the first delivery mechanism.
- Minimum supported Home Assistant version for the application UI.
- Exact editable workflow depth for the first milestone; Riley has decided the
  first release should include editable workflows rather than a read-only-only
  overview.
- Lower-version compatibility below Home Assistant `2026.6.4`; Riley accepted
  using the live validation target version as the minimum supported app target.

## Feasibility decision

Developing a Zero Net Export application inside Home Assistant is feasible and
better aligned with the product scope than continuing to force the workflow into
native device pages.

The direction is approved at documentation level by Riley's 2026-06-26 request.
Implementation target is Home Assistant `2026.6.4+`, based on the live
validation target queried through `/api/config` on 2026-06-26. Implementation
still requires a milestone-specific design and validation plan before code
changes.

## Validation for this documentation change

Pending after doc edits:

- `git diff --check`
- targeted text search for stale native-only/forbidden-panel steering language
- no application code changed
