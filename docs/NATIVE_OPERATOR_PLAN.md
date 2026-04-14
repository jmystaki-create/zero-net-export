# Native Home Assistant Operator Plan

> Steering note: this document explains the native-HA-only direction. `SUPERVISOR.md` is now the active steering layer for current goals, risks, release gates, and next actions.

## Status

The custom Zero Net Export panel route has been removed.

The project now treats these as the only supported operator surfaces:
- Home Assistant **Configure** flow for source mapping, managed devices, and controller tuning
- the integration device at **Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device** for diagnostics and setup/support buttons
- Home Assistant entities, notifications, automations/scripts, and Repairs for normal runtime/support workflows

Optional Lovelace/dashboard examples may still exist as supplementary debug visibility inside Home Assistant, but they are not part of the supported operator path.

## Why the direction changed

Real installs showed that the sidebar/custom-panel route added packaging, routing, and reliability risk without being required for the core product outcome. The native Home Assistant direction is still the right one, and there is no supported UI outside native Home Assistant integration/device surfaces. The implementation remains transitional. The next major milestone is to make the native path boring, reliable, easier to validate, and less dependent on raw inventory JSON for normal operator tasks.

## Current goals

1. Keep install and reload behavior stable in real Home Assistant environments
2. Make **Configure** the single supported setup/configuration path, with troubleshooting kept on native device/entity/notification/Repairs surfaces
3. Reduce day-to-day reliance on raw `device_inventory_json` in native flows without reintroducing a panel
4. Keep diagnostics and support snapshots reachable, more coherent, and easier to discover from native HA surfaces
5. Reduce dependence on custom frontend code for core operator workflows
6. Preserve release discipline and validation proof in real installs

## What stays

- source mapping and validation engine
- controller/planner/runtime logic
- device inventory model and guards
- diagnostics export and action history
- native device-page support actions
- Lovelace/dashboard examples where useful as optional debug visibility inside Home Assistant, not as part of the supported operator path

## What was removed from scope

- custom sidebar panel registration
- `/zero-net-export` routing as a supported setup path
- custom panel launcher/fallback pages
- any custom or external UI product positioning in active planning docs

## Near-term completion criteria

The current native-surface pivot is successful when:
- a fresh install can be completed through **Add Integration** plus **Configure**
- required source mapping works entirely in Configure
- managed devices can be persisted through Configure with native add/remove flows for common cases
- controller tuning works through Configure/native entities
- setup checklist, support center, and support snapshot remain reachable from the integration device at **Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device**
- release notes and validation docs all describe the same native-only but still-in-validation path
