# ZNE-590 — Managed climate device configuration design

Date: 2026-05-06
Status: Option A accepted by Riley; repo implementation in progress/validated locally; original-device attachment remains blocked unless explicitly approved as experimental

## User report

Riley compared two Home Assistant device pages for the same heated floor load:

1. Standard Home Assistant climate device page for `climate.lounge_room_thermostat`.
2. Zero Net Export managed-device page for the same load.

Observed problem: the standard climate page is useful and should be preserved. The Zero Net Export managed-device page shows confusing/internal `Settings — Test ...` entities and does not expose the managed-load settings the operator actually needs.

Requested outcome: preserve the original Home Assistant device screen, and add or expose a Home Assistant-native configuration surface for Zero Net Export device configuration. The useful operator controls should be things like:

- test load
- enabled yes/no
- configuration captured when the device was added

## Classification

- Type: bug / UX regression
- Area: managed_devices / native_device_page / entity surfaces
- Target environment: Home Assistant custom integration using native device/entity/config-flow surfaces
- Constraint classification: Entity/device/repair/notification supported for a native entity-based managed-load surface; exact card placement or custom frontend card is not supported without explicit project-direction approval.

## Constraint and feasibility check

### Supported

- Home Assistant integrations can expose native entities, and Home Assistant renders those entities on the device page for their associated device.
- Home Assistant device registry supports devices represented by one or more entities.
- Home Assistant device registry supports `configuration_url` links for configuration/navigation into Home Assistant paths.
- Zero Net Export project constraints allow native entities, native device registry behavior, options/config flows, repairs, diagnostics, and services/actions.
- Zero Net Export can create a compact, meaningful native entity set for a managed load:
  - config switch: `Zero Net Export enabled`
  - action button: `Test load`
  - read-only config summary sensor: `Zero Net Export configuration`
  - optional diagnostic result sensor: `Last test result`
  - optional numeric config entities only when they are truly operator-editable and named in domain language, e.g. `Priority`, `Nominal power`, or `Minimum off time`

### Unsupported / must not claim

- Zero Net Export cannot guarantee exact placement inside an existing Home Assistant device page card.
- Zero Net Export must not add a custom card, custom panel, sidebar app, external web UI, or Home Assistant frontend patch under current constraints.
- Zero Net Export must not replace or reshape the original thermostat/climate control card.
- Zero Net Export must not fake a frontend-native settings card by using a custom JavaScript panel or relying on undocumented Home Assistant internals.

### Unknown / requires proof before implementation

- Whether Zero Net Export can safely attach its own configuration entities directly to the existing thermostat device page for `climate.lounge_room_thermostat` without forging another integration's device identifiers, accidentally merging devices, or creating confusing ownership. This has now been investigated in `validation/zne-590-original-thermostat-device-feasibility.md`: the only proven native mechanism is registry matching/merging by identifiers or connections, which would require cohabiting with the Tuya-owned thermostat device registry row. That is blocked under current constraints unless Riley explicitly approves experimental cross-integration device registry merging.

### Original thermostat device page investigation result

Read-only Home Assistant source and live registry inspection found:

- Home Assistant entities attach to device pages through `device_info` identifiers/connections, not by assigning an arbitrary existing `device_id`.
- `DeviceRegistry.async_get_or_create` resolves a device by identifiers/connections and adds the calling config entry to the matched device row.
- The live `climate.lounge_room_thermostat` device is owned by `tuya_local` with identifier `("tuya_local", "bfde93729769c94ee3mmd3")`.
- The live ZNE managed-load page is a separate ZNE-owned device with identifier `("zero_net_export", "01KQES5GS0B2XTEAK1SDHEK7KX:managed-device:test")` and user name `Heated Floor - Lounge Room`.

Conclusion: placing ZNE entities on the original thermostat page is technically possible only by making ZNE match/cohabit the Tuya device registry row. That would depend on another integration's identifiers and alter another integration's visible device ownership surface. It also still would not guarantee exact card/row placement. Under `CONSTRAINTS.md`, this is not acceptable for the bug-fix path without explicit Riley approval as experimental work.

## Recommended design direction

### Design principle

Preserve the original device page by leaving the thermostat/climate device ownership and climate controls alone. Zero Net Export should expose only a small, native, meaningful managed-load control surface.

### Preferred native design

Use a concise Zero Net Export managed-load surface, rendered by native Home Assistant entities, with these sections by entity category/domain:

#### Configuration card

1. `Zero Net Export enabled`
   - Domain: `switch`
   - Category: `config`
   - Meaning: whether this load may be controlled by the selected Zero Net Export plan.
   - Avoid labels like `Settings — Test enabled`.

2. `Priority`
   - Domain: `number`
   - Category: `config`
   - Keep only if priority remains a real operator decision.
   - Rename from any `Settings — T...` / debug wording.

