# ZNE Managed Devices Load Dashboard Feasibility

Date: 2026-08-02
Scope: Managed Devices tab UI/UX refactor
Source review: `ui_ux_review.md` / Managed Devices section

## Target Environment

- Home Assistant sidebar custom panel delivered through the existing HACS integration.
- Frontend file: `custom_components/zero_net_export/frontend/zero-net-export-app.js`.
- Primary data source: `sensor.managed_devices_overview` attributes.
- Supporting live power data: existing Overview reconciliation sensors read by `_reconciliationMetrics()`.

## Live Evidence

Read-only Home Assistant API check returned HTTP `200` for `sensor.managed_devices_overview`.

Live managed fleet attributes showed:

- `managed_count=2`
- `enabled_count=1`
- `disabled_count=1`
- `usable_count=1`
- `nominal_power_w=2405`
- `active_count=1`
- `active_power_w=0`
- `candidate_count=31`
- `review_needed_count=16`
- `ready_candidate_count=15`

The live disabled-active device is `Lounge Room - Heated Floor`: disabled, not usable, observed active, `nominal_power_w=2400`, `current_power_w=null`.

## Supported

- The frontend can derive total, enabled, disabled, usable, and disabled-active nominal load from compact `managed_devices` attributes.
- The frontend can display measured per-device watts when `current_power_w` is present.
- The frontend can display estimated active load when `observed_active` is true and `current_power_w` is missing.
- The frontend can preserve existing controls because the first pass changes presentation only.
- The existing HACS release path can deliver the frontend change.

## Unsupported / Excluded For First Pass

- Treating nominal-power estimates as measured consumption is not supported.
- Changing planner/control behavior is out of scope.
- Bypassing existing enable/disable, remove, or promotion confirmation flows is out of scope.

## Unknown / Follow-Up

- Whether aggregate Home Assistant sensors should be added for enabled/disabled/estimated active load. The first pass can derive this in the frontend; backend sensors are tracked separately only if needed after validation.
- Candidate queue watt estimation may need backend semantics before it can be trusted. First pass keeps candidate promotion intact and records candidate load-awareness as a follow-up card.

## Implementation Decision

Proceed with a frontend-first Managed Devices refactor:

1. Add a managed-load dashboard using existing attributes and `_reconciliationMetrics()`.
2. Split the misleading `Power` traffic-light column into `Load` and `State`.
3. Add a disabled-active alert using estimated watts when measured power is missing.
4. Preserve all existing service calls, confirmation gates, filters, sorting, candidate review, promotion, Diagnostics, and HACS delivery.

## Validation Plan

- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- Focused pytest for managed devices panel source guards.
- Full unit test discovery before release.
- Browser proof after HACS install/restart: desktop and narrow/mobile Managed Devices tab.
- Live API proof that installed version and managed fleet attributes remain available.
