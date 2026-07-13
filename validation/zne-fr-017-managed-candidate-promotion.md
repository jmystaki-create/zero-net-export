# ZNE-FR-017 Managed Candidate Promotion

Date: 2026-07-13
Status: released/live-validated in v0.4.10

## Request

Riley requested a Managed Devices workflow that promotes devices from the
Unmanaged Candidate Queue into the managed Fleet List, including the workflow
that adds the Zero Net Export managed-device property in Home Assistant.

## Classification

- Type: feature
- State: Released/live-validated
- Primary surface: Zero Net Export Home Assistant application, Managed Devices tab
- Supporting surface: Home Assistant Zero Net Export integration/device registry

## Acceptance Criteria

- Each eligible unmanaged candidate has a visible `Review & promote` action in
  the Managed Devices app.
- The promote workflow shows the candidate name, entity id, kind, current
  reading, fit summary, warnings, suggested template, and editable managed-load
  settings.
- Saving writes one validated managed-device inventory payload to the selected
  Zero Net Export config entry.
- Duplicate promotions are blocked before changing config.
- Invalid candidates/settings show an operator-facing error and do not change
  config.
- The original Home Assistant device/entity owned by its source integration is
  not modified or removed.
- After save/reload, the promoted row appears in Fleet List and the Unmanaged
  Candidate Queue count/rows refresh.
- Home Assistant exposes the promoted load as a Zero Net Export managed child
  device using the existing managed-load `device_info` fields:
  `identifiers`, `via_device`, `configuration_url`, manufacturer/model/name,
  and integration version.

## Target Environment Feasibility

### Supported

- The Zero Net Export app owns the Managed Devices DOM and can add candidate-row
  actions and an in-app review form.
- The app can call Zero Net Export backend services with selected `entry_id`.
- Existing config/options flow code already implements the candidate promotion
  shape: pick candidate, review candidate, choose template, confirm add-time
  settings, validate inventory, save, and reload.
- Existing device model code defines the managed-device payload fields and
  templates for fixed and variable loads.
- Existing managed-load entity setup attaches ZNE managed entities to a child
  Home Assistant device using `managed_load_device_info(...)` with `via_device`
  and `configuration_url`.

### Unsupported / Excluded

- Do not add a custom `Promote` action to another integration's original Home
  Assistant device page or overflow menu. Prior HA source/live feasibility found
  no general custom-integration hook for arbitrary device-page action injection.
- Do not mutate or merge into another integration's original Home Assistant
  device registry row. Promotion creates a ZNE managed child device associated
  with the Zero Net Export config entry.
- Do not write directly to the Home Assistant file backend for release or live
  validation. Changes must flow through GitHub/HACS.

### Unknowns

- Final UI shape: inline expanded row, modal, or side panel. The simplest first
  implementation should use an inline candidate review panel inside the existing
  Managed Devices app.
- Whether ready candidates should allow one-click promotion. Initial release
  should require review/confirmation for all candidates to avoid accidental
  automation of unsafe loads.

## Recommended Operator Workflow

1. Operator opens Zero Net Export, then Managed Devices.
2. Fleet List remains first; Unmanaged Candidate Queue appears below it.
3. Operator clicks `Review & promote` on a candidate.
4. The app opens a candidate review panel with fit/warnings and suggested
   template.
5. Operator confirms or edits name, entity id, kind, template, nominal/min/max
   power, step, priority, enabled state, and timing limits.
6. Operator clicks `Promote to fleet`.
7. Backend validates the candidate and resulting inventory payload.
8. Backend writes `CONF_DEVICE_INVENTORY_JSON` for the selected ZNE entry and
   reloads that entry.
9. App refreshes. The candidate moves into Fleet List; unmanaged counts update.
10. Home Assistant shows a ZNE managed child device named
    `Managed Devices - <name>` under the Zero Net Export device/integration
    surface, linked back to the ZNE configuration route.

## Implementation Plan

### Backend

- Added `zero_net_export.promote_managed_device`.
- Inputs include selected `entry_id`, candidate `entity_id`, template key, and
  optional overrides for editable managed-load fields.
- The backend resolves the current selected config entry and live surfaced
  candidate server-side so the app cannot promote arbitrary stale data.
- Promotion builds a managed-device payload with candidate/template defaults.
- Promotion validates with `parse_device_configs(...)`.
- Promotion rejects already-managed entity ids, unavailable candidates, invalid
  settings, and duplicate managed-device keys.
- Promotion saves to `CONF_DEVICE_INVENTORY_JSON`, reloads the config entry, and
  creates a persistent notification that the original HA device/entity was left
  untouched.

### Frontend

