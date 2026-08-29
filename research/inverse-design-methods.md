# Inverse Design of Metal-Hydride Compositions: Method Landscape and Build Plan

**Scope.** Given the existing forward model in this repo (~1280 rows of `Composition` + `temperature(K)` → `H2_W% (max)`, CBFV/Magpie composition-averaged descriptors, Optuna-tuned CatBoost / ExtraTrees / stacking ensemble), what inverse-design methods exist in the hydride literature, which of them are actually buildable on top of *this* model, and with what tooling.

**Status:** research memo, no code written. Every factual claim below links to a primary source (peer-reviewed paper, official docs, or a package registry / repo API response). Claims I could not verify are explicitly marked **unverified**. Package versions and dates were read from the PyPI and GitHub REST APIs on 2026-08-29.

**On this folder.** The repo currently keeps prose at the root (`README.md`, `REPORT.md`), which describes the *forward* model that has been built. This document is forward-looking research about work that does not exist yet, so it does not belong in either. `research/` is proposed as the convention for literature reviews, method surveys and design memos — things that inform the code but do not document it. Future memos (e.g. a UQ calibration study, a database-integration survey) should land here too.

---

## 1. TL;DR

- **Build #1 (a week): forward-model-in-the-loop enumerate-and-screen.** Enumerate a large composition library over chemically sensible element subsets, featurize each candidate with the *existing* CBFV pipeline, predict with the *existing* CatBoost model, then filter by uncertainty + applicability domain + physics rules and rank. No new model, no inversion, no new maths. This is the shape of what [Ji et al. (2025, *J. Mater. Chem. A*)](https://doi.org/10.1039/d5ta06903c) and [Liang et al. (2025, *Mater. Today Commun.*)](https://doi.org/10.1016/j.mtcomm.2025.113870) actually did.
- **Build #2 (the thesis chapter): multi-objective evolutionary search in composition space.** NSGA-II/III over the composition simplex with the surrogate as the objective and physics rules as *constraints*, producing a Pareto front rather than a single "best" alloy. Precedent in hydrides: [Wu & Chen (2026, *Coatings*)](https://doi.org/10.3390/coatings16070794) screened 3000 candidates with NSGA-II on a 95–901-row dataset; [Zhou et al. (2025, *Adv. Sci.*)](https://doi.org/10.1002/advs.202513463) framed capacity-stability-cost explicitly as a Pareto problem.
- **Do not start with a VAE/GAN/diffusion model.** They are the wrong tool at 1280 rows. MatterGen trained on ~600k structures ([Zeni et al., 2025, *Nature*](https://doi.org/10.1038/s41586-025-08628-5)); CDVAE's MP-20 benchmark is 45,231 crystals ([Xie et al., ICLR 2022](https://arxiv.org/abs/2110.06197)); MatGAN trained on ICSD and was evaluated by generating 2 million samples ([Dan et al., 2020, *npj Comput. Mater.*](https://doi.org/10.1038/s41524-020-00352-0)). Even the one hydride paper that *does* use a VAE for inverse design had ~6000 records and still bolted a genetic algorithm on top to actually produce candidates ([Lu et al., 2025, *J. Mater. Inform.*](https://doi.org/10.20517/jmi.2025.56)).
- **The descriptors are not the problem — don't invert them.** `avg_*` / `dev_*` statistics are a many-to-one map from composition, so feature→composition inversion is ill-posed. Sidestep it entirely: optimize *in composition space* and recompute descriptors on the fly. The featurizer is cheap and this keeps every candidate on the physically valid manifold by construction.
- **Uncertainty and applicability domain are not optional extras — they are what stops the optimizer cheating.** A global optimizer will find and exploit extrapolation artifacts in a tree ensemble. CatBoost already ships `RMSEWithUncertainty`, `MultiQuantile` and virtual ensembles ([CatBoost docs](https://catboost.ai/docs/en/concepts/loss-functions-regression)); wrap with conformal intervals ([Angelopoulos & Bates, 2023](https://doi.org/10.1561/2200000101)) and an Element-Mover's-Distance novelty filter ([Baird et al., 2022, *Digital Discovery*](https://doi.org/10.1039/d1dd00028d)).

---

## 2. Method landscape

| Method | How it works | Data needed | Hydride papers using it | Fits this project? |
|---|---|---|---|---|
| **Enumerate-and-screen** (virtual high-throughput) | Generate a fixed library of candidate formulas, featurize, predict with surrogate, rank and filter | Only what the surrogate needs (~10²–10³) | [Ji et al. 2025](https://doi.org/10.1039/d5ta06903c) (framework precursor); [Beltrame et al. 2025](https://doi.org/10.3390/met15111221) (806 entries) | **Yes** — MVP |
| **GA / evolutionary search on surrogate** | Population of compositions evolved against surrogate-predicted fitness | Same as surrogate; GA itself needs none | [Ji et al. 2025](https://doi.org/10.1039/d5ta06903c) (ML+GA, lightweight BCC MPEAs); [Lu et al. 2025](https://doi.org/10.20517/jmi.2025.56) (GA, pop 200) | **Yes** |
| **Multi-objective EA (NSGA-II/III)** | Non-dominated sorting → Pareto front over competing objectives | Same as surrogate | [Wu & Chen 2026](https://doi.org/10.3390/coatings16070794) (NSGA-II, 3000 candidates); [Zhou et al. 2025](https://doi.org/10.1002/advs.202513463) (capacity/stability/cost) | **Yes** — best thesis chapter |
| **Swarm / metaheuristics (PSO, WOA)** | Non-gradient global search on surrogate | Same as surrogate | [Liang et al. 2025](https://doi.org/10.1016/j.mtcomm.2025.113870) (Whale Optimization, 444 samples → 20 candidates) | Yes, but no advantage over NSGA-II |
| **Bayesian optimization / active learning** | GP surrogate + acquisition function balancing exploit/explore; suggests next *experiment* | Works from tens of points; designed for small data | [Xue et al. 2016](https://doi.org/10.1038/ncomms11241) and [Gopakumar et al. 2018](https://doi.org/10.1038/s41598-018-21936-3) (alloys, not hydrides); hydride-specific BO **unverified** | **Maybe** — only if experiments will actually be run |
| **VAE / conditional VAE** | Encode composition to continuous latent, sample/optimize in latent, decode | 10⁴+ typical | [Lu et al. 2025](https://doi.org/10.20517/jmi.2025.56) (VAE, 134→3 latent, ~6000 records) | **No** at 1280 rows |
| **GAN (MatGAN, CubicGAN, CCDCGAN)** | Generator/discriminator adversarial sampling of composition or structure space | 10⁴–10⁶ | None hydride-specific found | **No** |
| **Diffusion (MatterGen, CDVAE, DiffCSP)** | Denoising generative process over atoms/lattice, property-conditioned via fine-tuning | ~10⁵–10⁶ | None hydride-specific found | **No** |
| **Invertible NN / normalizing flow (cINN)** | Learns a bijection property↔design, samples the full multimodal solution set | 10³–10⁴, task-dependent | None hydride-specific found | **Maybe** — interesting stretch goal |
| **Reinforcement learning** | Agent builds/edits a composition, rewarded by surrogate | Sample-hungry, but works with a surrogate environment | None hydride-specific found; [Karpovich et al. 2024](https://doi.org/10.1038/s41524-024-01474-5), [Yu et al. 2026](https://doi.org/10.1038/s41524-025-01894-x) (general inorganics) | **No** — no payoff over GA here |
| **LLM / agent-based** | Agents mine literature, propose and screen candidates | N/A (uses literature) | [Zhang et al. 2026, *Chem. Sci.*](https://doi.org/10.1039/d5sc09921h) (DIVE, hydrogen storage) | **Maybe** — for data extraction, not design |

---

## 3. Inverse design applied to hydrogen storage and metal hydrides

### 3.1 Surrogate + global optimizer — the dominant pattern

This is what the hydride field actually does. Four concrete, recent papers:

**Ji, Banerjee, Witman, Allendorf, Stavila & Singh (2025)**, *Design of Lightweight BCC Multi-Principal Element Alloys with Enhanced Hydrogen Storage Using a Machine Learning-driven Genetic Algorithm*, [*J. Mater. Chem. A* 13, 41274–41289](https://doi.org/10.1039/d5ta06903c). They interface ML models with a genetic algorithm as a "metaheuristic optimizer high-throughput framework", predicting hydrogen affinity, storage capacity and phase stability for BCC MPEAs over the element set {Mg, Al, Ti, V, Cr, Mn, Fe, Co, Ni, Cu, Nb, Mo}. Reported outputs include five new MPEAs at ≥3.5 wt% H, e.g. Cr₀.₀₉Mg₀.₇₃Ti₀.₁₈ (4.25 wt%) and Cr₀.₂₁Nb₀.₁₁Ti₀.₃₅V₀.₃₃ (3.5 wt%). Note the author list — Witman, Allendorf and Stavila are the authors of the ML-HydPARK dataset this project already uses, so this is the closest methodological sibling to the proposed work. (An open-access copy is indexed at [eScholarship](https://escholarship.org/uc/item/7x46t47g); the exact GA population/crossover settings and the phase-stability filter thresholds are **unverified** — both publisher and repository copies blocked automated retrieval, so read the PDF manually before replicating.)

**Lu, Luo, Li, Chen, Yao, Xu, Yan & Li (2025)**, *FIND: a forward–inverse navigation and discovery platform for hydrogen storage alloys*, [*J. Mater. Inform.* 5](https://doi.org/10.20517/jmi.2025.56). The single most relevant paper for this project's ambitions, because it builds exactly the "research application" being contemplated.
- Forward module: XGBoost, CatBoost, Random Forest and Gradient Boosting inside a `MultiOutputRegressor`, predicting plateau pressure, enthalpy, entropy and max capacity.
- Data: >1000 alloy systems, >6000 valid records, literature 2001–2024, 40 metallic elements.
- Features: 132 Magpie descriptors + temperature = 133 input dimensions. **Note the near-identity with this project's featurization.**
- Inverse module: a VAE mapping 134-dim input to a **3-dimensional latent space**, supporting temperature-conditioned generation, latent interpolation and noise-injected sampling — *plus* a genetic algorithm (population 200, Dirichlet-based hybrid initialization, crossover 0.8, adaptive mutation 0.3, tournament selection, top-10% elitism).
- Result: 27 unreported compositions in Mg–Ni–La–Ce / Mg–Ni–La targeting ≥6 wt% at ~450 K. External validation was against *published* measurements for La₀.₆MgₓNi₃.₄₅Nd₀.₁; **no new alloy was synthesized**.
- A bilingual web app was released at `find4hyalloy.zicp.fun` (liveness **unverified** — not fetched).

The lesson to draw: even with ~5× this project's data, the authors did not trust the VAE alone to produce candidates. The GA did the work.

**Wu & Chen (2026)**, *Stacking Ensemble Learning with Genetic Algorithm Optimization for Multi-Property Prediction and Inverse Design of BCC-Type V-Based Hydrogen Storage Alloys*, [*Coatings* 16, 794](https://doi.org/10.3390/coatings16070794). Directly relevant on two counts. First, the data scale — **95–901 experimental records across 17 alloying elements**, i.e. smaller than this project — and it still achieved 5-fold CV R² of 0.865–0.981 (desorption plateau pressure R² = 0.981). Second, the inverse step used **NSGA-II** to screen 3000 candidate compositions, converging on the V–Ti–Cr–Fe–Mn system, with first-principles calculations used to check thermodynamic stability of the recommendations. SHAP identified valence electron concentration and atomic size mismatch as the dominant features — the same physics-descriptor family already in this project's feature set.

**Liang, Liu, Zhang, Qiu, Fan, Liu & Yan (2025)**, *Machine learning and whale optimization algorithm for enhanced hydrogen storage alloy design*, [*Mater. Today Commun.* 49, 113870](https://doi.org/10.1016/j.mtcomm.2025.113870). **444 alloy samples**, seven categories, 16 elements as input features. AutoML (TPOT) selected Extremely Randomized Trees, R² = 0.84 for capacity; a GBDT classifier reached 96.3% on alloy type. The Whale Optimization Algorithm then produced 20 candidates, of which V₀.₆Ti₀.₂Cu₀.₁₅Y₀.₀₅ (3.137 wt%) and Mg₀.₇Cr₀.₁La₀.₁₅Al₀.₀₅ (4.138 wt%) were validated to within 10% prediction error. This is a *smaller-than-this-project* dataset yielding a publishable inverse-design result — the strongest single piece of evidence that the proposed work is feasible at 1280 rows.

### 3.2 Multi-objective and Pareto framing in hydrides

**Zhou et al. (2025)**, *Resolving the Capacity-Stability-Cost Trilemma in Multi-Principal-Element Hydrogen Storage Alloys Through Multi-Objective Optimization*, [*Adv. Sci.* 12, e13463](https://doi.org/10.1002/advs.202513463). Names the trilemma explicitly as "a fundamental Pareto-type challenge" and criticises the field for "fragmented" single-parameter optimization. Their optimized Ti₀.₈Zr₀.₂₂Mn₁.₂₂Cr₀.₅₃(VFe)₀.₂₅ C14 Laves MPEA reached 2.06 wt% at 20 °C under 1.6 MPa. Useful as the *motivating* citation for a multi-objective chapter, though the screening there was elemental/compositional rather than an EA over a surrogate.

Practical target windows quoted in the multi-objective hydride literature — desorption plateau ~0.1–1 MPa at room temperature, effective capacity >1.5 wt%, >90% retention over ≥100 cycles, desorption enthalpy −20 to −40 kJ mol⁻¹ H₂ — are useful as constraint bounds. Note that **this project's model predicts only capacity**, so plateau-pressure and cycling objectives are not available without a second model or a proxy.

### 3.3 Bayesian optimization and active learning

No hydride-specific BO paper surfaced in this search (**unverified** whether one exists). The canonical small-data alloy references are:
- [Xue et al. (2016), *Nat. Commun.* 7, 11241](https://doi.org/10.1038/ncomms11241) — adaptive design found new NiTi-based alloys with the smallest thermal dissipation, using uncertainty to trade off exploration against exploitation.
- [Gopakumar et al. (2018), *Sci. Rep.* 8, 3738](https://doi.org/10.1038/s41598-018-21936-3) — multi-objective adaptive design for materials discovery.

The important distinction: **BO is for choosing the next experiment, not for mining a fixed surrogate.** If this thesis includes no synthesis loop, BO's core value proposition is absent and a GA/NSGA-II sweep is strictly simpler. If a collaborator *will* synthesize a handful of alloys, invert this judgement — BO becomes the correct method and the thesis becomes much stronger.

### 3.4 Generative models

Applied to hydrides: essentially only the FIND VAE above, and a generative framework in [*Int. J. Hydrogen Energy*](https://www.sciencedirect.com/science/article/abs/pii/S0360319926003812) combining causal discovery with generative modelling plus a rule-based filter for economically infeasible compounds (publisher blocked retrieval; details **unverified**).

The general-purpose generative toolkit and its data appetite:

| Model | Reference | Training data scale |
|---|---|---|
| iMatGen | [Noh et al. 2019, *Matter* 1, 1370](https://doi.org/10.1016/j.matt.2019.08.017) | Single V–O system |
| MatGAN | [Dan et al. 2020, *npj Comput. Mater.* 6, 84](https://doi.org/10.1038/s41524-020-00352-0) | ICSD; 92.53% novelty over 2M generated samples |
| CubicGAN | [Zhao et al. 2021, *Adv. Sci.* 8, 2100566](https://doi.org/10.1002/advs.202100566) | >370,000 ternary materials |
| FTCP | [Ren et al. 2022, *Matter* 5, 314](https://doi.org/10.1016/j.matt.2021.11.032) | Invertible crystal representation + VAE |
| CDVAE | [Xie et al., ICLR 2022](https://arxiv.org/abs/2110.06197) | MP-20 = 45,231 crystals, 89 elements |
| MatterGen | [Zeni et al. 2025, *Nature* 639, 624](https://doi.org/10.1038/s41586-025-08628-5) | Alex-MP-20, ~600k structures |

A GAN/diffusion review for materials is available in [Jiang et al. (2024), *Mater. Genome Eng. Adv.* 2, e30](https://doi.org/10.1002/mgea.30).

### 3.5 Invertible NNs and normalizing flows

Conditional invertible NNs (cINN) are the theoretically *correct* answer to a one-to-many inverse problem: they learn a bijection and sample the full multimodal solution set rather than collapsing to one mode. Demonstrated for [multilayer thin films](https://doi.org/10.1088/2632-2153/acb48d) and [inverse photonic design](https://arxiv.org/abs/2208.14212), and for [microstructure design via conditional continuous normalizing flows](https://www.sciencedirect.com/science/article/pii/S1359645424010528). No hydride application found (**unverified**). Worth a paragraph in the thesis as "the principled alternative we did not have data for", not a build target.

### 3.6 Reinforcement learning

[Karpovich, Pan & Olivetti (2024), *npj Comput. Mater.* 10, 287](https://doi.org/10.1038/s41524-024-01474-5) apply deep RL to inverse inorganic materials design with multi-objective rewards over band gap, formation energy and bulk/shear modulus plus synthesis objectives. [Yu et al. (2026), *npj Comput. Mater.* 12](https://doi.org/10.1038/s41524-025-01894-x) (AIMatDesign) targets exactly the data-scarcity regime, augmenting experimental data via difference-based sampling into a "trusted experience pool", validated by synthesizing Zr-based bulk metallic glasses. RL is defensible here but buys nothing a GA does not, at much higher implementation cost.

### 3.7 LLM / agent approaches

[Zhang et al. (2026), *Chem. Sci.* 17, 3031–3042](https://doi.org/10.1039/d5sc09921h) — "DIVE" multi-agent workflow reads experimental data out of *graphical elements* in the hydrogen-storage literature, improving extraction accuracy 10–15% over commercial multimodal models and >30% over open-source ones, building a database of 30,000+ entries from 4,000 publications. The relevance here is **data acquisition, not design**: if the thesis needs more than 1280 rows, this is the published route to getting them.

### 3.8 High-entropy alloy hydrides

Very active and directly relevant to compositional search, because HEA design *is* a composition-space problem:
- [Halpren, Yao, Chen & Singh (2024), *Acta Mater.* 270, 119841](https://doi.org/10.1016/j.actamat.2024.119841) — ML-assisted design of BCC HEAs for room-temperature hydrogen storage.
- [Mahanta et al. (2025), *J. Energy Storage* 139, 118865](https://doi.org/10.1016/j.est.2025.118865) — ML prediction of HEAs for hydrogen storage with optimized thermodynamic and kinetic parameters.
- [Kurbanbekov et al. (2026), *Metals* 16, 577](https://doi.org/10.3390/met16060577) — review, fundamental principles to directed design strategies.
- [Liu et al. (2025), *Digital Twin* 2](https://doi.org/10.1080/27525783.2025.2511889) — review of ML-driven alloy digital design for hydrogen storage (publisher blocked retrieval; contents **unverified**, but it is the natural review to cite).

This matters practically: the HyStor dataset already contains LEA, MEA and HEA classes that HydPark lacked ([Wilson et al. 2024](https://doi.org/10.1016/j.ijhydene.2024.09.390)), so these families are represented in this project's training data and are legitimate search targets.

---

## 4. What actually fits a 1280-row, composition-averaged, tree-ensemble model

### 4.1 Why not generative models

Two independent arguments, both citable.

**The generative-model scale argument.** The table in §3.4 shows the working range of published materials generative models sits at 10⁴–10⁶ training examples. This project has ~1280 rows, and — critically — those rows are not 1280 distinct chemistries; `split_data.py` in this repo works on `unique_formulae`, so the *effective* chemical diversity is lower still. Generative models fail on small data specifically because the discriminator/decoder overfits the training examples, which is the failure mode identified for [GANs with limited data](https://papers.nips.cc/paper/2020/file/8d30aa96e72440759f74bd2306c1fa3d-Paper.pdf).

**The materials-ML crossover argument.** [Dunn et al. (2020), *npj Comput. Mater.* 6, 138](https://doi.org/10.1038/s41524-020-00406-3) built Matbench (13 tasks, 312 to 132k samples) and found descriptor-based classical ML remains competitive below roughly 10⁴ samples, with graph/deep networks pulling ahead above it. [De Breuck, Hautier & Rignanese (2021), *npj Comput. Mater.* 7](https://doi.org/10.1038/s41524-021-00552-2) built MODNet explicitly because "current machine-learning approaches generally require large amounts of data", and it outperforms graph networks on small datasets — their benchmark effort focused on the Matbench tasks with **fewer than 15,000 samples**. If a *discriminative* deep model is marginal at 1280 rows, a *generative* one is hopeless.

**The hydride-specific argument.** [Beltrame, Dematteis, Stavila, Rizzi, Baricco & Palumbo (2025), *Metals* 15, 1221](https://doi.org/10.3390/met15111221) expanded a hydride dataset from ~400 to 806 entries and studied the effect of dataset size and PADRE data augmentation directly. Their findings are a warning label for this project: accuracy improved markedly with dataset size; **augmentation helped only on the smaller datasets** and did not help in underrepresented pressure regimes; and clustering + cross-validation showed **limited generalizability across material classes**, with high accuracy only when training and testing *within* one hydride family (e.g. AB2). That last point is the single most important caveat for inverse design here — see §4.5.

### 4.2 Why generate-and-screen / surrogate-guided optimization is the realistic first build

- It reuses everything already built. No new model to train, no new validation burden.
- Every hydride inverse-design paper found in §3.1 is some version of it.
- Failure modes are visible and debuggable: you can print the candidate, its features, its prediction, its uncertainty and its filter verdicts.
- It scales down gracefully. A brute-force enumeration is a valid week-one deliverable; NSGA-II is a drop-in upgrade when the enumeration gets too big.

### 4.3 Handling the non-invertibility of `avg_*` / `dev_*` descriptors

The constraint is real: composition → descriptor is a well-defined function, but many-to-one, so descriptor → composition is ill-posed. Two strategies exist, and one clearly wins.

**Option A — optimize in composition space, recompute descriptors on the fly. Recommended.**
Parameterize a candidate as (element subset, fractions on the simplex, temperature). For each candidate: build the formula string → run `CBFV.composition.generate_features` → subset to the 22 selected descriptors → predict. The map is only ever evaluated *forwards*, so inversion never happens and **every candidate is a real composition by construction**. This is what `extract_features_cbfv.py` already does, just called per-candidate instead of once over a CSV.

Practical checks before building:
1. Confirm all 22 final descriptors are pure CBFV/Magpie composition statistics. From the names in `Machine_Model/reports/feature_selection/feature_selection_report.csv` (`avg_polzbl_divi_atom_mass`, `dev_Zunger_radii_sum`, `dev_Pauling_Electronegativity`, `avg_valence_d`, `avg_is_alkaline`, `dev_atom_mass_mult_therm_cond`, `dev_specific_heat`, `dev_bp_divi_atom_mass`, `dev_Covalent_Radius`, `dev_gilmor_number_of_valence_electron`, plus `range_*` statistics and `temperature(K)`) they appear to be — but if any hand-engineered physics feature (Miedema ΔH, shear-modulus mismatch, VEC) survived into the final set, its computation must be reimplemented as a callable, not read from a precomputed table.
2. Reuse the *exact* fitted `RobustScaler` from training. Refitting on candidates is a silent correctness bug.
3. Benchmark featurization throughput. `generate_features` has per-call overhead; batch candidates (featurize 10⁴ formulas in one call) rather than looping one at a time.

**Option B — invert in feature space, then decode by matching.** Optimize the 22 descriptors freely, then find the composition whose descriptors are nearest. This requires a decoding step against an enumerated library anyway, and in between it lets the optimizer wander into descriptor vectors that no composition can produce — the classic failure of unconstrained inverse design. Only worth doing as a *contrast experiment* in the thesis to demonstrate why Option A is correct.

### 4.4 Uncertainty quantification — the guard rail

A global optimizer maximizing a tree ensemble will find regions where the model is confidently wrong, because tree ensembles extrapolate as constants and the optimizer is explicitly hunting for extremes. Ranking by predicted mean alone is the single most likely way this project produces nonsense. Options, roughly in order of effort:

- **CatBoost native.** Already a project dependency. [Official docs](https://catboost.ai/docs/en/concepts/loss-functions-regression) confirm `Quantile`, `MultiQuantile` (one model, many quantiles, no GPU support) and `RMSEWithUncertainty` (returns estimated mean *and* variance, optimizing negative log-likelihood with natural gradients, similar in spirit to NGBoost). CatBoost also supports **virtual ensembles**, obtaining several predictions from a single trained model by truncation — cheaper than training an ensemble. Lowest-friction option by a wide margin.
- **Conformal prediction.** Distribution-free, finite-sample coverage guarantees on top of *any* point model — including the existing stacking ensemble. Reference: [Angelopoulos & Bates (2023), *Found. Trends Mach. Learn.* 16, 494–591](https://doi.org/10.1561/2200000101). Implementations: [MAPIE](https://github.com/scikit-learn-contrib/MAPIE) (v1.5.0, BSD-3, 1584 stars, actively pushed 2026-08-14) and [crepes](https://pypi.org/project/crepes/) (v0.9.1, BSD). Conformal is also the standard way to operationalize applicability domain in cheminformatics.
- **NGBoost.** [Duan et al., ICML 2020](https://proceedings.mlr.press/v119/duan20a.html) — natural gradient boosting for full probabilistic prediction. PyPI v0.5.11, Apache-2.0, last release 2026-06-26. Use if a second, independent probabilistic model is wanted for comparison.
- **Ensemble variance.** Disagreement across the existing 13-model benchmark, or across CV folds, is a free and interpretable uncertainty proxy. Weakest guarantees, zero implementation cost.

Recommended combination: **CatBoost `RMSEWithUncertainty` or `MultiQuantile` for the ranking signal, conformalized via MAPIE for honest intervals.** Then rank candidates by a *lower confidence bound* (e.g. the 10th-percentile prediction), not the mean. This automatically penalizes candidates the model is unsure about, without any extra machinery.

### 4.5 Applicability domain and novelty control

The Beltrame result (§4.1) — models generalize within an alloy family but not across families — means a candidate from an unfamiliar corner of composition space is not merely uncertain, it is *out of scope*. Three complementary screens:

- **Element Mover's Distance to the training set.** ElMD gives chemically intuitive composition-to-composition distances along a modified Pettifor scale ([repo](https://github.com/lrcfmd/ElMD), GPL-3.0, v0.5.15, pushed 2026-08-20). [DiSCoVeR / `mat_discover`](https://doi.org/10.1039/d1dd00028d) (Baird, Diep & Sparks, 2022, *Digital Discovery* 1, 226–240) combines ElMD with DensMAP + HDBSCAN* clustering specifically to trade off *performance against chemical novelty* — which is exactly the knob this project needs. Note maintenance: `mat_discover` last PyPI release 2023-06-23 (v2.2.9), last GitHub push 2024-08-20; usable, not actively developed.
- **Alloy-class membership.** The dataset already carries `Alloy_class`. Require a candidate to be assignable to a known class, or flag it loudly.
- **Extrapolative validation before you trust any of it.** Report leave-one-cluster-out CV ([Durdy et al. 2022, *Digital Discovery* 1, 763–778](https://doi.org/10.1039/d2dd00039c)) or leave-one-alloy-class-out alongside the existing random-split R². This repo's `split_data.py` already splits on *unique formulae* with stratification, which is genuinely good practice and better than most published hydride ML — but a formula-disjoint random split still measures interpolation across the chemical space, not extrapolation into new families. [Li et al. (2025), *Commun. Mater.* 6, 9](https://doi.org/10.1038/s43246-024-00731-w) analyzed 700+ OOD tasks and found heuristic criteria "mostly test interpolation rather than true extrapolation". **Expect the class-held-out R² to be substantially lower than 0.951, and say so in the thesis.** That honesty is itself a contribution.

### 4.6 Multi-objective optimization

Single-objective "maximize wt%" produces Mg-rich answers that are already known and thermodynamically inconvenient. The interesting thesis result is a Pareto front. Candidate objectives, and what this project can currently support:

| Objective | Available now? |
|---|---|
| Gravimetric capacity (wt%) | **Yes** — the existing model |
| Operating/desorption temperature | Partly — temperature is an *input*, so you can constrain it, but not predict a desorption temperature without a ΔH model |
| Plateau pressure / ΔH, ΔS | **No** — needs a second model. ML-HydPARK carries thermodynamic values, so this is buildable |
| Raw-material cost | **Yes** — deterministic from composition + price table |
| Volumetric density | Partly — needs density estimates or a lattice model |
| Chemical novelty (ElMD distance) | **Yes** — deterministic |
| Prediction uncertainty | **Yes** — from §4.4 |

A defensible and fully buildable three-objective problem *today*: **maximize LCB(capacity), minimize cost, maximize novelty**, subject to physics constraints. Adding a ΔH/plateau-pressure model from ML-HydPARK upgrades it to the physically complete formulation and is the natural second thesis chapter.

Algorithms: NSGA-II ([Deb et al. 2002, *IEEE Trans. Evol. Comput.* 6, 182–197](https://doi.org/10.1109/4235.996017)) for 2–3 objectives; NSGA-III for 4+, where reference-point-based selection maintains a uniform spread better than crowding distance. For expensive objectives, qEHVI / qNEHVI ([Daulton, Balandat & Bakshy, NeurIPS 2020](https://arxiv.org/abs/2006.05078); [BoTorch multi-objective docs](https://botorch.org/docs/multi_objective)) — but note that here the objectives are a *cheap* surrogate call, which is precisely the regime where an EA beats Bayesian optimization. Use NSGA-II/III.

---

## 5. Constraints and physical validity filters

Generated formulas must be screened or they are just numbers. Layered, cheapest first.

### 5.1 Compositional and structural rules

- **Simplex constraint.** Fractions sum to 1, each ≥ 0, and impose a minimum non-zero fraction (e.g. ≥0.01) so you don't emit meaningless trace elements. Cap the number of distinct elements to match the target family.
- **Family stoichiometry.** Enforce A:B ratios for the family being searched — AB₅, AB₂, AB, A₂B — rather than searching a free simplex. This is the highest-value single filter: it collapses the space and guarantees candidates look like real hydride chemistry.
- **Valence electron concentration windows.** VEC is a workhorse rule with real numbers behind it. For phase selection, [Guo, Ng, Lu & Liu (2011), *J. Appl. Phys.* 109, 103505](https://doi.org/10.1063/1.3587228) established the FCC/BCC VEC boundaries (sole BCC below ~6.87, sole FCC above ~8.0, mixed in between). For AB₂-type hydrogen storage alloys specifically, published design criteria include **VEC 6.2–6.5**, atomic size mismatch δ ≥ 9.7%, and hydride-forming/non-forming radius ratio r_A/r_B of 1.149–1.219 ([Springer, *High Energy Chem.*](https://link.springer.com/article/10.1134/S0018143924701601)). For BCC alloys, hydride destabilization is reported above VEC ≈ 4.75, with the best capacity/cyclability compromise in a narrow **VEC 4.75–5.0** window, and a TiZrCrMnFeNi HEA was designed around a total VEC of 6.4 for AB₂H₃ formation ([Kurbanbekov et al. 2026](https://doi.org/10.3390/met16060577)). **These windows are family-specific — do not apply one globally.**
- **Hume-Rothery / HEA solid-solution criteria.** δ (atomic size difference), ΔH_mix, ΔS_mix and Ω. Canonical sources: [Zhang et al. (2008), *Adv. Eng. Mater.* 10, 534–538](https://doi.org/10.1002/adem.200700240) and [Yang & Zhang (2012), *Mater. Chem. Phys.* 132, 233–238](https://doi.org/10.1016/j.matchemphys.2011.11.021) (Ω–δ criterion: solid solution when −20 < ΔH_mix < 5 kJ/mol, 12 < ΔS_mix < 17.5 J/K·mol, δ < 6.4%).
- **Miedema model.** [Miedema, de Boer & Boom (1977), *Calphad* 1, 341–359](https://doi.org/10.1016/0364-5916(77)90011-6) for formation enthalpies of alloys; [extended to predict hydrogen content in binary and ternary hydrides](https://www.sciencedirect.com/science/article/abs/pii/S0925838801019399). Miedema's "reverse stability" rule — a lower host-compound formation enthalpy gives a *more* stable hydride — is a useful sanity direction. This project already computes `Mixing enthalpy` and `Miedema_deltaH_ss_min`, so the machinery exists.

### 5.2 Thermodynamic screens

- **van 't Hoff.** ln p_H₂ = ΔH/RT − ΔS/R links plateau pressure, temperature and thermodynamics; ΔS is roughly constant at ~130 J K⁻¹ mol⁻¹ across metal–hydrogen systems (dominated by loss of gas-phase H₂ entropy). This means a **single predicted ΔH is nearly sufficient to place a candidate on a temperature/pressure map** — a very high-value, low-cost addition if a ΔH model is trained from ML-HydPARK.
- **Convex hull / formation energy.** Query [Materials Project](https://doi.org/10.1063/1.4812323), [OQMD](https://doi.org/10.1038/npjcompumats.2015.10), [JARVIS](https://doi.org/10.1038/s41524-020-00440-1) or AFLOW for energy above hull. Practical caveat: these are DFT databases of *ordered crystalline* compounds, and disordered multi-element solid solutions frequently have no entry. Treat a hull hit as confirmatory evidence, never as a hard reject.
- **DFT spot-checks.** [Wu & Chen (2026)](https://doi.org/10.3390/coatings16070794) used first-principles calculations to validate the thermodynamic stability of their NSGA-II recommendations. A handful of DFT checks on the top candidates is the standard way to close an inverse-design paper without synthesis.

### 5.3 Cost, toxicity, abundance

- **Price and abundance data.** [Theler, Kauwe & Sparks (2020), *Integr. Mater. Manuf. Innov.* 9, 144–150](https://doi.org/10.1007/s40192-020-00173-5) — elemental production per country and elemental prices 1998–2015, with Herfindahl–Hirschman Index (supply-concentration risk) reported per element per year. HHI is the standard criticality metric for flagging economic/supply risk in a proposed material.
- **Elemental property tables.** [Lee et al. (2024), *Data in Brief* 53, 110178](https://doi.org/10.1016/j.dib.2024.110178) — the Oliynyk elemental property dataset, used across multiple experimentally validated studies.
- **Practical rules for hydrides.** Down-weight or exclude Sc, and rare-earth-heavy formulations if cost is an objective; flag Be, Cd, and heavy-metal toxicity outright. Cost is a *deterministic* function of composition, so it costs nothing to add as an objective and immediately makes the Pareto front more interesting.

### 5.4 Don't rediscover known alloys

Every candidate should be checked against the training set and against external databases before being called "new". [Lu et al. (2025)](https://doi.org/10.20517/jmi.2025.56) reported "27 unreported alloy compositions" — that claim is only meaningful because they checked. Sources to check against: this project's own merged HyStor + ML-HydPARK table (exact-formula and near-neighbour ElMD match), the [HyMARC Hydrogen Storage Materials Database](https://datahub.hymarc.org/dataset/hydrogen-storage-materials-db) (>2000 hydride materials), and the general databases via OPTIMADE. Report the ElMD distance to the nearest known alloy for every proposed candidate — it turns "novel" from an assertion into a number.

---

## 6. Software and libraries

Versions and dates read from the PyPI JSON API and GitHub REST API on **2026-08-29**.

### 6.1 Optimization

| Package | Version | Last release | Licence | Notes |
|---|---|---|---|---|
| [Optuna](https://optuna.readthedocs.io/) | 4.9.0 | 2026-06-01 | MIT | **Already a project dependency.** Ships `NSGAIISampler` and `NSGAIIISampler`; NSGA-II is the *default* sampler for multi-objective studies. Both accept `constraints_func` with constrained-domination handling (>0 = violated). This means a multi-objective constrained search needs **zero new dependencies**. |
| [pymoo](https://pymoo.org/) | 0.6.2 | 2026-06-28 | Apache-2.0 | 2946 stars, pushed 2026-07-07. Purpose-built MOO framework; NSGA-II/III developed [in collaboration with Deb himself](https://doi.org/10.1109/access.2020.2990567) and recommended for official benchmarks. Better diagnostics, hypervolume tooling and MCDM than Optuna. Use if the EA *is* the contribution. |
| [BoTorch](https://botorch.org/) | 0.18.1 | 2026-06-08 | MIT | qEHVI/qNEHVI multi-objective BO. Overkill for a cheap surrogate. |
| [Ax](https://ax.dev/) (`ax-platform`) | 1.3.1 | 2026-06-09 | MIT | Higher-level wrapper over BoTorch. |
| [DEAP](https://pypi.org/project/deap/) | 1.4.4 | 2026-04-17 | LGPL | Flexible EA toolbox; more assembly required than pymoo. |
| [Nevergrad](https://github.com/facebookresearch/nevergrad) | 1.0.12 | 2025-04-23 | MIT | 4204 stars. Gradient-free optimizer zoo. |
| [SMAC3](https://pypi.org/project/smac/) | 2.4.0 | 2026-04-22 | BSD-3 | Algorithm configuration; not the right shape for this task. |
| [scikit-optimize](https://pypi.org/project/scikit-optimize/) | 0.10.2 | **2024-06-04** | BSD-3 | Two years without a release — **avoid for new work**. |

**Recommendation: Optuna for the MVP (already installed), pymoo for the thesis-grade multi-objective run.**

### 6.2 Materials informatics

| Package | Version | Last release / push | Notes |
|---|---|---|---|
| [pymatgen](https://pymatgen.org/) | 2026.5.4 | 2026-05-04, MIT | Already a dependency. `Composition` for formula parsing/validation. |
| [matminer](https://hackingmaterials.github.io/matminer/) | 0.10.1 | 2026-04-14; repo pushed 2026-08-24 | Already a dependency. [Ward et al. 2018](https://doi.org/10.1016/j.commatsci.2018.05.018). Actively maintained. |
| [CBFV](https://github.com/kaaiian/CBFV) | 1.1.0 | **PyPI 2021-10-24; repo pushed 2022-03-30** | Already a dependency and central to this pipeline. **Effectively unmaintained** (my inference from those dates). It works, but pin the version and vendor a copy — do not assume future Python compatibility. Companion paper: [Wang et al. 2020, *Chem. Mater.* 32, 4954](https://doi.org/10.1021/acs.chemmater.0c01907). |
| [mat_discover](https://github.com/sparks-baird/mat_discover) | 2.2.9 | PyPI 2023-06-23; pushed 2024-08-20, MIT | DiSCoVeR: performance vs. novelty trade-off. Semi-maintained. |
| [ElMD](https://github.com/lrcfmd/ElMD) | 0.5.15 | 2025-03-21; pushed 2026-08-20, GPL-3.0 | Element Mover's Distance. **Note GPL-3.0** — matters if the app is to be distributed. |
| ElM2D | 0.4.1 | **2021-10-19**, GPL-3.0 | Bulk pairwise ElMD. Stale; ElMD alone may suffice. |
| [MODNet](https://modnet.readthedocs.io/) | 0.4.5 | 2025-03-19; pushed 2024-05-07, MIT | **Highly relevant.** Purpose-built for limited materials datasets ([De Breuck et al. 2021](https://doi.org/10.1038/s41524-021-00552-2)). Worth benchmarking against the CatBoost model as a thesis comparison — but note the repo is quiet and the mirror queried had 0 stars, so budget integration time. |
| [CrabNet](https://github.com/anthony-wang/CrabNet) | 2.0.8 | 2023-01-10; pushed 2023-04-23, MIT | Composition-only attention network ([Wang et al. 2021, *npj Comput. Mater.* 7, 77](https://doi.org/10.1038/s41524-021-00545-1)). Stale. |
| [Roost](https://github.com/CompRhys/roost) | — | **repo ARCHIVED**, MIT | [Goodall & Lee 2020, *Nat. Commun.* 11, 6280](https://doi.org/10.1038/s41467-020-19964-7). Cite it; don't depend on it. |
| [XenonPy](https://github.com/yoshida-lab/XenonPy) | 0.6.7 | **PyPI 2022-10-31**; pushed 2024-07-15, BSD-3 | 290 compositional features; includes **iQSPR**, a Bayesian inverse-design module. Conceptually interesting for inverse design; stale packaging. |

### 6.3 Generative (reference only — not recommended for this build)

- [MatterGen](https://github.com/microsoft/mattergen) — MIT, 1804 stars, pushed 2026-08-27, **actively maintained**. Fine-tunable toward property constraints. Realistically needs far more data than this project has, and generates *structures*, not composition-property mappings.
- [CDVAE](https://github.com/txie-93/cdvae) — MIT, 378 stars, pushed 2024-08-14.
- [FTCP](https://github.com/PV-Lab/FTCP) — invertible crystal representation + VAE.
- MatGAN / CubicGAN — see §3.4 for references.

### 6.4 Uncertainty quantification

- [MAPIE](https://github.com/scikit-learn-contrib/MAPIE) — v1.5.0 (2026-08-05), BSD-3, 1584 stars, pushed 2026-08-14. Actively maintained, scikit-learn compatible, model-agnostic. **First choice.**
- [crepes](https://pypi.org/project/crepes/) — v0.9.1 (2026-06-12), BSD. Lighter alternative.
- [NGBoost](https://stanfordmlgroup.github.io/projects/ngboost/) — v0.5.11 (2026-06-26), Apache-2.0.
- **CatBoost native** — v1.2.10 (2026-02-18). `Quantile`, `MultiQuantile`, `RMSEWithUncertainty`, virtual ensembles ([docs](https://catboost.ai/docs/en/concepts/loss-functions-regression)). Zero new dependencies.
- LightGBM v4.7.0 — `objective='quantile'` with `alpha`.

### 6.5 Databases and APIs

| Source | Free programmatic API? | Notes |
|---|---|---|
| [Materials Project](https://next-gen.materialsproject.org/api) | **Yes** — `mp-api` v0.46.5 (2026-08-18), free API key | `MPRester` client. Best-maintained of the set. |
| [OQMD](https://oqmd.org/) | **Yes** — REST API; also via OPTIMADE | `qmpy` PyPI package is stale (2020-09-30); use the REST/OPTIMADE route. [Kirklin et al. 2015](https://doi.org/10.1038/npjcompumats.2015.10) |
| [AFLOW](http://aflowlib.org/) | **Yes** — REST/AFLUX; also OPTIMADE | `aflow` PyPI package stale (2020-02-29). |
| [JARVIS](https://jarvis.nist.gov/) | **Yes** — `jarvis-tools` v2026.6.12, MIT, 397 stars, pushed 2025-08-25 | [Choudhary et al. 2020](https://doi.org/10.1038/s41524-020-00440-1). Already used in this project's featurization. |
| [NOMAD](https://nomad-lab.eu/) | **Yes** — own API + OPTIMADE + Python package | |
| **OPTIMADE** | **Yes** — `optimade` v1.5.0 (2026-06-21) | One query across AFLOW, COD, Materials Cloud, MP, NOMAD, odbx, OQMD and more. [Andersen et al. 2021, *Sci. Data* 8, 217](https://doi.org/10.1038/s41597-021-00974-z); [Evans et al. 2024, *Digital Discovery* 3, 1509](https://doi.org/10.1039/d4dd00039k). **Use this instead of four separate clients.** |
| [ML-HydPARK](https://zenodo.org/records/10680097) | No API — Zenodo CSV download (v0.0.5, 2024-02-19) | Witman, Allendorf, Stavila (Sandia). Cite [Witman et al. 2020, *J. Phys. Chem. Lett.* 11, 40–47](https://doi.org/10.1021/acs.jpclett.9b02971). Already in this repo. |
| [HyStor](https://doi.org/10.1016/j.ijhydene.2024.09.390) | No API — supplementary data | [Wilson et al. 2024, *IJHE* 90, 460–469](https://doi.org/10.1016/j.ijhydene.2024.09.390). Already in this repo. |
| [HyMARC Hydrogen Storage Materials DB](https://datahub.hymarc.org/dataset/hydrogen-storage-materials-db) | CKAN portal, CSV download | >2000 hydride materials; incorporates the historical DOE/IEA-HIA HydPark. **Whether the CKAN API is openly queryable is unverified.** |

**On HyStor's scale.** [Wilson et al. (2024)](https://doi.org/10.1016/j.ijhydene.2024.09.390) report HyStor as **1282 data points** across ten alloy classes (AB2, AB, A2B, AB5, Mg, MIC, SS, LEA, MEA, HEA), 54 elements, 200–800 K, 0.1–7.19 wt%, adding 451 compositions to a HydPark that had not been updated since 2002. Their own HYST model reached **MAE 0.29, R² 0.79**. This project reports test R² 0.951 on a formula-disjoint stratified split — a large gap. It is plausibly genuine (different split protocol, different target transform, a tuned CatBoost vs. their model), but the thesis should address it head-on rather than leave a reader to notice it. A leave-one-alloy-class-out number (§4.5) is the cleanest way to settle it.

### 6.6 Application layer

No authoritative survey of what materials-design web tools use was found (**unverified**), so this is a judgement call on documented framework characteristics:

- **Streamlit** (v1.62.0, 2026-08-19) — **recommended.** Pure-Python, fastest path from script to interactive app, good with dataframes and Plotly (already a dependency). The FIND platform is a directly comparable deliverable ([Lu et al. 2025](https://doi.org/10.20517/jmi.2025.56)), though its stack is **unverified**.
- **Gradio** (v6.26.0, 2026-08-24) — oriented to ML model demos with Hugging Face integration; excellent for a single predict-box, weaker for a multi-panel screening dashboard.
- **Dash** (v4.4.1, 2026-07-21, MIT) — more customizable and better-performing than Streamlit, at the cost of more code. Choose if the app must outlive the thesis.
- **FastAPI + React** (FastAPI v0.141.1) — correct for a production service, wrong for a one-person thesis. Do not.

---

## 7. Recommended architectures

Three designs, ranked. Build A, then B. C only if A and B land early.

### Architecture A — "Screen-and-Rank" MVP (recommended first build)

**Effort: 5–8 developer-days.**

```
element subsets + stoichiometry grid + T grid
        │
        ▼
  candidate formulas ──► CBFV generate_features (batched, magpie)
        │                        │
        │                        ▼
        │                 subset to the 22 selected descriptors
        │                        │
        │                        ▼
        │                 fitted RobustScaler (loaded, NOT refitted)
        │                        │
        │                        ▼
        │                 CatBoost (MultiQuantile) ──► P10 / P50 / P90 wt%
        ▼                        │
  physics filters ◄──────────────┤
  (family stoichiometry,         │
   VEC window, δ, ΔH_mix)        ▼
        │                 MAPIE conformal interval
        ▼                        │
  ElMD distance to training set ─┤
        │                        │
        ▼                        ▼
  cost / HHI from element price table
        │
        ▼
  rank by LCB(wt%) ──► top-N table + Streamlit UI
```

**Components:** a `candidate_generator.py` (simplex/stoichiometry enumeration), a `featurize_candidates.py` wrapping the existing CBFV call, a `filters.py` (physics + AD + cost), a `rank.py`, and a one-page Streamlit app. Everything else is already in the repo.

**Main risk:** combinatorial blow-up. 54 elements taken 4 at a time on a fine fraction grid is billions of candidates. **Mitigation:** restrict to one alloy family per run, fix the element subset to 3–5 chemically motivated elements, and use a coarse fraction grid (0.05) first. If the enumeration is still too large, that is precisely the signal to move to Architecture B.

**Second risk:** CBFV featurization throughput. Measure it on day one — it determines whether enumeration or evolution is the right paradigm.

**Thesis claim:** "We invert a validated hydride capacity model by exhaustive, uncertainty-aware and physically constrained virtual screening, and propose N candidate compositions ranked by lower-confidence-bound capacity, each reported with its distance to the nearest known alloy."

### Architecture B — Constrained multi-objective evolutionary design (recommended thesis centerpiece)

**Effort: 18–25 developer-days on top of A.**

Replace enumeration with NSGA-II/III in pymoo (or Optuna's `NSGAIISampler` if avoiding a new dependency).

- **Decision variables:** element-subset selection (integer/categorical) + fractions on the simplex (real, repaired to sum to 1) + optionally temperature.
- **Objectives:** maximize LCB(capacity); minimize raw-material cost; maximize ElMD novelty. (Add minimize |ΔH − target| once a thermodynamics model exists — this is the upgrade that makes the work physically complete.)
- **Constraints** via `constraints_func` / pymoo constraint handling: VEC in the family window, δ bounds, ΔH_mix bounds, minimum element fraction, maximum element count, applicability-domain distance ceiling.
- **Output:** a Pareto front, plus a hypervolume-vs-generations convergence study, plus repeated runs with different seeds to show stability.
- **Post-hoc validation:** OPTIMADE query for each Pareto-optimal candidate to check for existing entries; DFT spot-checks on the top 3–5, following [Wu & Chen (2026)](https://doi.org/10.3390/coatings16070794).

**Main risk:** the optimizer exploits surrogate extrapolation. This is *the* failure mode, and it is why §4.4 and §4.5 are load-bearing rather than decorative. If the Pareto front is populated entirely by exotic chemistries with wide prediction intervals, the guard rails are too weak — tighten the AD ceiling and re-run. Budget time for two or three such iterations; treat them as a result, not a setback.

**Secondary risk:** mixed integer/continuous encoding is fiddly. Simplify by fixing the element subset per run and sweeping subsets in an outer loop — this also makes the results far easier to interpret and present.

**Thesis claim:** "We formulate hydride composition design as a constrained multi-objective optimization problem over the composition simplex, solved with NSGA-II against an uncertainty-calibrated CatBoost surrogate, and report a Pareto front trading capacity against cost and chemical novelty — with an explicit applicability-domain analysis showing where the surrogate can and cannot be trusted."

That claim is directly comparable to [Wu & Chen (2026)](https://doi.org/10.3390/coatings16070794) and [Ji et al. (2025)](https://doi.org/10.1039/d5ta06903c) while adding the UQ + applicability-domain rigour that neither of those emphasizes — which is a genuine, defensible novelty gap.

### Architecture C — Conditional generative / latent-space design (stretch, high risk)

**Effort: 30–45 developer-days, with a real chance of a null result.**

A conditional VAE or cINN over composition vectors (54-dim fraction vector, conditioned on target wt% and temperature), decoding to compositions, with A/B's screening stack as the filter. Compare against the GA baseline.

**Main risk: it probably will not beat the GA at this data scale**, for all the reasons in §4.1. FIND had ~5× the data and still needed a GA alongside its VAE ([Lu et al. 2025](https://doi.org/10.20517/jmi.2025.56)).

**Mitigations if attempted:** work on composition vectors (54 dims) rather than crystal structures — far lower-dimensional than what CDVAE/MatterGen tackle; use a cINN rather than a cVAE, since [cINNs cover multimodal solution sets better than cVAEs](https://doi.org/10.1088/2632-2153/acb48d), which is exactly the many-to-one structure of this problem; and augment the training pool with ML-HydPARK entries not currently used for the capacity model.

**Thesis claim:** "We evaluate conditional generative inverse design against evolutionary search for hydride composition design at realistic experimental data scale, and quantify the data threshold below which generative approaches do not pay off." **A negative result here is publishable and useful** — the field currently lacks a clean statement of that threshold for hydrides. Frame it that way from the start and the risk becomes manageable.

### Ranking summary

| | Effort | Risk | Reuses existing model | Thesis strength |
|---|---|---|---|---|
| **A — Screen-and-Rank** | 5–8 d | Low | Fully | Solid chapter |
| **B — Constrained MOO EA** | +18–25 d | Medium | Fully | Strong centerpiece |
| **C — Conditional generative** | +30–45 d | High | Partly | High variance; good as a comparison study |

*Effort figures are my engineering judgement for one developer already familiar with this codebase, not literature-derived.*

---

## 8. References

**Hydride-specific inverse design and ML**

1. Ji, K.; Banerjee, T.; Witman, M. D.; Allendorf, M.; Stavila, V.; Singh, P. (2025). *Design of Lightweight BCC Multi-Principal Element Alloys with Enhanced Hydrogen Storage Using a Machine Learning-driven Genetic Algorithm.* J. Mater. Chem. A 13, 41274–41289. https://doi.org/10.1039/d5ta06903c
2. Lu, X.; Luo, S.; Li, J.; Chen, M.; Yao, T.; Xu, Z.; Yan, Y.; Li, J. (2025). *FIND: a forward–inverse navigation and discovery platform for hydrogen storage alloys powered by data-driven machine learning.* J. Mater. Inform. 5. https://doi.org/10.20517/jmi.2025.56
3. Wu, Y.; Chen, X. (2026). *Stacking Ensemble Learning with Genetic Algorithm Optimization for Multi-Property Prediction and Inverse Design of BCC-Type V-Based Hydrogen Storage Alloys.* Coatings 16, 794. https://doi.org/10.3390/coatings16070794
4. Liang, X.; Liu, S.; Zhang, H.; Qiu, J.; Fan, C.; Liu, Y.; Yan, Y. (2025). *Machine learning and whale optimization algorithm for enhanced hydrogen storage alloy design.* Mater. Today Commun. 49, 113870. https://doi.org/10.1016/j.mtcomm.2025.113870
5. Zhou, P.; Zhou, Q.; Liu, W.; Lei, N.; Chen, Y.; Jiang, J.; Song, D.; Li, H.-W.; Li, Q.-Y.; Chen, L. (2025). *Resolving the Capacity-Stability-Cost Trilemma in Multi-Principal-Element Hydrogen Storage Alloys Through Multi-Objective Optimization.* Adv. Sci. 12, e13463. https://doi.org/10.1002/advs.202513463
6. Beltrame, G.; Dematteis, E.; Stavila, V.; Rizzi, P.; Baricco, M.; Palumbo, M. (2025). *Application of Machine Learning and Data Augmentation Algorithms in the Discovery of Metal Hydrides for Hydrogen Storage.* Metals 15, 1221. https://doi.org/10.3390/met15111221
7. Witman, M.; Ling, S.; Grant, D. M.; Walker, G. S.; Agarwal, S.; Stavila, V.; Allendorf, M. D. (2020). *Extracting an Empirical Intermetallic Hydride Design Principle from Limited Data via Interpretable Machine Learning.* J. Phys. Chem. Lett. 11, 40–47. https://doi.org/10.1021/acs.jpclett.9b02971
8. Wilson, N.; Verma, A.; Maharana, P. R.; Sahoo, A. B.; Joshi, K. (2024). *HyStor: An experimental database of hydrogen storage properties for various metal alloy classes.* Int. J. Hydrogen Energy 90, 460–469. https://doi.org/10.1016/j.ijhydene.2024.09.390
9. Halpren, E.; Yao, X.; Chen, Z. W.; Singh, C. V. (2024). *Machine learning assisted design of BCC high entropy alloys for room temperature hydrogen storage.* Acta Mater. 270, 119841. https://doi.org/10.1016/j.actamat.2024.119841
10. Mahanta, B. K.; Kumar, S.; Pathak, S. K.; Singh, S. K. (2025). *Machine learning-based prediction of high-entropy alloys for hydrogen storage with optimized thermodynamic and kinetic parameters.* J. Energy Storage 139, 118865. https://doi.org/10.1016/j.est.2025.118865
11. Yu, L.; Jiang, S.; Hu, C.; Wang, Y.; Xu, L.; He, H.; Wang, Y.; Du, X. (2025). *Machine Learning for Hydrogen Storage Properties of TiFe Alloys Based on Literature-Curated Data Set: Prediction and Limitation.* ACS Sustainable Chem. Eng. 13, 20810–20824. https://doi.org/10.1021/acssuschemeng.5c09139
12. Liu, T.; Xue, L.; Cheng, B.; Zhao, Y.; Dou, B.; Paredes, M.; Song, L. (2025). *Machine learning-driven alloy digital design for hydrogen storage: a review.* Digital Twin 2. https://doi.org/10.1080/27525783.2025.2511889
13. Kurbanbekov, S.; Skakov, M.; Kaisaruly, T.; Amangeldiyeva, Y.; Ramankulov, S.; Tussupzhanov, A.; Dauletkhanov, Y. (2026). *High-Entropy Alloys as Materials for Solid-State Hydrogen Storage: From Fundamental Principles to Directed Design Strategies.* Metals 16, 577. https://doi.org/10.3390/met16060577
14. Zhang, D.; Jia, X.; Tran, H. B.; Jang, S. H.; Zhang, L.; Sato, R.; Hashimoto, Y.; Sato, T.; Konno, K.; Orimo, S.; Li, H. (2026). *"DIVE" into hydrogen storage materials discovery with AI agents.* Chem. Sci. 17, 3031–3042. https://doi.org/10.1039/d5sc09921h
15. Witman, M.; Allendorf, M.; Stavila, V. *ML-HydPARK dataset v0.0.5* (2024). Zenodo. https://zenodo.org/records/10680097

**Generative and RL inverse design (general materials)**

16. Zeni, C.; Pinsler, R.; Zügner, D.; Fowler, A.; Horton, M.; Fu, X.; et al. (2025). *A generative model for inorganic materials design (MatterGen).* Nature 639, 624–632. https://doi.org/10.1038/s41586-025-08628-5
17. Xie, T.; Fu, X.; Ganea, O.-E.; Barzilay, R.; Jaakkola, T. (2022). *Crystal Diffusion Variational Autoencoder for Periodic Material Generation.* ICLR 2022. https://arxiv.org/abs/2110.06197
18. Dan, Y.; Zhao, Y.; Li, X.; Li, S.; Hu, M.; Hu, J. (2020). *Generative adversarial networks (GAN) based efficient sampling of chemical composition space for inverse design of inorganic materials.* npj Comput. Mater. 6, 84. https://doi.org/10.1038/s41524-020-00352-0
19. Zhao, Y.; Al-Fahdi, M.; Hu, M.; Siriwardane, E. M. D.; Song, Y.; Nasiri, A.; Hu, J. (2021). *High-Throughput Discovery of Novel Cubic Crystal Materials Using Deep Generative Neural Networks (CubicGAN).* Adv. Sci. 8, 2100566. https://doi.org/10.1002/advs.202100566
20. Ren, Z.; Tian, S. I. P.; Noh, J.; Oviedo, F.; et al. (2022). *An invertible crystallographic representation for general inverse design of inorganic crystals with targeted properties (FTCP).* Matter 5, 314–335. https://doi.org/10.1016/j.matt.2021.11.032
21. Noh, J.; Kim, J.; Stein, H. S.; Sanchez-Lengeling, B.; Gregoire, J. M.; Aspuru-Guzik, A.; Jung, Y. (2019). *Inverse Design of Solid-State Materials via a Continuous Representation (iMatGen).* Matter 1, 1370–1384. https://doi.org/10.1016/j.matt.2019.08.017
22. Jiang, Y.; Li, J.; Yang, X.; Yuan, R. (2024). *Applications of generative adversarial networks in materials science.* Mater. Genome Eng. Adv. 2, e30. https://doi.org/10.1002/mgea.30
23. Karpovich, C.; Pan, E.; Olivetti, E. A. (2024). *Deep reinforcement learning for inverse inorganic materials design.* npj Comput. Mater. 10, 287. https://doi.org/10.1038/s41524-024-01474-5
24. Yu, Y.; Bian, X.; Xiong, J.; Wu, X.; Qian, Q. (2026). *AIMatDesign: knowledge-augmented reinforcement learning for inverse materials design under data scarcity.* npj Comput. Mater. 12. https://doi.org/10.1038/s41524-025-01894-x
25. Luce, A.; Mahdavi, A.; Wankerl, H.; Marquardt, F. (2023). *Investigation of inverse design of multilayer thin-films with conditional invertible neural networks.* Mach. Learn.: Sci. Technol. 4, 015014. https://doi.org/10.1088/2632-2153/acb48d
26. Han, X.-Q.; Wang, X.-D.; Xu, M.-Y.; Feng, Z.; Yao, B.-W.; Guo, P.-J.; Gao, Z.-F.; Lu, Z.-Y. (2025). *AI-driven inverse design of materials: Past, present and future.* Chinese Physics Letters 42, 027403. https://doi.org/10.1088/0256-307X/42/2/027403

**Small-data ML, descriptors and validation**

27. Ward, L.; Agrawal, A.; Choudhary, A.; Wolverton, C. (2016). *A general-purpose machine learning framework for predicting properties of inorganic materials (Magpie).* npj Comput. Mater. 2, 16028. https://doi.org/10.1038/npjcompumats.2016.28
28. Ward, L.; Dunn, A.; Faghaninia, A.; et al. (2018). *Matminer: An open source toolkit for materials data mining.* Comput. Mater. Sci. 152, 60–69. https://doi.org/10.1016/j.commatsci.2018.05.018
29. Wang, A. Y.-T.; Murdock, R. J.; Kauwe, S. K.; Oliynyk, A. O.; Gurlo, A.; Brgoch, J.; Persson, K. A.; Sparks, T. D. (2020). *Machine Learning for Materials Scientists: An Introductory Guide toward Best Practices.* Chem. Mater. 32, 4954–4965. https://doi.org/10.1021/acs.chemmater.0c01907
30. Wang, A. Y.-T.; Kauwe, S. K.; Murdock, R. J.; Sparks, T. D. (2021). *Compositionally restricted attention-based network for materials property predictions (CrabNet).* npj Comput. Mater. 7, 77. https://doi.org/10.1038/s41524-021-00545-1
31. Goodall, R. E. A.; Lee, A. A. (2020). *Predicting materials properties without crystal structure: deep representation learning from stoichiometry (Roost).* Nat. Commun. 11, 6280. https://doi.org/10.1038/s41467-020-19964-7
32. De Breuck, P.-P.; Hautier, G.; Rignanese, G.-M. (2021). *Materials property prediction for limited datasets enabled by feature selection and joint learning with MODNet.* npj Comput. Mater. 7. https://doi.org/10.1038/s41524-021-00552-2
33. Dunn, A.; Wang, Q.; Ganose, A.; Dopp, D.; Jain, A. (2020). *Benchmarking materials property prediction methods: the Matbench test set and Automatminer reference algorithm.* npj Comput. Mater. 6, 138. https://doi.org/10.1038/s41524-020-00406-3
34. Baird, S. G.; Diep, T. Q.; Sparks, T. D. (2022). *DiSCoVeR: a materials discovery screening tool for high performance, unique chemical compositions.* Digital Discovery 1, 226–240. https://doi.org/10.1039/d1dd00028d
35. Durdy, S.; Gaultois, M. W.; Gusev, V. V.; Bollegala, D.; Rosseinsky, M. J. (2022). *Random projections and kernelised leave one cluster out cross validation: universal baselines and evaluation tools for supervised machine learning of material properties.* Digital Discovery 1, 763–778. https://doi.org/10.1039/d2dd00039c
36. Li, K.; Rubungo, A. N.; Lei, X.; Persaud, D.; Choudhary, K.; DeCost, B.; Dieng, A. B.; Hattrick-Simpers, J. (2025). *Probing out-of-distribution generalization in machine learning for materials.* Commun. Mater. 6, 9. https://doi.org/10.1038/s43246-024-00731-w
37. Karras, T.; Aittala, M.; Hellsten, J.; Laine, S.; Lehtinen, J.; Aila, T. (2020). *Training Generative Adversarial Networks with Limited Data.* NeurIPS 33. https://papers.nips.cc/paper/2020/file/8d30aa96e72440759f74bd2306c1fa3d-Paper.pdf

**Optimization and uncertainty quantification**

38. Deb, K.; Pratap, A.; Agarwal, S.; Meyarivan, T. (2002). *A fast and elitist multiobjective genetic algorithm: NSGA-II.* IEEE Trans. Evol. Comput. 6, 182–197. https://doi.org/10.1109/4235.996017
39. Blank, J.; Deb, K. (2020). *pymoo: Multi-Objective Optimization in Python.* IEEE Access 8, 89497–89509. https://doi.org/10.1109/access.2020.2990567
40. Akiba, T.; Sano, S.; Yanase, T.; Ohta, T.; Koyama, M. (2019). *Optuna: A Next-generation Hyperparameter Optimization Framework.* KDD '19, 2623–2631. https://doi.org/10.1145/3292500.3330701
41. Daulton, S.; Balandat, M.; Bakshy, E. (2020). *Differentiable Expected Hypervolume Improvement for Parallel Multi-Objective Bayesian Optimization.* NeurIPS 33. https://arxiv.org/abs/2006.05078
42. Xue, D.; Balachandran, P. V.; Hogden, J.; Theiler, J.; Xue, D.; Lookman, T. (2016). *Accelerated search for materials with targeted properties by adaptive design.* Nat. Commun. 7, 11241. https://doi.org/10.1038/ncomms11241
43. Gopakumar, A. M.; Balachandran, P. V.; Xue, D.; Gubernatis, J. E.; Lookman, T. (2018). *Multi-objective Optimization for Materials Discovery via Adaptive Design.* Sci. Rep. 8, 3738. https://doi.org/10.1038/s41598-018-21936-3
44. Duan, T.; Avati, A.; Ding, D. Y.; Thai, K. K.; Basu, S.; Ng, A. Y.; Schuler, A. (2020). *NGBoost: Natural Gradient Boosting for Probabilistic Prediction.* ICML, PMLR 119. https://proceedings.mlr.press/v119/duan20a.html
45. Angelopoulos, A. N.; Bates, S. (2023). *Conformal Prediction: A Gentle Introduction.* Found. Trends Mach. Learn. 16, 494–591. https://doi.org/10.1561/2200000101
46. Cordier, T.; Blot, V.; Lacombe, L.; Morzadec, T.; Capitaine, A.; Brunel, N. (2023). *Flexible and Systematic Uncertainty Estimation with Conformal Prediction via the MAPIE library.* PMLR 204. https://proceedings.mlr.press/v204/cordier23a.html

**Physical models, design rules and databases**

47. Miedema, A. R.; de Boer, F. R.; Boom, R. (1977). *Model predictions for the enthalpy of formation of transition metal alloys.* Calphad 1, 341–359. https://doi.org/10.1016/0364-5916(77)90011-6
48. Guo, S.; Ng, C.; Lu, J.; Liu, C. T. (2011). *Effect of valence electron concentration on stability of fcc or bcc phase in high entropy alloys.* J. Appl. Phys. 109, 103505. https://doi.org/10.1063/1.3587228
49. Zhang, Y.; Zhou, Y. J.; Lin, J. P.; Chen, G. L.; Liaw, P. K. (2008). *Solid-Solution Phase Formation Rules for Multi-component Alloys.* Adv. Eng. Mater. 10, 534–538. https://doi.org/10.1002/adem.200700240
50. Yang, X.; Zhang, Y. (2012). *Prediction of high-entropy stabilized solid-solution in multi-component alloys.* Mater. Chem. Phys. 132, 233–238. https://doi.org/10.1016/j.matchemphys.2011.11.021
51. Jain, A.; Ong, S. P.; Hautier, G.; et al. (2013). *The Materials Project: A materials genome approach to accelerating materials innovation.* APL Mater. 1, 011002. https://doi.org/10.1063/1.4812323
52. Kirklin, S.; Saal, J. E.; Meredig, B.; et al. (2015). *The Open Quantum Materials Database (OQMD): assessing the accuracy of DFT formation energies.* npj Comput. Mater. 1, 15010. https://doi.org/10.1038/npjcompumats.2015.10
53. Choudhary, K.; Garrity, K. F.; Reid, A. C. E.; et al. (2020). *The joint automated repository for various integrated simulations (JARVIS) for data-driven materials design.* npj Comput. Mater. 6, 173. https://doi.org/10.1038/s41524-020-00440-1
54. Andersen, C. W.; Armiento, R.; Blokhin, E.; et al. (2021). *OPTIMADE, an API for exchanging materials data.* Sci. Data 8, 217. https://doi.org/10.1038/s41597-021-00974-z
55. Evans, M. L.; Bergsma, J.; Merkys, A.; et al. (2024). *Developments and applications of the OPTIMADE API for materials discovery, design, and data exchange.* Digital Discovery 3, 1509–1533. https://doi.org/10.1039/d4dd00039k
56. Theler, B.; Kauwe, S. K.; Sparks, T. D. (2020). *Materials Abundance, Price, and Availability Data from the Years 1998 to 2015.* Integr. Mater. Manuf. Innov. 9, 144–150. https://doi.org/10.1007/s40192-020-00173-5
57. Lee, S.; Chen, C.; Garcia, G.; Oliynyk, A. (2024). *Machine learning descriptors in materials chemistry used in multiple experimentally validated studies: Oliynyk elemental property dataset.* Data in Brief 53, 110178. https://doi.org/10.1016/j.dib.2024.110178

**Documentation and repositories**

58. CatBoost — *Regression: objectives and metrics* (Quantile, MultiQuantile, RMSEWithUncertainty). https://catboost.ai/docs/en/concepts/loss-functions-regression
59. Optuna — `optuna.samplers.NSGAIISampler` / `NSGAIIISampler`. https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.NSGAIISampler.html
60. pymoo — NSGA-II / NSGA-III documentation. https://pymoo.org/algorithms/moo/nsga2.html
61. BoTorch — Multi-Objective Bayesian Optimization. https://botorch.org/docs/multi_objective
62. MAPIE — conformal prediction for scikit-learn. https://github.com/scikit-learn-contrib/MAPIE
63. CBFV — Composition-Based Feature Vectors. https://github.com/kaaiian/CBFV
64. ElMD — Element Mover's Distance. https://github.com/lrcfmd/ElMD
65. mat_discover / DiSCoVeR. https://github.com/sparks-baird/mat_discover
66. MODNet documentation. https://modnet.readthedocs.io/en/latest/
67. MatterGen (Microsoft). https://github.com/microsoft/mattergen
68. Materials Project API (`mp-api`). https://docs.materialsproject.org/downloading-data/using-the-api
69. HyMARC Hydrogen Storage Materials Database. https://datahub.hymarc.org/dataset/hydrogen-storage-materials-db
