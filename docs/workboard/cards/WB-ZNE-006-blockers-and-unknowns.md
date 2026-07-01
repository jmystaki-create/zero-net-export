# WB-ZNE-006 Blockers And Unknowns

Status: Ready
Priority: High
Labels: blockers, risks, unknowns, validation

## Purpose

Track blockers and unknowns that could prevent the app MVP from being validated or released safely.

## Current Blockers / Unknowns

- Browser proof path for the installed Sources workflow is now proven through the OpenClaw browser CLI; use it for future app-facing proof.
- Runtime control remains limited by source-health warnings and managed-device readiness in the validation Home Assistant instance.
- Live validation must continue through GitHub/HACS only.
- Future app workflow scope needs milestone-specific acceptance criteria before implementation.
- Historical native-device-page documentation can create drift if used instead of the current source-of-truth order.

## Acceptance Criteria

- Each blocker has a next diagnostic step.
- Each unknown is classified as product, architecture, validation, or environment.
- User approval needs are explicit.
- Risks are reviewed before any new release or milestone starts.

## Evidence Needed To Mark Done

- Browser proof is captured or the blocker has a fresh diagnostic record.
- Runtime/source-health blockers are summarized with current live state evidence.
- `PROJECT_STATUS.md` and `ROADMAP.md` reflect any resolved blockers.

## Next Diagnostic Step

Re-test the browser automation path for `/zero-net-export` and the Sources tab, then capture desktop/narrow proof or document the specific blocker.
