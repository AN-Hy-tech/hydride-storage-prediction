# HydMS — the project's vocabulary

A glossary and nothing else. Every term below is one that has been **conflated with another in
this repository at least once**, at a cost — a wrong number quoted, a sentinel aimed at the wrong
object, or five hours of a gate reading green over something it was not guarding. Nothing here is
an implementation detail, a decision, or a specification: those live in `docs/PRD-inverse-design.md`,
the cards, and `docs/adr/`.

**How to use it.** If you are about to write a number or a noun into prose that will be read by
somebody who was not in the room, check it here first. Card #35.

---

## What a number is about

The single most expensive confusion in this project. **Three different R² values exist, they are
all correct, and each answers a different question.** Naming them is what stops one being quoted
for another.

**Procedure score**:
How well the *modelling method* performs, estimated out-of-fold across every outer fold. It comes
from several models, none of which is ever shipped. The published reading is
`reports/model/evaluation.md`.
_Avoid_: "the R²", "the model's score", "test score", "CV score"

**Artifact score**:
How well **one specific promoted model** performs on rows it has never seen. One model, one held-out
split, one number, tied to an artifact version.
_Avoid_: "the R²", "the final score", "the real score"

**Transfer score**:
How well a model predicts an **alloy family it was never trained on** — the leave-one-alloy-class-out
reading. A claim about extrapolation, and the only one of the three that speaks to inverse design.
_Avoid_: "generalisation", "the LOACO number" *(the protocol is leave-one-class-out; the score is
the transfer score)*

> **The gaps between the three are findings in their own right.** A small procedure-to-artifact gap
> is evidence the procedure is stable. A large procedure-to-transfer gap is the argument for every
> guard rail in the project. Publishing one number in place of three destroys both statements — and
> choosing which to publish *after seeing all three* is selecting on the outcome, which is what leak
> L2 is, one layer up.

**Probe**:
A number produced deliberately at a reduced budget to find out what a real run will cost. **Never a
result**, whatever it looks like. Every table that can hold one records `probe` so a reader and a
gate can both tell.
_Avoid_: "a quick run", "a first pass", "preliminary results"

**As published**:
A figure from `REPORT.md` or the archival pipeline. It is *history*, not current performance, and
was produced by a pipeline with thirteen named leaks.
_Avoid_: quoting it without the qualifier

---

## What is being predicted

**Capacity**:
Maximum **material** gravimetric hydrogen storage, in weight percent, for a composition at a
temperature. Always material-level and always maximum.
_Avoid_: "storage", "wt%" alone, "H₂ content"

**Usable capacity**:
What a material actually delivers across a practical pressure and temperature swing. **This project
does not predict it** and has no pressure data with which to.
_Avoid_: treating it as interchangeable with capacity

**System capacity**:
Capacity including the tank, valves and balance of plant. **DOE targets are stated at this level.**
A material at 7 wt% does not meet a 5.5 wt% system target — comparing the two is a two-step
overstatement.
_Avoid_: comparing any model output directly to a DOE target without saying which level it is

---

## What a thing is

**Formula**:
The composition string exactly as the source data spells it. Two formula strings may describe one
material.
_Avoid_: using it as an identity — 1,149 formula strings in this dataset are 1,115 materials

**Canonical composition**:
The identity of a material, independent of how its formula was spelled. **This is what "the same
material" means here**, and it is what splits, folds and any grouping use, always by calling the
one shared key rather than re-deriving it.
_Avoid_: "the formula", "the composition string", re-implementing the key

**Candidate**:
A composition proposed for evaluation that may not exist yet. It is featurised by a forward
function call; descriptors are never inverted.
_Avoid_: "a material", "a sample", "a row"

**Alloy family**:
The structural class a composition belongs to — AB₅, AB₂, AB, A₂B, BCC solid solution, high-entropy,
and so on. **The unit across which this project does not assume transfer.**
_Avoid_: "alloy type", "class" unqualified

---

## What the model produces

**Prediction**:
An estimate together with **an interval and a domain verdict**. A bare number is not a prediction
here — it is a model output that has not yet been made into one.
_Avoid_: "the estimate", "the output", "the number"

> *State of the term, not part of the definition:* **both halves are enforced today, at the
> delivery layer, and gate HG-2 now measures it** (cards #48, #49, #75, #76, #77, all `done`
> 2026-09-11). The interval half is the surrogate's: it returns `lcb` and `interval_width` as
> columns, so a caller cannot get a point estimate without them. The domain-verdict half is
> `hydms.delivery.predict.predict_capacity()`, which answers with a `PredictionResult` whose
> `interval` and `domain` fields have **no defaults and cannot be `None`** — a type rather than a
> check. `novelty` has no default either, so a caller must *say* what it knows; `None` means "not
> measured", and the delivery path itself never returns it, because the novelty screen is in
> `delivery_screens()`. HG-2 adds the behavioural half: every `return` in `predict_capacity` is
> read from its source and required to be one of the two contract types — **exhaustively, not by
> sampling** — and eleven probes run against the served artifact.
>
> **The layer is the qualifier.** The surrogate alone still does not refuse an out-of-domain
> candidate, and its docstring still says so outright — so "prediction" in this glossary's sense
> is what the *delivery* layer produces, not what `hydms.surrogate.predict` returns.

**Lower confidence bound**:
The bottom of the calibrated interval, and **the ranking signal**. Ranking on the mean is what lets
an optimiser exploit extrapolation.
_Avoid_: "the prediction", "the lower estimate", ranking on the mean

