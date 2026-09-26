---
id: 91
status: backlog
priority: P4
blocked_by: [76, 78]
assignee: "@amirhossein"
tags: [ph, l6]
---

# The prediction record, and replay as its consumer

**No stage — belongs beside S6, may sit open across the lift** · **L6 Delivery** · Estimate: 1.5 d

> **Owns (hidden behind this module):** What the system remembers about an answer it gave — and the
> guarantee that the memory is enough to produce that answer again.

## Why this exists

Six months after a candidate is published, the question that will actually be asked is *why did it
say that, and which model said it*. Nothing in this phase can answer it today: a prediction is
computed, returned, and forgotten.

The failure this guards against is the phase's own: a confident wrong answer reaching a user. When
one does, the difference between a fixable defect and an unfalsifiable story is whether the run can
be reconstructed. `REPORT.md` is the cautionary case in this repository — its numbers cannot be
reproduced because nothing recorded what produced them, which is the whole of what `docs/FREEZE.md`
§Why is about.

**A record nobody reads catches nothing.** So the record is not a log: its consumer is a test.
**Replay** is the card's teeth — given a record, re-running its request against the artifact version
it names must reproduce the answer exactly. That makes the record a fixture rather than a stream,
and it catches nondeterminism, artifact drift, and a served path diverging from the library path.

## Done when

- [ ] A `PredictionRecord` type defined in the delivery contract layer beside `PredictionResult`
      (#75): the request as received, the artifact version that answered, every screen that ran with
      its code and reason, the interval, and the novelty distance where one exists
- [ ] **The library does not write it.** `predict_capacity()` (#76) stays pure — a side effect on
      every call is untestable, breaks the batch path, and would make #76's memoised bundle do I/O
      from a function with no reason to. The **service** (#78) writes; the library only returns
- [ ] Records are JSONL under a config-resolved directory, and the card states the `.gitignore`
      decision **explicitly** rather than leaving it to be discovered: real traffic is local and
      unversioned, so the directory is ignored — and therefore no CI check may read it, which is the
      trap found on `artifacts/current.json` (#34). Replay's fixtures are committed separately
- [ ] **Replay:** a committed set of records re-runs against the artifact version each one names and
      reproduces the answer to the tolerance AC-1 uses. A record whose version is absent from the
      store is a **skip with a named reason**, never a silent pass
- [ ] A record for a **refusal** is written on the same path as a record for an answer. A system that
      remembers only what it answered has a blind spot exactly where this phase expects its bugs
- [ ] **`CONTEXT.md` gains one entry: `Prediction record`** — added when this card lands, not before.
      The glossary already holds `Artifact version`, `Probe` and a run-provenance stamp, so "check
      the record" currently has three possible referents. The catalogue in #90 gets **no** entry: it
      is self-describing, lives in one file, and competes with no existing name
- [ ] **Register HG-5 in the gate harness — after `docs/FREEZE.md` says `freeze: lifted`, and not
      before.** One gate covering this card and #90. It is deferred rather than skipped because
      FREEZE.md names HG-1 … HG-4 as an unfreeze condition and a fifth gate would either edit that
      list or need a footnote explaining its absence. Neither this card nor #90 is an unfreeze
      condition; both may sit open across the lift, and this box is the reason one of them will

- [ ] **Bind the screen references to the artifact version, so a mismatch is *detectable* and not
      merely *visible*** (added 2026-09-11 by #76). **Not an unfreeze condition** — `docs/FREEZE.md`
      names HG-1 … HG-4 and the inherited AC criteria, and this widens none of them.

      A promoted artifact version is sealed; `hydms/screens/domain-reference.json` and
      `novelty-reference.json` are not, because they are properties of the **curated data** rather
      than of any one fit. So a served `v2` can in principle be screened against numbers measured
      from data it was never fitted on, and nothing says so. #76 did the half available to it —
      `ArtifactBundle.reference_digests` is the SHA-256 of each reference **as loaded**, so #78's
      `/v1/model` can state which reference answered — but a digest with nothing to compare against
      is provenance, not a check. The missing half is a **fit-time record**: the version's manifest
      (or a sibling written beside it) carrying the digests the fit was validated against, so a
      replay can say *mismatched* rather than only *here is what answered*.

      It lands here rather than on #34 or #4 for two reasons. Replay is the consumer that needs it —
      a record that reproduces an answer must know whether the rules that judged it moved — and #34
      is mid-flight promoting `v2`; adding a manifest field would require a re-save, and a re-save
      that looks like a promotion is the exact confusion FREEZE.md's "named by role, not by number"
      note exists to prevent. Until this lands, the honest reading of a digest is "this is what
      answered", **never** "this matches what was fitted": an absent record means unknown

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_record.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6; `docs/PRD-inverse-design.md` — S2, AC-4

## Narrative

- 2026-09-07: Created alongside #90 from a `/grill-with-docs` session. The split is the point: #90
  needs nothing that is not already `done` and can be worked immediately; this card needs the
  prediction path (#76) and the service (#78), neither of which exists. One card carrying both would
  have been unworkable until S6 and would have delayed the half that addresses the defect that
  prompted the session.

  **The seam decision — the library owns no I/O — is argued in #85, not here.** #85 is already
  titled "ADR: the delivery seam, and why the API owns no ML logic"; this is the same seam from the
  other side, and two ADRs about one seam is how a seam ends up with two stories. A box was added
  there. (by @assistant)
