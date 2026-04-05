# Release Process

This document describes how Zero Net Export releases are managed.

## Goals

- Keep `manifest.json` version aligned with the current intended release version.
- Keep `CHANGELOG.md` updated for every user-visible change.
- Produce clear release notes for each tagged version.
- Make it easy to publish Git tags and GitHub releases consistently.
- Make the Home Assistant / HACS-visible update path verifiable instead of assuming local commits or manifest-only bumps are enough.

## Versioning Policy

Use semantic-style versions where practical:

- `MAJOR`: breaking changes or major redesigns
- `MINOR`: new features, significant capability growth
- `PATCH`: fixes, compatibility updates, metadata/docs polish that affects installability or usability

Examples:
- `0.1.0` — first public baseline
- `0.1.1` — compatibility or install fix
- `0.2.0` — new capabilities or meaningful behavior expansion
- `1.0.0` — stable, validated release after real-world sign-off

## Files to Update for a Release

At minimum:

1. `custom_components/zero_net_export/manifest.json`
   - Update `version`
2. `CHANGELOG.md`
   - Move the relevant items from `Unreleased` into a versioned section
3. `branding/` assets
   - Update if the public project icon or logo changes
4. Optional: `README.md`
   - Update wording if release status materially changes
5. Optional: `docs/BRANDING.md`
   - Update if branding usage or packaging changes

## Standard Workflow

### For normal development changes

1. Make the code/docs change
2. Add a short user-facing entry to `CHANGELOG.md` under `## [Unreleased]`
3. Commit normally

### For a formal release

1. Decide the new version
2. Update `manifest.json` version
3. Move/organize changelog items into a dated version section
4. Commit with a release-oriented message, for example:
   - `release: prepare 0.1.1`
5. Create a git tag, for example:
   - `git tag v0.1.1`
6. Push branch and tag:
   - `git push origin main`
   - `git push origin v0.1.1`
7. Publish a GitHub Release using the matching version notes

## Critical HACS Reality Check

Manifest version bumps alone are **not** enough for the real user-facing HACS update path.

If the latest code only exists in local commits, or if the repository branch is ahead locally but the remote default branch and release tags are not updated, Home Assistant users will continue to receive the old packaged integration.

Treat these checks as mandatory before claiming a release is shipped:

1. `git status` is clean enough to release intentionally.
2. `git log origin/main..HEAD` is empty **after** pushing the release branch state.
3. `git tag --sort=-creatordate` includes the new version tag.
4. `git ls-remote --heads --tags origin` shows both the updated default branch commit and the new version tag on the remote.
5. A GitHub Release exists for the same version tag if the repo is using release-based discovery/visibility.
6. The packaged files on the remote include the intended onboarding/config-flow and frontend bundle changes.

If any of those checks fail, treat the release as **not yet user-visible**.

## Release Notes Template

Use this structure when creating a GitHub release:

```md
## Zero Net Export vX.Y.Z

### Added
- ...

### Changed
- ...

### Fixed
- ...

### Notes
- ...
```

## Current State

As of this document:
- the repository is under active versioned maintenance
- the first formal GitHub release may still need to be published manually if no tag exists yet

## Responsibility

Release management includes:
- keeping versions current
- updating changelog entries
- preparing release notes
- creating and pushing git tags when requested and when safe to do so
- verifying that the remote repo state now matches what HACS / Home Assistant users will actually install

GitHub web release publication may still require either:
- manual browser publication, or
- a separately configured GitHub API credential path
