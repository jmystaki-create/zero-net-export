<p align="center">
  <img src="zero-net-export.png" alt="Zero Net Export Logo" width="150"/>
</p>

<h1 align="center">Zero Net Export</h1>

<p align="center">
  <strong>Stop sending free power to the grid.</strong>
</p>

<p align="center">
  <a href="https://github.com/jmystaki-create/zero-net-export/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/jmystaki-create/zero-net-export/issues"><img src="https://img.shields.io/github/issues/jmystaki-create/zero-net-export?style=for-the-badge" alt="Issues"></a>
  <br>
  <em>Turn your Home Assistant into an active energy optimizer that keeps grid export at a precise target (ideally 0W).</em>
</p>

---

## 🚀 Quick Start

| **I want to...** | **Go here** |
| :--- | :--- |
| **Install via HACS** | [Add as Custom Repository](https://hacs.xyz/docs/faq/custom_repositories) → `jmystaki-create/zero-net-export` |
| **Install Manually** | [Copy to `custom_components`](#manual-installation) |
| **Set up the Dashboard** | [Dashboard Setup Guide](docs/DASHBOARD_SETUP.md) |
| **Understand the Logic** | [Control Loop Architecture](docs/CONTROL_LOOP.md) |

---

## 📖 Table of Contents

- [The Problem](#-the-problem)
- [The Solution](#-the-solution)
- [Key Features](#-key-features)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Documentation](#-documentation)
- [Safety & Reliability](#-safety--reliability)
- [Development Status](#-development-status)

---

## 🌍 The Problem

With export tariffs often near **zero**, every watt your solar panels push back to the grid is **money left on the table**. Standard Home Assistant automations are often too fragile to handle the real-time balancing required to keep export at zero without causing hardware stress or data errors.

## ⚡ The Solution

**Zero Net Export** transforms Home Assistant into an active energy strategist. It intelligently orchestrates your battery storage and flexible loads (EV chargers, hot water, pools) to absorb surplus solar *inside* your home.

Instead of letting excess energy vanish, it dynamically shifts consumption to match generation, ensuring you maximize self-consumption and get the most value from your solar investment.

## 🛡️ Key Features

- **Guard-First Control Engine**: Safety-first architecture with anti-flap logic, data validation, and safe-mode degradation.
- **Source-of-Truth Validation**: Ensures data integrity from solar, grid, and battery sources before acting.
- **Device Adapters**: Explicit control patterns (`fixed_toggle`, `variable_number`) for safe, resolved device control.
- **Runtime Safety**: Includes runtime caps, battery-reserve gating, and safe-mode degradation.
- **Explainable Decisions**: Rich diagnostics showing *why* actions were planned, blocked, or executed.
- **Operator Dashboard**: Lovelace dashboard scaffold for live monitoring and control.

---

## 📦 Installation

### Option 1: HACS (Recommended)

1.  Open **HACS** in Home Assistant.
2.  Click the **three dots (⋮)** → **Custom repositories**.
3.  Add:
    - **Repository**: `jmystaki-create/zero-net-export`
    - **Category**: `Integration`
4.  Click **Add**.
5.  Go to **Integrations**, find **Zero Net Export**, and click **Download**.
6.  **Restart Home Assistant**.

### Option 2: Manual Installation

1.  Copy the `custom_components/zero_net_export` folder into your Home Assistant `/config/custom_components/` directory.
2.  **Restart Home Assistant**.
3.  Go to **Settings** → **Devices & Services** → **Add Integration**.
4.  Search for **Zero Net Export**.

---

## ⚙️ Configuration

1.  Add the **Zero Net Export** integration.
2.  **Map your source entities**:
    - Solar Power
    - Grid Import/Export Power
    - Home Load Power
    - (Optional) Battery Entities
3.  Set your **Target Export** (e.g., `0W`) and **Deadband**.
4.  Configure your **controllable devices** (fixed or variable loads).

---

## 📚 Documentation

| Document | Description |
| :--- | :--- |
| [Architecture](docs/ARCHITECTURE.md) | System design and component overview |
| [Control Loop](docs/CONTROL_LOOP.md) | How the optimization logic works |
| [Dashboard Setup](docs/DASHBOARD_SETUP.md) | How to install the Lovelace UI |
| [Entity Model](docs/ENTITY_MODEL.md) | List of all created entities |
| [Product Spec](docs/PRODUCT_SPEC_V1.md) | Full product requirements and goals |

---

## 🛡️ Safety & Reliability

> **⚠️ Important**: This is a **developer preview**. Test in a non-production environment first.

- **Advisory Mode**: The controller operates in advisory mode by default; actual actuation requires explicit configuration.
- **Safe Mode**: Automatically enabled if source validation fails or data becomes stale.
- **Anti-Flap Logic**: Built-in delays and deadbands prevent rapid cycling of your hardware.
- **Data Validation**: Real-time checks ensure sensors are reporting valid data before acting.

---

## 🚧 Development Status

This integration is **functionally complete** and ready for real-world testing.

- [x] Config flow & source validation
- [x] Device model & guards
- [x] Guarded planner & executor
- [x] Diagnostics & action history
- [x] Dashboard scaffold
- [x] MIT license
- [ ] Real-world runtime validation (in progress)
- [ ] HACS release packaging (pending community feedback)

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