- Added a candidate-row action column with `Review & promote`.
- The app tracks the selected promotion candidate in state.
- The app renders a compact review/settings panel using the current app style.
- The app submits selected `entry_id`, candidate `entity_id`,
  template/settings overrides, and confirmation to the backend service.
- On success, the app clears the promotion panel and shows a reload/status
  message; on error, the existing inline message path displays the failure.

### Home Assistant Device Property Workflow

- Promotion does not edit the original entity's HA device.
- Promotion writes a ZNE managed-device inventory row.
- After reload, existing managed-load entities are created/refreshed for that
  inventory row.
- Those entities call `attach_managed_load_device(...)`, which sets
  `device_info` from `managed_load_device_info(...)`.
- Home Assistant's device registry then exposes a ZNE child device connected via
  the primary ZNE controller device, with `configuration_url` routing back to
  the supported ZNE configuration/integration path.

## Validation Plan

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- Focused Managed Devices frontend tests covering the candidate action, review
  panel, service payload, success state, and error state.
- Backend tests covering promotion, duplicate rejection, invalid candidate
  rejection, selected-entry scoping, fixed/variable templates, and original
  source preservation.
- Entity/device-info tests proving promoted managed loads expose identifiers,
  `via_device`, `configuration_url`, and expected display name/model.
- Full unit test discovery.
- `git diff --check`.
- Release/live validation through GitHub/HACS only:
  - install release in Home Assistant;
  - restart;
  - fingerprint match;
  - use Slave browser to promote a disposable candidate;
  - confirm Fleet List/Unmanaged queue movement;
  - confirm Home Assistant Zero Net Export device/integration surface shows the
    promoted managed child device;
  - remove the test managed record and confirm the original HA entity remains.

## Repo Validation

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
  - Result: PASS
- `python3 -m py_compile custom_components/zero_net_export/__init__.py`
  - Result: PASS
- `python3 -m unittest -v tests.test_managed_devices_panel`
  - Result: PASS, 23 tests
- `python3 -m unittest -v tests.test_integration_page_device_lists`
  - Result: PASS, 43 tests
- `python3 -m unittest -v tests.test_config_flow_device_runtime_overlay`
  - Result: PASS, 92 tests
- `python3 -m unittest -v tests.test_candidate_review_copy`
  - Result: PASS, 1 test
- `python3 -m unittest discover -v`
  - Result: PASS, 637 tests
- `git diff --check`
  - Result: PASS

## Release / Live Validation

- Release: `v0.4.10`
- GitHub release:
  `https://github.com/jmystaki-create/zero-net-export/releases/tag/v0.4.10`
- Release commit/tag source: `da01c4c`
- HACS/Home Assistant install:
  - `update.zero_net_export_update` installed/latest `v0.4.10`
  - `sensor.zero_net_export_installed_version` state `0.4.10`
- Install fingerprint:
  - `python3 scripts/validate_install_fingerprint.py /config/custom_components --ssh-host root@192.168.86.200 --ssh-port 2222`
  - Result: PASS, `overall_match=true`, manifest `0.4.10`, no tracked-file mismatches
- Services:
  - `zero_net_export.promote_managed_device` registered
  - `zero_net_export.remove_managed_device` registered
  - `zero_net_export.update_managed_device` registered
- Reversible live promotion proof:
  - Candidate: `switch.ac_outlet_1` (`Lounge Room - Heated Floor`)
  - Promotion service call used `enabled:false` and `confirm:true`
  - Result: disabled managed record `zne_fr017_validation_ac_outlet_1` appeared in Fleet List
  - Candidate queue result: `switch.ac_outlet_1` left the unmanaged queue while promoted
  - Cleanup: `zero_net_export.remove_managed_device` with `confirm:true` removed the validation record
  - Post-cleanup result: validation record count `0`, `switch.ac_outlet_1` restored to unmanaged candidates, original HA entity still present
- Slave browser proof:
  - App opened at `http://192.168.86.200:8123/zero-net-export?validation=zne-fr-017-v0410-promotion`
  - Header showed `Version 0.4.10`
  - Managed Devices showed Fleet List before Unmanaged Candidate Queue
  - Candidate rows showed `Review & promote`
  - Promotion panel rendered for `switch.ac_outlet_1` with editable settings and the confirmation text:
    `The original Home Assistant device/entity will not be modified.`
- Log review:
  - Known Zero Net Export recorder attribute-size warnings remain and are tracked under `ZNE-595`
  - No new Zero Net Export traceback or promotion-specific release blocker was found in the post-validation log review

## Recommendation

Proceed with the app-owned `Review & promote` workflow, backed by a dedicated
backend promotion service/helper and the existing ZNE managed child-device
metadata path. Keep native Home Assistant device pages as supporting navigation
surfaces through `configuration_url`; do not attempt unsupported custom device
page action injection.
