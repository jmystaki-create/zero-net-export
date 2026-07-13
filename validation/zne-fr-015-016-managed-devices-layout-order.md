# ZNE-FR-015 / ZNE-FR-016 Managed Devices Layout And Order Validation

Date: 2026-07-13

## Scope

Riley requested two Managed Devices app polish changes:

- Improve the Fleet Summary layout so the `0 Stale` chip does not sit oddly below the other counts or render as cramped `0Stale` text.
- Move unmanaged devices after managed devices in the Managed Devices page sequence.

## Target Environment Feasibility

- **Target environment:** existing Zero Net Export Home Assistant custom panel, served from `custom_components/zero_net_export/frontend/zero-net-export-app.js`.
- **Supported:** the existing panel owns its DOM and CSS and can reorder sections and adjust layout classes without Home Assistant frontend patches.
- **Unsupported / excluded:** no native Home Assistant device-page injection, no new Home Assistant API, and no backend entity schema changes are needed for this request.
- **Unknown:** final installed visual appearance still needs release/live browser proof after HACS install.

## Acceptance Criteria

- Fleet Summary total/enabled/disabled/blocked/stale counts remain present.
- Fleet Summary count and label text have visible spacing.
- Fleet Summary chips use an even compact wrapping layout.
- The managed Fleet List renders before the Unmanaged Candidate Queue.
- Unmanaged candidate counts and rows remain visible.

## Repo Validation

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
  - Result: PASS
- `python3 -m unittest -v tests.test_managed_devices_panel`
  - Result: PASS, 22 tests
- `python3 -m unittest discover -v`
  - Result: PASS, 636 tests
- `git diff --check`
  - Result: PASS

## Slave Browser Live Validation Attempt

Attempted: 2026-07-13 via Slave Debian Browser Node against `http://192.168.86.200:8123/zero-net-export?validation=zne-fr-015-016-layout-order-20260713`.

Result: **BLOCKED / NOT PASSED** because Home Assistant is still running the previously installed app build.

Evidence captured from the installed Home Assistant app:

- Header reported `Version 0.4.8 · 1 plan`.
- Fleet Summary still used the old `.zne-fleet-stats` / `.zne-stat` layout, not the new compact stat grid.
- Fleet Summary text rendered as `Fleet Summary 1 Total 1 Enabled 0 Disabled 0 Blocked 0 Stale`, and screenshot proof still showed cramped `1Total` / `0Stale` chips.
- DOM heading positions showed `Unmanaged Candidate Queue (30 candidates)` at top `655` and `Fleet List (1 devices)` at top `4550`.
- Computed check: `unmanagedBeforeFleetList=true`.

Conclusion: the local source changes are not yet installed in Home Assistant, so live UI validation cannot pass until the changes flow through the approved GitHub/HACS path.

## Release / Live Validation Pending

After packaging and installing through HACS:

- Open the Managed Devices tab in the Home Assistant app.
- Confirm Fleet Summary chips have clear count/label spacing and compact wrapping on desktop and narrow widths.
- Confirm Fleet List appears before Unmanaged Candidate Queue.
- Capture browser proof and run targeted Zero Net Export log checks.

## Release / Live Validation Passed

Release: `v0.4.9`

Evidence: `validation/0.4.9-release-validation.md`

Result: **PASS**

- GitHub release `v0.4.9` was published from commit `e01a6d5927d2ad4cbcea6da37caf4fc99a7d3630`.
- HACS installed `v0.4.9`; `update.zero_net_export_update` reported installed/latest `v0.4.9`.
- Install fingerprint validation over Home Assistant SSH reported `overall_match=true`, manifest `0.4.9`, expected component commit `e01a6d5`, and no legacy artifacts.
- Home Assistant restarted and loaded `sensor.zero_net_export_installed_version=0.4.9`.
- Slave browser desktop proof showed app header `Version 0.4.9 · 1 plan`, `.zne-fleet-summary-stats` present, `0 Stale` with a `4px` count/label gap, and `Fleet List (1 devices)` before `Unmanaged Candidate Queue (29 candidates)`.
- Slave browser narrow viewport proof at `390x844` retained separate stat text and `fleetListBeforeUnmanaged=true`.

Known unrelated runtime risk: recorder attribute-size warnings for Zero Net Export entities remain and are tracked under `ZNE-595`.
