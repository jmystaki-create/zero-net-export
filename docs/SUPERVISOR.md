# Supervisor

This is the active steering layer for Zero Net Export.

Use this document to decide what the project should do next, what is currently blocking release confidence, and what must be true before calling the native-HA-only operator experience ready.

Supporting detail lives in the spec, implementation, validation, and release docs. This file is the place that turns those into a current operating stance.

## Product state summary

### Current release-line position

Zero Net Export has now crossed an important line in the user's real Home Assistant instance: the integration loads, native entities are present again, and the product is no longer blocked primarily by startup crashes. The project is still in **late stabilization and native-surface consolidation**, but the center of gravity has shifted from startup survival to operator-UI coherence.

What is already true:
- the control engine, guard layer, explainability, and diagnostics model are substantially built
- the custom panel route has been removed from the shipped product
- the only supported operator path is now native Home Assistant integration/device surfaces: bootstrap install, then Configure for setup and tuning, plus the integration device page, entities, notifications, and Repairs for troubleshooting
- managed-device onboarding now has native add/edit/remove flows plus presets, unmanaged-candidate discovery, promotion review, shortlist guidance, and fleet review
- support center, setup checklist, support snapshot, and Repairs guidance now exist as real native HA support surfaces
- the integration now loads in the user's HA instance on the current `0.1.79` repo release line, exposes native entities again, and no longer appears to be dying in the early startup crash chain
- at least one real managed device is now present in the live HA install

What is not yet true:
- the native operator path is still not coherent enough that an operator can instantly tell where to manage devices, where to set policy, and where to review health from one obvious native surface
- the integration page still behaves more like a large entity pack than a polished operator product UI
- larger or more heterogeneous fleets still need more proof
- the product still uses JSON-backed inventory persistence internally, which is acceptable for now but remains a design pressure point
- release confidence still depends on screenshots, real installs, and package-distribution verification rather than repo-local confidence alone
- the current live blocker has shifted from startup failure to source validation and operator discoverability: the controller is loaded, but safe mode is blocking action because required mapped sources are unavailable or unknown in the real HA install

### Steering stance

The project should optimize for **real operator success in native Home Assistant**, not for adding more surfaces.

That now means two things at once:
1. keep fixing confirmed runtime/source friction in the real install
2. turn the existing native capabilities into a clearer operator workflow, with Configure becoming the obvious command center for sources, policy, managed devices, and support
3. treat real-install evidence as the primary roadmap signal
4. keep shrinking the gap between the intended native workflow and the actually shipped package
5. do not reintroduce any supported custom frontend, sidebar, panel, or external UI path unless project direction is explicitly re-decided with fresh evidence

## Current goals

1. Make Configure the clear native command center for sources, policy, managed devices, and support
2. Keep install, upgrade, and reload behavior stable in real Home Assistant environments
3. Make setup/support/diagnostics feel like one coherent native workflow instead of a scattered entity collection
4. Reduce operator dependence on raw JSON for normal device onboarding and editing
5. Provide a clearly discoverable native device-management path for tagging, reviewing, enabling, disabling, and editing managed devices
6. Provide a clearly discoverable native policy/settings path for mode, target export, deadband, reserve thresholds, and related controller behavior
7. Prove release quality with real-install validation and package-distribution checks

## Next-update definition of real progress

The next update only counts as real progress if it produces visible improvement in the user's actual Home Assistant install.

Minimum real-progress outcomes for the next update:
1. Zero Net Export stays loaded after install/restart and continues exposing native entities, not just during a brief success window
2. Configure becomes more self-explanatory as the place for source mapping, policy, and managed-device work
3. Native managed-device management becomes easier to discover and use for ordinary controllable loads, including common light/switch style entities where appropriate
4. The currently installed UI makes it obvious where to set policy and where to manage devices, even before the full expert dashboard pass is complete
5. Reload/restart verification proves the integration stays alive after install, and live source validation blockers are surfaced clearly enough that the operator can tell what to fix next

What does not count as enough progress for the next update:
- repo-only cleanup with no HA-visible improvement
- another release that merely changes the traceback but still leaves the operator unsure where configuration and device management live
- dashboard/support polish that ignores the current discoverability and workflow gaps

