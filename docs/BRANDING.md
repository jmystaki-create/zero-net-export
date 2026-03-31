# Branding

This project uses the repository asset below as its current primary brand image:

- `zero-net-export.png` — 1024×1024 square PNG

## Current Usage

The logo is currently used for:

- repository README branding
- release/readme visual identity
- future release assets and documentation

## Important Note About HACS / Home Assistant Icons

A logo file in the repository does **not automatically** become the icon shown in:

- the HACS integrations list
- the Home Assistant integration tile

Those surfaces typically rely on Home Assistant brand assets / branding infrastructure rather than a random repository image.

## Practical Branding Surfaces

### 1. GitHub repository page
Controlled by:
- `README.md`
- repository social preview / profile settings
- documentation assets

### 2. HACS custom repository tile
Usually controlled by:
- Home Assistant brand icon availability
- HACS rendering behavior for integration branding

### 3. Home Assistant integration UI
Usually controlled by:
- integration domain branding in the HA brand system

## What Has Been Prepared

- A square 1024×1024 PNG logo is present in the repository.
- README branding is already wired to use this logo.
- The repository now has release/changelog structure so branding can be kept consistent across releases.

## Next Step If Custom HACS / HA Tile Branding Is Required

If the goal is to make the logo appear in the HACS integration tile and Home Assistant integration surfaces, the next likely step is:

1. Prepare brand assets in the format expected by the Home Assistant brand pipeline.
2. Submit / align branding for the `zero_net_export` domain in the relevant branding path.

## Design Guidance

When updating the logo in the future:
- keep it square
- keep transparency if possible
- avoid tiny text inside the icon
- ensure it reads well at small sizes
- maintain a simple silhouette for the HACS / HA tile view
