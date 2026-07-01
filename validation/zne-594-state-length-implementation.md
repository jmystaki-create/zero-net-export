# ZNE-594 state length implementation

Date: 2026-07-01
Status: repo validated; pending release/live validation

## Scope

ZNE-594 fixes Home Assistant log errors where long operator next-step strings
could exceed the 255-character entity state limit for:

- `sensor.zero_net_export_source_blocker_next_step`
- `sensor.zero_net_export_command_center_next_step`

The accepted feasibility check is
`validation/zne-594-state-length-feasibility.md`.

## Change

- Added `_next_step_sensor_state(...)` in
  `custom_components/zero_net_export/sensor.py`.
- Applied it to the source-blocker next-step fallback from
  `build_native_operator_readiness(...).get("next_step")`.
- Applied it to command-center `next_action_summary` when exposed as the
  entity state.
- Preserved the full command-center next-step text in
  `extra_state_attributes["current_next_step"]`.
- Existing source-blocker attributes continue to preserve the full
  `current_native_next_step`.

## Acceptance criteria

- Affected next-step sensor state values are never longer than 255 characters.
- Full guidance remains available in attributes.
- Existing short next-step wording remains unchanged.
- Repo validation passes.

## Validation

Passed:

- `python3 -m unittest -q tests.test_sensor_entity_categories`
  - `Ran 60 tests`
  - `OK`
- `python3 -m py_compile custom_components/zero_net_export/sensor.py tests/test_sensor_entity_categories.py`
- `python3 -m unittest -q tests.test_command_center_summary`
  - `Ran 160 tests`
  - `OK`
- `python3 -m unittest discover -s tests`
  - `Ran 620 tests`
  - `OK`
  - Output includes expected negative-path `ERROR:` lines from release/deploy
    guard tests.
- `git diff --check`

## Remaining validation

- Release/live validation through the approved GitHub/HACS path.
- After installation, check Home Assistant logs for absence of
  `sensor.zero_net_export_*_next_step is longer than 255` errors.
- Browser Sources proof for `v0.2.3` remains a separate validation gap.
