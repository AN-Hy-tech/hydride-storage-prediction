# Hydride Domain Grounding: Storage Targets, Hydride Physics, ML Methodology and Informatics

**Scope.** Literature grounding for the `materials-science-specialist` Claude Skill in this repo, covering the
four areas its modules assert but do not currently cite: (1) hydrogen storage fundamentals and DOE targets,
(2) metal hydride families, thermodynamics and kinetics, (3) machine learning for hydride / materials property
prediction, and (4) computational materials informatics. Generative AI and inverse design are deliberately
**out of scope** here — they are covered in `research/inverse-design-methods.md` and cross-referenced.

**Status:** research memo. Written 2026-08-29; **sections 1, 3, 4 and 5 re-researched and rewritten
2026-08-30** to the standard of section 2 (see §5 for method and for the full list of corrections that pass
made). Every factual claim links to a primary source
(peer-reviewed paper with DOI, official documentation, or an official database/API response). Claims that
could not be verified are marked **unverified**. Numbers carried into the skill modules without citation are
explicitly marked **CONFIRMED**, **CORRECTED** or **UNVERIFIED** against what was found.

---

## 1. Hydrogen storage fundamentals and DOE targets

*(Re-researched 2026-08-30 against the DOE Target Explanation Document itself, which resolves the revision-date
question left open on 2026-08-29. Every number below is now traced to either the EERE target page or the TED
PDF, both accessed 2026-08-30.)*

