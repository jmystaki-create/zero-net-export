# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: stop spending runs on stale-hash cleanup; the repo candidate is now exact build `6cb7062`, so either ask James directly for explicit deploy/restart approval on that build or keep moving the next mapped non-live stage instead of repeating unchanged fingerprint bookkeeping

# Current blocker or none
blocker: unchanged live exact-build drift, confirmed again over the documented HA SSH path; the live install is still a divergent `0.1.87` build, and the real boundary is explicit deploy/restart approval for exact build `6cb7062`, not another release-target wording refresh

# Exact user action needed or none
user_action: James must explicitly approve deploy/restart of exact build `6cb7062` before formal release execution

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, and keep `0.1.86` as the current live correction line until `0.1.87` is explicitly frozen, approved, shipped, and validated. A live divergent `0.1.87` install is release drift, not a steering change.

# Last time this file materially changed
last_modified: 2026-04-19 18:36
