# Supervisor

This is the active steering layer for Zero Net Export.

Use this document to decide what the project should do next, what is currently blocking release confidence, and what must be true before calling the native-HA-only operator experience ready.

Supporting detail lives in the spec, implementation, validation, and release docs. This file is the place that turns those into a current operating stance.

## Product state summary

### Current release-line position

Zero Net Export is in **late stabilization and native-surface consolidation**.

What is already true:
- the control engine, guard layer, explainability, and diagnostics model are substantially built
- the custom panel route has been removed from the shipped product
- the only supported operator path is now native Home Assistant integration/device surfaces: bootstrap install, then Configure for setup and tuning, plus the integration device page, entities, notifications, and Repairs for troubleshooting
- managed-device onboarding now has native add/edit/remove flows plus presets and fleet review
- support center, setup checklist, support snapshot, and Repairs guidance now exist as real native HA support surfaces

What is not yet true:
- the native operator path has not yet been validated enough in real Home Assistant installs to call it boring and release-safe
- larger or more heterogeneous fleets still need more proof
- the product still uses JSON-backed inventory persistence internally, which is acceptable for now but remains a design pressure point
- release confidence still depends on screenshots, real installs, and package-distribution verification rather than repo-local confidence alone

### Steering stance

The project should optimize for **real operator success in native Home Assistant**, not for adding more surfaces.

That means:
1. fix confirmed friction before expanding scope
2. treat real-install evidence as the primary roadmap signal
3. keep shrinking the gap between the intended native workflow and the actually shipped package
4. do not reintroduce any supported custom frontend, sidebar, panel, or external UI path unless project direction is explicitly re-decided with fresh evidence

## Current goals

1. Make the native Configure workflow reliably complete for a normal operator
2. Keep install, upgrade, and reload behavior stable in real Home Assistant environments
3. Make setup/support/diagnostics feel like one coherent native workflow
4. Reduce operator dependence on raw JSON for normal device onboarding and editing
5. Prove release quality with real-install validation and package-distribution checks

## Gap and risk register

| ID | Gap / risk | Why it matters | Current signal | Exit condition |
|---|---|---|---|---|
| G1 | Native Configure flow may still contain real-world friction | This is now the primary product path | Recent real-install screenshots already caught broken setup handoff behavior, and combined/net grid energy selection still throws a Home Assistant field-level `Entity is neither a valid entity ID nor a valid UUID` error in at least one real install | A fresh install and post-install Configure flow work end-to-end in a real HA instance without workaround |
| G2 | Native support surfaces are improved but still somewhat fragmented | Operators need one clear troubleshooting path | Support center, snapshot, checklist, device actions, entities, and Repairs now coexist | Real validation shows operators can diagnose setup/runtime state without hunting across unrelated surfaces |
| G3 | Managed-device UX is better, but larger mixed fleets may still feel clumsy | Fleet installs are where native flows most often regress into friction | Native presets, edit flow, and fleet review exist, but broader real-world proof is limited | A 5-10+ device mixed install can be onboarded, reviewed, and adjusted without JSON for normal work |
| G4 | JSON-backed inventory remains an internal dependency | Internal structure can leak back into operator experience | Docs already acknowledge the transitional design | Normal operator tasks do not require JSON except recovery or bulk surgery |
| G5 | Release visibility can drift from local repo state | HACS/manual installs only reflect what is actually packaged and published | Past validation already exposed version/changelog mismatch in a real install | Tagged release, changelog, manifest, and tested package all match the same shipped build |
| G6 | Runtime safety features need more field proof | Safety logic is only trustworthy if behavior matches real devices | Guards, reserve gating, runtime caps, and action history exist, but real-install coverage is incomplete | At least one real install confirms expected behavior for core control and safety paths |

## Acceptance criteria

The current native-HA-only release line is acceptable when all of the following are true:

### A. Operator workflow acceptance
- a fresh install can be completed through Add Integration plus Configure
- required source mapping works entirely in Configure
- at least one common fixed load and one common variable load can be onboarded through native flows
- edit-in-place device updates work without JSON for normal cases
- the setup path does not depend on removed panel/launcher behavior

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

## Release gate checklist

Do not call the native-operator release line ready unless all gates below pass.

- [ ] Gate 1: Real install completed from add-integration through Configure without workaround
- [ ] Gate 2: Native managed-device onboarding works for normal fixed and variable devices
- [ ] Gate 3: Real control loop action path observed with trustworthy diagnostics
- [ ] Gate 4: Support/checklist/diagnostics/Repairs surfaces are coherent enough for operator triage
- [ ] Gate 5: Larger-fleet usability has at least one concrete validation pass, or is explicitly deferred in release notes
- [ ] Gate 6: Release metadata, tag, changelog, and distributed package are all aligned

## Prioritized next-action queue

### P0, do next
1. Continue the current real Home Assistant validation pass against the shipped native Configure workflow, using temporary operator workarounds where needed so broader runtime/device validation can continue
2. Capture exact friction in that run, especially around Configure, managed-device onboarding, and support-surface coherence
3. Fix only the confirmed friction that blocks a normal operator path, except for the currently deferred combined/net grid energy field bug which is documented below and may be revisited after broader operator validation
4. Re-run validation and record whether each issue is fully closed

### Deferred but explicitly tracked
1. Investigate the combined/net grid energy field bug in the native Configure flow: in at least one real Home Assistant install, selecting a valid energy entity still produces the field-level error `Entity is neither a valid entity ID nor a valid UUID`
2. Treat the current workaround, supplying a different working value to proceed, as temporary and acceptable only to unblock broader product validation
3. Highest-probability next investigation path: simplify the combined-grid energy form handling so the field validates as a plain selected entity before conversion into derived import/export bindings

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

## Source documents

- Product scope: `docs/PRODUCT_SPEC_V1.md`
- Current implementation trail: `docs/IMPLEMENTATION_PLAN.md`
- Native operator direction: `docs/NATIVE_OPERATOR_PLAN.md`
- Validation proof: `docs/VALIDATION_CHECKLIST.md`
- Release discipline: `docs/RELEASE_PROCESS.md`
