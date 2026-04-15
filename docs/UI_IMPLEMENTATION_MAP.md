# UI Implementation Map for 0.1.83

This file is the strict checklist for the **0.1.83 UI release**.

The goal is not repo activity. The goal is visible native Home Assistant UI outcomes that James can actually see and judge.

## Release intent

`0.1.83` is the **UI release**.

It should focus on the three native-UI outcomes James asked for:
1. a clear **managed vs unmanaged** device experience
2. a clear **promote / vet / review** native flow for bringing unmanaged devices into the managed fleet
3. a clear native information architecture split between **Controls**, **Sensors**, **Managed Devices**, and **Diagnostics**

If a change does not materially help one of those three visible outcomes, it should not displace this work unless it is required to keep the integration loading.

## 1. Already visible now

These things appear to exist in the current codebase and are at least partially exposed through native Home Assistant surfaces.

### Native IA labels and paths
- Configure has explicit paths and wording for:
  - Controls
  - Sensors and source mapping
  - Managed Devices
  - Diagnostics
- Native support/command-center text refers to these areas as distinct sections.

### Managed-device workflow building blocks
- Managed device add flow exists
- Managed device edit flow exists
- Managed device remove flow exists
- Fleet review / bulk enable-disable flow exists
- Candidate discovery exists for unmanaged entities
- Candidate shortlist path exists
- Full unmanaged candidate list path exists
- Candidate vetting/review step exists before promotion

### Supporting native entities/buttons
- unmanaged candidate count / overview sensors exist
- top unmanaged candidate sensors exist
- fleet console / support / diagnostics helper buttons exist

## 2. Implemented but not meaningfully visible

These items exist in code or strings, but they do not yet count as delivered UI from a real operator point of view.

### IA split is described more than it is felt
- The code and strings talk about Controls, Sensors, Managed Devices, and Diagnostics
- But the lived UI still does not make those boundaries obvious enough at a glance
- Too much of the experience still depends on explanatory text rather than a clearly felt native structure

### Managed vs unmanaged is present, but not visually crisp enough
- Current managed fleet summary exists
- Current unmanaged candidate summaries exist
- But the operator experience still does not feel like a strong side-by-side native workspace with an obvious "these are already managed" versus "these are ready for promotion" distinction

### Promotion flow exists, but still feels like scaffolding
- shortlist -> full list -> review candidate -> template -> save exists
- But it does not yet feel like a polished first-class product workflow in live HA

### Support/diagnostic helpers may be over-carrying the UX
- Several helper surfaces exist as notifications, summaries, or diagnostics text
- This makes the product feel more documented than designed
- James's success condition is visible UI clarity, not just richer support copy

## 3. Not implemented yet

These are the missing visible outcomes that prevent the requested UI from counting as done.

### A truly obvious Managed Devices landing experience
Not yet implemented well enough:
- a crisp top-level native managed-devices workspace that clearly separates:
  - already managed devices
  - unmanaged candidates ready for promotion
- an at-a-glance operator view that answers:
  - what is already in the fleet?
  - what is not in the fleet yet?
  - what should I promote next?

### A visibly strong promotion / vet / review path
Not yet implemented well enough:
- a promotion path that feels obvious and productized rather than step-fragmented
- clearer candidate quality signalling
- clearer post-vetting handoff into managed fleet state

### A truly clear four-bucket native IA
Not yet implemented well enough:
- Controls must feel like controller brain/settings only
- Sensors must feel like telemetry/source health only
- Managed Devices must feel like fleet ownership only
- Diagnostics must feel like troubleshooting/support only

Right now that separation is partially coded, but not clearly realized enough in live UI.

### Screenshot-grade proof
Not yet implemented:
- live screenshot evidence showing the requested UI outcome clearly
- release acceptance tied to what James can see in HA, not what the repo suggests

## 4. Must be in the 0.1.83 UI-complete milestone

`0.1.83` should not be called the UI release unless all of the following are true.

### A. Managed vs unmanaged is visually obvious
Required outcome:
- the Managed Devices native path clearly shows:
  - devices already managed by Zero Net Export
  - unmanaged candidates available for promotion
- this must be obvious without relying on long explanatory paragraphs

### B. Promotion / vet / review is visibly first-class
Required outcome:
- the native add/promote flow clearly supports:
  - choose candidate
  - review candidate
  - understand fit/warnings
  - promote into managed fleet
- the operator should not have to mentally stitch together multiple helper texts to understand what to do

### C. Controls / Sensors / Managed Devices / Diagnostics are clearly separated
Required outcome:
- each section has one clear ownership boundary
- there is minimal duplication/leakage across those four areas
- the UI makes it obvious where to go for each job

### D. The result is visible in live Home Assistant
Required outcome:
- James can inspect the live HA UI and see the intended improvement directly
- the release cannot be called complete based only on repo code, strings, or internal reasoning

## 5. Non-goals for 0.1.83 unless required for loading

These should not take priority over the UI release goal unless they are required to keep the integration alive:
- additional release-plumbing polish
- optional dashboard polish beyond what is needed for debug visibility
- more support text that does not improve visible operator clarity
- backend reshuffling that does not materially improve the requested native UI outcomes

## 6. Working rule for future progress reports

Do not count any item as UI progress unless it falls into one of these buckets:
- **already visible now**
- **implemented but not meaningfully visible**
- **not implemented yet**
- **must be in the 0.1.83 UI-complete milestone**

Do not let text-heavy guidance, diagnostics wording, or release plumbing masquerade as delivered UI.
