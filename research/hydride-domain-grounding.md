# Hydride Domain Grounding: Storage Targets, Hydride Physics, ML Methodology and Informatics

**Scope.** Literature grounding for the `materials-science-specialist` Claude Skill in this repo, covering the
four areas its modules assert but do not currently cite: (1) hydrogen storage fundamentals and DOE targets,
(2) metal hydride families, thermodynamics and kinetics, (3) machine learning for hydride / materials property
prediction, and (4) computational materials informatics. Generative AI and inverse design are deliberately
**out of scope** here — they are covered in `research/inverse-design-methods.md` and cross-referenced.

**Status:** research memo, in progress. Written 2026-08-29. Every factual claim links to a primary source
(peer-reviewed paper with DOI, official documentation, or an official database/API response). Claims that
could not be verified are marked **unverified**. Numbers carried into the skill modules without citation are
explicitly marked **CONFIRMED**, **CORRECTED** or **UNVERIFIED** against what was found.

---

## 1. Hydrogen storage fundamentals and DOE targets

*(Sections 1, 3 and 4 were written in the main session after the background research agent failed three times —
twice on server errors, once on a session rate limit. They rest on fewer searches than §2 and lean partly on
citations already verified in `research/inverse-design-methods.md`. Provenance is marked per claim.)*

### 1.1 The system-vs-material distinction

