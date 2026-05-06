# Zero Net Export — Non-Negotiable Development Constraints

Zero Net Export is a Home Assistant custom integration.

It is not a standalone app, not a custom Home Assistant frontend, not a sidebar panel, and not an external web UI unless the user explicitly approves a change in project direction.

This document is the highest-priority project rulebook for OpenClaw and all automated agents working on this repository.

If any other document conflicts with this document, this document wins.

---

## 1. Mandatory execution rule for every task

Work only inside the Home Assistant-native integration constraints defined in this document.

For every current issue, request, feature, bug, UX improvement, refactor, or UI change, OpenClaw must produce a feasibility classification **before coding**.

The classification must be one of:

- Native HA supported
- Options flow / config flow supported
- Entity/device/repair/notification supported
- Lovelace-only
- Custom frontend/panel required
- Not implementable

If the requested behavior requires any of the following, OpenClaw must stop and mark the task as blocked unless explicit user approval is given:

- Custom panel
- Sidebar app
- External web UI
- Home Assistant frontend patch
- Exact placement inside native Home Assistant rows, cards, menus, or controls that the integration API does not expose
- Any UI behavior not supported by current Home Assistant integration APIs

OpenClaw must not propose alternatives outside the approved native operator path unless explicitly asked.

The approved native operator path is:

Settings → Devices & Services → Integrations → Zero Net Export → Configure

Secondary supported paths are:

- Device page
- Entity pages
- Repairs
- Persistent notifications
- Diagnostics
- Services/actions
- Optional Lovelace examples for visibility only

---

## 2. Source of truth order

When documents disagree, use this authority order:

1. `CONSTRAINTS.md`
2. `PROJECT_STATUS.md`
3. `docs/ACTIVE_USER_REQUESTS.md`
4. `docs/BUGS.md`
5. `docs/SUPERVISOR.md`
6. Current implementation under `custom_components/zero_net_export`
7. `README.md`
8. Historical docs only if explicitly referenced by the user

Deprecated docs must not create work.

Historical design docs, old implementation maps, previous UX plans, or superseded notes must not override current constraints, active bugs, or current user-highlighted requests.

---

## 3. Allowed implementation surfaces

The integration may use these Home Assistant-native surfaces:

- Config flow for initial setup/bootstrap
- Options flow / Configure for normal setup and editing
- Native Home Assistant entities
- Native device registry behavior
- Native entity registry behavior
- Native services/actions
- Native Repairs issues
- Persistent notifications
- Diagnostics snapshots/downloads
- Translations under `strings.json`
- Tests and validation scripts
- Documentation
- Optional Lovelace dashboard examples for visibility only

The primary configuration and management surface is the integration Configure flow.

The device page, entity pages, Repairs, persistent notifications, diagnostics, and services/actions are supporting surfaces.

---

## 4. Forbidden work unless explicitly approved

Do not implement or propose the following unless the user explicitly approves a project direction change:

- Custom Home Assistant panel
- Sidebar app
- External web UI
- Custom frontend replacement for Home Assistant Settings
- Custom frontend replacement for Devices & Services
- Custom frontend replacement for the device page
- Home Assistant core patch
- Home Assistant frontend patch
- Custom JavaScript frontend as the primary operator workflow
- Custom card as the primary configuration workflow
- Raw JSON/YAML as the primary user workflow
- Workarounds that depend on undocumented Home Assistant internals
- Features that require exact placement inside native Home Assistant UI rows, menus, cards, or controls that integrations cannot control
- Any UX that assumes control over Home Assistant screens the integration does not own

If a requested behavior falls into this category, OpenClaw must stop and mark the task as blocked.

It may explain the boundary and suggest only approved native alternatives unless the user asks for non-native alternatives.

---

## 5. Product direction

Zero Net Export must remain a Home Assistant-native integration.

The primary operator path is:

Settings → Devices & Services → Integrations → Zero Net Export → Configure

The Configure flow owns:

- Setup
- Source sensor selection
- Import/export/grid role configuration
- Managed devices
- Device control settings
- Control mode
- Diagnostics visibility
- Safe reconfiguration

The integration device page may provide:

- Entity visibility
- Current status
- Diagnostic entities
- Links into native Home Assistant surfaces
- Supporting review/audit information

Repairs may provide:

- Missing required sensor warnings
- Invalid configuration warnings
- Unavailable source warnings
- Unsafe or incomplete setup warnings
- Recovery guidance

Persistent notifications may provide:

- Runtime warnings
- Operator-visible diagnostic messages
- One-off setup or migration notices

Services/actions may provide:

- Explicit operator-triggered behaviours
- Diagnostics actions
- Safe helper actions
- Managed-device operations where appropriate

Lovelace examples may provide:

- Optional dashboards
- Visibility examples
- Debug/operator views

Lovelace must not become the required primary configuration surface unless explicitly approved.

---

## 6. Required proof before implementation

Before coding, OpenClaw must state:

1. The requested behavior.
2. The Home Assistant surface it intends to use.
3. The feasibility classification.
4. Why that surface is allowed under this document.
5. The exact files it expects to change.

If the feasibility classification is one of:

- Lovelace-only
- Custom frontend/panel required
- Not implementable

then OpenClaw must not code.

It must stop and report the constraint boundary.

---

## 7. Feasibility classification definitions

### Native HA supported

Use this when the requested behavior is directly supported by standard Home Assistant integration patterns.

