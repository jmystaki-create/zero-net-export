# WB-ZNE-006 Blockers And Unknowns

Status: Ready
Priority: High
Labels: blockers, risks, unknowns, validation

## Purpose

Track blockers and unknowns that could prevent the app MVP from being validated or released safely.

## Current Blockers / Unknowns

- ZNE-599 currently blocks the app-native unmanaged-candidate promotion path:
  the confirmation checkbox does not stay pressed and the candidate is not added
  to the managed Fleet List.
- Browser proof path for the installed Sources workflow is now proven through the OpenClaw browser CLI; use it for future app-facing proof.
- Runtime/source-health state must be rechecked before each new workflow slice;
  latest release validation did not reopen a source-health blocker.
- Live validation must continue through GitHub/HACS only.
- Future app workflow scope needs milestone-specific acceptance criteria before implementation.
- Historical native-device-page documentation can create drift if used instead of the current source-of-truth order.

## Acceptance Criteria

- Each blocker has a next diagnostic step.
- Each unknown is classified as product, architecture, validation, or environment.
- User approval needs are explicit.
- Risks are reviewed before any new release or milestone starts.

## Evidence Needed To Mark Done

- Browser proof path remains available for app-facing validation.
- Runtime/source-health blockers are summarized with current live state evidence.
- `PROJECT_STATUS.md` and `ROADMAP.md` reflect any resolved blockers.

## Next Diagnostic Step

Reproduce/inspect `ZNE-599` in the Managed Devices promotion workflow, then
implement and release a corrective fix before scoping the next app milestone.
After `ZNE-599`, run the focused read-only `ZNE-597` Battery Power/unit proof
and inspect current live runtime/source-health readiness.
