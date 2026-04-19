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
- **Native Home Assistant setup path**: source mapping, managed-device configuration, and controller tuning live at **Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure**.
- **Configure is the intended command center**: the product direction is for operators to find sources, policy, managed devices, and support from one obvious native path.
- **Clear native section ownership is now a product goal**: Controls should hold the Zero Net Export brain, Sensors should hold mapped/system telemetry, Managed Devices should hold fleet operations, and Diagnostics should hold troubleshooting/support.
- **Native managed-device workspace**: day-to-day device onboarding and edit-in-place updates now have native add/remove/edit flows for fixed and variable devices, guided presets for common loads like hot water, pool pumps, EV chargers, and battery charge sinks, unmanaged-candidate discovery plus promotion review, and a fleet-review enable/disable step for staging larger installs without dropping into raw JSON.
- **Native Home Assistant operator surfaces**: Configure, the integration device at **Settings → Devices & Services → Integrations → Zero Net Export → Devices → open the Zero Net Export device**, entities, notifications, and Repairs are the supported operator path.
- **Native diagnostics actions**: device-page diagnostic buttons can raise a diagnostics guide, a setup checklist, and a detailed diagnostics snapshot as persistent notifications, and those button entities are callable from Scripts / Automations via `button.press`.
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
7.  If this is an upgrade or live fix, confirm the Zero Net Export entry comes back loaded and that previously saved source mappings still appear at **Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure**.
8.  If you need to prove the running Home Assistant package matches the intended repo build, run `python3 scripts/validate_install_fingerprint.py /path/to/your/config/custom_components` in this repo. It captures `tmp/expected-install-fingerprint.json`, compares the live install, saves `tmp/install-fingerprint-compare.json`, and exits non-zero on mismatch. You can point it at the Home Assistant config directory, the `custom_components` directory, or the installed `custom_components/zero_net_export` directory itself, as long as that install path is outside this repo. If the live Home Assistant shell does not expose `python3`, keep running the validator from this repo and add `--ssh-host <user@host>` plus `--ssh-port <port>` so the remote install path is inspected over SSH without remote Python. If you want the split steps for debugging, run `python3 scripts/print_expected_install_fingerprint.py --write-json tmp/expected-install-fingerprint.json`, then `python3 scripts/compare_install_fingerprint.py /path/to/your/config/custom_components --expected-json tmp/expected-install-fingerprint.json --write-json tmp/install-fingerprint-compare.json`. The compare helper refuses repo-local paths so a repo copy cannot be mistaken for live validation. The helper now keeps `expected_commit`, `expected_component_commit`, and `preferred_validation_commit` aligned on the latest component-changing commit, while exposing full repo HEAD separately as `repo_head_commit`, so doc-only or test-only repo commits do not create false deploy-candidate drift. Compare that component anchor and the tracked-file hashes with the installed package details shown in **Configure** or the device-page **Review diagnostics** / **Review diagnostics snapshot** actions.
9.  If you need one exact manual deploy from this repo before validation, first run `python3 scripts/deploy_exact_repo_build.py /path/to/your/config --dry-run` to preview the resolved destination, then rerun `python3 scripts/deploy_exact_repo_build.py /path/to/your/config` (or point either command at the live Home Assistant `custom_components` directory or the installed `custom_components/zero_net_export` directory outside this repo) when the target looks correct. It replaces the destination component directory instead of layering files onto an older copy, creates a timestamped backup by default, refuses to target this repo's own source component directory, and then runs `scripts/validate_install_fingerprint.py` against the deployed path before you restart Home Assistant. If you need to pin the deploy to the last component-changing commit instead of full repo HEAD, add `--expected-component-commit <commit>`.

### Option 2: Manual Installation

