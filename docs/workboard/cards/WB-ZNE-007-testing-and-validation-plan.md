# WB-ZNE-007 Testing And Validation Plan

Status: Ready
Priority: High
Labels: qa, validation, release, evidence

## Purpose

Define the validation standard for Zero Net Export work so cards cannot be marked complete based on assumptions.

## Standard Validation Stack

Repo validation:
- JavaScript syntax check for changed frontend assets.
- Python compile check for changed integration modules.
- Focused tests for the changed behavior.
- Full unittest discovery.
- `git diff --check`.

Live validation:
- Publish/install only through GitHub/HACS.
- Restart Home Assistant and wait for API recovery.
- Confirm installed/latest version and install fingerprint.
- Confirm app route and static asset route.
- Capture browser proof on desktop and narrow/mobile viewports for user-facing app work.
- Perform reversible live write proof only when safe and approved.
- Scan targeted Home Assistant logs for Zero Net Export errors/warnings/tracebacks.

## Acceptance Criteria

- Every Workboard card names the evidence needed to mark it done.
- User-facing app changes include browser proof.
- Backend writes include reversible proof where safe.
- Release cards include changelog, validation record, and risk review.

## Evidence Needed To Mark Done

- Validation plan is linked from active Workboard cards.
- Latest release validation is recorded in `validation/0.4.12-release-validation.md`.
- ZNE-595 recorder attribute cleanup has release/live validation evidence.
- ZNE-599 needs frontend/backend regression tests plus installed browser/API
  proof that a safe unmanaged candidate can be confirmed and promoted into the
  managed Fleet List.
- ZNE-597 still needs focused installed Battery Power/unit display proof.

## Current State

Latest installed release validation is `v0.4.12`. The next corrective validation
target is `ZNE-599`; because it changes the app promotion write path, closure
requires repo tests, frontend syntax validation, full discovery, GitHub/HACS
install, Home Assistant restart, browser/API proof of a safe promotion, original
entity preservation proof, and targeted log review.
