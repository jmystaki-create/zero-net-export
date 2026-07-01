# WB-ZNE-005 Next 10 Implementation Tasks

Status: Ready
Priority: High
Labels: planning, implementation, validation, roadmap

## Purpose

Maintain the next ten concrete tasks in priority order so development stays focused on validation and app-MVP progress.

## Next 10 Tasks

1. ~~Accept the feasibility check in `validation/zne-app-milestone-3-feasibility.md` for Milestone 3 (Managed Devices Fleet Control).~~ (Done)
2. ~~Approve starting Milestone 3 implementation.~~ (Done)
3. ~~Begin minimal design and implementation of the Managed Devices Fleet Control workflow.~~ (Stage 1 complete)
4. ~~Implement the smallest next app workflow slice (e.g., fleet list with filters and summary).~~ (Stage 1 complete)
5. ~~Validate the slice with repo tests, HACS install, HA restart, browser proof, and logs.~~ (Repo validation done; live validation pending)
6. Read-only inspect current live source-health warnings and classify blockers.
7. Resolve source-health warnings enough to make runtime readiness actionable.
8. Refine diagnostics/support surfaces for operator troubleshooting.
9. Reassess application MVP completion after the next validated slice.
10. Keep the OpenClaw Workboard updated on every ZNE turn, including status, blockers, validation evidence, and next action.

## Acceptance Criteria

- Tasks are ordered by validation and release-readiness value.
- Each task has a clear outcome.
- Work that requires live writes or release actions is not started without approval.
- New design/code work is gated by accepted target-environment feasibility.
- OpenClaw Workboard state is checked and updated whenever ZNE project state changes.

## Evidence Needed To Mark Done

- Each task is either completed with evidence or moved into a dedicated card.
- `ROADMAP.md` and `PROJECT_STATUS.md` reflect completed tasks.
- Validation artifacts are linked from `validation/`.
- Relevant OpenClaw Workboard card(s) exist or are updated for active ZNE work.

## Notes

Do not start implementation work until the next milestone feasibility check is written and accepted.
