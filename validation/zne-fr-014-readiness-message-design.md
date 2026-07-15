# ZNE-FR-014 Readiness Message Design Validation

Date: 2026-07-08
Status: released_live_validated_v0.4.5

## Request

Riley reported that the Overview Readiness design/messages are still very poor
and hard to understand. The screenshot showed dense command-center and next-step
strings rendered as narrow label/value rows.

## Feasibility Check

Target environment: Zero Net Export's Home Assistant custom panel frontend,
served by the integration as `zero-net-export-app.js`.

Result: supported.

Evidence:
- The Readiness section is fully owned by the ZNE custom panel frontend.
- Existing data comes from `hass.states`, including command-center status,
  command-center next step, source blocker summary, stale source summary, and
  control guard summary.
- The change requires only JS/CSS rendering changes and tests.

Unsupported/excluded:
- No Home Assistant core/frontend patch.
- No native Home Assistant page injection.
- No direct write to the live Home Assistant install.
- No new recorder-backed attributes.

## Implementation

- Added a summary verdict to the Readiness card.
- Renamed the focus block to `Do this first`.
- Converted dense command-center/device queue strings into concise facts.
- Changed issue cards to bullet-style `What is wrong` and ordered `How to
  resolve` content.
- Preserved the existing source, reconciliation, controls, and managed-device
  issue coverage.

## Repo Validation

Passed:
- `node --check custom_components/zero_net_export/frontend/zero-net-export-app.js`
- `python3 -m unittest tests.test_managed_devices_panel -v` - 19 tests OK
- `python3 -m unittest tests.test_operator_docs_consistency tests.test_release_info_install_guidance -v` - 46 tests OK
- `python3 -m unittest discover -s tests -v` - 630 tests OK
- `git diff --check`

## Release Validation

Released in `v0.4.4`; Readiness behavior was live validated during corrective
release `v0.4.5`.

Evidence: `validation/0.4.5-release-validation.md` records GitHub release,
HACS install, Home Assistant restart/recovery, installed package fingerprint,
installed version sensor `0.4.5`, and browser proof that the Overview Readiness
summary showed `Ready` with no blocking readiness issue.
