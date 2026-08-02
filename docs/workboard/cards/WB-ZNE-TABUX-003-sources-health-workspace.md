# WB-ZNE-TABUX-003 Sources Health Workspace

Status: done
Priority: high
Type: UI/UX implementation workboard card
Source: `ui_ux_review.md` / Approved Operator Tabs Redesign

## Outcome

Sources becomes a source-health workspace that explains whether readings are trustworthy enough to control.

## Acceptance Criteria

- [x] Add a source health strip with ready/blocked/stale/missing/unknown status.
- [x] Promote source blocker and stale-source summaries.
- [x] Show per-source role, requirement level, status, live value, freshness/age, issue count, and bound entity.
- [x] Keep source edit fields and selected-plan scoped save behavior.
- [x] Add a control-impact panel explaining runtime impact.

## Validation

- [x] Focused frontend source test verifies the new source-health workspace markers.
- [ ] Browser proof is captured before release closeout.

## Implementation Note

Implemented as a frontend presentation redesign with existing source role helpers and service wiring.
