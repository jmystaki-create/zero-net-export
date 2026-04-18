# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: finish or explicitly retire the next unfinished `0.1.87` repo-side UI workstream step in `docs/UI_IMPLEMENTATION_MAP.md` before elevating the same unchanged live fingerprint mismatch again; if the repo-side cut line later becomes release-ready, then ask James directly for explicit deploy/restart approval

# Current blocker or none
blocker: none on the repo side; documented HA fingerprint recheck in this run still shows the live install differs from repo component commit `eb5a8ea`, but that unchanged deploy boundary should stay secondary while mapped `0.1.87` UI runway remains

# Exact user action needed or none
user_action: none until the current repo-side `0.1.87` cut line is coherent enough to justify an explicit deploy/restart approval ask

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, and distinguish the live `0.1.86` correction line from the next `0.1.87` UI rollout target

# Last time this file materially changed
last_modified: 2026-04-19 05:05
