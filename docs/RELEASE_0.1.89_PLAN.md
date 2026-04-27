# Zero Net Export 0.1.89 Release Plan

## Superseded status

This plan is historical. `v0.1.89` was frozen, published, installed, restarted, and fingerprint-verified, but James's live device-page screenshot showed it did not deliver the required Managed Devices device-page surface.

Do not use this file as the active release plan or ask James to repeat the `0.1.89` install/restart/live-validation loop. The active corrective release plan is `docs/RELEASE_0.1.90_PLAN.md`, tracked by `ZNE-411`.

## Purpose

`0.1.89` was the clean follow-up release line for the UI fixes that landed after the already-published `v0.1.88` GitHub release.

Do **not** move or rewrite the published `v0.1.88` tag unless James explicitly asks for a retag. The safer path was the already-completed `0.1.89` follow-up release line.

## Current baseline at plan creation

- Published `v0.1.88` release/tag: already exists and should be treated as immutable unless explicitly overridden.
- Local release-planning baseline: repo `HEAD` was `bed3f82` when this plan was created.
- Helper-resolved component build at that point: `045f9a0`.
- Manifest still reports `0.1.88`; the version bump to `0.1.89` is part of the formal freeze step, not an accidental side effect of planning.
- Repo tests at the prior UI-completion check passed with `408` tests.

Always re-run `scripts/print_expected_install_fingerprint.py` immediately before release; the helper output is the source of truth for the final component-changing commit.

## Current execution state

- `v0.1.89` is now frozen and tagged at `844502b` (`release: freeze 0.1.89`).
- The pushed `v0.1.89` tag resolves to `844502b`; `origin/main` may include later docs-only state updates that do not change the component validation boundary.
- The GitHub release `Zero Net Export v0.1.89` is published, non-draft, non-prerelease, and currently reported as the latest release.
- The repo manifest now reports `0.1.89`; the old pre-freeze instruction that the manifest still reports `0.1.88` is historical baseline only.
- Current helper output reports `manifest_version=0.1.89` and `preferred_validation_commit=844502b`; the preferred component validation boundary remains the frozen tag even when later repo `HEAD` commits are docs-only.
- Repo tests at the freeze audit passed with `480` tests.

From here, do not ask James for permission to perform the already-completed version freeze again, repeat the already-completed GitHub publication check, or rerun the now-failed `0.1.89` install/restart/live-validation loop. The corrective `0.1.90` release/deploy/restart and fingerprint boundary is now complete; the remaining release-execution gap is screenshot-grade device-page Managed Devices evidence and action drill-down validation, unless a materially new release-blocking defect appears.

## Why 0.1.89 exists

After `v0.1.88` was published, repo-side UI fixes continued. Those fixes are exactly the kind of polish that should be in the build James tests if the goal is to validate the full `docs/UI_DESIGN.md` outcome.

The follow-up line avoids the ambiguity of a republished `0.1.88` while preserving a clean install/update path through GitHub/HACS.

## Scope

`0.1.89` was a **release-correction and validation release**, not a new feature expansion.

It should include:

1. **Post-0.1.88 UI polish already landed in repo**
   - workspace-first promotion/manual-add fallback wording
   - disabled fleet counts in command center, Managed Devices, sensors, and device-page review snapshots
   - source blockers kept global/first in fleet activity sensors
   - compact source-repair and Diagnostics fallback wording
   - no-candidate Managed Devices fallback labels that stay inside workspace language
   - command-center source setup wording using operator-facing `Source blockers` language instead of mapped-source jargon

2. **0.1.89 version freeze**
   - `custom_components/zero_net_export/manifest.json` is bumped to `0.1.89`
   - version-coupled tests/fixtures are aligned
   - the dated `0.1.89` changelog section exists
   - keep `0.1.88` history intact

3. **Release validation gates**
   - full unit test suite
   - expected install fingerprint captured
   - clean working tree
   - upstream/tag state checked before publishing
   - GitHub release visible as latest after publish

