# SUPERVISOR.md

This file is the steering guide for this project.

Use it to decide:
- what the project should optimize for
- what currently matters most
- what counts as real progress
- what should not be treated as progress
- how active bugs should be posted, worked, validated, and closed in conjunction with `docs/BUGS.md`

## Current position

The project is currently in: late stabilization and native-surface consolidation

What is already true:
- The integration loads again in the user’s real Home Assistant instance and native entities are present.
- The product is no longer primarily blocked by startup crashes.
- The only supported operator path is now native Home Assistant surfaces, with Configure, the Zero Net Export device at Settings -> Devices & Services -> Integrations -> Zero Net Export -> Devices -> open the Zero Net Export device, entities, notifications, and Repairs as the intended path.
- Managed-device onboarding already has native add, edit, remove, presets, unmanaged-candidate discovery, promotion review, shortlist guidance, and fleet review.
- Diagnostics guide, diagnostics snapshot, setup checklist, and Repairs guidance now exist as native diagnostics surfaces.
- At least one real managed device is now present in the live Home Assistant install.

What is not yet true:
- The native operator path is still not coherent enough that an operator can instantly tell where to manage devices, set policy, and review health.
- The integration still behaves too much like a large entity pack instead of a polished operator product UI.
- Larger or more heterogeneous fleets still need more proof.
- Release confidence still depends on real installs, screenshots, and distribution verification rather than repo-local confidence alone.
- The exact live install still does not match the current repo candidate, so live screenshot-grade proof remains gated by release drift and deploy/restart approval, not by lack of documented HA access.
- The user does not consider the requested visible native UI outcomes complete yet, even though some supporting scaffolding exists in code.

## Steering stance

Optimize for:
- Real operator success in native Home Assistant
- Clearer operator workflow through the existing native surfaces
- Real-install evidence as the main roadmap signal

Do not drift into:
- Adding more surfaces instead of improving the current native path
- Reintroducing any custom frontend, sidebar, panel, or external UI path without an explicit project-direction change

## Current goals

- Treat `0.1.86` as the current live correction line, but treat `0.1.87` as the current full UI rollout target defined by `docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md`.
- Make Configure the clear native command center for sources, policy, managed devices, and diagnostics.
- Separate the operator information architecture into four obvious native buckets: Controls, Sensors, Managed Devices, and Diagnostics.
- Keep the Zero Net Export brain/control surface focused on controller-level settings and decisions only, not managed-device inventory operations.
- Make Managed Devices a first-class native workspace for enablement, priority, overrides, promotion, and fleet review.
- Make managed versus unmanaged device state visually obvious in native Home Assistant surfaces.
- Make the native promote / vet / review flow feel like a first-class operator workflow rather than scaffolded helper text.
- Keep Sensors strictly about mapped/system telemetry and not a mixed dumping ground for managed-device controls.
- Introduce a clearer detailed-management path for managed devices, reachable from the native device view, for spreadsheet-style fleet detail and per-device review.
- Keep install, upgrade, reload, and restart behavior stable in real Home Assistant environments.
- Make setup, support, and diagnostics feel like one coherent native workflow.
- Reduce operator dependence on raw JSON for normal device onboarding and editing.
- Make device management and policy/settings clearly discoverable through native flows.
- Prove release quality with real-install validation and package-distribution checks.

## What counts as real progress now

A run counts as real progress only if it results in:
- Visible improvement in the user’s actual Home Assistant install.
- Configure becoming more self-explanatory as the place for source mapping, policy, and managed-device work.
- Managed-device management becoming easier to discover and use for ordinary controllable loads.
- The installed UI making it obvious what belongs under Controls, what belongs under Sensors, what belongs under Managed Devices, and what belongs under Diagnostics.
- The installed UI making it obvious where to set policy and where to manage devices.
- Restart and reload validation proving the integration stays alive and source blockers are surfaced clearly enough that the operator can tell what to fix next.
- A validated code change is committed, pushed, and, when appropriate, advanced through the release process defined in `RELEASE_MANAGEMENT.md`.

This does not count as enough progress:
- Repo-only cleanup with no Home Assistant visible improvement.
- Another change that alters the traceback or internals while still leaving the operator unsure where configuration and device management live.
- Dashboard or support polish that ignores the main discoverability and workflow gaps.
- Counting support text, diagnostics copy, or backend plumbing as delivered UI when James still cannot see the requested native UI outcome in Home Assistant.

## Main gaps or risks

- Native Configure flow may still contain real-world friction, including source-mapping problems in live installs.
- Native support and device-management surfaces exist but may still feel fragmented or buried.
- Larger mixed-fleet usability and runtime safety still need more real-world proof.
- Release visibility can drift from actual shipped package state.
- Source validation blockers are still preventing real control in the live install.
- Active bugs and regressions must stay explicitly tracked in `docs/BUGS.md` rather than being implied across scattered notes.

## Acceptance check

This phase is in good shape when:
- A fresh install can be completed through Add Integration and Configure without workaround.
- Required source mapping works entirely in Configure.
- At least one common fixed load and one common variable load can be onboarded through native flows.
- Edit-in-place device updates work without JSON for normal cases.
- The installed UI makes it obvious where to manage devices, where to set policy, and where to review runtime health.
- The controller reaches explainable plan/action states with real source data.
- At least one real managed device completes a real action path successfully.
- The tested install path is confirmed to be serving the exact intended package and version.

## Next actions

