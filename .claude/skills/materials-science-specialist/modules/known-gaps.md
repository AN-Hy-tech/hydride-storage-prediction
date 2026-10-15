# Known Gaps and Validation Tasks

Updated 2026-08-30 after `research/hydride-domain-grounding.md` §§1, 3, 4 were re-researched to the standard
of §2. (Previously updated 2026-08-29, when the memo was first written.)

## What is now sourced

- **Metal hydride families, thermodynamics, kinetics** — `research/hydride-domain-grounding.md` §2, verified
  against primary literature by a dedicated research agent. Per-family capacities, enthalpies, plateau windows,
  hysteresis mechanism and degradation rates now carry DOIs. This was the skill's weakest section; it is now
  its strongest.
- **DOE targets** — the primary **Target Explanation Document** (PDF, downloaded and text-extracted
  2026-08-30), not just the EERE summary page. Full three-column target table, the system-level and
  end-of-service-life definitions, the 5.6 kg normalisation basis, and the complete revision history.
- **ML methodology citations** — all fourteen §3 DOIs resolved field-by-field against the Crossref API on
  2026-08-30. None was fabricated or mismatched.
- **DFT database sizes** — queried from each provider's own OPTIMADE API on 2026-08-30, not from secondary
  literature.
- **DFT-vs-experiment subsection** — was uncited domain knowledge; every claim now carries a source.
- **Project numbers** — this repo's `REPORT.md` and the archival `src/`, read 2026-08-29. Both were
  shown wrong and deleted by card #107 (tag `machine-model-archive`); current numbers are in
  `docs/chapter1-revision.md`.
- **Inverse design / generative AI** — `research/inverse-design-methods.md`, DOI-cited.

## Corrections applied to this skill

### From memo §2 (2026-08-29)

| Was | Now |
|---|---|
| BCC ~3 wt%, reversible ~2 | **~4 total, 1.9–2.3 reversible**; the too-stable V monohydride is the mechanism |
| AB2 dH −28 to −35 | **−24 to −41** across the ZrMn2 substitution range |
| AB5 ~1.4 wt% | 1.38 stoichiometric, **1.2 measured** |
| AB2 ~1.8–2 wt% | **1.77 max, 1.34–1.40 after 150 cycles** |
| LiBH4 ~18 wt% | 18.5 total, **13.8 desorbable** |
| dS = −130 as a constant | Approximation; **LaNi5 needs ≈ −103 to −108**. Wrong at tens-of-percent for a specific alloy |
| dH ≈ −39 kJ/mol H2 | **Arithmetic consequence** of the entropy constant, not a measurement. Design windows: 20–30, or −10 to −60 |

### From memo §§1, 3, 4 (2026-08-30)