Examples:

- Creating entities
- Updating entity state
- Adding device info
- Adding services/actions
- Creating diagnostics
- Creating Repairs issues
- Creating persistent notifications

### Options flow / config flow supported

Use this when the requested behavior can be implemented inside Home Assistant’s native setup or Configure flows.

Examples:

- Selecting sensors
- Editing thresholds
- Enabling or disabling managed devices
- Editing device-control settings
- Re-running setup choices
- Validating configuration before saving

### Entity/device/repair/notification supported

Use this when the requested behavior belongs on entities, device pages, Repairs, persistent notifications, or services/actions.

Examples:

- Warning the user that a source sensor is unavailable
- Exposing export/import/current status as entities
- Creating a Repair when setup is incomplete
- Creating a persistent notification for a runtime blocker
- Adding a service/action for a safe explicit operator command

### Lovelace-only

Use this when the requested behavior can only be shown through dashboards, custom cards, or Lovelace UI composition.

OpenClaw must not implement Lovelace-only work as the primary product workflow unless explicitly approved.

### Custom frontend/panel required

Use this when the requested behavior requires a custom Home Assistant panel, sidebar item, JavaScript frontend, or replacement UI.

OpenClaw must stop unless explicitly approved.

### Not implementable

Use this when the requested behavior cannot be done inside the current Home Assistant integration boundaries.

OpenClaw must stop and explain the boundary.

---

## 8. UI and UX constraint rules

OpenClaw must not assume the integration can control arbitrary Home Assistant UI placement.

The integration cannot assume control over:

- Native Home Assistant sidebar layout
- Native device page row layout
- Native entity row buttons
- Native pencil/cog/action placement
- Native card layout outside supported entity metadata
- Native menu placement
- Native Settings page structure
- Native Devices & Services page structure

If the user requests exact placement inside a Home Assistant-native row, page, menu, or card, OpenClaw must classify the request before coding.

If the Home Assistant integration API does not expose that placement, the task is blocked unless the user approves a custom frontend/panel direction.

---

## 9. Development loop

Every task must follow this loop:

1. Read `CONSTRAINTS.md`.
2. Read `PROJECT_STATUS.md`.
3. Read `docs/ACTIVE_USER_REQUESTS.md`.
4. Read `docs/BUGS.md`.
5. Identify the smallest allowed native implementation.
6. State the requested behavior.
7. State the Home Assistant surface being changed.
8. State the feasibility classification.
9. State why the surface is allowed.
10. State expected files to change.
11. Implement only that change.
12. Run relevant tests.
13. Produce evidence.
14. Update project status only if materially changed.
15. Do not deploy, restart, tag, publish, or release unless explicitly approved.

---

## 10. Evidence requirements

OpenClaw must not claim a change is complete without evidence.

Acceptable evidence includes:

- Test output
- Validation script output
- Before/after screenshots when applicable
- Home Assistant log output
- Config flow validation evidence
- Options flow validation evidence
- Entity state evidence
- Repair issue evidence
- Persistent notification evidence
- Service/action registration evidence
- Diagnostics output evidence

Claims such as “should work”, “likely fixed”, “implemented”, or “ready” are not acceptable without evidence.

If evidence cannot be produced, OpenClaw must say so.

---

## 11. Testing requirements

Before claiming completion, OpenClaw must run the relevant available tests.

At minimum, for code changes, consider:

- Unit tests
- Integration tests
- Linting
- Translation validation
- Config flow tests
- Options flow tests
- Service/action tests
- Repairs tests
- Diagnostics tests
- Regression tests for the touched area

If tests cannot be run, OpenClaw must state:

- Which tests were not run
- Why they were not run
- What risk remains

---

## 12. Release and deployment restrictions

OpenClaw must not do any of the following without explicit user approval:

- Restart Home Assistant
- Deploy to a live Home Assistant instance
- Publish a release
- Create a git tag
- Push to GitHub
- Merge branches
- Delete branches
- Rewrite git history
- Bump version numbers for release
- Mark a release as ready
- Claim production readiness

Preparing release notes or release metadata is allowed only if the user asked for preparation.

Executing the release is not allowed unless explicitly approved.

---

## 13. Git and repository safety

OpenClaw must not perform destructive git operations without explicit approval.

Forbidden without approval:

- `git reset --hard`
- `git clean -fd`
- `git push --force`
- Branch deletion
- Tag deletion
- History rewrite
- Mass file deletion
- Large refactors unrelated to the task

Before committing, OpenClaw must be able to explain:

- What changed
- Why it changed
- Which constraint allowed it
- Which tests were run
- What evidence exists

---

## 14. Scope control

OpenClaw must implement the smallest useful allowed change.

Do not expand scope from:

- Bug fix into redesign
- UI request into frontend architecture
- Config flow improvement into custom panel
- Entity improvement into dashboard system
- Diagnostics improvement into external app
- One issue into broad refactor
- One operator request into a release plan

If a larger redesign appears useful, OpenClaw must document it as a proposal only.

It must not begin implementation without approval.

---

## 15. Handling impossible or blocked requests

When a request is blocked by this document, OpenClaw must respond using this format:

```text
Blocked by constraint.

Requested behavior:
<plain-English summary>

Constraint boundary:
<which rule blocks it>

Feasibility classification:
<classification>

Allowed native alternative:
<only if one exists>

Files changed:
None.