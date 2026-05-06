# SUPERVISOR.md

This file steers the Zero Net Export supervisor.

## Source of truth

`CONSTRAINTS.md` is the highest-priority rulebook for this repository. If any other document conflicts with `CONSTRAINTS.md`, `CONSTRAINTS.md` wins.

Use these documents, in order:

1. `CONSTRAINTS.md`
2. `PROJECT_STATUS.md`
3. `docs/ACTIVE_USER_REQUESTS.md`
4. `docs/BUGS.md`
5. current repo/test/live evidence
6. `/root/.openclaw/workspace/TOOLS.md` when Home Assistant access is needed

Deprecated and non-authoritative:

- `docs/UI_DESIGN.md`
- `docs/UI_IMPLEMENTATION_MAP.md`
- old version-specific release plans unless explicitly referenced by the current bug/request

## Current mission

Make concrete progress on Riley's highlighted bugs/features only:

- managed devices must be the only peer rows in the native integration/device list
- managed-device rows/actions need an obvious visible settings/gear affordance
- unmanaged candidates must not appear as peer `Un Managed — ...` rows beside managed devices
- unmanaged candidates should remain available behind Managed Devices workflow/backlog/review surfaces
- do not tag, release, deploy, restart Home Assistant, or claim release readiness without explicit approval and screenshot proof

## Run behavior

Every supervisor run should:

1. read `CONSTRAINTS.md` before any task intake, planning, coding, release preparation, or status update
2. read `PROJECT_STATUS.md`, `docs/ACTIVE_USER_REQUESTS.md`, and `docs/BUGS.md`
3. classify the requested behavior against `CONSTRAINTS.md` before coding or proposing implementation work
4. inspect current repo state before deciding work
5. implement or verify only the smallest allowed native/process change for the highlighted bugs/features
6. update `docs/BUGS.md` when a bug is confirmed, fixed, invalidated, or superseded
7. run focused tests for touched behavior, and broader tests when practical
8. report only the delta from this run, including whether the work stayed inside `CONSTRAINTS.md`

Do not spend runs defending or restoring deprecated design-map requirements.
Do not reopen old `0.1.91` / `1.91` scope unless Riley explicitly asks for it.
Do not treat old `Un Managed — ...` peer-row behavior as required; current guidance says those rows should be suppressed/removed from the peer list.

## User approval gates

Ask Riley before:

- deploying to Home Assistant
- restarting Home Assistant
- tagging or publishing a release
- claiming screenshot/live validation complete

The release candidate is not ready until repo tests pass and live screenshot evidence proves the highlighted UI behavior.
