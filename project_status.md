# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: re-open Configure on the exact deployed `0.1.83` build, confirm the `source_repair_step` 500 is gone, and then re-check the native Managed Devices and four-bucket UI outcome in live Home Assistant

# Current blocker or none
blocker: live config-entry/device absence is no longer the blocker; the remaining release-gate gap is post-deploy Configure and native-UI validation on the repaired live build

# Exact user action needed or none
user_action: none

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, and keep version tracking explicit across local repo state, remote GitHub state, and public release state

# Last time this file materially changed
last_modified: 2026-04-16 00:45
