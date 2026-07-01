# ZNE-APP-003 Target Environment Feasibility Check

Date: 2026-07-01
Status: draft; awaiting acceptance before design/code

## Target environment
Home Assistant custom application panel (sidebar-linked) backed by the existing
Zero Net Export integration.

## Feasibility question
Can the Managed Devices Fleet Control workflow be implemented as a Home Assistant
app panel using supported mechanisms, without native device-page/card/row injection
or direct file-backend deployment?

## Authoritative sources consulted
- Home Assistant developer documentation: `panel_custom` registration.
- Existing ZNE implementation (Milestone 1 & 2): static asset registration,
  panel registration, `hass` object access, entity state, services/actions.
- ZNE-APP-002 implementation and validation: Sources workflow app panel.

## Findings

### Supported
- Home Assistant panels can be registered via `panel_custom.async_register_panel(...)`
  and appear as sidebar-linked full-screen pages.
- Panels receive the Home Assistant `hass` object in JavaScript, allowing access
  to entity states, services, config entries, and diagnostics.
- Static frontend assets can be served via `http.async_register_static_paths(...)`
  or equivalent `StaticPathConfig` mechanism.
- Backend services/actions can be invoked from the app via `hass.callService(...)`.
- Config entry scoping is supported: services can accept `entry_id` and operate
  only on the selected plan/service context.
- Bulk actions can be implemented as backend services that accept a list of
  device IDs and apply changes in a single transaction.
- Strong confirmation can be enforced in the app UI (e.g., require typing
  "CONFIRM" before enabling the action button).
- Fleet summary counts can be derived from the managed-device inventory in the
  backend coordinator.
- Filter controls (plan, status, priority, readiness) can be implemented in the
  app frontend using entity state and backend-provided metadata.
- Drill-down detail view can display captured settings from the managed-device
  payload and runtime state from the coordinator.
- Edit captured settings can use the supported HA reconfigure/options flow
  scoped to the owning config entry.
- Remove from ZNE can use the supported backend service path (`zero_net_export.remove_managed_device`)
  and preserve the original HA device/entity.

### Unsupported (as primary strategy)
- Arbitrary injection into native Home Assistant device-page cards or row
  overflow menus.
- Direct editing of Home Assistant storage files for validation or release.
- Patching Home Assistant frontend/core to add custom UI elements.
- Relying on native device-page rows as the primary operator workflow.

### Unknown until implementation
- Exact frontend packaging/build approach (vanilla/Lit vs. alternative stack).
- Whether automatic panel registration or explicit YAML registration is needed
  for the first delivery mechanism.
- Whether additional backend websocket/API endpoints are required beyond current
  entity state and services for real-time fleet updates.
- Performance characteristics of fleet filtering/sorting with large device counts.

## Risks and side effects
- Backend services for bulk actions must be idempotent and transactional to
  avoid partial updates.
- Fleet filtering/sorting must be efficient to avoid UI lag with large fleets.
- Strong confirmation must be clearly communicated to operators to prevent
  accidental bulk changes.
- Removing managed devices must preserve original HA devices/entities to avoid
  unintended side effects.

## Feasibility conclusion
**Supported.** The Managed Devices Fleet Control workflow can be implemented as
a Home Assistant app panel using supported mechanisms. No native device-page
injection or direct file-backend deployment is required.

## Next steps before design/code
1. Accept this feasibility check.
2. Define milestone-specific acceptance criteria in `docs/ZNE_APP_MILESTONE_3_PLAN.md`.
3. Proceed with minimal design and implementation within the accepted feasible path.

## Acceptance
This feasibility check must be accepted before any design, mockup, or code work
for ZNE-APP-003 proceeds.

Acceptance status: **pending**.
