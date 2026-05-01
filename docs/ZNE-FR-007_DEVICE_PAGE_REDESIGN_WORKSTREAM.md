# ZNE-FR-007 — main device page two-tier redesign workstream

Status: design only — no implementation approved.

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
