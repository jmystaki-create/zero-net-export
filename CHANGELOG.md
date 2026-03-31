# Changelog

All notable changes to **Zero Net Export** will be documented in this file.

This project follows a practical Keep a Changelog style and uses semantic versioning for tagged releases where possible.

## [Unreleased]

### Added
- Placeholder panel shell follow-up work remains focused on guided source setup, guided device management, and operator mutations inside the app.

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
