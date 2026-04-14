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
| **Configure the integration** | Install the integration, restart Home Assistant, verify the entry loads cleanly, then open **Settings → Devices & Services → Integrations → Zero Net Export → Configure** |
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
- **Native managed-device workspace**: day-to-day device onboarding and edit-in-place updates now have native add/remove/edit flows for fixed and variable devices, guided presets for common loads like hot water, pool pumps, EV chargers, and battery charge sinks, unmanaged-candidate discovery plus promotion review, and a fleet-review enable/disable step for staging larger installs without dropping into raw JSON.
- **Native Home Assistant operator surfaces**: Configure, the integration device at **Settings → Devices & Services → Integrations → Zero Net Export → Devices → open the Zero Net Export device**, entities, notifications, and Repairs are the supported operator path.
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
7.  If this is an upgrade or live fix, confirm the Zero Net Export entry comes back loaded and that previously saved source mappings still appear in **Configure**.

### Option 2: Manual Installation

For manual installs or live repair work, prefer the exact deploy helper from this repo so the copied Home Assistant package can be compared against the intended local build before restart.

1.  From this repo, preview the resolved target first:
    ```bash
    python3 scripts/deploy_exact_repo_build.py /path/to/home-assistant/config --dry-run --expected-commit <intended_commit> --require-clean --require-upstream-sync
    ```
    Confirm the preview shows `repo_deploy_requirements_passed=true`, `copy_ready=true`, the intended `git_commit`, `git_upstream_commit`, `git_local_vs_upstream=in_sync`, `git_working_tree_dirty=false`, and `git_working_tree_changes=none`. If the preview stops on `git_local_vs_upstream=ahead`, `behind`, `diverged`, or `no_upstream`, follow the printed `remediation_command` first, then rerun the dry-run command.
2.  If the resolved destination is correct, deploy the exact repo build:
    ```bash
    python3 scripts/deploy_exact_repo_build.py /path/to/home-assistant/config --expected-commit <intended_commit> --require-clean --require-upstream-sync
    ```
3.  Confirm the deploy helper reports `post_copy_validation=passed` and `restart_ready=true`, then confirm the installed package matches the current repo fingerprint:
    ```bash
    python3 scripts/validate_install_fingerprint.py /path/to/home-assistant/config/custom_components
    ```
    The deploy helper now also prints the post-restart checklist, which points operators back to **Configure -> Sensors and source mapping** before trusting live control.
4.  If you only know the install root indirectly, you can also point the deploy helper at `/path/to/home-assistant/config/custom_components`, the full installed `.../custom_components/zero_net_export` path, or use discovery first. The discovery mode checks common Home Assistant env vars plus typical container, Home Assistant OS / Supervised, and bare-metal config paths:
    ```bash
    python3 scripts/deploy_exact_repo_build.py --discover-home-assistant-config
    ```
5.  **Restart Home Assistant**.
6.  If this is an upgrade or live fix, confirm the existing Zero Net Export entry comes back loaded, reopen **Configure -> Sensors and source mapping**, and confirm the previously saved source mappings still appear there before trusting live runtime results.
7.  If this is a fresh manual install with no existing entry yet, go to **Settings** → **Devices & Services** → **Add Integration**, then search for **Zero Net Export**.

---

## ⚙️ Configuration

### Primary operator path: native Home Assistant Configure flow

1.  Add the **Zero Net Export** integration.
2.  Complete the **minimal bootstrap config flow** by giving the system a clear name.
3.  Open **Settings** -> **Devices & Services** -> **Integrations** -> **Zero Net Export** -> **Configure**.
4.  Use **Sensors and source mapping** to map your source entities and review source health:
    - Solar Power
    - Grid sensors, either as one combined/net pair or as separate import/export entities
    - Home Load Power (optional if solar and grid sources are already mapped)
    - (Optional) Battery Entities
