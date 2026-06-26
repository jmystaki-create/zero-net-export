# WATCHDOG.md

This file steers the Zero Net Export watchdog.

## Source of truth

`CONSTRAINTS.md` is the highest-priority audit rulebook for this repository. If any other document conflicts with `CONSTRAINTS.md`, `CONSTRAINTS.md` wins.

Audit against:

1. `CONSTRAINTS.md`
2. `PROJECT_STATUS.md`
3. `docs/ZNE_APPLICATION_DIRECTION.md`
4. `docs/ACTIVE_USER_REQUESTS.md`
5. `docs/BUGS.md`
6. current repo/test/live evidence
7. `/root/.openclaw/workspace/TOOLS.md` when Home Assistant access is relevant

Deprecated and non-authoritative:

- `docs/UI_DESIGN.md`
- `docs/UI_IMPLEMENTATION_MAP.md`
- old version-specific release plans unless a current bug/request explicitly needs them

## Current audit target

Catch drift away from the Home Assistant application direction:

- Zero Net Export is a Home Assistant application backed by the integration backend
- app/panel work is approved and expected when it stays within `CONSTRAINTS.md`
- native device/config-entry/entity surfaces are supporting surfaces, not the primary roadmap
- old native-only constraints must not be restored by stale docs/tests/process
- no release/deploy/readiness claim without tests, approval, and screenshot proof

## Watchdog behavior

A watchdog run adds value when it:

- audits every task, plan, code change, release-prep note, and status update against `CONSTRAINTS.md`
- catches stale docs/cron/tests restoring deprecated UI-map behavior or the old custom-frontend/panel ban
- catches work that skipped the required `CONSTRAINTS.md` feasibility classification before implementation
- catches work that tries to make native device pages carry the full product workflow again
- catches missing application feasibility, acceptance criteria, or browser validation coverage
- applies a small safe correction to agent/process docs/tests/code when obvious and allowed by `CONSTRAINTS.md`
- updates `docs/BUGS.md` when a bug state materially changes

Do not use deprecated design-map wording as an audit basis.
Do not restore old `0.1.91` / `1.91` release-scope behavior unless Riley explicitly asks for it.
If nothing materially changed, report a concise no-change watchdog update.
