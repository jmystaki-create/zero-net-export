# ZNE Tier 1 native Home Assistant device-page feasibility check

Date: 2026-05-01
Status: Draft for Riley acceptance before any replacement Tier 1 mockup or implementation.

## Question

What can Zero Net Export actually control on a native Home Assistant device page, and what is owned by Home Assistant frontend?

## Target environment

- Home Assistant native device page under Settings > Devices & services > Devices.
- Custom integration entities registered through normal Home Assistant entity/device registries.
- Existing Zero Net Export custom integration, not a custom frontend panel.

## Authoritative evidence consulted

- Home Assistant developer docs: Device registry. A device is represented in HA via one or more entities; HA owns the device registry/device-page concept.
- Home Assistant developer docs: Entity. Integrations expose entities with `device_info`, `unique_id`, entity naming, state, icons/device classes/categories and other entity metadata.
- Home Assistant developer docs: Button entity. Button entities are stateless backend/device actions, not navigation controls.
- Home Assistant developer docs: Config entries/config flow. Config entries are UI-created persistent configuration; integrations can expose reconfigure/options flows.
- Project note: `docs/NATIVE_SURFACE_TECHNICAL_DIRECTION.md` says supported operator UX is native HA surfaces and no required custom sidebar/custom panel/external UI path.

## Supported / controllable by ZNE

These are valid Tier 1 design levers:

1. Entity inventory
   - Which ZNE entities exist for a controller/plan device.
   - Which entities are omitted entirely when they are misleading or not useful.

2. Entity domain/platform choice
   - Use the correct HA platform for the thing represented, for example sensor, binary_sensor, switch, number, select, button, update, diagnostics-style sensor.
   - Do not use button entities for navigation.

3. Entity metadata
   - Entity name/translation key.
   - Icon/device class/state class where applicable.
   - Entity category such as config or diagnostic where appropriate.
   - Default enabled/disabled state for noisy or advanced entities.

4. Entity state/value text
   - Short truthful states such as Ready, Needs sensor mapping, Limited, Enabled, Disabled.
   - Attributes for detail, provided they are not relied on as primary navigation UI.

5. Device registry metadata
   - Device name/model/manufacturer/sw_version/identifiers/via_device/configuration_url where supported by HA.
   - The supported `configuration_url` / Visit affordance may link to a real supported target, but it must not be represented as a fake entity action.

6. Attachment to native HA surfaces
   - Attach entities to the correct controller/plan device so HA renders them on that device page.
   - Keep existing Diagnostic and Connected devices/native device relationship surfaces when HA renders them.

## Owned by HA frontend / not controllable by ZNE

These are not valid Tier 1 design levers:

1. Card layout or ordering guarantees
   - ZNE cannot define a bespoke grid layout for the HA device page.
   - ZNE cannot guarantee custom positions such as Controls left, Sensors right, custom Activity row, etc.

2. Native card chrome
   - ZNE cannot redesign the HA device page header, card borders, typography, spacing, or responsive layout.

3. Entity row behaviour as browser navigation
   - ZNE cannot make entity row label text act as a frontend navigation link.
   - `button.press` is not a browser navigation mechanism.

4. Custom wizard inside Tier 1
   - ZNE cannot embed a custom multi-step setup wizard into the native device page without introducing custom frontend UI.

5. Native Logbook/Activity composition
   - ZNE can emit states/events indirectly through normal entities/services, but cannot design a bespoke Activity summary card inside the native device page.

## Unknown / requires live proof before design reliance

These must not be assumed in a mockup unless verified against the installed HA version/browser:

1. Exact native card ordering for this integration/device.
2. Exact rendering of Diagnostic and Connected devices cards for the current entity/device graph.
3. Exact label and placement of the Visit/configuration URL affordance.
4. Whether default-disabled diagnostic entities appear immediately or only after user enables them.
5. How many entities HA shows before collapsing/overflowing in the current frontend version.

## Feasible Tier 1 design boundary

A compliant Tier 1 mockup must use the actual native HA device page screenshot as the wireframe. It may annotate or replace only the ZNE-controlled content inside existing native structures:

- Device name and metadata.
- Entity rows and their labels/states/icons/categories.
- Which entities are primary versus diagnostic/advanced/default-disabled.
- Supported Visit/configuration URL destination, if actually configured.
- Existing Diagnostics and Connected devices surfaces as HA renders them.

A compliant Tier 1 mockup must not draw a new dashboard, new card grid, custom hero action, custom setup panel, or custom activity card.

## Acceptance criteria for replacement Tier 1 mockup

- Looks like the real native HA device page, not a designed custom page.
- Shows only changes available through ZNE entity/device metadata and state.
- Keeps Diagnostic and Connected devices surfaces if HA renders them.
- Excludes all fake launcher buttons and row-as-navigation behaviour.
- Clearly marks any exact frontend rendering that still needs live proof.

## Recommendation

Accept this feasibility boundary, then produce the replacement Tier 1 mockup by marking up the real HA screenshot/page structure rather than drawing a new page.
