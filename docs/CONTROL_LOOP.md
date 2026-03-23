# Control Loop

## Inputs
- mapped energy sources
- current mode
- export target and deadband
- device inventory
- device priority and policy settings
- battery policy / reserve

## Cycle outline

1. Read current runtime state
2. Validate values and source confidence
3. If confidence too low, enter safe mode
4. Parse / validate device inventory
5. Compute target error:
   - current export - target export
6. If within deadband, hold state unless another policy applies
7. Determine available control headroom across usable devices
8. Prefer variable-power devices for fine adjustment
9. Use fixed loads for coarse surplus absorption
10. Enforce min-on / min-off / max runtime / min runtime rules
11. Apply selected actions
12. Record explanation and action summary

## Control strategy for v1

### If export is above target
- increase variable loads if possible
- turn on next eligible fixed loads by priority if needed

### If import is above allowed tolerance
- reduce variable loads
- turn off lower-priority fixed loads if needed

### If battery below reserve
- block discretionary absorption actions depending on mode

## Anti-flap rules
- deadband around target
- per-device minimum on time
- per-device minimum off time
- optional action cooldown

## Current implementation boundary
- source validation can already block control
- device inventory can already distinguish configured vs usable devices
- per-device explainability exists
- advisory action planning is implemented: each cycle computes export error, holds inside deadband, prefers variable devices for fine adjustment, uses fixed devices for coarse steps where allowed, and exposes per-device planned actions
- planner modes are now materially distinct in the control loop:
  - `zero_export` uses the configured export target directly
  - `soft_zero_export` lifts the effective export target to at least the deadband, tolerating a small export margin
  - `self_consumption_max` lowers the effective target to at least one deadband below zero so controllable loads bias toward soaking extra surplus
  - `import_min` lifts the effective export target to at least the deadband and disables fixed-load absorption, so the controller avoids turning on coarse loads just to chase small exports
- an initial battery reserve policy is now implemented: when battery SOC falls below the configured reserve threshold, the planner holds discretionary surplus-absorption actions instead of turning on extra controllable load, while still allowing import-pressure shedding
- optional max-runtime safety caps are now implemented: when an active device exceeds its configured `max_active_seconds`, the planner pre-empts normal balancing and emits a safety action first (fixed loads are turned off; variable loads are wound back toward their configured minimum)
- variable-device planning is now current-target aware: increase/decrease actions are computed from each device's observed current target, capped by configured min/max/step limits, so the requested power is an incremental next target instead of an absolute reset guess
- runtime guard evaluation is now implemented: each configured device tracks observed active/inactive state plus last transition timing so planned actions can be classified as ready, already satisfied, or blocked by min-on / min-off / cooldown rules
- runtime-cap safety actions can now intentionally bypass normal min-on / cooldown anti-flap blocks, because they are treated as protective preemption rather than routine balancing
- controller-level sensors now expose how many planned actions are guard-approved versus blocked
- first live execution is now implemented, but intentionally narrowly: only guard-approved actions are attempted, each device must resolve to a safe adapter first, `fixed_toggle` devices use entity-domain `turn_on` / `turn_off`, `variable_number` devices use `number.set_value` / `input_number.set_value`, and unsupported cases remain blocked with explicit adapter reason state
- recent action results are recorded in runtime history attributes and emitted as `zero_net_export.action_applied` events
- safe-mode transitions now emit `zero_net_export.safe_mode_entered` / `zero_net_export.safe_mode_exited`, and source-mismatch transitions emit `zero_net_export.source_mismatch` / `zero_net_export.source_mismatch_cleared`
- per-device last requested / last applied power targets plus cumulative action counters now persist across reloads so the operator does not lose control context after a restart

## Safe mode behavior
- monitor only
- or conservative variable-load-only behavior
- emit clear explanation state
- mark every configured device as blocked rather than pretending it is ready

## Guard-layer intent

The new guard layer is the bridge between advisory planning and real actuation.

For each device it currently tracks:
- observed active/inactive state from the configured Home Assistant entity
- last observed state change time
- last observed on time
- last observed off time
- last guard-approved action time and type

This means the next milestone can safely add a service-call executor that only acts on guard-approved plans, instead of trying to mix state inference and actuation logic in one step.
