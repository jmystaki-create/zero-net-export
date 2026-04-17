# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: continue building the next unfinished `0.1.87` UI stages from `docs/UI_IMPLEMENTATION_MAP.md`, especially command-center reduction, stronger managed-vs-unmanaged workspace delivery, promotion-flow polish, and notification cleanup; only return to formal `0.1.86` release reconciliation when there is materially new release-boundary evidence instead of repeating the same unchanged approval ask

# Current blocker or none
blocker: live Home Assistant is still not exact-build aligned to the current component candidate (`preferred_validation_commit` / `expected_component_commit`), but that release-reconciliation boundary is no longer enough by itself to stop ongoing repo-side `0.1.87` UI progress; the real project risk is churn from repeated release/fingerprint/doc-state loops replacing visible product work

# Exact user action needed or none
user_action: none

# One short durable constraint
notes: keep native Home Assistant surfaces as the primary operator path, treat manual entity-ID fields only as a fallback when Home Assistant selector validation rejects a valid choice, keep version tracking explicit across local repo state, remote GitHub state, and public release state, and distinguish the live `0.1.86` correction line from the next `0.1.87` UI rollout target

# Last time this file materially changed
last_modified: 2026-04-18 02:37
