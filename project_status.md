# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: the repo-side UI work has moved to the clean `0.1.89` follow-up line after published `v0.1.88`; if the next run does not find a new concrete A-D/F implementation defect, ask James directly to approve the `0.1.89` freeze/release/deploy/restart path before Workstream G live validation

# Current blocker or none
blocker: explicit James approval is required before freezing, releasing, deploying, and restarting for the `0.1.89` exact-build Home Assistant validation; do not refresh release/fingerprint wording again unless live evidence, approval state, or the helper-resolved component boundary materially changes

# Exact user action needed or none
user_action: James should approve or decline the `0.1.89` freeze/release/deploy/restart path once the final A-D/F defect check remains clean

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, treat published `v0.1.88` as superseded for future UI validation unless James explicitly chooses to retag it, and treat unchanged live exact-build mismatch as release drift rather than a reason for more release-boundary bookkeeping.

# Last time this file materially changed
last_modified: 2026-04-26 17:29
