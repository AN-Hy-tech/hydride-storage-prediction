---
status: accepted
date: 2026-09-12
cards: "#85, written from the `## Narrative` notes on #76, #78 and #91"
---

# The delivery seam: the API owns no ML logic, and the library owns no I/O

`predict_capacity(formula, temperature_k)` is one deep module holding every step between a typed
composition and a trustworthy answer. The HTTP service is a transport over it that computes
nothing, and the Streamlit pages are HTTP clients of that service rather than in-process callers
of the library. In the other direction, the library performs no I/O: it reads no file per call,
writes no log, and will not write the prediction record that card #91 introduces — the service
does that.

Both halves are the same decision. **One prediction path, one set of guard rails, one thing for a
gate to check.**

---

## Context

Phase H exists because a pipeline produced numbers nobody could defend. The specific failure it
guards against is a confident wrong answer reaching a user, so the phase's deliverable is not a
model but a path that *refuses* when it should: a conformal interval, an applicability verdict and
a novelty distance on every answer, or no number at all.

That guarantee is only worth as much as the number of places it is implemented. Three consumers
were planned on one prediction — the HTTP API (#78), the Streamlit forward page (#82) and the
batch CSV screen (#84). If each assembled its own featurise → predict → screen sequence, the
honest-interval guarantee would become three guarantees that drift, and the gates would have
nothing single to measure.

## Decision

**The evaluator is the deep module; everything above it is a seam.**

Behind `predict_capacity()` sit parsing, canonicalisation, featurisation, column order, the scaler
that must not be refitted, quantile assembly, conformal widening, the applicability check and the
ElMD distance. None of it is reachable from what comes back. What comes back is a
`PredictionResult` that cannot be constructed without an interval and a domain verdict, or a
`Refusal` that has no field a number could occupy.

Above it:

- **The API computes nothing.** Four routes build the contract's own request type, hand it to the
  function, and serialise what comes back. `tests/delivery/test_api.py` parses every module in the
  package and fails on an import of the surrogate, the descriptors, the screens or an array
  library.
- **Streamlit talks HTTP.** The pages are clients of the service, so the API stays the single
  prediction path and gate HG-3 covers the interface too.
- **The library writes nothing.** `predict_capacity()` is pure.

## Why each half, and what was actually considered

### The API owns no ML logic

The alternative is the obvious one: let a handler reach into the bundle it was already handed and
compute what it needs. It is easy, it is faster by one function call, and it is how the API and
the app start disagreeing about what a user is told.

**The check that catches this needed two halves, and the first is the weaker** (#78). An import
scan over `api/` catches a handler reaching for the featuriser. It does not catch the likelier
defect: the handler is *handed* the bundle, and `bundle._surrogate.predict(...)` needs no import
at all. So a second test forbids a handler touching any private attribute of the bundle — which
works only because #76 made everything a transport may legitimately report *public* by design.
Both were staged red before they were trusted.

### The library owns no I/O

This is the half the title omits and the half a future reader is likelier to get wrong, because
the tempting change runs the other way. Card #91 writes a prediction record on every served
answer, and the genuine alternative was for the **library** to own it: then a record exists however
the prediction was obtained, including from a script that bypassed the service, which is a real
guarantee and not a small one.

It was rejected for three reasons, in order of weight:

1. A function with a side effect on every call is untestable in the way this project needs — every
   metamorphic and parity test would write to disk.
2. It breaks the batch path: #84's CSV screen is the case where one call should amortise over many
   rows, and per-call I/O is exactly what cannot be amortised.
3. #76's bundle is memoised. A pure function over an immutable, version-keyed object is a thing
   you can reason about; the same function doing I/O from inside a cache is not.

The consequence is accepted rather than hidden: **a script that imports the library leaves no
record.** The mitigation is that the HTTP door is the recommended one and the documented one
(`docs/API.md` says so in as many words), not that the gap does not exist.

### Why the app is an HTTP client and not an importer

An in-process Streamlit call would be faster and simpler, and it would give the app a private
prediction path that no contract test sees. Gate HG-3 sends HG-2's own probe set over HTTP and
requires the served body to equal the library's `to_dict()` **value for value**, reporting any
difference by JSON pointer; that assurance covers the app only while the app uses the transport it
checks.

*This half is a commitment made ahead of its code.* #82 is unbuilt and its `## Narrative` records
only its creation, so this paragraph is written from #78's notes and the service's own docstring
rather than from experience of the page. It is recorded here now precisely because the next person
to touch this layer will see the HTTP hop as pointless overhead and remove it.

## The five decisions this seam forced

Recorded with their arguments rather than their outcomes, because in every case the argument is
what stops the decision being re-opened.

**1 — The assembly order: null-check, featurise, predict, screen, resolve, answer.** Card #76
offered "screen before featurising" as an alternative and it turns out not to exist.
`ApplicabilityDomain` judges a **prediction** — it bounds the median head against the composition's
physical ceiling and against the capacity level above which the corpus holds one family — so a
screen that reads a prediction cannot run before one exists. Screening first would have meant two
passes and a rule for merging their verdicts, which is a second composition rule and the exact
defect #90 exists to make visible. A parse failure is therefore caught where it raises and mapped
to `indeterminate`, carrying the featuriser's own sentence.

**2 — Novelty is in `delivery_screens()`, so ElMD is required to predict at all.** The stated cost
was making an optional extra mandatory, and it was **already paid**: `pyproject.toml` calls
`novelty` a prediction-path dependency, CI installs it, and this project is GPL-3.0-or-later
*because* ElMD is. Leaving the screen out would have bought only a deployment where
`PredictionResult.novelty` is permanently `None` — a field whose documented meaning is "not
measured" quietly becoming "never measured" — and no test would ever have shown it, because CI
installs the extra. Only a deployment would, by answering with a blank.

**3 — One cache or two.** The delivery bundle memoises by `(store, version)` and
`hydms.surrogate.predict._LOADED` still memoises the surrogate. Two caches, one object: the bundle
holds the surrogate the lower layer already memoised rather than unpickling the booster twice, and
`clear_cache()` clears both. Neither caches the promotion pointer, so a rollback takes effect on
the next call. The exception to "no global mutable state" is stated rather than removed because
both caches hold immutable, content-addressed objects — an artifact version is written once and
never edited, so a key can only ever name one set of bytes.

**4 — A refusal and an invalid request share HTTP 422.** Not chosen. The runbook's acceptance
check fixes a refusal at 422 and card #78 fixes a malformed request there, and neither source
could be bent — so the distinction moved into the body: `refused` versus `error`, sharing no key,
with `answer_from()` refusing the second with its own sentence about a payload that does not say
whether it was refused. This is worth stating because the next reader will see one status code
handling two things and read it as sloppiness rather than as the resolution of a conflict between
two authorities. A 500 stays reserved for `DeliveryError`, which is the deployment failing and
never a statement about a candidate.

**5 — The transport declares less than it can.** Pydantic could enforce a non-empty formula and a
finite temperature. It must not, because `PredictionRequest` already does, and two owners of one
rule is how the sentence a caller is shown comes apart from the sentence the library would have
given. The transport declares only what it alone can see — JSON types, unknown fields,
`extra="forbid"` — and everything semantic reaches the contract and returns as the contract's own
sentence. That is the same "one owner per rule" argument as the seam itself, one level down.

The `extra="forbid"` on the batch body is load-bearing for a reason beyond tidiness: a `frame`
endpoint accepting an alloy-class column would have been easy to write and would have quietly made
`untrusted-family` reachable by typing, widening the vocabulary a user can meet. The HTTP door is
the *same* door as `predict_capacity()`'s, which is why gate HG-2 needed no change when the API
landed.

## Consequences

- **The measured price of the seam is one duplicated featurisation**, about 4 ms on a call whose
  fixed cost is an order of magnitude larger. A candidate is featurised in the delivery path for
  the screens to range-check, and again inside the surrogate, which owns the path from a formula
  to an interval. Removing it would mean either re-deriving the featurisation contract in two
  places or widening the surrogate's interface with a "predict from this matrix" door — the door
  "never scale, never reorder" is closed against.
- **A served prediction costs 66–78 ms** and splits 13 ms featurise / 22 ms surrogate / 34 ms
  screens. There is no hot spot and none of it is work: it is per-call pandas overhead on a one-row
  frame, three times over. The batch limit of 256 follows from that being linear with nothing
  amortised. The fix for a CSV of thousands is a batched call *in the library*, not a cleverer
  handler — which is #84's problem and is boxed there.
- **`docs/API.md` documents the HTTP door as the contract** and the library door as a short
  section, rather than as two parallel references. Two references for one seam is how a seam ends
  up with two stories.
- The library's purity is what makes #91 possible as a *service* concern, and #91's replay test is
  what will eventually prove the two doors agree over time rather than only at one commit.

## What would justify reversing this

Each of these is a real condition, not a rhetorical one:

- **A consumer that cannot speak HTTP.** If the thesis needs the predictor inside a notebook or a
  batch job where running a server is genuinely impractical, the answer is not to let that caller
  assemble its own path — it is to make the library door first-class and move HG-3's parity burden
  onto it. The seam would survive; only which side is canonical would change.
- **Batch cost dominating.** If #84 shows that per-row HTTP is the bottleneck for realistic CSVs,
  the correct response is a batched entry point *in the library* that the service calls once, not
  a handler that loops. That changes the interface, not the seam.
- **The purity claim becoming false anyway.** If `predict_capacity()` ever acquires I/O for some
  other reason, the argument for keeping the record in the service evaporates and #91 should be
  revisited whole.

What would **not** justify reversing it: that the HTTP hop looks like overhead. It is the overhead
that buys one prediction path, and the cost has been measured and written down above.

## Related

- [ADR index](README.md)
- `docs/API.md` — the caller-facing contract, generated
- `docs/REFUSALS.md` — every sentence the delivery path can produce, generated
- Cards #75, #76, #77, #78, #79, #85, #91
