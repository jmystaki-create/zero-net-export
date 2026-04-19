# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: stop spending runs on stale-hash cleanup; the current component-changing candidate is exact build `2d730e1`, so first judge whether the tighter Configure Diagnostics triage copy leaves any fresh mapped drift before freeze, and only then ask James directly for explicit deploy/restart approval on that build

# Current blocker or none
blocker: unchanged live exact-build drift, confirmed again over the documented HA SSH path; the live install is still a divergent `0.1.87` build, and release approval should only be considered against the current component-changing candidate `2d730e1` rather than any older stale target

# Exact user action needed or none
user_action: none until the `2d730e1` cut line is judged coherent enough for formal deploy/restart approval

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, and keep `0.1.86` as the current live correction line until `0.1.87` is explicitly frozen, approved, shipped, and validated. A live divergent `0.1.87` install is release drift, not a steering change.

# Last time this file materially changed
last_modified: 2026-04-19 22:23
