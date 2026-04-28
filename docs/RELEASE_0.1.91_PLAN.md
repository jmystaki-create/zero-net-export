# Zero Net Export 0.1.91 Release Plan — DEPRECATED

> **CURRENT STATUS: DEPRECATED/HISTORICAL.** Do not use this file as active release scope, acceptance criteria, deploy guidance, or validation authority. Current scope lives in `docs/ACTIVE_USER_REQUESTS.md` and current bug state lives in `docs/BUGS.md`.

## Why this plan is retired

This plan described the old `0.1.91` / release `1.91` integration-main-page device-list target. That target required both `Managed Devices — ...` rows and peer `Un Managed — ...` unmanaged-candidate rows under the Zero Net Export integration.

Riley's current highlighted scope supersedes that behavior:

1. Native integration/device peer rows must be **managed-only**.
2. Managed rows must visibly show a settings affordance such as `⚙ Settings`.
3. Peer `Un Managed — ...` unmanaged-candidate rows must be suppressed/removed, including stale registry rows from older builds.
4. Unmanaged candidates must remain available behind Managed Devices workflow/backlog/review surfaces instead of beside managed devices in the peer list.
5. No release, deploy, restart, fingerprint validation, readiness claim, or live screenshot validation is allowed without explicit Riley approval, passing tests, and screenshot proof for the current managed-only behavior.

## Historical note

The old release-target/fingerprint history, including `v0.1.91`, `v0.1.92`, `v0.1.93`, `v0.1.94`, and helper-resolved component boundaries, is historical process context only. It is not permission to deploy, restart Home Assistant, tag/release, fingerprint-validate, or call any candidate ready.

If this document conflicts with `docs/ACTIVE_USER_REQUESTS.md`, `docs/BUGS.md`, `docs/SUPERVISOR.md`, or `docs/WATCHDOG.md`, ignore this document and follow the current source of truth.
