# WB-ZNE-002 Architecture Inventory

Status: Ready
Priority: High
Labels: architecture, inventory, backend, frontend, home-assistant

## Purpose

Create and maintain a concise inventory of the current app/backend architecture so future work starts from verified surfaces instead of stale native-device assumptions.

## Acceptance Criteria

- Current primary UI surface is identified.
- Backend responsibilities are listed.
- Supported Home Assistant surfaces are separated from unsupported or forbidden surfaces.
- Current release baseline and validation records are linked.
- Gaps between current architecture and MVP are listed.

## Evidence Needed To Mark Done

- Workboard architecture/current-state section is populated.
- Existing architecture references are linked.
- Any new architecture claim is backed by `CONSTRAINTS.md`, feasibility records, source code, or live proof.

## Current Evidence

- `CONSTRAINTS.md`
- `docs/ARCHITECTURE.md`
- `docs/ZNE_APPLICATION_DIRECTION.md`
- `validation/zne-application-feasibility.md`
- `validation/zne-app-milestone-1-feasibility.md`
- `validation/zne-app-milestone-2-sources-feasibility.md`
- `validation/0.2.4-release-validation.md`

## Notes

Future architecture changes require a written target-environment feasibility check before design, mockup, or code.
