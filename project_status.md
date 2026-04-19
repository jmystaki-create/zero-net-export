# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: either ship the next actual component-changing `0.1.87` repo-side UI step from `docs/UI_IMPLEMENTATION_MAP.md`, or if the candidate is already coherent enough for release execution, ask James directly for explicit deploy/restart approval to ship exact build `481c9a7`; do not spend another run on doc-only release-anchor refreshes for the unchanged candidate

# Current blocker or none
blocker: unchanged live exact-build drift, confirmed again over the documented HA SSH path; the live install is still on a divergent `0.1.87` build, but repeating fingerprint or anchor bookkeeping without a new component build or approval is loop churn rather than progress

# Exact user action needed or none
user_action: none until the current repo-side `0.1.87` cut line is coherent enough to justify an explicit deploy/restart approval ask

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, and keep `0.1.86` as the current live correction line until `0.1.87` is explicitly frozen, approved, shipped, and validated. A live divergent `0.1.87` install is release drift, not a steering change.

# Last time this file materially changed
last_modified: 2026-04-19 15:03
