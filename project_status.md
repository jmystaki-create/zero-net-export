# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: inspect why the live Home Assistant install has no active `zero_net_export` config entry even though the exact intended `0.1.83` build is now deployed, then restore or recreate that entry before more UI/runtime validation

# Current blocker or none
blocker: live exact-build drift is now cleared, but Home Assistant currently has zero `zero_net_export` config entries, zero Zero Net Export devices, and only `update.zero_net_export_update` remains visible through the API

# Exact user action needed or none
user_action: none

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, and keep version tracking explicit across local repo state, remote GitHub state, and public release state

# Last time this file materially changed
last_modified: 2026-04-15 22:21
