# Reference Matrix

## Purpose

Compare the strongest discovered Home Assistant / energy-management references against the proposed **Zero Net Export** app.

---

## 1. `jmcollin78/solar_optimizer`

### Summary
A mature Home Assistant integration focused on maximizing solar self-consumption by controlling deferred and variable loads.

### What it does well
- HACS installable integration
- config UI for devices
- supports fixed loads and variable-power loads
- battery-aware inputs
- anti-flicker logic
- min on / min off rules
- daily min / max runtime concepts
- device prioritization
- optimization loop based on weighted import/export cost

### What it does not appear to solve fully
- strict zero-export / export-target control as the product identity
- operator-grade source validation and reconciliation
- mini-app style dashboard / control console
- explicit confidence and mismatch reporting
- grid-boundary-first modeling

### What to borrow
- config flow structure
- device abstraction
- battery-aware scheduling ideas
- anti-flicker / runtime guardrails
- variable-load handling
- priority handling

### What to improve
- stronger energy source validation
- better UX / operator control surface
- export-target modes
- explainable decisioning

---

## 2. `springfall2008/batpred`

### Summary
Battery prediction and charging automation / optimization for Home Assistant.

### What it does well
- optimization mindset
- battery strategy orientation
- likely useful forecasting patterns

### Relevance to Zero Net Export
- useful for future advanced strategy layer
- less relevant for the immediate HA mini-app control loop

### What to borrow
- prediction / planning concepts
- tariff-aware strategy concepts

### What not to rely on as the core product shape
- dashboard / mini-app UX
- direct zero-export device orchestration

---

## 3. `chrismelba/solar-optimiser`

### Summary
A HACS add-on described as helping optimize controlled loads, solar, and battery usage for Home Assistant.

### Value
- useful adjacent comparison
- confirms the concept space exists

### Current signal
- early / low adoption compared with Solar Optimizer
- not enough evidence yet to make it the primary benchmark

---

## 4. Dashboard Card Projects

### Examples
- `reptilex/tesla-style-solar-power-card`
- `Giorgio866/lumina-energy-card`

### What they are good for
- energy flow visualization
- dashboard ergonomics
- UI inspiration

### What they are not
- control engines
- source-validation systems
- export target controllers

---

## 5. Zero Net Export differentiation

### Existing ecosystem tends to have
- integrations
- automations
- scripts / blueprints
- cards
- battery optimizers

### Gap to fill
A cohesive Home Assistant mini app that combines:
- source validation
- export-target control
- fixed + variable device orchestration
- operator dashboard
- explainable decisions
- safety / degraded modes
- reporting

---

## Conclusion

The best direct reference is **`jmcollin78/solar_optimizer`**, but it should be treated as a **strong ancestor**, not the final shape.

**Zero Net Export** should borrow its operational maturity while differentiating on:
- export-target-first behavior
- source-of-truth validation
- operator UX
- explainability
- health / mismatch reporting
