# Zero Net Export 0.1.89 Release Plan

## Purpose

`0.1.89` is the clean follow-up release line for the UI fixes that landed after the already-published `v0.1.88` GitHub release.

Do **not** move or rewrite the published `v0.1.88` tag unless James explicitly asks for a retag. The safer path is to cut `v0.1.89` from the current helper-resolved component build once final gates pass.

## Current baseline at plan creation

- Published `v0.1.88` release/tag: already exists and should be treated as immutable unless explicitly overridden.
- Local release-planning baseline: repo `HEAD` was `bed3f82` when this plan was created.
- Helper-resolved component build at that point: `045f9a0`.
- Manifest still reports `0.1.88`; the version bump to `0.1.89` is part of the formal freeze step, not an accidental side effect of planning.
- Repo tests at the prior UI-completion check passed with `408` tests.

Always re-run `scripts/print_expected_install_fingerprint.py` immediately before release; the helper output is the source of truth for the final component-changing commit.

## Why 0.1.89 exists

After `v0.1.88` was published, repo-side UI fixes continued. Those fixes are exactly the kind of polish that should be in the build James tests if the goal is to validate the full `docs/UI_DESIGN.md` outcome.

The follow-up line avoids the ambiguity of a republished `0.1.88` while preserving a clean install/update path through GitHub/HACS.

## Scope

`0.1.89` should be a **release-correction and validation release**, not a new feature expansion.

It should include:

1. **Post-0.1.88 UI polish already landed in repo**
   - workspace-first promotion/manual-add fallback wording
   - disabled fleet counts in command center, Managed Devices, sensors, and device-page review snapshots
   - source blockers kept global/first in fleet activity sensors
   - compact source-repair and Diagnostics fallback wording
   - no-candidate Managed Devices fallback labels that stay inside workspace language
   - command-center source setup wording using operator-facing `Source blockers` language instead of mapped-source jargon

2. **0.1.89 version freeze**
   - bump `custom_components/zero_net_export/manifest.json` to `0.1.89`
   - align version-coupled tests/fixtures
   - add a dated `0.1.89` changelog section
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

### A. Freeze candidate

- [ ] Confirm repo is clean.
- [ ] Confirm current helper-resolved component build with `python3 scripts/print_expected_install_fingerprint.py --write-json tmp/expected-install-fingerprint.json`.
- [ ] Bump manifest/version-coupled expectations to `0.1.89`.
- [ ] Move relevant Unreleased changelog entries under `0.1.89` with release date.
- [ ] Run full tests: `python3 -m unittest discover -s tests -q`.
- [ ] Commit the freeze.

### B. Publish

- [ ] Push `main`.
- [ ] Create annotated tag `v0.1.89` at the approved freeze commit.
- [ ] Push `v0.1.89`.
- [ ] Publish GitHub release `Zero Net Export v0.1.89` from changelog notes.
- [ ] Verify GitHub latest release API returns `v0.1.89`, non-draft, non-prerelease.

### C. James install/test path

- [ ] James refreshes HACS metadata with **Update information**.
- [ ] James installs/updates to `v0.1.89`.
- [ ] James restarts Home Assistant.
- [ ] OpenClaw validates the live install fingerprint over the documented HA SSH path.
- [ ] OpenClaw checks Home Assistant logs for Zero Net Export-specific warnings/errors.
- [ ] James/OpenClaw inspect screenshots or live UI for the six `docs/UI_IMPLEMENTATION_MAP.md` acceptance outcomes.

## Acceptance outcomes

`0.1.89` is successful only if the live Home Assistant install shows:

1. Configure command center reads as a setup-first operator console with current operating picture visible.
2. Managed vs unmanaged devices are visually obvious in Configure -> Managed Devices.
3. Promote / vet / review is first-class and coherent.
4. Controls / Sensors / Managed Devices / Diagnostics are clearly distinct.
5. Device-page managed-device review is useful but secondary to Configure -> Managed Devices.
6. Runtime/setup/support notifications are tighter and easier to act on.
7. Live fingerprint matches the intended `0.1.89` build.
8. Zero Net Export logs do not reveal a new release-blocking regression.

## If validation fails

- Record exact evidence in `docs/BUGS.md`.
- Decide whether the issue is:
  - install drift / stale HACS cache,
  - live HA rendering mismatch,
  - runtime/load regression,
  - or genuine repo defect.
- Fix only the smallest release-blocking issue needed for a credible `0.1.89` candidate.
- Re-run the freeze gates before publishing any replacement build.
