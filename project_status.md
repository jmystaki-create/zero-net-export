# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: ask James directly whether he approves freeze/deploy/restart of the exact `e221549` candidate, because the latest audit did not find a fresh repo-side A-D/F defect stronger than the existing empty-fleet churn and unchanged six-file live mismatch

# Current blocker or none
blocker: formal release/deploy approval is now the real boundary for the exact `e221549` candidate; live exact-build mismatch remains unchanged on `button.py`, `config_flow.py`, `native_support.py`, `sensor.py`, `strings.json`, and `translations/en.json`

# Exact user action needed or none
user_action: James needs to explicitly approve freeze/deploy/restart of the exact `e221549` build before formal release execution, redeploy, or live validation continues

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, keep `0.1.86` as the current live correction line until `0.1.87` is explicitly frozen, approved, shipped, and validated, and treat the unchanged divergent live `0.1.87` install as release drift rather than as the default next-step ranking while implementation-map runway still exists.

# Last time this file materially changed
last_modified: 2026-04-22 07:17
