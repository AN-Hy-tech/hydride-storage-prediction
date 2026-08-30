# PRD — Inverse Design of Metal-Hydride Compositions

**Master's thesis proposal · Faculty of Metallurgical and Materials Engineering, Shiraz University**
Researcher: Amirhossein Nasiri · Draft 2026-08-30 · Status: for supervisor review

---

## 1. Summary

The HydMS project has a working **forward** model: given a chemical formula and a temperature, it
predicts maximum gravimetric hydrogen storage capacity (wt%). This proposal covers the **inverse**
problem — given a desired capacity, which alloys should we make?

We propose to build that inverse capability in two stages: an uncertainty-aware virtual screening
system (**Architecture A**), then a constrained multi-objective evolutionary design system
(**Architecture B**) that produces a Pareto front trading capacity against raw-material cost and
chemical novelty. The distinguishing contribution is not the optimizer — the hydride literature
already uses genetic algorithms — but the **guard rails**: calibrated prediction intervals, an
explicit applicability domain, and honest cross-family validation that states where the surrogate can
and cannot be trusted.

---

## 2. Where we begin

### 2.1 What exists today

| Asset | State |
|---|---|
| Merged dataset (HyStor + ML-HydPARK) | 1,279 rows, 1,149 unique formulae, 10 alloy classes, 54 elements |
| Featurisation | CBFV composition statistics → 282 features → 22 selected |
| Forward models | 13 benchmarked regressors + stacking ensemble; Optuna-tuned CatBoost |
| Reported performance | Stacking ensemble: Val R² 0.939, Test R² 0.892, Test MAE 0.223 wt% |
| Interpretability | SHAP, PDP, Pearson/MI correlations, temperature-subgroup analysis |
| Written record | `REPORT.md` (full methodology + results), two research memos in `research/` |

