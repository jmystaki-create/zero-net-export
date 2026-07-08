# WB-ZNE-011 Overview Readiness Clarity

Status: Validating
Priority: High
Labels: application, overview, readiness, ux, validation

## Purpose

Track Riley's 2026-07-08 request to make the Overview Readiness section clear,
structured, and actionable.

## Linked Request

- `ZNE-FR-013` - Overview Readiness should explain errors and resolution steps.

## Acceptance Criteria

- Readiness no longer squeezes long command-center text into a narrow two-column row.
- Controller, Safe mode, and Source mismatch are visible as compact status chips.
- Current focus is shown separately from issue detail.
- Active readiness issues are shown as cards with `What is wrong` and `How to resolve`.
- Source blockers, power reconciliation mismatch, controls readiness, and managed-device queue context are shown when present.
- Desktop and narrow browser validation are captured after release.

## Current State

- Target-environment feasibility: supported and recorded in `validation/zne-fr-013-overview-readiness-clarity.md`.
- Implementation: completed in `custom_components/zero_net_export/frontend/zero-net-export-app.js`.
- Repo validation: passed; evidence recorded in `validation/zne-fr-013-overview-readiness-clarity.md`.
- Release/live validation: pending normal release-management approval.

## Next Actions

1. Prepare release notes/version bump after approval.
2. Publish through the approved GitHub/HACS release path.
3. Restart Home Assistant.
4. Capture desktop/narrow browser proof of the Readiness card.
5. Record installed-version, fingerprint, HACS metadata, and targeted log evidence.

## Risks

- The current live issue text is sourced from existing command-center and source diagnostic attributes, so clarity depends on those backend messages remaining useful.
- ZNE-595 recorder attribute cleanup remains separate and should follow after this feature slice is validated.
