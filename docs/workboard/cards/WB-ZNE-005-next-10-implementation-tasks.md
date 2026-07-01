# WB-ZNE-005 Next 10 Implementation Tasks

Status: Ready
Priority: High
Labels: planning, implementation, validation, roadmap

## Purpose

Maintain the next ten concrete tasks in priority order so development stays focused on validation and app-MVP progress.

## Next 10 Tasks

1. Update the OpenClaw Workboard with the completed Sources browser proof state.
2. Read-only inspect current live source-health warnings and classify blockers.
3. Define the next app milestone acceptance criteria after Sources proof closure.
4. Write target-environment feasibility for the next app milestone before design/code.
5. Implement the smallest next app workflow slice inside the accepted app/custom-panel path.
6. Validate the next slice with repo tests, HACS install/update, Home Assistant restart, browser proof, and logs.
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
