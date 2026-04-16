# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: fix the `0.1.85` version-surface blocking-I/O regression, remove stale `0.1.83` release-target drift from project steering docs, then continue live native-UI validation on the current release line

# Current blocker or none
blocker: project steering and bug-tracker docs still contain stale `0.1.83` release-target wording even though the current live release line is `0.1.85`, and the latest version-display fix introduced blocking-I/O during Home Assistant startup

# Exact user action needed or none
user_action: none

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, and keep version tracking explicit across local repo state, remote GitHub state, and public release state

# Last time this file materially changed
last_modified: 2026-04-16 10:36
