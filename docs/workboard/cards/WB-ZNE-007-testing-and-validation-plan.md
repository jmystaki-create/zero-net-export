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
- Latest release validation is recorded in `validation/0.2.4-release-validation.md`.
- Sources browser proof gap is closed with desktop and narrow installed-app artifacts.

## Current Gap

Sources workflow has installed desktop and narrow browser proof on `0.2.4`.
