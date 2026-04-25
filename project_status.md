# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: work through the detailed missing-UI checklist toward `0.1.88`; stop treating unchanged release/fingerprint drift as the default headline, and only ask James for deploy/restart approval once the `0.1.88` checklist is genuinely ready for formal release validation

# Current blocker or none
blocker: none; the steering docs now point at `0.1.88`, so keep ranking the next unfinished mapped UI item ahead of unchanged release/fingerprint bookkeeping

# Exact user action needed or none
user_action: none

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, keep `0.1.86` as the current live correction line until the `0.1.88` UI-complete target is explicitly frozen, approved, shipped, and validated, and treat unchanged live exact-build mismatch as release drift rather than as the default next-step ranking while implementation-map runway still exists.

# Last time this file materially changed
last_modified: 2026-04-25 13:34
