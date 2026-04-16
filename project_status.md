# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: ask James directly to approve the formal `0.1.85` release flow now, then redeploy the exact repo candidate, clear the remaining `candidate_utils.py`, `entity.py`, and `sensor.py` fingerprint drift, and continue live native-UI validation

# Current blocker or none
blocker: formal release approval is still required before redeploy/restart work, and the installed component still has older `candidate_utils.py`, `entity.py`, and `sensor.py` files than repo HEAD

# Exact user action needed or none
user_action: James: approve the formal `0.1.85` Zero Net Export release execution so the end-to-end redeploy, restart, fingerprint recheck, and live HA validation can proceed

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, and keep version tracking explicit across local repo state, remote GitHub state, and public release state

# Last time this file materially changed
last_modified: 2026-04-16 12:15
