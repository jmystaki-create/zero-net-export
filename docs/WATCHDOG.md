# WATCHDOG.md

This file steers the Zero Net Export watchdog.

## Source of truth

`CONSTRAINTS.md` is the highest-priority audit rulebook for this repository. If any other document conflicts with `CONSTRAINTS.md`, `CONSTRAINTS.md` wins.

Audit against:

1. `CONSTRAINTS.md`
2. `PROJECT_STATUS.md`
3. `docs/ACTIVE_USER_REQUESTS.md`
4. `docs/BUGS.md`
5. current repo/test/live evidence
6. `/root/.openclaw/workspace/TOOLS.md` when Home Assistant access is relevant

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

- audits every task, plan, code change, release-prep note, and status update against `CONSTRAINTS.md`
- catches stale docs/cron/tests restoring deprecated UI-map behavior or any custom frontend/panel direction without explicit approval
- catches work that skipped the required `CONSTRAINTS.md` feasibility classification before implementation
- catches code or tests that still require `Un Managed — ...` peer rows
- catches missing gear/settings affordance coverage
- applies a small safe correction to agent/process docs/tests/code when obvious and allowed by `CONSTRAINTS.md`
- updates `docs/BUGS.md` when a bug state materially changes

Do not use deprecated design-map wording as an audit basis.
Do not restore old `0.1.91` / `1.91` release-scope behavior unless Riley explicitly asks for it.
If nothing materially changed, report a concise no-change watchdog update.
