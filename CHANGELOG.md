# Changelog

All notable changes to **Zero Net Export** will be documented in this file.

This project follows a practical Keep a Changelog style and uses semantic versioning for tagged releases where possible.

## [Unreleased]

### Added
- Real Home Assistant validation of the rebuilt panel workflow remains the highest-value next step.

## [0.1.9] - 2026-04-02

### Fixed
- Fixed the panel shell bootstrap lifecycle so the frontend now loads state correctly even when the custom element connects before Home Assistant injects `hass`, avoiding a permanent loading screen in real installs.

### Changed
- Integration version advanced to `0.1.9` for the panel bootstrap/runtime stability fix.

## [0.1.8] - 2026-04-02

### Fixed
- Fixed a panel backend runtime regression where the Settings payload referenced controller default constants that were not imported, which could break `zero_net_export/panel/get_state` and prevent the panel app from loading cleanly.

### Changed
- Integration version advanced to `0.1.8` for the panel runtime stability fix.

## [0.1.7] - 2026-04-02

### Added
- Added a real panel Settings payload with controller defaults, fleet health summary, panel-first workflow guidance, and direct documentation/release/support links.
- Expanded the Settings tab into an operator-facing release/support view instead of leaving it as a near-duplicate of runtime controls.

### Changed
- Panel schema advanced to `6` so the frontend can consume structured settings/release metadata.
- Integration version advanced to `0.1.7` for the first panel settings/release-management milestone.

## [0.1.6] - 2026-04-01

### Added
- Expanded the panel diagnostics payload with action history, source diagnostics, calibration hints, and per-device explanation data already available in the backend coordinator.
- Added an in-panel diagnostics view for recent action timeline, mapped-source health, and per-device planned-action/guard/result inspection.

### Changed
- Panel schema advanced to `5` so the frontend can consume richer diagnostics and explanation state.
- Integration version advanced to `0.1.6` for the first operator-grade diagnostics/explanation panel milestone.

## [0.1.5] - 2026-04-01

### Added
- Added explicit panel websocket mutations for `add_device` and `delete_device` so the sidebar app can manage the controllable device inventory directly.
- Added device-editor bootstrap payloads with configured device models, adapter choices, and Home Assistant entity suggestions for fixed and variable device templates.
- Added an in-panel device editor that supports add/edit/remove workflows for normal fixed and variable device onboarding.

### Changed
- Panel schema advanced to `4` and the Devices tab now treats structured device management as the primary operator path instead of deferring to raw JSON.
- Device inventory saves now validate through the existing backend parser before persisting updated options and reloading the integration.
- Integration version advanced to `0.1.5` for the first panel-side device management milestone.

## [0.1.4] - 2026-04-01

### Added
- Added panel source-mapping save support so operators can update the integration's mapped Home Assistant sensors directly from the sidebar app.
- Added source-mapping form inputs with sensor suggestions and refresh-interval editing in the Setup tab.

### Changed
- Panel schema advanced to `3` and Setup is now read/write for source mapping rather than diagnostics-only.
- Panel/backend flow now validates proposed source mappings before persisting them and reloads the config entry after a successful save.
- Integration version advanced to `0.1.4` for the first guided source-setup milestone.

## [0.1.3] - 2026-04-01

### Added
- Added panel websocket mutations for controller runtime settings and per-device operator overrides so the app can now perform common operator actions instead of staying read-only.
- Added in-panel controller controls for enable/disable, mode, target export, deadband, battery reserve, and reset-to-defaults.
- Added in-panel device controls for runtime enable/disable, priority override, and per-device override reset.

### Changed
- Panel schema advanced to `2` and the frontend now reflects saving/busy state during operator mutations.
- Panel docs now describe the current shell as read/write for runtime control while guided source and full device onboarding remain next.
- Integration version advanced to `0.1.3` for the first operator-mutation panel milestone.

## [0.1.2] - 2026-04-01

### Added
- Registered a real Home Assistant sidebar panel for Zero Net Export instead of leaving the app-first path as docs-only planning.
- Added a frontend panel bundle with tabbed shell sections for Overview, Setup, Devices, Diagnostics, and Settings.
- Added a normalized websocket payload at `zero_net_export/panel/get_state` so the panel can read structured overview, setup, device, and diagnostics state from the existing backend coordinator.

### Changed
- Integration startup now ensures the panel shell is registered alongside the existing backend coordinator/platform setup.
- README and implementation docs now reflect that the first panel shell milestone has been delivered.
- Integration version advanced to `0.1.2` for the panel-shell milestone.

### Fixed
- Removed the custom `icon` field from `manifest.json` as a likely contributor to wider Home Assistant UI/icon breakage during install.

## [0.1.1] - 2026-03-31

### Added
- `docs/PANEL_APP_REBUILD_PLAN.md` defining the app-first rebuild strategy.
- `docs/PANEL_APP_TECHNICAL_DESIGN.md` defining app sections, backend contract, and phased panel delivery.
- New project goals and implementation direction focused on a panel-style operator experience.
- A 4-hour supervision direction for finishing the project against the new app-first goals.
- Comprehensive UI goals covering setup, device management, operation, and diagnostics.
- Explicit architectural decision: panel app is now the chosen product path.

### Changed
- Design direction now explicitly rejects the original poor device configuration UX as a long-term operator workflow.
- Product documentation now treats the YAML dashboard as a transitional surface rather than the long-term primary UX.
- Implementation planning now includes stabilization plus panel-app rebuild phases.
- Integration version advanced toward `0.1.1` for stabilization work.

## [0.1.0] - 2026-03-31

### Added
- Release management structure for ongoing versioned maintenance.
- `CHANGELOG.md` to track user-visible changes by release.
- `docs/RELEASE_PROCESS.md` describing the release workflow.

### Added
- Initial Home Assistant custom integration scaffold for Zero Net Export.
- Config flow with source-of-truth validation.
- Device model for fixed and variable controllable loads.
- Guarded planner and executor for export-target control.
- Runtime safety controls including deadband, cooldown, min on/off, and battery reserve policy.
- Runtime-cap preemption support for managed devices.
- Diagnostics export, per-source diagnostics, action history, and daily reporting metrics.
- Lovelace dashboard scaffold and project documentation set.
- HACS metadata and MIT license.

### Notes
- `0.1.0` is the intended first public baseline, but it should only be treated as formally released once a matching git tag / GitHub release is created.
