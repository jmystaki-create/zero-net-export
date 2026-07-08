# WB-ZNE-010 Overview Console Live Metrics

Status: Validating
Priority: High
Labels: application, overview, realtime, validation, feature

## Purpose

Track Riley's 2026-07-08 request to make the Overview console feel alive by making Reconciliation Status more realtime and filling Source Power, Battery Power, and Confidence with meaningful current values or clear blockers.

## Linked Requests

- `ZNE-FR-011` - Reconciliation status should feel realtime.
- `ZNE-FR-012` - Overview console should include source power, battery power, and confidence.

## Acceptance Criteria

- Reconciliation Status refreshes predictably without adding excessive Home Assistant API load.
- Last-updated/freshness context is visible.
- Source Power resolves from current source/runtime state.
- Battery Power resolves from battery discharge minus charge when available.
- Confidence resolves from current source validation quality.
- Missing, stale, or blocked values explain the source role/blocker causing the gap.
- Existing Home Load, Surplus/Deficit, Reconciliation Error, and Executor State remain visible.
- Desktop and narrow browser validation are captured after release.

## Current State

- Target-environment feasibility: supported and recorded in `validation/zne-fr-011-012-overview-console-live-metrics.md`.
- Implementation: completed in `custom_components/zero_net_export/frontend/zero-net-export-app.js`.
- Repo validation: passed; evidence recorded in `validation/zne-fr-011-012-overview-console-live-metrics.md`.
- Release/live validation: not started; requires normal release-management approval.

## Next Actions

1. After user approval, prepare release notes/version bump.
2. Publish through the approved GitHub/HACS release path.
3. Restart Home Assistant.
4. Capture desktop/narrow browser proof of the Overview console.
5. Record installed-version, fingerprint, HACS metadata, and targeted log evidence.

## Risks

- Multi-plan installs may suffix entity IDs differently; validate against live app-visible entity names before calling multi-plan support complete.
- This slice intentionally does not add a new polling API, so all values depend on existing HA state propagation and current ZNE entity surfaces.
- ZNE-595 recorder attribute cleanup remains separate and should follow after this feature slice is validated.