## Gap and risk register

| ID | Gap / risk | Why it matters | Current signal | Exit condition |
|---|---|---|---|---|
| G1 | Native Configure flow may still contain real-world friction | This is now the primary product path | Recent real-install screenshots already caught broken setup handoff behavior, and combined/net grid energy selection can still throw a Home Assistant field-level `Entity is neither a valid entity ID nor a valid UUID` error in at least one real install even though `0.1.79` now ships both a native manual fallback field for that energy entity, a clearer command-center status summary, policy-readiness guidance on the policy screen, and stronger managed-device promotion guidance | A fresh install and post-install Configure flow work end-to-end in a real HA instance using only the intended native Configure path |
| G2 | Native support surfaces are improved but still somewhat fragmented | Operators need one clear troubleshooting path | Support center, snapshot, checklist, device actions, entities, and Repairs now coexist | Real validation shows operators can diagnose setup/runtime state without hunting across unrelated surfaces |
| G3 | Managed-device UX is better, but larger mixed fleets may still feel clumsy | Fleet installs are where native flows most often regress into friction | Native presets, edit flow, and fleet review exist, but broader real-world proof is limited | A 5-10+ device mixed install can be onboarded, reviewed, and adjusted without JSON for normal work |
| G4 | JSON-backed inventory remains an internal dependency | Internal structure can leak back into operator experience | Docs already acknowledge the transitional design | Normal operator tasks do not require JSON except recovery or bulk surgery |
| G5 | Release visibility can drift from local repo state | HACS/manual installs only reflect what is actually packaged and published | Past validation already exposed version/changelog mismatch in a real install | Tagged release, changelog, manifest, and tested package all match the same shipped build |
| G6 | Runtime safety features need more field proof | Safety logic is only trustworthy if behavior matches real devices | Guards, reserve gating, runtime caps, and action history exist, but real-install coverage is incomplete | At least one real install confirms expected behavior for core control and safety paths |
| G7 | Native operator workflow is still hard to discover | If the user installs successfully but still has to ask where to manage devices and set policy, the product UI is not coherent enough yet | Real HA now loads and exposes 144 entities, but the user still cannot easily tell where the main UI lives for tagging/managing devices and policy | Configure and the integration/device surfaces make those paths obvious without explanation from support |
| G8 | Native managed-device workflow still needs stronger fleet/product presentation | If lights/switches/plugs appear but the workflow still feels buried or fragmented, the native operator path remains weak | One real device is now present in HA, and the repo now ships unmanaged-candidate discovery, promotion review, shortlist guidance, and fleet-console handoff, but the installed UI still needs real-user proof that those clues make fleet management feel obvious instead of like an entity pack | Configure shows real selectable entities, one real device can be added successfully, and managed-device review/editing feels like a first-class native flow |
| G9 | Source validation now blocks control in the live install | Runtime safety is working, but the operator still needs a clearer path to understand and fix missing/unavailable mapped sources | Live HA now reports controller `blocked` because required mapped sources are unavailable or unknown | Source blockers are surfaced in a way that tells the operator exactly what to fix and where to fix it |

## Acceptance criteria

The current native-HA-only release line is acceptable when all of the following are true:

### A. Operator workflow acceptance
- a fresh install can be completed through Add Integration plus Configure
- required source mapping works entirely in Configure
- at least one common fixed load and one common variable load can be onboarded through native flows
- edit-in-place device updates work without JSON for normal cases
- the setup path does not depend on removed panel/launcher behavior
- setup completes far enough that the integration page does not stall at `No entries`
- ordinary controllable entities appear in the native add-device picker when the operator tries to add a light/switch/load
- the installed UI makes it obvious where to manage devices, where to set policy, and where to review runtime health without needing verbal guidance

### B. Support and diagnostics acceptance
- readiness, recommendation, checklist, support center, and support snapshot tell a consistent story
- device-page actions and Repairs surface the main blockers clearly
- operators can gather enough information for support without digging through raw developer attributes

### C. Runtime acceptance
- the controller reaches explainable plan/action states with real source data
- at least one real managed device completes a real action path successfully
- safety conditions such as safe mode, stale data, and guard blocks remain visible and understandable

