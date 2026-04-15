# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: ask James directly for approval to execute the formal Zero Net Export 0.1.83 release/deploy flow for the current pushed `0.1.83` candidate, because the real boundary is now live release execution through HACS/Home Assistant rather than more local repo wording

# Current blocker or none
blocker: explicit user release approval is still required before the documented HACS/Home Assistant deploy, restart, and live validation flow can begin; SSH-backed fingerprint validation in this run still shows the installed component at `0.1.81` with `overall_match=false` versus the current pushed `0.1.83` candidate

# Exact user action needed or none
user_action: approve the formal Zero Net Export 0.1.83 release/deploy flow for the current pushed `0.1.83` candidate, so the release can proceed end-to-end through the documented HACS/Home Assistant path

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, and keep version tracking explicit across local repo state, remote GitHub state, and public release state

# Last time this file materially changed
last_modified: 2026-04-15 19:14
