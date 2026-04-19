# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: stop spending runs on stale-hash cleanup; the current component-changing candidate is exact build `78c5023`, so first judge whether any remaining repo-side operator-console or Managed Devices wording drift still needs fixing before freeze, and only then ask James directly for explicit deploy/restart approval on that build

# Current blocker or none
blocker: unchanged live exact-build drift, confirmed again over the documented HA SSH path; the live install is still a divergent `0.1.87` build, but the immediate repo-side ranking drift was the stale `e316257` approval target rather than a new live failure

# Exact user action needed or none
user_action: none until the `78c5023` cut line is judged coherent enough for formal deploy/restart approval

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, and keep `0.1.86` as the current live correction line until `0.1.87` is explicitly frozen, approved, shipped, and validated. A live divergent `0.1.87` install is release drift, not a steering change.

# Last time this file materially changed
last_modified: 2026-04-19 21:07
