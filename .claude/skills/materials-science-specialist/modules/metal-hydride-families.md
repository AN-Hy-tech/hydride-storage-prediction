# Metal Hydride Families, Thermodynamics and Kinetics

**Confidence**: 🟡 Medium. Family/thermodynamics content is textbook-stable; specific numeric ranges below are
indicative and should be checked against a primary source before being quoted in the thesis.

## Intermetallic families

Named by stoichiometry, where **A** is the hydride-forming (stable-hydride) element and **B** is the
non-forming element that tunes stability downward.

| Family | Prototype | Typical capacity | Character |
|---|---|---|---|
| AB₅ | LaNi₅ | ~1.4 wt% | Easy activation, flat plateau, near-ambient, excellent cycling. The Ni-MH battery workhorse. Low capacity. |
| AB₂ (Laves) | ZrMn₂, TiMn₂ | ~1.8–2 wt% | Good cost/capacity balance; C14/C15 Laves phases; tunable over wide composition range |
| AB | TiFe | ~1.9 wt% | Cheapest; highest capacity among Ti-based intermetallics; **notoriously hard to activate**; sensitive to impurity poisoning |
| A₂B | Mg₂Ni | ~3.6 wt% | Higher capacity, but desorbs too high (~250–300 °C) |
| BCC solid solution | Ti–V–Cr | ~3 wt% (reversible often ~2) | High absolute capacity, but only part is reversible under practical conditions; V cost is the barrier |
| HEA / MEA | multi-principal | >3 wt% saturation reported, H/M > 2 | Active research area; composition-space design problem |

Usable capacities under real pressure/temperature swings are generally **< 2 wt%**, even where saturation
capacity is higher ([review, *Int. J. Hydrogen Energy*](https://www.sciencedirect.com/science/article/pii/S0360319926013236)).
Cost-effective picks like TiFe₀.₇Mn₀.₂ and TiMn₁.₉₅ sit near ~200 US$/kg H₂.

## Mg-based and complex hydrides

- **MgH₂** — ~7.6 wt% theoretical, cheap and abundant. The problem is thermodynamic, not compositional:
  ΔH ≈ −75 kJ/mol H₂ makes it far too stable, requiring ~300 °C for 1 bar desorption, with sluggish kinetics.
  Mitigations (nanostructuring, catalysis, reactive hydride composites) improve *kinetics* readily but
  **cannot change bulk ΔH** — a distinction worth being precise about.
  See [Nizam et al. 2026, *Asia-Pac. J. Chem. Eng.*, Mg-based hydrides for thermal energy storage](https://doi.org/10.1002/apj.70161).
- **Alanates** — NaAlH₄, ~5.6 wt% theoretical; Ti-catalysed reversibility was the breakthrough result, but
  multi-step decomposition means only part is practically accessible.
- **Borohydrides** — LiBH₄ (~18 wt% theoretical), Mg(BH₄)₂. Enormous gravimetric capacity, but high stability,
  very high desorption temperatures, and poor reversibility, often with B₂H₆ release.
- **Amides / Li-N-H systems** — reversible, but ammonia release is a fuel-cell poison.

**Guard rail:** theoretical capacity is not usable capacity. Do not quote 18 wt% for LiBH₄ as if it were deliverable.

## Thermodynamics

### PCT / PCI isotherms

Pressure-composition-temperature isotherms are the primary characterisation. Shape: solid-solution α-phase
(rising), **plateau** (α+β two-phase coexistence, flat by Gibbs' phase rule), then β-hydride (rising steeply).

Non-idealities that carry physical meaning:
- **Plateau slope** — compositional inhomogeneity in the alloy.
- **Hysteresis** — absorption plateau sits above desorption; attributed to lattice strain from the volume
  expansion accompanying hydride formation. Irreversible energy loss per cycle.
- **Plateau width** sets reversible capacity, which is what matters practically.

### van 't Hoff

The plateau pressure's temperature dependence gives the thermodynamics:

```
ln(P_eq / P_0) = ΔH/(R·T) − ΔS/R
```

Plot `ln P` against `1/T`; slope = ΔH/R, intercept = −ΔS/R. Because ΔS is dominated by the loss of gas-phase
H₂ entropy, it is roughly constant at **≈ −130 J/(mol H₂·K)** across most hydrides. **ΔH therefore effectively
sets the operating temperature.** For 1 bar at ~25 °C you need ΔH ≈ −39 kJ/mol H₂.

Indicative ΔH by family: AB₅ ≈ −30, AB₂ ≈ −28 to −35, TiFe ≈ −28, Mg₂Ni ≈ −64, MgH₂ ≈ −75 kJ/mol H₂.

### The central tradeoff

Light elements give high gravimetric capacity but form *too-stable* hydrides. Stability and capacity are
coupled through chemistry, which is exactly why this is a hard multi-objective design problem and why
single-objective "maximise wt%" search returns known, thermodynamically inconvenient Mg-rich answers.
See `modules/generative-ai-inverse-design.md`.

## Kinetics and degradation

- **Activation** — initial cycles to crack the passivating oxide and open the surface. TiFe is the classic
  hard case, often needing high-temperature/high-pressure treatment.
- **Rate-limiting steps** — surface dissociation, surface penetration, hydride-layer diffusion, or nucleation
  and growth. Which one dominates depends on material and conditions; a single "kinetics" number is meaningless
  without stating the regime.
- **Cycling degradation** — capacity fade from strain-induced defects, particle decrepitation, and
  **disproportionation** (metastable phases decomposing into more stable hydride + inert intermetallic).
- **Gaseous impurity poisoning** — CO, H₂S, O₂ and H₂O degrade surfaces; a serious practical constraint since
  it dictates required hydrogen purity.

## Why temperature is a legitimate model input

`temperature(K)` is a feature in this project's dataset, and this is physically correct, not a data-leak:
**measured capacity is a function of where on the PCT surface the measurement was taken.** The same alloy
yields different wt% at different temperatures because plateau pressure shifts per van 't Hoff. The model is
learning a slice of the PCT surface, not an intrinsic material constant.

Two honest caveats for the thesis:
1. Capacity also depends on **pressure**, which the dataset does not carry as a feature. The model therefore
   marginalises over whatever pressures the source measurements used — a real, statable limitation.
2. `temperature(K)` ranks 21st of 22 by SHAP importance (0.001), which sits awkwardly against its physical
   importance. Worth investigating rather than glossing: it may reflect a narrow temperature spread within
   alloy families, or correlation with composition-derived features.

HyStor spans **200–800 K** and 54 elements, so the temperature range is wide — see `modules/computational-materials-informatics.md`.
