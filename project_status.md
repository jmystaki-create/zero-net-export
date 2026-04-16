# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: ask James directly to approve the formal `0.1.85` release flow now, then reconcile the live `0.1.86` manifest drift back to the exact `0.1.85` repo candidate, rerun fingerprint validation to `overall_match=true`, and continue live native-UI validation

# Current blocker or none
blocker: formal release approval is still required before redeploy/restart work, and the live install is still a mixed release state with a `0.1.86` manifest on top of the current `0.1.85` repo candidate

# Exact user action needed or none
user_action: James: approve the formal `0.1.85` Zero Net Export release execution now so the live `0.1.86` manifest drift can be reconciled, fingerprint validation can return to `overall_match=true`, and end-to-end HA validation can proceed

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, and keep version tracking explicit across local repo state, remote GitHub state, and public release state

# Last time this file materially changed
last_modified: 2026-04-16 14:16
