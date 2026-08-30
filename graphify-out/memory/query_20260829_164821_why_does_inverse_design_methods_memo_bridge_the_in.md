---
type: "path_query"
date: "2026-08-29T16:48:21.816988+00:00"
question: "Why does Inverse Design Methods Memo bridge the inverse-design community into Data Pipeline and CBFV Featurisation?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["Inverse Design Methods Memo", "Enumerate-and-Screen (Architecture A)", "Optimise in Composition Space (Option A)", "Descriptor Non-Invertibility", "extract_features_cbfv.py", "CBFV Featurisation (Magpie + JARVIS)", "22 Selected Features", "Feature-Space Inversion (Option B)"]
---

# Q: Why does Inverse Design Methods Memo bridge the inverse-design community into Data Pipeline and CBFV Featurisation?

## Answer

The meaningful bridge is 4 hops: Inverse Design Methods Memo -> Enumerate-and-Screen (Architecture A) -> Optimise in Composition Space (Option A) -> extract_features_cbfv.py -> CBFV Featurisation (Magpie + JARVIS). The CLI shortest path routes through the HydMS Project hub instead, which is a hub artifact, not the semantic route.

The load-bearing node is Descriptor Non-Invertibility (research/inverse-design-methods.md:L135), a rationale-type node clustered into the Selected Features community rather than the Inverse Design community. Composition -> descriptor is well-defined but many-to-one, so descriptor -> composition is ill-posed. That constraint is what forces Option A (optimise in composition space, recompute descriptors forward per candidate) over Option B (invert the 22 descriptors, then decode by nearest-neighbour matching). Option A means extract_features_cbfv.py is not just a completed pipeline stage - it becomes the inner loop of the future candidate generator, called per candidate instead of once over a CSV.

Three concrete consequences the graph exposes: (1) all 22 selected descriptors must be pure CBFV/Magpie composition statistics, or any surviving hand-engineered physics feature must be reimplemented as a callable; (2) the fitted RobustScaler must be loaded, never refitted on candidates; (3) CBFV featurisation throughput becomes the deciding factor between enumeration (Architecture A) and evolution (Architecture B).

Graph weakness found: CBFV Featurisation (Magpie + JARVIS) has degree 1 - the memo depends on it critically but connects only via the script node, not the concept node. Feature-Space Inversion (Option B) also has degree 1, correctly reflecting that the memo treats it as a rejected contrast experiment.

## Outcome

- Signal: useful

## Source Nodes

- Inverse Design Methods Memo
- Enumerate-and-Screen (Architecture A)
- Optimise in Composition Space (Option A)
- Descriptor Non-Invertibility
- extract_features_cbfv.py
- CBFV Featurisation (Magpie + JARVIS)
- 22 Selected Features
- Feature-Space Inversion (Option B)