DOE targets are **system-level**. The primary page states targets are "for a complete system, including tank,
material, valves, regulators, piping, mounting brackets, insulation, added cooling capacity, and all other
balance-of-plant components"
([DOE EERE, accessed 2026-08-29](https://www.energy.gov/eere/fuelcells/doe-technical-targets-onboard-hydrogen-storage-light-duty-vehicles)).

**A 7 wt% material therefore does not meet a 5.5 wt% system target.** Tank, heat exchanger and balance of plant
typically cost a factor of ~2 or worse in gravimetric terms. This project predicts *material* capacity —
specifically `H2_W% (max)`, which per §2.0 is maximum measured capacity, not even reversible capacity. Comparing
its outputs to DOE system targets without stating that is a two-step overstatement.

### 1.2 The targets

Verified against the primary EERE page on 2026-08-29.

| Parameter | 2025 | Ultimate Full Fleet |
|---|---|---|
| System gravimetric | 1.8 kWh/kg (0.055 kg H2/kg, 5.5 wt%) | 2.2 kWh/kg (0.065 kg H2/kg, 6.5 wt%) |
| System volumetric | 1.3 kWh/L (0.040 kg H2/L) | 1.7 kWh/L (0.050 kg H2/L) |
| Storage system cost | $9/kWh net ($300/kg H2) | $8/kWh net ($266/kg H2) |
| Operating ambient temp | −40 to +60 °C (full solar load) | same |
| Min/max delivery temp | −40 to +85 °C | same |
| Operating pressure | 5–12 bar (absolute) | same |
| Fill time | 3–5 min | same |
| Cycle life | 1,500 cycles (1/4 to full) | same |

Onboard capacities of **5–13 kg H2** cover the light-duty platform range. Targets are set through the U.S. DRIVE
Partnership (DOE, USCAR, energy and utility companies).

**Revision date: NOT FOUND — unresolved.** The EERE page does not state an adoption or revision date, and I could
not locate one. **Cite the page with an access date, never a year.** The `targets_onboard_hydro_storage_explanation.pdf`
linked from that page is the place to look next.

**The operating window disqualifies materials independently of capacity.** A hydride that only desorbs usefully
above 85 °C, or cannot deliver into 5–12 bar, fails on those rows whatever its wt%. Against §2, this excludes
MgH2 (1 bar plateau at ~300 °C) outright on thermodynamics, not on capacity. And the 1,500-cycle requirement sits
against the AB2 degradation data in §2.5 — roughly 20% capacity loss in 150 cycles.

### 1.3 Storage classes

| Class | Mechanism | Strengths | Weaknesses |
|---|---|---|---|
| Compressed gas (350/700 bar) | Physical | Mature, fast fill, ambient | Poor volumetric density, tank cost |
| Cryogenic liquid | Physical | Good density | Liquefaction energy, boil-off |
| Cryo-compressed | Physical | Best physical volumetric | Complexity, boil-off |
| Physisorption (MOFs, carbons) | Van der Waals | Fast, fully reversible | Needs cryogenic temperatures |
| **Metal hydrides** | Chemical (interstitial) | High volumetric density, low pressure, safe, near-ambient | Heavy, heat management |
| Complex hydrides | Chemical (ionic/covalent) | High gravimetric capacity | Poor reversibility and kinetics |

DOE's stated pathways: near-term 700 bar compressed with focus on cost reduction; long-term cold/cryo-compressed
and materials-based storage.

### 1.4 Why hydrides remain relevant

Intermetallic hydrides give **under 2 wt% usable** under practical pressure/temperature swings (§2.1, sourced),
so they will not win onboard light-duty storage. They remain relevant where mass is not the binding constraint:

- **Stationary storage** — volumetric density and safety dominate, mass is nearly free.
  [Wang et al. 2025, *Adv. Sci.*, technoeconomic analysis of metal hydrides for stationary storage](https://doi.org/10.1002/advs.202415736).
- **Thermal energy storage and heat pumps** — see [Nizam et al. 2026, *Asia-Pac. J. Chem. Eng.*](https://doi.org/10.1002/apj.70161)
  for Mg-based thermal storage. **The specific "156 kWh/m3, 89.4% efficiency" figure for Mg2Ni + LaNi5-type
  systems that the skill carried is UNVERIFIED** — it came from a search summary of review literature and the
  primary source was not traced. Do not use it in the thesis without tracing it.
- **Hydrogen compression** — thermally driven, no moving parts; the hysteresis of §2.4 is precisely the pressure
  swing being exploited.
- **Purification** — selective absorption.

**Framing recommendation:** anchoring the thesis to stationary and thermal applications is more defensible than
anchoring it to automotive targets this material class structurally cannot meet.

---

## 2. Metal hydride families, thermodynamics and kinetics

### 2.0 How to read the numbers in this section

Three different quantities get called "capacity" in this literature and conflating them is the most common
error in hydride introductions:

1. **Stoichiometric (theoretical) capacity** — arithmetic from the fully hydrided formula unit. Exact, and
   exactly as useful as arithmetic ever is. Where a stoichiometric figure below is my own arithmetic rather
   than a quoted literature value, it is labelled *(stoichiometric arithmetic)*.
2. **Maximum measured capacity** — what a PCT isotherm reaches at high pressure. Usually below (1).
3. **Reversible / effective capacity** — what cycles between a practical pair of pressures at a practical
   temperature. This is what matters for a device, and it can be *half* of (2) — vanadium is the extreme case.

**This project's target variable is `H2_W% (max)`, i.e. closest to (2), not (3).** That is worth saying in the
thesis, because a reader who assumes (3) will think the model's predictions are optimistic by roughly 2x.

### 2.1 Intermetallic families

**A** is the hydride-forming element (stable binary hydride), **B** the non-forming element that destabilises
the hydride toward useful pressures — Miedema's *rule of reversed stability*, cited for a different purpose in
[`research/inverse-design-methods.md` §5.1](inverse-design-methods.md).

| Family | Prototype | Capacity (wt% H2) | dH (kJ/mol H2) | Plateau / operating window | Source |
|---|---|---|---|---|---|
| AB5 | LaNi5 | **1.2** reported; **1.38 stoichiometric** for LaNi5H6 *(arithmetic)* | **−30.8** | ~1 MPa absorption at 25 °C | [Modi & Aguey-Zinsou 2021](https://doi.org/10.3389/fenrg.2021.616115) |
| AB2 (C14/C15 Laves) | TiMn2, ZrMn2 | **1.77** max at 10 °C for a Zr-substituted C14 TiMn2; **1.34–1.40** retained over 150 cycles | **−28.7** (TiMn1.5); ZrMn2-based systems **≈ −24 to −41** | Plateau spans **8 to >90 bar at 25 °C** across the Zr-content range; TiMn2-based desorption pressure is >2 orders of magnitude above ZrMn2-based | [Modi & Aguey-Zinsou 2021](https://doi.org/10.3389/fenrg.2021.616115); [Zr-substituted TiMn2 study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12347593/); [Laves-phase review, *J. Alloys Compd.* 2022](https://doi.org/10.1016/j.jallcom.2022.165219) |
| AB | TiFe | **1.9** reported; **1.91 stoichiometric** for TiFeH2 *(arithmetic)* | **−28.1** | ≥1 MPa absorption / ≤0.7 MPa desorption at 40 °C | [Modi & Aguey-Zinsou 2021](https://doi.org/10.3389/fenrg.2021.616115); discovery paper [Reilly & Wiswall 1974](https://doi.org/10.1021/ic50131a042) |
| A2B | Mg2Ni | **3.6** | **−64.4 ± 4.2** (desorption) | 1 bar at **≈240 °C**; original synthesis 325 °C / 21 bar | [Reilly & Wiswall 1968](https://doi.org/10.1021/ic50069a016); [Dornheim 2011](https://doi.org/10.5772/21662) |
| BCC solid solution | Ti–V–Cr, V-based | **~4 total**; **1.9–2.3 reversible** | V monohydride (beta) too stable to desorb under moderate conditions | 0.1–1 MPa near room temperature | [Nakamura et al. 2003](https://doi.org/10.1016/S0925-8388(02)00831-9); [Yartys et al. 2005](https://doi.org/10.1016/j.jallcom.2005.01.139) |
| HEA / MEA | TiVZrNbHf | **H/M = 2.5** — above every constituent metal | — | — | [Sahlberg et al. 2016, *Sci. Rep.* 6, 36770](https://doi.org/10.1038/srep36770) |

**Verdict on the carried-over intermetallic numbers:**

- **AB5 ~1.4 wt% — CONFIRMED as stoichiometric, but qualify it.** LaNi5H6 is 1.38 wt% by arithmetic
  (La 138.905 + 5 x 58.693 = 432.37 g/mol; 6 H = 6.048 g/mol). The *measured* figure in
  [Modi & Aguey-Zinsou (2021)](https://doi.org/10.3389/fenrg.2021.616115) is **1.2 wt%**. Quote 1.4 as
  theoretical and ~1.2 as practical; do not quote 1.4 as if it were deliverable.
- **AB2 ~1.8–2 wt% — CONFIRMED at the top of its range, optimistic as a central value.** The best-documented
  recent C14 TiMn2 figure is **1.77 wt% maximum at 10 °C**, with **1.34–1.40 wt% surviving 150 cycles**
  ([study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12347593/)). "~1.8 wt% maximum, ~1.4 wt% cyclable" is the
  honest phrasing.
- **TiFe ~1.9 wt% — CONFIRMED.** Reported value and TiFeH2 arithmetic (2.016 / 105.73 = 1.91 wt%) agree.
- **Mg2Ni ~3.6 wt% — CONFIRMED**, traceable to the original [Reilly & Wiswall (1968)](https://doi.org/10.1021/ic50069a016).
- **BCC ~3 wt% (reversible ~2) — CORRECTED.** Total capacity is better stated as **~4 wt%** (V and Ti are
  mutually soluble in all proportions, giving close to 4 wt%), with the **reversible part 1.9–2.3 wt%**. The
  reason is specific and belongs in the skill: V-based BCC alloys hydride in two steps, and it is the
  **monohydride (VH / V2H, beta phase) that is too thermodynamically stable to desorb** under moderate
  conditions, so only the VH to VH2 half is usable
  ([Nakamura et al. 2003](https://doi.org/10.1016/S0925-8388(02)00831-9);
  [Yartys et al. 2005](https://doi.org/10.1016/j.jallcom.2005.01.139)). The carried "~3 wt%" understated the
  total and omitted the mechanism.
- **HEA ">3 wt% saturation, H/M > 2" — PARTIALLY CONFIRMED.** The claim to cite is
  [Sahlberg et al. (2016)](https://doi.org/10.1038/srep36770): TiVZrNbHf reaches **H/M = 2.5**, attributed to
  lattice strain making both tetrahedral *and* octahedral interstitial sites favourable. H/M = 2.5 exceeding
  the H/M = 2 ceiling of ordinary BCC dihydrides is the actual novelty. I found **no single primary value**
  for a general "HEA hydride" gravimetric capacity — treat any one number there as **unverified**.

### 2.2 Mg-based and complex hydrides

| Material | Theoretical wt% H2 | dH (kJ/mol H2) | Practical reality | Source |
|---|---|---|---|---|
| MgH2 | **7.66** *(arithmetic: 2.016 / 26.32)* | **−74.5** measured; **−78** in review | 1 bar plateau at **≈300 °C** | [Stampfer, Holley & Suttle 1960, *JACS* 82, 3504](https://doi.org/10.1021/ja01499a006); [Dornheim 2011](https://doi.org/10.5772/21662) |
| NaAlH4 | **5.6** over the two reversible steps (7.5 counting the NaH step, which needs >400 °C) | — | **4.5 wt%** actually cycled with a few mol% Ti dopant; desorption onsets cut to 100 °C and 185 °C | [Bogdanović & Schwickardi 1997, *J. Alloys Compd.* 253–254, 1](https://doi.org/10.1016/S0925-8388(96)03049-6) |
| LiBH4 | **18.5** total H content; **~13.8** releasable | — | LiH is stable to ~900 °C, so the last quarter of the hydrogen is inaccessible | [Züttel et al. 2003, *J. Power Sources* 118, 1](https://doi.org/10.1016/S0378-7753(03)00054-5) |
| Mg(BH4)2 | **14.9** *(arithmetic: 8.064 / 53.99)* | ~−40 for decomposition — **unverified**, review-summary only | Onset ~270 °C; stable [B12H12]2− intermediate above 400 °C blocks rehydrogenation | [Mg(BH4)2 review](https://www.sciencedirect.com/science/article/abs/pii/S1005030223003663) — publisher blocked retrieval, **contents unverified** |
| Li–N–H amides | **10.4** for Li3N to LiNH2 + 2LiH; **6.5** for the reversible Li2NH/LiNH2 step *(both arithmetic)* | — | Ammonia release poisons PEM fuel cells; the authors themselves note "the temperature required to release the hydrogen at usable pressures is too high for practical application of the present material" | [Chen, Xiong, Luo, Lin & Tan 2002, *Nature* 420, 302](https://doi.org/10.1038/nature01210) |

**Verdict on the carried-over complex-hydride numbers:**

- **MgH2 7.6 wt% theoretical — CONFIRMED** (7.66 by arithmetic).
- **MgH2 dH ≈ −75 kJ/mol H2 — CONFIRMED**, primary source [Stampfer et al. 1960](https://doi.org/10.1021/ja01499a006)
  (−74.5 kJ/mol H2). Review literature also quotes **−78** ([Dornheim 2011](https://doi.org/10.5772/21662));
  the honest range is −74 to −78 and any thesis number should name its source.
- **MgH2 ~300 °C for 1 bar — CONFIRMED.** [Dornheim (2011)](https://doi.org/10.5772/21662): "pure MgH2
  exhibits a hydrogen plateau pressure of 1 bar around 300 °C".
- **NaAlH4 5.6 wt% theoretical — CONFIRMED**, with the sourced qualifier that only **4.5 wt%** was actually
  cycled in the founding Ti-doping work ([Bogdanović & Schwickardi 1997](https://doi.org/10.1016/S0925-8388(96)03049-6)).
- **LiBH4 ~18 wt% theoretical — CONFIRMED but MISLEADING AS STATED.** 18.5 wt% is total hydrogen content;
  **13.8 wt% is the maximum desorbable**, because LiH does not decompose below ~900 °C
  ([Züttel et al. 2003](https://doi.org/10.1016/S0378-7753(03)00054-5)). The skill's existing guard rail
  ("do not quote 18 wt% as if it were deliverable") is correct — this is the citation for it.

### 2.3 Thermodynamics: PCT isotherms and the van 't Hoff relation

A pressure–composition–temperature (PCT/PCI) isotherm is the primary characterisation: rising alpha
solid-solution branch, a **flat plateau** where alpha and beta hydride coexist (flat by the Gibbs phase rule —
at fixed temperature a two-phase binary equilibrium leaves no remaining degree of freedom in pressure), then a
steeply rising beta branch.

The plateau pressure's temperature dependence gives the thermodynamics. In the form used by
[Modi & Aguey-Zinsou (2021)](https://doi.org/10.3389/fenrg.2021.616115):

```
ln(P_eq) = −dH/(R*T) + dS/R
```

Equivalently, with the sign convention used in the skill module and by
[Dornheim (2011)](https://doi.org/10.5772/21662), whose Eq. 16 reads `0.5 * ln(p/p0) = dH/RT − dS/R` —
**note the factor of one half**, which appears when dH and dS are quoted per mole of *H* rather than per mole
of *H2*. Sign and per-mole conventions are the single most common source of confusion when comparing
literature values; always check which one a quoted number uses.

**Extraction from data:** measure PCT isotherms at three or more temperatures, read the mid-plateau pressure
from each, plot `ln P` against `1/T`. Slope = dH/R, intercept = −dS/R. Absorption and desorption plateaus give
*different* lines because of hysteresis (§2.4), so always state which branch a quoted dH came from —
desorption is the convention for storage applications.

#### The near-constant dS ≈ −130 J/(mol H2 K) — CONFIRMED, with an important caveat

[Modi & Aguey-Zinsou (2021)](https://doi.org/10.3389/fenrg.2021.616115) state it directly: *"for metallic
hydrides this value is ~130 J mol−1K−1 H2"*. The physical reason is that the entropy change is dominated by
the destruction of gas-phase H2 translational entropy, so dS_f ≈ −S°(H2) = −130.7 J/(mol K) at 298 K and
0.1 MPa, essentially independent of which metal is absorbing.

**The caveat the skill should carry:** this is an approximation, not a law, and individual families deviate
enough to matter. LaNi5 illustrates it. Taking the sourced dH = −30.8 kJ/mol H2 and solving van 't Hoff for a
1-bar plateau at 298 K requires dS ≈ −103 J/(mol H2 K), not −130; with dS = −130 the predicted 298 K plateau
would be of order 0.1 bar rather than the ~1 MPa absorption pressure LaNi5 actually shows. Reported LaNi5
entropies cluster near **−108 J/(mol H2 K)** (**unverified** — I could not retrieve a primary tabulation;
Sandrock's [1999 panoramic overview](https://doi.org/10.1016/S0925-8388(99)00384-9) is the standard table to
check, and its full text was not retrievable here). A dedicated study of the constancy assumption exists
([*Int. J. Hydrogen Energy* 46, 2306–2311](https://doi.org/10.1016/j.ijhydene.2020.10.029) — DOI verified via
Crossref; full text paywalled, so its **conclusions are unverified**). Practical guidance: **−130 J/(mol H2 K)
is fine for a first-pass screen and wrong at the tens-of-percent level for any specific alloy.**

#### The dH ≈ −39 kJ/mol H2 for 1 bar at 25 °C — CONFIRMED as arithmetic, not as a measurement

At equilibrium with P_eq = P0 = 1 bar, `ln(P/P0) = 0`, so `dH = T * dS`. With T = 298.15 K and
dS = −130 J/(mol H2 K), **dH = −38.8 kJ/mol H2 ≈ −39**. The figure is therefore a direct consequence of the
entropy constant above and inherits all of its caveat. Present it as *"if you assume the universal entropy
constant, room-temperature 1-bar operation implies dH ≈ −39 kJ/mol H2"*, never as an independently measured
quantity. For context, [Dornheim (2011)](https://doi.org/10.5772/21662) gives the *design target* for
practical materials as **20–30 kJ/mol H2**, and
[Modi & Aguey-Zinsou (2021)](https://doi.org/10.3389/fenrg.2021.616115) give a desirable bond-strength window
of **−10 to −60 kJ/mol H2** for room-temperature uptake and release. Those tighter windows exist because a
real device needs a pressure *swing* between two temperatures, not a single 1-bar equilibrium point.

#### Carried-over dH-by-family values — verdict

| Carried value | Verdict | Sourced value |
|---|---|---|
| AB5 ≈ −30 | **CONFIRMED** | −30.8 ([Modi & Aguey-Zinsou 2021](https://doi.org/10.3389/fenrg.2021.616115)) |
| AB2 −28 to −35 | **CORRECTED — range is wider** | TiMn1.5 −28.7; ZrMn2-based systems span **≈ −24 to −41**. Use −24 to −41 for the family, since ZrMn2 substitution is precisely how AB2 plateau pressure is tuned ([Laves review](https://doi.org/10.1016/j.jallcom.2022.165219)) |
| TiFe ≈ −28 | **CONFIRMED** | −28.1 ([Modi & Aguey-Zinsou 2021](https://doi.org/10.3389/fenrg.2021.616115)) |
| Mg2Ni ≈ −64 | **CONFIRMED** | −64.4 ± 4.2 desorption ([Reilly & Wiswall 1968](https://doi.org/10.1021/ic50069a016)); [Dornheim](https://doi.org/10.5772/21662) quotes 67 |
| MgH2 ≈ −75 | **CONFIRMED** | −74.5 ([Stampfer et al. 1960](https://doi.org/10.1021/ja01499a006)); −78 in [Dornheim](https://doi.org/10.5772/21662) |

### 2.4 Hysteresis and plateau slope — physical origin

**Hysteresis.** The absorption plateau always sits *above* the desorption plateau; the loop does not close and
the enclosed area is irreversible work lost per cycle. The dominant explanation is **plastic deformation**:
the alpha-to-beta transformation involves a large volume expansion, coherency stresses exceed the yield
strength, and dislocations are generated during *both* hydride formation and decomposition. The quantitative
dislocation-production model is [Flanagan & Oates, *J. Less-Common Metals* 83, 127 (1982)](https://doi.org/10.1016/0022-5088(82)90176-X).
The honest state of the field comes from their own review: although plastic deformation is accepted as a
contributor, no existing theory accounts for the complete range of experimentally observed behaviour
([*Int. J. Hydrogen Energy* 13, 25–35 (1988)](https://doi.org/10.1016/0360-3199(88)90006-7)). Hysteresis is
also a clean textbook illustration of entropy production
([*J. Chem. Educ.* 64, 944](https://doi.org/10.1021/ed064p944)).

Concrete magnitude: TiFe shows ≥1 MPa absorption against ≤0.7 MPa desorption at 40 °C
([Modi & Aguey-Zinsou 2021](https://doi.org/10.3389/fenrg.2021.616115)) — about a 1.4x pressure ratio, which
is not small when the pressure swing is the thing doing useful work in a compressor or heat pump.

**Plateau slope.** A sloping rather than flat plateau means the material is not a single homogeneous phase at
a single equilibrium: compositional inhomogeneity (segregation, incomplete annealing, multi-phase
microstructure) makes different microscopic regions plateau at different pressures, and the macroscopic
isotherm is their superposition. Multi-element alloys — every HEA and every BCC solid solution in this
project's dataset — are intrinsically prone to it.

**Practical consequence for this project:** a sloping plateau makes "the capacity" ambiguous, because measured
wt% then depends strongly on the upper pressure of the measurement. Since the dataset carries temperature but
**not pressure**, sloping-plateau materials are a structural source of label noise. That is a defensible,
physics-grounded explanation for part of what CleanLab is detecting — and a better one than "some experiments
are just wrong".

### 2.5 Kinetics, activation and degradation

**Activation.** A freshly prepared alloy carries a passivating oxide and generally does not absorb hydrogen at
ambient conditions; TiFe is the canonical hard case
([Modi & Aguey-Zinsou 2021](https://doi.org/10.3389/fenrg.2021.616115): *"freshly prepared alloy does not
absorb hydrogen at ambient conditions"*). The conventional TiFe route is heating to roughly 400 °C under
hydrogen pressure. The mechanism is now understood as hydrogen uptake by a **Ti4Fe2O(1−x)** oxide on the TiFe
surface, cracking of that oxide, crack propagation into the matrix, and only then bulk absorption; the
air-exposed oxygen-rich film has been measured at ~20–30 nm. Severe plastic deformation (high-pressure
torsion, ball milling) and substitution (Mn, Zr, O) are the standard mitigations. These statements come from
[Dematteis et al., *Mater. Adv.* 2, 2524–2560 (2021)](https://doi.org/10.1039/D1MA00101A) — DOI verified via
Crossref, but **the publisher blocked automated full-text retrieval, so the specific numbers in this paragraph
are carried from a search summary of that review and must be checked against the PDF before thesis use.**

**Rate-limiting steps.** The absorption path is physisorption, dissociative chemisorption at the surface,
surface penetration, diffusion through the growing hydride layer, and nucleation and growth of the beta phase.
*Any* of these can be rate-limiting depending on material, particle size, temperature and pressure, which is
why a single "kinetics" number is meaningless without stating the regime and the kinetic model used to fit it
(JMAK, contracting volume, Jander, and so on). The correct single citation for state-of-the-field claims about
hydrogen storage materials generally is
[Hirscher et al. (2020), *J. Alloys Compd.* 827, 153548](https://doi.org/10.1016/j.jallcom.2019.153548), the
IEA Hydrogen TCP Task 32 review. **The distinction the skill already makes correctly:** catalysis,
nanostructuring and ball milling change *kinetics*; they do not change bulk dH. Changing dH requires changing
the chemistry or the reaction pathway — alloying, reactive hydride composites, or nanoconfinement at a scale
where surface-energy terms stop being negligible.

**Cycling degradation and disproportionation.** Capacity fades through strain-induced defect accumulation,
particle decrepitation into fines (with the attendant packing, heat-transfer and pyrophoricity problems), and
**disproportionation** — a metastable multi-component hydride decomposing into a more stable binary hydride
plus an inert intermetallic, which is not reversible under operating conditions. The AB2 data above give the
practical scale: **1.77 wt% maximum falling to 1.34–1.40 wt% retained over 150 cycles**
([Zr-substituted TiMn2](https://pmc.ncbi.nlm.nih.gov/articles/PMC12347593/)) — roughly 20% loss in 150 cycles,
against a DOE requirement of 1,500 cycles (§1).

**Gaseous impurity poisoning.** The standard reference point is Sandrock's cycling experiments with H2
containing 300 ppm H2O, O2 or CO: H2O and O2 dissociate on the surface and build a thick passivating complex
oxide, producing continuous capacity decay with cycling, while CO blocks dissociation sites and cuts the
reaction rate. This sets the hydrogen purity a real system must be fed, and it is a genuine reason laboratory
capacities overstate deployed capacities. Carried from the same
[Dematteis et al. (2021)](https://doi.org/10.1039/D1MA00101A) review via search summary; the primary Sandrock
poisoning papers were **not retrieved**, so treat the 300 ppm figure as **unverified**.

### 2.6 Why this matters for the ML model in this repo

Three consequences worth stating in the thesis, all grounded above:

1. **The target is maximum capacity, not reversible capacity.** For the BCC/V-based entries this is roughly a
   factor-of-two overstatement of what a device would deliver (§2.1). Predicting 3.5 wt% for a V-rich
   composition is not the same as promising a 3.5 wt% tank.
2. **Missing pressure is a physics gap, not merely a missing column.** Plateau slope (§2.4) makes measured
   capacity depend on measurement pressure, especially for the multi-element alloys that dominate the modern
   part of the dataset. This is the mechanism behind the "pressure is absent from the feature set" limitation
   the skill already flags.
3. **Activation state and processing history are unobserved confounders.** A TiFe entry measured after
   high-pressure-torsion activation and one measured after conventional thermal activation can differ
   materially, and composition-based featurisation cannot tell them apart (§2.5).

---

## 3. Machine learning for hydride and materials property prediction

The governing fact: **~1,279 rows, and fewer distinct chemistries than rows** (splits are on `unique_formulae`).
Most wrong answers in this domain come from ignoring the sample size.

### 3.1 Composition-based featurisation

- **Magpie** — the standard elemental-property descriptor set
  ([Ward, Agrawal, Choudhary & Wolverton 2016, *npj Comput. Mater.* 2, 16028](https://doi.org/10.1038/npjcompumats.2016.28)).
- **matminer** — featurizer library
  ([Ward et al. 2018, *Comput. Mater. Sci.* 152, 60](https://doi.org/10.1016/j.commatsci.2018.05.018)).
- **CBFV** — composition-based feature vectors, as used in this repo (Magpie + JARVIS presets).

`avg_*`, `dev_*` and `range_*` are stoichiometry-weighted statistics over elemental properties. What they
**cannot** encode, and what belongs in the thesis limitations:

1. **No structure.** C14 vs C15 Laves polymorphs, lattice parameters, interstitial site geometry — invisible.
   Given §2.1, where AB2 plateau pressure spans 8 to >90 bar across a substitution series, this is not a
   cosmetic omission.
2. **Many-to-one.** Composition to descriptor is not invertible; this is why feature-space inverse design is
   ill-posed (`research/inverse-design-methods.md` §4.3).
3. **No processing history or activation state.** §2.5 establishes these materially change measured capacity.

### 3.2 Why gradient-boosted trees, not deep nets

Evidence, not fashion:

- [Grinsztajn, Oyallon & Varoquaux, NeurIPS 2022 Datasets & Benchmarks](https://arxiv.org/abs/2207.08815) —
  45 datasets; tree-based models remain state-of-the-art on medium-sized (~10k) tabular data even before
  counting their speed advantage, traced to differing inductive biases.
- [Dunn, Wang, Ganose, Dopp & Jain 2020, *npj Comput. Mater.* 6, 138](https://doi.org/10.1038/s41524-020-00406-3) —
  Matbench, 13 tasks spanning 312 to 132k samples; descriptor-based classical ML stays competitive below roughly
  10^4 samples, graph/deep networks pull ahead above it.
- [De Breuck, Hautier & Rignanese 2021, *npj Comput. Mater.* 7](https://doi.org/10.1038/s41524-021-00552-2) —
  MODNet, built explicitly for the small-data regime, outperforming graph networks below ~15,000 samples.

At 1,279 rows the existing CatBoost/ExtraTrees/stacking choice is correct. When asked to add a GNN, transformer
or "materials foundation model", the defensible answer is usually **no** — spend the effort on validation.

### 3.3 Validation pitfalls — the section that decides whether results survive examination

1. **Composition leakage.** Duplicate and near-duplicate formulas across train/test inflate scores. This repo
   already splits on **unique formulae**, which is better than much published hydride ML.
2. **Formula-disjoint is still interpolation.** [Li et al. 2025, *Commun. Mater.* 6, 9](https://doi.org/10.1038/s43246-024-00731-w)
   analysed 700+ OOD tasks and found heuristic split criteria "mostly test interpolation rather than true
   extrapolation".
3. **Cross-family generalisation fails — the most important result for this thesis.**
   [Beltrame, Dematteis, Stavila, Rizzi, Baricco & Palumbo 2025, *Metals* 15, 1221](https://doi.org/10.3390/met15111221)
   expanded a hydride dataset from ~400 to 806 entries and found high accuracy **only when training and testing
   within one hydride family** (e.g. AB2), with limited generalisability across material classes; augmentation
   helped only on the smallest datasets and not in underrepresented pressure regimes.
   → **Report leave-one-alloy-class-out CV alongside random-split R2, and expect it to be much worse.**
   Method: [Durdy et al. 2022, *Digital Discovery* 1, 763](https://doi.org/10.1039/d2dd00039c) (leave-one-cluster-out).
4. **Selection and tuning inside the CV loop.** Boruta, SHAP and VIF selection run on the full training set
   before splitting leaks information. Nested CV, or an explicit statement of what was done and what it costs.
5. **Small-test-set variance.** At n=239 a test R2 of 0.916 carries a wide interval. Bootstrap it; do not report
   a bare point estimate.
6. **Tuning against the test set.** Reporting the best of 13 models x 100 Optuna trials by *test* score converts
   the test set into a validation set. Select on validation; touch test once.

### 3.4 Label noise, and a physics-grounded reason for it

Confident learning ([Northcutt, Jiang & Chuang 2021, *JAIR* 70, 1373](https://doi.org/10.1613/jair.1.12125))
estimates label noise and flags suspect entries; this pipeline uses CleanLab to drop ~10 train / 5 val / 8 test
samples.

**§2.4 supplies a physical explanation the thesis can use:** sloping plateaus make measured capacity depend on
the measurement's upper pressure, and the dataset carries temperature but not pressure. Multi-element alloys —
every HEA and BCC solid solution in the data — are intrinsically prone to sloping plateaus. That is a far
stronger account of what CleanLab detects than "some experiments are wrong".

Counter-caution: removing "outliers" that are real measurements in underrepresented regimes flatters metrics
while degrading the model where it matters. State what was removed and why.

### 3.5 Uncertainty and applicability domain

- **Conformal prediction** — distribution-free finite-sample coverage on any point model
  ([Angelopoulos & Bates 2023, *Found. Trends Mach. Learn.* 16, 494](https://doi.org/10.1561/2200000101));
  [MAPIE](https://github.com/scikit-learn-contrib/MAPIE), [crepes](https://pypi.org/project/crepes/).
- **CatBoost native** — `RMSEWithUncertainty`, `MultiQuantile`, virtual ensembles
  ([docs](https://catboost.ai/docs/en/concepts/loss-functions-regression)).
- **NGBoost** — [Duan et al., ICML 2020](https://proceedings.mlr.press/v119/duan20a.html).
- **Applicability domain** — Element Mover's Distance ([ElMD](https://github.com/lrcfmd/ElMD));
  [DiSCoVeR, Baird, Diep & Sparks 2022, *Digital Discovery* 1, 226](https://doi.org/10.1039/d1dd00028d)
  trades predicted performance against chemical novelty explicitly.

### 3.6 Published ML-on-hydride work

Dataset sizes here are small; say so rather than implying otherwise.

- **HyStor** — 1,282 metal alloys with maximum capacity at a given absorption temperature; 54 elements,
  200–800 K; curated HydPARK (831 entries) plus 451 compositions from articles and patents; adds LEA/MEA/HEA
  classes ([Wilson et al. 2024, *Int. J. Hydrogen Energy*](https://doi.org/10.1016/j.ijhydene.2024.09.390);
  [preprint](https://chemrxiv.org/doi/pdf/10.26434/chemrxiv-2024-6zkm0)).
- **ML-HydPARK** — cleaned CSV derived from DOE HydPARK ([Zenodo](https://zenodo.org/records/7324809)).
- [FIND platform, Lu et al. 2025, *J. Mater. Inform.*](https://doi.org/10.20517/jmi.2025.56) — ~6,000 records,
  VAE plus genetic algorithm.
- [Machine learning-driven alloy digital design for hydrogen storage: a review, 2025](https://doi.org/10.1080/27525783.2025.2511889).

A test R2 near 0.9 on a formula-disjoint split is a good result at this scale — but it is a statement about
interpolation within the sampled chemical space and must be presented as such.

---

## 4. Computational materials informatics

### 4.1 Databases

**Hydrogen-specific** — see §3.6 for HyStor / HydPARK / ML-HydPARK detail. The structural point worth carrying:
**HydPARK's last update was 2002**, which is why data scarcity in this field is systemic rather than incidental,
and why 1,279 rows is a normal-sized hydride dataset rather than an unusually small one.

**General DFT databases.** Entry counts are contested and drift. A Graph-ID linking study reports Materials
Project ~186,743, OQMD ~1,593,781 and AFLOW ~1,369,252 unique entries, while OQMD's own reflections paper
discusses [one million compounds](https://doi.org/10.1088/2515-7639/ac7ba9) and a 2026 source describes OQMD as
aggregating DFT results on over 600,000 compounds.

**These numbers are UNVERIFIED against the providers directly** — I did not query each database's own API, and
the sources disagree by close to an order of magnitude for OQMD. **Quote a count only with its source and date,
or better, query the provider at the time of writing.** The re-verification the failed agent was asked to do
remains outstanding.

- **Materials Project** — RESTful API, JSON datasets; `mp-api` / pymatgen client.
- **OQMD**, **AFLOW**, **NOMAD** — high-throughput DFT at scale.
- **OPTIMADE** — common API spec across providers
  ([paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8361091/),
  [providers dashboard](https://www.optimade.org/providers-dashboard/)). Prefer this to one client per database.

**Cross-database consistency is not a given.**
[Quantifying uncertainty in high-throughput DFT: a comparison of AFLOW, Materials Project and OQMD,
*Phys. Rev. Materials* 7, 053805](https://doi.org/10.1103/PhysRevMaterials.7.053805) compares them directly.
Do not pool values across databases without addressing this.

### 4.2 DFT for hydride formation enthalpy, and why it is not experiment

Workflow: structure, relaxation, total energies of metal / hydride / H2, formation enthalpy, optionally phonons
for zero-point and finite-temperature corrections.

Why DFT-computed and experimentally-measured quantities are **not interchangeable**:

1. **DFT gives one ordered structure at 0 K.** Experiment measures a real, often multiphase, defected sample at
   finite temperature and finite pressure. §2.4's plateau-slope discussion is exactly this gap made visible.
2. **Zero-point energy is not negligible for hydrogen.** H is the lightest element; ZPE corrections materially
   shift hydride formation enthalpies, and omitting them is a standard error.
3. **Functional dependence.** GGA/PBE errors on the H2 molecule and on metal–hydrogen bonding are systematic.
4. **Theoretical vs usable capacity again.** DFT naturally reports full stoichiometric occupancy — quantity (1)
   in §2.0. Experiment reports (2) or (3). LiBH4's 18.5 vs 13.8 vs deliverable is the cautionary case.

A DFT formation enthalpy is a good **screening signal** and a good physics cross-check on ML predictions. It is
not a label to mix into an experimental training set without saying so.

**Caveat on this subsection: written from domain knowledge, not from a retrieved primary source.** The claims are
standard, but each deserves a citation before thesis use. This is the least-sourced part of the memo.

### 4.3 Active learning

Bayesian optimization with a GP surrogate works from tens of points and is built for this regime — but it pays
off **only if experiments will actually be run**. In a computational-only thesis it is a chapter about a loop
that never closes. Cross-reference `research/inverse-design-methods.md` §3.3 and §4.4.

### 4.4 Tooling and reproducibility

- **pymatgen** — structures, composition parsing, database clients.
- **matminer** — featurizers ([Ward et al. 2018](https://doi.org/10.1016/j.commatsci.2018.05.018)).
- **ASE** — atomistic simulation environment.
- **atomate2 / jobflow** — reproducible high-throughput DFT workflows.
- [Abraham et al. 2026, *WIREs Comput. Mol. Sci.*, ML toolkits and frameworks for materials design](https://doi.org/10.1002/wcms.70067) — landscape review.

**Provenance discipline:** pin package versions; record which database snapshot and which date; keep the fitted
scaler (`RobustScaler`) and the 22-feature list as artefacts rather than things to be recomputed. This repo's
habit of writing each stage's output to `Machine_Model/reports/` is the right instinct — every number in
`REPORT.md` traces to the run that produced it.

---

## 5. Status, provenance and what is still open

**How this memo was produced.** §2 was written by a dedicated background research agent that verified claims
against retrieved primary sources; it is the most rigorous section and its CONFIRMED/CORRECTED verdicts are
trustworthy. §§1, 3, 4 were written in the main session after that agent failed three times (two server errors,
one session rate limit), and rest on fewer searches. §4.2 in particular is domain knowledge, not retrieved
sources, and is flagged as such.

**Corrections this memo makes to the skill modules** (all from §2, all sourced):

| Claim as carried | Corrected to |
|---|---|
| BCC solid solution ~3 wt%, reversible ~2 | **~4 wt% total, 1.9–2.3 reversible**; mechanism is the too-stable V monohydride, only VH→VH2 is usable |
| AB2 dH −28 to −35 | **−24 to −41** across the ZrMn2 substitution range |
| AB5 ~1.4 wt% | 1.38 **stoichiometric**, **1.2 measured** — do not present 1.4 as deliverable |
| AB2 ~1.8–2 wt% | **1.77 max, 1.34–1.40 after 150 cycles** |
| LiBH4 ~18 wt% | 18.5 total, **13.8 maximum desorbable** (LiH stable to ~900 °C) |
| dS ≈ −130 J/(mol H2 K) as a constant | Confirmed as an approximation; **LaNi5 needs ≈ −103 to −108** to reproduce its observed plateau. Wrong at the tens-of-percent level for a specific alloy |
| dH ≈ −39 kJ/mol H2 | Confirmed as **arithmetic consequence** of the entropy constant, not a measurement. Practical design windows are tighter: 20–30, or −10 to −60 |

**Still open:**

1. **DOE target revision date** — not stated on the EERE page; not found. Check `targets_onboard_hydro_storage_explanation.pdf`.
2. **The 156 kWh/m3 / 89.4% Mg2Ni+LaNi5 thermal-storage figure** — unverified, search-summary only. Trace or drop.
3. **Database entry counts** — unverified against providers; sources disagree by ~an order of magnitude for OQMD.
4. **LaNi5 entropy tabulation** — Sandrock's [1999 panoramic overview](https://doi.org/10.1016/S0925-8388(99)00384-9) is the standard table; full text not retrieved.
5. **Dematteis et al. 2021 numbers** (TiFe oxide thickness ~20–30 nm, activation mechanism) and **Sandrock's 300 ppm poisoning experiments** — carried from search summaries of a review whose full text was publisher-blocked. Check against the PDF.
6. **§4.2 DFT claims** — standard but uncited.
7. **§§1, 3, 4 generally** would benefit from the same agent treatment §2 received.