Do next:
1. Treat `docs/UI_IMPLEMENTATION_MAP.md`, especially its `Detailed remaining work map`, as the strict staged checklist for finishing the full `0.1.87` UI design scope.
2. Work the remaining steps in workstream order: opening operator console, Managed Devices workspace, promotion flow, four-bucket IA, notification/support cleanup, then exact-build release execution.
3. Treat the device-page deeper review path as primarily in live-proof posture unless new repo-side drift appears there, rather than reopening Workstream E by default.
4. Prefer the next unfinished UI workstream step over release-state bookkeeping whenever safe repo-side implementation work still exists.
5. Keep logging real remaining gaps against `docs/BUGS.md` so the release cut line is based on explicit evidence rather than vague feeling.
6. Once the remaining repo-side UI work is coherent enough, freeze the `0.1.87` cut line, bump versioned metadata, run the full validation pass, and execute the release flow.
7. Only ask James for formal release approval when the candidate has materially crossed a release boundary with new evidence, and otherwise continue building the next mapped `0.1.87` step instead of repeating the same release ask.

Do later:
- Validate a mixed-device fleet scenario, not just a single-device happy path.
- Tighten remaining cases where operators still get pushed back into JSON for normal edits.
- Package and release only after the exact tested build is verified as the one users will actually install.

## Bug-tracking rules

- `docs/BUGS.md` is the single source of truth for active bugs, regressions, validation state, and closure state.
- When a new confirmed bug or regression is found, add or update the relevant entry in `docs/BUGS.md` in the same run when reasonably possible.
- When a bug is being actively fixed, update the bug entry so repo-only fixes, live-validation state, and next action are explicit.
- Do not treat a bug as closed just because code changed. Follow the validation/closure rules in `docs/BUGS.md`.
- If a watchdog or supervisor run finds bug drift, missing validation, or a stale bug state, fixing the bug entry itself counts as legitimate project progress.

## Operating rules

- Prefer confirmed real-install friction over speculative UX polish.
- Supervisor is the builder, not a release-status clerk. Default to shipping the next meaningful `0.1.87` UI improvement whenever safe implementation work remains.
- Do not spend a run only refreshing candidate hashes, docs heads, or approval wording unless that correction materially changes a real decision.
- Treat repeated release-boundary reporting as edge-triggered, not level-triggered: ask once when a candidate newly becomes release-ready, then continue adjacent product work until there is materially new release evidence.
- Throttle exact-build fingerprint checks. Re-run them when preparing for deploy, after deploy, after restart, or when live-vs-repo uncertainty materially affects the decision in that run, not as rote every-cycle bookkeeping.
- If the same blocker is unchanged across recent runs and no new evidence was found, do not spend the run rephrasing it. Make adjacent product progress or send a concise no-change update.
- Prefer practical outcomes over theory.
- Prefer fewer stronger native surfaces over more surfaces.
- Prefer release-proofing and validation over roadmap expansion.
- Treat JSON reduction as a means, not the end goal.
- If blocked on the user, continue only with safe adjacent work.
- Do not reintroduce a custom panel as the default answer to native UX rough edges.
- Keep updates delta-only.
- Format thread updates for quick scanning: keep the `SUPERVISOR HH:MM` title on its own line, then separate the body with short bullet points or numbered bullets instead of one dense paragraph.
- If user action is needed, state the exact action needed.
- When progress depends on live runtime evidence, first use the documented access paths in TOOLS.md before asking the user for screenshots, logs, tracebacks, or validation evidence.
- Only treat live validation as a user blocker if the required evidence cannot be gathered through the documented access paths or requires human-only interaction.
- Treat `RELEASE_MANAGEMENT.md` as the authoritative release execution procedure for this project. Do not improvise release flow outside it.
- Treat shipping working code as part of project progress, not as a separate optional follow-up.
- When a safe, validated improvement is complete, commit it and push it unless a higher-priority project rule blocks that.
- When the project is sufficiently ready for release, follow `RELEASE_MANAGEMENT.md` rather than stopping at local code changes.
- Do not treat local repo progress as complete if the intended result depends on GitHub release visibility, HACS update, Home Assistant restart, or live post-release verification.
- If release execution requires explicit user approval, ask James for that approval at the point the project is release-ready, then continue the release flow through `RELEASE_MANAGEMENT.md`.
- Do not rely on implied approval, “next gap”, or embedded command suggestions when the real next step is a formal release. When the candidate is coherent enough for release, explicitly say that the release is ready and ask James for approval to execute it end-to-end.
- Supervisor updates should not make James infer that release approval is needed. If the actual boundary is formal release execution, state that directly in the thread.
- Keep version tracking explicit during ongoing work: verify local manifest/changelog version, current branch state, and local-vs-remote GitHub status before claiming release readiness or shipped progress.
- Distinguish clearly between local working version, pushed remote state, and publicly released GitHub version. Do not present them as the same unless they are verified to match.

## Source documents

Primary UI source-of-truth documents:
- UI design source of truth: `docs/UI_DESIGN.md`
- UI implementation / phase / status source of truth: `docs/UI_IMPLEMENTATION_MAP.md`
- Bug / regression / validation / closure source of truth: `docs/BUGS.md`

Other project references:
- Product scope: `docs/PRODUCT_SPEC_V1.md`
- Historical implementation trail: `docs/IMPLEMENTATION_PLAN.md`
- Historical native-direction trail: `docs/NATIVE_OPERATOR_PLAN.md`
- Validation proof: `docs/VALIDATION_CHECKLIST.md`
- Release discipline: `RELEASE_MANAGEMENT.md`
