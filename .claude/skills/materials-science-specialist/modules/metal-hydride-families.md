# Metal Hydride Families, Thermodynamics and Kinetics

**Confidence**: Medium-high. Numbers below are sourced from `research/hydride-domain-grounding.md` §2, which
verified them against primary literature. Items still marked **unverified** there are marked here too.

## Three things called "capacity" — do not conflate them

This is the most common error in hydride introductions:

1. **Stoichiometric (theoretical)** — arithmetic from the fully hydrided formula unit.
2. **Maximum measured** — what a PCT isotherm reaches at high pressure. Usually below (1).
3. **Reversible / effective** — what cycles between practical pressures at a practical temperature. Can be
   *half* of (2); vanadium is the extreme case. This is what a device delivers.

**This project's target `H2_W% (max)` is quantity (2), not (3).** Say so in the thesis: a reader assuming (3)
will think the predictions are optimistic by roughly 2x for the V-rich compositions.

## Intermetallic families

**A** forms a stable binary hydride; **B** destabilises it toward useful pressures (Miedema's rule of reversed
stability).

| Family | Prototype | Capacity (wt%) | dH (kJ/mol H2) | Window |
|---|---|---|---|---|
| AB5 | LaNi5 | **1.2 measured**, 1.38 stoichiometric | −30.8 | ~1 MPa absorption at 25 °C |
| AB2 (C14/C15 Laves) | TiMn2, ZrMn2 | **1.77 max**, 1.34–1.40 after 150 cycles | **−24 to −41** across the ZrMn2 range | Plateau spans 8 to >90 bar at 25 °C |
| AB | TiFe | 1.9 | −28.1 | ≥1 MPa abs / ≤0.7 MPa des at 40 °C |
| A2B | Mg2Ni | 3.6 | −64.4 ± 4.2 (desorption) | 1 bar at ~240 °C |
| BCC solid solution | Ti–V–Cr | **~4 total, 1.9–2.3 reversible** | V monohydride too stable to desorb | 0.1–1 MPa near RT |
| HEA / MEA | TiVZrNbHf | **H/M = 2.5** | — | — |