**The primary document.** The EERE page is a summary; the authoritative source is the
[Target Explanation Document: Onboard Hydrogen Storage for Light-Duty Fuel Cell Vehicles](https://www.energy.gov/sites/prod/files/2017/05/f34/fcto_targets_onboard_hydro_storage_explanation.pdf)
(22 pp., DOE Fuel Cell Technologies Office; PDF retrieved and text-extracted 2026-08-30 — referred to below as
**TED**). It carries the target table, the derivation of every row, and the revision history. Cite the TED, not
the summary page, whenever a number is load-bearing.

### 1.1 The system-vs-material distinction

DOE targets are **system-level**. The TED states it in footnote (a) to the target table, and the EERE page
repeats it verbatim:

> "Targets are for a complete system, including tank, material, valves, regulators, piping, mounting brackets,
> insulation, added cooling capacity, and all other balance-of-plant components. All capacities are defined as
> usable capacities that could be delivered to the fuel cell system. **All targets must be met at the end of
> service life.**"
> — [TED, footnote (a) to Table 1](https://www.energy.gov/sites/prod/files/2017/05/f34/fcto_targets_onboard_hydro_storage_explanation.pdf)

Two clauses in that footnote were missing from the earlier draft and both matter:

1. **Capacities are *usable* capacities** — quantity (3) in §2.0, not (2). The target is defined against the
   hydrogen actually deliverable to the fuel cell.
2. **All targets must be met at end of service life** — i.e. after the 1,500 cycles, not on a fresh sample.
   Against §2.5's AB2 degradation data (1.77 wt% falling to 1.34–1.40 over 150 cycles) this is a far harder
   constraint than the headline wt% suggests.

**The normalisation basis — NEW, and worth carrying.** The TED specifies that comparisons to the targets be
made at a fixed capacity: *"For a normalized comparison of system performance to the targets, a usable H2
storage capacity of **5.6 kg H2** should be used at the lower heating value of hydrogen (33.3 kWh/kg H2)"*
([TED, footnote (a)](https://www.energy.gov/sites/prod/files/2017/05/f34/fcto_targets_onboard_hydro_storage_explanation.pdf)).
Any system-level comparison this thesis makes should state that it is doing so at 5.6 kg usable H2.

**A 7 wt% material therefore does not meet a 5.5 wt% system target.** This project predicts *material*
capacity — specifically `H2_W% (max)`, which per §2.0 is maximum measured capacity, not reversible capacity.
Comparing its outputs to DOE system targets without saying so is a **two-step** overstatement: material→system,
and maximum→usable.

> **CORRECTED — the "factor of ~2" balance-of-plant penalty.** The earlier draft asserted that tank, heat
> exchanger and balance of plant "typically cost a factor of ~2 or worse in gravimetric terms." **No source was
> found for that ratio and it is not stated in the TED.** It is removed as a quantitative claim. What *is*
> sourced is the direction and the definition (system includes all balance of plant; capacities are usable and
> end-of-life), which is sufficient to make the argument without a fabricated multiplier. Treat any specific
> system/material ratio as **unverified** unless taken from a named system engineering study.

### 1.2 The targets

Verified twice on 2026-08-30: against the
[EERE summary page](https://www.energy.gov/eere/fuelcells/doe-technical-targets-onboard-hydrogen-storage-light-duty-vehicles)
and against **Table 1 of the TED**, which is headed *"(updated May 2017)"*. The two agree exactly.

| Parameter | Units | 2020 | 2025 | Ultimate |
|---|---|---|---|---|
| System gravimetric capacity (usable) | kWh/kg | 1.5 | **1.8** | **2.2** |
| | (kg H2/kg system) | (0.045) | **(0.055)** | **(0.065)** |
| System volumetric capacity (usable) | kWh/L | 1.0 | **1.3** | **1.7** |
| | (kg H2/L system) | (0.030) | **(0.040)** | **(0.050)** |
| Storage system cost | $/kWh net | 10 | **9** | **8** |
| | ($/kg H2) | 333 | **300** | **266** |
| Fuel cost | $/gge at pump | 4 | 4 | 4 |
| Operating ambient temperature | °C | −40/60 (sun) | −40/60 (sun) | −40/60 (sun) |
| Min/max delivery temperature | °C | −40/85 | −40/85 | −40/85 |
| Operational cycle life (1/4 tank to full) | cycles | 1,500 | 1,500 | 1,500 |
| Min delivery pressure from storage system | bar (abs) | 5 | 5 | 5 |
| Max delivery pressure from storage system | bar (abs) | 12 | 12 | 12 |
| Onboard efficiency | % | 90 | 90 | 90 |
| "Well"-to-powerplant efficiency | % | 60 | 60 | 60 |
| System fill time | min | 3–5 | 3–5 | 3–5 |
| Minimum full flow rate | (g/s)/kW | 0.02 | 0.02 | 0.02 |
| Start time to full flow (20 °C / −20 °C) | s | 5 / 15 | 5 / 15 | 5 / 15 |
| Dormancy time (min. to first release) | days | 7 | 10 | 14 |
| Boil-off loss (max, 30 days) | % | 10 | 10 | 10 |

Source for the whole table: [TED Table 1, "updated May 2017"](https://www.energy.gov/sites/prod/files/2017/05/f34/fcto_targets_onboard_hydro_storage_explanation.pdf),
cross-checked against the [EERE page](https://www.energy.gov/eere/fuelcells/doe-technical-targets-onboard-hydrogen-storage-light-duty-vehicles) (both accessed 2026-08-30).

#### Verdict on the carried-over §1 numbers

- **2025 and Ultimate gravimetric / volumetric / cost rows — CONFIRMED.** All eight values match the TED exactly.
- **Operating and delivery temperatures, pressures, fill time, cycle life — CONFIRMED.** −40/60 °C ambient
  (full sun), −40/85 °C delivery, 5–12 bar absolute, 3–5 min, 1,500 cycles.
- **Column label "Ultimate Full Fleet" — CORRECTED to "Ultimate".** The current table's third column is headed
  simply **Ultimate**. "Ultimate Full Fleet" is the *2009* terminology: *"Note that in 2009, the targets were
  developed for 2015 and 'Ultimate Full Fleet' targets were added to capture virtually all light-duty vehicle
  platforms ('significant market penetration')"* ([TED §3.0](https://www.energy.gov/sites/prod/files/2017/05/f34/fcto_targets_onboard_hydro_storage_explanation.pdf)).
  Using the old label implies the old target set.
- **The 2020 column was missing entirely — ADDED.** The current table has three target years, not two.
- **"Onboard capacities of 5–13 kg H2" — CORRECTED to 4–10 kg.** The TED says it three separate times:
  *"Storing enough hydrogen (**4-10 kg**) onboard a light-duty vehicle to achieve a 300 to 500 mile driving
  range is a significant challenge"*; *"the fuel storage requirement varied between approximately **4 to 10 kg**"*;
  and *"approximately **4 to 10 kg** of hydrogen, based on the corresponding vehicle type (class) and expected
  driving range"* ([TED](https://www.energy.gov/sites/prod/files/2017/05/f34/fcto_targets_onboard_hydro_storage_explanation.pdf)).
  The carried "5–13 kg" appears in neither the TED nor the EERE page. **Do not use it.**

#### Revision date — RESOLVED (this was open item #1)

The TED states the full history explicitly, and it is not a single date but three:

| Event | Date | TED wording |
|---|---|---|
| Original targets set | **2003** | *"The original targets were set in 2003 based on attempting to be competitive with conventional gasoline fuel systems"* |
| Last **major** revision | **2009** | *"revised in 2009 to enable greater than 300-mile range within the allocated package space and weight"*; *"the last major target revision was completed in 2009"* |
| Current table published | **May 2017** | Table 1 is headed *"(updated May 2017)"*; §3.0 summarises *"targets that have been revised and added since the last major target update in 2009"* |

One further detail explains the odd target years: the **2015 targets were shifted to 2025**, not met and
re-dated. *"The original 2015 targets were developed based on an assumption that the DOE funding for hydrogen
storage research and development would remain fairly constant. Since 2009, funding for the DOE Hydrogen Storage
Program has been at reduced levels ... thus impacting the ability to meet the 2015 targets and shifting these
targets to 2025"*
([TED §3.0](https://www.energy.gov/sites/prod/files/2017/05/f34/fcto_targets_onboard_hydro_storage_explanation.pdf),
citing [DOE Hydrogen and Fuel Cells Program Record #16010](https://www.hydrogen.energy.gov/pdfs/16010_historical_fuel_cell_h2_budgets.pdf)).

The targets are also **not permanent**: *"It is intended that U.S. DRIVE will review and update the hydrogen
storage system targets approximately every 5 years"* and the assumptions *"will be periodically revisited
approximately every 5 years"* (TED §2.0 and §4). Targets are set through the U.S. DRIVE Partnership (DOE, USCAR,
energy and utility companies).

> **How to cite this in the thesis.** *"DOE technical targets for onboard hydrogen storage, table updated May
> 2017, last major revision 2009 (DOE Fuel Cell Technologies Office, Target Explanation Document; accessed
> 2026-08-30)."* The earlier instruction to "cite with an access date, never a year" can now be relaxed: there
> **is** a defensible date to give, provided you say which of the three you mean. Keep the access date anyway,
> because the 5-year review cycle means the table can move.

**The operating window disqualifies materials independently of capacity.** A hydride that only desorbs usefully
above 85 °C, or cannot deliver into 5–12 bar absolute, fails those rows whatever its wt%. Against §2 this
excludes MgH2 (1 bar plateau at ~300 °C) outright on thermodynamics, not on capacity. And the 1,500-cycle
requirement — which must be met **at end of service life** (§1.1) — sits against the AB2 degradation data in
§2.5: roughly 20% capacity loss in 150 cycles.

### 1.3 Storage classes

| Class | Mechanism | Strengths | Weaknesses |
|---|---|---|---|
| Compressed gas (350/700 bar) | Physical | Mature, fast fill, ambient | Poor volumetric density, tank cost |
| Cryogenic liquid | Physical | Good density | Liquefaction energy, boil-off |
| Cryo-compressed | Physical | Best physical volumetric | Complexity, boil-off |
| Physisorption (MOFs, carbons) | Van der Waals | Fast, fully reversible | Needs cryogenic temperatures |
| **Metal hydrides** | Chemical (interstitial) | High volumetric density, low pressure, safe, near-ambient | Heavy, heat management |
| Complex hydrides | Chemical (ionic/covalent) | High gravimetric capacity | Poor reversibility and kinetics |

The gravimetric/volumetric asymmetry that drives the whole field is quantified in the TED: hydrogen has
*"nearly three times the energy content of gasoline when comparing lower heating values (**33 kWh/kg** for H2
compared to **12 kWh/kg** for gasoline). However, on a volume basis, the situation is reversed (approximately
**1.3 kWh/L** for 700 bar H2 at 15 °C compared to **8.8 kWh/L** for gasoline)"*
([TED §1](https://www.energy.gov/sites/prod/files/2017/05/f34/fcto_targets_onboard_hydro_storage_explanation.pdf)).
That ~7x volumetric deficit against gasoline, not the gravimetric figure, is the reason materials-based storage
is pursued at all. The [dormancy and boil-off rows](https://www.energy.gov/sites/prod/files/2017/05/f34/fcto_targets_onboard_hydro_storage_explanation.pdf)
in the table above exist specifically to constrain the cryogenic options.

The IEA Hydrogen TCP Task 32 review ([Hirscher et al. 2020, *J. Alloys Compd.* 827, 153548](https://doi.org/10.1016/j.jallcom.2019.153548)
— title, journal, volume and page verified via Crossref 2026-08-30) is the correct single citation for
state-of-the-field claims across these classes.

### 1.4 Why hydrides remain relevant

Intermetallic hydrides give **under 2 wt% usable** under practical pressure/temperature swings (§2.1, sourced),
so they will not win onboard light-duty storage. They remain relevant where mass is not the binding constraint:

- **Stationary storage** — volumetric density and safety dominate, mass is nearly free.
  [Wang, Peng, Witman, Stavila, Allendorf & Breunig 2025, "Technoeconomic Insights into Metal Hydrides for
  Stationary Hydrogen Storage", *Adv. Sci.* 12](https://doi.org/10.1002/advs.202415736) — **DOI, title, journal
  and volume CONFIRMED via Crossref 2026-08-30.**
- **Thermal energy storage and heat pumps** — [Nizam, Chaurasiya, Sharma & Pai, "A Review on Magnesium Based
  Metal Hydrides for Thermal Energy Storage Systems", *Asia-Pac. J. Chem. Eng.* 21](https://doi.org/10.1002/apj.70161).
  **DOI CONFIRMED via Crossref 2026-08-30**; note Crossref gives the issued year as **2025** (online-first) and
  the volume as **21**, against the "2026" carried earlier — cite as *Nizam et al., Asia-Pac. J. Chem. Eng. 21
  (2025/2026)* or simply by DOI.
- **Hydrogen compression** — thermally driven, no moving parts; the hysteresis of §2.4 is precisely the pressure
  swing being exploited.
- **Purification** — selective absorption.

#### The "156 kWh/m3 at 89.4% efficiency" figure — TRACED, and CORRECTED in what it means (open item #2)

**Primary source found.** The figure comes from
[Malleswararao, Aswin, Srinivasa Murthy & Dutta (2020), "Performance prediction of a coupled metal hydride
based thermal energy storage system", *Int. J. Hydrogen Energy* **45**(31), 16239–16253](https://doi.org/10.1016/j.ijhydene.2020.03.251)
(bibliographic record verified via Crossref; abstract retrieved via the Semantic Scholar API, both 2026-08-30).
The abstract states it directly:

> "The performance of a coupled system is analyzed considering **Mg2Ni** material for energy storage and
> **LaNi5** material for hydrogen storage. **A 3-D model is developed and simulated using COMSOL Multiphysics®**
> at charging and discharging temperatures of **300 °C and 230 °C**, respectively. The LaNi5 bed used for
> hydrogen storage is operated close to ambient temperature of 25 °C. The results of the first three consecutive
> cycles are presented. The thermal storage system achieved a **volumetric energy storage density of
> 156 kWh m−3 at energy storage efficiency of 89.4% during third cycle**."

**The number is real. The way the skill carried it was wrong in three respects:**

1. **It is a simulation, not a measurement.** A 3-D COMSOL Multiphysics finite-element model, not an
   experimental result. The skill presented it as a system performance figure.
2. **It is a single cycle of a three-cycle run** — the *third* cycle specifically. Not a steady-state or
   cycled-lifetime value.
3. **It is bought at 300 °C charging.** That is MgH2/Mg2Ni-class operating temperature, and it belongs next to
   §2.2's point that Mg-based systems need ~300 °C. Quoting "156 kWh/m3, 89.4%" without the 300 °C makes the
   system sound far more practical than it is.

**Verdict: KEEP, with the qualifiers.** Correct phrasing: *"a 3-D simulation of a coupled Mg2Ni/LaNi5 pair
predicts 156 kWh/m3 at 89.4% storage efficiency on the third cycle, charging at 300 °C and discharging at
230 °C ([Malleswararao et al. 2020](https://doi.org/10.1016/j.ijhydene.2020.03.251))."* Never as a measured
system capability.

For contrast, the same group's later work on the same hydride pair reports **long-term storage density of
532.64 MJ/m3 (≈148 kWh/m3) at 67.8% efficiency** and **buffer-mode 430.28 MJ/m3 (≈120 kWh/m3) at 91.2%**
([Malleswararao, Aswin, Srinivasa Murthy & Dutta 2022, *Energy* **258**, 124868](https://doi.org/10.1016/j.energy.2022.124868)
— record verified via Crossref 2026-08-30; **these two figures are from a search summary of the abstract and
the full text was not retrieved, so treat them as *unverified***). The spread across operating modes is the
point: a single efficiency number for a hydride thermal store is meaningless without its mode and temperatures.
The group has since published an experimental study on the same system
([*Int. J. Hydrogen Energy* **56**, 1371–1383, 2024](https://doi.org/10.1016/j.ijhydene.2023.12.191), record
verified via Crossref) — **that** is the paper to read before quoting any experimental number here.

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

*(Re-researched 2026-08-30. Every DOI in this section was resolved against the
[Crossref REST API](https://api.crossref.org/) and checked field-by-field — DOI, title, journal, year, volume,
pages, authors. Where a *claim attached to* a citation could be checked against the paper's own abstract, it
was. One claim did not survive: see the MODNet entry.)*

The governing fact: **~1,279 rows, and fewer distinct chemistries than rows** (splits are on `unique_formulae`).
Most wrong answers in this domain come from ignoring the sample size.

### 3.0 DOI verification table

Every §3 reference, resolved 2026-08-30. **Bold = a field that differed from what the memo carried** and has
been corrected below.

| Cited as | Verdict | Record as resolved by Crossref |
|---|---|---|
| Magpie — Ward et al. 2016, *npj Comput. Mater.* 2, 16028 | **CONFIRMED** | [10.1038/npjcompumats.2016.28](https://doi.org/10.1038/npjcompumats.2016.28) — "A general-purpose machine learning framework for predicting properties of inorganic materials", *npj Comput. Mater.* **2** (2016), Ward, Agrawal, Choudhary, Wolverton |
| matminer — Ward et al. 2018, *Comput. Mater. Sci.* 152, 60 | **CONFIRMED** | [10.1016/j.commatsci.2018.05.018](https://doi.org/10.1016/j.commatsci.2018.05.018) — "Matminer: An open source toolkit for materials data mining", *Comput. Mater. Sci.* **152**, **60–69** (2018), 17 authors incl. Ward, Dunn, Jain |
| Grinsztajn, Oyallon & Varoquaux, NeurIPS 2022 D&B | **CONFIRMED** | [arXiv:2207.08815](https://arxiv.org/abs/2207.08815), DOI [10.48550/arXiv.2207.08815](https://doi.org/10.48550/arXiv.2207.08815) — "Why do tree-based models still outperform deep learning on tabular data?" *(not in Crossref: arXiv DOIs are registered with DataCite, so the arXiv record is the primary check — verified there directly)* |
| Dunn et al. 2020 — Matbench | **CONFIRMED** | [10.1038/s41524-020-00406-3](https://doi.org/10.1038/s41524-020-00406-3) — "Benchmarking materials property prediction methods: the Matbench test set and Automatminer reference algorithm", *npj Comput. Mater.* **6** (2020), Dunn, Wang, Ganose, Dopp, Jain |
| De Breuck, Hautier & Rignanese 2021 — MODNet | **DOI CONFIRMED, attached claim CORRECTED** | [10.1038/s41524-021-00552-2](https://doi.org/10.1038/s41524-021-00552-2) — "Materials property prediction for limited datasets enabled by feature selection and joint learning with MODNet", *npj Comput. Mater.* **7** (2021) |
| CleanLab / confident learning — Northcutt, Jiang & Chuang 2021 | **CONFIRMED** | [10.1613/jair.1.12125](https://doi.org/10.1613/jair.1.12125) — "Confident Learning: Estimating Uncertainty in Dataset Labels", *JAIR* **70**, **1373–1411** (2021) |
| Li et al. 2025, *Commun. Mater.* 6 | **CONFIRMED** | [10.1038/s43246-024-00731-w](https://doi.org/10.1038/s43246-024-00731-w) — "Probing out-of-distribution generalization in machine learning for materials", *Commun. Mater.* **6** (2025), Li, Rubungo, Lei, Persaud, Choudhary, DeCost, Dieng, Hattrick-Simpers |
| Beltrame et al. 2025, *Metals* 15, 1221 | **CONFIRMED** | [10.3390/met15111221](https://doi.org/10.3390/met15111221) — "Application of Machine Learning and Data Augmentation Algorithms in the Discovery of Metal Hydrides", *Metals* **15**, 1221 (2025) |
| Durdy et al. 2022, *Digital Discovery* 1, 763 | **CONFIRMED** | [10.1039/d2dd00039c](https://doi.org/10.1039/d2dd00039c) — "Random projections and kernelised leave one cluster out cross validation", *Digital Discovery* **1**, **763–778** (2022), Durdy, Gaultois, Gusev, Bollegala, Rosseinsky |
| Angelopoulos & Bates 2023, *FnT ML* 16, 494 | **CONFIRMED** | [10.1561/2200000101](https://doi.org/10.1561/2200000101) — "Conformal Prediction: A Gentle Introduction", *Found. Trends Mach. Learn.* **16**, **494–591** (2023) |
| DiSCoVeR — Baird, Diep & Sparks 2022 | **CONFIRMED** | [10.1039/d1dd00028d](https://doi.org/10.1039/d1dd00028d) — "DiSCoVeR: a materials discovery screening tool for high performance, unique chemical compositions", *Digital Discovery* **1**, **226–240** (2022) |
| HyStor — Wilson et al. 2024 | **CONFIRMED, citation incomplete** | [10.1016/j.ijhydene.2024.09.390](https://doi.org/10.1016/j.ijhydene.2024.09.390) — "HyStor: An experimental database of hydrogen storage properties for various metal alloy classes", *Int. J. Hydrogen Energy* **90**, **460–469** (2024), Wilson, Verma, Maharana, Sahoo, Joshi. **Volume and pages were missing; add them.** |
| FIND platform — Lu et al. 2025 | **CONFIRMED** | [10.20517/jmi.2025.56](https://doi.org/10.20517/jmi.2025.56) — "FIND: a forward–inverse navigation and discovery platform for hydrogen storage alloys powered by data-driven machine learning", *J. Mater. Inform.* **5** (2025) |
| "ML-driven alloy digital design for hydrogen storage: a review" 2025 | **CONFIRMED, journal was missing** | [10.1080/27525783.2025.2511889](https://doi.org/10.1080/27525783.2025.2511889) — *Digital Twin* **2** (2025), Liu, Xue, Cheng, Zhao, Dou, Paredes, Song |

**Net result: no fabricated or mismatched DOI in §3.** All fourteen resolve to the paper they were cited as.
Two citations were incomplete (HyStor volume/pages, *Digital Twin* journal name) and one attached *claim* was
wrong (MODNet, below). That is the honest outcome of the check, and it is worth recording that the DOIs
themselves held up.

### 3.1 Composition-based featurisation

- **Magpie** — the standard elemental-property descriptor set
  ([Ward, Agrawal, Choudhary & Wolverton 2016, *npj Comput. Mater.* 2, 16028](https://doi.org/10.1038/npjcompumats.2016.28)).
- **matminer** — featurizer library
  ([Ward et al. 2018, *Comput. Mater. Sci.* 152, 60–69](https://doi.org/10.1016/j.commatsci.2018.05.018)).
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

Evidence, not fashion. Each claim below is now quoted from the paper's own abstract, not paraphrased.

- [Grinsztajn, Oyallon & Varoquaux, NeurIPS 2022 Datasets & Benchmarks](https://arxiv.org/abs/2207.08815) —
  **CONFIRMED verbatim.** The abstract: *"We define a standard set of **45 datasets** from varied domains with
  clear characteristics of tabular data ... Results show that **tree-based models remain state-of-the-art on
  medium-sized data (~10K samples) even without accounting for their superior speed.**"* The inductive-bias
  explanation is also theirs: robustness to uninformative features, orientation of the data, and learning
  irregular functions.
- [Dunn, Wang, Ganose, Dopp & Jain 2020, *npj Comput. Mater.* 6](https://doi.org/10.1038/s41524-020-00406-3) —
  **CONFIRMED verbatim.** Matbench is *"a set of **13 ML tasks**"* spanning *"from **312 to 132k samples**"*, and
  *"**crystal graph methods appear to outperform traditional machine learning methods given ~10^4 or greater
  data points**"*. The memo's phrasing of this was accurate.
- [De Breuck, Hautier & Rignanese 2021, *npj Comput. Mater.* 7](https://doi.org/10.1038/s41524-021-00552-2) —
  **CORRECTED.** The paper is real and says MODNet *"is shown to **outperform current graph-network models on
  small datasets**"*, with a headline result of *"vibrational entropy at 305 K ... predicted with a mean absolute
  test error of 0.009 meV/K/atom (four times lower than previous studies)"*. But the abstract **never states a
  ~15,000-sample threshold**. The memo's "outperforming graph networks below ~15,000 samples" attributes a
  specific number to this paper that it does not contain in its abstract. **Mark the 15,000 figure
  *unverified* and drop it**; say "on small datasets" and let the *quantified* crossover come from Matbench's
  ~10^4, which is sourced. *(The threshold may appear in the paper body or in a follow-up MODNet benchmarking
  paper; the full text was not retrieved here, so the claim is unsupported rather than disproved.)*

At 1,279 rows the existing CatBoost/ExtraTrees/stacking choice is correct — and note that 1,279 sits an order of
magnitude *below* the ~10^4 crossover Matbench identifies, so this is not a marginal call. When asked to add a
GNN, transformer or "materials foundation model", the defensible answer is usually **no** — spend the effort on
validation.

### 3.3 Validation pitfalls — the section that decides whether results survive examination

1. **Composition leakage.** Duplicate and near-duplicate formulas across train/test inflate scores. This repo
   already splits on **unique formulae**, which is better than much published hydride ML.
2. **Formula-disjoint is still interpolation.** [Li et al. 2025, *Commun. Mater.* 6](https://doi.org/10.1038/s43246-024-00731-w)
   analysed 700+ OOD tasks and found heuristic split criteria "mostly test interpolation rather than true
   extrapolation".
3. **Cross-family generalisation fails — the most important result for this thesis.**
   [Beltrame, Dematteis, Stavila, Rizzi, Baricco & Palumbo 2025, "Application of Machine Learning and Data
   Augmentation Algorithms in the Discovery of Metal Hydrides", *Metals* 15, 1221](https://doi.org/10.3390/met15111221)
   expanded a hydride dataset from ~400 to 806 entries and found high accuracy **only when training and testing
   within one hydride family** (e.g. AB2), with limited generalisability across material classes; augmentation
   helped only on the smallest datasets and not in underrepresented pressure regimes.
   → **Report leave-one-alloy-class-out CV alongside random-split R2, and expect it to be much worse.**
   Method: [Durdy et al. 2022, *Digital Discovery* 1, 763–778](https://doi.org/10.1039/d2dd00039c)
   (leave-one-cluster-out).
4. **Selection and tuning inside the CV loop.** Boruta, SHAP and VIF selection run on the full training set
   before splitting leaks information. Nested CV, or an explicit statement of what was done and what it costs.
5. **Small-test-set variance.** At n=239 a test R2 of 0.916 carries a wide interval. Bootstrap it; do not report
   a bare point estimate.
6. **Tuning against the test set.** Reporting the best of 13 models x 100 Optuna trials by *test* score converts
   the test set into a validation set. Select on validation; touch test once.

### 3.4 Label noise, and a physics-grounded reason for it

Confident learning ([Northcutt, Jiang & Chuang 2021, *JAIR* 70, 1373–1411](https://doi.org/10.1613/jair.1.12125))
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
  ([Angelopoulos & Bates 2023, "Conformal Prediction: A Gentle Introduction", *Found. Trends Mach. Learn.* 16,
  494–591](https://doi.org/10.1561/2200000101)); [MAPIE](https://github.com/scikit-learn-contrib/MAPIE),
  [crepes](https://pypi.org/project/crepes/).
- **CatBoost native** — `RMSEWithUncertainty`, `MultiQuantile`, virtual ensembles
  ([docs](https://catboost.ai/docs/en/concepts/loss-functions-regression)).
- **NGBoost** — [Duan et al., ICML 2020](https://proceedings.mlr.press/v119/duan20a.html).
- **Applicability domain** — Element Mover's Distance ([ElMD](https://github.com/lrcfmd/ElMD));
  [DiSCoVeR, Baird, Diep & Sparks 2022, *Digital Discovery* 1, 226–240](https://doi.org/10.1039/d1dd00028d)
  trades predicted performance against chemical novelty explicitly.

### 3.6 Published ML-on-hydride work

Dataset sizes here are small; say so rather than implying otherwise.

- **HyStor** — 1,282 metal alloys with maximum capacity at a given absorption temperature; 54 elements,
  200–800 K; curated HydPARK (831 entries) plus 451 compositions from articles and patents; adds LEA/MEA/HEA
  classes ([Wilson, Verma, Maharana, Sahoo & Joshi 2024, *Int. J. Hydrogen Energy* **90**, 460–469](https://doi.org/10.1016/j.ijhydene.2024.09.390);
  [preprint](https://chemrxiv.org/doi/pdf/10.26434/chemrxiv-2024-6zkm0)).
- **ML-HydPARK** — cleaned CSV derived from DOE HydPARK, by **Witman, Allendorf & Stavila (Sandia National
  Laboratories)**, **version 0.0.4, published 2022-11-15**, [DOI 10.5281/zenodo.7324809](https://doi.org/10.5281/zenodo.7324809)
  (Zenodo record read 2026-08-30). The record describes the dataset as *"continuously updated under version
  control as new metal alloy hydrides are published in the open literature"* — which is a claim about
  **ML-HydPARK**, not about HydPARK itself (see §4.1).
- [FIND platform, Lu et al. 2025, *J. Mater. Inform.* 5](https://doi.org/10.20517/jmi.2025.56) — ~6,000 records,
  VAE plus genetic algorithm.
- [Liu et al. 2025, "Machine learning-driven alloy digital design for hydrogen storage: a review",
  *Digital Twin* 2](https://doi.org/10.1080/27525783.2025.2511889).

A test R2 near 0.9 on a formula-disjoint split is a good result at this scale — but it is a statement about
interpolation within the sampled chemical space and must be presented as such.

---

## 4. Computational materials informatics

*(Re-researched 2026-08-30. §4.1's entry counts now come from **direct queries to each provider's own OPTIMADE
API**, not from a third-party linking study. §4.2, previously the least-sourced part of this memo, now carries a
citation under every claim.)*

### 4.1 Databases

**Hydrogen-specific** — see §3.6 for HyStor / HydPARK / ML-HydPARK detail.

The primary citation for HydPARK itself is
[Sandrock & Thomas, "The IEA/DOE/SNL on-line hydride databases", *Appl. Phys. A* **72**, 153–155 (2001)](https://doi.org/10.1007/s003390100770)
(record verified via Crossref 2026-08-30). It describes *"a series of comprehensive hydride databases ... freely
available on the Internet at hydpark.ca.sandia.gov"*, built under the International Energy Agency with DOE
funding and Sandia hosting.

> **UNVERIFIED — "HydPARK's last update was 2002".** This date is carried in the skill and was carried here. It
> could **not** be confirmed on 2026-08-30: the original `hydpark.ca.sandia.gov` host is long gone, the
> [ML-HydPARK Zenodo record](https://doi.org/10.5281/zenodo.7324809) says only that it was *"parsed and cleaned
> from the DOE's original publicly available HydPARK database"* without dating it, and the Sandrock & Thomas
> paper predates the claim (2001). **Do not put "2002" in the thesis as a sourced fact.** The defensible version
> of the same argument needs no date at all: HydPARK is a legacy DOE/IEA database no longer maintained at its
> original host, its content is only reachable today through derived redistributions (ML-HydPARK, HyStor), and
> the largest curated hydride dataset in the modern literature is still ~1,282 entries
> ([HyStor](https://doi.org/10.1016/j.ijhydene.2024.09.390)). *That* is why 1,279 rows is a normal-sized hydride
> dataset and why data scarcity here is structural rather than incidental.

#### General DFT databases — entry counts, queried directly (open item #3)

Each provider's own OPTIMADE `/v1/structures` endpoint was queried on **2026-08-30** and the `meta.data_returned`
field read off. This is the count *the provider itself reports for the data it exposes through OPTIMADE*.

| Provider | Carried in the skill | **Direct API answer, 2026-08-30** | Verdict |
|---|---|---|---|
| Materials Project | ~186,743 | **154,387** structures — [`optimade.materialsproject.org/v1/structures`](https://optimade.materialsproject.org/v1/structures?page_limit=1), OPTIMADE API v1.2.0, provider "Materials Project - OPTIMADE" | **CORRECTED** |
| OQMD | ~1,593,781 | **1,407,395** structures — [`oqmd.org/optimade/v1/structures`](http://oqmd.org/optimade/v1/structures?page_limit=1), OPTIMADE API v1.2.0, provider "OQMD / The Open Quantum Materials Database" | **CORRECTED** |
| AFLOW | ~1,369,252 | **Not retrievable.** `/v1/structures` returned **HTTP 500** on three attempts across the session; the sibling `/v1/info` endpoint responded normally (provider "AFLOW", API v1.0.0, maintainer `optimade@aflowlib.duke.edu`), so the service is up but the structures endpoint was failing | **UNVERIFIED** |

Notes that must travel with these numbers:

- **These are OPTIMADE-exposed structure counts, not "the size of the database".** A provider may index only
  part of its holdings through OPTIMADE, and a "structure" is not the same unit as a "material", an "entry" or a
  "calculation". The Materials Project figure in particular is materially smaller than counts quoted elsewhere
  for MP, and the most likely explanation is scope of the OPTIMADE endpoint rather than the database shrinking.
  **Say which endpoint and which unit you counted.**
- **Both corrected numbers are lower than what was carried**, and the carried numbers came from a third-party
  linking study rather than the providers. The order-of-magnitude disagreement previously flagged for OQMD does
  not survive contact with OQMD's own API: **1.41 million** is the same order as the 1.59 million carried and as
  the "one million compounds" of OQMD's own reflections paper
  ([Shen et al. 2022, *J. Phys.: Mater.* 5, 031001](https://doi.org/10.1088/2515-7639/ac7ba9), verified via
  Crossref). The "over 600,000 compounds" figure from a 2026 secondary source is the outlier and should be
  discarded.
- **Growth is fast enough that any count is a snapshot.** [Kirklin et al. (2015)](https://doi.org/10.1038/npjcompumats.2015.10)
  described OQMD as *"nearly 300,000 density functional theory (DFT) total energy calculations"*; the same
  database's API reports **1,407,395** structures eleven years later. Never quote a database size without its
  date.
- **Aggregate cross-check.** The [OPTIMADE providers dashboard](https://www.optimade.org/providers-dashboard/)
  reported **26,748,748 structures** across providers with aggregation enabled, spanning **42 sub-databases**,
  **28 known providers** and **21 available** (accessed 2026-08-30; the dashboard shows no timestamp of its own,
  which is itself a reason to prefer a direct provider query).

**Access, by preference order:**

- **OPTIMADE** — one API spec across providers
  ([Andersen et al. 2021, "OPTIMADE, an API for exchanging materials data", *Sci. Data* **8**, 217](https://doi.org/10.1038/s41597-021-00974-z)
  — record verified via Crossref 2026-08-30; the memo previously linked only a PMC mirror).
  Prefer this to one client per database, and note that it also gives you the count for free via
  `meta.data_returned`.
- **Materials Project** — RESTful API, JSON datasets; `mp-api` / pymatgen client.
- **OQMD**, **AFLOW**, **NOMAD** — high-throughput DFT at scale.

**Cross-database consistency is not a given.**
[Hegde, Borg, del Rosario, Kim, Hutchinson, Antono, Ling, Saxe, Saal & Meredig 2023, "Quantifying uncertainty in
high-throughput density functional theory: A comparison of AFLOW, Materials Project, and OQMD",
*Phys. Rev. Materials* **7**, 053805](https://doi.org/10.1103/PhysRevMaterials.7.053805) compares them directly.
(Full title verified via Crossref 2026-08-30 — the memo's shortened form was accurate.) Do not pool values
across databases without addressing this.

### 4.2 DFT for hydride formation enthalpy, and why it is not experiment

*(This subsection was previously **written from domain knowledge with no citations** and was flagged as the
weakest content in the memo. Every claim below now has a source, and one claim has been materially qualified by
what the sources actually say.)*

**Workflow.** Structure, relaxation, total energies of metal / hydride / H2, formation enthalpy, optionally
phonons for zero-point and finite-temperature corrections. The canonical statement of this approach for
hydrogen storage specifically is
[Wolverton, Siegel, Akbarzadeh & Ozoliņš 2008, "Discovery of novel hydrogen storage materials: an atomic scale
computational approach", *J. Phys.: Condens. Matter* **20**, 064228](https://doi.org/10.1088/0953-8984/20/6/064228)
(record verified via Crossref 2026-08-30; **publisher blocked full-text and abstract retrieval — IOPscience
returned a bot-check redirect — so this is cited for the approach it is known for, and its internals are
*unverified* here**). A dedicated, fully retrievable treatment of the narrower question is
[Andreasen, "Predicting formation enthalpies of metal hydrides", Risø-R-1484(EN), Risø National Laboratory,
December 2004, ISBN 87-550-3382-2](https://www.osti.gov/etdeweb/servlets/purl/20553542) (33 pp., 54 refs; PDF
retrieved and text-extracted 2026-08-30).

Why DFT-computed and experimentally-measured quantities are **not interchangeable**:

1. **DFT gives one ordered structure at 0 K.** Experiment measures a real, often multiphase, defected sample at
   finite temperature and finite pressure. §2.4's plateau-slope discussion is exactly this gap made visible.
   General treatment of what DFT can and cannot predict for energy materials:
   [Jain, Shin & Persson 2016, "Computational predictions of energy materials using density functional theory",
   *Nat. Rev. Mater.* **1**](https://doi.org/10.1038/natrevmats.2015.4) (verified via Crossref 2026-08-30).

2. **Zero-point energy is not negligible for hydrogen — but do not assume it is large either.** The claim as
   carried ("ZPE corrections materially shift hydride formation enthalpies, and omitting them is a standard
   error") is **supported for hydrides and contradicted for other systems**, and the distinction is the useful
   part:
   - *For an intermetallic hydride*, a 2025 first-principles study of the A2B7 alloy Nd3MgNi14 concludes
     that *"both hybrid exchange-correlation functionals and **zero-point energy corrections are necessary to
     obtain accurate absorption properties**"*
     ([Nadeau, Béjaud, Baguet, Geneste, Bottin & Antonius, arXiv:2509.05136](https://doi.org/10.48550/arXiv.2509.05136),
     abstract read 2026-08-30). **This is a preprint, not peer-reviewed** — flagged as such, and it is the
     closest directly on-point source found. Its abstract states the *necessity*, not a magnitude in kJ/mol.
   - *For oxides and halides*, the opposite holds: *"The zero-point vibrational and thermal contributions to
     the formation enthalpies are **small and with different signs — largely canceling each other**"*
     ([Friedrich, Usanmaz, Oses, Supka, Fornari, Buongiorno Nardelli, Toher & Curtarolo 2019, "Coordination
     corrected ab initio formation enthalpies", *npj Comput. Mater.* **5**](https://doi.org/10.1038/s41524-019-0192-1),
     peer-reviewed, abstract read 2026-08-30).
   - **The honest claim** is therefore: the ZPE/thermal cancellation that makes these terms ignorable in oxide
     thermochemistry **cannot be assumed for hydrides**, because hydrogen's vibrational frequencies are the
     highest in the periodic table and the H2 reference and the bound H sit in very different potentials. State
     that the corrections are included; do not quote an unsourced magnitude. **A specific kJ/mol ZPE
     contribution for a named hydride remains *unverified* here.**

3. **Functional dependence, quantified.** The largest DFT-vs-experiment comparison of formation energies found
   *"an apparent mean absolute error between experimental measurements and our calculations of
   **0.096 eV/atom**"* across 1,670 experimental formation energies
   ([Kirklin, Saal, Meredig, Thompson, Doak, Aykol, Rühl & Wolverton 2015, "The Open Quantum Materials Database
   (OQMD): assessing the accuracy of DFT formation energies", *npj Comput. Mater.* **1**](https://doi.org/10.1038/npjcompumats.2015.10),
   abstract read 2026-08-30). **The caveat in that same abstract is the more interesting half**, and it cuts
   against a naive reading: deviation *between different experimental measurements themselves* is
   **0.082 eV/atom**, so *"a significant fraction of the error between DFT and experimental formation energies
   may be attributed to experimental uncertainties."* Roughly: ~0.1 eV/atom ≈ 9.6 kJ/mol-atom is the honest
   scale of disagreement, and it is not all DFT's fault. Functional-specific corrections can reduce residual
   error to **27(24) meV/atom** with SCAN for binary/ternary oxides and halides
   ([Friedrich et al. 2019](https://doi.org/10.1038/s41524-019-0192-1); automated in
   [Friedrich et al. 2021, "Automated coordination corrected enthalpies with AFLOW-CCE", *Phys. Rev. Materials*
   **5**, 043803](https://doi.org/10.1103/PhysRevMaterials.5.043803)) — **note both benchmarks are on oxides and
   halides, not hydrides**, so those error bars do not transfer.

4. **Formation enthalpy is not decomposition enthalpy, and confusing them is a documented, current error in
   this literature.** A 2026 systematic review is devoted entirely to it:
   [Deligöz & Özışık, "Misinterpretation of formation enthalpy in DFT-based desorption temperature predictions
   for hydrogen storage materials: A systematic review", *J. Power Sources* **679**, 240161 (2026)](https://doi.org/10.1016/j.jpowsour.2026.240161)
   (bibliographic record verified via Crossref 2026-08-30; **no abstract is deposited with Crossref and the
   publisher's full text was not retrieved, so the review is cited for the problem named in its title, and its
   internal findings are *unverified* here**). The van 't Hoff machinery of §2.3 takes the **desorption**
   enthalpy; substituting the formation enthalpy of the hydride from its elements gives a different number and a
   wrong predicted desorption temperature. Given that this project's dataset is experimental, the practical rule
   is: **if you ever mix a DFT enthalpy into an argument about desorption temperature, state which enthalpy it
   is.**

5. **Theoretical vs usable capacity again.** DFT naturally reports full stoichiometric occupancy — quantity (1)
   in §2.0. Experiment reports (2) or (3). LiBH4's 18.5 vs 13.8 vs deliverable (§2.2, sourced) is the cautionary
   case, and it is a definitional gap, not a numerical error in either method.

A DFT formation enthalpy is a good **screening signal** and a good physics cross-check on ML predictions. It is
not a label to mix into an experimental training set without saying so — and §4.1's cross-database result
([Hegde et al. 2023](https://doi.org/10.1103/PhysRevMaterials.7.053805)) means it is not even safe to pool DFT
labels across *providers* without saying so.

### 4.3 Active learning

Bayesian optimization with a GP surrogate works from tens of points and is built for this regime — but it pays
off **only if experiments will actually be run**. In a computational-only thesis it is a chapter about a loop
that never closes. Cross-reference `research/inverse-design-methods.md` §3.3 and §4.4.

### 4.4 Tooling and reproducibility

- **pymatgen** — structures, composition parsing, database clients.
- **matminer** — featurizers ([Ward et al. 2018, *Comput. Mater. Sci.* 152, 60–69](https://doi.org/10.1016/j.commatsci.2018.05.018)).
- **ASE** — atomistic simulation environment.
- **atomate2 / jobflow** — reproducible high-throughput DFT workflows.
- [Abraham & Gogotsi 2026, "Machine Learning Toolkits and Frameworks for Materials Design",
  *WIREs Comput. Mol. Sci.* **16**](https://doi.org/10.1002/wcms.70067) — landscape review. **DOI, title,
  journal, volume and year CONFIRMED via Crossref 2026-08-30**; the memo previously cited it as "Abraham et al.",
  and Crossref lists exactly two authors, **Abraham and Gogotsi**.

**Provenance discipline:** pin package versions; record which database snapshot and which date — §4.1 is the
worked example of why. Keep the fitted scaler (`RobustScaler`) and the 22-feature list as artefacts rather than
things to be recomputed. This repo's habit of writing each stage's output to `Machine_Model/reports/` is the
right instinct — every number in `REPORT.md` traces to the run that produced it.

---

## 5. Status, provenance and what is still open

**How this memo was produced.** §2 was written on 2026-08-29 by a dedicated background research agent that
verified claims against retrieved primary sources. §§1, 3 and 4 were first drafted in the main session after
that agent failed three times (two server errors, one session rate limit) and rested on far fewer searches;
they were **re-researched on 2026-08-30** in the main session — no subagent — against the DOE Target Explanation
Document, the Crossref REST API, each database provider's own OPTIMADE API, the arXiv API and the Semantic
Scholar API. All four sections now carry per-claim provenance and explicit verdicts.

**Method used on 2026-08-30.** Every DOI in §§1, 3 and 4 was resolved against
[`api.crossref.org`](https://api.crossref.org/) and compared field-by-field (title, journal, year, volume,
pages, authors). Where the *claim attached to* a citation could be checked against the paper's own abstract, it
was — via publisher-neutral APIs, because several publishers (Elsevier, IOP, Wiley, ACS) blocked or elided
direct retrieval. Database sizes came from live provider APIs, not from secondary literature. Two PDFs (the DOE
TED, the Risø report) were downloaded and text-extracted locally.

### Corrections this memo makes to the skill modules

**From §2 (2026-08-29):**

| Claim as carried | Corrected to |
|---|---|
| BCC solid solution ~3 wt%, reversible ~2 | **~4 wt% total, 1.9–2.3 reversible**; mechanism is the too-stable V monohydride, only VH→VH2 is usable |
| AB2 dH −28 to −35 | **−24 to −41** across the ZrMn2 substitution range |
| AB5 ~1.4 wt% | 1.38 **stoichiometric**, **1.2 measured** — do not present 1.4 as deliverable |
| AB2 ~1.8–2 wt% | **1.77 max, 1.34–1.40 after 150 cycles** |
| LiBH4 ~18 wt% | 18.5 total, **13.8 maximum desorbable** (LiH stable to ~900 °C) |
| dS ≈ −130 J/(mol H2 K) as a constant | Confirmed as an approximation; **LaNi5 needs ≈ −103 to −108** to reproduce its observed plateau. Wrong at the tens-of-percent level for a specific alloy |
| dH ≈ −39 kJ/mol H2 | Confirmed as **arithmetic consequence** of the entropy constant, not a measurement. Practical design windows are tighter: 20–30, or −10 to −60 |

**From §§1, 3, 4 (2026-08-30):**

| Claim as carried | Corrected to | Where |
|---|---|---|
| Onboard capacity range **5–13 kg H2** | **4–10 kg H2** — stated three times in the DOE TED; "5–13" appears in neither the TED nor the EERE page | §1.2 |
| DOE target column "**Ultimate Full Fleet**" | "**Ultimate**". "Ultimate Full Fleet" is the superseded *2009* label | §1.2 |
| Target table has two columns (2025, Ultimate) | **Three: 2020, 2025, Ultimate** — the 2020 column was missing | §1.2 |
| Balance of plant costs "**a factor of ~2 or worse**" gravimetrically | **Removed — no source found.** The sourced argument (system includes all BOP; capacities are *usable* and *end-of-life*) stands without a multiplier | §1.1 |
| DOE revision date **NOT FOUND** | **RESOLVED: originals 2003, last major revision 2009, current table "updated May 2017"**; 2015 targets were re-dated to 2025 after funding cuts; U.S. DRIVE reviews ~every 5 years | §1.2 |
| "156 kWh/m3, 89.4%" **UNVERIFIED** | **TRACED** to [Malleswararao et al. 2020, *IJHE* 45(31) 16239–16253](https://doi.org/10.1016/j.ijhydene.2020.03.251) — and it is a **3-D COMSOL simulation, third cycle, 300 °C charge / 230 °C discharge**, not a measurement | §1.4 |
| Materials Project **~186,743** entries | **154,387** structures, from MP's own OPTIMADE API, 2026-08-30 | §4.1 |
| OQMD **~1,593,781** entries | **1,407,395** structures, from OQMD's own OPTIMADE API, 2026-08-30 | §4.1 |
| AFLOW **~1,369,252** entries | **UNVERIFIED** — provider `/v1/structures` returned HTTP 500 on three attempts, 2026-08-30 | §4.1 |
| MODNet "outperforms graph networks **below ~15,000 samples**" | **The ~15,000 threshold is not in the paper's abstract.** Say "on small datasets"; take the *quantified* crossover (~10^4) from Matbench, which is sourced | §3.2 |
| HydPARK "**last updated 2002**" | **UNVERIFIED** — no source found for the date. Make the argument without it | §4.1 |
| §4.2 DFT claims, **uncited** | **All five now carry citations**, and claim (2) on zero-point energy is materially qualified — ZPE/thermal terms largely cancel in oxides but that cancellation cannot be assumed for hydrides | §4.2 |
| Nizam et al. "**2026**", Abraham "**et al.**", Hegde short title, HyStor without volume/pages, *Digital Twin* journal unnamed | Bibliographic details corrected against Crossref | §§1.4, 3.0, 4.1, 4.4 |

### Still open

1. **AFLOW entry count** — the provider's OPTIMADE `/v1/structures` endpoint returned HTTP 500 throughout
   2026-08-30 while `/v1/info` responded normally. Retry the direct query; do not fall back to the
   third-party linking-study figure, which was wrong for both other providers.
2. **A ZPE magnitude for a named hydride.** The *necessity* of ZPE corrections for an intermetallic hydride is
   sourced ([Nadeau et al., preprint](https://doi.org/10.48550/arXiv.2509.05136)); a peer-reviewed kJ/mol
   figure is not. The Wolverton 2008 review is the obvious place to look and IOPscience blocked retrieval.
3. **Deligöz & Özışık 2026** ([DOI](https://doi.org/10.1016/j.jpowsour.2026.240161)) — cited for the problem in
   its title; no abstract is deposited with Crossref and the full text was not retrieved. Read the PDF before
   relying on its specific findings.
4. **Materials Project's OPTIMADE count (154,387) is much lower than counts quoted for MP elsewhere.** Most
   likely the OPTIMADE endpoint exposes a subset. Worth confirming against `mp-api` with a key before using the
   number as "the size of Materials Project" rather than "structures MP exposes via OPTIMADE".
5. **Malleswararao et al. 2022** long-term/buffer figures (532.64 MJ/m3 at 67.8%; 430.28 MJ/m3 at 91.2%) —
   from a search summary of the abstract, full text not retrieved. The group's
   [2024 experimental paper](https://doi.org/10.1016/j.ijhydene.2023.12.191) is the one to read for measured
   numbers.
6. **LaNi5 entropy tabulation** — [Sandrock 1999](https://doi.org/10.1016/S0925-8388(99)00384-9) is the standard
   table; full text not retrieved. *(Carried from 2026-08-29; unchanged.)*
7. **Dematteis et al. 2021 numbers** (TiFe oxide thickness ~20–30 nm, activation mechanism) and **Sandrock's
   300 ppm poisoning experiments** — carried from search summaries of a review whose full text was
   publisher-blocked. Check against the PDF. *(Carried from 2026-08-29; unchanged.)*

**Closed since 2026-08-29:** DOE target revision date (was #1); the 156 kWh/m3 thermal-storage figure (was #2);
Materials Project and OQMD entry counts (part of #3); §4.2's missing citations (was #6); the §3 DOI audit and
the general under-sourcing of §§1, 3, 4 (was #7).
