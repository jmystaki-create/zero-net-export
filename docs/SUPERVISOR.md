# SUPERVISOR.md

This file steers the Zero Net Export supervisor.

## Source of truth

`CONSTRAINTS.md` is the highest-priority rulebook for this repository. If any other document conflicts with `CONSTRAINTS.md`, `CONSTRAINTS.md` wins.

Use these documents, in order:

1. `CONSTRAINTS.md`
2. `PROJECT_STATUS.md`
3. `docs/ZNE_APPLICATION_DIRECTION.md`
4. `docs/ACTIVE_USER_REQUESTS.md`
5. `docs/BUGS.md`
6. current repo/test/live evidence
7. `/root/.openclaw/workspace/TOOLS.md` when Home Assistant access is needed

Deprecated and non-authoritative:

- `docs/UI_DESIGN.md`
- `docs/UI_IMPLEMENTATION_MAP.md`
- old version-specific release plans unless explicitly referenced by the current bug/request

## Current mission

Make concrete progress on the Home Assistant application port:

- treat Zero Net Export as a Home Assistant application backed by the integration backend
- use `docs/ZNE_APPLICATION_DIRECTION.md` for the app scope, information architecture, and open decisions
- keep native Home Assistant surfaces as supporting/fallback/automation surfaces
- preserve the existing backend/control engine unless a scoped app milestone requires changes
- do not revive native-device-page polishing as the roadmap unless Riley explicitly asks for stabilization
- do not tag, release, deploy, restart Home Assistant, or claim release readiness without explicit approval and screenshot proof

## Run behavior

Every supervisor run should:

1. read `CONSTRAINTS.md` before any task intake, planning, coding, release preparation, or status update
2. read `PROJECT_STATUS.md`, `docs/ZNE_APPLICATION_DIRECTION.md`, `docs/ACTIVE_USER_REQUESTS.md`, and `docs/BUGS.md`
3. classify the requested behavior against `CONSTRAINTS.md` before coding or proposing implementation work
4. inspect current repo state before deciding work
5. implement or verify only the smallest allowed application/backend/process change for the active milestone
6. update `docs/BUGS.md` when a bug is confirmed, fixed, invalidated, or superseded
7. run focused tests for touched behavior, and broader tests when practical
8. report only the delta from this run, including whether the work stayed inside `CONSTRAINTS.md`

Do not spend runs defending or restoring deprecated design-map requirements.
Do not reopen old `0.1.91` / `1.91` scope unless Riley explicitly asks for it.
Do not treat the old native-device-page direction as current roadmap; current guidance says the product shell is the Home Assistant application.

## User approval gates

Ask Riley before:

- deploying to Home Assistant
- restarting Home Assistant
- tagging or publishing a release
- claiming screenshot/live validation complete

The release candidate is not ready until repo tests pass and live screenshot/browser evidence proves the approved application milestone behavior.
