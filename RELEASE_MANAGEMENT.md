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
- open HACS
- locate **Zero Net Export**
- open the three-dot menu on the right
- click **Update information**

This forces HACS to refresh package metadata instead of waiting passively.

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

### 7. Restart Home Assistant
After a Zero Net Export Python/config-flow/runtime release:
- restart Home Assistant

Current rule: restart is the safe default after these releases, even if a reload-only path may become possible later.

### 8. Review Home Assistant logs for project-specific errors
After restart, inspect Home Assistant logs specifically for Zero Net Export related errors, warnings, retries, tracebacks, or runtime regressions.

This review should:
- focus on errors specific to this project/integration
- identify whether the just-released fix actually cleared the intended failure
- capture any newly exposed project-specific errors
- feed those findings into the next release automatically, without waiting for the user to restate them

### 9. Verify the live result
After restart and log review, verify live Home Assistant state, ideally via API plus UI where useful:
- config entry state
- current installed version if exposed
- presence of Zero Net Export entities
- whether the release-specific bug is fixed
- whether a new blocker appears

### 10. Report completion
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
- [ ] tag created and pushed
- [ ] GitHub release published/visible
- [ ] GitHub latest-release state verified after approval
- [ ] HACS `Update information` triggered
- [ ] HACS shows target version
- [ ] HACS upgraded package
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
