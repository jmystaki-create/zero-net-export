# ZNE Home Assistant guardrails Tier 1 / Tier 2 mockup

Date: 2026-05-01

## Feasibility gate

This mockup follows the accepted target-environment feasibility check:

- Tier 1 remains the native Home Assistant device page.
- Tier 1 uses native device/entity metadata, curated entity visibility, device `configuration_url` / Visit, and existing native Diagnostic / Connected devices surfaces.
- Native HA button entity `Press` is not treated as browser navigation.
- Tier 2 is a separate feature release using native Home Assistant config/options/reconfigure flow UI.
- No required custom `/zero-net-export` command-center panel is included.

## Artifacts

- `design-mockups/zne_tier1_ha_guardrails_mockup.png`
- `design-mockups/zne_tier2_native_flow_guardrails_mockup.png`
- Source HTML:
  - `design-mockups/zne_tier1_ha_guardrails_mockup.html`
  - `design-mockups/zne_tier2_native_flow_guardrails_mockup.html`
  - `design-mockups/zne_guardrails_mockups.html`

## Tier 1 intent

The Tier 1 page is a compact native Home Assistant device page:

- Device info with the supported `Visit / Configure` affordance.
- Controls card shows current control state only.
- Sensors card shows a small readiness/source summary.
- Diagnostics card remains present but compact.
- Connected devices surface remains present.
- Activity remains a brief HA-style event summary.
- No `Open setup` button entity rows are used as navigation.

## Tier 2 intent

The Tier 2 page is a native HA guided setup/config flow:

- Launched from supported HA surfaces such as Visit/configuration URL or integration Configure/options.
- Uses native form fields and Back/Cancel/Next controls.
- Covers Sensors, Controls, Managed devices, Diagnostics, and Save as flow steps.
- Keeps copy short and operator-focused.
- Does not require a maintained custom panel.

## Review status

Pending Riley review/acceptance before architecture or implementation continues.
