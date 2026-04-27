# Zero Net Export 0.1.91 Release Plan

`0.1.91` is the integration-main-page Managed Devices release.

This is the only approved scope for the next release line: make the Zero Net Export **main integration page** show real managed and unmanaged device lists under the Zero Net Export integration, matching the Home Assistant integration-page pattern shown by James.

Do not treat the `0.1.90` device-info-page entity/control work as satisfying this requirement. It does not.

## User-visible requirement

On `Settings -> Devices & Services -> Integrations -> Zero Net Export`, the integration detail page must show device groups like the HomeKit examples James supplied:

1. **Managed Devices**
   - A collapsible/grouped device list under Zero Net Export.
   - Each managed load appears as its own Home Assistant device row.
   - Rows should use the managed device name, device/model/type summary, and entity count naturally provided by Home Assistant.

2. **Un Managed**
   - A second collapsible/grouped device list below Managed Devices.
   - Each unmanaged candidate appears as its own Home Assistant device row.
   - Rows should make candidate devices visible before they are promoted.

The spelling James used was `Un Managed`; keep that label visible in planning/acceptance unless the final Home Assistant implementation proves HA requires a different exact display string. If the product label is normalized later, document that decision explicitly before implementation.

## Explicit non-goals

Do not use `0.1.91` for:

- more button renames
- more Activity-history wording
- more device-info-page Controls rows
- another Configure-only explanation
- release/deploy bookkeeping
- unrelated UI polish
- source-role, diagnostics, or control-loop work unless it is strictly required to expose the requested device lists

## What does not count

The following do **not** satisfy `0.1.91`:

- `Managed Devices overview` sensor rows on the Zero Net Export device page
- `Open Managed Devices workspace` buttons
- persistent notifications opened after pressing a button
- Configure flow screens alone
- API/entity-registry proof without the main integration page showing the requested lists
- screenshots of the individual Zero Net Export device info page

## Technical direction

The repo candidate exposes managed loads and unmanaged candidates as child Home Assistant devices associated with the Zero Net Export config entry through native entity device-info metadata, so Home Assistant can render them under the integration detail page's Devices area.

Home Assistant's native device APIs can create the integration-page device rows, but they do not expose a custom API for arbitrary literal nested headings inside one integration. The closest native representation now implemented in repo is one device row per load/candidate, with row names/models carrying the group language: `Managed Devices — ...` and `Un Managed — ...`. This must be accepted as the native constraint before release; do not substitute sensors/buttons/custom UI for this outcome.

## Acceptance criteria

`0.1.91` can be called successful only when live Home Assistant screenshot evidence shows the accepted native representation on the main integration page. If James rejects the closest native child-device representation because literal collapsible headings are required, do not release this candidate as successful. If James accepts the native constraint, visible `Managed Devices — ...` and `Un Managed — ...` device row/model grouping language is the acceptance target instead of silent substitution by sensors/buttons/custom UI.

1. The Zero Net Export main integration page is open.
2. A visible **Managed Devices** group/list or accepted native `Managed Devices — ...` row/model grouping appears under Zero Net Export.
3. Managed devices appear as individual device rows inside that list/grouping.
4. A visible **Un Managed** group/list or accepted native `Un Managed — ...` row/model grouping appears below it.
5. Unmanaged candidate devices appear as individual device rows inside that list/grouping.
6. The evidence is from the live installed build, not repo assumptions or API-only state.

## Required documentation/validation state

The repo implementation exists inside the approved scope, but component code changed after the historical `v0.1.91` tag at `7217f3b`; the helper-resolved exact `0.1.91` component boundary is now `c4802a3`. Do not treat the old tag or the post-tag helper boundary as Home Assistant deploy approval. Ask James directly to accept the closest native entity/device-info representation and approve the exact `c4802a3` release/deploy/restart path before any Home Assistant install/restart or success claim.