| Was | Now | Module |
|---|---|---|
| Onboard capacity **5–13 kg H2** | **4–10 kg H2** — stated three times in the DOE TED; "5–13" is in neither the TED nor the EERE page | `hydrogen-storage-fundamentals.md` |
| Target column "**Ultimate Full Fleet**" | "**Ultimate**" — "Full Fleet" is the superseded 2009 label | `hydrogen-storage-fundamentals.md` |
| Two target columns (2025, Ultimate) | **Three: 2020, 2025, Ultimate**, plus the dormancy rows | `hydrogen-storage-fundamentals.md` |
| Balance of plant costs "**a factor of ~2 or worse**" gravimetrically | **Removed — unsourced.** The sourced framing (system includes all BOP; capacities are *usable*; targets met at *end of service life*) carries the argument without a multiplier | `hydrogen-storage-fundamentals.md` |
| "Revision date not stated — cite with an access date, never a year" | **Resolved: set 2003, last major revision 2009, table "updated May 2017"**; 2015 targets re-dated to 2025 after funding cuts; reviewed ~every 5 years | `hydrogen-storage-fundamentals.md` |
| "156 kWh/m3, 89.4%" **unverified, trace or drop** | **Traced** to [Malleswararao et al. 2020](https://doi.org/10.1016/j.ijhydene.2020.03.251) — and it is a **3-D COMSOL simulation, third cycle, 300 °C charge / 230 °C discharge**, not a measurement | `hydrogen-storage-fundamentals.md` |
| Materials Project **~186,743** | **154,387** structures (MP's own OPTIMADE API, 2026-08-30) | `computational-materials-informatics.md` |
| OQMD **~1,593,781** | **1,407,395** structures (OQMD's own OPTIMADE API, 2026-08-30) | `computational-materials-informatics.md` |
| AFLOW **~1,369,252** | **Unverified** — provider endpoint returned HTTP 500 on three attempts | `computational-materials-informatics.md` |
| HydPARK "**last updated 2002**" | **Unverified** — no source found. Argument restated without the date; primary citation is [Sandrock & Thomas 2001](https://doi.org/10.1007/s003390100770) | `computational-materials-informatics.md` |
| DFT section, **no citations at all** | Five claims, five sources; ZPE claim materially qualified (cancels in oxides, cannot be assumed to cancel in hydrides); added the formation-vs-decomposition-enthalpy trap | `computational-materials-informatics.md` |
| HyStor without volume/pages; "ML-driven alloy design" review without journal | *Int. J. Hydrogen Energy* **90**, 460–469; *Digital Twin* **2** | `ml-for-hydrides.md` |

## What is still NOT verified

1. **AFLOW entry count** — the provider's OPTIMADE `/v1/structures` returned HTTP 500 on three attempts on
   2026-08-30 while `/v1/info` responded normally. Retry the direct query. **Do not** fall back to the
   third-party linking-study figure: it was wrong for both providers that could be checked.
2. **A zero-point-energy magnitude for a named hydride.** That ZPE corrections are *necessary* for an
   intermetallic hydride is sourced, but only to a **preprint**
   ([Nadeau et al. 2025](https://doi.org/10.48550/arXiv.2509.05136)). No peer-reviewed kJ/mol figure was found;
   IOPscience blocked retrieval of the obvious source ([Wolverton et al. 2008](https://doi.org/10.1088/0953-8984/20/6/064228)).
3. **Deligöz & Özışık 2026** ([DOI](https://doi.org/10.1016/j.jpowsour.2026.240161)) — cited for the problem
   named in its title; no abstract is deposited with Crossref and the full text was not retrieved. Read the PDF
   before relying on its specific findings.
4. **Materials Project's 154,387** is much lower than counts quoted for MP elsewhere — most likely the OPTIMADE
   endpoint exposes a subset. Confirm with `mp-api` and a key before calling it "the size of Materials Project".
5. **HydPARK's "last updated 2002"** — see the correction table. The date is unsourced; the argument no longer
   depends on it.
6. **Malleswararao et al. 2022** long-term/buffer figures (532.64 MJ/m3 at 67.8%; 430.28 MJ/m3 at 91.2%) —
   abstract search-summary only. The group's [2024 experimental paper](https://doi.org/10.1016/j.ijhydene.2023.12.191)
   is the one to read for measured numbers.
7. **LaNi5 entropy tabulation** — [Sandrock 1999](https://doi.org/10.1016/S0925-8388(99)00384-9) is the standard
   table; full text not retrieved.
8. **Dematteis et al. 2021 activation numbers** (TiFe oxide ~20–30 nm, Ti4Fe2O mechanism) and **Sandrock's
   300 ppm poisoning experiments** — carried from search summaries of a publisher-blocked review.

## Open questions specific to this project

1. **Why does `temperature(K)` rank 21st of 22 by SHAP (0.001)** when it determines where on the PCT surface a
   measurement sits? Narrow within-family temperature spread? Correlation with composition features?
2. **Pressure is absent from the feature set** — now understood as a *physics gap*, not just a missing column:
   plateau slope makes measured capacity depend on measurement pressure, especially for the multi-element
   alloys dominating the modern data. This is also a grounded explanation for part of what CleanLab detects.
3. **No leave-one-alloy-class-out result exists yet.** Given Beltrame's cross-family finding, this remains the
   most important missing validation number in the thesis.
4. **The target is `H2_W% (max)`, not reversible capacity.** For V-rich BCC compositions that is roughly a
   factor-of-two overstatement of what a device would deliver. Worth stating explicitly — and note the DOE
   targets are defined on *usable* capacity, which makes it a two-step gap.

## Correction log

- 2026-08-30 — Re-researched `research/hydride-domain-grounding.md` §§1, 3, 4 to the standard of §2, in the
  main session (no subagent), against the DOE Target Explanation Document, the Crossref REST API, each database
  provider's OPTIMADE API, the arXiv API and the Semantic Scholar API. §2 was left byte-for-byte unchanged.
  Propagated into the modules:
  - **`hydrogen-storage-fundamentals.md`** — target table rebuilt from the TED (three columns, dormancy rows);
    **5–13 kg → 4–10 kg**; **"Ultimate Full Fleet" → "Ultimate"**; added the 5.6 kg normalisation basis and the
    *usable* / *end-of-service-life* definitions; **removed the unsourced "factor of ~2" balance-of-plant
    claim**; resolved the revision date (2003 / 2009 / May 2017).
  - **`computational-materials-informatics.md`** — database counts replaced with direct provider-API answers
    (**MP 186,743 → 154,387**, **OQMD 1,593,781 → 1,407,395**, **AFLOW → unverified, HTTP 500**); HydPARK's
    "last updated 2002" demoted to unverified and the surrounding argument restated without it; the DFT
    subsection given a citation per claim, with the ZPE claim qualified and a fifth claim added on the
    formation-vs-decomposition-enthalpy error.
  - **`ml-for-hydrides.md`** — completed two citations (HyStor volume/pages; *Digital Twin* journal name).
  - **Checked and left alone:** the MODNet line already said "on small datasets". The memo's stronger
    "below ~15,000 samples" was **not** supported by the paper's abstract and has been corrected *in the memo*;
    the module never carried it.
- 2026-08-29 — Rewrote `metal-hydride-families.md` against `research/hydride-domain-grounding.md` §2: seven
  numeric corrections (table above), added the three-definitions-of-capacity framing, the BCC monohydride
  mechanism, sourced hysteresis and degradation, and DOIs throughout.
- 2026-08-29 — Corrected two factual errors in `research/inverse-design-methods.md`, both verified against the
  pipeline's own outputs first:
  - **`StandardScaler` → `RobustScaler`** (2 places). Every live path in the archival `src/` (tag `machine-model-archive`) uses
    `RobustScaler`; the only `StandardScaler` occurrences are commented-out dead code in `Catboostmodel.py`.
  - **"12 selected descriptors" → "22"** (4 places). `feature_selection_report.csv` is 23 lines = header + 22,
    matching `REPORT.md` §3.3.
- 2026-08-29 — Replaced the upstream generic template (self-described "Legacy template awaiting research
  upgrade", confidence Low) with hydride-specialised content. Removed `modules/core-guidance.md`.
