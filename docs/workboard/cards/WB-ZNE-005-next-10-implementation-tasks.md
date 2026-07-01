# WB-ZNE-005 Next 10 Implementation Tasks

Status: Ready
Priority: High
Labels: planning, implementation, validation, roadmap

## Purpose

Maintain the next ten concrete tasks in priority order so development stays focused on validation and app-MVP progress.

## Next 10 Tasks

1. Push local validation-doc commit `5936a0d docs: record 0.2.4 live validation`.
2. Capture desktop browser proof for installed Sources workflow.
3. Capture narrow/mobile browser proof for installed Sources workflow.
4. Record Sources browser proof in validation evidence and update project status.
5. Investigate the previous browser/node navigation failure and document the reliable path.
6. Read-only inspect current live source-health warnings and classify blockers.
7. Define the next app milestone acceptance criteria after Sources proof closes.
8. Write target-environment feasibility for the next app milestone before design/code.
9. Implement the smallest next app workflow slice inside the accepted app/custom-panel path.
10. Validate the next slice with repo tests, HACS install/update, Home Assistant restart, browser proof, and logs.

## Acceptance Criteria

- Tasks are ordered by validation and release-readiness value.
- Each task has a clear outcome.
- Work that requires live writes or release actions is not started without approval.
- New design/code work is gated by accepted target-environment feasibility.

## Evidence Needed To Mark Done

- Each task is either completed with evidence or moved into a dedicated card.
- `ROADMAP.md` and `PROJECT_STATUS.md` reflect completed tasks.
- Validation artifacts are linked from `validation/`.

## Notes

Do not start task 9 until the current browser proof gap is closed and task 8 is accepted.
