# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: audit the highest remaining mapped `0.1.87` repo-side A-D/F gap and ship the next concrete native-HA fix; do not let another unchanged fingerprint or deploy-approval cycle displace unfinished implementation-map runway

# Current blocker or none
blocker: none; the unchanged live exact-build mismatch remains a release-gate problem, but it is not the default blocker while mapped repo-side `0.1.87` work still remains

# Exact user action needed or none
user_action: none

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, keep `0.1.86` as the current live correction line until `0.1.87` is explicitly frozen, approved, shipped, and validated, and treat the unchanged divergent live `0.1.87` install as release drift rather than as the default next-step ranking while implementation-map runway still exists.

# Last time this file materially changed
last_modified: 2026-04-19 23:01