1.  Copy the `custom_components/zero_net_export` folder into your Home Assistant `/config/custom_components/` directory.
2.  **Restart Home Assistant**.
3.  If this is an upgrade or live fix, confirm the Zero Net Export entry comes back loaded and that previously saved source mappings still appear at **Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure**.
4.  If you need to prove the copied package is the intended build, run `python3 scripts/validate_install_fingerprint.py /path/to/your/config/custom_components` in this repo. It captures `tmp/expected-install-fingerprint.json`, compares the live install, saves `tmp/install-fingerprint-compare.json`, and exits non-zero on mismatch. You can point it at the Home Assistant config directory, the `custom_components` directory, or the installed `custom_components/zero_net_export` directory itself, as long as that install path is outside this repo. If the live Home Assistant shell does not expose `python3`, keep running the validator from this repo and add `--ssh-host <user@host>` plus `--ssh-port <port>` so the remote install path is inspected over SSH without remote Python. If you want the split steps for debugging, run `python3 scripts/print_expected_install_fingerprint.py --write-json tmp/expected-install-fingerprint.json`, then `python3 scripts/compare_install_fingerprint.py /path/to/your/config/custom_components --expected-json tmp/expected-install-fingerprint.json --write-json tmp/install-fingerprint-compare.json`. The compare helper refuses repo-local paths so a repo copy cannot be mistaken for live validation. The helper now keeps `expected_commit`, `expected_component_commit`, and `preferred_validation_commit` aligned on the latest component-changing commit, while exposing full repo HEAD separately as `repo_head_commit`, so doc-only or test-only repo commits do not create false candidate drift. Compare that component anchor and the tracked-file hashes with the installed package details shown in **Configure** or the device-page **Review diagnostics** / **Review diagnostics snapshot** actions.
5.  To replace a mixed manual install with one exact repo build, first run `python3 scripts/deploy_exact_repo_build.py /path/to/your/config --dry-run` to preview the resolved destination, then rerun `python3 scripts/deploy_exact_repo_build.py /path/to/your/config` before restart. It removes the old `custom_components/zero_net_export` directory at the destination, copies this repo's component directory into place, keeps a timestamped backup by default, refuses to target this repo's own source component directory, and runs the install fingerprint validation helper against the deployed path. If you need to pin the deploy target while repo-only docs keep moving, pass `--expected-component-commit <commit>`.
6.  Go to **Settings** → **Devices & Services** → **Add Integration**.
6.  Search for **Zero Net Export**.

---

## ⚙️ Configuration

### Primary operator path: Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure

1.  Add the **Zero Net Export** integration.
2.  Complete the **minimal bootstrap config flow** by giving the system a clear name.
3.  Open **Settings** -> **Devices & Services** -> **Integrations** -> **Zero Net Export** -> **Configure**.
4.  Use **Sources and source mapping** to map your source entities:
    - Solar Power
    - Grid sensors, either as one combined/net pair or as separate import/export entities
    - Home Load Power (optional if solar and grid sources are already mapped)
    - (Optional) Battery Entities
5.  Use **Managed devices** in Configure as the main device workspace: add fixed or variable controllable devices, review unmanaged candidates, promote the best-fit candidate into the managed fleet, then edit, enable or disable, and remove devices from that same native path. Use the fleet review there to stage larger installs. Use the JSON editor only for bulk structural edits or recovery.
6.  Treat **Managed devices** as the home for per-device enablement, priority, overrides, promotion, and deeper fleet review, rather than mixing those concerns into the controller brain surface.
7.  Use **Policy and controller settings** in Configure for target/deadband/reserve defaults and related control behavior once sources and managed devices are in place.
8.  Use **Diagnostics** in Configure for the next native triage step when runtime is blocked or unclear.
8.  For deeper verification, use the integration device at **Settings → Devices & Services → Integrations → Zero Net Export → Devices → open the Zero Net Export device**, then its buttons, entities, diagnostics, and **Repairs** after Configure points you to the next blocker.

### Advanced / fallback paths

- The initial add-integration flow remains bootstrap-only, and the normal post-install path is **Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure**.
- Managed devices are still persisted internally as structured inventory JSON, but **Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure** now hides most of that behind add/edit/remove forms for fixed and variable devices.
- The integration device at **Settings → Devices & Services → Integrations → Zero Net Export → Devices → open the Zero Net Export device** exposes native diagnostics actions, **Review diagnostics**, **Review diagnostics snapshot**, and **Show setup checklist**, so operators can surface troubleshooting state from normal Home Assistant device views or trigger the same actions from Scripts.
- Home Assistant **Repairs** now mirrors the most important setup/runtime blockers, which gives operators one more built-in native surface for triage without hunting through multiple entity sections first.

---

## 📚 Documentation

### Project control files

| File | Role |
| :--- | :--- |
| [project_status.md](project_status.md) | Current execution state for the project: status, next action, blocker, user action, notes, and last modified timestamp |
| [docs/SUPERVISOR.md](docs/SUPERVISOR.md) | Active project steering guide and source of truth for current direction, goals, risks, and next actions |
| `WATCHDOG.md` (workspace root) | Central audit guide used by watchdog-style runs to detect drift, stale state, and small safe corrective fixes |
| [RELEASE_MANAGEMENT.md](RELEASE_MANAGEMENT.md) | Operational release workflow, including GitHub visibility, HACS refresh, Home Assistant restart, and post-release log review |

### Reference and design documents

