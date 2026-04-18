# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: ask James directly for explicit deploy/restart approval to replace the drifted live `0.1.87` install with one exact current repo build, rerun fingerprint validation until `overall_match=true`, and then return to the next unfinished `0.1.87` UI workstream instead of repeating release/fingerprint churn

# Current blocker or none
blocker: live Home Assistant is still drifted from the preferred repo validation commit `1e61151` (`button.py`, `config_flow.py`, `manifest.json`, `native_support.py`, `sensor.py`, `strings.json`, and `translations/en.json` do not match, and the installed manifest is `0.1.87` while repo stays on the unfrozen `0.1.86` correction line), so exact-build redeploy/restart is the active release blocker until James explicitly approves that step

# Exact user action needed or none
user_action: James must explicitly approve deploy/restart of one exact current repo build to Home Assistant before another formal live validation pass

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, and distinguish the live `0.1.86` correction line from the next `0.1.87` UI rollout target

# Last time this file materially changed
last_modified: 2026-04-19 02:24
