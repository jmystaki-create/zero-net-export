# Source Health Fix: Battery Discharge Power `state_class` Mismatch

## Problem

The `sensor.anker_battery_discharge_power` entity exposes `state_class=total`
instead of the required `state_class=measurement`. On the validation Home
Assistant instance it also reports in `kW`, while ZNE runtime values are
displayed and reconciled as watts. This causes Zero Net Export (ZNE) to report
`sensor.zero_net_export_status=degraded` with the reason:

> "Validation degraded: battery_discharge_power state_class is total; expected 'measurement'"

## Root Cause

The source integration classifies the battery discharge power sensor as a
`total` (cumulative) value instead of a `measurement` (instantaneous) value.
The live source also uses `kW`, so the safest workaround is to expose a
template sensor in watts with correct power metadata.

## Solution: Template Sensor Workaround

Create a Home Assistant template sensor that wraps the original sensor,
converts kW to W, and exposes `state_class=measurement`.

### Step 1: Add Template Sensor to `configuration.yaml`

Add the following to your Home Assistant `configuration.yaml` file:

```yaml
template:
  - sensor:
      - name: "Anker Battery Discharge Power (Fixed)"
        unique_id: "anker_battery_discharge_power_fixed"
        state_class: "measurement"
        unit_of_measurement: "W"
        device_class: "power"
        state: >-
          {{ (states('sensor.anker_battery_discharge_power') | float(0) * 1000) | round(0) }}
        attributes:
          original_entity: "sensor.anker_battery_discharge_power"
          original_unit: "kW"
```

If your source entity already reports watts, remove the `* 1000` conversion.

### Step 2: Restart Home Assistant

After saving `configuration.yaml`, restart Home Assistant to apply the changes.

### Step 3: Update ZNE Configuration

1. Navigate to **Settings > Devices & Services > Zero Net Export**.
2. Click **Configure** on your ZNE entry.
3. Update the **Battery Discharge Power Source** field to use the new template sensor:
   - Old value: `sensor.anker_battery_discharge_power`
   - New value: `sensor.anker_battery_discharge_power_fixed`
4. Save the configuration.

### Step 4: Verify Fix

1. Check the fixed template sensor has:
   - `device_class=power`
   - `state_class=measurement`
   - `unit_of_measurement=W`
2. Check `sensor.zero_net_export_status` - it should report `ok` once ZNE is
   pointed at the fixed sensor and source values reconcile.
3. Check `sensor.zero_net_export_reason` - it should be empty or non-blocking.
4. Verify power reconciliation in the **Diagnostics** tab.

## Alternative: ZNE Adaptation (Fallback)

If you cannot add a template sensor, ZNE may be adapted to accept `state_class=total` for battery discharge power. This is a fallback option and may be implemented in a future release if there is sufficient demand.

## Reporting the Issue

Consider reporting this issue to the Anker/EcoFlow integration maintainers:
- GitHub: [home-assistant/core](https://github.com/home-assistant/core)
- Integration: `anker` or `ecoflow`

## References

- Home Assistant Sensor Documentation: https://www.home-assistant.io/integrations/sensor/
- ZNE Milestone 4 Plan: `docs/ZNE_APP_MILESTONE_4_PLAN.md`

---

**Last Updated**: 2026-07-01  
**Status**: Recommended Fix
