# ZNE-594 state length feasibility

Date: 2026-07-01
Status: feasibility written; awaiting acceptance before code changes

## Task

ZNE-594 tracks live Home Assistant log errors where
`sensor.zero_net_export_source_blocker_next_step` and
`sensor.zero_net_export_command_center_next_step` can publish entity state text
longer than Home Assistant's state limit.

## Target environment

- Home Assistant Core, installed validation target: `2026.6.4`
- Zero Net Export custom integration, latest released baseline: `v0.2.3`
- Affected surface: Home Assistant entity state machine for sensor
  `native_value` strings

## Feasibility findings

### Supported

- Home Assistant entity state strings must stay at or below 255 characters.
  Authoritative Home Assistant source defines
  `MAX_LENGTH_STATE_STATE: Final = 255` in `homeassistant/const.py` and
  `validate_state(state)` raises `InvalidStateError` when
  `len(state) > MAX_LENGTH_STATE_STATE`.
- Moving longer operator guidance into entity attributes is compatible with the
  existing ZNE pattern. The affected ZNE sensor already exposes detailed
  attributes for source blocker and command-center next-step entities.
- Shortening only the state value is consistent with existing ZNE code:
  `custom_components/zero_net_export/sensor.py` has `_truncate_sensor_state`,
  and `custom_components/zero_net_export/native_support.py` defines
  `MAX_NATIVE_SENSOR_STATE_CHARS = 255`.

### Unsupported

- Publishing full operator guidance directly as the entity state when the text
  can exceed 255 characters is not supported. Live HA logs show this falls back
  to `unknown`.
- Direct Home Assistant storage edits are not needed and remain outside the
  accepted validation path.

### Unknown

- Browser proof for the installed Sources workflow remains unresolved because
  the current browser-node navigation path is unavailable. This does not block
  the ZNE-594 state-length fix, but it remains a separate `0.2.3` validation
  gap.

## Local code evidence

- `custom_components/zero_net_export/sensor.py`
  - `_truncate_sensor_state(text, max_chars=255)` exists.
  - `_healthy_sources_next_step(...)` returns truncated state text.
  - `mapped_source_blocker_next_step` can return
    `build_native_operator_readiness(...).get("next_step")` directly.
  - `command_center_next_step` returns
    `build_native_command_center_summary(...).get("next_action_summary")`
    directly.
- `custom_components/zero_net_export/native_support.py`
  - `MAX_NATIVE_SENSOR_STATE_CHARS = 255` exists and is already used by many
    summary builders.
- `tests/test_sensor_entity_categories.py` and
  `tests/test_command_center_summary.py` already contain several state length
  assertions, so adding focused regression coverage for the two affected keys
  fits existing test style.

## Live evidence

- `tmp/ha-core-logs-after-source-write-tail80-scan.txt` captured Home
  Assistant log lines where the two next-step sensors exceeded 255 characters
  and fell back to `unknown`.
- `tmp/ha-states-v0.2.3-source-write-restored.json` showed current restored
  state lengths under the limit:
  - `sensor.zero_net_export_source_blocker_next_step`: 156
  - `sensor.zero_net_export_command_center_next_step`: 147

## Proposed implementation path

1. Add a small helper for next-step state values, reusing the existing
   255-character state contract.
2. Apply it to:
   - `mapped_source_blocker_next_step`
   - `command_center_next_step`
3. Preserve the full guidance in attributes that already expose source,
   readiness, and command-center detail.
4. Add focused tests proving long next-step source text is capped at 255
   characters while detail remains available through attributes.

## Validation plan

- Run focused sensor/entity tests for next-step state length.
- Run existing command-center/source guidance focused tests touched by the
  helper.
- Run `python3 -m py_compile custom_components/zero_net_export/sensor.py`.
- Run `git diff --check`.
- If released, validate through the GitHub/HACS path and check HA logs for the
  absence of `sensor.zero_net_export_*_next_step is longer than 255` errors.

## Acceptance gate

Do not implement code until this feasibility check is accepted.
