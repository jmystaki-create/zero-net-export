# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: remove the blocking-I/O version-surface regression from `entity.py`, then continue staged UI work from `docs/UI_IMPLEMENTATION_MAP.md` with command-center reduction and managed-device workspace redesign on the live `0.1.86` line

# Current blocker or none
blocker: the current `0.1.86` line still has a real blocking-I/O regression in `entity.py`, and the visible native device-page redesign is still far behind the staged UI plan

# Exact user action needed or none
user_action: none

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, and keep version tracking explicit across local repo state, remote GitHub state, and public release state

# Last time this file materially changed
last_modified: 2026-04-16 15:06