4. **Live Home Assistant validation after James installs**
   - HACS shows and installs `v0.1.89`
   - Home Assistant restarted
   - live install fingerprint matches the intended `0.1.89` build
   - logs checked for Zero Net Export errors/warnings
   - Configure command center reviewed
   - Managed Devices workspace reviewed
   - promotion/review flow reviewed
   - Controls / Sensors / Managed Devices / Diagnostics split reviewed
   - runtime/setup/support notifications reviewed

## Non-goals

Do not add new product surface area to `0.1.89` unless a blocker appears during validation.

Specifically avoid:

- optional dashboard work
- broad backend rewrites
- speculative wording churn that does not change the live HA experience
- doc-only release-boundary refreshes after the release target is already clear
- repeating unchanged live fingerprint mismatch notes unless the installed build changes

## Execution checklist

### A. Approval and freeze candidate

- [x] Confirm repo is clean.
- [x] Confirm current helper-resolved component build with `python3 scripts/print_expected_install_fingerprint.py --write-json tmp/expected-install-fingerprint.json`.
- [x] Freeze the `0.1.89` version-coupled release files.
- [x] Move relevant Unreleased changelog entries under `0.1.89` with release date.
- [x] Run full tests: `python3 -m unittest discover -s tests -q`.
- [x] Commit the approved freeze: `844502b`.

### B. Publish

- [x] Push `main`.
- [x] Create annotated tag `v0.1.89` at the approved freeze commit.
- [x] Push `v0.1.89`.
- [x] Publish GitHub release `Zero Net Export v0.1.89` from changelog notes.
- [x] Verify GitHub latest release API returns `v0.1.89`, non-draft, non-prerelease.

### C. James install/test path (historical, completed and failed)

- [x] James refreshed HACS metadata / installed or updated to `v0.1.89`.
- [x] James restarted Home Assistant.
- [x] OpenClaw validated the live install fingerprint over the documented HA SSH path; the deployed `0.1.89` build matched.
- [x] James inspected the live Zero Net Export device page.
- [x] James's live screenshot showed the device page did not visibly deliver the requested Managed Devices surface.
- [x] The failed device-page evidence is now tracked by `ZNE-411` and superseded by `docs/RELEASE_0.1.90_PLAN.md`.

Do not use this historical checklist to ask James to repeat the `0.1.89` install/restart/live-validation loop. The `0.1.90` approval, freeze, deploy, restart, and fingerprint path is now complete; the remaining release-execution gap is screenshot-grade device-page validation and Managed Devices action drill-down proof.

## Acceptance outcomes (historical, failed on device-page evidence)

`0.1.89` would have been successful only if the live Home Assistant install showed:

1. Configure command center reads as a setup-first operator console with current operating picture visible.
2. Managed vs unmanaged devices are visually obvious in Configure -> Managed Devices.
3. Promote / vet / review is first-class and coherent.
4. Controls / Sensors / Managed Devices / Diagnostics are clearly distinct.
5. Device-page managed-device review is useful but secondary to Configure -> Managed Devices.
6. Runtime/setup/support notifications are tighter and easier to act on.
7. Live fingerprint matches the intended `0.1.89` build.
8. Zero Net Export logs do not reveal a new release-blocking regression.

## Validation failure outcome

Validation did fail on the device-page Managed Devices outcome after the installed package was fingerprint-verified. That failure is no longer an open `0.1.89` release loop.

- Exact evidence is recorded in `docs/BUGS.md` under `ZNE-411`.
- The issue is a genuine native device-page product/UI gap, not install drift or stale HACS cache.
- Do not fix or republish another `0.1.89` candidate.
- Continue through `docs/RELEASE_0.1.90_PLAN.md` by capturing screenshot-grade device-page Managed Devices evidence and validating the Managed Devices action drill-down on the installed, fingerprint-matched `0.1.90` build.
