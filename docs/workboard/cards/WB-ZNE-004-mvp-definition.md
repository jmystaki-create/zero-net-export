# WB-ZNE-004 MVP Definition

Status: Ready
Priority: High
Labels: mvp, product, acceptance-criteria, release

## Purpose

Define the minimum useful Zero Net Export app MVP so development can measure progress against a product outcome rather than a stream of release fixes.

## MVP Candidate

The MVP is a Home Assistant app that lets an operator:
- See overall Zero Net Export readiness.
- Select the relevant plan/service context.
- Review and repair source-role bindings.
- Review managed devices and perform safe enabled/remove actions.
- Review and edit core controls.
- Understand why runtime control is blocked.
- Access diagnostics/support evidence.
- Trust that all writes are scoped to the selected config entry.

## Acceptance Criteria

- MVP workflows are listed with pass/fail validation requirements.
- Required live browser proof includes desktop and narrow/mobile viewport screenshots.
- Runtime readiness gaps are explicitly separated from release-install success.
- Destructive actions require strong confirmation.
- Multi-plan/service state remains entry-scoped.

## Evidence Needed To Mark Done

- MVP definition is agreed and reflected in `ROADMAP.md`.
- Each MVP workflow has validation records or an explicit remaining gap.
- Browser proof exists for primary app workflows.
- Runtime readiness evidence exists or runtime limitations are documented as non-MVP.

## Current Estimate

Application MVP is about 65% complete. The Sources milestone (ZNE-APP-002) is complete
for the accepted scope, including installed browser proof. Milestone 3 (Managed Devices
Fleet Control) is in draft; feasibility check and plan are written awaiting acceptance.

**Updated:** Milestone 3 feasibility check accepted on 2026-07-01 16:35 AEST. Implementation starting.
