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