For reference, the HyStor authors' own HYST model reports MAE 0.29 wt%, R² 0.79
([Wilson et al. 2024](https://doi.org/10.1016/j.ijhydene.2024.09.390)).

### 2.2 What a code audit found (2026-08-30)

An honest statement of the starting line. All five items are fixable and all are in scope for Phase 0.

1. **No trained artifacts are on disk.** The model, the fitted scaler and the data splits were never
   persisted to the repository. The pipeline must be re-run before anything can consume it.
2. **The pipeline does not currently run end-to-end.** Four broken links: the JARVIS featurisation
   script does not exist in the repository or its history; two scripts read from directories nothing
   writes; one script's output is never consumed; and feature selection reads the *pre*-outlier-removal
   splits, bypassing CleanLab and contradicting the written methodology.
3. **Three validation leaks.** The final model early-stops on the **test** set; feature selection runs
   on the full training set before cross-validation; and the best of 13 models × 100 trials is chosen
   partly on test score. The headline numbers are therefore optimistic by an unknown margin.
4. **No extrapolative validation.** The random split measures interpolation across chemical space.
   The literature's most important warning for this thesis is that hydride models generalise *within*
   an alloy family and poorly *across* families
   ([Beltrame et al. 2025](https://doi.org/10.3390/met15111221)).
5. **A licence problem in the dependency chain.** CBFV, which computes every descriptor, carries no
   licence at all — all rights reserved by default.

**These are not reasons to delay. Fixing them is the first phase, and reporting them is part of the
contribution.** A thesis that states its own validation limits is stronger than one that does not.

### 2.3 The one finding that makes the whole proposal viable

**All 22 selected features are pure composition statistics plus temperature.** No Miedema, no
WenAlloys, no structural descriptor survived feature selection. This means a candidate composition can
be featurised by a single forward function call — so the inverse problem never requires inverting the
descriptors, which would be mathematically ill-posed.

---

## 3. Where we are going

**Destination:** a reproducible, uncertainty-aware system that proposes and ranks *new* hydride
compositions, delivered as a documented Python package plus an interactive screening application,
with results defensible in a viva.

Concretely, at the end we will have:

1. A reproducible pipeline that runs from raw data to a calibrated surrogate with one command.
2. A capacity surrogate that emits **prediction intervals**, not point estimates.
3. A thermodynamics surrogate (ΔH, ΔS) placing every candidate on a temperature/pressure map.
4. A ranked candidate list for the AB₂ and AB₅ families, each entry reporting its predicted capacity
   interval, its distance to the nearest known alloy, its cost, and its physics-filter verdicts.
5. A Pareto front trading capacity against cost and novelty, with convergence and stability evidence.
6. An applicability-domain analysis stating where the model may and may not be believed.
7. A Streamlit application making all of the above inspectable.

---

## 4. The claim, and how we earn it

### 4.1 The claim

> We formulate hydride composition design as a **constrained multi-objective optimisation problem over
> the composition simplex**, solved with NSGA-II against an **uncertainty-calibrated** capacity
> surrogate, and report a **Pareto front** trading gravimetric capacity against raw-material cost and
> chemical novelty — accompanied by an explicit **applicability-domain analysis** that states where the
> surrogate can and cannot be trusted.

### 4.2 Why this is a contribution and not a repetition

The closest published work is directly comparable and does *not* do the last part:

| Study | Data scale | Inverse method | Uncertainty | Applicability domain |
|---|---|---|---|---|
| [Ji et al. 2025](https://doi.org/10.1039/d5ta06903c) | BCC MPEAs | ML + genetic algorithm | Not emphasised | Not emphasised |
| [Wu & Chen 2026](https://doi.org/10.3390/coatings16070794) | 95–901 records | Stacking + NSGA-II, 3000 candidates | Not emphasised | Not emphasised |
| [Liang et al. 2025](https://doi.org/10.1016/j.mtcomm.2025.113870) | 444 samples | AutoML + Whale Optimisation | Not emphasised | Not emphasised |
| [Lu et al. 2025 (FIND)](https://doi.org/10.20517/jmi.2025.56) | ~6000 records | VAE **+ GA** | Not emphasised | Not emphasised |
| **This work** | 1,279 rows | pymoo NSGA-II on the simplex | **Conformal intervals, LCB ranking** | **ElMD novelty + leave-one-class-out CV** |

The gap is real and it is the defensible part. Note also that Ji et al.'s author list includes Witman,
Allendorf and Stavila — the authors of the ML-HydPARK dataset this project already uses — so the
methodological sibling relationship is explicit.

### 4.3 How we earn it — the chain of evidence

Each link is a phase deliverable, and each is falsifiable:

1. **The surrogate is honest.** Leaks removed; test set touched once; conformal interval coverage
   measured against its nominal level. *Falsifiable: if coverage is badly off, the ranking signal is
   meaningless and we say so.*
2. **The surrogate's limits are stated.** Leave-one-alloy-class-out R² reported beside the random-split
   number. *We expect it to be substantially worse, and the honest gap is itself a result.*
3. **Candidates are real chemistry.** Optimisation happens in composition space, so every candidate is a
   valid composition by construction. Family stoichiometry, VEC windows and size-mismatch criteria are
   applied as constraints, family-specific rather than global.
4. **Candidates are ranked on what the model actually knows.** Ranking uses the lower confidence bound,
   never the mean, so uncertainty automatically penalises exotic candidates.
5. **"Novel" is a number, not an assertion.** Every candidate reports its Element Mover's Distance to
   the nearest known alloy, and is checked against external databases via OPTIMADE.
6. **The trade-off is shown, not hidden.** A Pareto front with hypervolume-versus-generation convergence
   and multi-seed stability, rather than a single cherry-picked alloy.

### 4.4 What we are explicitly *not* claiming

- **No experimental synthesis or validation.** This is a computational thesis. Candidates are
  *proposals*, not verified materials.
- **No system-level claim.** The model predicts *maximum material* gravimetric capacity. DOE targets
  are *system-level* and *usable* capacities measured at end of service life. Comparing our outputs to
  DOE targets without stating this would be a two-step overstatement.
- **No claim that capacity alone is sufficient.** Without pressure data the model cannot distinguish
  reversible from maximum capacity, which for BCC/V-based alloys is roughly a factor-of-two difference.

---

## 5. Users and user stories

**U1 — Researcher (primary).** Runs the screening and interprets the output.
**U2 — Supervisor / examiner.** Judges whether the method and its limits are sound.
**U3 — Experimental collaborator.** Decides whether a candidate is worth synthesising.
**U4 — Future student.** Inherits and extends the codebase.

| # | As a… | I want to… | So that… | Done when… |
|---|---|---|---|---|
| S1 | Researcher | run the whole pipeline from raw data with one command | results are reproducible and re-runnable after any change | one command produces a versioned artifact directory with a manifest recording git SHA, seeds and package versions |
| S2 | Researcher | get a prediction **interval**, not a single number | I can tell a confident prediction from a guess | the surrogate returns P10/P50/P90 with measured conformal coverage |
| S3 | Researcher | enumerate AB₂/AB₅ candidates over a chosen element set and screen them | I get a shortlist instead of a combinatorial explosion | a ranked CSV is produced with every filter verdict visible per candidate |
| S4 | Researcher | see how far each candidate is from anything already known | "novel" is measured rather than asserted | every candidate carries an ElMD distance to its nearest training neighbour |
| S5 | Researcher | trade capacity against cost and novelty rather than maximise one | the answer is not simply "the most Mg-rich alloy already in the literature" | a Pareto front is produced per element subset, with convergence evidence |
| S6 | Supervisor | see performance under a *family-held-out* split, not only a random one | I can judge whether candidates in a new family are trustworthy | leave-one-alloy-class-out R² is reported alongside random-split R² |
| S7 | Supervisor | see which decisions were made and why | the method can be examined rather than taken on faith | ADRs exist for the five hardest-to-reverse choices |
| S8 | Collaborator | know the predicted operating temperature and plateau pressure of a candidate | I can judge whether it is practically useful, not merely high-capacity | a ΔH/ΔS model places each candidate on a van 't Hoff map |
| S9 | Collaborator | filter candidates by cost and supply risk | I do not pursue an alloy that is unaffordable or unobtainable | cost and Herfindahl-Hirschman supply-risk indices are attached to every candidate |
| S10 | Collaborator | explore results without running code | I can engage with the work directly | a Streamlit application displays the ranked candidates and their filter verdicts |
| S11 | Future student | swap the target property without rewriting the pipeline | the work extends beyond this thesis | the thermodynamics model is trained by changing one configuration key |
| S12 | Future student | rely on the featuriser without a licence question | the code can be published and reused | the featuriser is reimplemented from citable sources under our own licence |

---

## 6. Scope

**In scope:** Phases 0/F/T/A/B below; AB₂ and AB₅ families; capacity + ΔH/ΔS surrogates; UQ and
applicability domain; cost and novelty objectives; Streamlit application; documentation (CONTEXT
glossary + ADRs).

**Out of scope for this thesis:** experimental synthesis; DFT calculations; generative models
(Architecture C, see §7); pressure as an input feature (no data); volumetric capacity; system-level
engineering; re-running the 13-model benchmark of `REPORT.md`.

---

## 7. Alternatives considered

### 7.1 Alternative inverse-design methods

| Alternative | Why not chosen |
|---|---|
| **Generative models** (VAE, GAN, diffusion) | Published materials generative models work at 10⁴–10⁶ training examples; MatterGen used ~600k structures, CDVAE's benchmark 45,231 crystals. We have 1,279 rows and only 1,149 distinct chemistries. Descriptor-based classical ML remains competitive below ~10⁴ samples ([Dunn et al. 2020](https://doi.org/10.1038/s41524-020-00406-3)). Decisive evidence: the one hydride paper that *did* use a VAE had ~5× our data and still bolted a genetic algorithm on top to actually produce candidates ([Lu et al. 2025](https://doi.org/10.20517/jmi.2025.56)). |
| **Inverting the descriptors** (optimise in feature space, then decode) | Composition → descriptor is many-to-one, so the inverse is ill-posed. It also lets the optimiser wander into descriptor vectors no composition can produce — the classic failure of unconstrained inverse design. Retained only as a possible *contrast experiment* to demonstrate why composition-space optimisation is correct. |
| **Bayesian optimisation / active learning** | Designed for the small-data regime and genuinely attractive — but its value is in choosing the *next experiment*. With no synthesis in scope, there is no loop to close. Reconsider if an experimental collaboration materialises. |
| **Swarm metaheuristics** (PSO, Whale Optimisation) | Works ([Liang et al. 2025](https://doi.org/10.1016/j.mtcomm.2025.113870)), but offers no advantage over NSGA-II while being less standard for multi-objective problems. |
| **Reinforcement learning** | Sample-hungry, no hydride precedent found, and no payoff over a genetic algorithm at this scale. |
| **LLM / agent-based design** | Promising for *literature data extraction* ([Zhang et al. 2026](https://doi.org/10.1039/d5sc09921h)), not for the optimisation itself. |
| **Enumeration only (Architecture A alone)** | A solid chapter but a thin thesis. It also breaks down as soon as the element set grows — which is precisely the signal to move to B. |

### 7.2 Alternative engineering choices

| Alternative | Why not chosen |
|---|---|
| **Reuse Witman et al.'s pretrained thermodynamics models** ([HEAhydrideMLv2](https://github.com/mwitman1/HEAhydrideMLv2)) | They exist and predict exactly what we need (ΔH, ΔS, ln p_eq, H/M). But: **no LICENSE file** (all rights reserved), last updated 2022, no dependency pins, built on data version v0.0.4 while we hold v0.0.5, and requiring their featuriser rather than ours. We train our own on the 772 complete rows already in the repository and cite theirs as the **benchmark**. |
| **Patch the existing pipeline's paths in place** | ~2–3 days versus ~5–7 for the rewrite. Rejected because both architectures need the featuriser as a *callable function*, not a script that reads a CSV — and this pipeline will be re-run every time the surrogate changes. |
| **Rewrite `Machine_Model/src/` in place** | Would orphan every number in `REPORT.md`. The old scripts stay as the archival record; new work lives in a new package. |
| **Full re-benchmark of all 13 models** | Most defensible, but 3–4 weeks before inverse design starts and it rewrites `REPORT.md` §§3–6. We fix the leaks, re-run selection once, and report old-versus-new as a comparison table. |
| **Optuna's NSGA-II sampler instead of pymoo** | Zero new dependencies, already installed. Rejected because the evolutionary algorithm *is* the thesis contribution, and pymoo provides the hypervolume and convergence diagnostics that chapter needs. |
| **Keep depending on CBFV** | Legal to install via pip, but it is unlicensed, unmaintained since 2022, and will break under NumPy 2.x. We reimplement the 22-feature calculation from citable element-property sources. |

---

## 8. Implementation

Sequential phases; each ends with a committed, runnable artifact. Effort is engineering judgement for
one developer already familiar with the codebase.

| Phase | Deliverable | Days |
|---|---|---|
| **0 — Provenance spike** | Identify which element-property table produces each of the 22 features. Hard stop gate: if any is unaccounted for, the reimplementation cannot begin. | 0.5 |
| **F — Featuriser** | `hydms/featurize/` — a licence-clean, batched, callable featuriser reproducing all 22 features. Sources: Oliynyk properties via [Lee et al. 2024](https://doi.org/10.1016/j.dib.2024.110178); JARVIS via [Choudhary et al. 2020](https://doi.org/10.1038/s41524-020-00440-1). **Acceptance: matches CBFV to 1e-9 on all 1,279 training formulae.** | 2–3 |
| **1 — Pipeline + surrogate** | `hydms/` config-driven package. Relative paths, one config file, versioned artifacts. Fix the CleanLab bypass and the test-set early stopping; re-run feature selection once; train CatBoost `MultiQuantile`; calibrate with MAPIE; add leave-one-alloy-class-out CV. | 5–7 |
| **T — Thermodynamics** | ΔH and ΔS surrogates on the 772 complete ML-HydPARK rows, same featuriser and validation code. `vant_hoff(ΔH, ΔS, T) → p_eq`. Sanity check: predicted ΔS must cluster near −130 J·mol⁻¹·K⁻¹. | 5–7 |
| **A — Screen-and-Rank** | Candidate enumeration (AB₂/AB₅, fraction grid 0.05, T grid 273–473 K), physics filters, ElMD novelty, cost + HHI, LCB ranking, Streamlit page. | 5–8 |
| **B — Multi-objective EA** | pymoo NSGA-II on the simplex with the element subset fixed per run and swept in an outer loop. Objectives: max LCB(capacity), min cost, max novelty; ΔH as a constraint window. Pareto fronts, hypervolume convergence, multi-seed stability, OPTIMADE novelty checks. | 18–25 |

**Total ≈ 36–51 developer-days (7–10 weeks focused work).**

**Documentation produced alongside:** a `CONTEXT.md` glossary pinning the terms that are easy to
conflate (candidate vs composition vs formula; *maximum material* capacity vs usable vs system;
surrogate vs reported production model; novelty vs uncertainty vs applicability domain), and five ADRs
covering the hardest-to-reverse decisions.

---

## 9. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **The optimiser exploits surrogate extrapolation.** A global optimiser maximising a tree ensemble will find regions where the model is confidently wrong, because tree ensembles extrapolate as constants and the optimiser hunts extremes. | **High** — this is *the* failure mode | Fatal to the result if unaddressed | LCB ranking, conformal intervals, applicability-domain ceiling, ElMD novelty filter. If the front is all exotic chemistry with wide intervals, tighten and re-run. Budget 2–3 such iterations and **report them as a result, not a setback**. |
| R2 | **Cross-family generalisation fails.** Hydride models are accurate within one family and poor across families ([Beltrame et al. 2025](https://doi.org/10.3390/met15111221)). | High | Limits how far candidates may stray | Restrict the search to AB₂/AB₅, where both capacity and thermodynamic data are densest (AB₂-family is 454 of 772 thermodynamic rows). Report leave-one-class-out R² and expect it to be much lower. |
| R3 | **The featuriser reimplementation does not match CBFV.** The composite descriptors could be built product-then-statistic or statistic-then-product. | Medium | Blocks Phases 1 onward | Phase 0 resolves the table mapping empirically; Phase F's acceptance test is exact numerical agreement. A day of slack is budgeted. |
| R4 | **Honest retraining lowers the headline numbers.** Removing three leaks may move test R² down from 0.951. | Medium–High | Cosmetic, not scientific | Report both, with the reason. A lower number that survives scrutiny is worth more than a higher one that does not. This is a presentation task, not a technical failure. |
| R5 | **Combinatorial blow-up in Architecture A.** 54 elements taken 4 at a time on a fine grid is billions of candidates. | Medium | Slows A | One family per run, 3–5 chemically motivated elements, coarse grid first. If still too large, that is precisely the signal to move to Architecture B. |
| R6 | **Featurisation throughput too slow for evolutionary search.** NSGA-II makes far more surrogate calls than enumeration. | Medium | Could force a redesign of B | **Measure throughput on day one of Phase A** — it determines whether enumeration or evolution is the right paradigm. Batch featurisation, never per-candidate loops. |
| R7 | **No experimental validation is possible.** | Certain | Bounds the claim | Stated up front as a scope limit (§4.4). Mitigated by OPTIMADE cross-checks and by following the standard close for computational inverse-design papers. |

---

## 10. Acceptance criteria

Fixed **before** results are seen, so that the outcome cannot be rationalised after the fact.

**Technical gates**

1. The pipeline runs end-to-end from `data/raw/` with one command, with no absolute paths, and
   re-running with the same seed reproduces identical metrics.
2. The reimplemented featuriser matches CBFV to 1e-9 on all 1,279 training formulae.
3. Conformal interval coverage on the held-out test set is within a few points of its nominal level.
4. Ten known training alloys fed through the screening path reproduce the trained model's predictions
   on those same rows — this catches scaler-refit and column-order bugs.
5. Predicted ΔS clusters near −130 J·mol⁻¹·K⁻¹.

**Scientific gates for the candidate list**

6. Leave-one-alloy-class-out R² is reported alongside the random-split number.
7. Every candidate reports **both** its ElMD distance to the nearest known alloy **and** its conformal
   interval width. No candidate is reported without both.
8. At least half of the top 20 candidates fall inside the applicability-domain ceiling and inside the
   family-specific VEC window. If fewer do, the guard rails are too weak: tighten and re-run.

---

## 11. Open questions for the supervisor

1. **Is a computational-only thesis acceptable**, or should we reserve time for an experimental
   collaboration? If synthesis becomes possible, Bayesian optimisation (§7.1) becomes the right method
   and the plan changes materially.
2. **AB₂ and AB₅ — the right families to target?** They are the best-populated in both datasets. Mg-based
   alloys have the highest capacities but the answers are likely to be already-known compositions.
3. **How should the honest-versus-published numbers be presented?** Our recommendation is a
   side-by-side table with the leaks named, in the methodology chapter.
4. **Is the Architecture C comparison worth attempting** if A and B finish early? A negative result —
   quantifying the data threshold below which generative approaches do not pay off for hydrides — would
   be publishable, but only if framed that way from the start.

---

## 12. Key references

1. Ji, K. *et al.* (2025). *Design of Lightweight BCC Multi-Principal Element Alloys with Enhanced
   Hydrogen Storage Using a Machine Learning-driven Genetic Algorithm.* **J. Mater. Chem. A** 13,
   41274. https://doi.org/10.1039/d5ta06903c
2. Lu, X. *et al.* (2025). *FIND: a forward–inverse navigation and discovery platform for hydrogen
   storage alloys.* **J. Mater. Inform.** 5. https://doi.org/10.20517/jmi.2025.56
3. Wu, Y.; Chen, X. (2026). *Stacking Ensemble Learning with Genetic Algorithm Optimization … Inverse
   Design of BCC-Type V-Based Hydrogen Storage Alloys.* **Coatings** 16, 794.
   https://doi.org/10.3390/coatings16070794
4. Liang, X. *et al.* (2025). *Machine learning and whale optimization algorithm for enhanced hydrogen
   storage alloy design.* **Mater. Today Commun.** 49, 113870.
   https://doi.org/10.1016/j.mtcomm.2025.113870
5. Beltrame, G. *et al.* (2025). *Application of Machine Learning and Data Augmentation Algorithms in
   the Discovery of Metal Hydrides for Hydrogen Storage.* **Metals** 15, 1221.
   https://doi.org/10.3390/met15111221
6. Witman, M. *et al.* (2020). *Extracting an Empirical Intermetallic Hydride Design Principle from
   Limited Data via Interpretable Machine Learning.* **J. Phys. Chem. Lett.** 11, 40.
   https://doi.org/10.1021/acs.jpclett.9b02971
7. Wilson, N. *et al.* (2024). *HyStor: An experimental database of hydrogen storage properties for
   various metal alloy classes.* **Int. J. Hydrogen Energy** 90, 460.
   https://doi.org/10.1016/j.ijhydene.2024.09.390
8. Deb, K. *et al.* (2002). *A fast and elitist multiobjective genetic algorithm: NSGA-II.*
   **IEEE Trans. Evol. Comput.** 6, 182. https://doi.org/10.1109/4235.996017
9. Angelopoulos, A. N.; Bates, S. (2023). *Conformal Prediction: A Gentle Introduction.*
   **Found. Trends Mach. Learn.** 16, 494. https://doi.org/10.1561/2200000101
10. Baird, S. G.; Diep, T. Q.; Sparks, T. D. (2022). *DiSCoVeR: a materials discovery screening tool
    for high performance, unique chemical compositions.* **Digital Discovery** 1, 226.
    https://doi.org/10.1039/d1dd00028d
11. Durdy, S. *et al.* (2022). *Random projections and kernelised leave one cluster out
    cross validation.* **Digital Discovery** 1, 763. https://doi.org/10.1039/d2dd00039c
12. Theler, G.; Kauwe, S. K.; Sparks, T. D. (2020). *Materials Cost and Supply Risk.*
    **Integr. Mater. Manuf. Innov.** 9, 144. https://doi.org/10.1007/s40192-020-00173-5

Full method landscape and library survey: `research/inverse-design-methods.md`.
Domain grounding, DOE targets and hydride physics: `research/hydride-domain-grounding.md`.
