# UI implementation map for native IA split

Branch: `ui-surface-correction-2026-04-12`

Purpose: tighten the native Home Assistant information architecture around **Controls**, **Sensors**, **Managed Devices**, **Diagnostics**, plus a deeper **Detailed Management** path, without adding a custom panel or doing release work.

## Highest-priority repo files to change next

### 1. `custom_components/zero_net_export/config_flow.py`
**Why next:** this is already the real command center. It owns the Configure menu labels, section descriptions, action sequencing, and most of the user-facing IA.

**Change next:**
- Rename and rebalance the top-level Configure sections so they match the target IA exactly.
- Keep **Controls** controller-only.
- Keep **Sensors** source mapping + source-health only.
- Keep **Managed Devices** onboarding, promotion, enablement, priority, overrides, edit/remove.
- Keep **Diagnostics** for troubleshooting and support only.
- Add or expose a clearer **Detailed Management** handoff from Managed Devices, rather than leaving deeper fleet review buried in generic forms.
- Reduce current cross-talk where policy/support/source context is repeated across multiple sections.

### 2. `custom_components/zero_net_export/native_support.py`
**Why next:** this file is the shared IA brain for paths, command-center summaries, readiness wording, repair steps, and support snapshot content.

**Change next:**
- Replace current path naming with the final IA vocabulary.
- Update `build_native_command_center_summary()` so recommended-section logic points to **Controls / Sensors / Managed Devices / Diagnostics** cleanly.
- Make status summaries section-specific instead of broad mixed summaries.
- Add a dedicated helper for **Detailed Management** handoff text and native device-view routing.
- Keep support/checklist output aligned with the new section ownership.

### 3. `custom_components/zero_net_export/strings.json`
**Why next:** this defines the actual Home Assistant Configure copy and option-step labels users see.

**Change next:**
- Rename menu options and step titles to the new IA.
- Rewrite descriptions so each section has one job.
- Make the command-center intro explain the five-part structure in plain operator language.
- Add explicit wording that **Detailed Management** is the deeper fleet/device-detail path.

### 4. `custom_components/zero_net_export/translations/en.json`
**Why next:** it must stay in lockstep with `strings.json` for the shipped native UX.

**Change next:**
- Mirror every IA rename and description update from `strings.json`.
- Keep terminology consistent: do not mix “policy”, “support”, “source mapping”, and “fleet review” across the wrong sections.

### 5. `custom_components/zero_net_export/sensor.py`
**Why next:** entity naming currently mixes controller, fleet, candidate, blocker, and command-center concerns together. This is the main place to make the entity model reflect the new IA.

**Change next:**
- Re-group or rename helper summary sensors around the new buckets.
- Keep controller summaries under **Controls** semantics.
- Keep mapped source health under **Sensors** semantics.
- Keep fleet/candidate/promotion summaries under **Managed Devices** semantics.
- Keep blocker/repair/command-center guidance under **Diagnostics** semantics.
- Add stronger per-device detail surfacing to support **Detailed Management** from the native device view.

### 6. `custom_components/zero_net_export/button.py`
**Why next:** buttons are the current native handoff points from the integration device page.

**Change next:**
- Rename button copy so it matches the new IA, especially command-center and support wording.
- Add or repurpose one button as the **Detailed Management** handoff if Home Assistant’s native device flow needs a stronger entry point.
- Keep command-center, support center, diagnostics snapshot, and setup checklist clearly separated.

### 7. `custom_components/zero_net_export/repairs.py`
**Why next:** Repairs is part of the intended Diagnostics surface, so issue text needs to reinforce the same IA.

**Change next:**
- Point setup/runtime repair text to **Sensors**, **Managed Devices**, or **Diagnostics** explicitly.
- Avoid sending users back to a vague “configure” concept when the precise section is known.
- Keep fallback guidance attached only to the relevant source-mapping path.

## Supporting files to update after the code-facing IA pass

### 8. `custom_components/zero_net_export/entity.py`
**Why next:** if the deeper device path becomes a stronger concept, this base device metadata may need minor adjustments so entities feel coherent under the integration device.

### 9. `docs/OPERATOR_SURFACES_UX.md`
**Why next:** this is already the clearest intent doc for the five-way split.

**Change next:**
- Convert it from target-state narrative into a checked implementation guide tied to the real Configure/device surfaces.

### 10. `docs/NATIVE_SURFACE_TECHNICAL_DIRECTION.md`
**Why next:** it defines the supported native-only contract.

**Change next:**
- Update supported-surface wording to reflect the final section names and the Detailed Management handoff.

### 11. `docs/SUPERVISOR.md`
**Why next:** this is the active steering layer.

**Change next:**
- Replace the current broad UI goal with the concrete next implementation sequence above.

### 12. `README.md`
**Why next:** it already states the intended split, but the operator-path section still uses some transitional labels.

**Change next:**
- Align the public operator-path explanation with the final Configure section names and the native device-detail handoff.

### 13. `tmp/command-center-preview.html` and `tmp/command-center-preview.svg`
**Why next:** they still show the older section labels.

**Change next:**
- Update the preview to show the final IA labels and the new Detailed Management entry point.
- Use only as preview collateral after the real strings/logic are settled.

## Recommended implementation order

1. `native_support.py`
2. `config_flow.py`
3. `strings.json`
4. `translations/en.json`
5. `sensor.py`
6. `button.py`
7. `repairs.py`
8. docs and preview assets

## Notes

- An existing UI branch already existed, so I switched to `ui-surface-correction-2026-04-12`.
- A local `project_status.md` change from `main` conflicted because that file is deleted on the UI branch. I preserved the working-tree copy locally and kept it out of git index changes.
- No release work performed.
