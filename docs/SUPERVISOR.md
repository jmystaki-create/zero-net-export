# SUPERVISOR.md

This file steers the Zero Net Export supervisor.

## Source of truth

Use these documents, in order:

1. `docs/ACTIVE_USER_REQUESTS.md`
2. `docs/BUGS.md`
3. current repo/test/live evidence
4. `/root/.openclaw/workspace/TOOLS.md` when Home Assistant access is needed

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

1. read `docs/ACTIVE_USER_REQUESTS.md` and `docs/BUGS.md`
2. inspect current repo state before deciding work
3. implement or verify the next safest fix for the highlighted bugs/features
4. update `docs/BUGS.md` when a bug is confirmed, fixed, invalidated, or superseded
5. run focused tests for touched behavior, and broader tests when practical
6. report only the delta from this run

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