### D. Release acceptance
- `manifest.json`, `CHANGELOG.md`, release tag, and tested package version all agree
- tested install path is confirmed to be serving that exact package
- validation evidence is recorded before release claims are made
- release execution follows the approved release-management workflow in `RELEASE_MANAGEMENT.md`, including approval, GitHub latest-release verification, forced HACS metadata refresh, HA restart, and post-release project-specific log review

## Release gate checklist

Do not call the native-operator release line ready unless all gates below pass.

- [ ] Gate 1: Real install completed from add-integration through Configure without workaround
- [ ] Gate 2: Native managed-device onboarding works for normal fixed and variable devices
- [ ] Gate 3: Real control loop action path observed with trustworthy diagnostics
- [ ] Gate 4: Support/checklist/diagnostics/Repairs surfaces are coherent enough for operator triage
- [ ] Gate 5: Larger-fleet usability has at least one concrete validation pass, or is explicitly deferred in release notes
- [ ] Gate 6: Release metadata, tag, changelog, and distributed package are all aligned
- [ ] Gate 7: Release execution followed `RELEASE_MANAGEMENT.md`, including post-restart Zero Net Export log review and roll-forward capture of project-specific errors for the next release
- [ ] Gate 8: The next release removes the current early startup blocker so the config entry no longer dies in `setup_retry`
- [ ] Gate 9: The integration page no longer shows `No entries` for Zero Net Export after setup
- [ ] Gate 10: The native add-device picker shows real selectable entities and one real controllable device can be saved in the user's HA instance

## Prioritized next-action queue

### P0, do next
1. Turn Configure into the clearly signposted native command center for sources, policy, managed devices, and support
2. Make managed-device review/add/edit/remove feel like a first-class native operator workflow instead of buried capability
3. Make policy/settings clearly discoverable as a distinct native path for mode, target export, deadband, reserve, and related controller behavior
4. Re-run restart and reload validation and record whether the integration stays alive after install, now that the `0.1.79` repo release line has crossed the startup-stability line locally and added stronger managed-device promotion guidance but still needs fresh live HA proof
5. Use the live source-validation blockers in the user's HA install to improve operator-facing remediation clarity, especially by naming the unavailable/stale mapped source roles and pointing operators back to Configure -> Sources
6. Then continue broader runtime/device validation

### Deferred but explicitly tracked
1. Validate the new native combined/net grid energy fallback field in a real Home Assistant install: confirm operators can finish source mapping by pasting the same entity ID when the picker still produces the field-level `Entity is neither a valid entity ID nor a valid UUID` error
2. Treat that native fallback as temporary and acceptable only to unblock broader product validation while the picker path is still being hardened
3. Highest-probability next investigation path: simplify the combined-grid energy form handling further so the picker validates cleanly without needing the manual fallback field

### P1, next after the validation pass
1. Validate a mixed-device fleet scenario, not just a single-device happy path
2. Tighten any remaining cases where operators still get pushed back into JSON for normal edits
3. Reduce overlap between support center, setup checklist, support snapshot, and Repairs if real usage shows duplication or confusion

### P2, only after the above is materially stronger
1. Package and release only after the exact tested build is verified as the one users will install
2. Then consider further fleet polish, richer diagnostics grouping, or future optimization features

## Operating rules for future work

When deciding what to do next:
- prefer confirmed real-install friction over speculative UX polish
- prefer fewer stronger native surfaces over more surfaces
- prefer release-proofing and validation over roadmap expansion
- treat JSON reduction as a means, not the end goal
- do not reintroduce a custom panel as the default answer to native UX rough edges
- treat `RELEASE_MANAGEMENT.md` as the operational release procedure for this project, not an optional suggestion
- after each release/restart, inspect Home Assistant logs for Zero Net Export specific errors and carry those findings into the next release by default, without waiting for the user to restate them

## Source documents

- Product scope: `docs/PRODUCT_SPEC_V1.md`
- Current implementation trail: `docs/IMPLEMENTATION_PLAN.md`
- Native operator direction: `docs/NATIVE_OPERATOR_PLAN.md`
- Validation proof: `docs/VALIDATION_CHECKLIST.md`
- Release discipline: `RELEASE_MANAGEMENT.md`
