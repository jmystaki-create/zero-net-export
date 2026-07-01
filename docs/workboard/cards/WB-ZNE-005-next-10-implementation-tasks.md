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
5. ~~Validate Stage 1 with repo tests.~~ (Done)
6. ~~Implement Stage 2 priority/readiness filters, sorting, enhanced columns, and bulk actions.~~ (Done)
7. ~~Live-validate the complete Stage 1+2 Managed Devices fleet workflow through GitHub/HACS, restart, fingerprint, browser proof, and logs.~~ (Done in `v0.2.5`, including populated `light.7th` proof)
8. ~~Add or identify a safe disposable managed device, then live-test populated Managed Devices rows and reversible bulk enable/disable.~~ (Done with `light.7th`; final ZNE record remains disabled)
9. ~~Decide whether bulk priority adjustment is required before closing Milestone 3, or move it to a later milestone.~~ (Deferred to a later milestone)
10. ~~Read-only inspect current live source-health warnings and classify blockers.~~ (Done; Milestone 4 baseline recorded)

## Next Active Tasks

1. Apply or guide the `sensor.anker_battery_discharge_power` template sensor
   workaround from `docs/SOURCE_HEALTH_FIX_GUIDE.md`.
2. Point ZNE at the fixed battery discharge source.
3. Capture live API proof for `sensor.zero_net_export_status=ok`.
4. Capture Diagnostics browser proof for the resolved source-health state.
5. Decide whether Milestone 4 needs a ZNE-side fallback release (`v0.2.6`) or
   closes as a Home Assistant configuration fix.

Standing rule: keep the OpenClaw Workboard updated on every ZNE turn, including
status, blockers, validation evidence, and next action.

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