3. Optional: `Nominal power`
   - Domain: `number` or read-only sensor depending on whether edits are safe.
   - Unit: W
   - Meaning: configured expected load size, e.g. `2400 W`.

#### Controls card

1. `Test load`
   - Domain: `button`
   - Meaning: run a safe, explicit operator-triggered test for this managed load.
   - Should not be named `Test review` or `Test reset`.
   - Must have a clear result surface before release.

#### Sensors card

1. `Zero Net Export status`
   - Domain: `sensor`
   - Short, human-readable state like `Enabled`, `Disabled`, `Blocked`, or `Ready`.
   - Attributes may carry details, but the visible state must not be a long pipe-delimited debug string.

2. `Zero Net Export configuration`
   - Domain: `sensor`
   - Read-only summary from the add flow:
     - source entity: `climate.lounge_room_thermostat`
     - load type: fixed / climate load
     - enabled default
     - nominal power
     - priority
     - plan/service owner, e.g. Winter Plan
   - This can be diagnostic/config-style summary but must use clear user-facing names.

#### Diagnostics card

Move detailed/internal fields here or hide them by default:

- current power unknowns
- guard internals
- last requested/applied power
- action result messages
- raw `blocked | fixed load | ...` debug strings
- reset/recovery-only buttons

### What to remove or hide from the current managed-device page

- `Settings — Test current power`
- `Settings — Test enabled`
- `Settings — T...` ambiguous priority/control number
- `Test reset...`
- `Test review`
- long pipe-delimited status as a primary visible entity state
- any entity whose name starts with `Settings — Test` unless it is genuinely a test action and labelled plainly as `Test load`

## Alternative design paths

### Option A — safest / recommended

Keep the original climate device page untouched. Fix the Zero Net Export managed-load device page so it contains only the meaningful native ZNE controls/configuration above.

Pros:
- Fully aligned with `CONSTRAINTS.md`.
- Avoids cross-integration device ownership risk.
- Preserves the original thermostat page exactly.
- Smallest safe implementation.

Cons:
- The ZNE controls appear on the ZNE managed-load page, not inside the original climate device's native thermostat page.

### Option B — investigate attaching ZNE config entities to the original thermostat page

Read-only Home Assistant source/live feasibility check completed. ZNE cannot safely associate its config entities with the existing climate device page under current constraints without cross-integration device registry merging/cohabitation.

Pros:
- Closest to Riley's preferred “same device page with an extra ZNE card” outcome.

Cons:
- Proven risky/blocked under current constraints.
- Exact card placement still cannot be guaranteed.
- Must not proceed unless Riley explicitly approves experimental cross-integration device registry merging.

### Option C — custom card/panel

Blocked by project constraints unless Riley explicitly approves a project direction change.

## Acceptance criteria

- Original `climate.lounge_room_thermostat` device page remains unchanged as a normal Home Assistant climate device page.
- ZNE managed-load surface exposes only meaningful operator controls/configuration:
  - enabled yes/no
  - test load
  - configuration captured during add
  - optional priority/nominal-power values if they are real user decisions
- Current confusing `Settings — Test ...` entities are removed, hidden, or renamed into clear operator language.
- Diagnostic/internal values are diagnostic/hidden by default, not primary page clutter.
- No custom frontend, sidebar panel, external UI, or Home Assistant frontend patch is introduced.
- Tests cover entity names, categories, visibility/default category, and managed climate load config summary.
- Live Home Assistant screenshot proof confirms the original climate page is preserved and the ZNE managed-load page/card is meaningful.

## Validation plan

1. Repo tests for entity names/categories and managed-load runtime details.
2. Full test discovery where practical.
3. `git diff --check`.
4. Release-managed install through GitHub/HACS only after approval.
5. Install fingerprint check.
6. Home Assistant restart/API recovery.
7. Browser proof for:
   - original `climate.lounge_room_thermostat` device page preserved
   - ZNE managed-load configuration surface has the accepted controls/configuration and no confusing `Settings — Test ...` clutter
8. Post-restart Zero Net Export log scan.

## Implementation status

Riley accepted Option A on 2026-05-06. The repo implementation follows the accepted path:

- the original thermostat/climate device page remains untouched;
- ZNE-owned managed-load rows use clear native entity names;
- `Test load` is exposed as a native button for the managed load;
- review/reset/runtime internals are diagnostic instead of primary configuration clutter;
- no custom frontend, sidebar panel, external UI, Home Assistant frontend patch, or cross-integration device registry merge was introduced.

Repo validation is recorded in `validation/zne-590-managed-climate-device-page-cleanup.md`. Live Home Assistant release validation is still required before closing ZNE-590.

## Recommendation

Continue with Option A through release-managed live validation. Run Option B only as a separate feasibility/experimental workstream if Riley specifically wants ZNE controls rendered on the original thermostat device page itself.