5.  Use **Managed devices** in Configure as the main device workspace: add fixed or variable controllable devices, review unmanaged candidates, promote the best-fit candidate into the managed fleet, then edit, enable or disable, and remove devices from that same native path. Use the fleet review there to stage larger installs. Use the JSON editor only for bulk structural edits or recovery.
6.  Use **Controls** in Configure for target/deadband/reserve defaults and related control behavior once **Sensors and source mapping** and **Managed devices** are in place.
7.  Use **Diagnostics** in Configure for the next native triage step when runtime is blocked or unclear.
8.  For deeper verification, use the integration device at **Settings → Devices & Services → Integrations → Zero Net Export → Devices → open the Zero Net Export device**, then its buttons, entities, diagnostics, and **Repairs** after Configure points you to the next blocker.

### Advanced / fallback paths

- The initial add-integration flow remains bootstrap-only, and the normal post-install path is the native Configure flow.
- Managed devices are still persisted internally as structured inventory JSON, but the primary native Configure flow now hides most of that behind add/edit/remove forms for fixed and variable devices.
- The Lovelace YAML dashboard remains optional debug visibility inside Home Assistant, not part of the supported operator path.
- The integration device at **Settings → Devices & Services → Integrations → Zero Net Export → Devices → open the Zero Net Export device** exposes native support actions, **Show support center**, **Show native diagnostics snapshot**, and **Show setup checklist**, so operators can surface troubleshooting state from normal Home Assistant device views or trigger the same actions from Scripts.
- Home Assistant **Repairs** now mirrors the most important setup/runtime blockers, which gives operators one more built-in native surface for triage without hunting through multiple entity sections first.

---

## 📚 Documentation

### Project control files

| File | Role |
| :--- | :--- |
| [project_status.md](project_status.md) | Current execution state for the project: status, next action, blocker, user action, notes, and last modified timestamp |
| [docs/SUPERVISOR.md](docs/SUPERVISOR.md) | Active project steering guide and source of truth for current direction, goals, risks, and next actions |
| [TOOLS.md](TOOLS.md) | Preferred live-evidence access paths for Home Assistant UI, APIs, logs, host inspection, and exact-build helper scripts before escalating to the user |
| `WATCHDOG.md` (workspace root) | Central audit guide used by watchdog-style runs to detect drift, stale state, and small safe corrective fixes |
| [RELEASE_MANAGEMENT.md](RELEASE_MANAGEMENT.md) | Operational release workflow, including GitHub visibility, HACS refresh, Home Assistant restart, and post-release log review |

### Reference and design documents

| Document | Description |
| :--- | :--- |
| [Architecture](docs/ARCHITECTURE.md) | System design and component overview |
| [Control Loop](docs/CONTROL_LOOP.md) | How the optimization logic works |
| [Native Operator Plan](docs/NATIVE_OPERATOR_PLAN.md) | Current native-only operator direction |
| [Native Surface Technical Direction](docs/NATIVE_SURFACE_TECHNICAL_DIRECTION.md) | Supported HA surfaces and backend contract |
| [Dashboard Setup](docs/DASHBOARD_SETUP.md) | How to install the optional Lovelace debug dashboard inside Home Assistant |
| [Entity Model](docs/ENTITY_MODEL.md) | List of all created entities |
| [Product Spec](docs/PRODUCT_SPEC_V1.md) | Full product requirements and goals |
| [Validation Checklist](docs/VALIDATION_CHECKLIST.md) | Real-installation sign-off checklist |
| [Release Process](docs/RELEASE_PROCESS.md) | Package and release sequence reference |
| [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) | Current implementation trail and work decomposition |
| [Operator Surfaces UX](docs/OPERATOR_SURFACES_UX.md) | Operator-facing flow and UX framing |
| [Reference Matrix](docs/REFERENCE_MATRIX.md) | Cross-reference of implementation/documentation intent |
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

**Current highest-value next step:** push the intended deploy-helper commit to the tracked remote branch, then from the real Home Assistant host or container run the exact deploy-helper discovery, dry-run, deploy, fingerprint validation, and restart sequence against that synchronized build before continuing live validation.

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
