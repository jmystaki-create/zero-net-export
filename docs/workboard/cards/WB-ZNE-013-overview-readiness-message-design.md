# WB-ZNE-013 Overview Readiness Message Design

Status: released_live_validated_v0.4.5
Labels: application, overview, readiness, ux, validation
Owner: dev
Created: 2026-07-08
Last updated: 2026-07-15

## Purpose

Track Riley's follow-up that the v0.4.3 Overview Readiness section is still
poor and hard to understand. The UI must stop exposing dense command-center
strings and instead explain the current readiness state in plain operational
language.

## Linked items

- `ZNE-FR-014` - Overview Readiness should use plain action-oriented messages.
- Builds on released `ZNE-FR-013`.

## Acceptance Criteria

- Readiness does not render raw command-center/device queue strings as
  label/value rows.
- The card starts with a short verdict.
- The first action is labelled as the first action, not as a path dump.
- Source, reconciliation, controls, and managed-device queue issues are shown
  as concise facts plus ordered resolution steps.
- Narrow cards remain readable without clipped or right-aligned paragraphs.

## Feasibility

Supported in the existing ZNE-owned Home Assistant custom panel using current
`hass.states` data and CSS. No Home Assistant frontend patch, native page
injection, direct live install write, or new recorder-backed attributes are
required.

## Validation

- Repo validation recorded in `validation/zne-fr-014-readiness-message-design.md`.
- Release/live validation recorded in `validation/0.4.5-release-validation.md`.

## Next Steps

No remaining action for this feature request. Continue to check Readiness copy
opportunistically during future app browser validation.