| Document | Description |
| :--- | :--- |
| [Architecture](docs/ARCHITECTURE.md) | System design and component overview |
| [Control Loop](docs/CONTROL_LOOP.md) | How the optimization logic works |
| [UI Design](docs/UI_DESIGN.md) | Single source of truth for the intended native Home Assistant UI design |
| [UI Implementation Map](docs/UI_IMPLEMENTATION_MAP.md) | Single source of truth for UI implementation status, completed work, remaining work, and delivery phases |
| [Bug Tracker](docs/BUGS.md) | Single source of truth for active bugs, regressions, validation state, and closure state |
| [Native Operator Plan](docs/NATIVE_OPERATOR_PLAN.md) | Historical native-only operator direction background |
| [Native Surface Technical Direction](docs/NATIVE_SURFACE_TECHNICAL_DIRECTION.md) | Historical technical-direction background |
| [Dashboard Setup](docs/DASHBOARD_SETUP.md) | How to install the optional Lovelace debug dashboard inside Home Assistant |
| [Entity Model](docs/ENTITY_MODEL.md) | List of all created entities |
| [Product Spec](docs/PRODUCT_SPEC_V1.md) | Full product requirements and goals |
| [Validation Checklist](docs/VALIDATION_CHECKLIST.md) | Real-installation sign-off checklist |
| [Release Process](docs/RELEASE_PROCESS.md) | Package and release sequence reference |
| `scripts/print_expected_install_fingerprint.py` | Prints the repo's expected tracked-file hashes plus the latest component-changing validation anchor (`expected_commit`, `expected_component_commit`, `preferred_validation_commit`) and the separate full repo HEAD (`repo_head_commit`) for comparing a live Home Assistant install against the intended build, and can optionally save that JSON snapshot for later use |
| `scripts/compare_install_fingerprint.py` | Compares the repo fingerprint, or a previously captured expected fingerprint JSON, against a chosen Home Assistant config, `custom_components`, or `zero_net_export` install path, reports manifest/file mismatch details, fails fast if the path does not actually contain the component, can save the comparison payload, and exits non-zero when the live files do not match |
| `scripts/validate_install_fingerprint.py` | One-command wrapper that captures the expected repo fingerprint, compares the live install path, saves both JSON artifacts, and exits non-zero when the live files do not match |
| `scripts/deploy_exact_repo_build.py` | Replaces one target `custom_components/zero_net_export` install path with this repo's exact component directory, can pin either repo HEAD or the latest component-changing commit before deploy, keeps a timestamped backup by default, and runs the fingerprint validator before restart |
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

The backend control engine is substantially built, and the project is now in a late **stabilization + native-surface consolidation** phase. The supported operator path remains centered on native Home Assistant surfaces: **Configure** plus `Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device`, with no supported custom panel, sidebar app, or external web UI path. The shipped experience is still transitional: managed devices still persist through inventory JSON under the hood, native Diagnostics, checklist, and Repairs surfaces are better unified but still not fully complete, and the current real-world UI gap is operator clarity, especially making it obvious what belongs under Controls, Sensors, Managed Devices, and Diagnostics from the installed native surfaces. The current live correction line remains **0.1.86**, and the next UI rollout target is **0.1.87**. Do not drift back to stale **0.1.83** or **0.1.85** wording, and do not treat **0.1.86** as the future UI target now that [`docs/UI_IMPLEMENTATION_MAP.md`](docs/UI_IMPLEMENTATION_MAP.md) defines **0.1.87** as the rollout checklist.

The active steering layer now lives in [`docs/SUPERVISOR.md`](docs/SUPERVISOR.md). For UI work, the intended design now lives in [`docs/UI_DESIGN.md`](docs/UI_DESIGN.md), and the implementation status / phase plan now lives in [`docs/UI_IMPLEMENTATION_MAP.md`](docs/UI_IMPLEMENTATION_MAP.md). Those two files are the UI source of truth.

**Current highest-value next step:** treat the current repo-side **0.1.87** UI shaping as materially complete enough that the main unresolved boundary is now explicit deploy/restart approval for exact build `481c9a7`, not another default round of repo-side workstream hunting. If a fresh repo-side drift appears, fix that first. Otherwise ask James directly for approval when presenting the current candidate as release-ready, then use the documented HA SSH path to validate the exact deployed build instead of repeating unchanged fingerprint or anchor bookkeeping.

- [x] Config flow & source validation
- [x] Device model & guards
- [x] Guarded planner & executor
- [x] Diagnostics & action history
- [x] Dashboard scaffold
- [x] MIT license
- [ ] Stabilize install/runtime behavior in real Home Assistant environments
- [x] Reduce add-integration onboarding to a minimal bootstrap step so `Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure` is the intended setup surface
- [x] Keep source mapping, managed devices, and controller tuning available from native Home Assistant surfaces
- [x] Reduce normal managed-device onboarding JSON leakage by adding native add/edit/remove device flows while keeping JSON as an advanced recovery path
- [x] Publish native readiness guidance so operators can see the current setup phase, blockers, and highest-value next step from Home Assistant notifications and diagnostics
- [x] Publish native diagnostics guide and diagnostics snapshot actions so operators can copy a concise runtime/setup/release summary into Discord or issue reports during real-world validation
- [x] Remove the custom panel route and related launcher/frontend code from the shipped integration
- [ ] Real-world validation of the rebuilt operator flow
- [ ] Final install/runtime hardening based on real HA feedback

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
