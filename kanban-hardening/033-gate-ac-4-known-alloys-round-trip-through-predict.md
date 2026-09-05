---
id: 33
status: done
priority: High
blocked_by: [5, 28]
assignee: "@amirhossein"
tags: [p1, l3, AC-4]
---

# GATE AC-4: known alloys round-trip through predict()

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** That the screening path and the training path agree.

## Why this exists

Ten known training alloys fed through `predict()` must reproduce the trained model's
predictions on those same rows.

This catches the two silent failure modes that would otherwise poison every candidate list:
**a refit scaler, and a reordered feature matrix.** Neither raises an error on its own.

## Done when

- [x] Ten training rows selected across different alloy classes — `_spread()` takes them round-robin over `Alloy_class`, one per class before a second from any, and the real run reached **all ten** (A2B, AB, AB2, AB5, HEA, LEA, MEA, MIC, Mg, SS). Deterministic and unseeded: a gate that sampled would report a failure nobody could reproduce
- [x] Predictions via the screening path match the training-time predictions to floating tolerance — **0.0000e+00** over all 30 predictions against a `1e-12` bar
- [x] Failure output shows per-feature values from both paths so the mismatch is diagnosable — and it separates the two failures this card names: when the two matrices hold the *same set* of values it says **column ORDER**, and when they do not it says a different computation. Both verdicts are exercised directly in `tests/gates/test_ac4_round_trip.py`, because reaching them through `predict()` could only ever produce one of them
- [x] Registered as `AC-4` and run by CI (fast lane; AC-3 and AC-4 together are 1.8 s)

