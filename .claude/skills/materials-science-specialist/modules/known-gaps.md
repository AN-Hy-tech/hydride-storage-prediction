# Known Gaps and Validation Tasks

Rewritten 2026-08-29, replacing the upstream template's placeholder gaps.

## What is solid

- **DOE targets** — read from the [primary EERE page](https://www.energy.gov/eere/fuelcells/doe-technical-targets-onboard-hydrogen-storage-light-duty-vehicles) on 2026-08-29. System-level status confirmed from the page's own wording.
- **Project numbers** — read from this repo's `REPORT.md` and `Machine_Model/src/` on 2026-08-29.
- **Inverse design / generative AI** — derived from `research/inverse-design-methods.md`, itself DOI-cited against primary sources.
- **ML methodology claims** — Grinsztajn (NeurIPS 2022), Dunn/Matbench, MODNet, Beltrame, Durdy, Li et al., CleanLab all carry working citations.

## What is NOT verified

1. **Numeric ranges in `metal-hydride-families.md`** — capacities, enthalpy values and desorption temperatures
   per family are indicative textbook figures assembled without a primary source per number. **Verify each
   against a primary reference before putting it in the thesis.** The entropy constant (about -130 J/(mol H2 K))
   and the -39 kJ/mol H2 figure for 1 bar at 25 C are standard but uncited here.
2. **The Mg2Ni/LaNi5 thermal-storage figures** (156 kWh/m3, 89.4% efficiency) come from a search summary of
   review literature, not the primary source. Trace before quoting.
3. **Database entry counts** (Materials Project ~186,743 / OQMD ~1,593,781 / AFLOW ~1,369,252) come from a
   linking study via search summary, and sources disagree. Re-check against each provider directly.
4. **DOE target revision date** — the EERE page does not state it. Cite with an access date, not a year.
5. **Kinetics and degradation section** — mechanistically standard but uncited.
6. **`research/hydride-domain-grounding.md` was never written.** A background research agent was launched to
   produce a fully DOI-cited memo for hydrogen-storage fundamentals, hydride families, ML methodology and
   informatics, but it died on a session rate limit before writing anything. The modules here were written
   from targeted web searches instead — fewer sources and less depth than `research/inverse-design-methods.md`.
   **Re-running that research is the single highest-value next step for this skill.**

## Open questions specific to this project

1. **Why does `temperature(K)` rank 21st of 22 by SHAP (0.001)** when it is physically decisive for where on the
   PCT surface a measurement sits? Narrow within-family temperature spread? Correlation with composition
   features? Worth an explicit investigation — it is the kind of thing an examiner will ask.
2. **Pressure is absent from the feature set.** Capacity is a function of the full PCT surface; the model
   marginalises over whatever pressures the source measurements used. Quantify the cost, or state it as a limitation.
3. **No leave-one-alloy-class-out result exists yet.** Given Beltrame's cross-family finding, this is the most
   important missing validation number in the thesis.
4. ~~`research/inverse-design-methods.md` section 4.3 says `StandardScaler`~~ — **fixed 2026-08-29**, see correction log.

## Correction log

- 2026-08-29 — Corrected two factual errors in `research/inverse-design-methods.md`, both verified against the
  pipeline's own outputs before editing:
  - **`StandardScaler` → `RobustScaler`** (2 places, section 4.3 and the architecture diagram). Every live
    code path in `Machine_Model/src/` uses `RobustScaler`; the only `StandardScaler` occurrences in the repo
    are commented-out dead code in `Catboostmodel.py`.
  - **"12 selected descriptors" → "22"** (4 places). `Machine_Model/reports/feature_selection/feature_selection_report.csv`
    has 23 lines = header + 22 features, matching `REPORT.md` section 3.3. The descriptor list in section 4.3
    was also re-pointed at that CSV rather than "the project brief".
- 2026-08-29 — Replaced the upstream generic template (self-described "Legacy template awaiting research
  upgrade", confidence Low) with hydride-specialised content. Removed `modules/core-guidance.md`, whose
  content was a generic "you are an expert in this domain" prompt superseded by the new modules.
