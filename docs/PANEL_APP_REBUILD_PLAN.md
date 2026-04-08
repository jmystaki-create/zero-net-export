# Native Home Assistant Operator Plan

## Status

The custom Zero Net Export panel route has been removed.

The project now treats these as the supported operator surfaces:
- Home Assistant **Configure** flow for source mapping, managed devices, and controller tuning
- integration device page entities/buttons for diagnostics and setup guidance
- optional Lovelace/dashboard examples as fallback operator views

## Why the direction changed

Real installs showed that the sidebar/custom-panel route added packaging, routing, and reliability risk without being required for the core product outcome. The next major milestone is to make the native Home Assistant path boring, reliable, and easy to validate.

## Current goals

1. Keep install and reload behavior stable in real Home Assistant environments
2. Make **Configure** the single supported setup/configuration path
3. Keep diagnostics and support snapshots reachable from native HA surfaces
4. Reduce dependence on custom frontend code for core operator workflows
5. Preserve release discipline and validation proof in real installs

## What stays

- source mapping and validation engine
- controller/planner/runtime logic
- device inventory model and guards
- diagnostics export and action history
- native device-page diagnostic buttons
- Lovelace/dashboard examples where useful

## What was removed from scope

- custom sidebar panel registration
- `/zero-net-export` routing as a supported setup path
- custom panel launcher/fallback pages
- panel-first product positioning in active planning docs

## Near-term completion criteria

The current native-surface pivot is successful when:
- a fresh install can be completed through **Add Integration** plus **Configure**
- required source mapping works entirely in Configure
- managed devices can be persisted through Configure
- controller tuning works through Configure/native entities
- setup checklist and support snapshot remain reachable from the device page
- release notes and validation docs all describe the same native-first path
