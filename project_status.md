# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: ask James directly for approval to execute the formal Zero Net Export release/deploy flow once the current candidate version/commit is confirmed, because the real boundary is live release execution through HACS/Home Assistant rather than more local repo wording

# Current blocker or none
blocker: project_status.md drift, it still points at old local commit `0c6b544` / `0.1.80`, while the repo is now at `0.1.82` with newer release-helper fixes and docs commits; release confidence is still blocked on explicit user approval plus live Home Assistant deployment and restart validation from one synchronized install path

# Exact user action needed or none
user_action: approve the formal Zero Net Export release/deploy flow after the current candidate version/commit is presented explicitly, so the release can proceed end-to-end through the documented HACS/Home Assistant path

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, and keep version tracking explicit across local repo state, remote GitHub state, and public release state

# Last time this file materially changed
last_modified: 2026-04-13 16:19
