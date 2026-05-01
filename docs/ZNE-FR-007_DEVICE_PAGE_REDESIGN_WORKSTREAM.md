# ZNE-FR-007 — main device page two-tier redesign workstream

Status: design only — Tier 1 native Home Assistant device-page design accepted; Tier 2 still pending. No implementation approved.

## User outcome

The main Zero Net Export Home Assistant device page should stop acting like a dense command wall. Tier 1 should stay on the native device page and show only the five most useful items per card. Tier 2 should be opened from buttons inside those cards and may contain the full detailed workflow.

## Acceptance criteria for design phase

- Research Home Assistant constraints before proposing implementation.
- Produce two distinct PNG mockups for Riley to review.
- Keep the concepts compatible with Home Assistant's native device/config-entry model unless the mockup explicitly moves detail into a custom panel/dashboard-style Tier 2 screen.
- Do not implement until Riley chooses a direction.

## Home Assistant constraints found

- Home Assistant devices are registry objects represented through one or more entities; the native device page is largely driven by device/entity metadata.
- Device registry `configuration_url` can link a device to a configuration URL, including Home Assistant internal paths.
- Config entries can expose reconfigure/options flows; config subentries can logically separate per-entry child configuration and support UI actions.
- Entity properties should stay lightweight; UI detail should not rely on heavy property calculation.
- Rich custom UI is possible through dashboard/custom-card/custom-panel style surfaces, but that is outside the native device-page card layout.
- Existing ZNE investigation found the native integration device row does not expose arbitrary custom row actions in the exact row location; supported navigation should use configuration URLs, buttons, config flows, subentry actions, or a custom panel.

## Mockup A — Native device-page compression

Intent: keep the first screen close to Home Assistant's native device page and make each native card a concise summary/launcher.

Tier 1 cards:
- Device info
- Controls
- Sensors
- Managed Devices
- Diagnostics
- Activity

Each card shows five rows only, then one Tier 2 button.

Best when:
- We want lowest implementation risk.
- We want to preserve Home Assistant native behavior.
- We can accept that exact layout/order is still partly constrained by HA.

Risk:
- Native HA may still constrain exact card placement and labels.
- Some polish may require hiding/reclassifying entities rather than true custom layout control.

Artifact: `design-mockups/zne_mockup_a.png` in the dev workspace.

## Mockup B — Operator command-center detail screen

Intent: keep Tier 1 native and simple, then open a purpose-built Tier 2 command-center screen for the expanded experience.

Tier 2 areas:
- Current decision
- Quick actions
- Navigation rail
- Operator summary
- Sensors detail
- Managed fleet detail
- Controls detail
- Diagnostics detail

Best when:
- We want the cleanest operator experience.
- We need real control over layout, language, grouping, and workflow.
- The detailed workflow has outgrown native HA cards.

Risk:
- Higher implementation effort.
- Requires maintaining a custom panel/dashboard-style surface as product UI.

Artifact: `design-mockups/zne_mockup_b.png` in the dev workspace.

## Recommendation

Recommend starting from Mockup A as the native Tier 1 structure, with Mockup B as the Tier 2 detail target for the cards that need rich workflow. This gives a low-risk first screen while still creating room for a better operator experience where Home Assistant's native page is too constrained.

## Current decision needed

Riley should choose one of:

1. A-first: native Tier 1 compression now, custom Tier 2 later.
2. B-first: build the custom command-center detail experience first and use native page only as a launcher.
3. Hybrid: approve A as Tier 1 and B as the Tier 2 destination model.

## 2026-05-01 correction — validated Tier 1 boundary

Riley clarified that the screenshoted Home Assistant device page is Tier 1 and should be treated as structurally constrained. This changes the design boundary:

- Tier 1 must remain inside Home Assistant's native device page structure.
- We should not design a new card grid for Tier 1.
- We can influence Tier 1 mainly by choosing which entities/buttons exist, their names/icons/categories, and which device they attach to.
- We should shrink Tier 1 to the key native sections Home Assistant already renders, especially:
  - Device info
  - Controls
  - Sensors
  - Activity
- Automation, Scenes, and Scripts appear as native Home Assistant device-page cards and are not useful ZNE product surfaces. Treat them as HA-owned/background, not core ZNE design real estate.
- Tier 2 may still use ZNE-owned navigation/buttons/config flows/custom panels for expanded workflows, but Tier 2 should be launched from a minimal Tier 1 affordance.

### Revised Tier 1 design principle

Tier 1 is not a dashboard. It is a native HA device summary.

For each native card we should pick only the most important items and remove/reclassify the rest so the screen becomes legible.

### Revised Tier 1 candidate content

Device info:
1. Plan/service name
2. Installed version
3. Setup/readiness status
4. Open main ZNE detail / command center
5. Download diagnostics

Controls:
1. Enabled
2. Mode
3. Target export
4. Battery reserve
5. Open controls detail / reset override

Sensors:
1. Active state
2. Active controlled power
3. Grid/source health
4. Battery SOC/reserve SOC
5. Actions today or last action

Activity:
1. Latest setup status change
2. Latest diagnostics event
3. Latest managed-device event
4. Latest control action
5. Latest blocker/repair event

### Revised next design task

Discard the earlier Tier 1 free-layout mockup as too unconstrained. Produce replacement Tier 1 mockups that preserve the screenshoted Home Assistant structure and only shrink/relabel/reprioritise what appears inside the existing native cards.

## Tier 1 constrained mockup — 2026-05-01

Status: accepted by Riley on 2026-05-01.

Produced a replacement Tier 1 mockup that preserves the screenshoted Home Assistant native device page structure instead of inventing a custom card grid.

Artifact sent for review:
- `/root/.openclaw/outbox/zero-net-export/2026-05-01/zne_tier1_native_constrained_design.png`

Design intent:
- Keep native cards: Device info, Controls, Sensors, Activity, plus HA-owned Automations/Scenes/Scripts.
- Use Automations/Scenes/Scripts as empty HA-owned cards, not ZNE product UI.
- Controls: keep only enabled, mode, target export, battery reserve, deadband, and one detail link.
- Sensors: keep readiness, active controlled power, grid/source health, battery SOC, actions today, and one mapping link.
- Activity: curate only meaningful setup/device/diagnostic/control/repair events.
- Move explanatory or workflow-heavy content to Tier 2.

## Tier 1 acceptance — 2026-05-01

Riley accepted the constrained Tier 1 design: keep the native Home Assistant device-page structure and shrink/reprioritise the visible ZNE entities/actions inside the existing cards.

Implementation remains explicitly unapproved until Riley asks to move from design to build. Next design task is Tier 2 detail flow design from the accepted Tier 1 launch points.
