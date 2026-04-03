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
| **Open the Operator App** | Install the integration, restart Home Assistant, then open **Zero Net Export** from the sidebar |
| **Use the fallback dashboard** | [Dashboard Setup Guide](docs/DASHBOARD_SETUP.md) |
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
- **Operator Panel App**: Home Assistant sidebar panel shell for overview, setup, devices, diagnostics, and settings.
- **Operator Dashboard**: Lovelace dashboard scaffold retained as a fallback/debugging surface.

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

### Primary operator path: panel app

1.  Add the **Zero Net Export** integration.
2.  Open **Zero Net Export** from the Home Assistant sidebar.
3.  Use the **Setup** tab to map your source entities:
    - Solar Power
    - Grid Import/Export Power
    - Home Load Power
    - (Optional) Battery Entities
4.  Use the **Devices** tab to add and manage controllable devices with the guided panel editor.
5.  Use the **Settings** tab to review runtime defaults and release/support information.
6.  Use **Overview** and **Diagnostics** for daily operation, warnings, and explanation.

### Advanced / fallback paths

- The Home Assistant config flow still establishes the backend entry and core source mapping.
- The Lovelace YAML dashboard remains available as a fallback/debugging surface, not the primary intended operator UX.

---

## 📚 Documentation

| Document | Description |
| :--- | :--- |
| [Architecture](docs/ARCHITECTURE.md) | System design and component overview |
| [Control Loop](docs/CONTROL_LOOP.md) | How the optimization logic works |
| [Panel-App Rebuild Plan](docs/PANEL_APP_REBUILD_PLAN.md) | New app-first direction and rebuild phases |
| [Panel App Technical Design](docs/PANEL_APP_TECHNICAL_DESIGN.md) | App sections, backend contract, and delivery milestones |
| [Dashboard Setup](docs/DASHBOARD_SETUP.md) | How to install the fallback/debug Lovelace UI |
| [Entity Model](docs/ENTITY_MODEL.md) | List of all created entities |
| [Product Spec](docs/PRODUCT_SPEC_V1.md) | Full product requirements and goals |
| [Validation Checklist](docs/VALIDATION_CHECKLIST.md) | Real-installation sign-off checklist |
| [Release Process](docs/RELEASE_PROCESS.md) | Versioning, changelog, tags, and release workflow |
| [Branding](docs/BRANDING.md) | Logo usage and HACS / Home Assistant branding notes |
| [Changelog](CHANGELOG.md) | User-visible changes by version |

---

## 🛡️ Safety & Reliability

> **⚠️ Important**: This is a **developer preview**. Test in a non-production environment first.

- **Advisory Mode**: The controller operates in advisory mode by default; actual actuation requires explicit configuration.
- **Safe Mode**: Automatically enabled if source validation fails or data becomes stale.
- **Anti-Flap Logic**: Built-in delays and deadbands prevent rapid cycling of your hardware.
- **Data Validation**: Real-time checks ensure sensors are reporting valid data before acting.

---

## 🚧 Development Status

The backend control engine is substantially built, and the project is now in a late **stabilization + app-first rebuild** phase focused on validating and hardening the shipped panel-first operator workflow in real Home Assistant installs.

- [x] Config flow & source validation
- [x] Device model & guards
- [x] Guarded planner & executor
- [x] Diagnostics & action history
- [x] Dashboard scaffold
- [x] MIT license
- [ ] Stabilize install/runtime behavior in real Home Assistant environments
- [x] Ship the first panel-style app shell in Home Assistant
- [x] Make the panel the primary intended operator UX for setup, devices, operation, diagnostics, and release/support context
- [x] Add full add/edit/remove device workflows to the panel so operators no longer need raw JSON for normal setup
- [x] Add guided device onboarding presets and direct edit flows so normal device setup feels panel-native instead of form spelunking
- [x] Add template-aware device entity suggestions so panel onboarding can point operators at likely switch/number targets instead of only offering a flat entity list
- [x] Add guided source mapping to the panel so operators can complete source setup in the app
- [x] Add role-specific source suggestions in the panel so operators can pick likely solar/grid/home/battery sensors without sifting through every entity manually
- [x] Add guided source-remediation detail in the panel so operators can inspect per-source metadata and validation issues without dropping into raw entity debugging
- [x] Add runtime operator controls to the panel for controller tuning and per-device override management
- [x] Add richer in-panel diagnostics and explanation views for recent actions, source health, and per-device control reasoning
- [x] Keep the panel state live enough for daily operation via automatic in-panel refresh while visible
- [x] Keep release metadata visible and accurate in-panel so operators/support can distinguish packaged integration version from HA config-entry schema version
- [x] Publish in-panel readiness guidance so operators can see the current setup phase, blockers, and highest-value next step without piecing it together from raw diagnostics
- [x] Publish an in-panel support snapshot so operators can copy a concise runtime/setup/release summary into Discord or issue reports during real-world validation
- [ ] Real-world validation of the rebuilt operator flow
- [ ] Final install/runtime hardening based on real HA feedback

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
