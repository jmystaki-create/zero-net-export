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

The likely implementation direction is to expose managed loads and unmanaged candidates as real Home Assistant device-registry devices associated with the Zero Net Export config entry, so Home Assistant renders them under the integration detail page's Devices area.

The design must target the integration detail page device list, not arbitrary custom cards. If Home Assistant cannot render two literal custom group headings for devices from one integration, the project must report that as a hard platform constraint before implementation and propose the closest native representation, instead of substituting renamed entities/buttons.

## Acceptance criteria

`0.1.91` can be called successful only when live Home Assistant screenshot evidence shows:

1. The Zero Net Export main integration page is open.
2. A visible **Managed Devices** group/list appears under Zero Net Export.
3. Managed devices appear as individual device rows inside that list.
4. A visible **Un Managed** group/list appears below it.
5. Unmanaged candidate devices appear as individual device rows inside that list.
6. The evidence is from the live installed build, not repo assumptions or API-only state.

## Required documentation/validation state

Before implementation resumes, all source-of-truth docs must agree that `0.1.91` is the active target and that its scope is limited to the integration-main-page managed/unmanaged device lists described above.

Before release/deploy, update version/release files only after the implementation exists and only within this approved scope.