- [x] **Compare like with like: `predict()` returns the CALIBRATED band (from #28).** Done, and measured rather than assumed: `test_the_raw_heads_would_have_failed_this_gate_on_a_working_pipeline` performs the wrong comparison once and requires it to fail on the outer two heads while passing on the median — which is exactly what this box predicts. The
      training-time heads are `QuantileModel.predict(features)` — raw. `predict()` widens the outer
      two by card #27's stored constant before back-transforming, so a round-trip that compares all
      three columns against a training-time `model.predict` will match on the median and fail on
      `q0.1` and `q0.9` by the transformed correction, every time, on a pipeline that is working.
      Either score the median head alone, or build the reference with
      `hydms.surrogate.conformal.calibrated_heads(model, features, conformal=conformal)`, which is
      exactly what `predict()` calls. `lcb` and `interval_width` are derived columns and are not
      part of the round trip
- [x] **The interface, so the gate does not re-assemble it:**
      `hydms.surrogate.predict.predict(formulas, temperatures, version=, store=)` returns
      `[q0.1, q0.5, q0.9, lcb, interval_width]` in weight percent on the caller's index;
      `load_surrogate(...).feature_names` is the fitted column order the failure output must show
      both paths' values for. `store=` points it at a directory, which is how this gate scores a
      candidate version before the promotion pointer moves

- [x] **AC-4 passed against `artifacts/v1` on 2026-09-06 — in a working tree that is not this
      commit.** `python -m hydms.gates run --fast` reported `AC-4 PASSED 0 / 1e-12`: all 30
      predictions agreeing between the screening path and the training path to 0.0000e+00 wt%, over
      10 rows the model grew on across all 10 alloy classes. **Read that with the caveat it needs:**
      at the commit that carries this box, `hydms/gates/ac4_known_alloy_round_trip.py` is still a
      `Pending` stub. The implementation was **uncommitted work by a concurrent session** sharing
      this checkout, alongside `hydms/gates/_artifact.py`, changes to `ac3_conformal_coverage.py`,
      `hydms/surrogate/predict.py` and `tests/gates/conftest.py`. None of it is staged here. So the
      pass is real and was observed, and it is **not** reproducible from this commit alone.

      **What that session's design settles, and it is worth not re-deriving.** The circle this card
      was written to worry about — `load_surrogate` refuses a version whose gates are unestablished,
      and the first thing recorded against a fresh version is a gate run — is answered in
      `hydms/gates/_artifact.py`: load the bundle with `require_gates=False`, the door
      `hydms.artifacts.store` documents for "the card that has just written a version and wants it
      back", then build the `Surrogate` through `surrogate_from`, the same code `load_surrogate`
      runs once it holds a bundle. The only line of the delivery path a gate skips is the check
      whose input that gate is producing. That is option (A) of the three below, taken with the
      guarantee intact. **Confirm it landed before ticking this**, and if it did, strike the three
      options rather than deleting them.

      **It landed, in the commit this box now sits in (2026-09-06).** The stub is gone;
      `hydms/gates/_artifact.py`, `surrogate_from`, both gate implementations and their tests are
      in the tree, and the pass above is reproducible from this commit. The reading in the
      paragraph above is right; what it leaves out is the thing that makes option (A)'s objection
      stop applying — the gate does not merely *avoid* `load_surrogate`, it runs the same assembly
      code. The three options were struck rather than deleted, below.

- [x] ~~**Three ways out, none free, and choosing is this card's job.**~~ **CHOSEN: (A), with the
      objection to it removed rather than accepted (2026-09-06).** Restored here struck, as the box
      above asks, because the reasoning that dissolved the objection is only legible beside the
      objection.

      **(A)** ~~Score through `hydms.artifacts.store.load(version, require_gates=False)`, the door
      the store documents for "the card that has just written a version and wants it back" — but
      then AC-4 does not exercise the delivery path it exists to certify.~~ **Taken.** The "but"
      followed from treating `load_surrogate` as one indivisible thing. It is two — *locating* a
      version, and *assembling* a `Surrogate` from the bundle once you hold it — and only the first
      has any opinion about gates. `surrogate_from(bundle)` is now the second half,
      `load_surrogate` calls it, and so does the gate. The only line of the delivery path AC-4
      skips is the gate check whose input it is producing; a refit scaler and a reordered matrix
      are both downstream of that line and exercised in full.

      **(B)** ~~Give `load_surrogate` a narrow, named escape used only by the gate harness — a hole
      in the guarantee #28 was built to make hole-free.~~ **Rejected, and pinned against.**
      `load_surrogate` grew no parameter and lost no guarantee.
      `tests/gates/test_artifact.py::test_a_version_with_no_gate_report_is_reachable_here_and_nowhere_else`
      asserts in one test that the gate passes over a version *and* that `load_surrogate` still
      raises `GatesIncomplete` on it, so the escape cannot widen without a red test saying so.

      **(C)** ~~Have #34 write a second version carrying the gate report and round-trip *that* —
      honest, and the version numbering then says what happened, at the cost of two versions on
      disk for one model.~~ **Not needed to run a gate.** #34 writes one anyway to *record* the
      result, because a manifest is sealed when it is written — but that is a cost of recording,
      not of checking, and it is #34's to pay.

      **The one thing this does not settle, and the reason a test pins it:**
      `test_the_gate_and_the_delivery_path_assemble_the_same_object`. If those two ever diverge,
      AC-4 is certifying something the search layer never calls — the duplication this gate exists
      to catch, arriving in the checker.

      **Which version a gate scores** is decided in the same module: the promoted one when there is
      one, otherwise the newest on disk, and every result names which and says so. Before #34
      promotes, the newest *is* the candidate; after it promotes, a gate that scored a later
      version would be certifying a model nobody ships.

## Runnable check

```bash
python -m hydms.gates run AC-4
```

## Traces to

`docs/PRD-inverse-design.md` — AC-4

## Narrative

- 2026-09-06: The knot dissolved instead of being cut, and the shape is worth keeping. All three
  written options traded something away — the delivery path, the guarantee, or a version directory
  — because all three treated `load_surrogate` as one decision. It is two, and only one half of it
  is about gates. When a guarantee blocks a legitimate caller, look for the seam inside the
  function before deciding which of the guarantee's clients to disappoint. (by @assistant)
- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
