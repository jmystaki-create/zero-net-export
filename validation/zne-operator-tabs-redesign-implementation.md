# Zero Net Export Operator Tabs Redesign Implementation

Date: 2026-08-02
Scope: tab order plus Sources, Controls, and Runtime tab redesign

## Implemented

- Reordered app tabs to `Overview -> Managed Devices -> Sources -> Controls -> Runtime -> Diagnostics -> Settings`.
- Redesigned Sources as a source-health workspace:
  - source health strip
  - reading trust summary
  - source blocker and stale-source prominence
  - control-impact panel
  - per-source role/status/live-value/freshness/bound-entity table
  - existing source-role edit fields and selected-plan scoped save retained
- Redesigned Controls as a policy workspace:
  - command bar with current enabled state, live mode, executor state, and one enable/disable action
  - grouped mode/target/deadband/reserve policy controls
  - safety guard card
  - "What Will Happen Next?" runtime preview
  - existing switch/select/number service calls retained
- Redesigned Runtime as an execution/activity workspace:
  - live execution header
  - power flow snapshot
  - decision panel
  - activity evidence
  - Diagnostics remains the raw/support detail surface
- Preserved Managed Devices watt dashboard and workflows.

## Validation Evidence

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js` passed.
- `python3 -m pytest tests/test_managed_devices_panel.py -q` passed: `31 passed`.
- `python3 -B -m unittest discover -s tests -q` passed: `Ran 647 tests ... OK`.
- `git diff --check` passed.

The full unittest command printed expected negative-case installer validation messages while still exiting successfully.

## Pending Before Release Closeout

- Desktop browser proof in Home Assistant.
- Narrow/mobile browser proof in Home Assistant.
- HACS release/install/restart validation if this scope is released.

