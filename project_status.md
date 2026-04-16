# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: ask James directly whether to proceed with the formal `0.1.86` release-reconciliation flow now, because GitHub already shows `v0.1.86` as the latest published release and the remaining blocker is Home Assistant-side exact-build/HACS reconciliation; name `f4b6f09` as the current component candidate, then push or intentionally deploy that exact candidate to resolve the remaining live `button.py`, `candidate_utils.py`, `config_flow.py`, `diagnostics.py`, `native_support.py`, `sensor.py`, `strings.json`, and `translations/en.json` drift before any `0.1.87` UI-release claim

# Current blocker or none
blocker: GitHub release visibility is now confirmed for `v0.1.86`, but the live Home Assistant install is still not fingerprint-aligned because `button.py`, `candidate_utils.py`, `config_flow.py`, `diagnostics.py`, `native_support.py`, `sensor.py`, `strings.json`, and `translations/en.json` do not match the current repo candidate, and local HEAD (`fee2d5d`) is also ahead of `origin/main` (`a70ee31`), so the real next boundary is explicit release approval for the HACS/exact-build reconciliation flow rather than more implied deploy/restart guidance

# Exact user action needed or none
user_action: James must explicitly approve the formal `0.1.86` release/reconciliation flow before deploy, restart, HACS refresh, or live validation continues

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, and distinguish the live `0.1.86` correction line from the next `0.1.87` UI rollout target

# Last time this file materially changed
last_modified: 2026-04-17 04:20
