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

## Release Closeout Evidence

- GitHub release `v0.4.20` published: https://github.com/jmystaki-create/zero-net-export/releases/tag/v0.4.20
- HACS/Home Assistant update entity installed/latest version: `v0.4.20`.
- Home Assistant restarted and `sensor.zero_net_export_installed_version` reports `0.4.20`.
- Live app rendered `Version 0.4.20` with tab order `Overview -> Managed Devices -> Sources -> Controls -> Runtime -> Diagnostics -> Settings`.
- Browser proof artifacts:
  - `validation/artifacts/zne-v0.4.20-overview-tab-order-desktop.png`
  - `validation/artifacts/zne-v0.4.20-managed-devices-desktop.jpg`
  - `validation/artifacts/zne-v0.4.20-sources-desktop.png`
  - `validation/artifacts/zne-v0.4.20-controls-desktop.png`
  - `validation/artifacts/zne-v0.4.20-runtime-desktop.png`
  - `validation/artifacts/zne-v0.4.20-managed-devices-mobile.jpg`
  - `validation/artifacts/zne-v0.4.20-runtime-mobile.png`

Live status note: Zero Net Export runtime may show source-role blockers when inverter/source entities are unavailable; that condition is separate from this UI/UX release.

