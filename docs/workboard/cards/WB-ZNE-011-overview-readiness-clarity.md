# WB-ZNE-011 Overview Readiness Clarity

Status: Done
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
- Release/live validation: passed in `v0.4.3`; evidence recorded in
  `validation/0.4.3-release-validation.md`.

## Release Evidence

- GitHub release `v0.4.3` published.
- HACS installed `v0.4.3`.
- Home Assistant restarted and recovered with installed version sensor `0.4.3`.
- Install fingerprint matched before and after restart.
- Browser proof confirmed `Version 0.4.3`, `Current focus`,
  `What is wrong`, and `How to resolve` on desktop and narrow viewports.

## Next Actions

1. Start `ZNE-595` recorder attribute cleanup.
2. Preserve the full readiness detail in diagnostics/app API surfaces while
   trimming recorder-backed entity attributes.

## Risks

- The current live issue text is sourced from existing command-center and source diagnostic attributes, so clarity depends on those backend messages remaining useful.
- ZNE-595 recorder attribute cleanup remains separate and should follow after this feature slice is validated.
