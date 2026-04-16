# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: redeploy the current `0.1.85` repo candidate after James approves release execution, then clear the remaining `entity.py` fingerprint drift and continue live native-UI validation

# Current blocker or none
blocker: the repo release metadata had drifted back to `0.1.83` while live HA is on `0.1.85`, and the installed component still has an older `entity.py` than repo HEAD

# Exact user action needed or none
user_action: none

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, and keep version tracking explicit across local repo state, remote GitHub state, and public release state

# Last time this file materially changed
last_modified: 2026-04-16 10:41