**Interval width**:
The size of the calibrated band for one prediction. **Not a constant** — the correction is estimated
in transformed space and the inverse transform is convex, so the same correction is a wider band at a
high prediction than at a low one.
_Avoid_: reading a single correction constant off a manifest and doubling it

**Coverage**:
The share of held-out rows whose true value falls inside the interval, read against the nominal
level the intervals claim. Always reported with the level it is being judged against.
_Avoid_: "accuracy", "confidence"

**Uncertainty** vs **Novelty** vs **Applicability domain**:
Three separate things that all mean "be careful". **Uncertainty** is interval width — how unsure the
model is. **Novelty** is distance to the nearest known alloy — how unlike anything seen this
candidate is. **Applicability domain** is a verdict — whether the candidate is in scope at all.

**The applicability domain is not the novelty distance, and that is measured rather than
stipulated** (card #48, 2026-09-07). Per-class transfer R² does not correlate with how isolated a
family is — Spearman −0.27 in element-fraction space and −0.28 in the model's own 14-feature space,
n = 10, and inverted at the ends. What the domain verdict is actually built on is a **capacity
level**: 5.19 wt%, the highest a candidate can be predicted at while more than one alloy class
still supports the claim. Three documents in this repository said "distance-based AD" before
anybody measured it, which is why this paragraph is here.
_Avoid_: using any of the three to stand for the others; calling the applicability domain a
distance

---

## The model itself

**Deployed fit**:
The one model this project ships, built by a single definition that screens, carves a calibration
slice, fits and calibrates — in that order, all of it or none of it. **The carve comes first**,
because a conformity score computed on a row the model was fitted on is a residual the model has
already minimised.
_Avoid_: "the final fit", "the trained model", "the full-data model" — for one day each of those
named a *different* object, and the committed explainability tables described a model with no band

**Artifact version**:
An immutable directory holding a model, its correction, its scaler and a manifest. **Written once
and never edited**, which is why certifying a version produces a *new* one.
_Avoid_: "the model", "the checkpoint", "the saved model"

**Artifact bundle**:
An **artifact version plus the screens that judge its answers**, loaded once and frozen —
`hydms.delivery.predict.ArtifactBundle`, built only by `load_bundle`. A version is a directory on
disk; a bundle is that directory *and* the rules, their reference sets and the digests of those
references. The distinction is load-bearing in two directions. **A version is sealed and a screen's
reference is not**, so the bundle reports `reference_digests` (SHA-256 of each reference **as
loaded**) to make a mismatch detectable — the fit-time *binding* is #91's and does not exist yet.
And a bundle is the only object that knows both what the screens will read and what the prediction
frame will write, which is why the column agreement is checked there and nowhere else (#76's QA
pass).
_Avoid_: "the model", "the artifacts", using it interchangeably with **artifact version** — and
caching it in a second place, because two caches for one artifact version is the failure the
"loads once" rule exists to prevent

**Promotion**:
The dated, recorded act of pointing `current` at a version. A pointer, so rolling back is a small
write rather than a retrain.
_Avoid_: "deploying", "releasing", "saving the model"

**Waiver**:
A named criterion a promotion is **proceeding without**, recorded on the promotion rather than on
the criterion or in the manifest. It may only ever say a criterion *was not checked* — a failed one
is never waivable — and it dies when the pointer moves.
_Avoid_: "skipping a gate", "overriding the gates", confusing it with disabling the gate check
entirely, which is a different and much wider thing

---

## Checks

**Gate**:
An acceptance criterion executed rather than remembered. An unimplemented gate reports **skipped,
never passed**: a check that cannot tell "checked and fine" from "not checked" is worse than no
check, because it reports safety it has not established.
_Avoid_: "the tests", "the checks", treating a skip as a pass

**Sentinel**:
A test written *against a specific past defect*, which must be demonstrated to go red when that
defect is reintroduced. Sentinels live in the package rather than the test tree, so the pipeline
carries its own guards.
_Avoid_: "a regression test" — a sentinel additionally carries the leak in miniature beside its
corrected twin

**Sentinel subject**:
The object a sentinel actually points at. **A sentinel is only as good as its subject**: one aimed
at a real, wired, working object that has quietly stopped being the thing that ships is guarding in
name only, and reports green while doing it.
_Avoid_: assuming a green sentinel means the right thing was guarded

**Smoke run** (two different things, and they are not interchangeable):
`python -m hydms.pipeline.smoke` is the **chain check** — every pipeline stage over a committed
235-row fixture in about twelve seconds, answering *does the chain still connect?* and nothing
else (card #73). `python -m hydms.surrogate.train --trials 2` is the **cost check** — the whole
cross-validation path at a tiny budget, about ten minutes, answering *will the real run get to the
end?* (`docs/RUNNING-THE-FIT.md` Step 3). Neither produces a quotable number, and they fail for
different reasons: the first goes red when a stage stops connecting to the next, the second when a
fit or a table-writing step is broken.
_Avoid_: "the smoke test" unqualified — say which, or say "the chain check" / "the cost check"

**Leak**:
A named, sited way held-out data influenced something before it was scored. Thirteen are inventoried
with their exact locations in the archival pipeline.
_Avoid_: "a bug", "data leakage" unqualified — each of the thirteen has an id, and the id is how it
is discussed
