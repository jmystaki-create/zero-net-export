# ZNE-588 Tier 2 candidate validation

Date: 2026-05-01
Status: candidate implemented locally; **not released**.

## Scope

Riley reported that the Tier 1 launcher buttons were visible but did not actually go anywhere, Diagnostics still ran for pages, and Tier 2 was not visible/accesssible.

This candidate changes the implementation boundary to match Home Assistant constraints:

- Native Home Assistant `button` rows are no longer treated as browser navigation controls.
- A real ZNE Tier 2 panel is registered at `/zero-net-export`.
- The existing managed-devices panel path remains available at `/zero-net-export-managed-devices` for compatibility.
- Tier 2 has visible sections for Overview, Sensors, Controls, Managed Devices, and Diagnostics.
- The primary controller device now exposes a `configuration_url` to `homeassistant://zero-net-export?section=overview&entry_id=<entry_id>`.
- Tier 1 launcher attributes/notifications now target the Tier 2 panel section URLs, e.g. `/zero-net-export?section=sensors&entry_id=<entry_id>`.
- Diagnostics are represented as a compact Tier 2 diagnostics section rather than treating the native device page as the long diagnostic surface.

## Important Home Assistant constraint

Home Assistant native button entities can run a press action, but they do not navigate the browser simply because an entity exposes `action_url`/`open_url` attributes. The previous implementation over-claimed this. The candidate provides an actual accessible Tier 2 page and uses launcher notifications/links plus device `configuration_url` as the supported access path.

## Repo validation evidence

Commands run from `/root/.openclaw/workspace/projects/zero-net-export`.

```text
python3 -m unittest -q tests.test_managed_devices_panel tests.test_button_entity_categories tests.test_integration_page_device_lists
----------------------------------------------------------------------
Ran 95 tests in 0.245s

OK
```

```text
python3 -m py_compile custom_components/zero_net_export/__init__.py custom_components/zero_net_export/button.py custom_components/zero_net_export/entity.py
# passed
```

```text
python3 -m unittest discover -s tests -q
----------------------------------------------------------------------
Ran 608 tests in 1.630s

OK
```

```text
git diff --check
# passed
```

## Screenshot/mock validation artifacts

Generated with a local Chromium harness using the implemented frontend component and mocked Home Assistant state. These prove the candidate frontend renders; they are not a live Home Assistant install validation.

- `/root/.openclaw/outbox/zero-net-export/2026-05-01/zne_tier2_overview_implemented.png`
- `/root/.openclaw/outbox/zero-net-export/2026-05-01/zne_tier2_sensors_implemented.png`
- `/root/.openclaw/outbox/zero-net-export/2026-05-01/zne_tier2_controls_implemented.png`
- `/root/.openclaw/outbox/zero-net-export/2026-05-01/zne_tier2_managed-devices_implemented.png`
- `/root/.openclaw/outbox/zero-net-export/2026-05-01/zne_tier2_diagnostics_implemented.png`

## Required before release

- Install candidate into Home Assistant through the approved release path only after Riley accepts the candidate evidence.
- Restart Home Assistant.
- Capture fresh live screenshots of:
  - actual device page with Tier 1 controls,
  - primary device configuration link opening Tier 2,
  - Tier 2 Sensors,
  - Tier 2 Controls,
  - Tier 2 Managed Devices,
  - compact Tier 2 Diagnostics,
  - diagnostics not overfilling the main native device page.
- Confirm installed fingerprint and runtime version.
- Review Home Assistant logs.

## Result

Candidate is repo-validated and screenshot-mocked, but **not released** and **not live-validated**.

## Live direct-deploy validation evidence

Date: 2026-05-01
Status: deployed to Home Assistant for validation; release acceptance still pending Riley screenshot review.

Deployment evidence:

- Release commit deployed: `04c124d`.
- Installed manifest version: `0.1.104`.
- Backup created before deploy: `/homeassistant/.openclaw_backups/zero_net_export-20260501-185826`.
- Restart evidence captured during deploy: Home Assistant API recovered after 25 seconds with `{"message":"API running."}`.
- Fingerprint comparison file: `tmp/install-fingerprint-compare-0.1.104-direct-deploy-now.json`.
- Fingerprint comparison result: `overall_match: true`; all tracked files match; no legacy discovery artifacts or stale bytecode paths found by the install fingerprint comparator.

Live Home Assistant entity evidence:

```text
button.winter_plan_open_controls_setup action_url /zero-net-export?section=controls&entry_id=01KQES4HMYAXXXSF6TQCAC8V28
button.winter_plan_open_sensors_setup action_url /zero-net-export?section=sensors&entry_id=01KQES4HMYAXXXSF6TQCAC8V28
button.winter_plan_open_managed_devices_setup action_url /zero-net-export?section=managed-devices&entry_id=01KQES4HMYAXXXSF6TQCAC8V28
button.winter_plan_open_diagnostics_setup action_url /zero-net-export?section=diagnostics&entry_id=01KQES4HMYAXXXSF6TQCAC8V28
button.summer_plan_open_controls_setup action_url /zero-net-export?section=controls&entry_id=01KQES5GS0B2XTEAK1SDHEK7KX
```

Live Tier 2 browser evidence captured from Home Assistant at `http://192.168.86.200:8123`:

- `/home/slave/.openclaw/media/zne-0.1.104/tier2-sensors.png`
- `/home/slave/.openclaw/media/zne-0.1.104/tier2-controls.png`
- `/home/slave/.openclaw/media/zne-0.1.104/tier2-managed-devices.png`
- `/home/slave/.openclaw/media/zne-0.1.104/tier2-diagnostics.png`
- `/home/slave/.openclaw/media/zne-0.1.104/tier1-integration.png`

Live Tier 2 Controls DOM evidence:

```text
Zero Net Export Tier 2 Accessible Tier 2 setup surface for Sensors, Controls, Managed Devices, and Diagnostics. Overview Sensors Controls Managed Devices Diagnostics Controls setup Review operator-facing control settings: enablement, mode, target export, reserve, and tuning controls. Winter Plan Enabled: on Winter Plan Target export: 0.0 Winter Plan Deadband: 100.0 Winter Plan Battery reserve SOC: 20.0 Winter Plan Mode: Zero export
```

Live compact Diagnostics DOM evidence:

```text
Zero Net Export Tier 2 Accessible Tier 2 setup surface for Sensors, Controls, Managed Devices, and Diagnostics. Overview Sensors Controls Managed Devices Diagnostics Diagnostics Compact Tier 2 diagnostics view. Showing the first 3 support items here instead of filling the native device page for pages. Winter Plan Diagnostic summary: Blocking source validation errors remain; safe mode is preventing control Winter Plan Review diagnostics: unknown Winter Plan Review diagnostics snapshot: unknown
```

Log evidence note:

- `/homeassistant/home-assistant.log.fault` exists and is zero bytes after restart.
- No current `/homeassistant/home-assistant.log` file was present at inspection time; historical `.log.1` and `.log.old` files exist, but do not contain current ZNE validation output.

Remaining acceptance gate:

- Riley must review and accept the live screenshots before this can be called fully accepted/released.
