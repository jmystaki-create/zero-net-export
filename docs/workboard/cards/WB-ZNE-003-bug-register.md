# WB-ZNE-003 Bug Register

Status: Ready
Priority: High
Labels: bugs, qa, validation, release-readiness

## Purpose

Maintain a clear bug register that distinguishes active defects, fixed/live-validated defects, and validation gaps.

## Acceptance Criteria

- Active bugs and validation gaps are summarized.
- Fixed bugs remain linked to `docs/BUGS.md` without re-opening historical work.
- Each active bug has expected behavior, evidence, next action, and closure criteria.
- Release-impacting bugs are prioritized ahead of new feature work.

## Evidence Needed To Mark Done

- `docs/BUGS.md` is current.
- Workboard known-bugs section reflects current active risk.
- Each bug closure has repo validation and live validation where applicable.

## Current Evidence

- `docs/BUGS.md`
- `validation/zne-594-state-length-feasibility.md`
- `validation/zne-594-state-length-implementation.md`
- `validation/0.2.4-release-validation.md`

## Current Focus

ZNE-594 is released/live-validated fixed in `0.2.4`. The active quality gap is not a new bug: it is missing installed browser proof for the Sources workflow.
