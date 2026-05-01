# ZNE Home Assistant guardrails Tier 1 / Tier 2 mockup

Date: 2026-05-01

## Status

Rejected. Do not use these mockups for implementation.

Riley rejected the Tier 1 mockup because it still invented a custom-looking layout instead of matching the actual native Home Assistant device page structure. The failure was a feasibility-gate failure: the mockup treated Home Assistant guardrails as visual style rather than hard frontend constraints.

Before any replacement Tier 1 design is produced, a narrower feasibility check must be written and accepted for the exact question: what can a custom integration control on the native Home Assistant device page, and what is owned by the Home Assistant frontend?

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

Rejected by Riley. No architecture or implementation may proceed from these artifacts.

Next required action: write and get acceptance for a native Home Assistant device-page feasibility check that uses the actual HA device page as the structural source of truth, then produce a corrected mockup only by changing controllable entity metadata/content.
