# Known Gaps and Validation Tasks

Updated 2026-08-29 after `research/hydride-domain-grounding.md` was written.

## What is now sourced

- **Metal hydride families, thermodynamics, kinetics** — `research/hydride-domain-grounding.md` §2, verified
  against primary literature by a dedicated research agent. Per-family capacities, enthalpies, plateau windows,
  hysteresis mechanism and degradation rates now carry DOIs. This was the skill's weakest section; it is now
  its strongest.
- **DOE targets** — primary EERE page, accessed 2026-08-29; system-level status confirmed from its own wording.
- **Project numbers** — this repo's `REPORT.md` and `Machine_Model/src/`, read 2026-08-29.
- **Inverse design / generative AI** — `research/inverse-design-methods.md`, DOI-cited.
- **ML methodology** — Grinsztajn (NeurIPS 2022), Dunn/Matbench, MODNet, Beltrame, Durdy, Li et al., CleanLab.

## Corrections applied to this skill

All from `research/hydride-domain-grounding.md` §2. The modules previously carried the left column.

| Was | Now |
|---|---|
| BCC ~3 wt%, reversible ~2 | **~4 total, 1.9–2.3 reversible**; the too-stable V monohydride is the mechanism |
| AB2 dH −28 to −35 | **−24 to −41** across the ZrMn2 substitution range |
| AB5 ~1.4 wt% | 1.38 stoichiometric, **1.2 measured** |
| AB2 ~1.8–2 wt% | **1.77 max, 1.34–1.40 after 150 cycles** |
| LiBH4 ~18 wt% | 18.5 total, **13.8 desorbable** |
| dS = −130 as a constant | Approximation; **LaNi5 needs ≈ −103 to −108**. Wrong at tens-of-percent for a specific alloy |
| dH ≈ −39 kJ/mol H2 | **Arithmetic consequence** of the entropy constant, not a measurement. Design windows: 20–30, or −10 to −60 |

## What is still NOT verified

1. **DOE target revision date** — not stated on the EERE page and not found. Cite with an access date, never a
   year. Next place to look: `targets_onboard_hydro_storage_explanation.pdf`, linked from that page.
2. **Mg2Ni + LaNi5 thermal storage at 156 kWh/m3 and 89.4% efficiency** — search-summary only, primary source
   never traced. Flagged in `hydrogen-storage-fundamentals.md`. Trace or drop before thesis use.
3. **Database entry counts** (MP ~186,743 / OQMD ~1,593,781 / AFLOW ~1,369,252) — from a linking study, and
   sources disagree by nearly an order of magnitude for OQMD. Query each provider directly.
4. **LaNi5 entropy tabulation** — [Sandrock 1999](https://doi.org/10.1016/S0925-8388(99)00384-9) is the standard
   table; full text not retrieved.
5. **Dematteis et al. 2021 activation numbers** (TiFe oxide ~20–30 nm, Ti4Fe2O mechanism) and **Sandrock's
   300 ppm poisoning experiments** — carried from search summaries of a publisher-blocked review.
6. **DFT subsection** (`computational-materials-informatics.md`, memo §4.2) — written from domain knowledge, not
   retrieved sources. Standard claims, but uncited. **The least-sourced part of the skill now.**
7. **Memo §§1, 3, 4 generally** — written in the main session after the research agent failed three times, so
   they rest on fewer searches than §2. They would benefit from the same agent treatment.

## Open questions specific to this project

1. **Why does `temperature(K)` rank 21st of 22 by SHAP (0.001)** when it determines where on the PCT surface a
   measurement sits? Narrow within-family temperature spread? Correlation with composition features?
2. **Pressure is absent from the feature set** — now understood as a *physics gap*, not just a missing column:
   plateau slope makes measured capacity depend on measurement pressure, especially for the multi-element
   alloys dominating the modern data. This is also a grounded explanation for part of what CleanLab detects.
3. **No leave-one-alloy-class-out result exists yet.** Given Beltrame's cross-family finding, this remains the
   most important missing validation number in the thesis.
4. **The target is `H2_W% (max)`, not reversible capacity.** For V-rich BCC compositions that is roughly a
   factor-of-two overstatement of what a device would deliver. Worth stating explicitly.

## Correction log

- 2026-08-29 — Rewrote `metal-hydride-families.md` against `research/hydride-domain-grounding.md` §2: seven
  numeric corrections (table above), added the three-definitions-of-capacity framing, the BCC monohydride
  mechanism, sourced hysteresis and degradation, and DOIs throughout.
- 2026-08-29 — Corrected two factual errors in `research/inverse-design-methods.md`, both verified against the
  pipeline's own outputs first:
  - **`StandardScaler` → `RobustScaler`** (2 places). Every live path in `Machine_Model/src/` uses
    `RobustScaler`; the only `StandardScaler` occurrences are commented-out dead code in `Catboostmodel.py`.
  - **"12 selected descriptors" → "22"** (4 places). `feature_selection_report.csv` is 23 lines = header + 22,
    matching `REPORT.md` §3.3.
- 2026-08-29 — Replaced the upstream generic template (self-described "Legacy template awaiting research
  upgrade", confidence Low) with hydride-specialised content. Removed `modules/core-guidance.md`.
