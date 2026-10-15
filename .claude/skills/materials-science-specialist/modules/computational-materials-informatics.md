# Computational Materials Informatics

**Confidence**: 🟡 Medium. Database entry counts drift — figures below carry access dates and should be
re-checked against the provider before quoting in the thesis.

## Databases

### Hydrogen-specific (what this project actually uses)

| Database | Contents | Notes |
|---|---|---|
| **HyStor** | 1,282 metal alloys, max H₂ capacity at a given absorption temperature | 54 elements, 200–800 K. Curated HydPARK (831 entries) + 451 compositions added from articles and patents. Adds LEA/MEA/HEA classes. [Wilson et al. 2024](https://doi.org/10.1016/j.ijhydene.2024.09.390), [preprint](https://chemrxiv.org/doi/pdf/10.26434/chemrxiv-2024-6zkm0) |
| **HydPARK** | DOE/IEA metal-hydride database | Legacy; no longer maintained at its original Sandia host, many missing entries. Primary citation: [Sandrock & Thomas 2001, *Appl. Phys. A* 72, 153–155](https://doi.org/10.1007/s003390100770). **The frequently-repeated "last updated 2002" could not be sourced — do not state it as fact.** |
| **ML-HydPARK** | Cleaned CSV of compositions, capacities, thermodynamics | Parsed from HydPARK for ML use. [Zenodo](https://zenodo.org/records/7324809) |

HydPARK's status is important context, and the argument survives without the unsourced date: it is a legacy
database reachable today only through derived redistributions (ML-HydPARK, HyStor), and the largest curated
hydride dataset in the modern literature is still ~1,282 entries. This field's data scarcity is structural, not
incidental, and it is why 1,279 rows is a normal-sized hydride dataset rather than a small one.

### General DFT databases

Entry counts drift, and secondary sources get them wrong. These were read from **each provider's own OPTIMADE
API** (`meta.data_returned` on `/v1/structures`) on **2026-08-30**:

| Provider | Structures via its own OPTIMADE API | Note |
|---|---|---|
| **Materials Project** | **154,387** | [endpoint](https://optimade.materialsproject.org/v1/structures?page_limit=1). Lower than counts quoted for MP elsewhere — likely the OPTIMADE endpoint exposes a subset |
| **OQMD** | **1,407,395** | [endpoint](http://oqmd.org/optimade/v1/structures?page_limit=1). Same order as the "one million compounds" of [Shen et al. 2022](https://doi.org/10.1088/2515-7639/ac7ba9) |
| **AFLOW** | **unverified** | `/v1/structures` returned HTTP 500 on three attempts; the sibling `/v1/info` responded normally |

An earlier version of this module carried MP ~186,743, OQMD ~1,593,781 and AFLOW ~1,369,252 from a third-party
linking study. **Both figures that could be checked against the provider were wrong.** For the scale of drift,
[Kirklin et al. 2015](https://doi.org/10.1038/npjcompumats.2015.10) described OQMD as "nearly 300,000" DFT
calculations. **Quote a count only with its endpoint, its unit and its date** — "structures exposed via
OPTIMADE" is not the same thing as "materials in the database".

- **Materials Project** — RESTful API, JSON datasets; `mp-api` / pymatgen client.
- **OQMD** — DFT results across a very large compound set.
- **AFLOW** — high-throughput DFT, extensive prototype library.
- **OPTIMADE** — a common API spec across providers ([paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8361091/),
  [providers dashboard](https://www.optimade.org/providers-dashboard/)). Use this rather than writing
  one client per database.

**Cross-database consistency is not a given.** [Hegde et al. 2023, "Quantifying uncertainty in high-throughput
density functional theory: A comparison of AFLOW, Materials Project, and OQMD", *Phys. Rev. Materials* 7,
053805](https://doi.org/10.1103/PhysRevMaterials.7.053805) compares them directly. Do not pool values across
databases without addressing this.

## DFT for hydrides — and why it is not interchangeable with experiment

Typical workflow: structure → relaxation → total energies of metal, hydride and H₂ → formation enthalpy,
optionally phonons for zero-point and finite-temperature corrections.

The standard reference for this workflow applied to hydrogen storage is
[Wolverton, Siegel, Akbarzadeh & Ozoliņš 2008, *J. Phys.: Condens. Matter* 20, 064228](https://doi.org/10.1088/0953-8984/20/6/064228);
for the narrower question, [Andreasen, "Predicting formation enthalpies of metal hydrides", Risø-R-1484(EN),
Risø National Laboratory, 2004](https://www.osti.gov/etdeweb/servlets/purl/20553542).

Reasons DFT-computed and experimentally-measured capacities are **different quantities**:
1. **DFT gives a specific ordered structure at 0 K.** Experiment measures a real, possibly multiphase,
   defected sample at finite temperature under a given pressure
   ([Jain, Shin & Persson 2016, *Nat. Rev. Mater.* 1](https://doi.org/10.1038/natrevmats.2015.4)).
2. **Zero-point energy matters for hydrides — but do not assume a magnitude.** A first-principles study of the
   A₂B₇ intermetallic Nd₃MgNi₁₄ finds "both hybrid exchange-correlation functionals and zero-point energy
   corrections are necessary to obtain accurate absorption properties"
   ([Nadeau et al. 2025, arXiv:2509.05136](https://doi.org/10.48550/arXiv.2509.05136) — **preprint, not
   peer-reviewed**). The contrast matters: in oxides and halides the ZPE and thermal terms are "small and with
   different signs — largely canceling each other"
   ([Friedrich et al. 2019, *npj Comput. Mater.* 5](https://doi.org/10.1038/s41524-019-0192-1)). That
   cancellation **cannot be assumed for hydrides**, since H has the highest vibrational frequencies in the
   periodic table. A specific kJ/mol ZPE figure for a named hydride is **not yet sourced**.
3. **Functional dependence, quantified.** DFT-vs-experiment mean absolute error over 1,670 formation energies
   is **0.096 eV/atom** — but experiment-vs-experiment disagreement is **0.082 eV/atom**, so much of that gap
   is experimental uncertainty, not DFT error
   ([Kirklin et al. 2015, *npj Comput. Mater.* 1](https://doi.org/10.1038/npjcompumats.2015.10)). Corrections
   reach 27(24) meV/atom with SCAN — **benchmarked on oxides/halides, so that error bar does not transfer to
   hydrides** ([Friedrich et al. 2019](https://doi.org/10.1038/s41524-019-0192-1);
   [AFLOW-CCE 2021](https://doi.org/10.1103/PhysRevMaterials.5.043803)).
4. **Formation enthalpy is not decomposition enthalpy.** Substituting one for the other in van 't Hoff gives a
   wrong desorption temperature, and the error is common enough to have drawn a dedicated systematic review
   ([Deligöz & Özışık 2026, *J. Power Sources* 679, 240161](https://doi.org/10.1016/j.jpowsour.2026.240161)).
   If you mix a DFT enthalpy into a desorption-temperature argument, **say which enthalpy it is**.
5. **Theoretical vs usable capacity.** DFT naturally reports full stoichiometric occupancy; experiment reports
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
writing every stage's output under `reports/` is the right instinct — but only if the published numbers are
then checked against those files. The archival pipeline's were not, and disagreed with them
(`docs/archive/REPORT-RECONCILIATION.md`).
