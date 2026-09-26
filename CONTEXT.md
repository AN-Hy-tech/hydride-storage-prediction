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

**Score**:
One number about the model **together with its reading, its interval — or the stated reason it
has none — and the run that produced it**. The procedure, artifact and transfer scores below are
the three kinds; a bare figure without the other parts is not a score, it is a number somebody will
quote for the wrong question.
_Avoid_: "metric" or "reading" for the whole object *(a reading is one part of a score)*

> *State of the term* (card #83, 2026-09-26): built as `hydms.evidence.reader.Score`, which
> cannot be constructed half-stated. A present value carries an interval or
> `no_interval_because`, and an absent one carries `absent_because`. The service serves them on
> `GET /v1/evidence`.

**Procedure score**:
How well the *modelling method* performs, estimated out-of-fold across every outer fold. It comes
from several models, none of which is ever shipped. The published reading is
`reports/model/evaluation.md`.
_Avoid_: "the R²", "the model's score", "test score", "CV score"

**Artifact score**:
How well **one specific promoted model** performs on rows it has never seen. One model, one held-out
split, one number, tied to an artifact version. The promoted version's is committed in
`reports/model/artifact-score.csv`, generated from its sealed gate record (#103).
_Avoid_: "the R²", "the final score", "the real score"

**Transfer score**:
How well a model predicts an **alloy family it was never trained on** — the leave-one-alloy-class-out
reading. A claim about extrapolation, and the only one of the three that speaks to inverse design.
_Avoid_: "generalisation", "the LOACO number" *(the protocol is leave-one-class-out; the score is
the transfer score)*

> **State of the term (2026-09-26):** quote it **with its run date** where the run record has one.
> Neither run so far does, so each is named by its commit: two seeded runs gave macro 0.2734
> (committed 2026-09-06) and 0.2559 (committed 2026-09-25; the one on disk), with Mg moving
> −0.338 → −0.508.
> #104 found the step that varied on 2026-09-26: the label screen's forest summed its trees in
> thread-finishing order. It now runs on one thread. Both committed runs predate that fix, so each
> is one draw from a spread nobody has sized. The next full run is the first expected to repeat.
> When #104 closes, rewrite this block.

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

**Run record**:
What a run writes about **itself** beside the tables it produced: which protocol, whether it was a
probe, the seed, the code and packages it ran on, and when it started and finished. It identifies a
run of the pipeline, never a model — a model is identified by its artifact version.
_Avoid_: "manifest" *(that is an artifact's)*, "metadata"

> *State of the term, not part of the definition* (card #105, 2026-09-26): built.
> `hydms/provenance.py` writes and reads it, and "is this a result?" is its `result()`, which
> nothing else re-implements (a source-parsing test holds the serving, screening, figure and gate
> packages to that). `train`, `loco`, `evaluate`, `calibrate` and `select` (#106) write one. The
> two committed records, `model-run.csv` and `loco-run.csv`, predate it and are not
> rewritten until the next real run replaces them.

**Run date**:
When the run **started**, as its own run record states. Not the date its tables were committed,
which can be hours later and on another day. A run whose record predates the field has **no run
date** — it is stated as not recorded, never inferred from the commit.
_Avoid_: "commit date" as a synonym, "date of the results"

> *State of the term* (card #105, 2026-09-26): every run from now on records `started_at` in
> local time with its offset, so the run date is the day the maintainer started it. **No
> committed run has one yet.** `loco.md` and `evaluation.md` both print *not recorded*, and the
> Chapter 1 paragraph on the two LOACO runs names them by commit, labelled as commits.

**As published**:
A figure from `REPORT.md` or the archival pipeline. It is *history*, not current performance, and
was produced by a pipeline with thirteen named leaks.
_Avoid_: quoting it without the qualifier

**Reading** *(of a number)*:
**Which evidence set a number was computed over** — never how the number was produced. The three
scores above are three readings of one model; `reports/model/evaluation-metrics.csv` carries a
column of that name; `hydms.figures.charts.parity()` takes one panel per reading, in the same
sense. It is not a synonym for "measured versus predicted": every point in a parity panel is a
prediction, and what the panel's name states is which protocol scored it.
_Avoid_: "reading" for the origin of a mark *(the charts call that `origin`, deliberately)*, and
"the out-of-fold reading" as though it named a model

> *State of the term, not part of the definition* (card #81, 2026-09-12): the collision was caught
> before it landed rather than after. `Series` was first written with a `reading` field holding
> `measured` / `predicted`, which would have put two senses of the word inside one module and one
> import of `evaluate`'s tables away from a page that draws both. The chart vocabulary has
> `Series.origin` instead, and `parity(readings=...)` keeps the word in the sense this glossary
> defines. Nothing enforces that — this entry is the whole of it.

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
> `delivery_screens()`. HG-2 adds the behavioural half: every `return` on the path is read from
> its source and required to be one of the two contract types — **exhaustively, not by
> sampling** — and eleven probes run against the served artifact. Since #84 (2026-09-26) the path
> is three functions: `predict_capacity` is `predict_many([request])[0]`, `predict_many` returns
> only what it stored in `answers`, and `_answer` builds each one. HG-2 reads all three, and the
> delegation between them.

>
> **The layer is the qualifier.** The surrogate alone still does not refuse an out-of-domain
> candidate, and its docstring still says so outright — so "prediction" in this glossary's sense
> is what the *delivery* layer produces, not what `hydms.surrogate.predict` returns.

**Refusal** vs **Invalid request**:
A **refusal** is an answer *about a material*: the screens judged this candidate and declined it, so
it carries a code from their declared vocabulary, a sentence naming the rule, and no number. An
**invalid request** is not an answer at all — the question could not be read, so no candidate ever
existed to judge, and there is nothing a refusal could honestly name. Over HTTP the two share a
status: **422** for both, fixed by `docs/PHASE-H-RUNBOOK.md` §6 for the refusal and by card #78 for
the other. **The body is therefore the whole of the difference** — a refusal carries `refused`, an
invalid request carries `error` — and a client that branches on the status code alone will read one
as the other. A third thing is neither: a `DeliveryError` is the *deployment* failing and is never a
statement about a candidate, so it is a 500.
_Avoid_: "error" for a refusal, "refused" for a malformed request, and reading the status alone

> *State of the term, not part of the definition:* **gate HG-3 measures the distinction at the
> transport** (card #79, `done` 2026-09-12). Eight malformed bodies are sent over HTTP and each must
> come back 422 carrying `error`, carrying no `refused`, and be **refused** by
> `hydms.delivery.contract.answer_from()`; every refusal must come back carrying `refused`, carrying
> no `error`, and rebuild through the same function into an object equal to the library's. So the
> one-key split is executable rather than a convention — and the failure it exists to catch, a
> client reading a rejected request as an answer, is the one that would otherwise be silent.
>
> **The client keeps it too** (card #82, 2026-09-24). `hydms.delivery.client` returns an
> `InvalidRequest` (not a `Refusal`) for a 422 carrying `error`, and the prediction page words it
> as "No material was judged". Both are tested over a real socket in `tests/delivery/test_app.py`.
>
> **A lookup has only the second kind** (card #82, 2026-09-24 night). `GET /v1/neighbours` judges
> no material, so it has no refusal: a blank formula, an unreadable one or a `k` out of range is a
> 422 carrying `error`, and an unreadable formula carries the novelty screen's own sentence — the
> one `POST /v1/predict` *refuses* the same string with. Same words, different kind, because one
> route judged a material and the other did not.

**Lower confidence bound**:
The bottom of the calibrated interval, and **the ranking signal**. Ranking on the mean is what lets
an optimiser exploit extrapolation.
_Avoid_: "the prediction", "the lower estimate", ranking on the mean

**Interval width**:
The size of the calibrated band for one prediction. **Not a constant** — the correction is estimated
in transformed space and the inverse transform is convex, so the same correction is a wider band at a
high prediction than at a low one.
_Avoid_: reading a single correction constant off a manifest and doubling it

> **A width can be negative, and that is a signal rather than an error** (card #93, 2026-09-12).
> A `MultiQuantile` booster fits its heads jointly without constraining them to be monotone —
> `quantile_metrics` counts `crossings` and measured **23 % of rows** on a small fit — and CQR's
> correction is one constant added to both outer heads, so it shifts a crossed band without
> re-ordering it. On the versions CI resolves, two of three probe candidates came back at
> **−0.094422** and **−0.029760** wt%. `hydms.surrogate.predict` reports that unclipped on purpose;
> `hydms.delivery.contract.Interval` refuses it.
>
> **State of the term:** "width" alone is a *measurement*, not a promise of a positive number. Say
> **crossed band** for the negative case and do not call it a narrow one — the whole danger is that
> `abs()` or a clip turns a defect a screen can see into the most confident-looking row in a batch.
> What the delivery layer should *say* about one is card **#94**, which is open.

**Coverage**:
The share of held-out rows whose true value falls inside the interval, read against the nominal
level the intervals claim. Always reported with the level it is being judged against.
_Avoid_: "accuracy", "confidence"

> **Held-out is load-bearing: coverage on the *calibration* rows is a construction, not a
> measurement** (card #93, 2026-09-12). Split CQR sets the correction to the `k`-th smallest
> conformity score with `k = ceil((n + 1) * level)`, so exactly `k` of `n` calibration rows sit
> inside the widened band and their coverage is `k / n` — on the fixture that found this,
> `46/56 = 0.8214285714285714`, identical on three different installations to every digit. It is a
> property of the arithmetic and it knows nothing about the fit. **Only the held-out number is
> evidence**, and that one is AC-3's.
>
> **State of the term:** never report coverage without saying which rows it is over. A conformal
> guarantee is `>= nominal`, never "closer to nominal" — on a finite calibration set it overshoots
> by up to `(1 + level) / n`, so a *better* uncalibrated model moves the calibrated number
> *further* from nominal. #93 exists because a test asserted the "closer" reading and a better fit
> broke it.

> **The word now names two unrelated numbers, and they are both reported by gates** (card #86,
> 2026-09-12). **Conformal coverage** is the entry above — a property of the *model*, measured
> against a nominal level, owned by AC-3 and card #27. **Test coverage** is the share of
> statements and branches under `hydms/` that the suite executes — a property of the *suite*,
> measured against the `fail_under` floor in `[tool.coverage.report]`, owned by HG-4 and card
> #86. They are both percentages, both called "coverage", both appear in `gate-results.json`,
> and neither says anything whatsoever about the other: a repository can hold 88 % test
> coverage over a model whose intervals cover 71 % of what they promise.
>
> **State of the term:** say *conformal coverage* or *test coverage* whenever both could be
> meant, which in a gate report is always. Bare "coverage" in prose about the model means the
> entry above; bare "coverage" in prose about CI means the floor. HG-4's own result string says
> "line-and-branch coverage of hydms/" for exactly this reason.

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

> *State of the term, not part of the definition:* **the scaler is on its way out of this list**
> (card #23, decided 2026-09-12; removal boxed on #7 since #34 closed). `v1`, `v2` and `v3` carry a
> `scaler` payload and always will — a version is sealed when written — but nothing reads it back
> at inference. The justification for keeping it named exactly one consumer, #48's applicability
> domain, and #48 landed as a *capacity* ceiling that reads no scaled matrix.
>
> **Corrected 2026-09-12, the day after this block was written, by the thing it predicted.** It
> said "the next version written holds a model, its correction and a manifest". The next version
> written was **`v3`**, promoted that evening, and it holds all four. The sentence was wrong about
> *which act changes a payload set*: **`promote` copies the payloads of the version it certifies —
> it fits nothing — so only a fit can drop a key.** The next *fit* is card #7's retrain, which is
> where the box now lives and where this entry changes with it. Until then the definition above is
> true of every version that exists.
>
> *Keep the correction rather than the clean sentence.* Nothing tests this file, so a prediction
> written into it is a claim no diff can go red on; this one survived exactly one day, and it
> survived because the version that falsified it was written by a command nobody thought of as
> writing a version.

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

**Reachable** (a reason code):
That *some* input can make the delivery path emit this code. It is **three different claims** and
they have already been written as one: *reachable at all*, *reachable through a given door*, and
*reached by a particular probe set*. A caller wants the second — "can I receive this by typing a
formula and a temperature?" — and a gate report states the third, because a dozen probes is what a
gate can afford. The three can disagree without any of them being wrong.
_Avoid_: "the code is unreachable" with no door and no measurement behind it

> *State of the term, not part of the definition* (cards #80, #90, 2026-09-12): all three readings
> are live in this repository right now, in documents a reader will put side by side.
> `docs/REFUSALS.md` splits by **door** — the *request* door (`predict_capacity`, a typed formula
> and temperature) against the *frame* door (`apply_screens` over a curated frame, which can also
> **state** a prediction, a band width and an alloy-class label). HG-2 and HG-3 report their own
> **probe set**, and currently record `above-physical-ceiling` and `out-of-domain` as *unreached on
> this fit* — the honest statement for eleven probes. `docs/API.md` reports a **50 x 10 sweep**
> through the request door and marks both reachable, which is a lower bound on what a caller can
> meet. Only `untrusted-family` is unreachable in the strong sense at the request door, and that is
> structural: the API declares exactly two fields, so there is no way to supply the label the rule
> judges.

**Trained range** vs **Applicability domain**:
A **trained range** is a numeric span the training rows covered — the 195–773 K window, the capacity
range, the fourteen feature spans. The **applicability domain** is a judgement about a *candidate
and its prediction*: the composition's physical capacity ceiling at H/M 3, the cross-family capacity
level, the family's measured transfer, and the width of the calibrated band. A candidate inside
every trained range can still be refused, which is why the order is featurise, predict, **then**
screen — a rule that reads a prediction cannot run before one exists.
_Avoid_: "in range" to mean "will be answered", and "out of domain" for a bounds violation (that is
`outside-feature-range`; `out-of-domain` is the cross-family capacity rule)

> **Element coverage is neither.** The corpus contains 50 elements across 780 canonical
> compositions, and **nothing refuses a composition for naming one outside that set** — the novelty
> screen measures ElMD *distance* on a chemical scale instead, which is the better rule, since an
> unseen element near a seen one is better supported than a seen element in an unseen arrangement.
> `docs/API.md` publishes the list because a caller has nowhere else to find it, and says in as many
> words that it is not a bound. Reading it as one is the conflation this entry exists to stop.

**Leak**:
A named, sited way held-out data influenced something before it was scored. Thirteen are inventoried
with their exact locations in the archival pipeline.
_Avoid_: "a bug", "data leakage" unqualified — each of the thirteen has an id, and the id is how it
is discussed

---

## The board

**Stage** (`S0`…`S8`):
A step of Phase H's execution order, owned by `kanban-hardening/README.md` § Stage → card map and
executed by `docs/PHASE-H-RUNBOOK.md` §3. It is stated on a card's **bold line under the title**,
and `No stage` is an assignment — the foundation and CI cards that slot in where their blockers
allow — never an absence.
_Avoid_: "phase" (Phase H is the whole freeze; `Phase 0 / Phase 1 / Phase A` belong to the frozen
board), and **reading an `S`-number in `tags:` as a stage**

**User story** (`S1`…`S12`):
A row of PRD §5 — who wants it, why, and what proves it. It appears in a card's `tags:` as a trace,
which is the entire reason the two collide: `S10` on #78 is "explore results without running code",
and there is no Stage 10.

> *State of the term, not part of the definition:* on 2026-09-11 **thirty-nine of sixty-four cards
> stated the wrong stage** — thirty-six still carrying the frozen board's `Phase` heading after
> #72's `git mv`, two claiming an `S1` the runbook contradicts, one an `S6` the README does. Nothing
> reads that line: not `check_board.py`, not a test, not an `--emit`. All are corrected and **#92**
> is the card for making the map load-bearing. Until it lands, this pair is checked by a reader or
> not at all.

**Blocker** (`blocked_by`):
The board's machine-readable dependency graph, and **the authority on order**. Where a runbook
arrow and a `blocked_by` edge disagree, the edge is right and the arrow is prose — S4 opened at #88,
not at the #24 its chain pointed to. An edge nothing supports is worse than a missing one: #89 was
held shut by an edge to #34 that its own *Done when* never asked for, and that took #83 with it.
_Avoid_: reading the runbook's `→` chains as dependencies; ask the board which card is startable
