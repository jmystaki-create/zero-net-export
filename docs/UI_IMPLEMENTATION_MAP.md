# UI implementation map for native command center

Branch: `ui-surface-correction-2026-04-12`

Purpose: keep the native Home Assistant command center coherent around the four supported Configure sections, **Sensors and source mapping**, **Controls**, **Managed devices**, and **Diagnostics**, with deeper device-detail work handed off through the native device view rather than a separate custom surface.

## Current supported IA

### Configure sections
- **Sensors and source mapping**: source mapping, mapped-source health, source-validation blockers, and source-remediation guidance.
- **Controls**: controller policy, thresholds, refresh behavior, and live mode readiness once sources and devices are ready.
- **Managed devices**: add, review, edit, remove, promote, and prioritize controllable loads.
- **Diagnostics**: runtime health, support snapshot, blocker summaries, install consistency, and troubleshooting guidance.

### Native handoff outside Configure
- **Detailed management** stays as the deeper native device-view handoff for per-device inspection and entity-level detail.
- Do not turn Detailed management into another top-level custom surface.

## What to protect in code

### `custom_components/zero_net_export/config_flow.py`
- Keep the Configure menu labels and descriptions aligned with the four-section command center above.
- Keep **Sensors and source mapping** clearly signposted as the place to repair unavailable or stale mapped roles.
- Keep **Controls** from pretending policy changes are actionable before source mapping and managed-device readiness are complete.
- Keep **Managed devices** focused on normal onboarding and edits, not source repair or support.
- Keep **Diagnostics** focused on runtime state, install consistency, and troubleshooting.

### `custom_components/zero_net_export/native_support.py`
- Keep recommended-section logic aligned with the real command-center flow.
- Name unavailable or stale mapped roles clearly when source validation is blocking control.
- Point source-related remediation back to **Configure -> Sensors and source mapping**.
- Keep device-view handoff wording explicit when the next useful step is deeper fleet or per-device review.

### `custom_components/zero_net_export/strings.json`
### `custom_components/zero_net_export/translations/en.json`
- Keep shipped wording locked to the current section names.
- Avoid older shorthand like plain **Sensors** when the actual screen label is **Sensors and source mapping**.
- Keep the command-center intro explicit about where sources, policy, devices, and diagnostics live.

### `custom_components/zero_net_export/sensor.py`
### `custom_components/zero_net_export/button.py`
### `custom_components/zero_net_export/repairs.py`
- Keep entity, button, and Repairs wording aligned with the four supported sections.
- Surface blocker summaries and next-step guidance in the section that can actually resolve them.
- Keep native troubleshooting text precise, especially for mapped-source failures.

## Supporting docs to keep aligned
- `README.md`
- `docs/OPERATOR_SURFACES_UX.md`
- `docs/NATIVE_SURFACE_TECHNICAL_DIRECTION.md`
- `docs/VALIDATION_CHECKLIST.md`
- `TOOLS.md`

## Current doc guardrails
- Prefer the exact label **Sensors and source mapping**.
- Describe Configure as the command center.
- Treat manual entity-id fields as fallback only when Home Assistant selector validation rejects a valid choice.
- Keep restart and exact-build validation guidance tied to the real helper scripts and post-restart Configure check.
- Do not reintroduce a custom panel, sidebar, or fifth primary setup surface.

## Notes
- This file is now a maintenance map, not a speculative redesign plan.
- Release execution still follows `RELEASE_MANAGEMENT.md`.