Primary sources: [Modi & Aguey-Zinsou 2021](https://doi.org/10.3389/fenrg.2021.616115);
[Reilly & Wiswall 1968](https://doi.org/10.1021/ic50069a016) and [1974](https://doi.org/10.1021/ic50131a042);
[Nakamura et al. 2003](https://doi.org/10.1016/S0925-8388(02)00831-9);
[Yartys et al. 2005](https://doi.org/10.1016/j.jallcom.2005.01.139);
[Sahlberg et al. 2016](https://doi.org/10.1038/srep36770);
[Laves-phase review 2022](https://doi.org/10.1016/j.jallcom.2022.165219).

**The BCC mechanism matters and is often omitted.** V-based BCC alloys hydride in two steps, and it is the
**monohydride (VH/V2H, beta) that is too thermodynamically stable to desorb** under moderate conditions — so
only the VH→VH2 half is usable. That is why total is ~4 wt% but reversible is 1.9–2.3.

**HEA caveat:** H/M = 2.5 exceeding the H/M = 2 ceiling of ordinary BCC dihydrides is the real novelty
(attributed to lattice strain making both tetrahedral *and* octahedral sites favourable). There is **no
verified single gravimetric number** for "HEA hydrides" generally — treat any such figure as unverified.

## Mg-based and complex hydrides

| Material | Theoretical wt% | Practical reality |
|---|---|---|
| MgH2 | 7.66 | dH = **−74.5** measured (−78 in review); 1 bar plateau at ~300 °C |
| NaAlH4 | 5.6 over two reversible steps | **4.5 wt% actually cycled** with Ti dopant |
| LiBH4 | 18.5 total H | **13.8 maximum desorbable** — LiH stable to ~900 °C |
| Mg(BH4)2 | 14.9 | Onset ~270 °C; [B12H12]2− intermediate blocks rehydrogenation |
| Li–N–H | 10.4 (6.5 reversible step) | Ammonia release poisons PEM fuel cells |

Sources: [Stampfer, Holley & Suttle 1960](https://doi.org/10.1021/ja01499a006);
[Dornheim 2011](https://doi.org/10.5772/21662);
[Bogdanović & Schwickardi 1997](https://doi.org/10.1016/S0925-8388(96)03049-6);
[Züttel et al. 2003](https://doi.org/10.1016/S0378-7753(03)00054-5);
[Chen et al. 2002, *Nature* 420, 302](https://doi.org/10.1038/nature01210).

**MgH2's problem is thermodynamic, not compositional.** dH ≈ −75 kJ/mol H2 is far too stable. Nanostructuring
and catalysis improve *kinetics* readily but **cannot change bulk dH** — be precise about this distinction.

## Thermodynamics

### PCT isotherms

Rising alpha branch, **flat plateau** where alpha and beta coexist (flat by the Gibbs phase rule — at fixed
temperature a two-phase binary equilibrium leaves no pressure degree of freedom), then steep beta branch.

### van 't Hoff

```
ln(P_eq) = -dH/(R*T) + dS/R
```

Measure PCT isotherms at three or more temperatures, read mid-plateau pressure, plot `ln P` vs `1/T`.
Slope = dH/R, intercept = −dS/R. Absorption and desorption give **different lines** because of hysteresis —
always state which branch a dH came from (desorption is the storage convention).

**Watch the conventions.** Some sources write `0.5 ln(p/p0) = dH/RT − dS/R`; the factor of one half appears
when dH and dS are per mole of *H* rather than per mole of *H2*. Sign and per-mole convention are the single
most common source of confusion when comparing literature values.

### The entropy constant — approximation, not law

dS ≈ **−130 J/(mol H2 K)** because the entropy change is dominated by destroying gas-phase H2 translational
entropy, so dS ≈ −S°(H2) = −130.7 J/(mol K), nearly independent of the metal.

**But individual families deviate enough to matter.** LaNi5 with its sourced dH = −30.8 needs
dS ≈ **−103 to −108** to reproduce its observed ~1 MPa plateau at 298 K; assuming −130 would predict ~0.1 bar.
**Fine for a first-pass screen, wrong at the tens-of-percent level for a specific alloy.**
(The −108 clustering is **unverified** — [Sandrock 1999](https://doi.org/10.1016/S0925-8388(99)00384-9) is the
standard table to check.)

### The −39 kJ/mol figure is arithmetic, not a measurement

At P_eq = P0, `ln(P/P0) = 0`, so `dH = T·dS` → with 298.15 K and −130, **dH = −38.8 kJ/mol H2**. It inherits
the entropy caveat entirely. Phrase it as *"assuming the universal entropy constant, room-temperature 1-bar
operation implies dH ≈ −39"* — never as an independently measured quantity.

Real design windows are tighter, because a device needs a pressure *swing* between two temperatures, not one
equilibrium point: **20–30 kJ/mol H2** ([Dornheim](https://doi.org/10.5772/21662)), or a bond-strength window
of **−10 to −60** ([Modi & Aguey-Zinsou](https://doi.org/10.3389/fenrg.2021.616115)).

### The central tradeoff

Light elements give high gravimetric capacity but form *too-stable* hydrides. Stability and capacity are
coupled through chemistry — which is why single-objective "maximise wt%" search returns known,
thermodynamically inconvenient Mg-rich answers. See `modules/generative-ai-inverse-design.md`.

## Hysteresis and plateau slope

**Hysteresis.** Absorption plateau always sits above desorption; the enclosed area is irreversible work lost
per cycle. Dominant explanation is **plastic deformation** — the alpha→beta volume expansion drives coherency
stresses past yield, generating dislocations during both formation and decomposition
([Flanagan & Oates 1982](https://doi.org/10.1016/0022-5088(82)90176-X)). Honest state of the field: no theory
accounts for the full range of observed behaviour ([Flanagan & Oates 1988](https://doi.org/10.1016/0360-3199(88)90006-7)).
Magnitude: TiFe runs ≥1 MPa absorption against ≤0.7 MPa desorption at 40 °C — a ~1.4x ratio, not small when
the pressure swing is what does useful work in a compressor or heat pump.

**Plateau slope.** A sloping plateau means the material is not a single homogeneous phase at a single
equilibrium: compositional inhomogeneity makes different regions plateau at different pressures, and the
isotherm is their superposition. Multi-element alloys — every HEA and BCC solid solution in this dataset —
are intrinsically prone to it.

## Kinetics, activation and degradation

- **Activation.** Fresh alloy carries a passivating oxide and generally will not absorb at ambient. TiFe is the
  canonical hard case (conventionally ~400 °C under H2 pressure). Mechanism: uptake by a Ti4Fe2O(1−x) surface
  oxide, cracking, crack propagation into the matrix, then bulk absorption; air-exposed film ~20–30 nm.
  Mitigations: severe plastic deformation (HPT, ball milling), substitution (Mn, Zr, O).
  From [Dematteis et al. 2021, *Mater. Adv.* 2, 2524](https://doi.org/10.1039/D1MA00101A) — **publisher blocked
  full-text retrieval; the specific numbers are search-summary and need checking against the PDF.**
- **Rate-limiting steps.** Physisorption → dissociative chemisorption → surface penetration → diffusion through
  the growing hydride layer → nucleation and growth. *Any* can dominate depending on material, particle size,
  temperature and pressure — so a single "kinetics" number is meaningless without the regime and the kinetic
  model (JMAK, contracting volume, Jander). State-of-field reference:
  [Hirscher et al. 2020, *J. Alloys Compd.* 827, 153548](https://doi.org/10.1016/j.jallcom.2019.153548) (IEA Task 32).
- **Cycling degradation.** Strain-induced defects, decrepitation into fines (packing, heat-transfer and
  pyrophoricity problems), and **disproportionation** into a stable binary hydride plus inert intermetallic.
  Practical scale: AB2 loses ~20% in 150 cycles (1.77 → 1.34–1.40 wt%) against a DOE requirement of 1,500.
- **Impurity poisoning.** H2O and O2 dissociate and build a passivating complex oxide (continuous decay); CO
  blocks dissociation sites (rate loss). Sandrock's 300 ppm cycling experiments are the reference point —
  **unverified**, carried via search summary. This is a genuine reason lab capacities overstate deployed ones.

## Why temperature is a legitimate model input

`temperature(K)` is a feature here and that is physically correct, not leakage: **measured capacity is a
function of where on the PCT surface the measurement was taken.** The same alloy gives different wt% at
different temperatures because plateau pressure shifts per van 't Hoff. The model learns a slice of the PCT
surface, not an intrinsic constant.

Two caveats for the thesis:

1. **Pressure is absent from the features**, and plateau slope makes measured capacity depend on the
   measurement's upper pressure — especially for the multi-element alloys that dominate the modern data.
   This is a *physics gap*, not merely a missing column, and it is a defensible, grounded explanation for part
   of what CleanLab detects — better than "some experiments are wrong".
2. **Activation state and processing history are unobserved confounders.** A TiFe entry measured after
   high-pressure-torsion activation differs materially from one after conventional thermal activation, and
   composition-based featurisation cannot tell them apart.

HyStor spans **200–800 K** and 54 elements — see `modules/computational-materials-informatics.md`.
