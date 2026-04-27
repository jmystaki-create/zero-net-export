# project_status.md

# This should match the project folder name
project_name: zero-net-export

# active | blocked | paused | done
status: active

# Single next best action
next_action: ask James directly whether `db5c246` / `v0.1.92` should replace the documented `0.1.91` release target for deploy/restart validation, or whether release execution should return to the approved `0.1.91` boundary before any Home Assistant install/restart; then capture integration-main-page screenshot evidence only after that approval boundary is explicit

# Current blocker or none
blocker: repo HEAD is now `db5c246` / `v0.1.92` while the source-of-truth docs still approve only `0.1.91` / release `1.91`; explicit James release-target acceptance plus release/deploy/restart approval is required before exact-build live validation

# Exact user action needed or none
user_action: James should decide whether the `0.1.92` candidate is the new approved release target or whether the project should return to the documented `0.1.91` boundary, accept or reject the closest native child-device representation, then approve or decline release/deploy/restart validation for that exact target

# One short durable constraint
notes: keep Zero Net Export native-Home-Assistant-only; the active scope is only the main integration page Managed Devices and Un Managed device-list outcome, not historical device-page work, broad legacy polish, custom UI, or repeated release/fingerprint bookkeeping.

# Last time this file materially changed
last_modified: 2026-04-27 22:52
