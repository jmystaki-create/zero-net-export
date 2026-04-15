# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: ask James directly for approval to redeploy the exact current shipped-component `0.1.83` candidate, rerun the fingerprint check until it reports `overall_match=true`, then re-open Configure and continue native-UI validation on the exact installed candidate

# Current blocker or none
blocker: the live Home Assistant install no longer matches the current repo candidate, so further Configure/native-UI validation would be against a stale build until the exact repo candidate is redeployed with explicit release approval

# Exact user action needed or none
user_action: approve redeploying the exact current shipped-component `0.1.83` candidate to Home Assistant so fingerprint validation can return to `overall_match=true` and live native-UI validation can continue on the exact installed build

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, and keep version tracking explicit across local repo state, remote GitHub state, and public release state

# Last time this file materially changed
last_modified: 2026-04-16 07:11
