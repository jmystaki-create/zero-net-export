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
- `validation/zne-595-recorder-attribute-budget.md`
- `validation/0.4.12-release-validation.md`
- `validation/zne-597-battery-power-source-mapping.md`

## Current Focus

ZNE-599 is open/high and is the immediate corrective priority. The installed
`v0.4.12` Managed Devices app opens the unmanaged-candidate `Review & promote`
workflow, but the required confirmation checkbox does not stay pressed and the
candidate is not added to the managed Fleet List.

ZNE-595 is released/live-validated fixed in `v0.4.12`; the recorder
attribute-size warning blocker is closed. ZNE-597 is shipped in `v0.4.4` but
still needs a focused installed Battery Power/unit display proof before full bug
closure. Historical fixed bugs remain in `docs/BUGS.md`.
