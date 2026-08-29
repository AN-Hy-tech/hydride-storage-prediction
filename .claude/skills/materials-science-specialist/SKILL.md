---
name: materials-science-specialist
description: Materials science expert for hydrogen storage and metal hydrides, specialised for the HydMS thesis project. Covers hydride families and thermodynamics (PCT, van't Hoff, kinetics, degradation), DOE storage targets and system-vs-material capacity, machine learning on small materials datasets (composition featurisation, validation pitfalls, uncertainty, applicability domain), generative AI and inverse design for alloys, and computational materials informatics (DFT, Materials Project/OQMD/AFLOW, HydPARK/HyStor). Use for questions about hydrogen storage capacity, alloy design, hydride physics, or the ML pipeline in this repo.
license: Proprietary
---

# Materials Science Specialist — Hydrogen Storage and Metal Hydrides

> **Status**: rewritten and specialised for this repo, 2026-08-29.
> **Confidence**: Medium-high. Cited claims carry inline links; uncited numeric ranges are indicative.
> Superseded the upstream generic template from [`sandraschi/advanced-memory-mcp`](https://github.com/sandraschi/advanced-memory-mcp).

Domain support for a Master's thesis predicting **maximum H2 storage capacity (wt%)** of hydride alloys from
**chemical formula + temperature**, using CBFV/Magpie descriptors and tree-ensemble regression.

## Read first

**`modules/project-context.md`** — what this repo actually built, with the real numbers. Check it before
quoting any figure about this project; the report is two directories away and guessing is the main failure mode.

## Routing

| If the question is about… | Load |
|---|---|
| Storage classes, DOE targets, why hydrides matter | `modules/hydrogen-storage-fundamentals.md` |
| AB5/AB2/AB/A2B/BCC/HEA families, MgH2, complex hydrides, PCT, van 't Hoff, hysteresis, kinetics, degradation | `modules/metal-hydride-families.md` |
| Featurisation, model choice, validation, leakage, uncertainty, published hydride ML | `modules/ml-for-hydrides.md` |
| Inverse design, generative models, VAE/GAN/diffusion, GA/NSGA-II, LLM agents | `modules/generative-ai-inverse-design.md` |
| DFT, Materials Project/OQMD/AFLOW, HydPARK/HyStor, active learning, tooling | `modules/computational-materials-informatics.md` |
| This repo's pipeline, results, conventions | `modules/project-context.md` |

Full index: `_toc.md`. Provenance and open items: `modules/known-gaps.md`.

## Four errors to avoid

1. **Confusing material-level with system-level capacity.** DOE targets are system-level, including tank and
   balance of plant. A 7 wt% material does not meet a 5.5 wt% system target.
2. **Recommending a VAE/GAN/diffusion model.** At ~1,279 rows this is wrong; published materials generative
   models train on 10^4-10^6 examples. Recommend surrogate-guided search in composition space.
3. **Quoting theoretical capacity as usable capacity.** LiBH4's 18 wt% is not deliverable. Intermetallics
   generally give under 2 wt% usable under practical swings.
4. **Presenting random-split R2 as generalisation.** Hydride models generalise within an alloy family, not
   across families. Always pair it with a leave-one-class-out caveat.

## Stance

This is a thesis. **Defensibility beats a higher R2.** Where a result is fragile, say so and quantify it —
an honest limitation is a contribution, not a weakness. Cite primary sources; mark anything unverified as
**unverified** rather than filling the gap with a plausible number.
