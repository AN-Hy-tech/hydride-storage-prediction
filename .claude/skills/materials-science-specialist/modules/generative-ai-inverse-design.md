# Generative AI and Inverse Design for Hydrides

**Confidence**: 🟢 Medium-high — derived from a verified, DOI-cited research memo in this repo.
**Primary source**: [`research/inverse-design-methods.md`](../../../../research/inverse-design-methods.md) — read it before answering any inverse-design question. It is longer, more specific, and carries the full citation set. This module is the summary; that memo is the authority.

---

## The one thing to get right

**Do not recommend a VAE, GAN, or diffusion model for this project.** It is the single most likely bad
answer to an inverse-design question here, because it is the fashionable answer everywhere else.

Published materials generative models operate at 10⁴–10⁶ training examples:

| Model | Reference | Training scale |
|---|---|---|
| CDVAE | [Xie et al., ICLR 2022](https://arxiv.org/abs/2110.06197) | MP-20 = 45,231 crystals |
| MatterGen | [Zeni et al. 2025, *Nature* 639, 624](https://doi.org/10.1038/s41586-025-08628-5) | Alex-MP-20, ~600k structures |
| CubicGAN | [Zhao et al. 2021, *Adv. Sci.* 8, 2100566](https://doi.org/10.1002/advs.202100566) | >370,000 ternaries |
| MatGAN | [Dan et al. 2020, *npj Comput. Mater.* 6, 84](https://doi.org/10.1038/s41524-020-00352-0) | ICSD; 2M samples generated |

This project has ~1,280 rows, and fewer distinct chemistries than that (splits are on `unique_formulae`).
Even the one hydride paper that *does* use a VAE had ~6,000 records and still bolted a genetic algorithm
on top to actually produce candidates ([Lu et al. 2025, *J. Mater. Inform.*](https://doi.org/10.20517/jmi.2025.56)).

Supporting evidence that descriptor-based classical ML holds up below ~10⁴ samples where deep models do not:
[Dunn et al. 2020, *npj Comput. Mater.* 6, 138](https://doi.org/10.1038/s41524-020-00406-3) (Matbench, 13 tasks,
312–132k samples) and [De Breuck et al. 2021, *npj Comput. Mater.* 7](https://doi.org/10.1038/s41524-021-00552-2)
(MODNet, built explicitly for the small-data regime). If a *discriminative* deep model is marginal at this
scale, a *generative* one is hopeless.

## What to recommend instead

**Surrogate-guided search in composition space.** Reuse the trained forward model; never invert it.

1. **Enumerate-and-screen (MVP).** Generate candidate formulas over chemically sensible element subsets,
   featurize with the *existing* CBFV pipeline, predict with the *existing* model, filter and rank.
   This is what the real hydride papers do — [Ji et al. 2025, *J. Mater. Chem. A*](https://doi.org/10.1039/d5ta06903c),
   [Liang et al. 2025, *Mater. Today Commun.*](https://doi.org/10.1016/j.mtcomm.2025.113870).
2. **Multi-objective evolutionary search (the thesis centrepiece).** NSGA-II/III over the composition
   simplex, physics rules as *constraints*, output a Pareto front rather than one "best" alloy.
   Precedent: [Wu & Chen 2026, *Coatings*](https://doi.org/10.3390/coatings16070794) (NSGA-II, 3000 candidates);
   [Zhou et al. 2025, *Adv. Sci.*](https://doi.org/10.1002/advs.202513463) (capacity/stability/cost Pareto).

### Why composition space, not feature space

`avg_*` / `dev_*` descriptors are a **many-to-one** map from composition, so descriptor → composition is
ill-posed. Sidestep it: parameterise candidates as (element subset, simplex fractions, temperature),
and recompute descriptors forwards for each one. Every candidate is then a real composition by construction.
Optimising freely in descriptor space lets the optimiser wander into vectors no composition can produce —
the classic failure of unconstrained inverse design.

## Guard rails — non-negotiable

A global optimiser maximising a tree ensemble **will** find regions where the model is confidently wrong;
tree ensembles extrapolate as constants and the optimiser is explicitly hunting extremes.

- **Rank by a lower confidence bound, never the predicted mean.** CatBoost ships `RMSEWithUncertainty`,
  `MultiQuantile` and virtual ensembles natively ([docs](https://catboost.ai/docs/en/concepts/loss-functions-regression)).
- **Conformalise for honest intervals** — [Angelopoulos & Bates 2023](https://doi.org/10.1561/2200000101),
  implemented in [MAPIE](https://github.com/scikit-learn-contrib/MAPIE) or [crepes](https://pypi.org/project/crepes/).
- **Applicability domain.** Element Mover's Distance to the training set ([ElMD](https://github.com/lrcfmd/ElMD));
  [DiSCoVeR](https://doi.org/10.1039/d1dd00028d) trades performance against chemical novelty explicitly.
- **Extrapolative validation.** [Beltrame et al. 2025, *Metals* 15, 1221](https://doi.org/10.3390/met15111221)
  found hydride models generalise *within* an alloy family but not across families. Report leave-one-class-out
  CV alongside random-split R², and expect it to be substantially worse. Saying so is itself a contribution.

## LLMs and agents — for data, not design

[Zhang et al. 2026, *Chem. Sci.* 17, 3031](https://doi.org/10.1039/d5sc09921h) ("DIVE") reads experimental data
out of *graphical elements* in the hydrogen-storage literature, building 30,000+ entries from 4,000 publications.
The relevance here is **data acquisition**: if the project needs more than 1,280 rows, this is the published route.
Do not pitch LLM agents as the design engine.

## Methods to mention but not build

- **Conditional invertible NNs / normalizing flows** — theoretically the *correct* answer to a one-to-many
  inverse problem, sampling the full multimodal solution set. No hydride application found. Worth a thesis
  paragraph as "the principled alternative we lacked data for", not a build target.
- **Reinforcement learning** — [Karpovich et al. 2024](https://doi.org/10.1038/s41524-024-01474-5),
  [AIMatDesign, Yu et al. 2026](https://doi.org/10.1038/s41524-025-01894-x). Defensible, but buys nothing
  a GA does not, at much higher cost.

## High-entropy alloy hydrides

Directly relevant, because HEA design *is* a composition-space problem, and the HyStor data already contains
LEA/MEA/HEA classes that HydPARK lacked ([Wilson et al. 2024](https://doi.org/10.1016/j.ijhydene.2024.09.390)).
- [Halpren et al. 2024, *Acta Mater.* 270, 119841](https://doi.org/10.1016/j.actamat.2024.119841) — ML-designed BCC HEAs for RT storage.
- [Mahanta et al. 2025, *J. Energy Storage* 139, 118865](https://doi.org/10.1016/j.est.2025.118865)
- [Kurbanbekov et al. 2026, *Metals* 16, 577](https://doi.org/10.3390/met16060577) — review.
