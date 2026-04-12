# Release Management

This file defines the standard release-management procedure for **Zero Net Export**.

## Goal

Ship a release all the way through to the real Home Assistant install, not just to GitHub.

A release is only considered complete when:
- code is committed and pushed,
- version/tag are aligned,
- GitHub release visibility is handled,
- HACS sees the new version,
- Home Assistant upgrades to that version,
- Home Assistant is restarted when required,
- the live integration is re-checked after restart.

## Operating Rule

The assistant manages this process, but must begin with explicit user approval to release.

## Standard Procedure

### 1. Ask for release approval
Before touching the live Home Assistant install, ask:
- whether to proceed with the release now
- which version/commit is being released, if not already obvious

No HACS or HA upgrade action should start before that approval.

### 2. Confirm release artifact exists
Before touching Home Assistant, confirm:
- target commit is on `main`
- target tag exists
- manifest version matches the intended release version
- changelog is updated
- GitHub release publication/visibility is complete or in progress as part of the same operation
- `python3 scripts/print_expected_install_fingerprint.py --write-json tmp/expected-install-fingerprint.json` reflects the exact repo build that is about to be deployed and saves one explicit expected commit plus tracked-file hash set for the later live-install comparison
- `python3 scripts/compare_install_fingerprint.py /path/to/home-assistant/config/custom_components --expected-json tmp/expected-install-fingerprint.json --write-json tmp/install-fingerprint-compare.json` is ready to compare that captured intended fingerprint against the actual install path immediately after deploy and before trusting restart validation, while also saving the comparison verdict as evidence

### 3. After approval, verify the latest version is actually published on GitHub
After the user approves release execution, but before touching HACS or Home Assistant, explicitly verify that the intended version is visible on GitHub as the newest release.

Minimum checks:
- the expected tag exists on the remote
- the corresponding GitHub release exists
- the GitHub release shows the intended version as the latest relevant release for this project
- the release payload/version visible on GitHub matches the manifest/tag version being deployed through HACS

If GitHub does not yet show the new release correctly, stop there and fix release publication/visibility first. Do not proceed to HACS until GitHub release state is confirmed.

### 4. Refresh HACS metadata in Home Assistant
In Home Assistant:
1. click **HACS**
2. in the HACS search bar, search for **Zero Net Export**
3. confirm the **Zero Net Export** row is visible in the HACS list, often under **Pending update** when an update path already exists
4. click the three-dot menu on the right side of the **Zero Net Export** row
5. click **Update information**

This forces HACS to refresh package metadata instead of waiting passively.

Practical note from real use: the reliable visual path is the HACS list row for **Zero Net Export** itself, found through HACS search, with the right-side three-dot overflow menu open. Do not rely on guessing a repository id or navigating by a fabricated direct HACS repository URL.

### 5. Wait for HACS to surface the new package version
Do not assume the update is visible immediately.

Wait until HACS shows the expected new version. If it does not appear:
- verify the GitHub release/tag state again
- refresh HACS metadata again if needed
- only proceed once the expected version is visible in HACS

### 6. Upgrade the package in HACS
Once the target version appears:
- trigger the HACS upgrade/install for the new version
- confirm HACS finishes the package update successfully

### 7. Compare the installed package against the intended repo build
Before trusting runtime validation after the package update:
- run `python3 scripts/compare_install_fingerprint.py /path/to/home-assistant/config/custom_components --expected-json tmp/expected-install-fingerprint.json --write-json tmp/install-fingerprint-compare.json`
- confirm the reported manifest version and tracked-file hashes all match the intended repo build
- if the comparison exits non-zero or does not fully match, stop and fix the install path/build mix before restart validation

### 8. Restart Home Assistant
After a Zero Net Export Python/config-flow/runtime release:
- restart Home Assistant

Current rule: restart is the safe default after these releases, even if a reload-only path may become possible later.

### 9. Review Home Assistant logs for project-specific errors
After restart, inspect Home Assistant logs specifically for Zero Net Export related errors, warnings, retries, tracebacks, or runtime regressions.

This review should:
- focus on errors specific to this project/integration
- identify whether the just-released fix actually cleared the intended failure
- capture any newly exposed project-specific errors
- feed those findings into the next release automatically, without waiting for the user to restate them

### 10. Verify the live result
After restart and log review, verify live Home Assistant state, ideally via API plus UI where useful:
- config entry state
- current installed version if exposed
- presence of Zero Net Export entities
- whether the release-specific bug is fixed
- whether a new blocker appears
- whether the installed package fingerprint shown in Configure or Health/support matches the intended repo build from `python3 scripts/print_expected_install_fingerprint.py`

### 11. Report completion
A release completion report should include:
- released version
- commit and tag
- whether GitHub release was published
- whether HACS updated successfully
- whether Home Assistant restarted successfully
- project-specific HA log findings after restart
- final HA verification result
- any remaining blocker or next step

## Release Checklist

- [ ] User explicitly approved release execution
- [ ] `main` contains intended release commit
- [ ] manifest version updated
- [ ] changelog updated
- [ ] Expected repo fingerprint captured with `python3 scripts/print_expected_install_fingerprint.py --write-json tmp/expected-install-fingerprint.json`
- [ ] tag created and pushed
- [ ] GitHub release published/visible
- [ ] GitHub latest-release state verified after approval
- [ ] HACS `Update information` triggered
- [ ] HACS shows target version
- [ ] HACS upgraded package
- [ ] Installed path compared with `scripts/compare_install_fingerprint.py --expected-json tmp/expected-install-fingerprint.json --write-json tmp/install-fingerprint-compare.json`
- [ ] Home Assistant restarted
- [ ] Project-specific HA logs reviewed after restart
- [ ] Live HA verification completed
- [ ] User notified of final result

## Current user-approved live release flow

When executing a release for Zero Net Export, use this user-preferred order:
1. Ask for approval to release
2. After approval, verify the new version is published on GitHub as the latest release
3. In HACS, use **Update information** on Zero Net Export
4. Wait for the updated package to appear
5. Upgrade to the new version in HACS
6. Restart Home Assistant
7. Review project-specific Home Assistant logs
8. Confirm release completion back to the user

## Notes

- For this project, push and release are treated as one operational workflow, not separate optional steps.
- Do not call a release done just because code was pushed.
- Live Home Assistant validation is part of release management.
- Before execution, present the release-management process back to the user when they ask to review it.
- Project-specific Home Assistant errors discovered during the post-release log review should be treated as input to the next Zero Net Export release by default, without waiting for the user to restate them.
