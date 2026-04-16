# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: ask James directly whether to proceed with the formal `0.1.86` release-reconciliation flow now, then deploy one exact repo build that resolves the remaining live `sensor.py` drift before any further UI claims

# Current blocker or none
blocker: the live Home Assistant install is still not fingerprint-aligned because `sensor.py` does not match repo HEAD, and the real next boundary is explicit release approval rather than more implied deploy/restart guidance

# Exact user action needed or none
user_action: James must explicitly approve the formal `0.1.86` release/reconciliation flow before deploy, restart, HACS refresh, or live validation continues

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, and keep version tracking explicit across local repo state, remote GitHub state, and public release state

# Last time this file materially changed
last_modified: 2026-04-16 15:23
