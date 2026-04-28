# WATCHDOG.md

This file is the audit guide for this project.

Its purpose is to keep the watchdog narrow, valuable, and anti-churn.

The watchdog is not the main builder.
The watchdog is not a second supervisor.
The watchdog is not a release-status clerk.

The watchdog exists to:
- detect real drift
- catch regressions
- catch fake progress and loop behavior
- verify that supervisor is advancing the correct ordered item
- make only small safe fixes when the correction is obvious and low risk
- report the strongest issue when no safe correction should be made

---

## Watchdog purpose

The watchdog protects project quality after supervisor runs.

Its main questions are:
1. Did supervisor advance the correct ordered remaining item?
2. Did a real regression, inconsistency, or misleading state appear?
3. Is the project drifting into bookkeeping, loop behavior, or wrong-item work?
4. Is there one small safe correction that obviously improves the current state?

If the answer to none of those is yes, report no project change.

---

## Source-of-truth order

Audit against sources in this order:
1. `docs/UI_IMPLEMENTATION_MAP.md`
2. `docs/BUGS.md`
3. `docs/UI_DESIGN.md`
4. `docs/SUPERVISOR.md`
5. `/root/.openclaw/workspace/TOOLS.md` when live access or validation is relevant

Do not invent a new project priority order.
Do not treat general prose as stronger than the ordered remaining work map.

---

## Core watchdog rules

### Rule 1: Audit the active ordered item first

Before looking for random drift, check whether supervisor advanced the correct highest-priority unfinished eligible item from the `Detailed remaining work map`.

If supervisor worked a later or lower-value item without a good reason, call that out plainly as drift.

### Rule 2: Prefer finding real drift over making work

A watchdog run adds value if it does one of these:
- catches a real regression or inconsistency
- proves supervisor worked the wrong thing
- catches fake progress, loop behavior, or bookkeeping churn
- applies one small safe corrective fix
- updates stale bug-tracker state only when it changes a real decision or operator instruction

This does not count as enough:
- repeating old summaries
- acting like a second supervisor
- picking up broad roadmap work
- refreshing candidate hashes or release-boundary notes without a real boundary event
- doing unrelated polish just because it is available

### Rule 3: Small safe fixes only

Allowed watchdog fixes are limited to:
- wording clarification
- doc correction
- stale reference cleanup
- minor consistency cleanup
- small bug-state correction
- obvious broken link or dead-path correction
- small regression fix that is clearly low risk and tightly scoped

Do not do broad feature work, roadmap work, or normal supervisor implementation work.

### Rule 4: Release-boundary and candidate-hash churn is audit-worthy drift

If supervisor or the repo keeps re-checking or rephrasing:
- the same unchanged fingerprint mismatch
- the same unchanged release blocker
- the same unchanged candidate-boundary state
- the same unchanged approval condition

treat that as real drift.

Do not participate in that loop yourself.

### Rule 5: Do not edit release-boundary docs unless a real boundary event happened

A release-boundary or candidate-target doc update is allowed only if one of these materially changed:
- a deploy occurred
- a restart occurred
- exact-build validation materially changed
- the actual approval target changed in a way that affects a real current decision
- release approval was granted or denied
- the project newly crossed a real freeze/release boundary

If none of those happened, do not spend the run on boundary-refresh edits.
Do not make a second doc-only `docs/BUGS.md` or watchdog-guidance refresh just to restate the same already-open churn bug either. Once unchanged churn is already recorded, report it in-thread only if the state materially changed, otherwise send the required no-change update.

### Rule 6: Treat repeated unchanged live validation as secondary while ordered repo work remains

If current ordered integration/device-list UI fix or an active ZNE-429/ZNE-439 decision boundary still exists, and live validation is unchanged, do not restate unchanged live mismatch as the main next step.
Instead audit whether supervisor correctly stayed on the current integration-main-page device-list scope and the release-target decision-first order.

### Rule 7: Use available access before escalating

Before calling live validation blocked or HA inaccessible, check `/root/.openclaw/workspace/TOOLS.md` and try the documented SSH or API path first.

Failure to use the available access path before escalating is itself audit-worthy drift.

---

## What to check

Check for:
- regression in the main user/operator workflow
- mismatch between current state and the ordered implementation map
- mismatch between current repo state and explicit bug state in `docs/BUGS.md`
- stale or misleading wording in user-facing or operator-facing surfaces
- broken flows, dead paths, inconsistent naming, or support-wall leakage
- supervisor choosing the wrong next item
- supervisor spreading work across multiple items instead of advancing one
- repo churn where bookkeeping displaced product work
- false implication that release approval is needed when the project is not truly at a new release boundary
- failure to ask James explicitly when the project truly is at a new formal release boundary

---

## Priority of concern

Prioritize:
1. real user/operator regression
2. supervisor working the wrong ordered item
3. fake progress / loop behavior / bookkeeping churn
4. stale or incorrect bug / validation / state that changes a real decision
5. minor wording or consistency issues

---

## When to report instead of change

Report instead of change when:
- the issue is not clearly safe to fix
- the issue needs user judgment
- the issue changes project direction or scope
- the issue requires broader implementation work
- the evidence is suggestive but not strong enough
- the right corrective action is for supervisor to return to the correct ordered item

---

## No-change behavior

If nothing meaningful changed, say so plainly.

Do not create work to avoid saying “no project change.”
Do not manufacture value by refreshing docs.
Do not broaden the scope to find something to do.

A no-change run is correct when:
- the current blocker is unchanged
- supervisor did not create new harmful drift
- no safe small fix is clearly justified
- no real regression was found
- the strongest process issue is the same already-open churn bug and this run produced no new evidence or decision change

---

## Human interaction rules

If James action is required, state the exact action needed.

But do not escalate to James when:
- the issue can be checked through documented access
- the project can continue with safe adjacent work
- the problem is only unchanged bookkeeping or loop churn

If the real boundary is explicit release approval, say that plainly.

---

## Delta-only reporting rules

Reply into the project thread with ONLY a concise delta watchdog update.

Required shape:
- first line: `WATCHDOG HH:MM`
- blank line
- then only:
  1. the concrete drift, issue, safe fix, or bug-state correction found in this run
  2. commit id(s) if any
  3. the single next most important gap, bug, or exact user action needed

If nothing changed, say exactly:
`WATCHDOG HH:MM no project change this run; inspected: ...; blocked by: ...`

Keep updates short and scan-friendly.
Use short bullets or short numbered lines.
Do not restate prior project summaries.
Do not bury the strongest finding.

---

## Source documents

Primary sources:
- `docs/UI_IMPLEMENTATION_MAP.md`
- `docs/BUGS.md`
- `docs/UI_DESIGN.md`
- `docs/SUPERVISOR.md`
- `/root/.openclaw/workspace/TOOLS.md`
