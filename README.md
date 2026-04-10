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
| **Configure the integration** | Install the integration, restart Home Assistant, then open **Settings → Devices & Services → Integrations → Zero Net Export → Configure** |
| **Use optional Lovelace debug visibility** | [Dashboard Setup Guide](docs/DASHBOARD_SETUP.md) |
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
- **Native Home Assistant setup path**: source mapping, managed-device configuration, and controller tuning live in the integration's Configure flow.
- **Configure is the intended command center**: the product direction is for operators to find sources, policy, managed devices, and support from one obvious native path.
- **Native managed-device workspace**: day-to-day device onboarding and edit-in-place updates now have native add/remove/edit flows for fixed and variable devices, guided presets for common loads like hot water, pool pumps, EV chargers, and battery charge sinks, plus a fleet-review enable/disable step for staging larger installs without dropping into raw JSON.
- **Native Home Assistant operator surfaces**: Configure, the integration device page, entities, notifications, and Repairs are the supported operator path.
- **Native support actions**: device-page diagnostic buttons can raise a combined support center, a setup checklist, and a detailed support snapshot as persistent notifications, and those button entities are callable from Scripts / Automations via `button.press`.
- **Native Repairs guidance**: Home Assistant's Repairs surface now flags incomplete setup, invalid managed-device configuration, and runtime attention states with actionable next steps.

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

### Primary operator path: native Home Assistant Configure flow

1.  Add the **Zero Net Export** integration.
2.  Complete the **minimal bootstrap config flow** by giving the system a clear name.
3.  Open **Settings** -> **Devices & Services** -> **Integrations** -> **Zero Net Export** -> **Configure**.
4.  Use **Native setup, source mapping, and refresh interval** to map your source entities:
    - Solar Power
    - Grid sensors, either as one combined/net pair or as separate import/export entities
    - Home Load Power (optional if solar and grid sources are already mapped)
    - (Optional) Battery Entities
5.  Use **Managed devices** in Configure to add fixed or variable controllable devices through native selectors. Use the fleet review there to quickly enable or disable devices across a larger install. Use the JSON editor only for bulk structural edits or recovery.
6.  Use **Controller tuning / policy** in Configure for target/deadband/reserve defaults and related control behavior.
7.  Use the managed-device steps in Configure to review, add, edit, enable/disable, and remove controllable loads.
8.  Use the integration device page buttons, entities, and diagnostics for normal runtime verification and troubleshooting.

### Advanced / fallback paths

- The initial add-integration flow remains bootstrap-only, and the normal post-install path is the native Configure flow.
- Managed devices are still persisted internally as structured inventory JSON, but the primary native Configure flow now hides most of that behind add/edit/remove forms for fixed and variable devices.
- The Lovelace YAML dashboard remains optional debug visibility inside Home Assistant, not part of the supported operator path.
- The integration device page exposes native support actions, **Show support center**, **Show native diagnostics snapshot**, and **Show setup checklist**, so operators can surface troubleshooting state from normal Home Assistant device views or trigger the same actions from Scripts.
- Home Assistant **Repairs** now mirrors the most important setup/runtime blockers, which gives operators one more built-in native surface for triage without hunting through multiple entity sections first.

---

## 📚 Documentation

| Document | Description |
| :--- | :--- |
| [Supervisor](docs/SUPERVISOR.md) | Active steering layer: product state, gaps, release gates, and next actions |
| [Architecture](docs/ARCHITECTURE.md) | System design and component overview |
| [Control Loop](docs/CONTROL_LOOP.md) | How the optimization logic works |
| [Native Operator Plan](docs/NATIVE_OPERATOR_PLAN.md) | Current native-only operator direction |
| [Native Surface Technical Direction](docs/NATIVE_SURFACE_TECHNICAL_DIRECTION.md) | Supported HA surfaces and backend contract |
| [Dashboard Setup](docs/DASHBOARD_SETUP.md) | How to install the optional Lovelace debug dashboard inside Home Assistant |
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

The backend control engine is substantially built, and the project is now in a late **stabilization + native-surface consolidation** phase. The only supported operator path is native Home Assistant integration/device surfaces. There is no supported custom panel, sidebar app, or external UI path, and Lovelace remains optional debug visibility inside Home Assistant. The shipped experience is still transitional: managed devices still persist through inventory JSON under the hood, native diagnostics/support/repairs are better unified but still not fully complete, and the current real-world UI gap is operator clarity, making it obvious where to manage devices, where to set policy, and where to review health from the installed native surfaces.

The active steering layer now lives in [`docs/SUPERVISOR.md`](docs/SUPERVISOR.md). It is the source of truth for the current product state, gap register, release gates, and prioritized next actions.

**Current highest-value next step:** turn Configure into the clearly signposted native command center for sources, policy, managed devices, and support, then keep validating that flow in real Home Assistant installs and convert confirmed friction into targeted releases.

- [x] Config flow & source validation
- [x] Device model & guards
- [x] Guarded planner & executor
- [x] Diagnostics & action history
- [x] Dashboard scaffold
- [x] MIT license
- [ ] Stabilize install/runtime behavior in real Home Assistant environments
- [x] Reduce add-integration onboarding to a minimal bootstrap step so the native Configure flow is the intended setup surface
- [x] Keep source mapping, managed devices, and controller tuning available from native Home Assistant surfaces
- [x] Reduce normal managed-device onboarding JSON leakage by adding native add/edit/remove device flows while keeping JSON as an advanced recovery path
- [x] Publish native readiness guidance so operators can see the current setup phase, blockers, and highest-value next step from Home Assistant notifications and diagnostics
- [x] Publish a native support center and support snapshot so operators can copy a concise runtime/setup/release summary into Discord or issue reports during real-world validation
- [x] Remove the custom panel route and related launcher/frontend code from the shipped integration
- [ ] Real-world validation of the rebuilt operator flow
- [ ] Final install/runtime hardening based on real HA feedback

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
