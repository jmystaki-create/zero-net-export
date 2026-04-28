# WATCHDOG.md

This file steers the Zero Net Export watchdog.

## Source of truth

Audit against:

1. `docs/ACTIVE_USER_REQUESTS.md`
2. `docs/BUGS.md`
3. current repo/test/live evidence
4. `/root/.openclaw/workspace/TOOLS.md` when Home Assistant access is relevant

Deprecated and non-authoritative:

- `docs/UI_DESIGN.md`
- `docs/UI_IMPLEMENTATION_MAP.md`
- old version-specific release plans unless a current bug/request explicitly needs them

## Current audit target

Catch drift away from Riley's highlighted bugs/features:

- managed-only peer rows in the integration/device list
- visible settings/gear affordance for managed devices
- no peer `Un Managed — ...` unmanaged-candidate rows beside managed devices
- unmanaged candidates still available through workflow/backlog/review surfaces
- no release/deploy/readiness claim without tests, approval, and screenshot proof

## Watchdog behavior

A watchdog run adds value when it:

- catches stale docs/cron/tests restoring deprecated UI-map behavior
- catches code or tests that still require `Un Managed — ...` peer rows
- catches missing gear/settings affordance coverage
- applies a small safe correction to docs/tests/code when obvious
- updates `docs/BUGS.md` when a bug state materially changes

Do not use deprecated design-map wording as an audit basis.
Do not restore old `0.1.91` / `1.91` release-scope behavior unless Riley explicitly asks for it.
If nothing materially changed, report a concise no-change watchdog update.
