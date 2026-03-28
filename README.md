<p align="center">
  <img src="zero-net-export.png" alt="Zero Net Export Logo" width="200"/>
</p>

# Zero Net Export

> **Stop sending free power to the grid.**

With export tariffs often near zero, every watt your solar panels push back to the grid is money left on the table. **Zero Net Export** solves this by turning your Home Assistant into an active energy optimizer that aggressively keeps your grid export at a precise, user-defined target—ideally **0W**.

Instead of letting excess solar vanish into the grid, this system intelligently orchestrates your battery storage and flexible loads (EV chargers, hot water, pools) to absorb that surplus *inside* your home. It dynamically shifts consumption to match generation, ensuring you maximize self-consumption and get the most value from your solar investment.

**Built for safety and reliability:**
Unlike fragile automation scripts, Zero Net Export is a **guard-first control engine**. It validates data integrity in real-time, applies anti-flap logic to protect your hardware from rapid cycling, and automatically degrades into a safe mode if sensors drift or data becomes uncertain. Whether you are avoiding export fees, balancing a microgrid, or simply trying to get every cent of value from your solar panels, Zero Net Export provides the operator-grade precision and safety needed to run your home as a true, self-sufficient energy system.

## Features

- **Source-of-Truth Validation**: Ensures data integrity from solar, grid, and battery sources before acting.
- **Guarded Control Loop**: Implements anti-flap logic (min on/off times, deadbands) and safety guards.
- **Device Adapters**: Explicit control patterns (`fixed_toggle`, `variable_number`) for safe, resolved device control.
- **Runtime Safety**: Includes runtime caps, battery-reserve gating, and safe-mode degradation.
- **Explainable Decisions**: Rich diagnostics showing why actions were planned, blocked, or executed.
- **Operator Dashboard**: Lovelace dashboard scaffold for live monitoring and control.

## Installation

### Option 1: HACS (Recommended)

1. Add this repository as a **Custom Repository** in HACS:
   - Repository: `jmystaki-create/zero-net-export`
   - Category: **Integration**
2. Click **Download**.
3. **Restart Home Assistant**.
4. Go to **Settings** → **Devices & Services** → **Add Integration**.
5. Search for **Zero Net Export**.

### Option 2: Manual Install

1. Copy the `custom_components/zero_net_export` folder into your Home Assistant `/config/custom_components/` directory.
2. **Restart Home Assistant**.
3. Add the integration via **Settings** → **Devices & Services**.

## Configuration

1. Add the **Zero Net Export** integration.
2. Map your source entities:
   - Solar power
   - Grid import/export power
   - Home load power
   - (Optional) Battery entities
3. Set your **Target Export** (e.g., 0W) and **Deadband**.
4. Configure controllable devices (fixed or variable loads).

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Control Loop Logic](docs/CONTROL_LOOP.md)
- [Dashboard Setup](docs/DASHBOARD_SETUP.md)
- [Entity Model](docs/ENTITY_MODEL.md)
- [Product Spec](docs/PRODUCT_SPEC_V1.md)

## Dashboard

A Lovelace dashboard scaffold is included at `examples/lovelace/zero_net_export_dashboard.yaml`.

1. Copy the YAML into your HA config (e.g., `/config/lovelace/zero_net_export_dashboard.yaml`).
2. Add it as a new dashboard in **Settings** → **Dashboards**.
3. Adjust entity IDs to match your setup.

## Safety Notes

- The controller operates in **advisory mode** by default; actual actuation requires explicit configuration.
- **Safe Mode** is enabled if source validation fails or data is stale.
- Always test in a non-production environment first.

## Development Status

This is a **developer preview**. It is functional but not yet production-hardened.

- [x] Config flow & source validation
- [x] Device model & guards
- [x] Guarded planner & executor
- [x] Diagnostics & action history
- [x] Dashboard scaffold
- [ ] Real-world runtime validation
- [ ] HACS release packaging

## License

MIT
