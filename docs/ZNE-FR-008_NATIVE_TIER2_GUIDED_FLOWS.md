# ZNE-FR-008 — native Tier 2 guided flows

Status: backlog / split from ZNE-588 on 2026-05-01.

## Purpose

Build the actual Tier 2 experience as a separate feature release instead of hiding it inside the ZNE-588 bug fix.

ZNE-588 now only fixes the native Tier 1 page so it is compact and truthful. This feature owns the larger workflow: native Home Assistant guided flows for deeper Sensors, Controls, Managed Devices, Diagnostics/review, and save/reload actions.

## Design boundary

- Tier 1 remains the native Home Assistant device page.
- Tier 2 uses native Home Assistant config-entry reconfigure/options/subentry flows.
- The custom `/zero-net-export` command-center panel is not part of this feature unless Riley explicitly re-approves that architecture.
- Button entities must not be treated as browser navigation controls unless live Home Assistant proof shows the navigation actually occurs.

## User outcome

From a clean native Tier 1 page, an operator can intentionally enter a native guided workflow to complete or review detailed setup without the Tier 1 page becoming a dense command wall.

## Initial Tier 2 flow map

- Sensors: source/sensor mapping, missing roles, health/progress summary.
- Controls: enabled/mode/target export/battery reserve/deadband/override review.
- Managed Devices: add/edit fixed-load and managed-device assignments using supported HA flows/panels only where approved.
- Diagnostics/review: compact readiness review, blockers, diagnostics download/reference, save/reload summary.
- Save/reload: explicit final confirmation and reload behaviour.

## Acceptance criteria

- Each Tier 2 entry path is mapped to a supported native HA flow mechanism before implementation.
- Copy stays short and operator-focused, consistent with ZNE-585/ZNE-586.
- Per-plan/config-entry scoping is preserved.
- No custom command-center panel is required for core setup unless explicitly approved.
- Focused config-flow/subentry tests cover each entry path and save/reload behaviour.
- Full unit discovery and `git diff --check` pass.
- Live Home Assistant browser proof shows the actual entry path and native flow screens before release acceptance.

## Relationship to ZNE-588

ZNE-588 must not complete this feature. ZNE-588 only fixes the current Tier 1 bug: misleading non-navigating setup buttons and over-dense Diagnostics on the native device page.
