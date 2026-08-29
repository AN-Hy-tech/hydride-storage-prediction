# Computational Materials Informatics

**Confidence**: 🟡 Medium. Database entry counts drift — figures below carry access dates and should be
re-checked against the provider before quoting in the thesis.

## Databases

### Hydrogen-specific (what this project actually uses)

| Database | Contents | Notes |
|---|---|---|
| **HyStor** | 1,282 metal alloys, max H₂ capacity at a given absorption temperature | 54 elements, 200–800 K. Curated HydPARK (831 entries) + 451 compositions added from articles and patents. Adds LEA/MEA/HEA classes. [Wilson et al. 2024](https://doi.org/10.1016/j.ijhydene.2024.09.390), [preprint](https://chemrxiv.org/doi/pdf/10.26434/chemrxiv-2024-6zkm0) |
| **HydPARK** | DOE metal-hydride database | **Last updated 2002**, many missing entries. Historically the only such database. |
| **ML-HydPARK** | Cleaned CSV of compositions, capacities, thermodynamics | Parsed from HydPARK for ML use. [Zenodo](https://zenodo.org/records/7324809) |

That HydPARK's last update is 2002 is important context: this field's data scarcity is structural, not
incidental, and it is why 1,279 rows is a normal-sized hydride dataset rather than a small one.

### General DFT databases

Entry counts vary by source and date — a Graph-ID linking study reported Materials Project ~186,743,
OQMD ~1,593,781 and AFLOW ~1,369,252 unique entries, while OQMD's own reflections paper discusses
[one million compounds](https://doi.org/10.1088/2515-7639/ac7ba9). **Quote a count only with its date and source.**

- **Materials Project** — RESTful API, JSON datasets; `mp-api` / pymatgen client.
- **OQMD** — DFT results across a very large compound set.
- **AFLOW** — high-throughput DFT, extensive prototype library.
- **OPTIMADE** — a common API spec across providers ([paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8361091/),
  [providers dashboard](https://www.optimade.org/providers-dashboard/)). Use this rather than writing
  one client per database.

**Cross-database consistency is not a given.** [Quantifying uncertainty in high-throughput DFT: AFLOW vs
Materials Project vs OQMD, *Phys. Rev. Materials* 7, 053805](https://doi.org/10.1103/PhysRevMaterials.7.053805)
compares them directly. Do not pool values across databases without addressing this.

## DFT for hydrides — and why it is not interchangeable with experiment

Typical workflow: structure → relaxation → total energies of metal, hydride and H₂ → formation enthalpy,
optionally phonons for zero-point and finite-temperature corrections.

Reasons DFT-computed and experimentally-measured capacities are **different quantities**:
1. **DFT gives a specific ordered structure at 0 K.** Experiment measures a real, possibly multiphase,
   defected sample at finite temperature under a given pressure.
2. **Zero-point energy is not negligible for hydrogen.** H is light; ZPE corrections materially shift hydride
   formation enthalpies and omitting them is a common error.
3. **Functional dependence.** GGA/PBE errors on H₂ and on metal-hydrogen bonding are systematic.
4. **Theoretical vs usable capacity.** DFT naturally reports full stoichiometric occupancy; experiment reports
   what is reversibly accessible in a pressure/temperature window. This is the LiBH₄-18-wt% trap again.

So: a DFT formation enthalpy is a good *screening* signal and a good physics cross-check on ML predictions.
It is not a label you can mix into an experimental training set without saying so.

## Active learning and experiment guidance

Bayesian optimization with a GP surrogate and an acquisition function works from tens of points and is designed
for exactly this regime — but it only pays off **if experiments will actually be run**. If the thesis is
computational-only, active learning is a chapter about a loop that never closes.
Cross-reference `modules/generative-ai-inverse-design.md` and `research/inverse-design-methods.md` §3.3.

## Tooling and reproducibility

- **pymatgen** — structures, composition parsing, database clients.
- **matminer** — featurizers ([Ward et al. 2018](https://doi.org/10.1016/j.commatsci.2018.05.018)).
- **ASE** — atomistic simulation environment, calculator interfaces.
- **atomate2 / jobflow** — reproducible high-throughput DFT workflows.
- **CBFV** — composition-based feature vectors, as used in this repo.
- [Abraham et al. 2026, *WIREs Comput. Mol. Sci.*, ML toolkits and frameworks for materials design](https://doi.org/10.1002/wcms.70067) — current landscape review.

**Provenance discipline for a thesis:** pin package versions; record which database snapshot and which date;
keep the fitted scaler and feature list as artefacts, not as things to be recomputed. This repo's habit of
writing every stage's output to `Machine_Model/reports/` is the right instinct — the numbers in the report can
be traced to the run that produced them.
